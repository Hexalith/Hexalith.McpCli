using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Execution;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Projects the immutable Catalog into the public discovery contract.</summary>
public sealed class CatalogService(CatalogProvider provider, ExecutionAvailability availability, bool strict) : ICatalog
{
    /// <inheritdoc />
    public CatalogLookupResult<ModulesDocument> ListModules()
    {
        CatalogAccess access = provider.Get(strict);
        if (access.Catalog is null)
        {
            return new(null, AccessError(access));
        }

        IReadOnlyList<ModuleSummary> modules = Array.AsReadOnly(access.Catalog.Modules
            .Select(module => new ModuleSummary(module.Name, module.Description, module.Operations.Count)).ToArray());
        return new(new ModulesDocument(modules), null);
    }

    /// <inheritdoc />
    public CatalogLookupResult<OperationsDocument> ListOperations(string module, string? kind = null)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(module);
        if (kind is not null && kind is not ("read" or "write"))
        {
            throw new ArgumentException("Kind must be read or write.", nameof(kind));
        }

        CatalogAccess access = provider.Get(strict);
        if (access.Catalog is null)
        {
            return new(null, AccessError(access));
        }

        ModuleDescriptor? selected = access.Catalog.Modules.FirstOrDefault(item => string.Equals(item.Name, module, StringComparison.Ordinal));
        if (selected is null)
        {
            return new(null, new OperationError("unknown_module", Module: module,
                Suggestions: Suggest(module, access.Catalog.Modules.Select(item => item.Name))));
        }

        IReadOnlyList<OperationSummary> operations = Array.AsReadOnly(selected.Operations
            .Where(item => kind is null || string.Equals(PublicKind(item.Kind), kind, StringComparison.Ordinal))
            .Select(item => new OperationSummary(item.Name, PublicKind(item.Kind), item.Description)).ToArray());
        return new(new OperationsDocument(selected.Name, operations), null);
    }

    /// <inheritdoc />
    public CatalogLookupResult<OperationDescriptionDocument> Describe(string operation)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(operation);
        CatalogAccess access = provider.Get(strict);
        if (access.Catalog is null)
        {
            return new(null, AccessError(access));
        }

        (ModuleDescriptor Module, OperationDescriptor Operation) selected = access.Catalog.Modules
            .SelectMany(module => module.Operations.Select(item => (Module: module, Operation: item)))
            .FirstOrDefault(item => string.Equals(item.Operation.Name, operation, StringComparison.Ordinal));
        if (selected.Operation is null)
        {
            return new(null, new OperationError("unknown_operation", Operation: operation,
                Suggestions: Suggest(operation, access.Catalog.Modules.SelectMany(item => item.Operations).Select(item => item.Name))));
        }

        (ModuleDescriptor module, OperationDescriptor descriptor) = selected;
        string? reason = availability.ReasonFor(descriptor.Kind);
        var arguments = new List<string>();
        if (module.FixedTenant is null)
        {
            arguments.Add("tenant");
        }

        arguments.Add("aggregateId");
        if (descriptor.Kind == OperationKind.Command)
        {
            arguments.AddRange(["correlationId", "idempotencyKey", "extensions"]);
        }
        else
        {
            arguments.AddRange(["entityId", "pageSize", "offset", "cursor"]);
        }

        var envelope = new OperationEnvelopeDocument(module.FixedTenant, descriptor.AggregateIdRequired,
            descriptor.IdempotencyKeyRequired, Array.AsReadOnly(arguments.ToArray()));
        var document = new OperationDescriptionDocument(descriptor.Name, PublicKind(descriptor.Kind), descriptor.Description,
            descriptor.SchemaDocument, descriptor.Example is null ? null : JsonNode.Parse(descriptor.Example), envelope,
            descriptor.LintFindings, reason is null, reason);
        return new(document, null);
    }

    private static OperationError AccessError(CatalogAccess access)
        => new(access.ErrorCode ?? "internal_error", Message: access.Message ?? "Catalog access failed.");

    private static string PublicKind(OperationKind kind) => kind == OperationKind.Command ? "write" : "read";

    private static IReadOnlyList<string> Suggest(string requested, IEnumerable<string> names)
        => Array.AsReadOnly(names
            .Select(name => (Name: name, Distance: Distance(requested, name)))
            .OrderBy(item => item.Distance)
            .ThenBy(item => item.Name, StringComparer.Ordinal)
            .Take(3)
            .Select(item => item.Name)
            .ToArray());

    private static int Distance(string left, string right)
    {
        left = left.ToUpperInvariant();
        right = right.ToUpperInvariant();
        var previous = new int[right.Length + 1];
        var current = new int[right.Length + 1];
        for (int column = 0; column <= right.Length; column++)
        {
            previous[column] = column;
        }

        for (int row = 1; row <= left.Length; row++)
        {
            current[0] = row;
            for (int column = 1; column <= right.Length; column++)
            {
                int cost = left[row - 1] == right[column - 1] ? 0 : 1;
                current[column] = Math.Min(Math.Min(previous[column] + 1, current[column - 1] + 1), previous[column - 1] + cost);
            }

            (previous, current) = (current, previous);
        }

        return previous[right.Length];
    }
}

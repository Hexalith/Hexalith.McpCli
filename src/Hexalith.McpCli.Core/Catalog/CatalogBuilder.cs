using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Schema;
using Hexalith.McpCli.Core.Serialization;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Builds one deterministic catalog from explicitly supplied Contracts assemblies.</summary>
public static class CatalogBuilder
{
    /// <summary>Discovers marked modules and valid decorated operations.</summary>
    /// <param name="assemblies">The assembly manifest; no other assemblies are scanned.</param>
    /// <returns>An immutable catalog and its declaration diagnostics.</returns>
    public static CatalogSnapshot Build(IReadOnlyList<Assembly> assemblies)
    {
        ArgumentNullException.ThrowIfNull(assemblies);
        if (assemblies.Any(assembly => assembly is null))
        {
            throw new ArgumentException("An assembly manifest cannot contain null entries.", nameof(assemblies));
        }

        var diagnostics = new List<CatalogDiagnostic>();
        var modules = new List<ModuleDescriptor>();
        var seenModules = new HashSet<string>(StringComparer.Ordinal);
        foreach (Assembly assembly in assemblies.Distinct().OrderBy(item => item.GetName().Name, StringComparer.Ordinal)
            .ThenBy(item => item.FullName, StringComparer.Ordinal)
            .ThenBy(item => item.ManifestModule.ModuleVersionId))
        {
            string assemblyName = assembly.GetName().Name ?? assembly.FullName ?? "<unknown>";
            HexalithModuleAttribute? marker = assembly.GetCustomAttribute<HexalithModuleAttribute>();
            if (marker is null)
            {
                continue;
            }

            string? markerProblem = DescribeMarkerProblem(marker);
            if (markerProblem is not null)
            {
                diagnostics.Add(Diagnostic(assemblyName, "invalid_module_declaration", markerProblem));
                continue;
            }

            if (marker.FixedTenant is not null && !RoutingResolver.IsTenantDomain(marker.FixedTenant))
            {
                diagnostics.Add(Diagnostic(assemblyName, "invalid_routing_value",
                    $"Module FixedTenant '{marker.FixedTenant}' must be 1 to 64 lowercase ASCII letters, digits, or hyphens, starting and ending with a letter or digit."));
                continue;
            }

            JsonSerializerOptions options;
            try
            {
                options = McpCliJson.ForModule(assembly, marker);
            }
            catch (ContractDeclarationException exception)
            {
                diagnostics.Add(Diagnostic(assemblyName, exception.Category, exception.Message));
                continue;
            }

            Type[] types;
            try
            {
                types = assembly.GetTypes();
            }
            catch (ReflectionTypeLoadException exception)
            {
                string cause = exception.LoaderExceptions.FirstOrDefault(item => item is not null)?.Message ?? exception.Message;
                diagnostics.Add(Diagnostic(assemblyName, "invalid_module_declaration",
                    $"The types of Contracts assembly {assemblyName} could not be loaded: {cause}"));
                continue;
            }

            if (!seenModules.Add(marker.Name))
            {
                diagnostics.Add(Diagnostic(assemblyName, "duplicate_module",
                    $"Module name {marker.Name} is already declared."));
                continue;
            }

            var operations = new List<OperationDescriptor>();
            var seenOperations = new HashSet<string>(StringComparer.Ordinal);
            foreach (Type type in types.OrderBy(item => item.FullName, StringComparer.Ordinal))
            {
                HexalithCommandAttribute? command = type.GetCustomAttribute<HexalithCommandAttribute>(false);
                HexalithQueryAttribute? query = type.GetCustomAttribute<HexalithQueryAttribute>(false);
                if (command is null && query is null)
                {
                    continue;
                }

                if (command is not null && query is not null)
                {
                    diagnostics.Add(Diagnostic(type.FullName, "conflicting_operation_kinds",
                        $"Type {type.Name} carries both HexalithCommand and HexalithQuery; keep exactly one."));
                    continue;
                }

                if (!type.IsClass || type.IsAbstract || type.ContainsGenericParameters)
                {
                    string shape = !type.IsClass ? "is not a class" : type.IsAbstract ? "is abstract" : "is an open generic type";
                    diagnostics.Add(Diagnostic(type.FullName, "invalid_operation_declaration",
                        $"Operation type {type.Name} {shape}; an operation must be a concrete, closed class."));
                    continue;
                }

                (OperationDescriptor Operation, IReadOnlyList<CatalogDiagnostic> Warnings) result;
                try
                {
                    result = BuildOperation(marker, options, type, command, query);
                }
                catch (ContractDeclarationException exception)
                {
                    diagnostics.Add(Diagnostic(type.FullName, exception.Category, exception.Message));
                    continue;
                }

                if (seenOperations.Add(result.Operation.Name))
                {
                    operations.Add(result.Operation);
                    diagnostics.AddRange(result.Warnings);
                }
                else
                {
                    diagnostics.Add(Diagnostic(type.FullName, "duplicate_operation_name",
                        $"Operation name {result.Operation.Name} is already declared by an earlier type."));
                }
            }

            OperationDescriptor[] valid = operations.OrderBy(item => item.Name, StringComparer.Ordinal).ToArray();
            if (valid.Length == 0)
            {
                diagnostics.Add(Diagnostic(assemblyName, "empty_module", $"Module {marker.Name} exposes no valid operations.", "warning"));
            }

            modules.Add(new ModuleDescriptor(marker.Name, marker.Description, marker.IdentifierKind, marker.FixedTenant,
                marker.WireTypeConvention, options, valid));
        }

        return new CatalogSnapshot(modules.OrderBy(item => item.Name, StringComparer.Ordinal).ToArray(),
            diagnostics.OrderBy(item => item.TypeName, StringComparer.Ordinal)
                .ThenBy(item => item.Category, StringComparer.Ordinal)
                .ThenBy(item => item.Severity, StringComparer.Ordinal)
                .ThenBy(item => item.Message, StringComparer.Ordinal).ToArray());
    }

    private static (OperationDescriptor Operation, IReadOnlyList<CatalogDiagnostic> Warnings) BuildOperation(
        HexalithModuleAttribute module, JsonSerializerOptions options, Type type, HexalithCommandAttribute? command,
        HexalithQueryAttribute? query)
    {
        OperationKind kind = command is null ? OperationKind.Query : OperationKind.Command;
        string attribute = command is null ? "HexalithQuery" : "HexalithCommand";
        string? explicitName = command?.Name ?? query?.Name;
        string derivedNameFailure = $"Operation type name {type.Name} does not yield a lowercase ASCII kebab-case name; set {attribute}.Name.";
        string part;
        if (explicitName is not null)
        {
            part = explicitName;
        }
        else
        {
            try
            {
                part = KebabCase.FromTypeName(type.Name);
            }
            catch (ArgumentException exception)
            {
                throw new ContractDeclarationException("invalid_operation_name", derivedNameFailure, exception);
            }
        }

        if (!IsCanonicalPart(part))
        {
            throw new ContractDeclarationException("invalid_operation_name", explicitName is null
                ? derivedNameFailure
                : $"{attribute}.Name '{explicitName}' must be lowercase ASCII kebab-case.");
        }

        if (string.IsNullOrWhiteSpace(command?.Description ?? query?.Description))
        {
            throw new ContractDeclarationException("missing_description", $"{attribute}.Description is empty or whitespace.");
        }

        string? aggregateProperty = command?.AggregateIdProperty ?? query?.AggregateIdProperty;
        string? aggregateConstant = query?.AggregateId;
        if (query is not null && aggregateProperty is not null && aggregateConstant is not null)
        {
            throw new ContractDeclarationException("ambiguous_aggregate_id",
                $"HexalithQuery sets both AggregateIdProperty '{aggregateProperty}' and AggregateId '{aggregateConstant}'; keep one.");
        }

        if (aggregateConstant is not null && !RoutingResolver.IsAggregateId(aggregateConstant))
        {
            throw new ContractDeclarationException("invalid_routing_value",
                $"HexalithQuery.AggregateId '{aggregateConstant}' must be 1 to 256 ASCII letters, digits, '.', '_', or '-', starting and ending with a letter or digit.");
        }

        RoutingResolution routing = RoutingResolver.Resolve(type, kind, module, part, command, query);
        var roleNames = new Dictionary<PropertyRole, string?>
        {
            [PropertyRole.AggregateId] = aggregateProperty,
            [PropertyRole.Tenant] = command?.TenantProperty ?? query?.TenantProperty,
            [PropertyRole.Correlation] = command?.CorrelationProperty,
            [PropertyRole.IdempotencyKey] = command?.IdempotencyKeyProperty,
            [PropertyRole.Actor] = command?.ActorProperty,
        };
        DerivedSchema schema = SchemaDeriver.Derive(type, options, module.IdentifierKind, kind == OperationKind.Command, roleNames);
        Func<JsonElement, string?>? accessor = AggregateIdAccessors.Create(type, options, schema.Bindings, kind);
        if (kind == OperationKind.Command && accessor is null)
        {
            throw new ContractDeclarationException("missing_routing_values",
                "The command has no aggregate identifier source; set HexalithCommand.AggregateIdProperty or implement ICommandContract.AggregateId.");
        }

        string? example = command?.Example ?? query?.Example;
        if (example is not null)
        {
            PayloadValidationResult validation = PayloadValidator.Validate(schema, example, kind == OperationKind.Command);
            if (!validation.IsValid)
            {
                // Report the most specific location, so the message names the failing member rather than only the root.
                PayloadViolation first = validation.Violations
                    .OrderByDescending(violation => violation.Path == "/" ? 0 : violation.Path.Count(character => character == '/'))
                    .ThenBy(violation => violation.Path, StringComparer.Ordinal)
                    .ThenBy(violation => violation.Message, StringComparer.Ordinal)
                    .First();
                throw new ContractDeclarationException("invalid_example",
                    $"{attribute}.Example violates the payload schema at {first.Path}: {first.Message}");
            }
        }

        bool idempotencyRequired = schema.Bindings.TryGetValue(PropertyRole.IdempotencyKey, out PropertyBinding? binding)
            && (binding.Metadata.IsRequired || !binding.Metadata.IsSetNullable);
        var operation = new OperationDescriptor(module.Name + "." + part, kind, command?.Description ?? query!.Description,
            example, schema, routing.Routing, accessor, aggregateConstant,
            kind == OperationKind.Query && accessor is null && aggregateConstant is null, idempotencyRequired, type);
        return (operation, routing.Warnings);
    }

    private static string? DescribeMarkerProblem(HexalithModuleAttribute marker)
    {
        if (!IsCanonicalPart(marker.Name))
        {
            return $"HexalithModule Name '{marker.Name}' must be lowercase ASCII kebab-case.";
        }

        if (string.IsNullOrWhiteSpace(marker.Description))
        {
            return "HexalithModule Description is empty or whitespace.";
        }

        if (marker.IdentifierKind is not (IdentifierKind.Ulid or IdentifierKind.String))
        {
            return $"HexalithModule IdentifierKind '{marker.IdentifierKind}' is not Ulid or String.";
        }

        return marker.WireTypeConvention is not (WireTypeConvention.Explicit or WireTypeConvention.FullTypeName or WireTypeConvention.KebabCase)
            ? $"HexalithModule WireTypeConvention '{marker.WireTypeConvention}' is not Explicit, FullTypeName, or KebabCase."
            : null;
    }

    private static CatalogDiagnostic Diagnostic(string? typeName, string category, string message, string severity = "error")
        => new(typeName ?? "<unknown>", category, severity, message);

    private static bool IsCanonicalPart(string? value) => value is { Length: > 0 }
        && value[0] is >= 'a' and <= 'z' or >= '0' and <= '9'
        && value[^1] is >= 'a' and <= 'z' or >= '0' and <= '9'
        && !value.Contains("--", StringComparison.Ordinal)
        && value.All(character => character is >= 'a' and <= 'z' or >= '0' and <= '9' or '-');

}

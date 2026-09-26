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

            if (!IsCanonicalPart(marker.Name) || string.IsNullOrWhiteSpace(marker.Description)
                || marker.IdentifierKind is not (IdentifierKind.Ulid or IdentifierKind.String)
                || marker.WireTypeConvention is not (WireTypeConvention.Explicit or WireTypeConvention.FullTypeName or WireTypeConvention.KebabCase))
            {
                diagnostics.Add(Diagnostic(assemblyName, "invalid_module_declaration", "The module marker has invalid values."));
                continue;
            }

            if (marker.FixedTenant is not null && !RoutingResolver.IsTenantDomain(marker.FixedTenant))
            {
                diagnostics.Add(Diagnostic(assemblyName, "invalid_routing_value", "The module fixed tenant is invalid."));
                continue;
            }

            JsonSerializerOptions options;
            try
            {
                options = McpCliJson.ForModule(assembly, marker);
            }
            catch (Exception exception) when (IsDeclarationFailure(exception))
            {
                diagnostics.Add(Diagnostic(assemblyName, "invalid_serializer_options_provider",
                    "The module serializer options provider could not be used."));
                continue;
            }

            Type[] types;
            try
            {
                types = assembly.GetTypes();
            }
            catch (ReflectionTypeLoadException)
            {
                diagnostics.Add(Diagnostic(assemblyName, "invalid_module_declaration",
                    "The Contracts assembly's types could not be loaded."));
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
                        "A contract cannot be both a command and a query."));
                    continue;
                }

                if (!type.IsClass || type.IsAbstract || type.ContainsGenericParameters)
                {
                    diagnostics.Add(Diagnostic(type.FullName, "invalid_operation_declaration",
                        "An operation must be a concrete, closed class."));
                    continue;
                }

                OperationDescriptor? operation = BuildOperation(marker, options, type, command, query, diagnostics);
                if (operation is not null)
                {
                    if (seenOperations.Add(operation.Name))
                    {
                        operations.Add(operation);
                    }
                    else
                    {
                        diagnostics.Add(Diagnostic(type.FullName, "duplicate_operation_name",
                            $"Operation name {operation.Name} is already declared."));
                    }
                }
            }

            OperationDescriptor[] valid = operations.OrderBy(item => item.Name, StringComparer.Ordinal).ToArray();
            if (valid.Length == 0)
            {
                diagnostics.Add(Diagnostic(assemblyName, "empty_module", "The module has no valid operations.", "warning"));
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

    private static OperationDescriptor? BuildOperation(HexalithModuleAttribute module, JsonSerializerOptions options,
        Type type, HexalithCommandAttribute? command, HexalithQueryAttribute? query, List<CatalogDiagnostic> diagnostics)
    {
        OperationKind kind = command is null ? OperationKind.Query : OperationKind.Command;
        string? explicitName = command?.Name ?? query?.Name;
        string part;
        try
        {
            part = explicitName ?? KebabCase.FromTypeName(type.Name);
        }
        catch (ArgumentException)
        {
            diagnostics.Add(Diagnostic(type.FullName, "invalid_operation_name",
                "The operation type name cannot be made canonical."));
            return null;
        }

        if (!IsCanonicalPart(part))
        {
            diagnostics.Add(Diagnostic(type.FullName, "invalid_operation_name",
                "The operation name must be lowercase ASCII kebab-case."));
            return null;
        }

        if (string.IsNullOrWhiteSpace(command?.Description ?? query?.Description))
        {
            diagnostics.Add(Diagnostic(type.FullName, "missing_description", "An operation description is required."));
            return null;
        }

        string? aggregateProperty = command?.AggregateIdProperty ?? query?.AggregateIdProperty;
        string? aggregateConstant = query?.AggregateId;
        if (aggregateProperty is not null && string.Equals(aggregateProperty,
            command?.TenantProperty ?? query?.TenantProperty, StringComparison.Ordinal))
        {
            diagnostics.Add(Diagnostic(type.FullName, "tenant_is_aggregate_id",
                "Tenant and aggregate identifier roles cannot share a payload member."));
            return null;
        }
        if (query is not null && aggregateProperty is not null && aggregateConstant is not null)
        {
            diagnostics.Add(Diagnostic(type.FullName, "ambiguous_aggregate_id",
                "A query cannot declare both an aggregate property and a constant."));
            return null;
        }

        if (aggregateConstant is not null && !RoutingResolver.IsAggregateId(aggregateConstant))
        {
            diagnostics.Add(Diagnostic(type.FullName, "invalid_routing_value",
                "The query aggregate identifier constant is invalid."));
            return null;
        }

        try
        {
            OperationRouting routing = RoutingResolver.Resolve(type, kind, module, part, command, query);
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
                diagnostics.Add(Diagnostic(type.FullName, "missing_routing_values",
                    "A command requires an aggregate identifier source."));
                return null;
            }

            string? example = command?.Example ?? query?.Example;
            if (example is not null && !PayloadValidator.Validate(schema, example, kind == OperationKind.Command).IsValid)
            {
                diagnostics.Add(Diagnostic(type.FullName, "invalid_example",
                    "The declared example does not validate against the payload schema."));
                return null;
            }

            bool idempotencyRequired = schema.Bindings.TryGetValue(PropertyRole.IdempotencyKey, out PropertyBinding? binding)
                && (binding.Metadata.IsRequired || !binding.Metadata.IsSetNullable);
            return new OperationDescriptor(module.Name + "." + part, kind, command?.Description ?? query!.Description,
                example, schema, routing, accessor, aggregateConstant, kind == OperationKind.Query && accessor is null && aggregateConstant is null,
                idempotencyRequired, type);
        }
        catch (Exception exception) when (IsDeclarationFailure(exception))
        {
            string code = Classify(exception);
            diagnostics.Add(Diagnostic(type.FullName, code, "The operation declaration could not be resolved."));
            return null;
        }
    }

    private static string Classify(Exception exception)
    {
        if (exception is ArgumentException argument && argument.Message.StartsWith("missing_routing_values", StringComparison.Ordinal))
        {
            return "missing_routing_values";
        }

        if (exception is ArgumentException routing && routing.Message.StartsWith("invalid_routing_value", StringComparison.Ordinal))
        {
            return "invalid_routing_value";
        }

        if (exception.Message.Contains("Two property roles", StringComparison.Ordinal))
        {
            return "conflicting_property_roles";
        }

        if (exception.Message.Contains("Property role", StringComparison.Ordinal)
            || exception.Message.Contains("property roles", StringComparison.Ordinal))
        {
            return "invalid_property_reference";
        }

        if (exception.Message.Contains("Declared identifier", StringComparison.Ordinal))
        {
            return "invalid_identifier_type";
        }

        return "invalid_schema";
    }

    private static CatalogDiagnostic Diagnostic(string? typeName, string category, string message, string severity = "error")
        => new(typeName ?? "<unknown>", category, severity, message);

    private static bool IsCanonicalPart(string? value) => value is { Length: > 0 }
        && value[0] is >= 'a' and <= 'z' or >= '0' and <= '9'
        && value[^1] is >= 'a' and <= 'z' or >= '0' and <= '9'
        && !value.Contains("--", StringComparison.Ordinal)
        && value.All(character => character is >= 'a' and <= 'z' or >= '0' and <= '9' or '-');

    private static bool IsDeclarationFailure(Exception exception)
        => exception is ArgumentException or InvalidOperationException or NotSupportedException or JsonException
            or TargetInvocationException or TypeInitializationException or TypeLoadException;
}

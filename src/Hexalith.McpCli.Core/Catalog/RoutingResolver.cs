using System.Reflection;
using System.Text.RegularExpressions;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Resolves contract interface and declaration routing at catalog construction.</summary>
internal static partial class RoutingResolver
{
    private const string DomainField = "Domain";
    private const string WireTypeField = "WireType";
    private const string ProjectionTypeField = "ProjectionType";
    private const string ProjectionActorTypeField = "ProjectionActorType";

    internal static RoutingResolution Resolve(Type type, OperationKind kind, HexalithModuleAttribute module,
        string namePart, HexalithCommandAttribute? command, HexalithQueryAttribute? query)
    {
        string? interfaceDomain = null;
        string? interfaceWireType = null;
        string? interfaceProjectionType = null;
        string contract = kind == OperationKind.Command ? nameof(ICommandContract) : nameof(IQueryContract);
        if (kind == OperationKind.Command && typeof(ICommandContract).IsAssignableFrom(type))
        {
            (interfaceDomain, interfaceWireType) = ReadCommand(type);
        }
        else if (kind == OperationKind.Query && typeof(IQueryContract).IsAssignableFrom(type))
        {
            (interfaceDomain, interfaceWireType, interfaceProjectionType) = ReadQuery(type);
        }

        string? conventionWireType = module.WireTypeConvention switch
        {
            WireTypeConvention.FullTypeName => type.FullName,
            WireTypeConvention.KebabCase => namePart,
            _ => null,
        };

        string typeName = type.FullName ?? "<unknown>";
        var warnings = new List<CatalogDiagnostic>();
        string? domain = ResolveField(DomainField, interfaceDomain,
            kind == OperationKind.Command ? command?.Domain : query?.Domain, null);
        string? wireType = ResolveField(WireTypeField, interfaceWireType,
            kind == OperationKind.Command ? command?.WireType : query?.WireType, conventionWireType);
        string? projectionType = kind == OperationKind.Query
            ? ResolveField(ProjectionTypeField, interfaceProjectionType, query?.ProjectionType, null)
            : null;
        string? projectionActorType = query?.ProjectionActorType;

        string[] missing = new[]
        {
            string.IsNullOrWhiteSpace(domain) ? DomainField : null,
            string.IsNullOrWhiteSpace(wireType) ? WireTypeField : null,
            kind == OperationKind.Query && string.IsNullOrWhiteSpace(projectionType) ? ProjectionTypeField : null,
        }.OfType<string>().ToArray();
        if (missing.Length > 0)
        {
            throw new ContractDeclarationException("missing_routing_values",
                $"No contract interface, attribute member, or Module convention supplies {string.Join(", ", missing)}.");
        }

        if (!IsTenantDomain(domain))
        {
            throw InvalidValue(DomainField, domain!, "must be 1 to 64 lowercase ASCII letters, digits, or hyphens, starting and ending with a letter or digit");
        }

        bool allowColon = kind == OperationKind.Command;
        if (!IsWireValue(wireType, allowColon))
        {
            throw InvalidValue(WireTypeField, wireType!, !allowColon && wireType!.Contains(':', StringComparison.Ordinal)
                ? "contains ':', which the Gateway reserves in a query wire type"
                : "must be at most 256 characters without '<', '>', '&', quotes, or script patterns");
        }

        if (projectionType is not null && !IsTenantDomain(projectionType))
        {
            throw InvalidValue(ProjectionTypeField, projectionType, "must be 1 to 64 lowercase ASCII letters, digits, or hyphens, starting and ending with a letter or digit");
        }

        if (projectionActorType is not null && !IsWireValue(projectionActorType, allowColon: false, 64))
        {
            throw InvalidValue(ProjectionActorTypeField, projectionActorType,
                "must be a nonblank value of at most 64 characters without ':', '<', '>', '&', quotes, or script patterns");
        }

        return new RoutingResolution(new OperationRouting(domain!, wireType!, projectionType, projectionActorType), warnings);

        // Interface wins, then attribute, then convention; an attribute beside a winning or equal source is reported.
        string? ResolveField(string name, string? interfaceValue, string? attributeValue, string? conventionValue)
        {
            if (interfaceValue is not null)
            {
                if (attributeValue is not null)
                {
                    warnings.Add(string.Equals(attributeValue, interfaceValue, StringComparison.Ordinal)
                        ? Warning("redundant_value", $"Attribute {name} '{attributeValue}' equals the {contract} value and is redundant.")
                        : Warning("conflicting_value",
                            $"Attribute {name} '{attributeValue}' differs from the {contract} value '{interfaceValue}'; the interface value is used."));
                }

                return interfaceValue;
            }

            if (attributeValue is not null)
            {
                if (string.Equals(attributeValue, conventionValue, StringComparison.Ordinal))
                {
                    warnings.Add(Warning("redundant_value",
                        $"Attribute {name} '{attributeValue}' equals the {module.WireTypeConvention} convention value and is redundant."));
                }

                return attributeValue;
            }

            return conventionValue;
        }

        CatalogDiagnostic Warning(string category, string message) => new(typeName, category, "warning", message);
    }

    internal static bool IsTenantDomain(string? value) => value is { Length: >= 1 and <= 64 }
        && IsAsciiLowerOrDigit(value[0])
        && IsAsciiLowerOrDigit(value[^1])
        && value.All(character => IsAsciiLowerOrDigit(character) || character == '-');

    internal static bool IsAggregateId(string? value) => value is { Length: >= 1 and <= 256 }
        && IsAsciiLetterOrDigit(value[0])
        && IsAsciiLetterOrDigit(value[^1])
        && value.All(character => IsAsciiLetterOrDigit(character) || character is '.' or '_' or '-');

    private static ContractDeclarationException InvalidValue(string field, string value, string rule)
        => new("invalid_routing_value", $"Routing value {field} '{value}' {rule}.");

    // Mirrors the pinned Gateway validators: only Query-side wire values reserve ':' as the actor ID separator.
    private static bool IsWireValue(string? value, bool allowColon, int maxLength = 256) => !string.IsNullOrWhiteSpace(value)
        && value.Length <= maxLength
        && (allowColon || !value.Contains(':'))
        && value.IndexOfAny(['<', '>', '&', '\'', '"']) < 0
        && !InjectionPattern().IsMatch(value);

    [GeneratedRegex(@"(?i)(javascript\s*:|on\w+\s*=|<\s*script)")]
    private static partial Regex InjectionPattern();

    private static bool IsAsciiLowerOrDigit(char value) => value is >= 'a' and <= 'z' or >= '0' and <= '9';

    private static bool IsAsciiLetterOrDigit(char value) => IsAsciiLowerOrDigit(value) || value is >= 'A' and <= 'Z';

    private static (string Domain, string WireType) ReadCommand(Type type)
        => ((string, string))Invoke(nameof(CommandValues), type, nameof(ICommandContract));

    private static (string Domain, string WireType, string ProjectionType) ReadQuery(Type type)
        => ((string, string, string))Invoke(nameof(QueryValues), type, nameof(IQueryContract));

    private static object Invoke(string methodName, Type type, string contract)
    {
        MethodInfo method = typeof(RoutingResolver).GetMethod(methodName, BindingFlags.NonPublic | BindingFlags.Static)!;
        try
        {
            return method.MakeGenericMethod(type).Invoke(null, null)!;
        }
        catch (TargetInvocationException exception) when (exception.InnerException is not null)
        {
            Exception cause = exception.InnerException is TypeInitializationException { InnerException: { } initializer }
                ? initializer
                : exception.InnerException;
            throw new ContractDeclarationException("invalid_routing_value",
                $"The {contract} static routing members of {type} threw {cause.GetType().Name}: {cause.Message}", cause);
        }
    }

    private static (string Domain, string WireType) CommandValues<T>() where T : ICommandContract
        => (T.Domain, T.CommandType);

    private static (string Domain, string WireType, string ProjectionType) QueryValues<T>() where T : IQueryContract
        => (T.Domain, T.QueryType, T.ProjectionType);
}

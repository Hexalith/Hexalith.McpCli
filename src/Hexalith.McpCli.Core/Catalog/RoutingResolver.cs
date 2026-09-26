using System.Reflection;
using System.Text.RegularExpressions;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Resolves contract interface and declaration routing at catalog construction.</summary>
internal static class RoutingResolver
{
    internal static OperationRouting Resolve(Type type, OperationKind kind, HexalithModuleAttribute module,
        string namePart, HexalithCommandAttribute? command, HexalithQueryAttribute? query)
    {
        string? domain = kind == OperationKind.Command ? command?.Domain : query?.Domain;
        string? wireType = kind == OperationKind.Command ? command?.WireType : query?.WireType;
        string? projectionType = query?.ProjectionType;
        if (kind == OperationKind.Command && typeof(ICommandContract).IsAssignableFrom(type))
        {
            (string interfaceDomain, string interfaceWireType) = ReadCommand(type);
            domain = interfaceDomain ?? domain;
            wireType = interfaceWireType ?? wireType;
        }
        else if (kind == OperationKind.Query && typeof(IQueryContract).IsAssignableFrom(type))
        {
            (string interfaceDomain, string interfaceWireType, string interfaceProjectionType) = ReadQuery(type);
            domain = interfaceDomain ?? domain;
            wireType = interfaceWireType ?? wireType;
            projectionType = interfaceProjectionType ?? projectionType;
        }

        wireType ??= module.WireTypeConvention switch
        {
            WireTypeConvention.FullTypeName => type.FullName,
            WireTypeConvention.KebabCase => namePart,
            _ => null,
        };

        if (string.IsNullOrWhiteSpace(domain) || string.IsNullOrWhiteSpace(wireType)
            || kind == OperationKind.Query && string.IsNullOrWhiteSpace(projectionType))
        {
            throw new ArgumentException("missing_routing_values");
        }

        if (!IsTenantDomain(domain) || !IsWireValue(wireType)
            || (kind == OperationKind.Query && projectionType is not null && !IsTenantDomain(projectionType))
            || (query?.ProjectionActorType is not null && !IsWireValue(query.ProjectionActorType, 64)))
        {
            throw new ArgumentException("invalid_routing_value");
        }

        return new OperationRouting(domain!, wireType!, projectionType, query?.ProjectionActorType);
    }

    internal static bool IsTenantDomain(string? value) => value is { Length: >= 1 and <= 64 }
        && IsAsciiLowerOrDigit(value[0])
        && IsAsciiLowerOrDigit(value[^1])
        && value.All(character => IsAsciiLowerOrDigit(character) || character == '-');

    internal static bool IsAggregateId(string? value) => value is { Length: >= 1 and <= 256 }
        && IsAsciiLetterOrDigit(value[0])
        && IsAsciiLetterOrDigit(value[^1])
        && value.All(character => IsAsciiLetterOrDigit(character) || character is '.' or '_' or '-');

    private static bool IsWireValue(string? value, int maxLength = 256) => !string.IsNullOrWhiteSpace(value)
        && value.Length <= maxLength
        && !value.Contains(':')
        && value.All(character => !char.IsControl(character) && character is not ('<' or '>' or '&' or '\'' or '"'))
        && !Regex.IsMatch(value, @"on\w+\s*=", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);

    private static bool IsAsciiLowerOrDigit(char value) => value is >= 'a' and <= 'z' or >= '0' and <= '9';

    private static bool IsAsciiLetterOrDigit(char value) => IsAsciiLowerOrDigit(value) || value is >= 'A' and <= 'Z';

    private static (string Domain, string WireType) ReadCommand(Type type)
        => ((string, string))Invoke(nameof(CommandValues), type);

    private static (string Domain, string WireType, string ProjectionType) ReadQuery(Type type)
        => ((string, string, string))Invoke(nameof(QueryValues), type);

    private static object Invoke(string methodName, Type type)
    {
        MethodInfo method = typeof(RoutingResolver).GetMethod(methodName, BindingFlags.NonPublic | BindingFlags.Static)!;
        try
        {
            return method.MakeGenericMethod(type).Invoke(null, null)!;
        }
        catch (TargetInvocationException exception) when (exception.InnerException is not null)
        {
            throw new ArgumentException("Contract interface routing could not be read.", exception.InnerException);
        }
    }

    private static (string Domain, string WireType) CommandValues<T>() where T : ICommandContract
        => (T.Domain, T.CommandType);

    private static (string Domain, string WireType, string ProjectionType) QueryValues<T>() where T : IQueryContract
        => (T.Domain, T.QueryType, T.ProjectionType);
}

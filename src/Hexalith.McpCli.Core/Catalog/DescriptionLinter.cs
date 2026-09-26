using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization.Metadata;
using System.Text.RegularExpressions;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Inspects the effective input schema for missing or misleading descriptions.</summary>
public static partial class DescriptionLinter
{
    /// <summary>Returns stable, immutable findings for a valid operation.</summary>
    /// <param name="contractType">The decorated payload type.</param>
    /// <param name="description">The declared operation description.</param>
    /// <param name="kind">Whether the operation is a command or query.</param>
    /// <param name="options">The module's canonical payload options.</param>
    /// <param name="schema">The validated exported schema and property bindings.</param>
    /// <returns>The sorted description findings.</returns>
    public static IReadOnlyList<LintFinding> Inspect(
        Type contractType,
        string description,
        OperationKind kind,
        JsonSerializerOptions options,
        DerivedSchema schema)
    {
        ArgumentNullException.ThrowIfNull(contractType);
        ArgumentNullException.ThrowIfNull(description);
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(schema);

        var findings = new List<LintFinding>();
        if (string.Equals(description.Trim(), HumanizeOperationName(contractType.Name), StringComparison.OrdinalIgnoreCase))
        {
            findings.Add(new LintFinding("hollow_description", "warning",
                $"Operation description only repeats the name of {contractType.Name}; explain what it does."));
        }

        JsonNode root = schema.Node;
        InspectNode(contractType, root, string.Empty, kind, options, schema.Bindings, findings);
        return Array.AsReadOnly(findings
            .OrderBy(finding => finding.Property ?? string.Empty, StringComparer.Ordinal)
            .ThenBy(finding => finding.Code, StringComparer.Ordinal)
            .ThenBy(finding => finding.Message, StringComparer.Ordinal)
            .ToArray());
    }

    private static void InspectNode(
        Type type,
        JsonNode? node,
        string pointer,
        OperationKind kind,
        JsonSerializerOptions options,
        IReadOnlyDictionary<PropertyRole, PropertyBinding> bindings,
        List<LintFinding> findings)
    {
        if (node is not JsonObject schemaNode)
        {
            return;
        }

        JsonTypeInfo typeInfo = options.GetTypeInfo(type);
        if (typeInfo.Kind == JsonTypeInfoKind.Enumerable && typeInfo.ElementType is { } elementType)
        {
            InspectNode(elementType, schemaNode["items"], pointer + "/items", kind, options, bindings, findings);
            return;
        }

        if (typeInfo.Kind == JsonTypeInfoKind.Dictionary && typeInfo.ElementType is { } valueType)
        {
            InspectNode(valueType, schemaNode["additionalProperties"], pointer + "/additionalProperties", kind, options, bindings, findings);
            return;
        }

        if (typeInfo.Kind != JsonTypeInfoKind.Object || schemaNode["properties"] is not JsonObject properties)
        {
            return;
        }

        foreach (JsonPropertyInfo metadata in typeInfo.Properties.OrderBy(property => property.Name, StringComparer.Ordinal))
        {
            if (!properties.TryGetPropertyValue(metadata.Name, out JsonNode? propertyNode) || propertyNode is null)
            {
                continue;
            }

            string propertyPointer = pointer + "/properties/" + Escape(metadata.Name);
            if (propertyNode is not JsonObject propertySchema
                || propertySchema["description"] is not JsonValue descriptionNode
                || !descriptionNode.TryGetValue<string>(out string? propertyDescription)
                || string.IsNullOrWhiteSpace(propertyDescription))
            {
                findings.Add(new LintFinding("missing_property_description", "warning",
                    $"Describe payload member {metadata.Name} so callers understand its meaning.", propertyPointer));
            }

            MemberInfo? member = metadata.AttributeProvider as MemberInfo;
            if (member is PropertyInfo or FieldInfo)
            {
                if (member.Name.EndsWith("Id", StringComparison.Ordinal)
                    && !(member is PropertyInfo property && Attribute.IsDefined(property, typeof(HexalithIdentifierAttribute), true))
                    && !(pointer.Length == 0
                        && bindings.TryGetValue(PropertyRole.AggregateId, out PropertyBinding? aggregate)
                        && ReferenceEquals(aggregate.Metadata, metadata)))
                {
                    string advice = member is FieldInfo
                        ? "Use a property marked with HexalithIdentifier when this is an identifier, or rename the field."
                        : "Mark it with HexalithIdentifier when it is an identifier, or rename the property.";
                    findings.Add(new LintFinding("unmarked_identifier_like_property", "warning",
                        $"Member {metadata.Name} looks like an identifier. {advice}", propertyPointer));
                }

                if (kind == OperationKind.Query && member.Name is "PageSize" or "Offset" or "Cursor")
                {
                    findings.Add(new LintFinding("payload_paging_member", "warning",
                        $"Move paging member {metadata.Name} to the query envelope argument.", propertyPointer));
                }
            }

            InspectNode(metadata.PropertyType, propertyNode, propertyPointer, kind, options, bindings, findings);
        }
    }

    private static string HumanizeOperationName(string name)
    {
        string stem = name.EndsWith("Command", StringComparison.Ordinal) ? name[..^"Command".Length]
            : name.EndsWith("Query", StringComparison.Ordinal) ? name[..^"Query".Length] : name;
        return PascalBoundary().Replace(stem, " ");
    }

    private static string Escape(string token) => token.Replace("~", "~0", StringComparison.Ordinal).Replace("/", "~1", StringComparison.Ordinal);

    [GeneratedRegex("(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", RegexOptions.CultureInvariant)]
    private static partial Regex PascalBoundary();
}

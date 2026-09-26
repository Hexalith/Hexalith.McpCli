using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization.Metadata;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>Inspects the effective input schema for missing or misleading descriptions.</summary>
public static class DescriptionLinter
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
        if (IsHollow(description, contractType.Name))
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

        JsonTypeInfo typeInfo = options.GetTypeInfo(Nullable.GetUnderlyingType(type) ?? type);
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
            MemberInfo? member = metadata.AttributeProvider as MemberInfo;
            if (propertyNode is not JsonObject propertySchema
                || propertySchema["description"] is not JsonValue descriptionNode
                || !descriptionNode.TryGetValue<string>(out string? propertyDescription)
                || string.IsNullOrWhiteSpace(propertyDescription))
            {
                findings.Add(new LintFinding("missing_property_description", "warning",
                    $"Describe payload member {member?.Name ?? metadata.Name} so callers understand its meaning.", propertyPointer));
            }

            if (member is PropertyInfo or FieldInfo)
            {
                // A root member bound to an envelope role, or the ICommandContract.AggregateId source, is not an unmarked identifier.
                bool declaredRoot = pointer.Length == 0
                    && (bindings.Values.Any(binding => ReferenceEquals(binding.Metadata, metadata))
                        || kind == OperationKind.Command
                            && !bindings.ContainsKey(PropertyRole.AggregateId)
                            && member.Name == nameof(ICommandContract.AggregateId)
                            && typeof(ICommandContract).IsAssignableFrom(type));
                if (member.Name.EndsWith("Id", StringComparison.Ordinal)
                    && !(member is PropertyInfo property && Attribute.IsDefined(property, typeof(HexalithIdentifierAttribute), true))
                    && !declaredRoot)
                {
                    string advice = member is FieldInfo
                        ? "Use a property marked with HexalithIdentifier when this is an identifier, or rename the field."
                        : "Mark it with HexalithIdentifier when it is an identifier, or rename the property.";
                    findings.Add(new LintFinding("unmarked_identifier_like_property", "warning",
                        $"Member {member.Name} looks like an identifier. {advice}", propertyPointer));
                }

                if (kind == OperationKind.Query && member.Name is "PageSize" or "Offset" or "Cursor")
                {
                    findings.Add(new LintFinding("payload_paging_member", "warning",
                        $"Move paging member {member.Name} to the query envelope argument.", propertyPointer));
                }
            }

            InspectNode(metadata.PropertyType, propertyNode, propertyPointer, kind, options, bindings, findings);
        }
    }

    // Letters and digits only, so spacing, punctuation, casing, and kebab-case variants of the name all count as hollow.
    private static bool IsHollow(string description, string name)
    {
        string stem = name.EndsWith("Command", StringComparison.Ordinal) ? name[..^"Command".Length]
            : name.EndsWith("Query", StringComparison.Ordinal) ? name[..^"Query".Length] : name;
        string text = LettersAndDigits(description);
        return string.Equals(text, LettersAndDigits(stem), StringComparison.OrdinalIgnoreCase)
            || string.Equals(text, LettersAndDigits(name), StringComparison.OrdinalIgnoreCase);
    }

    private static string LettersAndDigits(string value) => string.Concat(value.Where(char.IsLetterOrDigit));

    private static string Escape(string token) => token.Replace("~", "~0", StringComparison.Ordinal).Replace("/", "~1", StringComparison.Ordinal);
}

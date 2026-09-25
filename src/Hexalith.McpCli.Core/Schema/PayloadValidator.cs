using System.Text.Json;
using Json.Schema;

namespace Hexalith.McpCli.Core.Schema;

/// <summary>Validates examples and payload JSON using a previously derived schema.</summary>
public static class PayloadValidator
{
    private static readonly JsonDocumentOptions ParseOptions = new() { AllowDuplicateProperties = false };

    /// <summary>Validates JSON text and reports every evaluator violation location.</summary>
    /// <param name="schema">The stored operation schema.</param>
    /// <param name="json">The example or caller payload JSON.</param>
    /// <param name="isCommand">Whether the operation requires an object root.</param>
    /// <returns>All schema violations, or an empty result when valid.</returns>
    public static PayloadValidationResult Validate(DerivedSchema schema, string json, bool isCommand)
    {
        ArgumentNullException.ThrowIfNull(schema);
        ArgumentNullException.ThrowIfNull(json);
        JsonDocument document;
        try
        {
            document = JsonDocument.Parse(json, ParseOptions);
        }
        catch (Exception exception) when (exception is JsonException or ArgumentException)
        {
            // Invalid UTF-16 such as a lone surrogate cannot be transcoded and surfaces as ArgumentException.
            return new PayloadValidationResult([new PayloadViolation("/", exception.Message)]);
        }

        using (document)
        {
            return Validate(schema, document.RootElement, isCommand);
        }
    }

    /// <summary>Validates an already parsed JSON payload with the stored schema.</summary>
    /// <param name="schema">The stored operation schema.</param>
    /// <param name="payload">The payload value.</param>
    /// <param name="isCommand">Whether the operation requires an object root.</param>
    /// <returns>All schema violations, or an empty result when valid.</returns>
    public static PayloadValidationResult Validate(DerivedSchema schema, JsonElement payload, bool isCommand)
    {
        ArgumentNullException.ThrowIfNull(schema);
        if (payload.ValueKind == JsonValueKind.Undefined)
        {
            return new PayloadValidationResult([new PayloadViolation("/", "A JSON payload is required.")]);
        }

        if (isCommand && payload.ValueKind != JsonValueKind.Object)
        {
            return new PayloadValidationResult([new PayloadViolation("/", "A Command payload must be a JSON object.")]);
        }

        var duplicates = new List<PayloadViolation>();
        CollectDuplicates(payload, string.Empty, duplicates);
        if (duplicates.Count > 0)
        {
            return new PayloadValidationResult(duplicates);
        }

        EvaluationResults results = schema.Validator.Evaluate(payload, new EvaluationOptions { OutputFormat = OutputFormat.List });
        if (results.IsValid)
        {
            return new PayloadValidationResult([]);
        }

        var violations = new List<PayloadViolation>();
        Collect(results, violations);
        return new PayloadValidationResult(violations);
    }

    private static void CollectDuplicates(JsonElement element, string pointer, List<PayloadViolation> violations)
    {
        if (element.ValueKind == JsonValueKind.Object)
        {
            var names = new HashSet<string>(StringComparer.Ordinal);
            foreach (JsonProperty property in element.EnumerateObject())
            {
                string child = pointer + "/" + property.Name.Replace("~", "~0", StringComparison.Ordinal).Replace("/", "~1", StringComparison.Ordinal);
                if (!names.Add(property.Name))
                {
                    violations.Add(new PayloadViolation("/", $"Duplicate JSON property name at {child}."));
                    continue;
                }

                CollectDuplicates(property.Value, child, violations);
            }
        }
        else if (element.ValueKind == JsonValueKind.Array)
        {
            int index = 0;
            foreach (JsonElement item in element.EnumerateArray())
            {
                CollectDuplicates(item, pointer + "/" + index.ToString(System.Globalization.CultureInfo.InvariantCulture), violations);
                index++;
            }
        }
    }

    private static void Collect(EvaluationResults result, List<PayloadViolation> violations)
    {
        if (result.Errors is not null)
        {
            string path = result.InstanceLocation.ToString();
            foreach (KeyValuePair<string, string> error in result.Errors)
            {
                violations.Add(new PayloadViolation(path.Length == 0 ? "/" : path, error.Value));
            }
        }

        foreach (EvaluationResults detail in result.Details ?? [])
        {
            Collect(detail, violations);
        }
    }
}

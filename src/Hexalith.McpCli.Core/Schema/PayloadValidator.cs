using System.Text.Json;
using Json.Schema;

namespace Hexalith.McpCli.Core.Schema;

/// <summary>Validates examples and payload JSON using a previously derived schema.</summary>
public static class PayloadValidator
{
    /// <summary>Validates JSON text and reports every evaluator violation location.</summary>
    /// <param name="schema">The stored operation schema.</param>
    /// <param name="json">The example or caller payload JSON.</param>
    /// <param name="isCommand">Whether the operation requires an object root.</param>
    /// <returns>All schema violations, or an empty result when valid.</returns>
    public static PayloadValidationResult Validate(DerivedSchema schema, string json, bool isCommand)
    {
        ArgumentNullException.ThrowIfNull(schema);
        ArgumentNullException.ThrowIfNull(json);
        try
        {
            using JsonDocument document = JsonDocument.Parse(json);
            return Validate(schema, document.RootElement, isCommand);
        }
        catch (JsonException exception)
        {
            return new PayloadValidationResult([new PayloadViolation("/", exception.Message)]);
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

        EvaluationResults results = schema.Validator.Evaluate(payload, new EvaluationOptions { OutputFormat = OutputFormat.List });
        if (results.IsValid)
        {
            return new PayloadValidationResult([]);
        }

        var violations = new List<PayloadViolation>();
        Collect(results, violations);
        return new PayloadValidationResult(violations);
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

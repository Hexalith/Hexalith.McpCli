using System.Text.Json.Serialization;
using ByteAether.Ulid;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Execution;

/// <summary>The shared public error document returned by either head.</summary>
/// <param name="Code">The stable error code.</param>
/// <param name="Message">An explanation for a configuration or catalog error.</param>
/// <param name="Operation">The requested operation for an operation lookup or validation failure.</param>
/// <param name="Module">The requested module for a module lookup failure.</param>
/// <param name="Suggestions">Up to three nearest canonical names for a lookup failure.</param>
/// <param name="Violations">The validation violations.</param>
/// <param name="Status">The unclassified gateway HTTP status.</param>
/// <param name="Detail">The gateway error detail.</param>
/// <param name="Reason">The gateway reason code when supplied.</param>
/// <param name="Retryable">The gateway retry hint when supplied.</param>
/// <param name="ClientAction">The gateway remediation hint when supplied.</param>
/// <param name="RetryAfter">The gateway retry delay when supplied.</param>
/// <param name="CorrelationId">The gateway correlation identifier when supplied.</param>
/// <param name="Argument">The invalid CLI argument for a binding failure.</param>
public sealed record OperationError(
    string Code,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Message = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Operation = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Module = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] IReadOnlyList<string>? Suggestions = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] IReadOnlyList<PayloadViolation>? Violations = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] int? Status = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Detail = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Reason = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] bool? Retryable = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? ClientAction = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? RetryAfter = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? CorrelationId = null,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Argument = null)
{
    /// <summary>Copies a gateway failure without reclassifying its status or inventing metadata.</summary>
    /// <param name="exception">The gateway client failure.</param>
    /// <returns>The shared public gateway error.</returns>
    public static OperationError FromGateway(EventStoreGatewayException exception)
    {
        ArgumentNullException.ThrowIfNull(exception);
        return new OperationError(
            "gateway_error",
            Status: exception.StatusCode,
            Detail: FirstNonEmpty(exception.Detail, exception.Title) ?? "Gateway request failed.",
            Reason: FirstNonEmpty(exception.ReasonCode, exception.Code, exception.Reason),
            Retryable: exception.Retryable,
            ClientAction: FirstNonEmpty(exception.ClientAction),
            RetryAfter: FirstNonEmpty(exception.RetryAfter),
            CorrelationId: ValidCorrelationId(exception.CorrelationId));
    }

    private static string? ValidCorrelationId(string? value)
        => value is not null && Ulid.TryParse(value, provider: null, out Ulid parsed)
            && string.Equals(value, parsed.ToString(), StringComparison.Ordinal) ? value : null;

    private static string? FirstNonEmpty(params string?[] values)
        => values.FirstOrDefault(value => !string.IsNullOrWhiteSpace(value));
}

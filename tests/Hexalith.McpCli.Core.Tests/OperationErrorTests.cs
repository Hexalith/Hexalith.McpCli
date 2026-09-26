using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks the shared Gateway error mapping.</summary>
public sealed class OperationErrorTests
{
    /// <summary>Copies complete Gateway metadata without status or reason reclassification.</summary>
    [Fact]
    public void MapsCompleteGatewayError()
    {
        var exception = new EventStoreGatewayException(202, "Title", detail: "Detail", correlationId: "01J9MZHXT3RKM0VWXRXGSJDATK",
            reason: "legacy", retryAfter: "30", reasonCode: "stable", code: "fallback", retryable: false, clientAction: "inspect");

        OperationError error = OperationError.FromGateway(exception);
        JsonElement json = JsonSerializer.SerializeToElement(error, McpCliJson.Result);

        error.Code.ShouldBe("gateway_error");
        error.Status.ShouldBe(202);
        error.Detail.ShouldBe("Detail");
        error.Reason.ShouldBe("stable");
        error.Retryable.ShouldBe(false);
        error.ClientAction.ShouldBe("inspect");
        error.RetryAfter.ShouldBe("30");
        json.TryGetProperty("operation", out _).ShouldBeFalse();
        json.TryGetProperty("message", out _).ShouldBeFalse();
    }

    /// <summary>Omitted Gateway metadata stays omitted from the public document.</summary>
    [Fact]
    public void OmitsUnavailableGatewayMetadata()
    {
        var exception = new EventStoreGatewayException(409, "Conflict", reason: "legacy");

        JsonElement json = JsonSerializer.SerializeToElement(OperationError.FromGateway(exception), McpCliJson.Result);

        json.GetProperty("detail").GetString().ShouldBe("Conflict");
        json.GetProperty("reason").GetString().ShouldBe("legacy");
        json.TryGetProperty("retryable", out _).ShouldBeFalse();
        json.TryGetProperty("clientAction", out _).ShouldBeFalse();
        json.TryGetProperty("retryAfter", out _).ShouldBeFalse();
        json.TryGetProperty("correlationId", out _).ShouldBeFalse();
    }
}

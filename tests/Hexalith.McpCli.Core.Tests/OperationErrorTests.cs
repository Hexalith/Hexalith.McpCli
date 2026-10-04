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
        json.GetProperty("correlationId").GetString().ShouldBe("01J9MZHXT3RKM0VWXRXGSJDATK");
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

    /// <summary>A supplied lowercase ULID is valid Gateway metadata and retains its original text.</summary>
    [Fact]
    public void RetainsValidLowercaseGatewayCorrelationId()
    {
        const string supplied = "01j9mzhxt3rkm0vwxrxgsjdatk";
        var exception = new EventStoreGatewayException(409, "Conflict", correlationId: supplied);

        JsonElement json = JsonSerializer.SerializeToElement(OperationError.FromGateway(exception), McpCliJson.Result);

        json.GetProperty("correlationId").GetString().ShouldBe(supplied);
    }

    /// <summary>Blank fields use the specified precedence and invalid correlation text is omitted.</summary>
    [Theory]
    [InlineData(" ", "Title", " ", "code", "reason", "Title", "code")]
    [InlineData("Detail", "Title", "stable", "code", "reason", "Detail", "stable")]
    [InlineData(" ", " ", " ", " ", "reason", "Gateway request failed.", "reason")]
    [InlineData(" ", " ", " ", " ", " ", "Gateway request failed.", null)]
    public void BlankValuesUseStableFallbacks(string detail, string title, string reasonCode, string code,
        string reason, string expectedDetail, string? expectedReason)
    {
        var exception = new EventStoreGatewayException(200, title, detail: detail, reasonCode: reasonCode,
            code: code, reason: reason, correlationId: "bad-id", clientAction: " ", retryAfter: " ", retryable: true);
        JsonElement error = JsonSerializer.SerializeToElement(OperationError.FromGateway(exception), McpCliJson.Result);
        error.GetProperty("status").GetInt32().ShouldBe(200);
        error.GetProperty("detail").GetString().ShouldBe(expectedDetail);
        error.GetProperty("retryable").GetBoolean().ShouldBeTrue();
        if (expectedReason is null)
        {
            error.TryGetProperty("reason", out _).ShouldBeFalse();
        }
        else
        {
            error.GetProperty("reason").GetString().ShouldBe(expectedReason);
        }

        error.TryGetProperty("correlationId", out _).ShouldBeFalse();
        error.TryGetProperty("clientAction", out _).ShouldBeFalse();
        error.TryGetProperty("retryAfter", out _).ShouldBeFalse();
    }
}

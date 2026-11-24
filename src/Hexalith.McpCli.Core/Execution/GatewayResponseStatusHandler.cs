using System.Runtime.CompilerServices;
using Hexalith.EventStore.Client.Gateway;

namespace Hexalith.McpCli.Core.Execution;

/// <summary>Preserves the HTTP status for Gateway responses the SDK decodes successfully.</summary>
internal sealed class GatewayResponseStatusHandler : DelegatingHandler
{
    private static readonly AsyncLocal<StrongBox<int?>?> CurrentCapture = new();

    internal static async Task<(T Response, int? Status)> CaptureAsync<T>(Func<Task<T>> submit)
    {
        StrongBox<int?>? previous = CurrentCapture.Value;
        var capture = new StrongBox<int?>();
        CurrentCapture.Value = capture;
        try
        {
            T response = await submit().ConfigureAwait(false);
            return (response, capture.Value);
        }
        catch (InvalidOperationException exception) when (exception.InnerException is ArgumentException
            && capture.Value is >= 200 and <= 299)
        {
            // HttpContentJsonExtensions wraps an unrecognized response charset in InvalidOperationException.
            throw new EventStoreGatewayException(capture.Value.Value, "Invalid Gateway response",
                detail: "The Gateway response charset is invalid.", innerException: exception);
        }
        finally
        {
            CurrentCapture.Value = previous;
        }
    }

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, CancellationToken cancellationToken)
    {
        HttpResponseMessage response = await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
        if (CurrentCapture.Value is { } capture)
        {
            capture.Value = (int)response.StatusCode;
        }

        return response;
    }
}

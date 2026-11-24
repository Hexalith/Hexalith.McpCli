using System.Runtime.CompilerServices;

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

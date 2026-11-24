using System.Diagnostics;
using System.Text.Json;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Discovers the exact Dapr sidecars registered inside the test-owned private runtime.</summary>
internal static class GatewaySidecarEndpoint
{
    /// <summary>Reads bounded Dapr process discovery after the fixture has started its isolated topology.</summary>
    internal static async Task<Uri[]> DiscoverAsync(string[] appIds, CancellationToken cancellationToken)
    {
        // The fixture enforces isolation before starting resources or allowing this discovery.
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(10));
        var start = new ProcessStartInfo("dapr") { RedirectStandardOutput = true, RedirectStandardError = true };
        foreach (string argument in new[] { "list", "--output", "json" }) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start)
            ?? throw new InvalidOperationException("Cannot start isolated sidecar discovery.");
        Task<string> output = process.StandardOutput.ReadToEndAsync(deadline.Token);
        Task<string> error = process.StandardError.ReadToEndAsync(deadline.Token);
        try { await process.WaitForExitAsync(deadline.Token); }
        finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
        _ = await error;
        if (process.ExitCode != 0)
            throw new InvalidOperationException("Cannot discover isolated Dapr sidecar endpoints.");
        return FromSnapshot(await output.ConfigureAwait(false), appIds);
    }

    /// <summary>Selects the Gateway registration in shared boundary tests.</summary>
    internal static Uri FromSnapshot(string snapshot)
    {
        try
        {
            return FromSnapshot(snapshot, ["eventstore"])[0];
        }
        catch (InvalidDataException exception)
        {
            throw new InvalidDataException("Expected exactly one Gateway sidecar with a valid HTTP port.", exception);
        }
    }

    /// <summary>Selects the actual HTTP port for each requested registration in request order.</summary>
    internal static Uri[] FromSnapshot(string snapshot, string[] appIds)
    {
        using JsonDocument document = JsonDocument.Parse(snapshot);
        if (document.RootElement.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("Expected a list of isolated Dapr sidecar registrations.");

        var endpoints = new List<Uri>(appIds.Length);
        foreach (string appId in appIds)
        {
            JsonElement[] matches = document.RootElement.EnumerateArray().Where(value => value.ValueKind == JsonValueKind.Object
                && value.TryGetProperty("appId", out JsonElement app) && app.ValueKind == JsonValueKind.String
                && app.GetString() == appId).ToArray();
            if (matches.Length != 1 || !matches[0].TryGetProperty("httpPort", out JsonElement port)
                || port.ValueKind != JsonValueKind.Number || !port.TryGetInt32(out int number) || number is < 1 or > 65535)
                throw new InvalidDataException($"Expected exactly one {appId} sidecar with a valid HTTP port.");
            endpoints.Add(new UriBuilder("http", "127.0.0.1", number).Uri);
        }

        if (endpoints.Select(endpoint => endpoint.Port).Distinct().Count() != endpoints.Count)
            throw new InvalidDataException("Isolated Dapr sidecars must have distinct HTTP ports.");

        return endpoints.ToArray();
    }
}

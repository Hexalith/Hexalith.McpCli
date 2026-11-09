using System.Diagnostics;
using System.Text.Json;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Discovers the exact Gateway sidecar registered inside the test-owned private runtime.</summary>
internal static class GatewaySidecarEndpoint
{
    /// <summary>Reads bounded Dapr process discovery after the fixture has started its isolated topology.</summary>
    internal static async Task<Uri> DiscoverAsync(CancellationToken cancellationToken)
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
            throw new InvalidOperationException("Cannot discover the isolated Gateway sidecar endpoint.");
        return FromSnapshot(await output);
    }

    /// <summary>Selects one exact application registration and its actual HTTP port, with no fixed-port fallback.</summary>
    internal static Uri FromSnapshot(string snapshot)
    {
        using JsonDocument document = JsonDocument.Parse(snapshot);
        if (document.RootElement.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException("Expected exactly one Gateway sidecar with a valid HTTP port.");
        JsonElement[] matches = document.RootElement.EnumerateArray().Where(value => value.ValueKind == JsonValueKind.Object
            && value.TryGetProperty("appId", out JsonElement app) && app.ValueKind == JsonValueKind.String
            && app.GetString() == "eventstore").ToArray();
        if (matches.Length != 1 || !matches[0].TryGetProperty("httpPort", out JsonElement port)
            || port.ValueKind != JsonValueKind.Number || !port.TryGetInt32(out int number) || number is < 1 or > 65535)
            throw new InvalidDataException("Expected exactly one Gateway sidecar with a valid HTTP port.");
        return new UriBuilder("http", "127.0.0.1", number).Uri;
    }
}

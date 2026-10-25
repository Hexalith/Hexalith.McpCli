using System.Net;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text.Json;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Activates the existing platform writer protocol only for a proven fresh private store.</summary>
internal static class ProjectionWriterBootstrap
{
    /// <summary>Verifies the wrapper's immutable provider-native backup before authorizing any maintenance call.</summary>
    internal static string VerifyBackup(string receiptPath)
    {
        using JsonDocument proof = JsonDocument.Parse(File.ReadAllText(receiptPath), new JsonDocumentOptions { AllowDuplicateProperties = false });
        JsonElement root = proof.RootElement;
        if (root.GetProperty("databaseSize").GetInt32() != 0 || !root.GetProperty("createdBeforeApplications").GetBoolean())
            throw new InvalidOperationException("Writer bootstrap requires the wrapper's empty pre-application Redis backup.");
        string backup = root.GetProperty("backupFile").GetString()!;
        byte[] bytes = File.ReadAllBytes(backup);
        string hash = Convert.ToHexStringLower(SHA256.HashData(bytes));
        if (!bytes.AsSpan().StartsWith("REDIS"u8) || root.GetProperty("sha256").GetString() != hash
            || Path.GetDirectoryName(Path.GetFullPath(backup)) != Path.GetDirectoryName(Path.GetFullPath(receiptPath)))
            throw new InvalidOperationException("Writer bootstrap backup bytes or location do not match the private receipt.");
        return $"sha256:{hash};file:{Path.GetFullPath(backup)}";
    }

    /// <summary>Uses one authenticated maintenance activation, then only bounded readiness observations.</summary>
    internal static async Task ActivateAsync(HttpClient http, string receiptPath, string sourceCommit, CancellationToken cancellationToken)
    {
        if (Environment.GetEnvironmentVariable("MCPCLI_ISOLATED_TOPOLOGY") != "1")
            throw new InvalidOperationException("Writer bootstrap requires the isolated topology wrapper.");
        if (sourceCommit.Length != 40 || sourceCommit.Any(character => !char.IsAsciiHexDigitLower(character)))
            throw new InvalidOperationException("Writer bootstrap requires the exact EventStore source commit.");
        string output = Environment.GetEnvironmentVariable("MCPCLI_LIVE_OUTPUT")
            ?? throw new InvalidOperationException("MCPCLI_LIVE_OUTPUT must name the selected case evidence directory.");
        string backupReference = VerifyBackup(receiptPath);
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(30));
        // The wrapper proves a new empty store and excludes all old writers in private namespaces.
        // The fixture has completed bootstrap reads; no vector or named delivery has been submitted.
        using HttpResponseMessage response = await http.PostAsJsonAsync("api/v1/admin/projections/delivery-writer-protocol/activate",
            new { cutoverCommit = sourceCommit, backupReference, writersQuiesced = true, retryWorkersQuiesced = true,
                downgradeProhibitedAcknowledged = true }, deadline.Token).ConfigureAwait(false);
        if (response.StatusCode != HttpStatusCode.OK)
            throw new InvalidOperationException($"Private projection writer activation failed with HTTP {(int)response.StatusCode}.");
        using JsonDocument result = JsonDocument.Parse(await response.Content.ReadAsStringAsync(deadline.Token).ConfigureAwait(false));
        if (result.RootElement.GetProperty("status").GetString() != "Activated")
            throw new InvalidOperationException("Private projection writer activation returned no Activated receipt.");
        while (true)
        {
            using HttpResponseMessage ready = await http.GetAsync("ready", deadline.Token).ConfigureAwait(false);
            if (ready.StatusCode == HttpStatusCode.OK) break;
            await Task.Delay(TimeSpan.FromMilliseconds(250), deadline.Token).ConfigureAwait(false);
        }
        Directory.CreateDirectory(output);
        await File.WriteAllTextAsync(Path.Combine(output, "writer-bootstrap.json"),
            JsonSerializer.Serialize(new { result = "passed", sourceCommit, backupReference, activationCount = 1, readinessObserved = true }),
            cancellationToken).ConfigureAwait(false);
    }
}

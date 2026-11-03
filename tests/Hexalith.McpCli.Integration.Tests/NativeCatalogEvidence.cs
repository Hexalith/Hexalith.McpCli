using System.Text.Json;

using Hexalith.EventStore.Contracts.Routing;
using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Requires every actual SDK participant to read back the same persisted committed authority.</summary>
internal static class NativeCatalogEvidence
{
    /// <summary>Reads private coordination only after SDK hosts activate; emits only credential-free evidence.</summary>
    internal static async Task RequireAsync(CancellationToken cancellationToken)
    {
        string backup = Environment.GetEnvironmentVariable("MCPCLI_ISOLATED_REDIS_BACKUP_RECEIPT")
            ?? throw new InvalidOperationException("Native catalog evidence requires the isolated genesis backup.");
        await RequireAsync(backup, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>Validates the actual SDK readbacks associated with one verified wrapper-owned backup.</summary>
    internal static async Task RequireAsync(string backup, CancellationToken cancellationToken)
    {
        string backupReference = TopologyConfiguration.VerifyFreshBackup(backup);
        string run = Path.GetDirectoryName(backup)!;
        File.Delete(Path.Combine(run, "native-catalog.json"));
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromSeconds(60));
        string coordinatesPath = Path.Combine(run, "native-catalog-coordinates.json");
        while (!File.Exists(coordinatesPath)) await Task.Delay(100, deadline.Token).ConfigureAwait(false);
        using JsonDocument coordinates = JsonDocument.Parse(await File.ReadAllBytesAsync(coordinatesPath, deadline.Token).ConfigureAwait(false));
        string directory = coordinates.RootElement.GetProperty("directory").GetString()!;
        string root = coordinates.RootElement.GetProperty("rootDigest").GetString()!;
        string[] hosts = coordinates.RootElement.GetProperty("hosts").EnumerateArray().Select(value => value.GetString()!).ToArray();
        if (!hosts.SequenceEqual(new[] { "eventstore", "parties", "tenants" }, StringComparer.Ordinal))
            throw new InvalidDataException("The native catalog participant inventory is incomplete.");
        var readbacks = new List<RouteCatalogGenerationReadback>();
        foreach (string host in hosts)
        {
            string path = Path.Combine(directory, host + ".committed.json");
            while (!File.Exists(path)) await Task.Delay(100, deadline.Token).ConfigureAwait(false);
            RouteCatalogGenerationReadback actual = JsonSerializer.Deserialize<RouteCatalogGenerationReadback>(
                await File.ReadAllBytesAsync(path, deadline.Token).ConfigureAwait(false))
                ?? throw new InvalidDataException("An SDK participant omitted its persisted readback.");
            if (!actual.Serving || actual.RootDigest != root || actual.Generation != 1 || actual.Profile != "Development"
                || string.IsNullOrWhiteSpace(actual.AttemptId) || string.IsNullOrWhiteSpace(actual.ActivationBindingDigest)
                || !actual.RequiredHosts.OrderBy(peer => peer.HostId, StringComparer.Ordinal).Select(peer => peer.HostId).SequenceEqual(hosts, StringComparer.Ordinal)
                || actual.RequiredHosts.Any(peer => peer.AppId != peer.HostId
                    || peer.HostId != "eventstore" && string.IsNullOrWhiteSpace(peer.ExecutableDigest)
                    || string.IsNullOrWhiteSpace(peer.AuthenticationFingerprint) || string.IsNullOrWhiteSpace(peer.TopologyDigest)))
                throw new InvalidDataException("An SDK participant did not read back the complete actual native cohort.");
            if (readbacks.Count > 0 && JsonSerializer.Serialize(actual) != JsonSerializer.Serialize(readbacks[0]))
                throw new InvalidDataException("Native participants disagree on their actual persisted activation readbacks.");
            readbacks.Add(actual);
        }
        await File.WriteAllTextAsync(Path.Combine(run, "native-catalog.json"), JsonSerializer.Serialize(new
        {
            result = "passed", backupReference, sdkVersion = "4.0.4", rootDigest = root,
            hosts, inputs = coordinates.RootElement.GetProperty("inputs").Clone(), readback = readbacks[0], eventStoreSourceCommit = Environment.GetEnvironmentVariable("MCPCLI_EVENTSTORE_PACKAGE_SOURCE_COMMIT"),
        }), deadline.Token).ConfigureAwait(false);
    }
}

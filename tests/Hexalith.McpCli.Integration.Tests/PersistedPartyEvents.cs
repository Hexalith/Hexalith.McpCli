using System.Text.Json;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Reads persisted actor event envelopes in the private Gateway store independently of projections.</summary>
internal static class PersistedPartyEvents
{
    /// <summary>Requires exactly one durable deactivation event and returns its sequence.</summary>
    internal static async Task<long> RequireOneDeactivationAsync(string tenant, string party, CancellationToken cancellationToken)
    {
        IReadOnlyList<(long Sequence, string Type)> events = await ReadAsync(tenant, party, cancellationToken);
        Assert.NotEmpty(events);
        return Assert.Single(events, item => item.Type.EndsWith("PartyDeactivated", StringComparison.Ordinal)).Sequence;
    }

    /// <summary>Refuses any creation effect; a rejection-only stream is not an existing business party (ledger item 556).</summary>
    internal static async Task RequireNoPartyCreatedAsync(string tenant, string party, CancellationToken cancellationToken)
    {
        IReadOnlyList<(long Sequence, string Type)> events = await ReadAsync(tenant, party, cancellationToken);
        Assert.DoesNotContain(events, item => item.Type.EndsWith("PartyCreated", StringComparison.Ordinal));
        Assert.DoesNotContain(events, item => item.Type.EndsWith("PartyDeactivated", StringComparison.Ordinal));
    }

    private static async Task<IReadOnlyList<(long Sequence, string Type)>> ReadAsync(string tenant, string party, CancellationToken cancellationToken)
    {
        using var http = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:3501/"), Timeout = TimeSpan.FromSeconds(15) };
        // APP_API_TOKEN protects sidecar-to-app calls. Preserve the separate sidecar API credential if configured.
        string? sidecarToken = Environment.GetEnvironmentVariable("DAPR_API_TOKEN");
        if (!string.IsNullOrEmpty(sidecarToken)) http.DefaultRequestHeaders.Add("dapr-api-token", sidecarToken);
        string identity = $"{tenant}:party:{party}";
        string prefix = "v1.0/actors/AggregateActor/" + Uri.EscapeDataString(identity) + "/state/";
        using JsonDocument? metadata = await ReadStateAsync(identity + ":metadata");
        if (metadata is null) return [];
        long count = Property(metadata.RootElement, "currentSequence").GetInt64();
        var events = new List<(long Sequence, string Type)>();
        for (long sequence = 1; sequence <= count; sequence++)
        {
            using JsonDocument? envelope = await ReadStateAsync(identity + $":events:{sequence}");
            Assert.NotNull(envelope);
            events.Add((sequence, Property(envelope.RootElement, "eventTypeName").GetString()!));
        }
        return events;

        async Task<JsonDocument?> ReadStateAsync(string key)
        {
            using HttpResponseMessage response = await http.GetAsync(prefix + Uri.EscapeDataString(key), cancellationToken);
            response.EnsureSuccessStatusCode();
            string body = await response.Content.ReadAsStringAsync(cancellationToken);
            return string.IsNullOrWhiteSpace(body) ? null : JsonDocument.Parse(body);
        }
    }

    private static JsonElement Property(JsonElement value, string name)
        => value.EnumerateObject().Single(property => property.Name.Equals(name, StringComparison.OrdinalIgnoreCase)).Value;
}

using System.Text.Json;
using Shouldly;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Reads persisted actor event envelopes in the private Gateway store independently of projections.</summary>
internal static class PersistedPartyEvents
{
    /// <summary>Requires exactly one durable deactivation event and returns its sequence.</summary>
    internal static async Task<long> RequireOneDeactivationAsync(HttpClient http, string tenant, string party, CancellationToken cancellationToken)
    {
        var events = await ReadEventTypesAsync(http, tenant, party, cancellationToken);
        Assert.NotEmpty(events);
        return Assert.Single(events, item => item.Type.EndsWith("PartyDeactivated", StringComparison.Ordinal)).Sequence;
    }

    /// <summary>Refuses any creation effect; a rejection-only stream is not an existing business party (ledger item 556).</summary>
    internal static async Task RequireNoPartyCreatedAsync(HttpClient http, string tenant, string party, CancellationToken cancellationToken)
    {
        var events = await ReadEventTypesAsync(http, tenant, party, cancellationToken);
        Assert.DoesNotContain(events, item => item.Type.EndsWith("PartyCreated", StringComparison.Ordinal));
        Assert.DoesNotContain(events, item => item.Type.EndsWith("PartyDeactivated", StringComparison.Ordinal));
    }

    /// <summary>Checks that the accepted creation persisted the authenticated principal in its event envelope.</summary>
    internal static async Task RequireCreationActorAsync(HttpClient http, string tenant, string party,
        string correlationId, string authenticatedSubject, CancellationToken cancellationToken)
    {
        var events = await ReadAsync(http, tenant, party, static (_, envelope) =>
        {
            string type = Property(envelope, "eventTypeName").GetString()!;
            return type.EndsWith("PartyCreated", StringComparison.Ordinal)
                ? (Created: true, CorrelationId: OptionalStringProperty(envelope, "correlationId"),
                    UserId: OptionalStringProperty(envelope, "userId"))
                : (Created: false, CorrelationId: null, UserId: null);
        }, cancellationToken);
        var created = Assert.Single(events, item => item.Created);
        created.CorrelationId.ShouldBe(correlationId);
        Assert.True(string.Equals(created.UserId, authenticatedSubject, StringComparison.Ordinal),
            "The persisted creation user must match the synthetic signed subject.");
    }

    /// <summary>Reads the committed aggregate event sequence independently of its projection.</summary>
    internal static async Task<long> ReadSequenceAsync(HttpClient http, string tenant, string party, CancellationToken cancellationToken)
    {
        string identity = $"{tenant}:party:{party}";
        using JsonDocument? metadata = await ReadStateAsync(http, identity, identity + ":metadata", cancellationToken);
        return metadata is null ? 0 : Property(metadata.RootElement, "currentSequence").GetInt64();
    }

    /// <summary>Refuses a changed durable sequence even when an authorized projection remains stale.</summary>
    internal static async Task<long> RequireUnchangedSequenceAsync(HttpClient http, string tenant, string party,
        long before, CancellationToken cancellationToken)
    {
        long after = await ReadSequenceAsync(http, tenant, party, cancellationToken);
        after.ShouldBe(before, "A refused call changed the durable aggregate event sequence.");
        return after;
    }

    /// <summary>Creates a state client at the discovered endpoint, preserving only its separate sidecar API credential.</summary>
    internal static HttpClient CreateClient(Uri endpoint, string? sidecarToken)
    {
        var http = new HttpClient { BaseAddress = endpoint, Timeout = TimeSpan.FromSeconds(15) };
        // APP_API_TOKEN protects sidecar-to-app calls; DAPR_API_TOKEN protects this sidecar HTTP API.
        if (!string.IsNullOrEmpty(sidecarToken)) http.DefaultRequestHeaders.Add("dapr-api-token", sidecarToken);
        return http;
    }

    private static Task<IReadOnlyList<(long Sequence, string Type)>> ReadEventTypesAsync(
        HttpClient http, string tenant, string party, CancellationToken cancellationToken)
        => ReadAsync(http, tenant, party,
            static (sequence, envelope) => (sequence, Property(envelope, "eventTypeName").GetString()!), cancellationToken);

    private static async Task<IReadOnlyList<T>> ReadAsync<T>(HttpClient http, string tenant, string party,
        Func<long, JsonElement, T> project, CancellationToken cancellationToken)
    {
        string identity = $"{tenant}:party:{party}";
        using JsonDocument? metadata = await ReadStateAsync(http, identity, identity + ":metadata", cancellationToken);
        if (metadata is null) return [];
        long count = Property(metadata.RootElement, "currentSequence").GetInt64();
        var events = new List<T>();
        for (long sequence = 1; sequence <= count; sequence++)
        {
            using JsonDocument? envelope = await ReadStateAsync(http, identity, identity + $":events:{sequence}", cancellationToken);
            Assert.NotNull(envelope);
            events.Add(project(sequence, envelope.RootElement));
        }
        return events;

    }

    private static async Task<JsonDocument?> ReadStateAsync(HttpClient http, string identity, string key, CancellationToken cancellationToken)
    {
        string prefix = "v1.0/actors/AggregateActor/" + Uri.EscapeDataString(identity) + "/state/";
        using HttpResponseMessage response = await http.GetAsync(prefix + Uri.EscapeDataString(key), cancellationToken);
        response.EnsureSuccessStatusCode();
        string body = await response.Content.ReadAsStringAsync(cancellationToken);
        return string.IsNullOrWhiteSpace(body) ? null : JsonDocument.Parse(body);
    }

    private static JsonElement Property(JsonElement value, string name)
        => value.EnumerateObject().Single(property => property.Name.Equals(name, StringComparison.OrdinalIgnoreCase)).Value;

    private static string? OptionalStringProperty(JsonElement value, string name)
    {
        JsonElement element = value.EnumerateObject()
            .SingleOrDefault(property => property.Name.Equals(name, StringComparison.OrdinalIgnoreCase)).Value;
        return element.ValueKind == JsonValueKind.String ? element.GetString() : null;
    }
}

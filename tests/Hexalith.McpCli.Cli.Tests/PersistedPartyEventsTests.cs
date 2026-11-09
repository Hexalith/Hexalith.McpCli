using System.Text.Json;
using Hexalith.McpCli.Integration.Tests;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Protects both C05 persisted-state oracles against a fixed sidecar port or lost API credential.</summary>
public sealed class PersistedPartyEventsTests
{
    /// <summary>The exact Gateway registration supplies its dynamically assigned HTTP endpoint.</summary>
    [Fact]
    public void SidecarDiscoverySelectsTheExactGatewayHttpPort()
    {
        Uri endpoint = GatewaySidecarEndpoint.FromSnapshot("""[{"appId":"parties","httpPort":3501},{"appId":"eventstore","httpPort":43219}]""");
        endpoint.ShouldBe(new Uri("http://127.0.0.1:43219/"));
    }

    /// <summary>Missing, ambiguous or malformed discovery never falls back to a conventional port.</summary>
    /// <param name="snapshot">The incomplete discovery response.</param>
    [Theory]
    [InlineData("{}")]
    [InlineData("[]")]
    [InlineData("[{\"appId\":\"parties\",\"httpPort\":3501}]")]
    [InlineData("[{\"appId\":\"eventstore\"}]")]
    [InlineData("[{\"appId\":\"eventstore\",\"httpPort\":0}]")]
    [InlineData("[{\"appId\":\"eventstore\",\"httpPort\":65536}]")]
    [InlineData("[{\"appId\":\"eventstore\",\"httpPort\":\"43219\"}]")]
    [InlineData("[{\"appId\":\"eventstore\",\"httpPort\":43219},{\"appId\":\"eventstore\",\"httpPort\":43220}]")]
    public void InvalidSidecarDiscoveryFailsClosed(string snapshot)
        => Should.Throw<InvalidDataException>(() => GatewaySidecarEndpoint.FromSnapshot(snapshot)).Message
            .ShouldBe("Expected exactly one Gateway sidecar with a valid HTTP port.");

    /// <summary>Both state oracles reach the supplied endpoint and forward only an explicitly supplied Dapr API token.</summary>
    /// <param name="deactivation">Whether to require one deactivation instead of an absent business party.</param>
    /// <param name="token">The optional sidecar API credential.</param>
    [Theory]
    [InlineData(false, null)]
    [InlineData(false, "private-dapr-api-token")]
    [InlineData(true, null)]
    [InlineData(true, "private-dapr-api-token")]
    public async Task StateOraclesUseTheDiscoveredEndpointAndApiCredentialAsync(bool deactivation, string? token)
    {
        await using var sidecar = new ScriptedGateway(request =>
        {
            string path = Uri.UnescapeDataString(request.Path);
            string body = path.EndsWith(":metadata", StringComparison.Ordinal)
                ? JsonSerializer.Serialize(new { CurrentSequence = deactivation ? 3 : 1 })
                : JsonSerializer.Serialize(new { EventTypeName = !deactivation ? "CommandRejected"
                    : path.EndsWith(":events:1", StringComparison.Ordinal) ? "PartyCreated"
                    : path.EndsWith(":events:2", StringComparison.Ordinal) ? "PartyDeactivated" : "NoOp" });
            return ScriptedGateway.Response(200, "OK", "application/json", body);
        });
        Uri endpoint = GatewaySidecarEndpoint.FromSnapshot(JsonSerializer.Serialize(new[] { new { appId = "eventstore", httpPort = new Uri(sidecar.Url).Port } }));
        using HttpClient client = PersistedPartyEvents.CreateClient(endpoint, token);
        if (deactivation)
            (await PersistedPartyEvents.RequireOneDeactivationAsync(client, "tenant-b", "state-party", TestContext.Current.CancellationToken)).ShouldBe(2);
        else
            await PersistedPartyEvents.RequireNoPartyCreatedAsync(client, "tenant-b", "state-party", TestContext.Current.CancellationToken);
        sidecar.Requests.Count.ShouldBe(deactivation ? 4 : 2);
        foreach (GatewayRequest request in sidecar.Requests)
        {
            request.Method.ShouldBe("GET");
            request.Body.ShouldBeEmpty();
            Uri.UnescapeDataString(request.Path).ShouldStartWith("/v1.0/actors/AggregateActor/tenant-b:party:state-party/state/tenant-b:party:state-party:");
            request.Headers.ContainsKey("Authorization").ShouldBeFalse();
            request.Headers.ContainsKey("dapr-api-token").ShouldBe(token is not null);
            if (token is not null) request.Headers["dapr-api-token"].ShouldBe(token);
        }
    }

    /// <summary>A stale projection cannot excuse a newly committed aggregate event.</summary>
    [Fact]
    public async Task ChangedDurableSequenceIsRejectedAsync()
    {
        int sequence = 0;
        await using var sidecar = new ScriptedGateway(_ => ScriptedGateway.Response(200, "OK", "application/json",
            JsonSerializer.Serialize(new { CurrentSequence = Interlocked.Increment(ref sequence) })));
        using HttpClient client = PersistedPartyEvents.CreateClient(new Uri(sidecar.Url), null);
        long before = await PersistedPartyEvents.ReadSequenceAsync(client, "tenant-b", "state-party", TestContext.Current.CancellationToken);
        (await Assert.ThrowsAsync<ShouldAssertException>(() => PersistedPartyEvents.RequireUnchangedSequenceAsync(
            client, "tenant-b", "state-party", before, TestContext.Current.CancellationToken))).Message.ShouldContain("durable aggregate event sequence");
        sidecar.Requests.Count.ShouldBe(2);
    }

    /// <summary>Unchanged durable sequence checks read metadata only.</summary>
    [Fact]
    public async Task StableDurableSequencePassesAsync()
    {
        await using var sidecar = new ScriptedGateway(_ => ScriptedGateway.Response(200, "OK", "application/json", """{"currentSequence":7}"""));
        using HttpClient client = PersistedPartyEvents.CreateClient(new Uri(sidecar.Url), null);
        (await PersistedPartyEvents.RequireUnchangedSequenceAsync(client, "tenant-b", "state-party", 7, TestContext.Current.CancellationToken)).ShouldBe(7);
        sidecar.Requests.ShouldHaveSingleItem().Path.ShouldEndWith("metadata");
    }

    /// <summary>The deactivation oracle rejects empty, zero-match and duplicate-event streams.</summary>
    /// <param name="events">The stored event type names.</param>
    /// <param name="assertion">The expected rejecting oracle assertion.</param>
    [Theory]
    [InlineData("", "Assert.NotEmpty()")]
    [InlineData("PartyCreated", "Assert.Single()")]
    [InlineData("PartyCreated,PartyDeactivated,PartyDeactivated", "Assert.Single()")]
    public async Task DeactivationOracleRejectsUnsafeStreamsAsync(string events, string assertion)
    {
        await using var sidecar = EventStream(events);
        using HttpClient client = PersistedPartyEvents.CreateClient(new Uri(sidecar.Url), null);
        Exception failure = await Assert.ThrowsAnyAsync<Exception>(() => PersistedPartyEvents.RequireOneDeactivationAsync(
            client, "tenant-b", "state-party", TestContext.Current.CancellationToken));
        failure.Message.ShouldStartWith(assertion);
    }

    /// <summary>The missing-party oracle rejects both creation and deactivation effects.</summary>
    /// <param name="eventType">The forbidden stored event.</param>
    [Theory]
    [InlineData("PartyCreated")]
    [InlineData("PartyDeactivated")]
    public async Task MissingPartyOracleRejectsBusinessEffectsAsync(string eventType)
    {
        await using var sidecar = EventStream(eventType);
        using HttpClient client = PersistedPartyEvents.CreateClient(new Uri(sidecar.Url), null);
        Exception failure = await Assert.ThrowsAnyAsync<Exception>(() => PersistedPartyEvents.RequireNoPartyCreatedAsync(
            client, "tenant-b", "state-party", TestContext.Current.CancellationToken));
        failure.Message.ShouldStartWith("Assert.DoesNotContain()");
    }

    private static ScriptedGateway EventStream(string events)
    {
        string[] names = events.Length == 0 ? [] : events.Split(',');
        return new ScriptedGateway(request =>
        {
            string path = Uri.UnescapeDataString(request.Path);
            string body = path.EndsWith(":metadata", StringComparison.Ordinal)
                ? JsonSerializer.Serialize(new { CurrentSequence = names.Length })
                : JsonSerializer.Serialize(new { EventTypeName = names[int.Parse(path.Split(':')[^1], System.Globalization.CultureInfo.InvariantCulture) - 1] });
            return ScriptedGateway.Response(200, "OK", "application/json", body);
        });
    }

}

using System.IO.Pipelines;
using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Core;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using NSubstitute;
using Shouldly;

namespace Hexalith.McpCli.Mcp.Tests;

/// <summary>Runs SDK calls against the real Core and a controlled Gateway.</summary>
internal sealed class McpTestSession : IAsyncDisposable
{
    internal const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
    internal const string CorrelationId = "01J9MZHXT3RKM0VWXRXGSJDATK";
    internal const string MessageId = "01J9MZHXT3RKM0VWXRXGSJDATM";
    internal const string Key = "01J9MZHXT3RKM0VWXRXGSJDATN";
    internal const string CommandPayload = "{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\",\"Title\":\"Hello\"}";
    internal const string QueryPayload = "{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}";

    private readonly CancellationTokenSource _timeout = new(TimeSpan.FromSeconds(20));
    private readonly McpServer _server;
    private readonly Task _serverTask;

    private McpTestSession(ServiceProvider provider, IEventStoreGatewayClient gateway, McpServer server)
    {
        Provider = provider;
        Gateway = gateway;
        _server = server;
        _serverTask = server.RunAsync(_timeout.Token);
    }

    internal ServiceProvider Provider { get; }
    internal IEventStoreGatewayClient Gateway { get; }
    internal McpClient Client { get; private set; } = null!;
    internal CancellationToken Token => _timeout.Token;

    internal static ResolvedSettings Settings(string? tenant = "session-tenant", bool allowOverride = false,
        bool hasUrl = true, bool readOnly = false)
        => new(hasUrl ? new Uri("https://gateway.example/") : null, null, tenant, "operator-1", allowOverride,
            new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "task-id" }, "json", null, readOnly,
            false, null, new Dictionary<string, string>());

    internal static async Task<McpTestSession> CreateAsync(string version, ResolvedSettings? settings = null,
        Action<IServiceCollection, IEventStoreGatewayClient>? configure = null)
    {
        settings ??= Settings();
        var gateway = Substitute.For<IEventStoreGatewayClient>();
        gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(CorrelationId, MessageId: MessageId)));
        gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new EventStoreQueryResult(CorrelationId,
                JsonSerializer.SerializeToElement(new { arbitrary = new { values = new[] { 1, 2 } } }), false, null)));
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddMcpCliCore(settings, () => [typeof(CreateItemCommand).Assembly,
            typeof(global::Catalog.Routing.Contracts.Module).Assembly, typeof(global::Catalog.Lint.Contracts.Module).Assembly], _ => { });
        services.AddSingleton(gateway);
        configure?.Invoke(services, gateway);
        services.AddMcpCliMcpServer(settings);
        ServiceProvider provider = services.BuildServiceProvider();
        var clientToServer = new Pipe();
        var serverToClient = new Pipe();
        var server = McpServer.Create(new StreamServerTransport(clientToServer.Reader.AsStream(),
            serverToClient.Writer.AsStream(), "execution-test"),
            provider.GetRequiredService<IOptions<McpServerOptions>>().Value,
            provider.GetRequiredService<ILoggerFactory>(), provider);
        var session = new McpTestSession(provider, gateway, server);
        try
        {
            session.Client = await McpClient.CreateAsync(new StreamClientTransport(clientToServer.Writer.AsStream(),
                serverToClient.Reader.AsStream()), new McpClientOptions { ProtocolVersion = version },
                cancellationToken: session.Token);
            session.Client.NegotiatedProtocolVersion.ShouldBe(version);
            return session;
        }
        catch
        {
            await session.DisposeAsync();
            throw;
        }
    }

    internal async Task<CallToolResult> CallAsync(string tool, object? arguments = null)
    {
        Dictionary<string, object?> values = arguments is null ? [] : JsonSerializer.Deserialize<Dictionary<string, object?>>(
            JsonSerializer.Serialize(arguments, arguments.GetType(), McpCliJson.Result))!;
        return await Client.CallToolAsync(tool, values, cancellationToken: Token);
    }

    internal async Task<JsonElement> AssertParityAsync(OperationCall arguments)
    {
        OperationOutcome expected = await Provider.GetRequiredService<IOperationExecutor>().ExecuteAsync(arguments,
            Provider.GetRequiredService<EnvelopeContext>(), Token);
        Gateway.ClearReceivedCalls();
        CallToolResult actual = await CallAsync(arguments is SendCommandArguments ? "send_command" : "run_query", arguments);
        return AssertDocument(actual, expected.Error is null ? expected.Document! : new { error = expected.Error },
            expected.Error is not null);
    }

    internal static JsonElement AssertDocument(CallToolResult result, object expected, bool isError = false)
    {
        result.IsError.ShouldBe(isError);
        JsonElement actual = result.StructuredContent.ShouldNotBeNull();
        JsonElement canonical = JsonSerializer.SerializeToElement(expected, McpCliJson.Result);
        JsonElement.DeepEquals(actual, canonical).ShouldBeTrue(actual.GetRawText());
        using JsonDocument text = JsonDocument.Parse(result.Content.ShouldHaveSingleItem().ShouldBeOfType<TextContentBlock>().Text);
        JsonElement.DeepEquals(text.RootElement, actual).ShouldBeTrue();
        return actual;
    }

    public async ValueTask DisposeAsync()
    {
        if (Client is not null)
        {
            await Client.DisposeAsync();
        }

        await _timeout.CancelAsync();
        try
        {
            await _serverTask;
        }
        catch (OperationCanceledException)
        {
        }

        await _server.DisposeAsync();
        Provider.Dispose();
        _timeout.Dispose();
    }
}

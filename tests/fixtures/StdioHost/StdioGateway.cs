using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Microsoft.Extensions.DependencyInjection;
using NSubstitute;

namespace Hexalith.McpCli.StdioHost;

/// <summary>Substitutes only the Gateway while retaining the real CLI, Core and stdio host.</summary>
internal static class StdioGateway
{
    /// <summary>Registers deterministic Gateway responses for the child-process execution lane.</summary>
    internal static void Configure(IServiceCollection services)
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
            .Returns(call => Task.FromResult(new SubmitCommandResponse(((SubmitCommandRequest)call[0]).CorrelationId!,
                JsonSerializer.SerializeToElement(new { accepted = true }), "01J9MZHXT3RKM0VWXRXGSJDATM")));
        gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(call => ((SubmitQueryRequest)call[0]).EntityId == "gateway-error"
                ? throw new EventStoreGatewayException(409, "Conflict", detail: "Fixture Gateway refusal.")
                : Task.FromResult(new EventStoreQueryResult("01J9MZHXT3RKM0VWXRXGSJDATK",
                    JsonSerializer.SerializeToElement(new { items = Array.Empty<string>() }), false, null)
                {
                    Metadata = new QueryResponseMetadata(Paging: new QueryPagingMetadata(25, 0, null, 0, false)),
                }));
        services.AddSingleton(gateway);
    }
}

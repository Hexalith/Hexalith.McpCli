using System.Text.Json;

using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Integration.Tests;

using NSubstitute;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects the hosted nonmember control's exact rejection and independently observed unchanged target.</summary>
public sealed class NativeAdministratorBoundaryTests
{
    /// <summary>Only permission rejection plus independent absence before and after can satisfy the negative control.</summary>
    [Theory]
    [InlineData("rejected")]
    [InlineData("accepted")]
    [InlineData("unauthorized")]
    [InlineData("wrong-rejection")]
    [InlineData("authority-unavailable")]
    [InlineData("present-before")]
    [InlineData("changed-after")]
    [InlineData("missing-endpoint-before")]
    [InlineData("missing-endpoint-after")]
    [InlineData("unrelated-not-found-before")]
    [InlineData("unrelated-not-found-after")]
    public async Task RequiresOwnerPermissionRejectionAndUnchangedState(string outcome)
    {
        var nonmember = Substitute.For<IEventStoreGatewayClient>();
        var administrator = Substitute.For<IEventStoreGatewayClient>();
        var calls = new List<string>();
        SubmitCommandRequest? command = null;
        int reads = 0;
        administrator.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(call =>
            {
                calls.Add("read"); reads++;
                var request = call.Arg<SubmitQueryRequest>();
                Assert.Equal(NativeAdministratorBoundary.TargetTenant, request.Tenant);
                Assert.Equal(NativeAdministratorBoundary.TargetTenant, request.AggregateId);
                Assert.Null(request.ProjectionActorType);
                Assert.True(call.Arg<CancellationToken>().CanBeCanceled);
                return outcome == "present-before" || outcome == "changed-after" && reads == 2
                    ? Task.FromResult(new EventStoreQueryResult("correlation", JsonSerializer.SerializeToElement(new { id = request.AggregateId }), false, null))
                    : Task.FromException<EventStoreQueryResult>(outcome == "missing-endpoint-before"
                        || outcome == "missing-endpoint-after" && reads == 2
                        ? new EventStoreGatewayException(404, "Not Found")
                        : new EventStoreGatewayException(404, "Not Found", type: "https://hexalith.io/problems/not-found",
                            detail: "The requested resource was not found.", reasonCode: outcome == "unrelated-not-found-before"
                                || outcome == "unrelated-not-found-after" && reads == 2
                                ? "other_resource_missing" : QueryProblemReasonCodes.ProjectionMissing));
            });
        nonmember.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>()).Returns(call =>
        {
            calls.Add("command"); command = call.Arg<SubmitCommandRequest>();
            Assert.True(call.Arg<CancellationToken>().CanBeCanceled);
            return outcome == "accepted" ? Task.FromResult(new SubmitCommandResponse("correlation"))
                : Task.FromException<SubmitCommandResponse>(new EventStoreGatewayException(
                    outcome == "unauthorized" ? 401 : outcome == "authority-unavailable" ? 503 : 422, "Rejected",
                    reasonCode: outcome == "wrong-rejection" ? "tenant-not-found-rejection" : "insufficient-permissions-rejection"));
        });
        Task test = NativeAdministratorBoundary.RequireNonmemberRejectionAsync(nonmember, administrator, TestContext.Current.CancellationToken);
        if (outcome == "rejected")
        {
            await test;
            Assert.Equal(new[] { "read", "command", "read" }, calls);
            Assert.NotNull(command);
            Assert.Equal("platform:tenants", command.Tenant);
            Assert.Equal("create-tenant", command.CommandType);
            Assert.Equal(NativeAdministratorBoundary.TargetTenant, command.AggregateId);
            Assert.Equal(command.MessageId, command.IdempotencyKey);
            Assert.False(command.Payload.TryGetProperty("UserId", out _));
        }
        else
        {
            await Assert.ThrowsAnyAsync<Exception>(() => test);
            Assert.Equal(outcome == "present-before" || outcome.EndsWith("-before", StringComparison.Ordinal) ? 0 : 1,
                calls.Count(call => call == "command"));
        }
    }
}

using System;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.EventStore.Server.Pipeline.Queries;
using Hexalith.EventStore.Server.Queries;
using Microsoft.Extensions.Logging;

namespace Hexalith.EventStore.Queries;

public sealed class HandlerAwareQueryRouter(IQueryRouter inner, IDomainQueryHandlerRegistry registry, IDomainQueryInvoker invoker, ILogger<HandlerAwareQueryRouter> logger) : IQueryRouter
{
	public async Task<QueryRouterResult> RouteQueryAsync(SubmitQuery query, CancellationToken cancellationToken = default(CancellationToken))
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		cancellationToken.ThrowIfCancellationRequested();
		if (!(await registry.SupportsQueryAsync(query.Domain, query.QueryType, cancellationToken).ConfigureAwait(continueOnCapturedContext: false)))
		{
			return await inner.RouteQueryAsync(query, cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
		}
		logger.LogDebug("Routing query to domain handler endpoint: CorrelationId={CorrelationId}, Tenant={TenantId}, Domain={Domain}, QueryType={QueryType}, Stage=QueryHandlerRouting", query.CorrelationId, query.Tenant, query.Domain, query.QueryType);
		QueryEnvelope query2 = new QueryEnvelope(query.Tenant, query.Domain, query.AggregateId, query.QueryType, query.Payload, query.CorrelationId, query.UserId, query.EntityId, query.IsGlobalAdmin, query.Paging, query.OriginalActorId, query.AuthenticatedWorkloadId, query.IsDelegated, query.Scopes, query.Audience, query.DelegationId)
		{
			IdentityAdmissionProof = query.IdentityAdmissionProof,
			CallerAuthority = query.CallerAuthority
		};
		QueryResult queryResult = await invoker.InvokeAsync(query2, cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
		if (!queryResult.Success)
		{
			return (queryResult.ErrorMessage == "safe-denial") ? new QueryRouterResult(Success: false, null, NotFound: true) : new QueryRouterResult(Success: false, null, NotFound: false, queryResult.ErrorMessage, null, queryResult.Metadata);
		}
		byte[] payloadBytes = queryResult.PayloadBytes;
		if (payloadBytes == null || payloadBytes.Length <= 0)
		{
			return new QueryRouterResult(Success: false, null, NotFound: false, "Domain query handler returned an empty payload.");
		}
		try
		{
			JsonElement payload = queryResult.GetPayload();
			int num;
			if (!string.IsNullOrWhiteSpace(queryResult.ProjectionType))
			{
				QueryResponseProvenance? queryResponseProvenance = queryResult.Metadata?.Provenance;
				if (queryResponseProvenance.HasValue && queryResponseProvenance == QueryResponseProvenance.ProjectionBacked)
				{
					num = ((string.IsNullOrWhiteSpace(query.ProjectionType) || string.Equals(query.ProjectionType, queryResult.ProjectionType, StringComparison.Ordinal)) ? 1 : 0);
					goto IL_03e9;
				}
			}
			num = 0;
			goto IL_03e9;
			IL_03e9:
			bool flag = (byte)num != 0;
			return new QueryRouterResult(Success: true, payload, NotFound: false, null, flag ? queryResult.ProjectionType : null, flag ? queryResult.Metadata : StampHandlerComputed(queryResult.Metadata));
		}
		catch (JsonException)
		{
			return new QueryRouterResult(Success: false, null, NotFound: false, "Domain query handler returned a malformed payload.");
		}
	}

	private static QueryResponseMetadata StampHandlerComputed(QueryResponseMetadata? metadata)
	{
		QueryResponseMetadata queryResponseMetadata = metadata ?? new QueryResponseMetadata();
		ProjectionLifecycleState lifecycle = ProjectionLifecyclePolicy.Normalize(queryResponseMetadata.Lifecycle, QueryResponseProvenance.HandlerComputed);
		return queryResponseMetadata with
		{
			Provenance = QueryResponseProvenance.HandlerComputed,
			Lifecycle = lifecycle,
			IsStale = ProjectionLifecyclePolicy.ProjectIsStale(lifecycle, queryResponseMetadata.IsStale),
			IsDegraded = ProjectionLifecyclePolicy.ProjectIsDegraded(lifecycle, queryResponseMetadata.IsDegraded)
		};
	}
}

using Hexalith.Tenants.Authorization;
using System.Text.Json;

using Hexalith.EventStore.Client.Projections;
using Hexalith.EventStore.Client.Queries;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.Tenants.Configuration;
using Hexalith.Tenants.Contracts.Queries;
using Hexalith.Tenants.Server.Projections;
using Hexalith.Tenants.Telemetry;

using Microsoft.Extensions.Options;

namespace Hexalith.Tenants.Queries.Handlers;

/// <summary>
/// Serves the <c>get-tenant</c> query: full details for a single tenant, gated by tenant membership
/// or global-administrator role.
/// </summary>
/// <remarks>
/// Authorized API consumers receive the full configuration contract. FR-6 is a server-side UI display
/// policy: the BFF separately applies exact prefix grants and display-safe keys before browser rendering.
/// Missing or malformed UI display policy does not change this membership-authorized API response.
/// </remarks>
public sealed class GetTenantQueryHandler(
    IReadModelStore store,
    ITenantsGlobalAdministratorAuthority administratorAuthority,
    IQueryCursorCodec cursorCodec,
    TenantTelemetry telemetry,
    ILogger<GetTenantQueryHandler> logger,
    IOptions<ReadModelFreshnessOptions>? freshnessOptions = null,
    TimeProvider? timeProvider = null)
    : TenantQueryHandlerBase(store, administratorAuthority, cursorCodec, telemetry, logger, freshnessOptions, timeProvider) {
    /// <inheritdoc/>
    /// <summary>Gets the offline route declaration from the same owner metadata as runtime dispatch.</summary>
    public static Hexalith.EventStore.Contracts.Routing.RouteContractDeclaration CatalogDeclaration =>
        Hexalith.Tenants.Server.Routing.TenantCatalogCapabilities.HandlerQueries.Single(route => route.MessageType == GetTenantQuery.QueryType);

    public override string QueryType => CatalogDeclaration.MessageType!;

    /// <inheritdoc/>
    protected override async Task<QueryResult> ExecuteCoreAsync(QueryEnvelope envelope, CancellationToken cancellationToken) {
        cancellationToken.ThrowIfCancellationRequested();
        ReadModelEntry<TenantReadModel>? tenantEntry = await GetStateEntryAsync<TenantReadModel>(
            TenantProjectionKeyPrefix + envelope.AggregateId, cancellationToken).ConfigureAwait(false);
        TenantReadModel? model = tenantEntry?.Value;
        cancellationToken.ThrowIfCancellationRequested();

        if (model is null) {
            return await IsGlobalAdminAsync(envelope, cancellationToken).ConfigureAwait(false)
                ? new QueryResult(false, default, ErrorMessage: "Tenant not found")
                : new QueryResult(false, default, ErrorMessage: QueryAdapterFailureReason.Forbidden);
        }

        if (!await IsAuthorizedForTenantAsync(envelope, model, cancellationToken).ConfigureAwait(false)) {
            return new QueryResult(false, default, ErrorMessage: "Forbidden");
        }

        cancellationToken.ThrowIfCancellationRequested();
        TenantDetail detail = new(
            model.TenantId,
            model.Name,
            model.Description,
            model.Status,
            GetConcreteMembers(model).Select(m => new TenantMember(m.Key, m.Value)).ToList(),
            model.Configuration.ToDictionary(kvp => kvp.Key, kvp => kvp.Value),
            model.CreatedAt);

        JsonElement payload = SerializeToElement(detail);
        return CreateSuccessResult(payload, "tenants", model, tenantEntry?.ETag);
    }
}

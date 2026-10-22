using Catalog.Routing.Contracts;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Exercises a query tenant carried by a string-backed value object.</summary>
/// <param name="Tenant">The tenant filled from the trusted envelope.</param>
[HexalithQuery("Read items under a value-object tenant.", Domain = "routing", WireType = "items",
    ProjectionType = "items", AggregateId = "items", TenantProperty = nameof(Tenant))]
public sealed record ValueObjectEnvelopeQuery(EnvelopeValue Tenant);

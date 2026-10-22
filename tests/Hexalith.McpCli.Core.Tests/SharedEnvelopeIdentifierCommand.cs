using Catalog.Routing.Contracts;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Reuses one converter-backed CLR type for an envelope tenant and a payload identifier.</summary>
/// <param name="Tenant">The envelope tenant.</param>
/// <param name="ItemId">The independently constrained payload identifier.</param>
public sealed record SharedEnvelopeIdentifierCommand(EnvelopeValue Tenant, [property: HexalithIdentifier] EnvelopeValue ItemId);

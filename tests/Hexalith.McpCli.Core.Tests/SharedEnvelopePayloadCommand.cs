using Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Reuses an envelope value-object type in an ordinary payload member.</summary>
/// <typeparam name="T">The ordinary member's direct or nested serialization shape.</typeparam>
/// <param name="Tenant">The envelope tenant.</param>
/// <param name="Value">The ordinary payload member.</param>
public sealed record SharedEnvelopePayloadCommand<T>(EnvelopeValue Tenant, T Value);

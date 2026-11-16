using Hexalith.McpCli.Abstractions;

namespace Catalog.Invalid.Contracts;

/// <summary>Exercises rejection of a projection actor without its required projection type.</summary>
[HexalithQuery("Invalid actor-only projection query.", Domain = "invalid", ProjectionActorType = "ItemProjectionActor")]
public sealed record ActorOnlyProjectionQuery;

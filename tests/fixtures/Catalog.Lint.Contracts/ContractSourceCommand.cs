using System.ComponentModel;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.McpCli.Abstractions;

namespace Catalog.Lint.Contracts;

/// <summary>Exercises an ICommandContract aggregate source and a kebab-case hollow description.</summary>
/// <param name="AggregateId">The aggregate identifier read through the contract interface.</param>
/// <param name="Label">The label to apply.</param>
[HexalithCommand("contract-source-command")]
public sealed record ContractSourceCommand(
    [property: Description("The aggregate identifier read through the contract interface.")] string AggregateId,
    [property: Description("The label to apply.")] string Label) : ICommandContract
{
    /// <summary>Gets the interface command type.</summary>
    public static string CommandType => "contract-source";

    /// <summary>Gets the interface domain.</summary>
    public static string Domain => "lint-fixture";
}

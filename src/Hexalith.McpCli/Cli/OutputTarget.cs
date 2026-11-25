namespace Hexalith.McpCli.Cli;

/// <summary>The kind and filesystem identity of a result target at inspection time.</summary>
internal readonly record struct OutputTarget(OutputTargetKind Kind, ulong Volume = 0, ulong Low = 0, ulong High = 0)
{
    /// <summary>Refuses a replacement observed when the target is opened.</summary>
    internal void RequireMatch(OutputTarget opened)
    {
        if (this != opened)
        {
            throw new IOException("The result destination changed before it could be opened.");
        }
    }
}

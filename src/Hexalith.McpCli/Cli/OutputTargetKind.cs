namespace Hexalith.McpCli.Cli;

/// <summary>File kinds relevant to result writing.</summary>
internal enum OutputTargetKind
{
    Missing,
    Regular,
    Pipe,
    Device,
    Unsupported,
}

using ModelContextProtocol.Protocol;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>The observable channels of one CLI or MCP head invocation.</summary>
/// <param name="Exit">The process exit code returned by the runner.</param>
/// <param name="Output">CLI stdout, or MCP stdout remaining after the selected reply.</param>
/// <param name="Error">Everything written to standard error.</param>
/// <param name="Tool">The MCP tool result, when the MCP head served the call.</param>
/// <param name="ProtocolTranscript">All MCP process stdout frames, including intermediate notifications.</param>
internal sealed record HeadResult(int Exit, string Output, string Error, CallToolResult? Tool, string ProtocolTranscript = "")
{
    /// <summary>Gets the public document: CLI stdout, or the MCP structured content after checking it matches the text content.</summary>
    internal string Document => Tool is null ? Output : Tool.StructuredContent?.GetRawText() ?? string.Empty;

    /// <summary>Gets every channel concatenated for absence checks.</summary>
    internal string AllChannels => string.Join('\n', Output, Error, ProtocolTranscript, Tool is null ? string.Empty
        : string.Join('\n', Tool.Content.OfType<TextContentBlock>().Select(block => block.Text)),
        Tool?.StructuredContent?.GetRawText() ?? string.Empty);
}

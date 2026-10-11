using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Records the SDK client's first request while forwarding a real child-process stdio transport.</summary>
internal sealed class RecordingClientTransport(IClientTransport inner) : IClientTransport
{
    /// <inheritdoc />
    public string Name => inner.Name;

    /// <summary>Gets the ordered methods sent by the client.</summary>
    internal List<string> Methods { get; } = [];

    /// <inheritdoc />
    public async Task<ITransport> ConnectAsync(CancellationToken cancellationToken = default)
        => new RecordingTransport(await inner.ConnectAsync(cancellationToken).ConfigureAwait(false), Methods);
}

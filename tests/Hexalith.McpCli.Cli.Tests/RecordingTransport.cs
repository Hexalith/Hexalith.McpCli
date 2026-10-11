using System.Threading.Channels;
using ModelContextProtocol.Protocol;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Forwards SDK JSON-RPC traffic and records outgoing request methods.</summary>
internal sealed class RecordingTransport(ITransport inner, List<string> methods) : ITransport
{
    /// <inheritdoc />
    public ChannelReader<JsonRpcMessage> MessageReader => inner.MessageReader;

    /// <inheritdoc />
    public string? SessionId => inner.SessionId;

    /// <inheritdoc />
    public Task SendMessageAsync(JsonRpcMessage message, CancellationToken cancellationToken = default)
    {
        if (message is JsonRpcRequest request)
        {
            methods.Add(request.Method);
        }

        return inner.SendMessageAsync(message, cancellationToken);
    }

    /// <inheritdoc />
    public ValueTask DisposeAsync() => inner.DisposeAsync();
}

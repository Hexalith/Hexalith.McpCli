using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>
/// Serves exact scripted HTTP/1.1 response bytes on a loopback socket and captures every request, so a test controls
/// reason phrases, content types, malformed bodies and invalid header lines that an HTTP listener cannot emit.
/// </summary>
internal sealed class ScriptedGateway : IAsyncDisposable
{
    private readonly TcpListener _listener = new(IPAddress.Loopback, 0);
    private readonly CancellationTokenSource _stop = new();
    private readonly ConcurrentQueue<GatewayRequest> _requests = new();
    private readonly Func<GatewayRequest, Task<byte[]>> _respond;
    private readonly Task _accepting;

    /// <summary>Starts a gateway that answers every request with the bytes chosen by <paramref name="respond" />.</summary>
    /// <param name="respond">Builds the complete raw response for one captured request.</param>
    internal ScriptedGateway(Func<GatewayRequest, byte[]> respond)
        : this(request => Task.FromResult(respond(request)))
    {
    }

    /// <summary>Starts a capturing gateway with an asynchronous response provider.</summary>
    /// <param name="respond">Builds the raw response after asynchronous forwarding or inspection.</param>
    internal ScriptedGateway(Func<GatewayRequest, Task<byte[]>> respond)
    {
        _respond = respond;
        _listener.Start();
        Url = $"http://127.0.0.1:{((IPEndPoint)_listener.LocalEndpoint).Port}/";
        _accepting = AcceptAsync();
    }

    /// <summary>Gets the loopback gateway base URL.</summary>
    internal string Url { get; }

    /// <summary>Gets the requests captured so far, in arrival order.</summary>
    internal IReadOnlyList<GatewayRequest> Requests => [.. _requests];

    /// <summary>Builds a complete HTTP/1.1 response that closes its connection.</summary>
    /// <param name="status">The status code on the status line.</param>
    /// <param name="reason">The reason phrase on the status line.</param>
    /// <param name="contentType">The content type, or <see langword="null" /> for none.</param>
    /// <param name="body">The UTF-8 response body.</param>
    /// <param name="rawHeaderLines">Additional raw header lines written verbatim before the content headers.</param>
    /// <returns>The response bytes.</returns>
    internal static byte[] Response(int status, string reason, string? contentType, string body, params string[] rawHeaderLines)
    {
        byte[] content = Encoding.UTF8.GetBytes(body);
        var head = new StringBuilder($"HTTP/1.1 {status} {reason}\r\n");
        foreach (string line in rawHeaderLines)
        {
            head.Append(line).Append("\r\n");
        }

        if (contentType is not null)
        {
            head.Append("Content-Type: ").Append(contentType).Append("\r\n");
        }

        head.Append("Content-Length: ").Append(content.Length).Append("\r\nConnection: close\r\n\r\n");
        return [.. Encoding.ASCII.GetBytes(head.ToString()), .. content];
    }

    /// <summary>Builds a 202 command acceptance that echoes the submitted identifiers.</summary>
    /// <param name="request">The captured command request.</param>
    /// <returns>The response bytes.</returns>
    internal static byte[] AcceptCommand(GatewayRequest request)
    {
        using var document = System.Text.Json.JsonDocument.Parse(request.Body);
        string body = System.Text.Json.JsonSerializer.Serialize(new
        {
            correlationId = document.RootElement.GetProperty("correlationId").GetString(),
            messageId = document.RootElement.GetProperty("messageId").GetString(),
        });
        return Response(202, "Accepted", "application/json", body);
    }

    /// <inheritdoc />
    public async ValueTask DisposeAsync()
    {
        await _stop.CancelAsync();
        _listener.Stop();
        try
        {
            await _accepting;
        }
        catch (Exception exception) when (exception is OperationCanceledException or SocketException or ObjectDisposedException)
        {
        }

        _stop.Dispose();
    }

    private async Task AcceptAsync()
    {
        while (!_stop.IsCancellationRequested)
        {
            TcpClient client = await _listener.AcceptTcpClientAsync(_stop.Token);
            _ = Task.Run(() => ServeAsync(client));
        }
    }

    private async Task ServeAsync(TcpClient client)
    {
        using (client)
        {
            try
            {
                NetworkStream stream = client.GetStream();
                GatewayRequest? request = await ReadRequestAsync(stream, _stop.Token);
                if (request is null)
                {
                    return;
                }

                _requests.Enqueue(request);
                await stream.WriteAsync(await _respond(request), _stop.Token);
                await stream.FlushAsync(_stop.Token);
                client.Client.Shutdown(SocketShutdown.Send);
            }
            catch (Exception exception) when (exception is IOException or SocketException or OperationCanceledException
                or ObjectDisposedException)
            {
            }
        }
    }

    private static async Task<GatewayRequest?> ReadRequestAsync(NetworkStream stream, CancellationToken cancellationToken)
    {
        var buffer = new List<byte>();
        byte[] chunk = new byte[4096];
        int headerEnd;
        while ((headerEnd = IndexOf(buffer, "\r\n\r\n"u8)) < 0)
        {
            int read = await stream.ReadAsync(chunk, cancellationToken);
            if (read == 0)
            {
                return null;
            }

            buffer.AddRange(chunk.AsSpan(0, read));
        }

        string[] lines = Encoding.ASCII.GetString([.. buffer.GetRange(0, headerEnd)]).Split("\r\n");
        string[] requestLine = lines[0].Split(' ');
        var headers = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (string line in lines.Skip(1))
        {
            int colon = line.IndexOf(':', StringComparison.Ordinal);
            headers[line[..colon].Trim()] = line[(colon + 1)..].Trim();
        }

        List<byte> remainder = buffer.GetRange(headerEnd + 4, buffer.Count - headerEnd - 4);
        byte[] body;
        if (headers.TryGetValue("Content-Length", out string? length))
        {
            body = await ReadExactAsync(stream, remainder, int.Parse(length, System.Globalization.CultureInfo.InvariantCulture),
                cancellationToken);
        }
        else if (headers.TryGetValue("Transfer-Encoding", out string? encoding) && encoding.Contains("chunked", StringComparison.OrdinalIgnoreCase))
        {
            body = await ReadChunkedAsync(stream, remainder, cancellationToken);
        }
        else
        {
            body = [];
        }

        return new GatewayRequest(requestLine[0], requestLine[1], headers, Encoding.UTF8.GetString(body));
    }

    private static async Task<byte[]> ReadExactAsync(NetworkStream stream, List<byte> buffer, int count,
        CancellationToken cancellationToken)
    {
        byte[] chunk = new byte[4096];
        while (buffer.Count < count)
        {
            int read = await stream.ReadAsync(chunk, cancellationToken);
            if (read == 0)
            {
                throw new IOException("The request body ended early.");
            }

            buffer.AddRange(chunk.AsSpan(0, read));
        }

        return [.. buffer.GetRange(0, count)];
    }

    private static async Task<byte[]> ReadChunkedAsync(NetworkStream stream, List<byte> buffer, CancellationToken cancellationToken)
    {
        var body = new List<byte>();
        while (true)
        {
            int lineEnd;
            while ((lineEnd = IndexOf(buffer, "\r\n"u8)) < 0)
            {
                await FillAsync(stream, buffer, cancellationToken);
            }

            string sizeText = Encoding.ASCII.GetString([.. buffer.GetRange(0, lineEnd)]).Split(';')[0].Trim();
            int size = int.Parse(sizeText, System.Globalization.NumberStyles.HexNumber, System.Globalization.CultureInfo.InvariantCulture);
            buffer.RemoveRange(0, lineEnd + 2);
            while (buffer.Count < size + 2)
            {
                await FillAsync(stream, buffer, cancellationToken);
            }

            if (size == 0)
            {
                return [.. body];
            }

            body.AddRange(buffer.GetRange(0, size));
            buffer.RemoveRange(0, size + 2);
        }
    }

    private static async Task FillAsync(NetworkStream stream, List<byte> buffer, CancellationToken cancellationToken)
    {
        byte[] chunk = new byte[4096];
        int read = await stream.ReadAsync(chunk, cancellationToken);
        if (read == 0)
        {
            throw new IOException("The chunked request body ended early.");
        }

        buffer.AddRange(chunk.AsSpan(0, read));
    }

    private static int IndexOf(List<byte> buffer, ReadOnlySpan<byte> pattern)
    {
        for (int index = 0; index + pattern.Length <= buffer.Count; index++)
        {
            bool match = true;
            for (int offset = 0; offset < pattern.Length && match; offset++)
            {
                match = buffer[index + offset] == pattern[offset];
            }

            if (match)
            {
                return index;
            }
        }

        return -1;
    }
}

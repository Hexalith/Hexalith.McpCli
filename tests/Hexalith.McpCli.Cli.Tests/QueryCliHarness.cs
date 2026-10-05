using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text;
using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Settings;
using Shouldly;
using Lint = global::Catalog.Lint.Contracts;
using Routing = global::Catalog.Routing.Contracts;
using StringContracts = global::Catalog.String.Contracts;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Captures real CLI query or command requests with bounded loopback service and restored console streams.</summary>
internal sealed class QueryCliHarness : IAsyncDisposable
{
    /// <summary>The valid aggregate ULID shared by synthetic CLI cases.</summary>
    internal const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
    /// <summary>The valid lint query input before trusted tenant filling.</summary>
    internal const string InspectPayload = """
        {"ItemId":"01ARZ3NDEKTSV4RRFFQ69G5FAV","ExternalId":"ordinary/reference",
         "Nested":{"Label":"item","nested/~":"value"},"Entries":[]}
        """;

    private readonly string _directory = Path.Combine(Path.GetTempPath(), "mcpcli-query-acceptance-" + Guid.NewGuid().ToString("N"));
    private readonly CancellationTokenSource _timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
    private readonly HttpListener _gateway = new();
    private readonly ConcurrentQueue<(string Method, string Path, JsonElement Document)> _requests = new();
    private readonly Task _responses;

    /// <summary>Starts a bounded loopback Gateway returning a query document with optional paging or a command acceptance.</summary>
    /// <param name="paging">Optional response paging metadata for queries.</param>
    /// <param name="nullDocument">Whether the query response document is null.</param>
    /// <param name="commandResponse">Whether to return a command acceptance with HTTP 202 instead of a query response with HTTP 200.</param>
    internal QueryCliHarness(string? paging = null, bool nullDocument = false, bool commandResponse = false)
    {
        _timeout.CancelAfter(TimeSpan.FromSeconds(15));
        try
        {
            Directory.CreateDirectory(_directory);
            using var portProbe = new TcpListener(IPAddress.Loopback, 0);
            portProbe.Start();
            int port = ((IPEndPoint)portProbe.LocalEndpoint).Port;
            portProbe.Stop();
            Url = $"http://127.0.0.1:{port}/";
            _gateway.Prefixes.Add(Url);
            _gateway.Start();
            string metadata = paging is null ? "" : ",\"metadata\":{\"paging\":" + paging + "}";
            string document = nullDocument ? "null" : "{\"items\":[]}";
            byte[] response = Encoding.UTF8.GetBytes(
                $$$"""{"correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK","payload":{{{document}}},"success":true{{{metadata}}}}""");
            if (commandResponse)
            {
                response = Encoding.UTF8.GetBytes("""{"correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK","messageId":"01J9MZHXT3RKM0VWXRXGSJDATK"}""");
            }
            _responses = RespondAsync(response, commandResponse ? 202 : 200);
        }
        catch
        {
            _gateway.Close();
            _timeout.Dispose();
            if (Directory.Exists(_directory))
            {
                Directory.Delete(_directory, recursive: true);
            }

            throw;
        }
    }

    /// <summary>Gets the loopback Gateway URL.</summary>
    internal string Url { get; }

    /// <summary>Gets the number of captured Gateway requests.</summary>
    internal int Calls => _requests.Count;

    /// <summary>Invokes the real CLI parser and restores all streams even on failure.</summary>
    internal async Task<(int Exit, string Output, string Error)> InvokeAsync(
        string[] arguments, bool withUrl = true, string? readOnlyEnvironment = null, TextReader? standardInput = null)
    {
        TextReader originalIn = Console.In;
        TextWriter originalOut = Console.Out;
        TextWriter originalError = Console.Error;
        using var input = new StringReader("stdin must not be read");
        using var output = new StringWriter();
        using var error = new StringWriter();
        try
        {
            Console.SetIn(standardInput ?? input);
            Console.SetOut(output);
            Console.SetError(error);
            var store = new ProfileStore(Path.Combine(_directory, "mcpcli.json"));
            Func<IReadOnlyList<Assembly>> manifest = () => [typeof(Lint.Module).Assembly, typeof(Routing.Module).Assembly, typeof(StringContracts.Module).Assembly];
            string[] invocation = withUrl ? [.. arguments, "--url", Url] : arguments;
            int exit = await new CliRunner(store, manifest, key => key == "EVENTSTORE_READ_ONLY" ? readOnlyEnvironment : null).Parse(invocation)
                .InvokeAsync(cancellationToken: _timeout.Token);
            return (exit, output.ToString(), error.ToString());
        }
        finally
        {
            Console.SetIn(originalIn);
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    /// <summary>Checks the sole POST's route and complete JSON request.</summary>
    internal void AssertRequest(string expected)
    {
        (string method, string path, JsonElement document) = _requests.ShouldHaveSingleItem();
        method.ShouldBe("POST");
        path.ShouldBe("/api/v1/queries");
        AssertJson(document.GetRawText(), expected);
    }

    /// <summary>Checks complete documents with type-preserving JSON equality.</summary>
    internal static void AssertJson(string actual, string expected)
    {
        using JsonDocument actualDocument = JsonDocument.Parse(actual);
        using JsonDocument expectedDocument = JsonDocument.Parse(expected);
        JsonElement.DeepEquals(actualDocument.RootElement, expectedDocument.RootElement).ShouldBeTrue(actual);
    }

    /// <summary>Checks preserved fixture warnings and optional HTTP diagnostics on stderr.</summary>
    internal static void AssertDiagnostics(string stderr)
    {
        string[] lines = stderr.Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        lines.Count(line => line.StartsWith("warn: Hexalith.McpCli.Core.Catalog.CatalogProvider", StringComparison.Ordinal)).ShouldBe(7);
        lines.Count(line => line.StartsWith("Catalog warning conflicting_value", StringComparison.Ordinal)).ShouldBe(5);
        lines.Count(line => line.StartsWith("Catalog warning redundant_value", StringComparison.Ordinal)).ShouldBe(2);
        int httpMessages = lines.Count(line => line.StartsWith("info: System.Net.Http.HttpClient.IEventStoreGatewayClient", StringComparison.Ordinal));
        httpMessages.ShouldBeOneOf(0, 4);
        lines.Length.ShouldBe(14 + httpMessages * 2);
    }

    /// <inheritdoc/>
    public async ValueTask DisposeAsync()
    {
        try
        {
            await _timeout.CancelAsync();
            _gateway.Stop();
            try
            {
                await _responses;
            }
            catch (Exception exception) when (exception is OperationCanceledException or HttpListenerException or ObjectDisposedException)
            {
            }
        }
        finally
        {
            _gateway.Close();
            _timeout.Dispose();
            Directory.Delete(_directory, recursive: true);
        }
    }

    private async Task RespondAsync(byte[] response, int statusCode)
    {
        while (!_timeout.IsCancellationRequested)
        {
            HttpListenerContext context = await _gateway.GetContextAsync().WaitAsync(_timeout.Token);
            using var reader = new StreamReader(context.Request.InputStream);
            string body = await reader.ReadToEndAsync(_timeout.Token);
            using JsonDocument request = JsonDocument.Parse(body);
            _requests.Enqueue((context.Request.HttpMethod, context.Request.Url!.AbsolutePath, request.RootElement.Clone()));
            context.Response.StatusCode = statusCode;
            context.Response.ContentType = "application/json";
            context.Response.ContentLength64 = response.Length;
            await context.Response.OutputStream.WriteAsync(response, _timeout.Token);
            context.Response.Close();
        }
    }
}

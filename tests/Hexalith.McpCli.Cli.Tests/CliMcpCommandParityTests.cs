using System.IO.Pipelines;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using ByteAether.Ulid;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Mcp;
using Hexalith.McpCli.Sample.Contracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Checks command submission parity through the real gateway HTTP client.</summary>
public sealed class CliMcpCommandParityTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
    private const string CorrelationId = "01J9MZHXT3RKM0VWXRXGSJDATK";
    private const string IdempotencyKey = "01J9MZHXT3RKM0VWXRXGSJDATM";

    /// <summary>Both heads submit equivalent envelopes and echo only a caller-supplied idempotency key.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task CommandDocumentsAndGatewayRequestsMatchAsync(bool withIdempotencyKey)
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-command-parity-" + Guid.NewGuid().ToString("N"));
        using var portProbe = new TcpListener(IPAddress.Loopback, 0);
        portProbe.Start();
        int port = ((IPEndPoint)portProbe.LocalEndpoint).Port;
        portProbe.Stop();
        string url = $"http://127.0.0.1:{port}/";
        using var gateway = new HttpListener();
        gateway.Prefixes.Add(url);
        gateway.Start();
        var captured = new List<JsonNode>();
        Task responses = Task.Run(async () =>
        {
            for (int index = 0; index < 2; index++)
            {
                HttpListenerContext request = await gateway.GetContextAsync();
                request.Request.HttpMethod.ShouldBe("POST");
                request.Request.Url!.AbsolutePath.ShouldBe("/api/v1/commands");
                using var reader = new StreamReader(request.Request.InputStream);
                JsonNode body = JsonNode.Parse(await reader.ReadToEndAsync())!;
                captured.Add(body);
                string responseJson = JsonSerializer.Serialize(new
                {
                    correlationId = body["correlationId"]!.GetValue<string>(),
                    messageId = body["messageId"]!.GetValue<string>(),
                    resultPayload = new { accepted = true },
                });
                byte[] response = Encoding.UTF8.GetBytes(responseJson);
                request.Response.StatusCode = 202;
                request.Response.ContentType = "application/json";
                request.Response.ContentLength64 = response.Length;
                await request.Response.OutputStream.WriteAsync(response);
                request.Response.Close();
            }
        }, timeout.Token);

        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            Func<IReadOnlyList<System.Reflection.Assembly>> manifest = () => [typeof(CreateItemCommand).Assembly];
            var settings = new ResolvedSettings(new Uri(url), null, "sample-tenant", null, false,
                new HashSet<string>(), "json", null, false, false, null, new Dictionary<string, string>());
            var services = new ServiceCollection();
            services.AddLogging();
            services.AddMcpCliCore(settings, manifest, _ => { });
            services.AddMcpCliMcpServer(settings);
            using ServiceProvider provider = services.BuildServiceProvider();
            McpServerOptions options = provider.GetRequiredService<IOptions<McpServerOptions>>().Value;
            var clientToServer = new Pipe();
            var serverToClient = new Pipe();
            await using var serverTransport = new StreamServerTransport(
                clientToServer.Reader.AsStream(), serverToClient.Writer.AsStream(), "command-parity-server");
            var clientTransport = new StreamClientTransport(
                clientToServer.Writer.AsStream(), serverToClient.Reader.AsStream());
            await using McpServer server = McpServer.Create(serverTransport, options,
                provider.GetRequiredService<ILoggerFactory>(), provider);
            Task serverTask = server.RunAsync(timeout.Token);
            await using McpClient client = await McpClient.CreateAsync(clientTransport,
                new McpClientOptions { ProtocolVersion = "2025-06-18" }, cancellationToken: timeout.Token);

            string payload = $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""";
            var cliArgs = new List<string>
            {
                "send", "sample.create-item", "--payload", payload, "--correlation-id", CorrelationId, "--url", url,
            };
            if (withIdempotencyKey)
            {
                cliArgs.AddRange(["--idempotency-key", IdempotencyKey]);
            }

            TextWriter originalOut = Console.Out;
            using var output = new StringWriter();
            try
            {
                Console.SetOut(output);
                int exit = await new CliRunner(store, manifest).InvokeAsync(cliArgs, TestContext.Current.CancellationToken);
                exit.ShouldBe(0);
            }
            finally
            {
                Console.SetOut(originalOut);
            }

            var arguments = new Dictionary<string, object?>
            {
                ["operation"] = "sample.create-item", ["payload"] = payload, ["correlationId"] = CorrelationId,
            };
            if (withIdempotencyKey)
            {
                arguments["idempotencyKey"] = IdempotencyKey;
            }

            CallToolResult mcp = await client.CallToolAsync("send_command", arguments, cancellationToken: timeout.Token);
            mcp.IsError.ShouldBe(false);
            JsonNode cliDocument = JsonNode.Parse(output.ToString())!;
            JsonNode mcpDocument = JsonNode.Parse(mcp.StructuredContent.ShouldNotBeNull().GetRawText())!;
            cliDocument["messageId"]!.GetValue<string>().ShouldNotBe(mcpDocument["messageId"]!.GetValue<string>());
            cliDocument["messageId"] = "<generated>";
            mcpDocument["messageId"] = "<generated>";
            JsonElement.DeepEquals(JsonSerializer.SerializeToElement(cliDocument), JsonSerializer.SerializeToElement(mcpDocument)).ShouldBeTrue();
            if (withIdempotencyKey)
            {
                cliDocument["idempotencyKey"]!.GetValue<string>().ShouldBe(IdempotencyKey);
            }
            else
            {
                cliDocument.AsObject().ContainsKey("idempotencyKey").ShouldBeFalse();
            }

            await responses.WaitAsync(timeout.Token);
            captured.Count.ShouldBe(2);
            captured[0]["messageId"] = "<generated>";
            captured[1]["messageId"] = "<generated>";
            JsonElement.DeepEquals(JsonSerializer.SerializeToElement(captured[0]), JsonSerializer.SerializeToElement(captured[1])).ShouldBeTrue();
            captured[0]["domain"]!.GetValue<string>().ShouldBe("sample");
            captured[0]["commandType"]!.GetValue<string>().ShouldBe("create-item");
            captured[0]["tenant"]!.GetValue<string>().ShouldBe("sample-tenant");
            captured[0]["correlationId"]!.GetValue<string>().ShouldBe(CorrelationId);

            timeout.Cancel();
            try
            {
                await serverTask;
            }
            catch (OperationCanceledException)
            {
            }
        }
        finally
        {
            gateway.Stop();
            if (Directory.Exists(directory))
            {
                Directory.Delete(directory, recursive: true);
            }
        }
    }

    /// <summary>Every CLI payload source sends one catalog-routed command and returns the canonical accepted document.</summary>
    [Theory]
    [InlineData("inline", false, false)]
    [InlineData("inline", false, true)]
    [InlineData("inline", true, false)]
    [InlineData("inline", true, true)]
    [InlineData("file", false, false)]
    [InlineData("file", false, true)]
    [InlineData("file", true, false)]
    [InlineData("file", true, true)]
    [InlineData("stdin", false, false)]
    [InlineData("stdin", false, true)]
    [InlineData("stdin", true, false)]
    [InlineData("stdin", true, true)]
    public async Task PayloadSourcesSubmitOnceAndReturnCanonicalResultAsync(
        string source, bool withIdempotencyKey, bool withResult)
    {
        const string returnedMessageId = "01J9MZHXT3RKM0VWXRXGSJDATN";
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(15));
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-send-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            using var portProbe = new TcpListener(IPAddress.Loopback, 0);
            portProbe.Start();
            int port = ((IPEndPoint)portProbe.LocalEndpoint).Port;
            portProbe.Stop();
            string url = $"http://127.0.0.1:{port}/";
            using var gateway = new HttpListener();
            gateway.Prefixes.Add(url);
            gateway.Start();
            int calls = 0;
            string? method = null;
            string? path = null;
            JsonNode? captured = null;
            Task response = Task.Run(async () =>
            {
                HttpListenerContext context = await gateway.GetContextAsync().WaitAsync(timeout.Token);
                Interlocked.Increment(ref calls);
                method = context.Request.HttpMethod;
                path = context.Request.Url!.AbsolutePath;
                using var reader = new StreamReader(context.Request.InputStream);
                captured = JsonNode.Parse(await reader.ReadToEndAsync(timeout.Token));
                var document = new JsonObject
                {
                    ["correlationId"] = captured!["correlationId"]!.GetValue<string>(),
                    ["messageId"] = returnedMessageId,
                };
                if (withResult)
                {
                    document["resultPayload"] = new JsonObject { ["accepted"] = true };
                }

                byte[] bytes = Encoding.UTF8.GetBytes(document.ToJsonString());
                context.Response.StatusCode = 202;
                context.Response.ContentType = "application/json";
                context.Response.ContentLength64 = bytes.Length;
                await context.Response.OutputStream.WriteAsync(bytes, timeout.Token);
                context.Response.Close();

                // Keep accepting briefly so a queued retry cannot escape the one-call assertion.
                Task deadline = Task.Delay(TimeSpan.FromMilliseconds(250), timeout.Token);
                while (!deadline.IsCompleted)
                {
                    Task<HttpListenerContext> pending = gateway.GetContextAsync();
                    Task completed = await Task.WhenAny(pending, deadline);
                    if (completed == deadline && !pending.IsCompletedSuccessfully)
                    {
                        gateway.Stop();
                        try
                        {
                            await pending;
                        }
                        catch (Exception exception) when (exception is HttpListenerException or ObjectDisposedException)
                        {
                        }

                        break;
                    }

                    HttpListenerContext extra = await pending;
                    Interlocked.Increment(ref calls);
                    extra.Response.StatusCode = 202;
                    extra.Response.Close();
                }

                timeout.Token.ThrowIfCancellationRequested();
            }, timeout.Token);

            TextReader originalIn = Console.In;
            TextWriter originalOut = Console.Out;
            TextWriter originalError = Console.Error;
            using var output = new StringWriter();
            using var error = new StringWriter();
            string payload = $$"""{"ItemId":"{{ItemId}}","Title":"Hello"}""";
            using var input = new StringReader(source == "stdin" ? payload : "stdin must not be read");
            bool testFailed = false;
            try
            {
                string argument = payload;
                if (source == "file")
                {
                    string file = Path.Combine(directory, "command.json");
                    await File.WriteAllTextAsync(file, payload, timeout.Token);
                    argument = "@" + file;
                }
                else if (source == "stdin")
                {
                    argument = "-";
                }

                List<string> arguments = ["send", "sample.create-item", "--payload", argument, "--url", url];
                if (withIdempotencyKey)
                {
                    arguments.AddRange(["--correlation-id", CorrelationId, "--idempotency-key", IdempotencyKey]);
                }

                var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
                Func<IReadOnlyList<System.Reflection.Assembly>> manifest = () => [typeof(CreateItemCommand).Assembly];
                Console.SetIn(input);
                Console.SetOut(output);
                Console.SetError(error);
                int exit = await new CliRunner(store, manifest, _ => null).InvokeAsync(arguments, timeout.Token);

                exit.ShouldBe(0, output.ToString() + error.ToString());
                await response.WaitAsync(timeout.Token);
                calls.ShouldBe(1);
                method.ShouldBe("POST");
                path.ShouldBe("/api/v1/commands");
                captured.ShouldNotBeNull();
                captured["domain"]!.GetValue<string>().ShouldBe("sample");
                captured["commandType"]!.GetValue<string>().ShouldBe("create-item");
                captured["tenant"]!.GetValue<string>().ShouldBe("sample-tenant");
                captured["aggregateId"]!.GetValue<string>().ShouldBe(ItemId);
                captured["payload"]!["ItemId"]!.GetValue<string>().ShouldBe(ItemId);
                captured["payload"]!["Title"]!.GetValue<string>().ShouldBe("Hello");
                string submittedMessageId = captured["messageId"]!.GetValue<string>();
                Ulid.TryParse(submittedMessageId, provider: null, out _).ShouldBeTrue();
                string submittedCorrelationId = withIdempotencyKey ? CorrelationId : submittedMessageId;
                captured["correlationId"]!.GetValue<string>().ShouldBe(submittedCorrelationId);
                if (withIdempotencyKey)
                {
                    captured["idempotencyKey"]!.GetValue<string>().ShouldBe(IdempotencyKey);
                }
                else
                {
                    captured.AsObject().ContainsKey("idempotencyKey").ShouldBeFalse();
                }

                using JsonDocument result = JsonDocument.Parse(output.ToString());
                JsonElement root = result.RootElement;
                root.GetProperty("operation").GetString().ShouldBe("sample.create-item");
                root.GetProperty("messageId").GetString().ShouldBe(returnedMessageId);
                root.GetProperty("correlationId").GetString().ShouldBe(submittedCorrelationId);
                root.GetProperty("tenant").GetString().ShouldBe("sample-tenant");
                root.GetProperty("aggregateId").GetString().ShouldBe(ItemId);
                root.GetProperty("status").GetString().ShouldBe("accepted");
                root.TryGetProperty("duplicate", out _).ShouldBeFalse();
                root.EnumerateObject().Count().ShouldBe(6 + (withIdempotencyKey ? 1 : 0) + (withResult ? 1 : 0));
                if (withIdempotencyKey)
                {
                    root.GetProperty("idempotencyKey").GetString().ShouldBe(IdempotencyKey);
                }
                else
                {
                    root.TryGetProperty("idempotencyKey", out _).ShouldBeFalse();
                }

                if (withResult)
                {
                    root.GetProperty("result").GetProperty("accepted").GetBoolean().ShouldBeTrue();
                }
                else
                {
                    root.TryGetProperty("result", out _).ShouldBeFalse();
                }
            }
            catch
            {
                testFailed = true;
                throw;
            }
            finally
            {
                Console.SetIn(originalIn);
                Console.SetOut(originalOut);
                Console.SetError(originalError);
                timeout.Cancel();
                gateway.Stop();
                try
                {
                    await response;
                }
                catch (Exception exception) when (exception is OperationCanceledException or HttpListenerException or ObjectDisposedException)
                {
                }
                catch when (testFailed)
                {
                    // Preserve the original assertion failure.
                }
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

}

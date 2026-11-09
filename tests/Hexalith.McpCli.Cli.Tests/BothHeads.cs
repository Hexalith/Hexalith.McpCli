using System.IO.Pipelines;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Settings;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>
/// Runs one call through the real CLI verb and through the real <c>mcp</c> verb's host, capturing every channel.
/// Both heads resolve settings, build the host and log to standard error exactly as the shipped tool does; only
/// the MCP transport is replaced by in-process pipes.
/// </summary>
internal static class BothHeads
{
    /// <summary>Invokes the CLI head with captured standard streams and an injected environment reader.</summary>
    /// <param name="store">The private profile store.</param>
    /// <param name="manifest">The Contracts manifest.</param>
    /// <param name="environment">The only environment values the runner may read.</param>
    /// <param name="arguments">The complete CLI arguments.</param>
    /// <returns>The exit code and captured channels.</returns>
    internal static Task<HeadResult> InvokeCliAsync(ProfileStore store, Func<IReadOnlyList<Assembly>> manifest,
        IReadOnlyDictionary<string, string?> environment, IReadOnlyList<string> arguments)
        => InvokeCliAsync(store, manifest, Reader(environment), arguments);

    /// <summary>Invokes the CLI head with captured standard streams and an environment reader.</summary>
    /// <param name="store">The private profile store.</param>
    /// <param name="manifest">The Contracts manifest.</param>
    /// <param name="readEnvironment">The only environment reader the runner may use.</param>
    /// <param name="arguments">The complete CLI arguments.</param>
    /// <returns>The exit code and captured channels.</returns>
    internal static async Task<HeadResult> InvokeCliAsync(ProfileStore store, Func<IReadOnlyList<Assembly>> manifest,
        Func<string, string?> readEnvironment, IReadOnlyList<string> arguments)
    {
        TextReader originalIn = Console.In;
        TextWriter originalOut = Console.Out;
        TextWriter originalError = Console.Error;
        using var input = new StringReader("stdin must not be read");
        using var output = new StringWriter();
        using var error = new StringWriter();
        try
        {
            Console.SetIn(input);
            Console.SetOut(output);
            Console.SetError(error);
            int exit = await new CliRunner(store, manifest, readEnvironment)
                .InvokeAsync(arguments, TestContext.Current.CancellationToken);
            return new HeadResult(exit, output.ToString(), error.ToString(), null);
        }
        finally
        {
            Console.SetIn(originalIn);
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    /// <summary>Starts the <c>mcp</c> verb with the given global options and calls one tool over in-process pipes.</summary>
    /// <param name="store">The private profile store.</param>
    /// <param name="manifest">The Contracts manifest.</param>
    /// <param name="environment">The only environment values the runner may read.</param>
    /// <param name="globals">Global options appended after <c>mcp --transport stdio</c>.</param>
    /// <param name="tool">The tool to call, or <see langword="null" /> to only start the host.</param>
    /// <param name="arguments">The tool arguments.</param>
    /// <param name="inspect">An optional check of the started host before any tool call.</param>
    /// <returns>The exit code, captured channels and tool result; the result is null when no tool was called.</returns>
    internal static Task<HeadResult> InvokeMcpAsync(ProfileStore store, Func<IReadOnlyList<Assembly>> manifest,
        IReadOnlyDictionary<string, string?> environment, IReadOnlyList<string> globals, string? tool,
        IReadOnlyDictionary<string, object?>? arguments = null, Action<IHost>? inspect = null)
        => InvokeMcpAsync(store, manifest, Reader(environment), globals, tool, arguments, inspect);

    /// <summary>Starts the <c>mcp</c> verb with an environment reader and calls one tool over in-process pipes.</summary>
    /// <param name="store">The private profile store.</param>
    /// <param name="manifest">The Contracts manifest.</param>
    /// <param name="readEnvironment">The only environment reader the runner may use.</param>
    /// <param name="globals">Global options appended after <c>mcp --transport stdio</c>.</param>
    /// <param name="tool">The tool to call, or <see langword="null" /> to only start the host.</param>
    /// <param name="arguments">The tool arguments.</param>
    /// <param name="inspect">An optional check of the started host before any tool call.</param>
    /// <returns>The exit code, captured channels and tool result; the result is null when no tool was called.</returns>
    internal static async Task<HeadResult> InvokeMcpAsync(ProfileStore store, Func<IReadOnlyList<Assembly>> manifest,
        Func<string, string?> readEnvironment, IReadOnlyList<string> globals, string? tool,
        IReadOnlyDictionary<string, object?>? arguments = null, Action<IHost>? inspect = null)
    {
        CallToolResult? result = null;
        async Task<int> ServeAsync(IHost host, CancellationToken cancellationToken)
        {
            inspect?.Invoke(host);
            if (tool is null)
            {
                return 0;
            }

            McpServerOptions options = host.Services.GetRequiredService<IOptions<McpServerOptions>>().Value;
            var clientToServer = new Pipe();
            var serverToClient = new Pipe();
            await using var serverTransport = new StreamServerTransport(
                clientToServer.Reader.AsStream(), serverToClient.Writer.AsStream(), "both-heads-server");
            var clientTransport = new StreamClientTransport(clientToServer.Writer.AsStream(), serverToClient.Reader.AsStream());
            using var serving = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            serving.CancelAfter(TimeSpan.FromSeconds(20));
            await using McpServer server = McpServer.Create(serverTransport, options,
                host.Services.GetRequiredService<ILoggerFactory>(), host.Services);
            Task serverTask = server.RunAsync(serving.Token);
            await using (McpClient client = await McpClient.CreateAsync(clientTransport,
                new McpClientOptions { ProtocolVersion = "2025-06-18" }, cancellationToken: serving.Token))
            {
                result = await client.CallToolAsync(tool, arguments ?? new Dictionary<string, object?>(),
                    cancellationToken: serving.Token);
            }

            await serving.CancelAsync();
            try
            {
                await serverTask;
            }
            catch (OperationCanceledException)
            {
            }

            return 0;
        }

        TextReader originalIn = Console.In;
        TextWriter originalOut = Console.Out;
        TextWriter originalError = Console.Error;
        using var input = new StringReader("stdin must not be read");
        using var output = new StringWriter();
        using var error = new StringWriter();
        try
        {
            Console.SetIn(input);
            Console.SetOut(output);
            Console.SetError(error);
            int exit = await new CliRunner(store, manifest, readEnvironment, ServeAsync)
                .InvokeAsync(["mcp", "--transport", "stdio", .. globals], TestContext.Current.CancellationToken);
            return new HeadResult(exit, output.ToString(), error.ToString(), result);
        }
        finally
        {
            Console.SetIn(originalIn);
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    /// <summary>Checks one head's complete public document and its channel placement.</summary>
    /// <param name="result">The head result.</param>
    /// <param name="expected">The complete expected JSON document.</param>
    /// <param name="isError">Whether the document is an error document.</param>
    /// <param name="mask">JSON object members replaced by a placeholder before comparison.</param>
    internal static void AssertDocument(HeadResult result, string expected, bool isError, params string[] mask)
    {
        if (result.Tool is null)
        {
            result.Exit.ShouldBe(isError ? 2 : 0, result.Output + result.Error);
            AssertJson(result.Output, expected, mask);
            return;
        }

        result.Exit.ShouldBe(0, result.Error);
        result.Output.ShouldBeEmpty();
        result.Tool.IsError.ShouldBe(isError);
        AssertJson(result.Tool.StructuredContent.ShouldNotBeNull().GetRawText(), expected, mask);
        AssertJson(result.Tool.Content.ShouldHaveSingleItem().ShouldBeOfType<TextContentBlock>().Text, expected, mask);
    }

    /// <summary>Checks complete documents with type-preserving JSON equality after masking generated members.</summary>
    /// <param name="actual">The actual JSON.</param>
    /// <param name="expected">The expected JSON.</param>
    /// <param name="mask">Top-level member names replaced by a placeholder in both documents.</param>
    internal static void AssertJson(string actual, string expected, params string[] mask)
    {
        JsonNode actualNode = JsonNode.Parse(actual).ShouldNotBeNull();
        JsonNode expectedNode = JsonNode.Parse(expected).ShouldNotBeNull();
        foreach (string member in mask)
        {
            if (actualNode is JsonObject actualObject && actualObject.ContainsKey(member))
            {
                actualObject[member] = "<masked>";
            }

            if (expectedNode is JsonObject expectedObject && expectedObject.ContainsKey(member))
            {
                expectedObject[member] = "<masked>";
            }
        }

        JsonElement.DeepEquals(JsonSerializer.SerializeToElement(actualNode), JsonSerializer.SerializeToElement(expectedNode))
            .ShouldBeTrue(actual);
    }

    /// <summary>Returns a reader that serves only the supplied environment values.</summary>
    /// <param name="environment">The environment values.</param>
    /// <returns>The reader.</returns>
    internal static Func<string, string?> Reader(IReadOnlyDictionary<string, string?> environment)
        => name => environment.TryGetValue(name, out string? value) ? value : null;
}

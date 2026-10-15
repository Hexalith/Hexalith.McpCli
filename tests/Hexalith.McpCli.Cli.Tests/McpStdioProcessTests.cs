using System.ComponentModel;
using System.Diagnostics;
using System.Text.Json;
using Hexalith.McpCli.Core.Settings;
using ModelContextProtocol;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Exercises the built MCP host as a child process over its actual standard streams.</summary>
public sealed class McpStdioProcessTests
{
    /// <summary>Both SDK revisions discover and call the fixed tools with profile or offline environment settings.</summary>
    [Theory]
    [InlineData("2025-06-18", "initialize", true)]
    [InlineData("2025-06-18", "initialize", false)]
    [InlineData("2026-07-28", "server/discover", false)]
    public async Task SdkClientDiscoversOverCleanStdioAsync(string version, string firstMethod, bool useProfile)
    {
        string directory = TemporaryDirectory();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(20));
        Process? child = null;
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var environment = new Dictionary<string, string>();
            if (useProfile)
            {
                store.Add("dev", new ConnectionProfile(Url: "https://profile.invalid", Format: "table"));
                store.Use("dev");
            }
            else
            {
                environment["EVENTSTORE_FORMAT"] = "table";
            }

            Process process = child = Start(directory, environment, "mcp", "--transport", "stdio");
            Task<string> standardError = process.StandardError.ReadToEndAsync(timeout.Token);
            var standardOutput = new RecordingReadStream(process.StandardOutput.BaseStream);
            var transport = new RecordingClientTransport(new StreamClientTransport(
                process.StandardInput.BaseStream, standardOutput));
            await using (McpClient client = await McpClient.CreateAsync(transport,
                new McpClientOptions { ProtocolVersion = version }, cancellationToken: timeout.Token))
            {
                transport.Methods[0].ShouldBe(firstMethod);
                client.NegotiatedProtocolVersion.ShouldBe(version);
                IList<McpClientTool> tools = await client.ListToolsAsync(cancellationToken: timeout.Token);
                tools.Select(tool => tool.Name).ShouldBe([
                    "list_modules", "list_operations", "describe_operation", "send_command", "run_query",
                ]);

                CallToolResult modules = await client.CallToolAsync("list_modules", new Dictionary<string, object?>(),
                    cancellationToken: timeout.Token);
                modules.IsError.ShouldBe(false);
                modules.StructuredContent.ShouldNotBeNull().GetProperty("modules")[0]
                    .GetProperty("name").GetString().ShouldBe("sample");
                CallToolResult description = await client.CallToolAsync("describe_operation",
                    new Dictionary<string, object?> { ["operation"] = "sample.get-item" },
                    cancellationToken: timeout.Token);
                JsonElement operation = description.StructuredContent.ShouldNotBeNull();
                operation.GetProperty("submittable").GetBoolean().ShouldBe(useProfile);
                if (useProfile)
                {
                    operation.TryGetProperty("reason", out _).ShouldBeFalse();
                }
                else
                {
                    operation.GetProperty("reason").GetString().ShouldBe("configuration_invalid");
                }

                CallToolResult failure = await client.CallToolAsync("describe_operation",
                    new Dictionary<string, object?> { ["operation"] = "sample.missing" },
                    cancellationToken: timeout.Token);
                failure.IsError.ShouldBe(true);
                JsonElement error = failure.StructuredContent.ShouldNotBeNull();
                error.GetProperty("error").GetProperty("code").GetString().ShouldBe("unknown_operation");
                using JsonDocument text = JsonDocument.Parse(failure.Content.Single()
                    .ShouldBeOfType<TextContentBlock>().Text);
                JsonElement.DeepEquals(text.RootElement, error).ShouldBeTrue();

                CallToolResult afterFailure = await client.CallToolAsync("list_modules", new Dictionary<string, object?>(),
                    cancellationToken: timeout.Token);
                afterFailure.IsError.ShouldBe(false);
                JsonElement.DeepEquals(afterFailure.StructuredContent.ShouldNotBeNull(),
                    modules.StructuredContent.Value).ShouldBeTrue();
            }

            process.StandardInput.Close();
            await process.WaitForExitAsync(timeout.Token);
            process.ExitCode.ShouldBe(0);
            await standardOutput.CopyToAsync(Stream.Null, timeout.Token);
            AssertProtocolOutput(standardOutput.Transcript);
            string diagnostic = await standardError;
            diagnostic.ShouldNotContain("\"error\": {");
            diagnostic.ShouldNotContain("unknown_operation");
            diagnostic.ShouldNotContain("MCP server failed.");
            diagnostic.ShouldNotContain("This result is emitted as JSON; no table view is defined.");
        }
        finally
        {
            await StopAsync(child);
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Explicit JSON format overrides inherited table format while read-only mode narrows only the tool list.</summary>
    [Fact]
    public async Task ExplicitJsonAndReadOnlyEnvironmentKeepProtocolOutputAsync()
    {
        string directory = TemporaryDirectory();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(20));
        Process? child = null;
        try
        {
            Process process = child = Start(directory, new Dictionary<string, string>
            {
                ["EVENTSTORE_FORMAT"] = "table",
                ["EVENTSTORE_READ_ONLY"] = "true",
            }, "mcp", "--format", "json");
            Task<string> standardError = process.StandardError.ReadToEndAsync(timeout.Token);
            var standardOutput = new RecordingReadStream(process.StandardOutput.BaseStream);
            var transport = new StreamClientTransport(process.StandardInput.BaseStream, standardOutput);
            await using (McpClient client = await McpClient.CreateAsync(transport,
                new McpClientOptions { ProtocolVersion = "2026-07-28" }, cancellationToken: timeout.Token))
            {
                IList<McpClientTool> tools = await client.ListToolsAsync(cancellationToken: timeout.Token);
                tools.Select(tool => tool.Name).ShouldBe([
                    "list_modules", "list_operations", "describe_operation", "run_query",
                ]);
            }

            process.StandardInput.Close();
            await process.WaitForExitAsync(timeout.Token);
            process.ExitCode.ShouldBe(0);
            await standardOutput.CopyToAsync(Stream.Null, timeout.Token);
            AssertProtocolOutput(standardOutput.Transcript);
            string diagnostic = await standardError;
            diagnostic.ShouldNotContain("\"error\": {");
            diagnostic.ShouldNotContain("This result is emitted as JSON; no table view is defined.");
        }
        finally
        {
            await StopAsync(child);
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Cleanup races, timeouts, and kill failures preserve the session exception and allow directory cleanup.</summary>
    [Theory]
    [InlineData("exited")]
    [InlineData("timeout")]
    [InlineData("kill")]
    public async Task CleanupFailurePreservesOriginalSessionFailureAsync(string scenario)
    {
        string directory = TemporaryDirectory();
        var sessionFailure = new FormatException("Original session failure.");
        Exception cleanupFailure = scenario switch
        {
            "exited" => new InvalidOperationException("Child already exited."),
            "timeout" => new OperationCanceledException("Cleanup timed out."),
            _ => new Win32Exception("Child could not be killed."),
        };
        using var child = new Process();
        async Task FailSessionAsync()
        {
            try
            {
                throw sessionFailure;
            }
            finally
            {
                await StopAsync(child, _ => Task.FromException(cleanupFailure));
                Directory.Delete(directory, recursive: true);
            }
        }

        try
        {
            FormatException actual = await Should.ThrowAsync<FormatException>(FailSessionAsync);
            actual.ShouldBeSameAs(sessionFailure);
            Directory.Exists(directory).ShouldBeFalse();
        }
        finally
        {
            if (Directory.Exists(directory))
            {
                Directory.Delete(directory, recursive: true);
            }
        }
    }

    /// <summary>Presentation flags win before settings or manifest access and leave the requested path untouched.</summary>
    [Theory]
    [InlineData(true, true, "format")]
    [InlineData(true, false, "format")]
    [InlineData(false, true, "output")]
    public async Task InvalidPresentationOptionsStopBeforeCatalogAsync(bool includeTable, bool includeOutput, string argument)
    {
        string directory = TemporaryDirectory();
        try
        {
            string path = Path.Combine(directory, "untouched.json");
            await File.WriteAllTextAsync(path, "sentinel", TestContext.Current.CancellationToken);
            string[] arguments = (includeTable, includeOutput) switch
            {
                (true, true) => ["mcp", "--format", "table", "--output", path],
                (true, false) => ["mcp", "--format", "table"],
                _ => ["mcp", "--output", path],
            };
            (int exit, string output, string error) = await RunAsync(directory, new Dictionary<string, string>
            {
                ["EVENTSTORE_URL"] = "not-a-url",
                ["MCPCLI_STDIO_CATALOG"] = "empty",
            }, arguments);
            exit.ShouldBe(2);
            output.ShouldBeEmpty();
            AssertStartupError(error, "invalid_arguments", argument);
            (await File.ReadAllTextAsync(path, TestContext.Current.CancellationToken)).ShouldBe("sentinel");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Settings, empty Catalog, and strict diagnostics fail before serving with no stdout bytes.</summary>
    [Theory]
    [InlineData("settings", "configuration_invalid")]
    [InlineData("empty", "catalog_empty")]
    [InlineData("diagnostic", "catalog_invalid")]
    public async Task StartupFailuresWriteOneStructuredErrorAsync(string scenario, string code)
    {
        string directory = TemporaryDirectory();
        try
        {
            var environment = new Dictionary<string, string>();
            string[] arguments = ["mcp"];
            if (scenario == "settings")
            {
                environment["EVENTSTORE_URL"] = "not-a-url";
            }
            else
            {
                environment["MCPCLI_STDIO_CATALOG"] = scenario;
                if (scenario == "diagnostic")
                {
                    arguments = ["mcp", "--strict"];
                }
            }

            (int exit, string output, string error) = await RunAsync(directory, environment, arguments);
            exit.ShouldBe(2);
            output.ShouldBeEmpty();
            AssertStartupError(error, code);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Only the last framing newline may produce an empty split segment.</summary>
    [Fact]
    public void ProtocolTranscriptRejectsExtraBlankLines()
    {
        const string message = "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{}}\n";
        AssertProtocolOutput(message);
        Should.Throw<ShouldAssertException>(() => AssertProtocolOutput(message + "\n"));
    }

    /// <summary>A protocol version alone is not a JSON-RPC message.</summary>
    [Fact]
    public void ProtocolTranscriptRejectsVersionOnlyObject()
        => Should.Throw<JsonException>(() => AssertProtocolOutput("{\"jsonrpc\":\"2.0\"}\n"));

    private static void AssertStartupError(string diagnostic, string code, string? argument = null)
    {
        string marker = "{" + Environment.NewLine + "  \"error\"";
        int start = diagnostic.IndexOf(marker, StringComparison.Ordinal);
        start.ShouldBeGreaterThanOrEqualTo(0);
        diagnostic.IndexOf(marker, start + marker.Length, StringComparison.Ordinal).ShouldBe(-1);
        using JsonDocument parsed = JsonDocument.Parse(diagnostic[start..]);
        JsonElement document = parsed.RootElement;
        document.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
        JsonElement error = document.GetProperty("error");
        error.GetProperty("code").GetString().ShouldBe(code);
        if (argument is not null)
        {
            error.GetProperty("argument").GetString().ShouldBe(argument);
        }
    }

    private static async Task<(int Exit, string Output, string Error)> RunAsync(
        string directory, IReadOnlyDictionary<string, string> environment, params string[] arguments)
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        Process? process = null;
        try
        {
            process = Start(directory, environment, arguments);
            process.StandardInput.Close();
            Task<string> output = process.StandardOutput.ReadToEndAsync(timeout.Token);
            Task<string> error = process.StandardError.ReadToEndAsync(timeout.Token);
            await process.WaitForExitAsync(timeout.Token);
            return (process.ExitCode, await output, await error);
        }
        finally
        {
            await StopAsync(process);
        }
    }

    private static void AssertProtocolOutput(string output)
    {
        output.ShouldNotBeEmpty();
        string messages = output.EndsWith('\n') ? output[..^1] : output;
        foreach (string line in messages.Split('\n'))
        {
            line.ShouldNotBeNullOrWhiteSpace();
            JsonRpcMessage message = JsonSerializer.Deserialize<JsonRpcMessage>(line, McpJsonUtilities.DefaultOptions)
                .ShouldNotBeNull();
            message.JsonRpc.ShouldBe("2.0");
        }
    }

    private static async Task StopAsync(Process? process, Func<Process, Task>? stopProcess = null)
    {
        if (process is null)
        {
            return;
        }

        try
        {
            await (stopProcess ?? StopProcessAsync)(process);
        }
        catch (Exception exception) when (exception is InvalidOperationException or OperationCanceledException or Win32Exception)
        {
            // Best-effort cleanup must preserve the original session or assertion failure.
        }
        finally
        {
            process.Dispose();
        }

        static async Task StopProcessAsync(Process child)
        {
            if (!child.HasExited)
            {
                child.Kill(entireProcessTree: true);
            }

            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(5));
            await child.WaitForExitAsync(timeout.Token);
        }
    }

    private static Process Start(string directory, IReadOnlyDictionary<string, string> environment, params string[] arguments)
    {
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string root = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../../"));
        string fixture = Path.Combine(root, "tests", "fixtures", "StdioHost", "bin", configuration, "net10.0",
            "Hexalith.McpCli.StdioHost.dll");
        File.Exists(fixture).ShouldBeTrue($"Missing fixture at {fixture}; base {AppContext.BaseDirectory}");
        var start = new ProcessStartInfo
        {
            FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        foreach (string name in start.Environment.Keys.Where(name => name.StartsWith("EVENTSTORE_", StringComparison.Ordinal)).ToArray())
        {
            start.Environment.Remove(name);
        }

        start.Environment.Remove("MCPCLI_STDIO_CATALOG");

        start.Environment["HOME"] = directory;
        start.Environment["USERPROFILE"] = directory;
        start.Environment["MCPCLI_STDIO_PROFILE_PATH"] = Path.Combine(directory, "mcpcli.json");
        foreach ((string name, string value) in environment)
        {
            start.Environment[name] = value;
        }

        start.ArgumentList.Add(fixture);
        foreach (string argument in arguments)
        {
            start.ArgumentList.Add(argument);
        }

        return Process.Start(start).ShouldNotBeNull();
    }

    private static string TemporaryDirectory()
    {
        string path = Path.Combine(Path.GetTempPath(), "mcpcli-stdio-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }
}

using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text.Json;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Executes the AppHost entry point and proves its launch guards precede resource creation.</summary>
public sealed class TopologyLaunchTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "mcpcli-launch-" + Guid.NewGuid().ToString("N"));

    /// <summary>Root membership is enforced by the executable entry point.</summary>
    [Fact]
    public async Task MissingDeclaredRootStopsLaunch()
    {
        string assembly = PrepareHost();
        string project = Path.Combine(_root, "references", "Hexalith.EventStore", "src", "Hexalith.EventStore", "Hexalith.EventStore.csproj");
        var result = await InvokeAsync(assembly, new string('k', 32), "[]");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal($"Required root checkout 'references/Hexalith.EventStore' is not declared in '{Path.Combine(_root, ".gitmodules")}'. Required project: '{project}'.{Environment.NewLine}", result.Stderr);
    }

    /// <summary>The executable rejects a weak key before invoking Dapr or creating resources.</summary>
    [Fact]
    public async Task WeakSigningKeyStopsLaunch()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, "short-private-test-key", "invalid snapshot: Dapr must not run");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal("Authentication:JwtBearer:SigningKey must contain at least 32 UTF-8 bytes for the Development test topology." + Environment.NewLine, result.Stderr);
    }

    /// <summary>The executable rejects an occupied requested identity before adding a resource.</summary>
    [Fact]
    public async Task ExistingApplicationStopsLaunch()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[{\"appId\":\"eventstore\"}]");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal("Conflicting Dapr application IDs: eventstore. The requested test topology cannot start alongside these applications." + Environment.NewLine, result.Stderr);
    }

    /// <summary>Malformed Dapr records use the executable's diagnostic boundary before resources start.</summary>
    [Theory]
    [InlineData("[{}]")]
    [InlineData("[null]")]
    [InlineData("[42]")]
    [InlineData("[{\"appId\":42}]")]
    [InlineData("[{\"appId\":null}]")]
    [InlineData("[{\"appId\":\"\"}]")]
    public async Task MalformedDaprSnapshotStopsLaunch(string snapshot)
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), snapshot);
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal("Cannot validate topology conflicts: Dapr entry 0 must be an object with a non-empty string 'appId'." + Environment.NewLine, result.Stderr);
    }

    /// <summary>A qualified preflight exits cleanly without starting its source projects.</summary>
    [Fact]
    public async Task ValidPreflightExitsBeforeResourceCreation()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]");
        Assert.Equal(0, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal(string.Empty, result.Stderr);
    }

    /// <summary>Configuration conversion failures stay inside the executable diagnostic boundary.</summary>
    [Theory]
    [InlineData("not-a-port")]
    [InlineData("2147483648")]
    public async Task InvalidPortConversionStopsLaunch(string port)
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", port);
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal($"Failed to convert configuration value '{port}' at 'Dapr:GatewayHttpPort' to type 'System.Int32'." + Environment.NewLine, result.Stderr);
    }

    /// <summary>The helper's minimum port is enforced before any resources start.</summary>
    [Fact]
    public async Task PrivilegedPortStopsLaunch()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", "1023");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal("Dapr:GatewayHttpPort must be between 1024 and 65535." + Environment.NewLine, result.Stderr);
    }

    /// <summary>The lower helper boundary passes with no launch when available.</summary>
    [Fact]
    public async Task MinimumPortPassesPreflight()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", "1024");
        Assert.Equal(0, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal(string.Empty, result.Stderr);
    }

    /// <summary>A genuinely occupied port remains bound throughout the subprocess check.</summary>
    [Fact]
    public async Task OccupiedPortStopsLaunch()
    {
        string assembly = PrepareHost();
        PrepareSources();
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", port.ToString(System.Globalization.CultureInfo.InvariantCulture));
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal($"Gateway Dapr HTTP port {port} is already in use; the test topology cannot start." + Environment.NewLine, result.Stderr);
    }

    /// <summary>Nonzero Dapr failure preserves a bounded captured diagnostic.</summary>
    [Theory]
    [InlineData("sidecar metadata is unavailable")]
    [InlineData(null)]
    public async Task FailedDaprListReportsBoundedStderr(string? detail)
    {
        string assembly = PrepareHost();
        PrepareSources();
        string error = detail ?? new string('x', 600);
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", daprExit: "7", daprError: error);
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal($"Topology conflict check 'dapr list --output json' exited 7. stderr: {(detail ?? new string('x', 512) + "...")}" + Environment.NewLine, result.Stderr);
    }

    /// <summary>Checks actual composed app/sidecar environments and shared configuration before startup.</summary>
    [Fact]
    public async Task ComposedResourcesKeepTokensAclAndGatewayContentRoot()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", inspect: true);
        Assert.Equal(0, result.ExitCode);
        Assert.Equal(string.Empty, result.Stderr);
        using JsonDocument document = JsonDocument.Parse(result.Stdout);
        string host = document.RootElement.GetProperty("appHostDirectory").GetString()!;
        JsonElement[] resources = document.RootElement.GetProperty("resources").EnumerateArray().ToArray();
        Assert.Equal(new[] { "eventstore", "tenants", "parties" }, resources.Select(resource => resource.GetProperty("name").GetString()));
        Assert.Equal(3, resources.Select(resource => resource.GetProperty("tokenHash").GetString()).Distinct(StringComparer.Ordinal).Count());
        foreach (JsonElement resource in resources)
        {
            Assert.Equal(64, resource.GetProperty("appTokenLength").GetInt32());
            Assert.Equal(64, resource.GetProperty("sidecarTokenLength").GetInt32());
            Assert.True(resource.GetProperty("tokensMatch").GetBoolean());
            Assert.Equal(Path.Combine(host, "DaprComponents", "accesscontrol.yaml"), resource.GetProperty("configuration").GetString());
            if (resource.GetProperty("name").GetString() == "eventstore")
                Assert.Equal(host, resource.GetProperty("contentRoot").GetString());
        }
    }

    private string PrepareHost()
    {
        string repository = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string output = Path.Combine(repository, "tests", "Hexalith.McpCli.AppHost", "bin", configuration, "net10.0");
        string target = Path.Combine(_root, "tests", "Hexalith.McpCli.AppHost", "bin", configuration, "net10.0");
        Directory.CreateDirectory(Path.Combine(_root, "src"));
        foreach (string source in Directory.EnumerateFiles(output, "*", SearchOption.AllDirectories))
        {
            string destination = Path.Combine(target, Path.GetRelativePath(output, source));
            Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
            File.Copy(source, destination);
        }

        return Path.Combine(target, "Hexalith.McpCli.AppHost.dll");
    }

    private void PrepareSources()
    {
        string[] modules = ["Hexalith.EventStore", "Hexalith.Tenants", "Hexalith.Parties"];
        File.WriteAllText(Path.Combine(_root, ".gitmodules"), string.Join('\n', modules.Select(module =>
            $"[submodule \"{module}\"]\n path = references/{module}")));
        foreach (string module in modules)
        {
            string checkout = Path.Combine(_root, "references", module);
            string directory = Path.Combine(checkout, "src", module);
            Directory.CreateDirectory(directory);
            File.WriteAllText(Path.Combine(directory, module + ".csproj"), "<Project />");
            File.WriteAllText(Path.Combine(directory, "Program.cs"), "");
            var start = new ProcessStartInfo("git") { RedirectStandardOutput = true, RedirectStandardError = true };
            foreach (string argument in new[] { "init", "--quiet", checkout }) start.ArgumentList.Add(argument);
            using Process git = Process.Start(start)!;
            git.WaitForExit();
            Assert.Equal(0, git.ExitCode);
        }
    }

    private async Task<(int ExitCode, string Stdout, string Stderr)> InvokeAsync(string assembly, string key, string snapshot, string? requestedPort = null, string? daprExit = null, string? daprError = null, bool inspect = false)
    {
        string repository = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string stub = Path.Combine(repository, "tests", "fixtures", "Topology.DaprStub", "bin", configuration, "net10.0");
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        var start = new ProcessStartInfo("dotnet")
        {
            WorkingDirectory = _root, RedirectStandardOutput = true, RedirectStandardError = true,
        };
        foreach (string argument in new[] { assembly, inspect ? "--Topology:InspectComposition=true" : "--Topology:PreflightOnly=true", $"--Authentication:JwtBearer:SigningKey={key}", $"--Dapr:GatewayHttpPort={requestedPort ?? port.ToString(System.Globalization.CultureInfo.InvariantCulture)}" })
            start.ArgumentList.Add(argument);
        start.Environment["PATH"] = stub + Path.PathSeparator + start.Environment["PATH"];
        start.Environment["MCPCLI_TEST_DAPR_SNAPSHOT"] = snapshot;
        start.Environment["MCPCLI_TEST_DAPR_EXIT"] = daprExit;
        start.Environment["MCPCLI_TEST_DAPR_ERROR"] = daprError;
        using Process process = Process.Start(start)!;
        Task<string> output = process.StandardOutput.ReadToEndAsync();
        Task<string> error = process.StandardError.ReadToEndAsync();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(20));
        try { await process.WaitForExitAsync(timeout.Token).ConfigureAwait(false); }
        finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
        return (process.ExitCode, await output.ConfigureAwait(false), await error.ConfigureAwait(false));
    }

    /// <inheritdoc/>
    public void Dispose() => Directory.Delete(_root, recursive: true);
}

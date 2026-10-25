using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text.Json;
using System.Security.Cryptography;
using System.Text;

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

    /// <summary>Non-JSON Dapr output is contained by the executable diagnostic boundary.</summary>
    [Fact]
    public async Task NonJsonDaprOutputStopsLaunch()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "not-json");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        string expected = Assert.ThrowsAny<JsonException>(() => JsonDocument.Parse("not-json" + Environment.NewLine)).Message;
        Assert.Equal(expected + Environment.NewLine, result.Stderr);
    }

    /// <summary>A missing Dapr executable reports one diagnostic without an unhandled stack trace.</summary>
    [Fact]
    public async Task MissingDaprExecutableStopsLaunch()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", missingDapr: true);
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        string expected = new System.ComponentModel.Win32Exception(2).Message;
        Assert.Equal($"An error occurred trying to start process 'dapr' with working directory '{_root}'. {expected}" + Environment.NewLine, result.Stderr);
    }

    /// <summary>Every route field is required even when the executable only runs preflight.</summary>
    [Theory]
    [InlineData("TenantId")]
    [InlineData("Domain")]
    [InlineData("Version")]
    [InlineData("AppId")]
    [InlineData("MethodName")]
    public async Task EmptyRouteFieldStopsPreflight(string field)
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", extraArgument: $"--Gateway:Routes:system|tenants|v1:{field}= ");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal($"Gateway:Routes:system|tenants|v1:{field} is required." + Environment.NewLine, result.Stderr);
    }

    /// <summary>A registration with an absent field fails before preflight can report success.</summary>
    [Fact]
    public async Task MissingRouteFieldStopsPreflight()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", extraArgument: "--Gateway:Routes:extra:TenantId=system");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal("Gateway:Routes:extra:Domain is required." + Environment.NewLine, result.Stderr);
    }

    /// <summary>An empty configured topic override is rejected before topology creation.</summary>
    [Fact]
    public async Task EmptyTopicOverrideStopsPreflight()
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", extraArgument: "--Gateway:TopicOverrides:global-administrators= ");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal("Gateway:TopicOverrides:global-administrators is required." + Environment.NewLine, result.Stderr);
    }

    /// <summary>Malformed topology flags use the same exact exit and channel contract as port errors.</summary>
    [Theory]
    [InlineData("PreflightOnly")]
    [InlineData("InspectComposition")]
    public async Task NonBooleanTopologyFlagStopsLaunch(string flag)
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", extraArgument: $"--Topology:{flag}=invalid");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal($"Failed to convert configuration value 'invalid' at 'Topology:{flag}' to type 'System.Boolean'." + Environment.NewLine, result.Stderr);
    }

    /// <summary>Direct live execution requires the same isolation sentinel as the fixture.</summary>
    [Theory]
    [InlineData(null)]
    [InlineData("0")]
    public async Task DirectLiveLaunchWithoutIsolationStopsBeforeDapr(string? sentinel)
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "Dapr must not run", extraArgument: "--Topology:PreflightOnly=false", isolationSentinel: sentinel);
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal("Live topology tests require tools/live-topology/run-isolated.py; refusing to use host Dapr or Redis." + Environment.NewLine, result.Stderr);
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

    /// <summary>The executable enforces authentic bootstrap before creating any resource.</summary>
    [Theory]
    [InlineData("--Tenants:BootstrapGlobalAdminEnabled=false")]
    [InlineData("--Tenants:BootstrapGlobalAdminUserId=")]
    [InlineData("--Tenants:BootstrapGlobalAdminUserId=another-administrator")]
    public async Task IncompleteBootstrapStopsPreflight(string argument)
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", extraArgument: argument);
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        Assert.Equal("Tenants bootstrap must be enabled for the test-owned administrator 'mcpcli-live-admin'." + Environment.NewLine, result.Stderr);
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

    /// <summary>Both external probes enforce their ten-second limit through the executable boundary.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task SlowExternalProbeStopsLaunchWithBoundedDiagnostic(bool slowGit)
    {
        string assembly = PrepareHost();
        PrepareSources();
        var result = await InvokeAsync(assembly, new string('k', 32), "[]", slowGit: slowGit, daprDelay: slowGit ? null : "60000");
        Assert.Equal(2, result.ExitCode);
        Assert.Equal(string.Empty, result.Stdout);
        string expected = slowGit
            ? $"Root checkout verification exceeded 10 seconds for '{Path.Combine(_root, "references", "Hexalith.EventStore")}'."
            : "Topology conflict check 'dapr list --output json' exceeded 10 seconds.";
        Assert.Equal(expected + Environment.NewLine, result.Stderr);
    }

    /// <summary>Checks actual composed app/sidecar environments and shared configuration before startup.</summary>
    [Fact]
    public async Task ComposedResourcesKeepTokensAclAndGatewayContentRoot()
    {
        string assembly = PrepareHost();
        PrepareSources();
        const string signingKey = "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk";
        using var available = new TcpListener(IPAddress.Loopback, 0);
        available.Start();
        string gatewayPort = ((IPEndPoint)available.LocalEndpoint).Port.ToString(System.Globalization.CultureInfo.InvariantCulture);
        available.Stop();
        var result = await InvokeAsync(assembly, signingKey, "[]", requestedPort: gatewayPort, inspect: true,
            extraArguments: ["--Dapr:PlacementHostAddress=127.0.0.1:6050", "--Dapr:SchedulerHostAddress=127.0.0.1:6060"]);
        Assert.True(result.ExitCode == 0, result.Stderr + result.Stdout);
        Assert.Equal(string.Empty, result.Stderr);
        Assert.DoesNotContain(signingKey, result.Stdout);
        using JsonDocument document = JsonDocument.Parse(result.Stdout);
        string host = document.RootElement.GetProperty("appHostDirectory").GetString()!;
        Assert.Equal(new[] { "eventstore-app-api-token", "parties-app-api-token", "tenants-app-api-token" },
            document.RootElement.GetProperty("appChannelTokenParameters").EnumerateArray().Select(parameter => parameter.GetString()));
        JsonElement[] resources = document.RootElement.GetProperty("resources").EnumerateArray().ToArray();
        Assert.Equal(new[] { "eventstore", "tenants", "parties" }, resources.Select(resource => resource.GetProperty("name").GetString()));
        Assert.Equal(3, resources.Select(resource => resource.GetProperty("tokenHash").GetString()).Distinct(StringComparer.Ordinal).Count());
        foreach (JsonElement resource in resources)
        {
            Assert.Equal(64, resource.GetProperty("appTokenLength").GetInt32());
            Assert.Equal(64, resource.GetProperty("sidecarTokenLength").GetInt32());
            Assert.True(resource.GetProperty("tokensMatch").GetBoolean());
            Assert.Equal(Path.Combine(host, "DaprComponents", "accesscontrol.yaml"), resource.GetProperty("configuration").GetString());
            Assert.Equal("127.0.0.1:6050", resource.GetProperty("placementHostAddress").GetString());
            Assert.Equal("127.0.0.1:6060", resource.GetProperty("schedulerHostAddress").GetString());
            Assert.Equal("Development", resource.GetProperty("aspnetcoreEnvironment").GetString());
            Assert.Equal("Development", resource.GetProperty("dotnetEnvironment").GetString());
            JsonElement components = resource.GetProperty("components");
            Assert.Equal(2, components.EnumerateObject().Count());
            Assert.Equal(Path.Combine(host, "DaprComponents", "statestore.yaml"), components.GetProperty("statestore").GetString());
            Assert.Equal(Path.Combine(host, "DaprComponents", "pubsub.yaml"), components.GetProperty("pubsub").GetString());
            JsonElement[] endpoints = resource.GetProperty("endpoints").EnumerateArray().ToArray();
            Assert.NotEmpty(endpoints);
            foreach (JsonElement endpoint in endpoints)
            {
                Assert.Equal(JsonValueKind.Null, endpoint.GetProperty("port").ValueKind);
                Assert.Equal(JsonValueKind.Null, endpoint.GetProperty("targetPort").ValueKind);
            }
            string module = resource.GetProperty("name").GetString() switch
            {
                "eventstore" => "Hexalith.EventStore",
                "tenants" => "Hexalith.Tenants",
                "parties" => "Hexalith.Parties",
                _ => throw new InvalidOperationException("Unexpected resource."),
            };
            Assert.Equal(Path.Combine(_root, "references", module, "src", module, module + ".csproj"), resource.GetProperty("projectPath").GetString());
            JsonElement authentication = resource.GetProperty("authentication");
            Assert.Equal(string.Empty, authentication.GetProperty("authority").GetString());
            Assert.Equal("mcpcli-live-tests", authentication.GetProperty("issuer").GetString());
            Assert.Equal("hexalith-eventstore", authentication.GetProperty("audience").GetString());
            Assert.Equal("hexalith-eventstore", authentication.GetProperty("validAudience").GetString());
            Assert.Equal("HS256", authentication.GetProperty("algorithm").GetString());
            Assert.Equal("false", authentication.GetProperty("requireHttpsMetadata").GetString());
            Assert.Equal(Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(signingKey))), authentication.GetProperty("signingKeyHash").GetString());
            JsonElement settings = resource.GetProperty("gatewaySettings");
            Assert.Equal(module == "Hexalith.Tenants" ? "True" : null, resource.GetProperty("bootstrapEnabled").GetString());
            Assert.Equal(module == "Hexalith.Tenants" ? "mcpcli-live-admin" : null, resource.GetProperty("bootstrapUserId").GetString());
            if (module == "Hexalith.EventStore")
            {
                Assert.Equal(host, resource.GetProperty("contentRoot").GetString());
                Assert.Equal(int.Parse(gatewayPort, System.Globalization.CultureInfo.InvariantCulture), resource.GetProperty("daprHttpPort").GetInt32());
                var expected = new Dictionary<string, string>();
                foreach ((string route, string tenant, string domain, string app) in new[]
                {
                    ("system|tenants|v1", "system", "tenants", "tenants"),
                    ("system|global-administrators|v1", "system", "global-administrators", "tenants"),
                    ("*|party|v1", "*", "party", "parties"),
                })
                {
                    foreach ((string field, string value) in new[] { ("TenantId", tenant), ("Domain", domain), ("Version", "v1"), ("AppId", app), ("MethodName", "process") })
                        expected.Add($"EventStore__DomainServices__Registrations__{route}__{field}", value);
                }
                expected.Add("EventStore__Publisher__TopicOverrides__global-administrators", "tenants.events");
                Assert.Equal(expected.OrderBy(pair => pair.Key, StringComparer.Ordinal),
                    settings.EnumerateObject().Select(property => new KeyValuePair<string, string>(property.Name, property.Value.GetString()!)).OrderBy(pair => pair.Key, StringComparer.Ordinal));
            }
            else Assert.Empty(settings.EnumerateObject());
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
            Directory.CreateDirectory(Path.Combine(directory, "Properties"));
            File.WriteAllText(Path.Combine(directory, "Properties", "launchSettings.json"),
                """{"profiles":{"test":{"commandName":"Project","applicationUrl":"http://localhost:6123;https://localhost:7123"}}}""");
            var start = new ProcessStartInfo("git") { RedirectStandardOutput = true, RedirectStandardError = true };
            foreach (string argument in new[] { "init", "--quiet", checkout }) start.ArgumentList.Add(argument);
            using Process git = Process.Start(start)!;
            git.WaitForExit();
            Assert.Equal(0, git.ExitCode);
        }
    }

    private async Task<(int ExitCode, string Stdout, string Stderr)> InvokeAsync(string assembly, string key, string snapshot, string? requestedPort = null, string? daprExit = null, string? daprError = null, bool inspect = false, bool missingDapr = false, string? extraArgument = null, string? isolationSentinel = null, bool slowGit = false, string? daprDelay = null, string[]? extraArguments = null)
    {
        string repository = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string stub = Path.Combine(repository, "tests", "fixtures", "Topology.DaprStub", "bin", configuration, "net10.0");
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        string dotnet = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")
            ?? Path.GetFullPath(Path.Combine(System.Runtime.InteropServices.RuntimeEnvironment.GetRuntimeDirectory(), "..", "..", "..", OperatingSystem.IsWindows() ? "dotnet.exe" : "dotnet"));
        var start = new ProcessStartInfo(dotnet)
        {
            WorkingDirectory = _root, RedirectStandardOutput = true, RedirectStandardError = true,
        };
        foreach (string argument in new[] { assembly, inspect ? "--Topology:InspectComposition=true" : "--Topology:PreflightOnly=true", $"--Authentication:JwtBearer:SigningKey={key}", $"--Dapr:GatewayHttpPort={requestedPort ?? port.ToString(System.Globalization.CultureInfo.InvariantCulture)}" })
            start.ArgumentList.Add(argument);
        if (extraArgument is not null) start.ArgumentList.Add(extraArgument);
        foreach (string argument in extraArguments ?? []) start.ArgumentList.Add(argument);
        if (missingDapr)
        {
            string onlyGit = Path.Combine(_root, "git-only");
            Directory.CreateDirectory(onlyGit);
            string gitName = OperatingSystem.IsWindows() ? "git.exe" : "git";
            string git = start.Environment["PATH"]!.Split(Path.PathSeparator)
                .Select(directory => Path.Combine(directory, gitName)).First(File.Exists);
            File.CreateSymbolicLink(Path.Combine(onlyGit, gitName), git);
            start.Environment["PATH"] = onlyGit;
        }
        else start.Environment["PATH"] = stub + Path.PathSeparator + start.Environment["PATH"];
        if (slowGit)
        {
            string shim = Path.Combine(_root, "slow-git");
            Directory.CreateDirectory(shim);
            foreach (string file in Directory.EnumerateFiles(stub)) File.Copy(file, Path.Combine(shim, Path.GetFileName(file)));
            string executableSuffix = OperatingSystem.IsWindows() ? ".exe" : string.Empty;
            File.Move(Path.Combine(shim, "dapr" + executableSuffix), Path.Combine(shim, "git" + executableSuffix));
            start.Environment["PATH"] = shim + Path.PathSeparator + start.Environment["PATH"];
            start.Environment["MCPCLI_TEST_GIT_DELAY_MS"] = "60000";
        }
        start.Environment["MCPCLI_ISOLATED_TOPOLOGY"] = isolationSentinel;
        start.Environment["MCPCLI_TEST_DAPR_SNAPSHOT"] = snapshot;
        start.Environment["MCPCLI_TEST_DAPR_EXIT"] = daprExit;
        start.Environment["MCPCLI_TEST_DAPR_ERROR"] = daprError;
        start.Environment["MCPCLI_TEST_DAPR_DELAY_MS"] = daprDelay;
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

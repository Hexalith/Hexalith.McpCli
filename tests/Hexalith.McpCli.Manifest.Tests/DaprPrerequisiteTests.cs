using System.Diagnostics;
using System.Net;
using System.Net.Sockets;

using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Passes only when missing Dapr prerequisites produce the platform's explicit skip result.</summary>
public sealed class DaprPrerequisiteTests
{
    /// <summary>Executes the actual smoke in a fresh process with an unreachable reserved control-plane port.</summary>
    [Theory]
    [InlineData("basic", "Basic platform Redis, placement or scheduler prerequisites are unavailable.")]
    [InlineData("sentry", "Dapr Sentry is not reachable on localhost:50001.")]
    [InlineData("cli", "Dapr CLI is not available on PATH.")]
    [InlineData("slow-cli", "Dapr CLI '--version' exceeded 3 seconds.")]
    [InlineData("DAPR_TRUST_ANCHORS", "Required mTLS credential DAPR_TRUST_ANCHORS is missing.")]
    [InlineData("DAPR_CERT_CHAIN", "Required mTLS credential DAPR_CERT_CHAIN is missing.")]
    [InlineData("DAPR_CERT_KEY", "Required mTLS credential DAPR_CERT_KEY is missing.")]
    [InlineData("NAMESPACE", "Required mTLS setting NAMESPACE must be 'default'.")]
    [InlineData("DAPR_CONTROLPLANE_NAMESPACE", "Required mTLS setting DAPR_CONTROLPLANE_NAMESPACE must be 'default'.")]
    [InlineData("DAPR_CONTROLPLANE_TRUST_DOMAIN", "Required mTLS setting DAPR_CONTROLPLANE_TRUST_DOMAIN must be 'public'.")]
    public async Task MissingDaprProducesStandardSkipAndNeverClaimsLiveSuccess(string missing, string? expected)
    {
        using var sentry = new TcpListener(IPAddress.Loopback, 50001);
        using var missingSentry = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        if (missing == "basic")
        {
            try { sentry.Start(); }
            catch (SocketException) { Assert.True(await TopologyPrerequisites.IsSentryReachableAsync(50001)); }
        }
        if (missing == "sentry")
        {
            try { missingSentry.Bind(new IPEndPoint(IPAddress.Loopback, 50001)); }
            catch (SocketException exception) when (exception.SocketErrorCode == SocketError.AddressAlreadyInUse)
            {
                if (!await TopologyPrerequisites.IsSentryReachableAsync(50001)) throw;
                Assert.Skip("Cannot test missing Sentry: localhost:50001 already has a listener.");
            }
        }
        using var unavailable = new Socket(Socket.OSSupportsIPv6 ? AddressFamily.InterNetworkV6 : AddressFamily.InterNetwork,
            SocketType.Stream, ProtocolType.Tcp);
        if (Socket.OSSupportsIPv6) unavailable.DualMode = true;
        unavailable.Bind(new IPEndPoint(Socket.OSSupportsIPv6 ? IPAddress.IPv6Any : IPAddress.Loopback, 0));
        // Binding without listening reserves the port while ensuring TCP probes fail.
        string port = ((IPEndPoint)unavailable.LocalEndPoint!).Port.ToString(System.Globalization.CultureInfo.InvariantCulture);
        string root = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string assembly = Path.Combine(root, "tests", "Hexalith.McpCli.Integration.Tests", "bin", configuration, "net10.0", "Hexalith.McpCli.Integration.Tests.dll");
        string dotnet = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")
            ?? (Path.GetFileNameWithoutExtension(Environment.ProcessPath) == "dotnet" ? Environment.ProcessPath
                : Path.GetFullPath(Path.Combine(System.Runtime.InteropServices.RuntimeEnvironment.GetRuntimeDirectory(), "..", "..", "..", OperatingSystem.IsWindows() ? "dotnet.exe" : "dotnet")))!;
        var start = new ProcessStartInfo(dotnet)
        {
            WorkingDirectory = root, RedirectStandardOutput = true, RedirectStandardError = true,
        };
        start.ArgumentList.Add(assembly);
        start.ArgumentList.Add("-method");
        start.ArgumentList.Add("*AuthenticatedQueryReturnsSuccessfulDocument");
        string stub = Path.Combine(root, "tests", "fixtures", "Topology.DaprStub", "bin", configuration, "net10.0");
        string cliPath = Path.Combine(Path.GetTempPath(), "mcpcli-git-only-" + Guid.NewGuid().ToString("N"));
        if (missing == "cli")
        {
            Directory.CreateDirectory(cliPath);
            string gitName = OperatingSystem.IsWindows() ? "git.exe" : "git";
            string git = start.Environment["PATH"]!.Split(Path.PathSeparator)
                .Select(directory => Path.Combine(directory, gitName)).First(File.Exists);
            File.CreateSymbolicLink(Path.Combine(cliPath, gitName), git);
        }
        try
        {
            start.Environment["PATH"] = missing == "cli" ? cliPath : stub + Path.PathSeparator + start.Environment["PATH"];
            foreach (string variable in new[] { "DAPR_TRUST_ANCHORS", "DAPR_CERT_CHAIN", "DAPR_CERT_KEY" })
                start.Environment[variable] = missing == variable ? string.Empty : "test-credential-not-used-to-start-resources";
            start.Environment["NAMESPACE"] = missing == "NAMESPACE" ? string.Empty : "default";
            start.Environment["DAPR_CONTROLPLANE_NAMESPACE"] = missing == "DAPR_CONTROLPLANE_NAMESPACE" ? string.Empty : "default";
            start.Environment["DAPR_CONTROLPLANE_TRUST_DOMAIN"] = missing == "DAPR_CONTROLPLANE_TRUST_DOMAIN" ? string.Empty : "public";
            start.Environment["MCPCLI_ISOLATED_TOPOLOGY"] = "1";
            start.Environment["MCPCLI_TEST_DAPR_DELAY_MS"] = missing == "slow-cli" ? "10000" : null;
            start.Environment["HEXALITH_EVENTSTORE_TEST_PLACEMENT_PORT"] = port;
            start.Environment["HEXALITH_EVENTSTORE_TEST_SCHEDULER_PORT"] = port;
            using Process process = Process.Start(start)!;
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(30));
            Task<string> output = process.StandardOutput.ReadToEndAsync(timeout.Token);
            Task<string> error = process.StandardError.ReadToEndAsync(timeout.Token);
            try { await process.WaitForExitAsync(timeout.Token).ConfigureAwait(true); }
            finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
            string stdout = await output.ConfigureAwait(true);
            Assert.Equal(0, process.ExitCode);
            Assert.Equal(string.Empty, await error.ConfigureAwait(true));
            Assert.Contains("DAPR integration prerequisites are unavailable. Run 'dapr init' and ensure Redis, placement, and scheduler are reachable.", stdout);
            Assert.Contains("Total: 1, Errors: 0, Failed: 0, Skipped: 1", stdout);
            Assert.DoesNotContain("Skipped: 0", stdout);
            if (expected is not null) Assert.Contains(expected, stdout);
            if (missing == "basic") Assert.DoesNotContain("Dapr Sentry", stdout);
        }
        finally
        {
            if (Directory.Exists(cliPath)) Directory.Delete(cliPath, recursive: true);
        }
    }
    /// <summary>An existing Sentry listener skips only the unavailable absence scenario.</summary>
    [Fact]
    public async Task ExistingSentryListenerDoesNotFailPrerequisiteRun()
    {
        using var listener = new TcpListener(IPAddress.Loopback, 50001);
        try { listener.Start(); }
        catch (SocketException exception) when (exception.SocketErrorCode == SocketError.AddressAlreadyInUse)
        {
            Assert.True(await TopologyPrerequisites.IsSentryReachableAsync(50001));
        }
        string dotnet = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")
            ?? Path.GetFullPath(Path.Combine(System.Runtime.InteropServices.RuntimeEnvironment.GetRuntimeDirectory(), "..", "..", "..", OperatingSystem.IsWindows() ? "dotnet.exe" : "dotnet"));
        var start = new ProcessStartInfo(dotnet) { RedirectStandardOutput = true, RedirectStandardError = true };
        start.ArgumentList.Add(typeof(DaprPrerequisiteTests).Assembly.Location);
        start.ArgumentList.Add("-method");
        start.ArgumentList.Add("*MissingDaprProducesStandardSkipAndNeverClaimsLiveSuccess");
        using Process process = Process.Start(start)!;
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(30));
        Task<string> output = process.StandardOutput.ReadToEndAsync(timeout.Token);
        Task<string> error = process.StandardError.ReadToEndAsync(timeout.Token);
        try { await process.WaitForExitAsync(timeout.Token); }
        finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
        string stdout = await output;
        Assert.Equal(0, process.ExitCode);
        Assert.Equal(string.Empty, await error);
        Assert.Contains("Cannot test missing Sentry: localhost:50001 already has a listener.", stdout);
        Assert.Contains("Total: 10, Errors: 0, Failed: 0, Skipped: 1", stdout);
    }

    /// <summary>Sentry transport probing accepts a real listener and rejects a reserved non-listening port.</summary>
    [Fact]
    public async Task SentryProbeUsesBoundedRealTransport()
    {
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int available = ((IPEndPoint)listener.LocalEndpoint).Port;
        Assert.Null(await TopologyPrerequisites.GetMtlsFailureAsync(Setting, available));
        using var unavailable = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        unavailable.Bind(new IPEndPoint(IPAddress.Loopback, 0));
        int missing = ((IPEndPoint)unavailable.LocalEndPoint!).Port;
        var elapsed = Stopwatch.StartNew();
        Assert.Equal($"Dapr Sentry is not reachable on localhost:{missing}.", await TopologyPrerequisites.GetMtlsFailureAsync(Setting, missing));
        Assert.True(elapsed.Elapsed < TimeSpan.FromSeconds(4));

        static string Setting(string variable) => variable switch
        {
            "NAMESPACE" or "DAPR_CONTROLPLANE_NAMESPACE" => "default",
            "DAPR_CONTROLPLANE_TRUST_DOMAIN" => "public",
            _ => "present-test-credential",
        };
    }

}

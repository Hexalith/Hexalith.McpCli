using System.Diagnostics;
using System.Net.Sockets;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Checks topology-specific tools and mTLS inputs without starting infrastructure.</summary>
internal static class TopologyPrerequisites
{
    /// <summary>The retained explicit missing-prerequisite diagnostic.</summary>
    internal const string SkipReason = "DAPR integration prerequisites are unavailable. Run 'dapr init' and ensure Redis, placement, and scheduler are reachable.";

    /// <summary>Requires Redis PONG and the selected placement/scheduler transports.</summary>
    internal static async Task<bool> BasicAvailableAsync()
    {
        try
        {
            using var redis = new TcpClient();
            using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(3));
            await redis.ConnectAsync("localhost", 6379, deadline.Token).ConfigureAwait(false);
            using NetworkStream stream = redis.GetStream();
            await stream.WriteAsync("*1\r\n$4\r\nPING\r\n"u8.ToArray(), deadline.Token).ConfigureAwait(false);
            byte[] pong = new byte[5];
            await stream.ReadExactlyAsync(pong, deadline.Token).ConfigureAwait(false);
            return pong.AsSpan().SequenceEqual("+PONG"u8)
                && await IsSentryReachableAsync(Hexalith.EventStore.Testing.Integration.DaprLocalEndpoints.PlacementPort).ConfigureAwait(false)
                && await IsSentryReachableAsync(Hexalith.EventStore.Testing.Integration.DaprLocalEndpoints.SchedulerPort).ConfigureAwait(false);
        }
        catch (Exception failure) when (failure is IOException or SocketException or OperationCanceledException)
        {
            return false;
        }
    }

    /// <summary>Retains the original topology owner's bounded Docker-health refusal.</summary>
    internal static async Task<bool> IsDockerHealthyAsync(string executable = "docker")
    {
        try
        {
            var start = new ProcessStartInfo(executable) { RedirectStandardOutput = true, RedirectStandardError = true };
            foreach (string argument in new[] { "info", "--format", "{{.ServerVersion}}" }) start.ArgumentList.Add(argument);
            using Process process = Process.Start(start)!;
            Task<string> output = process.StandardOutput.ReadToEndAsync();
            Task<string> error = process.StandardError.ReadToEndAsync();
            using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(5));
            try { await process.WaitForExitAsync(deadline.Token).ConfigureAwait(false); }
            catch (OperationCanceledException)
            {
                if (!process.HasExited) process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync().ConfigureAwait(false);
                return false;
            }
            _ = await output.ConfigureAwait(false);
            _ = await error.ConfigureAwait(false);
            return process.ExitCode == 0;
        }
        catch (System.ComponentModel.Win32Exception) { return false; }
    }

    /// <summary>Returns the first missing requirement with bounded CLI and Sentry probes.</summary>
    internal static async Task<string?> GetFailureAsync()
    {
        try
        {
            var start = new ProcessStartInfo("dapr") { RedirectStandardOutput = true, RedirectStandardError = true };
            start.ArgumentList.Add("--version");
            using Process process = Process.Start(start)!;
            Task<string> output = process.StandardOutput.ReadToEndAsync();
            Task<string> error = process.StandardError.ReadToEndAsync();
            using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(3));
            try { await process.WaitForExitAsync(deadline.Token).ConfigureAwait(false); }
            catch (OperationCanceledException)
            {
                process.Kill(entireProcessTree: true);
                return "Dapr CLI '--version' exceeded 3 seconds.";
            }
            if (process.ExitCode != 0 || !(await output.ConfigureAwait(false)).Contains("CLI version:", StringComparison.Ordinal))
                return "Dapr CLI '--version' did not report an installed CLI.";
            _ = await error.ConfigureAwait(false);
        }
        catch (System.ComponentModel.Win32Exception) { return "Dapr CLI is not available on PATH."; }

        return await GetMtlsFailureAsync(Environment.GetEnvironmentVariable, 50001).ConfigureAwait(false);
    }

    /// <summary>Checks required mTLS inputs and Sentry transport; the fixture supplies the fixed CLI endpoint.</summary>
    internal static async Task<string?> GetMtlsFailureAsync(Func<string, string?> environment, int sentryPort)
    {
        foreach (string variable in new[] { "DAPR_TRUST_ANCHORS", "DAPR_CERT_CHAIN", "DAPR_CERT_KEY" })
        {
            if (string.IsNullOrWhiteSpace(environment(variable)))
                return $"Required mTLS credential {variable} is missing.";
        }
        foreach ((string variable, string expected) in new[]
        {
            ("NAMESPACE", "default"), ("DAPR_CONTROLPLANE_NAMESPACE", "default"), ("DAPR_CONTROLPLANE_TRUST_DOMAIN", "public"),
        })
        {
            if (environment(variable) != expected)
                return $"Required mTLS setting {variable} must be '{expected}'.";
        }
        return await IsSentryReachableAsync(sentryPort).ConfigureAwait(false)
            ? null : $"Dapr Sentry is not reachable on localhost:{sentryPort}.";
    }

    /// <summary>Bounds the Sentry transport probe; the fixture always supplies the standard CLI port.</summary>
    internal static async Task<bool> IsSentryReachableAsync(int port)
    {
        try
        {
            using var client = new TcpClient();
            using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(3));
            await client.ConnectAsync("localhost", port, deadline.Token).ConfigureAwait(false);
            return true;
        }
        catch (Exception exception) when (exception is SocketException or OperationCanceledException)
        {
            return false;
        }
    }
}

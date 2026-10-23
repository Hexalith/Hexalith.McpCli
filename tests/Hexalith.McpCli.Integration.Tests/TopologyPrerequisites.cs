using System.Diagnostics;
using System.Net.Sockets;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Checks topology-specific tools and mTLS inputs without starting infrastructure.</summary>
internal static class TopologyPrerequisites
{
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

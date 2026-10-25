using System.Diagnostics;
using System.Text.Json;

namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Runs the single production CLI adapter with a private endpoint and short-lived identity.</summary>
internal static class LiveVectorProcess
{
    /// <summary>Executes one bounded runner and requires its new semantic receipt to pass.</summary>
    internal static async Task RunAsync(string root, string operation, string output, string host, string binding,
        Uri endpoint, string token, CancellationToken cancellationToken)
    {
        var start = new ProcessStartInfo("python3")
        {
            WorkingDirectory = root,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        foreach (string argument in new[] { Path.Combine(root, "tools", "live-topology", "run_live.py"), "--operation", operation, "--output", output, "--host", host })
            start.ArgumentList.Add(argument);
        start.Environment["MCPCLI_LIVE_URL"] = endpoint.ToString();
        start.Environment["MCPCLI_LIVE_TOKEN"] = token;
        start.Environment["MCPCLI_LIVE_BINDING"] = binding;
        string receipt = Path.Combine(output, "live-result.json");
        File.Delete(receipt);
        using Process process = Process.Start(start)!;
        Task<string> stdout = process.StandardOutput.ReadToEndAsync(cancellationToken);
        Task<string> stderr = process.StandardError.ReadToEndAsync(cancellationToken);
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        deadline.CancelAfter(TimeSpan.FromMinutes(8));
        try { await process.WaitForExitAsync(deadline.Token).ConfigureAwait(false); }
        finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
        string diagnostic = ((await stdout.ConfigureAwait(false)) + (await stderr.ConfigureAwait(false))).Replace(token, "<redacted>", StringComparison.Ordinal);
        Assert.True(process.ExitCode == 0, $"Live vector {operation} failed: {diagnostic}");
        Assert.True(File.Exists(receipt), $"Live vector {operation} omitted its receipt.");
        using JsonDocument result = JsonDocument.Parse(await File.ReadAllTextAsync(receipt, cancellationToken).ConfigureAwait(false));
        Assert.Equal(operation, result.RootElement.GetProperty("operation").GetString());
        Assert.Equal("passed", result.RootElement.GetProperty("result").GetString());
    }
}

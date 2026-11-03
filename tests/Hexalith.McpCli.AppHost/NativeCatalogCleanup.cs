using System.Runtime.ExceptionServices;

namespace Hexalith.McpCli.AppHost;

/// <summary>Attempts independent owned cleanup while preserving the original preparation or disposal failure.</summary>
internal static class NativeCatalogCleanup
{
    /// <summary>Runs every cleanup; a supplied failure remains the exception reported by its caller.</summary>
    internal static async ValueTask RunAsync(Exception? original, params Func<ValueTask>[] actions)
    {
        Exception? first = original;
        var failures = new List<string>();
        foreach (Func<ValueTask> action in actions)
        {
            try { await action().ConfigureAwait(false); }
            catch (Exception failure)
            {
                first ??= failure;
                if (failure.Data.Contains("CatalogOwnedProcessStillRunning")) first.Data["CatalogOwnedProcessStillRunning"] = true;
                failures.Add(NativeCatalogDiagnostics.Sanitize(failure.GetType().Name + ": " + failure.Message));
            }
        }
        if (first is not null && failures.Count > 0) first.Data["CatalogCleanupFailures"] = failures.ToArray();
        if (original is null && first is not null) ExceptionDispatchInfo.Capture(first).Throw();
    }
}

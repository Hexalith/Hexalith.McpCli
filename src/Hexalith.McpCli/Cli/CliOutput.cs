using System.Text.Json;
using System.Text;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Core.Settings;

namespace Hexalith.McpCli.Cli;

/// <summary>Writes one public Core document to the CLI output channel.</summary>
internal static class CliOutput
{
    /// <summary>Writes a result or error using the requested format and destination.</summary>
    /// <param name="document">The successful result document.</param>
    /// <param name="error">The failure document, when no result is available.</param>
    /// <param name="settings">The resolved presentation settings.</param>
    /// <param name="cancellationToken">Cancels file output.</param>
    /// <param name="tableHeader">The verb's tab-separated column names, or null for JSON-only results.</param>
    /// <param name="afterDestinationTruncated">Test seam for a recoverable failure after existing-file truncation.</param>
    /// <returns>Zero for a result or two for an error.</returns>
    internal static async Task<int> WriteAsync(object? document, OperationError? error,
        ResolvedSettings settings, CancellationToken cancellationToken, string? tableHeader = null,
        Func<CancellationToken, Task>? afterDestinationTruncated = null)
    {
        if (error is null && settings.Format == "table" && tableHeader is null)
        {
            await Console.Error.WriteLineAsync("This result is emitted as JSON; no table view is defined.").ConfigureAwait(false);
        }

        string output = error is not null
            ? JsonSerializer.Serialize(new { error }, McpCliJson.Result)
            : settings.Format == "table" && tableHeader is not null
                ? FormatTable(document!, tableHeader)
                : JsonSerializer.Serialize(document, McpCliJson.Result);
        if (error is null && settings.Output is not null)
        {
            await WriteResultFileAsync(settings.Output, output + Environment.NewLine, cancellationToken,
                afterDestinationTruncated).ConfigureAwait(false);
        }
        else
        {
            await Console.Out.WriteLineAsync(output).ConfigureAwait(false);
        }

        return error is null ? 0 : 2;
    }

    internal static Task<int> WriteErrorAsync(OperationError error, CancellationToken cancellationToken)
    {
        _ = cancellationToken;
        return WriteDirectErrorAsync(error);
    }

    private static async Task<int> WriteDirectErrorAsync(OperationError error)
    {
        await Console.Out.WriteLineAsync(JsonSerializer.Serialize(new { error }, McpCliJson.Result)).ConfigureAwait(false);
        return 2;
    }

    private static async Task WriteResultFileAsync(string path, string output, CancellationToken cancellationToken,
        Func<CancellationToken, Task>? afterDestinationTruncated)
    {
        path = ResolveFinalSymlink(path);
        bool existing = File.Exists(path);
        string stagingDirectory = existing ? Path.GetTempPath() : Path.GetDirectoryName(Path.GetFullPath(path))!;
        string stagedPath = Path.Combine(stagingDirectory, ".mcpcli-result-" + Guid.NewGuid().ToString("N"));
        string? backupPath = null;
        try
        {
            await using (FileStream stage = CreatePrivateTemporaryFile(stagedPath))
            {
                await stage.WriteAsync(Encoding.UTF8.GetBytes(output), cancellationToken).ConfigureAwait(false);
                await stage.FlushAsync(cancellationToken).ConfigureAwait(false);
            }

            if (!existing)
            {
                File.Move(stagedPath, path);
                return;
            }

            if (OperatingSystem.IsWindows())
            {
                if ((File.GetAttributes(path) & FileAttributes.ReadOnly) != 0)
                {
                    throw new UnauthorizedAccessException("The existing result file is read-only.");
                }
            }
            else
            {
                UnixFileMode mode = File.GetUnixFileMode(path);
                if ((mode & (UnixFileMode.UserRead | UnixFileMode.GroupRead | UnixFileMode.OtherRead)) == 0
                    || (mode & (UnixFileMode.UserWrite | UnixFileMode.GroupWrite | UnixFileMode.OtherWrite)) == 0)
                {
                    throw new UnauthorizedAccessException("The existing result file cannot be safely updated.");
                }
            }

            backupPath = Path.Combine(Path.GetTempPath(), ".mcpcli-backup-" + Guid.NewGuid().ToString("N"));
            await using FileStream destination = new(path, FileMode.Open, FileAccess.ReadWrite, FileShare.Read,
                bufferSize: 4096, useAsync: true);
            if (!destination.CanSeek)
            {
                throw new IOException("The existing result target is not seekable.");
            }

            await using (FileStream backup = CreatePrivateTemporaryFile(backupPath))
            {
                await destination.CopyToAsync(backup, cancellationToken).ConfigureAwait(false);
                await backup.FlushAsync(cancellationToken).ConfigureAwait(false);
            }

            try
            {
                destination.Position = 0;
                destination.SetLength(0);
                if (afterDestinationTruncated is not null)
                {
                    await afterDestinationTruncated(cancellationToken).ConfigureAwait(false);
                }

                await using FileStream stage = new(stagedPath, FileMode.Open, FileAccess.Read, FileShare.Read,
                    bufferSize: 4096, useAsync: true);
                await stage.CopyToAsync(destination, cancellationToken).ConfigureAwait(false);
                await destination.FlushAsync(cancellationToken).ConfigureAwait(false);
            }
            catch
            {
                await using FileStream backup = new(backupPath, FileMode.Open, FileAccess.Read, FileShare.Read,
                    bufferSize: 4096, useAsync: true);
                destination.Position = 0;
                destination.SetLength(0);
                await backup.CopyToAsync(destination, CancellationToken.None).ConfigureAwait(false);
                await destination.FlushAsync(CancellationToken.None).ConfigureAwait(false);
                throw;
            }
        }
        finally
        {
            // A failed cleanup after the destination changes must not turn a successful invocation into exit 2.
            TryDelete(stagedPath);
            if (backupPath is not null)
            {
                TryDelete(backupPath);
            }
        }
    }

    private static string ResolveFinalSymlink(string path)
    {
        string resolved = Path.GetFullPath(path);
        for (int depth = 0; depth < 32; depth++)
        {
            string? target = new FileInfo(resolved).LinkTarget;
            if (target is null)
            {
                return resolved;
            }

            resolved = Path.GetFullPath(Path.IsPathRooted(target)
                ? target : Path.Combine(Path.GetDirectoryName(resolved)!, target));
        }

        throw new IOException("The result path has too many symbolic links.");
    }

    private static FileStream CreatePrivateTemporaryFile(string path)
    {
        var options = new FileStreamOptions
        {
            Mode = FileMode.CreateNew,
            Access = FileAccess.ReadWrite,
            Share = FileShare.None,
            Options = FileOptions.Asynchronous,
        };
        if (!OperatingSystem.IsWindows())
        {
            options.UnixCreateMode = UnixFileMode.UserRead | UnixFileMode.UserWrite;
        }

        return new FileStream(path, options);
    }

    private static void TryDelete(string path)
    {
        try
        {
            File.Delete(path);
        }
        catch (IOException)
        {
        }
        catch (UnauthorizedAccessException)
        {
        }
    }

    private static string FormatTable(object document, string header)
    {
        if (document is ModulesDocument modules)
        {
            return header + Environment.NewLine
                + string.Join(Environment.NewLine, modules.Modules.Select(module
                    => $"{module.Name}\t{module.OperationCount}\t{module.Description}"));
        }

        if (document is OperationsDocument operations)
        {
            return header + Environment.NewLine
                + string.Join(Environment.NewLine, operations.Operations.Select(operation
                    => $"{operation.Name}\t{operation.Kind}\t{operation.Description}"));
        }

        JsonElement json = JsonSerializer.SerializeToElement(document, McpCliJson.Result);
        return header + Environment.NewLine + string.Join(Environment.NewLine,
            json.EnumerateObject().Select(property => property.Name + "\t" + JsonSerializer.Serialize(property.Value)));
    }
}

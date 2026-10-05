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
        Func<FileStream, CancellationToken, Task>? afterDestinationTruncated = null)
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
        Func<FileStream, CancellationToken, Task>? afterDestinationTruncated)
    {
        path = ResolveFinalSymlink(path);
        bool existing = File.Exists(path);
        if (existing)
        {
            await using FileStream target = new(path, FileMode.Open, FileAccess.Write, FileShare.ReadWrite,
                bufferSize: 0, useAsync: true);
            if (!target.CanSeek || IsSpecialDevicePath(path))
            {
                await target.WriteAsync(Encoding.UTF8.GetBytes(output), cancellationToken).ConfigureAwait(false);
                await target.FlushAsync(cancellationToken).ConfigureAwait(false);
                return;
            }
        }

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
                bufferSize: 0, useAsync: true);
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
                    await afterDestinationTruncated(destination, cancellationToken).ConfigureAwait(false);
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

    private static bool IsSpecialDevicePath(string path)
        => !OperatingSystem.IsWindows() && path.StartsWith("/dev/", StringComparison.Ordinal)
            && !path.StartsWith("/dev/shm/", StringComparison.Ordinal);

    private static string ResolveFinalSymlink(string path)
    {
        if (Path.EndsInDirectorySeparator(path))
        {
            throw new IOException("A result file path cannot end in a directory separator.");
        }

        // Resolve one component at a time: lexical normalization of ".." before following a
        // directory link can select a different file than the operating system would open.
        string absolute = Path.IsPathRooted(path) ? path : Path.Combine(Directory.GetCurrentDirectory(), path);
        string root = Path.GetPathRoot(absolute)!;
        string current = root;
        var remaining = new LinkedList<string>(SplitComponents(absolute[root.Length..]));
        int linkCount = 0;
        while (remaining.First is not null)
        {
            string part = remaining.First.Value;
            remaining.RemoveFirst();
            if (part is "." or "..")
            {
                if (!Directory.Exists(current))
                {
                    throw new IOException("A result path parent is not a directory.");
                }

                if (part == "..")
                {
                    current = Path.GetDirectoryName(Path.TrimEndingDirectorySeparator(current)) ?? root;
                }

                continue;
            }

            string candidate = Path.Combine(current, part);
            string? target = new FileInfo(candidate).LinkTarget;
            if (target is null)
            {
                if (remaining.Count != 0 && !Directory.Exists(candidate))
                {
                    throw new IOException("A result path parent is not a directory.");
                }

                current = candidate;
                continue;
            }

            if (++linkCount > 40)
            {
                throw new IOException("The result path has too many symbolic links.");
            }

            // Proc fd links may name a pipe, socket, or unlinked file. Keep the fd path so
            // the open handle remains the destination even when its old name is gone. A
            // device such as /dev/null keeps its own path so it is written directly.
            if (remaining.Count == 0 && IsProcFdPath(candidate))
            {
                return Path.IsPathRooted(target) && IsSpecialDevicePath(target) ? target : candidate;
            }

            bool directoryRequired = Path.EndsInDirectorySeparator(target);
            if (Path.IsPathRooted(target))
            {
                current = Path.GetPathRoot(target)!;
                target = target[current.Length..];
            }

            string[] targetParts = SplitComponents(target);
            if (directoryRequired)
            {
                remaining.AddFirst(".");
            }

            for (int index = targetParts.Length - 1; index >= 0; index--)
            {
                remaining.AddFirst(targetParts[index]);
            }
        }

        return current;
    }

    private static bool IsProcFdPath(string path)
    {
        if (!OperatingSystem.IsLinux() || !int.TryParse(Path.GetFileName(path), out _))
        {
            return false;
        }

        string? fdDirectory = Path.GetDirectoryName(path);
        string? processDirectory = fdDirectory is null ? null : Path.GetDirectoryName(fdDirectory);
        return Path.GetFileName(fdDirectory) == "fd" && processDirectory is not null
            && Path.GetDirectoryName(processDirectory) == "/proc"
            && int.TryParse(Path.GetFileName(processDirectory), out _);
    }

    private static string[] SplitComponents(string path)
        => path.Split([Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar], StringSplitOptions.RemoveEmptyEntries);

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

        FileStream stream = new(path, options);
        try
        {
            if (!OperatingSystem.IsWindows())
            {
                // UnixCreateMode is still masked by the process umask.
                File.SetUnixFileMode(path, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            }

            return stream;
        }
        catch
        {
            stream.Dispose();
            TryDelete(path);
            throw;
        }
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

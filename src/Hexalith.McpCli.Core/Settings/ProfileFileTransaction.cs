using System.Security.AccessControl;
using System.Security.Principal;
using System.Text.Json;
using System.Runtime.Versioning;

namespace Hexalith.McpCli.Core.Settings;

/// <summary>Serializes one profile mutation through an exclusive cross-process lock.</summary>
internal sealed class ProfileFileTransaction(string path)
{
    private static readonly UnixFileMode PrivateFileMode = UnixFileMode.UserRead | UnixFileMode.UserWrite;
    private static readonly UnixFileMode PrivateDirectoryMode = PrivateFileMode | UnixFileMode.UserExecute;

    internal ProfileSnapshot Apply(Func<ProfileSnapshot> read, Func<ProfileSnapshot, ProfileSnapshot> update,
        JsonSerializerOptions options)
    {
        RejectNonRegularFile(path);
        string directory = Path.GetDirectoryName(path) ?? throw new InvalidDataException("The profile path has no directory.");
        RejectSymlinkDirectory(directory);
        Directory.CreateDirectory(directory);
        RejectSymlinkDirectory(directory);
        RestrictDirectory(directory);
        string lockPath = path + ".lock";
        RejectNonRegularFile(lockPath);
        using FileStream mutex = AcquireLock(lockPath);
        ProfileSnapshot next = update(read());
        RejectNonRegularFile(path);
        if (File.Exists(path))
        {
            RestrictFile(path);
        }

        string temporaryPath = path + ".tmp-" + Guid.NewGuid().ToString("N");
        try
        {
            using (FileStream temporary = CreatePrivateFile(temporaryPath))
            {
                JsonSerializer.Serialize(temporary, next, options);
                temporary.Flush(flushToDisk: true);
            }

            RejectNonRegularFile(path);
            if (OperatingSystem.IsWindows() && File.Exists(path))
            {
                File.Replace(temporaryPath, path, null);
                RestrictFile(path);
            }
            else
            {
                File.Move(temporaryPath, path, overwrite: true);
            }

            return next;
        }
        finally
        {
            if (File.Exists(temporaryPath))
            {
                File.Delete(temporaryPath);
            }
        }
    }

    private static FileStream AcquireLock(string lockPath)
    {
        DateTime deadline = DateTime.UtcNow.AddSeconds(10);
        while (true)
        {
            try
            {
                FileStream stream = new(lockPath, LockOptions());
                try
                {
                    RestrictFile(lockPath);
                    return stream;
                }
                catch
                {
                    stream.Dispose();
                    throw;
                }
            }
            catch (IOException) when (DateTime.UtcNow < deadline)
            {
                Thread.Sleep(25);
            }
        }
    }

    private static FileStream CreatePrivateFile(string path)
    {
        var options = new FileStreamOptions
        {
            Mode = FileMode.CreateNew,
            Access = FileAccess.Write,
            Share = FileShare.None,
            Options = FileOptions.WriteThrough,
        };
        if (!OperatingSystem.IsWindows())
        {
            options.UnixCreateMode = PrivateFileMode;
        }

        FileStream stream = new(path, options);
        try
        {
            RestrictFile(path);
            return stream;
        }
        catch
        {
            stream.Dispose();
            throw;
        }
    }

    private static FileStreamOptions LockOptions()
    {
        var options = new FileStreamOptions
        {
            Mode = FileMode.OpenOrCreate,
            Access = FileAccess.ReadWrite,
            Share = FileShare.None,
        };
        if (!OperatingSystem.IsWindows())
        {
            options.UnixCreateMode = PrivateFileMode;
        }

        return options;
    }

    private static void RestrictDirectory(string path)
    {
        if (!OperatingSystem.IsWindows())
        {
            File.SetUnixFileMode(path, PrivateDirectoryMode);
            return;
        }

        var directory = new DirectoryInfo(path);
        var security = new DirectorySecurity();
        security.SetAccessRuleProtection(isProtected: true, preserveInheritance: false);
        AddCurrentUserAndSystem(security);
        directory.SetAccessControl(security);
    }

    private static void RestrictFile(string path)
    {
        if (!OperatingSystem.IsWindows())
        {
            File.SetUnixFileMode(path, PrivateFileMode);
            return;
        }

        var file = new FileInfo(path);
        var security = new FileSecurity();
        security.SetAccessRuleProtection(isProtected: true, preserveInheritance: false);
        AddCurrentUserAndSystem(security);
        file.SetAccessControl(security);
    }

    [SupportedOSPlatform("windows")]
    private static void AddCurrentUserAndSystem(FileSystemSecurity security)
    {
        SecurityIdentifier user = WindowsIdentity.GetCurrent().User
            ?? throw new InvalidDataException("The current Windows user has no security identifier.");
        SecurityIdentifier system = new(WellKnownSidType.LocalSystemSid, null);
        security.AddAccessRule(new FileSystemAccessRule(user, FileSystemRights.FullControl, AccessControlType.Allow));
        security.AddAccessRule(new FileSystemAccessRule(system, FileSystemRights.FullControl, AccessControlType.Allow));
    }

    private static void RejectNonRegularFile(string path)
    {
        var file = new FileInfo(path);
        if (file.LinkTarget is not null || Directory.Exists(path))
        {
            throw new InvalidDataException("The mcpcli profile or lock path must be a regular file, not a symbolic link.");
        }
    }

    private static void RejectSymlinkDirectory(string path)
    {
        if (new DirectoryInfo(path).LinkTarget is not null)
        {
            throw new InvalidDataException("The mcpcli profile directory cannot be a symbolic link.");
        }
    }
}

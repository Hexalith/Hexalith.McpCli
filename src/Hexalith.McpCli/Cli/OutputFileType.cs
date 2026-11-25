using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace Hexalith.McpCli.Cli;

/// <summary>Inspects a result target without opening a potentially blocking pipe.</summary>
internal static class OutputFileType
{
    private const int ReadAccess = 4;
    private const int WriteAccess = 2;

    /// <summary>Reads the destination type and identity from the same filesystem observation.</summary>
    internal static OutputTarget Inspect(string path)
    {
        if (!OperatingSystem.IsWindows())
        {
            byte[]? native = UnixStatus(path);
            return native is null ? new(OutputTargetKind.Missing) : UnixTarget(native);
        }

        // Open metadata only. Backup semantics lets us classify directories from that same handle.
        const uint BackupSemantics = 0x02000000;
        using SafeFileHandle handle = OpenWindowsFile(WindowsMetadataPath(path), 0, 7, 0, 3, BackupSemantics, 0);
        if (handle.IsInvalid)
        {
            return Marshal.GetLastPInvokeError() is 2 or 3 ? new(OutputTargetKind.Missing)
                : throw new IOException("The result target cannot be inspected.");
        }

        return Inspect(handle);
    }

    /// <summary>Identifies the open handle before any result bytes are transferred.</summary>
    internal static OutputTarget Inspect(SafeFileHandle handle)
    {
        if (!OperatingSystem.IsWindows())
        {
            return UnixTarget(UnixStatus(handle));
        }

        switch (GetFileType(handle))
        {
            case 1: // FILE_TYPE_DISK
                var file = WindowsIdentity(handle, out bool directory);
                return directory ? new(OutputTargetKind.Unsupported)
                    : new(OutputTargetKind.Regular, file.Volume, file.Low, file.High);
            case 2: // FILE_TYPE_CHAR
                return new(OutputTargetKind.Device);
            default:
                return new(OutputTargetKind.Unsupported);
        }
    }

    private static OutputTarget UnixTarget(byte[] native)
    {
        int offset = OperatingSystem.IsLinux() ? 28 : OperatingSystem.IsMacOS() ? 4 : 24;
        int kind = BitConverter.ToUInt16(native, offset) & 0xF000;
        OutputTargetKind type = kind switch
        {
            0x8000 => OutputTargetKind.Regular,
            0x1000 => OutputTargetKind.Pipe,
            0x2000 or 0x6000 => OutputTargetKind.Device,
            _ => OutputTargetKind.Unsupported,
        };
        var file = UnixIdentity(native);
        return new(type, file.Volume, file.Low, file.High);
    }

    /// <summary>Reads the identity and link count for a filesystem entry.</summary>
    internal static (ulong Volume, ulong Low, ulong High, ulong Links)? FileIdentity(string path)
    {
        if (!OperatingSystem.IsWindows())
        {
            byte[]? native = UnixStatus(path);
            return native is null ? null : UnixIdentity(native);
        }

        const uint ShareReadWriteDelete = 7;
        const uint OpenExisting = 3;
        using SafeFileHandle handle = OpenWindowsFile(WindowsMetadataPath(path), 0, ShareReadWriteDelete, 0, OpenExisting, 0, 0);
        if (handle.IsInvalid)
        {
            return Marshal.GetLastPInvokeError() is 2 or 3
                ? null : throw new IOException("The file identity cannot be opened.");
        }

        return FileIdentity(handle);
    }

    private static string WindowsMetadataPath(string path)
    {
        if (path.Length < 260 || path.StartsWith(@"\\?\", StringComparison.Ordinal)
            || path.StartsWith(@"\\.\", StringComparison.Ordinal))
        {
            return path;
        }

        string full = Path.GetFullPath(path);
        return full.StartsWith(@"\\", StringComparison.Ordinal) ? @"\\?\UNC\" + full[2..] : @"\\?\" + full;
    }

    /// <summary>Reads the opened file's identity before any truncation.</summary>
    internal static (ulong Volume, ulong Low, ulong High, ulong Links) FileIdentity(SafeFileHandle handle)
        => OperatingSystem.IsWindows() ? WindowsIdentity(handle, out _) : UnixIdentity(UnixStatus(handle));

    private static (ulong Volume, ulong Low, ulong High, ulong Links) WindowsIdentity(SafeFileHandle handle, out bool directory)
    {
        const int FileIdInfo = 18;
        byte[] information = new byte[52]; // BY_HANDLE_FILE_INFORMATION
        if (!GetFileInformationByHandle(handle, information))
        {
            throw new IOException("The file identity cannot be read.");
        }

        directory = (BitConverter.ToUInt32(information, 0) & (uint)FileAttributes.Directory) != 0;
        uint links = BitConverter.ToUInt32(information, 40);
        byte[] id = new byte[24]; // FILE_ID_INFO
        if (GetFileInformationByHandleEx(handle, FileIdInfo, id, (uint)id.Length))
        {
            return (BitConverter.ToUInt64(id, 0), BitConverter.ToUInt64(id, 8), BitConverter.ToUInt64(id, 16), links);
        }

        ulong index = (ulong)BitConverter.ToUInt32(information, 44) << 32 | BitConverter.ToUInt32(information, 48);
        return (BitConverter.ToUInt32(information, 28), index, 0, links);
    }

    private static byte[] UnixStatus(SafeFileHandle handle)
    {
        byte[] native = new byte[256];
        int status = OperatingSystem.IsLinux()
            ? Statx((int)handle.DangerousGetHandle(), string.Empty, 0x1000, 0x105, native)
            : OperatingSystem.IsMacOS() && RuntimeInformation.ProcessArchitecture == Architecture.X64
                ? MacFstatInode64(handle, native)
                : Fstat(handle, native);
        if (status != 0)
        {
            throw new IOException("The opened result file cannot be inspected.");
        }

        return native;
    }

    private static (ulong Volume, ulong Low, ulong High, ulong Links) UnixIdentity(byte[] native)
    {
        if (OperatingSystem.IsLinux())
        {
            ulong volume = (ulong)BitConverter.ToUInt32(native, 136) << 32 | BitConverter.ToUInt32(native, 140);
            return (volume, BitConverter.ToUInt64(native, 32), 0, BitConverter.ToUInt32(native, 16));
        }

        bool mac = OperatingSystem.IsMacOS();
        ulong device = mac ? BitConverter.ToUInt32(native, 0) : BitConverter.ToUInt64(native, 0);
        ulong links = mac ? BitConverter.ToUInt16(native, 6) : BitConverter.ToUInt64(native, 16);
        return (device, BitConverter.ToUInt64(native, 8), 0, links);
    }

    private static byte[]? UnixStatus(string path)
    {
        byte[] native = new byte[256];
        int result;
        if (OperatingSystem.IsLinux())
        {
            // statx has a fixed layout across Linux architectures and is exported by glibc 2.28+.
            result = Statx(-100, path, 0, 0x105, native); // STATX_TYPE | STATX_NLINK | STATX_INO
        }
        else if (OperatingSystem.IsMacOS() && RuntimeInformation.ProcessArchitecture == Architecture.X64)
        {
            result = MacStatInode64(path, native);
        }
        else if (OperatingSystem.IsMacOS() && RuntimeInformation.ProcessArchitecture == Architecture.Arm64)
        {
            result = Stat(path, native);
        }
        else if (OperatingSystem.IsFreeBSD() && RuntimeInformation.ProcessArchitecture == Architecture.X64)
        {
            result = Stat(path, native);
        }
        else
        {
            throw new PlatformNotSupportedException("Result target inspection is unavailable on this ABI.");
        }

        if (result != 0)
        {
            int error = Marshal.GetLastPInvokeError();
            return error is 2 or 20 ? null : throw new IOException("The result target cannot be inspected.");
        }

        return native;
    }

    /// <summary>Opens an existing destination without waiting if the path now names a FIFO.</summary>
    internal static SafeFileHandle OpenExisting(string path, FileAccess access, FileShare share)
    {
        if (OperatingSystem.IsWindows())
        {
            return File.OpenHandle(path, FileMode.Open, access, share);
        }

        int closeOnExec = OperatingSystem.IsLinux() ? 0x80000 : OperatingSystem.IsMacOS() ? 0x1000000 : 0x100000;
        int accessFlags = access == FileAccess.ReadWrite ? 2 : 1;
        int descriptor = Open(path, accessFlags | UnixNonBlocking | closeOnExec);
        if (descriptor < 0)
        {
            throw new IOException("The result destination could not be opened without blocking.");
        }

        return new SafeFileHandle((nint)descriptor, ownsHandle: true);
    }

    private static int UnixNonBlocking => OperatingSystem.IsLinux() ? 0x800 : 0x4;

    /// <summary>Restores ordinary write semantics for the verified device handle.</summary>
    internal static void AllowBlockingDeviceWrites(SafeFileHandle handle)
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }

        if (SetIsNonBlocking(handle, 0) != 0)
        {
            throw new IOException("The result device could not be configured for writing.");
        }
    }

    /// <summary>Honors existing exclusive file sharing locks on regular Unix results.</summary>
    internal static void RequireSharedAccess(SafeFileHandle handle)
    {
        if (OperatingSystem.IsWindows()
            || (AppContext.TryGetSwitch("System.IO.DisableFileLocking", out bool disabled) && disabled)
            || Environment.GetEnvironmentVariable("DOTNET_SYSTEM_IO_DISABLEFILELOCKING") is "1" or "true")
        {
            return;
        }

        const int SharedNonBlocking = 1 | 4;
        int wouldBlock = OperatingSystem.IsLinux() ? 11 : 35;
        if (Flock(handle, SharedNonBlocking) != 0 && Marshal.GetLastPInvokeError() == wouldBlock)
        {
            throw new IOException("The existing result file is exclusively locked.");
        }
    }

    /// <summary>Writes to a Unix pipe without waiting for available capacity.</summary>
    internal static void WriteStream(SafeFileHandle handle, byte[] bytes, CancellationToken cancellationToken)
    {
        int offset = 0;
        while (offset < bytes.Length)
        {
            cancellationToken.ThrowIfCancellationRequested();
            // FileStream waits for readiness after EAGAIN, even on a nonblocking descriptor.
            nint written = Write(handle, ref bytes[offset], (nuint)(bytes.Length - offset));
            if (written < 0 && Marshal.GetLastPInvokeError() == 4) // EINTR
            {
                continue;
            }

            if (written <= 0)
            {
                throw new IOException("The result destination could not accept the output without blocking.");
            }

            offset += (int)written;
        }
    }

    [DllImport("kernel32.dll", EntryPoint = "CreateFileW", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)]
    private static extern SafeFileHandle OpenWindowsFile(string file, uint access, uint share,
        nint security, uint disposition, uint flags, nint template);

    [DllImport("kernel32.dll", ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetFileInformationByHandle(SafeFileHandle handle, [Out] byte[] information);

    [DllImport("kernel32.dll", ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetFileInformationByHandleEx(SafeFileHandle handle, int informationClass,
        [Out] byte[] information, uint size);

    [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true)]
    private static extern uint GetFileType(SafeFileHandle handle);

    [DllImport("libc", EntryPoint = "open", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int Open(string path, int flags);

    [DllImport("libc", EntryPoint = "write", SetLastError = true)]
    private static extern nint Write(SafeFileHandle descriptor, ref byte buffer, nuint count);

    [DllImport("libc", EntryPoint = "flock", SetLastError = true)]
    private static extern int Flock(SafeFileHandle descriptor, int operation);

    // The runtime shim calls variadic fcntl with the correct ABI on Unix, including macOS arm64.
    [DllImport("System.Native", EntryPoint = "SystemNative_FcntlSetIsNonBlocking", SetLastError = true)]
    private static extern int SetIsNonBlocking(SafeFileHandle descriptor, int isNonBlocking);

    internal static void RequireAccess(string path, bool read)
    {
        int flags = read ? ReadAccess | WriteAccess : WriteAccess;
        int result = OperatingSystem.IsLinux()
            ? Faccessat(-100, path, flags, 0x200)
            : Access(path, flags);
        if (result != 0)
        {
            throw new UnauthorizedAccessException("The result target is not accessible for writing.");
        }
    }

    [DllImport("libc", EntryPoint = "statx", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int Statx(int directory, string path, int flags, int mask, [Out] byte[] buffer);

    [DllImport("libc", EntryPoint = "stat$INODE64", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int MacStatInode64(string path, [Out] byte[] buffer);

    [DllImport("libc", EntryPoint = "stat", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int Stat(string path, [Out] byte[] buffer);

    [DllImport("libc", EntryPoint = "fstat$INODE64", SetLastError = true)]
    private static extern int MacFstatInode64(SafeFileHandle file, [Out] byte[] buffer);

    [DllImport("libc", EntryPoint = "fstat", SetLastError = true)]
    private static extern int Fstat(SafeFileHandle file, [Out] byte[] buffer);

    [DllImport("libc", EntryPoint = "faccessat", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int Faccessat(int directory, string path, int mode, int flags);

    [DllImport("libc", EntryPoint = "access", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int Access(string path, int mode);
}

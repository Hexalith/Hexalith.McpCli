using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace Hexalith.McpCli.Cli;

/// <summary>Inspects a result target without opening a potentially blocking pipe.</summary>
internal static class OutputFileType
{
    private const int ReadAccess = 4;
    private const int WriteAccess = 2;

    internal static OutputTargetKind Inspect(string path)
    {
        if (OperatingSystem.IsWindows())
        {
            try
            {
                FileAttributes attributes = File.GetAttributes(path);
                return (attributes & FileAttributes.Directory) != 0 ? OutputTargetKind.Unsupported
                    : (attributes & FileAttributes.Device) != 0 ? OutputTargetKind.Device
                    : OutputTargetKind.Regular;
            }
            catch (FileNotFoundException)
            {
                return OutputTargetKind.Missing;
            }
            catch (DirectoryNotFoundException)
            {
                return OutputTargetKind.Missing;
            }
        }

        byte[]? native = UnixStatus(path, out int offset);
        if (native is null)
        {
            return OutputTargetKind.Missing;
        }

        int kind = BitConverter.ToUInt16(native, offset) & 0xF000;
        return kind switch
        {
            0x8000 => OutputTargetKind.Regular,
            0x1000 => OutputTargetKind.Pipe,
            0x2000 or 0x6000 => OutputTargetKind.Device,
            _ => OutputTargetKind.Unsupported,
        };
    }

    /// <summary>Reads the identity and link count for a filesystem entry.</summary>
    internal static (ulong Volume, ulong Low, ulong High, ulong Links)? FileIdentity(string path)
    {
        if (!OperatingSystem.IsWindows())
        {
            byte[]? native = UnixStatus(path, out _);
            return native is null ? null : UnixIdentity(native);
        }

        const uint ShareReadWriteDelete = 7;
        const uint OpenExisting = 3;
        using SafeFileHandle handle = OpenWindowsFile(path, 0, ShareReadWriteDelete, 0, OpenExisting, 0, 0);
        if (handle.IsInvalid)
        {
            return Marshal.GetLastPInvokeError() is 2 or 3
                ? null : throw new IOException("The file identity cannot be opened.");
        }

        return FileIdentity(handle);
    }

    /// <summary>Reads the opened file's identity before any truncation.</summary>
    internal static (ulong Volume, ulong Low, ulong High, ulong Links) FileIdentity(SafeFileHandle handle)
    {
        if (OperatingSystem.IsWindows())
        {
            const int FileIdInfo = 18;
            byte[] information = new byte[52]; // BY_HANDLE_FILE_INFORMATION
            if (!GetFileInformationByHandle(handle, information))
            {
                throw new IOException("The file identity cannot be read.");
            }

            uint links = BitConverter.ToUInt32(information, 40);
            byte[] id = new byte[24]; // FILE_ID_INFO
            if (GetFileInformationByHandleEx(handle, FileIdInfo, id, (uint)id.Length))
            {
                return (BitConverter.ToUInt64(id, 0), BitConverter.ToUInt64(id, 8), BitConverter.ToUInt64(id, 16), links);
            }

            ulong index = (ulong)BitConverter.ToUInt32(information, 44) << 32 | BitConverter.ToUInt32(information, 48);
            return (BitConverter.ToUInt32(information, 28), index, 0, links);
        }

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

        return UnixIdentity(native);
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

    private static byte[]? UnixStatus(string path, out int offset)
    {
        byte[] native = new byte[256];
        int result;
        if (OperatingSystem.IsLinux())
        {
            // statx has a fixed layout across Linux architectures and is exported by glibc 2.28+.
            result = Statx(-100, path, 0, 0x105, native); // STATX_TYPE | STATX_NLINK | STATX_INO
            offset = 28;
        }
        else if (OperatingSystem.IsMacOS() && RuntimeInformation.ProcessArchitecture == Architecture.X64)
        {
            result = MacStatInode64(path, native);
            offset = 4;
        }
        else if (OperatingSystem.IsMacOS() && RuntimeInformation.ProcessArchitecture == Architecture.Arm64)
        {
            result = Stat(path, native);
            offset = 4;
        }
        else if (OperatingSystem.IsFreeBSD() && RuntimeInformation.ProcessArchitecture == Architecture.X64)
        {
            result = Stat(path, native);
            offset = 24;
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

    /// <summary>Writes to a Unix pipe without waiting for a reader or available capacity.</summary>
    internal static void WritePipe(string path, byte[] bytes, CancellationToken cancellationToken)
    {
        // This method is reached only for a native Unix FIFO classification.
        int nonBlocking = OperatingSystem.IsLinux() ? 0x800 : 0x4;
        int closeOnExec = OperatingSystem.IsLinux() ? 0x80000 : OperatingSystem.IsMacOS() ? 0x1000000 : 0x100000;
        int descriptor = Open(path, 1 | nonBlocking | closeOnExec);
        if (descriptor < 0)
        {
            throw new IOException("The result pipe could not be opened without blocking.");
        }

        using var handle = new SafeFileHandle((nint)descriptor, ownsHandle: true);
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
                throw new IOException("The result pipe could not accept the output without blocking.");
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

    [DllImport("libc", EntryPoint = "open", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int Open(string path, int flags);

    [DllImport("libc", EntryPoint = "write", SetLastError = true)]
    private static extern nint Write(SafeFileHandle descriptor, ref byte buffer, nuint count);

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

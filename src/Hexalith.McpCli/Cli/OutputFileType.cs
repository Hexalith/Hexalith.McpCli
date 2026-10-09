using System.Runtime.InteropServices;

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

        byte[] native = new byte[256];
        int offset;
        int result;
        if (OperatingSystem.IsLinux())
        {
            // statx has a fixed layout across Linux architectures and is exported by glibc 2.28+.
            result = Statx(-100, path, 0, 1, native);
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
            return error is 2 or 20 ? OutputTargetKind.Missing
                : throw new IOException("The result target cannot be inspected.");
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

    [DllImport("libc", EntryPoint = "faccessat", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int Faccessat(int directory, string path, int mode, int flags);

    [DllImport("libc", EntryPoint = "access", SetLastError = true, CharSet = CharSet.Ansi)]
    private static extern int Access(string path, int mode);
}

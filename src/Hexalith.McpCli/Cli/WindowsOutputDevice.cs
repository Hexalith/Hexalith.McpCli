using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace Hexalith.McpCli.Cli;

/// <summary>Opens Windows null and console destinations without treating them as filesystem paths.</summary>
internal static class WindowsOutputDevice
{
    /// <summary>Recognizes bare device names and their explicit Win32 device paths.</summary>
    internal static string? Resolve(string path)
    {
        if (!OperatingSystem.IsWindows())
        {
            return null;
        }

        return path.ToUpperInvariant() switch
        {
            "NUL" or @"\\.\NUL" => @"\\.\NUL",
            "CON" or "CONOUT$" or @"\\.\CON" or @"\\.\CONOUT$" => "CONOUT$",
            _ => null,
        };
    }

    /// <summary>Checks that a recognized device can be opened for output.</summary>
    internal static void Probe(string device)
    {
        using SafeFileHandle handle = Open(device);
    }

    /// <summary>Writes result bytes to NUL or Unicode text to the active console.</summary>
    internal static void Write(string device, string output, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        using SafeFileHandle handle = Open(device);
        if (device == "CONOUT$")
        {
            for (int offset = 0; offset < output.Length;)
            {
                cancellationToken.ThrowIfCancellationRequested();
                int length = Math.Min(4096, output.Length - offset);
                if (offset + length < output.Length && char.IsHighSurrogate(output[offset + length - 1]))
                {
                    length--;
                }

                if (!WriteConsole(handle, output.Substring(offset, length), (uint)length, out uint written, 0)
                    || written == 0)
                {
                    throw new IOException("The console could not accept the result.");
                }

                offset += (int)written;
            }

            return;
        }

        byte[] bytes = Encoding.UTF8.GetBytes(output);
        if (!WriteFile(handle, bytes, (uint)bytes.Length, out uint count, 0) || count != bytes.Length)
        {
            throw new IOException("The null device could not accept the result.");
        }
    }

    private static SafeFileHandle Open(string device)
    {
        const uint GenericWrite = 0x40000000;
        const uint ShareReadWrite = 3;
        const uint OpenExisting = 3;
        SafeFileHandle handle = CreateFile(device, GenericWrite, ShareReadWrite, 0, OpenExisting, 0, 0);
        if (handle.IsInvalid)
        {
            handle.Dispose();
            throw new IOException("The Windows result device cannot be opened.");
        }

        return handle;
    }

    [DllImport("kernel32.dll", EntryPoint = "CreateFileW", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern SafeFileHandle CreateFile(string file, uint access, uint share,
        nint security, uint disposition, uint flags, nint template);

    [DllImport("kernel32.dll", EntryPoint = "WriteConsoleW", CharSet = CharSet.Unicode, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool WriteConsole(SafeFileHandle handle, string text, uint length, out uint written, nint reserved);

    [DllImport("kernel32.dll", ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool WriteFile(SafeFileHandle handle, byte[] bytes, uint length, out uint written, nint overlapped);
}

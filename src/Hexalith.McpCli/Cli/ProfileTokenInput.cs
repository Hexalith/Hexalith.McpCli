using System.Text;

namespace Hexalith.McpCli.Cli;

/// <summary>Reads one credential without making it part of the command line.</summary>
internal static class ProfileTokenInput
{
    private const int MaximumLength = 16_384;

    /// <summary>Reads a nonblank token using the explicitly chosen input mode.</summary>
    internal static async Task<string> ReadAsync(string mode, CancellationToken cancellationToken)
    {
        string value = mode switch
        {
            "prompt" => await ReadTerminalAsync(cancellationToken).ConfigureAwait(false),
            "stdin" => await ReadRedirectedAsync(cancellationToken).ConfigureAwait(false),
            _ => throw new InvalidDataException("Token input must be prompt or stdin."),
        };

        if (string.IsNullOrWhiteSpace(value) || value.Any(char.IsControl))
        {
            throw new InvalidDataException("Token input must contain one nonblank line without control characters.");
        }

        return value;
    }

    private static async Task<string> ReadRedirectedAsync(CancellationToken cancellationToken)
    {
        if (!Console.IsInputRedirected)
        {
            throw new InvalidDataException("Stdin token input requires redirected standard input.");
        }

        using var reader = new StreamReader(Console.OpenStandardInput(), new UTF8Encoding(false, true),
            detectEncodingFromByteOrderMarks: false);
        var value = new StringBuilder();
        var character = new char[1];
        try
        {
            while (await reader.ReadAsync(character.AsMemory(), cancellationToken).ConfigureAwait(false) != 0)
            {
                if (character[0] == '\r')
                {
                    if (await reader.ReadAsync(character.AsMemory(), cancellationToken).ConfigureAwait(false) == 0
                        || character[0] != '\n')
                    {
                        throw new InvalidDataException("Token input must contain one nonblank line without control characters.");
                    }
                }

                if (character[0] == '\n')
                {
                    break;
                }

                Append(value, character[0]);
            }
        }
        catch (DecoderFallbackException)
        {
            throw new InvalidDataException("Stdin token input must use UTF-8.");
        }

        return value.ToString();
    }

    private static async Task<string> ReadTerminalAsync(CancellationToken cancellationToken)
    {
        if (Console.IsInputRedirected)
        {
            throw new InvalidDataException("A token prompt requires an interactive terminal.");
        }

        var value = new StringBuilder();
        bool previous = Console.TreatControlCAsInput;
        Console.TreatControlCAsInput = true;
        try
        {
            await Console.Error.WriteAsync("Token: ").ConfigureAwait(false);
            while (true)
            {
                cancellationToken.ThrowIfCancellationRequested();
                if (!Console.KeyAvailable)
                {
                    await Task.Delay(25, cancellationToken).ConfigureAwait(false);
                    continue;
                }

                ConsoleKeyInfo key = Console.ReadKey(intercept: true);
                switch (key.KeyChar)
                {
                    case '\r' or '\n':
                        return value.ToString();
                    case '\u0003' or '\u0004' or '\u001b':
                        throw new InvalidDataException("Token input was cancelled.");
                    case '\b':
                        if (value.Length > 0)
                        {
                            value.Length--;
                        }

                        break;
                    case not '\0':
                        Append(value, key.KeyChar);
                        break;
                }
            }
        }
        finally
        {
            Console.TreatControlCAsInput = previous;
            await Console.Error.WriteLineAsync().ConfigureAwait(false);
        }
    }

    private static void Append(StringBuilder value, char character)
    {
        if (value.Length == MaximumLength)
        {
            throw new InvalidDataException("Token input exceeds 16384 characters.");
        }

        value.Append(character);
    }
}

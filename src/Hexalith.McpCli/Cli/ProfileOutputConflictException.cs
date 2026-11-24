namespace Hexalith.McpCli.Cli;

/// <summary>A successful result cannot be written to a profile transaction file.</summary>
internal sealed class ProfileOutputConflictException() : IOException("The result destination belongs to the profile store.");

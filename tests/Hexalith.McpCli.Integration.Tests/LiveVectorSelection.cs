namespace Hexalith.McpCli.Integration.Tests;

/// <summary>Checks the process selector before a vector can share or contaminate another case's state.</summary>
internal static class LiveVectorSelection
{
    /// <summary>Requires one matching operation trait, selected operation and live test class.</summary>
    internal static void Require(string operation, string? selected, IReadOnlyList<string> arguments, string testClass)
    {
        if (selected != operation || arguments.Count(argument => argument == "-trait") != 1
            || !arguments.Contains("Operation=" + operation, StringComparer.Ordinal)
            || !arguments.Contains(testClass, StringComparer.Ordinal))
            throw new InvalidOperationException("Select exactly one approved live Operation with run-vectors.py; each case requires a fresh isolated topology.");
    }
}

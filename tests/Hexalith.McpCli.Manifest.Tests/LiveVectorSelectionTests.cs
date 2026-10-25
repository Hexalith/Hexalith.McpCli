using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects the single-case boundary independently of the parent's normal selection path.</summary>
public sealed class LiveVectorSelectionTests
{
    private const string Operation = "fixture.read-item";
    private const string TestClass = "Hexalith.McpCli.Integration.Tests.LiveVectorTests";

    /// <summary>The actual parent command form selects one matching case.</summary>
    [Fact]
    public void MatchingProcessSelectionIsAccepted()
        => LiveVectorSelection.Require(Operation, Operation, Arguments(), TestClass);

    /// <summary>Each selection component is required before the case can submit its first command.</summary>
    [Theory]
    [InlineData("missing-selection")]
    [InlineData("wrong-selection")]
    [InlineData("missing-trait")]
    [InlineData("duplicate-trait")]
    [InlineData("wrong-trait")]
    [InlineData("wrong-class")]
    public void InvalidProcessSelectionIsRefused(string defect)
    {
        string? selected = defect == "missing-selection" ? null : defect == "wrong-selection" ? "fixture.other" : Operation;
        List<string> arguments = Arguments();
        if (defect == "missing-trait") arguments.Remove("-trait");
        if (defect == "duplicate-trait") arguments.Add("-trait");
        if (defect == "wrong-trait") arguments[arguments.IndexOf("Operation=" + Operation)] = "Operation=fixture.other";
        if (defect == "wrong-class") arguments[arguments.IndexOf(TestClass)] = "Fixture.OtherTests";
        InvalidOperationException failure = Assert.Throws<InvalidOperationException>(() =>
            LiveVectorSelection.Require(Operation, selected, arguments, TestClass));
        Assert.Equal("Select exactly one approved live Operation with run-vectors.py; each case requires a fresh isolated topology.", failure.Message);
    }

    private static List<string> Arguments() => ["dotnet", "tests.dll", "-class", TestClass, "-trait", "Operation=" + Operation, "-failSkips"];
}

using Hexalith.McpCli.Abstractions;
using Shouldly;

namespace Hexalith.McpCli.Abstractions.Tests;

/// <summary>
/// Verifies canonical operation name parts.
/// </summary>
public sealed class KebabCaseTests
{
    /// <summary>Checks acronym, digit, interior suffix, and trailing suffix boundaries.</summary>
    /// <param name="typeName">The CLR operation type name.</param>
    /// <param name="expected">The expected canonical name part.</param>
    [Theory]
    [InlineData("TLSConfigCommand", "tls-config")]
    [InlineData("XMLHttpRequestQuery", "xml-http-request")]
    [InlineData("getHTTPStatusCommand", "get-http-status")]
    [InlineData("Task2RunCommand", "task2-run")]
    [InlineData("CommandCenterQuery", "command-center")]
    [InlineData("QueryItemsCommand", "query-items")]
    [InlineData("ExecuteCommandAgainCommand", "execute-command-again")]
    [InlineData("HTTP2ServerQuery", "http2-server")]
    [InlineData("SaveQueryCommand", "save-query")]
    [InlineData("FindCommandQuery", "find-command")]
    public void TypeNamesHaveExpectedCanonicalParts(string typeName, string expected)
        => KebabCase.FromTypeName(typeName).ShouldBe(expected);

    /// <summary>Verifies a non-trailing suffix remains part of a plain converted name.</summary>
    [Fact]
    public void ConvertDoesNotRemoveSuffixes()
        => KebabCase.Convert("CommandQuery").ShouldBe("command-query");

    /// <summary>Rejects CLR names that cannot form an ASCII kebab-case part.</summary>
    /// <param name="typeName">The unsupported CLR type name.</param>
    [Theory]
    [InlineData("Item_NameCommand")]
    [InlineData("RésuméCommand")]
    [InlineData("Item-NameQuery")]
    public void TypeNamesRejectUnsupportedCharacters(string typeName)
        => Should.Throw<ArgumentException>(() => KebabCase.FromTypeName(typeName));

    /// <summary>Rejects names whose trailing suffix leaves no operation part.</summary>
    /// <param name="typeName">The suffix-only CLR type name.</param>
    [Theory]
    [InlineData("Command")]
    [InlineData("Query")]
    public void SuffixOnlyTypeNamesAreRejected(string typeName)
        => Should.Throw<ArgumentException>(() => KebabCase.FromTypeName(typeName));
}

using System.Text.Json;
using Hexalith.McpCli.Core.Serialization;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks the shared result serializer options.</summary>
public sealed class McpCliJsonTests
{
    /// <summary>Indented results use LF on every operating system, whatever <see cref="Environment.NewLine"/> is.</summary>
    [Fact]
    public void ResultOptionsUseLfNewLines()
    {
        McpCliJson.Result.NewLine.ShouldBe("\n");
        string json = JsonSerializer.Serialize(new { outer = new { inner = new[] { 1, 2 } } }, McpCliJson.Result);
        json.ShouldContain("\n");
        json.ShouldNotContain("\r");
    }

    /// <summary>Result text keeps HTML-sensitive ASCII readable and escapes quotes, controls and every non-ASCII character.</summary>
    [Fact]
    public void SerializeTextWritesHtmlSensitiveAsciiAndEscapesNonAscii()
    {
        const string value = "Can't open <a> & b+c `d` \"e\" \\ caf\u00E9 \uD83D\uDE00 \u0001\n\u2028\u007F";

        string json = McpCliJson.SerializeText(new Dictionary<string, string> { ["m\u00E9ssage<'>"] = value });

        json.ShouldBe("{\n  \"m\\u00E9ssage<'>\": \"Can't open <a> & b+c `d` \\\"e\\\" \\\\ caf\\u00E9 \\uD83D\\uDE00 \\u0001\\n\\u2028\\u007F\"\n}");
        json.All(char.IsAscii).ShouldBeTrue();
        JsonDocument.Parse(json).RootElement.GetProperty("m\u00E9ssage<'>").GetString().ShouldBe(value);
    }

    /// <summary>Compact text uses the same escaping on one line, so table cells stay single-line ASCII.</summary>
    [Fact]
    public void SerializeCompactTextUsesTheSameEscapingOnOneLine()
    {
        JsonElement value = JsonSerializer.SerializeToElement(new[] { "O'Brien+<x>", "\u00E9\n" });

        McpCliJson.SerializeCompactText(value).ShouldBe("[\"O'Brien+<x>\",\"\\u00E9\\n\"]");
    }

    /// <summary>The structured result options keep the default encoder; only emitted text changes escaping.</summary>
    [Fact]
    public void ResultOptionsKeepTheDefaultEncoder()
    {
        McpCliJson.Result.Encoder.ShouldBeNull();
        JsonSerializer.Serialize("'", McpCliJson.Result).ShouldBe("\"\\u0027\"");
    }
}

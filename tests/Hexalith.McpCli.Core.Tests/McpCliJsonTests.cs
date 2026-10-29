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
}

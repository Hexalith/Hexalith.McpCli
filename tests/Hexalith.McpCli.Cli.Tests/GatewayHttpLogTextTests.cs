using Hexalith.McpCli.Hosting;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Pins the request text the Gateway HTTP loggers may write to standard error.</summary>
public sealed class GatewayHttpLogTextTests
{
    /// <summary>User information, query and fragment never reach the diagnostic channel.</summary>
    /// <param name="uri">The outgoing request URI.</param>
    /// <param name="expected">The logged text.</param>
    [Theory]
    [InlineData("http://127.0.0.1:18170/api/v1/commands", "http://127.0.0.1:18170/api/v1/commands")]
    [InlineData("https://user:secret-token@gateway.example/api/v1/queries?token=secret-token#secret-token",
        "https://gateway.example/api/v1/queries")]
    public void UriOmitsUserInformationQueryAndFragment(string uri, string expected)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post, uri);

        GatewayHttpLogText.Uri(request).ShouldBe(expected);
    }

    /// <summary>A request without an absolute URI logs no target text.</summary>
    [Fact]
    public void RelativeOrMissingUriLogsNothing()
    {
        using var relative = new HttpRequestMessage(HttpMethod.Post, new Uri("/api/v1/commands", UriKind.Relative));
        using var missing = new HttpRequestMessage { Method = HttpMethod.Post };

        GatewayHttpLogText.Uri(relative).ShouldBeEmpty();
        GatewayHttpLogText.Uri(missing).ShouldBeEmpty();
    }
}

using System.Text.Json;
using System.Text.RegularExpressions;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects the shared Redis components and their agreement with the isolated runtime.</summary>
public sealed class TopologyDaprComponentTests
{
    /// <summary>Every service receives the named Redis component with the required actor and key settings.</summary>
    [Theory]
    [InlineData("statestore", "state.redis")]
    [InlineData("pubsub", "pubsub.redis")]
    public void SharedComponentsMatchPrivateRedisAndServiceScopes(string name, string type)
    {
        string root = DependencyPolicyTests.FindRepositoryRoot();
        string path = Path.Combine(root, "tests", "Hexalith.McpCli.AppHost", "DaprComponents", name + ".yaml");
        // JSON is a YAML subset accepted by Dapr and keeps these values inspectable without another dependency.
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(path));
        JsonElement component = document.RootElement;
        Assert.Equal("dapr.io/v1alpha1", component.GetProperty("apiVersion").GetString());
        Assert.Equal("Component", component.GetProperty("kind").GetString());
        Assert.Equal(name, component.GetProperty("metadata").GetProperty("name").GetString());
        JsonElement spec = component.GetProperty("spec");
        Assert.Equal(type, spec.GetProperty("type").GetString());
        Assert.Equal("v1", spec.GetProperty("version").GetString());
        Dictionary<string, string?> metadata = spec.GetProperty("metadata").EnumerateArray()
            .ToDictionary(item => item.GetProperty("name").GetString()!, item => item.GetProperty("value").GetString(), StringComparer.Ordinal);
        var expected = new Dictionary<string, string?>(StringComparer.Ordinal)
        {
            ["redisHost"] = "localhost:6379",
            ["redisPassword"] = string.Empty,
        };
        if (name == "statestore")
        {
            expected["actorStateStore"] = "true";
            expected["keyPrefix"] = "name";
        }
        Assert.Equal(expected.OrderBy(item => item.Key, StringComparer.Ordinal), metadata.OrderBy(item => item.Key, StringComparer.Ordinal));
        Assert.Equal(new[] { "eventstore", "parties", "tenants" },
            component.GetProperty("scopes").EnumerateArray().Select(scope => scope.GetString()).Order(StringComparer.Ordinal));

        string wrapper = File.ReadAllText(Path.Combine(root, "tools", "live-topology", "run-isolated.py"));
        Match redis = Regex.Match(wrapper, @"'redis': \[str\(RUNTIME_DIR / 'bin/redis-server'\), '--bind', '127\.0\.0\.1', '--port', '(\d+)'", RegexOptions.CultureInvariant);
        Assert.True(redis.Success, "The isolated runtime must explicitly bind its private Redis port.");
        Assert.Equal("localhost:" + redis.Groups[1].Value, metadata["redisHost"]);
        Assert.Contains("'HEXALITH_EVENTSTORE_TEST_REDIS_PORT': '" + redis.Groups[1].Value + "'", wrapper, StringComparison.Ordinal);
    }
}

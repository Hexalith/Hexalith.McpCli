using System.Text.Json;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects the shared sidecar permission boundary used by the live topology.</summary>
public sealed class TopologyAccessControlTests
{
    /// <summary>Allows discovery only from the Gateway while all callers and methods remain explicitly bounded.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void MetadataDiscoveryRequiresGatewayPostAndDefaultDeny(bool published)
    {
        string path = Path.Combine(DependencyPolicyTests.FindRepositoryRoot(), "tests", "Hexalith.McpCli.AppHost",
            "DaprComponents", published ? "accesscontrol.published.yaml" : "accesscontrol.yaml");
        // JSON is a YAML subset accepted by Dapr, so this boundary needs no additional parser dependency.
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(path));
        JsonElement mtls = document.RootElement.GetProperty("spec").GetProperty("mtls");
        Assert.True(mtls.GetProperty("enabled").GetBoolean());
        Assert.Equal("127.0.0.1:50001", mtls.GetProperty("sentryAddress").GetString());
        Assert.Equal("public", mtls.GetProperty("controlPlaneTrustDomain").GetString());
        JsonElement access = document.RootElement.GetProperty("spec").GetProperty("accessControl");
        Assert.Equal(new[] { "defaultAction", "policies", "trustDomain" },
            access.EnumerateObject().Select(property => property.Name).Order(StringComparer.Ordinal));
        Assert.Equal("deny", access.GetProperty("defaultAction").GetString());
        Assert.Equal("public", access.GetProperty("trustDomain").GetString());
        Dictionary<string, JsonElement> policies = access.GetProperty("policies").EnumerateArray()
            .ToDictionary(policy => policy.GetProperty("appId").GetString()!, StringComparer.Ordinal);
        Assert.Equal(new[] { "eventstore", "parties", "tenants" }, policies.Keys.Order(StringComparer.Ordinal));
        foreach ((string caller, JsonElement policy) in policies)
        {
            Assert.Equal(new[] { "appId", "defaultAction", "namespace", "operations", "trustDomain" },
                policy.EnumerateObject().Select(property => property.Name).Order(StringComparer.Ordinal));
            Assert.Equal("deny", policy.GetProperty("defaultAction").GetString());
            Assert.Equal("public", policy.GetProperty("trustDomain").GetString());
            Assert.Equal("default", policy.GetProperty("namespace").GetString());
            JsonElement[] operations = policy.GetProperty("operations").EnumerateArray().ToArray();
            string[] allowedPaths = caller == "eventstore"
                ? ["/admin/operational-index-metadata", "/process", "/project", "/project/v2", "/query"]
                : caller == "tenants" ? published ? ["/api/v1/commands", "/api/v1/queries", "/api/v1/streams/read/workload"]
                    : ["/api/v1/commands", "/api/v1/queries"] : ["/api/v1/queries"];
            Assert.Equal(allowedPaths, operations.Select(operation => operation.GetProperty("name").GetString()).Order(StringComparer.Ordinal));
            Assert.All(operations, operation =>
            {
                Assert.Equal(new[] { "action", "httpVerb", "name" },
                    operation.EnumerateObject().Select(property => property.Name).Order(StringComparer.Ordinal));
                Assert.Equal("allow", operation.GetProperty("action").GetString());
                Assert.Equal(new[] { "POST" }, operation.GetProperty("httpVerb").EnumerateArray().Select(verb => verb.GetString()));
            });
        }
    }
}

using System.Security.Cryptography;
using System.Text.Json.Nodes;

namespace Hexalith.McpCli.AppHost;

/// <summary>Retains only credential-free SDK/reader preparation inventories before private receipts are disposed.</summary>
internal static class NativeCatalogPreparationEvidence
{
    /// <summary>Copies the existing SDK schema's identity and digest fields, never raw environment or custody.</summary>
    internal static JsonObject Capture(string tenantReceipt, string partyReceipt)
    {
        JsonObject tenant = JsonNode.Parse(File.ReadAllBytes(tenantReceipt))!.AsObject();
        JsonObject party = JsonNode.Parse(File.ReadAllBytes(partyReceipt))!.AsObject();
        JsonObject safeTenant = Select(tenant, "project", "projectPath", "projectSha256", "configuration", "targetFramework", "sdk",
            "buildEnvironmentDigest", "targetSha256", "assembly", "moduleVersionId", "declarations");
        safeTenant["operations"] = Inventory(tenant, "operations", "RouteId", "Digest");
        safeTenant["dependencies"] = Inventory(tenant, "dependencies", "name", "sha256");
        safeTenant["loadedSdk"] = Inventory(tenant, "loadedSdk", "assembly", "moduleVersionId", "sha256");
        if (tenant["ownerArtifacts"] is JsonObject artifacts)
            safeTenant["ownerArtifacts"] = new JsonObject
            {
                ["declarations"] = Select(artifacts["declarations"]!.AsObject(), "fileName", "assembly", "moduleVersionId", "sha256"),
                ["adapters"] = Select(artifacts["adapters"]!.AsObject(), "fileName", "assembly", "moduleVersionId", "sha256"),
            };
        return new JsonObject
        {
            ["tenantPreparationSha256"] = Digest(tenantReceipt),
            ["partyPreparationSha256"] = Digest(partyReceipt),
            ["tenantPreparation"] = safeTenant,
            ["partyPreparation"] = Select(party, "instanceId", "gatewayAppId", "sdkVersion", "templateSource", "templateHash",
                "templateProjectSha256", "readerProjectSha256", "templateProgramSha256", "readerProgramSha256",
                "templateCohortSha256", "readerCohortSha256", "buildsCatalogSha256", "globalJsonSha256", "bindingsSha256", "inputHashes", "auditReceiptSha256", "auditedPackageGraph"),
        };
    }

    private static JsonObject Select(JsonObject source, params string[] names)
    {
        var selected = new JsonObject();
        foreach (string name in names) if (source[name] is { } value) selected[name] = value.DeepClone();
        return selected;
    }

    private static JsonArray Inventory(JsonObject source, string name, params string[] fields)
        => new((source[name]?.AsArray() ?? []).Select(value => (JsonNode?)Select(value!.AsObject(), fields)).ToArray());

    private static string Digest(string path) => Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path)));
}

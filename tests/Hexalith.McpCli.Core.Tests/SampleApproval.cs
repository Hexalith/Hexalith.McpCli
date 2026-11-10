using System.Security.Cryptography;
using System.Text.Json.Nodes;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>A temporary approval directory holding the synthetic sample vectors and a receipt binding their hashes.</summary>
internal sealed class SampleApproval : IDisposable
{
    private const string Package = "Hexalith.McpCli.Sample.Contracts";

    /// <summary>Initializes a new instance of the <see cref="SampleApproval"/> class.</summary>
    /// <param name="module">The module name the receipt approves.</param>
    internal SampleApproval(string module = "sample")
    {
        Modules = Path.Combine(Path.GetTempPath(), "sample-shapes-" + Path.GetRandomFileName());
        string directory = Path.Combine(Modules, Package);
        Directory.CreateDirectory(directory);
        var hashes = new JsonObject();
        foreach (string name in new[] { "sample-command", "sample-query", "sample-rename" })
        {
            string target = Path.Combine(directory, name + ".vector.json");
            File.Copy(Path.Combine(AppContext.BaseDirectory, "conformance", name + ".json"), target);
            hashes[name + ".vector.json"] = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(target)));
        }

        File.WriteAllText(Path.Combine(directory, "approval.json"),
            new JsonObject { ["module"] = module, ["vectorFilesSha256"] = hashes }.ToJsonString());
    }

    /// <summary>Gets the temporary directory that holds the approval directory.</summary>
    internal string Modules { get; }

    /// <summary>Gets the path of one approved sample vector.</summary>
    /// <param name="name">The sample name without extension, such as <c>sample-query</c>.</param>
    /// <returns>The vector file path.</returns>
    internal string Vector(string name) => Path.Combine(Modules, Package, name + ".vector.json");

    /// <inheritdoc/>
    public void Dispose() => Directory.Delete(Modules, recursive: true);
}

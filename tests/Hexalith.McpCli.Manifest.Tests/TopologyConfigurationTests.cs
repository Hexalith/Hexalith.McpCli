using System.Diagnostics;
using System.Net;
using System.Net.Sockets;

using Hexalith.McpCli.AppHost;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects the root source, authentication and collision guards without starting a topology.</summary>
public sealed class TopologyConfigurationTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "mcpcli-topology-" + Guid.NewGuid().ToString("N"));

    /// <summary>Creates a declared, isolated root source workspace for a guard probe.</summary>
    public TopologyConfigurationTests()
    {
        Directory.CreateDirectory(_root);
        File.WriteAllText(Path.Combine(_root, ".gitmodules"), string.Join('\n', TopologyConfiguration.Modules.Select(
            module => $"[submodule \"{module}\"]\n path = references/{module}")));
        foreach (string module in TopologyConfiguration.Modules)
        {
            string checkout = Path.Combine(_root, "references", module);
            string project = Path.Combine(checkout, "src", module, module + ".csproj");
            Directory.CreateDirectory(Path.GetDirectoryName(project)!);
            File.WriteAllText(project, "<Project />");
            var start = new ProcessStartInfo("git");
            foreach (string argument in new[] { "init", "--quiet", checkout }) start.ArgumentList.Add(argument);
            using Process git = Process.Start(start)!;
            git.WaitForExit();
            Assert.Equal(0, git.ExitCode);
        }
    }

    /// <summary>A declared direct Git checkout is accepted.</summary>
    [Fact]
    public void DeclaredDirectRootSourcesPass() => TopologyConfiguration.ValidateWorkspace(_root);

    /// <summary>Every module must be explicitly declared by the root workspace.</summary>
    [Theory]
    [InlineData("Hexalith.EventStore")]
    [InlineData("Hexalith.Tenants")]
    [InlineData("Hexalith.Parties")]
    public void ExistingUndeclaredSourceFails(string module)
    {
        string modules = Path.Combine(_root, ".gitmodules");
        File.WriteAllText(modules, File.ReadAllText(modules).Replace("references/" + module, "references/Other/references/" + module, StringComparison.Ordinal));
        string project = Path.Combine(_root, "references", module, "src", module, module + ".csproj");
        Assert.Equal($"Required root checkout 'references/{module}' is not declared in '{modules}'. Required project: '{project}'.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateWorkspace(_root)).Message);
    }

    /// <summary>Nested or sibling files cannot substitute for the missing required direct path.</summary>
    [Theory]
    [InlineData("nested")]
    [InlineData("root-level")]
    public void AlternateLayoutCannotReplaceRootSource(string layout)
    {
        const string module = "Hexalith.Parties";
        string checkout = Path.Combine(_root, "references", module);
        string destination = layout == "nested"
            ? Path.Combine(_root, "references", "Other", "references", module)
            : Path.Combine(_root, module);
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        Directory.Move(checkout, destination);
        string project = Path.Combine(checkout, "src", module, module + ".csproj");
        Assert.Equal($"Required root source project '{project}' is missing. Initialize only the declared root checkout 'references/{module}'.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateWorkspace(_root)).Message);
    }

    /// <summary>A copied directory and a forged Git marker do not establish a root checkout.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void CopiedSourceIsNotAQualifiedCheckout(bool forgedMarker)
    {
        string checkout = Path.Combine(_root, "references", "Hexalith.Parties");
        Directory.Delete(Path.Combine(checkout, ".git"), recursive: true);
        if (forgedMarker) File.WriteAllText(Path.Combine(checkout, ".git"), "gitdir: missing");
        string expected = forgedMarker
            ? $"Required root checkout '{checkout}' is not its own Git working tree."
            : $"Required root checkout '{checkout}' must be a direct Git checkout, not a sibling link or copied source directory.";
        Assert.Equal(expected, Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateWorkspace(_root)).Message);
    }

    /// <summary>A link to another checkout cannot be admitted as the declared root checkout.</summary>
    [Fact]
    public void SiblingLinkIsRejected()
    {
        string checkout = Path.Combine(_root, "references", "Hexalith.Parties");
        string elsewhere = Path.Combine(_root, "elsewhere");
        Directory.Move(checkout, elsewhere);
        Directory.CreateSymbolicLink(checkout, elsewhere);
        Assert.Equal($"Required root checkout '{checkout}' must be a direct Git checkout, not a sibling link or copied source directory.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateWorkspace(_root)).Message);
    }

    /// <summary>No absent or undersized key can silently enable unauthenticated test traffic.</summary>
    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("short")]
    public void MissingOrWeakSigningKeyFails(string? key)
        => Assert.Equal("Authentication:JwtBearer:SigningKey must contain at least 32 UTF-8 bytes for the Development test topology.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateSigningKey(key)).Message);

    /// <summary>Each requested application identity is protected independently.</summary>
    [Theory]
    [InlineData("eventstore")]
    [InlineData("tenants")]
    [InlineData("parties")]
    public void ExistingRequestedApplicationFails(string appId)
        => Assert.Equal($"Conflicting Dapr application IDs: {appId}. The requested test topology cannot start alongside these applications.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateRunningApplications("[{\"appId\":\"" + appId + "\"}]")).Message);

    /// <summary>An unrelated application does not prevent an independent topology from running.</summary>
    [Fact]
    public void UnrelatedApplicationAndStrongKeyPass()
    {
        TopologyConfiguration.ValidateRunningApplications("[{\"appId\":\"other-service\"}]");
        TopologyConfiguration.ValidateSigningKey(new string('k', 32));
    }

    /// <summary>An unexpected conflict-check document fails closed.</summary>
    [Fact]
    public void NonArrayDaprSnapshotFails()
        => Assert.Equal("Cannot validate topology conflicts: 'dapr list --output json' must return an array.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateRunningApplications("{}")).Message);

    /// <summary>Malformed Dapr records fail with a stable preflight diagnostic.</summary>
    [Theory]
    [InlineData("[{}]")]
    [InlineData("[null]")]
    [InlineData("[42]")]
    [InlineData("[{\"appId\":42}]")]
    [InlineData("[{\"appId\":null}]")]
    [InlineData("[{\"appId\":\"\"}]")]
    public void MalformedDaprRecordFails(string snapshot)
        => Assert.Equal("Cannot validate topology conflicts: Dapr entry 0 must be an object with a non-empty string 'appId'.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateRunningApplications(snapshot)).Message);

    /// <summary>Invalid sidecar port settings fail before resource launch.</summary>
    [Theory]
    [InlineData(0)]
    [InlineData(1023)]
    [InlineData(65536)]
    public void InvalidGatewayPortFails(int port)
        => Assert.Equal("Dapr:GatewayHttpPort must be between 1024 and 65535.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateGatewayPort(port)).Message);

    /// <summary>A non-Dapr process occupying the Gateway sidecar port is also rejected.</summary>
    [Fact]
    public void OccupiedGatewayPortFails()
    {
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        Assert.Equal($"Gateway Dapr HTTP port {port} is already in use; the test topology cannot start.",
            Assert.Throws<InvalidOperationException>(() => TopologyConfiguration.ValidateGatewayPort(port)).Message);
    }

    /// <inheritdoc/>
    public void Dispose() => Directory.Delete(_root, recursive: true);
}

using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;

using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;

using Hexalith.EventStore.Aspire;
using System.Collections;
using System.Runtime.Loader;

namespace Hexalith.McpCli.AppHost;

/// <summary>Owns the genuine SDK catalog composition for one proven new isolated backend.</summary>
internal sealed class NativeCatalogRuntime : IAsyncDisposable
{
    private readonly DevelopmentRouteCatalogPreparedOwner _tenants;
    private readonly DevelopmentRouteCatalogComposition _catalog;
    private readonly string _reader;
    private readonly string _owner;
    private readonly string _custody;

    private NativeCatalogRuntime(DevelopmentRouteCatalogPreparedOwner tenants, DevelopmentRouteCatalogComposition catalog,
        string reader, string owner, string custody)
    {
        _tenants = tenants;
        _catalog = catalog;
        _reader = reader;
        _owner = owner;
        _custody = custody;
    }

    /// <summary>Uses real host metadata, the existing separate-artifact Platform reader and SDK activation.</summary>
    internal static async Task<NativeCatalogRuntime> CreateAsync(IDistributedApplicationBuilder builder,
        IResourceBuilder<ProjectResource> gateway, IResourceBuilder<ProjectResource> tenants,
        IResourceBuilder<ProjectResource> parties, string stateComponent)
    {
        string backup = Environment.GetEnvironmentVariable("MCPCLI_ISOLATED_REDIS_BACKUP_RECEIPT")
            ?? throw new InvalidOperationException("Native catalog startup requires the wrapper's pre-application Redis backup.");
        _ = TopologyConfiguration.VerifyFreshBackup(backup);
        string root = RepositoryProjectPaths.GetRepositoryRoot();
        string directory = Path.Combine(Path.GetDirectoryName(backup)!, "native-catalog-reader");
        string owner = Guid.NewGuid().ToString("N");
        string custodyDirectory = Path.Combine(Path.GetDirectoryName(backup)!, "native-catalog-custody");
        DevelopmentRouteCatalogPreparedOwner? tenantOwner = null;
        DevelopmentRouteCatalogComposition? catalog = null;
        try
        {
            using var deadline = new CancellationTokenSource(TimeSpan.FromMinutes(4));
            tenantOwner = await tenants.PrepareEventStoreDevelopmentOwnerAsync("Hexalith.Tenants.Contracts.dll",
                "Hexalith.Tenants.Server.dll", TimeSpan.FromMinutes(3), deadline.Token).ConfigureAwait(false);
            string adapter = Path.Combine(root, "references", "Hexalith.Parties", "src", "Hexalith.Parties.EventStoreExtensions",
                "bin", "Release", "net10.0", "Hexalith.Parties.EventStoreExtensions.dll");
            string contracts = Path.Combine(Path.GetDirectoryName(adapter)!, "Hexalith.Parties.Contracts.dll");
            // Parties deliberately supplies its adapter as a separate artifact. The Platform reader
            // validates its actual compiled factory and complete declaration/policy inventory.
            JsonElement partyArtifacts = default;
            await NativeCatalogTool.RunOwnedPreparationAsync(directory, owner, async () =>
            {
                using JsonDocument receipt = await NativeCatalogTool.GenerateAsync(new DirectoryInfo(root), directory,
                    owner, "eventstore", "4.0.4", [(contracts, adapter, "parties")], deadline.Token).ConfigureAwait(false);
                partyArtifacts = receipt.RootElement.GetProperty("loadedArtifacts").Clone();
                foreach (JsonElement artifact in partyArtifacts.EnumerateArray())
                {
                    string path = artifact.GetProperty("path").GetString()!;
                    if (artifact.GetProperty("sha256").GetString() != Digest(File.ReadAllBytes(path)))
                        throw new InvalidDataException("The Platform reader's actual loaded artifact changed after preparation.");
                }
            }).ConfigureAwait(false);
            string output = Path.Combine(directory, "reader", "output");
            // Share only byte-identical SDK images with the AppHost. No adapter is added to
            // the Parties server's dependency graph, and no SDK host loader guard is bypassed.
            foreach (Assembly shared in AppDomain.CurrentDomain.GetAssemblies().Where(assembly =>
                assembly.GetName().Name?.StartsWith("Hexalith.EventStore.", StringComparison.Ordinal) == true))
            {
                string path = Path.Combine(output, shared.GetName().Name + ".dll");
                if (File.Exists(path) && (!File.ReadAllBytes(path).AsSpan().SequenceEqual(File.ReadAllBytes(shared.Location))
                    || AssemblyName.GetAssemblyName(path).FullName != shared.FullName))
                    throw new InvalidDataException("The separately prepared reader SDK differs from the actual AppHost SDK.");
            }
            Assembly declarationAssembly = Assembly.LoadFrom(Path.Combine(output, "Hexalith.Parties.Contracts.dll"));
            Assembly adapterAssembly = Assembly.LoadFrom(Path.Combine(output, "Hexalith.Parties.EventStoreExtensions.dll"));
            NativeCatalogTool.CreatePrivateDirectory(custodyDirectory);
            File.WriteAllText(Path.Combine(custodyDirectory, ".owner"), owner);
            var custody = new DevelopmentRouteCatalogCompositionOptions(custodyDirectory,
                "mcpcli-routing", "mcpcli-routing", "isolated-v1",
                new Dictionary<string, string> { ["isolated-v1"] = Convert.ToBase64String(RandomNumberGenerator.GetBytes(32)) }, "isolated-v1");
            Assembly sdk = AssemblyLoadContext.GetLoadContext(tenantOwner.Owner.Adapters)!.LoadFromAssemblyName(new AssemblyName("Hexalith.EventStore.DomainService"));
            IEnumerable operational = (IEnumerable)sdk.GetType("Hexalith.EventStore.DomainService.EventStoreDomainServiceRoutes", throwOnError: true)!
                .GetProperty("Operational")!.GetValue(null)!;
            DevelopmentRouteCatalogInvocation[] domainCalls = operational.Cast<object>()
                .Select(route => new DevelopmentRouteCatalogInvocation(gateway, (string)route.GetType().GetProperty("Route")!.GetValue(route)!, ["POST"])).ToArray();
            catalog = builder.AddEventStoreDevelopmentRouteCatalog(gateway,
                [tenantOwner.Owner, new(parties, declarationAssembly, adapterAssembly)],
                [new(gateway, [new(tenants, "/api/v1/commands/bound/workload", ["POST"]),
                    new(tenants, "/api/v1/streams/read/workload", ["POST"]), new(tenants, "/api/v1/queries", ["POST"]),
                    new(parties, "/api/v1/queries", ["POST"])]) { TechnicalHttp = true },
                 new(tenants, domainCalls), new(parties, domainCalls)], stateComponent, custody);
            tenants.WithEnvironment("Tenants__BootstrapBoundWorkloadEnabled", "true")
                .WithEnvironment("Tenants__BootstrapBoundWorkloadReceiptPath", Path.Combine(catalog.Directory, "tenants.bootstrap.json"));
            gateway.WithEnvironment("Authentication__BoundCommand__AllowedDomains__tenants", "global-administrators");
            // This private coordinate file contains no digest keys or activation authority.
            await File.WriteAllTextAsync(Path.Combine(Path.GetDirectoryName(backup)!, "native-catalog-coordinates.json"),
                JsonSerializer.Serialize(new { directory = catalog.Directory, rootDigest = catalog.RootDigest,
                    hosts = new[] { "eventstore", "parties", "tenants" },
                    inputs = new
                    {
                        sourceSelectionSha256 = Digest(File.ReadAllBytes(Path.Combine(root, "tools", "live-topology", "native-runtime.json"))),
                        tenantPreparationSha256 = Digest(File.ReadAllBytes(Path.Combine(tenantOwner.Directory, "preparation.json"))),
                        partyPreparationSha256 = Digest(File.ReadAllBytes(Path.Combine(directory, "reader", "preparation.json"))),
                        partyArtifacts,
                    } }), deadline.Token).ConfigureAwait(false);
            return new(tenantOwner, catalog, directory, owner, custodyDirectory);
        }
        catch (Exception failure)
        {
            if (catalog is not null) await catalog.DisposeAsync().ConfigureAwait(false);
            if (tenantOwner is not null) await tenantOwner.DisposeAsync().ConfigureAwait(false);
            if (!failure.Data.Contains("CatalogOwnedProcessStillRunning")) NativeCatalogTool.DeleteOwnedDirectory(directory, owner);
            NativeCatalogTool.DeleteOwnedDirectory(custodyDirectory, owner);
            throw;
        }
    }

    /// <inheritdoc />
    public async ValueTask DisposeAsync()
    {
        try { await _catalog.DisposeAsync().ConfigureAwait(false); }
        finally
        {
            await _tenants.DisposeAsync().ConfigureAwait(false);
            NativeCatalogTool.DeleteOwnedDirectory(_reader, _owner);
            NativeCatalogTool.DeleteOwnedDirectory(_custody, _owner);
        }
    }

    private static string Digest(byte[] bytes) => Convert.ToHexStringLower(SHA256.HashData(bytes));
}

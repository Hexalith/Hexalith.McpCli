using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;

using CommunityToolkit.Aspire.Hosting.Dapr;

using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

using Hexalith.EventStore.Aspire;
using Hexalith.McpCli.AppHost;
using Hexalith.Parties.Aspire;
using Hexalith.Tenants.Aspire;

using Microsoft.Extensions.Configuration;

IDistributedApplicationBuilder builder = DistributedApplication.CreateBuilder(args);
builder.Configuration.AddJsonFile(Path.Combine(builder.AppHostDirectory, "appsettings.json"), optional: false)
    .AddEnvironmentVariables().AddCommandLine(args);
string? signingKey = builder.Configuration["Authentication:JwtBearer:SigningKey"];
int gatewayPort;
try
{
    gatewayPort = builder.Configuration.GetValue("Dapr:GatewayHttpPort", 3501);
    TopologyConfiguration.ValidateGatewayPort(gatewayPort);
    TopologyConfiguration.ValidateWorkspace(RepositoryProjectPaths.GetRepositoryRoot());
    TopologyConfiguration.ValidateSigningKey(signingKey);
    TopologyConfiguration.EnsureNoConflictingTopology(gatewayPort);
}
catch (Exception exception) when (exception is InvalidOperationException or TimeoutException
    or System.ComponentModel.Win32Exception or System.Text.Json.JsonException)
{
    Console.Error.WriteLine(exception.Message);
    return 2;
}

// Executable boundary checks run these same guards and exit before adding any resource.
if (builder.Configuration.GetValue<bool>("Topology:PreflightOnly")) return 0;

string components = Path.Combine(builder.AppHostDirectory, "DaprComponents");
string access = Path.Combine(components, "accesscontrol.yaml");
string? placement = builder.Configuration["Dapr:PlacementHostAddress"];
string? scheduler = builder.Configuration["Dapr:SchedulerHostAddress"];
IResourceBuilder<ParameterResource> key = builder.AddParameter("live-test-signing-key", () => signingKey!, secret: true);

// Load the test-owned settings instead of the source host's sample Development registrations.
IResourceBuilder<ProjectResource> gateway = builder.AddHexalithEventStoreGatewayProject()
    .WithEnvironment("ASPNETCORE_CONTENTROOT", builder.AppHostDirectory);
foreach (IConfigurationSection route in builder.Configuration.GetSection("Gateway:Routes").GetChildren())
{
    foreach (string field in new[] { "TenantId", "Domain", "Version", "AppId", "MethodName" })
    {
        gateway.WithEnvironment($"EventStore__DomainServices__Registrations__{route.Key}__{field}",
            route[field] ?? throw new InvalidOperationException($"Gateway:Routes:{route.Key}:{field} is required."));
    }
}

HexalithEventStoreResources topology = builder.AddHexalithEventStore(gateway, adminServer: null, adminUI: null,
    eventStoreDaprConfigPath: access, adminServerDaprConfigPath: null, resiliencyConfigPath: null,
    stateStoreComponentPath: Path.Combine(components, "statestore.yaml"),
    eventStoreDaprHttpPort: gatewayPort, daprPlacementHostAddress: placement,
    daprSchedulerHostAddress: scheduler, pubSubComponentPath: Path.Combine(components, "pubsub.yaml"));
gateway.WithGeneratedEventStoreAppChannelToken();
IResourceBuilder<ProjectResource> tenants = builder.AddHexalithTenantsServer(topology, access,
    daprPlacementHostAddress: placement, daprSchedulerHostAddress: scheduler)
    .WithGeneratedEventStoreAppChannelToken();
IResourceBuilder<ProjectResource> parties = builder.AddHexalithPartiesServer(topology, access,
    daprPlacementHostAddress: placement, daprSchedulerHostAddress: scheduler)
    .WithGeneratedEventStoreAppChannelToken();

foreach (IResourceBuilder<ProjectResource> resource in new[] { gateway, tenants, parties })
{
    resource.WithEnvironment("ASPNETCORE_ENVIRONMENT", "Development")
        .WithEnvironment("DOTNET_ENVIRONMENT", "Development")
        .WithEnvironment("Authentication__JwtBearer__Authority", string.Empty)
        .WithEnvironment("Authentication__JwtBearer__Issuer", "mcpcli-live-tests")
        .WithEnvironment("Authentication__JwtBearer__Audience", "hexalith-eventstore")
        .WithEnvironment("Authentication__JwtBearer__ValidAudiences__0", "hexalith-eventstore")
        .WithEnvironment("Authentication__JwtBearer__AllowedAlgorithms__0", "HS256")
        .WithEnvironment("Authentication__JwtBearer__SigningKey", key)
        .WithEnvironment("Authentication__JwtBearer__RequireHttpsMetadata", "false");
    foreach (EndpointAnnotation endpoint in resource.Resource.Annotations.OfType<EndpointAnnotation>())
    {
        endpoint.Port = null;
        endpoint.TargetPort = null;
    }
}

// Evaluate the actual composed model without starting it; never emit secret values.
if (builder.Configuration.GetValue<bool>("Topology:InspectComposition"))
{
    var snapshots = new List<object>();
    foreach (IResourceBuilder<ProjectResource> resource in new[] { gateway, tenants, parties })
    {
        DaprSidecarAnnotation sidecar = resource.Resource.Annotations.OfType<DaprSidecarAnnotation>().Single();
        Dictionary<string, object> appEnvironment = await EnvironmentAsync(resource.Resource);
        Dictionary<string, object> sidecarEnvironment = await EnvironmentAsync(sidecar.Sidecar);
        string? appToken = await ValueAsync(appEnvironment.GetValueOrDefault("APP_API_TOKEN"));
        string? sidecarToken = await ValueAsync(sidecarEnvironment.GetValueOrDefault("APP_API_TOKEN"));
        snapshots.Add(new
        {
            name = resource.Resource.Name,
            appTokenLength = appToken?.Length ?? 0,
            sidecarTokenLength = sidecarToken?.Length ?? 0,
            tokensMatch = !string.IsNullOrEmpty(appToken) && appToken == sidecarToken,
            tokenHash = appToken is null ? null : Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(appToken))),
            configuration = sidecar.Sidecar.Annotations.OfType<DaprSidecarOptionsAnnotation>().Last().Options.Config,
            contentRoot = await ValueAsync(appEnvironment.GetValueOrDefault("ASPNETCORE_CONTENTROOT")),
        });
    }
    Console.WriteLine(JsonSerializer.Serialize(new { appHostDirectory = builder.AppHostDirectory, resources = snapshots }));
    return 0;
}

await builder.Build().RunAsync().ConfigureAwait(false);

async Task<Dictionary<string, object>> EnvironmentAsync(IResource resource)
{
    var values = new Dictionary<string, object>();
    var context = new EnvironmentCallbackContext(builder.ExecutionContext, resource, values);
    foreach (EnvironmentCallbackAnnotation callback in resource.Annotations.OfType<EnvironmentCallbackAnnotation>())
        await callback.Callback(context).ConfigureAwait(false);
    return values;
}

static async Task<string?> ValueAsync(object? value) => value is IValueProvider provider
    ? await provider.GetValueAsync(CancellationToken.None).ConfigureAwait(false) : value?.ToString();
return 0;

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
bool preflightOnly;
bool inspectComposition;
var routes = new Dictionary<string, string>();
var topicOverrides = new Dictionary<string, string>();
try
{
    gatewayPort = builder.Configuration.GetValue("Dapr:GatewayHttpPort", 3501);
    preflightOnly = builder.Configuration.GetValue<bool>("Topology:PreflightOnly");
    inspectComposition = builder.Configuration.GetValue<bool>("Topology:InspectComposition");
    if (!preflightOnly && !inspectComposition && Environment.GetEnvironmentVariable("MCPCLI_ISOLATED_TOPOLOGY") != "1")
        throw new InvalidOperationException("Live topology tests require tools/live-topology/run-isolated.py; refusing to use host Dapr or Redis.");
    foreach (IConfigurationSection route in builder.Configuration.GetSection("Gateway:Routes").GetChildren())
    {
        foreach (string field in new[] { "TenantId", "Domain", "Version", "AppId", "MethodName" })
        {
            string? value = route[field];
            if (string.IsNullOrWhiteSpace(value))
                throw new InvalidOperationException($"Gateway:Routes:{route.Key}:{field} is required.");
            routes.Add($"EventStore__DomainServices__Registrations__{route.Key}__{field}", value);
        }
    }
    foreach (IConfigurationSection topic in builder.Configuration.GetSection("Gateway:TopicOverrides").GetChildren())
    {
        if (string.IsNullOrWhiteSpace(topic.Value))
            throw new InvalidOperationException($"Gateway:TopicOverrides:{topic.Key} is required.");
        topicOverrides.Add($"EventStore__Publisher__TopicOverrides__{topic.Key}", topic.Value);
    }
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
if (preflightOnly) return 0;

string components = Path.Combine(builder.AppHostDirectory, "DaprComponents");
string access = Path.Combine(components, "accesscontrol.yaml");
string? placement = builder.Configuration["Dapr:PlacementHostAddress"];
string? scheduler = builder.Configuration["Dapr:SchedulerHostAddress"];
IResourceBuilder<ParameterResource> key = builder.AddParameter("live-test-signing-key", () => signingKey!, secret: true);

// Load the test-owned settings instead of the source host's sample Development registrations.
IResourceBuilder<ProjectResource> gateway = builder.AddHexalithEventStoreGatewayProject()
    .WithEnvironment("ASPNETCORE_CONTENTROOT", builder.AppHostDirectory);
foreach ((string name, string value) in routes.Concat(topicOverrides))
    gateway.WithEnvironment(name, value);

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
if (inspectComposition)
{
    var snapshots = new List<object>();
    foreach (IResourceBuilder<ProjectResource> resource in new[] { gateway, tenants, parties })
    {
        DaprSidecarAnnotation sidecar = resource.Resource.Annotations.OfType<DaprSidecarAnnotation>().Single();
        DaprSidecarOptions options = sidecar.Sidecar.Annotations.OfType<DaprSidecarOptionsAnnotation>().Last().Options;
        Dictionary<string, object> appEnvironment = await EnvironmentAsync(resource.Resource);
        Dictionary<string, object> sidecarEnvironment = await EnvironmentAsync(sidecar.Sidecar);
        string? appToken = await ValueAsync(appEnvironment.GetValueOrDefault("APP_API_TOKEN"));
        string? sidecarToken = await ValueAsync(sidecarEnvironment.GetValueOrDefault("APP_API_TOKEN"));
        snapshots.Add(new
        {
            name = resource.Resource.Name,
            projectPath = resource.Resource.Annotations.OfType<IProjectMetadata>().Single().ProjectPath,
            aspnetcoreEnvironment = await ValueAsync(appEnvironment.GetValueOrDefault("ASPNETCORE_ENVIRONMENT")),
            dotnetEnvironment = await ValueAsync(appEnvironment.GetValueOrDefault("DOTNET_ENVIRONMENT")),
            endpoints = resource.Resource.Annotations.OfType<EndpointAnnotation>()
                .Select(endpoint => new { name = endpoint.Name, port = endpoint.Port, targetPort = endpoint.TargetPort }),
            gatewaySettings = appEnvironment.Keys.Where(name => name.StartsWith("EventStore__DomainServices__Registrations__", StringComparison.Ordinal)
                || name.StartsWith("EventStore__Publisher__TopicOverrides__", StringComparison.Ordinal))
                .ToDictionary(name => name, name => appEnvironment[name].ToString()),
            authentication = new
            {
                authority = await ValueAsync(appEnvironment.GetValueOrDefault("Authentication__JwtBearer__Authority")),
                issuer = await ValueAsync(appEnvironment.GetValueOrDefault("Authentication__JwtBearer__Issuer")),
                audience = await ValueAsync(appEnvironment.GetValueOrDefault("Authentication__JwtBearer__Audience")),
                validAudience = await ValueAsync(appEnvironment.GetValueOrDefault("Authentication__JwtBearer__ValidAudiences__0")),
                algorithm = await ValueAsync(appEnvironment.GetValueOrDefault("Authentication__JwtBearer__AllowedAlgorithms__0")),
                requireHttpsMetadata = await ValueAsync(appEnvironment.GetValueOrDefault("Authentication__JwtBearer__RequireHttpsMetadata")),
                signingKeyHash = Hash(await ValueAsync(appEnvironment.GetValueOrDefault("Authentication__JwtBearer__SigningKey"))),
            },
            daprHttpPort = options.DaprHttpPort,
            placementHostAddress = options.PlacementHostAddress,
            schedulerHostAddress = options.SchedulerHostAddress,
            components = sidecar.Sidecar.Annotations.OfType<DaprComponentReferenceAnnotation>()
                .ToDictionary(component => component.Component.Name, component => component.Component.Options?.LocalPath),
            appTokenLength = appToken?.Length ?? 0,
            sidecarTokenLength = sidecarToken?.Length ?? 0,
            tokensMatch = !string.IsNullOrEmpty(appToken) && appToken == sidecarToken,
            tokenHash = Hash(appToken),
            configuration = options.Config,
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

static string? Hash(string? value) => value is null ? null : Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value)));

static async Task<string?> ValueAsync(object? value) => value is IValueProvider provider
    ? await provider.GetValueAsync(CancellationToken.None).ConfigureAwait(false) : value?.ToString();
return 0;

using Hexalith.EventStore;
using Hexalith.EventStore.Extensions;
using Hexalith.EventStore.HealthChecks;
using Hexalith.EventStore.Middleware;
using Hexalith.EventStore.OpenApi;
using Hexalith.EventStore.Server.Configuration;
using Hexalith.EventStore.ServiceDefaults;
using Hexalith.EventStore.SignalRHub;
using Hexalith.EventStore.ServiceDefaults.Authentication;
using Hexalith.EventStore.Controllers;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);
builder.WebHost.ConfigureKestrel(options => options.Limits.MaxRequestBodySize = 1_048_576);
// Native gateway defaults remain below normal appsettings, environment and command-line overrides.
builder.Configuration.Sources.Insert(0, new Microsoft.Extensions.Configuration.Json.JsonConfigurationSource
{
    FileProvider = new Microsoft.Extensions.FileProviders.PhysicalFileProvider(AppContext.BaseDirectory),
    Path = "appsettings.gateway.json",
    Optional = false,
    ReloadOnChange = false,
});

builder.AddServiceDefaults();
builder.Services.AddDaprClient();
builder.Services.AddHealthChecks()
    .AddEventStoreDaprHealthChecks();
builder.Services.AddEventStore();
builder.Services.AddEventStoreServer(builder.Configuration);
builder.Services.AddEventStoreDomainQueryRouting();
if (!string.IsNullOrEmpty(builder.Configuration["EventStore:RouteCatalog:DevelopmentBootstrap:CatalogPath"]))
    Hexalith.EventStore.Server.Routing.RunScopedRouteCatalogGateway.AddEventStoreRunScopedCatalogGateway(builder.Services, builder.Configuration);
builder.Services.AddEventStoreSignalR(builder.Configuration);

WebApplication app = builder.Build();

// An explicit test-only probe consumes the actual Kestrel request body without
// an endpoint size attribute, so server-default regressions remain observable.
if (app.Configuration.GetValue<bool>("Testing:BodyLimitProbe"))
{
    app.MapPost("/testing/body-limit", async (HttpRequest request, CancellationToken token) =>
    {
        try
        {
            await request.Body.CopyToAsync(Stream.Null, token);
            return Results.Ok();
        }
        catch (BadHttpRequestException exception) when (exception.StatusCode == StatusCodes.Status413PayloadTooLarge)
        {
            return Results.StatusCode(exception.StatusCode);
        }
    }).RequireAuthorization(EventStoreHttpHostSecurityExtensions.HumanPolicy);
}

app.UseMiddleware<CorrelationIdMiddleware>();
app.UseExceptionHandler();
app.MapDefaultEndpoints();
app.UseRouting();
app.UseAuthentication();
app.UseRateLimiter();
app.UseEventStoreHttpHostSecurity();
app.UseAuthorization();
if (!string.IsNullOrEmpty(app.Configuration["EventStore:RouteCatalog:DevelopmentBootstrap:CatalogPath"]))
{
    if (Hexalith.EventStore.ServiceDefaults.Routing.TechnicalHttpRouteCatalogReceiver.IsEnabled(app.Configuration))
        Hexalith.EventStore.ServiceDefaults.Routing.TechnicalHttpRouteCatalogReceiver.UseDevelopmentTechnicalHttpCatalogReceiver(app,
            Hexalith.EventStore.Server.Routing.RunScopedRouteCatalogGateway.Operation);
    else
        Hexalith.EventStore.ServiceDefaults.Routing.FiniteRouteCatalogReceiver.UseFiniteDevelopmentRouteCatalogReceiver(app,
            Hexalith.EventStore.Server.Routing.RunScopedRouteCatalogGateway.Operation);
}
app.UseCloudEvents();

if (app.Configuration.GetValue("EventStore:OpenApi:Enabled", true))
{
    _ = app.MapOpenApi().RequireAuthorization(EventStoreHttpHostSecurityExtensions.HumanPolicy);
    _ = app.UseEventStoreHumanSurface("/swagger");
    _ = app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint("/openapi/v1.json", "Hexalith EventStore API v1");
        options.RoutePrefix = "swagger";
    });
}

app.MapControllers().WithEventStoreProjectionNotifications(app.Services, false);
app.MapErrorReferences();
app.MapApiVersionFallback();
app.MapSubscribeHandler().RequireEventStoreChannel();
app.MapActorsHandlers().WithMetadata(EventStoreActorCallbackEndpointMetadata.Instance).RequireEventStoreChannel();
app.MapApplicationRuntimeProofEndpoints();

SignalROptions? signalROptions = app.Configuration
    .GetSection("EventStore:SignalR")
    .Get<SignalROptions>();

if (signalROptions?.Enabled == true)
{
    _ = app.MapHub<ProjectionChangedHub>(ProjectionChangedHub.HubPath).RequireAuthorization(EventStoreHttpHostSecurityExtensions.HumanPolicy);
    _ = app.MapSignalRRuntimeProofEndpoints();
}

app.Run();

/// <summary>
/// Entry point exposed for package-built gateway tests.
/// </summary>
public partial class Program;

using System.Reflection;
using Hexalith.EventStore.Client.Registration;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Settings;
using Microsoft.Extensions.DependencyInjection;

namespace Hexalith.McpCli.Core;

/// <summary>Registers the shared Catalog, executor, settings, and one gateway client.</summary>
public static class McpCliCoreServiceCollectionExtensions
{
    /// <summary>Adds Core services without building or scanning the Catalog during registration.</summary>
    /// <param name="services">The process service collection.</param>
    /// <param name="settings">The already resolved settings snapshot.</param>
    /// <param name="manifest">The generated Contracts assembly manifest loader.</param>
    /// <param name="configureGateway">The hosting adapter's authentication handler configuration.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddMcpCliCore(
        this IServiceCollection services,
        ResolvedSettings settings,
        Func<IReadOnlyList<Assembly>> manifest,
        Action<IHttpClientBuilder> configureGateway)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(settings);
        ArgumentNullException.ThrowIfNull(manifest);
        ArgumentNullException.ThrowIfNull(configureGateway);

        services.AddSingleton(settings);
        services.AddSingleton(new ExecutionAvailability(settings.ReadOnly, settings.Url is not null));
        services.AddSingleton(new EnvelopeContext(settings.Tenant, settings.Actor,
            settings.AllowTenantOverride, settings.AllowedExtensions));
        services.AddSingleton(serviceProvider => new CatalogProvider(manifest,
            serviceProvider.GetRequiredService<Microsoft.Extensions.Logging.ILogger<CatalogProvider>>()));
        services.AddSingleton<ICatalog>(serviceProvider => new CatalogService(
            serviceProvider.GetRequiredService<CatalogProvider>(),
            serviceProvider.GetRequiredService<ExecutionAvailability>(), settings.Strict));
        services.AddSingleton<IOperationExecutor>(serviceProvider => new OperationExecutor(
            serviceProvider.GetRequiredService<CatalogProvider>(),
            serviceProvider.GetRequiredService<ExecutionAvailability>(),
            serviceProvider.GetRequiredService<Hexalith.EventStore.Client.Gateway.IEventStoreGatewayClient>(),
            settings.Strict));

        IHttpClientBuilder gatewayBuilder = services.AddEventStoreGatewayClient(options => options.BaseAddress = settings.Url);
        configureGateway(gatewayBuilder);
        return services;
    }
}

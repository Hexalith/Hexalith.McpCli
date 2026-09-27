using System.Reflection;
using Hexalith.McpCli.Core;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Mcp;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Hexalith.McpCli.Hosting;

/// <summary>Builds the shared process container for CLI and MCP verbs.</summary>
internal static class HostFactory
{
    internal static IHost Create(ResolvedSettings settings, bool mcp = false,
        Func<IReadOnlyList<Assembly>>? manifest = null)
    {
        HostApplicationBuilder builder = Host.CreateApplicationBuilder();
        builder.Logging.ClearProviders();
        builder.Logging.AddConsole(options => options.LogToStandardErrorThreshold = LogLevel.Trace);
        _ = builder.Services.AddMcpCliCore(settings, manifest ?? ManifestLoader.Load, gateway =>
        {
            if (settings.Token is not null)
            {
                builder.Services.AddTransient(_ => new StaticBearerTokenHandler(settings.Token));
                _ = gateway.AddHttpMessageHandler<StaticBearerTokenHandler>();
            }
        });
        if (mcp)
        {
            _ = builder.Services.AddMcpCliMcpServer(settings);
        }

        return builder.Build();
    }
}

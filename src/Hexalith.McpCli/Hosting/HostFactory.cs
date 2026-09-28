using System.Reflection;
using Hexalith.McpCli.Core;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Mcp;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Hexalith.McpCli.Hosting;

/// <summary>Builds the shared process container for CLI and MCP verbs.</summary>
internal static class HostFactory
{
    /// <summary>Resolves one settings snapshot and builds the single host for a CLI invocation.</summary>
    /// <param name="input">The explicit command-line settings.</param>
    /// <param name="profileStore">The private mcpcli profile store.</param>
    /// <param name="error">The source-specific resolution error, when resolution fails.</param>
    /// <param name="mcp">Whether to register the MCP stdio server.</param>
    /// <param name="manifest">The lazy Contracts assembly manifest.</param>
    /// <param name="readEnvironment">The environment reader, or the process environment by default.</param>
    /// <returns>The invocation host, or <see langword="null" /> when settings resolution fails.</returns>
    internal static IHost? Create(
        SettingsInput input,
        ProfileStore profileStore,
        out OperationError? error,
        bool mcp = false,
        Func<IReadOnlyList<Assembly>>? manifest = null,
        Func<string, string?>? readEnvironment = null)
    {
        SettingsResolution resolved = new SettingsBootstrap(profileStore, readEnvironment).Resolve(input);
        error = resolved.Error;
        return resolved.Settings is null ? null : CreateHost(resolved.Settings, mcp, manifest);
    }

    private static IHost CreateHost(ResolvedSettings settings, bool mcp,
        Func<IReadOnlyList<Assembly>>? manifest)
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

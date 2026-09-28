using System.CommandLine;
using System.CommandLine.Parsing;
using Hexalith.McpCli.Core.Settings;

namespace Hexalith.McpCli.Cli;

/// <summary>Defines and binds process-wide CLI options without resolving settings twice.</summary>
internal sealed class GlobalOptionsBinding
{
    internal Option<string?> Url { get; } = new("--url") { Description = "EventStore gateway URL", Recursive = true };
    internal Option<string?> Token { get; } = new("--token") { Description = "Gateway bearer token", Recursive = true };
    internal Option<string?> Tenant { get; } = new("--tenant") { Description = "Session tenant", Recursive = true };
    internal Option<string?> Actor { get; } = new("--actor") { Description = "Trusted operator actor", Recursive = true };
    internal Option<bool> AllowTenantOverride { get; } = new("--allow-tenant-override") { Description = "Allow MCP per-call tenant selection", Recursive = true };
    internal Option<string?> Profile { get; } = new("--profile") { Description = "Connection profile", Recursive = true };
    internal Option<string?> Format { get; } = new("--format") { Description = "json or table", Recursive = true };
    internal Option<string?> Output { get; } = new("--output") { Description = "Write the result to a file", Recursive = true };
    internal Option<bool> ReadOnly { get; } = new("--read-only") { Description = "Disable command submission", Recursive = true };
    internal Option<bool> Strict { get; } = new("--strict") { Description = "Reject any Catalog diagnostic", Recursive = true };

    internal void AddTo(RootCommand root)
    {
        root.Options.Add(Url);
        root.Options.Add(Token);
        root.Options.Add(Tenant);
        root.Options.Add(Actor);
        root.Options.Add(AllowTenantOverride);
        root.Options.Add(Profile);
        root.Options.Add(Format);
        root.Options.Add(Output);
        root.Options.Add(ReadOnly);
        root.Options.Add(Strict);
    }

    internal SettingsInput Read(ParseResult parsed)
        => new(
            ExplicitValue(parsed, Url),
            ExplicitValue(parsed, Token),
            ExplicitValue(parsed, Tenant),
            ExplicitValue(parsed, Actor),
            ExplicitFlag(parsed, AllowTenantOverride),
            ExplicitValue(parsed, Profile),
            ExplicitValue(parsed, Format),
            ExplicitValue(parsed, Output),
            ExplicitFlag(parsed, ReadOnly),
            ExplicitFlag(parsed, Strict));

    private static string? ExplicitValue(ParseResult parsed, Option<string?> option)
        => parsed.GetResult(option)?.Tokens.Count > 0 ? parsed.GetValue(option) : null;

    private static bool? ExplicitFlag(ParseResult parsed, Option<bool> option)
        => parsed.GetResult(option) is { Implicit: false } ? parsed.GetValue(option) : null;
}

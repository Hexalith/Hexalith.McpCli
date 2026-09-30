using System.CommandLine;
using System.CommandLine.Parsing;
using System.Text.Json;
using System.Reflection;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace Hexalith.McpCli.Cli;

/// <summary>Defines the generic CLI verbs as thin translations into Core calls.</summary>
internal sealed class CliRunner
{
    private readonly GlobalOptionsBinding _globals = new();
    private readonly ProfileStore _profileStore;
    private readonly Func<IReadOnlyList<Assembly>>? _manifest;
    private readonly Func<string, string?>? _readEnvironment;
    private readonly Func<IHost, CancellationToken, Task<int>>? _runMcp;

    /// <summary>Initializes a CLI runner with optional profile and manifest seams.</summary>
    /// <param name="profileStore">The private mcpcli profile store.</param>
    /// <param name="manifest">The lazy Contracts assembly manifest.</param>
    internal CliRunner(
        ProfileStore? profileStore = null,
        Func<IReadOnlyList<Assembly>>? manifest = null)
        : this(profileStore, manifest, null, null)
    {
    }

    /// <summary>Initializes a CLI runner with injectable profiles, manifests, and environment values.</summary>
    /// <param name="profileStore">The private mcpcli profile store.</param>
    /// <param name="manifest">The lazy Contracts assembly manifest.</param>
    /// <param name="readEnvironment">The environment reader.</param>
    internal CliRunner(
        ProfileStore? profileStore,
        Func<IReadOnlyList<Assembly>>? manifest,
        Func<string, string?>? readEnvironment)
        : this(profileStore, manifest, readEnvironment, null)
    {
    }

    /// <summary>Initializes a CLI runner with injectable profiles, manifests, environment values, and MCP execution.</summary>
    /// <param name="profileStore">The private mcpcli profile store.</param>
    /// <param name="manifest">The lazy Contracts assembly manifest.</param>
    /// <param name="readEnvironment">The environment reader.</param>
    /// <param name="runMcp">The MCP host runner, or the production host runner by default.</param>
    internal CliRunner(
        ProfileStore? profileStore,
        Func<IReadOnlyList<Assembly>>? manifest,
        Func<string, string?>? readEnvironment,
        Func<IHost, CancellationToken, Task<int>>? runMcp)
    {
        _profileStore = profileStore ?? new ProfileStore();
        _manifest = manifest;
        _readEnvironment = readEnvironment;
        _runMcp = runMcp;
    }

    /// <summary>Parses arguments with response-file expansion disabled so <c>@</c> values reach their options verbatim.</summary>
    /// <param name="args">The command-line arguments.</param>
    /// <returns>The parse result ready for invocation.</returns>
    internal ParseResult Parse(IReadOnlyList<string> args)
        => CreateRoot().Parse(args, new ParserConfiguration { ResponseFileTokenReplacer = null });

    private RootCommand CreateRoot()
    {
        RootCommand root = new("Hexalith MCP and CLI gateway tool");
        _globals.AddTo(root);
        root.Subcommands.Add(CreateModules());
        root.Subcommands.Add(CreateOperations());
        root.Subcommands.Add(CreateDescribe());
        root.Subcommands.Add(CreateSend());
        root.Subcommands.Add(CreateQuery());
        root.Subcommands.Add(CreateConfig());
        root.Subcommands.Add(CreateMcp());
        return root;
    }

    private Command CreateModules()
    {
        Command command = new("modules", "List declared modules");
        command.SetAction((parsed, cancellationToken) => RunAsync(parsed,
            (services, settings, token) =>
            {
                CatalogLookupResult<ModulesDocument> result = services.GetRequiredService<ICatalog>().ListModules();
                return CliOutput.WriteAsync(result.Document, result.Error, settings, token, tabular: true);
            }, cancellationToken));
        return command;
    }

    private Command CreateOperations()
    {
        Argument<string?> module = new("module") { Description = "Canonical module name", Arity = ArgumentArity.ZeroOrOne };
        Option<string?> kind = new("--kind") { Description = "read or write" };
        Command command = new("operations", "List a module's operations");
        command.Arguments.Add(module);
        command.Options.Add(kind);
        command.SetAction((parsed, cancellationToken) => RunAsync(parsed,
            (services, settings, token) =>
            {
                string? name = parsed.GetValue(module);
                if (string.IsNullOrWhiteSpace(name))
                {
                    return CliOutput.WriteErrorAsync(Invalid("module", "module is required and must be non-empty"), token);
                }

                string? filter = parsed.GetValue(kind);
                if (filter is not null && filter is not ("read" or "write"))
                {
                    return CliOutput.WriteErrorAsync(Invalid("kind", "kind must be read or write"), token);
                }

                CatalogLookupResult<OperationsDocument> result = services.GetRequiredService<ICatalog>().ListOperations(name, filter);
                return CliOutput.WriteAsync(result.Document, result.Error, settings, token, tabular: true);
            }, cancellationToken));
        return command;
    }

    private Command CreateDescribe()
    {
        Argument<string?> operation = new("operation") { Description = "Canonical operation name", Arity = ArgumentArity.ZeroOrOne };
        Option<bool> lint = new("--lint") { Description = "Exit 1 when description lint findings exist" };
        Command command = new("describe", "Describe one operation");
        command.Arguments.Add(operation);
        command.Options.Add(lint);
        command.SetAction((parsed, cancellationToken) => RunAsync(parsed,
            async (services, settings, token) =>
            {
                string? name = parsed.GetValue(operation);
                if (string.IsNullOrWhiteSpace(name))
                {
                    return await CliOutput.WriteErrorAsync(Invalid("operation", "operation is required and must be non-empty"), token)
                        .ConfigureAwait(false);
                }

                CatalogLookupResult<OperationDescriptionDocument> result = services.GetRequiredService<ICatalog>().Describe(name);
                int exit = await CliOutput.WriteAsync(result.Document, result.Error, settings, token).ConfigureAwait(false);
                return exit == 0 && parsed.GetValue(lint) && result.Document!.LintFindings.Count > 0 ? 1 : exit;
            }, cancellationToken));
        return command;
    }

    private Command CreateSend()
    {
        Argument<string?> operation = new("operation") { Description = "Canonical write operation", Arity = ArgumentArity.ZeroOrOne };
        Option<string?> payload = new("--payload") { Description = "JSON, @file, or - for stdin" };
        Option<string?> aggregateId = new("--aggregate-id");
        Option<string?> correlationId = new("--correlation-id");
        Option<string?> idempotencyKey = new("--idempotency-key");
        Option<string[]> extensions = new("--extension") { Description = "Allowlisted key=value; repeatable" };
        Command command = new("send", "Submit a declared command");
        command.Arguments.Add(operation);
        command.Options.Add(payload);
        command.Options.Add(aggregateId);
        command.Options.Add(correlationId);
        command.Options.Add(idempotencyKey);
        command.Options.Add(extensions);
        command.SetAction((parsed, cancellationToken) => RunAsync(parsed,
            async (services, settings, token) =>
            {
                string? name = parsed.GetValue(operation);
                if (string.IsNullOrWhiteSpace(name))
                {
                    return await CliOutput.WriteErrorAsync(Invalid("operation", "operation is required and must be non-empty"), token)
                        .ConfigureAwait(false);
                }

                string? content = await ReadPayloadAsync(parsed.GetValue(payload), token).ConfigureAwait(false);
                if (content is null)
                {
                    return await CliOutput.WriteErrorAsync(Invalid("payload", "payload JSON, @file, or stdin is required"), token)
                        .ConfigureAwait(false);
                }

                var map = new Dictionary<string, string>(StringComparer.Ordinal);
                foreach (string entry in parsed.GetValue(extensions) ?? [])
                {
                    int separator = entry.IndexOf('=');
                    if (separator < 1 || !map.TryAdd(entry[..separator], entry[(separator + 1)..]))
                    {
                        return await CliOutput.WriteErrorAsync(Invalid("extensions", "each extension must be a unique key=value"), token)
                            .ConfigureAwait(false);
                    }
                }

                var call = new SendCommandArguments(name, content, AggregateId: parsed.GetValue(aggregateId),
                    CorrelationId: parsed.GetValue(correlationId), IdempotencyKey: parsed.GetValue(idempotencyKey),
                    Extensions: map.Count == 0 ? null : map);
                OperationOutcome result = await services.GetRequiredService<IOperationExecutor>()
                    .ExecuteAsync(call, services.GetRequiredService<EnvelopeContext>(), token).ConfigureAwait(false);
                return await CliOutput.WriteAsync(result.Document, result.Error, settings, token).ConfigureAwait(false);
            }, cancellationToken));
        return command;
    }

    private Command CreateQuery()
    {
        Argument<string?> operation = new("operation") { Description = "Canonical read operation", Arity = ArgumentArity.ZeroOrOne };
        Option<string?> payload = new("--payload") { Description = "JSON, @file, or - for stdin" };
        Option<string?> aggregateId = new("--aggregate-id");
        Option<string?> entityId = new("--entity-id");
        Option<int?> pageSize = new("--page-size");
        Option<int?> offset = new("--offset");
        Option<string?> cursor = new("--cursor");
        Command command = new("query", "Run a declared query");
        command.Arguments.Add(operation);
        command.Options.Add(payload);
        command.Options.Add(aggregateId);
        command.Options.Add(entityId);
        command.Options.Add(pageSize);
        command.Options.Add(offset);
        command.Options.Add(cursor);
        command.SetAction((parsed, cancellationToken) => RunAsync(parsed,
            async (services, settings, token) =>
            {
                string? name = parsed.GetValue(operation);
                if (string.IsNullOrWhiteSpace(name))
                {
                    return await CliOutput.WriteErrorAsync(Invalid("operation", "operation is required and must be non-empty"), token)
                        .ConfigureAwait(false);
                }

                string? content = await ReadPayloadAsync(parsed.GetValue(payload), token).ConfigureAwait(false);
                if (content is null)
                {
                    return await CliOutput.WriteErrorAsync(Invalid("payload", "payload JSON, @file, or stdin is required"), token)
                        .ConfigureAwait(false);
                }

                var call = new RunQueryArguments(name, content, AggregateId: parsed.GetValue(aggregateId),
                    EntityId: parsed.GetValue(entityId), PageSize: parsed.GetValue(pageSize),
                    Offset: parsed.GetValue(offset), Cursor: parsed.GetValue(cursor));
                OperationOutcome result = await services.GetRequiredService<IOperationExecutor>()
                    .ExecuteAsync(call, services.GetRequiredService<EnvelopeContext>(), token).ConfigureAwait(false);
                return await CliOutput.WriteAsync(result.Document, result.Error, settings, token).ConfigureAwait(false);
            }, cancellationToken));
        return command;
    }

    private Command CreateConfig()
    {
        Command config = new("config", "Inspect and manage mcpcli profile settings");
        Command current = new("current", "Show resolved settings and sources");
        current.SetAction((parsed, cancellationToken) => RunAsync(parsed,
            (services, settings, token) =>
            {
                _ = services;
                object document = new
                {
                    profile = settings.Profile,
                    url = settings.Url?.ToString(),
                    token = ProfileStore.MaskToken(settings.Token),
                    settings.Tenant,
                    settings.Actor,
                    settings.AllowTenantOverride,
                    allowedExtensions = settings.AllowedExtensions
                        .OrderBy(extension => extension, StringComparer.OrdinalIgnoreCase)
                        .ThenBy(extension => extension, StringComparer.Ordinal)
                        .ToArray(),
                    settings.Format,
                    settings.Output,
                    settings.ReadOnly,
                    settings.Strict,
                    settings.Sources,
                };
                return CliOutput.WriteAsync(document, null, settings, token, tabular: true);
            }, cancellationToken));
        config.Subcommands.Add(current);
        config.Subcommands.Add(CreateConfigProfile());
        config.Subcommands.Add(CreateConfigUse());
        config.Subcommands.Add(CreateConfigSet());
        return config;
    }

    private Command CreateConfigProfile()
    {
        Command profile = new("profile", "Manage named connection profiles");
        Command list = new("list", "List profile names and masked credentials");
        list.SetAction((parsed, token) => RunManagementAsync(parsed, (_, settings, cancellationToken) =>
        {
            ProfileSnapshot snapshot = _profileStore.Read();
            object document = new
            {
                activeProfile = snapshot.ActiveProfile,
                profiles = snapshot.Profiles.OrderBy(entry => entry.Key, StringComparer.Ordinal)
                    .Select(entry => new
                    {
                        name = entry.Key,
                        url = entry.Value.Url,
                        token = ProfileStore.MaskToken(entry.Value.Token),
                        format = entry.Value.Format,
                        tenant = entry.Value.Tenant,
                        actor = entry.Value.Actor,
                        allowTenantOverride = entry.Value.AllowTenantOverride,
                        allowedExtensions = entry.Value.AllowedExtensions ?? [],
                    }).ToArray(),
            };
            return CliOutput.WriteAsync(document, null, settings, cancellationToken, tabular: true);
        }, token));

        Argument<string?> addName = new("name") { Arity = ArgumentArity.ZeroOrOne };
        Command add = new("add", "Add or replace a connection profile from --url, --token, and --format; set operator fields with config set");
        add.Arguments.Add(addName);
        add.SetAction((parsed, token) =>
        {
            // Operator settings are edited only through config set; an explicit flag here is refused, never dropped.
            OperationError? operatorFlag = RejectOperatorFlags(_globals.Read(parsed));
            return operatorFlag is not null
                ? CliOutput.WriteErrorAsync(operatorFlag, token)
                : RunManagementAsync(parsed,
                    (_, settings, cancellationToken) => AddProfileAsync(parsed, addName, settings, cancellationToken), token);
        });

        Argument<string?> removeName = new("name") { Arity = ArgumentArity.ZeroOrOne };
        Command remove = new("remove", "Remove a connection profile");
        remove.Arguments.Add(removeName);
        remove.SetAction((parsed, token) => RunManagementAsync(parsed, (_, settings, cancellationToken) =>
        {
            string? name = parsed.GetValue(removeName);
            if (name is null)
            {
                return CliOutput.WriteErrorAsync(Invalid("name", "profile name is required"), cancellationToken);
            }

            ProfileSnapshot snapshot = _profileStore.Remove(name);
            return CliOutput.WriteAsync(new { name, activeProfile = snapshot.ActiveProfile }, null, settings, cancellationToken, tabular: true);
        }, token));

        profile.Subcommands.Add(list);
        profile.Subcommands.Add(add);
        profile.Subcommands.Add(remove);
        return profile;
    }

    private Task<int> AddProfileAsync(ParseResult parsed, Argument<string?> addName, ResolvedSettings settings,
        CancellationToken cancellationToken)
    {
        string? name = parsed.GetValue(addName);
        SettingsInput input = _globals.Read(parsed);
        if (name is null)
        {
            return CliOutput.WriteErrorAsync(Invalid("name", "profile name is required"), cancellationToken);
        }

        if (input.Url is null)
        {
            return CliOutput.WriteErrorAsync(Invalid("url", "--url is required for profile add"), cancellationToken);
        }

        // Add replaces the whole record with only the supplied connection fields; the store rejects a
        // supplied-but-invalid name or value as configuration_invalid.
        ProfileSnapshot snapshot = _profileStore.Add(name, new ConnectionProfile(input.Url, input.Token, input.Format));
        return CliOutput.WriteAsync(new { name, activeProfile = snapshot.ActiveProfile }, null, settings, cancellationToken, tabular: true);
    }

    private static OperationError? RejectOperatorFlags(SettingsInput input)
        => input.Tenant is not null ? OperatorFlag("tenant", "--tenant")
            : input.Actor is not null ? OperatorFlag("actor", "--actor")
            : input.AllowTenantOverride is not null ? OperatorFlag("allowTenantOverride", "--allow-tenant-override")
            : null;

    private static OperationError OperatorFlag(string field, string flag)
        => Invalid(field, $"config profile add does not accept {flag} and wrote nothing; rerun it without {flag}, then run config set PROFILE {field} VALUE");

    private Command CreateConfigUse()
    {
        Argument<string?> name = new("name") { Arity = ArgumentArity.ZeroOrOne };
        Option<bool> clear = new("--clear") { Description = "Clear the active profile" };
        Command use = new("use", "Select or clear the active profile");
        use.Arguments.Add(name);
        use.Options.Add(clear);
        use.SetAction((parsed, token) => RunManagementAsync(parsed, (_, settings, cancellationToken) =>
        {
            string? selected = parsed.GetValue(name);
            bool shouldClear = parsed.GetValue(clear);
            if (shouldClear == (selected is not null))
            {
                return CliOutput.WriteErrorAsync(Invalid("name", "provide a profile name or --clear"), cancellationToken);
            }

            ProfileSnapshot snapshot = _profileStore.Use(shouldClear ? null : selected);
            return CliOutput.WriteAsync(new { activeProfile = snapshot.ActiveProfile }, null, settings, cancellationToken, tabular: true);
        }, token));
        return use;
    }

    private Command CreateConfigSet()
    {
        Argument<string?> name = new("profile") { Arity = ArgumentArity.ZeroOrOne };
        Argument<string?> field = new("field") { Arity = ArgumentArity.ZeroOrOne };
        Argument<string?> value = new("value") { Arity = ArgumentArity.ZeroOrOne };
        Command set = new("set", "Set tenant, actor, allowTenantOverride, or allowedExtensions");
        set.Arguments.Add(name);
        set.Arguments.Add(field);
        set.Arguments.Add(value);
        set.SetAction((parsed, token) => RunManagementAsync(parsed, (_, settings, cancellationToken) =>
        {
            string? selected = parsed.GetValue(name);
            string? key = parsed.GetValue(field);
            string? content = parsed.GetValue(value);
            if (selected is null || key is null || content is null)
            {
                return CliOutput.WriteErrorAsync(Invalid("set", "profile, field, and value are required"), cancellationToken);
            }

            // Supplied names, fields, and values are validated by the store and fail as configuration_invalid.
            _profileStore.Set(selected, key, content);
            return CliOutput.WriteAsync(new { profile = selected, field = key }, null, settings, cancellationToken, tabular: true);
        }, token));
        return set;
    }

    private Command CreateMcp()
    {
        Option<string?> transport = new("--transport") { Description = "stdio or http" };
        Command command = new("mcp", "Serve the generic MCP tools over stdio");
        command.Options.Add(transport);
        command.SetAction((parsed, cancellationToken) => RunMcpAsync(parsed, parsed.GetValue(transport), cancellationToken));
        return command;
    }

    private async Task<int> RunMcpAsync(ParseResult parsed, string? transport, CancellationToken cancellationToken)
    {
        if (transport is not null && transport != "stdio")
        {
            return await WriteMcpErrorAsync(new OperationError("unsupported_transport",
                Message: "Only stdio transport is available."), cancellationToken).ConfigureAwait(false);
        }

        try
        {
            SettingsInput input = _globals.Read(parsed);
            if (input.Format is not null && input.Format != "json")
            {
                return await WriteMcpErrorAsync(Invalid("format", "MCP stdio accepts only explicit json format."),
                    cancellationToken).ConfigureAwait(false);
            }

            if (input.Output is not null)
            {
                return await WriteMcpErrorAsync(Invalid("output", "MCP stdio cannot write protocol output to a file."),
                    cancellationToken).ConfigureAwait(false);
            }

            IHost? created = HostFactory.Create(input, _profileStore, out OperationError? error,
                mcp: true, _manifest, _readEnvironment);
            using IHost? host = created;
            if (error is not null)
            {
                return await WriteMcpErrorAsync(error, cancellationToken).ConfigureAwait(false);
            }

            IHost invocationHost = host ?? throw new InvalidOperationException("Settings resolution produced no host or error.");
            ResolvedSettings settings = invocationHost.Services.GetRequiredService<ResolvedSettings>();
            CatalogAccess catalog = invocationHost.Services.GetRequiredService<CatalogProvider>().Get(settings.Strict);
            if (catalog.Catalog is null)
            {
                return await WriteMcpErrorAsync(new OperationError(catalog.ErrorCode ?? "internal_error",
                    Message: catalog.Message), cancellationToken).ConfigureAwait(false);
            }

            return _runMcp is null
                ? await RunMcpHostAsync(invocationHost, cancellationToken).ConfigureAwait(false)
                : await _runMcp(invocationHost, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or InvalidDataException)
        {
            return await WriteMcpErrorAsync(new OperationError("configuration_invalid", Message: exception.Message),
                cancellationToken).ConfigureAwait(false);
        }
        catch (Exception)
        {
            return await WriteMcpErrorAsync(new OperationError("internal_error", Message: "MCP startup failed."),
                cancellationToken).ConfigureAwait(false);
        }
    }

    private static async Task<int> WriteMcpErrorAsync(OperationError error, CancellationToken cancellationToken)
    {
        await Console.Error.WriteLineAsync(JsonSerializer.Serialize(new { error }, McpCliJson.Result).AsMemory(),
            cancellationToken).ConfigureAwait(false);
        return 2;
    }

    private static async Task<int> RunMcpHostAsync(IHost host, CancellationToken cancellationToken)
    {
        await host.RunAsync(cancellationToken).ConfigureAwait(false);
        return 0;
    }

    private Task<int> RunAsync(ParseResult parsed,
        Func<IServiceProvider, ResolvedSettings, CancellationToken, Task<int>> action,
        CancellationToken cancellationToken)
        => RunAsync(parsed, action, presentationOnly: false, cancellationToken);

    private Task<int> RunManagementAsync(ParseResult parsed,
        Func<IServiceProvider, ResolvedSettings, CancellationToken, Task<int>> action,
        CancellationToken cancellationToken)
        => RunAsync(parsed, action, presentationOnly: true, cancellationToken);

    private async Task<int> RunAsync(ParseResult parsed,
        Func<IServiceProvider, ResolvedSettings, CancellationToken, Task<int>> action,
        bool presentationOnly,
        CancellationToken cancellationToken)
    {
        try
        {
            IHost? created = HostFactory.Create(_globals.Read(parsed), _profileStore, out OperationError? error,
                manifest: _manifest, readEnvironment: _readEnvironment, presentationOnly: presentationOnly);
            if (error is not null)
            {
                return await CliOutput.WriteErrorAsync(error, cancellationToken).ConfigureAwait(false);
            }

            using IHost host = created ?? throw new InvalidOperationException("Settings resolution produced no host or error.");
            ResolvedSettings settings = host.Services.GetRequiredService<ResolvedSettings>();
            return await action(host.Services, settings, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or InvalidDataException)
        {
            return await CliOutput.WriteErrorAsync(new OperationError("configuration_invalid", Message: exception.Message),
                cancellationToken).ConfigureAwait(false);
        }
        catch (Exception)
        {
            return await CliOutput.WriteErrorAsync(new OperationError("internal_error", Message: "The CLI action failed."),
                cancellationToken).ConfigureAwait(false);
        }
    }

    private static async Task<string?> ReadPayloadAsync(string? input, CancellationToken cancellationToken)
    {
        if (input is null)
        {
            return null;
        }

        if (input == "-")
        {
            return await Console.In.ReadToEndAsync(cancellationToken).ConfigureAwait(false);
        }

        return input.StartsWith('@') ? await File.ReadAllTextAsync(input[1..], cancellationToken).ConfigureAwait(false) : input;
    }

    private static OperationError Invalid(string argument, string message)
        => new("invalid_arguments", Message: message, Argument: argument);
}

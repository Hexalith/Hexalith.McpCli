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

    internal CliRunner(ProfileStore? profileStore = null, Func<IReadOnlyList<Assembly>>? manifest = null)
    {
        _profileStore = profileStore ?? new ProfileStore();
        _manifest = manifest;
    }

    internal RootCommand CreateRoot()
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
                    settings.AllowedExtensions,
                    settings.Format,
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
        list.SetAction((parsed, token) => RunAsync(parsed, (_, settings, cancellationToken) =>
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
        Command add = new("add", "Add or replace a connection profile");
        add.Arguments.Add(addName);
        add.SetAction((parsed, token) => RunAsync(parsed, (_, settings, cancellationToken) =>
        {
            string? name = parsed.GetValue(addName);
            SettingsInput input = _globals.Read(parsed);
            if (string.IsNullOrWhiteSpace(name))
            {
                return CliOutput.WriteErrorAsync(Invalid("name", "profile name is required"), cancellationToken);
            }

            if (input.Url is null)
            {
                return CliOutput.WriteErrorAsync(Invalid("url", "--url is required for profile add"), cancellationToken);
            }

            ProfileSnapshot snapshot = _profileStore.Add(name,
                new ConnectionProfile(input.Url, input.Token, input.Format ?? "json"));
            return CliOutput.WriteAsync(new { name, activeProfile = snapshot.ActiveProfile }, null, settings, cancellationToken, tabular: true);
        }, token));

        Argument<string?> removeName = new("name") { Arity = ArgumentArity.ZeroOrOne };
        Command remove = new("remove", "Remove a connection profile");
        remove.Arguments.Add(removeName);
        remove.SetAction((parsed, token) => RunAsync(parsed, (_, settings, cancellationToken) =>
        {
            string? name = parsed.GetValue(removeName);
            if (string.IsNullOrWhiteSpace(name))
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

    private Command CreateConfigUse()
    {
        Argument<string?> name = new("name") { Arity = ArgumentArity.ZeroOrOne };
        Option<bool> clear = new("--clear") { Description = "Clear the active profile" };
        Command use = new("use", "Select or clear the active profile");
        use.Arguments.Add(name);
        use.Options.Add(clear);
        use.SetAction((parsed, token) => RunAsync(parsed, (_, settings, cancellationToken) =>
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
        set.SetAction((parsed, token) => RunAsync(parsed, (_, settings, cancellationToken) =>
        {
            string? selected = parsed.GetValue(name);
            string? key = parsed.GetValue(field);
            string? content = parsed.GetValue(value);
            if (string.IsNullOrWhiteSpace(selected) || string.IsNullOrWhiteSpace(key) || content is null)
            {
                return CliOutput.WriteErrorAsync(Invalid("set", "profile, field, and value are required"), cancellationToken);
            }

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
            SettingsResolution resolved = Resolve(input);
            if (resolved.Error is not null)
            {
                return await WriteMcpErrorAsync(resolved.Error, cancellationToken).ConfigureAwait(false);
            }

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

            ResolvedSettings settings = resolved.Settings!;
            using IHost host = HostFactory.Create(settings, mcp: true, _manifest);
            CatalogAccess catalog = host.Services.GetRequiredService<CatalogProvider>().Get(settings.Strict);
            if (catalog.Catalog is null)
            {
                return await WriteMcpErrorAsync(new OperationError(catalog.ErrorCode ?? "internal_error",
                    Message: catalog.Message), cancellationToken).ConfigureAwait(false);
            }

            await host.RunAsync(cancellationToken).ConfigureAwait(false);
            return 0;
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

    private async Task<int> RunAsync(ParseResult parsed,
        Func<IServiceProvider, ResolvedSettings, CancellationToken, Task<int>> action,
        CancellationToken cancellationToken)
    {
        try
        {
            SettingsResolution resolved = Resolve(_globals.Read(parsed));
            if (resolved.Error is not null)
            {
                return await CliOutput.WriteErrorAsync(resolved.Error, cancellationToken).ConfigureAwait(false);
            }

            ResolvedSettings settings = resolved.Settings!;
            using IHost host = HostFactory.Create(settings, manifest: _manifest);
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

    private SettingsResolution Resolve(SettingsInput input)
    {
        var environment = new Dictionary<string, string?>(StringComparer.Ordinal);
        foreach (string name in new[]
        {
            "EVENTSTORE_PROFILE", "EVENTSTORE_URL", "EVENTSTORE_TOKEN", "EVENTSTORE_TENANT", "EVENTSTORE_ACTOR",
            "EVENTSTORE_ALLOW_TENANT_OVERRIDE", "EVENTSTORE_FORMAT", "EVENTSTORE_READ_ONLY", "EVENTSTORE_STRICT",
        })
        {
            environment[name] = Environment.GetEnvironmentVariable(name);
        }

        return new SettingsResolver(_profileStore, environment).Resolve(input);
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

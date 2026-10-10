using System.CommandLine;
using System.CommandLine.Completions;
using System.CommandLine.Help;
using System.CommandLine.Parsing;
using System.Reflection;
using System.Text.Json;
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

    /// <summary>Invokes one checked parse, including failures suppressed by help or version.</summary>
    internal async Task<int> InvokeAsync(IReadOnlyList<string> args, CancellationToken cancellationToken = default)
    {
        ParseResult parsed = Parse(args);
        HelpOption helpOption = parsed.RootCommandResult.Command.Options.OfType<HelpOption>().Single();
        var helpAliases = helpOption.Aliases.Append(helpOption.Name)
            .Concat(helpOption.Aliases.Where(alias => alias.StartsWith("-", StringComparison.Ordinal)
                && !alias.StartsWith("--", StringComparison.Ordinal)).Select(alias => "/" + alias[1..]))
            .ToHashSet(StringComparer.Ordinal);
        string? invalidToken = FindInvalidOption(args, parsed, helpAliases, out string invalidArgument);
        OperationError? failure = invalidToken is not null
            ? Invalid(args.TakeWhile(argument => argument != "--").Any(argument => helpAliases.Contains(argument) || argument == "--version")
                ? "arguments" : invalidArgument, "The command contains an unknown or malformed option.")
            : null;

        if (failure is null)
        {
            bool afterSeparator = false;
            bool hasHelp = false;
            bool hasVersion = false;
            var supplied = new List<string>();
            foreach (string argument in args)
            {
                if (argument == "--")
                {
                    afterSeparator = true;
                    supplied.Add(argument);
                    continue;
                }

                if (!afterSeparator && argument == "--version")
                {
                    hasVersion = true;
                }
                else if (!afterSeparator && helpAliases.Contains(argument))
                {
                    hasHelp = true;
                    continue;
                }

                supplied.Add(argument);
            }

            if (hasVersion && (args.Count != 1 || parsed.Errors.Count > 0))
            {
                failure = Invalid("arguments", "Version must be requested alone.");
            }
            else if (hasHelp)
            {
                // Bare help consists solely of the selected command path and help aliases.
                failure = supplied.SequenceEqual(CommandPath(parsed.CommandResult.Command))
                    ? null : Invalid("arguments", "Help must be requested without arguments or options.");
            }
            else if (parsed.Errors.Count > 0)
            {
                failure = ParseFailure(parsed, args);
            }
        }

        if (failure is not null)
        {
            return parsed.CommandResult.Command.Name == "mcp"
                ? await WriteMcpErrorAsync(failure, cancellationToken).ConfigureAwait(false)
                : await CliOutput.WriteErrorAsync(failure, cancellationToken).ConfigureAwait(false);
        }

        return await parsed.InvokeAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    private static string OptionName(string token)
    {
        int equal = token.IndexOf('=');
        int colon = token.IndexOf(':');
        int split = equal < 0 ? colon : colon < 0 ? equal : Math.Min(equal, colon);
        return split < 0 ? token : token[..split];
    }

    private static string? FindInvalidOption(IReadOnlyList<string> args, ParseResult parsed,
        HashSet<string> helpAliases, out string invalidArgument)
    {
        invalidArgument = "arguments";
        var names = parsed.RootCommandResult.Command.Options.Concat(parsed.CommandResult.Command.Options)
            .SelectMany(option => option.Aliases.Append(option.Name))
            .ToHashSet(StringComparer.Ordinal);
        bool afterSeparator = false;
        bool leadingDirectiveRun = true;
        for (int index = 0; index < args.Count; index++)
        {
            string token = args[index];
            if (leadingDirectiveRun)
            {
                if (token == parsed.RootCommandResult.Command.Name)
                {
                    continue;
                }

                if (token.Length > 2 && token[0] == '[' && token[1] is not (']' or ':') && token[^1] == ']')
                {
                    return token;
                }

                leadingDirectiveRun = false;
            }

            if (token == "--")
            {
                afterSeparator = true;
                continue;
            }

            if (afterSeparator || token == "-")
            {
                continue;
            }

            if (!token.StartsWith("-", StringComparison.Ordinal) && !token.StartsWith("/", StringComparison.Ordinal))
            {
                continue;
            }

            string name = OptionName(token);
            if (helpAliases.Contains(name) || name == "--version")
            {
                if (token != name)
                {
                    return token;
                }

                continue;
            }

            if (!token.StartsWith("-", StringComparison.Ordinal))
            {
                continue;
            }

            if (!names.Contains(name))
            {
                return token;
            }

            if (name is "--read-only" or "--strict" or "--allow-tenant-override" or "--clear" or "--lint"
                && token != name && !bool.TryParse(token[(name.Length + 1)..], out _))
            {
                invalidArgument = GlobalOptionsBinding.PublicArgumentName(name);
                return token;
            }

            if (name == "--transport" && token.Length > name.Length
                && token[(name.Length + 1)..].StartsWith("-", StringComparison.Ordinal))
            {
                return token;
            }

            if (token == name && index + 1 < args.Count && args[index + 1] != "--")
            {
                string next = args[index + 1];
                string nextName = OptionName(next);
                if ((helpAliases.Contains(nextName) || nextName == "--version") && next != nextName)
                {
                    return next;
                }

                if (!next.StartsWith("--", StringComparison.Ordinal)
                    && (name != "--transport" || !next.StartsWith("-", StringComparison.Ordinal)))
                {
                    // The parser decides whether this token is a value or a positional argument.
                    if (name is not ("--read-only" or "--strict" or "--allow-tenant-override" or "--clear" or "--lint")
                        || bool.TryParse(next, out _))
                    {
                        index++;
                    }
                }
            }
        }

        return null;
    }

    private static OperationError ParseFailure(ParseResult parsed, IReadOnlyList<string> args)
    {
        string? option = parsed.Errors.Select(error => error.SymbolResult)
            .OfType<OptionResult>().Select(result => result.Option.Name).FirstOrDefault();
        if (option is null)
        {
            bool afterSeparator = false;
            for (int index = 0; index < args.Count; index++)
            {
                string token = args[index];
                if (token == "--")
                {
                    afterSeparator = true;
                    continue;
                }

                if (afterSeparator)
                {
                    continue;
                }

                string name = OptionName(token);
                if (name is not ("--read-only" or "--strict" or "--allow-tenant-override" or "--clear" or "--lint"))
                {
                    continue;
                }

                string? value = token == name
                    ? index + 1 < args.Count && args[index + 1] != "--"
                        && !args[index + 1].StartsWith("-", StringComparison.Ordinal) ? args[index + 1] : null
                    : token[(name.Length + 1)..];
                if (value is not null && parsed.UnmatchedTokens.Contains(value) && !bool.TryParse(value, out _))
                {
                    option = name;
                    break;
                }
            }
        }

        string argument = option is null ? "arguments" : GlobalOptionsBinding.PublicArgumentName(option);
        return Invalid(argument, "The command arguments are missing or invalid.");
    }

    private static string[] CommandPath(Command command)
    {
        var parts = new List<string>();
        for (Command? current = command; current?.Parents.OfType<Command>().FirstOrDefault() is Command parent; current = parent)
        {
            parts.Add(current.Name);
        }

        parts.Reverse();
        return parts.ToArray();
    }

    private RootCommand CreateRoot()
    {
        RootCommand root = new("Hexalith MCP and CLI gateway tool");
        root.Directives.Remove(root.Directives.OfType<SuggestDirective>().Single());
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
                return CliOutput.WriteAsync(result.Document, result.Error, settings, token, tableHeader: "NAME\tOPERATIONS\tDESCRIPTION");
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
                return CliOutput.WriteAsync(result.Document, result.Error, settings, token, tableHeader: "NAME\tKIND\tDESCRIPTION");
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
        Option<string?> aggregateId = new("--aggregate-id") { Description = "Must equal the payload aggregate identifier; canonical uppercase ULID in ULID-kind modules" };
        Option<string?> correlationId = new("--correlation-id") { Description = "Caller-supplied canonical uppercase ULID correlation identifier" };
        Option<string?> idempotencyKey = new("--idempotency-key") { Description = "Caller-supplied canonical uppercase ULID idempotency key" };
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

                if (settings.ReadOnly)
                {
                    // Core owns lookup, kind, and availability ordering; no payload input is needed for refusal.
                    OperationOutcome refusal = await services.GetRequiredService<IOperationExecutor>()
                        .ExecuteAsync(new SendCommandArguments(name, string.Empty),
                            services.GetRequiredService<EnvelopeContext>(), token).ConfigureAwait(false);
                    return await CliOutput.WriteAsync(refusal.Document, refusal.Error, settings, token).ConfigureAwait(false);
                }

                (string? content, bool fileReadFailed) = await ReadPayloadAsync(parsed.GetValue(payload), token).ConfigureAwait(false);
                if (fileReadFailed)
                {
                    return await CliOutput.WriteErrorAsync(Invalid("payload", "Unable to read the payload file."), token)
                        .ConfigureAwait(false);
                }

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
                    .ExecuteAsync(call, services.GetRequiredService<EnvelopeContext>(), token,
                        _ => Task.FromResult(PreflightError(settings.Output))).ConfigureAwait(false);
                return await CliOutput.WriteAsync(result.Document, result.Error, settings, token).ConfigureAwait(false);
            }, cancellationToken));
        return command;
    }

    private Command CreateQuery()
    {
        Argument<string?> operation = new("operation") { Description = "Canonical read operation", Arity = ArgumentArity.ZeroOrOne };
        Option<string?> payload = new("--payload") { Description = "JSON, @file, or - for stdin" };
        Option<string?> aggregateId = new("--aggregate-id") { Description = "Explicit aggregate identifier; canonical uppercase ULID in ULID-kind modules" };
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

                (string? content, bool fileReadFailed) = await ReadPayloadAsync(parsed.GetValue(payload), token).ConfigureAwait(false);
                if (fileReadFailed)
                {
                    return await CliOutput.WriteErrorAsync(Invalid("payload", "Unable to read the payload file."), token)
                        .ConfigureAwait(false);
                }

                if (content is null)
                {
                    return await CliOutput.WriteErrorAsync(Invalid("payload", "payload JSON, @file, or stdin is required"), token)
                        .ConfigureAwait(false);
                }

                var call = new RunQueryArguments(name, content, AggregateId: parsed.GetValue(aggregateId),
                    EntityId: parsed.GetValue(entityId), PageSize: parsed.GetValue(pageSize),
                    Offset: parsed.GetValue(offset), Cursor: parsed.GetValue(cursor));
                OperationOutcome result = await services.GetRequiredService<IOperationExecutor>()
                    .ExecuteAsync(call, services.GetRequiredService<EnvelopeContext>(), token,
                        _ => Task.FromResult(PreflightError(settings.Output))).ConfigureAwait(false);
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
                return CliOutput.WriteAsync(document, null, settings, token, tableHeader: "FIELD\tVALUE");
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
            return CliOutput.WriteAsync(document, null, settings, cancellationToken, tableHeader: "FIELD\tVALUE");
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

            _profileStore.ValidateRemove(name);
            CliOutput.Preflight(settings.Output);
            ProfileSnapshot snapshot = _profileStore.Remove(name);
            return CliOutput.WriteAsync(new { name, activeProfile = snapshot.ActiveProfile }, null, settings, cancellationToken, tableHeader: "FIELD\tVALUE");
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
        var profile = new ConnectionProfile(input.Url, input.Token, input.Format);
        _profileStore.ValidateAdd(name, profile);
        CliOutput.Preflight(settings.Output);
        ProfileSnapshot snapshot = _profileStore.Add(name, profile);
        return CliOutput.WriteAsync(new { name, activeProfile = snapshot.ActiveProfile }, null, settings, cancellationToken, tableHeader: "FIELD\tVALUE");
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

            _profileStore.ValidateUse(shouldClear ? null : selected);
            CliOutput.Preflight(settings.Output);
            ProfileSnapshot snapshot = _profileStore.Use(shouldClear ? null : selected);
            return CliOutput.WriteAsync(new { activeProfile = snapshot.ActiveProfile }, null, settings, cancellationToken, tableHeader: "FIELD\tVALUE");
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
            _profileStore.ValidateSet(selected, key, content);
            CliOutput.Preflight(settings.Output);
            _profileStore.Set(selected, key, content);
            return CliOutput.WriteAsync(new { profile = selected, field = key }, null, settings, cancellationToken, tableHeader: "FIELD\tVALUE");
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
                Message: "Only stdio transport is available; HTTP transport is planned for the next release."), cancellationToken).ConfigureAwait(false);
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
        catch (Exception)
        {
            return await WriteMcpErrorAsync(new OperationError("internal_error", Message: "MCP server failed."),
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
        // Host configuration errors can name files; only profile validation inside the action is echoed.
        bool actionStarted = false;
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
            actionStarted = true;
            return await action(host.Services, settings, cancellationToken).ConfigureAwait(false);
        }
        catch (OutputPreflightException)
        {
            return await CliOutput.WriteErrorAsync(new OperationError("internal_error",
                Message: CliOutput.PreflightFailureMessage), cancellationToken).ConfigureAwait(false);
        }
        catch (InvalidDataException exception) when (presentationOnly && actionStarted)
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

    private static async Task<(string? Content, bool FileReadFailed)> ReadPayloadAsync(string? input, CancellationToken cancellationToken)
    {
        if (input is null)
        {
            return (null, false);
        }

        if (input == "-")
        {
            return (await Console.In.ReadToEndAsync(cancellationToken).ConfigureAwait(false), false);
        }

        if (!input.StartsWith('@'))
        {
            return (input, false);
        }

        try
        {
            return (await File.ReadAllTextAsync(input[1..], cancellationToken).ConfigureAwait(false), false);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or ArgumentException or NotSupportedException)
        {
            return (null, true);
        }
    }

    private static OperationError? PreflightError(string? output)
    {
        try
        {
            CliOutput.Preflight(output);
            return null;
        }
        catch (OutputPreflightException)
        {
            return new OperationError("internal_error", Message: CliOutput.PreflightFailureMessage);
        }
    }

    private static OperationError Invalid(string argument, string message)
        => new("invalid_arguments", Message: message, Argument: argument);
}

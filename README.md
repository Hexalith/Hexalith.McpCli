# Hexalith.McpCli

Hexalith.McpCli provides a shared MCP server and CLI for decorated Hexalith Contracts libraries.

Contracts authors reference `Hexalith.McpCli.Abstractions` and declare one module on the assembly. Place each operation type in its own file:

```csharp
// Module.cs
using Hexalith.McpCli.Abstractions;
[assembly: HexalithModule("inventory", "Manage inventory items.", IdentifierKind.Ulid,
    WireTypeConvention = WireTypeConvention.KebabCase)]
```

```csharp
// CreateItemCommand.cs
using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

[HexalithCommand("Create an inventory item.", Domain = "inventory",
    AggregateIdProperty = nameof(ItemId))]
public sealed record CreateItemCommand(
    [property: HexalithIdentifier, Description("The item's ULID.")] string ItemId);
```

```csharp
// GetItemQuery.cs
using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

[HexalithQuery("Read an inventory item.", Domain = "inventory",
    AggregateIdProperty = nameof(ItemId), ProjectionType = "inventory-items")]
public sealed record GetItemQuery(
    [property: HexalithIdentifier, Description("The item's ULID.")] string ItemId);
```

The module's identifier kind applies to `[HexalithIdentifier]` properties and aggregate identifier properties. Descriptions are required constructor arguments; routing values can instead come from the EventStore contract interfaces.

The `Hexalith.McpCli.Abstractions` package includes a build analyzer. Diagnostic `MCPCLI001` warns on a command or query type whose `[HexalithCommand]` or `[HexalithQuery]` description is empty, whitespace, or null. Supply a nonblank description to resolve it. The analyzer requires .NET SDK 10.0.4xx or later; an older SDK may report `CS9057` because its compiler cannot load the analyzer's Roslyn version. Contracts projects need only the Abstractions package reference.

## Bootstrap package release

The independent [Bootstrap package workflow](https://github.com/Hexalith/Hexalith.McpCli/blob/main/.github/workflows/bootstrap-package.yml) restores and builds only Abstractions and its bundled analyzer production projects. It runs the Abstractions and analyzer author-time tests (including synthetic Contracts fixtures), release rejection tests, and a decorated consumer build with a fresh package cache, explicit NuGet configuration and cleared fallback folders. Its deliberately blank description must produce exactly one `MCPCLI001` warning, proving the packaged analyzer loads. This gate needs no decorated upstream module, tool build, Aspire tier, or FR-22 evidence.

[`Hexalith.McpCli.Abstractions`](https://www.nuget.org/packages/Hexalith.McpCli.Abstractions) has no consumer-visible package dependencies. A standalone .NET 10 Contracts consumer pins one verified published version with a single exact reference, for example:

```xml
<PackageReference Include="Hexalith.McpCli.Abstractions" Version="[1.0.0]" />
```

Hexalith Contracts repositories use central package management. Their Builds catalog supplies `HexalithMcpCliVersion` and `<PackageVersion Include="Hexalith.McpCli.Abstractions" Version="$(HexalithMcpCliVersion)" />`; the Contracts project uses a versionless reference:

```xml
<PackageReference Include="Hexalith.McpCli.Abstractions" />
```

For a local gate, use a fresh checkout with the root-declared Builds submodule available:

```sh
bash -euo pipefail <<'EOF'
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
for project in Abstractions Analyzers; do
  test_project="tests/Hexalith.McpCli.${project}.Tests"
  dotnet restore "$test_project"
  dotnet build "$test_project" --configuration Release --no-restore -warnaserror
  dotnet test "$test_project" --configuration Release --no-build
done
MCPCLI_RELEASE_PHASE=bootstrap bash scripts/release-prepare.sh 1.0.0
EOF
```

Preparation restores/builds the Abstractions project, packs exactly one package into a fresh `nupkgs/bootstrap` directory, and compiles the decorated consumer against those prepared bytes before recording their SHA-256, preparation HEAD and clean-source state in the JSON receipt `nupkgs/bootstrap.sha256`. Publication and recovery require a receipt from clean source at the exact release SHA; a local dirty-source preparation cannot later be published merely by cleaning the checkout. An existing staging directory or receipt is refused; preserve it elsewhere before another run. Other artifacts under `nupkgs` are retained. Local preparation and consumer checks require no publication credentials.

Maintainers review and commit the validated source, validate every commit with the pinned commitlint tooling, and integrate it into `main`. Wait for successful **push** runs of `bootstrap-package.yml` and `commitlint.yml` at that exact current main SHA, then dispatch [Release](https://github.com/Hexalith/Hexalith.McpCli/blob/main/.github/workflows/release.yml) from `main` with phase `bootstrap` and an empty recovery version. Both new releases and recovery check current main and its independent results before requesting production approval. The source gate checks the committed checkout and rechecks current main and both results after production environment approval, after preparation before tagging, and immediately before publication. The `production` environment requires a maintainer's approval and accepts deployments only from `main`; self-approval and admin bypass are enabled, so this is a deliberate pause rather than an independent review. The production job uses the `Hexalith` nuget.org trusted-publishing policy bound to `release.yml` and the `production` environment; `NuGet/login` exchanges GitHub OIDC for a short-lived publication key before semantic-release prepares the package. Full-tool CI is independent of bootstrap publication. Phase `paired` remains blocked.

Semantic-release chooses the version, requires a nonblank NuGet key and confirms version availability, prepares and validates the package, and publishes a private snapshot whose hash must match the preparation receipt. NuGet authenticates the key and checks its push permissions at publication; preflight does not validate those permissions. Direct `release-publish.sh` invocation performs the same phase, version, key-presence, registry, staged-content and exact committed-source checks, using `DISPATCH_SHA`, `DISPATCH_REF`, `REPOSITORY` and GitHub authentication; a taken version or uncertain registry response stops publication. The scripts reject extra staged files, the wrong identity/version, missing compile/analyzer DLLs, and consumer dependency leakage. They do not rebuild during publication or skip duplicate versions.

Semantic-release creates `v<version>` before the NuGet push. If publication or GitHub release completion fails after tagging, dispatch [Release](https://github.com/Hexalith/Hexalith.McpCli/blob/main/.github/workflows/release.yml) from `main` with phase `bootstrap` and `recovery_version` set to that version. If the NuGet push may have succeeded, first wait until nuget.org lists the version: the version index lags a successful push while nuget.org validates the package, and a recovery that sees the version as absent pushes again and fails with HTTP 409. Recovery runs in the same trusted `release.yml`/`production` identity, checks that its workflow source is current green main, and checks the local tag against GitHub's tag, its ancestry to current main and successful independent **push** gates for its exact SHA. It preserves the reviewed preparation and recovery helpers before checking out the tag, then rebuilds and consumer-tests the tagged package in bootstrap staging. It publishes only when the version is absent. For a package this run just pushed, it retries a public-download 404 up to 91 attempts, ten seconds apart (15 minutes of waiting); other uncertain responses and a package still unavailable after that bound stop recovery. After that wait expires, wait until nuget.org lists the version before dispatching recovery again; it then takes the already-published path without another push. If already present, it downloads and validates the public package, compares all consumer content with the tagged build, and proves its analyzer loads before completing the GitHub release without another push. NuGet's repository signature and package core-properties metadata are excluded from content comparison; core properties record the packing NuGet version rather than consumer content. This fail-closed comparison requires matching build paths and toolchain versions; if rebuilding changes DLL bytes, recovery needs the original validated artifact and its source-bound receipt. Mismatching contents or uncertain registry responses stop recovery.

The recovery orchestrator sets `MCPCLI_RECOVERY_VERSION` to the requested version when calling the publisher. This switches its source gate from exact current main to the matching green tagged ancestor of current main; a value that differs from the prepared package version is rejected. Direct invocation with this variable follows the same tagged-source policy and still requires the source-bound receipt and all ordinary publication checks.

After each release, record the committed SHA, gate/release URLs, prepared receipt SHA-256, public signed-package SHA-256 and public-feed consumer proof with the release evidence. Preparation and publication print the prepared receipt hash; recovery prints the public signed-package hash. NuGet's repository signature makes the two hashes differ. From the repository root, run the consumer check with the verified published version and a fresh target directory, for example:

```sh
bash scripts/smoke-bootstrap-consumer.sh 1.0.0 https://api.nuget.org/v3/index.json "$(mktemp -d)/consumer"
```

Update the verified published version in `HexalithMcpCliVersion` and the Abstractions entry in the owning Hexalith.Builds catalog, run its documented complete audit refresh and validation, and record the integrated Builds revision.

## Gateway boundary

The CLI and MCP server share one catalog and executor. McpCli discovers operations only from flagged, referenced `*.Contracts` packages. It submits commands and queries to the EventStore gateway; the gateway routes them to the owning module server. McpCli never connects to a module server or references its implementation packages.

`DependencyPolicyTests` enforces this boundary against the restored production graph and project references. `tools/dependency-policy.json` pins the exact closure reachable from the approved stack roots, the Decoration Package, and each flagged Contracts module. A module cannot widen that baseline or import another module's packages. Every rejected dependency includes its resolved identity and path from `Hexalith.McpCli`; every restored package permits only the `Microsoft.NETCore.App` framework reference. Adding a production direct root requires a PRD change and review of `directPackages`.

Test projects may use the policy's `directPackages`, enrolled modules, the Decoration Package, the named test packages (including EventStore testing/Aspire helpers and `Hexalith.Tenants.Aspire`), and the synthetic `Hexalith.McpCli.Sample.Contracts` fixture. Any other package, including one listed only in `baselinePackages`, is rejected as a direct test dependency. The gate checks the references evaluated in Debug and Release, plus every `PackageReference` and `ProjectReference` in the test project file itself, whatever its condition. The test packages and the sample are rejected in the production runtime graph even if added to a production policy list. The build-time analyzer project at `src/Hexalith.McpCli.Analyzers` is excluded from the production source-project checks; it uses `Microsoft.CodeAnalysis.CSharp` and `Microsoft.CodeAnalysis.Analyzers` with `PrivateAssets="all"`. Test projects may reference local `src/` projects and `tests/` fixtures, but cannot reference projects in `references/`. `Hexalith.Parties.Aspire` remains unapproved until published and reviewed.

Offline captured closures prove that decorated Tenants- and Parties-shaped packages can depend on McpCli Abstractions without adding production dependencies. `Hexalith.Projects.Contracts` 1.0.0 remains excluded: its closure adds `Microsoft.AspNetCore.App` and UI/web dependencies such as Fluxor, Fluent UI, and FrontComposer.Shell. Adding those packages to the baseline still fails the gate. Run a fresh `dotnet restore Hexalith.McpCli.slnx` before building and running `tests/Hexalith.McpCli.Manifest.Tests`; the candidate checks read committed fixtures and require no network restore.

The requested Works, Timesheets, Agents, Conversations, Projects, and Folders packages are not enrolled yet. Their current Contracts assemblies lack declarations or live gateway paths required by the [integration spec](https://github.com/Hexalith/Hexalith.McpCli/blob/main/_bmad-output/implementation-artifacts/spec-add-six-domain-modules.md). Until decorated, verified packages are published and pinned, `hexalith modules` returns `catalog_empty`. This is a release readiness state, not a connection failure.

## Run and debug from the Platform workspace

Run and debug McpCli from the Hexalith.Platform workspace, where this repository is the direct `references/Hexalith.McpCli` submodule. [`module/hexalith.module-manifest.v2.json`](https://github.com/Hexalith/Hexalith.McpCli/blob/main/module/hexalith.module-manifest.v2.json) declares McpCli with no servers and no interfaces. Its only dependency is `eventstore`, the gateway McpCli targets, so that gateway is its whole minimum environment. Platform pins a Builds tool of `4.34.0` or later, the first release that builds run-scoped McpCli; the [Platform README](https://github.com/Hexalith/Hexalith.Platform/blob/main/README.md#module-tool) names the current pin. From the Platform root, restore and run that pinned tool:

```sh
dotnet tool restore
dotnet tool run hexalith-module -- debug --manifest references/Hexalith.McpCli/module/hexalith.module-manifest.v2.json
```

The tool starts the EventStore gateway from source. It builds this checkout's `src/Hexalith.McpCli` in Debug into the run workspace, never packs or publishes it, and leaves this checkout's `bin` and `obj` untouched. When the environment is ready, an `HXI010` diagnostic names the run-scoped `Hexalith.McpCli.dll`, and `down` deletes it with the run. A CLI exits after each command, so launch that DLL under a debugger rather than attaching to a process; the [Platform README](https://github.com/Hexalith/Hexalith.Platform/blob/main/README.md#launch-mcpcli-under-a-debugger) has the recipe. Offline discovery verbs such as `modules` need no gateway URL and return `catalog_empty` until modules are enrolled.

This repository's own `references/*`, including `references/Hexalith.Platform`, serve only this repository's own builds and tests. A run from this repository's root is not Platform evidence. Inside a Platform checkout, leave them uninitialized: the tool refuses any initialized nested submodule (`HXW003`).

## CLI and MCP

Run the executable from source with `dotnet run --project src/Hexalith.McpCli --`, or use `hexalith` after installing the tool package. A gateway URL is required for execution, but discovery works offline.

```sh
hexalith modules
hexalith operations your-module --kind read
hexalith describe your-module.your-operation --lint
hexalith config profile add dev --url https://gateway.example
hexalith config set dev tenant acme
hexalith config set dev allowedExtensions task-id,trace-id
hexalith config use dev
hexalith config current
hexalith send your-module.your-command --payload @command.json --idempotency-key 01ARZ3NDEKTSV4RRFFQ69G5FAV
hexalith send your-module.your-command --payload @command.json --extension task-id=abc --extension trace-id=xyz
hexalith query your-module.your-query --payload @query.json --page-size 25
hexalith mcp --transport stdio
```

`--url`, `--token`, `--tenant`, `--actor`, `--allow-tenant-override`, `--profile`, `--format json|table`, `--output`, `--read-only`, and `--strict` are global options. Command and query payloads can be inline JSON, `@file`, or `-` for stdin. `--read-only` removes command submission from the MCP tool list and makes CLI `send` fail. The local profile file is `~/.eventstore/mcpcli.json`; token values are masked in `config` output. `config profile`, `config use`, and `config set` ignore `--profile` and `EVENTSTORE_PROFILE` and render their output using `--format`, then `EVENTSTORE_FORMAT`, then `json`, never the active profile's format.

Commands use `hexalith send MODULE.OPERATION --payload '{"ItemId":"..."}'`, `--payload @command.json`, or `cat command.json | hexalith send MODULE.OPERATION --payload -`. The payload follows the declared schema and supplies the aggregate identifier; an optional `--aggregate-id` must equal it. A successful send exits 0, makes one Gateway request, and returns `operation`, the Gateway `messageId` when provided (otherwise the submitted message ID), the submitted `correlationId`, resolved `tenant` and `aggregateId`, and `status: "accepted"`. Each call generates a new ULID message ID and uses it as correlation unless `--correlation-id` supplies one. `--correlation-id` and `--idempotency-key` must be canonical uppercase ULIDs; any other value, including lowercase ULID text, fails with `validation_failed` instead of being replaced. The tool never generates an idempotency key. When a command declares a non-nullable or serializer-required idempotency member, the caller must supply `--idempotency-key`, including when a required member is nullable. `describe` reports this requirement as `envelope.idempotencyKeyRequired: true`. A supplied key replaces any raw mapped payload value; without it, a raw non-null key is rejected and a raw null key is removed. The result includes `idempotencyKey` only when supplied and `result` only when returned by the Gateway. It never includes a `duplicate` field. Validation failures exit 2 and submit nothing. Gateway failures exit 2 with a `gateway_error` document. A timeout or other uncertain Gateway outcome may have reached the Gateway; `gateway_error` reasons `gateway-timeout` and `gateway-unreachable` are uncertain even when the detail says the Gateway could not be reached. Do not assume that submitting the command again is safe.

Queries use `hexalith query MODULE.OPERATION --payload '{"Key":"item-42"}'`, `--payload @query.json`, or `cat query.json | hexalith query MODULE.OPERATION --payload -`. The payload follows the operation's described schema and preserves its property casing. Aggregate selection uses `--aggregate-id`, then the declared payload accessor, then a query's declared constant. An explicit value must agree with a payload accessor, may override a constant, and is required when neither source exists. Validation completes before exactly one Gateway submission using the catalog's routing values.

Enable a read-only session with `--read-only` or `EVENTSTORE_READ_ONLY=true`. After settings resolution and catalog access succeed, a `send` naming a declared write returns `read_only` with exit code 2 and zero Gateway requests, even without a Gateway URL. Refusal happens before reading payload files or stdin, parsing JSON, processing `--extension key=value` entries, or validating `--aggregate-id`, `--correlation-id`, and `--idempotency-key`. A missing or blank `send` operation returns `invalid_arguments` for `operation` before catalog lookup in either mode. For read-only `send`, an unknown operation returns `unknown_operation` and naming a read operation returns `validation_failed`; these errors take precedence over missing or unreadable payloads and malformed extensions. Without read-only mode, `send` returns `invalid_arguments` for missing payloads or unreadable payload files, an `--extension` value with no `=`, an empty key before `=`, or repeated identical extension keys before those operation errors. Queries and discovery remain available; writes remain listed and describe reports `submittable: false, reason: read_only`. An explicit `--read-only false` overrides the environment setting. Run `hexalith config current --format json` with the same read-only flag and environment to check `readOnly` and its origin in `sources.readOnly` (`flag`, `EVENTSTORE_READ_ONLY`, or `default`).

`--read-only` enables the mode without a value, or accepts an explicit `true` or `false` value (case-insensitive). The flag does not accept `1` or `0` as boolean values; use `true` or `false`. For example, `operations --read-only 0` enables read-only mode and takes `0` as the module name. `EVENTSTORE_READ_ONLY` accepts exactly `true`, `false`, `1`, or `0`, with case-sensitive matching. Settings resolution for discovery, execution, `config` (including profile management), and MCP stdio startup rejects any other value, including `True`, with `configuration_invalid` and exit code 2 unless an explicit `--read-only` flag overrides it. Command-line parse failures, help, `--version`, MCP `--transport`, `--format`, or `--output` errors, and `config profile add` refusal of `--tenant`, `--actor`, or `--allow-tenant-override` can return before this check. An earlier configuration error, such as an invalid Gateway URL or a missing selected profile, can also take precedence.

The global CLI `--tenant` sets the session tenant; it is never a per-call override. A module's fixed tenant wins over that session value. A query requires a resolved tenant. MCP per-call tenants may replace a session tenant only when tenant override is enabled; matching values need no override, and a per-call value cannot conflict with a fixed tenant. When no session tenant is configured, an MCP per-call tenant is used as supplied, without the override gate. Commands take a declared payload tenant from the resolved tenant and a declared actor from the session only. A command that declares an actor requires a session actor from `--actor`, `EVENTSTORE_ACTOR`, or the selected profile's `actor`; without one it fails with `validation_failed` at `/actor`, even if the payload supplies an actor. If the caller includes either mapped member, it must be a JSON string exactly matching the trusted value. The executor fills omitted or matching members before submission and validates the rebuilt payload. A mapped correlation member is always replaced with the supplied `--correlation-id` or the generated message ID.

Commands and queries follow the module's declared ULID or String kind for aggregate identifiers. In ULID-kind modules, aggregate identifiers and marked payload identifiers must use canonical uppercase ULID text. Payload properties of CLR type `Ulid` must also use canonical uppercase text in any module, as must `Ulid` elements in nested collections and dictionaries. In String-kind modules, marked string-typed payload properties have no added ULID pattern or nonempty requirement; other schema rules may still constrain them. Aggregate identifiers also require 1–256 ASCII letters, digits, dots, underscores, or hyphens, starting and ending with a letter or digit. Tenant values require 1–64 lowercase ASCII letters, digits, or hyphens with the same start/end rule. A declared payload tenant member is filled from the resolved tenant; a conflicting or non-string caller value fails validation.

Queries accept `--entity-id` for an optional entity within the aggregate. Entity identifiers require 1–256 ASCII letters, digits, dots, underscores, or hyphens, starting and ending with a letter or digit. They follow this Gateway syntax even for ULID-kind modules.

Only the selected Profile supplies the extension allowlist, which is empty by default; unlisted keys are refused. Set a Profile's extension allowlist with `config set PROFILE allowedExtensions task-id,trace-id`, using comma-separated keys without spaces; `config set PROFILE allowedExtensions ''` clears the list. Supply values with repeatable `send --extension key=value` options or the MCP `send_command` tool's `extensions` object. Both heads use the same validation. Allowlist matching ignores case, but a call cannot contain two keys that differ only by case. Keys may contain ASCII letters, digits, dots, underscores, hyphens, and colons; each colon-separated segment must start and end with a letter or digit. Keys and values must pass the Gateway's injection checks, and values cannot contain `<`, `>`, `&`, `'`, or `"`. The reserved `actor:globalAdmin` key and every key beginning with `identity:` are rejected regardless of case, both in Profile allowlists and command calls. A colon-delimited key also requires exactly one Gateway trusted-extension policy to claim and accept it for that authenticated caller and command. At most 32 entries are allowed, with keys up to 100 UTF-16 code units, values up to 1,000 UTF-16 code units, and 4,096 UTF-8 bytes combined. Both heads send approved keys and values unchanged; queries do not carry extensions.

Extension checks reject case-insensitive script or HTML patterns (`javascript` followed by optional whitespace and `:`, `on` followed by word characters, optional whitespace and `=`, or `<` followed by optional whitespace and `script`, `iframe`, `object`, or `embed`), SQL patterns (an apostrophe and semicolon followed by optional whitespace and `DROP`, `ALTER`, `DELETE`, `INSERT`, `UPDATE`, or `EXEC`; `UNION` followed by whitespace and `SELECT`; or `--` followed only by whitespace to the end), LDAP fragments `)(`, `*)(`, `|(`, or `&(`, and path traversal fragments `../` or `..\`. These checks match anywhere in a key or value, so values such as `session_id=abc` and `partition_key=7` are refused by the `on…=` rule. Values also reject control characters below U+0020 except tab, LF, and CR.

`--page-size` accepts 1–200, `--offset` accepts 0–2,147,483,647, and `--cursor` accepts at most 4,096 UTF-16 code units. A nonblank cursor cannot be combined with an offset, including offset 0; empty or whitespace cursors are preserved. To request the next page when the projection uses cursor paging, pass the returned `paging.nextCursor` as `--cursor` without `--offset`. These options populate the query envelope's `Paging` with only the values supplied. Omitting all three omits envelope paging. Payload members named `PageSize`, `Offset`, or `Cursor` remain ordinary payload data, retain their lint warnings, and never supply or override envelope paging.

Query success exits 0 and always returns `operation`, `tenant`, and `document`, including `"document": null` when the Gateway returns no payload. `paging` appears only when returned by the Gateway; it includes `pageSize` and independently returned `offset`, `nextCursor`, `totalCount`, or `hasMore`. Unavailable metadata is omitted; returned zero counts/offsets and `hasMore: false` are preserved. Request paging never supplies result metadata. Queries carry no correlation identifier or extensions. Validation failures exit 2 without submitting to the Gateway.

`modules`, `operations <module>`, and `describe <operation>` browse the local Contracts catalog without making Gateway requests, even when a URL is configured. Modules and operations are listed in ordinal name order. `operations` includes both reads and writes by default; `--kind read` or `--kind write` filters the list. Read-only mode keeps writes visible. `describe` includes the payload schema, an example when declared, envelope requirements and arguments, and `lintFindings`. Without a URL it reports `submittable: false` and `reason: configuration_invalid`; a write in read-only mode reports `reason: read_only` first. `submittable` reflects only read-only mode and whether a URL is configured; it does not check the token, tenant, actor, or Gateway reachability. Module property casing is preserved in schemas and examples.

With `--format table`, modules use tab-separated `NAME`, `OPERATIONS`, `DESCRIPTION` columns, operations use `NAME`, `KIND`, `DESCRIPTION`, and configuration displays use `FIELD`, `VALUE`. Raw `NAME`, `KIND`, and `DESCRIPTION` cells escape backslash as `\\`, tab as `\t`, carriage return as `\r`, and newline as `\n`; configuration `VALUE` cells retain their serialized JSON escapes. `describe` stays JSON. It exits 0 even with lint findings unless `--lint` is supplied; with that flag, findings produce exit 1 without changing the document. Errors exit 2.

### Output and exit codes

Results use the canonical JSON serializer on stdout, or in `--output` when a result file is selected. Tables apply only to module, operation, and configuration displays. Successful `describe`, `send`, and `query` results remain JSON and emit one format note on stderr when table format was requested.

- Exit 0 means a result. Help, version, and normal MCP shutdown also exit 0.
- Exit 1 is reserved for `describe --lint` with findings.
- Exit 2 means no result. Non-MCP failures are one JSON object on stdout containing only `error`; `--format table` and `--output` do not redirect or change it. MCP failures before request serving use stderr and leave stdout empty.

If an action does not stop after Ctrl+C or SIGTERM, System.CommandLine's termination timeout can instead return 130 or 143. Failures before result writing leave an existing result file unchanged; runtime write failures and interruptions have the restoration risks described below. An interrupted `send` can also exit 2 with `internal_error` after the Gateway accepted it; do not retry without a trusted idempotency mechanism.

`error.code` is one of `validation_failed`, `gateway_error`, `unknown_operation`, `unknown_module`, `invalid_arguments`, `read_only`, `catalog_empty`, `catalog_invalid`, `unsupported_transport`, `configuration_invalid`, or `internal_error`. Validation errors identify the requested operation and all detected violations with JSON Pointer paths. Unknown names include up to three canonical suggestions. Unexpected failures return a fixed `internal_error` message without exception text or secrets. `mcp --transport http` is refused with `unsupported_transport` because HTTP is planned for the next release.

### Parsing and help

- Parse failures return `invalid_arguments` and exit 2, without printing usage or echoing supplied values. Unknown-option and invalid-argument messages point to `--help` for usage. The `argument` member names a recognized option (for example, `pageSize` or `readOnly`), or uses `arguments` for command syntax. MCP parse failures use stderr; other parse failures use stdout.
- Help must appear alone after its command path, such as `hexalith send --help`. `--version` must be the only argument.
- Leading directive-shaped tokens such as `[suggest]` are refused.
- Put `--` before a positional value beginning with `-` or matching a slash help alias or its attached-value form. Examples: `hexalith config set dev actor -- -bob`, `hexalith config set dev actor -- /h`, and `hexalith config set dev actor -- /h:x` (also for `/?`).
- Every token after `--` is positional, so put options before it.
- For an option value beginning with `-` or resembling a help alias, attaching it with `=` or `:` is unambiguous. Examples: `--token=--abc` and `--token=-h`.

### Execution, configuration, and MCP

`gateway_error.status` is copied from the EventStore client exception, including when the client reports a malformed or semantically failed `2xx` response. A Gateway Problem Details `status` may differ from the HTTP response status. `detail` falls back from the client exception's Detail to Title, then a generic message. `reason`, `retryable`, `clientAction`, `retryAfter`, and `correlationId` appear only when the exception provides them, and a `correlationId` that is not a canonical uppercase ULID is omitted; no message or retry identifier is invented. A Gateway error after a command submission is not proof that the command was rejected, so do not retry an uncertain outcome without a trusted idempotency mechanism.

On Unix, new regular `--output` files use mode 0600; on Windows they inherit the directory ACL. Before a Gateway request or profile mutation, the CLI checks predictable destination and staging failures without changing the result target. These preflight failures use `internal_error` with the stable message `The result destination cannot be written; no request was sent.` New regular files stage beside the destination; existing regular files and backups stage in the system temporary directory. Existing regular files retain their permissions, ACL, and symbolic-link target; a dangling output link creates its target. Read-only and write-only existing files are refused before mutation because their previous bytes cannot be safely replaced or backed up. Character devices, pipes, and FIFOs receive output directly. Runtime failures can still occur after preflight, including disk exhaustion, a disappearing path, or a device error. Writing to a named FIFO without a reader waits for one to connect. A caught write failure to a regular file restores its previous bytes; process interruption or another failure during restoration can leave a partial file. A `send` may already have been accepted if a later runtime write to `--output` fails and the CLI exits 2; do not retry that command solely because the result file was not written. Likewise, a `config profile add`, `config profile remove`, `config use`, or `config set` change may already be saved when that write fails; check `config current` or `config profile list` before retrying.

Catalog diagnostics go to stderr while ordinary discovery retains valid entries. `--strict` rejects any catalog diagnostic, including warnings, with `catalog_invalid` at exit 2 before checking for an empty catalog. Lint findings alone do not invalidate a strict catalog. A catalog with no valid operations returns `catalog_empty` at exit 2 when strict diagnostics have not already rejected it. `config` and `--version` bypass catalog construction.

`config profile add` stores only `--url`, `--token`, and `--format`, never environment values; it replaces the whole record when the profile already exists and refuses an explicit `--tenant`, `--actor`, or `--allow-tenant-override` without writing anything. After adding the profile, `config set` changes one of `tenant`, `actor`, `allowTenantOverride`, or `allowedExtensions` while keeping every other field.

Start the server with `hexalith mcp --transport stdio`. It starts without a prompt, resolves settings and checks the local Catalog before serving, and supports both the 2025-06-18 initialization flow and the 2026-07-28 discovery flow. Discovery works without a Gateway URL. Stdout carries only JSON-RPC; logs and diagnostics use stderr. A valid inherited `table` format does not change protocol output, and explicit `--format json` is accepted. Explicit `--format table` and any `--output` are rejected before Catalog or transport startup; format takes precedence when both are supplied, and the output path is not opened.

Before serving, invalid settings, an empty Catalog, or strict Catalog diagnostics produce one structured `{"error": ...}` document on stderr, exit 2, and leave stdout empty. Once serving, tool failures are MCP results, without a second stderr error document. A normal client shutdown exits 0. An unexpected host failure exits 2 with the fixed stderr diagnostic `MCP server stopped unexpectedly.`

The stdio MCP server advertises five generic tools in a normal session, in this order: `list_modules`, `list_operations`, `describe_operation`, `send_command`, and `run_query`. A read-only session advertises four, omitting only `send_command`. Start with `list_modules` for names and operation counts, pass a module name to `list_operations` (optionally with `kind: "read"` or `"write"`), then pass an operation name to `describe_operation` for its payload schema, optional example, envelope arguments, lint findings, and `submittable` state. When the description says `submittable: true`, use `run_query` for a read or `send_command` for a write. `submittable` reflects only read-only mode and whether a URL is configured; it does not check the token, tenant, actor, or Gateway reachability. These discovery calls work without a Gateway URL; descriptions then report `submittable: false` with `reason: configuration_invalid`. In a read-only MCP session, writes remain visible in discovery and describe reports `reason: read_only` for them, which takes precedence over `configuration_invalid`. Its protocol output uses stdout and diagnostics use stderr. The HTTP MCP transport is reserved for a later release.

MCP execution requires `operation` and `payload` as strings: `payload` contains JSON text with the module's property casing, for example `{"operation":"sample.get-item","payload":"{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}"}` for an enrolled sample contract. File and stdin shorthand (`@file`, `-`) belongs to the CLI; MCP passes JSON text directly. Both execution tools accept optional string `tenant` and `aggregateId`. `send_command` also accepts string `correlationId` and `idempotencyKey`, plus an `extensions` object mapping keys to string values. `run_query` accepts string `entityId` and `cursor`, plus integer `pageSize` and `offset`. The tenant, identifier, extension, and paging rules above apply unchanged.

MCP success returns the same complete document as CLI/Core in `structuredContent`, with `isError: false` and matching JSON in the first text content item. Command results omit `idempotencyKey` unless supplied and `result` unless returned; query results always contain `document`, preserving objects, scalars, arrays, and JSON null, and include `paging` only when the Gateway returns it. Core refusals and Gateway failures return `isError: true` with the same `{"error": ...}` document in structured and text content. Unexpected tool exceptions return a sanitized `internal_error`. Missing required arguments and values that do not match the input schema return JSON-RPC invalid-parameters errors before execution. `run_query` `pageSize` and `offset` values that are not representable as an Int32 integer (for example `2147483648`, `25.0`, or `1e20`) also return invalid-parameters, with the message "<field> must be representable as an Int32 integer." Each advertised output schema has an object root and closed success/error document branches; embedded payload schemas and returned JSON values retain their own allowed structure. Both the legacy `2025-06-18` initialization flow and the `2026-07-28` discovery flow are verified through SDK stdio clients.

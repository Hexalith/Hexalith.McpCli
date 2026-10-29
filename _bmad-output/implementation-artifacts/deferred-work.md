# Deferred Work

## Deferred from: code review of spec-1-1-declare-a-module-and-its-operations.md (2026-09-23)

- **The `KebabCase` helper cannot be shared with the `netstandard2.0` analyzer.** `src/Hexalith.McpCli.Abstractions/KebabCase.cs:17` uses `ArgumentException.ThrowIfNullOrWhiteSpace` and range slicing (`[..^n]`). The architecture requires one helper shared by the Catalog and the analyzer. The analyzer is `netstandard2.0`, and the Abstractions package is `net10.0` only. Story 1.7 must choose between linked source and multi-targeting, and add a `netstandard2.0` compile check so the naming rule cannot fork.
- **Bootstrap releases remain possible after paired releases start.** `scripts/release-request.py:12` (`validate_request`) and `scripts/verify-release-source.py:39` accept `bootstrap` without checking whether `Hexalith.McpCli` has already been published. That cannot happen yet because `paired` always fails. The paired-release story must make bootstrap fail once the tool package exists, or it could split the AD-17 single version line.
- **StyleCop header rule vs practice.** The Code style row in the architecture spine requires a StyleCop header. No new `.cs` file has one, and sibling Tenants does not use them either. Either amend the spine or adopt headers (with `StyleCop.Analyzers`) across the repo.
- **No rule for non-canonical names.** `HexalithModuleAttribute.Name` and the `Name` override on `HexalithCommand` and `HexalithQuery` are taken as written. A value such as `Inventory`, `tls_config` or `a.b` would break the `<module>.<operation>` split or produce non-canonical Operation Names. The PRD and architecture define no diagnostic category for this. Stories 1.4 and 1.5 should add one, possibly with an `IsCanonical` helper next to `KebabCase`.
- **No diagnostic for a type with both operation attributes.** A type can carry both `[HexalithCommand]` and `[HexalithQuery]`, which makes its kind (write or read) ambiguous and would defeat the read-only filter. No Catalog diagnostic category covers this case. Stories 1.4 and 1.5 should add one.

## Deferred from: code review of spec-1-3-derive-the-operation-s-json-schema.md (2026-09-25)

- **The CLAUDE.md dependency allowlist omits `JsonSchema.Net`.** `src/Hexalith.McpCli.Core/Hexalith.McpCli.Core.csproj` references `JsonSchema.Net`, which is outside the transitive closure of `Hexalith.EventStore.Contracts`. The story spec and the architecture spine approve it as a pinned Stack package, so update the shared `AGENTS.md` baseline (and its synced copies) to name it.
  status: done 2026-10-10
  resolution: The bmad-project-context refresh made the `AGENTS.md` policy line (and its synced copies) name `tools/dependency-policy.json`, which lists `JsonSchema.Net`, as the allowlist.
- **`PayloadValidator` may fail open.** `src/Hexalith.McpCli.Core/Schema/PayloadValidator.cs:171` builds violations only from nodes that carry `Errors`, and `IsValid` is `Violations.Count == 0`. If JsonSchema.Net 9.4 ever returns an invalid `List` result without an error message, an invalid payload would pass. Unverified; settle by confirming the output guarantee or adding a fallback `/` violation when `results.IsValid` is false and none were collected.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-derive-the-operation-s-json-schema.md`
  summary: `/pushall` step 3 commits submodule changes on a detached HEAD with `git add -A`, so step 4's checkout orphans the commit and untracked files can be staged.
  evidence: `.claude/skills/pushall/SKILL.md` (and its three copies) runs `add -A && commit` in step 3 before `checkout <default-branch>` in step 4; root-declared submodules are normally checked out detached.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-derive-the-operation-s-json-schema.md`
  summary: `/pushall` uses fixed commit messages without commitlint validation, and `allowed-tools: Bash(git *)` blocks both commitlint and the validation step 7 requires.
  evidence: CLAUDE.md requires validating every assistant-used commit message with the pinned commitlint CLI; `build: merge <ref> into <default-branch> via /pushall` is never validated and may exceed header length for long ref names.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-derive-the-operation-s-json-schema.md`
  summary: Story 1.5 must report free-form Payload members (`object`, `JsonElement`, `JsonNode`, and collections of them) as a "free-form member" declaration diagnostic rather than the generic "opaque" wording; the resolved review decision keeps rejecting them so every Payload has a closed Schema.
  evidence: `SchemaDeriver.Transform` throws `NotSupportedException` ("Opaque serialized member Data…" / "Opaque element type System.Object…") for these types at src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:182 and :308.

## Deferred from: code review of spec-1-4-discover-valid-operations-in-one-catalog.md (2026-09-26)

- **Diagnostic categories are chosen by matching exception message text.** `CatalogBuilder.Classify` (`src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:234`) substring-matches `SchemaDeriver` and `RoutingResolver` messages, so the interface-routing read failure is reported as `invalid_schema`. `IsDeclarationFailure` catches broad BCL exceptions, which can hide internal McpCli bugs as operation exclusions. Several emitted categories (`invalid_module_declaration`, `conflicting_operation_kinds`, `invalid_operation_declaration`, `invalid_operation_name`, `invalid_schema`) are outside the spine taxonomy. Story 1.5 should throw and catch a coded declaration-failure exception and align the categories with the spine.
- **Catalog diagnostic messages drop the failure detail.** `CatalogBuilder.cs:229` and similar sites emit generic messages and discard `exception.Message`, so authors cannot see which member or value failed. Story 1.5's "actionable message" AC should carry the detail.
- **Routing resolution discards which source won.** `RoutingResolver.Resolve` (`src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs:21`) overwrites attribute values with interface values, so `redundant_value` and `conflicting_value` (a Story 1.5 AC and the spine's "Routing per field" convention) cannot be emitted. `CompetingRouteCommand` and `InterfaceItemQuery` already conflict silently.

## Deferred from: review of story 1.7 while concurrent CLI, settings, and executor work was present (2026-09-27)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Bare boolean CLI switches can be ignored, including the read-only safety flag.
  evidence: `GlobalOptionsBinding.ExplicitFlag` requires a value token, while a bare System.CommandLine boolean option has none; this belongs to concurrent CLI work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: The settings resolver rejects documented boolean environment values `1` and `0`.
  evidence: PRD addendum §E accepts both, but `SettingsResolver.SelectBoolean` calls only `bool.TryParse`; this belongs to concurrent settings work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Table format can replace required JSON for describe, send, and query.
  evidence: `CliOutput.WriteAsync` formats every successful document as a table, while PRD FR-12 requires JSON for those verbs; this belongs to concurrent CLI work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Invalid profile paths can be silently treated as absent profiles.
  evidence: `ProfileStore.Read` returns defaults when `File.Exists` is false, which includes a directory or dangling symlink; this belongs to concurrent settings work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: A profile with more than 32 valid allowed extension keys is rejected.
  evidence: `SettingsResolver` passes the allowlist to `ExtensionValidator.Validate`, whose 32-entry limit is for one submitted command; this belongs to concurrent settings work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Executor cancellation is reported as an internal error.
  evidence: `OperationExecutor.ExecuteAsync` catches `OperationCanceledException` in its blanket catch; this belongs to concurrent executor work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Malformed Gateway response identifiers can enter a successful command result.
  evidence: `OperationExecutor` copies response IDs without the ULID validation required by PRD addendum §G. Story 2.9 review loop 3 deferred successful-response hardening under its frozen decision.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Malformed Gateway paging metadata can enter a successful query result.
  evidence: `OperationExecutor` copies paging values without checking a nonempty cursor or numeric constraints. Story 2.9 review loop 3 deferred successful-response hardening under its frozen decision.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Concurrent CLI and settings paths lack focused behavior tests.
  evidence: No current test covers settings precedence, bare boolean switches, boolean environment values, or the format behavior described in PRD FR-12.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: A null or blank executor operation can become an internal error instead of input validation.
  evidence: Executor lookup calls `CatalogService.Describe`, which throws for a blank operation and is caught as `internal_error`; this belongs to concurrent executor work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: An explicit Query aggregate ID can override the Operation's declared constant.
  evidence: `call.AggregateId ?? accessorId ?? operation.AggregateIdConstant` prefers the caller value without checking conflict; this belongs to concurrent executor work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: A whitespace query cursor can be sent with an offset.
  evidence: `ValidateQueryArguments` checks cursor length and a nonblank cursor with offset, but does not reject a supplied blank cursor; this belongs to executor work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Config output reveals the full value of tokens four characters or shorter.
  evidence: `ProfileStore.MaskToken` preserves the first four characters regardless of token length; this belongs to profile work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: The conformance runner accepts unexpected fields in captured Gateway requests.
  evidence: `run_loopback.py:_expect_fields` checks only expected dictionary keys, leaving extra envelope or routing fields unchecked; this belongs to conformance work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Conformance vectors can pass when both Heads omit a required public result field.
  evidence: The runner compares CLI and MCP documents and executes vector-specific assertions without an unconditional check of the command and query result shape; this belongs to conformance work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: The unsupported HTTP transport error omits the promised release timing.
  evidence: `CliRunner.RunMcpAsync` says only that stdio is available, while the PRD requires a message naming the next release; this belongs to CLI work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Bearer authentication is not checked at the Gateway request boundary.
  evidence: The CLI command parity test uses a null token and has no Authorization header assertion; removing `StaticBearerTokenHandler` would leave it passing. This belongs to hosting and CLI work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Returned paging cursors are not verified in CLI and MCP query documents.
  evidence: Query parity uses a Gateway response without paging, while the Core test inspects only the in-memory result; this belongs to query work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: MCP operation-kind filtering is not verified through the handler.
  evidence: Core filtering is tested, but MCP parity calls `list_operations` without `kind`; this belongs to MCP work.
  status: resolved in Story 3.1 (2026-10-11); `McpProtocolTests.DiscoversAndCallsWithTheCoreDocumentAsync` lists `sample` operations through the SDK with no `kind`, `read`, and `write`, and pins the `invalid_arguments` document for `kind: "Read"`.

## Deferred from: resumed review of story 1.8 (2026-09-27)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance offset validation lacks the runtime Int32 maximum.
  evidence: Medium; both baseline 9b3b099bf117eac880b9b6e12422990a168519eb and the reviewed schema accept offset 2147483648, while RunQueryArguments.Offset is int?. Align this existing range gap before downstream runner compatibility acceptance.
  status: resolved in Story 1.8 (2026-09-27); the schema enforces 2147483647, with boundary and every-call-position regression coverage.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Integral floating-point paging accepted by JSON Schema is rendered as an invalid CLI integer.
  evidence: Medium; both validator versions accept pageSize 1.0; run_loopback.py _call_args uses str(value), yielding --page-size 1.0. Story 4.11 should normalize accepted integral numeric values or settle an explicit representation rule.
  status: resolved in Story 1.8 (2026-09-27); all contract integer fields require integer JSON tokens through the shared validator's strict type checker.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance paging comparisons equate booleans with integers.
  evidence: Medium; both validator versions accept expectedGateway.body.paging.pageSize true for envelope.pageSize 1 because validate.py _check_step uses Python dictionary equality. Distinguish JSON boolean and number types before downstream request-consistency acceptance.
  status: resolved in Story 1.8 (2026-09-27); expected paging must match supplied keys, types, and values at every call position.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance cursor limits count Unicode code points while Core counts UTF-16 units.
  evidence: Medium; both validator versions accept 3000 emoji, while OperationExecutor.ValidateQueryArguments rejects their 6000 UTF-16 units. Align the pre-existing schema/runtime limit before downstream compatibility acceptance.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance extension inputs omit fixed runtime restrictions.
  evidence: Medium; both validator versions accept 33 matching extensions. ExtensionValidator also checks key grammar, 100-character keys, 1000-character values, forbidden content and 4096 total UTF-8 bytes; these restrictions are absent from the existing contract tooling independently of the deployment allowlist.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Expected Gateway fields can contradict absent optional envelope inputs.
  evidence: Medium; both validator versions accept invented expected extensions with no supplied extensions and expected paging with no supplied paging. Core maps these fields directly from the missing inputs; extend the existing presence-only consistency checks before downstream acceptance.
  status: resolved in Story 1.8 (2026-09-27); absent extensions and paging must remain absent in request expectations, including empty and null expectations.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance expected requests can contain known fields belonging to the other operation kind.
  evidence: Medium; both validator versions accept idempotencyKey in a query expectedGateway.body although query request construction has no such field. Preserve open Module data while checking incompatible known request fields before downstream compatibility acceptance.
  status: resolved in Story 1.8 (2026-09-27); known Command-only and Query-only request fields are rejected on the opposite kind while arbitrary Module data remains open.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance routing inputs omit unconditional Gateway identifier syntax and length restrictions.
  evidence: Medium; both validator versions accept entityId / in the envelope and expected request, while RoutingResolver.IsAggregateId rejects it. Apply common routing constraints independently of Module payload identifier kinds before downstream compatibility acceptance.

## Deferred from: Story 1.8 follow-up review (2026-09-27)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance envelope ULIDs require uppercase while the pinned runtime parser also accepts lowercase.
  evidence: Medium; both baseline 9b3b099bf117eac880b9b6e12422990a168519eb and current schema reject 01j9mzhxt3rkm0vwxrxgsjdatk; the review's ByteAether.Ulid 1.4.1 probe accepts it. Resolve the existing v1 representation rule during downstream compatibility work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Python parsing can silently underflow Module-owned numeric tokens before conformance execution.
  evidence: Medium; baseline and current validator accept raw 1e-400 as 0.0. The unchanged runner also uses json.loads and json.dumps, losing the original value; settle supported numeric representation or precision preservation in runner work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Offline vector validation accepts Payload nesting deeper than the execution parser supports.
  evidence: Medium; baseline and current validator accept 65 nested arrays, while OperationExecutor uses JsonDocument.Parse with the default depth limit. The review reproduced the runtime rejection; add Payload depth compatibility to Story 4.11 acceptance.
- source_spec: `_bmad-output/implementation-artifacts/spec-remediate-epic-1-conformance-gaps.md`
  summary: Conformance Number comparison may lose distinctions beyond binary floating-point precision.
  evidence: Unverified medium; Python rounds some finite decimal/exponent tokens before comparison and execution, but the approved intent does not define arbitrary-precision Number semantics. An explicit representation and precision decision would settle whether lossless parsing is required.
- source_spec: `_bmad-output/implementation-artifacts/spec-remediate-epic-1-conformance-gaps.md`
  summary: Conformance extension inputs do not mirror all fixed runtime extension restrictions.
  evidence: Medium; the unchanged vector schema accepts keys and sizes that ExtensionValidator rejects, including path-like keys, count, per-value, injection, and total UTF-8 limits. This behavior predates the remediation and needs a separate compatibility change.
- source_spec: `_bmad-output/implementation-artifacts/spec-remediate-epic-1-conformance-gaps.md`
  summary: Migration planning artifacts disagree on inventory dispositions, v1 scope, retirement claims, and the no-new-proprietary-surface rule.
  evidence: Medium; the concurrent planning-history advance left AD-21 and Story 4.5 on include/exclude-only semantics, conflicts over EventStore Admin timing and temporary exceptions, and stale PRD wording and metrics. Reconcile the architecture, PRD, epics, and authoritative agent baseline together.

## Deferred from: code review of spec-2-1-inspect-effective-session-settings.md (2026-09-28)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: Profile-management verbs can read or mutate a second profile snapshot after invocation settings were resolved.
  evidence: This predates Story 2.1: `config profile list|add|remove`, `config use`, and `config set` operate on `ProfileStore` inside the action after `RunAsync` resolved format/output from an earlier snapshot, so a concurrent writer can make the displayed or mutated state inconsistent with those invocation settings; profile-management transaction and snapshot semantics belong to Stories 2.2 and 2.3.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: Profile-management verbs cannot repair the configuration that blocks them.
  evidence: Pre-existing: `config profile add/remove/use/set` run through `CliRunner.RunAsync` settings resolution, so a missing `EVENTSTORE_PROFILE` or a corrupt `mcpcli.json` blocks the very verbs that would repair it; address with Stories 2.2/2.3.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: A nonblank output path can fail only after a Gateway action has completed.
  evidence: Pre-existing: `--output` is not validated before execution, so `send` can reach the Gateway and then fail writing the result file in `CliOutput.WriteAsync`; output-file preflight and retained-handle semantics belong to Story 2.11 output routing, and the frozen Story 2.1 intent excludes execution behavior changes.
  status: resolved in Story 2.11 (2026-10-10); predictable output failures are preflighted before the Gateway call. Runtime write failures remain tracked in this ledger under the Story 2.11 accepted-send entry.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: Cancellation during MCP host startup is mapped through the generic startup-error path.
  evidence: Pre-existing: cancellation while `host.RunAsync` is starting in `RunMcpHostAsync` falls into the generic catch and reports `internal_error` exit 2 instead of a clean exit; clean stdio lifecycle cancellation belongs to Epic 3.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: Offline CLI actions can still depend on unrelated application configuration loaded by the default Host builder.
  evidence: Pre-existing: `HostFactory.CreateHost` uses `Host.CreateApplicationBuilder()`, which loads content-root `appsettings*.json` and every environment variable (including `EVENTSTORE_ADMIN_*`) into an unused `IConfiguration`; consider `Host.CreateEmptyApplicationBuilder` in a separate hosting hardening change.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: Verb-action I/O failures are reported as configuration errors with raw exception text.
  evidence: Pre-existing: `CliRunner.RunAsync`'s outer catch maps any `IOException`/`UnauthorizedAccessException`/`InvalidDataException` thrown by a verb action (for example an output-file write) to `configuration_invalid` with the raw exception message, which can include absolute home paths; the baseline catch wrapped the action too. Address with Story 2.9 stable failure documents.
  status: resolved in Story 2.9 (2026-10-05); host setup failures and action I/O return a fixed `internal_error`, only profile validation raised inside a `config` action stays `configuration_invalid`, and a missing or unreadable `@file` is `invalid_arguments`. `ExecutionFailureCommandTests` and `ConfigCommandTests.MalformedApplicationConfigurationUsesSafeInternalErrorAsync` cover payload files, profile action I/O, failed result writes, and malformed host configuration without leaking paths.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-2-add-and-select-a-private-profile.md`
  summary: Blank or empty names for `config profile remove` and `config set` fail as `invalid_arguments`, while `add` and `use` report them as `configuration_invalid`.
  evidence: `CliRunner` `remove`/`set` still guard with `string.IsNullOrWhiteSpace`, whereas Story 2.2 routes a supplied invalid `add` name to `ProfileStore.ValidateName`; Story 2.2's frozen intent excluded `set`/`remove` semantic changes, so align them in Story 2.3.
  status: resolved in Story 2.3 (2026-09-29); `remove` and `set` report `invalid_arguments` only for absent arguments and send every supplied value to `ProfileStore` validation (`configuration_invalid`).

- source_spec: `_bmad-output/implementation-artifacts/spec-2-2-add-and-select-a-private-profile.md`
  summary: `config profile add` silently ignores `--tenant`, `--actor`, and `--allow-tenant-override` instead of storing or rejecting them.
  evidence: Pre-existing: `add` builds `ConnectionProfile(input.Url, input.Token, input.Format)` per AD-14, so global operator flags succeed without effect; decide in Story 2.3 whether to store them or reject them as `invalid_arguments`.
  status: resolved in Story 2.3 (2026-09-29); an explicit `--tenant`, `--actor`, or `--allow-tenant-override` on `add` fails as `invalid_arguments` naming the first offending flag, points to `config set`, and writes nothing.

## Deferred from: implementation of spec-2-3-update-and-remove-profiles-safely.md (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: No run has executed Story 2.3's Windows evidence. The Core ACL tests (`WindowsProfileFilesHavePrivateAcls`, `WindowsTemporaryFileHasPrivateAclBeforeTokenBytesAreWritten`) skip off Windows, and the CLI process tests `ConcurrentSetProcessesPreserveBothValuesAsync` and `VerbsNeverOpenAdminProfilesAsync` skip on Windows, so AD-14's Windows ACL, cross-process locking and admin-isolation guarantees have no executed Windows evidence.
  evidence: `.github/workflows/ci.yml` runs only on `ubuntu-latest`; on Linux the Core tests show 2 skipped (the ACL tests), confirmed by the second-pass verification-gap review. A `windows-latest` job alone is not enough: the process tests redirect HOME/USERPROFILE, which `Environment.GetFolderPath(SpecialFolder.UserProfile)` ignores on Windows (known-folder API), so the CLI also needs a home override that Windows honors before those tests can run there. The pre-existing read-only `CurrentExecutableReadsProcessEnvironmentAsync` likewise reads the developer's real `~/.eventstore/mcpcli.json` on Windows (the mutating `ExecutableStoresAtPrefixedTokenVerbatimAsync` case is the entry below). Adding the Windows job and the home override is shared CI and hosting infrastructure outside a profile story, and Story 4.16 owns it: its Windows installation check now also runs the Core and CLI test suites with a Windows-honored home override (seventh-pass review decision, 2026-09-29), so the Story 2.3 Linux/Windows ACL criterion gets executed evidence before v1 release. This entry also traces the second-pass review's "no run has executed the Windows ACL tests" deferral.
  status: open; Story 4.16 adds `MCPCLI_HOME` (`src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:26`), removes the home-related process skips (`tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:2027`, `:2071`), and requires actual Windows suite/XML receipts (`.github/workflows/release.yml:276`). Linux execution is recorded in `evidence/story-4-16/implementation-20261029/README.md`; Windows acceptance remains pending.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: System.CommandLine parse errors on config verbs and query numeric options print help to stdout, echo the unmatched token on stderr, and exit 1 instead of a single error document with exit 2.
  evidence: Reproduced on the Release build: `config set dev tenant a b` prints the `set` help on stdout and `Unrecognized command or argument 'b'.` on stderr with exit 1. Pre-existing default ParseErrorAction; it breaks the epic's "stdout holds only the result document, exit 2 when no result" rule and can echo a mistyped positional secret. The same parse failure also bypasses the `config profile add` operator-flag refusal, so these cases never report `invalid_arguments` with exit 2: `add dev --url U --tenant` (no value; help on stdout, exit 1; second-pass acceptance audit), `add dev --url U --allow-tenant-override yes` (`Unrecognized command or argument 'yes'.`, help on stdout, exit 1) and `add dev --url U --tenant=` (`Required argument missing`, exit 1), the last two reproduced on the Release build in the fifth-pass review. Story 2.6's query paging options fail the same way: `--offset 2147483648` and `--page-size abc` on `query string-fixture.list-items --payload '{}'` print usage on stdout and a parse error on stderr with exit 1, before any executor call (Story 2.6 implementation review and code review, 2026-10-02). Test these through `QueryCliHarness` over the fixture catalog: the production CLI enrolls no Contracts, so once parsing is fixed the same command there exits 2 with `catalog_empty` and could pass for a fix. Owned by Story 2.11 (predictable output and exit codes); include every case above in that story's tests.
  status: resolved in Story 2.11 (2026-10-10); `CliOutputContractTests.ParserFailuresUseSafeDocumentsAsync` and `QueryCliHarness` cases verify one safe `invalid_arguments` document at exit 2, with no usage or token echo.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: Pre-existing process-level CLI tests redirect HOME/USERPROFILE, which Windows ignores, so running them on Windows mutates the developer's real `~/.eventstore/mcpcli.json`.
  evidence: `Environment.GetFolderPath(SpecialFolder.UserProfile)` uses the known-folder API on Windows, not USERPROFILE; `ExecutableStoresAtPrefixedTokenVerbatimAsync` (ConfigCommandTests) adds a `dev` profile to the real store there. Story 2.3's new process tests skip on Windows; the pre-existing one predates this story.
  status: implementation corrected in Story 4.16: child processes now use `MCPCLI_HOME` (`tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:186`, `:235`, `:2203`). Actual Windows execution remains pending with the preceding evidence entry.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, third pass (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: A stored `tenant` or `actor` cannot be cleared. `config set dev tenant ""` fails validation, and the only way back is `config profile add`, which replaces the whole record and drops the token, format and allowed extensions.
  evidence: `ProfileStore.Set` assigns the value as given, and `ValidateProfile` rejects a blank tenant or actor. Story 2.3's frozen Never forbids a field-unset verb, and the new `add` operator-flag error sends users to `config set`. By design for v1, but no story owns the clearing path yet.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, fifth pass (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: Profile-management success documents serialize `"activeProfile": null`, although addendum §G and the Epic 2 output rule require absent optional members to be omitted.
  evidence: `McpCliJson.Result` has no `WhenWritingNull`. Story 2.2's matrix specifies `use --clear → null`, and `ConfigCommandTests.ListUseAndClearMaskEveryTokenAsync`, `RemoveClearsOnlyItsOwnSelectionAsync`, and `AddAcceptsOtherGlobalOptionsAsync` assert `JsonValueKind.Null`; the last test also pins the exact result members `name` and `activeProfile`. The planning artifacts need to agree on null or omission before any code changes; Story 2.11 (predictable output) is the natural owner.
  status: preserved by Story 2.11 (2026-10-10); its frozen Never rule keeps Story 2.2's explicit `activeProfile: null` clear result. Planning reconciliation remains open.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, sixth pass (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: `config profile add`, `config set`, and `config profile remove` with an unwritable `--output` path report `internal_error` (exit 2) even though `mcpcli.json` was already changed.
  evidence: `CliRunner` commits through `ProfileStore` before `CliOutput.WriteAsync` writes the success document to `settings.Output`; a missing output directory raises `DirectoryNotFoundException`, which `RunManagementAsync` now maps to `internal_error`; the profile change still precedes the failed output. Pre-existing at baseline `6fe785e`; a retried `remove` then fails as "does not exist". Found in the sixth-pass review of Story 2.3; Story 2.11 (predictable output and exit codes) is the natural owner.
  status: resolved in Story 2.11 (2026-10-10); `CliOutputContractTests` verifies a missing result directory returns the preflight error before `config set` changes the profile.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, ninth pass (2026-09-30)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: Profile names still accept a trailing newline, because their validation regex ends in `$`, which in .NET also matches before a final `\n`.
  evidence: `ProfileStore.ProfileNamePattern` (`^[a-zA-Z0-9_-]{1,64}$`, `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:298`) ends in `$`. The ninth-pass blind-hunter reproduced this on the Release build: `config profile add $'dev\n' --url …` exits 0 and stores a separate `"dev\n"` profile; profile load also accepts it (`:63`, `:241`). This name rule predates Story 2.3 (Story 2.2). Fix the remaining profile-name rule with the absolute `\z` anchor and newline rows in the Core and CLI invalid-input theories. Story 2.8 resolved the allowed-extension-key portion of this finding: `ExtensionValidator.KeyPattern` now uses `\z` (`src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:89`), with rejection coverage in `ExtensionKeyWithFinalNewlineMakesZeroCallsAsync` (`tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:501`) and the `ProfileStoreTests` `task-id\n` row (`tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs:350`).

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: `config set` stores invalid nonblank profile tenants that cause `send`/`query` to fail when they become the resolved tenant.
  evidence: `ProfileStore.ValidateProfile` (`src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:263`) rejects only blank tenant values. `OperationExecutor` (l.118) checks the resolved tenant with `RoutingResolver.IsTenantDomain`: lowercase ASCII, digits and `-`, 1–64 characters. So `config set dev tenant ACME` or `tenant 'acme corp'` exits 0, and execution fails with "The tenant does not match the Gateway tenant pattern" when that profile tenant becomes the resolved tenant. Fixed-tenant modules use their declared tenant instead of the profile tenant, and this grammar check does not apply to actor values. This is pre-existing Story 2.2 validation. Moving the tenant rule into the store also means deciding whether `--tenant` and `EVENTSTORE_TENANT` are checked at resolution time, so it needs an owning settings or execution story.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, eleventh pass (2026-09-30)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: The rules for `config set` values and `config profile remove` are documented nowhere a user looks: neither `--help` nor the README gives them.
  evidence: `config set --help` shows bare `<profile> <field> <value>`: the `profile`, `field` and `value` arguments (`src/Hexalith.McpCli/Cli/CliRunner.cs:393-395`) and the `add`/`remove` `name` arguments (l.305, l.318) have no `Description`, unlike the `module` argument of `operations` (l.97). `README.md` never gives the `allowedExtensions` syntax (comma-separated, not trimmed, `""` stores `[]`) or the accepted `allowTenantOverride` values (`true`, `false`, `1`, `0`). It also never says that `tenant` and `actor` cannot be cleared, or that `remove` clears the active selection only when it names the removed profile. Pre-existing: the argument definitions and README coverage predate baseline `6fe785e`. Found by the eleventh-pass blind-hunter; no owning story yet.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, thirteenth pass (2026-09-30)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: Result and error documents escape `'`, `<`, `>`, `&` and `+` as `\u00XX`, so raw OS messages and values with those characters reach the terminal escaped.
  evidence: `McpCliJson.CreateResult` (`src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs:103-113`) sets no `Encoder`, so the default HTML-safe `JavaScriptEncoder` applies. Reproduced on the Release build: `config profile list --output /missing/dir/f` prints `"Could not find a part of the path \u0027/missing/dir/f\u0027."`. The thirteenth-pass blind-hunter also reproduced it for `config set` while the lock is held. The ninth-pass patch removed these characters from the new `add` refusal message only. Pre-existing: the encoder predates baseline `6fe785e` and is shared with execution and MCP output, which Story 2.3's Never excludes. Suggested owner: Story 2.11 (predictable CLI output). Fix: set `Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping` (or an equivalent) on the result options, and add focused checks for the specific HTML escapes (`\u0027`, `\u003C`, `\u003E`, `\u0026`, `\u002B`) or the expected decoded message content. Valid JSON control-character escapes must remain permitted.
  status: open without an owner; Story 2.11 explicitly declined the encoder change under its frozen "Preserve JSON escaping" rule.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: The README documents no error codes, so a script that branches on `error.code` has no documented contract.
  evidence: `README.md` never mentions `invalid_arguments`, `configuration_invalid`, or the exit codes of any verb. Story 2.3 made a missing positional argument `invalid_arguments` and a supplied but invalid name, field or value `configuration_invalid`, both exit 2; these rules appear only in the spec and tests. Pre-existing: no verb's error codes were documented at baseline `6fe785e`. Story 2.11 owns the exit-code and addendum §G error-document contract. This entry is related to the eleventh-pass documentation entry above.
  status: resolved in Story 2.11 (2026-10-10); `README.md` now lists the public error codes and exits 0, 1 and 2 with their output channels.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md (2026-10-01)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: A token can be stored in a profile only by passing it as `--token` on the command line, so the secret ends up in shell history and, while the process runs, in `/proc/<pid>/cmdline`.
  evidence: `config profile add` builds the record from parsed flags only (`new ConnectionProfile(input.Url, input.Token, input.Format)`, `src/Hexalith.McpCli/Cli/CliRunner.cs:356`). It ignores `EVENTSTORE_TOKEN` (pinned by `AddIgnoresEnvironmentOperatorSettingsAsync`), response files are disabled (`CliRunner.cs:67`), and `@`-prefixed values are stored verbatim, so there is no stdin, file or prompt source. The README says `add` stores `--token` and "never environment values", but does not mention the argv exposure or that the token is kept as plaintext in `mcpcli.json`, protected only by mode 0600 or the ACL. Pre-existing: this is the Story 2.2 / AD-14 `add` input rule at baseline `6fe785e`. A secret-safe input such as `--token -` or a prompt adds public surface and needs an owning settings story. Found by the final-HEAD blind-hunter review of Story 2.3; no owning story yet.

## Deferred from: code review of spec-2-4-browse-the-catalog-from-the-cli.md (2026-10-01)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-browse-the-catalog-from-the-cli.md`
  summary: An empty `--format table` list prints the header followed by a blank row, which a line-oriented script reads as an empty record.
  evidence: `CliOutput.FormatTable` (`src/Hexalith.McpCli/Cli/CliOutput.cs:66-69`) returns `header + Environment.NewLine + string.Join(...)` and `WriteAsync` then writes it with a trailing newline, so `operations marked-empty --format table` (or a `--kind` filter with no matches) prints `NAME\tKIND\tDESCRIPTION`, then an empty line. Pre-existing: the baseline `edc459e` used the same concatenation, and Story 2.4's frozen intent preserves existing rows; `DiscoveryCommandTests.TablesPreserveModuleOperationAndEmptyRowsAsync` now pins `header + NewLine + NewLine`. Suggested owner: Story 2.11 (table rendering AC). Fix: append the separator only when rows exist and update that assertion.
  status: resolved in Story 2.11 (2026-10-10); `DiscoveryCommandTests` verifies an empty table prints only its header and one newline.

## Deferred from: code review of spec-2-5-run-a-valid-query-through-the-gateway.md (2026-10-01)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-5-run-a-valid-query-through-the-gateway.md`
  summary: The Story 2.5 acceptance criteria in epics.md and epic-2-context.md still require the live query proof to run on the existing EventStore AppHost and root-declared checkouts and to record "the local startup path". The delivered proof was a user-authorized reuse of the running topology.
  evidence: `_bmad-output/planning-artifacts/epics.md:665` and the epic-2-context.md "Cross-Story Dependencies" paragraph describe the original plan. The spec's Spec Change Log (2026-10-01) records the user's authorization to reuse the running Tenants AppHost from `/home/administrator/projects/hexalith/tenants` (runtime Tenants `78e0918`, EventStore `19dc1f8`), and `query-spike-2-5.md` records the substitution, with no startup performed. A retrospective (bmad-retrospective) that reads epics.md would check the story against the outdated criterion. Fix: annotate the Story 2.5 AC in epics.md (and regenerate or edit epic-2-context.md) to accept the authorized running-topology proof, or carry the mismatch into the Story 4.8 handoff.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-5-run-a-valid-query-through-the-gateway.md`
  summary: The AGENTS.md/CLAUDE.md policy line allows a per-call MCP tenant "only under the operator gate", which is stricter than the approved tenant rule.
  evidence: `AGENTS.md:84` (byte-identical in `CLAUDE.md` and `.github/copilot-instructions.md`). epics.md (Story 2.5 tenant AC), epic-2-context.md, the Story 2.5 frozen spec and `OperationExecutor.ResolveTenant` (`src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:297`) all honor a per-call tenant when no session tenant exists *or* override is enabled. `QueryExecutionTests` pins the no-session case. An agent that follows the policy line could "fix" the executor against the architecture. Pre-existing wording. Fix: edit `AGENTS.md`, copy it to the other two entry points, and run `scripts/check-agent-instructions-sync.sh`.
  status: done 2026-10-10
  resolution: The bmad-project-context refresh rewrote the tenant policy line in `AGENTS.md` and its synced copies to the approved rule, including the per-call tenant used as supplied when no session tenant exists.

## Deferred from: code review of spec-2-6-validate-and-page-query-calls.md (2026-10-02)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-6-validate-and-page-query-calls.md`
  summary: A String-kind payload accessor failure points at `/aggregateId`, a member the caller never supplied, while a ULID accessor fails at its payload member; reconcile the pointer for derived identifiers in Story 2.9.
  evidence: `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:216-220` checks the Gateway syntax of the resolved aggregate after accessor extraction and reports `/aggregateId`; ULID identifiers fail earlier through the schema pattern at `/ItemId`. `QueryValidationTests.InvalidStringPayloadAccessorMakesZeroCallsAsync` pins `/aggregateId` for an invalid `LookupQuery.Key`. The frozen Story 2.6 matrix allows `/aggregateId`, but the spec's Code Map says "accessor failures use payload pointers". Pre-existing executor behavior.
  status: resolved in Story 2.9 (2026-10-04); invalid accessor values use the mapped payload pointer, pinned at `/Key` and escaped `/key~1~0` by `QueryValidationTests` and `ExecutionFailureTests`; explicit sources still use `/aggregateId`.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-6-validate-and-page-query-calls.md`
  summary: Envelope violation messages name the path, not the failed rule, so a missing tenant reads as a pattern mismatch and both cursor rules share one message; give each rule its own text in Story 2.9.
  evidence: `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:120` reports "The tenant does not match the Gateway tenant pattern." when no tenant resolved (`IsTenantDomain(null)`); `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:314` reports "Cursor must be at most 4096 characters and cannot be combined with offset." for both an over-long cursor and a cursor-plus-offset conflict. `QueryValidationCommandTests.MissingTenantMakesNoRequestsAsync` and the cursor rows pin both texts and must change with them. Pre-existing executor messages.
  status: resolved in Story 2.9 (2026-10-04); missing tenant, invalid tenant syntax, overlong cursor, and cursor/offset conflict have distinct messages with zero-call coverage in `ExecutionFailureTests` and `QueryValidationCommandTests`.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-6-validate-and-page-query-calls.md`
  summary: Lowercase ULID text reaches the Gateway unchanged and addresses a different aggregate than its canonical uppercase form. Story 2.8 owns the fix; intended rule (user decision, 2026-10-02): reject non-canonical (lowercase) ULID text for aggregate arguments and marked identifiers.
  evidence: `SchemaDeriver.UlidPattern` (`src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:18`) and `Ulid.TryParse` in `OperationExecutor.IsUlid` accept lowercase Crockford text, and the executor forwards it as given. EventStore's `AggregateIdentity` lowercases tenant and domain but keeps `AggregateId` case-sensitive (`ActorId` is `{tenant}:{domain}:{aggregateId}`), so a lowercase query reads an empty or missing projection and a lowercase command would start a split stream. Story 2.6 tests pin the current pass-through and must flip with the fix: the ULID row of `QueryValidationTests.ValidIdentifierBoundariesArePreservedAsync` and `QueryPagingCommandTests.EntityAndTenantBoundaryValuesArePreservedAsync`. Deferred because Story 2.8 owns identifier validation, nothing ships before Epic 4, and Story 2.6 stays test-only; the change renegotiates the frozen `Ulid.TryParse` rule.
  status: resolved in Story 2.8 (2026-10-03); Core rejects non-canonical aggregate and marked ULID text, caller correlation IDs, and idempotency keys before Gateway submission. `ValidIdentifierBoundariesArePreservedAsync` and `EntityAndTenantBoundaryValuesArePreservedAsync` now use canonical uppercase IDs and still assert pass-through. Rejection is covered by `InvalidUlidAggregateArgumentsUseEnvelopePathAsync`, `LowercaseAggregateUlidIsRejectedBeforeGatewayAsync`, `LowercaseAggregateUlidMakesZeroCallsAsync`, and `InvalidEnvelopeUlidFailsBeforeGatewayAsync`.

## Deferred from: code review of spec-2-7-submit-a-command-once.md (2026-10-02)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-7-submit-a-command-once.md`
  summary: Decide how to handle a successful Gateway response with an empty or whitespace command message ID.
  evidence: `SubmitCommandResponse.MessageId` is nullable and the EventStore client validates only `CorrelationId` in a successful response. The pre-existing `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:229` expression uses `response.MessageId ?? messageId`, so an empty or whitespace value reaches the accepted document and cannot be used to track the command. Decide whether to fall back to the submitted ID or reject the malformed response before changing the mapping.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-7-submit-a-command-once.md`
  summary: An uncertain command failure (Gateway timeout or unreachable) returns no identifier the caller can use to check the outcome.
  evidence: `EventStoreGatewayClient.CreateTransportException` sets no correlation, `OperationError.FromGateway` copies only `exception.CorrelationId` (`src/Hexalith.McpCli.Core/Execution/OperationError.cs:52`), and the executor's catch (`src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:34`) drops the message and correlation IDs it generated at `:147-148`. The Gateway status endpoint is keyed by message ID (`CommandStatusController.cs:58`), and callers never supply one, so after the README's "may have reached the Gateway" warning nothing can be polled, even with `--correlation-id`. Story 2.9 froze the decision to add no generated tracking fields to errors and documents the retry warning in README; this remains deferred. Under a caller idempotency key the Gateway tracks status by its own execution message ID (`CommandsController.cs:193`), which can differ from the submitted one.

## Deferred from: build review resumption of spec-2-8-protect-command-identity-and-extensions.md (2026-10-03)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: Extension validation still sorts and visits every entry after a submitted map exceeds the 32-entry limit.
  evidence: `ExtensionValidator.Validate` (`src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:22`) adds a count violation but still sorts and visits every entry at `:29`, taking O(n log n) work and building more violations for a request already known to be invalid. This behavior predates Story 2.8; a later cleanup can return after the count failure while preserving the refusal.

## Deferred from: code review of spec-2-8-protect-command-identity-and-extensions.md (2026-10-03, third pass)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: Planning documents and architecture decisions still prescribe acceptance when `Ulid.TryParse` succeeds, but Story 2.8 renegotiated the rule (Spec Change Log 2026-10-03). Core now also requires canonical uppercase text for ULID aggregates, marked identifiers, CLR `Ulid` properties, and caller correlation and idempotency keys.
  evidence: `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md:103` and `:348`, `_bmad-output/planning-artifacts/epics.md:711`, `_bmad-output/implementation-artifacts/epic-2-context.md:32` and `:34`, and `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md:106` (AD-8 aggregate validation) and `:200` (identifier convention) prescribe ULID parsing without the canonical-text requirement enforced by `OperationExecutor.IsCanonicalUlid` (`src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:361`) and `SchemaDeriver.UlidPattern` (`src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:18`). Reconcile the planning and architecture documents through a correct-course note or epic-context regeneration.

## Deferred from: final build review of spec-2-8-protect-command-identity-and-extensions.md (2026-10-03)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: The pre-existing reachable SQL extension sanitizer alternatives lack independent negative execution tests.
  evidence: `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:95` rejects `UNION SELECT` and a trailing SQL comment through `SqlPattern` alternatives `UNION\s+SELECT` and `--\s*$`, but the negative values in `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:469` exercise other checks; deleting either alternative would evade those examples. The `';\s*(DROP|ALTER|DELETE|INSERT|UPDATE|EXEC)` alternative cannot fire alone because the dangerous-character check refuses the apostrophe in values and `KeyPattern` refuses it in keys. Add allowlisted values for each reachable alternative without dangerous characters and assert their member pointer and zero Gateway calls.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: The pre-existing reachable LDAP extension sanitizer alternatives lack independent negative execution tests.
  evidence: `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:98` rejects `)(` (also covering `*)(`) and `|(` through `LdapPattern`, but the negative values in `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:469` exercise other checks; deleting either independent alternative would evade those examples. The `&(` alternative cannot fire alone because the dangerous-character check refuses the ampersand in values and `KeyPattern` refuses it in keys. Add allowlisted values for each reachable alternative without dangerous characters and assert their member pointer and zero Gateway calls.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: The pre-existing XSS event-handler extension sanitizer alternative lacks an independent negative execution test.
  evidence: `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:92` rejects event-handler assignments such as `onclick=alert(1)` through the `XssPattern` alternative `on\w+\s*=`, but the negative values in `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:469` do not exercise it alone; deleting that alternative would evade those examples. The `<\s*script`, `<\s*iframe`, `<\s*object`, and `<\s*embed` alternatives cannot fire alone because the dangerous-character check refuses `<` in values and `KeyPattern` refuses it in keys. Add an allowlisted value without dangerous characters and assert its member pointer and zero Gateway calls.

## Deferred from: code review of spec-2-8-protect-command-identity-and-extensions.md (2026-10-03, post-completion pass)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: A ULID-kind query whose declared aggregate constant is not canonical ULID text is advertised as callable without `--aggregate-id`, but calls using that noncanonical constant fail.
  evidence: `CatalogBuilder` checks a query's `AggregateId` constant only with `RoutingResolver.IsAggregateId` (`src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:193`), never against the module's Identifier Kind. `tests/fixtures/Catalog.Routing.Contracts/ListItemsQuery.cs:7` declares `AggregateId = "routing-list"` in the ULID-kind routing fixture, and `tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs:143` pins `AggregateIdRequired` false, yet `OperationExecutor` rejects that constant at `/aggregateId` (`src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:216-220`). Passing the same noncanonical constant explicitly also fails; a canonical explicit aggregate overrides the constant at `OperationExecutor.cs:215` and succeeds when the remaining inputs are valid. This behavior predates Story 2.8, which also makes lowercase ULID constants fail. Decide whether Identifier Kind governs query constants (exempt them, or refuse them at catalog build) before Epic 4 declares module queries.

## Deferred from: post-completion build review of spec-2-8-protect-command-identity-and-extensions.md (2026-10-03)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: Discovery does not expose a module's Identifier Kind, so callers cannot determine the aggregate format from discovery when an operation has no mapped aggregate property.
  evidence: `src/Hexalith.McpCli.Core/Catalog/ModuleSummary.cs:7` exposes only name, description, and operation count; `src/Hexalith.McpCli.Core/Catalog/OperationEnvelopeDocument.cs:10` exposes only fixed tenant, requirements, and argument names. Both omit Identifier Kind at baseline `1554a84d792a0178a342d62367259999fd45e0b9`, before Story 2.8, even though execution already distinguished ULID-kind and String-kind aggregates. Decide how the public discovery documents and MCP schemas should advertise identifier rules in a later change.

## Deferred from: code review of spec-2-8-protect-command-identity-and-extensions.md (2026-10-03, follow-up pass)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: The executor validates caller envelope ULIDs and command extensions before filling and revalidating the payload, while the architecture orders them after fill, revalidation, and the aggregate accessor.
  evidence: AD-9 (`_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md:112`) and `_bmad-output/implementation-artifacts/epic-2-context.md:40` put identifier and extension validation after "fill and revalidate". `OperationExecutor` checks the correlation ID and idempotency key at `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:150-158` and extensions at `:178`, before `Fill` (`:195-198`), final validation (`:202`), and the aggregate check (`:216-220`). Every refusal still makes zero Gateway calls; the visible effect is which violation a multi-fault call reports (a bad extension hides a payload or aggregate violation). Pre-existing at baseline `1554a84` (`:149`, `:172`), and Story 2.8's task kept the ordering. Either reorder the executor or amend AD-9 and the epic context so conformance and error-precedence tests have one rule.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: `query --help` describes `--aggregate-id` but not `--entity-id`, `--page-size`, `--offset`, or `--cursor`.
  evidence: `src/Hexalith.McpCli/Cli/CliRunner.cs:205-208` creates those options without a `Description`, and `RunQueryArguments.EntityId` (`src/Hexalith.McpCli.Core/Execution/RunQueryArguments.cs:8`) says only "The optional entity identifier." Since Story 2.8 the aggregate help states the canonical uppercase ULID rule, but nothing tells a caller that entity identifiers follow Gateway syntax and accept lowercase, or gives the paging ranges and the cursor/offset exclusion that README documents. Pre-existing since Stories 2.5 and 2.6.

## Deferred from: code review of spec-2-8-protect-command-identity-and-extensions.md (2026-10-04, boundary-closure pass)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-8-protect-command-identity-and-extensions.md`
  summary: Conformance vectors cannot express a successful command call with extensions, because the loopback runner never supplies an extension allowlist.
  evidence: `tools/conformance-vectors/v1/schema.json:64` accepts `envelope.extensions`, and `tools/conformance-vectors/v1/run_loopback.py:345-347` forwards them to both heads. But `run_loopback.py:222` points each head at an empty `MCPCLI_CONFORMANCE_PROFILE_PATH` profile and never writes one, the vector schema has no allowlist input, and the allowlist comes only from the selected Profile (`src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs:103`). Every vector that supplies extensions is therefore refused by both heads with `validation_failed` at `/extensions/<key>` ("The extension key is not allowlisted.", `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:39`), although `tools/conformance-vectors/v1/README.md:15` says supplied extensions must match the expected request exactly. No sample vector uses extensions. Pre-existing: the runner and schema predate baseline `1554a84`, and allowlist enforcement predates Story 2.8. Add an allowlist input that the runner writes into the temporary Profile, plus a sample vector that sends a mixed-case approved key through both heads, before Epic 4 modules write extension vectors.

## Deferred from: review of spec-2-9-explain-execution-failures-with-stable-documents.md (2026-10-05)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-9-explain-execution-failures-with-stable-documents.md`
  summary: MCP protocol coverage does not exercise a Gateway failure, including a 2xx client exception status.
  evidence: `McpProtocolTests` covers unknown operation errors but no Gateway rejection; review loop 1 deferred this pre-existing protocol test gap to MCP execution work.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-9-explain-execution-failures-with-stable-documents.md`
  summary: Unknown CLI verbs use parser help and exit 1 instead of a stable error document.
  evidence: System.CommandLine rejects unknown verbs before a verb action; review loop 1 deferred this pre-existing parser behavior to Story 2.11.
  status: resolved in Story 2.11 (2026-10-10); `CliOutputContractTests.ParserFailuresUseSafeDocumentsAsync` verifies unknown verbs return `invalid_arguments` at exit 2 without usage or stderr token echo.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-9-explain-execution-failures-with-stable-documents.md`
  summary: Writing CLI output to a FIFO with no reader can block before cancellation takes effect.
  evidence: `CliOutput.WriteResultFileAsync` opens an existing FIFO synchronously before checking `CanSeek`; the baseline `File.WriteAllTextAsync` likewise opened the FIFO before a reader arrived. A nonblocking FIFO open and error policy are needed to bound this pre-existing behavior.

## Deferred from: code review of spec-2-9-explain-execution-failures-with-stable-documents.md (2026-10-05, pass 2)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-9-explain-execution-failures-with-stable-documents.md`
  summary: Windows `--output NUL` or `CON` may fail, or may create a literal file, instead of writing to the device.
  evidence: Unverified; would be medium if confirmed. `CliOutput.IsSpecialDevicePath` (`src/Hexalith.McpCli/Cli/CliOutput.cs:161`) is always false on Windows. `ResolveFinalSymlink` combines a relative device name with the working directory without calling `Path.GetFullPath`, so the result goes through `File.Exists` and the staged `File.Move`. The baseline `File.WriteAllTextAsync("NUL")` opened `\\.\NUL`. Settle it by running `hexalith config current --output NUL` on Windows 10 and Windows 11 and checking the exit code and whether a file named `NUL` is created; if it reproduces, detect reserved device names or character-device handles on Windows and write to them directly.

## Deferred from: implementation of spec-2-10-refuse-writes-in-read-only-mode.md (2026-10-05)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-10-refuse-writes-in-read-only-mode.md`
  summary: Reconcile the pre-existing EventStore package versions with the exact dependency policy so the Manifest acceptance gate passes.
  evidence: Story 2.10 full Manifest run exited 1 in ProductionContractsStayWithinPinnedDependencyClosure: Client and Contracts restore as 3.112.0 while tools/dependency-policy.json pins 3.110.0; current Builds declares 3.113.0. These inputs are unchanged by story 2.10. Seven other Manifest tests and all five other test suites pass. Exact command and logs are recorded in the story spec; dependency changes are outside this story.
  status: resolved by `4d39200` (2026-10-05) for 3.113.0, then by `c6cd224` (2026-10-08) for 3.117.1. The `342e072` Builds bump moved the `HexalithEventStoreVersion` default to 3.117.1 and failed CI run 37814775292. After a fresh restore, the policy pins that exact version and the full Manifest suite passes 8/8. When bumping `references/`, run the Manifest suite and align the policy in the same commit.

## Deferred from: code review of spec-2-10-refuse-writes-in-read-only-mode.md (2026-10-05)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-10-refuse-writes-in-read-only-mode.md`
  summary: Global option help does not name environment variables or explicit boolean values; `--read-only` says only "Disable command submission".
  evidence: Pre-existing since `de67938`. `src/Hexalith.McpCli/Cli/GlobalOptionsBinding.cs:10-19` descriptions omit every `EVENTSTORE_*` variable, so `--help` does not reveal `EVENTSTORE_READ_ONLY` or that `--read-only false` overrides it. This is a CLI-wide help convention; settle it once for all global options rather than for `--read-only` alone.

## Deferred from: code review of spec-2-11-keep-cli-output-and-exit-codes-predictable.md (2026-10-09)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: CI never executes the CLI's native output file-type inspection on macOS, linux-arm64, or linux-arm32.
  evidence: `src/Hexalith.McpCli/Cli/OutputFileType.cs:38` uses fixed-layout Linux `statx` and platform-specific macOS `stat` symbols and `st_mode` layouts, but `.github/workflows/ci.yml:18` delegates to `Hexalith.Builds/.github/workflows/domain-ci.yml@main`, which runs only on `ubuntu-latest` x64; the conformance jobs are also `ubuntu-latest`. A Linux `statx` interop failure or a wrong macOS symbol or offset could reject existing `--output` targets while CI stays green. The Windows branch is already tracked at the Story 2.3 Windows-evidence entry (Story 4.16 owns the Windows test run); this entry covers only the macOS and ARM legs, which belong in the shared Builds workflow matrix or Story 4.16's macOS installation check.
  status: open; Story 4.16 adds the macOS installation smoke and complete CLI suite (`.github/workflows/release.yml:245`, `:276`), but no macOS runner result has executed in this implementation session. ARM qualification remains deferred; no platform acceptance is claimed.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: Verify output to a seekable character device located outside `/dev` before relying on preflight to protect mutations.
  evidence: `CliOutput.Preflight` (`src/Hexalith.McpCli/Cli/CliOutput.cs:17`) accepts a writable device at `:54` by native file type, while `WriteResultFileAsync` (`src/Hexalith.McpCli/Cli/CliOutput.cs:147`) writes directly only when the handle is nonseekable or the resolved path begins under `/dev/`. A privileged fixture that creates or mounts a character device outside `/dev` and confirms `FileStream.CanSeek` is true would show whether a later staged write can fail after a Gateway call or profile mutation. Such a target was not reachable in the current nonprivileged Linux test environment.

## Deferred from: code review of spec-2-11-keep-cli-output-and-exit-codes-predictable.md (2026-10-10)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: An accepted `send` whose runtime `--output` write fails reports only "The CLI action failed.", losing the message and generated correlation identifiers.
  evidence: Medium. `CliRunner.RunAsync`'s catch-all (`src/Hexalith.McpCli/Cli/CliRunner.cs:794`) discards the `CommandResult` when `CliOutput.WriteAsync` throws after the Gateway accepted the command; `ExecutionFailureCommandTests.AcceptedCommandDeviceWriteFailureReportsAfterOneRequestAsync` pins `internal_error` after one request via `/dev/full`. The README says not to retry, but without `messageId` or a generated `correlationId` the caller cannot check the outcome. Pre-existing: the baseline `AcceptedCommandOutputFailureReportsErrorAfterOneRequestAsync` asserted the same document. Returning the identifiers needs a new error member or a stderr channel, so it needs a contract decision.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: `--output` naming the profile file overwrites the profile store with the result document.
  evidence: Medium. Reproduced 2026-10-10 on the HEAD Debug build with an isolated `HOME`: `config profile add dev --url https://gw.example`, then `config use dev --output ~/.eventstore/mcpcli.json` exits 0 and leaves `{"activeProfile":"dev"}`; the next `config current` returns `configuration_invalid`, and every stored profile and token is lost. Preflight accepts the existing regular file (`src/Hexalith.McpCli/Cli/CliRunner.cs:645`) and the writer replaces it after `ProfileStore.Use`. Pre-existing writer behavior: Story 2.11 review loops 1–7 deferred it (B1 and carried items) without a ledger entry. A guard that compares the resolved output with `ProfileStore.ProfilePath`, its lock and temporary files, including hard links, needs an owning settings story.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: Verify the FreeBSD x64 native result-target inspection on an existing output file.
  evidence: Unverified, medium if wrong. `src/Hexalith.McpCli/Cli/OutputFileType.cs:51` reads `st_mode` from the FreeBSD x64 `stat` layout, but the shared CI job at `.github/workflows/ci.yml:18` invokes `domain-ci.yml@main` on Ubuntu x64. A FreeBSD x64 run of `CliOutputContractTests.MutationPreflightRemovesProbeFilesAsync` would settle whether valid existing-file output is classified correctly before a profile mutation.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: No running test reaches the existing-file mode-bit preflight guard, the only preflight refusal a root process gets for a read-only or write-only result file.
  evidence: Medium. For root, `faccessat(..., AT_EACCESS)` in `OutputFileType.RequireAccess` succeeds whatever the mode bits are. That leaves the read/write mode-bit check in `CliOutput.PreflightCore` (`src/Hexalith.McpCli/Cli/CliOutput.cs:67-72`) as the only refusal of a 0400 or 0200 existing target before a Gateway request or profile mutation. As non-root, which is how CI runs, `RequireAccess` rejects such a file first. As root, `DeniedRegularAndNewFileParentPreventMutationAsync` is skipped entirely (`tests/Hexalith.McpCli.Cli.Tests/CliOutputContractTests.cs:969`), so deleting the guard keeps every run green. Without it, a root send or config mutation would complete and then fail in the writer's own mode check with "The CLI action failed." Settle with a privileged CI run that asserts the preflight document, an unchanged profile and zero Gateway calls for a 0400 target. As a cheaper partial step, split the existing-file case out of the root skip so root developer runs exercise it.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: The agent-instruction channel summary says CLI results and errors both go to stdout as JSON, which misstates table, file and MCP output.
  evidence: Low. `AGENTS.md:110` (synced to `CLAUDE.md:110` and `.github/copilot-instructions.md:110`): with `--format table`, `modules`, `operations` and `config` results are tab-separated tables (`src/Hexalith.McpCli/Cli/CliOutput.cs:110`); with `--output`, results go to the file and stdout stays empty; `mcp` failures use stderr. An agent following the line could "fix" table or file output. The line sits in the bmad-project-context managed block, so correct it in the next refresh.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: The agent instructions' "Out of version one (PRD §8.2)" refusal list mixes PRD sections and omits scoped-out items.
  evidence: Low. `AGENTS.md:86` (and its synced copies) lists "any OAuth or identity server", which is a §8.3 non-goal (`_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md:513`). It omits §8.2's query correlation and extensions, search, filter, order-by and freshness Query arguments, and command status lookup (`prd.md:506-507`), plus §8.3's rule that the tool never calls a Module's REST or Dapr API (`prd.md:514`). Correct it in the next bmad-project-context refresh.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-11-keep-cli-output-and-exit-codes-predictable.md`
  summary: The `\z` regex pitfall in the agent instructions has no scope and could be applied to JSON Schema patterns.
  evidence: Low. `AGENTS.md:120` (and its synced copies) says to anchor validation regexes with `\z`, while `AGENTS.md:85` names `SchemaDeriver.UlidPattern` (`src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:18`, emitted at `:303` and `:390`) as the schema check. That pattern is an ECMA-262 JSON Schema `pattern`, where `\z` is not an end anchor, so applying the pitfall there would break client-side ULID validation; DW-1's planned `[GeneratedRegex]` scan would not catch it. Limit the line to .NET `Regex` and `[GeneratedRegex]` in the next bmad-project-context refresh.

## Deferred from: bmad-project-context refresh of the agent instructions (2026-10-10)

### DW-1: Fail tests on `$`-anchored validation regexes

origin: bmad-project-context refresh of the agent instructions, 2026-10-10
location: src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:364
severity: medium
reason: Add a Core.Tests test that reflects over `[GeneratedRegex]` patterns in `src` and fails when a `^`-anchored pattern ends in `$` instead of `\z`, because .NET `$` also matches before a trailing newline and reviews reported this defect class about eight times. Fix the remaining `ProfileStore.ProfileNamePattern` instance first (the open spec-2-3 ninth-pass entry); once the test lands, a refresh deletes the `\z` pitfall line from the AGENTS.md managed block.
status: open

### DW-2: Fail tests when a CLI option or argument has no Description

origin: bmad-project-context refresh of the agent instructions, 2026-10-10
location: src/Hexalith.McpCli/Cli/CliRunner.cs
severity: medium
reason: Add a Cli.Tests test that walks the command tree and fails on any option or argument without a `Description`; reviews flagged missing descriptions eight times (specs 2.3, 2.8, 2.10) and about ten still lack one, overlapping the open spec-2-3 eleventh-pass and spec-2-8 follow-up-pass entries. The user chose this check over an AGENTS.md line, so no instruction covers the rule until it lands.
status: open

## Deferred from: review of spec-3-1-discover-operations-through-a-fixed-mcp-surface.md (2026-10-10)

- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-discover-operations-through-a-fixed-mcp-surface.md`
  summary: Validate each MCP output schema against actual success and error structured documents.
  evidence: Medium. `tests/Hexalith.McpCli.Mcp.Tests/McpToolRegistrationTests.cs:34` checks only the `oneOf` branch count. Story 3.3 explicitly requires closed success and error branches validated under both protocol revisions.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-discover-operations-through-a-fixed-mcp-surface.md`
  summary: Verify distinct version-appropriate MCP session flows rather than varying only the requested protocol version.
  evidence: Medium. `tests/Hexalith.McpCli.Mcp.Tests/McpProtocolTests.cs:65` asserts each requested revision is negotiated, but both revisions run over in-process streams and never check handshake-free discovery. Story 3.2 owns the stdio exchange through each version-appropriate flow.
  status: resolved in Story 3.2 (2026-10-11); `McpStdioProcessTests.SdkClientDiscoversOverCleanStdioAsync` connects pinned SDK clients to the fixture process, records `initialize` as the 2025-06-18 first request and `server/discover` as the 2026-07-28 first request, then verifies discovery and normal shutdown.

## Deferred from: code review of spec-3-1-discover-operations-through-a-fixed-mcp-surface.md (2026-10-11)

- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-discover-operations-through-a-fixed-mcp-surface.md`
  summary: The README does not say how MCP failures reach the client.
  evidence: Low. `README.md:124` documents discovery only. Error delivery as `isError: true` with `{"error": …}` in `structuredContent` and the first text item (`src/Hexalith.McpCli.Mcp/McpToolHandlers.cs:99-109`), and protocol InvalidParams for a missing or blank `module` or `operation` (`src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:70-76`), predate baseline `12b54bd`. Story 3.3's acceptance criteria pin the MCP error contract; document both channels in the README in that change.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-discover-operations-through-a-fixed-mcp-surface.md`
  summary: MCP input schemas carry no parameter descriptions or `kind` enum.
  evidence: Medium. The `McpToolHandlers` parameters (`src/Hexalith.McpCli.Mcp/McpToolHandlers.cs:20`, `:49-52`, `:62-65`) have no description attributes, so `McpServerTool.Create` advertises `kind` without its allowed values and `payload` as a bare string with no hint that it is JSON text. An agent learns either rule only from a failed call. Pre-existing at baseline `12b54bd`. Story 3.3 binds the §E arguments; add descriptions there and keep the input budget below 8,000 characters.

## Deferred from: code review of spec-3-2-run-the-mcp-server-over-clean-stdio.md (2026-10-16)

- source_spec: `_bmad-output/implementation-artifacts/spec-3-2-run-the-mcp-server-over-clean-stdio.md`
  summary: The real SDK hosted service is never faulted, so the fault detection in `RunMcpHostAsync` is pinned only by a synthetic `BackgroundService`.
  evidence: Unverified Medium. `src/Hexalith.McpCli/Cli/CliRunner.cs:787-788` filters `OfType<BackgroundService>()`; `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:732` uses its own `FaultingService`, and the process tests assert only exit 0. If an SDK upgrade registers the stdio server as a plain `IHostedService`, a serving fault exits 0 again. Assert that the hosted service from `HostFactory.Create(mcp: true)` is a `BackgroundService` to settle it.

## Deferred from: code review of spec-3-3-execute-calls-with-structured-mcp-results.md (2026-10-16)

- source_spec: `_bmad-output/implementation-artifacts/spec-3-3-execute-calls-with-structured-mcp-results.md`
  summary: The Int32 paging check reads `pageSize` and `offset` by exact name, so a differently cased key may still reach the SDK's case-insensitive binding.
  evidence: Unverified Medium. `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:89` loops over the two exact names. Settle it by sending `{"PageSize": 2147483648}` through the stdio fixture and checking stderr for a `JsonException`.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-3-execute-calls-with-structured-mcp-results.md`
  summary: An existing `QueryCommandTests` HTTP-listener cleanup race failed the first CLI test run.
  evidence: Low. `_bmad-output/implementation-artifacts/spec-3-3-execute-calls-with-structured-mcp-results.md:106` records it; the affected method passed in isolation and no ledger entry tracked it.

## Deferred from: code review of spec-4-1-approve-the-parties-migration-inventory.md (2026-10-16)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-1-approve-the-parties-migration-inventory.md`
  summary: The inventory maps no expected outcome for `delete_party` on a missing or erased party, so Stories 4.11/4.13 have no oracle for that case.
  evidence: Unverified Medium. `_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md:124` (C05) covers only the already-inactive case. Settle it by reading the pinned Parties `delete_party` pre-read in `src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs` and checking whether C05 or T07 already defines not-found and erased behavior.

## Deferred from: spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md (2026-10-16)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md`
  summary: Reconcile the exact production dependency policy after the separately committed Builds bump, then verify it against a fresh restore.
  evidence: Medium; pre-existing before the approved Story 4.3 implementation. Commit `1a6d725fb89545bce56b7be1e16683461cf9cfe7` advances `references/Hexalith.Builds`; its `Props/Directory.Packages.props:242` and `:244` require Microsoft.Extensions.Hosting/Http 10.0.13, while `tools/dependency-policy.json:51` and `:53` require 10.0.12. Current `src/Hexalith.McpCli/obj/project.assets.json` still contains 10.0.12 and is stale for those pins. `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:137` rejects restored versions outside the exact policy. The McpCli dependency maintainer should run `dotnet restore Hexalith.McpCli.slnx`, align every changed version in the policy, build and run Manifest.Tests; this documentation-only story neither changes those dependencies nor claims that broad gate passed.


## Deferred from: code review of spec-4-5-gate-module-coverage-against-the-approved-inventory.md (2026-10-17)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-5-gate-module-coverage-against-the-approved-inventory.md`
  summary: Nothing ties an enrolled module to a required coverage inventory, so a module can be enrolled without the gate ever running for it.
  evidence: Medium. The gate runs only where a test calls `InventoryCoverageGate.CheckFile` with a hand-copied artifact (`tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj:15`); `tools/inventory-coverage/v1/README.md:92` hands off per-module test wiring, while enrollment is meant to be configuration only. No module is enrolled yet (`tools/dependency-policy.json` `modules: {}`). The first enrolling story (4.9/4.10) should fail CI when a `modules` entry has no approved inventory, without module-specific code.

## Deferred from: code review of spec-4-6-publish-the-bootstrap-decoration-package.md (2026-10-18)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-6-publish-the-bootstrap-decoration-package.md`
  summary: The agent instructions do not name the release script suite or the bootstrap gate that runs it.
  evidence: Low. `AGENTS.md:96` (`Running and verifying`, synced to `CLAUDE.md` and `.github/copilot-instructions.md`) lists only .NET test commands. It has no `python3 -m unittest discover -s scripts/tests` command and does not mention `.github/workflows/bootstrap-package.yml:31`, so an agent changing `scripts/release-*.sh` or the release Python scripts may skip `scripts/tests/test_bootstrap_release.py` until CI runs it. Add one line in the next bmad-project-context refresh, copy it to the other two entry points, and run `scripts/check-agent-instructions-sync.sh`.

## Deferred from: code review of spec-4-7-enforce-the-production-dependency-boundary.md (2026-10-18)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-7-enforce-the-production-dependency-boundary.md`
  summary: The production dependency gate does not inspect `Reference` (including `HintPath`) or `PackageDownload` items in `src/` projects.
  evidence: Medium; pre-existing. `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:33`, `:53` and `:62` read only `ProjectReference`, `FrameworkReference` and `PackageReference`, and `RestoredDependencyGraph.cs:87` reads only `project.assets.json`, which never lists these items. A `<Reference Include="X" HintPath="../../references/.../X.dll" />` in a production project would ship another module's assembly with every gate green. Add a source-project failure for any `Reference` or `PackageDownload` item, with an exact-diagnostic test.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-7-enforce-the-production-dependency-boundary.md`
  summary: Per-project dependency direction (Abstractions has zero package references; Core has no MCP, System.CommandLine or ASP.NET dependency) is not enforced in CI.
  evidence: Medium; pre-existing. `_bmad-output/planning-artifacts/epics.md:138` requires the hexagonal direction (AD1–AD3), but `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyGate.cs:105` and `:218` accept any `directPackages` entry on any production project, so Abstractions adding `ModelContextProtocol` or Core adding `System.CommandLine` passes Manifest.Tests. Only `scripts/validate-release-packages.py:64` checks Abstractions, at release time. Add a reviewed per-project allowance to the policy or the gate, without module-specific code.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-7-enforce-the-production-dependency-boundary.md`
  summary: The dependency gate does not detect a stale or missing `src/Hexalith.McpCli/obj/project.assets.json`.
  evidence: Low; pre-existing (the replaced test read the same file). `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs:944` loads whatever assets file exists. A stale restore gives a local false pass, or misleading "Direct package X has no production reference" failures, the pitfall `CLAUDE.md` records ("a stale restore passes locally and fails in CI"). A missing file throws a bare `FileNotFoundException`. CI restores fresh. Compare `project.restore.projectPath` and the tool's evaluated `PackageReference` items with the assets file, and fail with a message to run `dotnet restore Hexalith.McpCli.slnx`.

## Deferred from: spec-4-8-make-tenants-gateway-ready-for-v1.md (2026-10-19)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: Release the decorated `Hexalith.Tenants.Contracts`, bump `HexalithTenantsVersion` in Hexalith.Builds, move McpCli's Builds gitlink, and enroll Tenants by flagged reference and `modules` pin.
  evidence: Split from Story 4.8 at the scope gate on 2026-10-19 (user chose "Split"). Publication is irreversible and needs an explicit go-ahead; it covers the epic AC "Given the first approved decorated Tenants Contracts release" (`_bmad-output/planning-artifacts/epics.md:1311-1314`). Today `references/Hexalith.Builds/Props/Directory.Packages.props:14` pins 5.8.0 (undecorated) and `tools/dependency-policy.json` has `modules: {}`. Re-validate the vectors against the immutable release artifact with its final version, record the description review in the Tenants pull request, then run a fresh restore and Manifest.Tests with every changed policy version updated.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: Live vectors cannot feed a returned continuation cursor or run-generated audit times into a later step, so the Tenants live paging and filter proof cannot run under vector contract v1.
  status: resolved in Story 4.13 (2026-10-25); strict hash-bound companion plans capture actual cursors/timestamps and bind later Query calls without changing v1 vector bytes. `tools/live-topology/live_plans.py:90` resolves typed bindings, `tools/live-topology/run_live.py:19` checks live documents, and `_bmad-output/implementation-artifacts/evidence/story-4-13/parent-audit/live-acceptance-audit.json:1` records all 21 passing cases, including Tenants continuation and audit category/time inclusion/exclusion, with all 53 declared Command steps submitted once.
  evidence: Handed to Story 4.13 at the Story 4.8 scope gate on 2026-10-19 (user chose "Hand off to 4.13"). `tools/conformance-vectors/v1/schema.json:76` and `:92` accept only a literal `cursor`, and `tools/conformance-vectors/v1/validate.py:193-196` requires the expected Gateway paging to equal those literal envelope values. A live cursor is codec-protected and unknown in advance. `_bmad-output/planning-artifacts/epics.md:1301-1304` keeps Tenants Gateway-ready acceptance blocked until a live non-default page and its returned cursor pass, so Story 4.13 needs an approved way to capture a step output, without module-specific code.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: `tenants.get-user-tenants` called without a payload `UserId` lists a user literally named `index`, instead of the caller.
  evidence: Low; pre-existing handler rule, now reachable through McpCli. The Gateway defaults the entity id to the aggregate id, and `/home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants/Queries/Handlers/GetUserTenantsQueryHandler.cs:135` targets any non-blank entity, so the target becomes `index` and the result is usually empty. The operation description tells callers to always set `UserId`. The Tenants maintainer should choose: treat an entity equal to the aggregate id as the caller (changes REST only for a real user named `index`), or make `UserId` schema-required.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: Generic gateway callers cannot select the audit owner stream, because `GetTenantAuditQuery.Stream` is read only from the REST camelCase `stream` field.
  evidence: Low; Story 4.8's boundary named only the `From`, `To` and `Category` filters. `/home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants.Contracts/Queries/GetTenantAuditQuery.cs:35` describes `Stream` as having no effect for McpCli calls. The Tenants maintainer should decide whether McpCli callers may select `tenant` or `global-administrators` (system scope only) and, if so, honor the CLR `Stream` with the same selector validation.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: Any caller can add the first member, with any role including TenantOwner, to a tenant that has never had a member; that path is now reachable through McpCli.
  evidence: Medium; pre-existing authorization rule, confirmed by the Story 4.8 NFR-8 reviewer (round 2, observation 16). `/home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants.Server/Aggregates/TenantAggregate.cs:104` gates owner checks on `state.HasMembershipHistory` (`TenantState.cs:13,45`), and `tenants.add-user-to-tenant` now exposes it to agents. Story 4.8 forbade changing authorization. The Tenants maintainer should confirm it is intended, or restrict first-member creation, for example to a global administrator.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: Tenants IntegrationTests fails deterministically on `TenantsApiStructuralTests.TenantsSources_DelegateDaprRoutingHeaderOwnershipToThePlatformHandlerOnly`, which flags `src/Hexalith.Tenants/Authorization/TenantOwnerSourceGateway.cs`.
  evidence: Medium; pre-existing, unrelated to Story 4.8. Rerun on 2026-10-20 it failed 1/1 (`/home/administrator/projects/hexalith/tenants/tests/Hexalith.Tenants.IntegrationTests/TenantsApiStructuralTests.cs:181`). The flagged file was last changed in `bbd95f95`, and Story 4.8 touches neither it nor IntegrationTests. Fix in the Tenants repository: either move that file's Dapr routing-header handling to the platform handler, or correct the structural rule.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: Enrolling the decorated Tenants Contracts forces McpCli onto EventStore 3.125.1 or later and Commons 2.30.3, which changes the tool's own gateway client and needs the conformance gates.
  evidence: Medium. The decorated Contracts depends on EventStore.Contracts 3.125.1 or later, and the Story 4.8 scratch host built only with `-p:HexalithEventStoreVersion=3.125.1 -p:HexalithCommonsVersion=2.30.3` (`_bmad-output/implementation-artifacts/evidence/story-4-8/verification.md`). Meanwhile `references/Hexalith.Builds/Props/Directory.Packages.props:6,9` and `tools/dependency-policy.json:26-27` pin 2.30.1 and 3.124.0. The enrolling story must move these pins with the Builds gitlink and update every policy version. It must also run `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` and `bash tools/conformance-vectors/v1/run-sample-loopback.sh` (then `dotnet restore Hexalith.McpCli.slnx`), plus Manifest.Tests, because the gateway client changes.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: A Tenants release could ship from pushed commit `6b62b6b3`, whose decorated descriptions promise filtering and paging that its handlers ignore; the vector approval is bound to no vector revision.
  evidence: Medium. `6b62b6b3` on Tenants `origin/main` carries only the decoration snapshot, and `/home/administrator/projects/hexalith/tenants/.github/workflows/release.yml:8` can run from any `main` commit by manual dispatch. `_bmad-output/implementation-artifacts/evidence/story-4-8/approvals.md:37` records the vector revision as "Not yet committed". Release only from a commit that contains Story 4.8's handler migration, vectors and description fixes. Record that commit and the immutable release artifact's sha512 in the vector approval before enrollment.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-8-make-tenants-gateway-ready-for-v1.md`
  summary: `tenants.set-tenant-configuration` accepts an empty `Key` through the gateway, because the Tenants `SubmitCommand` payload validators do not run for gateway submissions.
  evidence: Low; pre-existing, now reachable through McpCli (Story 4.8 code review, 2026-10-20). `/home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants.Server/Aggregates/TenantAggregate.cs:155` rejects only keys longer than 256 characters. The `MinimumLength(1)` rule in `SetTenantConfigurationValidator` is reached only through `TenantSubmitCommandValidator`, which switches on CLR names such as `nameof(SetTenantConfiguration)` (`/home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants/Validation/TenantSubmitCommandValidator.cs:20-27`). Gateway submissions carry wire types such as `set-tenant-configuration`, the validator tests build commands with `typeof(T).Name`, and the validator is registered (`Program.cs:70`) in a host that is domain-service only (`Program.cs:40`). The same mismatch skips the `AddUserToTenant`, `ChangeUserRole` and `RemoveTenantConfiguration` payload validators. REST cannot send an empty key because it is a route segment. Deferred because changing domain behavior is outside Story 4.8's boundary. The Tenants maintainer should choose: reject empty keys in the aggregate, or rewire or remove the validators that never run. The Story 4.8 code review changed the `Key` description to "at most 256 characters" (uncommitted in the Tenants working tree on 2026-10-20).

## Deferred from: code review of spec-4-9-declare-parties-commands-for-the-gateway.md (2026-10-20)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-9-declare-parties-commands-for-the-gateway.md`
  summary: Changing a preferred contact channel's `Type` without `IsPreferred` leaves two preferred channels of the target type.
  evidence: Medium; pre-existing aggregate behavior, now reachable through `parties.update-party`. `/home/administrator/projects/hexalith/parties/src/Hexalith.Parties/Domain/PartyAggregate.cs:554` emits `PreferredContactChannelChanged` only when `IsPreferred == true`, and the apply step keeps the old flag (`:1697`), so a preferred Email moved to Phone stays preferred beside the existing preferred Phone. A later `IsPreferred=true` on it emits nothing, because it is already preferred and its type no longer changes. The standalone `UpdateContactChannel` path has the same rule (`:1228`). The Story 4.9 descriptions tell callers to send `IsPreferred=true` with a type change. Story 4.9 forbade domain changes. The Parties maintainer should choose: emit the preference change whenever a preferred channel changes type, or reject type changes on preferred channels that omit `IsPreferred`.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-9-declare-parties-commands-for-the-gateway.md`
  summary: A Parties validation rejection persists one failure per invalid list item, with no cap.
  evidence: Medium; pre-existing. `/home/administrator/projects/hexalith/parties/src/Hexalith.Parties/Domain/PartyDomainProcessor.cs:610` maps every FluentValidation error into `PartyCommandValidationRejected.Failures`, and the composite validators keep evaluating per-item rules after the sub-operation cap fails. Empty-string removal IDs already produced one failure each. Story 4.9's per-item `NotNull` rules add null items as a second route, with two failures per null removal ID because `NotEmpty` also fires. A single request carrying a long list of nulls or empty IDs therefore persists a rejection event that grows with the request. Cap the reported failures, or stop per-item rules once the cap fails, in the Parties repository.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-9-declare-parties-commands-for-the-gateway.md`
  summary: Parties CI never builds McpCli's Catalog over `Hexalith.Parties.Contracts`, so a declaration McpCli rejects can ship with Parties CI green.
  evidence: Medium. `/home/administrator/projects/hexalith/parties/tests/Hexalith.Parties.Contracts.Tests/McpCliDecorationTests.cs:42` checks examples only with STJ deserialization, whose enum read ignores case, while `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:217-229` validates them against the case-sensitive derived schema. An example with `"Type":"person"` would pass Parties CI and fail McpCli discovery with `invalid_example`. The Parties `tests/conformance-vectors/mcpcli-v1/*.json` files are not run by any Parties workflow, and Story 4.9 checked the Catalog once, by hand (`_bmad-output/implementation-artifacts/evidence/story-4-9/catalog-checks.json`). Story 4.10 rebinds the vectors to the complete artifact, so add an automated Catalog, lint and vector gate there or in Parties CI.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-9-declare-parties-commands-for-the-gateway.md`
  summary: `update-party` and `deactivate-party` change a party that was never created when its stream holds only rejection events.
  evidence: Medium; pre-existing aggregate behavior, now reachable through McpCli (Story 4.9 code review pass 3, 2026-10-20). The chain of evidence:
    - EventStore stores domain rejections as ordinary stream events (`references/Hexalith.EventStore/src/Hexalith.EventStore.Server/Actors/AggregateActor.cs:1428` and `:1710-1723`).
    - When there is no snapshot but events exist, `/home/administrator/projects/hexalith/parties/src/Hexalith.Parties/Domain/PartyDomainProcessor.cs:427` rehydrates a new `PartyState`. Replaying ignores rejection events, which have no `Apply` overload (`:518-535`).
    - `Handle(UpdatePartyComposite)` (`PartyAggregate.cs:232`) and `Handle(DeactivateParty)` (`:870`) check only `state is null`, not `HasBeenCreated`. `IsActive` defaults to true (`PartyState.cs:35`).

    The failure case: a first `update-party` on a missing or mistyped ID stores `PartyNotFound`, which is an `IRejectionEvent`. A second `update-party` then appends contact-channel or identifier events, and `deactivate-party` appends `PartyDeactivated`, all for a party that was never created. Only the create handlers check `HasBeenCreated` (`PartyAggregate.cs:59`, `:721`). Fixing this is a domain change outside Story 4.9's boundary. The Parties maintainer should reject non-create commands when `!state.HasBeenCreated`, and add a regression test in the processor or aggregate that makes two calls on a missing ID.

## Deferred from: code review of spec-4-10-add-parties-queries-and-pin-complete-coverage.md (2026-10-21)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-10-add-parties-queries-and-pin-complete-coverage.md`
  summary: The agent instructions still describe module enrollment as only a flagged `PackageReference` plus a `modules` pin.
  evidence: Low. `AGENTS.md:83` (byte-identical in `CLAUDE.md` and `.github/copilot-instructions.md`). Since Story 4.10, CI's `enrolled-module-conformance` job also requires `tools/conformance-vectors/v1/modules/<PackageId>/approval.json` with exact artifact, inventory and vector hashes plus complete vectors (`tools/conformance-vectors/v1/check_enrolled.py:92-107`), and `EnrolledModuleCoverageTests` requires a release `tools/inventory-coverage/v1/<module>-approved.json` (`tests/Hexalith.McpCli.Core.Tests/EnrolledInventoryCoverageGate.cs:22`). An agent following the line turns CI red, and "Running and verifying" names neither `check_enrolled.py` nor the inventory. Correct both in the next bmad-project-context refresh, copy `AGENTS.md` to the other two entry points, and run `scripts/check-agent-instructions-sync.sh`.
  status: resolved (2026-10-28)
  resolution: `AGENTS.md:84` now requires release inventories, exact artifact/inventory/vector approvals, complete vectors and companion live plans; `AGENTS.md:104` names the coverage and enrolled-replay gates with prerequisites. Synced to both entry points and tracked in `spec-resolve-five-deferred-guidance-items.md`.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-10-add-parties-queries-and-pin-complete-coverage.md`
  summary: The A1 Parties inventory's eligibility rule contradicts the Story 4.10 enrollment.
  evidence: Low. `_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md:31-33` says `include` values "become eligible for enrollment only after the missing Contracts, authorization and behavior evidence proves readiness". `src/Hexalith.McpCli/Hexalith.McpCli.csproj:24` now enrolls `Hexalith.Parties.Contracts`, while the frozen 4.10 intent keeps C06–C08 and Stories 4.11/4.13 as downstream gates (`spec-4-10-add-parties-queries-and-pin-complete-coverage.md:51`). Agents reading the inventory as context for 4.11/4.13 meet a contradictory rule. The inventory is owner-approved A1 evidence, so the owner should reword or annotate the eligibility sentence; no code change is needed.

## Deferred from: final implementation review of spec-4-11-prove-both-heads-agree-against-a-loopback-gateway.md (2026-10-22)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-11-prove-both-heads-agree-against-a-loopback-gateway.md`
  summary: The established replay helper discards successful-process stderr instead of retaining it with operation observations.
  evidence: Low; pre-existing in baseline `fce41d05e25b8c2076cc02266608460ec86ed635`. `tools/conformance-vectors/v1/run_loopback.py:277` returns parsed CLI stdout without retaining stderr, and `:322` closes the normal MCP stderr pipe. Existing product channel-contract tests remain in place, and no current incorrect product output was demonstrated; replay receipts themselves cannot supply those channel diagnostics. A future harness improvement should retain both channels and define expected MCP startup logging separately from CLI diagnostics. Parent searched the ledger before appending and found no equivalent open entry.

## Deferred from: code review of spec-4-11-prove-both-heads-agree-against-a-loopback-gateway.md (2026-10-22)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-11-prove-both-heads-agree-against-a-loopback-gateway.md`
  summary: The 500 ms first-construction limit also runs in the ordinary parallel unit tier and may flake under CI CPU contention.
  evidence: Unverified (`maybe-false`); medium if true. `tests/Hexalith.McpCli.Core.Tests/CatalogPerformanceTests.cs:15` is a plain `[Fact]`. Core.Tests is in the `ci` job's unit list (`.github/workflows/ci.yml:25`). `LimitViolation` applies without `MCPCLI_BENCHMARK_REQUIRE_V1` (`CatalogPerformanceTests.cs:76`). The child therefore competes with Core.Tests' parallel classes for ubuntu-latest CPU. Two local 14-core parallel runs measured 146.3 and 124.9 ms; the dedicated Ubuntu step measured 194.5 and 242.6 ms. To settle it, record the unit-tier child's `elapsedMilliseconds` across several ubuntu-latest `ci` runs. If the margin is thin, enforce the limit only in the dedicated `enrolled-module-conformance` step, or put the class in a non-parallel collection.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-11-prove-both-heads-agree-against-a-loopback-gateway.md`
  summary: The agent instructions still present the ConformanceHost as the way to reproduce isolated-module or empty-catalog behavior.
  evidence: Low. `AGENTS.md:119` is byte-identical in `CLAUDE.md` and `.github/copilot-instructions.md`. `tests/Hexalith.McpCli.ConformanceHost/Hexalith.McpCli.ConformanceHost.csproj:6` now defaults to `ConformanceProduction=true`, which loads the production manifest without the sample. Only `-p:ConformanceProduction=false` restores the isolated sample host (`tools/conformance-vectors/v1/run-sample-loopback.sh:18-20`). An agent that follows the line reproduces against Parties and Tenants instead of an isolated module. Correct this in the next bmad-project-context refresh, together with the open enrollment-wording entry under the Story 4.10 heading. Then copy `AGENTS.md` to the other two entry points and run `scripts/check-agent-instructions-sync.sh`.
  status: resolved (2026-10-28)
  resolution: `AGENTS.md:123` distinguishes the production host, fixture/empty assembly injection, and the sample script's explicit `ConformanceProduction=false` restore/build; it also requires restoring/rebuilding the production host before production checks. Synced to both entry points and tracked in `spec-resolve-five-deferred-guidance-items.md`.

## Deferred from: resumed pass 4 implementation review of spec-4-11-prove-both-heads-agree-against-a-loopback-gateway.md (2026-10-22)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-11-prove-both-heads-agree-against-a-loopback-gateway.md`
  summary: Preserve completed package results in the root enrollment receipt when a later package fails.
  evidence: Low; inherited from baseline `fce41d05e25b8c2076cc02266608460ec86ed635`. `tools/conformance-vectors/v1/check_enrolled.py:182-190` accumulates successful child results locally and assigns root `results` only after the complete package loop. A later verification failure leaves root results empty, although the completed package's separate verification receipt remains available. Persist each completed result as progress without changing overall acceptance.

## Deferred from: code review of spec-4-12-compose-the-v1-live-test-topology.md (2026-10-23)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-12-compose-the-v1-live-test-topology.md`
  summary: The published platform topology fixture can wait indefinitely for its cross-process lock before starting its startup timeout.
  evidence: Medium; pre-existing in EventStore.Testing.Integration 3.126.1. `references/Hexalith.EventStore/src/Hexalith.EventStore.Testing.Integration/AspireTopologyFixtureBase.cs:113` calls `AcquireDaprFixtureLock` before constructing its startup CTS; `:203` retries the exclusive file open indefinitely. The platform owner should add cancellation and a finite acquisition deadline. McpCli must retain the published lifecycle rather than copy it; its supported command uses a separate outer process deadline. No equivalent ledger entry existed when checked.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-12-compose-the-v1-live-test-topology.md`
  summary: The agent instructions do not describe the Story 4.12 live-topology test project and tools.
  evidence: Low. `AGENTS.md:100`, which is byte-identical in `CLAUDE.md` and `.github/copilot-instructions.md`, says a test project absent from the CI test list is silently skipped. `tests/Hexalith.McpCli.Integration.Tests` is deliberately absent from `unit-test-projects` (`.github/workflows/ci.yml:22-28`), because its fixture refuses to run outside `tools/live-topology/run-isolated.py` (`tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:35-36`). The `dotnet test tests/<Project>` command prescribed at `AGENTS.md:99` therefore fails for that project. The instructions also omit CI's `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` check (`.github/workflows/ci.yml:123`). `AGENTS.md:99` says Manifest.Tests takes about 35 s, but it took 47.2 s in CI run `40000531511`. An agent that follows the rule could add the project to the unit list and turn CI red. Correct this in the next bmad-project-context refresh, aligned with Story 4.14's live lane, then copy `AGENTS.md` to the other two entry points and run `scripts/check-agent-instructions-sync.sh`. The parent searched the ledger before appending and found no equivalent entry.
  status: resolved (2026-10-28)
  resolution: `AGENTS.md:100` limits direct test runs to ordinary projects, removes stale timings and distinguishes CI tiers; `AGENTS.md:102` documents isolated live execution and outer deadlines, and `AGENTS.md:103` supplies non-live Python checks and preflight prerequisites. Synced to both entry points and tracked in `spec-resolve-five-deferred-guidance-items.md`.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-12-compose-the-v1-live-test-topology.md`
  summary: The agent instructions' "zero module-specific code" policy does not exempt the Story 4.12 live-topology test composition.
  evidence: Low; from code review pass 4 (2026-10-24). `AGENTS.md:83` (byte-identical in `CLAUDE.md` and `.github/copilot-instructions.md`) says "Zero module-specific code in this repo. Enrolling a module is configuration only." The spec-required test AppHost composes named modules: `tests/Hexalith.McpCli.AppHost/Program.cs:82` and `:85` call `AddHexalithTenantsServer` and `AddHexalithPartiesServer`, `tests/Hexalith.McpCli.AppHost/TopologyConfiguration.cs:13` and `:16` list the three applications and checkouts, and `tests/Hexalith.McpCli.Integration.Tests/GatewaySmokeTests.cs:26` queries `ListTenantsQuery`. None of it branches per module. An agent following the rule could report the topology as a violation or refuse later live-topology work. Scope the rule to production `src/` and name the test topology as the exception in the same bmad-project-context refresh as the entry above; then copy `AGENTS.md` to the other two entry points and run `scripts/check-agent-instructions-sync.sh`. The parent searched the ledger before appending and found no equivalent entry.
  status: resolved (2026-10-28)
  resolution: `AGENTS.md:82` distinguishes production restrictions from the continuing test dependency allowlist; `AGENTS.md:83` permits the existing test-only composition and integration assertions while preserving generic runners and upstream ownership of module behavior. Synced to both entry points and tracked in `spec-resolve-five-deferred-guidance-items.md`.

## Deferred from: code review of spec-4-13-test-every-vector-against-live-gateway-semantics.md (2026-10-26)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-13-test-every-vector-against-live-gateway-semantics.md`
  summary: RID runtime DLL bytes are compared only when the deps-relative path already exists beside the host, so a flattened copy can skip the check.
  evidence: Unverified (`maybe-false`); medium if true. `tools/live-topology/live_plans.py:283` compares bytes only when `(host.parent / asset).is_file()`. The next loop checks non-RID `runtime` assets by file name. Settle by listing `runtimeTargets` in the built `tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.deps.json` and checking whether any of those DLLs exist beside the host under a flattened name with bytes that differ from the nupkg. Chunk A review. The ledger had no equivalent entry.

## Deferred from: implementation review of spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md (2026-10-26)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md`
  summary: Qualify the live lane on the actual hosted Ubuntu runner and resolve any namespace prerequisite restrictions.
  evidence: Originally unverified (maybe-false); medium if true. `tools/live-topology/ci.py:155` probes capability-bearing user/PID/network/mount namespaces, and the upstream Aspire job uses ubuntu-latest. Hosted run `40377962105` proves bounded hosted-only namespace setup and the real re-probe succeed; attempt 2 of `40381146665` passes all 21 vectors and the independent smoke, as recorded in the source spec's 2026-10-27 review findings. Isolation and native namespace proofs remain required.
  status: resolved (2026-10-27) by the recorded hosted namespace and full-live evidence; new Builds-pin publication/hosted qualification is tracked separately below.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md`
  summary: Publish the newly qualified Builds revision and obtain hosted CI acceptance for the updated pinned caller.
  evidence: High integration blocker for the current pin. The former `35587cfd104c5750d8ec3c0716933f386d6a0232` revision was published and passed hosted run `40381146665`, attempt 2, as recorded in the source spec. Review patch P13 now moves `.github/workflows/ci.yml:18` and the gitlink to documentation-only child `857ef02dbb4bde1bd4e678546aa41e73fb7d68b1`. `_bmad-output/implementation-artifacts/evidence/story-4-14/review-patches-20261027/verification.json:5` records this new locally qualified, unpublished revision, 323 owner workflow assertions and complete passing local hooks. Its exact owner patch and local Git bundle are retained alongside the index. This implementation stage prohibits pushes and Git remote operations, so no hosted resolution or acceptance is claimed for the new pin.
  status: resolved (2026-10-28) by hosted run `40658496696` (HEAD `dbce3b1`, pin and gitlink `3d7f49a5430294da5bcd437cbdace85c62c42027`): `ci / aspire-tests` passed, and artifact `12803579896` records `fullLiveAccepted: true` with all 21 vectors and the smoke passed. `857ef02` was superseded by the published `3d7f49a` pin. Recorded by code review pass 3 of the source spec.

## Deferred from: code review of spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md (2026-10-27)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md`
  summary: The blocking hosted live lane is intermittent. A Dapr sidecar can lose its gRPC port to another process inside the private topology, and the fixture's liveness checks do not detect the dead sidecar before vectors run.
  evidence: High (verified occurrence, recurrence rate unknown).
    - Attempt 1 of hosted run `40381146665` (HEAD `f6fc9ae`) failed. Its `aspire-hook-evidence` artifact is `12681110107`, generation `5887d89d9f734931bd0391b432a64ff2`, and its runtime-diagnostics `command.stdout.txt` is for run `20261026T185945Z-d09a00de`.
    - In that run, the Parties sidecar logged `Failed to listen for gRPC server on TCP address :44173 with error: listen tcp :44173: bind: address already in use` and then `Dapr runtime stopped`. Port 44173 is inside Linux's default ephemeral range.
    - EventStore's `POST /v1.0/invoke/parties/method/process` then returned 500 (`DomainServiceException`), so `parties.create-party` failed with `gateway_error` 500 at `/invocation`.
    - Attempt 2 (artifact `12680213617`) passed all 21 vectors and the smoke.
    - The fixture (`tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:51`) passed resource liveness before the vector ran. The CI hooks failed the attempt correctly.
    - Possible directions, not yet decided:
      - prove each sidecar's health before vectors;
      - keep the private network namespace's `net.ipv4.ip_local_port_range` away from the ports the topology allocates;
      - assign fixed ports inside each private namespace.
    - Settle the rate by running the hosted lane repeatedly and grepping each artifact for `address already in use`.
    - The ledger had no equivalent entry.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md`
  summary: The agent instructions still say `HexalithEventStoreVersion` comes from the Builds props, but McpCli now pins it in `Directory.Build.props`.
  evidence: Low to medium.
    - `AGENTS.md:92` (byte-identical in `CLAUDE.md` and `.github/copilot-instructions.md`) says the compiled EventStore package is `HexalithEventStoreVersion` "in the Builds props".
    - `Directory.Build.props:4` now pins 3.127.0, while `references/Hexalith.Builds/Props/Directory.Packages.props:9` defaults to 3.128.0.
    - An agent that confirms members against the Builds value could use a 3.128.0-only API, which then fails to compile against the restored 3.127.0 package.
    - Fix in the next bmad-project-context refresh: point the line at `Directory.Build.props`, copy `AGENTS.md` to the other two entry points, and run `scripts/check-agent-instructions-sync.sh`.
    - The ledger had no equivalent entry.
  status: resolved (2026-10-28)
  resolution: `AGENTS.md:78`, `AGENTS.md:93`, and `AGENTS.md:99` identify root `Directory.Build.props` as the module-pin source before the central Builds import and require checking effective restored APIs. MSBuild confirms EventStore 3.128.3, Parties 1.5.1, and Tenants 5.10.0. Synced to both entry points and tracked in `spec-resolve-five-deferred-guidance-items.md`.

## Deferred from: code review pass 4 of spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md (2026-10-28)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md`
  summary: The agent instructions list outdated ModelContextProtocol and System.CommandLine versions.
  evidence: Low.
    - `AGENTS.md:78` (byte-identical in `CLAUDE.md` and `.github/copilot-instructions.md`) says "ModelContextProtocol 2.2.0, System.CommandLine 2.0.12".
    - `tools/dependency-policy.json:64-66` pins ModelContextProtocol 2.3.0 and System.CommandLine 2.0.14. The story 4.14 range moved System.CommandLine from 2.0.13 to 2.0.14.
    - An agent trusting the instructions can look up APIs or release notes for the wrong package versions.
    - Fix: correct the versions in `AGENTS.md`, or drop them in favor of the central catalog and policy. Then copy `AGENTS.md` to the other two entry points and run `scripts/check-agent-instructions-sync.sh`.
    - The ledger had no equivalent entry.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-14-make-the-live-semantic-lane-blocking-in-ci.md`
  summary: The generic-runner rule in the agent instructions does not cover the spec-required, module-specific source-build list in the CI hook.
  evidence: Low.
    - `AGENTS.md:83` (added by `3c3a0f2`) says "Keep the runners in `tools/live-topology/` generic; change module behavior upstream".
    - `tools/live-topology/ci.py:26-29` names EventStore, Tenants and Parties and carries the approved Tenants `SOURCE_EVENTSTORE` exception. Story 4.14 requires both: it builds "the three root source servers", and the exception was approved on 2026-10-28.
    - An agent or reviewer following the rule will flag or "fix" this required code, as pass-4 BH1 did.
    - Fix: state in `AGENTS.md` that the CI hook's root source-build list and its approved Tenants exception are test-only composition. Copy it to `CLAUDE.md` and `.github/copilot-instructions.md`, then run `scripts/check-agent-instructions-sync.sh`.
    - The ledger had no equivalent entry.

## Deferred from: code review of spec-4-15-publish-the-no-new-server-rule.md (2026-10-28)

- source_spec: `_bmad-output/implementation-artifacts/spec-4-15-publish-the-no-new-server-rule.md`
  summary: Four of the six approved migration inventories pin source revisions that do not exist in their upstream repositories, so nobody else can check those inventories against source.
  evidence: Medium; pre-existing from Stories 4.2–4.4.
    - `_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md:6` (`e2252f29a2dba2b64786ee483eb59fbceaadd387`), `chatbot-migration-inventory-v1.md:6` (`acc934599cf1efff36b0643eddc6a3cc4c2978d5`), `frontcomposer-migration-inventory-v1.md:6` (`81a440a8890a17edb39924bd0cf676eb6f6b5c25`) and `projects-migration-inventory-v1.md:6` (`3d256e632a7645bc2261e668ac7c74be81155f58`) all pin unpublished revisions.
    - GitHub returns HTTP 422 "No commit found" for each one, and the sibling clones under `/home/administrator/projects/hexalith/` lack the objects.
    - The objects exist only in this checkout's `references/Hexalith.{Folders,ChatBot,FrontComposer,Projects}` clones. They were McpCli gitlinks at `cad469e` (on `origin/main`), so published McpCli history also points at commits that do not exist on GitHub.
    - Parties `49373094` and Memories `f6b60d5a` are on upstream `main`.
    - Story 4.15's published plan (`Hexalith.AI.Tools/hexalith-mcpcli-migration-instructions.md:24`, `:38-42`) calls these "source-pinned" immutable snapshots.
    - Fix, for the inventory owners: either push the four objects to a preserved upstream ref, or publish versioned inventory revisions re-pinned to published source.
    - The ledger had no equivalent entry.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-15-publish-the-no-new-server-rule.md`
  summary: Hexalith.AI.Tools now pins a commitlint policy, but no CI job or commit hook enforces it.
  evidence: Medium; pre-existing gap in the owning repository.
    - AI.Tools `5be77fc` ships `commitlint.config.mjs`, `package.json` (`@commitlint/cli` and `config-conventional` 21.2.2) and `package-lock.json`.
    - Its tracked `.github/` has no workflows, and nothing installs a commit-msg hook.
    - The AI.Tools baseline (`references/Hexalith.AI.Tools/AGENTS.md:56`) names a hook and a blocking CI commitlint gate as its enforcement layers.
    - `references/Hexalith.Builds/.github/workflows/commitlint.yml:3-6` is the reusable gate for repositories that ship exactly these files. McpCli calls it from `.github/workflows/commitlint.yml`.
    - The only evidence the policy works is the one-time `_bmad-output/implementation-artifacts/evidence/story-4-15/parent-final/commitlint.json`. A dropped `extends`, an empty-rules regression or a non-conventional message would therefore reach AI.Tools `main` unchecked.
    - Fix upstream: add a pull-request/push caller of `Hexalith/Hexalith.Builds/.github/workflows/commitlint.yml@<pinned sha>` to AI.Tools.
    - The ledger had no equivalent entry.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-15-publish-the-no-new-server-rule.md`
  summary: Relative links in the root README break on nuget.org, which renders that README for both packages.
  evidence: Low; pre-existing pattern.
    - `src/Hexalith.McpCli/Hexalith.McpCli.csproj:14` and `:18`, and `src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj:5` and `:8`, pack `README.md` as `PackageReadmeFile`.
    - nuget.org cannot resolve relative links such as `_bmad-output/...` and `tools/...`.
    - Affected links: `README.md:46` (new in Story 4.15) and the existing `:130`, `:259`, `:261`, `:269`, `:276` and `:287`.
    - The Bootstrap section already uses absolute GitHub URLs.
    - Fix before Story 4.18 publishes: make every repository link absolute (`https://github.com/Hexalith/Hexalith.McpCli/blob/main/...`), or pin them to a revision.
    - The ledger had no equivalent entry.

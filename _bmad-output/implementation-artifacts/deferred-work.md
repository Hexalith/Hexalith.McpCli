# Deferred Work

## Deferred from: code review of spec-1-1-declare-a-module-and-its-operations.md (2026-09-23)

- **The `KebabCase` helper cannot be shared with the `netstandard2.0` analyzer.** `src/Hexalith.McpCli.Abstractions/KebabCase.cs:17` uses `ArgumentException.ThrowIfNullOrWhiteSpace` and range slicing (`[..^n]`). The architecture requires one helper shared by the Catalog and the analyzer. The analyzer is `netstandard2.0`, and the Abstractions package is `net10.0` only. Story 1.7 must choose between linked source and multi-targeting, and add a `netstandard2.0` compile check so the naming rule cannot fork.
- **Bootstrap releases remain possible after paired releases start.** `scripts/release-preflight.sh:9` accepts `bootstrap` unconditionally, and nothing checks whether `Hexalith.McpCli` has already been published. That cannot happen yet because `paired` always fails. The paired-release story must make bootstrap fail once the tool package exists, or it could split the AD-17 single version line.
- **StyleCop header rule vs practice.** The Code style row in the architecture spine requires a StyleCop header. No new `.cs` file has one, and sibling Tenants does not use them either. Either amend the spine or adopt headers (with `StyleCop.Analyzers`) across the repo.
- **No rule for non-canonical names.** `HexalithModuleAttribute.Name` and the `Name` override on `HexalithCommand` and `HexalithQuery` are taken as written. A value such as `Inventory`, `tls_config` or `a.b` would break the `<module>.<operation>` split or produce non-canonical Operation Names. The PRD and architecture define no diagnostic category for this. Stories 1.4 and 1.5 should add one, possibly with an `IsCanonical` helper next to `KebabCase`.
- **No diagnostic for a type with both operation attributes.** A type can carry both `[HexalithCommand]` and `[HexalithQuery]`, which makes its kind (write or read) ambiguous and would defeat the read-only filter. No Catalog diagnostic category covers this case. Stories 1.4 and 1.5 should add one.

## Deferred from: code review of spec-1-3-derive-the-operation-s-json-schema.md (2026-09-25)

- **The CLAUDE.md dependency allowlist omits `JsonSchema.Net`.** `src/Hexalith.McpCli.Core/Hexalith.McpCli.Core.csproj` references `JsonSchema.Net`, which is outside the transitive closure of `Hexalith.EventStore.Contracts`. The story spec and the architecture spine approve it as a pinned Stack package, so update the shared `AGENTS.md` baseline (and its synced copies) to name it.
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
  evidence: `OperationExecutor` copies response IDs without the ULID validation required by PRD addendum §G; this belongs to concurrent executor work.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-warn-on-missing-operation-descriptions-at-build-time.md`
  summary: Malformed Gateway paging metadata can enter a successful query result.
  evidence: `OperationExecutor` copies paging values without checking a nonempty cursor or numeric constraints; this belongs to concurrent executor work.
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

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: Cancellation during MCP host startup is mapped through the generic startup-error path.
  evidence: Pre-existing: cancellation while `host.RunAsync` is starting in `RunMcpHostAsync` falls into the generic catch and reports `internal_error` exit 2 instead of a clean exit; clean stdio lifecycle cancellation belongs to Epic 3.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: Offline CLI actions can still depend on unrelated application configuration loaded by the default Host builder.
  evidence: Pre-existing: `HostFactory.CreateHost` uses `Host.CreateApplicationBuilder()`, which loads content-root `appsettings*.json` and every environment variable (including `EVENTSTORE_ADMIN_*`) into an unused `IConfiguration`; consider `Host.CreateEmptyApplicationBuilder` in a separate hosting hardening change.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-inspect-effective-session-settings.md`
  summary: Verb-action I/O failures are reported as configuration errors with raw exception text.
  evidence: Pre-existing: `CliRunner.RunAsync`'s outer catch maps any `IOException`/`UnauthorizedAccessException`/`InvalidDataException` thrown by a verb action (for example an output-file write) to `configuration_invalid` with the raw exception message, which can include absolute home paths; the baseline catch wrapped the action too. Address with Story 2.9 stable failure documents.

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

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: System.CommandLine parse errors on config verbs print help to stdout, echo the unmatched token on stderr, and exit 1 instead of a single error document with exit 2.
  evidence: Reproduced on the Release build: `config set dev tenant a b` prints the `set` help on stdout and `Unrecognized command or argument 'b'.` on stderr with exit 1. Pre-existing default ParseErrorAction; it breaks the epic's "stdout holds only the result document, exit 2 when no result" rule and can echo a mistyped positional secret. The same parse failure also bypasses the `config profile add` operator-flag refusal, so these cases never report `invalid_arguments` with exit 2: `add dev --url U --tenant` (no value; help on stdout, exit 1; second-pass acceptance audit), `add dev --url U --allow-tenant-override yes` (`Unrecognized command or argument 'yes'.`, help on stdout, exit 1) and `add dev --url U --tenant=` (`Required argument missing`, exit 1), the last two reproduced on the Release build in the fifth-pass review. Owned by Story 2.11 (predictable output and exit codes); include every case above in that story's tests.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: Pre-existing process-level CLI tests redirect HOME/USERPROFILE, which Windows ignores, so running them on Windows mutates the developer's real `~/.eventstore/mcpcli.json`.
  evidence: `Environment.GetFolderPath(SpecialFolder.UserProfile)` uses the known-folder API on Windows, not USERPROFILE; `ExecutableStoresAtPrefixedTokenVerbatimAsync` (ConfigCommandTests) adds a `dev` profile to the real store there. Story 2.3's new process tests skip on Windows; the pre-existing one predates this story.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, third pass (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: A stored `tenant` or `actor` cannot be cleared. `config set dev tenant ""` fails validation, and the only way back is `config profile add`, which replaces the whole record and drops the token, format and allowed extensions.
  evidence: `ProfileStore.Set` assigns the value as given, and `ValidateProfile` rejects a blank tenant or actor. Story 2.3's frozen Never forbids a field-unset verb, and the new `add` operator-flag error sends users to `config set`. By design for v1, but no story owns the clearing path yet.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, fifth pass (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: Profile-management success documents serialize `"activeProfile": null`, although addendum §G and the Epic 2 output rule require absent optional members to be omitted.
  evidence: `McpCliJson.Result` has no `WhenWritingNull`. Story 2.2's matrix specifies `use --clear → null`, and `ConfigCommandTests.ListUseAndClearMaskEveryTokenAsync`, `RemoveClearsOnlyItsOwnSelectionAsync`, and `AddAcceptsOtherGlobalOptionsAsync` assert `JsonValueKind.Null`; the last test also pins the exact result members `name` and `activeProfile`. The planning artifacts need to agree on null or omission before any code changes; Story 2.11 (predictable output) is the natural owner.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, sixth pass (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: `config profile add`, `config set`, and `config profile remove` with an unwritable `--output` path report `configuration_invalid` (exit 2) even though `mcpcli.json` was already changed.
  evidence: `CliRunner` commits through `ProfileStore` before `CliOutput.WriteAsync` writes the success document to `settings.Output`; a missing output directory raises `DirectoryNotFoundException`, which `RunManagementAsync` maps to `configuration_invalid`. Pre-existing at baseline `6fe785e`; a retried `remove` then fails as "does not exist". Found in the sixth-pass review of Story 2.3; Story 2.11 (predictable output and exit codes) is the natural owner.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md, ninth pass (2026-09-30)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: Profile names and allowed-extension keys accept a trailing newline, because the validation regexes end in `$`, which in .NET also matches before a final `\n`.
  evidence: `ProfileStore.ProfileNamePattern` (`^[a-zA-Z0-9_-]{1,64}$`, `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:298`) and `ExtensionValidator.KeyPattern` (`src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:68`) have no `RegexOptions` and end in `$`. The ninth-pass blind-hunter reproduced this on the Release build: `config profile add $'dev\n' --url …` exits 0 and stores a separate `"dev\n"` profile. `config set $'dev\n' allowedExtensions $'task-id\n'` stores `["task-id\n"]`, and `task-id,task-id\n` passes the case-insensitive duplicate check. This is pre-existing: the name rule comes from Story 2.2, and `KeyPattern` is shared with command-extension execution, which Story 2.3's Never excludes. Fix: anchor with `\z` and add newline rows to the Core and CLI invalid-input theories.

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

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: The README documents no error codes, so a script that branches on `error.code` has no documented contract.
  evidence: `README.md` never mentions `invalid_arguments`, `configuration_invalid`, or the exit codes of any verb. Story 2.3 made a missing positional argument `invalid_arguments` and a supplied but invalid name, field or value `configuration_invalid`, both exit 2; these rules appear only in the spec and tests. Pre-existing: no verb's error codes were documented at baseline `6fe785e`. Story 2.11 owns the exit-code and addendum §G error-document contract. This entry is related to the eleventh-pass documentation entry above.

## Deferred from: code review of spec-2-3-update-and-remove-profiles-safely.md (2026-10-01)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-update-and-remove-profiles-safely.md`
  summary: A token can be stored in a profile only by passing it as `--token` on the command line, so the secret ends up in shell history and, while the process runs, in `/proc/<pid>/cmdline`.
  evidence: `config profile add` builds the record from parsed flags only (`new ConnectionProfile(input.Url, input.Token, input.Format)`, `src/Hexalith.McpCli/Cli/CliRunner.cs:356`). It ignores `EVENTSTORE_TOKEN` (pinned by `AddIgnoresEnvironmentOperatorSettingsAsync`), response files are disabled (`CliRunner.cs:67`), and `@`-prefixed values are stored verbatim, so there is no stdin, file or prompt source. The README says `add` stores `--token` and "never environment values", but does not mention the argv exposure or that the token is kept as plaintext in `mcpcli.json`, protected only by mode 0600 or the ACL. Pre-existing: this is the Story 2.2 / AD-14 `add` input rule at baseline `6fe785e`. A secret-safe input such as `--token -` or a prompt adds public surface and needs an owning settings story. Found by the final-HEAD blind-hunter review of Story 2.3; no owning story yet.

## Deferred from: code review of spec-2-4-browse-the-catalog-from-the-cli.md (2026-10-01)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-browse-the-catalog-from-the-cli.md`
  summary: An empty `--format table` list prints the header followed by a blank row, which a line-oriented script reads as an empty record.
  evidence: `CliOutput.FormatTable` (`src/Hexalith.McpCli/Cli/CliOutput.cs:66-69`) returns `header + Environment.NewLine + string.Join(...)` and `WriteAsync` then writes it with a trailing newline, so `operations marked-empty --format table` (or a `--kind` filter with no matches) prints `NAME\tKIND\tDESCRIPTION`, then an empty line. Pre-existing: the baseline `edc459e` used the same concatenation, and Story 2.4's frozen intent preserves existing rows; `DiscoveryCommandTests.TablesPreserveModuleOperationAndEmptyRowsAsync` now pins `header + NewLine + NewLine`. Suggested owner: Story 2.11 (table rendering AC). Fix: append the separator only when rows exist and update that assertion.

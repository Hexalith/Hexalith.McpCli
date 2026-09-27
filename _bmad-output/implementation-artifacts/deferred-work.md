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
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Integral floating-point paging accepted by JSON Schema is rendered as an invalid CLI integer.
  evidence: Medium; both validator versions accept pageSize 1.0; run_loopback.py _call_args uses str(value), yielding --page-size 1.0. Story 4.11 should normalize accepted integral numeric values or settle an explicit representation rule.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance paging comparisons equate booleans with integers.
  evidence: Medium; both validator versions accept expectedGateway.body.paging.pageSize true for envelope.pageSize 1 because validate.py _check_step uses Python dictionary equality. Distinguish JSON boolean and number types before downstream request-consistency acceptance.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance cursor limits count Unicode code points while Core counts UTF-16 units.
  evidence: Medium; both validator versions accept 3000 emoji, while OperationExecutor.ValidateQueryArguments rejects their 6000 UTF-16 units. Align the pre-existing schema/runtime limit before downstream compatibility acceptance.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance extension inputs omit fixed runtime restrictions.
  evidence: Medium; both validator versions accept 33 matching extensions. ExtensionValidator also checks key grammar, 100-character keys, 1000-character values, forbidden content and 4096 total UTF-8 bytes; these restrictions are absent from the existing contract tooling independently of the deployment allowlist.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Expected Gateway fields can contradict absent optional envelope inputs.
  evidence: Medium; both validator versions accept invented expected extensions with no supplied extensions and expected paging with no supplied paging. Core maps these fields directly from the missing inputs; extend the existing presence-only consistency checks before downstream acceptance.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance expected requests can contain known fields belonging to the other operation kind.
  evidence: Medium; both validator versions accept idempotencyKey in a query expectedGateway.body although query request construction has no such field. Preserve open Module data while checking incompatible known request fields before downstream compatibility acceptance.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md`
  summary: Conformance routing inputs omit unconditional Gateway identifier syntax and length restrictions.
  evidence: Medium; both validator versions accept entityId / in the envelope and expected request, while RoutingResolver.IsAggregateId rejects it. Apply common routing constraints independently of Module payload identifier kinds before downstream compatibility acceptance.

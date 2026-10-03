---
title: 'Protect Command Identity and Extensions'
type: 'feature'
created: '2026-10-02'
status: 'in-progress'
baseline_commit: '1554a84d792a0178a342d62367259999fd45e0b9'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Caller-controlled identity fields or extensions can violate session policy. Raw idempotency fields can wrongly block a valid caller key; lowercase ULID aggregates can address different EventStore streams.

**Approach:** Enforce Payload ownership and extension policy in Core, validate rebuilt Payload before accessor or submission, and require canonical uppercase ULID aggregate and marked identifier text.

## Boundaries & Constraints

**Always:** Resolve Tenant from fixed Module, permitted per-call value, or session; Actor only from session. Present mapped Tenant/Actor members must be JSON strings ordinally equal to resolved values; otherwise fail at escaped member pointers. Fill omitted/matching members. Generate one message ULID, reuse it for omitted correlation, and overwrite raw correlation. A supplied ULID idempotency key overwrites any raw mapped value; without a key, reject non-null raw values at `/idempotencyKey`, remove raw null, and require the key for non-nullable or serializer-required members, including required nullable. Validate a copy without mapped envelope fields, then rebuilt Payload, before computed `ICommandContract.AggregateId` access. Commands require object roots; allowed nested nulls survive. Reject lowercase ULID aggregates, marked identifiers, and caller correlation and idempotency keys per the user decisions; accepted values pass unchanged. Allow only Profile-approved extension keys case-insensitively, within pinned Gateway sanitizer and request-validator grammar, injection, count, length, and UTF-8 limits. Refusals make zero Gateway calls; successes make one.

**Never:** Read Tenant or Actor from Payload as an authority; generate an idempotency key; apply envelope identity or extension fields to Queries; add module-specific code or dependencies; edit `references/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Owned identity | Omitted or matching declared Tenant/Actor, raw malformed correlation, supplied valid key over malformed idempotency | Resolved values replace mapped fields; computed getter sees rebuilt Payload | Conflict, null, or non-string Tenant/Actor fails at mapped pointer |
| No key | Optional raw null or absent key; non-null raw key; required nullable key | Raw null removed; optional member omitted | Non-null raw or required member fails at `/idempotencyKey` |
| Payload shape | Null/non-object Command root; valid nested null; ordinary invalid/unknown member | Nested null survives when Schema permits; ordinary constraints still apply | Invalid root at `/`, Schema violations with pointers |
| Identifiers | Canonical and lowercase ULID aggregate argument/accessor/marked member | Canonical passes unchanged | Lowercase rejected before Gateway; entity ID still follows Gateway syntax |
| Extensions | Allowed mixed-case key; unsafe/oversize/count/UTF-8 boundary | Safe values pass unchanged | Refuse at `/extensions` or escaped key pointer |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — prefill, ownership, fill, final validation, accessor, single submission; fix supplied-key overwrite.
- `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs` — marked/typed ULID pattern; preserve envelope-required removal and nested nullability.
- `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs` — allowlist, pointers, sanitizer; add Gateway request-validator dangerous characters.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs`, `OperationDescriptor.cs`, `AggregateIdAccessors.cs` — reuse required-key metadata, mapped members, late accessor.
- `src/Hexalith.McpCli.Core/McpCliCoreServiceCollectionExtensions.cs`, `src/Hexalith.McpCli/Hosting/HostFactory.cs` — retain one Gateway client, host-only bearer handler.
- `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs`, `SchemaTests.cs`, `QueryValidationTests.cs`, `tests/Hexalith.McpCli.Cli.Tests/QueryPagingCommandTests.cs` — acceptance and prior lowercase expectations.
- `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/ExtensionMetadataSanitizer.cs`, `SubmitCommandRequestValidator.cs` — read-only pinned rules.

## Tasks & Acceptance

**Execution:**
- [x] `tests/fixtures/Catalog.Routing.Contracts/RequiredNullableIdempotencyCommand.cs` and `ComputedEnvelopeCommand.cs` — add missing edge-case contracts.
- [x] `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs` — cover raw ownership, omitted filled required members, malformed overwritten fields, no-key cases, root/nested null, all extension boundaries, and zero/one Gateway calls.
- [x] `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — allow supplied-key overwrite and check aggregate ULID canonical form separately from envelope ULIDs; keep validation ordering.
- [x] `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs` and `tests/Hexalith.McpCli.Core.Tests/SchemaTests.cs` — require canonical uppercase marked/typed ULIDs and pin the advertised Schema.
- [x] `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs` — reject Gateway dangerous characters; test escaped-key and boundaries in executor tests.
- [x] `tests/Hexalith.McpCli.Core.Tests/QueryValidationTests.cs` and `tests/Hexalith.McpCli.Cli.Tests/QueryPagingCommandTests.cs` — flip the prior lowercase pass-through expectations while preserving valid entity and Tenant boundaries.
- [x] `README.md` — document identity ownership, idempotency, allowlist, and canonical ULIDs.

**Acceptance Criteria:**
- Given a declared identity mapping and session, when a Command runs, then trusted values reach one Gateway request or precise validation fails before submission.
- Given allowed extensions, when a Command supplies them, then only Gateway-compatible keys and values reach one request.
- Given a noncanonical ULID aggregate or marked identifier, when either head calls Core, then validation fails before submission.

### Review Findings

Code review 2026-10-03 of `1554a84..a343378`; layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor (none failed). Verification Gap traced every behavioral change to a test that fails on its smallest regression.

- [x] [Review][Patch] Lowercase caller correlation or idempotency ULIDs pass the envelope check, then fail at a payload pointer the caller never wrote — medium (blind-hunter+edge-case-hunter+verification-gap+acceptance-auditor). `SchemaDeriver.IsSupportedRoleType` lets Correlation and IdempotencyKey bind to CLR `Ulid`/`Ulid?` members (`SchemaDeriver.cs:196-197`). Those members now get the uppercase-only `UlidPattern` (`SchemaDeriver.cs:18`, `:301-304`). The executor still accepts lowercase envelope values through `Ulid.TryParse` (`OperationExecutor.cs:150`, `:155`), and `Fill` writes them unchanged (`:192-193`). Final validation (`:197`) then rejects them at `/Correlation` or `/Idempotency`, not at `/correlationId` or `/idempotencyKey`. Before this change the same value succeeded, and it still succeeds for `string` members. Three layers reproduced this against the built Core assembly; no test or fixture declares a `Ulid`-typed role member. Same root cause: the Gateway treats the idempotency key as an opaque ordinal string (`SubmitCommandRequestValidator.cs:93-97`), so `01arz…` and `01ARZ…` are different deduplication keys and a retry that changes the casing can submit twice (pre-existing since Story 2.7). Options: (1) canonicalize accepted envelope ULIDs with `parsed.ToString()` before filling, submitting and echoing; (2) reject noncanonical envelope ULIDs at `/correlationId` and `/idempotencyKey`, which renegotiates the frozen "`Ulid.TryParse`" wording; (3) canonicalize only the text filled into `Ulid`-typed role members; (4) defer. Resolved by user decision 2026-10-03: option 2. Canonicalizing would contradict Story 2.7's "accept caller values unchanged" rule, and rejection matches the Story 2.6 aggregate decision. The executor now checks both envelope values with `IsCanonicalUlid` at `/correlationId` and `/idempotencyKey`; `IsUlid` was removed; README and the frozen Always clause updated. [src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:150]
- [x] [Review][Patch] README understates where uppercase ULID text is required — low (acceptance-auditor+blind-hunter). "ULID aggregate identifiers and marked payload identifiers must use canonical uppercase text" can be read as covering marked identifiers in String-kind modules, which stay nonempty strings. It also omits that every CLR `Ulid`-typed payload member requires uppercase in every module, including nested collection and dictionary elements (`SchemaDeriver.cs:301`, `SchemaTests` `/Ids/0`, `/ByName/a`, `/Optional/0`). Envelope correlation and idempotency casing is now stated at `README.md:67`. [README.md:73]
- [x] [Review][Patch] README does not say a payload correlation member is replaced — low (blind-hunter). The story documents raw Tenant, Actor and idempotency handling, but not that a mapped correlation member is always overwritten by `--correlation-id` or the generated message ID (`OperationExecutor.cs:148`, `:192`), while a raw idempotency value is refused in the same situation. Add one sentence to the identity-ownership text. [README.md:67]
- [x] [Review][Patch] The reserved key literal appears twice, and the test cannot tell which check fired — low (blind-hunter). `"actor:globalAdmin"` is written at `ExtensionValidator.cs:40` and `:72`. `ReservedExtensionMakesZeroCallsAsync` asserts only the pointer, so deleting the "reserved" branch silently turns the message into "The extension key is invalid." Use one constant and assert the reserved message. [src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:40; tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:484]
- [x] [Review][Patch] The lowercase-ULID ledger entry this story resolves is not marked resolved — low (blind-hunter). The ledger records resolutions with a `status: resolved in Story …` line (`deferred-work.md:96`), but the Story 2.6 entry Story 2.8 owns has none, so a later ledger sweep would treat it as open. [_bmad-output/implementation-artifacts/deferred-work.md:267]

**Rejected**

- false — The extension snapshot copy can throw on a duplicate or null key (edge-case-hunter): both heads bind real `Dictionary` instances that cannot hold either, and the same copy already existed at submission before this change. Only a deliberately broken custom `IReadOnlyDictionary` reaches it, and it then fails loudly as `internal_error`.
- false — A lowercase-ULID contract `Example` now fails catalog build (edge-case-hunter): such an example violates the advertised Schema and would fail at call time, so `invalid_example` is the intended consequence. No enrolled or referenced Contracts package has one.
- false — Overwriting a supplied key over a valid raw ULID is unpinned (blind-hunter): the old code refused any non-matching raw key, so `SuppliedKeyFillsRequiredNullableMemberAsync` (malformed `"bad"`) fails on a revert. The coupled computed-accessor rows name no missed defect.
- false — Spec `done` versus sprint `review` (blind-hunter): the sprint entry moves only when this review closes, the same path Story 2.7 took (`954a426`).
- false — An oversized extension map produces an unbounded error document (blind-hunter): at most three violations per entry the caller sent, so the error grows linearly with the caller's own input.
- false — The README presents configurable Gateway limits as fixed (blind-hunter): it states the CLI's local limits, which epic-2-context.md fixes. They are the strictest combination of the pinned sanitizer defaults and the request validator, and a stricter Gateway reports its own `gateway_error`.
- false — Verification skipped the other test projects and the Release solution build (blind-hunter): no Abstractions, Analyzers, Manifest or ConformanceHost source uses the ULID pattern or the routing fixture, and no repository file outside the new negative tests contains lowercase ULID text.
- low — Existing profile files holding `actor:globalAdmin` or a newline-terminated key become unreadable (edge-case-hunter+acceptance-auditor+blind-hunter): there is no release (no tags; nothing ships before Epic 4), so only local development files could hold one, and read-time tolerance adds new branches.
- low — A lowercase ULID query constant passes catalog validation but fails every call (edge-case-hunter+blind-hunter): no module declares one, `--aggregate-id` overrides it, and the fix needs a shared canonical helper plus a new catalog check.
- low — An allowlisted `traceparent` or `tracestate` is replaced by the Gateway (edge-case-hunter): an operator must allowlist the key, the overwrite is the Gateway's own trace propagation (`SubmitCommandExtensions.cs:32-39`), and a reserved list is a new guard.
- low — AC3's "either head" is tested only through CLI `query` (acceptance-auditor+blind-hunter): the MCP head passes the aggregate argument to the same Core executor; an MCP protocol fixture adds machinery without a distinct branch, as triage item Blind 7 already concluded.
- Rejected because the fix would edit the spec (acceptance-auditor): AC2's "only Gateway-compatible keys" overstates local enforcement for colon keys, which require a Gateway-side trusted-extension policy. The frozen Always clause asks only for the sanitizer and validator rules, and the README documents the policy requirement.
- Rejected because the fix would edit the spec (blind-hunter): the Code Map lists planned files that were not touched and omits fixture and test files that were.

Code review 2026-10-03 (third pass) of the full range `1554a84..64e363b`, excluding this spec and `sprint-status.yaml`; layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor (none failed). Verification Gap found no gaps. Items the earlier passes already settled are carried, not reopened.

- [x] [Review][Patch] Tests pin only all-lowercase text as noncanonical, so a weaker canonical check would pass the suite — low (blind-hunter). The pinned ByteAether.Ulid 1.4.1 `Ulid.TryParse` accepts `…FAO` (→ `…FA0`), `…FAI`/`…FAL` (→ `…FA1`), `…FAU` (→ `…FFZ`), `81ARZ…` (→ `01ARZ…`) and mixed case (verified by probe). `IsCanonicalUlid`'s round-trip rejects all of them, but every negative row uses `01arz3ndektsv4rrffq69g5fav`, so a `value == value.ToUpperInvariant() && Ulid.TryParse(...)` regression would let `81ARZ…` or `…FAO` reach a different stream. Add alias, overflow, and mixed-case rows to both theories. [tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:306; tests/Hexalith.McpCli.Core.Tests/QueryValidationTests.cs:189]
- [x] [Review][Patch] The ledger resolution line misdescribes which tests assert rejection — low (edge-case-hunter+blind-hunter). It says "the prior lowercase pass-through tests now assert rejection", but `ValidIdentifierBoundariesArePreservedAsync` and `EntityAndTenantBoundaryValuesArePreservedAsync` now use uppercase `ItemId` and still assert pass-through. Rejection is pinned by new rows and tests (`InvalidUlidAggregateArgumentsUseEnvelopePathAsync`, `LowercaseAggregateUlidIsRejectedBeforeGatewayAsync`, `LowercaseAggregateUlidMakesZeroCallsAsync`). The line also omits that the rule now also covers caller correlation and idempotency keys. [_bmad-output/implementation-artifacts/deferred-work.md:270]
- [x] [Review][Patch] The new Story 2.8 ledger entry has no `file:line` anchor, and its summary reads as an instruction — low (blind-hunter). Other entries state the defect and cite `path:line`. [_bmad-output/implementation-artifacts/deferred-work.md:285]
- [x] [Review][Patch] README claims every CLR `Ulid`-typed payload member is constrained, but fields are not — low (edge-case-hunter). `SchemaDeriver.Transform` applies the pattern only inside `if (clrProperty is not null)`, and `clrProperty` is `AttributeProvider as PropertyInfo`, so a `[JsonInclude]` `Ulid` field exports `{}`. No enrolled, referenced, or fixture contract declares one, and the code gap alone would be rejected as low. The README sentence is new, though, so narrow it to properties. [README.md:73]
- [x] [Review][Patch] README omits that a non-nullable idempotency member also requires `--idempotency-key` — low (acceptance-auditor). `CatalogBuilder` sets `idempotencyRequired` for `IsRequired || !IsSetNullable` (`CatalogBuilder.cs:233-234`), so `EnvelopeItemCommand`'s positional `string Idempotency` needs a key. The README names only the "required … even if nullable" case. Mention non-nullable members and `describe`'s `envelope.idempotencyKeyRequired`. [README.md:67]
- [x] [Review][Patch] README puts command identifier rules in the query paragraph and never says MCP `send_command` takes the same extensions — low (blind-hunter). The paragraph opening "Queries accept `--entity-id`" now carries canonical-ULID rules that also apply to command payloads and envelopes. The extension paragraph shows only CLI syntax, although `send_command` binds an `extensions` object through the same Core validation. [README.md:73; README.md:75]
- [x] [Review][Patch] README leaves out extension rules operators will hit — low (blind-hunter). `config set … allowedExtensions` splits on `,` without trimming (`ProfileStore.cs:157`), so `"task-id, trace-id"` is refused, and an empty value clears the list. Each colon-separated key segment must also start and end with a letter or digit. [README.md:75]
- [x] [Review][Patch] `send --help` and `SendCommandArguments` docs do not state the canonical uppercase ULID rule — low (blind-hunter). `--aggregate-id`, `--correlation-id`, and `--idempotency-key` have no `Description` (`CliRunner.cs:151-153`), unlike `--payload` and `--extension`. The record's XML docs still say only "ULID". [src/Hexalith.McpCli/Cli/CliRunner.cs:151; src/Hexalith.McpCli.Core/Execution/SendCommandArguments.cs:8]
- [x] [Review][Defer] Planning documents still state the pre-renegotiation `Ulid.TryParse` acceptance rule — low (acceptance-auditor). `prd.md:103`, `prd.md:348`, `epics.md:711`, and `epic-2-context.md` say identifiers are validated with `Ulid.TryParse`, but Core now also requires canonical uppercase text (Spec Change Log 2026-10-03). [_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md:103] — deferred: the fix edits other planning specs; recorded in `deferred-work.md` for a correct-course or epic-context regeneration before Story 2.9.
- [x] [Review][Defer] Marked String-kind payload identifiers may be empty, contrary to the epic's "nonempty string" rule, and README now documents that — low (acceptance-auditor). `SchemaDeriver` adds no `minLength` for them (`SchemaDeriver.cs:301-310`). [README.md:73] — deferred: pre-existing, and already tracked as open sprint action item `epic-1-retro-item-5-string-identifier-contract` (Story 2.6 deferred it there too); no new ledger entry. The README describes current behavior accurately until that decision lands.

**Rejected (third pass)**

- low — A lowercase ULID query constant passes catalog validation but fails every call (edge-case-hunter): carried rejection from both earlier passes. No module declares one, `--aggregate-id` overrides it, and the fix needs a new catalog check.
- low — Existing profile files holding a reserved or newline-terminated key become unreadable, and `config set` cannot repair them (edge-case-hunter): carried rejection. Nothing has been released, so only local development files could hold such a key, and read-time tolerance adds new branches.
- low — The MCP tool and `describe` envelope do not show the canonical ULID rule (blind-hunter): the refusal message states the rule exactly, ULID generators emit canonical text, and exposing the rule adds public discovery surface.
- false — `ExtensionValidator` docs are stale and the reserved check is duplicated (blind-hunter): every added rule is a Gateway rule, which the summary already covers. Both checks read one constant. The explicit branch gives a distinct message, and `IsValidKey`'s clause serves `ProfileStore` and `SettingsResolver`.
- false — CLI exact duplicates and case-only duplicates get different error codes (blind-hunter): case collisions are `validation_failed` in both heads through Core, so making the CLI case-insensitive would break head parity. An exact duplicate cannot be bound into the CLI dictionary at all, so it is a separate binding error.
- low — Identifier test gaps across module kinds (blind-hunter): `IdentifiersFollowDeclaredKind(String)` already pins the top-level CLR `Ulid` pattern to the pinned uppercase constant. String-kind aggregate checks are gated on `IdentifierKind.Ulid` and have no ULID-shape logic to regress. The query accessor `/ItemId` uses the same validator as the command row in `LowercaseAggregateUlidMakesZeroCallsAsync`.
- low — `ChangingExtensions` detects only a second enumeration (blind-hunter): the executor copies once through the `Dictionary` constructor. Catching a hypothetical indexer re-read means rewriting the test double, and the `Interlocked`/`Volatile` calls cause no harm.
- false — `RequiredNullableIdempotencyAppearsInDiscovery` does not pin removal from the advertised `required` array (blind-hunter): prefill validates `operation.Schema` with envelope members removed, so `SuppliedKeyFillsRequiredNullableMemberAsync` fails if `Idempotency` stays required.
- false — `SuppliedKeyFillsRequiredNullableMemberAsync` reuses `CorrelationId` as the idempotency key (blind-hunter): the file already uses `CorrelationId` as its shared valid ULID for keys (`OperationExecutorTests.cs:141`, `:362`), and the assertion names `Idempotency`.

Code review 2026-10-03 (post-completion pass) of the full range `1554a84..0f09132`, excluding this spec and `sprint-status.yaml`; layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor (none failed). Verification Gap found no gaps. Items the earlier passes already settled are carried, not reopened, except where new evidence is noted.

- [ ] [Review][Patch] Two new ledger entries use a bare `source_spec` — low (acceptance-auditor+blind-hunter). The final-build entries write `spec-2-8-protect-command-identity-and-extensions.md`; every other ledger entry, including this story's two earlier ones, uses the full `_bmad-output/implementation-artifacts/` path, so a ledger sweep that resolves `source_spec` as a path misses the spec. [_bmad-output/implementation-artifacts/deferred-work.md:295]
- [ ] [Review][Patch] The third-pass ledger entry omits the agent entry points and architecture spine that still prescribe `Ulid.TryParse` — low (blind-hunter). `AGENTS.md:85`, `CLAUDE.md:85`, and `.github/copilot-instructions.md:85` say "validate with `Ulid.TryParse`"; `ARCHITECTURE-SPINE.md:106` (AD-8 aggregate validation) and `:200` (identifier convention) prescribe `Ulid.TryParse(value, provider: null, out _)`. Every agent session loads the entry points, so a later story can reintroduce a parse-only check that accepts lowercase. The entry also cites `epic-2-context.md` by quotation instead of `:32` and `:34`. Extend the entry's evidence; the document edits stay deferred because they change agent-context files and other specs. [_bmad-output/implementation-artifacts/deferred-work.md:290]
- [ ] [Review][Patch] The sanitizer-coverage ledger entries name only two of the reachable untested patterns — low (blind-hunter). No test exercises `--\s*$` (`SqlPattern`), `|(` (`LdapPattern`), or `on\w+\s*=` (`XssPattern`) alone, so deleting any of them also passes the suite. `';\s*DROP…`, `&(`, and `<\s*iframe|object|embed` can no longer fire alone because the dangerous-character check (values) and `KeyPattern` (keys) refuse those characters first. [_bmad-output/implementation-artifacts/deferred-work.md:296]
- [ ] [Review][Patch] The root-pointer rows cannot catch a wrong pointer — low (acceptance-auditor). `InvalidPayloadFailsBeforeGatewayAsync` asserts `Path.StartsWith("/")`, which every JSON Pointer satisfies, so the `null` and `[]` rows the Matrix audit cites for "Invalid root at `/`" would also pass with a violation at `/ItemId`. `PayloadValidator.cs:50-53` returns exactly `/` today. Assert exact paths. [tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:217]
- [ ] [Review][Patch] An MCP `extensions: {}` reaches the Gateway as an empty object, while the CLI omits it — low (blind-hunter). The snapshot keeps an empty map; CLI `send` passes `null` when no `--extension` is given (`CliRunner.cs:192`), and the Gateway client omits only null members (`EventStoreGatewayClient.cs:22`, `WhenWritingNull`). The same call therefore puts `"extensions":{}` on the wire only from MCP. Normalize an empty snapshot to `null` in Core and assert it. [src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:172]
- [ ] [Review][Patch] A test summary says a final newline fails the Gateway key grammar, but the pinned Gateway accepts it — low (edge-case-hunter). The pinned sanitizer's `KeyPattern` ends with `$` and its control check permits `\n` (`ExtensionMetadataSanitizer.cs:109`, `:118`), and `SubmitCommandRequestValidator` has no key grammar, so the Gateway accepts `task-id\n`; only the local `\z` anchor refuses it. Say that the local rule is stricter. [tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:454]
- [ ] [Review][Patch] README gives extension key and value limits in characters, but both are counted in UTF-16 code units — low (blind-hunter). `value.Length > 1_000` counts UTF-16 units, as the pinned Gateway does, and the same README says "UTF-16 code units" for `--cursor`. A 600-emoji value (1,200 units) is refused although README allows 1,000 characters. [README.md:77]
- [x] [Review][Defer] A ULID-kind query whose aggregate constant is not canonical ULID text is advertised as callable but always fails — medium (verification-gap+edge-case-hunter). `CatalogBuilder` checks the constant only with `RoutingResolver.IsAggregateId`. `ListItemsQuery` declares `AggregateId = "routing-list"` in the ULID-kind routing fixture, and `CatalogTests.cs:143` pins `AggregateIdRequired` false. Yet every call without `--aggregate-id` fails at `/aggregateId` (`OperationExecutor.cs:210-215`), and the caller cannot pass the constant instead. This new evidence widens the carried "lowercase query constant" rejection, which assumed no declaration existed. [src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:193] — deferred: pre-existing since Story 2.5; needs a decision on whether Identifier Kind governs query constants (exempt them, or refuse them at catalog build) before Epic 4 declares module queries.
- [x] [Review][Defer] Profile names accept a trailing newline — low (blind-hunter). `ProfileNamePattern` ends with `$`, which .NET matches before a final `\n`, so `dev\n` passes `config profile add` and profile load (`ProfileStore.cs:63`, `:241`). This story fixed the same defect in `ExtensionValidator.KeyPattern`. [src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:298] — deferred: pre-existing since Story 2.2 and outside this story's extension scope.
- [x] [Review][Defer] The conformance vector schema does not mirror this story's new extension rules — low (blind-hunter). `schema.json` requires only string values, so a vector can approve a dangerous-character value, the reserved key, or case-only duplicate keys that Core now refuses. [tools/conformance-vectors/v1/schema.json:64] — deferred: already tracked (`deferred-work.md:109`, `:138`, "omit fixed runtime restrictions"); no new ledger entry.

**Rejected (post-completion pass)**

- low — The MCP binding keeps the last of two exact-duplicate `extensions` JSON keys (blind-hunter): MCP clients serialize objects and practically never emit duplicate keys, and the surviving value is fully validated. The binding predates this story. Refusing duplicates means changing MCP-wide serializer options, which also changes duplicate handling for payloads.
- low — A lowercase aggregate ULID gets the generic aggregate refusal message (blind-hunter): CLI help, README, and the argument docs state the canonical rule, and ULID generators emit uppercase. A dedicated message needs a new branch in the aggregate check.
- low — CLI `--extension` parsing and CLI `send` lowercase identifiers have no CLI-level tests (blind-hunter): the parser is unchanged since `de67938`, and Core tests pin every rule the CLI forwards to. The earlier Blind 6 and Blind 7 decisions on head-level fixtures apply.
- false — README repeats the payload tenant rule in the identifier paragraph (blind-hunter): that sentence is the only statement covering query payload tenant members, because the executor fills and checks the tenant binding for both kinds. The tenant paragraph's new text covers commands only, so removing either sentence loses a rule.
- low — Stale reserved or newline-terminated allowlist keys make an existing profile file unreadable (edge-case-hunter): carried rejection from every earlier pass. Nothing has shipped.
- false — A custom dictionary with duplicate or null keys becomes `internal_error` (edge-case-hunter): carried rejection. Neither head binds such a dictionary.

## Implementation Notes

- The executor retains its prefill and final-schema pipeline. A supplied key now overwrites raw mapped idempotency data; absent-key non-null data still fails before submission.
- Aggregate ULIDs use a canonical-text check separate from envelope ULID parsing. The advertised identifier Schema now permits uppercase Crockford text only.
- Extension validation now includes the pinned Gateway request validator's dangerous-character rule. Synthetic contracts exercise serializer-required nullable keys and a getter that needs envelope-filled required members; their discovery snapshots were updated.
- The diff audit added missing-Actor, malformed raw-field, required-member, and discovery coverage. No production dependency or `references/` file changed.
- Review fixes reject newline-terminated, case-colliding, and reserved extension keys. The executor validates and submits one extension snapshot; docs explain Profile setup and Gateway policy for namespaced keys. Accepted-limit and nested-ULID tests now check the submitted data and rejection paths.

## Spec Change Log

- 2026-10-03: The user renegotiated the frozen envelope ULID rule during code review. Caller correlation and idempotency keys must now be canonical uppercase ULIDs, like aggregate and marked identifiers, instead of any text `Ulid.TryParse` accepts. Accepted values still pass unchanged, so Story 2.7's rule holds. The Always clause now reflects the decision.

## Review Triage Log

- Blind 1 — medium, patch: `ExtensionValidator.KeyPattern` ends with `$`, which .NET can match before a final newline; `IsValidKey` otherwise accepts such a key. Use an absolute end anchor and cover the key.
- Blind 2 — medium, patch: `CommandsController.BuildTrustedExtensions` writes into an ordinal-ignore-case dictionary, so distinct submitted keys differing only by case silently collapse. Reject them before the Gateway call.
- Blind 3 — medium, patch: `CommandsController` ignores `actor:globalAdmin` case-insensitively, while the current validator and allowlist accept it. Reject the reserved key locally and during Profile key validation.
- Blind 4 — low, patch: the new README extension paragraph does not explain that colon-delimited keys require exactly one Gateway trusted-extension policy to claim and accept them; otherwise the Gateway rejects the request.
- Blind 5 — low, patch: README names the allowlist and extensions without showing the existing `config set PROFILE allowedExtensions ...` and repeatable `send --extension key=value` syntax.
- Blind 6 — low, reject: no single CLI test reads a selected Profile and submits an allowed extension, but `SettingsResolver`, the host's `EnvelopeContext`, Core validation, and CLI submission are tested at their existing seams. A new HTTP/Profile integration fixture is more than a direct correction for this low-risk coverage gap.
- Blind 7 — low, reject: no new MCP protocol test includes extensions, but `McpToolHandlers.SendCommand` passes the bound dictionary unchanged to the same tested executor. A protocol fixture adds machinery without a distinct policy branch.
- Blind 8 — low, patch: accepted extension-limit cases assert one call but not that the copied request retains every key and value; capture and compare the submitted dictionary.
- Blind 9 — low, patch: the Schema pattern also constrains nested CLR `Ulid` members in String-kind modules; existing `UlidElementsAreConstrained` pins the pattern and positive values but not lowercase rejection on nested paths.
- Edge 1 — medium, patch: `SendCommandArguments.Extensions` is an `IReadOnlyDictionary` that can wrap a mutable dictionary; a concurrent mutation after validation can put an unchecked value into the later request copy. Validate and submit the same local snapshot.
- Edge 2 — medium, patch: the same validation-then-copy window can violate the claimed Gateway-compatible extension guarantee; it shares Edge 1's snapshot fix.
- Patch closure — all patch findings above were fixed and the full Core, CLI, and MCP verification commands passed after the changes.

Review resumption 2026-10-03 of the full diff through the final README and reserved-key fixes; Blind Hunter, Edge Case Hunter, and Verification Gap reviewed it. Verification Gap found no gaps. Each new finding follows, in reviewer order.

- Blind resumption 1 — low, carried rejection: a lowercase ULID query constant is discoverable but fails at execution; the earlier triage row for this same catalog location remains accurate. No enrolled module declares one, an explicit aggregate can override it, and a catalog rule needs a new shared canonical check.
- Blind resumption 2 — low, patch: the README claimed all String-kind marked members must be nonempty, although `SchemaDeriver` adds no such constraint to non-aggregate members. The sentence now states the actual schema rule; aggregate Gateway validation remains separate.
- Blind resumption 3 — low, defer: `ExtensionValidator` reports an excessive count and still sorts and visits the entire map, using O(n log n) work and proportional violations. This behavior predates Story 2.8; record a bounded early-return improvement in the deferred ledger.
- Blind resumption 4 — low, reject: an oversized key appears in its error pointer, but the response grows only linearly with caller input. The unusually large key is already rejected, and changing pointer behavior adds a special branch for a case unlikely in normal use.
- Blind resumption 5 — false, carried rejection: a deliberately malformed custom dictionary with a null key can throw during the snapshot copy, but neither CLI nor MCP binds one; both use real dictionaries, and the preexisting request copy already had the same failure for a custom caller.
- Blind resumption 6 — false, reject: no fixture combines CLR `Ulid` role members with lowercase envelope input, but `IsCanonicalUlid` rejects at the envelope pointers before payload filling for either role type; the schema tests separately pin the typed pattern. No divergent behavior was shown.
- Blind resumption 7 — low, carried rejection: the CLI/MCP HTTP parity fixture still omits extensions. The earlier Blind 7 decision applies because both heads feed the same tested Core executor, and the protocol fixture would add machinery without a separate policy branch.
- Blind resumption 8 — low, carried rejection: no single test loads a selected Profile and sends an extension. The earlier Blind 6 decision applies; Profile storage, settings resolution, host context, and submission are covered at their existing seams.
- Blind resumption 9 — false, reject: the Core negative tests omit a syntactically valid injection key, but `ProfileStoreTests` exercises `javascript:x` through the same `ExtensionValidator.IsValidKey` called during execution. The claimed untested check is already covered.
- Blind resumption 10 — false, reject: no new positive test sends tab, newline, or carriage return in an extension value, but `HasForbiddenControl` explicitly permits all three and the pinned sanitizer permits them; no rejection path was identified.
- Blind resumption 11 — false, reject: the changed CLI boundary test uses an uppercase aggregate while entity validation still uses unchanged Gateway syntax and accepts lowercase letters. The missing extra positive row does not indicate changed behavior.
- Blind resumption 12 — false, carried rejection: a different valid raw ULID would test the same overwrite branch as the malformed raw value in `SuppliedKeyFillsRequiredNullableMemberAsync`; the earlier triage row already explains why reverting the fix fails that test.
- Edge resumption 1 — false, carried rejection: the custom null-key dictionary is the same claim as Blind resumption 5 and the earlier edge-case triage row. It is unreachable through either head and was possible in the previous request-copy path.


Final build review 2026-10-03: Blind Hunter, Edge Case Hunter, and Verification Gap reviewed the full baseline diff. Edge Case Hunter returned no findings; Verification Gap found no gaps. Blind Hunter's ten findings were individually triaged:

- Final Blind 1 — low, patch: `CliRunner.CreateQuery` still has no `--aggregate-id` description, and `RunQueryArguments.AggregateId` omits the canonical text rule. Ordinary query callers use the same changed validation rule as send callers. Add the same scoped help and XML description; no behavior or public arguments change.
- Final Blind 2 — low, patch: successful extension tests exercise only unnamespaced keys, leaving the new reserved-key exclusion without a positive ordinary namespace example. Add a mixed-case namespaced key to the existing successful-extension test and assert unchanged submission through the same setup.
- Final Blind 3 — low, reject: all-zero and maximum canonical ULIDs have no explicit positive execution rows, but the helper has no representation-specific branch and uses the same parse/ordinal round-trip for every value. Ordinary generated identifiers are already accepted and preserved. Exercising these unusual synthetic extremes would expand execution-test setup without correcting a demonstrated rejection.
- Final Blind 4 — low, defer: `UNION SELECT` has no independent extension test, so deletion of the pre-existing SQL sanitizer pattern would evade the current negative examples. `HasInjection` and `SqlPattern` were unchanged by this story; record a focused baseline security-coverage improvement.
- Final Blind 5 — low, defer: `)(` has no independent extension test, so deletion of the pre-existing LDAP sanitizer pattern would evade the current negative examples. `HasInjection` and `LdapPattern` were unchanged by this story; record a focused baseline security-coverage improvement.
- Final Blind 6 — low, patch: the extension boundary test accepts any `/extensions` prefix and would miss a wrong diagnostic location for count, UTF-8 total, key, or value limits. Tighten the existing expected pointers to `/extensions` or the exact member pointer.
- Final Blind 7 — low, reject: the Implementation Notes retain the old explanation of separate envelope parsing although both envelope and aggregate checks now call `IsCanonicalUlid`. The smallest fix edits this build's spec, which the review workflow rejects; execution and public docs are correct.
- Final Blind 8 — low, carried defer: oversized extension maps still sort and scan after count failure, exactly as Blind resumption 3 describes. The deferred ledger already tracks the bounded early-return improvement; no duplicate entry or guard is added.
- Final Blind 9 — low, carried rejection: a lowercase query constant can still pass catalog construction and fail ordinary execution, exactly as Blind resumption 1 describes. No enrolled module declares one; an explicit aggregate overrides it, and adding a catalog validation rule is more than a direct correction for this low-frequency case.
- Final Blind 10 — low, carried defer: planning artifacts still contain pre-renegotiation ULID acceptance wording. The third-pass Defer finding and ledger entry already assign reconciliation before Story 2.9; preserve that decision and the user's existing entry.

## Verification

**Commands:**
- `dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Debug --no-restore -m:1` — passed, zero warnings/errors.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Debug/net10.0/Hexalith.McpCli.Core.Tests.dll` — 488 total, zero failures/errors, two Windows-only ACL skips, zero not run (third-pass patch closure).
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1` — passed, zero warnings/errors.
- `dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll` — 339 total, zero failures/errors/skips, zero not run (third-pass patch closure).
- `dotnet build tests/Hexalith.McpCli.Mcp.Tests/Hexalith.McpCli.Mcp.Tests.csproj --configuration Debug --no-restore -m:1` — passed, zero warnings/errors.
- `dotnet tests/Hexalith.McpCli.Mcp.Tests/bin/Debug/net10.0/Hexalith.McpCli.Mcp.Tests.dll` — six total, zero failures.
- `git diff --check` — passed.
- `npx --no -- commitlint --edit /tmp/mcpcli-story-2-8-commit-bDEkvf.txt` — passed for `feat(command): protect command identity and extensions`.

Third-pass patch closure 2026-10-03: all eight Patch findings are fixed. The existing theories now include 18 additional negative cases for mixed-case, O/I/L/U aliases, and overflowing ULID text; each asserts the envelope pointer and zero Gateway calls. README, rendered CLI help, argument XML documentation, and both ledger corrections reflect current behavior. The two third-pass deferred findings remain tracked. The frozen intent and original baseline were preserved.

Additional checks:
- `dotnet src/Hexalith.McpCli/bin/Debug/net10.0/Hexalith.McpCli.dll send --help` — passed; all three identifier descriptions state the canonical uppercase rule, with aggregate identifiers scoped to ULID-kind modules.
- Byte-level check of the four changed C# files — passed; all line endings are CRLF.

Matrix audit: every covering test below ran in the passing full Core or CLI suite; the only skips were the two unrelated Windows ACL tests.

| Matrix row | Passing coverage |
|---|---|
| Owned identity | `ComputedAccessorSeesTrustedEnvelopeAndNestedNullAsync`, `RawIdentityConflictMakesZeroCallsAsync`, `MissingTrustedActorMakesZeroCallsAsync`, `CommandFillsMappedEnvelopeAndEscapedPropertyAsync` |
| No key | `OptionalIdempotencyIsAbsentWithoutCallerKeyAsync`, `RequiredNullableIdempotencyNeedsCallerKeyAsync`, `PayloadOnlyIdempotencyKeyFailsBeforeGatewayAsync`, `SuppliedKeyFillsRequiredNullableMemberAsync` |
| Payload shape | `InvalidPayloadFailsBeforeGatewayAsync`, `ComputedAccessorSeesTrustedEnvelopeAndNestedNullAsync` |
| Identifiers | `InvalidEnvelopeUlidFailsBeforeGatewayAsync`, `InvalidUlidAggregateArgumentsUseEnvelopePathAsync`, `LowercaseAggregateUlidMakesZeroCallsAsync`, `UlidSchemaRejectsLowercaseMarkedAndTypedValues`, `ValidIdentifierBoundariesArePreservedAsync`, `LowercaseAggregateUlidIsRejectedBeforeGatewayAsync` |
| Extensions | `MixedCaseApprovedExtensionReachesGatewayOnceAsync`, `DangerousExtensionValuesMakeZeroCallsAsync`, `UnsafeExtensionKeyUsesEscapedPointerAsync`, `ExtensionBoundariesMakeExpectedGatewayCallsAsync`, `MutableExtensionsCannotChangeAfterValidationAsync` |

Final build review patch closure 2026-10-03: Final Blind 1, 2, and 6 are fixed. Query aggregate help and XML docs match send; the existing successful extension test also preserves `Trace:Task-ID`; count/byte failures now assert `/extensions` and key/value failures assert their exact member pointer. The final Core, CLI, and MCP Debug builds each passed with zero warnings/errors. Full suites passed: Core 488 total (two Windows-only ACL skips, zero not run), CLI 339 total, MCP six total; all reported zero failures/errors. The two newly deferred sanitizer-coverage improvements and existing deferrals remain in the ledger.

- `dotnet src/Hexalith.McpCli/bin/Debug/net10.0/Hexalith.McpCli.dll query --help` — passed; the aggregate description matches send and scopes canonical ULIDs to ULID-kind modules.
- Final `send --help`, `git diff --check`, and CRLF checks — passed after the review patches. The original commitlint evidence above belongs to the earlier committed implementation; completion-commit validation is recorded below.

Completion commit validation: `npx --no -- commitlint --edit /tmp/mcpcli-story-2-8-completion-nnem95_2.txt` — passed (exit 0), using the repository-pinned `@commitlint/cli` 21.2.2 and the exact full message `fix(command): complete identity and extension review fixes`.

---
title: "Reconciliation review: PRD -> Architecture Spine"
reviewed: ARCHITECTURE-SPINE.md (status draft, 2026-09-22)
against: prds/prd-mcpcli-2026-09-21/prd.md (status final, updated 2026-09-22) and addendum.md
created: 2026-09-22
---

# Reconciliation review: PRD -> Architecture Spine

Method: every PRD requirement (FR-1..FR-22, NFR-1..NFR-8), the §4 guardrails, §7 public surface, §8 scope, §9 success metrics, §10 open questions, and the §11 assumption index were checked one by one against the spine's ADs, conventions, stack, structural seed, capability map, deferred list, and open questions. The addendum (§B, §E) was used where the PRD delegates a rule to it. Two reference facts were verified in `references/Hexalith.EventStore`: the EventStore host launch profile does listen on `http://localhost:8080`, and `FakeEventStoreGatewayClient`, `AspireTopologyFixtureBase`, and `MaskToken` exist as the spine names them.

Findings list only what did not land, landed wrongly, was renamed silently, or was resolved silently. Each has the PRD cite, the spine cite, and a one-line fix.

## Verdict

The spine is a faithful build substrate for roughly 80% of the PRD, and its one declared amendment (AD-8) is flagged for a PRD update. It should not go to epics as-is: two FR-16 consistency checks are dropped (one of them silently rewrites a Payload tenant), the v1 done-definition (Tenants and Parties end to end, FR-20) is not covered by the harness, the MCP head's option handling contradicts FR-13/FR-19, and the AD-8 amendment is under-scoped relative to what it actually changes in §3, §4, FR-3 and FR-7.

## Critical

### C-1. FR-16 disagreement rules dropped: tenant mismatch is silently overwritten, aggregate-id mismatch is silently ignored

- PRD: FR-16 consequences: "An explicit argument that disagrees with the Payload is `validation_failed`"; "A Payload tenant value that differs from the Envelope Tenant is `validation_failed`; otherwise the properties named by `tenantProperty` ... are overwritten". Addendum §E `aggregateId` row repeats the first rule. §4 Tenant guardrail: envelope-only.
- Spine: AD-9 orders the executor as "resolve aggregate identifier as explicit argument, else `AggregateIdPath` value" (no comparison when both exist) and "overwrite envelope-filled properties from the Envelope" (no comparison before the overwrite). AD-1 says every FR-13..FR-19 rule is implemented once in Core, so no head will add the check either.
- Effect if built as written: a Payload carrying tenant B submitted under envelope tenant A is rewritten to A and accepted; an explicit `--aggregate-id` that contradicts the Payload wins without an error.
- Fix: add two steps to AD-9, after Payload validation: "if an explicit aggregate identifier and an `AggregateIdPath` value both exist and differ, `validation_failed`; if a `tenantProperty` value exists and differs from the resolved Tenant, `validation_failed`; only then overwrite".

## High

### H-1. FR-20 done-definition (Tenants and Parties end to end) has no harness: Parties is absent from the test topology and from the deferred list

- PRD: FR-20 "v1 is done when the tool is released and Tenants and Parties are covered end to end"; §8 "v1 is done when ... Tenants and Parties are covered end to end"; SM-4 "identical Catalog data and results for every Operation".
- Spine: AD-16 composes "the EventStore platform ... plus the Tenants domain service". Deferred: "Composition of Projects and Folders in the test AppHost. Added when each becomes Gateway-ready". Parties appears in neither; the structural seed says "Aspire topology: EventStore platform + Tenants".
- Fix: either add the Parties domain service to AD-16's topology (and to the Tenants-composition open question, which then covers both), or state explicitly that Parties end-to-end coverage is verified outside this harness and how, and flag the FR-20 wording for a PRD update.

### H-2. "The MCP head has no flags" contradicts FR-13 and FR-19 for the `mcp` verb

- PRD: FR-13 "Every verb accepts `--url`, `--token`, `--tenant`, `--profile`, `--format json|table`, `--output <file>`, and `--read-only`"; FR-19 "When the tool starts with `--read-only` or `EVENTSTORE_READ_ONLY`"; FR-12 lists `mcp` as a verb; §4 Read-only "enforced in the executor"; UJ-1 wires the stdio server into Claude Code, where startup flags are the normal way to select a profile.
- Spine: AD-13 "The MCP head has no flags; it resolves from environment and Profile at startup and from tool arguments per call". Nothing says the `mcp` verb's global options feed the MCP head's `ResolvedSettings`.
- Fix: reword AD-13 to "the MCP adapter parses no argv; the `mcp` verb resolves the FR-13 global options (flag, environment, Profile, default) into `ResolvedSettings` once at startup and passes them to `AddMcpCliMcpServer()`; per-call tool arguments override Tenant, correlation, and idempotency only".

### H-3. AD-4's manifest recipe cannot emit a Gateway-not-ready Module, so FR-20's "zero Operations plus a startup diagnostic" cannot happen

- PRD: FR-20 "A referenced Module that is not yet Gateway-ready appears in `list_modules` with zero Operations and a startup diagnostic"; FR-3 "an undecorated assembly contributes nothing and produces no diagnostic" (so "not Gateway-ready" must mean marker present, no decorated Operations). FR-6's category list has no category for it either (PRD-internal gap).
- Spine: AD-4 emits manifest entries "as `typeof(<first decorated type>).Assembly`"; a marker-only assembly has no decorated type to name, so it drops out of the manifest and never reaches `CatalogBuilder`. Conventions "categories per FR-6" cannot produce the diagnostic FR-20 asks for. Addendum §D notes `Hexalith.Folders.Contracts` today holds no command or query records at all, so this is the live case for Folders.
- Fix: AD-4 anchors the manifest entry on any public type of the marked assembly (or on the assembly identity through the marker attribute's declaring assembly) and adds a warning category `module_without_operations`; flag FR-6's category list for a PRD update.

### H-4. AD-8 amendment is under-scoped: it changes §3, §4, FR-3 and two further FR-7 prongs, but declares only "the name-based identifier heuristic"

- PRD: §3 "Identifier ... Identifiers are ULIDs"; §4 "Identifiers. ULIDs, validated with `Ulid.TryParse`"; FR-7 "An Identifier is a property whose type is a known identifier type, whose name ends in `Id`, or that the Decoration Package marks" and "A value-object identifier with a single string member serializes as that member"; FR-3 / §5.1 the Module marker carries "the Module Name and a one-line description".
- Spine: AD-8 marks identifiers only by `[HexalithIdentifier]` or by `aggregateIdProperty` under `IdentifierKind = Ulid`, which (a) drops the "known identifier type" prong, (b) drops the value-object single-member rule entirely (JsonSchemaExporter will render such a type as an object), (c) creates a class of non-ULID identifiers (Tenants `system`), contradicting §3 and §4 as written, and (d) adds a third member `IdentifierKind` to the Module marker (conventions row "Decoration Attributes"). Only (the name prong) is declared; the open question "PRD FR-7 amendment" names FR-7 only.
- Fix: widen AD-8's "Amends" to "PRD §3 Identifier, §4 Identifiers, FR-3 marker members, FR-7 all three prongs and the value-object rule", state what happens to a single-string-member value object (converter, or unsupported with a diagnostic), and list all four PRD locations in the open question.

## Medium

### M-1. Discovery result shapes and `submittable` reason are not in the call model, so FR-9 and SM-4 have no Core-owned record for them

- PRD: FR-9 `describe_operation` returns "description, kind, Schema, example, the Envelope arguments the caller may supply, and `submittable`, with a reason when it is false"; FR-19 "`submittable: false, reason: read_only`"; §7 makes "result shapes" part of the public Generic Tool contract; SM-4 requires identical Catalog data across heads.
- Spine: AD-5 owns only `CommandResult`, `QueryResult`, `OperationError`; AD-12 takes `OutputSchema` "from the AD-5 records", which do not include a module list, an operation list, or an operation description. AD-3's `OperationDescriptor` has `Submittable` but no reason, and `EnvelopeFilledProperties` is the inverse of "Envelope arguments the caller may supply".
- Fix: add `ModuleSummary`, `OperationSummary`, and `OperationDescription(..., Submittable, SubmittableReason?, AcceptedEnvelopeArguments)` to AD-5 as Core-owned discovery records that both heads render verbatim.

### M-2. "A Payload that is not JSON is one violation" cannot be produced by Core because the call model already carries a parsed `JsonElement`

- PRD: FR-11 "a Payload that is not JSON is one violation" under `validation_failed`; AD-1 (spine) "every rule in FR-13 to FR-19 is implemented once, in Core".
- Spine: AD-5 `OperationCall(OperationName, Payload: JsonElement, ...)` forces each head to parse text before calling Core, so the invalid-JSON violation is produced twice (once per head) or not at all.
- Fix: make `OperationCall.Payload` a raw string (or `ReadOnlyMemory<byte>`) parsed inside `OperationExecutor` with `McpCliJson.Payload`, so the parse error is one `validation_failed` violation from Core.

### M-3. `OperationError` has no member for the "up to three nearest Operation Names"

- PRD: FR-11 "Unknown Operation Name: `code: unknown_operation` and up to three nearest Operation Names".
- Spine: AD-9 computes them; AD-5 `OperationError(Code, OperationName?, Violations?, Gateway?)` has nowhere to put them.
- Fix: add `Suggestions?: IReadOnlyList<string>` to `OperationError` in AD-5.

### M-4. Two overlapping envelope records (`EnvelopeArguments` and `EnvelopeContext`) with no merge rule, and `UserId` introduced without a PRD home

- PRD: FR-13 one resolution order per option (per-call argument, flag, environment, Profile, default); §4 Identity in v1 "the audit trail says 'the tool', not the human"; user identity is the HTTP release (§8.2).
- Spine: AD-5 `EnvelopeArguments(Tenant?, AggregateId?, CorrelationId?, IdempotencyKey?, EntityId?, Paging?, Extensions?)` and AD-10 `EnvelopeContext(Tenant?, CorrelationId?, UserId?, Extensions?)` both carry Tenant, CorrelationId, Extensions; the sequence diagram passes both to the executor. Which wins for Tenant is not stated; `UserId` has no v1 source.
- Fix: collapse to one record (per-call arguments) plus `ResolvedSettings` (startup values), state that per-call wins per AD-13, and either drop `UserId` from v1 or mark it "reserved for the HTTP release, always null in v1".

### M-5. NFR-8 is claimed in `binds` but no AD, convention, or capability-map row implements the hollow-description lint

- PRD: NFR-8 "a lint rejects a description equal to the humanized type name (SM-C4)"; SM-C4.
- Spine: front matter binds NFR-8; the capability map omits NFR-8 (and NFR-3, which is at least covered by the determinism convention); the only mention is under Deferred, "the runtime lint in `describe --lint` covers it first", but no diagnostic category or lint rule for it is defined anywhere (FR-4's `describe --lint` covers undescribed properties only; AD-8 adds `unmarked_identifier`).
- Fix: add a `hollow_description` warning category to the diagnostics convention (startup warning, `describe --lint` exit 1, promoted by `--strict`) and a capability-map row for NFR-8.

### M-6. One shared version for both packages conflicts with §7's per-artifact breaking-change rules

- PRD: §7 "Renaming a Generic Tool, changing an argument, or changing the Operation Name form is a major version ... A Contracts Library builds unchanged across minor versions of the Decoration Package".
- Spine: AD-17 "Both packages share one version" under semantic-release. A major bump caused by a Generic Tool rename is then also a major bump of `Hexalith.McpCli.Abstractions` with no attribute change, and every Contracts Library sees a breaking-version signal it does not need.
- Fix: either state in AD-17 that the Decoration Package's semver is decoupled (separate `tagFormat`/release config, as Hexalith.Builds allows) or amend §7 to say the two artifacts version together and flag it for a PRD update.

### M-7. §4 "Zero module-specific code" and AD-15 versus AD-16: the test AppHost names and composes the Tenants domain service

- PRD: §4 "No type, branch, or configuration in this repository names a Module" and "Test projects may contain one synthetic sample Contracts Library, never referenced by the tool package"; §4 Dependency policy "Never an aggregate, projection, handler, client, or server project of any Module".
- Spine: AD-15 extends the ban to test projects ("never a Module ... server package"), while AD-16 composes "the Tenants domain service, the way `Hexalith.Tenants.AppHost` does" (which references the Tenants server project) in `tests/Hexalith.McpCli.AppHost`. The open question "Tenants composition" admits a package or source checkout as options, both of which AD-15 forbids. The test AppHost is also repository configuration that names a Module.
- Fix: AD-16 fixes the composition to a container image (the only option consistent with AD-15), and the spine states the test-topology exemption to §4 explicitly and flags §4 for a PRD update.

## Low

### L-1. PRD open questions and assumptions resolved silently

- OQ-7 (package identifiers, CLI command name): resolved by AD-17 (`Hexalith.McpCli.Abstractions`, `Hexalith.McpCli`, `ToolCommandName = hexalith`) without listing OQ-7 as closed.
- OQ-2 (module layout): resolved by the structural seed (flat) without mention; consistent with the repository's own `AGENTS.md`.
- OQ-4 (analyzer feasibility): AD-18 designs packaging and says "may ship before the analyzer exists", which is the PRD's fallback; not listed as resolved.
- NFR-7 assumption (harness choice): resolved by AD-16 (Aspire), which the PRD delegated; say so.
- FR-13 assumptions (JSON default, `EVENTSTORE_` prefix, tenant-required Queries): adopted by AD-13 and AD-9 without saying they are still PRD assumptions. The prefix does not collide with the admin CLI, which uses `EVENTSTORE_ADMIN_*` (verified).
- AD-13 URL default `http://localhost:8080` is tagged [ASSUMPTION], but the addendum §E delegates the default to the architecture and the EventStore host launch profile does use 8080 (verified); it can be promoted to a decision.
- Fix: add a short "PRD items resolved here" list under Open Questions naming OQ-2, OQ-4, OQ-7 and the assumptions adopted, so the PRD's §11 index can be updated in one pass.

### L-2. Error-code set extended without a PRD cross-reference

- PRD: FR-11 names `validation_failed` and `unknown_operation`; FR-19 `read_only`; FR-14 exit 2 lists gateway rejection, unsupported transport, startup failure without codes.
- Spine: conventions add `gateway_error`, `configuration_missing`, `unsupported_transport`. Additive and sensible, but §7 counts result shapes as public surface.
- Fix: note in the conventions row that the three codes extend FR-11 and flag FR-11 for the full list.

### L-3. `send_command` gains `Destructive = true`, not in the PRD annotation set

- PRD: FR-9 "`send_command` carries `readOnlyHint: false` and `idempotentHint: false`".
- Spine: AD-12 adds `Destructive = true`. Matches the MCP default, but it is an addition to the §7 Generic Tool contract.
- Fix: either drop it or add "destructiveHint: true" to FR-9 in the PRD update.

### L-4. `describe --lint` gains an `unmarked_identifier` warning; its exit-code and `--strict` behaviour are unstated

- PRD: FR-4 defines `describe --lint` as undescribed properties, exit 1 if any; FR-6 `--strict` promotes warnings to errors.
- Spine: AD-8 adds `unmarked_identifier` as a `describe --lint` warning only; unclear whether it triggers exit 1 or counts under `--strict` at startup.
- Fix: state that `unmarked_identifier` is a startup warning category (so `--strict` sees it) and contributes to `describe --lint` exit 1, and flag FR-4/FR-6 for the PRD update.

### L-5. Payload property casing is a public-contract decision the PRD never states

- PRD: FR-7 and addendum §E describe the Payload only as "validated against the Schema".
- Spine: AD-6 fixes `PropertyNamingPolicy = null` (PascalCase property names in the Schema and the Payload, `additionalProperties: false`), so an agent sending `partyId` gets a violation. Correct for the Gateway, but it belongs in the §7 surface.
- Fix: flag for the PRD update: "Payload property names are the CLR names verbatim".

### L-6. SM-4 "identical results" cannot be byte-identical for Commands

- PRD: SM-4 identical results for every Operation; §4 one generated message identifier per call.
- Spine: AD-5 "byte-identical for the same call" and AD-16 "compares both heads' documents for equality"; `CommandResult.MessageId` is generated per call and cannot be supplied (AD-9), so two Command submissions never match byte for byte.
- Fix: AD-16 states the comparison excludes generated identifiers (MessageId, generated IdempotencyKey, Gateway correlation id) for Commands and is full for Query documents and discovery output.

### L-7. "Tokens never appear in any output" and "MaskToken shows four characters" sit in one sentence

- PRD: FR-18 / NFR-5 "Tokens never appear on stdout or stderr, including in errors and verbose logs".
- Spine: conventions "Tokens never appear in any output; `MaskToken` shows four characters". The admin CLI's `config current` and `profile list` print the masked token; fine, but the two clauses read as a contradiction.
- Fix: "Tokens never appear in any output except as `MaskToken` output (four trailing characters) in `config current` and `config profile list`".

### L-8. Small PRD items with no spine home

- FR-18 `config tenant <profile> <tenant>`: `McpCliSettingsStore` exists, but the deferred `config` parity list names only `profile add|remove|list`, `use`, `current`.
- FR-12 `mcp --transport http` "with a message naming the release in which it arrives": the spine's Deferred entry gives the code only.
- FR-10 release-checklist item (Claude Code, Claude Desktop, VS Code smoke test): AD-17 has no release checklist.
- SM-6 (successful `send_command` within 15 minutes from the README alone): no README in the structural seed and no onboarding artifact.
- AD-9 carries a `[ADOPTED]` tag no other AD has and the spine does not define it.
- Fix: add `tenant` to the `config` list, the release message to Deferred, a release-checklist line to AD-17, `README.md` to the structural seed, and either define or drop `[ADOPTED]`.

## Deliberate amendments and whether they are flagged

| Amendment | Declared in spine | Flagged for PRD update | Note |
| --- | --- | --- | --- |
| Identifier recognition by marker instead of name (FR-7) | Yes, AD-8 "Amends PRD FR-7" | Yes, Open Questions "PRD FR-7 amendment" | Scope understated; see H-4 |
| Module marker gains `IdentifierKind` (FR-3, §5.1) | No (conventions row only) | No | Part of H-4 |
| Aspire chosen as harness (NFR-7 assumption) | Implicit in AD-16 | No | PRD delegated it; see L-1 |
| Test AppHost composes a Module's domain service (§4) | No | No | See M-7 |
| Error codes extended (FR-11) | No | No | See L-2 |
| `destructiveHint` added (FR-9) | No | No | See L-3 |
| Package ids and command name (OQ-7), flat layout (OQ-2) | Implicit in AD-17 and seed | No | See L-1 |

## What was checked and found consistent (no finding)

FR-1 kind mapping and empty-description handling (AD-3, AD-18, diagnostics convention); FR-2 per-field routing (conventions row); FR-5 generated manifest, untrimmed tool, ordinal sort (AD-4, AD-17, determinism); FR-6 startup-failure rule and `--strict` (diagnostics convention); FR-8 naming (conventions row); FR-9 five tools, four in Read-only, three-part descriptions, `readOnlyHint` values (AD-12); FR-10 stdio, stderr logging, no prompt (AD-12, AD-13); FR-14 exit codes (conventions row); FR-15 validate-all-then-refuse (AD-7, AD-9); FR-16 generated ULIDs, Routing Values in the Envelope, aggregate-less Query carried as OQ-3 (AD-9, identifier convention, Open Questions); FR-17 single gateway call, no retry, one `HttpClient` test, result members (AD-9, AD-11, AD-5); FR-18 shared `profiles.json` schema and separate `mcpcli.json` (AD-14); FR-19 executor-enforced refusal and list-tools omission (AD-9, AD-12); FR-21/FR-22 kept outside `src/` (capability map); NFR-1 benchmark, NFR-2 character-count test, NFR-4 channels and `LoggerMessage`, NFR-6 untrimmed cross-platform global tool (AD-12, AD-17, channels convention); §4 dependency policy, tenant envelope-only, identity-as-token-owner, idempotency, read-only-in-executor, no hosted infrastructure (AD-9, AD-10, AD-15, runtime view); §7 two packages, Decoration Package first (AD-17, AD-18); §8.2 out-of-scope list mirrored in Deferred; SM-C2 and SM-C3 (AD-12, AD-15); OQ-1 and OQ-3 carried forward explicitly.

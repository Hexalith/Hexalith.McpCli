---
title: "Reconciliation review: architecture spine vs brief, brief addendum, PRD addendum"
subject: _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md
sources:
  - _bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/brief.md
  - _bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/addendum.md
  - _bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md
  - _bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md (cross-checked where the spine cites an FR)
  - references/Hexalith.Builds/Props/Directory.Packages.props, references/Hexalith.EventStore, references/Hexalith.Tenants (pins and patterns verified)
reviewer: reconciliation reviewer (read-only)
date: 2026-09-22
verdict: not reconciled
---

# Reconciliation review

**Verdict.** The spine honors D1 to D6, the `serve` to `mcp` rename, the profile split, the ULID rule, the never-retry rule, and every §F deferral, but it breaks the "only EventStore client + Contracts" guardrail in its own test harness (AD-16 contradicts AD-15 and the brief), drops two executor consistency checks that back the tenant guardrail, and loses several quiet requirements (no Spectre.Console, the six environment variable names, the `mcp` verb's global flags, the Projects/Folders pins).

Method: each decision, constraint, guardrail, §B bullet, §E row, and §F item was located in the spine (AD, convention, stack, seed, deferred, or open question). Only items that did not land, landed wrongly, or landed ambiguously are listed. Pins were checked against `references/Hexalith.Builds/Props/Directory.Packages.props`; the AD-16 composition claim was checked against `references/Hexalith.Tenants/src/Hexalith.Tenants.AppHost/Program.cs`.

## Critical

### C1. AD-16 composes a Module server into the test topology, which every source forbids

- **Source.** Brief, Scope, "Guardrails that hold in every release": "The only Hexalith dependencies are the EventStore client package and the Contracts libraries being exposed." Brief, Scope, "Out of version one, and refused if proposed": "Any reference to an aggregate, projection, handler, or server-side project from another module." Brief addendum, "Constraints on every option", last bullet. PRD §4 Dependency policy: "Never an aggregate, projection, handler, client, or server project of any Module. Test projects may contain one synthetic sample Contracts Library, never referenced by the tool package." PRD §4 Zero module-specific code: "No type, branch, or configuration in this repository names a Module." PRD SM-C3.
- **Spine.** AD-16 Rule: "`tests/Hexalith.McpCli.AppHost` composes the EventStore platform through `Hexalith.EventStore.Aspire` plus the Tenants domain service, the way `Hexalith.Tenants.AppHost` does." Structural seed: `Hexalith.McpCli.AppHost/ # Aspire topology: EventStore platform + Tenants`. AD-15 Rule allows tests "the Aspire composition helpers needed to run the topology". Open Questions, "Tenants composition in the test AppHost": "from a package, a container image, or a source checkout".
- **Why it is wrong.** `Hexalith.Tenants.AppHost/Program.cs` composes Tenants with `builder.AddHexalithTenantsServer(...)` from `Hexalith.Tenants.Aspire` (a `ProjectReference` in its csproj), which adds the `Hexalith.Tenants` server project as an Aspire project resource. Doing it "the way Hexalith.Tenants.AppHost does" therefore means referencing `Hexalith.Tenants.Aspire` and the Tenants server: exactly the aggregate/server reference the brief refuses and AD-15's own last clause forbids. The "Aspire composition helpers" carve-out in AD-15 is the loophole that lets it in, and two of the three options in the open question (package, source checkout) are violations, not choices. The test AppHost is also repository configuration that names a Module.
- **Fix.** Rewrite AD-16 so the topology contains only the EventStore platform plus a domain service for `tests/Hexalith.McpCli.Sample.Contracts` (built in `tests/`), or a Tenants container image pulled by name with no Hexalith.Tenants package or project reference; strike "and the Aspire composition helpers needed to run the topology" from AD-15; restrict the open question to "container image or externally running EventStore".

## High

### H1. AD-9 drops the two disagreement checks that enforce "tenant from the envelope, never the payload"

- **Source.** Brief addendum, "Constraints on every option": "Tenant is always envelope-supplied (profile, flag, or forwarded header), never taken from the payload." PRD addendum §E, `aggregateId` row: "explicit value wins; disagreement with the Payload is a validation failure." PRD FR-16: "A Payload tenant value that differs from the Envelope Tenant is `validation_failed`; otherwise the properties named by `tenantProperty`, `correlationProperty`, and `idempotencyKeyProperty` are overwritten"; "An explicit argument that disagrees with the Payload is `validation_failed`."
- **Spine.** AD-9 Rule: "resolve aggregate identifier as explicit argument, else `AggregateIdPath` value" (a fallback chain, no comparison) and "overwrite envelope-filled properties from the Envelope" (a silent overwrite, no comparison). Neither disagreement is an error anywhere in the spine.
- **Fix.** Add two ordered steps to AD-9: "if an explicit aggregate identifier and the `AggregateIdPath` value both exist and differ, `validation_failed`; if the Payload's `tenantProperty` value exists and differs from the resolved Tenant, `validation_failed`; then overwrite."

### H2. AD-13 removes the global flags from the `mcp` verb

- **Source.** PRD addendum §B: "Transport switch is `hexalith mcp --transport stdio|http`." §E: "Global CLI options: `--url`, `--token`, `--tenant`, `--profile`, `--format json|table`, `--output <file>`, `--read-only`, `--strict`." PRD FR-12 lists `mcp` as a verb; FR-13: "Every verb accepts `--url`, `--token`, `--tenant`, `--profile`, `--format json|table`, `--output <file>`, and `--read-only`"; FR-19: "When the tool starts with `--read-only` or `EVENTSTORE_READ_ONLY` ... the MCP Server omits `send_command`."
- **Spine.** AD-13 Rule: "The MCP head has no flags; it resolves from environment and Profile at startup and from tool arguments per call." Read literally, `hexalith mcp --read-only --profile test` is unsupported and Read-only Mode for an MCP session is environment-only.
- **Fix.** Replace the sentence with: "the `mcp` verb accepts the global flags like every verb plus `--transport`; the MCP adapter itself never parses argv and receives `ResolvedSettings` from the composition root; tool arguments override per call."

### H3. Projects and Folders Contracts pins are missing from the Stack

- **Source.** Brief, Executive Summary and Scope: "Version one covers Tenants, Parties, Projects, and Folders." PRD FR-20: "The v1 tool references the Contracts Libraries of Tenants, Parties, Projects, and Folders by pinned package."
- **Spine.** AD-2 diagram names all four; the Stack table pins only `Hexalith.Tenants.Contracts 5.7.0` and `Hexalith.Parties.Contracts 1.1.1`. The catalog has `HexalithProjectsVersion 1.0.0` and `HexalithFoldersVersion 1.0.0` with `Hexalith.Projects.Contracts` and `Hexalith.Folders.Contracts` entries, so the omission is not a missing upstream pin.
- **Fix.** Add the two rows (1.0.0 each), or state in AD-15/FR-20's map row that they are referenced from day one and contribute nothing until decorated.

## Medium

### M1. "No Spectre.Console" is lost, and the spine introduces the one component that would attract it

- **Source.** PRD addendum §B: "Pinned packages: ... No Spectre.Console." Brief addendum, Conventions: "No Spectre.Console anywhere."
- **Spine.** No mention. Structural seed adds `Cli/ (... OutputWriter, TableFormatter)` and the Table output convention, with no rule on what the formatter may depend on.
- **Fix.** Add to AD-15 or the Table output convention: "no Spectre.Console or any console-UI package; `TableFormatter` is hand-written as in `Hexalith.EventStore.Admin.Cli`."

### M2. `ModelContextProtocol.AspNetCore 2.2.0` pin dropped from the Stack

- **Source.** PRD addendum §B: "Pinned packages: ModelContextProtocol 2.2.0, ModelContextProtocol.AspNetCore 2.2.0, System.CommandLine 2.0.12." Brief addendum D4 Option C (chosen): "One binary, both transports."
- **Spine.** Stack lists `ModelContextProtocol, ModelContextProtocol.Core 2.2.0` and `System.CommandLine 2.0.12`; AspNetCore is absent. Not referencing it in v1 is consistent with AD-1, but the pin that the HTTP release will use is now recorded nowhere in the architecture.
- **Fix.** Add a Stack row "ModelContextProtocol.AspNetCore 2.2.0 (HTTP release; not referenced in v1)".

### M3. The six environment variable names are replaced by a glob

- **Source.** PRD addendum §E: "Environment variables: `EVENTSTORE_URL`, `EVENTSTORE_TOKEN`, `EVENTSTORE_TENANT`, `EVENTSTORE_FORMAT`, `EVENTSTORE_READ_ONLY`, `EVENTSTORE_PROFILE`." No variable for `--strict` or `--output`. PRD FR-13: prefix `EVENTSTORE_` without `ADMIN`.
- **Spine.** AD-13 Rule: "environment variable (`EVENTSTORE_*`)". `ResolvedSettings` carries `Strict` and `Output`, inviting `EVENTSTORE_STRICT` and `EVENTSTORE_OUTPUT`; the glob also matches the admin tools' `EVENTSTORE_ADMIN_URL` / `EVENTSTORE_ADMIN_TOKEN` (see `Hexalith.EventStore.Admin.Cli/GlobalOptionsBinding.cs`), which this tool must not read.
- **Fix.** List the six names verbatim in AD-13 and state that `--strict` and `--output` are flag-only and `EVENTSTORE_ADMIN_*` is never read.

### M4. Two overlapping envelope records with no precedence between them

- **Source.** PRD addendum §E, `tenant` row: "per-call argument wins over flag"; resolution order "per-call argument, flag, environment variable, Profile, default".
- **Spine.** AD-5: `OperationCall(..., EnvelopeArguments)` with `EnvelopeArguments(Tenant?, ..., CorrelationId?, ..., Extensions?)`. AD-10: "the executor receives an `EnvelopeContext(Tenant?, CorrelationId?, UserId?, Extensions?)` value that the head builds per call from settings and arguments." Call pipeline: "OperationCall + EnvelopeContext". Tenant, CorrelationId, and Extensions exist in both; which one the executor reads, and whether AD-13 precedence is applied by the head or the executor, is undefined.
- **Fix.** Keep one record, or state: "`EnvelopeContext` is the head-resolved value (AD-13 precedence already applied); the executor reads only `EnvelopeContext`; `EnvelopeArguments` is input to that resolution."

### M5. AD-8's FR-7 amendment silently drops the value-object identifier rule

- **Source.** Brief guardrail: "Identifiers are ULIDs and are never validated as GUIDs." PRD FR-7: "An Identifier is a property whose type is a known identifier type, whose name ends in `Id`, or that the Decoration Package marks ... A value-object identifier with a single string member serializes as that member."
- **Spine.** AD-8 keeps only the "marked" branch and drops "known identifier type" and the single-member serialization clause. AD-6 then fixes `McpCliJson.Payload` with no converters and "No other `JsonSerializerOptions` is constructed", so a single-member identifier record is exported as an object schema and submitted as `{ "Value": "..." }`, which the Gateway's own writers would not produce.
- **Fix.** Extend AD-8: "a marked property whose CLR type is a single-string-member value object is schema'd and serialized as that string, through a converter registered on `McpCliJson.Payload`"; note the drop in the FR-7 open question so the PRD amendment is complete.

## Low

### L1. AD-9 reads as if a caller may supply the message identifier

- **Source.** Brief addendum constraint: "Message ID and idempotency key are generated by the tool per call; correlation ID optionally passed through." PRD §4 Idempotency; §E has no `messageId` argument.
- **Spine.** AD-9 Rule: "generate `MessageId` and `IdempotencyKey` as ULIDs unless supplied" while AD-9 Prevents: "a head or a caller supplying a message identifier."
- **Fix.** "generate `MessageId` always; use the caller's `IdempotencyKey` or generate one."

### L2. The five tool names and their fixed order are never stated

- **Source.** Brief addendum D3 Option B (chosen): `list_modules`, `list_operations`, `describe_operation`, `send_command`, `run_query`. PRD §7: the Generic Tool contract (five names) is public surface. PRD addendum §C: deterministic `tools/list` ordering keeps prompt caches warm.
- **Spine.** AD-12 mandates "the fixed set ... in a fixed order" without defining the order; only `describe_operation` (AD-3) and `send_command` (AD-12) are named.
- **Fix.** Name the five in AD-12 in discovery order: `list_modules`, `list_operations`, `describe_operation`, `run_query`, `send_command`.

### L3. `mcp --transport http` loses the message that names the release

- **Source.** PRD FR-12: "`mcp --transport http` exits 2 with a message naming the release in which it arrives." PRD addendum §B transport bullet.
- **Spine.** Deferred: "exits 2 with `unsupported_transport` until then." Code only, no message.
- **Fix.** Add to the error-codes convention: "`unsupported_transport` carries the release name."

### L4. Token convention contradicts itself and does not cover `ResolvedSettings`

- **Source.** PRD FR-18: "Tokens never appear on stdout or stderr, including in errors and verbose logs." Admin CLI shows `MaskToken` in `config current` / `profile list`.
- **Spine.** Channels convention: "Tokens never appear in any output; `MaskToken` shows four characters" (both cannot be true). `ResolvedSettings(Url, Token, ...)` is a record whose default `ToString` would print the token if logged.
- **Fix.** "Tokens never appear unmasked; `config current` and `profile list` show `MaskToken`; `ResolvedSettings` redacts `Token` in `ToString`."

### L5. `submittable` has no `reason`

- **Source.** Brief guardrail: read-only is "one filter away". PRD FR-19: "`describe_operation` on a Command returns `submittable: false, reason: read_only`."
- **Spine.** AD-3 `OperationDescriptor(..., Submittable)` with no reason; the Catalog is built before Read-only Mode is known to be the only cause.
- **Fix.** Add `SubmittableReason?` to the descriptor or compute both in `ICatalog` from `ResolvedSettings.ReadOnly`.

### L6. "No OAuth or identity server" is not restated where "issuer" is

- **Source.** Brief, Scope: "Any OAuth or identity server" is refused; Next release: "No new authentication server." PRD §8.3.
- **Spine.** Deferred, HTTP bullet: "issuer, token validation, and header forwarding are designed before the HTTP story" with no statement that the issuer is external.
- **Fix.** Append "no OAuth or identity server is built in v1 or the HTTP release; the issuer is external."

### L7. §E rows with no home in the spine

- **Source.** PRD addendum §E: `kind` filter (`list_operations`, `--kind read|write`); `--payload @file` and stdin; `--extension key=value` repeatable; `idempotencyKey` on `send_command` only.
- **Spine.** `EnvelopeArguments` carries `IdempotencyKey?` for Queries too; no `kind` filter on `ICatalog`; payload sources and extension syntax are absent. Story-level, but the spine's "under the spelling given" guarantee (FR-12) is not anchored.
- **Fix.** One sentence in AD-5: "argument names and spellings are those of PRD addendum §E; `IdempotencyKey` on a Query is `validation_failed`."

### L8. `EVENTSTORE_READ_ONLY` parsing rule not carried

- **Source.** PRD FR-19: ".NET boolean parsing."
- **Spine.** AD-13 says nothing about how `ReadOnly` is parsed from the environment.
- **Fix.** Add "(`bool.Parse` semantics)" to AD-13.

### L9. AD-12 diverges from the "pattern to copy" without citing why

- **Source.** PRD addendum §B: "Stdio host pattern to copy: `Hexalith.EventStore.Admin.Mcp` (static `[McpServerToolType]` classes, logging forced to stderr)"; a later §B bullet endorses `McpServerTool.Create` plus a custom list-tools handler for a catalog-driven surface.
- **Spine.** AD-12 Prevents "static `[McpServerToolType]` classes" and keeps only the logging half of the pattern. Consistent with §B's second bullet, but the divergence from the named pattern is not attributed.
- **Fix.** Cite the §B dynamic-tools bullet in AD-12's rationale.

## Coverage of items that did land (for traceability, one line each)

- D1 hybrid: attributes for description/kind/example, interface-first routing with attribute fallback and `conflicting_value` (conventions: Decoration Attributes, Routing per field).
- D2 compile-time references + assembly marker: AD-4; plug-in folder in Deferred.
- D3 five generic tools: AD-12; typed tools behind a filter in Deferred.
- D4 one binary, stdio v1, HTTP next with forwarding handler and no auth server: AD-10 seam (`UserId` included), Deferred, runtime table; `mcp --transport http` exits 2.
- D5 thin companion with profiles and exit codes from the admin CLI: AD-13, AD-14, exit-code convention; per-operation subcommands and shell completion in Deferred.
- D6 replace: FR-21/FR-22 mapped to documents outside `src/`; parity needs (kind, correlation, tenant, task via extensions) supported by `OperationDescriptor.Kind` and `EnvelopeArguments`.
- Verb rename `serve` to `mcp`: used consistently (AD-11, runtime view, Deferred); `serve` does not appear.
- ULIDs never GUIDs: AD-8, identifier-generation convention (`ByteAether.Ulid 1.4.1`, in the catalog).
- Never retries: AD-9 Prevents, Deferred.
- Read-only as a startup filter, enforced in the executor: AD-9, AD-12, AD-13.
- stdout/stderr discipline, `LoggerMessage`, no `Console.WriteLine` outside the output writer: Channels convention, AD-12 logging.
- Profile file schema, permissions, name regex, `mcpcli.json` layout: AD-14 (verified against `ProfileManager.cs`).
- Resolution order and defaults (`json`, URL designated as `http://localhost:8080`, no default tenant): AD-13 (port verified against the EventStore host launch profile).
- §F deferrals (search/filters/order-by/freshness/`ifNoneMatch`, command status, retries): Deferred, with the message identifier returned meanwhile.
- Untrimmed publish or rooted assemblies: AD-4, AD-17.
- Flat layout, `.slnx`, central package management, .NET 10 / C# 14, xUnit v3 + Shouldly + NSubstitute, `TreatWarningsAsErrors`: conventions, Stack, Structural seed.
- Pins that match the catalog: ModelContextProtocol 2.2.0, System.CommandLine 2.0.12, EventStore 3.106.0, Tenants.Contracts 5.7.0, Parties.Contracts 1.1.1, ByteAether.Ulid 1.4.1, Microsoft.Extensions.* 10.0.12, Microsoft.CodeAnalysis 5.9.0, xunit.v3 4.0.1, Shouldly 4.3.0, NSubstitute 6.2.0, Verify.XunitV3 33.0.2, Aspire.Hosting.Testing 13.5.4, CommunityToolkit.Aspire.Hosting.Dapr 13.5.1-beta.757, SDK 10.0.401; JsonSchema.Net is correctly flagged as a new pin.

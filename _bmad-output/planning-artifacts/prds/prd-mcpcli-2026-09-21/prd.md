---
title: Hexalith.McpCli PRD
status: final
created: 2026-09-21
updated: 2026-11-20
changeProposals:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-06.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-08.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10-shape-coverage.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-20.md
---

# PRD: Hexalith.McpCli
*Working title. The repository is `mcpcli`; the module name follows the sibling-module convention.*

## 0. Document purpose

This PRD is for the Hexalith maintainers and for the workflows that follow it: architecture, epics and stories, and the migration plan for the legacy per-module MCP servers. It builds on the product brief at `_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/` and does not restate its research. Rejected alternatives, transport mechanics, and comparables are in the adjacent `addendum.md`. Addendum §E, which defines arguments, and §G, which defines results, are normative for FR-9, FR-11, and FR-12. Section 4 owns the guardrails, §5.1 owns attribute and marker members, and each FR owns its behavior. The Glossary and §4 summarize those requirements and link to their owners. Unconfirmed inferences carry an inline `[ASSUMPTION]` tag and are indexed in §11.

**Status on 2026-11-20.** The first paired release, 2.0.1, shipped on 2026-11-05. The current source enrolls 26 Operations across Tenants, Parties and Projects (§8.1). Folders enrollment, Projects native read qualification and legacy retirement remain open. The stdio service uses the operator’s credential. The planned HTTP release adds shared sessions with per-user authority (§8.2). [Migration status](../../../../docs/release/migration-status.md)

The [20 November audit follow-up](../../sprint-change-proposal-2026-11-20.md) schedules Stories 5.13–5.21. Their acceptance criteria below describe backlog work. The audit covered commit `53205cdb`. On the updated `main` commit, `6993abfe`, the hosted build failed during environment setup. Windows and macOS jobs skipped. This run supplies no live or cross-platform qualification for the candidate. [CI run 44724309497](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/44724309497)

**Scope reconciliation approved 2026-11-06.** The product owner approved P1–P8 in the [platform-scope change proposal](../../sprint-change-proposal-2026-11-06.md). These clauses reconcile already shipped behavior; they do not imply earlier authorization by frozen story specs or decide the separate bootstrap/publication-history findings. Story 5.18 tracks the remaining F7 tenant-input gap under FR-16.

## 1. Vision

Hexalith.McpCli is the target Hexalith-owned MCP and CLI surface, for agent-eligible operations across domain and technical modules. Retained compatibility binaries keep their owner-specific removal gates, and the named compiler and vector-migration tools remain local. The first increment gives operators one generic MCP Server and one thin CLI driven by a single Catalog. Each of the six original Legacy Servers has its own retirement gates under FR-21. A Module declares each gateway-ready Operation once, in its Contracts Library, with a Decoration Attribute that carries what the agent needs and the contract cannot express: a description a stranger can understand, an example, and routing fallbacks. The Catalog discovers those declarations at startup and describes them to the agent; the shared executor validates each Payload, fills the Envelope, and submits through the Gateway. Production code under `src/` must stay module-independent. McpCli enrolls an eligible Contracts package by reference and rebuild. AD-23 assigns each non-Gateway capability a disposition and names the evidence required for cutover.

The goal is that a human or agent can do every **agent-eligible** Hexalith operation through one shared machine surface; UI-only and human-confirmation operations remain on confidential interactive UI under Platform AD-14. Hexalith is a CQRS platform in which business actions are Commands and reads are Queries, and the gateway-ready target state carries them through the EventStore Gateway. Infrastructure administration and resource-like capabilities follow adopted AD-23 dispositions; confidential UI, withdrawal and named local exemptions need no invented McpCli extension. Today that uniformity is hidden:

- each Legacy Server has its own transport, tool naming, description mechanism, and authentication story;
- only one of them reaches the Gateway;
- descriptions live in XML documentation comments that do not exist at runtime, so every server redescribes its operations by hand and drifts from the code.

There is no triggering incident; the bet is that the Agents, ChatBot, and Conversations Modules will soon need to act on business data across Modules, and that six dialects will not survive that contact.

Two consequences follow now. Shared sessions need to act with each user’s authority, which makes HTTP the next planned transport (§8.2). And a Command without a description is a Command an agent cannot use, so the Decoration Attribute stops being decoration and becomes part of what it means for a Hexalith Operation to exist: every Module that ships after 2026-09-21 ships agent-ready, or is not finished (FR-22).

## 2. Target user

### 2.1 Jobs to be done

- **Agent operator** (a developer with a dev or test EventStore). Install one .NET tool, point a Profile at the Gateway, and have an MCP-capable agent list, describe, and run every decorated Operation across Modules. Success is a cross-module task with no per-module setup.
- **LLM agent session** (Claude Code, Claude Desktop, VS Code, and the Agents, ChatBot, and Conversations Modules). Discover what Hexalith can do, understand each Operation from description and Schema alone, act, and get errors it can reason about.
- **Module author.** Make a Module visible to every agent on the day it ships by decorating its Contracts Library, and never write an MCP server again.
- **Shell user or CI script.** Call the same Catalog and Operations from a terminal with JSON on stdout, so a script and an agent cannot disagree about what Hexalith can do.

### 2.2 Non-users and the admin-plane boundary (v1)

The first increment serves business administration modeled as Gateway Commands and Queries. The Gateway checks the credential and the Operation’s scope. Tenants Commands and cross-tenant reads use `platform:tenants`. Single-tenant reads use the selected public tenant. End users and infrastructure administrators use the appropriate interactive UI for confidential actions. AD-23 assigns remote Admin A1–A4 to confidential UI and withdraws local Admin A5–A8 from the public target. The Admin inventory retains G1–G6, including UI coverage, independent authorization and persisted-effect checks before either binary retires (FR-21). Shared hosted sessions with per-user authority belong to the HTTP release (§8.2).

### 2.3 Key user journeys

- **UJ-1. Nadia checks a tenant member across two Modules.** Nadia installs the tool, configures a Profile for the test Gateway and tenant `acme`, and connects Claude Code over stdio. She has permission to read tenant membership and the Party record for a test member whose Party ID she already knows. The agent uses `list_modules`, `list_operations` and `describe_operation` to discover both Queries. It calls `run_query` for `tenants.get-tenant-users` under `acme`, then for `parties.get-party` with the fixture’s Party ID. Nadia checks membership and the returned Party record. Her original request also proposed creating a Party. That write (`parties.create-party`, T04) requires the FR-21 owner decision before it can count as a public-agent success. **If an authorized Command times out**, the agent reports an unknown outcome and leaves Nadia to inspect business state or EventStore operator tooling. Deliberate reuse of a caller-supplied idempotency key requires a trusted adapter for that Command on the target deployment.
- **UJ-2. An agent session explores a Module it has never seen.** The Conversations Module's agent is asked about tenant membership. It follows the same discovery sequence for `tenants`, sees each Operation with its kind and description, picks `tenants.get-tenant-users`, reads its Schema and example, and calls `run_query`. The result comes back paged with a cursor. A separate description of `tenants.list-tenants` reports the declared `platform:tenants` scope and omits a per-call tenant argument. Nobody wrote a tenants-specific prompt or tool. **Edge case:** the session runs in Read-only Mode; `send_command` is absent from its tool list, so it reports that it can look but not act.
- **UJ-3. Marc adds a Projects read to both Heads.** Marc maintains the Projects Contracts package. To add an eligible read, he decorates its Query with a description, example and Routing Values, then publishes the updated package with its existing Module marker. This repository bumps the package reference and rebuilds. Agents and scripts can discover the added read through either Head. **Edge case:** one record lacks a description; the Catalog excludes it and reports it on stderr at startup, so the gap is visible, not silent.

## 3. Glossary

Downstream readers and workflows use these terms exactly. Terms owned by a requirement point to it.

**Declaration**

- **Module** — a Hexalith domain module. Identified in the Catalog by its **Module Name**, a lowercase kebab-case string declared on its Contracts Library assembly.
- **Contracts Library** — the `*.Contracts` NuGet package of a Module holding its Command and Query type definitions. The only Module artifact this product references, under the dependency allowlist (§4).
- **Operation** — a Command or a Query. A class or record decorated with a Decoration Attribute. Each has exactly one Operation Name.
- **Command** — an Operation that writes to one aggregate through the Gateway. Kind `write`.
- **Query** — an Operation that reads through the Gateway. The handler can read a projection or compute the result directly. Kind `read`.
- **Operation Name** — the canonical identifier of an Operation, `<module-name>.<operation>` in kebab-case, for example `parties.create-party`. Identical in both Heads and independent of the Wire Type.
- **Wire Type** — the operation type string the Gateway dispatches on (for example, `create-tenant` for Tenants or a full CLR type name for a Parties Command). One of the Routing Values, never shown as the Operation Name.
- **Routing Values** — domain, Wire Type, the aggregate identifier source (a Payload property, the contract getter, or a constant), and any projection selectors a Query uses. A named projection actor requires a projection type (FR-2). Supplied by the EventStore contract interfaces when implemented, else by the Decoration Attribute.
- **Decoration Attribute** — the command or query attribute applied to an Operation type; members in §5.1.
- **Module marker** — the assembly attribute declaring a Module; members in §5.1.
- **Decoration Package** — the dependency-free NuGet package `Hexalith.McpCli.Abstractions`, built here, holding the Decoration Attributes, the identifier attribute, the Module marker, and the bundled analyzer (FR-1).
- **Identifier** — a Payload property marked with the identifier attribute or named by `aggregateIdProperty` (FR-7). Never inferred from a name suffix. Typed and validated by its Module's Identifier Kind.
- **Identifier Kind** — `Ulid` or `String`, declared once per Module on the Module marker (FR-3). Governs the Schema and validation of every Identifier in that Module (FR-7, FR-15). The message identifier the tool generates and any caller-supplied idempotency key or correlation identifier are always ULIDs regardless of that kind.

**Catalog and Heads**

- **Catalog** — the in-memory registry of Modules and Operations both Heads read; built per §5.2.
- **Head** — one of the two surfaces over the Catalog: the MCP Server and the CLI.
- **MCP Server** — the Head speaking the Model Context Protocol over stdio, exposing the five Generic Tools.
- **Generic Tool** — one of `list_modules`, `list_operations`, `describe_operation`, `send_command`, `run_query` (FR-9). The set never changes with the Catalog.
- **CLI** — the Head exposing the verbs in FR-12, installed as the `hexalith` command from the `Hexalith.McpCli` tool package (§7).
- **Payload** — the JSON body of an Operation, validated against its Schema before submission.
- **Schema** — the JSON Schema derived from the Operation type (FR-7).

**Execution**

- **Envelope** — the Gateway submission record around a Payload (FR-16; field list in addendum §B).
- **Gateway** — the EventStore gateway reached through the `Hexalith.EventStore.Client` package. The only backend this product talks to.
- **Tenant** — the tenant identifier placed in the Envelope. Resolved per FR-16 from an Operation's exact declared platform scope, else the Module's exact fixed tenant, else canonical public session/per-call values under the operator gate. In v1 the flag, environment variable and Profile supply session settings. The hosted design must bind tenant access to authenticated authority (§8.2). The executor never reads the Tenant from the Payload.
- **Actor** — the principal recorded as the author of a Command when its Operation names an `actorProperty`. In v1 the session flag, environment variable or Profile supplies the Actor (FR-16). Hosted calls require the authenticated actor and attested effective origin (§8.2).
- **Profile** — a named connection configuration in this tool's own profile file, default `~/.eventstore/mcpcli.json`, relocatable through `MCPCLI_HOME` under FR-18.
- **Read-only Mode** — a startup option under which write submission is refused and `send_command` is not advertised; discovery is unchanged (FR-19).

**Migration**

- **Legacy Server** — a proprietary Hexalith MCP server or plug-in being replaced by McpCli. The first six are listed in addendum §D; EventStore Admin MCP also enters the later administration migration inventory (FR-21).
- **Frozen CLI** — a proprietary CLI retained for compatibility during migration under FR-21/22. The FrontComposer compiler commands and the Memories local embedding-migration tool have explicit local-tooling exemptions under AD-23 (addendum §D).
- **Gateway-ready** — the state of a Module whose agent-facing Operations exist as decorated Command and Query types in a published Contracts Library and are accepted by the Gateway (checklist in §8.1).

## 4. Constraints and guardrails

Each rule below is authoritative; FRs reference them rather than restate them.

- **Dependency allowlist.** Direct production package references are limited to the first-party Decoration Package, `Hexalith.EventStore.Client`, the exposed Modules' `*.Contracts` packages, and the named pinned Stack packages. The allowed transitive baseline is the exact locked closure of the pinned EventStore client, `Hexalith.EventStore.Contracts`, and Stack packages; it includes the client's Dapr and Microsoft dependencies and the Contracts closure's `Hexalith.Commons.UniqueIds` and `ByteAether.Ulid`. An exposed Contracts Library may add its own identity and reference the dependency-free Decoration Package, but may add no other package identity outside that baseline. A CI test over restored assets enforces the direct references, approved baseline identities and versions, Module Contracts closure, no additional Module or Hexalith package, and no framework reference beyond `Microsoft.NETCore.App` (FR-20). Adding an external package outside this policy is a PRD change. The tool package never references an aggregate, projection, handler, client, or server project of any Module. Test projects may add the EventStore testing and Aspire composition packages the architecture names, plus one synthetic sample Contracts Library (the sample Module) never referenced by the tool package.
- **Zero module-specific code.** Production source types, branches, hand-authored scan lists and runtime configuration must stay module-independent. Test fixtures may name Modules. Pinned Contracts `PackageReference` entries and scan metadata generated from the restored dependency graph are permitted because they are the declarative enrollment mechanism (FR-5, FR-20).
- **Tenant.** Envelope-only, resolved by the executor (FR-16); never read from the Payload. A declared platform scope or fixed tenant cannot be overridden. Public variable-scope input is lowercased without trimming before the operator-gated session/per-call comparison; public `system` is reserved. A scope declaration grants no Gateway authority.
- **Identity in v1.** The stdio server acts as whoever owns the configured token; the audit trail says "the tool", not the human. The Actor an Operation records is an operator setting (Profile, flag, environment), never chosen by the agent per call, and the extension keys a call may carry are limited to an operator allowlist (FR-16, FR-18). This limitation is accepted for development and test use, and it is why HTTP transport is the next release.
- **Identifiers.** Message IDs, correlation IDs and idempotency keys must be canonical uppercase ULIDs (FR-16). Payload Identifiers and the aggregate identifier are typed by explicit marking and validated by the Module's Identifier Kind, never guessed from a name (FR-3, FR-7, FR-15). The Tenant is a non-empty string and is never ULID-validated. Every Envelope field is pre-validated against the Gateway's published patterns before submission (FR-15).
- **Idempotency.** One generated message identifier per call. An idempotency key is optional and caller-supplied only: the tool never invents one, never retries, and never claims generic deduplication because Gateway support depends on a trusted adapter registered for that Command type. When supplied, the key is passed through and echoed in the result (FR-16, FR-17).
- **Read-only.** Enforced in the executor, never by hints alone (FR-19).
- **Cost.** No hosted infrastructure in v1.

## 5. Features

Each feature opens with a description and the journeys it realizes, then its FRs; each FR states the rule, then its testable consequences. FR numbers are stable identifiers grouped by feature, not in numeric order (FR-19 sits in §5.5 beside the executor it constrains, FR-18 in §5.6).

| Feature | FRs |
|---|---|
| §5.1 Operation decoration | FR-1 mark a type, FR-2 routing values, FR-3 declare a Module, FR-4 describe properties |
| §5.2 Catalog | FR-5 build, FR-6 diagnostics, FR-7 Schema, FR-8 names |
| §5.3 MCP Server | FR-9 five tools, FR-10 stdio, FR-11 results and errors |
| §5.4 CLI | FR-12 verbs, FR-13 options, FR-14 exit codes |
| §5.5 Execution | FR-15 validate, FR-16 Envelope, FR-17 submit, FR-19 Read-only Mode |
| §5.6 Configuration | FR-18 Profiles |
| §5.7 Coverage and policy | FR-20 v1 Modules, FR-21 parity and migration, FR-22 no-new-server rule |

### 5.1 Operation decoration

**Description:** A Module author marks a class or record as a Command or Query with one Decoration Attribute, describes each property with `System.ComponentModel.Description`, and marks Identifier properties with the identifier attribute (FR-7). Routing Values come from the contract interfaces when implemented and from the attribute otherwise. Only Commands and Queries are decorated; events, read models, and value objects are not. Realizes UJ-3. The two tables below are the only description of the members; FRs refer to them.

**Decoration Attribute members**

| Member | Applies to | Required when | Meaning |
|---|---|---|---|
| `description` | both | always | What the Operation does, for a reader who has never seen the code |
| `example` | both | optional | A JSON Payload that validates against the Schema |
| `name` | both | optional | Overrides the derived `<operation>` part of the Operation Name |
| `domain` | both | no contract interface | Gateway domain, for example `party` |
| `wireType` | both | no contract interface, unless the marker's `wireTypeConvention` derives it | Wire Type the Gateway dispatches on |
| `aggregateIdProperty` | both | attribute-routed Command; optional for an interface-routed Command (contract getter) and for a Query | Payload property holding the aggregate identifier |
| `aggregateId` | query | list-style Query with no aggregate identifier property | Constant aggregate identifier the Gateway requires (it rejects an empty one); mutually exclusive with `aggregateIdProperty` |
| `projectionType` | query | required when `projectionActorType` is set and the interface supplies no type | Identifies the projection to read. A computed Query can omit both selectors. |
| `projectionActorType` | query | optional | Named actor that serves the projection. The attribute supplies this selector and FR-2 requires a resolved `projectionType`. |
| `platformScope` | both | optional | Exact cataloged platform request scope: `platform:` followed by a nonempty lowercase ASCII name containing letters, digits and single hyphens, starting and ending with a letter or digit; cannot coexist with Module `fixedTenant`; the Gateway independently authorizes it |
| `tenantProperty` | both | record declares a tenant member | Payload property the executor fills from the Envelope Tenant; never the aggregate identifier source |
| `correlationProperty` | command | record declares one | Payload property filled from the resolved command correlation identifier |
| `idempotencyKeyProperty` | command | record declares one | Payload property filled from the Envelope idempotency key |
| `actorProperty` | command | record declares an actor or principal member | Payload property filled from the resolved Actor (FR-16) |

Property-reference members (`aggregateIdProperty`, `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty`, `actorProperty`) name exact, case-sensitive top-level CLR properties, not serialized JSON names or paths. The Catalog resolves each once through effective Module serializer metadata, including `[JsonPropertyName]`, to one included, deserializable serialized member and escaped JSON Pointer. Schema generation, filling, ownership checks, and accessors use that same mapping. Missing, ignored, ambiguous, or converter-opaque targets exclude the Operation with `invalid_property_reference`. Multiple envelope roles, or an envelope role and `aggregateIdProperty`, cannot own the same serialized member; exclude with `conflicting_property_roles`, except the tenant/aggregate collision retains `tenant_is_aggregate_id`.

**Module marker members**

| Member | Required | Meaning |
|---|---|---|
| `name` | always | Module Name |
| `description` | always | One line for `list_modules` |
| `identifierKind` | always | `Ulid` or `String` (FR-3) |
| `fixedTenant` | optional | Exact Envelope Tenant every Operation of the Module runs under; cannot coexist with an Operation `platformScope`; surfaced by `describe_operation`, applied by FR-16 |
| `wireTypeConvention` | optional, default `Explicit` | How the Catalog derives a Wire Type when the attribute gives none: `Explicit` (none derived), `FullTypeName` (the CLR full type name, namespace included, not assembly-qualified), or `KebabCase` (the FR-8 name part) |
| `serializerOptionsProvider` | optional | A `Type` in the marked Contracts assembly. It must declare a public static, non-indexed `Options` property of exact type `JsonSerializerOptions` with a public getter that returns a non-null value. For Module Payloads, FR-7 applies its converters in declaration order ahead of the tool’s built-in converters. The tool owns the metadata resolver, other settings and Envelope serialization. An invalid provider excludes the Module (FR-6). |

#### FR-1: Mark a type as a Command or a Query

A Module author can apply the command or query Decoration Attribute to a class or record in a Contracts Library with a required description and the members above.

**Consequences (testable):**
- A type with the command attribute enters the Catalog with kind `write`; with the query attribute, kind `read`.
- Decorating a type is the owning maintainer's consent to expose that Operation to agents and operators through the Gateway without human confirmation; UI-only and human-confirmation operations are never decorated (§1). The Gateway still authorizes every call (AD-22). McpCli reports a decorated Operation missing from the FR-21 inventory and keeps it in the Catalog (AD-21). The existing Parties declarations conflict with K12 and require the owner reconciliation in FR-21.
- An empty or whitespace description is a build warning from a bundled analyzer and always a startup diagnostic that excludes the type (FR-6). The analyzer is a separate project packed into the Decoration Package and a separable story, and the package may ship before it exists; startup exclusion is the guaranteed behavior (OQ-4, resolved).
- An example that does not validate against the Schema is a startup diagnostic.
- The Decoration Package has no package references visible to a consumer; the analyzer's own dependencies are private assets.

#### FR-2: Resolve Routing Values per field

For each Routing Value, the Catalog uses the contract interface when the interface defines that field, else the attribute member, else the marker's `wireTypeConvention` for the Wire Type.

**Consequences (testable):**
- A Tenants Command implementing `ICommandContract` needs no `domain`, `wireType`, or `aggregateIdProperty`; a Tenants Query implementing `IQueryContract` needs no `domain`, `wireType`, or `projectionType`. `IQueryContract` carries no aggregate identifier, so a Query declares `aggregateIdProperty` (per-tenant reads) or `aggregateId` (list reads); a Query with neither stays in the Catalog and `describe_operation` reports `aggregateIdRequired: true`, meaning the explicit argument is mandatory (FR-16).
- A computed Query such as `projects.list` can omit both projection selectors. A projection type alone is valid. An actor selector without a resolved projection type excludes the Query with `missing_routing_values`.
- A Parties Command with no interface and no attribute routing members is excluded with a diagnostic naming the missing members; with `wireTypeConvention = FullTypeName` on the marker, only `domain` and `aggregateIdProperty` are needed.
- An attribute value equal to the interface or convention value is a redundant-value warning. One that differs from an interface value is a conflicting-value warning and the interface value is used; one that differs from a convention-derived value is used as given, since the convention is only a fallback.
- Domain is a per-Operation value and may differ within one Module (Tenants routes its global-administrator Commands, which v1 does not decorate, to a second domain).

#### FR-3: Declare a Module

A Module author can mark a Contracts Library assembly with the Module marker (members in §5.1).

**Consequences (testable):**
- The Catalog scans only assemblies carrying the marker; an undecorated assembly is invisible and produces no diagnostic (FR-20 distinguishes it from a marked assembly with no Operations).
- The Identifier Kind applies to every Identifier of the Module (FR-7, FR-15). Both v1 Modules declare `String`: Tenants because its aggregate identifiers are managed tenant names such as `acme`; Parties because it has not adopted ULIDs. The `Ulid` kind has no v1 consumer.
- A `fixedTenant` is the exact Envelope Tenant of every Operation in the Module (FR-16). An Operation may instead declare `platformScope` only when its Module has no fixed tenant; malformed scopes or a scope/fixed-tenant combination are excluded with `invalid_routing_value`. Neither value is inferred from the Module name.
- Current Tenants Commands and cross-tenant reads (`tenants.list-tenants`, `tenants.get-user-tenants`) declare `platform:tenants`. Single-tenant reads (`tenants.get-tenant`, `tenants.get-tenant-users`, `tenants.get-tenant-audit`) use the selected public tenant and matching managed-tenant aggregate identifier. Tenants declares no fixed `system` scope; these are enrolled Contracts facts, not generic executor branches.

#### FR-4: Describe properties

Every property carrying `System.ComponentModel.Description` gets a `description` in the Schema, and `describe --lint` on the CLI reports the description and property gaps of one Operation.

**Consequences (testable):**
- `describe --lint` reports a hollow Operation description that equals its humanized type name. It recursively reports undescribed properties, unmarked identifier-like properties (FR-7), and Payload paging members named `PageSize`, `Offset`, or `Cursor`. Paging travels only through `run_query` arguments (FR-16). The command exits 1 if any finding exists.
- Every `describe_operation` and `describe` result includes `lintFindings`; each finding has `code`, `severity`, and `message`. A property-level finding also has `property`, an RFC 6901 JSON Pointer using Module-serialized property names; the operation-level `hollow_description` finding omits it. An Operation with no findings returns an empty array. The `--lint` flag changes only the CLI exit-code behavior (FR-14), not the result shape.
- These findings are lint-only: they never appear as Catalog diagnostics (FR-6).

### 5.2 Catalog

**Description:** At startup the tool builds one Catalog from every referenced Contracts Library carrying the Module marker. Both Heads read it, so they cannot disagree. Realizes UJ-1, UJ-2, UJ-3.

#### FR-5: Build the Catalog from referenced assemblies

The tool builds the Catalog at startup from the Contracts Libraries compiled into it; the assembly list is generated at build time from the package references flagged `HexalithContracts="true"` and never hand-maintained, and assemblies are never loaded from a folder.

**Consequences (testable):**
- Adding a Module is a flagged package reference and a rebuild; no source change in this repository. A test asserts the generated list equals the flagged set.
- The tool is published untrimmed, so a referenced assembly that no code touches is still scanned; if trimming is ever enabled, Contracts assemblies must be rooted first.
- Modules and Operations are sorted by name, and JSON is written with the tool's canonical serializer options, so discovery output is byte-identical across runs and operating systems for one build.

#### FR-6: Report Catalog problems at startup

Every decorated type or Module the Catalog cannot expose as declared is reported once on stderr with its name, a category, and a severity, and the tool continues. Diagnostics never change an exit code (FR-14) unless `--strict` is set, in which case any diagnostic, warnings included, ends the verbs that build the Catalog with exit 2 and `code: catalog_invalid` before any result.

**Consequences (testable):**

| Category | Severity | Trigger |
|---|---|---|
| `missing_description` | error, type excluded | Empty or whitespace description (FR-1) |
| `missing_routing_values` | error, type excluded | A required Routing Value has no source, including a Query’s projection type when an actor selector is present (FR-2) |
| `invalid_routing_value` | error, type excluded | A domain, Wire Type, projection type, projection actor type, Module `FixedTenant`, Operation `platformScope` (including a scope/fixed-tenant conflict), or `aggregateId` constant outside the Gateway patterns, or a contract interface routing member that throws (FR-15) |
| `duplicate_operation_name` | error, later type excluded | Two types resolve to one Operation Name (FR-8) |
| `invalid_example` | error, type excluded | Example does not validate against the Schema (FR-1) |
| `invalid_identifier_type` | error, type excluded | An Identifier that does not serialize as a JSON string (FR-7) |
| `tenant_is_aggregate_id` | error, type excluded | `tenantProperty` names the aggregate identifier source. On Tenants, `TenantId` is the aggregate identifier, not the tenant |
| `invalid_property_reference` | error, type excluded | A property-reference member cannot resolve to one included, deserializable serialized property under Module options, or is converter-opaque or of an unsupported type for its role |
| `conflicting_property_roles` | error, type excluded | Two envelope roles, or an envelope role and the aggregate property source, own one serialized member; the tenant/aggregate case uses `tenant_is_aggregate_id` |
| `ambiguous_aggregate_id` | error, type excluded | Both `aggregateId` and `aggregateIdProperty` set |
| `duplicate_module` | error, later assembly excluded | Two assemblies declare one Module Name |
| `invalid_module_declaration` | error, assembly excluded | The Module marker's name, description, Identifier Kind, or wire type convention is invalid, or the Contracts assembly's types cannot be loaded (FR-3) |
| `invalid_serializer_options_provider` | error, assembly excluded | The provider is outside the marked assembly, its `Options` property fails the §5.1 contract, or the getter throws or returns null. |
| `conflicting_operation_kinds` | error, type excluded | One type carries both the Command and the Query decoration (FR-1) |
| `invalid_operation_declaration` | error, type excluded | A decorated type is abstract, open generic, or not a class (FR-1) |
| `invalid_operation_name` | error, type excluded | An explicit or type-derived Operation Name part is not lowercase ASCII kebab-case (FR-8) |
| `invalid_schema` | error, type excluded | The payload uses extension data, polymorphism, a free-form (`object`, `JsonElement`, `JsonDocument`, `JsonNode`) or converter-opaque member, a Command payload that is not a JSON object, or has a System.Text.Json contract error (FR-7) |
| `conflicting_value` | warning, kept | Attribute value differs from the interface value (FR-2) |
| `redundant_value` | warning, kept | Attribute value equals the interface or convention value (FR-2) |
| `empty_module` | warning, kept | A marked assembly exposes zero Operations (FR-20) |

- Scan order is deterministic: assemblies in the generated list order (sorted by assembly name), types within an assembly by ordinal full type name; the first declaration of a duplicate Module Name or Operation Name survives.
- An empty Catalog fails only the verbs that need it (the discovery verbs, `send`, `query`, and `mcp`) with exit 2 and `code: catalog_empty`; `config` and `--version` never build the Catalog and always run (FR-14).
- The `mcp` verb validates settings, builds the Catalog, and applies `--strict` before opening the JSON-RPC channel. Any failure before the server starts serving MCP requests writes one structured error to stderr, writes nothing to stdout, and exits 2. Once requests can be served, failures travel only as JSON-RPC/MCP errors (FR-10, FR-14).

#### FR-7: Derive a JSON Schema per Operation

The Catalog derives from the Operation type a Schema that includes every settable or constructor-bound property and rejects unknown properties.

**Consequences (testable):**
- Required, nullable, enum, nested type, and collection members map to the corresponding JSON Schema constructs; `additionalProperties` is `false`. Get-only members with neither a setter nor a constructor parameter (such as `ICommandContract.AggregateId`) are not Schema properties; the executor reads them through the accessor (FR-16).
- An Identifier is a property marked with the identifier attribute or named by `aggregateIdProperty`; it is typed `string`, with the ULID pattern when the Module's Identifier Kind is `Ulid`, and never with `format: uuid`. A property whose CLR type is `ByteAether.Ulid.Ulid`, recognized by full name so the Decoration Package needs no reference to it, gets the pattern regardless of the kind.
- An Identifier's CLR type must serialize as a JSON string; a value-object identifier serializes as its own declared converter or the marker's `serializerOptionsProvider` dictates, and the tool adds no converter. An Identifier that does not serialize as a string excludes the Operation with an `invalid_identifier_type` diagnostic (FR-6).
- An unmarked property whose name ends in `Id` retains the ordinary Schema derived from its declared type and serializer contract and produces a `describe --lint` warning (FR-4); the name suffix never types or rewrites a property. A string Schema therefore appears only when the declared serialization is already a JSON string.
- Serialized members resolved from `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty`, or `actorProperty` are marked `readOnly`, removed from `required`, and filled by the executor (FR-16); a caller may omit them. Pre-fill validation checks a copy with only those mapped members removed; ownership checks retain the raw values. The complete rebuilt Payload is then checked against the unmodified Schema, including those members' types and patterns. `readOnly` alone does not suppress validation.
- A Command Payload Schema has a non-null object root, including when the .NET exporter initially emits an object-or-null root. Nested nullable members retain their declared nullability. A Query root follows its declared contract Schema and the Gateway's optional Query Payload rule.

#### FR-8: Name Operations canonically

Each Operation's name part is the type name in kebab-case with a trailing `Command` or `Query` removed, unless the attribute `name` member overrides it.

**Consequences (testable):**
- `CreateParty` in `parties` is `parties.create-party`; `GetTenantUsersQuery` in `tenants` is `tenants.get-tenant-users`.
- Two types resolving to one Operation Name is a diagnostic; the later in scan order (FR-6) is excluded.

### 5.3 MCP Server

**Description:** The MCP Server exposes exactly five Generic Tools over stdio. The tool surface never changes with the Catalog, so it fits any client's tool budget and never needs list-changed notifications. Realizes UJ-1, UJ-2.

#### FR-9: Expose five Generic Tools

An agent can call the five Generic Tools and no others; their arguments are the addendum §E table and their results the addendum §G documents, which both Heads implement.

**Consequences (testable):**
- `tools/list` returns `list_modules`, `list_operations`, `describe_operation`, `send_command`, `run_query` in that order, or the same sequence without `send_command` in Read-only Mode. The order is verified through the protocol in fresh processes.
- `list_modules` returns each Module Name with its description and Operation count; `list_operations` takes a Module Name and an optional kind and returns Operation Name, kind, description, or `unknown_module` when a non-empty requested Module Name is absent; `describe_operation` returns description, kind, Schema, example when declared, the Envelope arguments the caller may supply (whether `aggregateId` or `idempotencyKey` is required, the exact declared platform scope or Module fixed tenant when present), `lintFindings`, and head-level `submittable`, with a reason when it is false.
- `submittable` reports surface availability from Read-only Mode and resolved Gateway URL only. It is `false` with `reason: read_only` for a Command in Read-only Mode; otherwise it is `false` with `reason: configuration_invalid` when the session has no resolved Gateway URL; otherwise it is `true`. Tenant, actor, Payload, and per-call Envelope requirements are evaluated only on execution and do not change this discovery value. An offline discovery fixture covers both read and write Operations.
- Each tool description has three labeled parts: `Purpose`, `Use when`, and `Next`.
- The three discovery tools and `run_query` carry `readOnlyHint: true`; `send_command` carries `readOnlyHint: false` and `idempotentHint: false`.

**Deferred generic arguments.** v1 exposes no dedicated `run_query` arguments for search, filters, order-by or freshness. The FR-21 parity check still covers supported behavior implemented through an owner-approved Payload and handler (AD-23 K03).

#### FR-10: Serve over stdio with clean channels

The MCP Server runs as a local process over stdio; stdout carries JSON-RPC only and all logging goes to stderr.

**Consequences (testable):**
- A test that drives the server with the ModelContextProtocol client SDK over stdio establishes a session through the version-appropriate legacy `initialize` or 2026-07-28 discovery path, then completes `tools/list` and one call to each tool without a parse error. The release checklist separately covers Claude Code, Claude Desktop, and VS Code.
- The server starts from a Profile or environment variables with no interactive prompt.
- Settings and Catalog validation complete before the server serves MCP requests. Tests for malformed settings, an empty Catalog, and `mcp --strict` diagnostics each assert one structured stderr error, exit 2, and zero stdout bytes; once requests can be served, tests assert failures use JSON-RPC/MCP errors only under both protocol revisions.

#### FR-11: Return structured results and errors

Once input binding succeeds, every tool returns structured content with a declared output schema. Tool failures return a structured error. MCP input-binding failures use a JSON-RPC error (addendum §E). Both Heads serialize the same result and error record types. Addendum §G is the exhaustive contract for their field names, nesting, required and optional members, and omission rules; declared schemas and architecture records must conform to it.

**Consequences (testable):**
- Validation failure: `code: validation_failed`, the Operation Name, and one entry per violation with JSON path and message; a Payload that is not JSON is one violation.
- Gateway-client failure: return `code: gateway_error` with the exception status and the mapped detail defined in addendum §G. Include the reason code, retryable flag, client action, retry-after value, and correlation identifier only when the client exception provides them. This includes HTTP-success responses represented by `EventStoreGatewayException` because they are malformed or fail semantic validation; their `2xx` status is preserved.
- Unknown Operation Name: `code: unknown_operation` and up to three nearest Operation Names by case-insensitive edit distance.
- Unknown non-empty Module Name in `list_operations`: `code: unknown_module`, the requested Module Name, and up to three nearest declared Module Names by case-insensitive edit distance (addendum §G). Missing or empty `module` fails Head input binding before Catalog dispatch: MCP returns a JSON-RPC invalid-parameters error; CLI exits 2 with the §G `invalid_arguments` document.
- A required MCP `payload` must be a JSON string. An object in its place fails binding with JSON-RPC `-32602`. Malformed JSON inside the string for an available Operation reaches the executor and yields `validation_failed`. A bound `list_operations` call with `kind` set to `Read` yields a tool error with `isError: true` and `invalid_arguments` for `kind` (addendum §§E, G).
- Any other exception: `code: internal_error` with a message, never a stack trace.
- Snapshot tests assert each addendum §G result and error schema, including types, constraints, enums, required members, and optional-member omission, and run the same fixtures through both Heads.

### 5.4 CLI

**Description:** The CLI is a thin companion over the same Catalog and executor. It proves the Catalog without MCP, lets a script do anything an agent can, and hosts the MCP Server through the `mcp` verb (the brief called it `serve`; renamed so the verb names the protocol). Realizes UJ-1, UJ-3.

#### FR-12: Expose the matching verbs

A shell user can run `modules`, `operations <module> [--kind]`, `describe <operation> [--lint]`, `send <operation>`, `query <operation>`, `mcp`, and `config`.

**Consequences (testable):**
- Each Head implements every argument assigned to it in the addendum §E table, under the spelling given there.
- `send` and `query` accept the Payload as `--payload <json>`, `--payload @file`, or stdin.
- `mcp` starts the MCP Server over stdio; `mcp --transport http` exits 2 with `code: unsupported_transport` and a message naming the release in which it arrives, before building the Catalog.
- `--format table` renders `modules`, `operations`, and `config`; on `describe`, `send`, and `query` the output is JSON with one stderr note, and the exit code is unaffected.

#### FR-13: Resolve global options in one order

Every verb accepts `--url`, `--token`, `--tenant`, `--actor`, `--allow-tenant-override`, `--profile`, `--format json|table`, `--output <file>`, `--read-only`, and `--strict`. Resolve `--profile` first, in this order: flag, environment variable, then active Profile. Resolve every other option in this order: flag, environment variable, selected Profile, then default. Use only the sources listed for that option in addendum §E. For `mcp --transport stdio`, the adopted AD-13 policy ignores valid inherited format settings, accepts explicit `--format json`, and rejects explicit `--format table` or any `--output` before Catalog/transport startup with one stderr `invalid_arguments` document (`argument: format` or `output`, format first if both), zero stdout bytes, exit 2, and no output file opened. Malformed inherited settings still fail validation. These are session settings; the CLI has no per-call tenant. Only the MCP tools carry a per-call `tenant` argument, governed by FR-16.

**Consequences (testable):**
- The order is testable per option with a fixture that sets every source. When both URL and token resolve, they must come from the same source (flags, environment or selected Profile). A mixed pair fails as `configuration_invalid` before any Gateway request. A URL alone is permitted.
- Story 5.16 requires both Heads to refuse a bearer token over non-loopback HTTP before sending any request. HTTPS and the documented private loopback port-forward are supported. Addendum §E gives the profile-entry criteria.
- Defaults differ from the admin CLI: `json` is the default format, and the URL has no default. `modules`, `operations`, `describe`, `config`, `--version`, and MCP discovery work without one; `send`, `query`, and the corresponding MCP execution calls return `configuration_invalid` when execution has no resolved URL, rather than silently falling back to the admin API. `[ASSUMPTION: a tool whose primary reader is an agent defaults to JSON.]`
- Environment variable names are in addendum §E; they use the `EVENTSTORE_` prefix without `ADMIN`. `[ASSUMPTION: this tool is not the admin plane, so it must not read the admin CLI's variables.]`
- Boolean options (`--read-only`, `--strict`, `--allow-tenant-override`) accept `true`, `false`, `1`, and `0` from the environment; anything else is `configuration_invalid`, exit 2.

#### FR-14: Use one exit-code contract

Handled CLI outcomes use the codes below. If Ctrl+C or SIGTERM exceeds the command parser’s termination timeout, the process can exit 130 or 143 respectively.

**Consequences (testable):**

| Exit | Meaning | Output |
|---|---|---|
| 0 | Successful invocation | Results go to stdout by default or to the file selected by `--output`, with stdout empty. Help and version produce informational output. Normal MCP shutdown also exits 0. |
| 1 | `describe --lint` produced at least one finding (FR-4) | The same result document goes to stdout or the selected output file. |
| 2 | Handled failure, including refusal, validation, configuration, Gateway or output errors | Ordinary CLI errors go to stdout as one JSON error even with `--format table` or `--output`. An `mcp` failure before request serving writes the error to stderr and leaves stdout empty. Once serving, request errors use the protocol (FR-10). |

- Catalog diagnostics go to stderr and never move an invocation between rows; only `--strict` turns them into row 2 (FR-6).
- The CLI checks the output destination before submitting a Gateway request or saving a configuration change. Rejecting the destination at this point sends zero Gateway requests and preserves the saved Profile. A later write failure can return exit 2 with `internal_error` after the Gateway accepted the Command or the Profile was saved. Inspect business state or the saved Profile before deciding whether to retry (FR-17).

### 5.5 Execution, Envelope, and Read-only Mode

**Description:** Both Heads share one executor. It validates the Payload, fills the Envelope, submits through the Gateway client, maps the response, and enforces Read-only Mode. Nothing module-specific lives here. Realizes UJ-1, UJ-2.

#### FR-15: Validate before submitting

The executor validates every Payload against the Schema and refuses to submit an invalid one; all violations are reported together. It also pre-validates every Envelope field against the Gateway's published rules, so a Gateway 400 is never the first signal of a tool-side mistake.

**Consequences (testable):**
- An invalid Payload never reaches the Gateway; the substituted Gateway client records zero calls.
- The Core executor accepts a Command call only for a write Operation and a Query call only for a read Operation. After Operation lookup and before availability or Payload checks, a mismatch is `validation_failed` at `/operation` in every session, with zero Gateway calls. A matching write call in Read-only Mode retains the `read_only` response before a missing-URL error.
- A JSON null or non-object Command Payload is `validation_failed` at `/` before contract accessor use or Gateway submission; nullable nested properties remain valid when their Schema permits them.
- The explicit aggregate identifier argument and the resolved aggregate identifier are checked by the Module's Identifier Kind: a canonical uppercase ULID for `Ulid`, a non-empty value for `String` (FR-3).
- Per call, an ordinary resolved Tenant contains 1–64 lowercase ASCII letters, digits or hyphens and starts and ends with a letter or digit. Variable-scope session/per-call inputs are lowercased invariantly without trimming before selection; public `system` is refused. A declared platform scope uses the separate §5.1 scope grammar and exact matching, rather than the ordinary tenant pattern; supplying a platform-looking value to an ordinary Operation cannot grant platform authority (FR-16).
- Aggregate and entity identifiers match the Gateway's alphanumeric, dot, hyphen, and underscore pattern of at most 256 characters with no colon; extension keys are in the Profile's allowlist (FR-16). Each failure is a `validation_failed` entry at `/tenant`, `/aggregateId`, `/entityId`, or `/extensions/<key>`. Routing Values, fixed tenants and declared platform scopes are checked once at Catalog build (FR-6).

#### FR-16: Fill the Envelope

The executor generates a message identifier per call, passes through a caller-supplied idempotency key without inventing one, resolves the Tenant, the Actor, and the aggregate identifier, and for Commands passes a caller-supplied correlation identifier and allowed extensions through. When the caller omits the optional command correlation identifier, the resolved correlation identifier is the generated message identifier; the executor never generates a second identifier for correlation.

**Consequences (testable):**
- Generated message identifiers are ULIDs and differ between calls; a caller-supplied idempotency key or correlation identifier that is not a ULID is a validation failure. The same resolved command correlation identifier (`callerCorrelationId ?? generatedMessageId`) is sent in `SubmitCommandRequest`, written to any declared `correlationProperty`, and returned as `correlationId` in the success document, even when the Gateway echoes a different valid correlation identifier.
- Command fixtures cover supplied and omitted correlation identifiers and overwrite any caller Payload value under `correlationProperty` with the resolved value before rebuilt-Payload validation.
- The Tenant resolves in this order, and a Command or Query with no Tenant from any source is `validation_failed`:
  1. The Operation's exact `platformScope`, when declared; otherwise the Module's exact `fixedTenant`. The declarations cannot coexist. The session Tenant is ignored, any per-call value must match the declaration using ordinal equality, and `allowTenantOverride` cannot replace a declaration. Conflicts fail at `/tenant` before any Gateway call.
  2. For variable-scope Operations, the session and per-call MCP inputs are lowercased invariantly without trimming before selection and override comparison. A per-call value is selected when no session Tenant resolves from the FR-13 chain or `allowTenantOverride` is set. Matching canonical values need no override; a differing value without permission is `validation_failed` at `/tenant`.
  3. Otherwise the canonical session Tenant from the FR-13 chain is used. CLI `--tenant` remains a session setting. The ordinary tenant pattern and reserved public `system` refusal apply after resolution; exact historical fixed-tenant compatibility is retained.
- The Gateway independently authorizes the cataloged scope, operation, credential, surface and permission. A tool declaration grants no platform authority. Under Story 5.18, once EventStore lands the matching canonicalizer, both Heads must reject non-ASCII public tenant input at `/tenant` before lowercasing or comparing it, with zero Gateway calls. Uppercase ASCII remains valid. The exact declared-scope, reserved-tenant and override rules above still apply.
- The aggregate identifier resolves in this order, and a Command or Query resolving to nothing is `validation_failed`; an empty aggregate identifier is never sent:
  1. The explicit argument. One that disagrees with the accessor value is `validation_failed`.
  2. The value of an accessor compiled once at startup, which reads `aggregateIdProperty` when set and otherwise the `ICommandContract` getter. A Command with no accessor source is excluded from the Catalog (FR-2).
  3. The Query's `aggregateId` constant.
- An Operation naming an `actorProperty` requires a resolved Actor and returns `validation_failed` when it is missing. In v1 the Actor comes from the session flag, environment or Profile. Shared HTTP calls must derive the Actor from authenticated identity under §8.2. `[ASSUMPTION: in v1 the operator states the actor principal in the Profile; the tool never decodes the token.]`
- A present raw value under `tenantProperty` or `actorProperty` must be a JSON string ordinally equal to the resolved value (including a declared platform scope for `tenantProperty`); null, non-string, or differing values produce `validation_failed` at the mapped member pointer. Otherwise, the executor overwrites the properties named by `tenantProperty`, `correlationProperty`, and `actorProperty` with their Envelope values before submission. When the caller supplies an idempotency key, the executor overwrites `idempotencyKeyProperty` with that key. Without a per-call key, a non-null raw value there is `validation_failed` at `/idempotencyKey`; a raw null is removed before final validation and submission. If an Operation has a non-nullable or serializer-required `idempotencyKeyProperty` (effective `JsonPropertyInfo.IsRequired` under the Module's Payload options), discovery reports `idempotencyKeyRequired: true`, and omitting the key produces `validation_failed` at `/idempotencyKey` before contract materialization.
- The executor preserves the raw Payload for ownership checks and schema-validates a copy with only the mapped envelope-owned members removed, without constructing the contract. Ordinary members, unknown names, and root constraints remain checked. It resolves envelope values, checks raw Tenant/Actor disagreements and Payload-only idempotency keys, fills the owned members, then validates the complete rebuilt Payload against the unmodified Schema. Raw correlation values and, when a caller supplies a key, raw idempotency values may have any JSON shape because they are overwritten; their old type/pattern constraints must not preempt the ownership rules. It reads an `ICommandContract.AggregateId` getter only from that complete, validated Payload. Omitted envelope-owned members that the Schema permits cannot fail required-member deserialization before filling; conflicting supplied Tenant or Actor values still fail before overwrite.
- Extensions travel only on Commands and only with keys in the Profile's `allowedExtensions` list, default empty (FR-18). Queries carry neither a correlation identifier nor extensions in v1, because the pinned client's query request has no such members (§8.2).
- Paging travels only as `run_query` arguments mapped to the Gateway's paging options; a Payload member named like one is sent as ordinary Payload, neither stripped nor mapped (FR-4).
- The Envelope carries the Routing Values, never the Operation Name.

#### FR-17: Submit and map the response

The executor submits through the `Hexalith.EventStore.Client` gateway client, returns the Gateway's result as JSON, and never retries.

**Consequences (testable):**
- A successful Command returns the canonical `messageId` supplied by the Gateway. If the acknowledgment omits `messageId` or sets it to null, return the submitted message ID. Its `correlationId` always equals the submitted correlation ID (FR-16). The result echoes `idempotencyKey` only when supplied. The Gateway does not distinguish a replay from pending admission, so the result omits `duplicate`.
- **Story 5.17 (backlog).** A present empty, whitespace-only or noncanonical acknowledgment `messageId` must produce `gateway_error` after exactly one submission. Validate the ID at the Gateway client’s HTTP response boundary, where the actual numeric status is available. Carry that status, the submitted correlation ID and a “Command may have succeeded” detail through the client exception to both Heads. The pinned 5.4.0 success DTO discards HTTP status. Delivery depends on a compatible client or response-preserving adapter. Exercise HTTP 200 and 202 with different echoed correlation IDs, canonical IDs, omitted/null IDs and malformed IDs. Each error must meet the existing §G schema.
- Query results include the document. When paging metadata applies, they include page size and each available offset, next cursor, total count, and has-more value. Omit absent metadata; do not supply defaults. Query results have no correlation identifier in v1 (§8.2). A Query-side `gateway_error` includes one only when the client exception provides it.
- The only outbound HTTP is through the gateway client; a test asserts no other `HttpClient` registration.

#### FR-19: Refuse writes in Read-only Mode

When the tool starts with `--read-only` or `EVENTSTORE_READ_ONLY` (FR-13), write submission is refused with `code: read_only`.

**Consequences (testable):**
- The MCP Server does not register `send_command`, so `tools/list` omits it; the CLI `send` verb exits 2 with `code: read_only`.
- The executor, called directly with a `write` Operation, returns `read_only` without touching the Gateway client; this is the guarantee, not the tool list.
- `list_operations` still lists Commands with kind `write`; `describe_operation` on a Command returns `submittable: false, reason: read_only`.
- `--read-only` on a read verb is accepted and has no effect.

### 5.6 Configuration and Profiles

**Description:** Connection settings live in this tool's own file, default `~/.eventstore/mcpcli.json`; an absolute `MCPCLI_HOME` relocates it under the selected home as defined by FR-18. It has the admin CLI's shape and `config` verbs but is not shared with it: one profile name cannot serve both tools, since the admin URL and token target the admin API and the admin CLI rewrites its file from its own typed model. Realizes UJ-1.

#### FR-18: Manage Profiles

A shell user can select a Profile by name; a Profile holds `url`, `token`, `format`, `tenant`, `actor`, `allowTenantOverride`, and `allowedExtensions` (addendum §E).

**Consequences (testable):**
- The active Profile is used when `--profile` is absent; `config use`, `config current`, and `config profile list|add|remove` behave as in the admin CLI, and `config set <profile> <field> <value>` manages the remaining fields. `[ASSUMPTION: shell completion is deferred.]`
- The store uses an explicit constructor file path first; otherwise an absolute `MCPCLI_HOME` selects `<MCPCLI_HOME>/.eventstore/mcpcli.json`; an unset override uses `<user-profile>/.eventstore/mcpcli.json` on each supported OS. Empty, whitespace-only, relative, control-character-containing or existing-file overrides fail as `configuration_invalid` without exposing the supplied path or falling back to the real user's home. This selector changes the file location, not session setting precedence or identity. Atomic writes, permissions, ACLs, link rejection and isolation from the admin CLI's `profiles.json` remain required.
- A `format` other than `json` or `table` is `configuration_invalid`, exit 2.
- Tokens never appear on stdout or stderr, including in errors and verbose logs. Story 5.16 requires private entry and rotation by a non-echoing prompt or explicit stdin mode, with conflicting inputs rejected. Profile mutations must reject unsafe stored URL/token pairs. Cancellation or invalid input must preserve the previous Profile and permissions (addendum §E).
- Under Story 5.19 a successful creation or update must reopen on the next read. Accept up to 1,048,576 serialized UTF-8 bytes inclusive. On overflow, return a configuration error before replacement, clean up the temporary file and preserve the previous bytes, active Profile and permissions.

### 5.7 Coverage, migration, and policy commitments

**Description:** Apart from FR-20, these requirements are commitments rather than code in this repository. The end state is one server and one CLI for all of Hexalith. The product owner chose replacement over a strangler pattern to remove the inconsistency for good, accepting cross-repository coordination for the deletions. Realizes UJ-3.

#### FR-20: Cover the v1 Modules

The tool pins only Contracts Libraries that satisfy the dependency allowlist (§4) and exposes every valid decorated Operation in those packages. Tenants and Parties are the required v1 Modules. Section 8.1 records subsequent enrollments. V1 is done when the tool is released and Tenants and Parties are covered end to end. Versioned, maintainer-approved conformance vectors in the owning Module repository cover every Operation Shape in `list_operations`: the combination of kind, Identifier Kind, Wire Type convention, tenant source (exact `platformScope`, Module `fixedTenant`, or public), aggregate-identifier source (property, constant, or none), query projection selector (`projectionType`, `projectionActorType`, or none), and required idempotency key that the Catalog derives from the decorations (AD-16). Per-Operation handler semantics are tested in the owning Module repository. v1 coverage evidence produced under the earlier one-vector-per-Operation rule remains valid. Both Heads execute every vector against the same reset loopback Gateway script and produce equal canonical documents and captured Gateway requests after masking only generated message and correlation identifiers (SM-4); each request also matches the vector's expected inputs. Separately, a blocking Aspire test executes each approved live vector once against a running EventStore and asserts Gateway acceptance or a returned Query document plus the vector's semantic checks (NFR-7). Each Module has at least one live vector per Operation kind it declares; for a new enrollment, its live Command vector creates an aggregate in a prerequisite, then submits a second Command to it with a caller-supplied idempotency key and reads the effect back with a postcondition Query. A live Command is not submitted twice merely to compare documents. A follow-on Module must meet the same dependency, parity and live-evidence gates before its coverage is qualified.

**Consequences (testable):**
- Package references only; CI builds contain no project reference to any Module, and the allowlist test rejects any referenced Contracts Library whose closure breaks the rule.
- A referenced Module whose assembly carries the marker but exposes no Operation appears in `list_modules` with zero Operations and an `empty_module` warning; an unmarked assembly is invisible (FR-3, FR-6).
- Projects.Contracts 2.0.0 passes the allowlist and exposes four reads. Under Story 5.21, Projects and EventStore must settle Payload versus Envelope paging under AD-20. DW-82 requires both Heads to return the expected IDs in order across two populated pages, an authorized detail result and a denial that discloses no protected data. Retain the empty or Unavailable case. Record host revision, package, roles, synthetic IDs and owner verdict before claiming native read qualification (addendum §H).
- A generic runner rejects an Operation Shape without an approved vector and a duplicate or stale vector. A vector is stale when its Operation is absent from the restored Catalog or the Catalog rejects its inputs. Vectors supply valid Payload and Envelope values, prerequisite Operation calls, and semantic assertions; this repository contains no Module-specific setup code.
- McpCli maintainers approve one versioned, closed vector contract and shared compatibility validator before Tenants or Parties author vectors. That companion test artifact fixes generic prerequisites, inputs, scripted Gateway responses, assertion vocabulary, and supported format versions. Each vector names its owning Contracts package ID and the version it was authored against. The shared validator compares the package ID with the owning Contracts release artifact before Module maintainer approval; the runner validates every vector against the flagged restored production package before loopback or live execution. A version difference alone is reported, not failed, and needs no re-approval.
- Tenants coverage requires upstream audit handlers to honor the effective serialized `From`, `To`, and `Category` members and exposed paged handlers to consume `QueryEnvelope.Paging`. Live vectors use discriminating data to assert non-default filtered results and actual page contents for a non-default page size and a subsequent cursor. Retained legacy Payload paging members cannot govern generic envelope requests. Passing status codes or paging metadata alone cannot satisfy this gate.
- Parties coverage passes only when the maintainer-approved, versioned FR-21 inventory matches the built Catalog. Each included canonical Operation Name must appear exactly once in `list_operations parties`. A build-time Catalog-descriptor or reflection test must separately match each Operation to its decorated contract type. Each excluded legacy operation must have an approved exclusion row with a rationale.

#### FR-21: Define parity and produce the migration plan

A Legacy Server or Frozen CLI is retired only when each supported operation has an owner-approved McpCli replacement or explicit product withdrawal, with authorization and behavior proven on the selected environment. Gateway-ready Command and Query operations use decorated Contracts; adopted AD-23 assigns confidential UI, explicit withdrawal, named retained local-tooling exemptions or deferral to other classes. Confidential UI, withdrawal and the named exemptions require no new McpCli transport; their independent evidence and retirement gates remain binding. The first versioned migration inventory is a v1 deliverable owned by the McpCli maintainers; ecosystem retirement continues in a successor epic.

**Consequences (testable):**
- The plan is the durable, versioned inventory for every proprietary Hexalith module MCP server, MCP plug-in, and CLI, including EventStore Admin. Every row names the legacy operation, records `replace`, `withdraw`, or `defer`, gives the rationale, security class, replacement contract or unresolved gap, and owning maintainer's approval reference. First-increment Gateway-ready rows also name the decorated contract type and retain the existing `include`/`exclude` coverage field: `include` requires `replace`, while `exclude` requires an approved `withdraw` or `defer` disposition and cannot silently mean deletion. Stream/file transport remains deferred. Ordinary Payload search, filters, ordering and freshness follow AD-23 K03 with owner-defined handler semantics and independent evidence; advanced generic arguments deferred by FR-9 remain tracked gaps. Envelope-only paging remains AD-20.
- A coverage check compares every included row's canonical Operation Name and decorated type with the built Catalog and verifies approved withdrawals and deferrals. Missing, mismatched, duplicate or stale approved vectors fail; vectors cover each Operation Shape. Version differences and cataloged Operations no inventory row mentions are reported, never failed: decoration is the owner's consent to agent exposure. Inventories gate retirement, never configure runtime exposure or add CLR type names to public results. AD-23 K12 classifies the enrolled Parties T04 create, T05 update and T07 deactivate Commands as restricted. The Parties maintainer and McpCli product, architecture and security owners must reconcile inventory and exposure before claiming public eligibility or retirement. Verify the approved outcome through both Heads and demonstrate direct and chained denials with zero unauthorized effects.
- Task and actor context that Projects and ChatBot carry today travels as ordinary Payload properties, through `actorProperty`, or in allowed Envelope extensions, never in module-specific code here.
- FrontComposer's host and the Projects plug-in are deleted together; Memories, which fronts per-user JWT identity today, cannot retire before the HTTP release; that prerequisite is necessary but insufficient for its independent authorization, behavior, release and rollback gates.

Story 5.14 requires the product CI job to run the proprietary-surface census on the candidate’s committed direct submodule revisions. Owners review new and stale classifications. Unapproved surfaces, stale evidence and scan errors must fail the check. Record the hosted verdict against the candidate SHA. Stories 5.10 and 5.11 delivered the approved migration inventory updates. The owner-approved [AI.Tools plan 1.3.0](https://github.com/Hexalith/Hexalith.AI.Tools/blob/01e64857ab73bde74be137c675a8376c4da8cbee/hexalith-mcpcli-migration-instructions.md) is integrated. Story 5.11 still tracks release-note integration. [Migration status](../../../../docs/release/migration-status.md)

#### FR-22: Publish the no-new-server rule

The Hexalith agent instructions (`hexalith-llm-instructions.md` in Hexalith.AI.Tools) state that no new proprietary per-module MCP server, plug-in, or CLI is created; Hexalith.McpCli owns new Hexalith MCP/CLI presentation. Existing proprietary module MCP/CLI implementations are migration compatibility, limited to fixes needed for safety and continuity and listed in the migration plan. Gateway-ready agent Operations are declared in decorated Contracts; other capability classes follow adopted AD-23: confidential UI, explicit withdrawal, named retained local-tooling exemptions or deferral. Confidential UI, withdrawal and those exemptions need no invented McpCli extension; their independent owner and retirement gates remain binding.

**Consequence (testable):** the story closes only when the rule is merged into the authoritative Hexalith.AI.Tools instructions and this repository's `AGENTS.md` points to the merged baseline. Opening a pull request is progress evidence, not completion. Paired v1 publication is blocked until release evidence records the authoritative merge, a root-declared baseline reference containing it, byte-identical `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`, and a passing `scripts/check-agent-instructions-sync.sh`. This gate exempts the one-time Abstractions-only bootstrap.

## 6. Cross-cutting non-functional requirements

- **NFR-1 Startup.** On `ubuntu-latest`, the first `CatalogBuilder.Build` in a fresh process must take **500 ms or less**. Load every assembly in the restored production manifest (currently Tenants, Parties and Projects) plus exactly one synthetic `Ulid` sample before starting the clock. Tenants and Parties are the required v1 minimum. The measurement excludes process startup and top-level assembly loading. Cover the alternate Identifier Kind in isolation. `[ASSUMPTION: the 500 ms Catalog budget leaves enough time for client initialization.]`
- **NFR-2 Tool budget.** The five Generic Tool names, descriptions, and input schemas together stay under 8,000 characters, so the server fits a client's tool budget alongside other servers; a snapshot test measures that figure and, separately, the output schemas. `[ASSUMPTION: roughly 2,000 tokens; characters are tokenizer-independent.]`
- **NFR-3 Determinism.** See FR-5.
- **NFR-4 Channel discipline.** See FR-10; logs use source-generated `LoggerMessage` methods.
- **NFR-5 Secrets.** See FR-18.
- **NFR-6 Portability.** A .NET 11 global tool for Linux, Windows, and macOS with no native dependencies. The EventStore client package carries the Dapr SDK; its size is accepted unless the EventStore owner publishes a gateway-only client package.
- **NFR-7 Testability.** The executor is testable with a substituted Gateway client. Out-of-process parity tests drive both Heads through a reset loopback Gateway, while a blocking Aspire test runs each Module's approved live vectors (at least one per declared Operation kind) once against EventStore and asserts accepted Commands or returned Query documents plus semantic effects, not only status codes (spine AD-16). Story 5.13 requires a verifiable dependency audit and a passing full Linux lane on the candidate SHA, including every approved live vector and both independent cases. Windows and macOS product checks must pass on that SHA. Preflight counts identify cases to run. Story 5.20 requires Linux checks to reap their own descendants on timeout or refuse launch if safe supervision is unavailable.
- **NFR-8 Description quality.** Every exposed description is understandable by someone who has never seen the code, verified by review of the Catalog dump (SM-5); a lint rejects a description equal to the humanized type name (SM-C4).

## 7. Public surface and versioning

- **Surface.** Three artifacts: the Decoration Package `Hexalith.McpCli.Abstractions`, the tool package `Hexalith.McpCli` (CLI plus MCP Server, installed as the `hexalith` command), and the Generic Tool contract (five names, the addendum §E argument table, the addendum §G result documents, and the Operation Name form). Both packages share one version.
- **Breaking changes.** Renaming a Generic Tool, changing an argument, or changing the Operation Name form is a major version; adding an optional argument or result field is minor. A Contracts Library builds unchanged across minor versions of the Decoration Package. Operation Name, domain, and Wire Type stability is a Module obligation (§8.1); this tool's version cannot signal a Module-driven break.
- **Release order.** The Decoration Package is published from this repository before any upstream decoration begins; a Module version reaches agents when this tool bumps the pin and releases. `[ASSUMPTION: no automatic bump.]`
- **Paired release qualification (Story 5.15, backlog).** Operator acceptance and platform checks must identify the two final package archives by version, source SHA and individual hashes. Story 5.15 requires promotion to stop if either digest changes, the source differs or required acceptance is missing. The current workflow takes `delivered-sha`. McpCli and CiCd release owners must agree where to verify the final pair and rehearse that path without publication before claiming it qualified. CI fixture hashes cover only those fixtures. See NFR-7 for the Linux, Windows and macOS checks on the candidate commit. The 2.0.1 exception required Epic 3’s output-contract remediation before a later publication. That item closed on 2026-11-08. Each candidate still needs the package, operator and platform evidence above. [Epic 3 remediation](../../../implementation-artifacts/epic-3-retro-2026-10-16.md#f1-remediation-evidence--2026-11-08) · [Release restrictions](../../../../docs/release/migration-status.md)
- **Details.** Runtime targets and pinned packages are in addendum §B.

## 8. MVP scope

v1 is done when the tool is released and Tenants and Parties are covered end to end (FR-20). Each subsequent candidate must supply its own qualification evidence (§7).

### 8.1 In scope, in dependency order, with upstream prerequisites

1. Test fixture Contracts Library (§4) so every other story can close in this repository.
2. Decoration Package, published first (FR-1 to FR-4; the analyzer is a separable story).
3. Catalog (FR-5 to FR-8).
4. Query spike: `tenants.list-tenants` returns a page through the pinned client's query call from a throwaway harness, proving the `aggregateId` constant before the executor is built.
5. Executor and Read-only Mode (FR-15 to FR-17, FR-19).
6. MCP Server (FR-9 to FR-11) and CLI with Profiles (FR-12 to FR-14, FR-18).
7. Coverage, migration plan, and upstream rule (FR-20, FR-21, FR-22).

#### Gateway-ready checklist, common to every Module

1. Reference the Decoration Package.
2. Declare the marker with Module Name, description and Identifier Kind; declare `fixedTenant` only where the entire Module runs under one exact tenant, or per-Operation `platformScope` where appropriate, never both.
3. Decorate every agent-facing Command and Query.
4. Make every decorated type serialize completely from its own attributes or the marker's `serializerOptionsProvider`.
5. Publish the Contracts Library as a NuGet package and bump its version.
6. Have descriptions reviewed against NFR-8, with owning-maintainer approval recorded in the Module's pull request or a versioned McpCli evidence record. Under the single-maintainer model accepted in Epic 4 retrospective F11 on 2026-11-06, the requesting owner may provide that approval. Module approvals bind the inventory and vector hashes. The restore independently verifies the package archive against the NuGet content hash in `project.assets.json`.
7. Keep Operation Name, domain, and Wire Type stable, because renaming any of them silently breaks agents.
8. For a Module replacing a Legacy Server or Frozen CLI, version and approve its FR-21 operation inventory and pass the inventory-to-Catalog coverage check.
9. Version and approve conformance vectors that cover every Operation Shape the Module uses, with at least one live vector per declared Operation kind; test each Operation's handler semantics in the Module repository; pass the generic shape-coverage and live gates (FR-20). Decorate only Operations you consent to expose to agents without human confirmation (FR-1).

Work is tracked in each Module's own repository.

#### Module enrollment on 2026-11-20

The original v1 scope requires Tenants and Parties. The production manifest now also includes Projects. Counts below describe offline discovery. Live acceptance follows FR-20. [Production manifest and cohort](../../../../README.md#gateway-boundary)

| Module | Contracts pin | Operations | Remaining qualification or migration gate |
|---|---|---:|---|
| Tenants | 8.0.2 | 15 | `refresh-tenant-access` shares an approved Operation Shape. Its own downstream repair effect still needs owner evidence. |
| Parties | 4.0.0 | 7 | Four Commands and three Queries are enrolled. G01–G06 and the FR-21 decision on T04/T05/T07 still gate retirement. |
| Projects | 2.0.0 | 4 | Four Queries are enrolled. Native populated reads, paging and denial evidence remain open under DW-82. |
| Folders | Unenrolled | — | Epic 6 requires an eligible published Contracts package and a server-free composition helper. K12 and the inventory gate removal. |

#### Module-specific prerequisites

- **Tenants.** `identifierKind = String`, no `fixedTenant`; Commands and cross-tenant reads declare `platform:tenants`, while single-tenant reads use the selected public tenant and matching managed-tenant aggregate identifier; descriptions and examples; `aggregateIdProperty` on per-tenant Queries and an `aggregateId` constant on list Queries (`list-tenants`, `get-user-tenants`), value chosen by the maintainer within the Gateway pattern; migrate exposed paged handlers to `QueryEnvelope.Paging` and align audit filters with the declared serialized `From`, `To`, and `Category` fields before Gateway-ready acceptance; prove filtering and non-default paging/continuation through AD-16 live vectors; drop legacy `Cursor` and `PageSize` Payload members or retain them with lint warnings only for other clients, never as the source of generic paging; do not decorate the global-administrator Commands in v1.
- **Parties.** The maintainer approved domain `party`, attribute routing, full CLR Command Wire Types, String identifiers and root `PartyId` in the [A1 inventory decision](../../../implementation-artifacts/parties-migration-inventory-v1.md#a1-session-approval-2026-10-16). FR-20 checks the seven included targets. Retain an approved disposition for every excluded legacy operation and the independent FR-21 retirement gates.
- **Projects.** The 2.0.0 Contracts package removed the web/UI closure that excluded 1.0.0. Its four Queries use the shared executor. Story 5.21 owns the qualification criteria in FR-20 and addendum §H. Projects contributes to SM-1.
- **Folders.** The maintainer must publish decorated Contracts for the agent-eligible inventory and provide a server-free helper for live tests. Prove the approved dry-run, redaction, freshness and authorization behavior, and keep restricted or mixed K12 operations out of the public surface pending the owner decision. Folders contributes to SM-1. See addendum §H and Epic 6.

### 8.2 Out of scope for MVP

- **Shared HTTP transport** is the planned next release. AD-23 K10 defers hosted per-user authority until the design meets Platform AD-14. Downstream calls must use token exchange with an approved issuer, audience and client mapping. Forwarding the inbound bearer token is prohibited. For synchronous calls, bind the actor to the authenticated token subject. For asynchronous steps, use the attested original actor. Attest the call chain’s effective origin in both cases. The Gateway must authorize the selected tenant, scope, surface and permission. Caller-supplied identity headers grant no authority. OQ-1 requires denial evidence on the selected environment. [AD-23 K10](../../architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md)
- Legacy Server and Frozen CLI deletions: after the first increment, per Module, per FR-21 and the approved successor migration epic.
- Query correlation identifier and extensions: the pinned client's query request cannot carry them (FR-16); revisit when the client does.
- Dedicated generic Query arguments for search, filters, order-by, freshness and entity scoping beyond `entityId` remain deferred. Supported Module Payload and handler semantics still require FR-21 evidence. Gateway Command status lookup is also deferred. The result includes the message identifier for tracing.
- Parked, not scheduled: typed tools behind a module filter (SM-C2 forbids chasing them in v1), generated per-Operation subcommands, shell completion, plug-in loading of Contracts Libraries, event stream reading, MCP resources and prompts, executor retries.

### 8.3 Non-goals (explicit)

- EventStore infrastructure administration is outside the first increment, but its Admin CLI/MCP are in the mandatory successor migration scope; §2.2 defines the cutover prerequisite.
- Operating an OAuth or identity server is outside v1 and the next release. The hosted transport relies on the platform for token exchange (§8.2).
- Not a second executor: the tool never calls a Module's REST or Dapr API. Modules that expose Operations only that way are not covered until Gateway-ready.

## 9. Success metrics

Checked three months after v1 ships.

**Primary**
- **SM-1 Zero module-specific code.** Meet this target when Tenants, Parties, Projects and Folders all pass FR-20 through the shared Catalog and executor. Projects still needs native read qualification under DW-82. Folders still needs enrollment (§8.1). Validates FR-5, FR-20.
- **SM-2 Cross-module task.** An agent completes a task spanning two Modules with Operations authorized for that agent on the selected environment (UJ-1), using only the Generic Tools, with no per-module prompt or tool. Validates FR-9, FR-15 to FR-17.
- **SM-3 First deletion.** Delete at least one Legacy Server by 2027-02-05, three months after the first paired release. The recorded owner choice was “Labels + slip”. The 2026-11-16 assessment records zero evidenced retirements across PS01–PS14. SM-3 remains pending. Validates FR-21. [Retirement gates by surface](../../../../docs/release/migration-status.md)
- **SM-4 Heads agree.** For every approved vector, together covering every Operation Shape, tests run both out-of-process Heads with identical inputs against one reset loopback Gateway response script and obtain identical Catalog data, error documents, canonical result documents, and captured Gateway requests after masking only generated message and correlation identifiers. Captured method, path, routing, Envelope, Payload, and paging match each other and the vector's expected inputs. Caller-supplied `idempotencyKey` is equal and present in both results when supplied and omitted by both when absent. The separate FR-20 live lane executes each approved live vector once against EventStore and checks its semantic outcome. Validates FR-5, FR-11, FR-12, FR-20.

**Secondary**
- **SM-5 Description quality.** Every description passes a reviewer who has never seen the code, recorded with owning-maintainer approval in the Module's pull request or versioned McpCli evidence under the §8.1 checklist and the accepted F11 single-maintainer model. Validates FR-1, NFR-8.
- **SM-6 Time to first action.** A new operator reaches a successful `send_command` within 15 minutes using only the README, measured in a timed session recorded in the release checklist. `[ASSUMPTION: 15 minutes is a target, not a measured baseline.]` Validates FR-13, FR-18.
- **SM-7 First-party adoption.** At least one of Agents, ChatBot, or Conversations reaches business data through the Generic Tools. Validates the §1 bet.

**Counter-metrics (do not optimize)**
- **SM-C1 No new per-module server or CLI** after 2026-09-21. Counterbalances SM-3.
- **SM-C2 Five tools in v1.** Do not chase SM-2 by adding typed tools.
- **SM-C3 No dependency creep.** Coverage gained by referencing a Module's server or client project, or by widening the §4 allowlist without a PRD change, is a failure. Counterbalances SM-1.
- **SM-C4 No hollow descriptions.** A description equal to the humanized type name counts against SM-5.

## 10. Handoff and open questions

Numbering is stable so downstream references stay valid.

### 10.1 Handoff to architecture

The earlier AD-7/9/11/15/19 handoff is complete and recorded in `verify-update-2026-09-22.md`. The architecture spine at `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md` binds these decisions at their implementation gates:

- Before the fixture story: keep one declared synthetic Module and construct the other Identifier Kind in isolation.
- Before the dependency-closure test or Module pins: AD-15 distinguishes the Decoration Package from the external dependency allowlist.
- Before Schema and Catalog implementation: AD-6/7 preserve Module serializer casing, and AD-8 preserves an unmarked `*Id` property's serializer-derived Schema with lint only.
- Before settings resolution: AD-13 requires a URL only when execution reaches the Gateway.
- Before executor implementation: AD-9 and the identifier-generation convention use caller-supplied idempotency keys only, expose no generic retry or duplicate promise, resolve omitted command correlation to the generated message identifier, and preserve the actual status on every `EventStoreGatewayException`, including malformed-success `2xx` responses.
- Before either Head or its output schemas: AD-5/12 conform to the exhaustive addendum §G records, including lint findings and member types and constraints; the channel convention applies the pre-request-serving MCP stderr/empty-stdout rule to every startup failure.
- Before Catalog public-contract implementation: AD-3/5 return `unknown_module` for a non-empty `list_operations` lookup miss, using the exhaustive addendum §G variant.
- Before the v1 release gate: AD-16 runs every approved Module vector through both Heads against reset loopback Gateway scripts for parity and runs the subset with approved companion plans once against EventStore for semantics (at least one per declared Operation kind). AD-21 separately verifies the approved Legacy Server and Frozen CLI inventory against the Catalog. The blocking CI tier uses the approved Parties Aspire helper and the selected native runtime for that candidate.

### 10.2 Open

1. **HTTP authentication design.** Architecture owns the issuer, audience and client mapping, token exchange and actor/effective-origin attestation design. Before the HTTP story can qualify, document that design and prove on the selected environment that requests with invalid authority or an unauthorized origin are denied. The McpCli product owner approves K10 closure (§8.2).
6. **Deletion order.** The product owner revisits the order when a surface meets its inventory, authorization, behavior and cutover gates. Parties remains blocked. SM-3 retains its 2027-02-05 deadline.

### 10.3 Resolved

2. **Module layout.** Resolved by the architecture spine (2026-09-22): flat layout `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*.Tests` like the sibling Modules (addendum §B).
3. **Aggregate-less Queries.** Resolved from source (2026-09-22): the Gateway's query validator rejects an empty aggregate identifier, and sibling clients send a per-Query constant (Parties `parties`); hence the `aggregateId` attribute member (§5.1, FR-16) and the §8.1 query spike.
4. **Analyzer feasibility.** Resolved by the architecture spine (2026-09-22): the analyzer is a separate project packed into the Decoration Package, so a Module author needs one reference; it is a separable story and the package may ship before it (FR-1).
5. **Parties routing choice.** The Parties owner retained full CLR Command Wire Types and attribute routing under A1 (§8.1).
7. **Package identifiers and CLI command name.** Resolved by the architecture spine (2026-09-22): command `hexalith`; packages `Hexalith.McpCli` (tool) and `Hexalith.McpCli.Abstractions` (Decoration Package), one shared version (§7).
8. **Original v1 decoration schedule.** The first paired release shipped on 2026-11-05. Section 8.1 records current Contracts pins. New candidates still need their own qualification.
9. **Gateway deduplication.** Resolved from the pinned EventStore source (2026-09-22): logical retry safety is conditional on a trusted adapter registered per Command type, and `SubmitCommandResponse` has no replay/duplicate classification. v1 therefore passes through only caller-supplied keys, never retries, and exposes no generic safe-retry or `duplicate` promise (UJ-1, FR-16, FR-17).

## 11. Assumptions index

Each inline `[ASSUMPTION]` tag carries its own rationale; this table is the confirmation checklist.

| Location | Assumption | Who confirms |
|---|---|---|
| FR-13 | JSON is the right default format for an agent-first tool | Product owner |
| FR-13 | The tool must not read the admin CLI's environment variables | Product owner |
| FR-16 | In v1 the operator states the Actor in the Profile; the tool never decodes the token | Product owner, architecture |
| FR-18 | Shell completion is deferred | Product owner |
| NFR-1 | The 500 ms Catalog budget leaves enough time for client initialization | Architecture, when client timeout evidence or the enrolled manifest changes |
| NFR-2 | 8,000 characters is roughly 2,000 tokens | Architecture, by snapshot test |
| §7 | No automatic pin bump when a Module publishes | Product owner |
| SM-6 | 15 minutes is a target, not a baseline | Product owner |

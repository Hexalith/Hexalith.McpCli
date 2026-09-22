---
title: Hexalith.McpCli PRD
status: final
created: 2026-09-21
updated: 2026-09-22
---

# PRD: Hexalith.McpCli
*Working title. The repository is `mcpcli`; the module name follows the sibling-module convention.*

## 0. Document purpose

This PRD is for the Hexalith maintainers and for the workflows that follow it: architecture, epics and stories, and the migration plan for the legacy per-module MCP servers. It builds on the product brief at `_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/` and does not restate its research. Rejected alternatives, transport mechanics, and comparables live in `addendum.md` next to this file; its §E argument table and §G result documents are normative, and FR-9, FR-11, and FR-12 are specified against them. Guardrails live in §4, attribute and marker members in §5.1, and behavior in the owning FR; the Glossary and §4 summarize and point to those owners. Unconfirmed inferences carry an inline `[ASSUMPTION]` tag and are indexed in §11.

## 1. Vision

Hexalith.McpCli replaces the six Legacy Server packages with one generic MCP Server and one thin CLI, both driven by a single Catalog. A Module declares each Operation once, in its Contracts Library, with a Decoration Attribute that carries what the agent needs and the contract cannot express: a description a stranger can understand, an example, and routing fallbacks. The Catalog discovers those declarations at startup and describes them to the agent; the shared executor validates each Payload, fills the Envelope, and submits through the Gateway. The repository contains zero module-specific code; adding a Module is a package reference and a rebuild.

The goal is that a human can do any operation in Hexalith through an LLM agent, and that an agent is a peer of the Hexalith user interface rather than a second-class client bolted onto each Module. Hexalith is a CQRS platform in which every business action is a Command and every read is a Query, and the target state is that all of them travel through one EventStore Gateway. Today that uniformity is hidden:

- each Legacy Server has its own transport, tool naming, description mechanism, and authentication story;
- only one of them reaches the Gateway;
- descriptions live in XML documentation comments that do not exist at runtime, so every server redescribes its operations by hand and drifts from the code.

There is no triggering incident; the bet is that the Agents, ChatBot, and Conversations Modules will soon need to act on business data across Modules, and that six dialects will not survive that contact.

Two consequences follow now. Identity forwarding becomes essential, which is why the HTTP transport is the next release rather than a distant one. And a Command without a description is a Command an agent cannot use, so the Decoration Attribute stops being decoration and becomes part of what it means for a Hexalith Operation to exist: every Module that ships after 2026-09-21 ships agent-ready, or is not finished (FR-22).

**Status (2026-09-22).** v1 is blocked on upstream decoration of Tenants and Parties; dates are open (OQ-8) and there is no scope fallback (§8). The HTTP transport is the only committed next release and is load-bearing for per-user identity (§8.2). The migration plan is a v1 deliverable (FR-21). Folders is the largest prerequisite; it gates SM-1, not v1. The architecture spine needs the amendments listed in §10.1 before the executor epic.

## 2. Target user

### 2.1 Jobs to be done

- **Agent operator** (a developer with a dev or test EventStore). Install one .NET tool, point a Profile at the Gateway, and have an MCP-capable agent list, describe, and run every decorated Operation across Modules. Success is a cross-module task with no per-module setup.
- **LLM agent session** (Claude Code, Claude Desktop, VS Code, and the Agents, ChatBot, and Conversations Modules). Discover what Hexalith can do, understand each Operation from description and Schema alone, act, and get errors it can reason about.
- **Module author.** Make a Module visible to every agent on the day it ships by decorating its Contracts Library, and never write an MCP server again.
- **Shell user or CI script.** Call the same Catalog and Operations from a terminal with JSON on stdout, so a script and an agent cannot disagree about what Hexalith can do.

### 2.2 Non-users and the admin-plane boundary (v1)

Non-users: EventStore infrastructure administrators (streams, subscriptions, and clusters stay with `Hexalith.EventStore.Admin.Cli` and `.Admin.Mcp`), end users of Hexalith web applications, and anyone who needs per-user identity across a shared hosted server (the HTTP release, §8.2). Business administration modeled as Commands and Queries is in scope even when it needs a platform-administrator token, as every Tenants Operation does (FR-3): the boundary is the Gateway, not the token.

### 2.3 Key user journeys

- **UJ-1. Nadia wires her agent to a test EventStore and runs a two-module task.** Nadia, a Hexalith developer, installs the tool, creates a Profile with the Gateway URL, a token, and the default Tenant `acme`, and adds the stdio server to Claude Code. She asks the agent to check who belongs to `acme` and then create a party for the newest member. The agent walks the discovery sequence (`list_modules`, `list_operations`, `describe_operation`), then calls `run_query` on `tenants.get-tenant-users` (whose description says the Envelope Tenant is fixed to `system`, so the agent passes none) and `send_command` on `parties.create-party` under `acme`. Both results carry identifiers she can trace: the Command result carries its message identifier and idempotency key. **Edge case:** the second call times out before any result document arrives; because the agent supplied its own idempotency key on the first attempt, it retries with the same key. `[ASSUMPTION: the Gateway deduplicates on the idempotency key and the result says whether it did; OQ-9 asks the EventStore owner.]`
- **UJ-2. An agent session explores a Module it has never seen.** The Conversations Module's agent is asked about tenant membership. It follows the same discovery sequence for `tenants`, sees each Operation with its kind and description, picks `tenants.get-tenant-users`, reads its Schema and example, and calls `run_query`. The result comes back paged with a cursor. Nobody wrote a tenants-specific prompt or tool. **Edge case:** the session runs in Read-only Mode; `send_command` is absent from its tool list, so it reports that it can look but not act.
- **UJ-3. Marc adds a Module and it appears everywhere.** Marc maintains Projects. Once `Hexalith.Projects.Contracts` satisfies the dependency allowlist (§4), he adds the Decoration Package, decorates each Command and Query with a description, example, and Routing Values, marks the assembly as a Module, and publishes the package. This repository bumps the package reference and rebuilds. Every agent and every script now sees `projects.*` Operations with no change here. **Edge case:** one record lacks a description; the Catalog excludes it and reports it on stderr at startup, so the gap is visible, not silent.

## 3. Glossary

Downstream readers and workflows use these terms exactly. Terms owned by a requirement point to it.

**Declaration**

- **Module** — a Hexalith domain module. Identified in the Catalog by its **Module Name**, a lowercase kebab-case string declared on its Contracts Library assembly.
- **Contracts Library** — the `*.Contracts` NuGet package of a Module holding its Command and Query type definitions. The only Module artifact this product references, under the dependency allowlist (§4).
- **Operation** — a Command or a Query. A class or record decorated with a Decoration Attribute. Each has exactly one Operation Name.
- **Command** — an Operation that writes to one aggregate through the Gateway. Kind `write`.
- **Query** — an Operation that reads from a projection through the Gateway. Kind `read`.
- **Operation Name** — the canonical identifier of an Operation, `<module-name>.<operation>` in kebab-case, for example `parties.create-party`. Identical in both Heads and independent of the Wire Type.
- **Wire Type** — the operation type string the Gateway dispatches on (today `create-tenant` for Tenants; a full CLR type name for Parties Commands, Parties having no Query types yet). One of the Routing Values, never shown as the Operation Name.
- **Routing Values** — domain, Wire Type, the aggregate identifier source (a Payload property, the contract getter, or a constant), and, for Queries, the projection type and (when the Module serves its projection through a named actor) the projection actor type. Supplied by the EventStore contract interfaces when implemented, else by the Decoration Attribute.
- **Decoration Attribute** — the command or query attribute applied to an Operation type; members in §5.1.
- **Module marker** — the assembly attribute declaring a Module; members in §5.1.
- **Decoration Package** — the dependency-free NuGet package `Hexalith.McpCli.Abstractions`, built here, holding the Decoration Attributes, the identifier attribute, the Module marker, and the bundled analyzer (FR-1).
- **Identifier** — a Payload property marked with the identifier attribute or named by `aggregateIdProperty` (FR-7). Never inferred from a name suffix. Typed and validated by its Module's Identifier Kind.
- **Identifier Kind** — `Ulid` or `String`, declared once per Module on the Module marker (FR-3). Governs the Schema and validation of every Identifier in that Module (FR-7, FR-15). Envelope identifiers the tool generates or the caller supplies (message identifier, idempotency key, correlation identifier) are always ULIDs regardless of that kind.

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
- **Tenant** — the tenant identifier placed in the Envelope. Resolved per FR-16 from the Module's fixed tenant, the session settings (flag, environment variable, Profile; next release a forwarded header), or, under the FR-16 gate, a per-call MCP argument. Never read from the Payload.
- **Actor** — the principal recorded as the author of a Command when its Operation names an `actorProperty`. Resolved from a flag, an environment variable, or a Profile, never per call; next release from the forwarded user header (FR-16).
- **Profile** — a named connection configuration in `~/.eventstore/mcpcli.json` (FR-18).
- **Read-only Mode** — a startup option under which write submission is refused and `send_command` is not advertised; discovery is unchanged (FR-19).

**Migration**

- **Legacy Server** — one of the six per-module MCP packages this product replaces, listed in addendum §D: the standalone servers of Parties, Folders, ChatBot, and Memories; the FrontComposer descriptor-driven host; and the Projects plug-in it hosts (FR-21).
- **Frozen CLI** — one of the five existing per-module agent CLIs (Folders, Projects, ChatBot, FrontComposer, and Memories), frozen to bug fixes by FR-22 and inventoried by FR-21.
- **Gateway-ready** — the state of a Module whose agent-facing Operations exist as decorated Command and Query types in a published Contracts Library and are accepted by the Gateway (checklist in §8.1).

## 4. Constraints and guardrails

Each rule below is authoritative; FRs reference them rather than restate them.

- **Dependency allowlist.** The tool package references exactly: the EventStore client package; `*.Contracts` packages of the Modules being exposed; and the transitive closure of `Hexalith.EventStore.Contracts` at the pinned version, today `Hexalith.Commons.UniqueIds` and `ByteAether.Ulid`. A Contracts Library is referenced only when its own transitive closure stays inside that allowlist and adds no framework reference beyond `Microsoft.NETCore.App`; a CI test over the restored dependency graph enforces it (FR-20). Adding a package to the allowlist is a PRD change. The tool package never references an aggregate, projection, handler, client, or server project of any Module. Test projects may add the EventStore testing and Aspire composition packages the architecture names, plus one synthetic sample Contracts Library (the sample Module) never referenced by the tool package.
- **Zero module-specific code.** No type, branch, or configuration in this repository names a Module.
- **Tenant.** Envelope-only, resolved by the executor (FR-16); never read from the Payload; a per-call MCP argument is honored only under the FR-16 gate.
- **Identity in v1.** The stdio server acts as whoever owns the configured token; the audit trail says "the tool", not the human. The Actor an Operation records is an operator setting (Profile, flag, environment), never chosen by the agent per call, and the extension keys a call may carry are limited to an operator allowlist (FR-16, FR-18). Accepted for dev and test use, and the reason the HTTP transport is the next release.
- **Identifiers.** Envelope identifiers, generated or caller-supplied, are ULIDs validated with `Ulid.TryParse`, never `Guid.TryParse` (FR-16). Payload Identifiers and the aggregate identifier are typed by explicit marking and validated by the Module's Identifier Kind, never guessed from a name (FR-3, FR-7, FR-15). The Tenant is a non-empty string and is never ULID-validated. Every Envelope field is pre-validated against the Gateway's published patterns before submission (FR-15).
- **Idempotency.** One generated message identifier per call; one idempotency key per call, caller-supplied or generated and returned in the result; the tool never retries (FR-16, FR-17).
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
| `projectionType` | query | no `IQueryContract` | Projection the Query reads |
| `projectionActorType` | query | optional; only when the Module serves the projection through a named actor | Projection actor type for the Envelope; the interface does not carry it |
| `tenantProperty` | both | record declares a tenant member | Payload property the executor fills from the Envelope Tenant; never the aggregate identifier source |
| `correlationProperty` | both | record declares one | Payload property filled from the Envelope correlation identifier |
| `idempotencyKeyProperty` | command | record declares one | Payload property filled from the Envelope idempotency key |
| `actorProperty` | command | record declares an actor or principal member | Payload property filled from the resolved Actor (FR-16) |

**Module marker members**

| Member | Required | Meaning |
|---|---|---|
| `name` | always | Module Name |
| `description` | always | One line for `list_modules` |
| `identifierKind` | always | `Ulid` or `String` (FR-3) |
| `fixedTenant` | optional | Envelope Tenant every Operation of the Module runs under (Tenants: `system`); surfaced by `describe_operation`, applied by FR-16 |
| `wireTypeConvention` | optional, default `Explicit` | How the Catalog derives a Wire Type when the attribute gives none: `Explicit` (none derived), `FullTypeName` (the CLR full type name, namespace included, not assembly-qualified), or `KebabCase` (the FR-8 name part) |
| `serializerOptionsProvider` | optional | Static member of a type in the Contracts Library returning the `JsonSerializerOptions` the Module's converters need; for that Module's Payload types its converters take precedence over the tool's canonical options in Schema derivation and Payload handling (FR-7); the Envelope is always serialized with the tool's options |

#### FR-1: Mark a type as a Command or a Query

A Module author can apply the command or query Decoration Attribute to a class or record in a Contracts Library with a required description and the members above.

**Consequences (testable):**
- A type with the command attribute enters the Catalog with kind `write`; with the query attribute, kind `read`.
- An empty or whitespace description is a build warning from a bundled analyzer and always a startup diagnostic that excludes the type (FR-6). The analyzer is a separate project packed into the Decoration Package and a separable story, and the package may ship before it exists; startup exclusion is the guaranteed behavior (OQ-4, resolved).
- An example that does not validate against the Schema is a startup diagnostic.
- The Decoration Package has no package references visible to a consumer; the analyzer's own dependencies are private assets.

#### FR-2: Resolve Routing Values per field

For each Routing Value, the Catalog uses the contract interface when the interface defines that field, else the attribute member, else the marker's `wireTypeConvention` for the Wire Type.

**Consequences (testable):**
- A Tenants Command implementing `ICommandContract` needs no `domain`, `wireType`, or `aggregateIdProperty`; a Tenants Query implementing `IQueryContract` needs no `domain`, `wireType`, or `projectionType`. `IQueryContract` carries no aggregate identifier, so a Query declares `aggregateIdProperty` (per-tenant reads) or `aggregateId` (list reads); a Query with neither stays in the Catalog and `describe_operation` reports `aggregateIdRequired: true`, meaning the explicit argument is mandatory (FR-16).
- A Parties Command with no interface and no attribute routing members is excluded with a diagnostic naming the missing members; with `wireTypeConvention = FullTypeName` on the marker, only `domain` and `aggregateIdProperty` are needed.
- An attribute value equal to the interface or convention value is a redundant-value warning. One that differs from an interface value is a conflicting-value warning and the interface value is used; one that differs from a convention-derived value is used as given, since the convention is only a fallback.
- Domain is a per-Operation value and may differ within one Module (Tenants routes its global-administrator Commands, which v1 does not decorate, to a second domain).

#### FR-3: Declare a Module

A Module author can mark a Contracts Library assembly with the Module marker (members in §5.1).

**Consequences (testable):**
- The Catalog scans only assemblies carrying the marker; an undecorated assembly is invisible and produces no diagnostic (FR-20 distinguishes it from a marked assembly with no Operations).
- The Identifier Kind applies to every Identifier of the Module (FR-7, FR-15). Both v1 Modules declare `String`: Tenants because its aggregate identifiers are managed tenant names such as `acme`; Parties because it has not adopted ULIDs. The `Ulid` kind has no v1 consumer.
- A `fixedTenant` is the Envelope Tenant of every Operation in the Module (FR-16). Tenants declares `system`, because its Gateway validators reject any other tenant and expect the managed tenant in the aggregate identifier.

#### FR-4: Describe properties

Every property carrying `System.ComponentModel.Description` gets a `description` in the Schema, and `describe --lint` on the CLI reports the property-level gaps of one Operation.

**Consequences (testable):**
- `describe --lint` lists undescribed properties; unmarked identifier-like properties (FR-7); and Payload paging members named `PageSize`, `Offset`, or `Cursor` (paging travels only as `run_query` arguments, FR-16). It exits 1 if any exist.
- These property-level findings are lint-only: they never appear as Catalog diagnostics (FR-6).

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
| `missing_routing_values` | error, type excluded | A Routing Value with no interface, attribute, or convention source (FR-2) |
| `invalid_routing_value` | error, type excluded | A domain, Wire Type, projection type, or `aggregateId` constant outside the Gateway patterns (FR-15) |
| `duplicate_operation_name` | error, later type excluded | Two types resolve to one Operation Name (FR-8) |
| `invalid_example` | error, type excluded | Example does not validate against the Schema (FR-1) |
| `invalid_identifier_type` | error, type excluded | An Identifier that does not serialize as a JSON string (FR-7) |
| `tenant_is_aggregate_id` | error, type excluded | `tenantProperty` names the aggregate identifier source. On Tenants, `TenantId` is the aggregate identifier, not the tenant |
| `ambiguous_aggregate_id` | error, type excluded | Both `aggregateId` and `aggregateIdProperty` set |
| `duplicate_module` | error, later assembly excluded | Two assemblies declare one Module Name |
| `conflicting_value` | warning, kept | Attribute value differs from the interface value (FR-2) |
| `redundant_value` | warning, kept | Attribute value equals the interface or convention value (FR-2) |
| `empty_module` | warning, kept | A marked assembly exposes zero Operations (FR-20) |

- Scan order is deterministic: assemblies in the generated list order (sorted by assembly name), types within an assembly by ordinal full type name; the first declaration of a duplicate Module Name or Operation Name survives.
- An empty Catalog fails only the verbs that need it (the discovery verbs, `send`, `query`, and `mcp`) with exit 2 and `code: catalog_empty`; `config` and `--version` never build the Catalog and always run (FR-14).

#### FR-7: Derive a JSON Schema per Operation

The Catalog derives from the Operation type a Schema that includes every settable or constructor-bound property and rejects unknown properties.

**Consequences (testable):**
- Required, nullable, enum, nested type, and collection members map to the corresponding JSON Schema constructs; `additionalProperties` is `false`. Get-only members with neither a setter nor a constructor parameter (such as `ICommandContract.AggregateId`) are not Schema properties; the executor reads them through the accessor (FR-16).
- An Identifier is a property marked with the identifier attribute or named by `aggregateIdProperty`; it is typed `string`, with the ULID pattern when the Module's Identifier Kind is `Ulid`, and never with `format: uuid`. A property whose CLR type is `ByteAether.Ulid.Ulid`, recognized by full name so the Decoration Package needs no reference to it, gets the pattern regardless of the kind.
- An Identifier's CLR type must serialize as a JSON string; a value-object identifier serializes as its own declared converter or the marker's `serializerOptionsProvider` dictates, and the tool adds no converter. An Identifier that does not serialize as a string excludes the Operation with an `invalid_identifier_type` diagnostic (FR-6).
- An unmarked property whose name ends in `Id` is a plain string in the Schema and a `describe --lint` warning (FR-4); the name suffix never types a property.
- Properties named by `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty`, or `actorProperty` are marked `readOnly`, removed from `required`, and filled by the executor (FR-16); a caller may omit them.

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
- `tools/list` returns exactly five tools, or four without `send_command` in Read-only Mode.
- `list_modules` returns each Module Name with its description and Operation count; `list_operations` takes a Module Name and an optional kind and returns Operation Name, kind, description; `describe_operation` returns description, kind, Schema, example, the Envelope arguments the caller may supply (whether `aggregateId` is required, the Module's fixed tenant if any), and `submittable`, with a reason when it is false.
- Each tool description has three labeled parts: `Purpose`, `Use when`, and `Next`.
- The three discovery tools and `run_query` carry `readOnlyHint: true`; `send_command` carries `readOnlyHint: false` and `idempotentHint: false`.

**Out of scope for v1:** search, filters, order-by, and freshness arguments on `run_query`; deferred (§8.2) and excluded from the parity bar (FR-21).

#### FR-10: Serve over stdio with clean channels

The MCP Server runs as a local process over stdio; stdout carries JSON-RPC only and all logging goes to stderr.

**Consequences (testable):**
- A test that drives the server with the ModelContextProtocol client SDK over stdio completes initialize, `tools/list`, and one call of each tool without a parse error; Claude Code, Claude Desktop, and VS Code are a release-checklist item.
- The server starts from a Profile or environment variables with no interactive prompt.

#### FR-11: Return structured results and errors

Every tool returns structured content with a declared output schema; failures return a structured error, never a stack trace. Both Heads serialize the same result and error record types (addendum §G).

**Consequences (testable):**
- Validation failure: `code: validation_failed`, the Operation Name, and one entry per violation with JSON path and message; a Payload that is not JSON is one violation.
- Gateway failure: `code: gateway_error` with status, reason code, detail, retryable flag, retry-after, client action, and correlation identifier, mapped from the client's exception.
- Unknown Operation Name: `code: unknown_operation` and up to three nearest Operation Names by case-insensitive edit distance.
- Any other exception: `code: internal_error` with a message, never a stack trace.

### 5.4 CLI

**Description:** The CLI is a thin companion over the same Catalog and executor. It proves the Catalog without MCP, lets a script do anything an agent can, and hosts the MCP Server through the `mcp` verb (the brief called it `serve`; renamed so the verb names the protocol). Realizes UJ-1, UJ-3.

#### FR-12: Expose the matching verbs

A shell user can run `modules`, `operations <module> [--kind]`, `describe <operation> [--lint]`, `send <operation>`, `query <operation>`, `mcp`, and `config`.

**Consequences (testable):**
- Every argument in the addendum §E table exists in both Heads under the spelling given there.
- `send` and `query` accept the Payload as `--payload <json>`, `--payload @file`, or stdin.
- `mcp` starts the MCP Server over stdio; `mcp --transport http` exits 2 with `code: unsupported_transport` and a message naming the release in which it arrives, before building the Catalog.
- `--format table` renders `modules`, `operations`, and `config`; on `describe`, `send`, and `query` the output is JSON with one stderr note, and the exit code is unaffected.

#### FR-13: Resolve global options in one order

Every verb accepts `--url`, `--token`, `--tenant`, `--actor`, `--allow-tenant-override`, `--profile`, `--format json|table`, `--output <file>`, `--read-only`, and `--strict`. `--profile` resolves first (flag, environment variable, then the active Profile); every other option then resolves in the order flag, environment variable, selected Profile, default, using the sources addendum §E lists for it. These are session settings; the CLI has no per-call tenant. Only the MCP tools carry a per-call `tenant` argument, governed by FR-16.

**Consequences (testable):**
- The order is testable per option with a fixture that sets every source.
- Defaults differ from the admin CLI: `json` is the default format, and the URL has no default, so a missing URL is `configuration_invalid`, exit 2, rather than a silent fallback to the admin API. `[ASSUMPTION: a tool whose primary reader is an agent defaults to JSON.]`
- Environment variable names are in addendum §E; they use the `EVENTSTORE_` prefix without `ADMIN`. `[ASSUMPTION: this tool is not the admin plane, so it must not read the admin CLI's variables.]`
- Boolean options (`--read-only`, `--strict`, `--allow-tenant-override`) accept `true`, `false`, `1`, and `0` from the environment; anything else is `configuration_invalid`, exit 2.

#### FR-14: Use one exit-code contract

Every CLI invocation ends with one of three exit codes, and the code depends only on the invocation's own outcome.

**Consequences (testable):**

| Exit | Meaning | Stdout |
|---|---|---|
| 0 | Result document produced | result |
| 1 | Result document produced by `describe --lint` and at least one lint finding listed (FR-4) | result |
| 2 | No result document: validation failure, Gateway rejection, read-only refusal, unsupported transport, unsupported format, invalid configuration, empty Catalog, `--strict` diagnostic | structured error (FR-11) |

- Catalog diagnostics go to stderr and never move an invocation between rows; only `--strict` turns them into row 2 (FR-6).

### 5.5 Execution, Envelope, and Read-only Mode

**Description:** Both Heads share one executor. It validates the Payload, fills the Envelope, submits through the Gateway client, maps the response, and enforces Read-only Mode. Nothing module-specific lives here. Realizes UJ-1, UJ-2.

#### FR-15: Validate before submitting

The executor validates every Payload against the Schema and refuses to submit an invalid one; all violations are reported together. It also pre-validates every Envelope field against the Gateway's published rules, so a Gateway 400 is never the first signal of a tool-side mistake.

**Consequences (testable):**
- An invalid Payload never reaches the Gateway; the substituted Gateway client records zero calls.
- The explicit aggregate identifier argument and the resolved aggregate identifier are checked by the Module's Identifier Kind: `Ulid.TryParse` for `Ulid`, non-empty for `String` (FR-3).
- Per call, the Tenant matches the Gateway's lowercase alphanumeric-and-hyphen pattern of at most 64 characters; the aggregate and entity identifiers match its alphanumeric, dot, hyphen, and underscore pattern of at most 256 characters with no colon; extension keys are in the Profile's allowlist (FR-16). Each failure is a `validation_failed` entry at `/tenant`, `/aggregateId`, `/entityId`, or `/extensions/<key>`. Routing Values are checked against the same patterns once, at Catalog build (FR-6).

#### FR-16: Fill the Envelope

The executor generates a message identifier per call, uses the caller's idempotency key or generates one, resolves the Tenant, the Actor, and the aggregate identifier, and for Commands passes a caller-supplied correlation identifier and allowed extensions through.

**Consequences (testable):**
- Generated message identifiers and idempotency keys are ULIDs and differ between calls; a caller-supplied idempotency key or correlation identifier that is not a ULID is a validation failure.
- The Tenant resolves in this order, and a Command or Query with no Tenant from any source is `validation_failed`:
  1. The Module's `fixedTenant`, when declared. The session Tenant is ignored for that Operation; a differing per-call value is `validation_failed` at `/tenant`.
  2. The per-call MCP argument, honored only when no session Tenant resolves from the FR-13 chain or when `allowTenantOverride` is set for the session; otherwise a differing per-call value is `validation_failed`.
  3. The session Tenant from the FR-13 chain.
- The aggregate identifier resolves in this order, and a Command or Query resolving to nothing is `validation_failed`; an empty aggregate identifier is never sent:
  1. The explicit argument. One that disagrees with the accessor value is `validation_failed`.
  2. The value of an accessor compiled once at startup, which reads `aggregateIdProperty` when set and otherwise the `ICommandContract` getter. A Command with no accessor source is excluded from the Catalog (FR-2).
  3. The Query's `aggregateId` constant.
- Actor: an Operation naming an `actorProperty` requires a resolved Actor (flag, environment, Profile; next release the forwarded user header) and is `validation_failed` without one. `[ASSUMPTION: in v1 the operator states the actor principal in the Profile; the tool never decodes the token.]`
- A Payload value under `tenantProperty` or `actorProperty` that differs from the resolved value is `validation_failed`; otherwise the properties named by `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty`, and `actorProperty` are overwritten from the Envelope before submission.
- Extensions travel only on Commands and only with keys in the Profile's `allowedExtensions` list, default empty (FR-18). Queries carry neither a correlation identifier nor extensions in v1, because the pinned client's query request has no such members (§8.2).
- Paging travels only as `run_query` arguments mapped to the Gateway's paging options; a Payload member named like one is sent as ordinary Payload, neither stripped nor mapped (FR-4).
- The Envelope carries the Routing Values, never the Operation Name.

#### FR-17: Submit and map the response

The executor submits through the `Hexalith.EventStore.Client` gateway client, returns the Gateway's result as JSON, and never retries.

**Consequences (testable):**
- Command results include the message identifier and idempotency key used, plus the Gateway's correlation identifier; they state whether the Gateway reported a duplicate, once OQ-9 confirms the response carries it.
- Query results include the document and, when paging applies, page size, offset, next cursor, total count, and has-more; no correlation identifier in v1 (§8.2). A Query-side `gateway_error` carries the correlation identifier only when the client's exception exposes one.
- The only outbound HTTP is through the gateway client; a test asserts no other `HttpClient` registration.

#### FR-19: Refuse writes in Read-only Mode

When the tool starts with `--read-only` or `EVENTSTORE_READ_ONLY` (FR-13), write submission is refused with `code: read_only`.

**Consequences (testable):**
- The MCP Server does not register `send_command`, so `tools/list` omits it; the CLI `send` verb exits 2 with `code: read_only`.
- The executor, called directly with a `write` Operation, returns `read_only` without touching the Gateway client; this is the guarantee, not the tool list.
- `list_operations` still lists Commands with kind `write`; `describe_operation` on a Command returns `submittable: false, reason: read_only`.
- `--read-only` on a read verb is accepted and has no effect.

### 5.6 Configuration and Profiles

**Description:** Connection settings live in this tool's own file, `~/.eventstore/mcpcli.json`. It has the admin CLI's shape and `config` verbs but is not shared with it: one profile name cannot serve both tools, since the admin URL and token target the admin API and the admin CLI rewrites its file from its own typed model. Realizes UJ-1.

#### FR-18: Manage Profiles

A shell user can select a Profile by name; a Profile holds `url`, `token`, `format`, `tenant`, `actor`, `allowTenantOverride`, and `allowedExtensions` (addendum §E).

**Consequences (testable):**
- The active Profile is used when `--profile` is absent; `config use`, `config current`, and `config profile list|add|remove` behave as in the admin CLI, and `config set <profile> <field> <value>` manages the remaining fields. `[ASSUMPTION: shell completion is deferred.]`
- A `format` other than `json` or `table` is `configuration_invalid`, exit 2.
- Tokens never appear on stdout or stderr, including in errors and verbose logs.

### 5.7 Coverage, migration, and policy commitments

**Description:** Apart from FR-20, these requirements are commitments rather than code in this repository. The end state is one server and one CLI for all of Hexalith. The product owner chose replacement over a strangler pattern to remove the inconsistency for good, accepting cross-repository coordination for the deletions. Realizes UJ-3.

#### FR-20: Cover the v1 Modules

The v1 tool references by pinned package only the Contracts Libraries that satisfy the dependency allowlist (§4), today Tenants and Parties, and exposes every decorated Operation in them. v1 is done when the tool is released and Tenants and Parties are covered end to end: for every Operation in `list_operations`, both Heads submit it against a running EventStore in the test harness, the Gateway accepts it, and the two result documents are equal (NFR-7, SM-4). Projects and Folders are added when they satisfy the allowlist and are Gateway-ready.

**Consequences (testable):**
- Package references only; CI builds contain no project reference to any Module, and the allowlist test rejects any referenced Contracts Library whose closure breaks the rule.
- A referenced Module whose assembly carries the marker but exposes no Operation appears in `list_modules` with zero Operations and an `empty_module` warning; an unmarked assembly is invisible (FR-3, FR-6).
- `Hexalith.Projects.Contracts` fails the allowlist today (it carries web framework and UI packages); slimming it is a Projects Gateway-ready prerequisite (§8.1).

#### FR-21: Define parity and produce the migration plan

A Legacy Server is deleted when its Module is Gateway-ready for every agent-facing Operation, meaning every tool or resource whose effect is a Command or Query through the Gateway; the migration plan is a v1 deliverable owned by the McpCli maintainers.

**Consequences (testable):**
- The plan lists, per Legacy Server and per Frozen CLI, a full inventory of its operations, the decorated type covering each, and the operations dropped (stream and file resources, and the search, filter, order-by, and freshness variants deferred by FR-9).
- Task and actor context that Projects and ChatBot carry today travels as ordinary Payload properties, through `actorProperty`, or in allowed Envelope extensions, never in module-specific code here.
- FrontComposer's host and the Projects plug-in are deleted together; Memories, which fronts per-user JWT identity today, is deleted only after the HTTP release.

#### FR-22: Publish the no-new-server rule

The Hexalith agent instructions (`hexalith-llm-instructions.md` in Hexalith.AI.Tools) state that from 2026-09-21 no new per-module MCP server or per-module agent CLI is created, that a Module's agent surface is its decorated Contracts Library, and that the Frozen CLIs are limited to bug fixes and listed in the migration plan.

**Consequence (testable):** the story closes when the pull request adding the rule is opened upstream and linked from this repository's `AGENTS.md`; its merge is tracked by the migration plan, not by this story.

## 6. Cross-cutting non-functional requirements

- **NFR-1 Startup.** The Catalog for the v1 Modules plus the sample Module builds in under 500 ms on `ubuntu-latest`, the CI runner the architecture names, so the stdio server is ready before a client's first request times out. `[ASSUMPTION: threshold from typical MCP client initialize timeouts; tune after the first measurement.]`
- **NFR-2 Tool budget.** The five Generic Tool names, descriptions, and input schemas together stay under 8,000 characters, so the server fits a client's tool budget alongside other servers; a snapshot test measures that figure and, separately, the output schemas. `[ASSUMPTION: roughly 2,000 tokens; characters are tokenizer-independent.]`
- **NFR-3 Determinism.** See FR-5.
- **NFR-4 Channel discipline.** See FR-10; logs use source-generated `LoggerMessage` methods.
- **NFR-5 Secrets.** See FR-18.
- **NFR-6 Portability.** A .NET 10 global tool for Linux, Windows, and macOS with no native dependencies. The EventStore client package carries the Dapr SDK; its size is accepted unless the EventStore owner publishes a gateway-only client package.
- **NFR-7 Testability.** The executor is testable with a substituted Gateway client; integration tests run against an EventStore started by the Aspire harness the architecture defines (spine AD-16) and assert accepted Commands and returned Query documents, not only status codes.
- **NFR-8 Description quality.** Every exposed description is understandable by someone who has never seen the code, verified by review of the Catalog dump (SM-5); a lint rejects a description equal to the humanized type name (SM-C4).

## 7. Public surface and versioning

- **Surface.** Three artifacts: the Decoration Package `Hexalith.McpCli.Abstractions`, the tool package `Hexalith.McpCli` (CLI plus MCP Server, installed as the `hexalith` command), and the Generic Tool contract (five names, the addendum §E argument table, the addendum §G result documents, and the Operation Name form). Both packages share one version.
- **Breaking changes.** Renaming a Generic Tool, changing an argument, or changing the Operation Name form is a major version; adding an optional argument or result field is minor. A Contracts Library builds unchanged across minor versions of the Decoration Package. Operation Name, domain, and Wire Type stability is a Module obligation (§8.1); this tool's version cannot signal a Module-driven break.
- **Release order.** The Decoration Package is published from this repository before any upstream decoration begins; a Module version reaches agents when this tool bumps the pin and releases. `[ASSUMPTION: no automatic bump.]`
- **Details.** Runtime targets and pinned packages are in addendum §B.

## 8. MVP scope

v1 is done when the tool is released and Tenants and Parties are covered end to end (FR-20). There is no scope fallback: if upstream decoration slips, the v1 date moves (OQ-8).

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
2. Declare the marker with Module Name, description, Identifier Kind, and `fixedTenant` where the Module runs under one tenant.
3. Decorate every agent-facing Command and Query.
4. Make every decorated type serialize completely from its own attributes or the marker's `serializerOptionsProvider`.
5. Publish the Contracts Library as a NuGet package and bump its version.
6. Have descriptions reviewed against NFR-8, with the review recorded in the Module's pull request.
7. Keep Operation Name, domain, and Wire Type stable, because renaming any of them silently breaks agents.

Work is tracked in each Module's own repository.

#### Upstream decoration schedule

Dates are open (OQ-8); the release is blocked until both v1 rows are met, and the product owner is the escalation owner.

| Module | Owner | Target Contracts version | Earliest pinnable tool release | Status |
|---|---|---|---|---|
| Tenants | Tenants maintainer | open | v1 | prerequisite, blocks v1 |
| Parties | Parties maintainer | open | v1 | prerequisite, blocks v1 |
| Projects | Projects maintainer | open | after v1 | follow-on |
| Folders | Folders maintainer | open | after v1 | follow-on, gates SM-1 |

#### Module-specific prerequisites

- **Tenants.** `fixedTenant = "system"`, `identifierKind = String`; descriptions and examples; `aggregateIdProperty` on per-tenant Queries and an `aggregateId` constant on list Queries (`list-tenants`, `get-user-tenants`), value chosen by the maintainer within the Gateway pattern; drop the `Cursor` and `PageSize` Payload members or accept the lint warning (FR-4); do not decorate the global-administrator Commands in v1.
- **Parties.** `identifierKind = String`. Query types do not exist; create one per read the Legacy Server exposes, served by the Parties projection actor (`projectionActorType`) with the `parties` list constant it already uses. On Commands, either keep attribute routing with today's values (`domain = "party"`, `wireTypeConvention = FullTypeName`, `aggregateIdProperty = PartyId`) or migrate to `ICommandContract` with kebab-case Wire Types, a breaking wire change; the maintainer chooses (OQ-5). Publish the agent-facing subset; the erasure and key-rotation Commands are probably not in it.
- **Projects.** Slim `Hexalith.Projects.Contracts` until it satisfies the allowlist (§4, FR-20); then add Query types for the Legacy Server's 11 resources and attribute routing with `actorProperty = ActorPrincipalId`. Detail in addendum §H.
- **Folders.** Publish decorated Command and Query types for the agent-facing subset of today's 49 REST tools, handled by a Folders domain service; acceptance is `list_operations folders` showing the agreed subset, each accepted by the Gateway. Owner: the Folders maintainer. Detail in addendum §H. The largest prerequisite: it does not gate v1 (FR-20), but it gates SM-1.

### 8.2 Out of scope for MVP

- HTTP transport with bearer, Tenant, and user header forwarding: the only committed next release, after an authentication design pass (OQ-1). Load-bearing for per-user identity.
- Legacy Server and Frozen CLI deletions: after v1, per Module, per FR-21.
- Query correlation identifier and extensions: the pinned client's query request cannot carry them (FR-16); revisit when the client does.
- Search, filter, order-by, freshness, and entity-scoped Query arguments beyond `entityId`, and command status lookup through the Gateway's status call: deferred; meanwhile the message identifier is returned for tracing.
- Parked, not scheduled: typed tools behind a module filter (SM-C2 forbids chasing them in v1), generated per-Operation subcommands, shell completion, plug-in loading of Contracts Libraries, event stream reading, MCP resources and prompts, executor retries.

### 8.3 Non-goals (explicit)

- Not the EventStore admin plane (`Hexalith.EventStore.Admin.Cli`, `.Admin.Mcp`); §2.2 draws the line.
- Not an identity provider: no OAuth or identity server in v1 or the next release; parked, not rejected forever.
- Not a second executor: the tool never calls a Module's REST or Dapr API. Modules that expose Operations only that way are not covered until Gateway-ready.

## 9. Success metrics

Checked three months after v1 ships.

**Primary**
- **SM-1 Zero module-specific code.** Tenants, Parties, and every Module that became Gateway-ready since are exposed with no module-specific code here, and one further Module was added by a package reference and a rebuild. Validates FR-5, FR-20.
- **SM-2 Cross-module task.** An agent completes a task spanning two Modules using only the Generic Tools, with no per-module prompt or tool. Validates FR-9, FR-15 to FR-17.
- **SM-3 First deletion.** At least one Legacy Server deleted. Validates FR-21.
- **SM-4 Heads agree.** A test runs both Heads against one EventStore with identical inputs for every Operation and gets identical Catalog data, identical error documents, and identical results once volatile Command result fields (message identifier, idempotency key, correlation identifier) are masked. Validates FR-5, FR-11, FR-12.

**Secondary**
- **SM-5 Description quality.** Every description passes a reviewer who has never seen the code, recorded in the Module's pull request per the §8.1 checklist. Validates FR-1, NFR-8.
- **SM-6 Time to first action.** A new operator reaches a successful `send_command` within 15 minutes using only the README, measured in a timed session recorded in the release checklist. `[ASSUMPTION: 15 minutes is a target, not a measured baseline.]` Validates FR-13, FR-18.
- **SM-7 First-party adoption.** At least one of Agents, ChatBot, or Conversations reaches business data through the Generic Tools. Validates the §1 bet.

**Counter-metrics (do not optimize)**
- **SM-C1 No new per-module server or CLI** after 2026-09-21. Counterbalances SM-3.
- **SM-C2 Five tools in v1.** Do not chase SM-2 by adding typed tools.
- **SM-C3 No dependency creep.** Coverage gained by referencing a Module's server or client project, or by widening the §4 allowlist without a PRD change, is a failure. Counterbalances SM-1.
- **SM-C4 No hollow descriptions.** A description equal to the humanized type name counts against SM-5.

## 10. Open questions

Numbering is stable so downstream references stay valid.

### 10.1 Handoff to architecture

This revision (2026-09-22) changes rules the architecture spine at `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md` encodes; the spine must be updated before the executor epic: AD-15 (allowlist wording), AD-9 (per-call tenant gate, `actorProperty`, no Query correlation or extensions), AD-19 (`aggregateId` constant, no empty identifier), AD-7 (`actorProperty` as an envelope-filled property), AD-11 (profile store and new Profile fields).

### 10.2 Open

1. **HTTP authentication design.** Issuer, token validation, header forwarding. Owner: architecture. Revisit before the HTTP transport story.
5. **Parties routing choice.** Attribute routing with today's full-type-name Wire Types, or migration to `ICommandContract`. Owner: Parties maintainer. Revisit before Parties decoration starts.
6. **Deletion order.** Owner: product owner. Revisit when the migration plan (FR-21) is drafted.
8. **Upstream decoration dates.** Target Contracts versions and dates for the §8.1 schedule. Owner: product owner with the Tenants and Parties maintainers. Revisit before the Decoration Package is published.
9. **Gateway deduplication.** Whether the Gateway deduplicates a resubmitted idempotency key and reports it in the command response, so UJ-1's retry and the FR-17 result can state it. Owner: EventStore owner. Revisit before FR-17 is implemented.

### 10.3 Resolved

2. **Module layout.** Resolved by the architecture spine (2026-09-22): flat layout `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*.Tests` like the sibling Modules (addendum §B).
3. **Aggregate-less Queries.** Resolved from source (2026-09-22): the Gateway's query validator rejects an empty aggregate identifier, and sibling clients send a per-Query constant (Parties `parties`); hence the `aggregateId` attribute member (§5.1, FR-16) and the §8.1 query spike.
4. **Analyzer feasibility.** Resolved by the architecture spine (2026-09-22): the analyzer is a separate project packed into the Decoration Package, so a Module author needs one reference; it is a separable story and the package may ship before it (FR-1).
7. **Package identifiers and CLI command name.** Resolved by the architecture spine (2026-09-22): command `hexalith`; packages `Hexalith.McpCli` (tool) and `Hexalith.McpCli.Abstractions` (Decoration Package), one shared version (§7).

## 11. Assumptions index

Each inline `[ASSUMPTION]` tag carries its own rationale; this table is the confirmation checklist.

| Location | Assumption | Who confirms |
|---|---|---|
| UJ-1 | The Gateway deduplicates on the idempotency key and reports it | EventStore owner (OQ-9) |
| FR-13 | JSON is the right default format for an agent-first tool | Product owner |
| FR-13 | The tool must not read the admin CLI's environment variables | Product owner |
| FR-16 | In v1 the operator states the Actor in the Profile; the tool never decodes the token | Product owner, architecture |
| FR-18 | Shell completion is deferred | Product owner |
| NFR-1 | 500 ms is the right startup threshold | Architecture, after first measurement |
| NFR-2 | 8,000 characters is roughly 2,000 tokens | Architecture, by snapshot test |
| §7 | No automatic pin bump when a Module publishes | Product owner |
| SM-6 | 15 minutes is a target, not a baseline | Product owner |

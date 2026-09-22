---
title: Hexalith.McpCli PRD
status: final
created: 2026-09-21
updated: 2026-09-22
---

# PRD: Hexalith.McpCli
*Working title. The repository is `mcpcli`; the module name follows the sibling-module convention.*

## 0. Document Purpose

This PRD is for the Hexalith maintainers and for the workflows that follow it: architecture, epics and stories, and the migration plan for the legacy per-module MCP servers. It builds on the product brief at `_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/` and does not restate its research. Rejected alternatives, transport mechanics, the tool argument table, and comparables live in `addendum.md` next to this file. Each rule is stated once, in §4 for guardrails and in its owning FR for behavior, and cross-referenced elsewhere. Unconfirmed inferences carry an inline `[ASSUMPTION]` tag and are indexed in §11.

## 1. Vision

Hexalith.McpCli replaces six handwritten per-module MCP servers with one generic MCP Server and one thin CLI, both driven by a single Catalog. A Module declares each Operation once, in its Contracts Library, with a Decoration Attribute that carries what the agent needs and the contract cannot express: a description a stranger can understand, an example, and routing fallbacks. The Catalog discovers those declarations at startup and describes them to the agent; the shared executor validates each Payload, fills the Envelope, and submits through the Gateway. The repository contains zero module-specific code; adding a Module is a package reference and a rebuild.

The goal is that a human can do any operation in Hexalith through an LLM agent, and that an agent is a peer of the Hexalith user interface rather than a second-class client bolted onto each Module. Hexalith is a CQRS platform in which every business action is a Command and every read is a Query, and the target state is that all of them travel through one EventStore Gateway. Today that uniformity is hidden: the six servers each have their own transport, tool naming, description mechanism, and authentication story, only one reaches the Gateway, and descriptions live in XML documentation comments that do not exist at runtime, so every server redescribes its operations by hand and drifts from the code. There is no triggering incident; the bet is that the Agents, ChatBot, and Conversations Modules will soon need to act on business data across Modules, and that six dialects will not survive that contact.

Two consequences follow now. Identity forwarding becomes essential, which is why the HTTP transport is the next release rather than a distant one. And a Command without a description is a Command an agent cannot use, so the Decoration Attribute stops being decoration and becomes part of what it means for a Hexalith Operation to exist: every Module that ships after 2026-09-21 ships agent-ready, or is not finished (FR-22).

## 2. Target User

### 2.1 Jobs To Be Done

- **Agent operator** (a developer with a dev or test EventStore). Install one .NET tool, point a Profile at the Gateway, and have an MCP-capable agent list, describe, and run every decorated Operation across Modules. Success is a cross-module task with no per-module setup.
- **LLM agent session** (Claude Code, Claude Desktop, VS Code, and the Agents, ChatBot, and Conversations Modules). Discover what Hexalith can do, understand each Operation from description and Schema alone, act, and get errors it can reason about.
- **Module author.** Make a Module visible to every agent on the day it ships by decorating its Contracts Library, and never write an MCP server again.
- **Shell user or CI script.** Call the same Catalog and Operations from a terminal with JSON on stdout, so a script and an agent cannot disagree about what Hexalith can do.

### 2.2 Non-Users (v1)

Platform administrators (the admin plane stays with `Hexalith.EventStore.Admin.Cli` and `.Admin.Mcp`), end users of Hexalith web applications, and anyone who needs per-user identity across a shared hosted server (the HTTP release, §8.2).

### 2.3 Key User Journeys

- **UJ-1. Nadia wires her agent to a test EventStore and runs a two-module task.** Nadia, a Hexalith developer, installs the tool, creates a Profile with the Gateway URL and a token, sets its default Tenant, and adds the stdio server to Claude Code. She asks the agent to create a party and then a project owned by it. The agent walks the discovery sequence, `list_modules`, `list_operations`, `describe_operation`, then calls `send_command` twice, with the aggregate identifier from the first result flowing into the second. Both results carry a message identifier and an idempotency key she can trace. **Edge case:** the second call times out; the agent retries with the idempotency key from its first attempt and the Gateway deduplicates it.
- **UJ-2. An agent session explores a Module it has never seen.** The Conversations Module's agent is asked about tenant membership. It follows the same discovery sequence for `tenants`, sees each Operation with its kind and description, picks `tenants.get-tenant-users`, reads its Schema and example, and calls `run_query`. The result comes back paged with a cursor. Nobody wrote a tenants-specific prompt or tool. **Edge case:** the session runs in Read-only Mode; `send_command` is absent from its tool list, so it reports that it can look but not act.
- **UJ-3. Marc adds a Module and it appears everywhere.** Marc maintains Projects. He adds the Decoration Package to `Hexalith.Projects.Contracts`, decorates each Command and Query with a description, example, and routing values, marks the assembly as a Module, and publishes the package. This repository bumps the package reference and rebuilds. Every agent and every script now sees `projects.*` Operations with no change here. **Edge case:** one record lacks a description; the Catalog excludes it and reports it on stderr at startup, so the gap is visible, not silent.

## 3. Glossary

Downstream readers and workflows use these terms exactly. Terms owned by a requirement point to it.

- **Module** — a Hexalith domain module. Identified in the Catalog by its **Module Name**, a lowercase kebab-case string declared on its Contracts Library assembly.
- **Contracts Library** — the `*.Contracts` NuGet package of a Module holding its Command and Query type definitions. The only Module artifact this product references; its transitive EventStore contract packages are allowed.
- **Operation** — a Command or a Query. A class or record decorated with a Decoration Attribute. Each has exactly one Operation Name.
- **Command** — an Operation that writes to one aggregate through the Gateway. Kind `write`.
- **Query** — an Operation that reads from a projection through the Gateway. Kind `read`.
- **Operation Name** — the canonical identifier of an Operation, `<module-name>.<operation>` in kebab-case, for example `parties.create-party`. Identical in both Heads and independent of the Wire Type.
- **Wire Type** — the operation type string the Gateway dispatches on (today `create-tenant` for Tenants, a full CLR type name for Parties). One of the Routing Values, never shown as the Operation Name.
- **Routing Values** — domain, Wire Type, aggregate identifier property, and, for Queries, projection type and projection actor type. Supplied by the EventStore contract interfaces when implemented, else by the Decoration Attribute.
- **Decoration Attribute** — the command or query attribute applied to an Operation type; members in §5.1.
- **Decoration Package** — the dependency-free NuGet package, built in this repository, containing the Decoration Attributes and the Module marker.
- **Catalog** — the in-memory registry of Modules and Operations both Heads read; built per §5.2.
- **Head** — one of the two surfaces over the Catalog: the MCP Server and the CLI.
- **MCP Server** — the Head speaking the Model Context Protocol over stdio, exposing the five Generic Tools.
- **Generic Tool** — one of `list_modules`, `list_operations`, `describe_operation`, `send_command`, `run_query` (FR-9). The set never changes with the Catalog.
- **CLI** — the Head exposing the verbs in FR-12.
- **Payload** — the JSON body of an Operation, validated against its Schema before submission.
- **Schema** — the JSON Schema derived from the Operation type (FR-7).
- **Identifier** — a property the Catalog recognizes as an identifier (FR-7). Identifiers are ULIDs.
- **Envelope** — the Gateway submission record around a Payload (FR-16; field list in addendum §B).
- **Gateway** — the EventStore gateway reached through the `Hexalith.EventStore.Client` package. The only backend this product talks to.
- **Tenant** — the tenant identifier placed in the Envelope from a per-call argument, a flag, an environment variable, a Profile, or, next release, a forwarded header. Never read from the Payload.
- **Profile** — a named connection configuration shared with the admin CLI (FR-18).
- **Read-only Mode** — a startup option under which write submission is refused and `send_command` is not advertised; discovery is unchanged (FR-19).
- **Legacy Server** — one of the per-module MCP surfaces this product replaces: the standalone servers of Parties, Folders, ChatBot, and Memories, plus the FrontComposer descriptor-driven host with its hosted Projects plug-in (FR-21).
- **Frozen CLI** — one of the five existing per-module agent CLIs, Folders, Projects, ChatBot, FrontComposer, and Memories, frozen to bug fixes by FR-22 and inventoried by FR-21.
- **Gateway-ready** — the state of a Module whose agent-facing Operations exist as decorated Command and Query types in a published Contracts Library and are accepted by the Gateway (checklist in §8.1).

## 4. Constraints and Guardrails

Each rule below is authoritative; FRs reference them rather than restate them.

- **Dependency policy.** Exactly two kinds of Hexalith dependency: the EventStore client package and the Contracts Libraries being exposed, with their transitive EventStore contract packages. Never an aggregate, projection, handler, client, or server project of any Module. Test projects may contain one synthetic sample Contracts Library, never referenced by the tool package.
- **Zero module-specific code.** No type, branch, or configuration in this repository names a Module.
- **Tenant.** Envelope-only, from the sources listed in §3; never read from the Payload (FR-13, FR-16).
- **Identity in v1.** The stdio server acts as whoever owns the configured token; the audit trail says "the tool", not the human. Accepted for dev and test use, and the reason the HTTP transport is the next release.
- **Identifiers.** ULIDs, validated with `Ulid.TryParse`, never `Guid.TryParse` (FR-7, FR-15).
- **Idempotency.** One generated message identifier per call; one idempotency key per call, caller-supplied or generated and returned in the result; the tool never retries (FR-16, FR-17).
- **Read-only.** Enforced in the executor, never by hints alone (FR-19).
- **Cost.** No hosted infrastructure in v1.

## 5. Features

### 5.1 Operation Decoration

**Description:** A Module author marks a class or record as a Command or Query with one Decoration Attribute and describes each property with `System.ComponentModel.Description`. Routing Values come from the contract interfaces when implemented and from the attribute otherwise. Only Commands and Queries are decorated; events, read models, and value objects are not. Realizes UJ-3.

**Decoration Attribute members**

| Member | Applies to | Required when | Meaning |
|---|---|---|---|
| `description` | both | always | What the Operation does, for a reader who has never seen the code |
| `example` | both | optional | A JSON Payload that validates against the Schema |
| `name` | both | optional | Overrides the derived `<operation>` part of the Operation Name |
| `domain` | both | no contract interface | Gateway domain, for example `party` |
| `wireType` | both | no contract interface | Wire Type the Gateway dispatches on |
| `aggregateIdProperty` | both | no contract interface, or always for a Query | Payload property holding the aggregate identifier |
| `projectionType` | query | no `IQueryContract` | Projection the Query reads |
| `projectionActorType` | query | Module has its own projection actor (Tenants) | Actor type for the Envelope; the interface does not carry it |
| `tenantProperty` | both | record declares a tenant member | Payload property the executor fills from the Envelope Tenant |
| `correlationProperty` | both | record declares one | Payload property filled from the Envelope correlation identifier |
| `idempotencyKeyProperty` | command | record declares one | Payload property filled from the Envelope idempotency key |

#### FR-1: Mark a type as a Command or a Query

A Module author can apply the command or query Decoration Attribute to a class or record in a Contracts Library with a required description and the members above.

**Consequences (testable):**
- A type with the command attribute enters the Catalog with kind `write`; with the query attribute, kind `read`.
- An empty or whitespace description is a build warning from a bundled analyzer and always a startup diagnostic that excludes the type (FR-6). `[ASSUMPTION: the analyzer is a separable story; startup exclusion is the guaranteed behavior (OQ-4).]`
- An example that does not validate against the Schema is a startup diagnostic.
- The Decoration Package has no package references.

#### FR-2: Resolve Routing Values per field

For each Routing Value, the Catalog uses the contract interface when the interface defines that field, else the attribute member.

**Consequences (testable):**
- A Tenants Command implementing `ICommandContract` needs no `domain`, `wireType`, or `aggregateIdProperty` on its attribute; a Tenants Query still needs `projectionActorType` and `aggregateIdProperty`.
- A Parties Command with no interface and no attribute routing members is excluded with a diagnostic naming the missing members.
- An attribute value equal to the interface value is ignored; one that differs is a conflicting-value warning and the interface value is used.
- Domain is a per-Operation value and may differ within one Module (Tenants routes global-administrator Commands to a second domain).

#### FR-3: Declare a Module

A Module author can mark a Contracts Library assembly with the Module marker carrying the Module Name and a one-line description.

**Consequences (testable):**
- The Catalog scans only assemblies carrying the marker; an undecorated assembly contributes nothing and produces no diagnostic.
- Two assemblies declaring the same Module Name is a startup error.

#### FR-4: Describe properties

Every property carrying `System.ComponentModel.Description` gets a `description` in the Schema; `describe --lint` on the CLI lists undescribed properties of an Operation and exits 1 if any exist.

### 5.2 Catalog

**Description:** At startup the tool builds one Catalog from every referenced Contracts Library carrying the Module marker. Both Heads read it, so they cannot disagree. Realizes UJ-1, UJ-2, UJ-3.

#### FR-5: Build the Catalog from referenced assemblies

The tool builds the Catalog at startup from the Contracts Libraries compiled into it; the assembly list is generated at build time from the project's package references and never hand-maintained, and assemblies are never loaded from a folder.

**Consequences (testable):**
- Adding a Module is a package reference and a rebuild; no source change in this repository.
- The tool is published untrimmed or with Contracts assemblies rooted, so a referenced assembly that no code touches is still scanned.
- Modules and Operations are sorted by name, and JSON is written with the tool's canonical serializer options, so discovery output is byte-identical across runs and operating systems for one build.

#### FR-6: Report Catalog problems at startup

Every decorated type the Catalog cannot expose is reported once on stderr with its type name, a category, and a severity, and the tool continues.

**Consequences (testable):**
- Error categories (type excluded): missing description, missing Routing Values, duplicate Operation Name, invalid example, duplicate Module Name. Warning categories (type kept): conflicting attribute value, undescribed property.
- Startup fails only when the Catalog is empty, or when `--strict` is set and any diagnostic is reported; `--strict` promotes warnings to errors for CI.

#### FR-7: Derive a JSON Schema per Operation

The Catalog derives a Schema from the Operation type that includes every declared property and rejects unknown properties.

**Consequences (testable):**
- Required, nullable, enum, nested type, and collection members map to the corresponding JSON Schema constructs; `additionalProperties` is `false`.
- An Identifier is a property whose type is a known identifier type, whose name ends in `Id`, or that the Decoration Package marks; it is typed as a string with a ULID pattern, never `format: uuid`. A value-object identifier with a single string member serializes as that member.
- Properties named by `tenantProperty`, `correlationProperty`, or `idempotencyKeyProperty` are marked `readOnly` in the Schema and filled by the executor (FR-16); a caller may omit them.

#### FR-8: Name Operations canonically

Each Operation's name part is the type name in kebab-case with a trailing `Command` or `Query` removed, unless the attribute `name` member overrides it.

**Consequences (testable):**
- `CreateParty` in `parties` is `parties.create-party`; `GetTenantUsersQuery` in `tenants` is `tenants.get-tenant-users`.
- Two types resolving to one Operation Name is a diagnostic; the second is excluded.

### 5.3 MCP Server

**Description:** The MCP Server exposes exactly five Generic Tools over stdio. The tool surface never changes with the Catalog, so it fits any client's tool budget and never needs list-changed notifications. Realizes UJ-1, UJ-2.

#### FR-9: Expose five Generic Tools

An agent can call the five Generic Tools and no others; their arguments are defined by the argument table in `addendum.md` §E, which both Heads implement.

**Consequences (testable):**
- `tools/list` returns exactly five tools, or four without `send_command` in Read-only Mode.
- `list_modules` returns each Module Name with its description; `list_operations` takes a Module Name and an optional kind and returns Operation Name, kind, description; `describe_operation` returns description, kind, Schema, example, the Envelope arguments the caller may supply, and `submittable`, with a reason when it is false.
- Argument sets for `send_command` and `run_query` are the addendum §E rows for those tools.
- Each tool description has three labeled parts: what it does, when to use it, what to call next.
- The three discovery tools and `run_query` carry `readOnlyHint: true`; `send_command` carries `readOnlyHint: false` and `idempotentHint: false`.

**Out of scope for v1:** search, filters, order-by, and freshness arguments on `run_query`; deferred (§8.2) and excluded from the parity bar (FR-21).

#### FR-10: Serve over stdio with clean channels

The MCP Server runs as a local process over stdio; stdout carries JSON-RPC only and all logging goes to stderr.

**Consequences (testable):**
- A test that drives the server with the ModelContextProtocol client SDK over stdio completes initialize, `tools/list`, and one call of each tool without a parse error; Claude Code, Claude Desktop, and VS Code are a release-checklist item.
- The server starts from a Profile or environment variables with no interactive prompt.

#### FR-11: Return structured results and errors

Every tool returns structured content with a declared output schema; failures return a structured error, never a stack trace.

**Consequences (testable):**
- Validation failure: `code: validation_failed`, the Operation Name, and one entry per violation with JSON path and message; a Payload that is not JSON is one violation.
- Gateway failure: status, reason code, detail, retryable flag, retry-after, client action, and correlation identifier, mapped from the client's exception.
- Unknown Operation Name: `code: unknown_operation` and up to three nearest Operation Names.

### 5.4 CLI

**Description:** The CLI is a thin companion over the same Catalog and executor. It proves the Catalog without MCP, lets a script do anything an agent can, and hosts the MCP Server through the `mcp` verb (the brief called it `serve`; renamed so the verb names the protocol). Realizes UJ-1, UJ-3.

#### FR-12: Expose the matching verbs

A shell user can run `modules`, `operations <module> [--kind]`, `describe <operation> [--lint]`, `send <operation>`, `query <operation>`, `mcp`, and `config`.

**Consequences (testable):**
- Every argument in the addendum §E table exists in both Heads under the spelling given there.
- `send` and `query` accept the Payload as `--payload <json>`, `--payload @file`, or stdin.
- `mcp` starts the MCP Server over stdio; `mcp --transport http` exits 2 with a message naming the release in which it arrives.

#### FR-13: Resolve global options in one order

Every verb accepts `--url`, `--token`, `--tenant`, `--profile`, `--format json|table`, `--output <file>`, and `--read-only`; each value resolves as per-call argument, then flag, then environment variable, then Profile, then default.

**Consequences (testable):**
- The order is testable per option with a fixture that sets every source.
- Defaults differ from the admin CLI: `json` is the default format and the default URL is the Gateway, not the admin API. `[ASSUMPTION: a tool whose primary reader is an agent defaults to JSON.]`
- Environment variable names are in addendum §E; they use the `EVENTSTORE_` prefix without `ADMIN`. `[ASSUMPTION: this tool is not the admin plane.]`
- A Command with no Tenant from any source is a validation failure. No Decoration Attribute member marks a Query tenant-less in v1; the only tenant-less Queries are the global-administrator ones, which are not decorated in v1 (§8.1). `[ASSUMPTION]`

#### FR-14: Use one exit-code contract

| Exit | Meaning | Stdout |
|---|---|---|
| 0 | Result document produced, no diagnostics for this invocation | result |
| 1 | Result document produced, and a diagnostic was written to stderr for this invocation (discovery verbs and `describe --lint` only; Catalog diagnostics never degrade `send` or `query`) | result |
| 2 | No result document: validation failure, Gateway rejection, read-only refusal, unsupported transport, startup failure | structured error (FR-11) |

### 5.5 Execution, Envelope, and Read-only Mode

**Description:** Both Heads share one executor. It validates the Payload, fills the Envelope, submits through the Gateway client, maps the response, and enforces Read-only Mode. Nothing module-specific lives here. Realizes UJ-1, UJ-2.

#### FR-15: Validate before submitting

The executor validates every Payload against the Schema and refuses to submit an invalid one; all violations are reported together, and Identifiers are checked with `Ulid.TryParse`.

**Consequence (testable):** an invalid Payload never reaches the Gateway; the substituted Gateway client records zero calls.

#### FR-16: Fill the Envelope

The executor generates a message identifier per call, uses the caller's idempotency key or generates one, places the resolved Tenant, passes a caller-supplied correlation identifier and extensions through, and resolves the aggregate identifier for Commands and Queries alike.

**Consequences (testable):**
- Generated message identifiers and idempotency keys are ULIDs and differ between calls; a caller-supplied idempotency key or correlation identifier that is not a ULID is a validation failure.
- The aggregate identifier resolves as: explicit argument, else the `aggregateIdProperty` value in the Payload, else the `ICommandContract` aggregate identifier read through a JSON path derived once at startup. An explicit argument that disagrees with the Payload is `validation_failed`; a Command with none is `validation_failed`. `[ASSUMPTION: a Query with none sends an empty aggregate identifier pending OQ-3.]`
- A Payload tenant value that differs from the Envelope Tenant is `validation_failed`; otherwise the properties named by `tenantProperty`, `correlationProperty`, and `idempotencyKeyProperty` are overwritten from the Envelope before submission.
- The Envelope carries the Routing Values, never the Operation Name.

#### FR-17: Submit and map the response

The executor submits through the `Hexalith.EventStore.Client` gateway client, returns the Gateway's result as JSON, and never retries.

**Consequences (testable):**
- Command results include the message identifier and idempotency key used, plus the Gateway's correlation identifier.
- Query results include the document and, when paging applies, page size, offset, next cursor, total count, and has-more.
- The only outbound HTTP is through the gateway client; a test asserts no other `HttpClient` registration.

#### FR-19: Refuse writes in Read-only Mode

When the tool starts with `--read-only` or `EVENTSTORE_READ_ONLY` (.NET boolean parsing), the MCP Server omits `send_command` from `tools/list`, the CLI `send` verb exits 2 with `code: read_only`, and the executor refuses a hand-crafted `send_command` request over stdio with the same code.

**Consequences (testable):**
- `list_operations` still lists Commands with kind `write`; `describe_operation` on a Command returns `submittable: false, reason: read_only`.
- `--read-only` on a read verb is accepted and has no effect.

### 5.6 Configuration and Profiles

**Description:** Connection settings come from the profile file the admin CLI already uses. The admin CLI rewrites that file from its own typed model, so a field it does not know would be lost; this tool therefore keeps the default Tenant per Profile in a separate file (FR-18). Realizes UJ-1.

#### FR-18: Read Profiles and keep a default Tenant

A shell user can select a Profile by name; the tool reads URL, token, and format from `~/.eventstore/profiles.json` and reads its default Tenant from `~/.eventstore/mcpcli.json`, keyed by Profile name and managed by `config tenant <profile> <tenant>`.

**Consequences (testable):**
- The active Profile is used when `--profile` is absent; `config use`, `config current`, and `config profile list|add|remove` behave as in the admin CLI. `[ASSUMPTION: shell completion is deferred.]`
- Tokens never appear on stdout or stderr, including in errors and verbose logs.

### 5.7 Coverage, Migration, and Policy Commitments

**Description:** Apart from FR-20, these requirements are commitments rather than code in this repository. The end state is one server and one CLI for all of Hexalith. The product owner chose replacement over a strangler pattern to remove the inconsistency for good, accepting cross-repository coordination for the deletions. Realizes UJ-3.

#### FR-20: Cover the v1 Modules

The v1 tool references the Contracts Libraries of Tenants, Parties, Projects, and Folders by pinned package and exposes every decorated Operation in them; v1 is done when the tool is released and Tenants and Parties are covered end to end.

**Consequences (testable):**
- Package references only; CI builds contain no project reference to any Module.
- A referenced Module that is not yet Gateway-ready appears in `list_modules` with zero Operations and a startup diagnostic. Projects and Folders follow as they become Gateway-ready and do not gate the v1 release.

#### FR-21: Define parity and produce the migration plan

A Legacy Server is deleted when its Module is Gateway-ready for every agent-facing Operation, meaning every tool or resource whose effect is a Command or Query through the Gateway; the migration plan is a v1 deliverable owned by the McpCli maintainers.

**Consequences (testable):**
- The plan lists, per Legacy Server and per Frozen CLI, a full inventory of its operations, the decorated type covering each, and the operations dropped (stream and file resources, and the search, filter, order-by, and freshness variants deferred by FR-9).
- Task and actor context that Projects and ChatBot carry today travels as ordinary Payload properties or in Envelope extensions, never in module-specific code here.
- FrontComposer's host and the Projects plug-in are deleted together; Memories, which fronts per-user JWT identity today, is deleted only after the HTTP release.

#### FR-22: Publish the no-new-server rule

The Hexalith agent instructions (`hexalith-llm-instructions.md` in Hexalith.AI.Tools) state that from 2026-09-21 no new per-module MCP server or per-module agent CLI is created, that a Module's agent surface is its decorated Contracts Library, and that the Frozen CLIs are limited to bug fixes and listed in the migration plan.

**Consequence (testable):** the story closes when the pull request adding the rule is merged upstream and this repository's `AGENTS.md` references it.

## 6. Cross-Cutting Non-Functional Requirements

- **NFR-1 Startup.** The Catalog for four Modules builds in under 500 ms on the CI runner class used for this repository, so the stdio server is ready before a client's first request times out. `[ASSUMPTION: threshold from typical MCP client initialize timeouts; tune after the first measurement.]`
- **NFR-2 Tool budget.** The five Generic Tool definitions together stay under 8,000 characters, so the server fits a client's tool budget alongside other servers. `[ASSUMPTION: roughly 2,000 tokens; characters are tokenizer-independent.]`
- **NFR-3 Determinism.** See FR-5.
- **NFR-4 Channel discipline.** See FR-10; logs use source-generated `LoggerMessage` methods.
- **NFR-5 Secrets.** See FR-18.
- **NFR-6 Portability.** A .NET 10 global tool for Linux, Windows, and macOS with no native dependencies.
- **NFR-7 Testability.** The executor is testable with a substituted Gateway client; integration tests run against an EventStore started by the test harness and assert accepted Commands and returned Query documents, not only status codes. `[ASSUMPTION: architecture picks the harness, Aspire or a container.]`
- **NFR-8 Description quality.** Every exposed description is understandable by someone who has never seen the code, verified by review of the Catalog dump (SM-5); a lint rejects a description equal to the humanized type name (SM-C4).

## 7. Public Surface and Versioning

- **Surface.** Three artifacts: the Decoration Package, the tool package (CLI plus MCP Server), and the Generic Tool contract (five names, the argument table, result shapes, and the Operation Name form).
- **Breaking changes.** Renaming a Generic Tool, changing an argument, or changing the Operation Name form is a major version; adding an optional argument or result field is minor. A Contracts Library builds unchanged across minor versions of the Decoration Package.
- **Release order.** The Decoration Package is published from this repository before any upstream decoration begins; a Module version reaches agents when this tool bumps the pin and releases. `[ASSUMPTION: no automatic bump.]`
- Runtime targets and pinned packages are in addendum §B.

## 8. MVP Scope

v1 is done when the tool is released and Tenants and Parties are covered end to end (FR-20).

### 8.1 In Scope, in dependency order

1. Test fixture Contracts Library (§4) so every other story can close in this repository.
2. Decoration Package, published first (FR-1 to FR-4; the analyzer is a separable story).
3. Catalog (FR-5 to FR-8).
4. Executor and Read-only Mode (FR-15 to FR-17, FR-19).
5. MCP Server (FR-9 to FR-11) and CLI with Profiles (FR-12 to FR-14, FR-18).
6. Coverage, migration plan, and upstream rule (FR-20, FR-21, FR-22).

**Gateway-ready checklist, common to every Module.** Reference the Decoration Package; decorate every agent-facing Command and Query; publish the Contracts Library as a NuGet package and bump its version; have descriptions reviewed against NFR-8 with the review recorded in the Module's pull request; keep domain and Wire Type stable, because renaming either silently breaks the Catalog mapping. Work is tracked in each Module's own repository.

**Module-specific prerequisites.**
- **Tenants.** Descriptions and examples; `projectionActorType` and `aggregateIdProperty` on Query attributes; decide whether the `Cursor` and `PageSize` Payload members give way to Envelope paging; do not decorate the global-administrator Commands in v1.
- **Parties.** Query types do not exist; create one per read the Legacy Server exposes, served by the Parties projection actor. On Commands, either keep attribute routing with today's values (`domain = "party"`, Wire Type the full CLR type name, `aggregateIdProperty = PartyId`) or migrate to `ICommandContract` with kebab-case Wire Types, a breaking wire change; the maintainer chooses (OQ-5). Publish the agent-facing subset; the erasure and key-rotation Commands are probably not in it.
- **Projects.** Query types for the 11 resources the Legacy Server exposes; attribute routing (`wireType` from the instance `CommandType`, `aggregateIdProperty = ProjectId`); `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty` naming the existing members, so records are unchanged; decide whether the server-side tenant guard in the Projects command submitter moves into the aggregate, since direct Gateway submission bypasses it.
- **Folders.** Today `Hexalith.Folders.Contracts` holds read models and OpenAPI only, and the Legacy Server exposes 49 tools over REST with dry-run, redaction, and freshness semantics. Folders becomes Gateway-ready by publishing decorated Command and Query types for its agent-facing subset, handled by a Folders domain service; dry-run, redaction, and freshness either move into handlers or are dropped and listed in the migration plan. Owner: the Folders maintainer. Acceptance: `list_operations folders` shows the agreed subset and each Operation is accepted by the Gateway. `[NOTE FOR PM]` The largest prerequisite; it does not gate v1 (FR-20), but it gates SM-1.

### 8.2 Out of Scope for MVP

- HTTP transport with bearer, Tenant, and user header forwarding: next release, after an authentication design pass (OQ-1). `[NOTE FOR PM]` Load-bearing for per-user identity.
- Legacy Server and Frozen CLI deletions: after v1, per Module, per FR-21.
- Search, filter, order-by, freshness, and entity-scoped Query arguments beyond `entityId`; command status lookup through the Gateway's status call: deferred; meanwhile the message identifier is returned for tracing.
- Typed tools behind a module filter: first follow-up candidate. Generated per-Operation subcommands, shell completion, plug-in loading of Contracts Libraries, event stream reading, MCP resources and prompts, executor retries: parked.

### 8.3 Non-Goals (Explicit)

- Not the admin plane (`Hexalith.EventStore.Admin.Cli`, `.Admin.Mcp`).
- Not an identity provider: no OAuth or identity server in v1 or the next release; parked, not rejected forever.
- Not a second executor: the tool never calls a Module's REST or Dapr API. Modules that expose Operations only that way are not covered until Gateway-ready.

## 9. Success Metrics

Checked three months after v1 ships.

**Primary**
- **SM-1 Zero module-specific code.** All four Modules exposed with no module-specific code here, and a fifth Module added by a package reference and a rebuild. Validates FR-5, FR-20.
- **SM-2 Cross-module task.** An agent completes a task spanning two Modules using only the Generic Tools, with no per-module prompt or tool. Validates FR-9, FR-15 to FR-17.
- **SM-3 First deletion.** At least one Legacy Server deleted. Validates FR-21.
- **SM-4 Heads agree.** A test runs both Heads against one EventStore and gets identical Catalog data and results for every Operation. Validates FR-5, FR-12.

**Secondary**
- **SM-5 Description quality.** Every description passes a reviewer who has never seen the code. Validates FR-1, NFR-8.
- **SM-6 Time to first action.** A new operator reaches a successful `send_command` within 15 minutes using only the README. `[ASSUMPTION: target]` Validates FR-13, FR-18.
- **SM-7 First-party adoption.** At least one of Agents, ChatBot, or Conversations reaches business data through the Generic Tools. Validates the §1 bet.

**Counter-metrics (do not optimize)**
- **SM-C1 No new per-module server or CLI** after 2026-09-21. Counterbalances SM-3.
- **SM-C2 Five tools in v1.** Do not chase SM-2 by adding typed tools.
- **SM-C3 No dependency creep.** Coverage gained by referencing a Module's server or client project is a failure. Counterbalances SM-1.
- **SM-C4 No hollow descriptions.** A description equal to the humanized type name counts against SM-5.

## 10. Open Questions

1. **HTTP authentication design.** Issuer, token validation, header forwarding. Owner: architecture. Revisit before the HTTP transport story.
2. **Module layout.** `hexalith-llm-instructions.md` documents a nested layout no Module follows; this PRD assumes the flat sibling layout (addendum §B). Owner: maintainers. Revisit before scaffolding.
3. **Aggregate-less Queries.** What the Gateway expects as aggregate identifier for list-style Queries. Owner: EventStore owner. Revisit before FR-16 is implemented.
4. **Analyzer feasibility.** Whether the Roslyn analyzer for missing descriptions ships in v1 (FR-1). Owner: maintainers.
5. **Parties routing choice.** Attribute routing with today's full-type-name Wire Types, or migration to `ICommandContract`. Owner: Parties maintainer. Revisit before Parties decoration starts.
6. **Deletion order.** Owner: product owner. Revisit when the migration plan (FR-21) is drafted.
7. **Package identifiers and CLI command name.** The brief uses `hexalith`. Owner: maintainers. Revisit before scaffolding.

## 11. Assumptions Index

Inline `[ASSUMPTION]` tags, each carrying its own rationale, appear at: FR-1 (analyzer), FR-13 (JSON default, environment prefix, tenant-less Queries), FR-16 (aggregate-less Queries), FR-18 (shell completion), NFR-1, NFR-2, NFR-7, §7 (no automatic bump), SM-6. A terminology slip in the brief's earliest memlog entry ("client libraries" for `*.Contracts`) was resolved during drafting and is recorded in `.memlog.md`.

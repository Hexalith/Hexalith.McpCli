---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
extractionStatus: confirmed
epicDesignStatus: approved
completedEpics:
  - 1
  - 2
  - 3
  - 4
storyDraftStatus: confirmed
validationStatus: passed
approvedStories:
  - "1.1"
  - "1.2"
  - "1.3"
  - "1.4"
  - "1.5"
  - "1.6"
  - "1.7"
  - "1.8"
  - "2.1"
  - "2.2"
  - "2.3"
  - "2.4"
  - "2.5"
  - "2.6"
  - "2.7"
  - "2.8"
  - "2.9"
  - "2.10"
  - "2.11"
  - "3.1"
  - "3.2"
  - "3.3"
  - "4.1"
  - "4.2"
  - "4.3"
  - "4.4"
  - "4.5"
  - "4.6"
  - "4.7"
  - "4.8"
  - "4.9"
  - "4.10"
  - "4.11"
  - "4.12"
  - "4.13"
  - "4.14"
  - "4.15"
  - "4.16"
  - "4.17"
  - "4.18"
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md
  - _bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md
---

# mcpcli - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for mcpcli, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: A Module author can decorate a Contracts class or record as a Command or Query with a required description and optional valid JSON example; the Catalog exposes it as `write` or `read`, excludes missing descriptions or invalid examples with startup diagnostics, and a bundled analyzer warns on missing descriptions when available.

FR2: The Catalog resolves each Gateway routing value from its contract interface, then its decoration attribute, then the Module's Wire Type convention where applicable; it reports missing, redundant, and conflicting values and supports explicit Query aggregate identifier properties or constants, with an explicit call argument required when neither is declared.

FR3: A Contracts assembly declares its canonical Module Name, description, `IdentifierKind`, and optional fixed Tenant, Wire Type convention, and serializer options provider; only marked assemblies are scanned, and the declared Identifier Kind and fixed Tenant govern every Operation in that Module.

FR4: Property descriptions appear in each Operation Schema; `describe_operation` and CLI `describe` always include specific lint findings for missing nested property descriptions, unmarked identifier-like properties, Payload paging members, and hollow Operation descriptions; `describe --lint` exits 1 when findings exist.

FR5: At startup, build one immutable Catalog from compiled-in Contracts packages flagged in the tool's package references, using a generated assembly manifest rather than a hand-maintained list or folder scan; enrolling a Module takes a package reference and rebuild, and discovery is deterministic across runs and operating systems.

FR6: Report every invalid Module or decorated type once on stderr with name, category, and severity; exclude invalid declarations but keep valid ones, use deterministic duplicate precedence, fail Catalog-dependent verbs on an empty Catalog, and make `--strict` fail on any diagnostic while `config` and `--version` remain available.

FR7: Derive a closed JSON Schema for each Operation's serializable Payload, including required, nullable, enum, nested, and collection members; preserve Module serializer converters and casing, mark Envelope-filled properties read-only, and type only explicitly marked or aggregate-source Identifiers by Module Identifier Kind, excluding identifiers that cannot serialize as JSON strings.

FR8: Give each Operation a stable `<module>.<kebab-case-operation>` name derived from its type after removing a Command or Query suffix, unless overridden by its decoration; keep that name distinct from the Gateway Wire Type and reject later duplicates with diagnostics.

FR9: Expose exactly five generic MCP tools (`list_modules`, `list_operations`, `describe_operation`, `send_command`, `run_query`), or four in Read-only Mode, with the addendum §E arguments and §G results, descriptive tool text and annotations, Module and kind filtering, operation Schema and Envelope discovery, and correct `submittable` state.

FR10: Run the MCP Server over stdio with JSON-RPC alone on stdout, logging on stderr, no interactive startup, SDK-driven legacy initialization or 2026-07-28 discovery and list/call behavior, and structured stderr-only failure before request serving versus MCP errors afterward.

FR11: Return the exact addendum §G structured success and error documents from both Heads, including output schemas, validation violations, Gateway status and supplied metadata, unknown Operation or Module suggestions, and no stack traces; preserve required fields and omit absent optional fields.

FR12: Offer CLI verbs `modules`, `operations`, `describe`, `send`, `query`, `mcp`, and `config` with the addendum §E arguments; accept JSON Payload inline, from a file, or stdin; render supported table views; and reject `mcp --transport http` as unsupported in v1.

FR13: Resolve Profile selection from flag, environment, then active Profile, and each session setting from flag, environment, selected Profile, then default using only documented sources; use JSON as the default format, no default Gateway URL, and validate boolean environment values while allowing offline discovery.

FR14: Use CLI exit 0 for a result, exit 1 only for a `describe --lint` result with findings, and exit 2 for a structured failure with no result; diagnostics affect the code only under `--strict`, and MCP failures before request serving keep stdout empty.

FR15: Validate every Payload against its Operation Schema and every resolved Envelope value against Gateway rules before submission, return all violations with JSON Pointers, validate aggregate identifiers by Module Identifier Kind, and make no Gateway call on invalid input.

FR16: Build each Gateway Envelope with one generated ULID message identifier, an optional caller-supplied ULID idempotency key, command correlation resolved to the supplied ULID or message identifier, fixed/gated/session Tenant precedence, a compiled aggregate identifier accessor or Query constant, operator-resolved Actor, allowed Command extensions, and query paging; reject disagreements and invalid values, fill declared Payload fields, and revalidate the rebuilt Payload.

FR17: Submit Commands and Queries exactly once through `Hexalith.EventStore.Client`, with no executor retry or other outbound HTTP client; return canonical Command identifiers and status, caller idempotency key only when supplied, Query document and available paging metadata, and preserve Gateway error details without inferring replay or duplicate status.

FR18: Manage this tool's own `~/.eventstore/mcpcli.json` Profiles through `config use`, `current`, `profile list|add|remove`, and `set`; support URL, token, format, Tenant, Actor, Tenant override gate, and allowed extension keys, and never expose tokens in output or logs.

FR19: In Read-only Mode, omit `send_command` from MCP tool registration, make CLI `send` fail with `read_only`, and enforce the same refusal inside the executor without a Gateway call while leaving discovery and Queries available.

FR20: Ship v1 only when decorated Tenants and Parties Contracts packages satisfy the dependency allowlist and every exposed Operation has one approved Module-owned conformance vector; compare both Heads against reset loopback Gateway scripts, execute every vector once in a blocking live Aspire lane, and enforce Parties inventory-to-Catalog coverage before release.

FR21: Produce versioned, maintainer-approved include/exclude inventories for every Legacy Server and Frozen CLI, with rationale and decorated type for included rows; a generic coverage gate checks exact canonical Operation and CLR type matches plus approved exclusions, and deletion waits for Module Gateway readiness, with FrontComposer and Projects removed together and Memories after HTTP identity support.

FR22: Publish the no-new-per-module-server-or-agent-CLI rule in the authoritative Hexalith.AI.Tools instructions, make decorated Contracts the Module agent surface, freeze existing per-module CLIs to bug fixes, and close the work only after the rule is merged and this repository points to that baseline.

### NonFunctional Requirements

NFR1: On `ubuntu-latest`, build a Catalog containing the v1 Modules and the one declared synthetic sample Module in under 500 ms; measure this in CI while testing the other Identifier Kind through isolated construction.

NFR2: Keep the five generic tool names, descriptions, and input schemas together under 8,000 characters; measure them by snapshot test and measure output schemas separately.

NFR3: Produce byte-identical Catalog discovery output for a given build across runs and operating systems, using stable ordering and canonical serialization (FR5).

NFR4: Reserve MCP stdout for JSON-RPC, CLI stdout for its result or error document, and stderr for logs and diagnostics; use source-generated logging methods (FR10).

NFR5: Keep tokens out of stdout, stderr, errors, and verbose logs, with masked presentation in `config current` (FR18).

NFR6: Package a framework-dependent, untrimmed .NET 10 global tool for Linux, Windows, and macOS without native dependencies; accept the EventStore client's Dapr SDK transitive dependency.

NFR7: Test the executor with a substituted Gateway client, drive both Heads out of process through a reset loopback Gateway for parity, and run each approved Module vector once against live EventStore with semantic assertions in a blocking Aspire gate.

NFR8: Ensure each exposed description is understandable without source-code context; review the Catalog dump and flag descriptions equal to humanized type names (FR4).

### Additional Requirements

- **Greenfield structural seed (Epic 1 Story 1 consideration):** Create the `.slnx` solution, flat `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*` projects, `global.json` from Hexalith.Builds, central package-management imports, root build configuration, and the single synthetic `Sample.Contracts` fixture specified by the architecture. No starter application template is named.
- Keep the hexagonal dependency direction: Abstractions has zero package references; Core has no MCP, System.CommandLine, or ASP.NET dependency; MCP and CLI are adapters; only the tool executable references Module Contracts packages; one composition root and one immutable Catalog serve both Heads (AD1–AD3, AD11).
- Generate `ModuleAssemblyManifest.g.cs` after `ResolveReferences` from flagged `HexalithContracts="true"` package references, match by `NuGetPackageId`, require exactly one Contracts assembly per flag, sort assembly names ordinally, and test manifest-to-reference equivalence, including marked-empty and unmarked assemblies (AD4).
- Define Core argument, result, and error records to match addendum §E/§G exactly, with one canonical result serializer; test all public document variants, optional-member omission, input surface mapping, and cross-head document equality (AD5).
- Use one cached, read-only Payload options instance per Module, preserving its converter order while fixing canonical non-converter settings including a tool-owned `DefaultJsonTypeInfoResolver` before `MakeReadOnly()`; derive Schema through `JsonSchemaExporter`, force a non-null Command object root without changing nested nullability, and validate with `JsonSchema.Net` `OutputFormat.List` (AD6–AD7).
- Compile aggregate identifier accessors once at Catalog build, including a JSON property read and `ICommandContract` getter path; preserve explicit argument precedence and Query constants while rejecting Command declarations with no source (AD19).
- Validate Command extensions against the operator allowlist and pinned Gateway sanitizer grammar, with at most 32 entries, key length 100, value length 1,000, and combined UTF-8 size 4,096 bytes; validate query paging `pageSize` 1..200, nonnegative `offset`, cursor length at most 4,096, and cursor/offset exclusivity before Gateway submission (AD9, AD20).
- Register the gateway client once through `AddMcpCliCore`; attach the static bearer handler only in the tool host, keep credentials out of Core, and retain the handler seam for the subsequent HTTP release (AD10–AD11).
- Build MCP tools dynamically with the pinned SDK's `McpServerTool.Create`, one Read-only-filtered `ToolCollection`, an SDK list filter that orders the assembled response, closed success/error output-schema branches, and built-in call dispatch; test schema conformance and annotation behavior under both required MCP protocol revisions (AD12).
- Make Profile mutations atomic and cross-process safe: lock, reload, validate, write and flush a restrictive same-directory temporary file, then replace; reject symlinks and malformed targets; enforce Unix permissions and Windows ACLs before token bytes are written (AD14).
- Enforce the exact production dependency allowlist and locked transitive closure from restored assets, including framework references; allow only named test-only EventStore/Aspire packages and the synthetic Contracts fixture outside production (AD15).
- Approve the McpCli-owned versioned vector contract and shared validator before upstream vector authoring; build generic conformance-vector and migration-inventory gates without Module-specific runtime branches; compare captured Gateway requests as well as documents under loopback, and assert live semantic effects without submitting a Command twice merely for parity (AD16, AD21).
- Compose the live AppHost with EventStore and Tenants through published Aspire helpers and Parties once a server-code-free `Hexalith.Parties.Aspire` package exists; require an upstream bounded source-build path in Hexalith.Builds or helper-managed build before claiming the blocking Aspire CI gate (AD16, open questions).
- Coordinate upstream `JsonSchema.Net 9.4.0` and `HexalithMcpCliVersion` catalog additions, first decorated Tenants and Parties Contracts releases, exact version pins, and Parties Aspire helper publication; these are explicit release dependencies, not substitutes for local implementation (AD15–AD17, open questions).
- Package and publish the dependency-free Decoration Package first through an Abstractions-only bootstrap gate; after upstream decorations, use one version for Abstractions and tool packages, validate exact staged IDs and versions, install the staged tool for smoke checks, and publish only from a green source SHA (AD17–AD18).
- Pin the architecture Stack versions, use `.NET 10`, C# 14, `xUnit v3`/Shouldly/NSubstitute, source-generated logging, one C# type per file, and the Hexalith.Builds build conventions; keep the tool framework-dependent and untrimmed (Architecture Stack, conventions, AD17).
- Treat HTTP authentication, hosted transport, additional typed tools and CLI subcommands, MCP resources/prompts, plug-in loading, event-stream reads, retries, and advanced Query arguments as deferred; v1 returns `unsupported_transport` for HTTP (Architecture Deferred; PRD §8.2).

### UX Design Requirements

No UX design contract exists for this CLI and MCP product; no separate UX-DR items were extracted.

### FR Coverage Map

FR1: Epic 1 — Declare a Command or Query with a useful description and valid example.
FR2: Epic 1 — Resolve Gateway routing per field from contracts, attributes, and convention.
FR3: Epic 1 — Declare a Module and its identifier, tenant, and serializer policy.
FR4: Epic 1 — Describe properties and expose actionable lint findings.
FR5: Epic 1 — Build deterministic discovery from flagged Contracts packages.
FR6: Epic 1 — Report Catalog diagnostics and enforce empty/strict behavior.
FR7: Epic 1 — Derive a closed, Module-aware JSON Schema.
FR8: Epic 1 — Assign canonical Operation Names and reject collisions.
FR9: Epic 3 — Advertise and run the fixed generic MCP tool set.
FR10: Epic 3 — Serve MCP over clean stdio JSON-RPC channels.
FR11: Epic 2 — Define shared structured result and error documents; Epic 3 verifies MCP carriage and output schemas.
FR12: Epic 2 — Provide CLI discovery, execution, configuration, and output verbs; Epic 3 completes the `mcp` stdio verb.
FR13: Epic 2 — Resolve session settings in the documented precedence order.
FR14: Epic 2 — Apply the CLI result, lint, and failure exit-code contract.
FR15: Epic 2 — Validate Payload and Envelope before submission.
FR16: Epic 2 — Resolve Tenant, Actor, aggregate identity, identifiers, extensions, and paging into the Envelope.
FR17: Epic 2 — Submit once through the EventStore gateway client and map its result.
FR18: Epic 2 — Manage separate, secret-safe Profiles.
FR19: Epic 2 — Refuse writes inside the executor and CLI; Epic 3 omits the MCP write tool.
FR20: Epic 1 — Approve the shared conformance-vector contract and validator before upstream authoring; Epic 4 — Prove approved Tenants and Parties coverage and v1 release readiness.
FR21: Epic 4 — Produce approved migration inventories and enforce inventory-to-Catalog parity.
FR22: Epic 4 — Merge the authoritative no-new-server and frozen-CLI rule.

## Epic List

### Epic 1: Module Authors Can Publish Discoverable Operations

A Module author can ship a decorated Contracts Library and verify that its Commands and Queries enter a deterministic Catalog with accurate routing, Schemas, descriptions, and diagnostics. The structural seed and synthetic Contracts fixture are built here so the capability can be checked before upstream Module releases exist.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8; the FR20 vector-authoring prerequisite.

**Implementation notes:** Build the dependency-free Abstractions package and optional bundled analyzer, generated assembly manifest, one immutable Core Catalog, Module-aware serialization, Schema derivation, and author-facing Catalog and lint checks. Story 1.8 supplies the shared vector contract and validator before upstream Module vector authoring. Keep this epic usable with the synthetic Module alone. The Package can be published before the v1 tool.

### Epic 2: Operators Can Configure and Run Operations from the Terminal

An operator or script can select a Profile, discover Operations, submit valid Commands and Queries through the EventStore Gateway, inspect canonical results and errors, and enforce Read-only Mode from one `hexalith` CLI.

**FRs covered:** FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19.

**Implementation notes:** Use Epic 1's Catalog; add the shared executor and document records, safe Profile store, settings resolver, one composition root, gateway client, and CLI adapter. Implement the CLI's `mcp` command binding and unsupported-HTTP response here; Epic 3 supplies its stdio server. The shared records define the full §G contract, with MCP-specific carriage verified in Epic 3.

### Epic 3: Agents Can Use One Generic MCP Server

An MCP-capable agent can discover and execute every available Operation through five fixed tools over stdio, with the same behavior and documents as the CLI; a Read-only session exposes only four tools.

**FRs covered:** FR9, FR10. This epic also completes the MCP-facing acceptance of FR11, FR12, and FR19.

**Implementation notes:** Adapt the existing Catalog and executor through one Read-only-filtered `ToolCollection`; use the SDK's post-handler list filter for fixed order and built-in call dispatch, advertised output schemas, clean JSON-RPC channels, and pre-request-serving error behavior. No Module-specific tool code is added.

### Epic 4: Maintainers Can Verify and Release v1 Coverage

Maintainers can demonstrate that approved Tenants and Parties Operations work through both Heads, have the required migration inventory and conformance evidence, and release the generic tool with an authoritative rule against new per-Module agent servers and CLIs.

**FRs covered:** FR20, FR21, FR22.

**Implementation notes:** Enforce the dependency closure; run generic loopback parity and once-per-vector live semantic gates; version and approve Legacy Server/Frozen CLI inventories; complete upstream Contracts, Aspire helper, Builds, and Hexalith.AI.Tools prerequisites; then validate and publish the two packages at one version. Projects, Folders, and legacy deletions follow their PRD gates after v1.

## Epic 1: Module Authors Can Publish Discoverable Operations

A Module author can ship a decorated Contracts Library and verify that its Commands and Queries enter a deterministic Catalog with accurate routing, Schemas, descriptions, and diagnostics.

### Story 1.1: Declare a Module and Its Operations

As a Module author,
I want a buildable Decoration Package with attributes for my Contracts Library,
So that I can declare agent-facing Commands and Queries without adding a per-Module server.

**Requirements:** FR1, FR3, FR8

**Acceptance Criteria:**

**Given** a new checkout with the root-declared Hexalith.Builds reference,
**When** I restore and build `Hexalith.McpCli.slnx`,
**Then** the .NET 10 solution builds the flat `Hexalith.McpCli.Abstractions` and synthetic `Sample.Contracts` projects using the pinned SDK, central package management, and warnings as errors,
**And** no legacy `.sln` file or nested source layout is introduced.

**Given** the architecture's structural seed,
**When** Story 1.1 creates the repository scaffold,
**Then** it includes `Directory.Build.props` with the three-path import of `references/Hexalith.Builds/Props/Directory.Packages.props`, root `Directory.Packages.props`, `global.json` copied from Hexalith.Builds, and `tests/Directory.Build.props`,
**And** it includes `package.json`, `commitlint.config.mjs`, `.releaserc.json`, `tools/release-packages.json`, and thin `.github/workflows/ci.yml`, `release.yml`, and `commitlint.yml` files, ready for their later story gates.

**Given** the seeded delivery files,
**When** their configuration is inspected,
**Then** `ci.yml` calls the Hexalith.Builds reusable `domain-ci.yml`, `release.yml` supports the Abstractions-only bootstrap before the paired release, and `tools/release-packages.json` names exactly `Hexalith.McpCli.Abstractions` and `Hexalith.McpCli` for that paired release,
**And** package and commitlint configuration uses the repository's pinned Conventional Commits tooling and `.releaserc.json` defines the architecture's single semantic-release version path.

**Given** a Contracts project that references `Hexalith.McpCli.Abstractions`,
**When** I mark its assembly with `[HexalithModule]`, mark a class or record with `[HexalithCommand]` or `[HexalithQuery]`, and mark an identifier property with `[HexalithIdentifier]`,
**Then** the declarations compile with the PRD §5.1 marker and operation members, including required description and Identifier Kind,
**And** the package has no consumer-visible package dependencies.

**Given** the synthetic `Sample.Contracts` project,
**When** it builds,
**Then** it declares exactly one `Ulid`-kind Module with an interface-routed Command, an attribute-routed Command, a converter-backed value-object identifier, and a Query,
**And** no production project references this test fixture.

**Given** type names with suffixes, acronyms, and digits,
**When** the shared Abstractions naming helper converts them,
**Then** it produces the architecture's canonical kebab-case name parts, including `TLSConfig` → `tls-config`,
**And** it removes only a trailing `Command` or `Query` suffix.

### Story 1.2: Enroll a Contracts Package by Reference

As a tool maintainer,
I want the build to generate its Contracts assembly manifest from flagged package references,
So that adding a Module requires a package reference and rebuild rather than a source-maintained scan list.

**Requirements:** FR5, NFR3

**Acceptance Criteria:**

**Given** a `*.Contracts` package reference marked `HexalithContracts="true"` in the tool project,
**When** the build finishes `ResolveReferences`,
**Then** an MSBuild target matches that package by `NuGetPackageId` and generates `ModuleAssemblyManifest.g.cs` with its Contracts assembly name,
**And** generated assembly names are sorted ordinally.

**Given** a flagged package that contributes zero or multiple Contracts assemblies,
**When** the manifest target runs,
**Then** the build fails with a diagnostic naming the package and mismatch,
**And** it does not silently select an assembly.

**Given** flagged and unflagged package references in an isolated build fixture,
**When** a build test compares the generated manifest with those references,
**Then** it finds exactly one entry for each valid flagged package and none for unflagged packages,
**And** neither the tool source nor runtime configuration contains a hand-maintained assembly list or folder scan.

**Given** the synthetic sample Module and isolated marked-empty and unmarked assembly fixtures,
**When** their packages are enrolled in the build fixture,
**Then** the manifest includes all flagged assemblies regardless of their markers or Operation counts,
**And** assembly marker presence or Operation count does not change whether a flagged assembly appears in the generated manifest.

### Story 1.3: Derive the Operation's JSON Schema

As a Module author,
I want each decorated Payload type to produce a Schema that matches its JSON serialization,
So that agents can prepare valid arguments without knowing the CLR type.

**Requirements:** FR1, FR7

**Acceptance Criteria:**

**Given** the Hexalith.Builds central package catalog before the first Schema CI restore,
**When** `JsonSchema.Net` is introduced for Schema validation,
**Then** version `9.4.0` is pinned in the owning Builds repository and consumed through central package management,
**And** this repository does not patch its read-only `references/` checkout or use an inline package version.

**Given** a decorated type with required, nullable, enum, nested, collection, settable, constructor-bound, and get-only members,
**When** its Schema is derived,
**Then** the Schema represents every serializable input member, excludes a get-only member with no constructor binding, and sets `additionalProperties: false`,
**And** `[Description]` text appears on the corresponding serialized properties.

**Given** a Module marker naming a valid serializer options provider in the same Contracts assembly,
**When** Schema derivation uses that Module,
**Then** it reads the provider's static options once, caches read-only Module Payload options, preserves provider converters ahead of canonical converters, and applies the tool's canonical non-converter settings,
**And** embedded property names follow the Module's serialization contract.

**Given** a property marked `[HexalithIdentifier]` or named by `aggregateIdProperty`,
**When** its Schema is derived,
**Then** it is a JSON string with a ULID pattern for an `Ulid`-kind Module and an ordinary string for a `String`-kind Module,
**And** a `ByteAether.Ulid.Ulid` property gets the ULID pattern regardless of Module kind, while an unmarked `*Id` property keeps its serializer-derived Schema.

**Given** a property named by `tenantProperty`, `correlationProperty`, `idempotencyKeyProperty`, or `actorProperty`,
**When** its Schema is derived,
**Then** that property is marked `readOnly` and removed from `required`,
**And** a similar property that is not named by the decoration remains an ordinary Payload member.

**Given** a declared example and the derived Schema,
**When** the example is validated with `JsonSchema.Net`,
**Then** a matching example passes and a mismatching example reports its violation locations,
**And** the Payload validator accepts or rejects sample Payloads using that same derived Schema.

### Story 1.4: Discover Valid Operations in One Catalog

As a Module author,
I want the tool to build a Catalog from my decorated Contracts assembly,
So that both Heads can discover the same stable Operations and routing details.

**Requirements:** FR2, FR3, FR5, FR8, NFR3

**Acceptance Criteria:**

**Given** the assembly list produced by Story 1.2,
**When** `CatalogBuilder.Build` processes it,
**Then** it scans only assemblies with `[HexalithModule]`, builds one immutable Module and Operation descriptor set, and sorts Modules and Operations ordinally,
**And** an unmarked assembly stays invisible without a diagnostic.

**Given** interface-routed and attribute-routed Commands and Queries in the sample fixture,
**When** the Catalog resolves domain, Wire Type, aggregate identifier source, projection type, and optional projection actor type,
**Then** each field uses its contract interface value first, its attribute value second, and the marker's Wire Type convention only as a fallback,
**And** a Wire Type remains separate from the canonical Operation Name.

**Given** an `ICommandContract` whose aggregate identifier is a computed getter, a Query with `aggregateIdProperty`, a Query with an `aggregateId` constant, and a Query with neither,
**When** their descriptors are built,
**Then** each applicable property or interface getter has one compiled accessor, the constant is stored when declared, and the source-free Query reports `aggregateIdRequired: true`,
**And** no Command without an aggregate identifier source is exposed as valid.

**Given** decorated types with ordinary names, acronym and digit boundaries, and an explicit `name` override,
**When** the Catalog names them,
**Then** every exposed Operation has the canonical `<module>.<operation>` name defined by FR8,
**And** output ordering and canonical serialization are byte-identical for repeated builds from the same assemblies.

**Given** a Module with a fixed Tenant, Identifier Kind, and serializer options provider,
**When** its descriptor is inspected,
**Then** those declared values and the Schema from Story 1.3 are retained for the executor and both Heads,
**And** no Head has to reflect over the Contracts type again.

### Story 1.5: Diagnose Catalog Declarations

As a Module author,
I want clear, deterministic diagnostics for declarations the Catalog cannot expose,
So that I can fix gaps before agents rely on them.

**Requirements:** FR1, FR2, FR6

**Acceptance Criteria:**

**Given** declarations with a missing description or routing value, an invalid identifier type or example, or an invalid serializer provider,
**When** the Catalog builds,
**Then** it excludes the affected type or Module with the architecture's specific error category, severity, type name, and actionable message,
**And** valid declarations remain available.

**Given** invalid Gateway routing values, an ambiguous Query aggregate identifier, or a Tenant property used as the aggregate identifier,
**When** the Catalog builds,
**Then** it reports `invalid_routing_value`, `ambiguous_aggregate_id`, or `tenant_is_aggregate_id` as appropriate,
**And** the invalid Operation is excluded before execution.

**Given** a property-reference attribute using a top-level CLR property with `[JsonPropertyName]`,
**When** the Catalog builds,
**Then** it caches one effective serialized name and escaped pointer shared by Schema, envelope filling, ownership checks, and the aggregate accessor,
**And** an unknown, ignored, ambiguous, or converter-opaque member excludes the Operation with `invalid_property_reference`.

**Given** two envelope roles or an envelope role and `aggregateIdProperty` resolving to one serialized member,
**When** the Catalog checks ownership after serialization mapping,
**Then** it excludes the Operation with `conflicting_property_roles`, retaining `tenant_is_aggregate_id` for that specific collision,
**And** fixtures cover tenant/actor aliasing, correlation/aggregate aliasing, and renamed serialized members.

**Given** duplicate Module or Operation Names,
**When** assemblies and types are scanned in ordinal order,
**Then** the first declaration survives and each later duplicate is excluded with its specific diagnostic,
**And** repeated builds produce the same survivor and diagnostic order.

**Given** an attribute routing value that equals an interface or convention value, or conflicts with an interface value,
**When** routing is resolved,
**Then** the Catalog retains the Operation and emits `redundant_value` or `conflicting_value` as appropriate,
**And** the interface value wins a conflict while an explicit attribute value may override a convention.

**Given** a marked assembly with no exposed Operations, an unmarked assembly, and a Catalog with no valid Operations,
**When** the Catalog is inspected,
**Then** the marked assembly remains visible with an `empty_module` warning, the unmarked assembly is invisible without a warning, and Catalog-dependent access returns `catalog_empty`,
**And** Catalog-free operations do not trigger a build.

**Given** any Catalog diagnostic,
**When** the Catalog is first built,
**Then** it is logged once to stderr through structured logging and is absent from public discovery documents,
**And** strict validation returns `catalog_invalid` for warnings as well as errors while normal mode retains valid Operations.

### Story 1.6: Inspect Description Quality

As a Module author,
I want actionable lint findings beside each Operation's Schema,
So that I can improve descriptions before publishing a Contracts package.

**Requirements:** FR4, NFR8

**Acceptance Criteria:**

**Given** a decorated Operation with nested objects and collections,
**When** the Catalog produces its description result,
**Then** it recursively reports `missing_property_description` for undescribed serializable properties,
**And** each property finding includes a `code`, `severity: warning`, nonempty message, and RFC 6901 pointer using the Module's serialized property names.

**Given** an unmarked property whose name looks like an identifier, a Payload member named `PageSize`, `Offset`, or `Cursor`, or an Operation description equal to its humanized type name,
**When** lint runs,
**Then** it reports `unmarked_identifier_like_property`, `payload_paging_member`, or `hollow_description` respectively,
**And** the operation-level hollow-description finding has no `property` member.

**Given** an Operation with complete descriptions and no lint issue,
**When** it is described,
**Then** `lintFindings` is an empty array,
**And** lint findings never enter Catalog diagnostics or exclude the Operation.

**Given** a property name containing `~` or `/` under Module-specific JSON casing,
**When** lint emits its pointer,
**Then** it uses RFC 6901 escaping and points to the serialized property,
**And** repeating discovery yields the same finding order and document.

### Story 1.7: Warn on Missing Operation Descriptions at Build Time

As a Module author,
I want a compiler warning when I leave a Command or Query description blank,
So that I can fix the declaration before the Catalog excludes it at startup.

**Requirements:** FR1

**Acceptance Criteria:**

**Given** a class or record decorated with `[HexalithCommand]` or `[HexalithQuery]` and an empty or whitespace description,
**When** the consuming Contracts project builds,
**Then** the bundled analyzer reports a warning at that declaration,
**And** a nonblank description produces no such warning.

**Given** a Contracts project with one reference to `Hexalith.McpCli.Abstractions`,
**When** the package is restored,
**Then** the analyzer is loaded from `analyzers/dotnet/cs` without a second package reference,
**And** unrelated classes and records are not analyzed as Operations.

**Given** the Abstractions and analyzer projects,
**When** the Decoration Package is packed and inspected,
**Then** Abstractions has no consumer-visible package dependencies, while the analyzer's Roslyn dependencies remain private,
**And** the analyzer project follows the architecture's `netstandard2.0` and Roslyn component settings.

### Story 1.8: Define and Validate the Conformance Vector Contract

As a Module author,
I want an approved vector format and a shared validator before I author conformance evidence,
So that my Contracts release can supply compatible inputs and semantic expectations for the generic test runners.

**Requirements:** FR20, NFR7; architecture AD-16

**Dependencies:** Story 1.1's structural seed and synthetic Contracts fixture. This story completes without the executor, either Head, decorated Tenants or Parties releases, or the live AppHost. Stories 4.8–4.10 consume its approved artifact before upstream vector authoring; Story 4.11 consumes it for parity execution.

**Acceptance Criteria:**

**Given** upstream Tenants and Parties vector authoring has not begun,
**When** McpCli maintainers approve the companion vector contract and shared validator,
**Then** a versioned, closed schema fixes canonical Operation Names, owning Contracts package ID and exact version, generic prerequisite calls, Payload and Envelope inputs, expected Gateway requests, scripted responses, semantic assertion vocabulary, and supported format versions,
**And** the contract and validator are test artifacts outside production source, with no Module-specific branches or additional production dependency.

**Given** valid Command and Query vectors for the existing synthetic Contracts fixture and its locally packed immutable release artifact,
**When** the shared validator runs without a Gateway connection,
**Then** it accepts compatible vectors and verifies their owning package ID and exact version against that artifact,
**And** fixtures with unsupported format versions, unknown fields, invalid contract-defined inputs or assertions, or a mismatched package ID/version fail with actionable locations and reasons.

**Given** the approved schema, validator, and synthetic examples,
**When** a Module maintainer follows the versioned authoring instructions,
**Then** they can run the same validator against their vectors and owning immutable Contracts release artifact before approving those vectors,
**And** the handoff records the approved contract version, validator invocation, and compatibility policy; real Module vector authoring is not required to complete this story.

**Given** the validator's reusable entry point and synthetic package identity/version fixtures,
**When** local tests supply the expected package identity/version as a runner would,
**Then** matching vectors pass and stale vectors fail through the same validation rules used for author approval,
**And** the handoff assigns restored production-package rechecks and parity execution to Story 4.11 and live semantic execution to Story 4.13; neither runner is a completion gate for Story 1.8.

## Epic 2: Operators Can Configure and Run Operations from the Terminal

An operator or script can select a Profile, discover Operations, submit valid Commands and Queries through the EventStore Gateway, inspect canonical results and errors, and enforce Read-only Mode from one `hexalith` CLI.

### Story 2.1: Inspect Effective Session Settings

As an operator,
I want the CLI to resolve and show the settings it will use,
So that I can verify the Gateway target and execution context before submitting an Operation.

**Requirements:** FR13, FR18, NFR5

**Acceptance Criteria:**

**Given** a version-1 `~/.eventstore/mcpcli.json` with an active Profile, an `EVENTSTORE_PROFILE` value, and a `--profile` flag,
**When** `config current` runs under each combination,
**Then** Profile selection follows flag, environment, then active Profile,
**And** the tool does not read the admin CLI's `profiles.json`.

**Given** a selected Profile, environment values, and global flags for the documented settings,
**When** the settings resolver runs,
**Then** each setting uses flag, environment, Profile, then default where that source exists,
**And** `config current` shows each resolved value and its source while masking the token to its first four characters.

**Given** no Gateway URL,
**When** I run `config current` or `--version`,
**Then** the command succeeds without building a Catalog or opening a Gateway connection,
**And** the resolved settings retain an absent URL for execution preflight.

**Given** `EVENTSTORE_READ_ONLY`, `EVENTSTORE_STRICT`, or `EVENTSTORE_ALLOW_TENANT_OVERRIDE`,
**When** its value is `true`, `false`, `1`, or `0`,
**Then** it resolves to the corresponding boolean,
**And** any other value returns `configuration_invalid` with its source identified and exit code 2.

**Given** the CLI composition root,
**When** an implemented verb starts,
**Then** it builds one Host container with one `ResolvedSettings` singleton,
**And** Core and Heads receive settings from DI rather than reading environment variables or the Profile file themselves.

### Story 2.2: Add and Select a Private Profile

As an operator,
I want to add, list, and select Gateway Profiles,
So that I can switch environments without exposing credentials or editing JSON by hand.

**Requirements:** FR18, NFR5

**Acceptance Criteria:**

**Given** no `~/.eventstore/mcpcli.json`,
**When** I run `config profile add <name> --url <url>` with optional token and format,
**Then** the tool creates a version-1 Profile file owned by this tool,
**And** it leaves the admin CLI's `profiles.json` untouched.

**Given** Profiles with valid names,
**When** I run `config profile list`, `config use <name>`, `config use --clear`, or `config current`,
**Then** list shows Profiles, use selects or clears the active Profile, and current shows resolved values and sources,
**And** tokens are masked in every output and log.

**Given** a Profile name outside `^[a-zA-Z0-9_-]{1,64}$`, an invalid URL or format, or a missing Profile selected by `use`,
**When** the command runs,
**Then** it returns `configuration_invalid` without changing the file,
**And** no token value appears in the error.

**Given** a valid Profile mutation,
**When** the store writes a token,
**Then** it takes an exclusive cross-process lock, reloads and validates the latest target, writes and flushes a same-directory temporary file with restrictive permissions, and atomically replaces the target,
**And** Unix permissions or Windows ACLs protect the directory, target, temporary, and lock files before token bytes are written.

**Given** a symlink at the target or lock path, or a malformed or unsupported-version target,
**When** a Profile command runs,
**Then** it fails without following the symlink or overwriting the target,
**And** a stale temporary file is ignored.

### Story 2.3: Update and Remove Profiles Safely

As an operator,
I want to change execution context fields and remove obsolete Profiles,
So that my CLI configuration stays accurate without losing concurrent edits.

**Requirements:** FR18, NFR5

**Acceptance Criteria:**

**Given** an existing Profile,
**When** I run `config set <profile> <field> <value>` for `tenant`, `actor`, `allowTenantOverride`, or `allowedExtensions`,
**Then** only the named field changes, with comma-separated extension keys stored as a validated list,
**And** an unknown field, invalid value, or case-insensitive duplicate extension key fails without writing.

**Given** an active Profile,
**When** I remove it with `config profile remove <name>`,
**Then** the Profile is removed and the active selection is cleared,
**And** removing a missing Profile fails without changing the file.

**Given** an existing Profile name,
**When** I run `config profile add` for that name,
**Then** its Profile record is replaced as specified by the config contract,
**And** other Profiles and the active selection are preserved.

**Given** two concurrent Profile mutations,
**When** both commands finish,
**Then** each transaction reloads the latest file under the lock and neither successful change is lost,
**And** a simulated interrupted write leaves either the complete previous file or the complete new file.

**Given** Linux and Windows test environments,
**When** Profile files are created and updated,
**Then** tests verify the required permissions or ACLs on the directory, target, temporary, and lock files,
**And** the tool never opens the admin CLI's Profile path.

### Story 2.4: Browse the Catalog from the CLI

As a shell user,
I want to list Modules and Operations and describe one Operation without a Gateway connection,
So that I can choose a valid call and inspect its Schema before executing it.

**Requirements:** FR4, FR5, FR6, FR11, FR12, FR14

**Acceptance Criteria:**

**Given** a Catalog and no resolved Gateway URL,
**When** I run `hexalith modules`, `operations <module> [--kind read|write]`, or `describe <operation>`,
**Then** each command returns the exact addendum §G JSON document with canonical names, ordering, descriptions, Schema, Envelope arguments, lint findings, and `submittable: false` with `reason: configuration_invalid`,
**And** no Gateway client call occurs.

**Given** a nonempty unknown Module Name or Operation Name,
**When** I run `operations` or `describe`,
**Then** the CLI returns `unknown_module` or `unknown_operation` with at most three suggestions ordered by case-insensitive edit distance and ordinal ties,
**And** a missing or empty `module` returns `invalid_arguments` before Catalog dispatch.

**Given** `describe --lint`,
**When** the Operation has lint findings,
**Then** the same describe result is written with exit code 1,
**And** `describe` without `--lint` writes that result with exit code 0.

**Given** `--format table`,
**When** I run `modules`, `operations`, or a `config` display verb,
**Then** the CLI renders their declared columns as a table,
**And** `describe` stays JSON, emits one stderr note, and keeps its result-based exit code.

**Given** Catalog diagnostics or an empty Catalog,
**When** I run a discovery verb with and without `--strict`,
**Then** ordinary mode retains valid results, strict mode returns `catalog_invalid` for any diagnostic, and an empty Catalog returns `catalog_empty`,
**And** `config` and `--version` remain available without building the Catalog.

### Story 2.5: Run a Valid Query Through the Gateway

As a shell user,
I want `hexalith query` to submit a decorated Query through the shared executor,
So that I can read business data with the same routing the agent will use.

**Requirements:** FR12, FR15, FR16, FR17

**Acceptance Criteria:**

**Given** the pinned EventStore client and a throwaway Gateway harness before Story 4.12 creates this repository's test AppHost,
**When** the `tenants.list-tenants` Query spike runs against EventStore Gateway and Tenants started locally through the existing EventStore AppHost and root-declared checkouts,
**Then** the harness calls the pinned client directly and receives a page without depending on a decorated Tenants Contracts release or the Story 4.12 topology,
**And** the spike records the local startup path, Gateway endpoint, required test identity, request routing, and response evidence without storing credentials.

**Given** the existing Tenants list Query route uses `index` as its aggregate identifier,
**When** the spike selects the candidate `aggregateId` constant before Story 4.8,
**Then** it verifies `index` against the pinned Gateway identifier pattern and the live `tenants.list-tenants` response, recording the source and result,
**And** Story 4.8's Tenants maintainer confirms or corrects that candidate when declaring the final list-Query constant in the owning Contracts package.

**Given** a valid Query, Payload, Gateway URL, and resolved Tenant,
**When** I run `hexalith query <operation>` with `--payload <json>`, `--payload @file`, or stdin,
**Then** the executor validates the Payload against the Catalog Schema and sends one `SubmitQueryRequest` through `IEventStoreGatewayClient`,
**And** its domain, Wire Type, projection, and aggregate identifier come from the descriptor rather than the Operation Name.

**Given** an explicit aggregate identifier, a compiled property accessor, or a Query constant,
**When** the executor resolves the aggregate identifier,
**Then** it uses explicit argument, accessor, then constant in that order; an explicit value may override the constant,
**And** a disagreement with an accessor value or a missing result returns `validation_failed` without a Gateway call.

**Given** a Module with `fixedTenant`, session Tenant, and optional per-call Tenant in the Core argument record,
**When** the executor resolves the Tenant,
**Then** fixed Tenant wins, while a per-call Tenant is honored only when no session Tenant exists or the operator enabled override,
**And** a differing disallowed per-call value or missing Tenant returns `validation_failed` before submission.

**Given** a successful Gateway Query response,
**When** the CLI writes the result,
**Then** it emits the addendum §G `run_query` document with required `operation`, `tenant`, and `document` fields, including a JSON null document when returned,
**And** Query requests and results contain no synthesized correlation identifier or extensions.

### Story 2.6: Validate and Page Query Calls

As a shell user,
I want invalid Query inputs rejected before submission and paging handled in the Envelope,
So that a failed call is actionable and a successful read preserves Gateway paging.

**Requirements:** FR4, FR15, FR16, FR17

**Acceptance Criteria:**

**Given** malformed JSON or a Payload with multiple Schema violations,
**When** I invoke a Query,
**Then** the executor returns `validation_failed` with every violation and RFC 6901 path; malformed JSON is one violation at `/`,
**And** the Gateway client records zero calls.

**Given** a Query aggregate identifier in an `Ulid`-kind or `String`-kind Module, plus Tenant and entity identifiers,
**When** execution validates the resolved Envelope,
**Then** it uses `Ulid.TryParse` for `Ulid`, nonempty validation for `String`, and the Gateway's published patterns and lengths for Tenant, aggregate, and entity identifiers,
**And** each invalid value produces a violation at `/tenant`, `/aggregateId`, or `/entityId` before submission.

**Given** `--page-size`, `--offset`, or `--cursor`,
**When** I run a Query,
**Then** valid values map only to `SubmitQueryRequest.Paging`,
**And** page size outside 1–200, negative offset, cursor longer than 4,096 characters, or a nonblank cursor combined with offset fails at the matching pointer without a Gateway call.

**Given** a Query Payload with a member named `PageSize`, `Offset`, or `Cursor`,
**When** the Query is sent,
**Then** that member remains ordinary Payload and is neither stripped nor mapped to paging,
**And** the Catalog lint flags the member separately.

**Given** a Query declaring `tenantProperty` and a resolved Envelope Tenant,
**When** its Payload is prepared for submission,
**Then** a matching or omitted property is filled from the Envelope and the rebuilt Payload is validated again,
**And** a conflicting caller value returns `validation_failed` without a Gateway call.

**Given** Gateway paging metadata,
**When** a Query succeeds,
**Then** the result includes `paging.pageSize` and independently includes only the available offset, next cursor, total count, and has-more fields,
**And** absent metadata is omitted rather than replaced by defaults.

**Given** no resolved Gateway URL,
**When** execution reaches the Query preflight,
**Then** it returns `configuration_invalid` without creating a Gateway request,
**And** offline Catalog discovery remains available.

### Story 2.7: Submit a Command Once

As a shell user,
I want `hexalith send` to submit a decorated Command and return traceable identifiers,
So that I can perform a business action and inspect its accepted result.

**Requirements:** FR12, FR15, FR16, FR17

**Acceptance Criteria:**

**Given** a valid Command, Payload, Gateway URL, Tenant, and aggregate identifier,
**When** I run `hexalith send <operation>` with inline JSON, `@file`, or stdin,
**Then** the shared executor validates the Payload and sends exactly one `SubmitCommandRequest` through `IEventStoreGatewayClient`,
**And** the request uses Catalog routing values rather than the public Operation Name.

**Given** a write Operation named through `run_query` or `hexalith query`, or a read Operation named through `send_command` or `hexalith send`,
**When** the shared executor resolves the descriptor in either writable or Read-only Mode,
**Then** it returns `validation_failed` at `/operation` before availability or Payload checks,
**And** a direct Core call has the same result with zero Gateway calls.

**Given** a Command call with no correlation identifier,
**When** the executor builds its Envelope,
**Then** it generates one ULID message identifier and uses that same value as the resolved correlation identifier,
**And** separate calls generate different message identifiers without generating an idempotency key.

**Given** caller-supplied correlation and idempotency identifiers,
**When** they are valid ULIDs,
**Then** the executor passes them through unchanged and echoes the idempotency key only when supplied,
**And** invalid values return `validation_failed` without a Gateway call.

**Given** an `ICommandContract` aggregate identifier getter or an `aggregateIdProperty` accessor,
**When** a Command includes an explicit aggregate identifier,
**Then** the executor compares it with the compiled accessor value using ordinal equality,
**And** a disagreement returns `validation_failed` at `/aggregateId` without submission.

**Given** a successful Gateway Command response,
**When** the CLI writes the result,
**Then** it emits the addendum §G Command document with canonical Gateway `messageId`, resolved `correlationId`, Tenant, aggregate identifier, and `status: accepted`,
**And** the returned correlation identifier matches the one submitted, `result` appears only when the Gateway returned a payload, and no `duplicate` field is invented.

**Given** a timeout or unknown Command outcome,
**When** the gateway client call ends without a success response,
**Then** the executor does not retry or claim generic deduplication,
**And** the error does not imply that another submission is safe.

### Story 2.8: Protect Command Identity and Extensions

As an operator,
I want Command identity fields and extensions resolved under my session policy,
So that an agent cannot silently impersonate an Actor or change the Tenant.

**Requirements:** FR15, FR16, FR17, NFR5

**Acceptance Criteria:**

**Given** a Command declaring `tenantProperty` or `actorProperty`,
**When** the executor receives a Payload and resolved session Tenant and Actor,
**Then** it rejects a conflicting caller value, requires Actor when declared, and fills matching or omitted fields from the session context,
**And** Tenant and Actor are never taken from a per-call Payload value.

**Given** a Command declaring `correlationProperty` or `idempotencyKeyProperty`,
**When** the executor builds the Envelope,
**Then** it overwrites the correlation Payload field with the resolved command correlation identifier and fills the idempotency field only when the caller supplied a key,
**And** a non-nullable or serializer-required idempotency field without a supplied key returns `validation_failed` at `/idempotencyKey`, including a required nullable member; without a key, a non-null raw field also fails and a raw null is removed before submission.

**Given** raw null or incorrectly typed idempotency fields and invalid raw correlation values,
**When** the caller supplies a valid Envelope key and correlation resolves,
**Then** pre-fill validation checks a copy without mapped envelope-owned members while retaining all ordinary/unknown-member constraints,
**And** the raw values are overwritten before complete-Payload validation, with no premature schema rejection.

**Given** no caller key and a declared idempotency member,
**When** raw ownership checks run,
**Then** a non-null raw value fails at `/idempotencyKey`, a raw null is removed, and an omitted required key fails at `/idempotencyKey` before materialization,
**And** raw null, non-string, or conflicting Tenant/Actor values fail at their mapped property pointers before overwrite with zero Gateway calls.

**Given** a contract whose required tenant, actor, or correlation member is envelope-filled and whose `ICommandContract.AggregateId` getter is computed,
**When** the caller omits those allowed Payload members,
**Then** the executor fills them and validates the rebuilt Payload before deserializing the contract for the getter,
**And** a conflicting supplied Tenant or Actor is still `validation_failed` with zero Gateway calls.

**Given** a Command Payload of JSON null or another non-object root,
**When** Core validates it against the advertised Schema,
**Then** it returns `validation_failed` at `/` before accessor use or Gateway submission,
**And** a nested null permitted by the contract Schema remains valid.

**Given** Command extensions and the Profile's allowed extension keys,
**When** the executor validates them,
**Then** only allowlisted keys pass, using case-insensitive membership and the pinned Gateway sanitizer's grammar and injection checks,
**And** it rejects more than 32 entries, keys over 100 characters, values over 1,000 characters, or a combined UTF-8 size over 4,096 bytes at `/extensions` or the escaped key pointer before submission.

**Given** Envelope-filled Payload fields,
**When** the executor has filled them,
**Then** it validates the rebuilt Payload against the stored Schema before constructing the Gateway request,
**And** any violation leaves the Gateway client with zero calls.

**Given** the tool host's Gateway client registration,
**When** a Command is submitted,
**Then** there is one Gateway `HttpClient` registration with the host's static bearer handler,
**And** Core does not read the token or register an authentication handler.

### Story 2.9: Explain Execution Failures with Stable Documents

As a shell user,
I want each failed call to return a structured error with useful details,
So that a script or agent can decide what to fix or inspect next.

**Requirements:** FR11, FR14, NFR5

**Acceptance Criteria:**

**Given** a Gateway Problem Details response, malformed successful Command or Query response, or semantic Query failure reported by `EventStoreGatewayException`,
**When** the executor maps the exception,
**Then** `gateway_error` preserves the exception's actual integer status, including a possible `2xx`, and uses the first nonempty Detail or Title,
**And** reason, retryable, client action, retry-after, and correlation identifier appear only when the client exception supplies them.

**Given** an unknown Operation Name,
**When** execution or description looks it up,
**Then** `unknown_operation` includes the requested name and at most three nearest canonical names,
**And** suggestions are ordered by case-insensitive edit distance with ordinal tie-breaking.

**Given** a Payload or Envelope validation failure,
**When** the executor returns `validation_failed`,
**Then** the document includes the Operation Name and a nonempty array of path-and-message violations,
**And** no Gateway request is made.

**Given** an unexpected exception outside expected validation and Gateway failures,
**When** the tool maps it,
**Then** it returns `internal_error` with a message and no stack trace or token,
**And** the CLI uses the same `{ "error": ... }` shape as Core.

**Given** fixtures for every addendum §G success and error variant,
**When** their records are serialized with `McpCliJson.Result`,
**Then** required members, types, constraints, enum values, empty arrays, and optional-member omission match the contract,
**And** the CLI writes an error document with exit code 2 and no result document.

### Story 2.10: Refuse Writes in Read-only Mode

As an operator,
I want a Read-only session that refuses Command submission,
So that exploration cannot accidentally change business state.

**Requirements:** FR19

**Acceptance Criteria:**

**Given** `--read-only` or `EVENTSTORE_READ_ONLY=true`,
**When** I run `hexalith send <operation>`,
**Then** the CLI returns `read_only` with exit code 2,
**And** the Gateway client records zero calls.

**Given** a write Operation invoked directly through `IOperationExecutor` in Read-only Mode,
**When** execution starts,
**Then** it returns `read_only` before Payload parsing or Gateway submission,
**And** a missing Gateway URL does not replace the `read_only` reason.

**Given** Read-only Mode,
**When** I list or describe Operations,
**Then** Commands still appear as kind `write` and describe reports `submittable: false, reason: read_only`,
**And** Queries and discovery remain available.

**Given** Read-only Mode on a read verb,
**When** I execute a valid Query,
**Then** it follows the normal Query path,
**And** the flag causes no additional validation failure.

### Story 2.11: Keep CLI Output and Exit Codes Predictable

As a shell user,
I want a stable output and exit-code contract across verbs,
So that scripts can distinguish results, lint findings, and failures.

**Requirements:** FR12, FR13, FR14, NFR4

**Acceptance Criteria:**

**Given** a successful non-MCP verb,
**When** I use the default format or `--output <file>`,
**Then** the canonical JSON result goes to stdout or the chosen file respectively,
**And** logs, Catalog diagnostics, and format notes go only to stderr.

**Given** `--format table`,
**When** I run `modules`, `operations`, or a `config` display verb,
**Then** the supported table is rendered,
**And** `describe`, `send`, and `query` still emit JSON with one stderr note and unchanged exit behavior.

**Given** a successful result, a `describe --lint` result with findings, or any no-result failure,
**When** the CLI exits,
**Then** it uses code 0, 1, or 2 respectively,
**And** normal Catalog diagnostics do not alter that code unless `--strict` was requested.

**Given** a missing required CLI argument, unsupported format, or invalid setting,
**When** input binding or configuration fails,
**Then** the CLI emits the matching addendum §G error document with exit code 2,
**And** it does not emit a partial result.

**Given** `hexalith mcp --transport http`,
**When** the verb parses the transport before Catalog construction,
**Then** it exits 2 with `unsupported_transport` and a message naming the next release,
**And** because the server has not started serving MCP requests, the structured error goes to stderr with zero stdout bytes.

## Epic 3: Agents Can Use One Generic MCP Server

An MCP-capable agent can discover and execute every available Operation through five fixed tools over stdio, with the same behavior and documents as the CLI; a Read-only session exposes only four tools.

### Story 3.1: Discover Operations Through a Fixed MCP Surface

As an LLM agent,
I want a small, stable set of discovery tools,
So that I can understand available Modules and Operations without a tool per Operation.

**Requirements:** FR9, FR19, NFR2

**Acceptance Criteria:**

**Given** a normal session,
**When** the MCP SDK lists tools,
**Then** it advertises exactly `list_modules`, `list_operations`, `describe_operation`, `send_command`, and `run_query` in fixed order,
**And** each tool is created with `McpServerTool.Create`, listed through a pinned SDK post-handler ordering filter, dispatched through its built-in call path, and described with labeled `Purpose`, `Use when`, and `Next` parts.

**Given** a Read-only session,
**When** the server registers its one filtered `ToolCollection`,
**Then** `send_command` is absent and the other four tools remain in the same order in fresh `tools/list` protocol sessions,
**And** direct write execution is still refused by the shared executor.

**Given** the tool definitions,
**When** their annotations and input schemas are inspected,
**Then** discovery tools and `run_query` have `readOnlyHint: true`, while `send_command` has `readOnlyHint: false`, `idempotentHint: false`, and `destructiveHint: true`,
**And** the five names, descriptions, and input schemas together contain fewer than 8,000 characters.

**Given** a Catalog, with or without a Gateway URL,
**When** the tools are invoked through an in-process MCP SDK test host,
**Then** `list_modules`, `list_operations` with optional kind filter, and `describe_operation` return the addendum §G discovery documents using the §E arguments, including Operation counts, Schema, example when present, Envelope arguments, lint findings, and head-level `submittable`,
**And** a missing URL affects execution availability rather than offline discovery.

**Given** a nonempty unknown Module Name or a missing `module` argument,
**When** the agent calls `list_operations`,
**Then** the former returns `unknown_module` with suggestions and the latter fails MCP input binding before Catalog dispatch,
**And** the server adds no per-Operation tools as the Catalog grows.

### Story 3.2: Run the MCP Server over Clean Stdio

As an agent operator,
I want `hexalith mcp` to start as a local stdio server without a prompt,
So that an MCP client can connect reliably and parse every response.

**Requirements:** FR10, FR14, NFR4

**Acceptance Criteria:**

**Given** settings from a Profile or environment variables,
**When** I run `hexalith mcp --transport stdio`,
**Then** the existing tool Host resolves settings once, builds the Catalog, and starts the pinned SDK's stdio transport,
**And** no interactive prompt or second settings resolver appears.

**Given** valid inherited `format: table` settings or explicit `--format json`,
**When** `mcp --transport stdio` starts under the adopted AD-13 policy,
**Then** it serves JSON-RPC normally with no formatting note,
**And** inherited format settings do not alter the protocol stream.

**Given** explicit `--format table` or any `--output` on `mcp --transport stdio`,
**When** the composition root checks the parsed flags,
**Then** it emits one stderr `invalid_arguments` document naming `format` or `output` (format first if both), exits 2 with zero stdout, and opens no output path,
**And** neither Catalog construction nor transport startup has begun; malformed inherited settings still fail normal validation.

**Given** a valid Catalog and no Gateway URL,
**When** an SDK client establishes a session through the version-appropriate flow, lists tools, and calls a discovery tool,
**Then** the exchange completes over JSON-RPC without a parse error,
**And** offline discovery remains available.

**Given** normal startup and tool calls,
**When** the server logs or reports Catalog diagnostics,
**Then** stdout contains JSON-RPC frames only and logging goes to stderr through the configured provider and source-generated log methods,
**And** no `Console.WriteLine` call writes from the MCP server.

**Given** malformed settings, an empty Catalog, or a `--strict` Catalog diagnostic,
**When** startup fails before the server starts serving MCP requests,
**Then** the process writes exactly one structured error to stderr and zero bytes to stdout, then exits 2,
**And** no partial MCP session is advertised.

**Given** an MCP session serving requests,
**When** a tool call fails,
**Then** the failure travels through MCP/JSON-RPC only,
**And** the server does not write a second structured error document to stderr.

### Story 3.3: Execute Calls with Structured MCP Results

As an LLM agent,
I want Command and Query calls to return the same structured documents as the CLI,
So that I can reason about results and failures without a separate MCP dialect.

**Requirements:** FR9, FR11, FR12, NFR7

**Acceptance Criteria:**

**Given** the addendum §E MCP arguments,
**When** I call `send_command` or `run_query`,
**Then** the MCP Head binds them to the shared Core argument records and calls the same executor as the CLI,
**And** only MCP may supply a per-call Tenant, subject to the operator gate already enforced by Core.

**Given** a successful Command or Query call,
**When** the MCP tool returns,
**Then** `structuredContent` contains the canonical addendum §G result document,
**And** its JSON fields and omission rules match the CLI's Core-owned record for the same inputs.

**Given** a Core error,
**When** an MCP tool returns it,
**Then** the result has `isError: true`, `structuredContent.error` with the exact §G variant, and matching JSON in `Content[0].Text`,
**And** no exception escapes the tool boundary.

**Given** each advertised tool,
**When** its output schema is inspected and used to validate success and error fixtures,
**Then** the root is an object with closed success and `{ error: ... }` branches in `oneOf`,
**And** both branches conform under a pre-2026-07-28 MCP protocol version and the 2026-07-28 revision, with output-schema size measured separately from the input-tool budget.

**Given** an SDK stdio client and a substituted Gateway client,
**When** it establishes a session through the version-appropriate flow, lists tools, and calls each available tool once,
**Then** every call completes without a JSON-RPC parse error,
**And** execution without a resolved URL returns `configuration_invalid` while discovery remains usable.

## Epic 4: Maintainers Can Verify and Release v1 Coverage

Maintainers can demonstrate that approved Tenants and Parties Operations work through both Heads, have the required migration inventory and conformance evidence, and release the generic tool with an authoritative rule against new per-Module agent servers and CLIs.

### Story 4.1: Approve the Parties Migration Inventory

As a McpCli maintainer,
I want an approved inventory of every Parties Legacy Server operation,
So that v1 coverage can be checked against an explicit replacement scope.

**Requirements:** FR21

**Acceptance Criteria:**

**Given** the current `Hexalith.Parties.Mcp` surface,
**When** its tools and resources are inventoried,
**Then** every legacy operation has a versioned row outside `src/` marked `include` or `exclude`,
**And** each row records its rationale and the Parties maintainer's approval reference.

**Given** an included Parties write or read,
**When** its row is reviewed,
**Then** it names the intended canonical Operation Name and decorated Contracts type,
**And** an included read identifies the Query contract needed to replace its Legacy Server behavior.

**Given** erasure, key rotation, or another excluded legacy behavior,
**When** the inventory is approved,
**Then** its exclusion has a specific rationale rather than being omitted,
**And** the inventory remains a migration and test artifact rather than runtime configuration.

**Given** the open Parties routing decision,
**When** decoration work begins,
**Then** the maintainer records whether Commands retain attribute routing with full-type-name Wire Types or adopt `ICommandContract`,
**And** any wire-breaking choice is explicit before the Contracts package is published.

### Story 4.2: Approve the Folders Migration Inventory

As a McpCli maintainer,
I want the Folders server and Frozen CLI mapped to Gateway-ready Operations,
So that its large REST surface has an agreed migration scope.

**Requirements:** FR21

**Acceptance Criteria:**

**Given** the Folders Legacy Server's 49 tools and the Folders Frozen CLI,
**When** their agent-facing operations are inventoried,
**Then** every operation has a versioned include or exclude row with rationale and Folders maintainer approval,
**And** included rows name a canonical Operation and intended decorated Command or Query type.

**Given** an operation with dry-run, redaction, freshness, or another REST-only behavior,
**When** the row is classified,
**Then** inclusion identifies where equivalent behavior will live in Gateway handlers, or exclusion records the lost behavior and reason,
**And** the inventory does not claim parity merely because a name matches.

**Given** a tool or resource whose effect is not a Gateway Command or Query,
**When** it is reviewed,
**Then** the row explicitly excludes it or records the future Gateway prerequisite,
**And** the generic McpCli runtime gains no Folders-specific branch.

**Given** the approved inventory,
**When** migration readiness is reported,
**Then** Folders remains a post-v1 addition until its Contracts package satisfies the dependency allowlist and its included Operations pass Gateway coverage,
**And** its Legacy Server and Frozen CLI are not marked deletable early.

### Story 4.3: Approve Projects and FrontComposer Migration Inventories

As a McpCli maintainer,
I want the FrontComposer host and Projects plug-in inventoried together,
So that their shared deletion gate is based on agreed Operation coverage.

**Requirements:** FR21

**Acceptance Criteria:**

**Given** `Hexalith.FrontComposer.Mcp`, its Projects plug-in, and their Frozen CLIs,
**When** the surfaces are inventoried,
**Then** each legacy operation has a versioned include or exclude row with rationale, intended canonical Operation and decorated type when included, and the owning maintainer's approval reference,
**And** the inventories distinguish host behavior from Projects business Operations.

**Given** the Projects server's resource reads, including its 11 known resources,
**When** an included row is defined,
**Then** it identifies the Query contract and Gateway semantics needed for parity,
**And** a stream, file, or deferred search/freshness variant has an approved exclusion row.

**Given** Projects task and actor context or its current server-side Tenant guard,
**When** a row is approved,
**Then** it records whether context becomes ordinary Payload, `actorProperty`, or allowed Envelope extensions and where the Tenant guard moves for direct Gateway submission,
**And** no Projects-specific behavior is assigned to generic McpCli code.

**Given** the approved inventories,
**When** deletion readiness is evaluated,
**Then** FrontComposer's host and the Projects plug-in are marked deletable only together after Projects is Gateway-ready and passes coverage,
**And** Projects' dependency-heavy Contracts package must first be slimmed to the allowlist.

### Story 4.4: Approve ChatBot and Memories Migration Inventories

As a McpCli maintainer,
I want the remaining legacy agent surfaces inventoried,
So that their later replacement preserves the behavior and identity guarantees users depend on.

**Requirements:** FR21

**Acceptance Criteria:**

**Given** the ChatBot and Memories Legacy Servers and Frozen CLIs,
**When** their operations are inventoried,
**Then** every agent-facing operation has a versioned include or exclude row with rationale, intended canonical Operation and decorated type when included, and maintainer approval,
**And** the rows remain outside runtime source and configuration.

**Given** ChatBot task, actor, Tenant, or correlation context,
**When** an included row is reviewed,
**Then** it states how that context will travel as Payload, an allowed Envelope field, or an operator setting,
**And** the generic executor gains no ChatBot-specific path.

**Given** a Memories operation that currently depends on per-user JWT identity,
**When** its migration status is assessed,
**Then** the inventory records that identity requirement and the Gateway-ready replacement path,
**And** the Memories Legacy Server is not marked deletable before the HTTP release supports forwarded per-user identity.

**Given** a legacy resource or behavior outside v1's Gateway Command and Query contract,
**When** the inventory is approved,
**Then** it has an explicit exclusion with rationale,
**And** no missing row is treated as implicit parity.

### Story 4.5: Gate Module Coverage Against the Approved Inventory

As a McpCli maintainer,
I want an automated comparison between approved legacy inventories and the built Catalog,
So that a release cannot silently omit or misidentify an Operation.

**Requirements:** FR20, FR21

**Acceptance Criteria:**

**Given** a versioned inventory with include and exclude rows,
**When** the generic coverage check runs for a Module,
**Then** every included canonical Operation Name appears exactly once in `list_operations <module>` and maps to the named decorated CLR contract type in `OperationDescriptor.ContractType`,
**And** CLR type names remain absent from public discovery documents.

**Given** a legacy operation that is missing, extra, duplicated, mapped to a different type, or excluded without approval and rationale,
**When** the check runs,
**Then** it fails with the specific row and mismatch,
**And** it does not treat conformance-vector coverage as a substitute for inventory coverage.

**Given** a synthetic approved inventory and matching Catalog fixture,
**When** the generic coverage gate runs,
**Then** its include, exclude, duplicate, and CLR-type checks pass or fail as specified without requiring a future Parties package,
**And** the gate can be applied to Parties once its decorated Contracts release is available.

**Given** the inventory files and the generic runner,
**When** production code is inspected,
**Then** inventories are consumed only by planning and tests,
**And** no Module Name, CLR type name, or per-Module branch from an inventory is embedded in runtime configuration or source.

### Story 4.6: Publish the Bootstrap Decoration Package

As a Module maintainer,
I want a validated `Hexalith.McpCli.Abstractions` package available before decorating upstream Contracts,
So that Tenants and Parties can adopt the common declarations without waiting for the full tool release.

**Requirements:** FR1, FR20, NFR6

**Acceptance Criteria:**

**Given** the completed Abstractions project and author-time tests,
**When** the one-time bootstrap CI gate runs,
**Then** it builds and packs only `Hexalith.McpCli.Abstractions` at the chosen version and verifies its exact package ID, version, analyzer contents when present, and zero consumer-visible package-reference closure,
**And** decorated Contracts pins, the unreleased tool, and the Aspire tier are not required for this bootstrap gate.

**Given** the bootstrap release workflow,
**When** publication is requested,
**Then** it checks a green source SHA, an available version, credentials, and validated staged package contents before pushing,
**And** only the validated Abstractions package is published from that phase.

**Given** upstream Hexalith.Builds version management,
**When** the package version is introduced,
**Then** the `HexalithMcpCliVersion` property is added in the owning Builds repository for later paired releases,
**And** this repository's read-only `references/` checkout is not edited as the upstream change.

**Given** the published Decoration Package,
**When** Tenants or Parties begins decoration,
**Then** its Contracts library can take one exact package reference,
**And** no per-Module MCP server or CLI implementation is needed for the declaration itself.

### Story 4.7: Enforce the Production Dependency Boundary

As a McpCli maintainer,
I want a restored-assets gate for the dependency allowlist,
So that adding a Module cannot pull server or UI packages into the global tool.

**Requirements:** FR20, NFR6

**Acceptance Criteria:**

**Given** the tool's restored assets,
**When** the dependency gate runs,
**Then** it permits only the first-party Decoration Package, the pinned EventStore client, flagged exposed `*.Contracts` packages, and the named pinned Stack packages as direct production roots,
**And** it verifies the exact approved transitive identities and versions from the EventStore and Stack baseline.

**Given** an exposed Contracts package that adds another package identity, a forbidden framework reference, or a Module aggregate, projection, handler, client, or server project reference,
**When** the gate runs,
**Then** it fails with the offending dependency path,
**And** it does not widen the allowlist without a PRD change.

**Given** the approved test projects,
**When** the same policy is evaluated,
**Then** their named EventStore testing and Aspire composition dependencies plus the synthetic sample Contracts fixture are allowed only in tests,
**And** the production tool never references the sample fixture.

**Given** a candidate `Hexalith.Projects.Contracts` pin with its current web and UI closure,
**When** the gate evaluates it,
**Then** it fails and leaves Projects outside the tool until the upstream Contracts package is slimmed,
**And** Tenants and Parties can be admitted when their exact decorated pins pass the same gate.

### Story 4.8: Make Tenants Gateway-ready for v1

As a Tenants maintainer,
I want its supported Commands and Queries declared in the published Contracts package,
So that the generic tool can expose tenant operations without Tenants-specific code.

**Requirements:** FR3, FR20, NFR8

**Vector prerequisite:** Complete Story 1.8 and use its approved contract and shared validator before authoring Tenants vectors.

**Acceptance Criteria:**

**Given** the published Decoration Package,
**When** the Tenants Contracts library is updated in its owning repository,
**Then** its Module marker declares `name: tenants`, `identifierKind: String`, and `fixedTenant: system`,
**And** every v1 agent-facing Command and Query has a reviewed description, valid example, and stable canonical Operation Name.

**Given** per-tenant and list-style Tenants Queries,
**When** they are decorated,
**Then** per-tenant reads declare an aggregate identifier property and list reads declare a Gateway-valid aggregate identifier constant,
**And** exposed paged handlers consume `QueryEnvelope.Paging`; retained legacy Payload paging members cannot govern generic requests even when their lint findings are accepted.

**Given** audit entries that differ in time and category,
**When** a live conformance scenario sends non-default `From`, `To`, and `Category` using the contract's effective serialized names,
**Then** the upstream handler returns the expected filtered records,
**And** successful status alone cannot pass the audit-filter readiness gate.

**Given** sufficient records for multiple pages,
**When** a live scenario requests a non-default page size and then the returned continuation cursor through Envelope paging,
**Then** the actual page sizes and contents match the vector's expectations,
**And** Gateway-ready acceptance remains blocked until both handler migrations and these semantic vectors pass against the decorated Contracts release and matching live handler source.

**Given** Tenants' global-administrator Commands,
**When** v1 scope is checked,
**Then** those Commands remain outside the decorated v1 Catalog as specified by the PRD,
**And** the included Operations use their contract interface routing without redundant attribute values.

**Given** the first approved decorated Tenants Contracts release,
**When** its exact package version is flagged in the tool,
**Then** `list_operations tenants` exposes every decorated Operation and the dependency gate passes,
**And** adding the Module required only the package pin and rebuild in this repository.

**Given** each exposed Tenants Operation,
**When** its owning-repository conformance vector is reviewed,
**Then** the vector has valid Payload, Envelope, prerequisites, and semantic assertions with maintainer approval,
**And** no Operation lacks a versioned vector validated against the McpCli-owned contract approved before upstream authoring.

**Given** the generated Tenants Catalog dump,
**When** someone unfamiliar with its source reviews descriptions,
**Then** every exposed description is understandable without source context and the review is recorded in the Tenants pull request,
**And** hollow-description lint findings are resolved or explicitly tracked before release.

### Story 4.9: Declare Parties Commands for the Gateway

As a Parties maintainer,
I want the approved write operations decorated in Contracts,
So that the generic Catalog can expose them with correct Gateway routing.

**Requirements:** FR20, FR21, NFR8

**Vector prerequisite:** Complete Story 1.8 and use its approved contract and shared validator before authoring Parties Command vectors.

**Acceptance Criteria:**

**Given** the approved Parties inventory and Decoration Package,
**When** Parties Command contracts are decorated in their owning repository,
**Then** every included write has a reviewed description, valid example, stable canonical Operation Name, and `String`-kind Module marker,
**And** excluded writes remain documented in the inventory rather than silently disappearing.

**Given** the maintainer's recorded routing choice,
**When** the Catalog builds Parties Command descriptors,
**Then** it resolves domain, Wire Type, and aggregate identifier source from the chosen attribute or `ICommandContract` path,
**And** current full-type-name Wire Types stay stable unless the approved choice explicitly includes a breaking wire migration.

**Given** an attribute-routed Parties Command,
**When** its aggregate identifier is read,
**Then** the declared `PartyId` property supplies the identifier and passes `String`-kind and Gateway pattern validation,
**And** the Envelope Tenant is resolved by the generic executor rather than from Payload.

**Given** each included Parties Command,
**When** its versioned conformance vector is reviewed,
**Then** it contains valid Payload and Envelope inputs, prerequisite calls, and semantic success assertions with maintainer approval,
**And** it passes the same McpCli-owned vector validator as Tenants before approval, while the command set can be inspected by `CatalogBuilder` without Parties-specific runtime code.

### Story 4.10: Add Parties Queries and Pin Complete Coverage

As a Parties maintainer,
I want each approved read represented by a decorated Query in a published Contracts package,
So that v1 can expose the full approved Parties surface through the Gateway.

**Requirements:** FR20, FR21, NFR8

**Vector prerequisite:** Complete Story 1.8 and use its approved contract and shared validator before authoring Parties Query vectors.

**Acceptance Criteria:**

**Given** each included Parties read in the approved inventory,
**When** a Query contract is added,
**Then** it declares its description, valid example, Gateway domain and Wire Type, projection type, and `projectionActorType` where the named actor serves the projection,
**And** list-style reads use the existing Gateway-valid `parties` aggregate identifier constant.

**Given** each new Parties Query,
**When** its versioned conformance vector is reviewed,
**Then** it supplies valid Payload and Envelope values, generic prerequisites, and semantic Query assertions with maintainer approval,
**And** it passes the same McpCli-owned vector validator as Tenants before approval, while the Query is accepted by the Gateway without a Parties-specific McpCli path.

**Given** the complete decorated Parties Contracts release,
**When** its exact version is flagged in the tool project,
**Then** the dependency closure gate passes and `list_operations parties` exposes every decorated write and read,
**And** no unapproved package identity or Module server/client reference is introduced.

**Given** the approved Parties inventory and built Catalog,
**When** the generic inventory gate runs,
**Then** every included canonical name and decorated CLR type matches exactly once, every exclusion remains approved, and no extra Parties Operation appears,
**And** this gate blocks the v1 release on mismatch.

**Given** the generated Parties Catalog dump,
**When** someone unfamiliar with its source reviews descriptions,
**Then** every exposed Command and Query description is understandable without source context and the review is recorded in the Parties pull request,
**And** hollow-description lint findings are resolved or explicitly tracked before release.

### Story 4.11: Prove Both Heads Agree Against a Loopback Gateway

As a McpCli maintainer,
I want deterministic out-of-process parity evidence for every exposed Operation,
So that the CLI and MCP server cannot ship different behavior for the same call.

**Requirements:** FR11, FR20, NFR1, NFR3, NFR7

**Dependencies:** Story 1.8's approved vector contract and validator, both implemented Heads, and the decorated Contracts releases and approved vectors from Stories 4.8–4.10.

**Acceptance Criteria:**

**Given** the built production Catalog and approved Module-owned conformance vectors,
**When** the generic runner starts,
**Then** it reuses Story 1.8's contract and shared validator, rechecks each vector's Contracts package ID and exact version against the flagged restored package, and rejects missing, duplicate, stale, or incompatible vectors for any listed Operation,
**And** it contains no Module-specific setup branch or production test hook.

**Given** a vector's valid inputs and reset scripted loopback Gateway responses,
**When** the runner drives the CLI process and MCP stdio client separately,
**Then** discovery, success, and error documents are equal after canonical serialization, masking only generated message and correlation identifiers,
**And** caller-supplied idempotency keys remain unmasked, equal, and present or absent in both results as supplied.

**Given** the requests captured from both Heads,
**When** the runner compares them,
**Then** method, path, routing, Envelope, Payload, and paging match each other and the vector's expected inputs after the same limited identifier masking,
**And** the loopback script resets between Head runs.

**Given** benchmark Catalog construction,
**When** CI measures the v1 Modules plus exactly one declared synthetic sample Module on `ubuntu-latest`,
**Then** the build completes within NFR1's 500 ms limit,
**And** the other Identifier Kind is tested by isolated Catalog construction rather than a second production-like Module.

### Story 4.12: Compose the v1 Live Test Topology

As a test maintainer,
I want a repeatable EventStore, Tenants, and Parties topology,
So that approved Operations can be checked against a real Gateway.

**Requirements:** FR20, NFR7

**Acceptance Criteria:**

**Given** the Parties repository,
**When** its maintainer publishes `Hexalith.Parties.Aspire`,
**Then** the helper has an exact version and no server package dependency, and locates its server source through root-declared workspace checkouts,
**And** the helper is changed in its owning repository rather than inside this repository's `references/` checkout.

**Given** published EventStore, Tenants, and Parties Aspire helpers,
**When** `tests/Hexalith.McpCli.AppHost` starts,
**Then** it composes the v1 Gateway and domain services through those helpers,
**And** the test project does not reference a Module aggregate, projection, handler, client, or server package.

**Given** the integration test fixture,
**When** it starts the AppHost,
**Then** it uses `AspireTopologyFixtureBase` and the standard Dapr prerequisite check to wait for usable resources,
**And** the topology can serve a bounded Gateway smoke request before the full vector lane runs.

**Given** workspace submodules,
**When** the topology locates Module server source,
**Then** it uses only root-declared `references/` checkouts,
**And** no nested or recursive submodule initialization is needed.

### Story 4.13: Test Every Vector Against Live Gateway Semantics

As a test maintainer,
I want each approved vector exercised once against live EventStore,
So that a matching JSON shape alone cannot pass a broken business Operation.

**Requirements:** FR20, NFR7

**Acceptance Criteria:**

**Given** approved Tenants and Parties vectors and the v1 AppHost,
**When** the live integration lane runs,
**Then** it executes each vector once with its generic prerequisite Operation calls, asserts Command acceptance or a returned Query document, and checks the vector's semantic effects,
**And** no live Command is submitted twice merely to compare the two Heads.

**Given** the live test project,
**When** it runs against the v1 AppHost,
**Then** topology tests carry the integration trait, use the Microsoft.Testing.Platform runner and standard Dapr prerequisite check, and report the failing Operation on a vector or semantic mismatch,
**And** the test code contains no per-Module setup branch.

### Story 4.14: Make the Live Semantic Lane Blocking in CI

As a release maintainer,
I want the live vector tests to be a blocking CI gate,
So that a v1 release cannot bypass an unbuildable or failing Aspire topology.

**Requirements:** FR20, NFR7

**Acceptance Criteria:**

**Given** the Hexalith.Builds `domain-ci.yml` workflow,
**When** the v1 CI job runs,
**Then** an upstream bounded source-build seam or helper-managed source build makes root-declared Module server sources available before Aspire tests,
**And** the owning Builds repository contains the upstream change rather than a local edit inside `references/`.

**Given** this repository's CI workflow,
**When** it calls `domain-ci.yml`,
**Then** `aspire-test-project` names the integration project, `test-platform` is `microsoft-testing-platform`, and `aspire-continue-on-error` is `false`,
**And** Dapr initialization and the focused Release build and test lanes run before the live tier.

**Given** a missing helper, failed source build, failed vector, or failed semantic assertion,
**When** CI completes,
**Then** the v1 release remains blocked with the specific prerequisite or Operation reported,
**And** the gate is not weakened or marked optional.

### Story 4.15: Publish the No-new-server Rule

As a Hexalith Module author,
I want one authoritative rule for new agent surfaces,
So that new Modules use decorated Contracts instead of creating another server or CLI.

**Requirements:** FR22

**Acceptance Criteria:**

**Given** the Hexalith.AI.Tools instruction baseline,
**When** the rule is updated in its owning repository,
**Then** it states that from 2026-09-21 no new per-Module MCP server or per-Module agent CLI is created,
**And** a Module's agent-facing surface is its decorated Contracts Library.

**Given** the existing Frozen CLIs,
**When** the rule is reviewed,
**Then** it limits them to bug fixes and points to the versioned migration plan listing them,
**And** it does not treat those CLIs as a template for new Modules.

**Given** a proposed instruction change,
**When** completion and paired v1 release readiness are assessed,
**Then** the authoritative upstream rule has been merged, not merely proposed in a pull request,
**And** evidence records the merge, the root-declared baseline reference containing it, byte-identical local `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`, and a successful `scripts/check-agent-instructions-sync.sh`; an open pull request cannot unblock paired publication, while the Abstractions-only bootstrap is exempt.

### Story 4.16: Stage and Validate the Paired Packages

As a release maintainer,
I want validated package artifacts for one shared version,
So that publication can use exactly the tool and Decoration Package that passed the gates.

**Requirements:** FR20, NFR3, NFR6

**Acceptance Criteria:**

**Given** a green `main` source SHA and completed dependency, inventory, loopback, live semantic, and instruction gates, including recorded FR-22 merge/baseline/synchronization evidence,
**When** the paired release workflow runs,
**Then** semantic-release selects one version and packs exactly `Hexalith.McpCli.Abstractions` and `Hexalith.McpCli` from `tools/release-packages.json` into a clean staging directory,
**And** the staged packages have the exact IDs and shared version before any publication.

**Given** the staged tool package,
**When** release validation inspects and installs it from an isolated local source,
**Then** it verifies NuGet structure, the marked Contracts assemblies, `hexalith --version`, and offline discovery and config smoke commands,
**And** the tool is framework-dependent, untrimmed, and uses `ToolCommandName=hexalith`.

**Given** Linux, Windows, and macOS installation checks,
**When** the staged .NET 10 tool is installed,
**Then** it runs without native dependencies or hosted v1 infrastructure,
**And** stdout and stderr retain their CLI and MCP channel contracts while Catalog discovery JSON stays byte-identical for the same build across operating systems.

### Story 4.17: Verify the Operator Setup Experience

As an agent operator,
I want clear setup instructions verified in common MCP clients,
So that I can reach a cross-Module action with one installed tool.

**Requirements:** FR20, NFR6

**Acceptance Criteria:**

**Given** the staged tool and README,
**When** an operator follows setup in Claude Code, Claude Desktop, and VS Code,
**Then** initialization, discovery, and an approved cross-Module task are recorded in the release checklist,
**And** no per-Module server or prompt is needed.

**Given** a new operator using only the README,
**When** a timed session starts from tool installation,
**Then** it records whether a successful `send_command` occurs within the 15-minute target,
**And** any missed target is reported as a measured result rather than hidden by the release workflow.

### Story 4.18: Publish the Validated Package Pair

As a release maintainer,
I want the validated packages published together from a green source SHA,
So that operators can install the exact pair proven by CI and smoke checks.

**Requirements:** FR20, NFR6

**Acceptance Criteria:**

**Given** the staged artifacts, completed client checklist, publication credentials, and an available version,
**When** the release preflight runs,
**Then** it confirms the exact green source SHA, package IDs, shared version, and all blocking gates before any push,
**And** a failed preflight prevents either paired package from being published.

**Given** a successful preflight,
**When** the release publishes to nuget.org,
**Then** it pushes only the validated Abstractions and tool packages and records their resulting versions,
**And** the packages share the version selected by semantic-release.

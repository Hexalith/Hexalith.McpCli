---
inventory_version: '1.0.0'
status: approved
module: technical-tools
source_repository: 'https://github.com/Hexalith/Hexalith.FrontComposer'
source_revision: 'fbb9c3822dfa407e72739238cd472567f45f1e82'
historical_inventory: '_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.md'
historical_source_revision: '81a440a8890a17edb39924bd0cf676eb6f6b5c25'
census_scope: 'root .gitmodules: 17 declared references at the reviewed McpCli gitlinks'
source_spec: '_bmad-output/implementation-artifacts/spec-5-1-inventory-eventstore-admin-and-technical-tool-operations.md'
approval_status: approved
approval_ref: '#a1-owning-maintainer-approval-2026-11-08'
approval_authority: requesting-user-owning-maintainer
external_maintainer_approval: approved
---

# Technical tools migration inventory v1

Approved inventory **1.0.0** has two parts. The first reconciles the
current FrontComposer compiler, resource, skill-resource and lifecycle surfaces
at the full source revision above with the immutable
[FrontComposer inventory 1.0.0](frontcomposer-migration-inventory-v1.md),
whose rows stay pinned to `81a440a8890a17edb39924bd0cf676eb6f6b5c25` under
their own limited A1 session approval. It records **one configurable-name
lifecycle tool, two manifest-defined families, 13 documentation resources, two
compiler CLI leaves and nine variants**, and names the inspected manifest host
consumers. The second part is a bounded census of every proprietary CLI/MCP
project in the 17 root-declared references, with owning roles and removal
gates.

Every concrete row is approved **defer / exclude** under A1. No gateway-ready decorated
replacement, canonical McpCli operation or generic non-gateway contract exists
for these capabilities. A1 records owning-maintainer approval of the
dispositions and inventory completeness at the reviewed revisions. The
[EventStore Admin companion](eventstore-admin-migration-inventory-v1.md)
inventories both administration heads. Both documents are migration
documentation outside `src/`, never runtime configuration or execution
authority.

Governing decisions, at their pinned revisions: the AI.Tools ownership rule
(`references/Hexalith.AI.Tools/hexalith-llm-instructions.md:65`, exempt tooling `:80`) and migration plan 1.1.0 (`references/Hexalith.AI.Tools/hexalith-mcpcli-migration-instructions.md:2`, its
versioned-update rule `:42` and successor scope `:70`); Platform AD-11 scope,
legacy and new surfaces (`references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:183`, `:184`, `:185`) and AD-14 surface classes
(`references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:211`); and EventStore AD-22 consumer-removal authority (`references/Hexalith.EventStore/_bmad-output/planning-artifacts/architecture.md:297`).
Anchors that begin with `references/` are relative to the McpCli root.

## A1 Owning-maintainer approval (2026-11-08)

- **Approver and authority:** the requesting user in this conversation, who
  explicitly confirmed "Authorized for all listed maintainer roles" after
  being asked whether that authority covers EventStore, platform/operator,
  FrontComposer and every census owner. This records that declared authority;
  no additional named-person signature is inferred.
- **Exact approving instruction:** "I approve", following presentation of both
  `1.0.0-candidate.3` inventories and their pending 156-row approval gate.
- **Approved scope:** FH01–FH03, FD01–FD13, FC01–FC02, FV01–FV09, FK01–FK04, PS01–PS13, PE01–PE07, PN01–PN09 and G1–G5 (65 rows). Every disposition remains
  `defer / exclude`; prerequisite rows acknowledge unresolved downstream work,
  rather than claiming it has been performed.
- **Version and revisions:** inventory `1.0.0`, finalized from the reviewed
  `1.0.0-candidate.3` without changing source facts, scope or dispositions;
  McpCli revision `fa7c51601041ee6cf0d2f9d4613fb405758f2f7c` plus the exact reviewed
  candidate bytes. The [approval receipt](evidence/story-5-1/approval/approval.json)
  binds this inventory's final SHA-256, its preserved candidate SHA-256, all
  row IDs and all 17 census revisions, including EventStore
  `3d4ba67db99f2f0bcd64b7d353609b555870cc9b` and FrontComposer
  `fbb9c3822dfa407e72739238cd472567f45f1e82`.
- **History and limits:** the earlier "approve and stop" approved only the
  specification. A session-only approval would leave owning-maintainer
  acceptance pending; the explicit authority confirmation above supplies the
  missing ownership decision for these rows. Inventory approval supplies no
  generic contract, Gateway enrollment, live authorization or parity evidence,
  and no runtime exposure, execution, publication or retirement permission.
- **Completion:** A1 resolves the owning-maintainer inventory review required
  by Story 5.1. Unresolved replacement and retirement gates remain prerequisites
  of Stories 5.2–5.5.

Approved deferrals retain the FrontComposer host, documentation and compiler
tooling and every census surface. Exclusion is neither withdrawal nor deletion
permission.

## Source pins and reconciliation method

Read clean FrontComposer checkout `fbb9c3822dfa407e72739238cd472567f45f1e82`
on `main`. The historical pin is **not an ancestor** of that revision. It
branches from merge base `b06f86d554363ea5b8192cbc149a75c820dab2b8`, from which
it differs only by removing lines from the developer configuration files
`.codex/config.toml` and `.mcp.json`, neither a surface path. The merge base is
an ancestor of the current revision. The historical pin's availability outside
this checkout is already tracked (`deferred-work.md:677`); this candidate adds
no ledger entry for it.

Reconciliation compares the historical pin with the current revision tree to
tree:

- `src/Hexalith.FrontComposer.Mcp/` and `docs/skills/frontcomposer/` have
  identical Git trees at both revisions, so every host, documentation-resource
  and lifecycle behavior and line anchor recorded by the historical inventory
  applies unchanged.
- `src/Hexalith.FrontComposer.Cli/` differs in six files (89 insertions, 30
  deletions): `CliApplication.cs`, `MigrationPlanner.cs`, `PathUtilities.cs`,
  `ProjectDocumentLoader.cs`, `README.md` and `WriteSafetyPolicy.cs`. The
  verb set is unchanged; FV09 records the new path-safety behavior.

Paths are relative to `references/Hexalith.FrontComposer/`. `Mcp/` and `Cli/`
abbreviate `src/Hexalith.FrontComposer.Mcp/` and
`src/Hexalith.FrontComposer.Cli/`; `Corpus/` means
`docs/skills/frontcomposer/`. Corpus files are ordinary Markdown resources,
not agent `SKILL.md` manifests; only their resource metadata was read and no
skill under `references/` was discovered, loaded or executed. No compiler
command, migration, build or host was run.

## FrontComposer host surfaces

| ID | Surface | Historical row | Current-source reconciliation | Transport | Expected behavior | Disposition | Coverage | Missing replacement / rationale | Security class | Owner | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FH01 | `frontcomposer.lifecycle.subscribe` (default `LifecycleToolName`, configurable) | H01, V01 | unchanged: identical `Mcp/` tree | Authenticated HTTP MCP `/mcp` tool | One tool taking exactly one canonical ULID `correlationId` or `messageId` and no other property; returns a bounded in-process lifecycle snapshot after rechecking admission to the recorded tool; unknown or hidden handles fail without disclosure. | defer | exclude | No generic status/lifecycle contract or transport; the store has no originating tenant/user binding, so ownership proof is a prerequisite (FV01). Gateway acceptance is not effect confirmation. | Handle lookup with current-tool admission; originating ownership unproven | FrontComposer owning maintainer role | `Mcp/FrontComposerMcpOptions.cs:52`; `Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs:46`; `Mcp/Invocation/FrontComposerMcpLifecycleStore.cs:110` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FH02 | Manifest-defined command tool family | H02 | unchanged: identical `Mcp/` tree | Authenticated HTTP MCP tools | Registered manifests and generated manifest assemblies supply the tool names; admitted command descriptors are listed beside the lifecycle tool. Not a finite framework business catalog: each consumer's concrete tools belong to that consumer (FK rows). | defer | exclude | Each consumer needs its own pinned business inventory, exact decorated Contracts and authorization proof; no dynamic plug-in loading or module-specific adapter in McpCli v1. | Tenant/policy-authorized write or module-defined action | FrontComposer owning maintainer role; consumer owners for concrete names | `Mcp/FrontComposerMcpOptions.cs:12`; `Mcp/FrontComposerMcpDescriptorRegistry.cs:97`, `:121` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FH03 | Manifest-defined projection resource family | H03 | unchanged: identical `Mcp/` tree | Authenticated HTTP MCP resource reads | Descriptor URIs map to projection queries rendered as bounded Markdown; visibility, descriptor epoch and schema are rechecked before query and before rendering. Not a finite catalog (FK rows). | defer | exclude | A decorated Query may replace business data only after its semantics are proved; Markdown resource rendering and schema negotiation need a separate decision. MCP resources are out of McpCli v1. | Tenant-filtered projection read | FrontComposer owning maintainer role; consumer owners for concrete resources | `Mcp/FrontComposerMcpServerOptionsConfigurator.cs:27`; `Mcp/Invocation/FrontComposerMcpProjectionReader.cs:59`, `:76`, `:90` | [A1](#a1-owning-maintainer-approval-2026-11-08) |

FH01 and FH03 are reads. FH02 is an open family that can contain consumer
writes; its effects and confirmation are classified by each consumer's own
inventory (FK rows), not here.

The lifecycle acknowledgement URI `frontcomposer://lifecycle/{correlationId}`
is metadata, not a registered resource. The configurator registers manifest
projections and documentation resources only. No MCP prompt, fixed polling or
streaming resource, erasure tool or key-rotation tool is registered; the
`MaxLifecycleLongPollMs` option (`Mcp/FrontComposerMcpOptions.cs:62`) does not
create a long-poll operation, and the API-key dictionary is configuration.

## Documentation and skill resources

Each URI has prefix `frontcomposer://skills/`. FD01–FD12 are the embedded
ordinary corpus documents (`Mcp/Hexalith.FrontComposer.Mcp.csproj:30` embeds
`**/*.md`); FD13 is the synthetic aggregate manifest added by
`Mcp/Skills/FrontComposerSkillResourceProvider.cs:70`. Every document supplies
its id at line 2 and URI at line 8. The tracked
`Corpus/benchmark-prompts/v1/prompt-set.json` is not Markdown, is not embedded
and is not a resource. All rows are framework documentation reads served over
authenticated HTTP MCP; they bypass the tenant projection gate while endpoint
authorization remains. Keep the documentation available while a delivery
decision is deferred.

| ID | Resource id | URI suffix | Historical row | Current-source reconciliation | Disposition | Coverage | Rationale / security class | Owner | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FD01 | `index` | `index` | D01 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/index.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD02 | `team-overlays` | `team-overlays` | D02 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/team-overlays.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD03 | `domain-commands` | `domain/commands` | D03 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/domain/commands.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD04 | `domain-projections` | `domain/projections` | D04 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/domain/projections.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD05 | `domain-validation` | `domain/validation` | D05 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/domain/validation.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD06 | `mcp-projection-markdown` | `mcp/projection-markdown` | D06 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/mcp/projection-markdown.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD07 | `mcp-tools-resources-lifecycle` | `mcp/tools-resources-lifecycle` | D07 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/mcp/tools-resources-lifecycle.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD08 | `migration-versioned-corpus-rules` | `migration/versioned-corpus-rules` | D08 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/migration/versioned-corpus-rules.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD09 | `samples-new-bounded-context` | `samples/new-bounded-context` | D09 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/samples/new-bounded-context.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD10 | `security-tenant-and-policy-boundaries` | `security/tenant-and-policy-boundaries` | D10 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/security/tenant-and-policy-boundaries.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD11 | `setup-package-and-hosting` | `setup/package-and-hosting` | D11 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/setup/package-and-hosting.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD12 | `testing-generated-code-validator` | `testing/generated-code-validator` | D12 | unchanged: identical corpus tree | defer | exclude | Framework documentation; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Corpus/testing/generated-code-validator.md:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FD13 | `skills-manifest` | `manifest` | D13 | unchanged: identical `Mcp/` tree | defer | exclude | Synthetic framework documentation index; non-Gateway read; no approved documentation transport. | FrontComposer owning maintainer role | `Mcp/Skills/FrontComposerSkillResourceProvider.cs:102`; `Mcp/Skills/SkillCorpusAggregateManifestBuilder.cs:8` | [A1](#a1-owning-maintainer-approval-2026-11-08) |

## FrontComposer compiler CLI leaves

`Cli/CliApplication.cs:19`–`:24` dispatches exactly two verbs; any other first
argument is rejected. The `frontcomposer` tool is local developer tooling,
distinct from every Projects CLI spelling. Neither leaf is a Gateway business
operation.

| ID | CLI leaf | Historical row | Current-source reconciliation | Transport | Expected behavior | Effect | Confirmation | Disposition | Coverage | Missing replacement / rationale | Security class | Owner | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FC01 | `inspect` | C01, V06 | `InspectCommand.cs` and verb help unchanged; shared project/solution path canonicalization changed (FV09) | Local CLI process | Generated-source and diagnostic inspection with type, project, solution, configuration (default Debug) and framework selectors, text or JSON output, severity filter, fail-on-warning/error and absolute-path choice. `--build` explicitly opts in to a build subprocess. Without it, inspection reads existing generated output without establishing freshness against current source (FV06). | local read; optional build subprocess | `--build` flag only | defer | exclude | No approved generic compiler/developer-tool contract; retain local tooling rather than inventing a Gateway Query. | Local source read; optional build execution | FrontComposer owning maintainer role | `Cli/CliApplication.cs:20`; `Cli/InspectCommand.cs:7`, `:19`; `Cli/GeneratedOutputLoader.cs:25`, `:49` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FC02 | `migrate` | C02, V07 | changed: path-safety and planner messages (FV09); verb, options and catalog unchanged | Local CLI process | Versioned source migration planning, default dry-run; `--from`/`--to`, project/solution selectors, text or JSON, fail-on-findings; the only catalog edge is 9.1.0 to 9.2.0. `--apply` writes files (FV07). MSBuild imports are not evaluated; a top-level Import emits a stderr warning and files contributed only through imports are not migrated, so success does not establish complete project coverage. | dry-run: local read. With `--apply`, destructive: rewrites project source files | explicit `--apply` flag; no interactive prompt; presence-based, so `--apply=false` also applies (FV08) | defer | exclude | Requires a separate compiler-tool ownership and replacement decision, never a domain Command. Inventory approval never authorizes running it. | Local file mutation when applied | FrontComposer owning maintainer role | `Cli/CliApplication.cs:22`; `Cli/MigrationCommand.cs:13`, `:19`, `:33`; `Cli/ProjectDocumentLoader.cs:6`; `Cli/MigrationCatalog.cs:4` | [A1](#a1-owning-maintainer-approval-2026-11-08) |

## FrontComposer behavior variants

FV01–FV08 reconcile the historical V01–V08 at the current revision; FV06 also
records the shared project-selection change. FV09 details the current path-safety
supplement.

| ID | Historical row | Current behavior | Current-source reconciliation | Disposition / coverage | Required handoff / rationale | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FV01 | V01 | Lifecycle input requires exactly one canonical ULID handle; lookup returns bounded in-memory transitions only after current-tool admission is rechecked. The process-wide store has no originating tenant/user binding. | unchanged: identical `Mcp/` tree | defer / exclude | No lifecycle streaming, event reading or polling engine in McpCli v1. An approved generic status design must prove originating ownership and define expiry, history and long-poll limits. | `Mcp/McpJsonSchemaBuilder.cs:57`; `Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs:92`; `Mcp/Invocation/FrontComposerMcpLifecycleStore.cs:307` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FV02 | V02 | HTTP `/mcp` requires authorization plus tenant tool and resource gates; sample allow-all gates are rejected outside Development. | unchanged: identical `Mcp/` tree | defer / exclude | McpCli v1 stdio has no forwarded per-user HTTP identity or host policy; a later approved generic HTTP design owns transport replacement. | `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:59`, `:79`; `Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs:34` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FV03 | V03 | API-key header defaults to `X-FrontComposer-Mcp-Key`; invalid or multiple keys fail without claims fallback. A valid key takes precedence over claims and yields tenant/user only; the no-key claims path keeps roles and claims. No erasure or key-rotation operation is registered; `ApiKeys` is configuration. | unchanged: identical `Mcp/` tree | defer / exclude | An operator actor/tenant or allowlisted extension is not equivalent authenticated authority. No identity server or module-specific auth adapter. | `Mcp/HttpFrontComposerMcpAgentContextAccessor.cs:79`, `:96`, `:110`; `Mcp/FrontComposerMcpOptions.cs:18`, `:20` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FV04 | V04 | Policy-gated tools are hidden without a working gate; caller-supplied derivable identity, message and correlation fields are rejected and server fields injected; unknown and hidden failures are sanitized. | unchanged: identical `Mcp/` tree | defer / exclude | Preserve deny-before-dispatch and nondisclosure; Catalog listing and read-only semantics do not prove policy parity. | `Mcp/Invocation/FrontComposerMcpToolAdmissionService.cs:122`, `:207`; `Mcp/Invocation/FrontComposerMcpCommandInvoker.cs:66`, `:219` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FV05 | V05 | Projection reads recheck visibility, descriptor epochs and schema fingerprints, clamp take from options (default 50) and bound rows, cells and Markdown. Corpus documents bypass the tenant projection gate. | unchanged: identical `Mcp/` tree | defer / exclude | JSON Query output alone is not Markdown, resource or schema-negotiation parity; MCP resources and prompts are out of McpCli v1. | `Mcp/Invocation/FrontComposerMcpProjectionReader.cs:45`, `:76`; `Mcp/FrontComposerMcpOptions.cs:24`; `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:66` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FV06 | V06 | `inspect` options as in FC01; text is the default format; source severity also accepts `information`. Without `--build`, existing generated files and diagnostics are read with no source/output freshness check; a requested build must succeed before inspection. | command implementation unchanged; shared selection canonicalization changed (FV09) | defer / exclude | Preserve the local workflow and explicit build choice and freshness limitation; no generated McpCli subcommand or compiler dependency. | `Cli/CliApplication.cs:52`; `Cli/InspectCommand.cs:29`, `:78`; `Cli/GeneratedOutputLoader.cs:25`, `:49`; `Cli/ProjectSelection.cs:7`, `:26`, `:52` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FV07 | V07 | `migrate --apply` rejects a combined dry-run, rechecks canonical targets and source hashes, then writes sequentially. Earlier writes remain after a later failure or cancellation, and the result reports `applied:false`. MSBuild imports are not evaluated and import-only files are excluded; detected top-level imports produce a stderr warning (FC02). | apply flow unchanged; target admission now also uses FV09 | defer / exclude | Destructive local source mutation guarded only by an explicit flag. Make drift detection, retained partial writes, import-coverage warning and `applied:false` explicit in any compatibility decision; this inventory executed no migration. | `Cli/MigrationCommand.cs:33`, `:40`; `Cli/MigrationApplier.cs:12`, `:28`, `:33`, `:51` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FV08 | V08 | No argument, `help`, `--help` or `-h` prints help; exit codes 0 success, 1 findings, 2 invalid input, 3 generated output missing, 4 apply failure. `.csproj` and single-project `.sln` are supported; `.slnx` and `.fsproj` fail closed. Options accept `--name value` and `--name=value`, repeated named options are rejected, and flags use presence, so `--apply=false` selects apply. | help text changed in one line (migrate diffs now "bounded informational output"); the README now states that migrate output is not scrubbed of usernames, tenant values or secrets; parser unchanged | defer / exclude | Preserve or explicitly approve parser syntax, duplicate rejection, presence-based flags and the output privacy limit; McpCli JSON, error, exit and `.slnx` contracts do not replace this tool. | `Cli/CliApplication.cs:13`, `:41`, `:55`, `:56`; `Cli/CommandOptions.cs:31`, `:91`, `:99` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FV09 | none (current-source supplement) | Migration planning skips linked files, linked ancestor directories and junctions below the project, and nested repositories (a `.git` marker below the project root), before reading source. Canonicalization resolves ancestors first. `inspect` also reaches this changed helper through `ProjectSelection.Resolve`: explicit project/solution paths and solution project entries resolve ancestor links before file/type and solution-directory containment checks. Identical `InspectCommand.cs` does not establish identical selection behavior. Apply rejects unsafe targets again. Lexically distinct paths to one document are de-duplicated, preferring a non-linked spelling. Inaccessible path metadata counts as unsafe. | new since the historical pin: `WriteSafetyPolicy.cs`, `PathUtilities.cs`, `MigrationPlanner.cs`, `ProjectDocumentLoader.cs` | defer / exclude | Preserve this safety and continuity fix in any compatibility decision. The historical A1 does not cover it; owner review of this supplement is required. | `Cli/WriteSafetyPolicy.cs:4`; `Cli/PathUtilities.cs:32`, `:61`, `:86`; `Cli/ProjectSelection.cs:7`, `:26`, `:52`; `Cli/MigrationPlanner.cs:55`; `Cli/ProjectDocumentLoader.cs:39` | [A1](#a1-owning-maintainer-approval-2026-11-08) |

## Manifest host consumers

FH02 and FH03 are open families. These are the consumers found in tracked
source of the 17 root references. This is not an ecosystem-wide catalog:
repositories outside the census, uninspected dynamic hosts and future
manifests need their own inventories before host retirement.

| ID | Consumer | Repository and revision | Relationship | Concrete operations | Owner | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FK01 | `Hexalith.Projects.Mcp` plug-in | `references/Hexalith.Projects` `31cb92c4362becd83938bd550ca62d07b6af448a` | `AddProjectsMcp` adds the Projects manifest and calls `AddFrontComposerMcp`; `MapProjectsMcp` calls `MapFrontComposerMcp`. No tracked production host in the census calls `AddProjectsMcp`. | Five tools and 11 resources in the [Projects inventory 1.0.0](projects-migration-inventory-v1.md), pinned to `3d256e632a7645bc2261e668ac7c74be81155f58`, which is not an ancestor of the current revision. Since that pin, `src/Hexalith.Projects.Mcp` and `src/Hexalith.Projects.Cli` are unchanged, but two rendered `Contracts/Ui` projection types gained fields; whether that requires a versioned companion update is an owner decision (G3). | Projects owning maintainer role | `src/Hexalith.Projects.Mcp/ProjectsMcpModule.cs:35`, `:51`, `:62` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FK02 | FrontComposer `Counter.Web` sample | `references/Hexalith.FrontComposer` `fbb9c3822dfa407e72739238cd472567f45f1e82` | Sample host: when MCP is enabled it registers sample gates and manifest assemblies and maps `/mcp`. | Generated from sample domain assemblies; sample and test only, not a shipped surface. | FrontComposer owning maintainer role | `samples/Counter/Counter.Web/Program.cs:196`, `:232` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FK03 | `Hexalith.Parties.UI` | `references/Hexalith.Parties` `1308ad000c79ebc394fc395588f9af91092e8c4c` | Package or project dependency on `Hexalith.FrontComposer.Mcp`; no `AddFrontComposerMcp`, `MapFrontComposerMcp` or other FrontComposer MCP registration in tracked Parties source. | None observed; a dependency consumer, not an observed host. Parties MCP tools are owned by the [Parties inventory](parties-migration-inventory-v1.md). | Parties owning maintainer role | `src/Hexalith.Parties.UI/Hexalith.Parties.UI.csproj:66`, `:67` | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| FK04 | FrontComposer test projects | `references/Hexalith.FrontComposer` `fbb9c3822dfa407e72739238cd472567f45f1e82` | `Mcp.Tests`, `Shell.Tests.Bench` and `SourceTools.Tests` reference the MCP project. | Test fixtures only. | FrontComposer owning maintainer role | `tests/Hexalith.FrontComposer.Mcp.Tests/Hexalith.FrontComposer.Mcp.Tests.csproj:1` | [A1](#a1-owning-maintainer-approval-2026-11-08) |

## Proprietary CLI/MCP package census

Scope: the 17 references declared by the root `.gitmodules`, each clean at the
recorded full revision. The scan uses `git ls-files` in each root, so nested
gitlinks are never initialized or traversed. A production surface is a tracked
`src/` project, outside test projects, that is named `*.Cli` or `*.Mcp`,
references the ModelContextProtocol package or `Hexalith.FrontComposer.Mcp`,
or is packed as a .NET tool. A project that only references the host library
without registering or mapping it (FK03) is a dependency consumer, not a
surface. Hosts were also searched for MCP server registrations. Captured
implementation artifacts are excluded. Project
existence is distinct from publication or deployment: the packaging column
records source metadata only.

### Production surfaces

| ID | Project | Repository and revision | Kind and transport | Packaging metadata | Operation inventory | Owning maintainer role | Removal gate | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PS01 | `src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj` | `references/Hexalith.EventStore` `3d4ba67db99f2f0bcd64b7d353609b555870cc9b` | CLI to Admin HTTP | Exe; `PackAsTool` `eventstore-admin`; listed in `tools/release-packages.json` | [EventStore Admin candidate](eventstore-admin-migration-inventory-v1.md) AC01–AC31, AU01–AU06 | EventStore owning maintainer; platform/operator maintainer | Companion G1–G6: approved generic administration contract and destructive-operation safety evidence first | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS02 | `src/Hexalith.EventStore.Admin.Mcp/Hexalith.EventStore.Admin.Mcp.csproj` | `references/Hexalith.EventStore` `3d4ba67db99f2f0bcd64b7d353609b555870cc9b` | stdio MCP to Admin HTTP | Exe; `IsPackable` false | [EventStore Admin candidate](eventstore-admin-migration-inventory-v1.md) AM01–AM28 | EventStore owning maintainer; platform/operator maintainer | Companion G1–G6 | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS03 | `src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj` | `references/Hexalith.FrontComposer` `fbb9c3822dfa407e72739238cd472567f45f1e82` | Local compiler CLI | Exe; `PackAsTool` `frontcomposer`; listed in `tools/release-packages.json` | FC01–FC02 here; historical C01–C02 | FrontComposer owning maintainer | G2 compiler-tool decision; not removable with the MCP host by default | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS04 | `src/Hexalith.FrontComposer.Mcp/Hexalith.FrontComposer.Mcp.csproj` | `references/Hexalith.FrontComposer` `fbb9c3822dfa407e72739238cd472567f45f1e82` | HTTP MCP host library | Library; `IsPackable` true; listed in `tools/release-packages.json` | FH, FD and FV rows here; historical H, D and V rows; consumers FK01–FK04 | FrontComposer owning maintainer | G4: retire together with the Projects plug-in after every host consumer is accounted for | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS05 | `src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj` | `references/Hexalith.Parties` `1308ad000c79ebc394fc395588f9af91092e8c4c` | Stateless HTTP MCP server | Web; `IsPackable` false; container `parties-mcp` | [Parties inventory 1.0.0](parties-migration-inventory-v1.md) at `493730941329d1bca3b4f6b2f6a67ffe305c2443` (ancestor); no surface-project change since | Parties owning maintainer | Parties inventory gates; replacement evidence and approved withdrawal for every row | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS06 | `src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj` | `references/Hexalith.Memories` `246157a7ff8e2dcd8d356c833a77a02514490d2f` | CLI | Exe; `PackAsTool` `memories`; listed in `tools/release-packages.json` | [Memories inventory 1.0.0](memories-migration-inventory-v1.md) at `f6b60d5a2e9b81d84fddad789c7d9bed40d3a533` (ancestor); 1 CLI file changed since the pin (34 insertions), classification not assessed (G3) | Memories owning maintainer | Memories gates, including forwarded per-user identity in the HTTP release | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS07 | `src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj` | `references/Hexalith.Memories` `246157a7ff8e2dcd8d356c833a77a02514490d2f` | Stateless HTTP MCP server | Web; `IsPackable` true; container `memories-mcp` | [Memories inventory 1.0.0](memories-migration-inventory-v1.md); 3 MCP files changed since the pin (26 insertions, 3 deletions), classification not assessed (G3) | Memories owning maintainer | Memories gates, including forwarded per-user identity in the HTTP release | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS08 | `src/Hexalith.Projects.Cli/Hexalith.Projects.Cli.csproj` | `references/Hexalith.Projects` `31cb92c4362becd83938bd550ca62d07b6af448a` | CLI | Exe; `IsPackable` false | [Projects inventory 1.0.0](projects-migration-inventory-v1.md) at `3d256e632a7645bc2261e668ac7c74be81155f58` (not an ancestor); no CLI change since | Projects owning maintainer | Projects inventory gates | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS09 | `src/Hexalith.Projects.Mcp/Hexalith.Projects.Mcp.csproj` | `references/Hexalith.Projects` `31cb92c4362becd83938bd550ca62d07b6af448a` | FrontComposer MCP plug-in library | Library; `IsPackable` false | [Projects inventory 1.0.0](projects-migration-inventory-v1.md); see FK01 | Projects owning maintainer | G4: retire together with the FrontComposer host | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS10 | `src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj` | `references/Hexalith.Folders` `e88c940000446e13d17d86a7288649d8653a7138` | CLI | Exe; `PackAsTool` `folders`; `IsPackable` true; not in `tools/release-packages.json` | [Folders inventory 1.0.0](folders-migration-inventory-v1.md) at `e2252f29a2dba2b64786ee483eb59fbceaadd387` (not an ancestor); Folders CLI and MCP together changed 17 files since the pin (156 insertions, 359 deletions), classification not assessed (G3) | Folders owning maintainer | Folders inventory gates | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS11 | `src/Hexalith.Folders.Mcp/Hexalith.Folders.Mcp.csproj` | `references/Hexalith.Folders` `e88c940000446e13d17d86a7288649d8653a7138` | stdio MCP server | Exe; `IsPackable` false | [Folders inventory 1.0.0](folders-migration-inventory-v1.md); 49 tool attributes at both the pin and the current revision | Folders owning maintainer | Folders inventory gates | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS12 | `src/Hexalith.ChatBot.Cli/Hexalith.ChatBot.Cli.csproj` | `references/Hexalith.ChatBot` `b13c58006d292836a9c8b242de476765676e5fb2` | CLI | Exe; `IsPackable` false | [ChatBot inventory 1.0.0](chatbot-migration-inventory-v1.md) at `acc934599cf1efff36b0643eddc6a3cc4c2978d5` (not an ancestor); ChatBot CLI and MCP together changed 2 formatter files since the pin (9 insertions, 3 deletions), classification not assessed (G3) | ChatBot owning maintainer | ChatBot inventory gates | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PS13 | `src/Hexalith.ChatBot.Mcp/Hexalith.ChatBot.Mcp.csproj` | `references/Hexalith.ChatBot` `b13c58006d292836a9c8b242de476765676e5fb2` | stdio MCP server | Exe; `IsPackable` false | [ChatBot inventory 1.0.0](chatbot-migration-inventory-v1.md) | ChatBot owning maintainer | ChatBot inventory gates | [A1](#a1-owning-maintainer-approval-2026-11-08) |

Every owner above is a repository maintainer role. No tracked ownership file
names a person for these repositories; Platform's `.github/CODEOWNERS:2`
assigns only the Platform repository.

### Exempt, test and non-surface tooling

| ID | Projects or files | Classification | Evidence and scope limit | Approval |
| --- | --- | --- | --- | --- |
| PE01 | Builds `567604b616613ba429be0609636d805db776a709` `src/libraries/Hexalith.Builds.Module.Cli` (`hexalith-module`), including its `pack/projects/EventStore/Host.csproj` and `pack/projects/Ui/Host.csproj` templates | Exempt build and workspace tooling | Named by the authoritative AI.Tools ownership rule as tooling that never invokes module operations (`references/Hexalith.AI.Tools/hexalith-llm-instructions.md:80`). The two `Host.csproj` files are packaging templates, not shipped CLI/MCP surfaces. Owner: Builds maintainer role. | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PE02 | Builds `567604b616613ba429be0609636d805db776a709` `src/libraries/Hexalith.Builds.Evidence.Cli` (`hexalith-evidence`) | Exempt evidence tooling | Named by the same rule and by Platform AD-11 Scope (`references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:183`). Owner: Builds maintainer role. | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PE03 | Platform `Hexalith.Platform.CatalogBuilder` and `Hexalith.Platform.Protection.Qualification.Enrollment`, `.Executor` and `.Observer` | Platform build and qualification tooling | Executables without System.CommandLine, the MCP package or tool packing; Platform AD-11 Scope places the Platform tool and qualification tooling outside the module-operation rule (`references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:183`). Classification is by source reading; the Platform owner should confirm. | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PE04 | Folders `src/Hexalith.Folders.Client/Generation` and Projects `src/Hexalith.Projects.Client/Generation` | Build-time REST client generators | Non-packable executables that read a contract and write generated client source; they invoke no module operation. Classification is by source reading; the Folders and Projects owners should confirm. | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PE05 | 13 `.Cli.Tests` and `.Mcp.Tests` projects (EventStore 2, FrontComposer 2, Parties 1, Memories 2, Projects 2, Folders 2, ChatBot 2), plus Memories `IntegrationTests` and the FK04 FrontComposer tests | Test fixtures | They test the PS surfaces and are not additional production surfaces. | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PE06 | Repository-local `.mcp.json`, `.vscode/mcp.json` and `.cursor/mcp.json` in ChatBot, EventStore, Folders, FrontComposer, Projects, Tenants and Timesheets, and `[mcp_servers.*]` tables in tracked `.codex/config.toml` files (11 roots track one; only Memories and Projects declare servers) | External developer MCP client configuration | They register only external developer servers (Microsoft Learn and Fluent UI Blazor); none routes a Hexalith legacy server. External developer tools are outside the rule. | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PE07 | Nested references, captured `_bmad-output`, evidence and `docs/implementation` snapshots inside the roots | Out of census scope | Nested gitlinks are not initialized; captured artifacts can contain historical project files that ship nothing. | [A1](#a1-owning-maintainer-approval-2026-11-08) |

### Root references without a production surface

| ID | Root reference | Revision | Finding | Owning maintainer role | Approval |
| --- | --- | --- | --- | --- | --- |
| PN01 | `references/Hexalith.AI.Tools` | `1745b6663ad32bb1288167135ed0f979366c53a0` | No tracked project file; instruction repository. | AI.Tools maintainer role | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PN02 | `references/Hexalith.Commons` | `11555ace9efcae2928a00122dcba91243e5a8a1a` | No production CLI/MCP project, MCP package reference, MCP registration or packed tool. | Commons maintainer role | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PN03 | `references/Hexalith.PolymorphicSerializations` | `bce4eb9f45c6b131b960ab4fa39e50ff01e51960` | No production CLI/MCP project, MCP package reference, MCP registration or packed tool. | PolymorphicSerializations maintainer role | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PN04 | `references/Hexalith.Conversations` | `9a5c684de5ee4876448faa26737f6afd36cf33e7` | No production CLI/MCP project, MCP package reference, MCP registration or packed tool; `Admin.Web` is a web UI. | Conversations maintainer role | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PN05 | `references/Hexalith.Tenants` | `d88aef6b52d7e8a2e2d81132b1d76b7e1d1f0f35` | No production CLI/MCP project, MCP package reference, MCP registration or packed tool; Tenants operations are enrolled in McpCli through decorated Contracts. | Tenants maintainer role | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PN06 | `references/Hexalith.Agents` | `7957108c30d38b8e82eb072cf3437b6a67627cd7` | No production CLI/MCP project, MCP package reference, MCP registration or packed tool. | Agents maintainer role | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PN07 | `references/Hexalith.Works` | `2e9fafba151a184eb4552796db7eecc25ffaf8c7` | No production CLI/MCP project, MCP package reference, MCP registration or packed tool. | Works maintainer role | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PN08 | `references/Hexalith.Timesheets` | `f5bee2c91bec6e1e78d81b604cea6af0cee764fe` | No production CLI/MCP project, MCP package reference, MCP registration or packed tool. | Timesheets maintainer role | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| PN09 | `references/Hexalith.Platform` | `01e5b6530af96ad6eaa69cc1867d43def56c43ca` | No production CLI/MCP project, MCP package reference, MCP registration or packed tool; PE03 tooling is outside scope. | Platform maintainer; `.github/CODEOWNERS:2` assigns `* @jpiquot` for this repository only | [A1](#a1-owning-maintainer-approval-2026-11-08) |

The Builds root carries PE01 and PE02 only. The census asserts nothing about
repositories outside `.gitmodules`, unpublished forks or dynamic hosts that
compose these packages elsewhere.

Composition and deployment routing points for the PS surfaces, read from
source only (nothing was deployed or run): the Parties AppHost references
Parties.Mcp (`references/Hexalith.Parties/src/Hexalith.Parties.AppHost/Hexalith.Parties.AppHost.csproj:18`);
the Memories AppHost references Memories.Mcp
(`references/Hexalith.Memories/src/Hexalith.Memories.AppHost/Hexalith.Memories.AppHost.csproj:14`); and
the Memories Kubernetes base deploys `memories-mcp`
(`references/Hexalith.Memories/deploy/kubernetes/base/mcp-deployment.yaml:4`) with its Dapr
configuration (`references/Hexalith.Memories/deploy/kubernetes/base/dapr/mcp-config.yaml:4`), service
(`references/Hexalith.Memories/deploy/kubernetes/base/services.yaml:17`), access-control entry
(`references/Hexalith.Memories/deploy/kubernetes/base/dapr/config.yaml:28`) and production image
override (`references/Hexalith.Memories/deploy/kubernetes/overlays/production/kustomization.yaml:55`).
The PS packaging column records the release lists and containers. The
`eventstore-admin` Dapr access-control files in EventStore and Tenants name the
Admin.Server sidecar, not the CLI tool.

## Retirement and replacement prerequisites

| ID | Required decision / evidence | Owning maintainer role | Approval |
| --- | --- | --- | --- |
| G1 | Review every FH, FD, FC, FV, FK, PS, PE and PN row and retain A1 as the approval record binding instruction, authority, inventory version and revisions. This A1 includes the explicit owning-maintainer authority confirmation; the historical A1 stays limited to its own rows. | FrontComposer owning maintainer and each census owner | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| G2 | Decide generic lifecycle/status, documentation-resource, schema/Markdown resource and local compiler-tool treatment, or explicit withdrawals (Story 5.2). Until then no MCP resource, prompt, stream reader, executor retry, plug-in loading or module-specific adapter is added to McpCli v1. | FrontComposer and McpCli contract/transport/security maintainers | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| G3 | Re-pin or confirm the companion module inventories whose surface source changed since their pins (FK01, PS06, PS07, PS10, PS12) under the migration plan's versioned-update rule (`references/Hexalith.AI.Tools/hexalith-mcpcli-migration-instructions.md:42`), and inventory any additional manifest consumer before host retirement. | Projects, Memories, Folders and ChatBot owning maintainers | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| G4 | Keep every PS binary or package versioned and labeled as a compatibility surface with its removal gate, outside every Platform composition (AD-11, `references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:184`), and stop routing it from the AppHost and deployment points listed under the census. Retire a surface only after approved replacements or withdrawals, selected-environment authorization, audit, output and exit-code parity, preserved or owner-approved REST/Dapr semantics, freshness, redaction, task context, actor attribution, paging, token budgets and idempotency, and any EventStore AD-22 consumer-removal authority (`references/Hexalith.EventStore/_bmad-output/planning-artifacts/architecture.md:297`). A module with a deferred operation is never counted as retired (Story 5.5). FrontComposer host and Projects plug-in retire together; Memories waits for forwarded per-user identity; EventStore Admin waits for its administration contract and destructive-operation safety evidence. | Each PS owning maintainer and the Platform maintainer | [A1](#a1-owning-maintainer-approval-2026-11-08) |
| G5 | Add the CI rejection of new proprietary per-module MCP/CLI projects or release entries without a named-owner, expiring migration exception (Story 5.5), using this census as the baseline. | McpCli and Platform maintainers | [A1](#a1-owning-maintainer-approval-2026-11-08) |

Verification: [Story 5.1 static checks](evidence/story-5-1/verification.md).

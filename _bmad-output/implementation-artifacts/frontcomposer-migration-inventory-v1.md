---
inventory_version: '1.0.0'
status: approved
module: frontcomposer
source_repository: 'https://github.com/Hexalith/Hexalith.FrontComposer'
source_revision: '81a440a8890a17edb39924bd0cf676eb6f6b5c25'
source_spec: '_bmad-output/implementation-artifacts/spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md'
approval_status: session-approved
approval_authority: requesting-user-session
approval_ref: '#a1-session-approval-2026-10-16'
external_maintainer_approval: unasserted
---

# FrontComposer migration inventory v1

Inventory **1.0.0** records the session-approved deferred scope in
[A1](#a1-session-approval-2026-10-16). It covers the framework host separately
from the [Projects business inventory](projects-migration-inventory-v1.md), with
a shared retirement gate. Source was clean at the full revision above. It records **one
fixed-name framework tool, 13 framework documentation resources and two local
compiler CLI leaves**, plus manifest-defined tool/resource families and host
behavior variants. The lifecycle tool's default name is configurable; the resource
set can expand with other manifests. Counts describe source registrations, not a
live host, authenticated visibility or behavior proof.

With only Projects registered, the source-defined potential set is six tools
(five Projects plus lifecycle) and 24 resources (11 Projects plus 13 framework
documents), subject to admission and additional host registrations. This does not
assert a fixed ecosystem-wide host catalog. Projects names appear once in the
companion inventory, not again as framework business operations.

Every row is approved **defer / exclude** within A1's session scope. The host's
lifecycle, documentation, schema, HTTP identity and compiler capabilities have
no gateway-ready decorated
Command/Query replacement established here. No canonical McpCli operation/type
is invented for them. The inventories are documentation outside `src/`, never
runtime configuration.

## A1 Session approval (2026-10-16)

- **Approver and authority:** the requesting user in the source-spec session.
  This is session scope approval for both source-pinned inventories; no external
  FrontComposer or Projects owning-maintainer sign-off is asserted. Metadata and
  every row reference this limited decision, never an external approval.
- **Exact approving instruction:** "approve", after presentation of the
  recommendation that all current rows in both inventories remain
  `defer / exclude`, retaining legacy surfaces. The
  [source spec's approved decision](spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md#boundaries--constraints)
  and [Implementation Notes](spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md#implementation-notes)
  record that instruction and its limits.
- **Source and version:** inventory 1.0.0, finalized from candidate
  1.0.0-candidate.1 at FrontComposer revision
  `81a440a8890a17edb39924bd0cf676eb6f6b5c25`, together with Projects inventory
  1.0.0 at `3d256e632a7645bc2261e668ac7c74be81155f58`.
- **Approved scope:** H01–H03, D01–D13, C01–C02 and V01–V08 remain
  `defer / exclude`. The FrontComposer maintainer owns these handoffs; G1–G4
  retain their stated owning roles and unresolved prerequisites. A1 approves
  retaining the gaps, not their future resolution. All companion rows share
  this decision.
- **Post-approval prerequisite clarifications (2026-10-16):** review corrected
  H01/V01 lifecycle ownership claims, V03 key/claims authority and unsupported
  erasure/key-rotation variants, V07 partial application and V08 parser behavior;
  V05 also links the effective take settings used by Projects V01. These additions
  change no approved disposition, coverage, authority or source pin; A1 does not
  claim the user reviewed these later clarifications.
- **Accepted current limitation:** none of these framework capabilities is
  included in McpCli. The host, documentation and compiler tooling remain
  available; Projects surfaces are counted once in the companion. Additional
  manifest consumers need their own inventory before host retirement.
- **Limits:** finalizing these inventories supplies no external owner approval,
  generic contract/transport decision, Gateway readiness, Catalog/dependency
  coverage, authorization/behavior/release proof, exposure, publication,
  withdrawal, retention change or retirement permission. Missing external owner
  approval still blocks an owner-approved completeness claim and the shared
  retirement gate. Neither host nor plug-in is deletable under A1.

Excluding a row from McpCli coverage retains its legacy capability. Future loss
of a convenience requires a later approved decision; Projects approval alone
cannot approve framework or other manifest consumers' retirement.

## Source notation

Paths are relative to the pinned `references/Hexalith.FrontComposer/` checkout.
`Mcp/` and `Cli/` abbreviate `src/Hexalith.FrontComposer.Mcp/` and
`src/Hexalith.FrontComposer.Cli/`. `Corpus/` means
`docs/skills/frontcomposer/`. The corpus files are ordinary Markdown resources,
not repository agent `SKILL.md` manifests. Only their resource metadata and the
ordinary host source were inspected; no repository skill was loaded.

## Framework host surfaces

| ID | Legacy surface | Disposition | Coverage | Missing replacement / rationale | Security class | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H01 | `frontcomposer.lifecycle.subscribe` | defer | exclude | Current bounded in-memory lifecycle snapshot looks up a correlation/message handle and rechecks admission to the recorded tool. The store has no originating tenant/user binding; explicit ownership proof is required before a future generic status/transport replacement. Gateway acceptance alone does not replace observed lifecycle. V01 applies. | Handle lookup with current-tool-admission check; originating ownership unproven | `Mcp/FrontComposerMcpOptions.cs:52`; `Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs:46`; `Mcp/Invocation/FrontComposerMcpLifecycleStore.cs:110`, `:307` | [A1](#a1-session-approval-2026-10-16) |
| H02 | Manifest-defined command tool family | defer | exclude | Registered/generated manifests determine the names; Projects' five concrete tools are M01–M05 in the companion. Other consumers need their own pinned inventories, exact Contracts and approval before host removal. No dynamic plug-in loading in McpCli v1. | Tenant/policy-authorized write or module-defined action | `Mcp/FrontComposerMcpOptions.cs:12`; `Mcp/FrontComposerMcpDescriptorRegistry.cs:97` | [A1](#a1-session-approval-2026-10-16) |
| H03 | Manifest-defined projection resource family | defer | exclude | Projects' 11 resources are R01–R11 in the companion. Other descriptors remain host-owned. Each included business read requires a decorated Contracts Query and Gateway semantics; Markdown resource rendering needs a separate decision. | Tenant-filtered projection read | `Mcp/FrontComposerMcpServerOptionsConfigurator.cs:27`; `Mcp/FrontComposerMcpResource.cs:13` | [A1](#a1-session-approval-2026-10-16) |

The advertised `frontcomposer://lifecycle/{correlationId}` is not an additional
registered resource: lifecycle acknowledgements name it, but the configurator
registers manifest projections and documentation resources only. No MCP prompts
or independent framework business command list is registered by this source.

## Framework documentation resources

Each URI below has prefix `frontcomposer://skills/`. The first 12 are ordinary
embedded corpus documents; D13 is a synthetic aggregate manifest. Every row is a
framework documentation read, has no Gateway Query, and requires a separate
documentation delivery/transport decision. Keep documentation accessible while
that decision is deferred; no corpus execution or deletion is authorized.

| ID | Resource id | URI suffix | Disposition | Coverage | Rationale / security class | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D01 | `index` | `index` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/index.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D02 | `team-overlays` | `team-overlays` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/team-overlays.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D03 | `domain-commands` | `domain/commands` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/domain/commands.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D04 | `domain-projections` | `domain/projections` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/domain/projections.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D05 | `domain-validation` | `domain/validation` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/domain/validation.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D06 | `mcp-projection-markdown` | `mcp/projection-markdown` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/mcp/projection-markdown.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D07 | `mcp-tools-resources-lifecycle` | `mcp/tools-resources-lifecycle` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/mcp/tools-resources-lifecycle.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D08 | `migration-versioned-corpus-rules` | `migration/versioned-corpus-rules` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/migration/versioned-corpus-rules.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D09 | `samples-new-bounded-context` | `samples/new-bounded-context` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/samples/new-bounded-context.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D10 | `security-tenant-and-policy-boundaries` | `security/tenant-and-policy-boundaries` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/security/tenant-and-policy-boundaries.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D11 | `setup-package-and-hosting` | `setup/package-and-hosting` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/setup/package-and-hosting.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D12 | `testing-generated-code-validator` | `testing/generated-code-validator` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/testing/generated-code-validator.md:8` | [A1](#a1-session-approval-2026-10-16) |
| D13 | `skills-manifest` | `manifest` | defer | exclude | Synthetic framework documentation index; non-Gateway read. | `Mcp/Skills/FrontComposerSkillResourceProvider.cs:102`; `Mcp/Skills/SkillCorpusAggregateManifestBuilder.cs:8` | [A1](#a1-session-approval-2026-10-16) |

The embedding glob is declared in `Mcp/Hexalith.FrontComposer.Mcp.csproj:30`;
`Mcp/Skills/FrontComposerSkillResourceProvider.cs:70` adds the synthetic resource.
Document metadata supplies IDs at line 2 and URIs at line 8. The source checker
checks this finite set without discovering or loading agent skills.

## FrontComposer CLI boundary

The FrontComposer CLI is compiler/developer tooling, distinct from Projects'
18 Frozen CLI spellings. Neither leaf is a Gateway business operation. Retain
these tools pending a separate owner decision; do not treat migration of the MCP
package as evidence that local compiler tooling can be removed.

| ID | CLI leaf | Disposition | Coverage | Rationale / missing replacement | Security class | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | `inspect` | defer | exclude | Generated-source/diagnostic inspection, optional build; retain developer tooling rather than inventing a Gateway Query. V06 specifies selectors/options. | Local source read; optional build execution | `Cli/CliApplication.cs:19`; `Cli/InspectCommand.cs:7` | [A1](#a1-session-approval-2026-10-16) |
| C02 | `migrate` | defer | exclude | Local versioned source migration, default dry-run and explicit apply; requires a separate compiler-tool ownership/replacement decision, never a domain Command. | Local file mutation when applied | `Cli/CliApplication.cs:22`; `Cli/MigrationCommand.cs:13` | [A1](#a1-session-approval-2026-10-16) |

## Host and CLI compatibility variants

| ID | Current behavior | Disposition / coverage | Required handoff / rationale | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- |
| V01 | Lifecycle input requires exactly one canonical ULID correlationId/messageId; lookup returns bounded in-memory transitions only after current-tool admission is rechecked. The process-wide store indexes handles and has no originating tenant/user binding. Acknowledgement URI is metadata, not a registered event stream. | defer / exclude | No lifecycle streaming, event reading or polling engine in v1. Require explicit originating ownership proof in an approved generic status design, including expiry/history/long-poll limits, before replacement; acceptance is not effect confirmation. | `Mcp/McpJsonSchemaBuilder.cs:57`; `Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs:46`, `:92`; `Mcp/Invocation/FrontComposerMcpLifecycleStore.cs:110`, `:307` | [A1](#a1-session-approval-2026-10-16) |
| V02 | HTTP `/mcp` requires authorization and real tenant tool/resource gates; sample allow-all gates are rejected outside Development. | defer / exclude | McpCli v1 stdio has no equivalent forwarded per-user HTTP identity or host policy. Preserve authenticated tenant authority at Gateway/module admission; a later approved generic HTTP design owns transport replacement. | `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:59`, `:79`; `Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs:21` | [A1](#a1-session-approval-2026-10-16) |
| V03 | API-key header defaults to X-FrontComposer-Mcp-Key; supplied invalid/multiple keys fail without claims fallback. A valid key takes precedence over authenticated claims and calls Create with claimsSource: null, yielding tenant/user only; the no-key authenticated-claims path preserves source roles/claims. No erasure/key-rotation operation is registered in inspected fixed framework/CLI surfaces: ApiKeys is configuration, not a rotation tool. Dynamic manifest operations remain H02-owned. | defer / exclude | Keep caller provenance and the key/claims authority difference explicit; an operator actor/tenant or allowlisted extension is not equivalent authenticated authority. Unsupported erasure/key-rotation variants remain defer/exclude; manifest owners must inventory their operations separately. No new identity server or module-specific auth adapter. | `Mcp/HttpFrontComposerMcpAgentContextAccessor.cs:79`, `:96`, `:110`, `:179`; `Mcp/FrontComposerMcpOptions.cs:18`, `:20` | [A1](#a1-session-approval-2026-10-16) |
| V04 | Policy-gated tools are hidden without a working policy gate; caller-supplied derivable identity/message/correlation fields are rejected and server fields injected. Unknown/hidden failures are sanitized. | defer / exclude | Preserve deny-before-dispatch and nondisclosure when replacing typed tools. Generic Catalog listing/read-only semantics are different and do not prove policy parity. | `Mcp/Invocation/FrontComposerMcpToolAdmissionService.cs:122`, `:207`; `Mcp/Invocation/FrontComposerMcpCommandInvoker.cs:66`, `:219` | [A1](#a1-session-approval-2026-10-16) |
| V05 | Projection reads recheck tenant visibility before query/render, descriptor epochs and schema fingerprints, bound take/rows/cells/Markdown and produce Markdown. x-frontcomposer-schema-fingerprint accepts supported algorithms and lowercase SHA-256 syntax with length bounds. Corpus docs bypass the tenant projection gate. | defer / exclude | Preserve redaction, output bounds, schema failure and freshness semantics at appropriate boundaries. JSON Query output alone is not Markdown/resource/schema-negotiation parity; no MCP resources/prompts in v1. | `Mcp/Invocation/FrontComposerMcpProjectionReader.cs:45`, `:76`; `Mcp/FrontComposerMcpOptions.cs:24`; `Mcp/HttpFrontComposerMcpAgentContextAccessor.cs:113`; `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:66` | [A1](#a1-session-approval-2026-10-16) |
| V06 | Inspect supports type/project/solution/configuration/framework selectors, optional build, format, severity, fail-on-warning/error and absolute paths. | defer / exclude | Preserve local developer workflow and explicit build choice separately. CLI supports text default or JSON; source severity also accepts information. No generated McpCli subcommand or compiler dependency. | `Cli/CliApplication.cs:52`; `Cli/InspectCommand.cs:7`, `:78` | [A1](#a1-session-approval-2026-10-16) |
| V07 | Migrate supports from/to, project/solution, dry-run/apply, text/JSON and fail-on-findings; current catalog only 9.1.0 to 9.2.0; safety policy excludes submodule paths. Apply rechecks canonical targets and source hashes before sequential writes. Earlier writes remain after a later failure/cancellation; partial runs report applied:false. | defer / exclude | Retain safe local dry-run/apply semantics and make drift detection, retained partial writes and applied:false explicit in any future compatibility decision. This inventory executes no migration tooling, build inputs or external writes. | `Cli/MigrationCommand.cs:13`, `:39`; `Cli/MigrationCatalog.cs:4`; `Cli/WriteSafetyPolicy.cs:4`; `Cli/MigrationApplier.cs:9`, `:28`, `:33`, `:51` | [A1](#a1-session-approval-2026-10-16) |
| V08 | Root no-arg/help/--help/-h returns help; CLI exit codes 0–4; legacy solution selector supports .sln and rejects .slnx. Options accept --name value and --name=value, reject repeated named options, and flags use presence rather than parsed Boolean values: --apply=false selects apply. | defer / exclude | Record current behavior without executing legacy .sln or migration tooling. An explicit future compatibility decision must preserve or approve changes to parser syntax, duplicate rejection and presence-based flags; McpCli JSON/error/exit and .slnx contracts do not replace this developer tool. | `Cli/CliApplication.cs:13`, `:41`, `:54`; `Cli/CommandOptions.cs:31`, `:91`, `:99`; `Cli/MigrationCommand.cs:13` | [A1](#a1-session-approval-2026-10-16) |

## Shared retirement prerequisites

A1 retains these unresolved gates and their owning roles; it does not fulfill
them. The host and Projects plug-in remain nondeletable together until both
inventories' retirement gates pass, including other host consumers' capabilities.

| ID | Required decision / evidence | Owning maintainer role | Approval |
| --- | --- | --- | --- |
| G1 | Approve both pinned inventories and every exclusion with actual authority references. Inventory each additional manifest/host registration before asserting complete host coverage; Projects-only counts are not an ecosystem census. | Projects and FrontComposer owning maintainers | [A1](#a1-session-approval-2026-10-16) |
| G2 | Slim and publish Projects Contracts, approve exact canonical/decorated mappings and Gateway routing, then pass independent Catalog coverage, both-head conformance, tenant/policy denied cases, persisted effects and release gates. | Projects, Gateway and McpCli maintainers | [A1](#a1-session-approval-2026-10-16) |
| G3 | Resolve lifecycle, HTTP caller authority, schema/resource/documentation transport and local compiler ownership through approved generic decisions or explicit withdrawals. No per-module server/plugin, REST adapter, executor retry, stream reader or MCP resource is added to v1. | FrontComposer and McpCli contract/transport/security maintainers | [A1](#a1-session-approval-2026-10-16) |
| G4 | Mark FrontComposer host and Projects plug-in deletable only together after G1–G3 and the companion G1–G6 pass. Keep other manifest, document and local compiler consumers accounted for. Deferral/exclusion never opens deletion. | Projects and FrontComposer owning maintainers | [A1](#a1-session-approval-2026-10-16) |

Verification: [Story 4.3 static checks](evidence/story-4-3/verification.md).

---
inventory_version: '1.0.0-candidate.1'
status: draft
module: frontcomposer
source_repository: 'https://github.com/Hexalith/Hexalith.FrontComposer'
source_revision: '81a440a8890a17edb39924bd0cf676eb6f6b5c25'
source_spec: '_bmad-output/implementation-artifacts/spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md'
approval_status: pending
approval_ref: '#a0-approval-pending'
---

# FrontComposer migration inventory v1 candidate

This inventory covers the framework host separately from the
[Projects business inventory](projects-migration-inventory-v1.md), with a shared
retirement gate. Source was clean at the full revision above. It records **one
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

Every row is recommended **defer / exclude**. The host's lifecycle, documentation,
schema, HTTP identity and compiler capabilities have no gateway-ready decorated
Command/Query replacement established here. No canonical McpCli operation/type
is invented for them. The inventories are documentation outside `src/`, never
runtime configuration.

## A0 Approval pending

The requesting user's build instruction authorizes preparation, not owning
maintainer approval. All A0 references mean **pending**. The FrontComposer
maintainer owns H01–H03, D01–D13, C01–C02 and V01–V08; G1–G4 identify shared
handoff owners. Record actual approval authority/reference, exact version and
both source revisions before claiming approval. Session approval must be labelled
as such, without inventing a named external signatory.

Recommended deferrals retain all existing surfaces. Excluding a row from McpCli
coverage is neither withdrawal nor authorization to delete its host, package,
documentation or compiler tooling. Future loss of a convenience still requires
an approved decision. Projects approval alone cannot approve framework or other
manifest consumers' retirement.

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
| H01 | `frontcomposer.lifecycle.subscribe` | defer | exclude | Current bounded in-memory lifecycle snapshot requires an approved generic status/transport contract; Gateway acceptance alone does not replace observed lifecycle. V01 applies. | Identity-bound command lifecycle read | `Mcp/FrontComposerMcpOptions.cs:52`; `Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs:46` | [A0](#a0-approval-pending) |
| H02 | Manifest-defined command tool family | defer | exclude | Registered/generated manifests determine the names; Projects' five concrete tools are M01–M05 in the companion. Other consumers need their own pinned inventories, exact Contracts and approval before host removal. No dynamic plug-in loading in McpCli v1. | Tenant/policy-authorized write or module-defined action | `Mcp/FrontComposerMcpOptions.cs:12`; `Mcp/FrontComposerMcpDescriptorRegistry.cs:97` | [A0](#a0-approval-pending) |
| H03 | Manifest-defined projection resource family | defer | exclude | Projects' 11 resources are R01–R11 in the companion. Other descriptors remain host-owned. Each included business read requires a decorated Contracts Query and Gateway semantics; Markdown resource rendering needs a separate decision. | Tenant-filtered projection read | `Mcp/FrontComposerMcpServerOptionsConfigurator.cs:27`; `Mcp/FrontComposerMcpResource.cs:13` | [A0](#a0-approval-pending) |

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
| D01 | `index` | `index` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/index.md:8` | [A0](#a0-approval-pending) |
| D02 | `team-overlays` | `team-overlays` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/team-overlays.md:8` | [A0](#a0-approval-pending) |
| D03 | `domain-commands` | `domain/commands` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/domain/commands.md:8` | [A0](#a0-approval-pending) |
| D04 | `domain-projections` | `domain/projections` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/domain/projections.md:8` | [A0](#a0-approval-pending) |
| D05 | `domain-validation` | `domain/validation` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/domain/validation.md:8` | [A0](#a0-approval-pending) |
| D06 | `mcp-projection-markdown` | `mcp/projection-markdown` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/mcp/projection-markdown.md:8` | [A0](#a0-approval-pending) |
| D07 | `mcp-tools-resources-lifecycle` | `mcp/tools-resources-lifecycle` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/mcp/tools-resources-lifecycle.md:8` | [A0](#a0-approval-pending) |
| D08 | `migration-versioned-corpus-rules` | `migration/versioned-corpus-rules` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/migration/versioned-corpus-rules.md:8` | [A0](#a0-approval-pending) |
| D09 | `samples-new-bounded-context` | `samples/new-bounded-context` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/samples/new-bounded-context.md:8` | [A0](#a0-approval-pending) |
| D10 | `security-tenant-and-policy-boundaries` | `security/tenant-and-policy-boundaries` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/security/tenant-and-policy-boundaries.md:8` | [A0](#a0-approval-pending) |
| D11 | `setup-package-and-hosting` | `setup/package-and-hosting` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/setup/package-and-hosting.md:8` | [A0](#a0-approval-pending) |
| D12 | `testing-generated-code-validator` | `testing/generated-code-validator` | defer | exclude | Framework documentation; non-Gateway read. | `Corpus/testing/generated-code-validator.md:8` | [A0](#a0-approval-pending) |
| D13 | `skills-manifest` | `manifest` | defer | exclude | Synthetic framework documentation index; non-Gateway read. | `Mcp/Skills/FrontComposerSkillResourceProvider.cs:102`; `Mcp/Skills/SkillCorpusAggregateManifestBuilder.cs:8` | [A0](#a0-approval-pending) |

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
| C01 | `inspect` | defer | exclude | Generated-source/diagnostic inspection, optional build; retain developer tooling rather than inventing a Gateway Query. V06 specifies selectors/options. | Local source read; optional build execution | `Cli/CliApplication.cs:19`; `Cli/InspectCommand.cs:7` | [A0](#a0-approval-pending) |
| C02 | `migrate` | defer | exclude | Local versioned source migration, default dry-run and explicit apply; requires a separate compiler-tool ownership/replacement decision, never a domain Command. | Local file mutation when applied | `Cli/CliApplication.cs:22`; `Cli/MigrationCommand.cs:13` | [A0](#a0-approval-pending) |

## Host and CLI compatibility variants

| ID | Current behavior | Disposition / coverage | Required handoff / rationale | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- |
| V01 | Lifecycle input requires exactly one canonical ULID correlationId/messageId; current admission is rechecked before returning bounded in-memory transitions. Acknowledgement URI is metadata, not a registered event stream. | defer / exclude | No lifecycle streaming, event reading or polling engine in v1. Decide authenticated generic status semantics and expiry/history/long-poll limits before claiming replacement; acceptance is not effect confirmation. | `Mcp/McpJsonSchemaBuilder.cs:57`; `Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs:46`, `:92`; `Mcp/Invocation/FrontComposerMcpLifecycleStore.cs:73` | [A0](#a0-approval-pending) |
| V02 | HTTP `/mcp` requires authorization and real tenant tool/resource gates; sample allow-all gates are rejected outside Development. | defer / exclude | McpCli v1 stdio has no equivalent forwarded per-user HTTP identity or host policy. Preserve authenticated tenant authority at Gateway/module admission; a later approved generic HTTP design owns transport replacement. | `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:59`, `:79`; `Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs:21` | [A0](#a0-approval-pending) |
| V03 | API-key header defaults to X-FrontComposer-Mcp-Key; supplied invalid/multiple keys fail without claims fallback; otherwise authenticated tenant/user claims supply identity. | defer / exclude | Keep caller provenance, precedence and policy claims intact; a configured operator actor/tenant or allowlisted extension is not equivalent authenticated authority. No new identity server or module-specific auth adapter. | `Mcp/HttpFrontComposerMcpAgentContextAccessor.cs:79`, `:179`; `Mcp/FrontComposerMcpOptions.cs:18` | [A0](#a0-approval-pending) |
| V04 | Policy-gated tools are hidden without a working policy gate; caller-supplied derivable identity/message/correlation fields are rejected and server fields injected. Unknown/hidden failures are sanitized. | defer / exclude | Preserve deny-before-dispatch and nondisclosure when replacing typed tools. Generic Catalog listing/read-only semantics are different and do not prove policy parity. | `Mcp/Invocation/FrontComposerMcpToolAdmissionService.cs:122`, `:207`; `Mcp/Invocation/FrontComposerMcpCommandInvoker.cs:66`, `:219` | [A0](#a0-approval-pending) |
| V05 | Projection reads recheck tenant visibility before query/render, descriptor epochs and schema fingerprints, bound take/rows/cells/Markdown and produce Markdown. Corpus docs bypass the tenant projection gate. | defer / exclude | Preserve redaction, output bounds, schema failure and freshness semantics at appropriate boundaries. JSON Query output alone is not Markdown/resource/schema-negotiation parity; no MCP resources/prompts in v1. | `Mcp/Invocation/FrontComposerMcpProjectionReader.cs:45`; `Mcp/HttpFrontComposerMcpAgentContextAccessor.cs:113`; `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:66` | [A0](#a0-approval-pending) |
| V06 | Inspect supports type/project/solution/configuration/framework selectors, optional build, format, severity, fail-on-warning/error and absolute paths. | defer / exclude | Preserve local developer workflow and explicit build choice separately. CLI supports text default or JSON; source severity also accepts information. No generated McpCli subcommand or compiler dependency. | `Cli/CliApplication.cs:52`; `Cli/InspectCommand.cs:7`, `:78` | [A0](#a0-approval-pending) |
| V07 | Migrate supports from/to, project/solution, dry-run/apply, text/JSON and fail-on-findings; current catalog only 9.1.0 to 9.2.0; safety policy excludes submodule paths. | defer / exclude | Retain safe local dry-run/apply semantics in owning compiler tooling. This build does not execute migration, build inputs or write external files. | `Cli/MigrationCommand.cs:13`, `:39`; `Cli/MigrationCatalog.cs:4`; `Cli/WriteSafetyPolicy.cs:4` | [A0](#a0-approval-pending) |
| V08 | Root no-arg/help/--help/-h returns help; CLI exit codes 0–4; legacy solution selector supports .sln and rejects .slnx. | defer / exclude | Record current behavior without running a forbidden legacy .sln workflow. Preserve developer compatibility through a separate decision; McpCli's JSON/error/exit contract and required .slnx do not replace this tool. | `Cli/CliApplication.cs:13`, `:41`, `:54` | [A0](#a0-approval-pending) |

## Shared retirement prerequisites

| ID | Required decision / evidence | Owning maintainer role | Approval |
| --- | --- | --- | --- |
| G1 | Approve both pinned inventories and every exclusion with actual authority references. Inventory each additional manifest/host registration before asserting complete host coverage; Projects-only counts are not an ecosystem census. | Projects and FrontComposer owning maintainers | [A0](#a0-approval-pending) |
| G2 | Slim and publish Projects Contracts, approve exact canonical/decorated mappings and Gateway routing, then pass independent Catalog coverage, both-head conformance, tenant/policy denied cases, persisted effects and release gates. | Projects, Gateway and McpCli maintainers | [A0](#a0-approval-pending) |
| G3 | Resolve lifecycle, HTTP caller authority, schema/resource/documentation transport and local compiler ownership through approved generic decisions or explicit withdrawals. No per-module server/plugin, REST adapter, executor retry, stream reader or MCP resource is added to v1. | FrontComposer and McpCli contract/transport/security maintainers | [A0](#a0-approval-pending) |
| G4 | Mark FrontComposer host and Projects plug-in deletable only together after G1–G3 and the companion G1–G6 pass. Keep other manifest, document and local compiler consumers accounted for. Deferral/exclusion never opens deletion. | Projects and FrontComposer owning maintainers | [A0](#a0-approval-pending) |

Verification: [Story 4.3 static checks](evidence/story-4-3/verification.md).

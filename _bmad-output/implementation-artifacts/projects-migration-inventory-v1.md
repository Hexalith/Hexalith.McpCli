---
inventory_version: '1.0.0-candidate.1'
status: draft
module: projects
source_repository: 'https://github.com/Hexalith/Hexalith.Projects'
source_revision: '3d256e632a7645bc2261e668ac7c74be81155f58'
source_spec: '_bmad-output/implementation-artifacts/spec-4-3-approve-projects-and-frontcomposer-migration-inventories.md'
approval_status: pending
approval_ref: '#a0-approval-pending'
---

# Projects migration inventory v1 candidate

This source-pinned candidate accounts for **11 MCP resources, five maintenance
tools and 18 Frozen CLI spellings**. The Projects checkout was clean at the
revision above. It updates the September draft's evidence without changing that
historical snapshot. Its companion is the
[FrontComposer inventory](frontcomposer-migration-inventory-v1.md).

Every current row is recommended **defer / exclude**. No Projects Contracts type
has McpCli decorations at this pin, and its dependency-heavy Contracts project
cannot be enrolled as it stands. No row currently supplies a gateway-ready
canonical Operation plus decorated CLR type. Read handoffs below describe the
missing Query semantics, not approved names, existing replacement DTOs or Catalog
coverage. All tables are documentation outside `src/`, never runtime configuration.

## A0 Approval pending

No inventory approval has been given in this build session. The request to build
Story 4.3 authorizes investigation and preparation; it does not establish Projects
or FrontComposer owner sign-off. All A0 references explicitly mean **pending**.
The Projects maintainer owns R01–R11, M01–M05, L01–L18 and V01–V12; the roles in
G1–G6 own their respective handoffs. Finalization must record the actual approving
instruction/reference, authority, source revisions, version, covered rows and
limits. Session approval must be labelled as such, without inventing an external
signatory. Missing owner approval blocks an owner-approved completeness claim.

The recommended decision preserves all legacy capabilities for now. It proposes
no withdrawal, enrollment, exposure, publication or deletion. Accepting these
deferrals does not accept future behavior loss; any `replace / include` revision
requires exact canonical names, decorated types, Gateway routing and proof.

## Source notation

Paths below are relative to the pinned `references/Hexalith.Projects/` checkout.
`Mcp/`, `Cli/`, `Contracts/` and `Server/` abbreviate
`src/Hexalith.Projects.Mcp/`, `src/Hexalith.Projects.Cli/`,
`src/Hexalith.Projects.Contracts/` and `src/Hexalith.Projects.Server/`.
The descriptor declares resources at `Mcp/ProjectsMcpDescriptors.cs:24` and
maintenance actions at `:43`; `:84` constructs the resource URIs and `:95`
constructs tool names. Those are legacy protocol names, not McpCli operations.

## Legacy resources and missing Query semantics

All resources use `frontcomposer://Projects/projections/<resource-name>`.
None is currently included. Each eventual included read must name its own typed,
decorated Contracts Query and exact Gateway domain, wire, aggregate and projection
route; a resource descriptor or matching context Query is insufficient (G1–G4).

| ID | Legacy resource | Disposition | Coverage | Query requirement / rationale | Security class | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | `projects.inventory` | defer | exclude | Typed visible inventory Query; preserve lifecycle, bounded rows, freshness and tenant filtering (V01). | Tenant metadata read | `Mcp/ProjectsMcpResourceReader.cs:96` | [A0](#a0-approval-pending) |
| R02 | `projects.detail` | defer | exclude | Typed detail Query; choose explicit project selection versus legacy first-visible default (V01). | Tenant metadata read | `Mcp/ProjectsMcpResourceReader.cs:121` | [A0](#a0-approval-pending) |
| R03 | `projects.operatorDiagnostic` | defer | exclude | Typed bounded diagnostic Query; preserve lifecycle, safe reasons, task/correlation/audit evidence and no command bodies. | Operator diagnostic read | `Mcp/ProjectsMcpResourceReader.cs:142` | [A0](#a0-approval-pending) |
| R04 | `projects.referenceHealth` | defer | exclude | Typed reference-health Query; preserve bounded reference rows, trust state and observation/watermark evidence. | Cross-module reference metadata | `Mcp/ProjectsMcpResourceReader.cs:162` | [A0](#a0-approval-pending) |
| R05 | `projects.resolutionTrace` | defer | exclude | Static descriptor only; never claim CLI REST resolution parity from it (V02). Decide a Query or approved static-document exclusion. | Public-shaped metadata behind host gates | `Mcp/ProjectsMcpResourceReader.cs:377` | [A0](#a0-approval-pending) |
| R06 | `projects.auditTimeline` | defer | exclude | Typed bounded audit Query; suppress idempotency keys and command bodies, preserve safe task/correlation evidence. | Sensitive audit metadata | `Mcp/ProjectsMcpResourceReader.cs:183` | [A0](#a0-approval-pending) |
| R07 | `projects.safeDiagnosticExport` | defer | exclude | Typed redacted summary Query; export means JSON metadata, not file/content transport (V10). | Redacted operator diagnostic | `Mcp/ProjectsMcpResourceReader.cs:205` | [A0](#a0-approval-pending) |
| R08 | `projects.warningQueue` | defer | exclude | Typed composite Query; preserve visible-project scan window, partial diagnostic failures, bounded rows and total semantics (V03). | Tenant diagnostic metadata | `Mcp/ProjectsMcpResourceReader.cs:224` | [A0](#a0-approval-pending) |
| R09 | `projects.warningScanSummary` | defer | exclude | Typed composite summary Query with scan and unavailability evidence; no empty-success substitution for failed reads. | Tenant diagnostic metadata | `Mcp/ProjectsMcpResourceReader.cs:231` | [A0](#a0-approval-pending) |
| R10 | `projects.operationalDashboard` | defer | exclude | Typed composite Query retaining active/archived and warning counters; not just an inventory alias. | Tenant diagnostic metadata | `Mcp/ProjectsMcpResourceReader.cs:246` | [A0](#a0-approval-pending) |
| R11 | `projects.maintenanceAction` | defer | exclude | Static action/confirmation/lifecycle metadata; decide an approved documentation replacement independently of executable writes (V04). | Maintenance metadata behind host gates | `Mcp/ProjectsMcpResourceReader.cs:361` | [A0](#a0-approval-pending) |

## Legacy maintenance tools

Source Command candidates under `Hexalith.Projects.Contracts.Commands` are
undecorated and differ from the strict request DTOs admitted by the server. G1
must resolve those schemas and their explicit legacy wire discriminators before
any canonical McpCli name/type is approved. Shared source candidates are not
counted as separate operations merely because a CLI spelling also invokes them.

| ID | Legacy tool | Disposition | Coverage | Existing source candidate / unresolved mapping | Rationale and security class | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | `projects.archive` | defer | exclude | `Hexalith.Projects.Contracts.Commands.ArchiveProject`; wire `Hexalith.Projects.Commands.ArchiveProject` | Lifecycle write; preserve confirmation, dry-run evidence, actor/tenant authority, task and caller idempotency (V05–V08). | `Mcp/ProjectsMcpCommandService.cs:63` | [A0](#a0-approval-pending) |
| M02 | `projects.restore` | defer | exclude | `Hexalith.Projects.Contracts.Commands.RestoreProject`; wire `Hexalith.Projects.Commands.RestoreProject` | Lifecycle write; same admission and confirmation gates as M01. | `Mcp/ProjectsMcpCommandService.cs:74` | [A0](#a0-approval-pending) |
| M03 | `projects.relink` | defer | exclude | Folder: `Hexalith.Projects.Contracts.Commands.SetProjectFolder`; file: `Hexalith.Projects.Contracts.Commands.LinkFileReference`; memory: `Hexalith.Projects.Contracts.Commands.LinkMemory`. Explicit wires omit `.Contracts`. Conversation relink is unsupported. | Cross-module reference write; split by reference kind, preserve labels, folder replacement confirmation and transient file ACL evidence (V06). | `Mcp/ProjectsMcpCommandService.cs:92` | [A0](#a0-approval-pending) |
| M04 | `projects.unlink` | defer | exclude | File: `Hexalith.Projects.Contracts.Commands.UnlinkFileReference`; memory: `Hexalith.Projects.Contracts.Commands.UnlinkMemory`; explicit wires omit `.Contracts`. Conversation unlink uses the Conversations assignment authority, not a Projects Command. Folder unlink is unsupported. | Destructive reference write; cross-module authorization and unlink ownership need an approved mapping (V06). | `Mcp/ProjectsMcpCommandService.cs:150` | [A0](#a0-approval-pending) |
| M05 | `projects.reevaluate` | defer | exclude | REST `RefreshProjectContextAsync`; existing `Hexalith.Projects.Contracts.Queries.RefreshProjectContextQuery` is not decorated or a registered equivalent refresh handler. | Read-style context refresh wrapped as Accepted; decide Query effects and freshness, do not fabricate a Command or infer committed effects (V07). | `Mcp/ProjectsMcpCommandService.cs:205` | [A0](#a0-approval-pending) |

## Frozen CLI spellings

The parser accepts the optional leading `projects` token, ten read spellings,
seven mutation/preview spellings and `diagnostic export`. Source declarations:
`Cli/ProjectsCliParser.cs:35`, `:49`, `:81`; dispatch:
`Cli/ProjectsCliApplication.cs:39`. Each spelling remains explicit even when it
shares behavior with another row. Tool and CLI equivalence is conditional on the
differences in V01–V12, not asserted by the association column.

| ID | Spelling after `projects` | Association | Disposition | Coverage | Rationale / missing contract | Security class | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L01 | `list` | R01 | defer | exclude | Typed visible inventory Query, preserving CLI result shape. | Tenant metadata read | [A0](#a0-approval-pending) |
| L02 | `describe` | R02 | defer | exclude | Explicit `--project-id`; unlike resource first-visible default. | Tenant metadata read | [A0](#a0-approval-pending) |
| L03 | `inspect` | R02, L02 | defer | exclude | Separate accepted spelling sharing detail dispatch. | Tenant metadata read | [A0](#a0-approval-pending) |
| L04 | `trace` | V02 | defer | exclude | Actual conversation/attachment resolution Query needed; R05 is static. | Cross-module resolution metadata | [A0](#a0-approval-pending) |
| L05 | `trace-resolution` | L04 | defer | exclude | Parser alias; same resolution variants and requirements. | Cross-module resolution metadata | [A0](#a0-approval-pending) |
| L06 | `validate` | R04 | defer | exclude | Explicit-project reference-health Query. | Cross-module reference metadata | [A0](#a0-approval-pending) |
| L07 | `validate-references` | L06 | defer | exclude | Parser alias; retain validation semantics. | Cross-module reference metadata | [A0](#a0-approval-pending) |
| L08 | `audit` | R06 | defer | exclude | Explicit-project bounded audit Query. | Sensitive audit metadata | [A0](#a0-approval-pending) |
| L09 | `warnings` | R08, R09 | defer | exclude | Composite warning rows and scan summary, preserving bounded/partial outcomes. | Tenant diagnostic metadata | [A0](#a0-approval-pending) |
| L10 | `dashboard` | R10 | defer | exclude | Composite counters Query, not an inventory alias. | Tenant diagnostic metadata | [A0](#a0-approval-pending) |
| L11 | `diagnostic export` | R07 | defer | exclude | Explicit-project safe JSON export; no local-file export adapter. | Redacted operator diagnostic | [A0](#a0-approval-pending) |
| L12 | `dry-run` | V04 | defer | exclude | Local preview only; decide documentation/non-Gateway replacement. | Local preview metadata | [A0](#a0-approval-pending) |
| L13 | `preview` | V04 | defer | exclude | Local preview dispatch; distinct displayed command. | Local preview metadata | [A0](#a0-approval-pending) |
| L14 | `archive` | M01 | defer | exclude | Command plus diagnostic audit reload (V05,V07); no generic post-submit polling. | Lifecycle write | [A0](#a0-approval-pending) |
| L15 | `restore` | M02 | defer | exclude | Command plus diagnostic audit reload (V05,V07). | Lifecycle write | [A0](#a0-approval-pending) |
| L16 | `relink` | M03 | defer | exclude | Folder/file/memory variants; transient file ACL context required. | Cross-module reference write | [A0](#a0-approval-pending) |
| L17 | `unlink` | M04 | defer | exclude | Conversation/file/memory variants; no folder variant. | Destructive reference write | [A0](#a0-approval-pending) |
| L18 | `reevaluate` | M05 | defer | exclude | Query refresh plus diagnostic reload; different evidence requirements from MCP. | Context refresh read | [A0](#a0-approval-pending) |

## Compatibility and excluded variants

Every variant is proposed `defer / exclude`; none authorizes removing legacy
behavior. Unimplemented or unsupported variants are named explicitly rather than
counted as additional supported operations.

| ID | Variant and current behavior | Disposition / coverage | Required handoff and security implication | Source evidence | Approval |
| --- | --- | --- | --- | --- | --- |
| V01 | Resource detail/diagnostics select first visible project; CLI requires `--project-id`. Resource audit defaults 25, maximum 100; inventory defaults 25, maximum 100. | defer / exclude | Define selection, lifecycle filtering, totals and authoritative envelope paging per new Query; never leak another tenant or silently equate distinct defaults. | `Mcp/ProjectsMcpResourceReader.cs:24`, `:393`; `Cli/ProjectsCliApplication.cs:42` | [A0](#a0-approval-pending) |
| V02 | CLI resolution selects conversation mode with `--conversation-id`, else repeated `--folder-id` / `--file-id`; supports `--include-archived` and optional `--correlation-id`. R05 returns static zero counts/epoch. | defer / exclude | Define separate bounded typed resolution Queries, redacted candidate/exclusion semantics and freshness. Existing context Queries are not an equivalent resolution contract. | `Cli/ProjectsCliApplication.cs:296`; `Mcp/ProjectsMcpResourceReader.cs:377` | [A0](#a0-approval-pending) |
| V03 | Warning reads scan the first 25 visible projects in ordinal project-ID order and count unavailable diagnostics; queue rows and summary/dashboard differ. | defer / exclude | Preserve partial/unavailable outcomes, stable scan ordering and trustworthy totals; dashboard lifecycle counts use the full visible list. Do not label incomplete scans complete. | `Mcp/ProjectsMcpResourceReader.cs:268`; `src/Hexalith.Projects.Client/Diagnostics/ProjectWarningScanWindow.cs:15`; `Cli/ProjectsCliApplication.cs:220` | [A0](#a0-approval-pending) |
| V04 | MCP R11 describes lifecycle/confirmation; CLI `dry-run` / `preview` produces local metadata using optional `--action` / `--project-id`. | defer / exclude | No state validation or signed dry-run proof is established by local preview. Keep metadata and executable operations distinct; a future non-Gateway decision owns this convenience. | `Mcp/ProjectsMcpResourceReader.cs:361`; `Cli/ProjectsCliApplication.cs:328` | [A0](#a0-approval-pending) |
| V05 | CLI mutations require project, correlation and task; non-reevaluate actions also require caller key, confirmation and nonblank dry-run evidence. MCP derives correlation/task and reevaluate still requires dry-run evidence; CLI reevaluate does not. MCP's descriptor marks confirmation/key required even for reevaluate, while its service/action metadata exempts them. | defer / exclude | Preserve effective guards at authenticated Gateway/module admission and settle descriptor/service disagreement; decide any changed evidence contract explicitly. Do not add a module-specific confirmation engine to McpCli. | `Mcp/ProjectsMcpDescriptors.cs:116`; `Mcp/ProjectsMcpCommandService.cs:226`; `Cli/ProjectsCliApplication.cs:341` | [A0](#a0-approval-pending) |
| V06 | Relink folder/file/memory; unlink conversation/file/memory. File relink requires transient folder/workspace/path; optional reference label supplies display metadata. Descriptor enum lists all four kinds but does not implement all combinations. | defer / exclude | Split Commands by actual ownership; transient file values are ordinary payload validation inputs, never file-content transport or trusted authority. Preserve foreign ACL checks and folder replacement confirmation; reject unsupported combinations. | `Mcp/ProjectsMcpCommandService.cs:92`, `:150`, `:247`; `Cli/ProjectsCliApplication.cs:405`, `:469` | [A0](#a0-approval-pending) |
| V07 | MCP dispatch reports Acknowledged then Syncing (reevaluate Confirmed); CLI reloads diagnostics and searches correlation audit evidence. Reevaluate synthesizes Accepted after a REST refresh. | defer / exclude | Generic send returns Gateway acceptance only. Separate submitted versus observed effects; any future confirmation Query or stream needs its own contract/transport decision. No inferred replay/commit result or executor retry. | `Mcp/ProjectsMcpCommandService.cs:36`; `Cli/ProjectsCliApplication.cs:386`, `:530` | [A0](#a0-approval-pending) |
| V08 | MCP fallback correlation uses a GUID-shaped hex value and derives a task fallback; reads also generate correlation hex. Legacy REST submission uses caller idempotency key as MessageId. | defer / exclude | Adopt canonical uppercase ULIDs for McpCli correlation/idempotency without weakening validation. Prove migration to a fresh per-call MessageId plus separate caller-only IdempotencyKey preserves replay/conflict semantics; keep task identity independent. | `Mcp/ProjectsMcpCommandService.cs:59`; `Mcp/ProjectsMcpResourceReader.cs:434`; `Server/EventStoreProjectCommandSubmitter.cs:301` | [A0](#a0-approval-pending) |
| V09 | REST submission uses envelope Tenant and correlation plus `extensions["taskId"]`; processor actor comes from UserId and task falls back to correlation. | defer / exclude | Recommend retaining taskId as an explicitly allowlisted Command extension, subject to G2/G3 proof; ordinary domain/transient reference values stay payload. Tenant stays envelope-only. Actor is operator-resolved; `actorProperty` only fills a declared actor payload member, never tenant/task. Neither actor nor task is an authorization grant. Queries have no generic extension bag. | `Server/EventStoreProjectCommandSubmitter.cs:299`; `Server/ProjectsDomainProcessor.cs:108`, `:805`; McpCli-local `src/Hexalith.McpCli.Core/Execution/RunQueryArguments.cs:12` | [A0](#a0-approval-pending) |
| V10 | No stream reader, file upload/download/content export, or search operation is registered in these descriptors/parser. File relink carries a reference/path; diagnostic export is safe JSON metadata. Reads request Eventually_consistent. | defer / exclude | Future stream/file/search and alternate freshness variants require explicit owner-approved generic contract/transport decisions and exclusions until then. Preserve current redaction and observation evidence; never imply existing capability from a name. | `Mcp/ProjectsMcpDescriptors.cs:24`; `Cli/ProjectsCliParser.cs:35`; `Mcp/ProjectsMcpResourceReader.cs:96`; `Cli/ProjectsCliApplication.cs:278` | [A0](#a0-approval-pending) |
| V11 | CLI uses `HEXALITH_PROJECTS_BASE_ADDRESS`; missing/invalid address fails on stderr before dispatch. Results are JSON stdout; operational errors use its error writer; semantic exit codes are 0/2/3/4/5/10. | defer / exclude | Approve future script migration to McpCli profiles/Gateway settings, shared JSON/error channels and exit 2 for failures; no Projects-specific profile, REST client or output wrapper. | `Cli/Program.cs:9`; `Cli/ProjectsCliApplication.cs:558`; `Cli/ProjectsCliExitCodes.cs:10` | [A0](#a0-approval-pending) |
| V12 | Parser permits repeated arbitrary `--name value` pairs, with `confirm` / `include-archived` flags; last single value wins and folder/file arrays preserve all values. | defer / exclude | Preserve consumed options above; arbitrary ignored options and unconditional JSON formatting do not promise new generic options, shell completion or generated subcommands. | `Cli/ProjectsCliParser.cs:100`; `Cli/ProjectsCliApplication.cs:555` | [A0](#a0-approval-pending) |

## Gateway prerequisites and owning roles

| ID | Unresolved prerequisite and required evidence | Owning maintainer role | Approval |
| --- | --- | --- | --- |
| G1 | Publish slim decorated Contracts with exact schemas, canonical names, explicit wire/domain/project aggregate routes, identifier kind and Query semantics. Source records are not the strict callback payloads. Contracts currently references Conversations.Contracts, FrontComposer.Contracts/Shell, Fluxor, FluentUI and ASP.NET; analyzer-only SourceTools must be assessed separately. Verify the exact released closure against McpCli's dependency policy rather than enrolling source projects. | Projects Contracts and McpCli dependency maintainers | [A0](#a0-approval-pending) |
| G2 | Preserve verified tenant/principal binding and layered reference/lifecycle authorization at direct Gateway/module admission. Legacy REST policy/tenant checks cannot disappear when adapters are bypassed; envelope tenant and actor are inputs, not identity evidence. Prove cross-tenant and unauthorized requests disclose nothing and cause no effect. | Projects security and EventStore/Gateway maintainers | [A0](#a0-approval-pending) |
| G3 | Approve task/correlation/actor/key handoff, strict serialization and replay compatibility for each split Command; decide allowlisted task extensions versus ordinary payload explicitly. `actorProperty` fills a declared actor field from the generic operator actor, never task or tenant. Identity assertion extensions remain forbidden. Query task/freshness requires an approved payload/handler decision. | Projects command/query and generic contract maintainers | [A0](#a0-approval-pending) |
| G4 | Add resource-equivalent Query handlers, redaction/paging/selection/composite/freshness semantics and read vectors. Current registration has three general context handlers plus a workload-bound ChatBot authority handler, not coverage for these 11 resources. Refresh has a wire constant/DTO but no corresponding equivalent registered handler. | Projects query and projection maintainers | [A0](#a0-approval-pending) |
| G5 | Compare the approved inventory independently with the Catalog, then prove both heads, Gateway requests, denied cases, persisted effects and metadata under exact package/vector pins. Static documentation checks are insufficient. | Projects and McpCli conformance maintainers | [A0](#a0-approval-pending) |
| G6 | Retire FrontComposer's host and Projects plug-in only together after Gateway readiness, dependency compliance, complete approved coverage and authorization/behavior/release evidence. Resolve host lifecycle/resource/HTTP capabilities in the companion inventory; neither exclusion nor this candidate authorizes deletion. | Projects and FrontComposer owning maintainers | [A0](#a0-approval-pending) |

Supporting anchors: `Contracts/Hexalith.Projects.Contracts.csproj:18`;
`Server/ProjectsServerModule.cs:23`; `Server/ProjectsServerServiceCollectionExtensions.cs:131`,
`:173`; `Server/Queries/ProjectChatBotAuthorityQueryHandler.cs:49`;
`Server/Authorization/ProjectAuthorizationGate.cs:399`, `:575` (missing/system
tenant, actor and caller-context disagreement fail closed);
`Server/Queries/ProjectQueryEnvelopePrincipalBinding.cs:37` (authenticated subject,
tenant and workload/delegation binding); `Server/ProjectsDomainProcessor.cs:43`
(strict unknown-payload rejection). Direct `/process` validation alone does not
prove equivalence to the full REST authorization gate.
Source completeness checks are preserved in
[Story 4.3 verification](evidence/story-4-3/verification.md).

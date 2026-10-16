---
inventory_version: '1.0.0'
status: approved
module: folders
source_repository: 'https://github.com/Hexalith/Hexalith.Folders'
source_revision: 'e2252f29a2dba2b64786ee483eb59fbceaadd387'
source_spec: '_bmad-output/implementation-artifacts/spec-4-2-approve-the-folders-migration-inventory.md'
maintainer_approval_ref: '#a1-session-approval-2026-10-16'
---

# Folders migration inventory v1

Inventory **1.0.0** records the requesting user's approved deferred scope in
[A1](#a1-session-approval-2026-10-16). It reconciles **49 MCP tools (14 mutations,
35 reads), two MCP resources and 42 Frozen CLI leaves (14 mutations, 28 reads)**
against the clean source revision above and supersedes the unapproved September
draft. It is a documentation and future test artifact outside `src/`, never
runtime configuration.

Every current legacy row is **defer / exclude** from current McpCli coverage.
No Gateway-ready decorated replacement exists at this pin. Folders remains a
post-v1 addition; the existing server and CLI continue to own their behavior.

The normalized table retains **48 possible future operations: 13 Commands and
35 Queries**. `add-file`, `change-file` and `remove-file` share a proposed
`MutateFiles` contract; the ACL grant/revoke variants split into two contracts.
These names/types are roadmap candidates, not included Catalog operations or
existing published DTOs. Query wire/projection routes and exact schemas remain
upstream prerequisites. Moving any row to `replace / include` requires a later
approved inventory revision plus the readiness gates below.

## A1 Session approval (2026-10-16)

- **Approver and authority:** the requesting user in the source-spec session;
  no named Folders maintainer, external signatory or separate upstream approval
  is asserted. Every row's approval reference resolves to this session decision.
- **Exact approving instruction:** "approve and stop", recorded in the
  [source spec's Implementation Notes](spec-4-2-approve-the-folders-migration-inventory.md#implementation-notes)
  after presentation of the complete candidate and recommended deferred scope.
  This final inventory records that decision; the instruction did not grant
  Gateway exposure or authorize execution of future candidates.
- **Source and version:** inventory 1.0.0, finalized from candidate
  1.0.0-candidate.1 at Folders revision
  `e2252f29a2dba2b64786ee483eb59fbceaadd387`.
- **Approved scope:** `defer / exclude` for M01–M49, R01–R02 and L01–L42;
  retain the 48 unique roadmap candidates C01–C13 and Q01–Q35, their shared file
  mutation and split ACL mappings, V01–V10 compatibility decisions and N01–N04
  adjacent exclusions. G1–G6 remain unresolved prerequisites with owning roles.
- **Accepted current limitation:** no Folders operation is included in McpCli.
  The legacy surfaces and their local-file, auto-key, resource, freshness and
  other adapter conveniences stay available through the existing server/CLI.
  Their absence from generic McpCli is recorded here; acceptance of each future
  behavior loss or replacement still requires a later approved revision.
- **Limits:** scope approval supplies no decorated Contracts, package/closure
  evidence, Catalog coverage, Gateway query routing, authenticated tenant/task
  authority, behavior/authorization/live execution proof, new transport,
  dependency exception, runtime change, publication or retention decision.
  No withdrawal or early legacy server/CLI deletion is approved. Existing
  upstream draft Story 5.8 and Projects v1/v2 decisions do not extend A1.

## Reading the rows

- `defer / exclude` retains the legacy capability while documenting what must
  precede a replacement. No row is `withdraw`; no row is currently `include`.
- Future Command types are under `Hexalith.Folders.Contracts.Commands`;
  future Query types under `Hexalith.Folders.Contracts.Queries`. The full names
  are explicit in the target tables. Shared targets occur once there.
- G1–G6 identify unresolved prerequisites and owning roles. V01–V10 record
  concrete compatibility variants. A row's targets, rationale and these rules
  together define its handoff; a matching name alone is insufficient.
- All source paths in evidence cells and the source section are relative to
  the pinned `references/Hexalith.Folders/` checkout unless labelled McpCli-local.

## Gateway prerequisites and owners

A1 approves retaining these gaps and their ownership handoffs; it does not
approve a future implementation or claim that the prerequisites have passed.

| ID | Gap and required evidence | Owning maintainer role | Approval reference |
| --- | --- | --- | --- |
| G1 | Add public typed Contracts DTOs/decorations and verify the exact decorated package's restored closure against AD-15. Current Contracts has no direct package references, but no decorated Command/Query either. Explicitly map existing command wires `Hexalith.Folders.Commands.*` rather than deriving the different `Contracts.Commands.*` full names. Use domain `folders`; determine aggregate/property routing per DTO and String-kind opaque identifier compatibility before publication. Query wire/projection routes remain unresolved. C05 specifically requires reserved ProviderBindingActorId routing and tenant/namespace separation before state lookup: derive the binding actor from the public reference, admit only that reserved namespace, and reject an actor equal to the tenant (`src/Hexalith.Folders.Server/FoldersDomainServiceEndpoints.cs:2109`; `src/Hexalith.Folders.Server/FoldersDomainServiceRequestHandler.cs:85`, `:228`; `src/Hexalith.Folders/Aggregates/Organization/ProviderBindingActorId.cs:13`). | Folders Contracts and McpCli dependency maintainers | [A1](#a1-session-approval-2026-10-16) |
| G2 | Preserve verified tenant/actor authority, layered folder/action authorization, revocation, task/workspace/lease ownership, deny-before-access and content/search egress policy. Envelope tenant/actor are comparison inputs, never self-authenticating authority. Prove denied cross-tenant reads/writes disclose no protected data and cause no mutation. | Folders security and EventStore/Gateway maintainers | [A1](#a1-session-approval-2026-10-16) |
| G3 | `/process` and its processor require lowercase message/correlation/tenant/aggregate/user IDs and `extensions["taskId"]`; McpCli generates canonical uppercase ULIDs. Resolve this upstream without silently lowercasing aggregate IDs or weakening McpCli. Preserve caller idempotency keys independently of generated message IDs; prove replay, changed-input conflict, expiry and task association through admission and persisted effects. Mark key requirements explicitly on future DTOs. | Folders command and EventStore admission maintainers | [A1](#a1-session-approval-2026-10-16) |
| G4 | Register Gateway query handlers for all reads. `/project` now delivers event projections; it is not a query dispatcher. Define supported payload fields and authoritative envelope paging, exact freshness/default rules, task context and rejection of unsupported combinations. McpCli v1 queries carry no extensions/freshness arguments; a Contracts payload works only if an approved handler translates its semantics. Avoid payload/envelope paging conflicts. | Folders query and generic contract/transport maintainers | [A1](#a1-session-approval-2026-10-16) |
| G5 | Preserve metadata-only results/errors, redaction and safe diagnostics before returning data to either generic head. Resolve inline/file staging and policy evidence without importing the Folders client or adding an adapter. Default content/path/delete/commit/context implementations are unavailable; prove configured live effects before inclusion. | Folders file, privacy and runtime maintainers | [A1](#a1-session-approval-2026-10-16) |
| G6 | Preserve provider credential references, readiness/failure/reconciliation semantics and authorization before external egress. Non-Gateway effects or staging require an approved generic contract/transport decision; operation naming is no authority to add REST calls to McpCli. | Folders provider and platform/operator maintainers | [A1](#a1-session-approval-2026-10-16) |

## Legacy MCP tool rows

Each tool is listed once; variant rules below also apply. The `Source` column
anchors the exact tool declaration. All rows reference the approved deferred
scope in A1.

| ID | Legacy tool | Disposition | Coverage | Future target(s) | Rationale / unresolved gap | Security class | Source | Approval reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | `add-file` | defer | exclude | C10 | Add variant of shared mutation; inline content/staging and policy evidence unresolved (G1–G3,G5; V04–V07). | Content-bearing write | `src/Hexalith.Folders.Mcp/Tools/FileTools.cs:24` | [A1](#a1-session-approval-2026-10-16) |
| M02 | `archive-folder` | defer | exclude | C01 | Lifecycle archive, not permission erasure; retain admission and authorization (G1–G3). | Destructive lifecycle write | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:80` | [A1](#a1-session-approval-2026-10-16) |
| M03 | `bind-repository` | defer | exclude | C02 | Preserve repository identity, binding policy and provider evidence (G1–G3,G6). | Repository configuration write | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:44` | [A1](#a1-session-approval-2026-10-16) |
| M04 | `change-file` | defer | exclude | C10 | Change variant of shared mutation; preserve distinct operation kind and content limits (G1–G3,G5; V04–V07). | Content-bearing write | `src/Hexalith.Folders.Mcp/Tools/FileTools.cs:43` | [A1](#a1-session-approval-2026-10-16) |
| M05 | `commit-workspace` | defer | exclude | C03 | Commit execution/reconciliation and metadata-only provider evidence unresolved (G1–G3,G5,G6). | External repository write | `src/Hexalith.Folders.Mcp/Tools/CommitTools.cs:21` | [A1](#a1-session-approval-2026-10-16) |
| M06 | `configure-branch-ref-policy` | defer | exclude | C04 | Preserve allowed-branch policy validation and privileged action gate (G1–G3,G6). | Security policy write | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:133` | [A1](#a1-session-approval-2026-10-16) |
| M07 | `configure-provider-binding` | defer | exclude | C05 | Preserve credential references; no raw provider secrets in payload/results (G1–G3,G6). | Provider/security configuration write | `src/Hexalith.Folders.Mcp/Tools/ProviderTools.cs:20` | [A1](#a1-session-approval-2026-10-16) |
| M08 | `create-folder` | defer | exclude | C06 | Preserve creation validation, identifiers and tenant authority (G1–G3). | Lifecycle write | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:20` | [A1](#a1-session-approval-2026-10-16) |
| M09 | `create-repository-backed-folder` | defer | exclude | C07 | Retain composite creation/binding semantics and provider guards (G1–G3,G6). | Repository lifecycle write | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:32` | [A1](#a1-session-approval-2026-10-16) |
| M10 | `lock-workspace` | defer | exclude | C09 | Retain lease/lock proof, ownership and conflict behavior (G1–G3; V03). | Concurrency-control write | `src/Hexalith.Folders.Mcp/Tools/WorkspaceTools.cs:34` | [A1](#a1-session-approval-2026-10-16) |
| M11 | `prepare-workspace` | defer | exclude | C11 | Retain preparation and path/provider readiness guards (G1–G3,G5,G6). | Workspace lifecycle write | `src/Hexalith.Folders.Mcp/Tools/WorkspaceTools.cs:20` | [A1](#a1-session-approval-2026-10-16) |
| M12 | `release-workspace-lock` | defer | exclude | C12 | Retain owned lock proof and safe release conditions (G1–G3; V03). | Concurrency-control write | `src/Hexalith.Folders.Mcp/Tools/WorkspaceTools.cs:60` | [A1](#a1-session-approval-2026-10-16) |
| M13 | `remove-file` | defer | exclude | C10 | Remove variant of shared mutation; deletion evidence and ownership required (G1–G3,G5; V04,V06,V07). | Destructive file write | `src/Hexalith.Folders.Mcp/Tools/FileTools.cs:62` | [A1](#a1-session-approval-2026-10-16) |
| M14 | `update-folder-acl-entry` | defer | exclude | C08, C13 | Split body.effect grant/revoke explicitly; do not treat ACL erasure as revocation (G1–G3; V08). | Authorization administration write | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:107` | [A1](#a1-session-approval-2026-10-16) |
| M15 | `get-audit-record` | defer | exclude | Q01 | Preserve audit visibility, redaction and filter/paging semantics (G1,G2,G4,G5; V01,V02,V06). | Audit/personal metadata read | `src/Hexalith.Folders.Mcp/Tools/AuditTools.cs:33` | [A1](#a1-session-approval-2026-10-16) |
| M16 | `get-branch-ref-policy` | defer | exclude | Q02 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:146` | [A1](#a1-session-approval-2026-10-16) |
| M17 | `get-commit-evidence` | defer | exclude | Q03 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/CommitTools.cs:35` | [A1](#a1-session-approval-2026-10-16) |
| M18 | `get-dirty-state-diagnostics` | defer | exclude | Q04 | Preserve diagnostic visibility, authorization scope and freshness; no CLI leaf exists (G1,G2,G4,G5; V01,V06). | Protected diagnostic read | `src/Hexalith.Folders.Mcp/Tools/DiagnosticsTools.cs:66` | [A1](#a1-session-approval-2026-10-16) |
| M19 | `get-effective-permissions` | defer | exclude | Q05 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:121` | [A1](#a1-session-approval-2026-10-16) |
| M20 | `get-failed-operation-diagnostics` | defer | exclude | Q06 | Preserve diagnostic visibility, authorization scope and freshness; no CLI leaf exists (G1,G2,G4,G5; V01,V06). | Protected diagnostic read | `src/Hexalith.Folders.Mcp/Tools/DiagnosticsTools.cs:78` | [A1](#a1-session-approval-2026-10-16) |
| M21 | `get-folder-file-metadata` | defer | exclude | Q07 | Preserve typed context/search inputs, task scope, path/egress policy and metadata-only output (G1,G2,G4–G6; V01–V06). | Protected file/context metadata read | `src/Hexalith.Folders.Mcp/Tools/ContextTools.cs:36` | [A1](#a1-session-approval-2026-10-16) |
| M22 | `get-folder-indexing-status` | defer | exclude | Q08 | Preserve typed context/search inputs, task scope, path/egress policy and metadata-only output (G1,G2,G4–G6; V01–V06). | Protected file/context metadata read | `src/Hexalith.Folders.Mcp/Tools/ContextTools.cs:106` | [A1](#a1-session-approval-2026-10-16) |
| M23 | `get-folder-lifecycle-status` | defer | exclude | Q09 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:69` | [A1](#a1-session-approval-2026-10-16) |
| M24 | `get-lock-diagnostics` | defer | exclude | Q10 | Preserve diagnostic visibility, authorization scope and freshness; no CLI leaf exists (G1,G2,G4,G5; V01,V06). | Protected diagnostic read | `src/Hexalith.Folders.Mcp/Tools/DiagnosticsTools.cs:54` | [A1](#a1-session-approval-2026-10-16) |
| M25 | `get-operation-timeline-entry` | defer | exclude | Q11 | Preserve audit visibility, redaction and filter/paging semantics (G1,G2,G4,G5; V01,V02,V06). | Audit/personal metadata read | `src/Hexalith.Folders.Mcp/Tools/AuditTools.cs:59` | [A1](#a1-session-approval-2026-10-16) |
| M26 | `get-projection-freshness` | defer | exclude | Q12 | Preserve diagnostic visibility, authorization scope and freshness; no CLI leaf exists (G1,G2,G4,G5; V01,V06). | Protected diagnostic read | `src/Hexalith.Folders.Mcp/Tools/DiagnosticsTools.cs:90` | [A1](#a1-session-approval-2026-10-16) |
| M27 | `get-provider-binding` | defer | exclude | Q13 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/ProviderTools.cs:33` | [A1](#a1-session-approval-2026-10-16) |
| M28 | `get-provider-outcome` | defer | exclude | Q14 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/CommitTools.cs:48` | [A1](#a1-session-approval-2026-10-16) |
| M29 | `get-provider-status-diagnostics` | defer | exclude | Q15 | Preserve diagnostic visibility, authorization scope and freshness; no CLI leaf exists (G1,G2,G4,G5; V01,V06). | Protected diagnostic read | `src/Hexalith.Folders.Mcp/Tools/DiagnosticsTools.cs:31` | [A1](#a1-session-approval-2026-10-16) |
| M30 | `get-provider-support-evidence` | defer | exclude | Q16 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/ProviderTools.cs:55` | [A1](#a1-session-approval-2026-10-16) |
| M31 | `get-readiness-diagnostics` | defer | exclude | Q17 | Preserve diagnostic visibility, authorization scope and freshness; no CLI leaf exists (G1,G2,G4,G5; V01,V06). | Protected diagnostic read | `src/Hexalith.Folders.Mcp/Tools/DiagnosticsTools.cs:20` | [A1](#a1-session-approval-2026-10-16) |
| M32 | `get-reconciliation-status` | defer | exclude | Q18 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/CommitTools.cs:61` | [A1](#a1-session-approval-2026-10-16) |
| M33 | `get-repository-binding` | defer | exclude | Q19 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:57` | [A1](#a1-session-approval-2026-10-16) |
| M34 | `get-sync-status-diagnostics` | defer | exclude | Q20 | Preserve diagnostic visibility, authorization scope and freshness; no CLI leaf exists (G1,G2,G4,G5; V01,V06). | Protected diagnostic read | `src/Hexalith.Folders.Mcp/Tools/DiagnosticsTools.cs:42` | [A1](#a1-session-approval-2026-10-16) |
| M35 | `get-task-status` | defer | exclude | Q21 | Task ID is a route resource, not task-header context; preserve folder authorization scope (G1,G2,G4; V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/CommitTools.cs:74` | [A1](#a1-session-approval-2026-10-16) |
| M36 | `get-workspace-cleanup-status` | defer | exclude | Q22 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/WorkspaceTools.cs:112` | [A1](#a1-session-approval-2026-10-16) |
| M37 | `get-workspace-lock` | defer | exclude | Q23 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/WorkspaceTools.cs:48` | [A1](#a1-session-approval-2026-10-16) |
| M38 | `get-workspace-retry-eligibility` | defer | exclude | Q24 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/WorkspaceTools.cs:74` | [A1](#a1-session-approval-2026-10-16) |
| M39 | `get-workspace-status` | defer | exclude | Q25 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/WorkspaceTools.cs:100` | [A1](#a1-session-approval-2026-10-16) |
| M40 | `get-workspace-transition-evidence` | defer | exclude | Q26 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/WorkspaceTools.cs:87` | [A1](#a1-session-approval-2026-10-16) |
| M41 | `glob-folder-files` | defer | exclude | Q27 | Preserve typed context/search inputs, task scope, path/egress policy and metadata-only output (G1,G2,G4–G6; V01–V06). | Protected file/context metadata read | `src/Hexalith.Folders.Mcp/Tools/ContextTools.cs:64` | [A1](#a1-session-approval-2026-10-16) |
| M42 | `list-audit-trail` | defer | exclude | Q28 | Preserve audit visibility, redaction and filter/paging semantics (G1,G2,G4,G5; V01,V02,V06). | Audit/personal metadata read | `src/Hexalith.Folders.Mcp/Tools/AuditTools.cs:19` | [A1](#a1-session-approval-2026-10-16) |
| M43 | `list-folder-acl-entries` | defer | exclude | Q29 | Preserve route identifiers, operation-specific freshness and authorization (G1,G2,G4; V01–V03). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/FolderTools.cs:93` | [A1](#a1-session-approval-2026-10-16) |
| M44 | `list-folder-files` | defer | exclude | Q30 | Preserve typed context/search inputs, task scope, path/egress policy and metadata-only output (G1,G2,G4–G6; V01–V06). | Protected file/context metadata read | `src/Hexalith.Folders.Mcp/Tools/ContextTools.cs:21` | [A1](#a1-session-approval-2026-10-16) |
| M45 | `list-operation-timeline` | defer | exclude | Q31 | Preserve audit visibility, redaction and filter/paging semantics (G1,G2,G4,G5; V01,V02,V06). | Audit/personal metadata read | `src/Hexalith.Folders.Mcp/Tools/AuditTools.cs:45` | [A1](#a1-session-approval-2026-10-16) |
| M46 | `read-file-range` | defer | exclude | Q32 | Preserve typed context/search inputs, task scope, path/egress policy and metadata-only output (G1,G2,G4–G6; V01–V06). | Protected file/context metadata read | `src/Hexalith.Folders.Mcp/Tools/ContextTools.cs:78` | [A1](#a1-session-approval-2026-10-16) |
| M47 | `search-folder-files` | defer | exclude | Q33 | Preserve typed context/search inputs, task scope, path/egress policy and metadata-only output (G1,G2,G4–G6; V01–V06). | Protected file/context metadata read | `src/Hexalith.Folders.Mcp/Tools/ContextTools.cs:50` | [A1](#a1-session-approval-2026-10-16) |
| M48 | `search-folder-indexed-files` | defer | exclude | Q34 | Preserve typed context/search inputs, task scope, path/egress policy and metadata-only output (G1,G2,G4–G6; V01–V06). | Protected file/context metadata read | `src/Hexalith.Folders.Mcp/Tools/ContextTools.cs:92` | [A1](#a1-session-approval-2026-10-16) |
| M49 | `validate-provider-readiness` | defer | exclude | Q35 | POST query, not a Command: preserve typed readiness input, exact snapshot consistency and provider egress guards (G1,G2,G4,G6). | Protected operational read | `src/Hexalith.Folders.Mcp/Tools/ProviderTools.cs:44` | [A1](#a1-session-approval-2026-10-16) |

## Normalized future Command candidates

All 13 candidates are deferred/excluded, not current coverage. Full explicit
wire values preserve existing recognizers if an eventual owner-approved design
retains these routes. That routing proposal does not resolve G2/G3 admission.

| ID | Canonical future name | Intended decorated CLR type (new) | Existing wire candidate | Prerequisites | Approval reference |
| --- | --- | --- | --- | --- | --- |
| C01 | `folders.archive-folder` | `Hexalith.Folders.Contracts.Commands.ArchiveFolder` | `Hexalith.Folders.Commands.ArchiveFolder` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C02 | `folders.bind-repository` | `Hexalith.Folders.Contracts.Commands.BindRepository` | `Hexalith.Folders.Commands.BindRepository` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C03 | `folders.commit-workspace` | `Hexalith.Folders.Contracts.Commands.CommitWorkspace` | `Hexalith.Folders.Commands.CommitWorkspace` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C04 | `folders.configure-branch-ref-policy` | `Hexalith.Folders.Contracts.Commands.ConfigureBranchRefPolicy` | `Hexalith.Folders.Commands.ConfigureBranchRefPolicy` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C05 | `folders.configure-provider-binding` | `Hexalith.Folders.Contracts.Commands.ConfigureProviderBinding` | `Hexalith.Folders.Commands.ConfigureProviderBinding` | G1–G3; linked tool/variant rules; preserve reserved ProviderBindingActorId admission and tenant/namespace separation under G1 (`src/Hexalith.Folders.Server/FoldersDomainServiceRequestHandler.cs:228`) | [A1](#a1-session-approval-2026-10-16) |
| C06 | `folders.create-folder` | `Hexalith.Folders.Contracts.Commands.CreateFolder` | `Hexalith.Folders.Commands.CreateFolder` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C07 | `folders.create-repository-backed-folder` | `Hexalith.Folders.Contracts.Commands.CreateRepositoryBackedFolder` | `Hexalith.Folders.Commands.CreateRepositoryBackedFolder` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C08 | `folders.grant-folder-access` | `Hexalith.Folders.Contracts.Commands.GrantFolderAccess` | `Hexalith.Folders.Commands.GrantFolderAccess` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C09 | `folders.lock-workspace` | `Hexalith.Folders.Contracts.Commands.LockWorkspace` | `Hexalith.Folders.Commands.LockWorkspace` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C10 | `folders.mutate-files` | `Hexalith.Folders.Contracts.Commands.MutateFiles` | `Hexalith.Folders.Commands.MutateFiles` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C11 | `folders.prepare-workspace` | `Hexalith.Folders.Contracts.Commands.PrepareWorkspace` | `Hexalith.Folders.Commands.PrepareWorkspace` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C12 | `folders.release-workspace-lock` | `Hexalith.Folders.Contracts.Commands.ReleaseWorkspaceLock` | `Hexalith.Folders.Commands.ReleaseWorkspaceLock` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| C13 | `folders.revoke-folder-access` | `Hexalith.Folders.Contracts.Commands.RevokeFolderAccess` | `Hexalith.Folders.Commands.RevokeFolderAccess` | G1–G3; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |

## Normalized future Query candidates

All 35 candidates are deferred/excluded and absent as decorated Contracts DTOs.
The observed freshness class is the only accepted explicit value in the current
SDK operation catalog; omission selects the legacy default. Future handlers
must prove equivalent semantics and define paging precedence. These names do
not establish a Gateway wire/projection route.

| ID | Canonical future name | Intended decorated CLR type (new) | Observed exact freshness | Prerequisites | Approval reference |
| --- | --- | --- | --- | --- | --- |
| Q01 | `folders.get-audit-record` | `Hexalith.Folders.Contracts.Queries.GetAuditRecord` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q02 | `folders.get-branch-ref-policy` | `Hexalith.Folders.Contracts.Queries.GetBranchRefPolicy` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q03 | `folders.get-commit-evidence` | `Hexalith.Folders.Contracts.Queries.GetCommitEvidence` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q04 | `folders.get-dirty-state-diagnostics` | `Hexalith.Folders.Contracts.Queries.GetDirtyStateDiagnostics` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q05 | `folders.get-effective-permissions` | `Hexalith.Folders.Contracts.Queries.GetEffectivePermissions` | `read_your_writes` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q06 | `folders.get-failed-operation-diagnostics` | `Hexalith.Folders.Contracts.Queries.GetFailedOperationDiagnostics` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q07 | `folders.get-folder-file-metadata` | `Hexalith.Folders.Contracts.Queries.GetFolderFileMetadata` | `snapshot_per_task` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q08 | `folders.get-folder-indexing-status` | `Hexalith.Folders.Contracts.Queries.GetFolderIndexingStatus` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q09 | `folders.get-folder-lifecycle-status` | `Hexalith.Folders.Contracts.Queries.GetFolderLifecycleStatus` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q10 | `folders.get-lock-diagnostics` | `Hexalith.Folders.Contracts.Queries.GetLockDiagnostics` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q11 | `folders.get-operation-timeline-entry` | `Hexalith.Folders.Contracts.Queries.GetOperationTimelineEntry` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q12 | `folders.get-projection-freshness` | `Hexalith.Folders.Contracts.Queries.GetProjectionFreshness` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q13 | `folders.get-provider-binding` | `Hexalith.Folders.Contracts.Queries.GetProviderBinding` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q14 | `folders.get-provider-outcome` | `Hexalith.Folders.Contracts.Queries.GetProviderOutcome` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q15 | `folders.get-provider-status-diagnostics` | `Hexalith.Folders.Contracts.Queries.GetProviderStatusDiagnostics` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q16 | `folders.get-provider-support-evidence` | `Hexalith.Folders.Contracts.Queries.GetProviderSupportEvidence` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q17 | `folders.get-readiness-diagnostics` | `Hexalith.Folders.Contracts.Queries.GetReadinessDiagnostics` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q18 | `folders.get-reconciliation-status` | `Hexalith.Folders.Contracts.Queries.GetReconciliationStatus` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q19 | `folders.get-repository-binding` | `Hexalith.Folders.Contracts.Queries.GetRepositoryBinding` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q20 | `folders.get-sync-status-diagnostics` | `Hexalith.Folders.Contracts.Queries.GetSyncStatusDiagnostics` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q21 | `folders.get-task-status` | `Hexalith.Folders.Contracts.Queries.GetTaskStatus` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q22 | `folders.get-workspace-cleanup-status` | `Hexalith.Folders.Contracts.Queries.GetWorkspaceCleanupStatus` | `read_your_writes` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q23 | `folders.get-workspace-lock` | `Hexalith.Folders.Contracts.Queries.GetWorkspaceLock` | `read_your_writes` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q24 | `folders.get-workspace-retry-eligibility` | `Hexalith.Folders.Contracts.Queries.GetWorkspaceRetryEligibility` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q25 | `folders.get-workspace-status` | `Hexalith.Folders.Contracts.Queries.GetWorkspaceStatus` | `read_your_writes` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q26 | `folders.get-workspace-transition-evidence` | `Hexalith.Folders.Contracts.Queries.GetWorkspaceTransitionEvidence` | `snapshot_per_task` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q27 | `folders.glob-folder-files` | `Hexalith.Folders.Contracts.Queries.GlobFolderFiles` | `snapshot_per_task` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q28 | `folders.list-audit-trail` | `Hexalith.Folders.Contracts.Queries.ListAuditTrail` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q29 | `folders.list-folder-acl-entries` | `Hexalith.Folders.Contracts.Queries.ListFolderAclEntries` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q30 | `folders.list-folder-files` | `Hexalith.Folders.Contracts.Queries.ListFolderFiles` | `snapshot_per_task` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q31 | `folders.list-operation-timeline` | `Hexalith.Folders.Contracts.Queries.ListOperationTimeline` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q32 | `folders.read-file-range` | `Hexalith.Folders.Contracts.Queries.ReadFileRange` | `snapshot_per_task` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q33 | `folders.search-folder-files` | `Hexalith.Folders.Contracts.Queries.SearchFolderFiles` | `snapshot_per_task` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q34 | `folders.search-folder-indexed-files` | `Hexalith.Folders.Contracts.Queries.SearchFolderIndexedFiles` | `eventually_consistent` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |
| Q35 | `folders.validate-provider-readiness` | `Hexalith.Folders.Contracts.Queries.ValidateProviderReadiness` | `snapshot_per_task` | G1,G2,G4; linked tool/variant rules | [A1](#a1-session-approval-2026-10-16) |

## Legacy MCP resource rows

Resource transport is outside McpCli v1. The shared query semantics remain
future candidates; no generic MCP resource is added and no current surface is
withdrawn. These two rows do not add target operations.

| ID | Resource / URI template | Disposition | Coverage | Future semantics | Rationale / security class | Source | Approval reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | `audit-trail` / `folders://audit-trail/{folderId}` | defer | exclude | Q28 | Resource uses omitted freshness/filter/cursor/limit; preserve default authorized metadata view through a future Query. Protected audit read; G1,G2,G4,G5. | `src/Hexalith.Folders.Mcp/Resources/AuditTrailResource.cs:26` | [A1](#a1-session-approval-2026-10-16) |
| R02 | `folder-tree` / `folders://folder-tree/{folderId}/{workspaceId}/{taskId}` | defer | exclude | Q30 | Resource requires task context and omits freshness/cursor/limit; preserve default metadata-only tree through a future Query. Protected context read; G1,G2,G4,G5. | `src/Hexalith.Folders.Mcp/Resources/FolderTreeResource.cs:29` | [A1](#a1-session-approval-2026-10-16) |

## Frozen CLI leaf rows

The actual command tree has **42** leaves: provider 4, folder 11, workspace 8,
file 3, commit 5, context 7 and audit 4. Each row inherits its linked tool's
domain/security prerequisites and the explicitly listed adapter variants.
The seven diagnostics tools have no CLI counterpart. The parity fixture's
placeholder adapter expectations do not manufacture diagnostic CLI leaves.

| ID | Frozen CLI leaf | Linked MCP tool | Disposition | Coverage | Future target(s) | Rationale / security class | Source | Approval reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L01 | `provider configure-binding` | `configure-provider-binding` | defer | exclude | C05 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Provider/security configuration write. | `src/Hexalith.Folders.Cli/Commands/Provider/ProviderCommand.cs:24` | [A1](#a1-session-approval-2026-10-16) |
| L02 | `provider get-binding` | `get-provider-binding` | defer | exclude | Q13 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Provider/ProviderCommand.cs:40` | [A1](#a1-session-approval-2026-10-16) |
| L03 | `provider validate-readiness` | `validate-provider-readiness` | defer | exclude | Q35 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Provider/ProviderCommand.cs:55` | [A1](#a1-session-approval-2026-10-16) |
| L04 | `provider support-evidence` | `get-provider-support-evidence` | defer | exclude | Q16 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Provider/ProviderCommand.cs:71` | [A1](#a1-session-approval-2026-10-16) |
| L05 | `folder create` | `create-folder` | defer | exclude | C06 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Lifecycle write. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:24` | [A1](#a1-session-approval-2026-10-16) |
| L06 | `folder create-repo-backed` | `create-repository-backed-folder` | defer | exclude | C07 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Repository lifecycle write. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:38` | [A1](#a1-session-approval-2026-10-16) |
| L07 | `folder bind-repo` | `bind-repository` | defer | exclude | C02 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Repository configuration write. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:53` | [A1](#a1-session-approval-2026-10-16) |
| L08 | `folder get-repo-binding` | `get-repository-binding` | defer | exclude | Q19 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:70` | [A1](#a1-session-approval-2026-10-16) |
| L09 | `folder status` | `get-folder-lifecycle-status` | defer | exclude | Q09 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:86` | [A1](#a1-session-approval-2026-10-16) |
| L10 | `folder archive` | `archive-folder` | defer | exclude | C01 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Destructive lifecycle write. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:101` | [A1](#a1-session-approval-2026-10-16) |
| L11 | `folder effective-permissions` | `get-effective-permissions` | defer | exclude | Q05 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:117` | [A1](#a1-session-approval-2026-10-16) |
| L12 | `folder acl list` | `list-folder-acl-entries` | defer | exclude | Q29 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:146` | [A1](#a1-session-approval-2026-10-16) |
| L13 | `folder acl update` | `update-folder-acl-entry` | defer | exclude | C08, C13 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09,V08. Authorization administration write. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:165` | [A1](#a1-session-approval-2026-10-16) |
| L14 | `folder branch-policy set` | `configure-branch-ref-policy` | defer | exclude | C04 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Security policy write. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:189` | [A1](#a1-session-approval-2026-10-16) |
| L15 | `folder branch-policy get` | `get-branch-ref-policy` | defer | exclude | Q02 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Folder/FolderCommand.cs:205` | [A1](#a1-session-approval-2026-10-16) |
| L16 | `workspace prepare` | `prepare-workspace` | defer | exclude | C11 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Workspace lifecycle write. | `src/Hexalith.Folders.Cli/Commands/Workspace/WorkspaceCommand.cs:23` | [A1](#a1-session-approval-2026-10-16) |
| L17 | `workspace lock` | `lock-workspace` | defer | exclude | C09 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Concurrency-control write. | `src/Hexalith.Folders.Cli/Commands/Workspace/WorkspaceCommand.cs:38` | [A1](#a1-session-approval-2026-10-16) |
| L18 | `workspace release` | `release-workspace-lock` | defer | exclude | C12 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Concurrency-control write. | `src/Hexalith.Folders.Cli/Commands/Workspace/WorkspaceCommand.cs:53` | [A1](#a1-session-approval-2026-10-16) |
| L19 | `workspace get-lock` | `get-workspace-lock` | defer | exclude | Q23 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Workspace/WorkspaceCommand.cs:68` | [A1](#a1-session-approval-2026-10-16) |
| L20 | `workspace status` | `get-workspace-status` | defer | exclude | Q25 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Workspace/WorkspaceCommand.cs:78` | [A1](#a1-session-approval-2026-10-16) |
| L21 | `workspace retry-eligibility` | `get-workspace-retry-eligibility` | defer | exclude | Q24 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Workspace/WorkspaceCommand.cs:88` | [A1](#a1-session-approval-2026-10-16) |
| L22 | `workspace transition-evidence` | `get-workspace-transition-evidence` | defer | exclude | Q26 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Workspace/WorkspaceCommand.cs:98` | [A1](#a1-session-approval-2026-10-16) |
| L23 | `workspace cleanup-status` | `get-workspace-cleanup-status` | defer | exclude | Q22 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Workspace/WorkspaceCommand.cs:108` | [A1](#a1-session-approval-2026-10-16) |
| L24 | `file add` | `add-file` | defer | exclude | C10 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09,V04,V05. Content-bearing write. | `src/Hexalith.Folders.Cli/Commands/File/FileCommand.cs:27` | [A1](#a1-session-approval-2026-10-16) |
| L25 | `file change` | `change-file` | defer | exclude | C10 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09,V04,V05. Content-bearing write. | `src/Hexalith.Folders.Cli/Commands/File/FileCommand.cs:28` | [A1](#a1-session-approval-2026-10-16) |
| L26 | `file remove` | `remove-file` | defer | exclude | C10 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. Destructive file write. | `src/Hexalith.Folders.Cli/Commands/File/FileCommand.cs:88` | [A1](#a1-session-approval-2026-10-16) |
| L27 | `commit create` | `commit-workspace` | defer | exclude | C03 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V03,V07,V09. External repository write. | `src/Hexalith.Folders.Cli/Commands/Commit/CommitCommand.cs:29` | [A1](#a1-session-approval-2026-10-16) |
| L28 | `commit evidence` | `get-commit-evidence` | defer | exclude | Q03 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Commit/CommitCommand.cs:44` | [A1](#a1-session-approval-2026-10-16) |
| L29 | `commit provider-outcome` | `get-provider-outcome` | defer | exclude | Q14 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Commit/CommitCommand.cs:53` | [A1](#a1-session-approval-2026-10-16) |
| L30 | `commit reconciliation-status` | `get-reconciliation-status` | defer | exclude | Q18 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Commit/CommitCommand.cs:66` | [A1](#a1-session-approval-2026-10-16) |
| L31 | `commit task-status` | `get-task-status` | defer | exclude | Q21 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Commit/CommitCommand.cs:86` | [A1](#a1-session-approval-2026-10-16) |
| L32 | `context list` | `list-folder-files` | defer | exclude | Q30 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Context/ContextCommand.cs:30` | [A1](#a1-session-approval-2026-10-16) |
| L33 | `context metadata` | `get-folder-file-metadata` | defer | exclude | Q07 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Context/ContextCommand.cs:47` | [A1](#a1-session-approval-2026-10-16) |
| L34 | `context search` | `search-folder-files` | defer | exclude | Q33 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Context/ContextCommand.cs:63` | [A1](#a1-session-approval-2026-10-16) |
| L35 | `context glob` | `glob-folder-files` | defer | exclude | Q27 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Context/ContextCommand.cs:79` | [A1](#a1-session-approval-2026-10-16) |
| L36 | `context read-range` | `read-file-range` | defer | exclude | Q32 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Context/ContextCommand.cs:95` | [A1](#a1-session-approval-2026-10-16) |
| L37 | `context index-search` | `search-folder-indexed-files` | defer | exclude | Q34 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Context/ContextCommand.cs:111` | [A1](#a1-session-approval-2026-10-16) |
| L38 | `context indexing-status` | `get-folder-indexing-status` | defer | exclude | Q08 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Context/ContextCommand.cs:129` | [A1](#a1-session-approval-2026-10-16) |
| L39 | `audit list` | `list-audit-trail` | defer | exclude | Q28 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Audit/AuditCommand.cs:22` | [A1](#a1-session-approval-2026-10-16) |
| L40 | `audit get` | `get-audit-record` | defer | exclude | Q01 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Audit/AuditCommand.cs:34` | [A1](#a1-session-approval-2026-10-16) |
| L41 | `audit timeline list` | `list-operation-timeline` | defer | exclude | Q31 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Audit/AuditCommand.cs:56` | [A1](#a1-session-approval-2026-10-16) |
| L42 | `audit timeline get` | `get-operation-timeline-entry` | defer | exclude | Q11 | Retain legacy leaf until Gateway equivalent and adapter differences pass; V01–V03,V06,V09. Protected metadata read. | `src/Hexalith.Folders.Cli/Commands/Audit/AuditCommand.cs:68` | [A1](#a1-session-approval-2026-10-16) |

## Behavior variants and compatibility decisions

All variants remain deferred/excluded with their linked surface. An exclusion
records the absent generic experience; it does not silently withdraw legacy
behavior. The eventual replacement design must preserve equivalent behavior or
obtain explicit acceptance of each loss/change before retirement.

| ID | Legacy behavior / affected rows | Disposition / coverage | Future equivalent or unresolved gap / lost behavior | Security class | Approval reference |
| --- | --- | --- | --- | --- | --- |
| V01 | All 35 reads; all 28 CLI queries accept freshness | defer / exclude | Exactly one explicit value per operation, as tabulated in Q01–Q35; unsupported choices are rejected. G4 must preserve each omission/default and rejection rule. Generic v1 has no freshness argument; do not silently drop the request. | Read consistency / authorization context | [A1](#a1-session-approval-2026-10-16) |
| V02 | Provider support evidence, context list, ACL list, audit list and timeline list paging; filters on ACL and the two audit lists | defer / exclude | Cursor/limit/filter must become supported typed query inputs or an approved generic envelope mapping. Define envelope PageSize/Offset/Cursor precedence and legacy limit translation upstream; reject conflicts. Prove filters before paging, totals and continuations. | Protected metadata read | [A1](#a1-session-approval-2026-10-16) |
| V03 | Task/workspace scope on all mutations and nine task-required reads; effective-permissions optional task context | defer / exclude | Nine reads: six context reads except indexing status, plus workspace retry eligibility/transition evidence/cleanup status. Preserve explicit task and workspace identity in approved contracts/handlers. Indexing status uses folder only. get-task-status task ID identifies a route resource and additionally needs folder authorization, not a fabricated task header. Queries have no generic extension bag today. | Tenant/task/workspace isolation | [A1](#a1-session-approval-2026-10-16) |
| V04 | add/change file content input | defer / exclude | MCP accepts base64; CLI reads --file path or stdin. Upload helper selects Add/Change inline transport, NFC path metadata, optional original media type and default metadata_only policy class. It derives requestSchemaVersion `v2`, decoded byteLength, a `hashref_` reference containing the SHA-256 digest as 64 lowercase hex characters, and the `PutFileInline` transport discriminator (`src/Hexalith.Folders.Client/Convenience/FileUpload.cs:30`, `:89`, `:191`). Future Contracts/handlers must explicitly preserve or validate that derived evidence and content policy without a Folders client adapter. Generic JSON calls do not recreate local-file convenience. | Content-bearing write | [A1](#a1-session-approval-2026-10-16) |
| V05 | Inline/streamed upload limits | defer / exclude | The decoded inline boundary is inclusive at 262144 bytes; 262145–1048576 bytes require out-of-band staging and `PutFileStream`, with 1048576 the inclusive absolute per-file maximum (`src/Hexalith.Folders.Client/Convenience/FileUpload.cs:25`, `:28`, `:58`, `:63`, `:127`). In-memory inline input in that intermediate range yields retryable `input_limit_exceeded` / `d9_inline_limit_exceeded` and streaming-required guidance; above 1048576 bytes it yields nonretryable `input_limit_exceeded` / `file_content_limit_exceeded`, never advice to bypass the maximum (`src/Hexalith.Folders.Mcp/Errors/McpFailure.cs:111`, `:126`; `src/Hexalith.Folders.Cli/Commands/CommandPipeline.cs:188`, `:205`). Streamed staging remains SDK/REST-only, not another tool/leaf; an approved future generic contract/transport and live content store are prerequisites. | Content transport / resource limits | [A1](#a1-session-approval-2026-10-16) |
| V06 | Metadata-only outputs, redaction and safe errors on every surface, including authorized read-file-range | defer / exclude | Both adapters recursively suppress contentBytes, inlineContent and streamDescriptor. Gateway responses must preserve this before generic heads serialize raw results; retain authorization-before-read, diagnostic visibility and safe errors without leaking content, paths or secrets in result/error/diagnostic channels. Future content reads require separate approval. | Privacy/content protection | [A1](#a1-session-approval-2026-10-16) |
| V07 | Correlation/message IDs and caller idempotency sourcing | defer / exclude | Legacy mutations require task/key; CLI additionally offers --allow-auto-key, whereas McpCli never generates a key. That convenience is absent generically and needs explicit future loss/change acceptance. Separately from the lowercase-envelope mismatch in G3, legacy callers may supply SDK-derived `sha256:<hex>` keys (64 lowercase hex characters; `src/Hexalith.Folders.Client/Idempotency/HexalithIdempotencyHasher.cs:27`), while every supplied McpCli key must be a canonical uppercase ULID (McpCli-local `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:159`). Folders/EventStore maintainers must approve an upstream key-format/replay migration preserving caller ownership, equivalent-input replay, changed-input conflict, expiry and task association. No silent hash-to-ULID conversion, generated replacement key or weakening of generic key rules is authorized. Opaque payload IDs remain String candidates, never silently converted to ULIDs. | Replay safety / identity integrity | [A1](#a1-session-approval-2026-10-16) |
| V08 | update-folder-acl-entry body.effect grant/revoke | defer / exclude | Name grant/revoke separately (C08/C13 in the normalized table) and retain ACL entry/subject/resource/action/condition validation and authorization. No equivalence to permission-row erasure. | Authorization administration | [A1](#a1-session-approval-2026-10-16) |
| V09 | Adapter inputs, credentials, results and output channels | defer / exclude | Legacy CLI supports inline/@file/stdin typed JSON, REST setup, human/json output and stderr errors. CLI token precedence is `HEXALITH_TOKEN` environment > per-tenant `~/.hexalith/credentials.json` > --token; `HEXALITH_TENANT` selects the section, falling back to `default`, and selects credentials rather than granting tenant authority (`src/Hexalith.Folders.Cli/Credentials/CredentialResolver.cs:34`; `src/Hexalith.Folders.Cli/Credentials/CredentialStore.cs:14`). MCP precedence is `HEXALITH_TOKEN` environment > inline `folders:auth:token` > token file; `HEXALITH_FOLDERS_AUTH_TOKENFILE` overrides `folders:auth:tokenFile` for that final path (`src/Hexalith.Folders.Mcp/Credentials/McpCredentialResolver.cs:50`). Legacy CLI distinguishes usage 64, credential 65, access 66, lock 67, idempotency conflict 68, validation 69, provider 70, unknown outcome 71, reconciliation 72, authority unavailable 73, lifecycle 74, redacted 75, expired key 76, concurrency 77 and internal/unmapped 1 (`src/Hexalith.Folders.Cli/FoldersExitCodes.cs:20`; `src/Hexalith.Folders.Cli/Errors/ErrorProjection.cs:23`). McpCli operational errors use exit 2 and stdout JSON (McpCli-local `src/Hexalith.McpCli/Cli/CliOutput.cs:123`); these legacy automation distinctions and credential-selection behavior need an explicitly accepted setup/result migration and no-secret proof. A1 approves deferral only, not those future losses or credential changes; global options create no new leaves. | Operator credential / output safety | [A1](#a1-session-approval-2026-10-16) |
| V10 | Dry-run or other unimplemented REST-only capability | defer / exclude | No operation dry-run parameter/implementation was found in pinned src or the parity fixture. Do not claim existing dry-run parity. Any requested simulation, external staging or non-Gateway effect needs separately approved semantics and a generic contract/transport decision. | Future capability / effect control | [A1](#a1-session-approval-2026-10-16) |

## Adjacent nonlegacy exclusions

These are not extra tools, resources or CLI leaves and do not increase the
93-surface count. Separate prior decisions do not authorize McpCli exposure.

| ID | Capability | Disposition / coverage | Rationale / prerequisite and owning maintainer role | Security class | Approval reference |
| --- | --- | --- | --- | --- | --- |
| N01 | Permission maintenance inspect/conditional erase/read-back | defer / exclude | Worker maintenance endpoint outside the agent surface; permission/platform maintainer must approve token authority, ETag concurrency and destructive effects under a generic operator contract before exposure. | Destructive operator maintenance | [A1](#a1-session-approval-2026-10-16) |
| N02 | Key rotation / deployment credential administration | defer / exclude | Deployment/platform configuration, no legacy MCP/CLI rotation operation found. Platform/security maintainer owns any future generic contract and credential/destruction policy; no tool invented. | Security administration | [A1](#a1-session-approval-2026-10-16) |
| N03 | Organization ACL baseline/grant/revoke commands | defer / exclude | Wire recognizers exist but are absent from the 49 tools and 42 leaves. Folders authorization maintainer owns future agent scope and layered authority proof; folder ACL rows do not imply organization-wide exposure. | Organization authorization administration | [A1](#a1-session-approval-2026-10-16) |
| N04 | Future v2-only RenewWorkspaceLock | defer / exclude | October 7 decision schedules upstream work after Story 1.17 and requires regenerated inventory. It does not add a current legacy leaf or approve this FR-21 scope. Folders workspace maintainer owns future contract, lease semantics and revised inventory. | Concurrency-control write | [A1](#a1-session-approval-2026-10-16) |

## Readiness and retention gates

Approval of a deferred inventory can complete Story 4.2's scope decision. It
cannot satisfy Folders coverage or enrollment: no included row exists. A later
replacement revision must name eligible canonical names and exact decorated
CLR types, pass AD-15's exact package/closure gate and AD-21's independent
Catalog set/type match, and provide one approved execution vector per included
operation with loopback request/result parity and live persisted semantic proof.

All applicable G/V requirements remain blocking, including configured live
executors, authenticated tenant/task authorization, metadata-only output,
freshness/filter/paging, canonical identifier compatibility and caller-key
admission. No feature is substituted into v1 for a delayed module. Folders
stays post-v1. Keep both legacy MCP server and Frozen CLI until approved
replacement or explicit withdrawal plus authorization, behavior and release
evidence exists. Resource replacement or deferred exclusion never authorizes
a resource endpoint in generic McpCli v1.

## Source evidence and draft reconciliation

- `src/Hexalith.Folders.Mcp/Program.cs:64`: stdio tool/resource assembly registration;
  exact tool attributes are anchored in each M row.
- `src/Hexalith.Folders.Cli/CliApplication.cs:45` and
  `Commands/{Provider,Folder,Workspace,File,Commit,Context,Audit}/*Command.cs`
  under that project: the actual 42-leaf tree. `tests/fixtures/parity-contract.yaml`
  has 49 operation IDs, but diagnostics adapter expectations are explicitly
  `non_policy_placeholder: true`, not proof of implemented CLI commands.
- `src/Hexalith.Folders.Client/Serialization/OperationFreshness.cs:25` and
  `Generated/HexalithFoldersIdempotencyHelpers.g.cs:196` under that project:
  exact per-read freshness classes; CLI `Commands/CommandOptions.cs:45`/`:81`
  and provider/context/folder/audit command files pin input options and paging.
- `src/Hexalith.Folders.Mcp/Tools/FileTools.cs:24`/`:43`/`:90`,
  CLI `Commands/File/FileCommand.cs:40`/`:103`, and Client
  `Convenience/FoldersFileUploadExtensions.cs:37`/`:103`: inline input and
  separate SDK-only streamed transport. Public OpenAPI header at
  `src/Hexalith.Folders.Contracts/openapi/hexalith.folders.v1.yaml:79`
  additionally documents per-file/batch bounds for upstream validation.
- `src/Hexalith.Folders.Mcp/Infrastructure/MetadataOnlyJson.cs:29` and
  `src/Hexalith.Folders.Cli/Infrastructure/MetadataOnlyJson.cs:22`:
  recursive content suppression, including authorized range reads.
- `src/Hexalith.Folders.Server/FoldersDomainServiceRequestHandler.cs:27`/`:245`
  and `src/Hexalith.Folders.Server/FolderDomainProcessor.cs`: lowercase canonical envelope validation and required
  taskId. `FoldersDomainServiceEndpoints.cs:1601`/`:3548` under Server sends a
  separate caller key and lowercase generated message ID; processor CreateFolder
  and Archive conversion use envelope.MessageId as domain idempotency identity.
- `src/Hexalith.Folders.Server/FoldersServerModule.cs:30`–`:62`,
  aggregate `MutateWorkspaceFile.cs:26`/`CommitWorkspace.cs:22`, and
  `FoldersDomainServiceEndpoints.cs:1905`/`:1934`: domain/wires and ACL split.
- `src/Hexalith.Folders.Server/FoldersDomainServiceEndpoints.cs:105`:
  current `/project` dispatches event projections (200/404 or 422), correcting
  the September draft's obsolete 501 claim. No IDomainQueryHandler or McpCli
  operation decoration was found in current src. Contracts csproj has no
  package references; `FoldersContractMetadata.cs:6` retains scaffold metadata.
- `src/Hexalith.Folders.Server/FoldersServerServiceCollectionExtensions.cs:90`:
  default unavailable file/path/delete/commit/context implementations.
- `src/Hexalith.Folders.Workers/FolderPermissionMaintenanceEndpoints.cs:18`;
  `docs/operations/container-images-and-dapr-app-ids.md:85`;
  Server `Authorization/FolderCommandActionTokenMapper.cs:12`: N01–N03.
- `_bmad-output/implementation-artifacts/spec-5-8-cli-workspace-preparation-and-lock-lifecycle.md:43`
  proposes workspace contracts but remains draft with approval open;
  `story-4-19-prerequisites-decision-2026-10-07.md:16` in the same folder
  records the separate, conditional future renewal decision (N04).
- McpCli-local `src/Hexalith.McpCli.Core/Execution/RunQueryArguments.cs:14`
  shows paging without query extensions/freshness; `ExtensionValidator.cs:37`
  requires configured allowed command extensions, so taskId must be explicitly
  allowlisted wherever an approved command path uses it.

Static source and row checks are recorded in
[Story 4.2 verification](evidence/story-4-2/verification.md). They prove inventory
completeness against this source pin, not packaged Catalog or Gateway behavior.

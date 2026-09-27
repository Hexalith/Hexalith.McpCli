# Folders agent operation migration inventory (draft v0)

**Source snapshot:** `Hexalith.Folders` commit `18cf524bc4e6943b5141afb9a79b976abce5fb2b` (2026-09-27),
`tests/fixtures/parity-contract.yaml` and `src/Hexalith.Folders.Mcp/Tools/`.
The parity fixture and MCP tool declarations contain the same 49 operation names.
This draft records the legacy surface before the Folders maintainer chooses the
agent-facing subset. It is not the approved FR-21 inventory and must not be used
to enroll `Hexalith.Folders.Contracts`.

**Decision needed:** For each row, record `include` with the decorated Contracts
type and gateway vector, or `exclude` with a rationale. Record the owning Folders
maintainer's approval reference and inventory version. An included operation
must pass the AD-21 catalog match and AD-16 loopback and live gateway gates.

## Commands (14)

| Legacy MCP tool | Current EventStore `/process` wire command candidate | Migration decision |
| --- | --- | --- |
| `add-file` | `MutateFiles` | Pending |
| `archive-folder` | `ArchiveFolder` | Pending |
| `bind-repository` | `BindRepository` | Pending |
| `change-file` | `MutateFiles` | Pending |
| `commit-workspace` | `CommitWorkspace` | Pending |
| `configure-branch-ref-policy` | `ConfigureBranchRefPolicy` | Pending |
| `configure-provider-binding` | `ConfigureProviderBinding` | Pending |
| `create-folder` | `CreateFolder` | Pending |
| `create-repository-backed-folder` | `CreateRepositoryBackedFolder` | Pending |
| `lock-workspace` | `LockWorkspace` | Pending |
| `prepare-workspace` | `PrepareWorkspace` | Pending |
| `release-workspace-lock` | `ReleaseWorkspaceLock` | Pending |
| `remove-file` | `MutateFiles` | Pending |
| `update-folder-acl-entry` | `GrantFolderAccess` or `RevokeFolderAccess`; split required | Pending |

The command names in the table abbreviate the wire prefix
`Hexalith.Folders.Commands.`. The candidates come from `FoldersServerModule`
and `FolderCommandActionTokenMapper`, not from Contracts DTOs. The current Contracts
package has no command types. `/process` requires a canonical `taskId` envelope
extension, a caller idempotency key for the REST/MCP mutating surface, and layered
authorization. Preserve the REST command's request validation, policy checks,
dry-run behavior, and idempotency admission when adding a gateway path. Current
default registrations include unavailable file content and commit executors, so
wire-command recognition alone is insufficient evidence of live execution.

## Queries (35)

| Legacy MCP tool | Legacy family | Migration decision |
| --- | --- | --- |
| `get-audit-record` | audit | Pending |
| `get-branch-ref-policy` | query status | Pending |
| `get-commit-evidence` | query status | Pending |
| `get-dirty-state-diagnostics` | operations console projection | Pending |
| `get-effective-permissions` | query status | Pending |
| `get-failed-operation-diagnostics` | operations console projection | Pending |
| `get-folder-file-metadata` | context query | Pending |
| `get-folder-indexing-status` | context query | Pending |
| `get-folder-lifecycle-status` | query status | Pending |
| `get-lock-diagnostics` | operations console projection | Pending |
| `get-operation-timeline-entry` | audit | Pending |
| `get-projection-freshness` | operations console projection | Pending |
| `get-provider-binding` | query status | Pending |
| `get-provider-outcome` | query status | Pending |
| `get-provider-status-diagnostics` | operations console projection | Pending |
| `get-provider-support-evidence` | query status | Pending |
| `get-readiness-diagnostics` | operations console projection | Pending |
| `get-reconciliation-status` | query status | Pending |
| `get-repository-binding` | query status | Pending |
| `get-sync-status-diagnostics` | operations console projection | Pending |
| `get-task-status` | query status | Pending |
| `get-workspace-cleanup-status` | query status | Pending |
| `get-workspace-lock` | query status | Pending |
| `get-workspace-retry-eligibility` | query status | Pending |
| `get-workspace-status` | query status | Pending |
| `get-workspace-transition-evidence` | query status | Pending |
| `glob-folder-files` | context query | Pending |
| `list-audit-trail` | audit | Pending |
| `list-folder-acl-entries` | query status | Pending |
| `list-folder-files` | context query | Pending |
| `list-operation-timeline` | audit | Pending |
| `read-file-range` | context query | Pending |
| `search-folder-files` | context query | Pending |
| `search-folder-indexed-files` | context query | Pending |
| `validate-provider-readiness` | query status | Pending |

These handlers currently serve REST endpoints. The Folders server has no
registered `IDomainQueryHandler` for the EventStore gateway, and its `/project`
endpoint returns 501. Included reads need Contracts query DTOs and live gateway
query handlers, with the existing authorization, redaction, freshness, and path
policy applied before data access. Search, filter, and freshness variants need
explicit inclusion or documented exclusion because McpCli v1 does not offer
generic arguments for them.

## Legacy MCP resources (2)

| Resource | Same underlying operation | Migration decision |
| --- | --- | --- |
| `audit-trail` | `list-audit-trail` | Pending: include as the query operation or approve exclusion of the separate resource surface |
| `folder-tree` | `list-folder-files` | Pending: include as the query operation or approve exclusion of the separate resource surface |

These resources call the same REST client operations as the named tools. McpCli
v1 exposes generic tools only, so the FR-21 inventory must explicitly account
for their semantics without adding a resource endpoint. The Folders CLI leaf
verbs are mapped below and need their own approved decisions. The generic
McpCli runtime adds no Folders-specific adapter.

## Frozen CLI leaf verbs (42)

The current `Hexalith.Folders.Cli` command tree has 42 leaf verbs. Each calls
the same generated client operation as the linked legacy MCP tool, including
`file add` and `file change`, which both use the file-upload helper with a
different operation kind. The linked tool's migration decision also needs an
explicit CLI decision and rationale in the approved inventory; this table does
not approve either surface.

| Frozen CLI leaf verb | Linked legacy MCP tool | Decision |
| --- | --- | --- |
| `provider configure-binding` | `configure-provider-binding` | Pending |
| `provider get-binding` | `get-provider-binding` | Pending |
| `provider validate-readiness` | `validate-provider-readiness` | Pending |
| `provider support-evidence` | `get-provider-support-evidence` | Pending |
| `folder create` | `create-folder` | Pending |
| `folder create-repo-backed` | `create-repository-backed-folder` | Pending |
| `folder bind-repo` | `bind-repository` | Pending |
| `folder get-repo-binding` | `get-repository-binding` | Pending |
| `folder status` | `get-folder-lifecycle-status` | Pending |
| `folder archive` | `archive-folder` | Pending |
| `folder effective-permissions` | `get-effective-permissions` | Pending |
| `folder acl list` | `list-folder-acl-entries` | Pending |
| `folder acl update` | `update-folder-acl-entry` | Pending |
| `folder branch-policy set` | `configure-branch-ref-policy` | Pending |
| `folder branch-policy get` | `get-branch-ref-policy` | Pending |
| `workspace prepare` | `prepare-workspace` | Pending |
| `workspace lock` | `lock-workspace` | Pending |
| `workspace release` | `release-workspace-lock` | Pending |
| `workspace get-lock` | `get-workspace-lock` | Pending |
| `workspace status` | `get-workspace-status` | Pending |
| `workspace retry-eligibility` | `get-workspace-retry-eligibility` | Pending |
| `workspace transition-evidence` | `get-workspace-transition-evidence` | Pending |
| `workspace cleanup-status` | `get-workspace-cleanup-status` | Pending |
| `file add` | `add-file` | Pending |
| `file change` | `change-file` | Pending |
| `file remove` | `remove-file` | Pending |
| `commit create` | `commit-workspace` | Pending |
| `commit evidence` | `get-commit-evidence` | Pending |
| `commit provider-outcome` | `get-provider-outcome` | Pending |
| `commit reconciliation-status` | `get-reconciliation-status` | Pending |
| `commit task-status` | `get-task-status` | Pending |
| `context list` | `list-folder-files` | Pending |
| `context metadata` | `get-folder-file-metadata` | Pending |
| `context search` | `search-folder-files` | Pending |
| `context glob` | `glob-folder-files` | Pending |
| `context read-range` | `read-file-range` | Pending |
| `context index-search` | `search-folder-indexed-files` | Pending |
| `context indexing-status` | `get-folder-indexing-status` | Pending |
| `audit list` | `list-audit-trail` | Pending |
| `audit get` | `get-audit-record` | Pending |
| `audit timeline list` | `list-operation-timeline` | Pending |
| `audit timeline get` | `get-operation-timeline-entry` | Pending |

The seven MCP-only tools are `get-dirty-state-diagnostics`,
`get-failed-operation-diagnostics`, `get-lock-diagnostics`,
`get-projection-freshness`, `get-provider-status-diagnostics`,
`get-readiness-diagnostics`, and `get-sync-status-diagnostics`. Several CLI
queries expose freshness or filter options that generic `run_query` v1 does
not provide. The approved inventory must record those variants as exclusions
or define a supported Contracts payload and Gateway handler for them.

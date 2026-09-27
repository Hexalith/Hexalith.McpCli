# Projects agent operation migration inventory (draft v0)

**Source snapshot:** `Hexalith.Projects` commit
`2e0c0b55a732a474f3a70cbfcda279da392d17b5` (2026-09-27),
`src/Hexalith.Projects.Mcp/ProjectsMcpDescriptors.cs` and
`src/Hexalith.Projects.Cli/ProjectsCliParser.cs`. The sibling repository has
unrelated working-tree changes; this inventory reads the current descriptor and
parser source and makes no edits there.

The FrontComposer-hosted Projects plug-in declares 11 read-only MCP resources
and five maintenance tools. The Frozen Projects CLI accepts 18 command
spellings, including three read aliases. The tables record the full legacy
agent surface before the Projects maintainer chooses the Gateway-ready subset.
They are not an approved FR-21 inventory and cannot be used to enroll
`Hexalith.Projects.Contracts`.

**Approval needed:** Give every row an `include` decision with canonical
Operation Name, decorated Contracts type, validated Gateway route, and vector,
or an `exclude` decision with rationale. Record the inventory version and
Projects maintainer approval reference. Any included Operation must pass the
AD-15 dependency closure and AD-16 loopback and live semantic gates.

## Legacy MCP resources (11)

| Resource name | Current source or behavior | Migration decision |
| --- | --- | --- |
| `projects.inventory` | Visible project list through REST client | Pending |
| `projects.detail` | Project detail through REST client | Pending |
| `projects.operatorDiagnostic` | Bounded operator diagnostic through REST client | Pending |
| `projects.referenceHealth` | Reference rows derived from operator diagnostic | Pending |
| `projects.resolutionTrace` | Static trace metadata; CLI `trace` performs a separate REST resolution | Pending |
| `projects.auditTimeline` | Audit rows derived from operator diagnostic | Pending |
| `projects.safeDiagnosticExport` | Redacted summary derived from operator diagnostic | Pending |
| `projects.warningQueue` | Composite visible inventory and bounded diagnostics | Pending |
| `projects.warningScanSummary` | Composite warning counts | Pending |
| `projects.operationalDashboard` | Composite inventory and warning counts | Pending |
| `projects.maintenanceAction` | Static maintenance preview metadata | Pending |

These are FrontComposer MCP resources. McpCli v1 exposes generic tools only,
so an included read needs a Contracts query DTO and an EventStore
`IDomainQueryHandler`; an excluded read needs an approved rationale. The three
currently registered Projects Gateway query handlers serve different context
queries and do not establish parity for these 11 resources. Composite reads,
redaction, tenant scoping, and freshness need handler-level semantics if
included. `projects.resolutionTrace` and CLI `trace` are distinct behaviors.

## Legacy MCP maintenance tools (5)

| Tool name | Current REST path / possible gateway contract | Migration decision |
| --- | --- | --- |
| `projects.archive` | `ArchiveProject` | Pending |
| `projects.restore` | `RestoreProject` | Pending |
| `projects.relink` | `SetProjectFolder`, `LinkFileReference`, or `LinkMemory`, selected by reference kind | Pending: split or approved exclusion |
| `projects.unlink` | REST `UnlinkProjectConversation`, `UnlinkFileReference`, or `UnlinkMemory`, selected by reference kind | Pending: split or approved exclusion |
| `projects.reevaluate` | REST `RefreshProjectContext`; currently a read-style refresh call, not an aggregate Command | Pending: query mapping or approved exclusion |

The current plug-in calls the generated REST client. Its command service
derives task and correlation values, checks confirmation and dry-run evidence,
and applies the `projects:maintain` policy. Direct Gateway submission would
bypass the REST submitter and its tenant and authorization guards. Included
commands therefore require equivalent authority checks at the Gateway/module
boundary and live handler evidence. Caller-supplied idempotency keys stay in
the envelope. The existing public Contracts command records and strict
Gateway payloads do not yet match these wrapper requests.

## Frozen CLI command spellings (18)

| CLI spelling after `projects` | Related MCP surface | Migration decision |
| --- | --- | --- |
| `list` | `projects.inventory` | Pending |
| `describe` | `projects.detail` | Pending |
| `inspect` | `projects.detail` alias | Pending |
| `trace` | REST resolution; `projects.resolutionTrace` is metadata only | Pending: distinct semantics |
| `trace-resolution` | Alias of CLI `trace` | Pending |
| `validate` | `projects.referenceHealth` | Pending |
| `validate-references` | Alias of CLI `validate` | Pending |
| `audit` | `projects.auditTimeline` | Pending |
| `warnings` | `projects.warningQueue` and `projects.warningScanSummary` | Pending |
| `dashboard` | `projects.operationalDashboard` | Pending |
| `diagnostic export` | `projects.safeDiagnosticExport` | Pending |
| `dry-run` | Local preview; `projects.maintenanceAction` is static metadata | Pending: distinct semantics |
| `preview` | Local preview; `projects.maintenanceAction` is static metadata | Pending: distinct semantics |
| `archive` | `projects.archive` | Pending |
| `restore` | `projects.restore` | Pending |
| `relink` | `projects.relink` | Pending |
| `unlink` | `projects.unlink` | Pending |
| `reevaluate` | `projects.reevaluate` | Pending |

The CLI calls the generated REST client for reads and mutations, except its
local `dry-run` and `preview` paths. The approved inventory must account for
those local behaviors, aliases, REST-only resolution, audit confirmation, and
CLI option variants. McpCli adds no Projects-specific adapter.

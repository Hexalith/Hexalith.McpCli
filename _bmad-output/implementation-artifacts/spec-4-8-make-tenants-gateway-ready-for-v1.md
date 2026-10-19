---
title: '4.8 Make Tenants gateway-ready for v1'
type: 'feature'
created: '2026-10-19'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `Hexalith.Tenants.Contracts` has no McpCli decoration. Its query
handlers read paging and audit filters only from camelCase payload keys, while
McpCli sends CLR-named payloads and envelope paging, so McpCli filters and paging
are silently ignored and no paging metadata returns.

**Approach:** In the owning Tenants repo, decorate the v1 Commands and Queries with
Decoration Package 1.0.0, migrate paged handlers to `QueryEnvelope.Paging`, honor
CLR-named audit filters, and author one McpCli v1 vector per exposed operation,
proven through a scratch McpCli host.

## Boundaries & Constraints

**Always:** Marker `tenants`, `IdentifierKind.String`, `FixedTenant = "system"`;
NFR-8 descriptions and a schema-valid `Example` everywhere. Interface routing
only: no `Domain`, `WireType`, `ProjectionType`, Command `AggregateIdProperty` or
`TenantProperty`. Per-tenant Queries use `AggregateIdProperty = nameof(TenantId)`;
list Queries use constant `index`. Present envelope paging alone governs: existing
policy clamps, codec and scopes; offset rejected; every paged success returns
`QueryResponseMetadata.Paging` (`PageSize`, `NextCursor`, `HasMore`). Otherwise
only the REST controllers' camelCase `cursor`/`pageSize` apply. Audit honors CLR
`From`, `To`, `Category` with the camelCase validation. Vectors name the exact
package version.

**Never:** Decorate `BootstrapGlobalAdmin`, `SetGlobalAdministrator`,
`RemoveGlobalAdministrator`, `GetGlobalAdministratorsQuery` or
`ResolveTenantOwnerAuthority`. Widen authorization, break REST/UI paging, change
wire types, domains or payload shapes, edit `references/` or McpCli source, change
the vector contract, or push, open PRs, publish or enroll.

**Decisions (2026-10-19, requesting user):** Split: release, Builds bump and
enrollment are deferred. Exclude the global-administrator Query. The user, as
Tenants maintainer, confirms `index` and approves vectors; a fresh-context
reviewer given only the Catalog dump performs the NFR-8 review; both go to story
evidence. Vectors stay loopback-valid with scripted cursors; Tenants tests prove
filtering and continuation; live proof is Story 4.13's, so Gateway-ready
acceptance stays blocked.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Envelope page | `Paging{PageSize:2}`, 3 rows | 2 rows; `PageSize` 2, `NextCursor`, `HasMore` true | N/A |
| Continuation | `Paging{Cursor}` from above | last row; `HasMore` false | bad cursor → existing invalid-cursor failure |
| Envelope wins | plus payload `pageSize` 1 | 2 rows | N/A |
| CLR payload paging | payload `PageSize` 1, no envelope paging | default size | N/A |
| Offset | `Paging{Offset:0}` | no rows | invalid page |
| CLR audit filters | `From`/`To`/`Category`, mixed entries | matching entries only | existing validation |
| Spelling conflict | `from` ≠ `From` | no rows | invalid request |
| User tenants | payload `UserId` X, no entity id | X's tenants, unchanged authorization | entity id ≠ payload → failure |
| REST legacy | camelCase keys | unchanged | unchanged |

</frozen-after-approval>

## Code Map

Paths are relative to `/home/administrator/projects/hexalith/tenants` (clean
`main`, `c4c78179`) unless prefixed `mcpcli:`.

- `src/Hexalith.Tenants.Contracts/Hexalith.Tenants.Contracts.csproj` -- add
  Abstractions as a package/project pair like EventStore.Contracts
  (`tests/Hexalith.Tenants.Contracts.Tests/PackageGovernanceTests.cs:353`); source
  `references/Hexalith.McpCli/src/Hexalith.McpCli.Abstractions`; Builds pins 1.0.0.
- `src/Hexalith.Tenants.Contracts/{Commands,Queries}/*.cs` -- 9 included
  `ICommandContract` records (`AggregateId => TenantId`, not `[JsonIgnore]`); 5
  `IQueryContract` classes (`ListTenants`, `GetTenant`, `GetTenantUsers`,
  `GetUserTenants`, `GetTenantAudit`). Paging members stay (accepted
  `payload_paging_member` lint) but must not be schema-required.
- `src/Hexalith.Tenants/Queries/Handlers/TenantQueryHandlerBase.cs:189,302-344,436`
  -- payload parsing, `ProtectCursor`; `TenantQueryPaginationPayloadParser.cs`;
  `../TenantQueryPaginationPolicy.cs` clamps; `ListTenantsQueryHandler.cs:31-77`
  (cursor only in payload); `GetUserTenantsQueryHandler.cs:32`;
  `GetTenantAuditQueryHandler.cs:79-89`.
- EventStore 3.125.1 -- `QueryPagingOptions`, `QueryResponseMetadata`,
  `QueryPagingMetadata`, `QueryAdapterFailureReason.InvalidPage`.
- `scripts/validate-nuget-packages.py:35` -- dependency allowlist.
- `mcpcli:src/Hexalith.McpCli.Abstractions/`; patterns
  `mcpcli:tests/Hexalith.McpCli.Sample.Contracts/CreateItemCommand.cs`,
  `mcpcli:tests/fixtures/Catalog.String.Contracts/ListItemsQuery.cs`;
  `mcpcli:tools/conformance-vectors/v1/` (validator, loopback scripts).

## Tasks & Acceptance

**Execution:**
- [ ] Contracts csproj, governance tests, package validator -- reference Abstractions.
- [ ] `src/Hexalith.Tenants.Contracts/Module.cs` -- assembly marker.
- [ ] `Commands/*.cs`, `Queries/*.cs` -- decorate; `[Description]`, `[HexalithIdentifier]`.
- [ ] `src/Hexalith.Tenants/Queries/Handlers/*` -- implement the matrix.
- [ ] `tests/Hexalith.Tenants.{Contracts,Server}.Tests/` -- decoration set; each matrix row per paged handler.
- [ ] `tests/conformance-vectors/mcpcli-v1/*.json` -- one vector per operation, including filter and two-step paging.
- [ ] `mcpcli:_bmad-output/implementation-artifacts/evidence/story-4-8/` -- scratch-host Catalog dump, lint, `--strict`, vector and loopback results, approvals.

**Acceptance Criteria:**
- Given the locally packed Contracts in a scratch McpCli host, when `list_operations
  tenants` runs, then exactly 14 operations appear with zero diagnostics and only
  `payload_paging_member` lint findings.
- Given that artifact, when `validate.py` runs with the 14 names, then no vector is
  missing, duplicate or extra, and loopback passes.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

Generated REST controllers serialize camelCase; McpCli always sends CLR names
(`McpCliJson.CreatePayload`). Hence CLR `PageSize`/`Cursor` never govern paging,
while CLR filters must.

## Verification

**Commands:**
- `dotnet restore Hexalith.Tenants.slnx && dotnet build Hexalith.Tenants.slnx --no-restore -c Release -warnaserror` -- 0 warnings
- `dotnet test tests/Hexalith.Tenants.Contracts.Tests --no-build -c Release`, then Server.Tests -- pass
- `dotnet pack src/Hexalith.Tenants.Contracts -c Release -p:Version=0.0.0-story48` into the session scratchpad, then `python3 references/Hexalith.McpCli/tools/conformance-vectors/v1/validate.py --artifact` that nupkg `--expected-package-id Hexalith.Tenants.Contracts --expected-package-version 0.0.0-story48 --operations-file` (the 14 names) `tests/conformance-vectors/mcpcli-v1/*.json` -- passes

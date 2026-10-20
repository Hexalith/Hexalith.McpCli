---
title: '4.8 Make Tenants gateway-ready for v1'
type: 'feature'
created: '2026-10-19'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'f2242b76e117c93f3bcf77320ca5d133a61e9308'
tenants_baseline_commit: '43786ea8c4a3cdd69562f7eec1109c1b891f6492'
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
`main`, `43786ea8`) unless prefixed `mcpcli:`.

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
- [x] Contracts csproj, governance tests, package validator -- reference Abstractions.
- [x] `src/Hexalith.Tenants.Contracts/Module.cs` -- assembly marker.
- [x] `Commands/*.cs`, `Queries/*.cs` -- decorate; `[Description]`, `[HexalithIdentifier]`.
- [x] `src/Hexalith.Tenants/Queries/Handlers/*` -- implement the matrix.
- [x] `tests/Hexalith.Tenants.{Contracts,Server}.Tests/` -- decoration set; each matrix row per paged handler.
- [x] `tests/conformance-vectors/mcpcli-v1/*.json` -- one vector per operation, including filter and two-step paging.
- [x] `mcpcli:_bmad-output/implementation-artifacts/evidence/story-4-8/` -- scratch-host Catalog dump, lint, `--strict`, vector and loopback results, approvals. The requesting user, as Tenants maintainer, confirmed `index` and approved the vectors on 2026-10-20 (`evidence/story-4-8/approvals.md`).

**Acceptance Criteria:**
- Given the locally packed Contracts in a scratch McpCli host, when `list_operations
  tenants` runs, then exactly 14 operations appear with zero diagnostics and only
  `payload_paging_member` lint findings.
- Given that artifact, when `validate.py` runs with the 14 names, then no vector is
  missing, duplicate or extra, and loopback passes.

## Implementation Notes

The Tenants changes were made in the `Hexalith.Tenants` working tree on `main`,
starting from `43786ea8`. A concurrent process in that tree committed and pushed
a mid-story snapshot of the Contracts decoration as `6b62b6b3`. The rest is
uncommitted in the working tree: handlers, tests, vectors, docs and the
NFR-8 description fixes. Evidence is in `evidence/story-4-8/`.

- Envelope paging lives in one helper, `TenantQueryEnvelopePaging`. When
  `QueryEnvelope.Paging` is non-null it alone governs: the existing clamps apply
  (a missing or non-positive size uses the family default), the codec and scopes
  are unchanged, and any `Offset` returns `invalid-page`. Success merges
  `Paging(PageSize, NextCursor only when HasMore, HasMore)` into the existing
  ETag/freshness metadata. Without envelope paging, the camelCase legacy parse is
  unchanged and no paging metadata is added, so REST responses gain no new headers.
- `GetGlobalAdministratorsQueryHandler` shares the standard pagination path, so it
  also honors envelope paging. It stays undecorated.
- Audit: `From`/`To`/`Category` are read under both spellings with the camelCase
  validation. Two set values that differ return `invalid-envelope` (dates compare
  by instant, categories after parsing). Under envelope paging the payload
  `cursor`/`pageSize` are not read. `Stream` is still read only from REST
  `stream`, as the boundary lists only the three filters. Its schema description
  says "Ignored by this tool".
- `get-user-tenants` uses a non-blank payload `UserId` as the target, and an
  entity identifier equal to the aggregate identifier counts as absent (the
  Gateway default routing). A distinct entity identifier that differs, or a
  non-string or undecodable `UserId`, returns `invalid-envelope` before any read.
  With no payload user, a blank one or null, the previous entity-or-self rule
  applies.
- `scripts/validate-nuget-packages.py` is unchanged. Its allowlist only exempts IDs
  that hit a forbidden fragment, and the 0.0.0-story48 five-package pack validated
  with `Hexalith.McpCli.Abstractions` in the Contracts, Client, Server and Testing
  closures. `CiQualityGateScriptTests` pins that acceptance instead.
- Scratch host: a copy of `ConformanceHost` in the session scratchpad, built with
  `-p:HexalithEventStoreVersion=3.125.1 -p:HexalithCommonsVersion=2.30.3`
  (the Tenants Builds pins), an isolated `NUGET_PACKAGES` and `--artifacts-path`,
  so McpCli's `obj/` was untouched. The Contracts package requires EventStore
  >= 3.125.1, which is above McpCli's 3.124.0 pin.
- NFR-8: three fresh-context reviews of the Catalog dump. Rounds 1 and 2 were
  PASS WITH NOTES and their accurate notes were applied. Round 3 was PASS WITH
  NOTES with no blocking finding; a follow-up review then changed wording only
  (next-page cursor guidance, get-tenant paging arguments "not used"). The remaining notes and
  the first-member bootstrap observation are for the Tenants maintainer
  (`evidence/story-4-8/nfr8-review.md`, `approvals.md` §4).

## Spec Change Log

## Review Triage Log

Pass 1 (2026-10-20). Layers: blind hunter (B), edge-case hunter (E), verification gap (V).

| ID | Finding | Verdict | Evidence and route |
|----|---------|---------|--------------------|
| B1 | `McpCliDecorationTests` member-description check uses `?.`, so a missing `[Description]` asserts nothing | medium | The null-conditional skips the Shouldly extension call; no other Tenants test reads `DescriptionAttribute`. Grouped with E5 and V1. **patch** |
| B2 | Paged descriptions promise `nextCursor`, but a default-size McpCli call returns none | medium | `OperationExecutor.cs:263` sends no envelope paging without arguments; `TenantQueryEnvelopePaging.CreateMetadata` returns null on the legacy path, so only the document `cursor` remains. Grouped with V2. **patch** |
| B3 | `get-user-tenants` without `UserId` lists a user literally named `index` | low | Real: the Gateway defaults the entity to the aggregate id. The behavior predates this story (old line 32), and the description warns callers. Grouped with E2. **defer** |
| B4 | Audit `Category` parser accepts numeric, undefined and comma-list values | low | Unreachable from McpCli: the schema enum allows only `Access`/`Administrative` (`catalog-dump.json:377`). The REST path is unchanged existing parsing, and the fix adds a guard. Grouped with E3. **reject** |
| B5 | Open maintainer decisions exist only in evidence, not the ledger | medium | Real: `approvals.md` §4 items and the pre-existing IntegrationTests failure have no ledger entry. **defer** (one entry per untracked item) |
| B6 | The enrollment deferral omits the forced EventStore/Commons bump and conformance gates | medium | The scratch host needed `HexalithEventStoreVersion=3.125.1` and `HexalithCommonsVersion=2.30.3` (`verification.md`); McpCli pins EventStore 3.124.0. **defer** |
| B7 | Pushed `6b62b6b3` holds decoration without handler migration; the vector approval is bound to no revision | medium | Real: `origin/main` descriptions promise filtering and paging the handlers there ignore, and `release.yml` can run from it. Grouped with E8. **defer** |
| B8 | Sprint status `in-progress` while the spec is `in-review` | false | step-05 syncs the story to `review`; transient workflow state. **reject** |
| B9 | Spec and verification notes describe earlier text and checks | low | The spec wording and Verification-section parts would edit this spec, so they are rejected. `verification.md` saying only round-1 fixes are uncommitted is a direct correction. **patch** (verification.md only) |
| B10 | Numeric limits in descriptions are hard-coded with no test against the constants | low | Future-drift only; the fix adds a test. **reject** |
| B11 | The identifier-marking test uses the `Id` suffix | low | Mirrors McpCli's own `unmarked_identifier_like_property` lint and is accurate for every current member; the fix adds a pinned set. **reject** |
| B12 | The package-validator test uses a synthetic dependency list | low | The real five-package 0.0.0-story48 pack was validated (`verification.md`); the fix adds tests. **reject** |
| B13 | The NFR-8 dump shows `submittable: false` | low | Descriptions are identical whatever the gateway configuration; the fix needs regeneration and re-review. **reject** |
| E1 | An aggregate override equal to the entity id silently prefers the payload user | low | Contrived (needs a deliberate aggregate override); authorization is still evaluated for the resolved user. Comparing with constant `index` would falsely reject overrides without an entity. **reject** |
| E2 | Omitted `UserId` targets `index` | low | Same root cause as B3. **defer** (with B3) |
| E3 | `Category` numeric/comma values | low | Same as B4. **reject** |
| E4 | CLR `From`/`To` without an offset parse in host local time | low | Existing date parsing; the description requires an offset; the fix adds a guard. **reject** |
| E5 | Member-description `?.` short-circuit | medium | Same as B1. **patch** (with B1) |
| E6 | Source-mode McpCli root not found when Tenants sits under McpCli `references/` | low | Same three-candidate pattern as the other roots, falling back to the identical published Abstractions 1.0.0. **reject** |
| E7 | `get-tenant` says paging arguments "have no effect", but McpCli and the Gateway still validate them | low | `OperationExecutor.cs:327` rejects pageSize outside 1-200; a direct wording correction. **patch** |
| E8 | The vector approval is tied to no vector revision or release artifact | low | `approvals.md` binds a scratch artifact hash and leaves the revision "not yet committed". Grouped with B7. **defer** (with B7) |
| V1 | Member-description test cannot fail (pre-verified gap) | medium | Same as B1. **patch** (with B1) |
| V2 | Default reads return no `nextCursor` | medium | Same as B2. **patch** (with B2) |

## Design Notes

Generated REST controllers serialize camelCase; McpCli always sends CLR names
(`McpCliJson.CreatePayload`). Hence CLR `PageSize`/`Cursor` never govern paging,
while CLR filters must.

## Verification

**Commands:**
- `dotnet restore Hexalith.Tenants.slnx && dotnet build Hexalith.Tenants.slnx --no-restore -c Release -warnaserror` -- 0 warnings
- `dotnet test tests/Hexalith.Tenants.Contracts.Tests --no-build -c Release`, then Server.Tests -- pass
- `dotnet pack src/Hexalith.Tenants.Contracts -c Release -p:Version=0.0.0-story48` into the session scratchpad, then `python3 references/Hexalith.McpCli/tools/conformance-vectors/v1/validate.py --artifact` that nupkg `--expected-package-id Hexalith.Tenants.Contracts --expected-package-version 0.0.0-story48 --operations-file` (the 14 names) `tests/conformance-vectors/mcpcli-v1/*.json` -- passes

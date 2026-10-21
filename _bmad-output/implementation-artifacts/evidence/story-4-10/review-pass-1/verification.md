# Story 4.10 local candidate

The complete local candidate is reviewable. This story remains **in progress**:
fresh complete-artifact/vector and release-inventory maintainer approval,
protected publication, published-byte revalidation and production enrollment are
still required. Historical Story 4.9 approval evidence is unchanged.

## Exact artifact

- Package: `Hexalith.Parties.Contracts` version `0.0.0-story410`.
- Retained local bytes: `artifacts/Hexalith.Parties.Contracts.0.0.0-story410.nupkg`.
- Hash: `sha512-hZfPC0pZaJa/gTFc5EwLInXwFvCrHoqXbTSezEbHkr9ss681wpf1muvcD6ipJ1eezxCyEttwzszSlI/ks9X1og==`.
- [Pending approval receipt](pending-approval.json) binds source, vector and verifier
  manifests to this artifact; it explicitly records no fresh approval.
- [Source revisions](source-revisions.json) records full Git identities. Another
  process advanced Parties HEAD during this work; this worker did not stage,
  commit, push, branch, update submodules or change tracked contents under `references/`.

## Delivered behavior

Exactly three Queries complete the seven-operation Catalog. GetParty retains
PartyDetail/party-detail routing and root PartyId; list/search retain
PartyIndex/PartySearch, party-index and aggregate parties. String IDs, envelope
tenant authority and historical actor compatibility names remain. The actual
concrete SDK handlers read canonical models directly.

Erased details now return the safe missing outcome; inactive detail remains
visible. Erased canonical detail is defensively redacted before caching, with
retained timestamps. List/search filter before paging; search receives no erased
entries. Invalid instants/ranges, duplicate case aliases, date filters on search,
unsupported search modes and CaseId reject. New DTOs contain no payload paging.
Envelope paging alone governs whenever present, with default size 20/offset 0,
maximum 100, aligned offsets and scoped cursors. Absent envelope paging retains
the existing payload page/default behavior. All exposed members have descriptions
and schema-valid examples; original Command declaration wording is unchanged.

The shared generic coverage now checks every module in the built shipping
manifest and requires an approved release inventory. Missing inventories and
synthetic approvals fail. Parties' draft release inventory deliberately fails
with pending/scope-only approval. Exact accepted lint preserves only the eight
previously accepted Tenants paging findings; Parties has no lint exceptions.
CI additionally binds restored bytes to approval hashes and exact vector filename/
SHA256 maps, rejecting added, removed, renamed or changed vectors. Its new Python
regressions run explicitly even with an empty shipping manifest.

The dependency-policy reconciliation changes only Commons.UniqueIds 2.30.1 →
2.30.3 and EventStore.Client/Contracts 3.124.0 → 3.126.0, matching a fresh restore.
No packages were added to the baseline closure. `modules` remains empty; the
selected Builds checkout already supplies those versions and its gitlink was not
moved by this worker.

## Executed verification

[Exact commands/results and retained logs](checks.json), [artifact checks](verification.json)
and the [matrix audit](matrix-test-audit.md) contain the repeatable evidence.

- Parties Release restore (`-p:Configuration=Release`) and full serialized Release
  build with `--no-restore -warnaserror -m:1`: passed, zero warnings/errors.
- Contracts 201/201, Server 315/315 and Client 330/330: passed, zero skips. Client
  exact dependency expectations now include the declaration-only Abstractions
  inherited by the existing Contracts dependency; forbidden dependencies and the
  size budget remain checked.
- Focused SDK query/privacy/matrix suite: **758/758 passed**, zero skips, with
  every case retained in [xUnit XML](query-tests.xml).
- Broad Parties domain run: 2042 passed, three pre-existing configuration fitness
  failures, zero skips. See [exact failures](broad-domain-failures.txt) and
  [baseline proof](broad-domain-log.json). Both sibling-layout rows and
  FinalDependencyReceiptsMatchTheSelectedPackageAndSourceGraph assert old
  Directory.Build.props source-selection logic removed by the pinned module
  tool. Those source/config/test files match HEAD and were not changed here.
  Focused reproduction still fails both layout rows. No broad green result is
  claimed; later added guard cases are covered by the focused final run.
- McpCli Release restore/build: passed, zero warnings/errors. Individual suites:
  Abstractions 20, Analyzers 19, Core 659 (+2 existing skips), Manifest 103,
  CLI 479 (+2 existing skips), MCP 58 passed. Final Manifest ran after fresh
  restore and policy reconciliation. Generic coverage/description subset:
  101/101 passed, zero skips, [xUnit XML](coverage-tests.xml).
- Catalog: exactly seven operations, no diagnostics, all strict discovery and
  description lint checks passed with no Parties lint findings.
- Complete shared validation/replay: all **seven** vectors passed through CLI and
  MCP, retaining every original write Query postcondition. Query scripted
  responses gained the required correlationId so those historical postconditions
  can execute; their semantic assertions were preserved.
- Both CI sample gates passed. Each ran all **80 Python regressions**, including
  altered artifact bytes, missing/stale approval, vector-set/byte changes and
  exact accepted-lint scope. Loopback was followed by a fresh solution restore.
- The enrolled-package checker passed with zero enrolled packages. This proves
  no production enrollment or published-artifact acceptance. Pending inventory
  checking returned expected exit 1 and ten approval findings.
- Whitespace checks passed using `core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol`,
  honoring tracked CRLF source files; no persistent Git configuration changed.

## Remaining release prerequisites

1. Independent description review must use the built `parties.*.stdout.txt`
   documents without source context; record its result against this candidate.
2. Obtain fresh owning-maintainer approval of this exact package hash, seven
   vector hashes and complete release inventory. A1 is scope approval only.
   `parties-candidate.json` must remain unapproved until that decision exists.
3. Resolve the three unrelated Parties configuration fitness blockers upstream,
   then run exact-source full CI through the owning release prerequisites.
4. Use the existing protected Parties release workflow. No remote operation or
   publication was performed. Fetch/verify the published bytes through the owner
   process, rebind vectors to that published version/hash, and rerun all artifact
   checks before enrollment.
5. Deliver the published central pin through Builds owner gates, enroll the
   versionless marked Contracts reference, approve the release inventory/vector
   receipt, reconcile any new restored closure and test all seven shipped
   discovery operations.

Scripted replay establishes transport envelopes and public result/error parity.
It does not prove live credentials/authorization, cross-tenant denial or persisted
command effects. C06–C08 and Stories 4.11/4.13 remain downstream gates. The legacy
host was not retired, IDs were not converted, and no module adapter was added to
McpCli.

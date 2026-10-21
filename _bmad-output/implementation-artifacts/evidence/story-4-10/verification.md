# Story 4.10 final local candidate after review patches

The requesting user **approved this exact candidate, seven vectors and release
inventory on 2026-10-20**. [The recorded decision](candidate-approval.json) binds
that approval to the reviewed hashes without asserting a separate external
signatory. Story 4.10 remains **in progress**: green owning CI, protected
publication, published-byte verification and production enrollment remain open.
Historical Story 4.9 approvals remain unchanged.

After approval, the [approved-inventory artifact verification](approved-candidate/verification.json)
passed all seven strict discovery operations, clean descriptions, exact public
names/CLR types and all seven complete CLI/MCP vectors. The inventory gate
returned an empty findings array. Original pending inputs remain retained as
historical evidence; the new `parties-approved.json` references the actual session
approval. It grants no publication, live authorization or retirement proof.

Another process committed the query work in Parties
`e55da59006f55410b9390403c67253b4f8423e18` while continuing workspace adoption.
The artifact and vectors still match the approved bytes. The only later change
among the recorded source inputs at approval recording was Parties README; the
approval receipt records that drift. The isolated release correction was carried
to latest main base `defb8d2f9a8b2c8732226227413c1808f3d7cafb` while preserving
concurrent health/security fixes. [The reviewed upstream handoff](release-readiness/parent-verification.md)
records 2,119 domain and 66 Sample tests passing, the unchanged approved bytes,
[Parties PR #56](https://github.com/Hexalith/Hexalith.Parties/pull/56), and the
separate nine-pointer owner sign-off still required by the release checklist.

[The upstream prerequisite PR is merged](https://github.com/Hexalith/Hexalith.Parties/pull/56)
at `fa708d1cdb71a8926c9ed82e2e18a3ce58fd52ef` after complete PR CI passed
4,846 unit/integration tests and 98 Aspire tests, with six preserved historical
health scenarios skipped. The required exact-main push CI is running. The
[separate nine-pointer owner decision](release-readiness/gitlink-signoff-request.json)
is pending; the merged-main RC gate remains exit 1. No release was dispatched.

## Exact artifact and preserved history

- Package: `Hexalith.Parties.Contracts` version `0.0.0-story410`.
- Retained bytes: `artifacts/Hexalith.Parties.Contracts.0.0.0-story410.nupkg`.
- Raw archive hash: `sha512-+gUcg4QyUd/GldA6JcYdBO8jzyWXavP7hg1fBikv0j6uO62gi3C/hyC9dp+IAQ3KLC8qQXxu726EfA6/NoT5/g==`.
- [Pending receipt](pending-approval.json) binds the refreshed source, seven-vector
  and verifier manifests to these exact candidate bytes. It remains the historical
  input to [the subsequent approval](candidate-approval.json).
- [First review archive](review-pass-1/verification.md) preserves the earlier
  candidate, manifests, broad verification and review evidence unchanged. The
  first description review applies to that earlier candidate. Logs in the root
  named `story410-*`, `query-tests.*`, `coverage-tests.*` and baseline records are
  historical copies; current patch evidence has the `review-` prefix.
- [Source revisions](source-revisions.json) records the local candidate phase's
  owning repository identities. Subsequent prerequisite commit/push/PR records
  are in [the release handoff](release-readiness/parent-verification.md).

## Review corrections

Both public index routes safely reject unpaired-surrogate property names and
values through the existing invalid-envelope outcome before reading state. The
mixed paging fixture now contains one independently excluded row for each of the
four timestamp bounds, keeping the expected effective totals and pages.

List/search descriptions explicitly require the returned `paging.nextCursor`,
unchanged query/filter/envelope-tenant/user/page-size scope, and no offset when
continuing. Replacement descriptions explain omitted optional nested values
become null and `OrganizationDetails.IsNaturalPerson` defaults false inside a
supplied replacement while the root classification remains unchanged. No update
behavior changed. List/search vectors also pin returned identity, type and active
status alongside their existing count and paging assertions.

Python accepted-lint input now requires an array of objects, matching the C#
gate. Verifier startup invalidates any old successful receipt/hash, records
pending then failed/passed status, and emits captured subprocess output on
failure. Inventory/lint bytes are frozen, retained and hashed. Actual restored
package identities, versions and both hash meanings are retained before scratch
cleanup: `artifactHash` hashes the raw archive; `assetsHash` and `cacheContentHash`
record NuGet's restore content hash. For signed NuGet packages those hashes can
differ. Restore metadata is checked against the assets hash, and the raw archive
is checked against its `.nupkg.sha512` sidecar when present.

The existing sample loopback CI path now executes a temporary packaged-sample
process fixture. Its nonempty enrollment calls the actual enrolled checker and
verifier through complete replay. A separate structurally valid vector with a
false semantic assertion must reach replay, fail with assertion diagnostics,
and leave a failed receipt without a success hash. Synthetic sample authority
exists only in temporary test data; the shipping manifest still has no modules.

## Focused verification for these patches

[Exact commands, results and log hashes](checks.json), the [artifact receipt](verification.json)
and [matrix audit](matrix-test-audit.md) retain the current evidence.

- Python enrollment/verifier regressions: **20 passed**.
- Concrete SDK query handler class: **738 passed**, zero failures/skips, retained
  in [xUnit XML](review-query-tests.xml). After the final extra before-read
  assertions, the malformed-payload method alone was rebuilt and rerun:
  **18 passed**, zero failures/skips.
- Contracts decoration/description class: **2 passed**, zero failures/skips.
  Focused Release builds passed with zero warnings/errors.
- Real packaged-sample process fixture: **both branches passed**. The positive
  branch exercised nonempty enrollment, inventory/lint and complete replay with
  **53 resolved packages** and input hashes. The false-assertion branch confirmed
  replay diagnostics and removal of stale success evidence.
- Repacked Parties artifact: **seven strict discovery operations**, all seven
  descriptions clean, **all seven complete vectors passed CLI and MCP replay**.
  The receipt retains **53 resolved package identities/versions/hashes**. The
  list/search identity/type/active assertions executed in that replay.
- Pending release inventory: **expected exit 1**, ten pending/scope-only approval
  findings; the failed receipt retains the inventory input digest and no success
  hash. See [negative receipt](approval-gate-negative/verification.json).
- Shell syntax and CRLF-aware whitespace checks passed in both owning repos,
  followed by an actual trailing-space check. No persistent Git config changed.

These patch checks were followed by [independent full verification](parent-final/verification.md).
Both final Release builds and all McpCli checks pass. Parties retains the same
three baseline fitness failures; its other 2,064 domain tests pass. The archived
broad results remain historical and are not substituted for these final runs.

The [final independent description review](description-review-final.json) passed
against the exact seven current built documents without source/spec context.
[Integrity verification](parent-final/integrity.json) matched every source,
vector and verifier input, exact artifact bytes, final description hashes and
the original first-review receipts. The pending receipt now also binds the
authoritative A1 migration scope, including N01–N04 exclusions, and the pending
machine-readable release inventory candidate.

## Unchanged release prerequisites and baseline blockers

The initial broad Parties command was
`dotnet test tests/Hexalith.Parties.Tests --no-build --configuration Release`:
exit **2**, **2042 passed, three failed, zero skips**. The failures were
`FinalDependencyReceiptsMatchTheSelectedPackageAndSourceGraph` and both
`McpCliSiblingLayoutsSelectAbstractionsProjectWithoutNestedCheckout` rows
(`Hexalith.McpCli`, `references/Hexalith.McpCli`).
[Exact baseline command/result](review-pass-1/broad-domain-log.json),
[failure excerpts](review-pass-1/broad-domain-failures.txt) and the
[focused layout reproduction](review-pass-1/baseline-layout-tests.log) remain
unchanged. The proof command
`git diff --exit-code HEAD -- Directory.Build.props src/Hexalith.Parties.Contracts/Hexalith.Parties.Contracts.csproj tests/Hexalith.Parties.Tests/FitnessTests/PlatformApiPrerequisitesTests.cs`
returned **0**: those upstream source-selection/configuration expectations were
not changed by this work. Independent final verification reran the full domain
suite: exit **2**, **2,064 passed, the same three failed, zero skips**, and repeated
the unchanged-input proof successfully. Exact final logs are retained under
[`parent-final/`](parent-final/verification.md).

The already-authorized baseline reconciliation remains Commons.UniqueIds
2.30.1 → 2.30.3 and EventStore.Client/Contracts 3.124.0 → 3.126.0, matching the
selected central catalog and fresh restored closure. No Builds gitlink moved;
`modules` remains empty. The generic lint gate retains only the eight explicitly
accepted historical Tenants paging findings; Parties has no lint exceptions.

1. Resolve the unrelated upstream baseline blockers and complete owning CI.
2. Publish through the protected owner workflow, retrieve the published bytes,
   rebind the vectors to that exact published version/hash and revalidate.
3. Deliver the central version pin through Builds owner gates, then enroll the
   versionless marked Contracts reference with its approved inventory/receipt
   and verify the shipping seven-operation discovery surface.

Scripted replay proves transport routing and public result/error parity. It does
not prove live credentials/authorization, cross-tenant denial or persisted command
effects. C06–C08 and Stories 4.11/4.13 remain downstream gates.

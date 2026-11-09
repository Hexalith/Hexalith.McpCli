---
title: '5.4 Prove shared-head parity and safety'
type: 'feature'
created: '2026-11-09'
updated: '2026-11-09T18:04:03+01:00'
status: 'in-progress'
baseline_commit: 'f6c8e0e3a2105f555e6eec3c667b088085c47fc4'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing proves yet that McpCli can replace `Parties.Mcp` safely on a named environment.
- The live lane runs only the seven happy-path vectors, through the CLI head.
- No test pins a 401 or 403 document, or any tenant negative, for a Parties operation.
- C05's delete oracles and C08's cross-tenant denial are never exercised live.
- Restricted Admin names are never probed, with or without `confirm: true`.
- No evidence set binds the candidate, Catalog digest and environment by hash.

**Approach:**
- Add generic offline guards over the enrolled Parties 1.5.1 catalog, run through both heads.
- Add live boundary cases, and live MCP-head reads, on the CI live topology.
- Assemble one redacted, hash-bound evidence set with a C01–C08 variant matrix.
- HALT for the Parties owner's exact-byte approval and verdict.
- Production `src/` changes only where a guard exposes a defect.

## Boundaries & Constraints

**Always:**
- Only tests name Parties, Tenants or EventStore.
- `src/` and the runners in `tools/live-topology/` stay generic: no module names and no fixed vector or runtime counts. Derive the expected runtime count instead of keeping `ci.py`'s literal `22`.
- Every guard asserts the full error document, stdout, stderr, MCP `Content` and `StructuredContent`, and the Gateway request count. It fails when the guard is removed.
- Each live Command is submitted once. Head parity comes from loopback (`check_enrolled.py`), never from resubmitting.
- A no-mutation claim rests on a persisted end-state read with an authorized identity, not on the error alone.
- Each variant row cites one of these, or is marked a gap: a McpCli test, a loopback or live receipt, or a Parties upstream test at the enrolled revision. Matching operation names proves nothing.

**Never:**
- Add module-specific code, error mapping, `confirm` handling or dependencies to `src/`.
- Change identifier validators.
- Edit `references/`.
- Change the approved vectors, live plans or `approval.json`, or enroll another Parties version.
- Claim a release, publication or retirement. Story 5.5 owns retirement, and `epic-4-retro-item-6` binds release claims.
- Fix F7 or redactor item 5 here.

**Decisions (2026-11-09, user):**
1. **F7 accepted.** The user, as owner, answered "accept". Until `epic-4-retro-item-9-ascii-tenant-input` closes, U+212A KELVIN SIGN may alias an ASCII tenant; the Gateway's `TenantCanonicalizer` behaves the same way.
   - Pin this as the accepted limitation and record the acceptance in the evidence.
   - Every other non-ASCII look-alike must fail closed.
2. **Selected environment: the CI live topology** ("CI topology via PR").
   - It is the v1 disposable Aspire topology: public EventStore 4.1.0 and Tenants 7.0.5 archives, plus the qualified Parties source.
   - GitHub Actions runs it on a PR to `main`, and the evidence is the downloaded `TestResults/live-ci` artifact.
   - This authorizes pushing a non-`main` branch and opening that PR when the live run is due.
3. **Live MCP head included.**
   - `run_live.py` also runs every Parties Query vector through the MCP head (reads only).
   - The boundary cases run through both heads, including the MCP-only per-call override denial.
   - Commands stay CLI-only and are submitted once.
4. **Scope split: redactor item 5 first.**
   - The hardened redactor and the committed secret scan are a separate change (ledger entry under this spec's heading in `deferred-work.md`).
   - The offline and live test work proceeds now.
   - The committed live run and evidence set wait until that change lands, and the evidence must pass its scan.
5. **Gaps: the owner decides each one** at the approval HALT.
   - Either a versioned, owner-approved Parties inventory 1.3.0 amendment records an approved change, or the gap stays blocking with a ledger owner.
   - The story ends with an approved verdict: `retirement-ready` or `retirement-blocked`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| No token | Parties Query and Command with no token; the Gateway answers 401 | `gateway_error` with status 401; equal documents from both heads | No `Authorization` header is sent; live, nothing is mutated |
| Invalid token | Forged signature | 401 `gateway_error`; the token appears on no channel | Live, nothing is mutated |
| Unauthorized principal | A token granted only `tenant-a`, or a nonmember token, used with session tenant `tenant-b` or an allowed MCP per-call override to `tenant-b` | Gateway refusal through both heads, with the documented status | The `tenant-b` party is neither disclosed nor changed |
| Override disabled | MCP per-call tenant differs from the session, without `allow-tenant-override` | `validation_failed` at `/tenant` | Zero Gateway calls |
| Platform scope as tenant | `platform:tenants` as session or per-call tenant on a Parties operation | `validation_failed` at `/tenant` | Zero calls |
| Reserved tenant | `system` or `SYSTEM` | `validation_failed` at `/tenant`, "…reserved." | Zero calls |
| Look-alikes | Cyrillic `а`, U+0130, fullwidth letters | `validation_failed` at `/tenant` | Zero calls |
| F7 limitation | `Kelvin` spelled with U+212A | Wire value `kelvin` (accepted-limitation pin) | The test names item 9, so the fix must flip it |
| Restricted names | Admin and confirm-gated legacy names, and Tenants-excluded operations, with `confirm: true` in both arguments and payload | Absent from `list_operations` and `operations`; `unknown_operation` through both heads | Zero calls |
| C05 missing | Live deactivate of a party that was never created | 404 `party-not-found` | No party is created |
| C05 concurrent repeat | Two concurrent deactivations of one active party, with distinct message IDs | Both accepted; the party is inactive | Exactly one deactivation event is persisted |

</frozen-after-approval>

## Code Map

- `tests/Hexalith.McpCli.Cli.Tests/PartiesMigrationCompatibilityTests.cs`, `BothHeads.cs`, `ScriptedGateway.cs` -- the both-heads harness to reuse.
  - `PlatformScopeCommandTests.cs:13-41` and `tests/Hexalith.McpCli.Mcp.Tests/PlatformScopeProtocolTests.cs:19-50` show the full-document, zero-call pattern for `system`.
  - `QueryValidationCommandTests.cs:55` holds the only non-ASCII case (`é`).
  - No head test pins 401 or 403: `ExecutionFailureCommandTests.cs:34-63` covers only 422, 409, 5xx and 2xx.
- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:115-134` -- lowercases the tenant, then checks the pattern. U+0130 is refused; U+212A aliases. `:316-340` holds the scope and override refusals. Do not change any of it.
- `README.md` -- the error-code list is at `:559`; a Gateway 401 or 403 is a `gateway_error` carrying that status. CLI `--tenant` is the session tenant (`:531`).
- `src/Hexalith.McpCli/Cli/CliRunner.cs:87-90` -- an unknown option returns `invalid_arguments`.
- `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:81-85`, `:126-139` -- MCP likely ignores extra arguments. Pin that behavior; do not change it, since `epic-3-retro-item-2` owns call-envelope validation.
- `tests/Hexalith.McpCli.Core.Tests/EnrolledModuleCoverageTests.cs:15-29` with `tools/inventory-coverage/v1/*-approved.json` -- the catalog equals exactly the `include` sets, and Tenants excludes six operations. Admin inventory 1.0.1 has no `include` row (`eventstore-admin-migration-inventory-v1.md:157-258`).
- Live identities:
  - `tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:65-130` and `NativeFixtureIdentity.cs:12-46` -- signed tenant, domain, permission and nonmember claims.
  - `NativeAdministratorBoundary.cs:20-50` -- a refusal with the target checked absent before and after.
  - `GatewaySmokeTests.cs:29-64` -- the 401 pattern.
- Live runners:
  - `tools/live-topology/run_live.py:39` -- `observe` is CLI-only; `tools/conformance-vectors/v1/run_loopback.py:247-279` provides `HeadProcess.cli` and `.mcp`.
  - `tools/live-topology/ci.py:757-781` -- the independent smoke case and the literal `22`.
  - `.github/workflows/ci.yml:150-169` -- the exact discovery assertion.
- `tools/conformance-vectors/v1/check_enrolled.py` → `run_loopback.py:782-864` -- discovery parity, a reset `ReplayGateway` per head, and equal documents and requests for all seven Parties vectors. It computes no Catalog digest.
- Binding precedent: `tools/live-topology/live_plans.py:25` (`BINDING_KEYS`) and `_bmad-output/implementation-artifacts/evidence/story-4-13/live-complete/*/parties.*/live-result.json`.
- Variant sources:
  - Inventory `:178-185` (C01–C08).
  - `evidence/story-5-3/verification.md:221-311`.
  - `evidence/story-4-10/matrix-test-audit.md`, for the Parties-side C01, C02 and C04 tests.
  - Legacy `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/` has no task-context, freshness or output-budget behavior; it only bounds input (`Tools/PartiesMcpTools.cs:566`, C03/C04). Record those variants as "absent at source", with anchors.
- `deferred-work.md:556` (a rejection-only stream reachable by update and deactivate) and `:827` (profile identity beside a flag or environment connection) bear on C05 and C08. Cite them; do not duplicate them.

## Tasks & Acceptance

**Execution:**
- [x] `tests/Hexalith.McpCli.Cli.Tests/PartiesRetirementSafetyTests.cs` -- every offline matrix row, through both heads over the production catalog: 401 and 403 documents from `ScriptedGateway`, override disabled, platform scope, reserved tenant, look-alikes, the F7 pin, and restricted names with `confirm: true`.
- [x] `tests/Hexalith.McpCli.Integration.Tests/` -- a boundary class, plus identity helpers, for the live rows through both heads: 401s, cross-tenant refusal, nonmember, C05 missing and C05 concurrent repeat, each followed by an authorized end-state read.
- [x] `tools/live-topology/run_live.py`, `ci.py` and `.github/workflows/ci.yml`:
  - Add MCP reads for Query vectors.
  - Run the boundary class as an independent isolated case.
  - Derive the counts.
  - Extend the discovery assertion.
  - Cover each change in `test_*.py`.
- [x] After the split redactor change lands: push a branch, open the PR, and download and verify the live artifact.
- [ ] `_bmad-output/implementation-artifacts/evidence/story-5-4/`:
  - `manifest.json`: the full commit; SHA-256 of the head binaries; the Parties 1.5.1 artifact hash; the Catalog digest (SHA-256 of the sorted-key, compact `list_operations` structured content); the components and revisions of the environment; the vector, plan, approval and inventory hashes; and the CI run ID and artifact hash.
  - `parity-matrix.md`: C01–C08 and the seven variants. Admin and technical rows are marked "absent; name similarity proves nothing".
  - The scan receipt, the F7 acceptance and `verification.md`.
  - HALT for the owner's exact-byte approval and verdict, then record the receipt.
- [x] `README.md`, `sprint-status.yaml` and `deferred-work.md` -- document a 401 or 403 as a `gateway_error` and the F7 limitation. Record status, and grep the ledger before appending.

**Acceptance Criteria:**
- Given the CI live topology, when the lane runs, then all seven Parties vectors, the MCP reads and every boundary case pass with `fullLiveAccepted: true`, and `check_enrolled.py` reports `fullV1Accepted`.
- Given the evidence set, when the owner reviews it, then every C01–C08 and variant row is preserved, an approved change or a named gap, and the receipt binds the exact bytes and the verdict.
- Given the whole change, when it is built, then `src/` has no new module name or dependency, and `DependencyPolicyTests` and `EnrolledModuleCoverageTests` pass unchanged.

## Implementation Notes

- Offline production-catalog safety covers both call kinds, both heads, session/per-call tenant refusals, all inventoried Admin names and six excluded Tenants targets. The accepted Kelvin alias has a dedicated item-9 pin. No production source, identifier validator, dependency policy, approved vector, live plan, approval file or reference checkout was changed.
- The boundary uses real ConformanceHost CLI and stdio MCP processes, with complete channel assertions, a counting forwarder and authorized before/after business-state reads. A separate offline process-harness regression covers successful and refused calls without topology. The in-process harness waits for the MCP response writer before teardown.
- Negative-control tokens have tenant-A-only or no tenant grants and omit the administrator role. This proves exact signed-grant authorization, not persisted Parties membership. The existing administrator bootstrap separately verifies persisted native membership. Boundary owner grants are isolated from unchanged vector/smoke grants.
- The selected cohort’s absent detail returns `500/query_internal_error` with `actor-not-found-infrastructure`, as inventory C05 records. Missing deactivation returns `404/party-not-found`; separate CLI/MCP absent targets also verify persisted events contain no creation/deactivation effect (a rejection-only stream can remain). Before/after comparisons remove only observation-time `freshness`, retaining every business member.
- Concurrent CLI processes use distinct generated message IDs. The qualified Gateway awaits the owner’s `ProcessCommandAsync` before returning acceptance; after both return, the boundary waits for the authorized inactive projection and requires exactly one persisted deactivation event in the actor’s stream. The actor ID and state keys follow qualified EventStore `dbc6e7e08d605ba6c6c790e3e08a15dc8bbdec8a`. Any configured sidecar `DAPR_API_TOKEN` is retained for state reads; app-channel authentication is unchanged.
- The generic runner executes every Query observation through MCP as well as CLI, while every vector Command stays CLI-only. Semantic receipts require both Query heads. CI derives expected counts from approved vectors and its independent-case registry; it allocates each independent case 960 seconds and reserves 600 seconds within the unchanged 17700-second outer budget.
- [Review][Resolved prerequisite] The separate redactor/committed secret-scan change closes the existing planning deferral in `deferred-work.md` under this spec's heading; see `spec-epic-4-retro-item-5-harden-ci-redaction.md` and `evidence/epic-4-retro-item-5/verification.md`. Story 5.4's dedicated live CI and final hash-bound scanned packet are now retained; its exact-byte owner approval/verdict remains pending. The rejection-only-stream and mixed-profile-identity work is already tracked (`deferred-work.md:556`, `deferred-work.md:833`). The final manifest binds executed evidence; no approved retirement verdict is asserted.

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` -- expected: 0 warnings.
- `dotnet test tests/<Core|Cli|Mcp|Manifest>.Tests --no-build --configuration Release`, one project at a time -- expected: all pass.
- `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'`, then `run-vectors.py --preflight-only`, then the CI discovery listing -- expected: pass, with the new cases listed.
- `python3 tools/conformance-vectors/v1/check_enrolled.py --output <task-dir>` -- expected: `fullV1Accepted: true`.
- The split change's secret scan over `evidence/story-5-4/` -- expected: zero findings.

### Local implementation verification (2026-11-09)

> Historical snapshot before the redactor prerequisite and dedicated PR runs. The final CI qualification below supersedes its pending-live statements.

The story remains **in-progress**. The live boundary is compiled and discovered, but has not executed. The frozen redactor/secret-scan prerequisite prevents the committed CI run, final evidence binding and owner approval/verdict. No `fullLiveAccepted` or retirement verdict is claimed.

- Normal solution restore and Release build with `-warnaserror`: passed, zero warnings/errors (`/tmp/story54-restore.log`, `/tmp/story54-build-final.log`).
- Core: 877 succeeded, four Windows-only skips; final full CLI: 582 succeeded, two Windows-only skips (584 total), including all 26 new safety/process-harness cases; MCP: 94 passed. Logs: `/tmp/story54-core-tests.log`, `/tmp/story54-cli-final.log`, `/tmp/story54-mcp-tests.log`.
- Manifest: 362 passed with no skips, including unchanged dependency/fixture closure guards (`/tmp/story54-manifest-final.log`, `/tmp/story54-manifest-final.xml`). An earlier shared in-process project-reference attempt changed the reviewed fixture closure; it was removed before the successful run. The final live harness uses the existing ConformanceHost process and no new package or production project reference.
- New safety/process-harness tests: 26 passed, no skips (`/tmp/story54-head-tests-final.log`); the process cases exercise real CLI and stdio MCP success and 401 documents, every output channel and Gateway counts without topology.
- Generic runner: 27 Python cases passed; lane: 15 passed; plan/dependency checks: 38 passed. The first 94-case CI-hook run passed 90 and exposed four stale expectations for the added independent case; all four pass after correction (`/tmp/story54-ci-fixes.log`). The clean full sweep passed 203 cases (`/tmp/story54-python-final.log`); the later receipt-attribution fix and its additional test passed all 27 affected runner cases (`/tmp/story54-runner-final.log`). All 204 currently discovered cases are therefore covered by these successful runs.
- Preflight-only passed with `fullLiveAccepted: false` (`/tmp/mcpcli-story54-live-preflight/live-lane.json`). Discovery matched exactly every approved vector plus smoke and boundary: 23 cases today (`/tmp/story54-discovery.txt`). These checks start no live services.
- `check_enrolled.py --output /tmp/mcpcli-story54-enrolled` passed: Parties 1.5.1 (7 operations), Tenants 7.0.5 (14 operations), aggregate `fullV1Accepted: true` (`/tmp/mcpcli-story54-enrolled/enrolled.json`, `/tmp/story54-enrolled.log`). The 203-case full Python sweep and 27-case affected-runner rerun above passed. No production Core validation, Sample.Contracts or Gateway wire behavior changed, so sample conformance gates are not required by this implementation.

### Frozen matrix audit (historical implementation snapshot)

This table records coverage before dedicated CI qualification. The final executed coverage and remaining gaps are in `evidence/story-5-4/parity-matrix.md`.

`Safety` below means `tests/Hexalith.McpCli.Cli.Tests/PartiesRetirementSafetyTests.cs`; all named safety tests executed in the passing 26-case head run. `Live` means `SharedHeadBoundaryTests.SharedHeadsPreserveAuthorizationAndDeactivationSafety`; it is built/discovered only. Every offline refusal checks complete stdout/stderr, MCP Content/StructuredContent and Gateway request cardinality.

| Frozen row | Covering test / evidence | Live status |
| --- | --- | --- |
| No token | `Safety.CredentialRefusalsPreserveTheCompleteGatewayErrorAsync`, 401/null token, Command and Query | Live not run—redactor prerequisite; designed authorized before/after reads and absent Authorization header |
| Invalid token | Same test, 401/forged credential, both call kinds; process harness also passes 401 through each head | Live not run—redactor prerequisite; signed wrong-key control |
| Unauthorized principal | Same test, complete 403 documents; Live covers tenant-A/no-grant principals and allowed per-call override | Live not run—redactor prerequisite; no persisted Parties-membership claim |
| Override disabled | `Safety.DisabledMcpOverrideMakesNoGatewayCallsAsync`, both call kinds | Live not run—redactor prerequisite |
| Platform scope as tenant | `Safety.PublicTenantNegativesHaveNoGatewayCallsAsync`, session and MCP per-call input, both call kinds | Live not run—redactor prerequisite |
| Reserved tenant | Same test, `system` and `SYSTEM`, both call kinds and tenant sources | Live not run—redactor prerequisite |
| Look-alikes | Same test, Cyrillic a, U+0130 and fullwidth tenant, both call kinds and tenant sources | Live not run—redactor prerequisite |
| F7 limitation | `Safety.AcceptedF7Item9KelvinAliasReachesTheGatewayAsAsciiAsync`, exact `kelvin` wire value through both heads | Accepted offline limitation pin; item 9 stays open |
| Restricted names | `Safety.RestrictedNamesCannotBeDiscoveredOrAuthorizedByConfirmAsync`, every inventoried Admin name and six excluded Tenants names, with/without confirm, both heads/call kinds | Offline zero-call guard passed; no live restricted mutation is attempted |
| C05 missing | Live uses a different never-created target per head, 404/`party-not-found`, authorized absence read plus persisted creation/deactivation exclusion | Live not run—redactor prerequisite |
| C05 concurrent repeat | Live starts two CLI processes once each, asserts distinct message IDs, authorized inactive state and exactly one persisted deactivation event | Live not run—redactor prerequisite |

All final local logs and the Manifest XML, discovery listing and summary receipts are preserved under `/tmp/mcpcli-story54-verification/`. `git diff --check` passed. The committed live run, evidence manifest/variant matrix/scan receipt and owner verdict remain unchecked tasks under the frozen prerequisite.

### Fresh revalidation of the existing implementation (2026-11-09)

The implementation already present at `1c18a42aa9439bfc29009951f29968cac2a71436` satisfies the local execution tasks; no additional production, test, runner, dependency or approved-input changes were necessary. Fresh checks passed:

- Solution restore and Release build with `-warnaserror`: zero warnings or errors.
- Core: 877 succeeded, four Windows-only skips; CLI: 582 succeeded, two Windows-only skips; MCP: 94 passed; Manifest: 362 passed. The four projects ran one at a time.
- Complete live-topology Python sweep: all 204 tests passed in 569.967 seconds.
- Preflight-only: passed with `fullLiveAccepted: false`; discovery matched exactly the 21 approved vectors plus independent smoke and shared-head boundary (23 cases).
- Enrolled gate: both exact artifact replays and the combined production-manifest replay passed, with 21 operations and `fullV1Accepted: true`.

Fresh command logs are `/tmp/story54-current-{restore,build,Core,Cli,Mcp,Manifest,python,preflight,enrolled}.log`; discovery is `/tmp/story54-current-discovery.txt`. Receipts are under `/tmp/mcpcli-story54-current-live-preflight/` and `/tmp/mcpcli-story54-current-enrolled/`. No live topology was started. The story remains **in-progress**: the separate redactor/committed-secret-scan prerequisite still prevents the committed live run, final hash-bound evidence set and exact-byte owner approval/verdict.

### Separate prerequisite completed (2026-11-09)

`epic-4-retro-item-5-harden-ci-redaction` now supplies the shared Python redactor
and committed evidence scanner, verified separately in
`evidence/epic-4-retro-item-5/verification.md`. The preceding revalidation note
records the state before that prerequisite. Story 5.4 remains **in-progress**:
its dedicated live CI run, final hash-bound packet and its own scan receipt, and
exact-byte owner approval/verdict remain pending. This prerequisite's receipt
does not establish Story 5.4 live acceptance or authorize retirement.

### Committed live qualification follow-up (2026-11-09)

The prior CI run `42614718738` passed all 21 approved live vectors and the
independent smoke, then exposed a boundary-test assertion defect before its
negative cases ran: the qualified Gateway includes a business `resultPayload`
on create acceptance, while the test expected an acceptance document without
`result`. The boundary now checks the complete copied result against the
captured response and exact submitted identifiers. Concurrent acceptances are
paired with their originating requests. The process-harness regression runs
both heads with and without the optional result; it preserves every public
channel and request-count assertion. Production behavior and approved inputs
are unchanged. A fresh dedicated PR lane is required; the failed historical
lane establishes no full live acceptance.

CI preparation now retains `head-catalog.json`: equal CLI/MCP discovery from
the actual hosted binaries, every head DLL hash, each module's sorted-key
compact `list_operations` structured-content SHA-256, and the digest of the
complete module-to-content map. This generic read-only capture supplies the
final packet's exact candidate/Catalog binding without relying on a local
rebuild. Offline tests cover discovery failure/mismatch, empty Catalog and
binary drift; CI-hook coverage pins the bounded capture and failure path.

Fresh local follow-up checks passed: solution restore and Release build with
zero warnings/errors; Core 877 passed (four OS skips), CLI 584 passed (two OS
skips), MCP 94 passed and Manifest 362 passed. The six process-harness cases,
seven capture-helper regressions and focused CI capture/failure-path case all
passed. Full affected CI-hook verification continues before final evidence.

### Qualified authentication oracles and early boundary (2026-11-09)

PR run `42631573309` passed every vector and smoke, then reached a second
boundary oracle defect: public EventStore 4.1.0 sends structured 401 errors,
not a bare HTTP reason phrase. Its pinned `ConfigureJwtBearerOptions` supplies
reason `authentication_required`, distinct missing/invalid-token details and
no correlation field. The boundary now pins those complete documents and the
two exact tenant-grant 403 shapes from `AuthorizationExceptionHandler`.
Eight new process cases exercise all four shapes for Commands and Queries
through CLI and MCP, including every channel and Gateway cardinality.

The generic pre-vector independent-case registry now runs the boundary once
before the long vector sweep; a failed boundary stops there. The post-vector
registry retains smoke, including after vector failures. Preparation provenance
is rechecked after the early case because it may rebuild hosts. Counts and
budgets remain derived from the combined registry. Focused CI-hook checks pin
the new order, refusal before vectors, post-boundary drift and the existing
vector/smoke failure and cancellation behavior. Production behavior, identifier
validators, dependencies and approved inputs remain unchanged.

The Release build passes with zero warnings/errors; all 14 process-harness
cases pass; the full CLI project passes 592 cases with two OS-only skips.
Five focused ordering/failure/cancellation checks and the new early-drift
check pass. Broad CI-hook verification continues while the next PR candidate
is qualified. Prior attempt receipts remain distinct from its final packet.

### Empty 401 transport response (2026-11-09)

Run `42641067905` passed the Query credential/grant cases, then found an empty
401 response for the forged-token Command; the early boundary correctly kept
vectors unrun. The generic client already maps that exact HTTP fallback to
`gateway_error`, status 401 and detail `Unauthorized`, without a reason field.
The boundary now asserts that complete fallback for an empty body and retains
the pinned structured challenge for every nonempty body. Live credential
receipts record the response format and full public error, and missing-token
CLI/MCP documents are compared directly per call kind. Four more process cases
pin empty missing/invalid-token challenges through both heads and call kinds.
The clean 99-test CI-hook sweep passed; production behavior remains unchanged.

### Command grant refusals before the structured pipeline (2026-11-09)

Run `42645969397` then exposed the first tenant-A-grant Command returning an
empty 403. Qualified EventStore `dbc6e7e08d605ba6c6c790e3e08a15dc8bbdec8a`
`CommandsController.cs:146-149` returns `Forbid()` before pipeline dispatch for
missing tenant grants. The boundary now pins its whole existing public
`gateway_error` / 403 / `Forbidden` fallback, including absent optional members;
Query refusals retain the complete structured tenant-mismatch/nonmember oracle.
Four additional both-head process cases cover the empty 403 transport for both
call kinds and both signed-grant scenarios. Vectors stayed unrun after the early
boundary failure. No production behavior, approved input or runner changed.

### Discovered sidecar endpoint for persisted C05 evidence (2026-11-09)

Run `42648730822` passed the credential, override and tenant-negative rows, then
found the C05 state helper’s fixed-port assumption (`127.0.0.1:3501`). The
restored fixture helper exposes no supported sidecar application object. The
fixture now discovers exactly one `eventstore` sidecar through bounded
`dapr list --output json` inside the already-required isolated namespace and
passes its actual HTTP client to both persisted-state oracles. The separate
`DAPR_API_TOKEN`, when configured, is preserved; no bearer credential is sent
to the sidecar API. Offline regressions require an ephemeral discovered port,
reject missing/duplicate/invalid registrations and prove both C05 helpers read
the expected state keys with and without the API token. No runner, production
source, approved input or dependency changed.

### Final CI qualification and pending owner checkpoint (2026-11-09)

Candidate `3e8f6a4e681018c7ca8356997d4fd28378217d37` passed CI run `42652261452` on draft PR #5. All 21 approved vectors, independent shared-head boundary and Gateway smoke passed; both live Query heads are required and each live Command is submitted once. Hosted `check_enrolled.py` reports `fullV1Accepted: true`; live receipts report `fullLiveAccepted: true`. All 216 hosted topology checks passed and discovery matched the 21 vectors plus the two independent cases. The six ordinary projects passed 1,985 tests with six OS-only skips; Manifest and enrolled inventory checks remain unchanged.

The latest Release build has zero warnings/errors. All 77 named offline safety, compatibility, process and identity cases passed without skips, including 22 process cases through both heads. The clean 99-hook sweep applies to unchanged Python source. Initial failing sweeps and earlier live attempts retain their own status and exact artifact bindings; none is promoted into final acceptance.

The complete packet is `evidence/story-5-4/`: manifest, C01–C08/seven-variant matrix, F7 acceptance, source audit, full text receipts and logs, verification and secret scan. It binds the actual hosted checkout and equal candidate tree, every head DLL, exact Catalog content, Contracts artifact, environment/source revisions, approved inputs, CI run/artifact digests and retained text hashes. The source audit clearly distinguishes upstream tests at the enrolled revision from tests executed in this run. Production source, dependencies, identifiers, approved vectors/plans/approvals/inventories and reference gitlinks are unchanged.

**HALT remains at the frozen owner checkpoint.** Exact-byte approval and an approved `retirement-ready` or `retirement-blocked` verdict are not recorded. The proposal is `retirement-blocked`, keeping G01–G06 open with the matrix’s named ledger owners; no inventory 1.3.0 amendment is asserted. Story 5.4 remains in-progress until that response and its bound receipt. No release, publication or retirement is claimed.

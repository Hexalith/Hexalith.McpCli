---
title: '4.13 Test every vector against live Gateway semantics'
type: 'feature'
created: '2026-10-25'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'aabc03c68c56ac8085ee1b145654576f5fd201a4'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Replay proves transport agreement but cannot prove persistent business effects. All 21 approved vectors need live proof, including Tenants continuation and audit filters handed off from Story 4.8.

**Approach:** Execute each vector through one production CLI adapter against a fresh disposable v1 topology. Add explicit, test-only live plans for dynamic values and bounded observations; preserve the approved v1 vectors.

## Boundaries & Constraints

**Always:** Recheck restored packages, approval hashes, inventories, complete Catalog coverage and Core compatibility before execution. Submit each declared Command step once; poll only Queries for asynchronous readiness. Preserve static assertions; explicitly bind scripted cursors to real results. Configure the existing authenticated Development bootstrap and verify persisted administrator authority through a privileged Query. Retain authentication, mTLS, default deny, standard Dapr prerequisites and platform fixture lifecycle.

**Never:** Add module-specific runner branches, direct domain/state-store setup, Command retries, excluded Operations to the Catalog, dependency upgrades, reference edits or publication. Blocking live CI wiring remains Story 4.14. Test bootstrap mutations stay inside fresh private Redis; user topologies remain untouched.

**Decision (2026-10-25, requesting user):** Restore compatibility upstream in the owning Parties repository, then integrate it. Necessary upstream platform prerequisites and qualified reference/package integration are authorized exceptions to the dependency/reference limits above. Preserve approved Contracts and vector bytes, keep reference contents read-only, and isolate existing upstream user edits. Any new publication requires a concrete qualified candidate before its release step.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Complete approved inputs | Run all 21 vectors, each in fresh state; assert acceptance/documents and semantic effects |
| Stale package, vector or live-plan binding | Fail preflight before any vector Command |
| Delayed bootstrap/projection | Poll declared read observations within a deadline; never resubmit writes |
| Dynamic cursor/time | Capture typed values, bind later calls, prove continuation contents and audit inclusion/exclusion |
| Missing prerequisite, invalid selector or unresolved binding | Report explicit failure/skip; never claim full live acceptance |
| Semantic mismatch | Name vector, Operation, phase and assertion path; retain sanitized results |

</frozen-after-approval>

## Code Map

- `tools/conformance-vectors/v1/{check_enrolled.py,validate.py,run_loopback.py}`: reuse approval/artifact checks, shared validator, production Core preflight and typed assertions; scripted-response success checks are unsuitable for live results.
- `tests/Hexalith.McpCli.ConformanceHost/`: existing production-manifest CLI adapter and offline compatibility entry point.
- `tests/Hexalith.McpCli.Integration.Tests/`: platform fixture, standard prerequisite skips and authenticated smoke. A separate short-lived live identity gains the declared write/read scopes; the persisted administrator query proves its authority before vectors run.
- `tests/Hexalith.McpCli.AppHost/`: helper composition and declarative routes. Normal Tenants bootstrap uses the shared Development signing contract; projection delivery needs explicit sidecar permission.
- `tools/live-topology/run-isolated.py`: owned namespaces, fresh Redis, daemon lifecycle and bounded child receipts. Reuse unchanged where possible.
- Owning Parties `src/Hexalith.Parties/Program.cs` already passes the host assembly through `PartyAggregate`. Clean-owner tests and actual live `/query` HTTP 200 logs prove metadata/handler discovery works. `PartySdkQueryFailureReason.ReadModelUnavailable` uses the historical `actor-not-found-infrastructure` alias; investigate missing canonical projection data rather than adding duplicate host registrations or actors.
- Owning Parties has unrelated staged/unstaged user changes, including `PartySdkQueryHandlerTests.cs`. Preserve them; isolate the repair or restrict exact owned paths.
- The actual named projection coordinator refuses fresh-store delivery until writer v2 is activated. Use existing authenticated `/api/v1/admin/projections/delivery-writer-protocol/activate`, with an actual empty private Redis backup captured before application startup, and admit only required EventStore projection POST routes. Never write the marker directly.
- Owning Parties `src/Hexalith.Parties/Extensions/PartiesServiceCollectionExtensions.cs:407` applies a broad string-enum converter to HTTP JSON. SDK `/project/v2` uses `Results.Ok(ProjectionDispatchResponse)`; Gateway expects plain Web numeric enums and silently rejects string statuses. Qualify `JsonNumberEnumConverter<ProjectionDispatchStatus>` before the broad HTTP converter. Preserve `PartiesJsonOptions.Default`, approved Contracts and Party payload enum strings; no SDK package change is required.

## Tasks & Acceptance

**Execution:**
- [x] Owning Parties `src/Hexalith.Parties/Extensions/PartiesServiceCollectionExtensions.cs` and a new `tests/Hexalith.Parties.Tests/Gateway/PartyProjectionProtocolSerializationTests.cs` — prove the real-host `Results.Ok` wire failure before fixing it; preserve numeric Completed/AlreadyCompleted, successful plain-Web Gateway deserialization and string Party payload enums, then qualify upstream integration without unrelated owner edits.
- [x] `tools/live-topology/run-isolated.py` and `tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs` — capture/verify a real empty private-store backup before applications start, then activate writer v2 through the authenticated maintenance API before vector calls. Test backup/activation failures and retain explicit private receipts.
- [x] `tools/live-topology/{live-plan.schema.json,live_plans.py,plans/}` — define strict companion plans bound to exact vector digests; cover all 21 vectors with explicit cursor/time captures, generic read barriers and audit boundary probes. Validate resolved calls through Core; reject unknown fields and weakened static assertions.
- [x] `tools/live-topology/run_live.py` — reuse existing validators and CLI adapter for one selected vector; execute declared steps once, bound read convergence, capture real values and retain result/phase diagnostics without credentials.
- [x] `tools/live-topology/run-vectors.py` — preflight the full enrolled set, launch one isolated test process per vector and require exactly one passing, unskipped selected case per child. Invalidate stale success; record complete coverage and partial failures.
- [x] `tests/Hexalith.McpCli.Integration.Tests/{LiveVectorTests.cs,LiveVectorProcess.cs,AspireTopologyFixture.cs,Hexalith.McpCli.Integration.Tests.csproj}` — expose Operation-labelled theory cases with Integration trait/MTP; enforce single-vector selection, pass discovered endpoint and short-lived identity privately to the runner, and preserve the independent smoke.
- [x] `tests/Hexalith.McpCli.AppHost/{Program.cs,appsettings.json,DaprComponents/accesscontrol.yaml}` — configure authentic bootstrap declaratively and admit only required authenticated bootstrap/projection POST routes.
- [x] `tools/live-topology/test_*.py` and `tests/Hexalith.McpCli.Manifest.Tests/{TopologyAccessControlTests.cs,TopologyConfigurationTests.cs}` — protect preflight, selection/isolation, typed binding, query deadlines, single write submission, failure receipts and topology permissions with removal-sensitive checks.
- [x] `.github/workflows/ci.yml`, `README.md`, `tools/live-topology/README.md` — extend non-live discovery to the complete vector set plus smoke; document bounded full-lane execution and skip semantics without adding Story 4.14's blocking tier.
- [x] `_bmad-output/implementation-artifacts/evidence/story-4-13/` — retain exact commands, package/vector/plan bindings, 21 live outcomes and non-live validation results.

**Acceptance Criteria:**
- Given approved Tenants and Parties vectors, when the full isolated lane completes, then all 21 execute with their prerequisite calls and persistent semantic checks, and no Command step is duplicated for parity or convergence.
- Given paged and audit vectors, when live plans resolve captured values, then non-default pages and returned cursors produce expected later contents, and category/time probes exclude nonmatching persisted events.
- Given delayed or broken effects, when bounded observations finish, then the lane fails with the Operation and assertion path rather than passing on response shape or acceptance alone.
- Given unavailable Dapr or incomplete execution, when MTP reports results, then standard prerequisite diagnostics remain visible and the full-lane receipt cannot report success.

## Implementation Notes

Implemented strict companion plans for all 21 approved vectors, the generic CLI live executor, isolated per-vector orchestration and receipts, Operation-labelled xUnit cases, authenticated bootstrap with persisted authority verification, narrow POST ACL additions, non-live guards and discovery, and documentation. Approved vector and approval bytes remain unchanged.

The user advanced root gitlinks at `8962e2f` during implementation. Preserve that selection; the exact EventStore 3.127.0 dependency closure and its test expectations were reconciled without changing the enrolled Contracts versions. The `/dev/shm` environment failure was resolved by restoring its standard mode, then the unchanged CLI suite passed 479 cases with two existing Windows skips.

The initial missing-actor diagnosis was disproved by clean-owner actual-host tests and authenticated live query dispatch. Fresh-store writer-v2 activation was the first infrastructure prerequisite. The first complete post-bootstrap lane then passed 18 vectors and failed three Parties mutations: the host's string-enum converter broke numeric projection acknowledgments. Historical attempts, including an explicitly rejected one-vector coverage bug, remain evidence and cannot grant completion.

The owner repair is committed at `d83fec24167aafd4edfc4d2f7310d6a87a218a1c` and proposed in Parties PR #58. Its real-host tests fail before the fix and pass afterward; the clean reference checkout is integrated and its server rebuild passes. The active owning repository's unrelated staged and working files were preserved. No Contracts or SDK publication was needed. A fresh complete lane against this integrated source passes all 21 vectors with zero skips. The independent parent audit proves all 53 declared Command steps have exactly one submission; actual paging/audit probes and every owned cleanup pass. Final post-review verification passes: Release warnings-as-errors build, 240 Manifest cases, CLI 479 with two Windows skips, the other non-live suites, 70 live-tool and 158 conformance Python cases, both sample conformance gates, exact 22-case discovery, a fresh 21-vector lane and final independent smoke. Its 142 phases contain exactly 53 Command submissions with distinct message IDs and 89 Query attempts. The six-row matrix audit passes. All fourteen review findings are patched; none are deferred.

The independent smoke initially exposed a startup race: liveness passed before the handler-aware route was ready, so the fallback projection actor returned 404 on an empty store. Reuse the existing bounded persisted-administrator Query barrier before its original single ListTenants request; preserve both 401 checks, the final success/document assertions and immediate failures from that final request.

Verification commands, source bindings and historical outcomes are indexed in `evidence/story-4-13/README.md`.

## Spec Change Log

- 2026-10-25: The user approved the recommended resolution of pass-3 P5: preserve Parties' existing paging contract and test offset 2 with pageSize 2. Update only the companion probes and their regression expectations, then rerun the full lane and complete build review. The prior offset-1 failure packet remains historical evidence; arbitrary-offset support is outside this continuation.

## Review Triage Log


| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B1 | high | patch: adapter handoff | `run-vectors.py` preflights `args.host`, but neither the child environment nor `LiveVectorProcess` forwards it. A custom adapter can be qualified while the default executes; forward the existing selection. |
| B2 | medium | patch: command envelope | Reproduced `observe()` accepting the approved Parties command without `aggregateId`. Its original vector asserts only accepted status, so check the generic expected Gateway aggregate identity as well. |
| B3 | medium | patch: per-call identity | The command path validates ULID syntax and correlation but retains no cross-phase message-ID set. The two declared deactivate calls can return the same ID while state assertions remain true; require fresh IDs within the vector. |
| B4 | medium | patch: progress receipts | `main()` writes an empty pending receipt, then only its final block persists the in-memory phases. The outer hard kill can bypass that block, losing already completed submissions; persist sanitized progress and mark ordinary failed phases explicitly. |
| B5 | low | patch: assertion selector | Reproduced `index: 6.0` passing JSON Schema and raising an unlocated list-index TypeError. Require an integer JSON token before indexing and retain the action location. |
| B6 | medium | patch: persisted barrier | Reproduced all command barriers reduced to `/operation` assertions passing `load_plan()`. Those checks cannot observe persisted content; reject this demonstrated non-persistent barrier without interpreting module data in the runner. |
| B7 | low | patch: RESP framing | The new backup code compares one `recv()` with a complete RESP line, although TCP can split it. Read the short complete response before comparison; a fragmented reply must not reject a healthy private store. |
| B8 | medium | patch: filter observations | List/search each seed one matching party; ignoring the supplied predicates can produce the same original result. Add nonmatching read observations for the declared filters without extra Commands or vector edits. |
| B9 | medium | patch: update observations | LastName is explicitly supplied, rather than omitted, but neither update observation checks it; unchanged type and channel identity/type/preference are also unasserted. Clearing these fields can preserve every current assertion. Add the contract-defined preservation/content assertions. |
| B10 | medium | patch: preflight wiring tests | Existing live-tool tests exercise helper functions or replace `preflight()` wholesale. They do not fail if this new preflight stops invoking artifact/inventory/Core validators; add actual preflight rejection tests at those delegation boundaries. |
| E1 | high | patch: adapter handoff (B1) | Independently confirms the same existing `--host` value is absent from the child and C# handoff. Same defect as B1, retained as a separate reviewed claim. |
| E2 | high | patch: executable dependencies | The closure check reads the source project's assets, while host verification checks only the enrolled Contracts artifacts. A cached older Gateway.Client can replace the adapter DLL without either check noticing; verify the adapter dependency identities and actual private runtime bytes against the restored production closure. |
| E3 | medium | patch: binding handoff | Parent and child take separate snapshots; their hashes are compared only after the child has executed. A valid changed plan can submit vector Commands before the mismatch fails. Require the parent's expected bindings before `execute()`. |
| V1 | high | patch: orchestration cardinality | The verification-gap layer demonstrated all 52 tests passing with `execute()` replaced by an immediate failure. A skipped already-inactive deactivate invocation can leave business assertions true, and consumers accept a receipt without phases. Exercise the executor boundary and enforce declared phase/Command-attempt coverage in lane acceptance. |

All fourteen findings were graded before grouping. B1/E1 share the same adapter-handoff defect; the other roots remain separate. Each smallest fix is an internal correction or test/plan observation, adds no public surface, and addresses demonstrated state. No intent or specification loopback is required. No finding is deferred.

**Completion:** All patch groups are implemented and covered by the 70-case Python and 240-case Manifest runs, including actual C# child handoff, genuine stale DLL rejection, preflight delegation, executor cardinality and hard-termination progress. The final complete live generation `a45347517d3446de80684c5b084ca366` passes all 21 vectors and the added filter/update observations; the separate final smoke also passes. Parent receipt/phase/binding/cleanup audits pass.

The later committed-code review patches P1–P14 are complete. The persisted
administrator predicate is now protected by three real-client Manifest cases,
including its actual 60-second deadline, and a compiled weakened-predicate
mutation fails. The complete offline preflight now runs in the existing CI
venv; every missing plan/identity/entry/selector guard has focused coverage.
Writer-bootstrap validation precedes a passing vector receipt and a successful
preflight-only run prints its summary. The private URL guard also refuses empty
userinfo, and the identity declares `command:submit`. Documentation corrections
cover idempotent steps, exact ACL routes, the 3.127.0 fixture packages,
companion-plan enrollment and Python 3.11.

The fresh full lane `7370f00a1b6b4b4d8a576175a650c257` qualifies the current
user-selected Parties `559b91c8` and EventStore `6ca1b4cb` source checkouts:
21 passed, zero failures/skips, 142 phases, exactly 53 Command submissions with
53 distinct message IDs and 89 Query attempts. Its independent binding,
assertion, cursor/time, genesis-backup and cleanup audit passes, as does the
separate final smoke. Fresh restore, Release warnings-as-errors build, all six
non-live .NET suites (243 Manifest cases), 81 live-tool and 158 conformance
Python cases, exact 22-case discovery, complete offline preflight and all three
source-server builds pass. All 24 targeted Python mutations are detected.
Evidence and exact commands: `evidence/story-4-13/review-patches-20261025/`.

### Resumed build review (2026-10-25)

All three required layers completed against the full baseline diff. Each finding was graded before grouping; seven claims survive as six internal patch groups. No intent/specification loopback or deferral is required.

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| R2-B1 | low | reject | RID omission is reproducible with a synthetic Linux runtime dependency. The exact approved production closure has only Windows EventLog RID assets; the supported Linux lane has no active RID DLL to omit. Adding active-RID selection/guards addresses no current runtime failure and adds complexity. |
| R2-B2 | low | reject | `require_phases` checks phase identity and submission cardinality. Its sole production writer, `execute`/`observe`, records and verifies the actual documents before marking a phase passed; the demonstrated receipt requires external fabrication or replacing that writer. Revalidating every document in the consumer duplicates that boundary for an unlikely malformed-receipt case. |
| R2-B3 | low | reject | carried: checkout commit versus deployed bytes was already triaged under the 2026-10-25 code review. This private activation receipt records the cutover source; current qualification separately hashes every actual server assembly and checks the selected source commits. Adding runtime dirty-tree/provenance guards remains unnecessary complexity for this recorded private lane. |
| R2-B4 | low | reject | `fromisoformat` accepts a space-separated timestamp, but real captures come from the Gateway's typed timestamp serializer and retain timezone/type checks. No production capture with the proposed syntax was shown; another parser guard would add complexity without an observed failure. |
| R2-B5 | medium | patch: create observation | The create vector and its read barrier omit supplied last name, enum/preference fields and collection counts. Changing those persisted values still passes the present assertions. Add companion content assertions without changing approved vector bytes. |
| R2-B6 | low | patch: CI evidence | The new complete preflight writes its receipts to runner temp, and this job has no artifact upload. Retain that existing directory with the repository's pinned upload action and `always()` so failures remain diagnosable. |
| R2-B7 | low | patch: adapter diagnostics | `validate_call` discards exit/stdout/stderr on invalid JSON and omits stderr on a failed valid response. Preserve the failed command and sanitized process diagnostics in the existing internal failure message and test the boundary. |
| R2-B8 | low | reject | carried: non-atomic `live-lane.json` writes were already triaged in the code-review rejected list. A kill during the small write produces an unparsable receipt that fails closed; atomic receipt hardening is extra complexity for that unlikely window. |
| R2-B9 | medium | patch: writer deadline | Persistent readiness 503s never appear in the current writer-bootstrap tests; deleting the 30-second aggregate deadline leaves them green. Protect the shipped timeout and caller cancellation, exactly one activation, and absence of a success receipt. |
| R2-B10 | medium | patch: process failures | The actual C# handoff test covers success only. Add child fixtures that protect nonzero exit, missing receipt, wrong Operation and failed result, including stale receipt invalidation and credential-safe diagnostics. |
| R2-E1 | medium | patch: timeout paths | Repeated Gateway 404s for an unpersisted entity never reach a document assertion, so `observe` times out with the Operation/phase but no declared assertion path. Include those paths in the existing read-deadline diagnostic and test the absent-document case. |
| R2-V1 | medium | patch: writer deadline (R2-B9) | Pre-verified regression gap: perpetual readiness 503s escape only through the untested 30-second cancellation and otherwise consume the wrapper's 900-second bound. Same missing timeout test as R2-B9. |

**Final resumed-build verification:** All six follow-up groups above are fixed and protected by focused tests. Fresh parent verification passes the Release warnings-as-errors build, all six non-live .NET suites (1,529 passed; five existing skips), 249 Manifest cases, 85 live-tool and 158 conformance Python cases, complete offline preflight and exact 22-case discovery. The final generation `f072ccf25ff44237a3e7c3e7a63f485e` passes all 21 vectors with zero skips; independent audits prove 142 phases, 53 unique single Command submissions, real cursor/time bindings and all cleanup. The separate smoke and six-row matrix audit pass. Final commands, source/binary bindings and sanitized receipts are in `evidence/story-4-13/build-resume-final-20261025/README.md`. No findings are deferred.

### Final review after approved paging clarification (2026-10-25)

The blind review returned ten claims; edge-case and verification-gap reviewers returned no findings. Each claim was graded before grouping. The parent independently rechecked the passing 21-vector receipt, all 144 phases, 53 unique single Command submissions, all bindings/assertions/cleanup, and every matrix test name against its passing output.

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| R3-B1 | medium | patch: archive preservation | `pass-3-final-20261025/retain-evidence.py:29` reopens the input archive with `w:gz` after deleting its originals. A rerun would replace it with an empty archive. Refuse pre-existing archives before copying or deleting anything, and prove refusal preserves retained hashes. |
| R3-B2 | low | reject | carried: R2-B8 and the earlier code review already rejected atomic public-receipt writes. The code is unchanged; a kill during a small write fails closed, and adding another atomic-write path addresses an unlikely window. |
| R3-B3 | low | reject | Two simultaneous callers deliberately sharing one `--output` can overwrite its latest public receipt. Individual generations remain separate and each command reports its own exit/result. Output-directory locking or a new receipt surface adds complexity for this unusual operator collision. |
| R3-B4 | false | reject | The failed outcome points to its child output directory, whose `child.stdout.txt` retains the exact isolated runtime path before startup. Both real failed cases were located and retained using that output; diagnostics and cleanup locations are not lost when `isolatedReceipt` is absent from the success-only fields. |
| R3-B5 | low | reject | `HeadProcess.cli` does omit stderr for valid JSON, but the shipped calls use JSON output and their expected failures carry complete error documents with empty stderr. No missing real diagnostic was demonstrated. Extending the shared adapter return/receipt contract adds complexity for a hypothetical auxiliary diagnostic. |
| R3-B6 | low | reject | carried: the prior code review rejected binding local executable DLLs against an overlapping rebuild. No code at that boundary changed. This qualification separately checks all 507 runtime DLL hashes; adding a new per-child binding addresses an uncommon rebuild during a lane. |
| R3-B7 | low | reject | The second-page probes assert the approved goal's items, total count and offset; retained live results also show correct page size/page/hasMore. A metadata-only mutant could evade these particular assertions, but no incorrect producer was demonstrated. Additional guards for every optional returned field add coverage beyond the approved probe without resolving a present failure. |
| R3-B8 | maybe-false | reject | No implementation that empties all populated later pages was demonstrated. The approved Parties vector contains one matching item, and the user explicitly chose its supported second-page boundary; Tenants separately proves populated continuation contents. Assessing the proposed module defect needs a separately approved populated Parties fixture, adding Commands and scope to the preserved vectors (low if true here). |
| R3-B9 | low | patch: nonretry coverage | The focused runner suite protects 401/403 but not the individual 400 or non-Gateway refusal branches. The actual offset-1 run demonstrates a reachable 400, and removing that category would delay its refusal. Extend the existing test to assert the exact diagnostic and one attempt for each category. |
| R3-B10 | low | patch: audit prerequisites documentation | The one-off paging/reuse scripts bind the recorded checkout/runtime paths; the reuse audit also requires the original built DLLs, which are intentionally not shipped in the packet. Clarify these prerequisites and identify the explicit-path retained-result audit, rather than adding a new portable audit API. |

Three small patch groups survive: archive preservation, focused nonretry tests, and evidence documentation. No execution/plan change, intent loopback or deferral is required.

**Final review completion:** All three patch groups are complete. The parent reran all 88 live-tool tests successfully and independently verified all live assertions/bindings/cleanup, both packet indexes, all archive members and 507 unchanged runtime DLLs. The only post-qualification source change is the expanded nonretry test; execution code and plans retain the passing 21-vector qualification. No findings are deferred. Parent evidence: `evidence/story-4-13/pass-3-parent-review-20261025/`.

## Design Notes

The original implementation choices and pass-3 P5 are resolved. The user approved preserving Parties' existing paging contract and testing offset 2 with page size 2. The McpCli footprint is test tooling, topology configuration and documentation, plus the qualified upstream host protocol repair and reference integration. The historical owner packet records Parties PR #58 and its independently reproduced baseline CI failures; the current user-selected squash-merge checkout is qualified by the new review-patch packet above.

Fresh state per vector preserves fixed Parties identifiers and exact Tenants index counts. Companion plans leave v1 schema, owner approval receipts and vector bytes intact. They close the existing dynamic-value handoff at `deferred-work.md:513`; they cannot silently discard business assertions. Infrastructure bootstrap uses the existing server-owned path, while vector setup remains generic Operation calls.

## Verification

- `dotnet restore Hexalith.McpCli.slnx`, then `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`.
- Run each existing non-live test project separately; run Python suites under `tools/live-topology` and `tools/conformance-vectors/v1`, plus exact MTP discovery.
- Build the three root source servers using the documented Story 4.12 commands; bootstrap private binaries and run `run-vectors.py` with outer and per-child deadlines. Require 21 passed vectors, zero failures/skips and owned cleanup.

### Review Findings (code review, 2026-10-25)

Code review 2026-10-25 of the committed story range `aabc03c..7f503ae` (`8962e2f`, `7f503ae`), plus the owning Parties fix `d83fec24`.

- **Code-only scope:** excludes `_bmad-output/` and `references/`. 59 files, +5,142/−39, 5,801 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 46 normalized findings (BH 18, EC 11, VG 7, AA 10). 19 survive as 14 patch entries; 27 are rejected. No decision is needed, and nothing is deferred.

Parent checks during triage:
- EventStore lets global administrators skip the permission, domain and tenant checks (`ClaimsRbacValidator.cs:35-37`, `ClaimsTenantValidator.cs:23`). Commands require `command:submit` or `commands:*` (`AuthorizationConstants.cs:4-5`).
- The Parties vector `deactivate-party` declares two identical `parties.deactivate-party` Command steps on `party-story49`: the prerequisite at `/prerequisites/1` and the `/invocation`.
- Every Manifest test child that reads `MCPCLI_ISOLATED_TOPOLOGY` sets it explicitly (`DaprPrerequisiteTests.cs:81`, `TopologyFixtureLaunchTests.cs:38`, `TopologyLaunchTests.cs:442`). Only `ProjectionWriterBootstrap.ActivateAsync` reads `MCPCLI_LIVE_OUTPUT`.
- No isolated child in the story evidence exceeded 54.3 s `commandElapsedSeconds`; the wrapper bound is 900 s.
- `datetime.fromisoformat` accepts the 7-digit fractional audit timestamps on Python 3.11 and later (checked on 3.14.4). Earlier versions reject them, and no README states a minimum Python version.
- `6043ca8` was committed during this review. It moves only gitlinks: Parties goes from `d83fec24`, a PR #58 branch commit, to the squash merge `559b91c8` on Parties main. Builds goes from `1783c0a` to `e171c5a`, with no change to `Props/Directory.Packages.props`. The live evidence remains bound to `d83fec24`, and `d83fec24` and `559b91c8` differ in 82 files.

- [x] [Review][Patch] P1 — medium. The persisted-administrator barrier has no test that fails when it is removed. [tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:106]
  - `RequireAdministratorAuthorityAsync` gates every vector and the smoke, but only live callers reach it. Replacing its predicate with `result.Payload is not null` leaves every non-live test green. A live run would then fail only intermittently, as Commands race the bootstrap (VG, BH, AA).
  - Fix: move the polling into a static helper that takes an `HttpClient`, like `ProjectionWriterBootstrap`, and link it into Manifest.Tests. Using `ProjectionWriterBootstrapHandler`, test three cases: a document without the administrator keeps polling; one with the administrator returns; a run that never sees it throws the exact `TimeoutException` message.
- [x] [Review][Patch] P2 — medium. CI never runs the complete preflight, so 18 of the 21 plans pass Core validation only in the manual live lane. [.github/workflows/ci.yml:125]
  - VG added an unknown payload property to a `tenants.get-tenant-audit` observation. `load_plan` and every CI test accepted it; `validate_call` rejects it. VG ran `run-vectors.py --preflight-only` locally with no topology, and it exited 0 (VG).
  - Fix: add `python3 tools/live-topology/run-vectors.py --output "$RUNNER_TEMP/live-preflight" --preflight-only` to the `topology-vector-discovery` job after its build, inside the existing venv.
- [x] [Review][Patch] P3 — medium. Seven `load_plan` binding guards have no failing test. [tools/live-topology/live_plans.py:125]
  - The guards: duplicate binding target, cursor bound to a capture not from `/paging/nextCursor`, time binding without a timestamp capture, step binding over non-`scripted-` input, duplicate capture name, duplicate assertion index, and capture tuple mismatch.
  - VG removed all seven, and the suite stayed green. Dropping the `/paging/nextCursor` check would let any returned string feed the continuation cursor (VG).
  - Fix: add one `reject(...)` case per guard in `test_live_plans.py`, based on `tenants.get-tenant-users` and `tenants.get-tenant-audit`.
- [x] [Review][Patch] P4 — medium. The checks in `observe()` on the returned document's identity are untested. [tools/live-topology/run_live.py:40]
  - No test fails when these are removed: the `/operation` and `/tenant` match, the required query `/document`, the Command ULID format, and the `correlationId` default. For Parties Commands and plan observations, these checks are the only tenant check (VG).
  - Fix: add `RunnerTests` cases for a mismatched tenant or operation, a query without `document`, a non-ULID `messageId` and a mismatched `correlationId`. Each should raise `VectorError` after exactly one CLI call.
- [x] [Review][Patch] P5 — medium. The live entry guards are untested. [tools/live-topology/run_live.py:149]
  - Removing any of these leaves every test green: the `MCPCLI_ISOLATED_TOPOLOGY=1` requirement, the loopback-http-only endpoint with no userinfo, query or fragment, the non-empty token, and the `--child-timeout` range in `run-vectors.py:95`. Without the hostname check, admin-token Commands could go to any URL (VG).
  - Fix: add a table test in `test_live_runner.py` for each refused environment. It should assert exit 1, a `failed` receipt, and that neither `preflight` nor `execute` is called. Add a `test_lane.py` case for `--child-timeout 961` that starts no child.
- [x] [Review][Patch] P6 — medium. Nothing ties the parent's child command to `LiveVectorSelection.Require`. [tools/live-topology/run-vectors.py:117]
  - `LiveVectorSelectionTests.MatchingProcessSelectionIsAccepted` claims to use "the actual parent command form" but builds its own list. `test_lane.py` checks only `Operation=<op>` and `run-isolated.py`. Adding a second `-trait` or renaming the `-class` value keeps every test green but breaks every live child (VG).
  - Fix: in `test_failed_children_keep_all_operation_outcomes_and_exact_selectors`, assert there is exactly one `-trait` and that the token after `-class` is `Hexalith.McpCli.Integration.Tests.LiveVectorTests`.
- [x] [Review][Patch] P7 — low. A vector is marked `passed` before its writer-bootstrap binding is checked. [tools/live-topology/run-vectors.py:150]
  - `outcome.update(result='passed', …)` runs before `writer-bootstrap.json` is validated. A SIGTERM between the two raises `SystemExit`, which `except Exception` does not catch, so the saved receipt lists that vector as passed (BH, EC).
  - Fix: move the `outcome.update(result='passed', …)` call after the bootstrap check.
- [x] [Review][Patch] P8 — low. A successful `--preflight-only` run prints nothing. [tools/live-topology/run-vectors.py:109]
  - `return 0` inside the `try` skips the summary `print` after `finally`, so the documented diagnostic command prints no stdout result (VG).
  - Fix: let the preflight-only path fall through to the existing summary instead of returning early.
- [x] [Review][Patch] P9 — low. The live identity declares `command:write`, which is not an EventStore permission. [tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:150]
  - EventStore accepts only `command:submit` or `commands:*` for Commands. The identity is authorized only because `global_admin` bypasses the permission check, so the declared write scope has no effect. Without that bypass, every vector Command would be denied (AA).
  - Fix: declare `command:submit`, which EventStore's own local token also uses (`LocalAuthenticationTokenCommand.cs:96`).
- [x] [Review][Patch] P10 — low. The docs claim every Command's read barrier observes a persisted change. Repeated idempotent Commands cannot show one. [tools/live-topology/README.md:113]
  - The approved `deactivate-party` vector deactivates the same party twice. `persisted-invocation` asserts the same `isActive: false` that `persisted-prerequisites-1` already proved, so it passes whatever the second Command did. `require_phases` proves one accepted submission, but no state change (BH, AA, EC).
  - A generic "barrier value must change" guard would reject this approved vector.
  - Fix (wording only): in the lane README and `README.md:268`, say that a repeated idempotent Command step is proven by its single accepted submission plus unchanged persisted state, not by a new effect.
- [x] [Review][Patch] P11 — low. The lane README misstates the ACL entries. [tools/live-topology/README.md:97]
  - "POST `/project` from EventStore (including `/project/v2`)" reads as one prefix rule. `accesscontrol.yaml` and `TopologyAccessControlTests` declare two exact entries (AA).
  - Fix (wording only): "POST `/project` and `/project/v2` from EventStore".
- [x] [Review][Patch] P12 — low. The README still gives the platform fixture's EventStore server packages as 3.126.1. [README.md:97]
  - This change pins `.Server`, `.DomainService` and `.ServiceDefaults` at 3.127.0 in `DependencyPolicyTests` and `tools/dependency-policy.json`, but leaves the README sentence unchanged (BH).
  - Fix: change it to 3.127.0.
- [x] [Review][Patch] P13 — low. The enrollment docs omit the new companion-plan requirement. [README.md:122]
  - Preflight refuses a vector without `tools/live-topology/plans/<operation>.json` ("Live plan inventory differs"). CI discovery now compares cases with the vector files and pins 21. The enrollment paragraph mentions neither, and further domain modules are planned (BH).
  - Fix: add one sentence. Each approved vector needs a strict companion plan, and the v1 count pins in `ci.yml` and `test_live_plans.py` change with v1 scope.
- [x] [Review][Patch] P14 — low. The lane needs Python 3.11 or later, which is not documented. [tools/live-topology/README.md:71]
  - `live_plans.timestamp()` uses `datetime.fromisoformat`, which rejects the Gateway's 7-digit fractional audit timestamps before Python 3.11. On older interpreters the audit captures fail as "Invalid timestamp" (BH).
  - Fix: state the Python 3.11 minimum in the lane README.

#### Rejected (code review, 2026-10-25)

- `low` — `LiveVectorProcess` starts `python3` from `PATH`, while the parent uses `sys.executable` (BH). With the documented commands both resolve to the same interpreter, and a missing `jsonschema` fails loudly at import. The fix adds an environment parameter.
- `low` — The nested time bounds (360 s startup + 60 s + 40 s + 480 s runner) exceed the wrapper's 900 s, and the 8-minute runner deadline throws without stdout (BH, AA, EC). Observed children take at most 54 s. A kill fails closed, `run-vectors.py` names the Operation, and `live-result.json` keeps the phase progress. No single constant makes every bound nest (the audit plan's worst case is about 615 s), so the fix means restructuring the shared 4.12 wrapper bound.
- `low` — `ActivateAsync` reports a readiness timeout as a bare `TaskCanceledException`, and a malformed 200 body as `KeyNotFoundException` or `JsonException` (BH). These fail loudly on states never observed, and the fix adds guard branches.
- `false` — A non-object payload or an item without `userId` escapes the authority retry loop (EC; the BH sub-claim is merged into P1). Before readiness the Gateway answers 404, which is caught as `EventStoreGatewayException`. An immediate loud failure on a malformed document is correct.
- `low` — `cutoverCommit` comes from `git rev-parse` of the checkout, not the deployed bytes, and a dirty tree goes unnoticed (BH, EC). It only records the activation in a disposable private store. Adding a dirty-tree guard is a new branch.
- `false` — Writer activation cites a stale genesis backup, and in-flight bootstrap deliveries break the quiescence attestation (BH, EC). Capturing the backup before application startup is the spec's Code Map decision. The authority barrier (`LiveVectorTests.cs:36`) runs before activation (`:37`) and proves that the only writer's projected effect has already landed, and no other application writes in the private namespace.
- `false` — `ProjectionWriterBootstrapTests` changes process-wide variables that parallel tests inherit (BH). No other reader exists (see the parent checks).
- `maybe-false` (low if true) — The AppHost's token-parameter check depends on the helper's parameter name and its fallback branch is dead (BH). Versions are pinned exactly, and a helper bump already reruns `TopologyLaunchTests`. Settling it would need a helper that renames the parameter.
- `false` — The Parties fix pins only `ProjectionDispatchStatus`, and its test calls `Results.Ok` directly (BH). The passing lane exercises every endpoint the Gateway calls on the Parties host (`/process`, `/query`, `/project/v2`). The spec's task 1 asks for proof at the real-host `Results.Ok` level. The other gitlink commits are the user's own sync.
- `false` — `aspire.config.json` lacks a final newline and sits outside the Code Map (BH, AA). It arrived in the user's sync commit `8962e2f`, not the story commit, and no tool or CI check reads its trailing newline. Adding ConformanceHost to `Hexalith.McpCli.slnx` lets the documented solution build produce the default `--host` adapter.
- `low` — `observe()` retries deterministic failures and ignores `retryable` until the 45 s deadline, and may check a stale `document` (BH). A stale document can only be a non-terminal earlier result, because a terminal one would already have raised. Retrying only delays a failure that still fails closed with its last error. The fix adds classification branches.
- `maybe-false` (low if true) — The ACL admits v1 `/project` as well as `/project/v2` without proof that v1 is needed (BH). To settle it, remove `/project` and rerun the lane. Default deny still governs every other route.
- `low` — `ValidateBootstrap` has no test for a non-boolean flag (BH). `GetValue<bool>` throws `InvalidOperationException`, which the existing diagnostic boundary already catches, and nobody passes non-boolean values in practice.
- `false` — The EventStore policy bump (3.127.0) landed in a later commit than the Builds gitlink move (AA). `HEAD` is consistent, and both commits are already pushed.
- `false` — The integrated Parties commit is not on Parties main (AA). This is superseded: `6043ca8` moved the gitlink to `559b91c8`. The evidence binding to `d83fec24` is noted in the parent checks.
- `false` — The Acceptance Auditor's ruled-out 15 s HTTP timeout and its six-row matrix confirmation (AA). The auditor reported both as non-defects.
- `low` — `run_live` does not hash the adapter DLL and project assemblies, so a rebuild between parent and child goes unnoticed (EC). That requires rebuilding the checkout during a lane run. The child re-runs the package, artifact and Catalog preflight, and the fix adds a new binding key.
- `false` — Live JWT tenants and domains are hard-coded, so a vector with another tenant would get 403 (EC). Global administrators bypass tenant and domain validation (see the parent checks).
- `false` — `LiveVectorSelection.Require` runs only after the collection fixture has started the topology (EC). It still runs before any vector Command (`LiveVectorTests.cs:33` precedes `:36-41`), and the fixture refuses a non-isolated environment (`AspireTopologyFixture.cs:43`), so only private disposable state is touched.
- `low` — `live-lane.json` is not written atomically (EC). Truncation needs a SIGKILL during a sub-millisecond write after the TERM-path save, and an unparseable receipt fails closed.
- `false` — "Endpoint and identity travel privately" is contradicted by the CLI's `--url` argument (EC). The sentence describes the C#-to-runner handoff, which uses environment variables (`LiveVectorProcess.cs:21-22`). The `--url` value is a non-secret loopback address inside the private PID namespace, and the token stays in `EVENTSTORE_TOKEN`.

### Review Findings (code review pass 3, 2026-10-25)

Code review 2026-10-25 of the committed story range `aabc03c..0d0ca22` (`8962e2f`, `7f503ae`, `6043ca8`, `4b60d49`, `0d0ca22`).

- **Code-only scope:** excludes `_bmad-output/` and `references/`. 59 files, +5,591/−41, 6,250 diff lines, full mode, with `epic-4-context.md` as context. The Parties fix reviewed in pass 1 (`d83fec24`, now the squash merge `559b91c8`) is outside this diff.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 32 normalized findings (BH 15, EC 8, VG 5, AA 4). 9 survive as 9 patch entries; 23 are rejected. No decision is needed, and nothing is deferred.

Parent checks during triage:
- `main` has no branch protection or rulesets (`gh api repos/{owner}/{repo}/branches/main/protection` returns 404 "Branch not protected"; `rules/branches/main` returns `[]`), so renaming the CI job cannot orphan a required check.
- No approved vector step expects an error: none has a `scriptedResponse.statusCode` of 400 or more, or an `/error` assertion.
- The pinned 3.127.0 helper calls `WithGeneratedEventStoreAppChannelToken()` for the Gateway only when `ExecutionContext.IsRunMode` (`src/Hexalith.EventStore.Aspire/HexalithEventStoreExtensions.cs:273-276` at tag `v3.127.0`). Live runs and `--Topology:InspectComposition` both build in run mode.
- Only the `tenants.remove-user-from-tenant` `/invocation` barrier has no positive document assertion (`/document/items arrayLength 0`). Its previous barrier proved the user present, so it still observes a real change.
- Final evidence timings (`evidence/story-4-13/build-resume-final-20261025/commands.json`): Manifest.Tests 61.6 s, complete preflight 34.9 s, full 21-vector lane 876 s.
- Each of the eight `preflight()` refusals AA4 names duplicates a later check: strict module/operation discovery, `validate_call`, plan loading or CI discovery. `run-isolated.py:230` independently refuses a missing `MCPCLI_ISOLATED_RUNTIME_DIR`.

- [x] [Review][Patch] P1 — medium. The authority barrier's retry on Gateway errors has no test. [tests/Hexalith.McpCli.Integration.Tests/AdministratorAuthorityBootstrap.cs:38]
  - All three `AdministratorAuthorityBootstrapTests` reply HTTP 200 with `success: true`. Deleting or narrowing the `EventStoreGatewayException` catch keeps them green. A single readiness 404/503 would then abort the smoke and every vector, which is the startup race this barrier was added for (VG).
  - Fix: using `ProjectionWriterBootstrapHandler`, answer 503 first and the administrator document second; assert two calls and success. Add a deadline variant that asserts the "Privileged query HTTP 503." text in the `TimeoutException` message.
- [x] [Review][Patch] P2 — medium. The `writer-bootstrap.json` contract between C# and Python is never pinned. [tests/Hexalith.McpCli.Integration.Tests/ProjectionWriterBootstrap.cs:56]
  - `run-vectors.py:149-155` rebuilds `sha256:<sha256>;file:<backupFile>` from the wrapper receipt and requires an exact match and a 40-character `sourceCommit`. The C# test compares the request body only with `VerifyBackup`'s own output (`ProjectionWriterBootstrapTests.cs:39`), and asserts only `result`, `activationCount` and `readinessObserved` in the receipt. `test_lane.py` hand-writes both files. Changing the separator, or dropping either field, leaves every test green and fails all 21 live children (VG).
  - Fix: in `ActivationIsSubmittedOnceAndReadinessOnlyPolls`, assert that the receipt's `backupReference` equals `"sha256:" + <receipt sha256> + ";file:" + <full backupFile path>`, built from the test's own receipt values, and that `sourceCommit` equals the submitted commit.
- [x] [Review][Patch] P3 — medium. No test drives `run_live.main` to a passing receipt. [tools/live-topology/run_live.py:162]
  - Every `main` test ends in a failure or a kill. VG turned `report['binding'] = …` into a local that is still compared but no longer stored, and all 19 `test_live_runner.py` tests passed. Every live child would then fail the lane's "missing, stale or unsuccessful semantic receipt" check (VG).
  - Fix: add a `RunnerTests` case that patches `preflight` (binding matching `MCPCLI_LIVE_BINDING`) and `execute` (appending passing phases). Assert exit 0 and the receipt's `operation`, `result: passed`, `binding` and phases.
- [x] [Review][Patch] P4 — medium. Nothing protects `fullLiveAccepted: false` for a selected subset. [tools/live-topology/run-vectors.py:162]
  - The only success test runs one vector against a one-operation coverage list, so a subset and the complete set look the same. VG changed the expression to `failed == 0 and passed == len(report['vectors'])`, and all 11 `test_lane.py` tests passed. A single-vector diagnostic would then write `result: passed` and `fullLiveAccepted: true`, against AC4 (VG).
  - Fix: add a `LaneTests` case with two covered operations, `--operation` naming the second, and a passing child. Assert exit 0, exactly one child selected with `Operation=<second>`, `result: partial` and `fullLiveAccepted: false`.
- [x] [Review][Patch] P5 — medium. Parties list and search never observe a non-first page. [tools/live-topology/plans/parties.list-parties.json:58]
  - Both vectors seed one party and use `pageSize: 2, offset: 0`. Every added probe also uses `offset: 0` (`parties.list-parties.json:58,93,128`; `parties.search-parties.json:58,93,128`). A server that ignores the Envelope offset passes every Parties assertion, so AC2's "non-default pages … produce expected later contents" is unproven for Parties (AA).
  - Fix (user-approved clarification, 2026-10-25): add one Query probe to each plan, with the invocation's own filters and Envelope `offset: 2, pageSize: 2`. Assert `/document/items arrayLength 0`, `/document/totalCount equals 1`, `/paging/offset equals 2` and `/paging/totalCount equals 1`. This is the supported second-page boundary under Parties' existing page-aligned offset contract. No Command, approved vector, dependency or upstream changes; requalify with a fresh complete lane.
- [x] [Review][Patch] P6 — low. A failed live vector reports neither its phase nor its assertion path outside the nested receipt. [tools/live-topology/run_live.py:176]
  - `run_live` prints only `FAILED <op>; receipt: <path>`, and that is all `LiveVectorProcess` puts in the xUnit failure and therefore in `tests.xml`. `live-lane.json` says only "isolated child exited 1; see <output>". The phase and paths exist only in `<generation>/<op>/live-result.json` (AC3; I/O row "Semantic mismatch") (AA).
  - Fix: on failure, also print the token-redacted `report['error']`, which already names the phase, the Operation and the declared assertion paths. Assert it in an existing failing `main` test.
- [x] [Review][Patch] P7 — low. `--operation ""` runs the complete lane. [tools/live-topology/run-vectors.py:100]
  - `if args.operation:` treats an empty selector, for example from an unset shell variable, as no selector. The diagnostic then starts all 21 vectors instead of refusing (EC).
  - Fix: use `if args.operation is not None:`, and add a `test_lane.py` case that asserts the refusal and that no child starts.
- [x] [Review][Patch] P8 — low. A missing `MCPCLI_ISOLATED_RUNTIME_DIR` is refused only after the full preflight. [tools/live-topology/run-vectors.py:109]
  - The check runs after the preflight, which took 34.9 s in the final evidence, whereas `--child-timeout` is validated first (BH).
  - Fix: for runs without `--preflight-only`, move the check before `preflight()`, next to the child-timeout check, and assert that preflight is not called.
- [x] [Review][Patch] P9 — low. The AppHost's app-channel comment gives the wrong reason for the fallback. [tests/Hexalith.McpCli.AppHost/Program.cs:83]
  - The comment attributes the branch to "earlier approved helpers". The pinned 3.127.0 helper provisions `eventstore-app-api-token` only in run mode (see the parent checks), and every supported path is run mode. The fallback can therefore run only outside run mode, where the helper deliberately leaves the token to the deployment (BH).
  - Fix (wording only): say that the pinned helper provisions the Gateway token in run mode, and the explicit wiring applies only when it has not.

**Historical offset-1 qualification (2026-10-25):** P1–P4 and P6–P9 are implemented and verified. The initial P5 companion probes (`offset: 1`, `pageSize: 2`, original filters) were implemented but remained unqualified. Fresh full generation `f326d72cd5224ea48852c8f3ac1f8be6` executes all 21 vectors with 19 passes, two failures and zero skips. Only `parties.list-parties` and `parties.search-parties` fail, both at `offset-after-only-match` with Gateway HTTP 400 `query_invalid_page` ("The supplied cursor is invalid."). The receipt correctly retains `fullLiveAccepted: false`.

The selected Parties owner commit `559b91c812a422f9890e448f7942e645f3739b2b` explicitly rejects offsets not divisible by page size at `references/Hexalith.Parties/src/Hexalith.Parties/Queries/PartySdkQueryService.cs:665`. Its existing `PublicPaging_RejectsInvalidBoundsCursorAndOffsetBeforeReadAsync` test pins these exact list/search inputs at `references/Hexalith.Parties/tests/Hexalith.Parties.Tests/Gateway/PartySdkQueryHandlerTests.cs:2730` and `:2733`, and asserts rejection before reads at `:2741`–`:2745`. Changing only the guard would also be insufficient: list/search currently convert offsets to page numbers before invoking their paged providers. The user subsequently resolved this demonstrated contract conflict by approving the supported next-page probe (`offset: 2`, `pageSize: 2`), as recorded in the Spec Change Log. The historical failure packet remains preserved; approved vectors, Contracts, dependencies and reference checkouts remain unchanged.

Fresh verification passes restore, Release warnings-as-errors build, all three source-server builds, all six non-live .NET suites (1,531 passed, five existing skips; 251 Manifest cases), 88 live-tool and 158 conformance Python tests, complete offline preflight and exact 22-case discovery. Five focused Python mutations are detected. The independent smoke passes with zero skips. The full-run audit verifies all 144 declared phases, exactly 53 single Command submissions with distinct IDs, the successful static/cursor/time assertions, the two precise paging refusals and all 22 private topology cleanups. Exact commands, source/binary bindings, failure receipts and owner anchors are retained in `evidence/story-4-13/pass-3-patches-20261025/README.md`. No failing live result is presented as full acceptance.

**Final pass-3 qualification after user approval (2026-10-25):** All nine patches are implemented and verified. Generation `2ee4b89b49db4c22b0ea4965a302bb19` passes all 21 vectors with zero failures/skips and `fullLiveAccepted: true`. Its independent audit proves 144 phases, exactly 53 single Command submissions with distinct IDs, 91 Query attempts, real cursor/time bindings, every original/additional assertion and all 21 private cleanups. Both Parties probes preserve the invocation filters, return empty second pages at offset 2/pageSize 2, and retain totalCount 1. Fresh 88-case live-tool tests, complete offline preflight and the six-row matrix audit pass. Exact hashes prove the existing .NET/source-build, conformance, discovery and independent-smoke evidence remains applicable; only the two plans and their Python regression expectations changed. The offset-1 packet is preserved byte-for-byte as historical evidence. Final commands, bindings, audits and sanitized receipts: `evidence/story-4-13/pass-3-final-20261025/README.md`.

#### Rejected (code review pass 3, 2026-10-25)

- `low` — The nested time bounds exceed the wrapper's 900 s, and the audit plan's 11 Query phases × 45 s exceed the 480 s runner budget (BH). Carried from pass 1. A passing phase converges in well under a second, so the worst case arises only on phases that are already failing. A kill fails closed, and `live-result.json` keeps the phase progress.
- `low` — The same nested time bounds, reported as worst-case budgets (EC). Carried from pass 1, as above.
- `low` — The 8-minute runner deadline, the readiness loop and the `git` wait end in a bare `OperationCanceledException` (BH). Carried from pass 1, and R2-B9 pinned the readiness deadline's current behaviour. All three fail loudly; the fix adds conversion branches.
- `low` — The `LiveVectorProcess` 8-minute deadline throws without diagnostics (EC). Carried from pass 1, as above.
- `low` — The repeated idempotent `deactivate-party` proof cannot exclude a late effect, and the barrier rule accepts only-negative assertions (BH). Pass 1's P10 settled this wording. The only barrier without a positive assertion follows a positive earlier observation (see the parent checks), so a generic guard would address plans that do not exist.
- `false` — `aspire.config.json` is accidental and outside Platform rules (BH). It came from the user's sync commit `8962e2f`, not the story commits. Carried from pass 1.
- `low` — Manifest.Tests now waits on the real 60 s and 30 s deadlines (BH). Pass 1's P1 and R2-B9 chose this deliberately, to protect the shipped deadlines. The measured run is 61.6 s, and injectable deadlines would add parameters. CLAUDE.md's "about 35 s" is now about 62 s, but no command depends on that figure.
- `low` — `LiveVectorProcess` uses `python3` from `PATH` while the parent uses `sys.executable`, and Manifest.Tests now needs `python3` (BH). The interpreter mismatch is carried from pass 1. Manifest.Tests runs only on `ubuntu-latest`, where `python3` exists, and the conformance gates already require it.
- `low` — A SIGTERM leaves `live-lane.json` saying `pending` with a `running` vector (BH). Only the 6-hour outer deadline sends TERM. The receipt keeps `fullLiveAccepted: false` and the process exits 143, and the fix adds an interrupted state.
- `low` — Sentry issuer credentials reach the runner and CLI environments (BH). They belong to a disposable private CA, created per run inside the owned namespace, and no receipt or diagnostic writes the environment. An allow-list adds complexity.
- `false` — The hard-coded live claims are not checked against the plans (BH). Global administrators bypass tenant and domain validation. Carried from pass 1.
- `low` — `cutoverCommit` is not bound to the deployed bytes (BH). Carried from pass 1 and R2-B3.
- `low` — The same `cutoverCommit` claim, for a dirty tree (EC). Carried, as above.
- `false` — Malformed administrator documents escape the authority poll loop (BH). An immediate loud failure is correct. Carried from pass 1.
- `false` — The same malformed-document claim (EC). Carried, as above.
- `low` — The live tooling imports private `run_loopback` helpers (BH). A loopback refactor would fail at import and in `test_live_runner.py`/`test_live_plans.py`; promoting a shared module is a refactor.
- `low` — `live-plan.schema.json` duplicates its definitions in both `oneOf` branches and gives vague errors (BH). The issue is developer-only, and the fix is a schema refactor.
- `false` — The CI job rename orphans a required check, and the discovery temp file keeps its old name. These are rejected sub-claims of the BH finding that survives as P8, so they are not counted among the 23 rejected findings. `main` has no required checks (see the parent checks), and only the same step reads the temp file.
- `low` — A readiness `GET` that throws `HttpRequestException` aborts after the one-time activation (EC). The Gateway that just answered the activation keeps serving, no such fault was observed, and the fix adds a catch branch.
- `false` — Preflight accepts a vector step that expects an error, which then fails live (EC). No approved vector expects an error (see the parent checks), and a future one would fail loudly.
- `low` — Python older than 3.11 makes the timestamp captures fail as read deadlines (EC). P14 documents the 3.11 minimum, the deadline message keeps the "Invalid timestamp" failure, and a runtime guard adds a branch.
- `low` — CI lists the live cases but never runs them (VG). The spec's Never boundary assigns blocking live CI to Story 4.14, and that story's AC owns it (`_bmad-output/planning-artifacts/epics.md:1477`).
- `low` — The plan schema and validator allow time bindings only at `/payload/From` and `/payload/To` (AA). The allow-list is generic and carries no module identity. Enrolling a module with differently named time fields is rare, and widening the allow-list changes both schema branches and the guard that pass 1's P3 protects.
- `low` — Eight `preflight()` refusals, the runtime-directory refusal and the inherited-variable stripping have no removal-sensitive tests (AA). Each duplicates a later check (see the parent checks), so removing one leaves another failing check, and tests cannot protect such duplicates without deleting them.

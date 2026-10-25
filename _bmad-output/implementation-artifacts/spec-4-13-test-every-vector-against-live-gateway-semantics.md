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

## Design Notes

No unresolved intent choices remain. The McpCli footprint is test tooling, topology configuration and documentation, plus the qualified upstream host protocol repair and reference integration. Parties PR #58 remains open on independently reproduced baseline CI failures.

Fresh state per vector preserves fixed Parties identifiers and exact Tenants index counts. Companion plans leave v1 schema, owner approval receipts and vector bytes intact. They close the existing dynamic-value handoff at `deferred-work.md:513`; they cannot silently discard business assertions. Infrastructure bootstrap uses the existing server-owned path, while vector setup remains generic Operation calls.

## Verification

- `dotnet restore Hexalith.McpCli.slnx`, then `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`.
- Run each existing non-live test project separately; run Python suites under `tools/live-topology` and `tools/conformance-vectors/v1`, plus exact MTP discovery.
- Build the three root source servers using the documented Story 4.12 commands; bootstrap private binaries and run `run-vectors.py` with outer and per-child deadlines. Require 21 passed vectors, zero failures/skips and owned cleanup.

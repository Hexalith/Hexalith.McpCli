---
title: '4.13 Test every vector against live Gateway semantics'
type: 'feature'
created: '2026-10-25'
status: 'in-progress'
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
- `tests/Hexalith.McpCli.Integration.Tests/`: existing platform fixture, runtime skips and authenticated smoke; its token currently permits only Tenants reads.
- `tests/Hexalith.McpCli.AppHost/`: helper composition and declarative routes. Normal Tenants bootstrap uses the shared Development signing contract; projection delivery needs explicit sidecar permission.
- `tools/live-topology/run-isolated.py`: owned namespaces, fresh Redis, daemon lifecycle and bounded child receipts. Reuse unchanged where possible.

## Tasks & Acceptance

**Execution:**
- [ ] `tools/live-topology/{live-plan.schema.json,live_plans.py,plans/}` — define strict companion plans bound to exact vector digests; cover all 21 vectors with explicit cursor/time captures, generic read barriers and audit boundary probes. Validate resolved calls through Core; reject unknown fields and weakened static assertions.
- [ ] `tools/live-topology/run_live.py` — reuse existing validators and CLI adapter for one selected vector; execute declared steps once, bound read convergence, capture real values and retain result/phase diagnostics without credentials.
- [ ] `tools/live-topology/run-vectors.py` — preflight the full enrolled set, launch one isolated test process per vector and require exactly one passing, unskipped selected case per child. Invalidate stale success; record complete coverage and partial failures.
- [ ] `tests/Hexalith.McpCli.Integration.Tests/{LiveVectorTests.cs,LiveVectorProcess.cs,AspireTopologyFixture.cs,Hexalith.McpCli.Integration.Tests.csproj}` — expose Operation-labelled theory cases with Integration trait/MTP; enforce single-vector selection, pass discovered endpoint and short-lived identity privately to the runner, and preserve the independent smoke.
- [ ] `tests/Hexalith.McpCli.AppHost/{Program.cs,appsettings.json,DaprComponents/accesscontrol.yaml}` — configure authentic bootstrap declaratively and admit only required authenticated bootstrap/projection POST routes.
- [ ] `tools/live-topology/test_*.py` and `tests/Hexalith.McpCli.Manifest.Tests/{TopologyAccessControlTests.cs,TopologyConfigurationTests.cs}` — protect preflight, selection/isolation, typed binding, query deadlines, single write submission, failure receipts and topology permissions with removal-sensitive checks.
- [ ] `.github/workflows/ci.yml`, `README.md`, `tools/live-topology/README.md` — extend non-live discovery to the complete vector set plus smoke; document bounded full-lane execution and skip semantics without adding Story 4.14's blocking tier.
- [ ] `_bmad-output/implementation-artifacts/evidence/story-4-13/` — retain exact commands, package/vector/plan bindings, 21 live outcomes and non-live validation results.

**Acceptance Criteria:**
- Given approved Tenants and Parties vectors, when the full isolated lane completes, then all 21 execute with their prerequisite calls and persistent semantic checks, and no Command step is duplicated for parity or convergence.
- Given paged and audit vectors, when live plans resolve captured values, then non-default pages and returned cursors produce expected later contents, and category/time probes exclude nonmatching persisted events.
- Given delayed or broken effects, when bounded observations finish, then the lane fails with the Operation and assertion path rather than passing on response shape or acceptance alone.
- Given unavailable Dapr or incomplete execution, when MTP reports results, then standard prerequisite diagnostics remain visible and the full-lane receipt cannot report success.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

No unresolved intent choices or external irreversible actions remain. The footprint is test tooling, topology configuration and documentation.

Fresh state per vector preserves fixed Parties identifiers and exact Tenants index counts. Companion plans leave v1 schema, owner approval receipts and vector bytes intact. They close the existing dynamic-value handoff at `deferred-work.md:513`; they cannot silently discard business assertions. Infrastructure bootstrap uses the existing server-owned path, while vector setup remains generic Operation calls.

## Verification

- `dotnet restore Hexalith.McpCli.slnx`, then `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`.
- Run each existing non-live test project separately; run Python suites under `tools/live-topology` and `tools/conformance-vectors/v1`, plus exact MTP discovery.
- Build the three root source servers using the documented Story 4.12 commands; bootstrap private binaries and run `run-vectors.py` with outer and per-child deadlines. Require 21 passed vectors, zero failures/skips and owned cleanup.

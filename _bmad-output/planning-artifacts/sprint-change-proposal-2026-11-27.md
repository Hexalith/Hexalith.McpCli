---
title: Reduce CI/CD duration, remove harness overengineering, and fail fast
created: '2026-11-27'
status: applied
review_mode: batch
scope: sprint plan, PRD FR-20/NFR-7, Architecture AD-16, and upstream Hexalith.CiCd proposal
baseline: bb11083c084b926e80aebb09ba42366284e4a405
source_action: 'User investigated 3.5+ hour CI run 45982074357 on 2026-11-27, identified CI harness overengineering and slow failure feedback, and invoked /bmad-correct-course to apply all six recommended optimizations.'
approval: 'Administrator explicitly approved ("approve") on 2026-11-27; C1–C7 applied to prd.md, ARCHITECTURE-SPINE.md, epics.md, and sprint-status.yaml.'
---

# Sprint Change Proposal: Reduce CI/CD Duration, Remove Harness Overengineering, and Fail Fast

## 1. Issue Summary

### Trigger and context

On 2026-11-27, CI run [#45982074357](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/45982074357) on `main` (`bb11083c`, *fix(ci): start tenant bootstrap after peer catalog observations*) took **3h 44m 54s** end-to-end (`10:26:08Z` → `14:11:02Z`), blocking the dispatched Release run ([#45985940361](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/45985940361)) for hours and delaying a **3m 41s** Windows job failure until **3h 40m** after push.

### Issue classification

**Failed approach requiring a different solution** (compounded by technical scaling limits after adopting the 5-host native cohort and folding all Linux checks into a single serial `after-unit-tests` hook).

### Evidence

1. **Completed timing breakdown — CI run `45982074357` (full green Linux job `140448220333`, `bb11083c`):**
   - Stages 1–4 environment setup (checkout, guard, Release restore/build, all 6 C# unit test projects): **7m 24s** (`10:26:12Z` → `10:33:36Z`).
   - `scripts/product_ci.py linux`: **55m 42s** (`10:33:36Z` → `11:29:18Z`). Measured from immediately preceding run `45972012463` (same script/revision):
     - `unittest discover -s tools/live-topology` (CI-script self-tests): **29m 23s**
     - `tools/conformance-vectors/v1/run-sample-loopback.sh` (repeated repo copies + empty-cache `NUGET_PACKAGES` cold restores + `-m:1` rebuilds): **13m 36s**
     - `tools/conformance-vectors/v1/check_enrolled.py` (3 isolated cold restores/builds before production replay): **9m 11s**
     - Packaging, smoke validation, preflight: **~2m 30s**
   - `tools/live-topology/prepare-ci.sh`: **3m 24s** (`11:29:18Z` → `11:32:42Z`).
   - `tools/live-topology/run-ci.sh` (24 serial cold-booted 5-host isolated topologies): **2h 33m 29s** (`11:32:42Z` → `14:06:11Z`):
     - `SharedHeadBoundaryTests` (`boundary`): **7m 28s**
     - 22 live vectors (`run-vectors.py`, avg **6m 17s** each): **2h 18m 18s**
     - `GatewaySmokeTests` (`smoke`): **7m 22s**
   - `windows-macos-product`: **4m 20s** (passed) / `windows-windows-product`: **3m 41s** (failed — only started after 3h 40m).

2. **Harness-to-product inversion and policy conflict:**
   - Production code (`src/**/*.cs`): **7,752 LOC**.
   - C# tests (`tests/**/*.cs`): **35,069 LOC** (runs in **~4m 40s**).
   - Python CI/conformance/live-topology scripts and self-tests (`tools/live-topology/*.py` 9,273 LOC, `tools/conformance-vectors/v1/*.py` 6,225 LOC, `scripts/*.py` 5,007 LOC): **20,505 LOC**, consuming **~96% of total CI time**.
   - `tools/live-topology/test_ci.py` alone is **198 KB** and invokes real `dotnet msbuild` subprocesses inside `unittest`, directly conflicting with `AGENTS.md` / `hexalith-llm-instructions.md`: *"Checks of CI itself, agent tooling, story evidence or workflow YAML do not belong in module CI."*

3. **Slow failure feedback loop:**
   - All 6 prior failed runs (`45972012463`, `45970566489`, `45920445432`, `45873099100`, `45849364550`, `45833184405`) waited **~60+ minutes** in `product_ci.py` before reaching `prepare-ci.sh` or `boundary`.
   - `run-vectors.py` catches every per-vector exception and continues looping across all 22 vectors (up to `960s` each, bounded only by the `11,280s` = 3h 08m outer cap), never failing fast on systematic startup/timeout errors.
   - `NativeCatalogRuntime.CreateAsync` repeats two `PrepareEventStoreDevelopmentOwnerAsync` child `dotnet build`s (`tenants` + `projects`) and Platform `CatalogBuilder` from scratch **24 times** per CI run on identical sealed binaries.

4. **Redundant live topologies vs. Story 5.12 shape coverage:**
   - Story 5.12 (`sprint-change-proposal-2026-11-10-shape-coverage.md`) established that McpCli's generic translation branches on **Operation Shape** (not per-operation), requiring at least one live vector per declared Operation kind per Module for new enrollments, yet left all 21 historical Tenants (14) and Parties (7) live plans active alongside `projects.list` (total **22** live plans). Under the 5-host native cohort (`eventstore`, `tenants`, `parties`, `projects`, `projects-workers`), those 14 redundant live plans add **~88 minutes** of serial cold boots with no unique generic coverage.

---

## 2. Impact Analysis

### 2.1 Change Navigation Checklist Summary

| Section | Checklist Items | Status | Key Findings |
| --- | --- | --- | --- |
| 1. Trigger & Context | 1.1–1.3 | `[x]` Done | Triggered by live-CI stabilization under Story 5.13 (`bb11083c`, run `45982074357`, 3h 44m 54s). Complete timing and LOC evidence collected. |
| 2. Epic Impact | 2.1–2.5 | `[x]` Done | Epics 1–4 (done) unchanged. Epic 5 (in-progress): amend backlog Story 5.13 live-count wording and add Stories 5.25–5.28. Epic 6 (backlog) benefits automatically via faster enrollment CI without changing Folders acceptance criteria. |
| 3. Artifact Conflicts | 3.1–3.4 | `[x]` Done | PRD FR-20 & NFR-7, Architecture AD-16, and Epics (`epics.md` + `sprint-status.yaml`) require targeted amendments. UX: `[N/A]` (zero user-facing CLI/MCP change). Secondary CI/test artifacts and an upstream `Hexalith.CiCd` proposal identified. |
| 4. Path Forward | 4.1–4.4 | `[x]` Done | Option 1 (Direct Adjustment) selected. Option 2 (Rollback) not viable (5-host native cohort and shared CiCd workflow are required). Option 3 (MVP Review) `[N/A]` (v1 shipped; product scope unchanged). |
| 5. Proposal Components | 5.1–5.5 | `[x]` Done | All five sections compiled below with explicit OLD → NEW edit proposals and owner handoffs. |
| 6. Final Review & Handoff | 6.1–6.5 | `[x]` Done | Approved by Administrator on 2026-11-27 (`approve`); C1–C7 applied to `prd.md`, `ARCHITECTURE-SPINE.md`, `epics.md`, and `sprint-status.yaml`, and routed for implementation. |

### 2.2 Epic Impact

| Epic | Status | Impact |
| --- | --- | --- |
| Epics 1–4 | `done` | None. Historical v1 and Story 4.11–4.14 evidence remains valid; completed story text is unchanged. |
| Epic 5 | `in-progress` | Amend backlog **Story 5.13** (remove hardcoded `22 plus two` live-plan count so it binds to the active approved companion-plan set). Add four independently deliverable stories: **5.25** (fail-fast & gate reordering), **5.26** (remove CI-script self-tests & cold-cache rebuilds), **5.27** (reduce live plans to shape/FR-20 minimum + pre-prepare catalog metadata + bounded concurrency/topology reuse), and **5.28** (upstream `Hexalith.CiCd` parallel job-split proposal). Schedule 5.25–5.27 ahead of or alongside 5.13/5.14/5.21 so every subsequent Epic 5 PR runs in ~20–30 minutes instead of 3.5+ hours. |
| Epic 6 | `backlog` | Positive impact only. Stories 6.1–6.4 already follow Story 5.12's shape/kind live rule; faster CI and pre-prepared catalog metadata directly speed up Folders enrollment without altering any acceptance criterion. |

### 2.3 Artifact Conflicts

| Artifact | Conflict / Update Needed |
| --- | --- |
| **PRD** ([`prd.md`](prds/prd-mcpcli-2026-09-21/prd.md)) | **FR-20** (§5.7) and **NFR-7** (§6): clarify that existing Modules (Tenants and Parties) may trim companion live plans to the same shape-/kind-covering set (retaining mandatory Tenants audit-filter and envelope-paging live proofs and all loopback vectors), and that blocking CI uses fail-fast and pre-prepared fixtures without running CI-script self-tests in the product gate. No user-facing feature or MVP scope changes. |
| **Architecture Spine** ([`ARCHITECTURE-SPINE.md`](architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md)) | **AD-16** (`Live semantics`, `Topology`, `Candidate evidence`): replace "Retain existing approved plans" with explicit permission to reduce companion live plans to the shape-/FR-20-covering set while keeping all vectors in loopback parity; authorize pre-prepared hash-bound catalog owner metadata from `prepare-ci.sh`, bounded parallel isolated namespaces (`unshare`) or verified per-module clean topology reuse, fail-fast on infrastructure/consecutive vector failures, early crashed-host detection, and removal of CI-script self-tests from the product hook. |
| **Epics** ([`epics.md`](epics.md)) | Update **Story 5.13** bullet 3; add **Stories 5.25–5.28** under Epic 5; record this proposal in frontmatter. |
| **Sprint Status** ([`sprint-status.yaml`](../implementation-artifacts/sprint-status.yaml)) | Add `5-25`, `5-26`, `5-27`, `5-28` as `backlog` under `epic-5`. |
| **UI / UX** | **N/A** — zero changes to CLI verbs, flags, MCP tools, error documents, or operator workflows. |
| **Secondary artifacts** *(updated during implementation of 5.25–5.28)* | `.github/actions/after-unit-tests/action.yml`, `scripts/product_ci.py`, `tools/live-topology/{ci.py,run-vectors.py,run-isolated.py,README.md,plans-current/}`, `tools/conformance-vectors/v1/{run-sample-loopback.sh,run_packaged_process_fixture.py,check_enrolled.py,verify_artifact.py,README.md}`, `tests/Hexalith.McpCli.AppHost/NativeCatalogRuntime.cs`, `tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs`, `README.md`, `AGENTS.md` (and synced `CLAUDE.md`, `.github/copilot-instructions.md`). |
| **Upstream `Hexalith.CiCd`** *(owned externally)* | `.github/workflows/ci.yml` and `.github/hexalith-ci.json` are owned by `Hexalith.CiCd` and MUST NOT be edited here. Story 5.28 produces an upstream proposal to split Linux conformance vs. live Aspire jobs and unblock Windows/macOS jobs as soon as package staging completes. |

### 2.4 Technical & Platform Impact

- **Zero production `src/` changes** and **zero weakening of dependency audits, package-integrity checks, loopback parity, or live authorization/persistence assertions**.
- **All 26 conformance vectors remain in loopback parity** (`check_enrolled.py` still replays all 26 approved vectors across CLI and MCP against reset loopback Gateway scripts).
- **Live companion plans reduce from 22 → 8** (10 isolated topologies total including `boundary` and `smoke`), covering 100% of enrolled Modules, 100% of declared Operation kinds, 100% of distinct Operation Shapes, and 100% of mandatory FR-20/AD-16 semantic proofs:

| Module | Retained live plans (8 total) | Dropped redundant live plans (14; remain loopback-only) | Why retained plans are sufficient |
| --- | --- | --- | --- |
| **Tenants** (4) | `tenants.update-tenant`, `tenants.get-tenant-audit`, `tenants.list-tenants`, `tenants.get-tenant` | `create-tenant`, `disable-tenant`, `enable-tenant`, `add-user-to-tenant`, `change-user-role`, `remove-user-from-tenant`, `set-tenant-configuration`, `remove-tenant-configuration`, `get-tenant-users`, `get-user-tenants` | Covers Command (prerequisite create → second Command with caller idempotency key → postcondition Query per AD-16/P6), FR-20 audit `From`/`To`/`Category` filter proof, FR-20 `platform:tenants` + `QueryEnvelope.Paging` continuation proof, and `public` variable-scope single-tenant `aggregateIdProperty` shape. |
| **Parties** (3) | `parties.update-party`, `parties.get-party`, `parties.list-parties` | `create-party`, `deactivate-party`, `reactivate-party`, `search-parties` | Covers Command (prerequisite create → second Command with caller idempotency key → postcondition Query — specifically the scenario that caught the Parties converter defect in P6), per-entity `aggregateIdProperty` Query, and constant `aggregateId` list Query (both Parties Query shapes). |
| **Projects** (1) | `projects.list` | *(none; other 3 are already loopback-only)* | Covers Projects Query kind; Story 5.21 extends populated/denial assertions under DW-82. |

- **Projected CI wall-clock impact:**

| Phase | Baseline (`45982074357`) | After Stories 5.25–5.27 (repo-local) | After Story 5.28 (`Hexalith.CiCd` split) |
| --- | ---: | ---: | ---: |
| Stages 1–4 env setup + Release build + 6 C# test suites | 7m 24s | ~7m 30s | ~7m 30s |
| `product_ci.py linux` (packaging, loopback, enrolled) | 55m 42s | **~4–6 min** | Runs in parallel |
| `prepare-ci.sh` (including 1× catalog owner prep) | 3m 24s | ~4m 30s | ~4m 30s |
| `run-ci.sh` (`boundary` + 8 live plans + `smoke`, pre-prepared metadata, 2 workers) | 2h 33m 29s | **~12–18 min** | ~12–18 min |
| Windows + macOS product jobs | +4m 20s (after 3h 40m wait) | +4m 20s (after ~28–35m) | Runs in parallel after staging (~10m from push) |
| **Total end-to-end wall-clock** | **3h 44m 54s** | **~30–38 min** (~83–86% faster) | **~22–28 min** (~88–90% faster) |
| **Time to detect recurrent live/Windows failure** | **1h 12m – 3h 44m** | **~12–15 min** | **~10–15 min** |

---

## 3. Recommended Approach

**Selected Path: Option 1 — Direct Adjustment** (targeted PRD/AD-16 clarifications, Story 5.13 alignment, four new Epic 5 stories 5.25–5.28, and an upstream `Hexalith.CiCd` proposal).

- **Why not Option 2 (Rollback)?** Rolling back the 5-host native cohort (`Projects`) or the shared `Hexalith.CiCd` workflow would discard required platform integration and violate `Hexalith.CiCd` ownership policy.
- **Why not Option 3 (MVP Review)?** v1 has shipped; no product feature, contract, or security guarantee is removed.
- **Effort & Risk:**
  - **5.25 (Fail-fast & reordering):** Low effort (~1 day), Low risk. Immediate feedback-loop win.
  - **5.26 (Drop CI self-tests from product gate & reuse warm caches):** Low–Medium effort (1–2 days), Low risk. Cuts ~48–50 min immediately while keeping all hash/integrity assertions intact.
  - **5.27 (Trim live plans 22 → 8 + pre-prepare catalog metadata + bounded concurrency/reuse):** Medium effort (2–3 days), Medium risk (requires keeping strict isolation/custody proofs and updating `plans-current/` + `NativeCatalogRuntime.cs` + `ci.py` discovery checks cleanly).
  - **5.28 (Upstream `Hexalith.CiCd` job split):** Low effort (½ day proposal; external CiCd delivery timeline), Low risk.
- **Trade-offs accepted:**
  - 14 Tenants and Parties operations move from live-executed to loopback-only in McpCli CI (their handler semantics remain owned and tested in the Tenants and Parties repositories per FR-20/Story 5.12).
  - `tools/live-topology` Python self-tests no longer block every product push; they run locally when editing `tools/live-topology/**` (or via a dedicated non-blocking/path-filtered check if later adopted in `Hexalith.CiCd`).
  - Parallelizing 2 isolated `unshare` workers increases peak runner CPU/RAM usage slightly, so concurrency stays bounded (`--max-workers 2`, configurable to `1` for constrained machines).

---

## 4. Detailed Change Proposals

### 4.1 PRD Modifications (`_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md`)

#### C1. Frontmatter `changeProposals` & `updated`

- **File:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md` (lines 5–11)
- **OLD:**
```yaml
updated: 2026-11-20
changeProposals:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-06.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-08.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10-shape-coverage.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-20.md
```
- **NEW:**
```yaml
updated: 2026-11-27
changeProposals:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-06.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-08.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10-shape-coverage.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-20.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-27.md
```
- **Rationale:** Record the approved sprint change proposal in PRD provenance.

#### C2. PRD §5.7 — FR-20 (Live vector scope for existing and new Modules)

- **File:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md` (line 436)
- **OLD:**
```markdown
Separately, a blocking Aspire test executes each approved live vector once against a running EventStore and asserts Gateway acceptance or a returned Query document plus the vector's semantic checks (NFR-7). Each Module has at least one live vector per Operation kind it declares; for a new enrollment, its live Command vector creates an aggregate in a prerequisite, then submits a second Command to it with a caller-supplied idempotency key and reads the effect back with a postcondition Query. A live Command is not submitted twice merely to compare documents.
```
- **NEW:**
```markdown
Separately, a blocking Aspire test executes each approved live vector (every approved vector carrying a companion live plan) once against a running EventStore and asserts Gateway acceptance or a returned Query document plus the vector's semantic checks (NFR-7). Every enrolled Module maintains at least one live vector per Operation kind it declares and covers its distinct Operation Shapes and any Module-specific live proofs below (such as Tenants audit filtering and envelope paging), while all approved vectors without companion plans remain covered by out-of-process loopback parity; for a Command live vector, the scenario creates an aggregate in a prerequisite, then submits a second Command to it with a caller-supplied idempotency key and reads the effect back with a postcondition Query. A live Command is not submitted twice merely to compare documents.
```
- **Rationale:** Extends Story 5.12's shape/kind live rule consistently to existing Tenants and Parties modules so 14 redundant live topologies can move to loopback-only without weakening loopback parity, shape coverage, keyed-Command coverage, or Tenants audit/paging proofs.

#### C3. PRD §6 — NFR-7 (Testability, fail-fast, and CI gate hygiene)

- **File:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md` (line 473)
- **OLD:**
```markdown
- **NFR-7 Testability.** The executor is testable with a substituted Gateway client. Out-of-process parity tests drive both Heads through a reset loopback Gateway, while a blocking Aspire test runs each Module's approved live vectors (at least one per declared Operation kind) once against EventStore and asserts accepted Commands or returned Query documents plus semantic effects, not only status codes (spine AD-16). Story 5.13 requires a verifiable dependency audit and a passing full Linux lane on the candidate SHA, including every approved live vector and both independent cases. Windows and macOS product checks must pass on that SHA. Preflight counts identify cases to run. Story 5.20 requires Linux checks to reap their own descendants on timeout or refuse launch if safe supervision is unavailable.
```
- **NEW:**
```markdown
- **NFR-7 Testability.** The executor is testable with a substituted Gateway client. Out-of-process parity tests drive both Heads through a reset loopback Gateway, while a blocking Aspire test runs each Module's approved companion-plan live vectors (covering every declared Operation kind, distinct Operation Shape, and mandatory Module live proofs) once against EventStore and asserts accepted Commands or returned Query documents plus semantic effects, not only status codes (spine AD-16). Story 5.13 requires a verifiable dependency audit and a passing full Linux lane on the candidate SHA, including every active approved live plan and both independent cases. Windows and macOS product checks must pass on that SHA. Preflight counts identify cases to run. Blocking product CI checks product behavior only (excluding CI-script self-tests), reuses verified pre-prepared fixtures and warm caches, and fails fast on infrastructure, crashed-host, or repeated vector failures (Stories 5.25–5.27). Story 5.20 requires Linux checks to reap their own descendants on timeout or refuse launch if safe supervision is unavailable.
```
- **Rationale:** Codifies fail-fast, fixture reuse, and exclusion of CI-script self-tests from blocking product CI under NFR-7.

---

### 4.2 Architecture Modifications (`_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md`)

#### C4. AD-16 — Integration harness (`Live semantics`, `Topology`, `Candidate evidence`)

- **File:** `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md` (lines 203–206)
- **OLD:**
```markdown
- **Live semantics:** select the approved vectors with matching hash-bound companion plans, with at least one live vector per declared Operation kind per Module. A plan without a vector fails. Run each selected vector once and assert its expected effects. For new Command enrollments, create the aggregate in setup, submit a second Command with a caller-supplied key and query the persisted effect. Retain existing approved plans. For exposed Tenants audit and paged reads, verify the serialized `From`, `To` and `Category` filters and non-default page contents and continuation under AD-20. Per-operation handler semantics belong to the owner.
- **Topology:** the generic runner consumes the vectors and plans. The test AppHost and Integration.Tests own module-aware composition, fixture identities and persisted-state assertions. The native cohort is selected in `tools/live-topology/native-runtime-current.json`. In McpCli repository CI, the isolated Aspire lifecycle runs the owned Gateway and qualified hosts with private Dapr and state. The complete lane requires all selected vectors, independent authenticated smoke and shared-head authorization/deactivation cases, zero skips and owned cleanup. For Platform integration, the Platform runner alone provisions, waits for readiness, records ownership and cleans up. Participating McpCli tests consume its versioned environment descriptor. A repository AppHost run qualifies only the McpCli lane. Platform staging requires separate evidence from its runner.
- **Catalog budget:** in a fresh process, load every restored production manifest assembly plus exactly one synthetic `Ulid` sample before timing the first `CatalogBuilder.Build`. Accept at most 500 ms on Ubuntu. Require Tenants and Parties as the v1 minimum and include Projects while enrolled. The benchmark records its cohort and elapsed time. An earlier cohort's measurement qualifies that cohort only.
- **Candidate evidence:** the Linux after-unit-tests hook runs the package and conformance checks, prepares the native fixtures and runs the full live lane. Story 5.13 requires verifiable advisory data for the selected restore, a complete green Linux lane and passing Windows/macOS product jobs on the same commit. Confirmed advisory-feed rotation permits one fresh isolated restore. Audit that restore and its artifacts against the new snapshot. Unavailable data, a persistent mismatch or a policy violation fails qualification. Under Story 5.20, a timed-out Linux check must reap its owned descendants, preserve unrelated processes and report loss of ownership visibility. Refuse launch if the environment cannot support safe supervision. These are backlog acceptance criteria.
```
- **NEW:**
```markdown
- **Live semantics:** select the approved vectors with matching hash-bound companion plans, covering at least one live vector per declared Operation kind per Module, every distinct Operation Shape, and any Module-specific live proofs (including Tenants serialized `From`, `To` and `Category` audit filters and non-default `QueryEnvelope.Paging` contents and continuation under AD-20). A plan without a vector fails. Approved vectors without a companion plan remain loopback-only and still run in parity replay. Run each selected live vector once and assert its expected effects; each Module's Command live vector creates the aggregate in setup, submits a second Command to it with a caller-supplied idempotency key and queries the persisted effect. Existing Modules may align their companion live plans to this minimal set (Story 5.27: 8 plans across Tenants, Parties and Projects) while preserving all loopback vectors. Per-operation handler semantics belong to the owner.
- **Topology:** the generic runner consumes the vectors and plans. The test AppHost and Integration.Tests own module-aware composition, fixture identities and persisted-state assertions. The native cohort is selected in `tools/live-topology/native-runtime-current.json`. In McpCli repository CI, the isolated Aspire lifecycle runs the owned Gateway and qualified hosts with private Dapr and state. To avoid redundant per-vector rebuilds and serial stalls, `prepare-ci.sh` may pre-prepare and hash-bind SDK catalog owner metadata once for reuse across isolated runs, `run-vectors.py` may execute independent isolated namespaces (`unshare`) with bounded concurrency or reuse a verified clean isolated topology per module/group when private state and owned cleanup remain proven, and the fixture must fail fast when any required host process exits or fails to start. The complete lane requires all active companion-plan vectors, independent authenticated smoke and shared-head authorization/deactivation cases, zero skips and owned cleanup; `run-vectors.py` fails fast on infrastructure timeouts or consecutive vector failures rather than looping through remaining cases. For Platform integration, the Platform runner alone provisions, waits for readiness, records ownership and cleans up. Participating McpCli tests consume its versioned environment descriptor. A repository AppHost run qualifies only the McpCli lane. Platform staging requires separate evidence from its runner.
- **Catalog budget:** in a fresh process, load every restored production manifest assembly plus exactly one synthetic `Ulid` sample before timing the first `CatalogBuilder.Build`. Accept at most 500 ms on Ubuntu. Require Tenants and Parties as the v1 minimum and include Projects while enrolled. The benchmark records its cohort and elapsed time. An earlier cohort's measurement qualifies that cohort only.
- **Candidate evidence:** the Linux after-unit-tests hook orders fast package smoke and live `prepare`/`boundary` gates ahead of heavier suites, omits CI-script self-tests from blocking product CI (keeping them runnable on demand), reuses warm NuGet caches and shared Release build outputs without weakening restored-package hash verification, and runs the full live lane (Stories 5.25–5.27). Story 5.28 tracks an upstream `Hexalith.CiCd` proposal to parallelize product conformance, live Aspire, and Windows/macOS jobs. Story 5.13 requires verifiable advisory data for the selected restore, a complete green Linux lane and passing Windows/macOS product jobs on the same commit. Confirmed advisory-feed rotation permits one fresh isolated restore. Audit that restore and its artifacts against the new snapshot. Unavailable data, a persistent mismatch or a policy violation fails qualification. Under Story 5.20, a timed-out Linux check must reap its owned descendants, preserve unrelated processes and report loss of ownership visibility. Refuse launch if the environment cannot support safe supervision. These are backlog acceptance criteria.
```
- **Rationale:** Aligns AD-16 with all six approved CI/CD optimization levers while preserving every security, isolation, hash-binding, and semantic guarantee.

---

### 4.3 Epics & Stories Modifications (`_bmad-output/planning-artifacts/epics.md`)

#### C5. Story 5.13 — Align live vector count with active approved companion plans

- **File:** `_bmad-output/planning-artifacts/epics.md` (line 2163)
- **OLD:**
```markdown
- Run the full Linux lane on the candidate SHA and record the actual outcomes of the approved live vectors and independent cases (22 plus two at the audit baseline). Require passing Windows and macOS product jobs on that SHA. A discovery or preflight receipt alone cannot satisfy this story.
```
- **NEW:**
```markdown
- Run the full Linux lane on the candidate SHA and record the actual outcomes of every active approved companion-plan live vector and both independent cases (22 plus two at the 2026-11-20 audit baseline; reduced to 8 plus two once Story 5.27 lands). Require passing Windows and macOS product jobs on that SHA. A discovery or preflight receipt alone cannot satisfy this story.
```
- **Rationale:** Prevents Story 5.13 from conflicting with Story 5.27's live-plan reduction.

#### C6. Add Stories 5.25–5.28 under Epic 5

- **File:** `_bmad-output/planning-artifacts/epics.md` (insert immediately after Story 5.24, before `## Epic 6`)
- **OLD:**
```markdown
- Through CLI and stdio MCP, verify discovery marks the aggregate ID optional for an admitted default and a Query that omits it sends that default to the Gateway. Verify a valid explicit ID overrides the constant. A Query with neither declaration remains discoverable with `aggregateIdRequired: true`.

## Epic 6: Replace and Retire the Folders CLI and MCP Server
```
- **NEW:**
```markdown
- Through CLI and stdio MCP, verify discovery marks the aggregate ID optional for an admitted default and a Query that omits it sends that default to the Gateway. Verify a valid explicit ID overrides the constant. A Query with neither declaration remains discoverable with `aggregateIdRequired: true`.

### Story 5.25: Fail Fast and Reorder Product CI Gates

As a McpCli maintainer, I need CI to surface live-topology and packaging failures within ~15 minutes instead of waiting 60+ minutes or looping for 3+ hours on broken runs. McpCli owns `.github/actions/after-unit-tests/action.yml`, `tools/live-topology/run-vectors.py`, and `tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs`. [AD-16, NFR-7](architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md)

- Reorder `.github/actions/after-unit-tests/action.yml` so fast package staging/validation/smoke runs first (~25s), followed by `prepare-ci.sh` and the `boundary` live gate before slower conformance and live-vector loops, while keeping all existing artifact uploads (`mcpcli-product-packages`, `mcpcli-linux-product-diagnostics`).
- Add bounded fail-fast to `tools/live-topology/run-vectors.py` (default `--max-failures 2`, and immediate abort on infrastructure/timeout exit code `124` or fixture initialization failure), marking remaining vectors `skipped-fail-fast` in `live-lane.json` so full live acceptance remains `false` and the run terminates in minutes instead of looping up to the 3h 08m cap.
- Update `AspireTopologyFixture.cs` to observe Aspire resource terminal failure states (`FailedToStart`, `Exited`) during startup/readiness waiting and fail immediately with the crashed resource's identity instead of waiting out 2-minute readiness or 15-minute command timeouts.
- Cover fail-fast termination, `skipped-fail-fast` receipt status, and early crashed-host detection with focused unit/runner tests; verify no test weakens `fullLiveAccepted` or masks failures.

### Story 5.26: Remove CI-Script Self-Tests and Cold-Cache Rebuilds from Product CI

As a McpCli maintainer, I need `scripts/product_ci.py linux` to finish in ~4–6 minutes instead of ~55 minutes by stopping CI-script self-tests in the blocking product gate and eliminating redundant empty-cache NuGet downloads and single-threaded rebuilds. McpCli owns `scripts/product_ci.py` and the conformance-vector scripts. [AD-16, NFR-7, AGENTS.md CI policy](architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md)

- Remove the `tools/live-topology` Python `unittest` suite (~29.5 min) from `scripts/product_ci.py linux` so blocking product CI checks product behavior rather than CI scripts themselves (per `AGENTS.md` / `hexalith-llm-instructions.md`). Refactor the slow `dotnet msbuild` subprocess cases in `tools/live-topology/test_ci.py` to mock MSBuild or separate into an opt-in local suite so on-demand execution runs quickly.
- Eliminate empty temporary `NUGET_PACKAGES` cold restores and redundant `-m:1` rebuilds in `tools/conformance-vectors/v1/run-sample-loopback.sh`, `run_packaged_process_fixture.py`, and `check_enrolled.py` / `verify_artifact.py`: reuse the warm runner NuGet package cache (read-only / isolated feed overlay for local sample packages) and the already-built Release outputs without mutating shared `bin/` or `obj/` assets.
- Avoid redundant per-module isolated host rebuilds in `check_enrolled.py` where restored-package integrity (`project.assets.json` + archive SHA-512), inventory coverage, shape coverage, and `production_replay` already verify the exact restored production graph, while keeping `verify_artifact.py` available for standalone candidate-package verification.
- Verify `scripts/product_ci.py linux` completes with all package, sample-validation, sample-loopback, enrolled-coverage, and live-preflight checks passing and records its wall-clock reduction.

### Story 5.27: Reduce Live Vector Plans to Shape/FR-20 Coverage and Optimize Isolated Execution

As a McpCli maintainer, I need the blocking live Aspire lane to run in ~12–18 minutes instead of 2h 33m while keeping 100% of Operation Shapes, declared Operation kinds, FR-20 Tenants audit/paging proofs, and all 26 loopback parity vectors covered. McpCli owns `tools/live-topology/` and `tests/Hexalith.McpCli.{AppHost,Integration.Tests}`. [FR-20, NFR-7, AD-16](architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md)

- Trim `tools/live-topology/plans-current/` from 22 plans to the 8 shape- and FR-20-covering plans: Tenants (`tenants.update-tenant`, `tenants.get-tenant-audit`, `tenants.list-tenants`, `tenants.get-tenant`), Parties (`parties.update-party`, `parties.get-party`, `parties.list-parties`), and Projects (`projects.list`). Retain all 26 conformance vectors unchanged in `tools/conformance-vectors/v1/current/modules/` so the 14 de-planned operations continue running in loopback parity. Upgrade `tenants.update-tenant` and `parties.update-party` live vectors/plans to include a caller-supplied idempotency key per AD-16/P6 (closing the Story 5.12 deferred keying follow-up).
- Pre-prepare `PrepareEventStoreDevelopmentOwnerAsync` owner metadata (`tenants` and `projects`) and Platform `CatalogBuilder` output **once** during `tools/live-topology/prepare-ci.sh`, hash-bind the prepared bundle in `preparation.json`, and consume it in `NativeCatalogRuntime.cs` instead of running 2× `dotnet build` + CatalogBuilder inside every isolated test run.
- Add bounded parallel isolated-namespace execution (`--max-workers 2`, default 2 on ≥4-vCPU Linux runners, configurable to 1) in `tools/live-topology/run-vectors.py` — leveraging `run-isolated.py`'s existing `unshare --user --net --pid --mount` isolation — and/or reuse a verified clean isolated topology per module when private state reset and owned cleanup receipts remain verified.
- Update `tools/live-topology/README.md`, `tools/conformance-vectors/v1/README.md`, `README.md`, and `AGENTS.md` (+ byte-identical `CLAUDE.md` and `.github/copilot-instructions.md` via `scripts/check-agent-instructions-sync.sh`). Verify `topology-vector-discovery`, `check_enrolled.py`, preflight, and a full green live CI run on the candidate SHA.

### Story 5.28: Propose Upstream Hexalith.CiCd Job Split for Parallel Product, Live, and Platform Lanes

As a McpCli maintainer, I want `Hexalith.CiCd` to parallelize Linux conformance checks, the live Aspire lane, and Windows/macOS product jobs so platform regressions surface in ~10 minutes instead of waiting behind the entire live lane. `Hexalith.CiCd` owns `.github/workflows/ci.yml` and `.github/hexalith-ci.json`; McpCli owns the proposal and module-side hook split. [AD-16, AGENTS.md Hexalith.CiCd ownership](architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md)

- Author and submit an upstream change proposal/PR to `Hexalith.CiCd` (making zero local edits to owned `.github/workflows/**` or `.github/hexalith-ci.json` in McpCli) that:
  1. Allows `windows-windows-product` and `windows-macos-product` to depend on a fast package-staging job/output rather than blocking on the full Linux live Aspire lane.
  2. Allows Linux product conformance (`product_ci.py`) and Linux live Aspire (`prepare-ci.sh` + `run-ci.sh`) to execute as parallel jobs consuming the shared Release build / staged package artifact.
- Record the upstream `Hexalith.CiCd` tracking reference and adopt the delivered workflow once `Hexalith.CiCd` rolls it out to McpCli, keeping `python3 references/Hexalith.Builds/check.py` passing.

## Epic 6: Replace and Retire the Folders CLI and MCP Server
```
- **Rationale:** Breaks the six approved levers into four independently deliverable, verifiable stories with clear repo-local vs. `Hexalith.CiCd` ownership boundaries.

---

### 4.4 Sprint Status Modifications (`_bmad-output/implementation-artifacts/sprint-status.yaml`)

#### C7. Add Stories 5.25–5.28 to Epic 5 backlog

- **File:** `_bmad-output/implementation-artifacts/sprint-status.yaml` (after line 117)
- **OLD:**
```yaml
  5-24-reject-invalid-default-query-ids-at-catalog-admission: review # 2026-11-23, implemented in spec-reconcile-deferred-query-contract.md.
  epic-5-retrospective: optional
```
- **NEW:**
```yaml
  5-24-reject-invalid-default-query-ids-at-catalog-admission: review # 2026-11-23, implemented in spec-reconcile-deferred-query-contract.md.
  5-25-fail-fast-and-reorder-product-ci-gates: backlog # 2026-11-27 CI/CD optimization proposal; run before or alongside 5.13.
  5-26-remove-ci-script-self-tests-and-cold-cache-rebuilds-from-product-ci: backlog # 2026-11-27 CI/CD optimization proposal.
  5-27-reduce-live-vector-plans-to-shape-fr20-coverage-and-optimize-isolated-execution: backlog # 2026-11-27 CI/CD optimization proposal; aligns live plans from 22 to 8 and pre-prepares catalog metadata.
  5-28-propose-upstream-hexalith-cicd-job-split-for-parallel-lanes: backlog # 2026-11-27 upstream Hexalith.CiCd proposal (do not edit owned workflow files locally).
  epic-5-retrospective: optional
```
- **Rationale:** Tracks all four stories in `sprint-status.yaml` for sprint scheduling.

---

## 5. Implementation Handoff

### Scope Classification

**Moderate** — requires targeted PRD/Architecture alignment (`FR-20`, `NFR-7`, `AD-16`), Epic 5 backlog reorganization (amend 5.13 + add 5.25–5.28), repo-local CI/test implementation, and an upstream `Hexalith.CiCd` proposal.

### Sequencing and Responsibilities

| Order | Recipient / Role | Deliverable & Responsibility |
| --- | --- | --- |
| 0 | **Product Owner / User (Administrator)** | Approve this Sprint Change Proposal (authorizing edits C1–C7 to `prd.md`, `ARCHITECTURE-SPINE.md`, `epics.md`, and `sprint-status.yaml`). |
| 1 | **Developer (`bmad-agent-dev`) — Story 5.25** | Implement fail-fast in `run-vectors.py`, early crashed-host detection in `AspireTopologyFixture.cs`, and gate reordering in `.github/actions/after-unit-tests/action.yml`. *(Immediate ~15 min failure detection.)* |
| 2 | **Developer (`bmad-agent-dev`) — Story 5.26** | Remove `tools/live-topology` self-tests from `scripts/product_ci.py` and eliminate cold-cache rebuilds in `run-sample-loopback.sh` and `check_enrolled.py`. *(Cuts ~48–50 min immediately.)* |
| 3 | **Developer (`bmad-agent-dev`) — Story 5.27** | Trim `plans-current/` from 22 → 8 plans (with keyed second-Command vectors for Tenants & Parties), pre-prepare catalog owner metadata once in `prepare-ci.sh`, enable bounded `--max-workers 2` isolated execution, update docs & synced agent instructions, and verify a full green live CI run. *(Cuts live lane from 2h 33m → ~12–18 min.)* |
| 4 | **McpCli Maintainer + `Hexalith.CiCd` Owner — Story 5.28** | Submit upstream `Hexalith.CiCd` proposal to parallelize product conformance, live Aspire, and Windows/macOS jobs. Never edit owned `.github/workflows/**` or `.github/hexalith-ci.json` from this repo. |
| 5 | **Developer (`bmad-agent-dev`) — Story 5.13** | Complete Story 5.13 (including investigating the 3m 41s `windows-windows-product` failure observed on `45982074357`) on the fast CI lane. |

### Success Criteria

1. `prd.md`, `ARCHITECTURE-SPINE.md`, `epics.md`, and `sprint-status.yaml` updated cleanly per C1–C7 upon approval.
2. Full Linux CI job (`ci / Build and tests`) finishes in **≤ 35 minutes** (down from **3h 40m 30s**) on a green commit, with `python3 references/Hexalith.Builds/check.py` passing.
3. Recurrent live-topology or Windows failures surface in **≤ 15 minutes** instead of 1h 12m – 3h 44m.
4. Zero regressions in dependency policy (`Manifest.Tests`), all 6 C# test suites, all 26 loopback parity vectors (`check_enrolled.py`), all 8 shape-/FR-20-covering live plans + `boundary` + `smoke`, and cross-platform Windows/macOS product checks.

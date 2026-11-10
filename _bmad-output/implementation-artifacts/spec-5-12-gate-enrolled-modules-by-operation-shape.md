---
title: '5.12 Gate enrolled modules by operation shape'
type: 'feature'
created: '2026-11-10'
status: 'done'
baseline_commit: 'a8511184975c258e8ea7e2483c1b92968422ac3d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-10-shape-coverage.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Today's enrollment gates require one vector and one live plan for every decorated operation. Each receipt is bound to the exact artifact hash and version, and any operation the inventory does not list fails. Every module release therefore needs a matching McpCli change, even when no operation changed.

**Approach:**
- Derive each operation's Operation Shape in C# from Catalog descriptors. The C# enrolled test, `check_enrolled.py`, `verify_artifact.py`, `validate.py --operations-file` and the live preflight then all require coverage by shape.
- A version difference, or a cataloged operation that no inventory row mentions, is reported, not failed. Receipts drop the artifact-hash binding.
- The live lane requires at least one live vector with a plan for each declared operation kind.
- The existing 21 vectors, their plans and the inventories all stay.

## Boundaries & Constraints

**Always:**
- **Shape tuple.** A shape is the tuple below, scoped per module:
  - `kind`
  - `identifierKind`
  - `wireTypeConvention`
  - `tenantSource`: `platformScope`, `fixedTenant` or `public`
  - `aggregateIdSource`: `property`, `constant` or `none`
  - `projectionSelector`: `projectionActorType`, `projectionType` or `none`
  - `idempotencyKey`: `required` or `optional`

  Only the Core.Tests `OperationShape` code derives it. Python treats the key as an opaque string.
- **Unchanged checks.** Restored-package integrity, the vector and inventory hash maps, duplicate and stale vector rejection, the `include`/`withdraw`/`defer` inventory guards and AD-17 release validation stay as they are.
- **Visible reports.** A report appears as a stderr `reported: …` line and in a `reported` array in `enrolled.json`, `verification.json` and `live-lane.json`. A report never changes the exit code.
- **Tested guards.** Every new or changed guard has a test that fails when the guard is removed. The test asserts the full finding or report text, plus exit codes and stdout/stderr where a CLI is involved.
- **Generic code.** Gate code and Core.Tests assertions name no module and pin no module count.
- **Docs.** The README, both tool READMEs and `AGENTS.md` (copied byte-identical to `CLAUDE.md` and `.github/copilot-instructions.md`) state the new rules. So do the Command/Query attribute XML docs (the consent sentence).

**Never:**
- Delete or rewrite any vector, plan or inventory.
- Change production `src/` behavior; only XML docs change there.
- Enforce consent mechanically or with name heuristics.
- Edit `references/`, edit planning files other than the story's status row, or commit or push.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Covered | Current 21 vectors | Every gate passes; 6 shapes are listed as covered | N/A |
| Uncovered shape | The only vector of a shape is removed | C# test and validator fail with `<module>: Operation Shape '<key>' has no approved vector (operations: <names>).` | exit 1 |
| Stale vector | The vector's operation is absent from the restored Catalog | Existing stale finding | exit 1 |
| Version differs | Receipt or vector version ≠ restored package | Reported; the vector still runs | exit unchanged |
| Receipt binds an artifact | Top-level `artifactHash` in `approval.json` | Fail: the receipt must not bind an artifact hash | exit 1 |
| Uninventoried operation | A cataloged operation that no row mentions | Reported, public and internal | pass |
| Inventory guard | `include` row missing or mismatched; `withdraw`/`defer` contract present | Existing failure text | fail |
| Missing live kind | A module kind has no live vector with a plan | Live preflight fails, naming the module and kind | exit 1 |
| Vector without plan | Approved vector, no plan | Loopback only; no live case | N/A |
| Orphan plan | A plan with no approved vector | Live preflight fails | exit 1 |

</frozen-after-approval>

## Code Map

- `tests/Hexalith.McpCli.Core.Tests/EnrolledModuleCoverageTests.cs:15-44` -- production test. It reads manifest entries via reflection and builds a `CatalogProvider`. Add the shape gate and its removal tests here.
- `tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs:302-326` -- `Compare`. The included and excluded checks stay. The two `unexpected operation` adds at `:317-325` become reports.
- `tests/Hexalith.McpCli.Core.Tests/EnrolledInventoryCoverageGate.cs` -- forwards reports.
- `tests/Hexalith.McpCli.Core.Tests/InventoryCoverageTests.cs:95-225` -- the expected lists that contain `unexpected operation` move to report assertions.
- `src/Hexalith.McpCli.Core/Catalog/{OperationDescriptor,ModuleDescriptor,OperationRouting}.cs` -- the descriptor sources: `Kind`, `PlatformScope`, `AggregateIdAccessor`/`AggregateIdConstant`, `IdempotencyKeyRequired`, `Routing.ProjectionType`/`ProjectionActorType`, plus the module's `IdentifierKind`, `FixedTenant` and `WireTypeConvention`.
- `tests/Hexalith.McpCli.ConformanceHost/{Program.cs:57-70,*.csproj:10}` -- `--manifest-catalog` gains a `shape` per operation, and `--inventory` writes reports to stderr. Compile in `../Hexalith.McpCli.Core.Tests/OperationShape.cs`.
- `tools/conformance-vectors/v1/validate.py:254-308` -- `validate_vectors`:
  - Coverage reads an operation→shape object.
  - The package-version mismatch at `:280` becomes a report; an ID mismatch still fails.
  - The `--operations-file` array form is refused.
- `tools/conformance-vectors/v1/check_enrolled.py:18-37,171-190` -- `artifact_for`:
  - Return `(artifact, restored)`.
  - A version difference is reported; a top-level `artifactHash` is refused.
  - Stop passing `receipt['artifactHash']` to `verify`.
- `tools/conformance-vectors/v1/verify_artifact.py:222-235` -- read shapes from `--manifest-catalog`, store `shapes`/`reported` in the receipt, and copy `OperationShape.cs` into the isolated host.
- `tools/conformance-vectors/v1/run_loopback.py:743-815` -- add `_manifest_shapes`, and give `run_catalog` the shapes. Test patches of `_manifest_operations` need a matching `_manifest_shapes` patch.
- `tools/live-topology/live_plans.py:321-400`:
  - Use the restored version and hash for the selection binding.
  - Validate by shapes and require each declared kind to have a plan-backed vector.
  - Plans must be a subset of the approved vectors, and selections are the vectors that have plans.
  - Add an optional `reports`.
- `tools/live-topology/{run-vectors.py:20-31,ci.py:741-750}` and `.github/workflows/ci.yml:163` -- the expected live set becomes the approved vector files that have `plans/<operation>.json`.
- `tools/conformance-vectors/v1/modules/*/approval.json` -- remove the top-level `artifactHash`. Keep the Tenants `historicalCandidate`.
- Docs: `README.md:458,481,628`; Gateway boundary `:446`; `tools/conformance-vectors/v1/README.md:5,58-75,81-120`; `tools/inventory-coverage/v1/README.md` "Comparison and diagnostics"; `AGENTS.md:84`; `src/Hexalith.McpCli.Abstractions/Hexalith{Command,Query}Attribute.cs` summaries.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- there is no keyed-scenario entry yet. The rebind wording at `:781`, `:812` and `:813` is noted only in the review rows.
- Do not change: vectors, plans, inventories, `test_live_plans.py:49` (v1 count pin), `native-runtime.json`, `references/`.

## Tasks & Acceptance

**Execution:**
- [x] `tests/Hexalith.McpCli.Core.Tests/OperationShape.cs` (new) -- a record with the seven components. It has a static `From(ModuleDescriptor, OperationDescriptor)` and a `Key` such as `kind=query;identifierKind=string;…`. Single source of shape derivation.
- [x] `tests/Hexalith.McpCli.Core.Tests/ShapeCoverageGate.cs` (new) -- for each manifest entry, find its approval directory case-insensitively and read `module` and `vectorFilesSha256`. Count only hash-matching vectors, then fail each uncovered shape and report the covered ones. Generic gate.
- [x] `tests/Hexalith.McpCli.Core.Tests/{EnrolledModuleCoverageTests,OperationShapeTests}.cs`:
  - The production gate reports its shapes through test output.
  - Removing the only vector of a computed single-vector shape fails, naming that shape.
  - A table-driven test over fixture catalogs (Sample, Catalog.String, Catalog.Routing, Catalog.Explicit) shows that each component value changes the key.
- [x] `tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj` -- copy `tools/conformance-vectors/v1/modules/**` and `sample-*.json` to the output.
- [x] `InventoryCoverageGate.cs`, `EnrolledInventoryCoverageGate.cs`, `InventoryCoverageTests.cs` -- add an optional `ICollection<string>? reports`. Report `public operation X: reported, not failed; no inventory row mentions this cataloged operation.` and the internal variant with its type. An operation counts as mentioned when its name, or its descriptor's type, matches a target. Assert the full report and finding sets.
- [x] ConformanceHost `Program.cs` and `.csproj` -- add `shape`, write reports to stderr, and keep the `--inventory` stdout array.
- [x] `validate.py`, `test_validate.py` -- shapes and reports; CLI exit, stdout and stderr tests.
- [x] `check_enrolled.py`, `verify_artifact.py`, `run_loopback.py`, and the `test_enrolled.py`/`test_loopback.py` updates -- reported versions, the refused `artifactHash`, shapes in the receipts and `enrolled.json`.
- [x] `live_plans.py`, `run-vectors.py`, `ci.py`, `ci.yml`, plus `test_live_plans.py`/`test_lane.py`/`test_ci.py` -- per-kind live vectors, the orphan-plan failure, the plan-backed expected set and `reported`.
- [x] Both `approval.json` files -- drop the top-level `artifactHash`.
- [x] Docs and the XML docs listed in the Code Map -- the new rules and the consent sentence. In the vector README's approval rules, the live Command vector of a new enrollment must:
  - create an aggregate in a prerequisite;
  - submit a second Command to it with a caller-supplied idempotency key;
  - read the effect back with a postcondition Query. Sync `AGENTS.md` and run `scripts/check-agent-instructions-sync.sh`.
- [x] `deferred-work.md` -- add one entry under a new 5.12 heading: Parties and Tenants adopt the keyed second-Command live scenario at their next vector amendment.
- [x] `sprint-status.yaml` -- set the 5-12 status by hand and keep every comment.

**Acceptance Criteria:**
- Given the enrolled production Catalog and the 21 vectors, when `EnrolledModuleCoverageTests` runs, then it passes and reports 6 covered shapes (3 per module).
- Given the change, when CI's gates run locally, then they pass with no diff to any vector, plan or inventory. Those gates are the Release build with `-warnaserror`, Core and Manifest tests, both Python suites, `check_enrolled.py`, the live preflight and the topology-vector discovery assertion.
- Given the three agent entry points, when `scripts/check-agent-instructions-sync.sh` runs, then it passes.

### Review Findings

Code review pass 2 (bmad-code-review, 2026-11-10). The scope was code-only: commit `fdfe6a3` without `_bmad-output/` and `references/` (39 files, 3,283 diff lines). Pass 1 reviewed the uncommitted change and its patches went into the same commit, so no smaller since-pass-1 range exists. Non-story commit `c9a46a1` (Builds `52ea174` pins and policy) was left out.

Four layers ran and none failed: Blind Hunter (B1–B13), Edge Case Hunter (E1–E7), Verification Gap (V1–V3 gaps) and Acceptance Auditor (A1–A7).

Of 30 findings, 9 group into 7 patches. There is no decision; 2 are deferred and 19 are rejected.

Independent re-checks during triage:
- CI run 42849005018 at HEAD `c9a46a1` passed every job: `enrolled-module-conformance`, `topology-vector-discovery`, `ci / build-and-test` and `ci / aspire-tests`; only `performance-tests` was skipped. Run 42845755811 at `fdfe6a3` failed `build-and-test` and `topology-vector-discovery`. That matches the Builds-gitlink cause recorded in pass 1, which `c9a46a1` fixed; the failed-job logs could not be retrieved.
- The Acceptance Auditor reproduced AC1 at HEAD: `EnrolledModuleCoverageTests` passed 13 of 13 with six covered shapes, three per module. AC3: `scripts/check-agent-instructions-sync.sh` exit 0.
- A concurrent Story 5.6 session has uncommitted edits to `.github/workflows/ci.yml`, `scripts/verify-release-source.py`, `scripts/tests/test_paired_publication.py`, `.gitattributes` and `sprint-status.yaml`. No patch below edits those files, except the P2 test, which only reads `ci.yml`.

- [x] [Review][Patch] P1: no C# test pins pooled shape coverage, where one vector covers every operation of its shape
  - `ShapeCoverageGate.Check` fails a shape only when no hash-approved vector exists for any of its operations. That rule is what lets a newly decorated operation with an existing shape ship without a vector.
  - Every C# fixture gives each operation its own vector: `SampleApproval` writes all three sample vectors, the removal cases touch only the single-operation query shape, and production has 21 vectors for 21 operations.
  - So changing the test to `shape.VectorOperations.Count != shape.Operations.Count`, which is the old per-operation rule, passes every C# test. Only Python pins the pooled rule (`test_validate.py` `test_one_vector_covers_every_operation_of_its_shape`).
  - Fix: add a fact `OneVectorCoversEveryOperationOfItsSampleShape` that deletes `sample-rename`. It should assert no findings and the exact reports: `… covered by approved vector(s) for sample.create-item (operations: sample.create-item, sample.rename-item).` plus the unchanged query report.
  - (V1, medium) [tests/Hexalith.McpCli.Core.Tests/ShapeCoverageGate.cs:23]
- [x] [Review][Patch] P2: no test runs the `topology-vector-discovery` live-set filter
  - The inline heredoc keeps only vectors with `tools/live-topology/plans/<operation>.json`.
  - `CiWorkflowTests` only checks that the final condition string is in the text (`test_ci.py:2338`). With 21 plans for 21 vectors, dropping the filter changes nothing and every test passes. That breaks the frozen "Tested guards" constraint.
  - The same filter is tested in `ci.py` (`test_approved_vector_without_a_plan_is_loopback_only_and_not_expected_live`) and in `run-vectors.py` (`test_expected_live_set_is_every_approved_vector_with_a_companion_plan`).
  - Fix: in `CiWorkflowTests`, extract the `<<'PYTHON'` block from the job and run it with `python3 - <discovery.txt>` in a fixture root that holds one planned and one loopback-only vector. Accept the list without the loopback-only case, and reject it with exit 1 and the exact message when that case is expected.
  - Not changed: the C# two-directory branch from A1 (rejected below).
  - (V3, A1 part; low) [.github/workflows/ci.yml:165]
- [x] [Review][Patch] P3: the vector README says `EnrolledModuleCoverageTests` "applies the same rule", but the C# gate fails neither duplicate nor stale vectors
  - The preceding sentence is "A duplicate or stale vector also fails". `ShapeCoverageGate` silently drops a missing or hash-mismatched file, an unlisted file, a vector whose operation is absent, and duplicates. Only the Python gates (`approved_vectors`, `validate_vectors`) fail those cases, in the same CI job.
  - Fix: a direct wording correction. The C# test applies the same uncovered-shape rule, and the Python gates alone fail duplicate, stale, unlisted or changed vector files.
  - (B4, E7; low) [tools/conformance-vectors/v1/README.md:21]
- [x] [Review][Patch] P4: "the module-scoped tuple that McpCli's generic translation branches on" overclaims
  - `OperationExecutor.cs:102-182` also branches on `PropertyBindings` (Actor, Tenant and IdempotencyKey roles) and `EnvelopeFilledProperties`, which the frozen seven-component tuple leaves out.
  - The approved proposal (§1) says "the routing and envelope fields that McpCli's generic code branches on".
  - Fix: use the proposal's wording in the README and in the `OperationShape` summary. Core executor tests, not vectors, cover payload role bindings.
  - Not changed: adding components (intent-fixed, rejected in pass 1 BH3+ECH1).
  - (B1; low) [tools/conformance-vectors/v1/README.md:9]
- [x] [Review][Patch] P5: README says "A Contracts version change that alters no vector or inventory is reported, not failed", but the required live lane hard-requires Tenants Contracts 7.0.5
  - `ci.py` calls `native_cohort.verify_runtime_assets(…, 'Hexalith.Tenants.Contracts/7.0.5')`, and `native_cohort.manifest` requires `('Hexalith.Tenants.Contracts', '7.0.5')` from `native-runtime.json`.
  - So a version-only Tenants bump turns `ci / aspire-tests` red until the native cohort moves. The ledger note in pass 1 already calls that a separate selection.
  - Fix: a direct wording correction. The report-only rule covers the enrollment gates. The live lane's native runtime cohort (`tools/live-topology/native-runtime.json`) is a separate selection that moves with a Tenants release.
  - (E6; low) [README.md:460]
- [x] [Review][Patch] P6: the new live-plan test pins the restored module versions
  - `test_version_difference_is_reported_and_the_binding_uses_the_restored_package` asserts report text containing `restored package version 1.5.1` and `7.0.5`. A version-only Parties or Tenants bump then breaks it, against the story's intent that a release changing no operation needs no McpCli change beyond the pin.
  - Fix: build the expected report strings from the restored bindings, whose versions the test already checks against `project.assets.json`. Keep the full-text assertion.
  - (A2; low) [tools/live-topology/test_live_plans.py:429]
- [x] [Review][Patch] P7: the count-pin test name and its README trigger describe vectors, but the pin now counts companion plans
  - `test_all_21_approved_vectors_have_valid_plans` asserts 21 plan files, each with an approved vector. It no longer checks that every approved vector has a plan.
  - README "Update the v1 count pin … only when the approved v1 scope changes" misses that adding or removing a plan changes the pin even when v1 scope does not. For example, Epic 6 enrollment adds plans.
  - Fix: rename the test (for example `test_all_21_companion_plans_are_valid_for_approved_vectors`) and say that the pin counts companion plans and moves with each added or removed plan.
  - (B11; low) [tools/live-topology/test_live_plans.py:49]
- [x] [Review][Defer] D1: `AGENTS.md` still says "`run-vectors.py` invokes that wrapper for every vector" [AGENTS.md:102] — deferred: the fix edits the agent-context files, which also means `CLAUDE.md` and `.github/copilot-instructions.md` plus the sync check. After 5.12 the wrapper runs only plan-backed vectors (A3, low) Ledger: `deferred-work.md:983`.
- [x] [Review][Defer] D2: no test checks the `enrolled-module-conformance` `STAGING_JOBS` step names against `ci.yml` [scripts/verify-release-source.py:38] — deferred: pre-existing gap, since the old step name was not checked either. The rename is correct in both files today. A mismatch would block a paired release loudly at `validate_jobs`. The concurrent Story 5.6 session is editing `test_paired_publication.py` and both source files now (V2, low) Ledger: `deferred-work.md:989`.

Rejected:
- B1 (components part) low: adding payload bindings to the tuple is excluded by the frozen seven-component Intent (pass 1 BH3+ECH1). The wording part is P4.
- B2 low: no committed archive byte pin. Excluded by the frozen Intent ("Receipts drop the artifact-hash binding"); surfaced to the product owner in pass 1 (BH1).
- B3 low: the `artifactHash` refusal covers only the top-level key. The spec scopes it to the top level and keeps the Tenants `historicalCandidate`. `publishedArtifactBinding` is an evidence path, not a hash (pass 1 BH10). A key allowlist would be a new guard.
- B5 low: `ShapeCoverageGate` throws on a malformed receipt, accepts `../` names, and has no test with two case-variant directories. A throw fails the test loudly. Python `approved_vectors` fails non-exact names in the same job. A two-directory test needs a case-sensitive file system (a platform-conditional guard).
- B6 low: no enum-sync test. An unknown enum value throws in `OperationShape.From`, which fails every gate loudly.
- B7 low: live coverage is per kind, not per shape. That is the frozen Intent ("at least one live vector with a plan for each declared operation kind").
- B8 low: the keyed second-Command scenario is not gated. It is an authoring rule by Intent, tracked by the existing 5.12 ledger entry.
- B9 false: the shape facts return on an empty manifest. The sibling fact asserts the generic empty-Catalog error, and zero modules have zero shapes to cover.
- B10 low: the README operation list is unchecked. Pre-existing; every current operation is still an included row with a vector.
- B11: see P7.
- B12 low: duplicated parsers, two host launches and a repeated live-set rule. Efficiency and refactoring only, with no wrong result shown (pass 1 BH11/BH12).
- B13 false: the Python fixture pins the C# key on purpose. It is pass 1's VG1 real-host check, and the gates still compare keys opaquely.
- E1, E2 low: same as B5.
- E3 low: `CopyDirectory` runs before `try`. It only matters when production vectors are missing from the build output, and the test fails either way. The fix would add a guard.
- E4 false: `manifest_shapes` input comes only from the repository's own ConformanceHost serializer, so a non-list `operations` cannot occur.
- E5 false: loopback-only vectors never run live. `run_catalog` in `check_enrolled.py` still Core-validates every approved vector.
- A1 (C# part) low: same as B5. The CI part is P2.
- A4 low: asserting a single vector on the production removal target would pin production data (Design Notes: no hard-coded count). The sample fact pins the exact single-vector case.
- A5 low: the `test_live_plans.py:49` change is a recorded deviation, approved as pass 1 BH2. Reverting it would edit the spec.
- A6 low: the `STAGING_JOBS` rename follows the CI step rename and leaves behavior unchanged (recorded in pass 1).
- A7 false: AC2 at HEAD. CI run 42849005018 at `c9a46a1` passed every gate job, including live `aspire-tests`.

Code review pass 3 (bmad-code-review, 2026-11-10).
- **Pass 2 patches.** P1–P7 above were applied by another session in the local commit `38fbc43 fix: stories 5.12 5.6`, which also carries Story 5.6, so their rows are now checked.
- **Scope: code-only.** The diff is `fdfe6a3` plus only the 5.12 hunks of `38fbc43`: the C# tests, the `OperationShape` summary, both READMEs, `test_ci.py` and `test_live_plans.py`. It was built as a tree-snapshot diff from `fdfe6a3^`: 39 files, 3,354 lines.
- **Left out:** `_bmad-output/`, `references/`, the Story 5.6 hunks (census README paragraph, `ci.yml` census job, `STAGING_JOBS` census entry) and non-story commit `c9a46a1`.
- **Snapshot check.** The snapshot equals HEAD for every file except those that `c9a46a1` and 5.6 touch.

Four layers ran and none failed: Blind Hunter (B1–B13), Edge Case Hunter (E1–E8), Verification Gap (V1–V2 gaps) and Acceptance Auditor (A1–A5).

Of 28 findings, 7 group into 6 patches and 1 is deferred as already tracked. There is no decision, and 20 are rejected.

Independent re-checks during triage:
- The Acceptance Auditor reproduced AC1 at HEAD: `EnrolledModuleCoverageTests` passed 14 of 14, with six covered shapes, three per module. AC3: `scripts/check-agent-instructions-sync.sh` exit 0.
- AC2 was re-checked in part. The conformance-vector suite (185 tests), `test_live_plans.py` (48), and `CiWorkflowTests` plus `test_lane` (20) passed, and no vector, plan or inventory changed since `a851118`. Manifest tests, `check_enrolled.py`, the live preflight and the discovery job were not re-run.
- `38fbc43` is local only, one commit ahead of `origin/main`, so no CI run covers it. The last green run is 42849005018 at `c9a46a1`.
- During triage, a concurrent Story 5.6 session again had uncommitted edits to `.github/workflows/ci.yml`, `scripts/tests/test_paired_publication.py` and `tools/proprietary-surfaces/v1/`. No patch below edits those files.

- [ ] [Review][Patch] P1: no live preflight test runs the real `validate_vectors` with an uncovered shape or a vector version difference
  - `live_plans.preflight` passes `_manifest_shapes(head, package)` to `validate_vectors` and forwards the result with `report(vector_reports)`.
  - The mocked test (`test_live_plans.py:343-346`) ignores the arguments. `LiveKindCoverageTests` runs only the complete production set at matching versions.
  - `test_version_difference_is_reported_and_the_binding_uses_the_restored_package` patches `live_plans._load_json` for `approval.json` only, but `validate_vectors` reads vectors through `validate._load_json`.
  - So every test still passes if the shape map is replaced with `None` or `report(vector_reports)` is deleted. The first drops the live lane's shape and stale-vector recheck. The second drops every vector-version report from `live-lane.json` after a version-only module release. Both break the frozen "Tested guards" constraint.
  - Fix: add two `LiveKindCoverageTests` cases.
    - Patch `live_plans._manifest_shapes` to add `parties.extra` with its own key for the Parties package. Assert the exact `VectorError` `parties: Operation Shape '<key>' has no approved vector (operations: parties.extra).`
    - Patch `validate._load_json` so every vector's `package.version` is `0.0.1`. Assert the exact `…:/package/version: … differs from release artifact version …; reported, not failed` reports, built from the frozen vector paths and the restored versions.
  - (V2, A1; medium) [tools/live-topology/live_plans.py:391]
- [ ] [Review][Patch] P2: the companion-plan count pin counts every plan, so Folders enrollment must edit it
  - Design Notes say "Folders enrollment must not edit a count".
  - After pass 2 P7, `test_all_21_companion_plans_are_valid_for_approved_vectors` counts every `plans/*.json`. README says to update it "whenever a plan is added or removed, including when a new enrollment adds plans", and every enrollment needs at least one plan per declared kind.
  - Fix: count only plans whose module prefix is in `tools/conformance-vectors/v1/v1-scope.json` `requiredModules`, and still load and check every plan. README should say the pin moves only when a v1 module's plan is added or removed.
  - (A2; low) [tools/live-topology/test_live_plans.py:54]
- [ ] [Review][Patch] P3: `test_missing_live_kind_fails_naming_the_module_and_kind` hard-codes the current Parties query plans
  - It removes exactly `parties.get-party`, `parties.list-parties` and `parties.search-parties`. A Parties vector amendment that adds a planned query leaves one in place, so no `VectorError` is raised and the test fails. That goes against the pass 2 P6 rule that a module release needs no test edit.
  - Fix: derive the removed set from the approved Parties vectors whose `kind` is `query`.
  - (A4; low) [tools/live-topology/test_live_plans.py:414]
- [ ] [Review][Patch] P4: `verify_artifact.py` still raises "Artifact hash differs from the approved receipt."
  - Receipts can no longer carry an artifact hash, and enrollment never passes `expected_hash` (`test_enrolled.py:483`). The vector README calls `--expected-hash` a standalone candidate check.
  - Fix: name `--expected-hash` in the message, and assert the exact text in `test_wrong_artifact_hash_retains_failed_identity`, which matches only `hash differs` today.
  - (B12; low) [tools/conformance-vectors/v1/verify_artifact.py:184]
- [ ] [Review][Patch] P5: README says a newly decorated operation with an existing shape "needs no vector, plan, inventory or approval change", but a lint finding still needs an approved row
  - `DescriptionLintGate` in `EnrolledModuleCoverageTests` and `check_lint` (`verify_artifact.py:73-86`) require an operation's description lint findings to equal the `<module>-accepted-lint.json` rows exactly, each with an `approvalReference`. `tenants-accepted-lint.json` already holds eight rows.
  - Fix: a direct wording correction stating that a lint finding on the new operation still needs an approved accepted-lint row.
  - (E8; low) [README.md:468]
- [ ] [Review][Patch] P6: `EnrolledModuleCoverageTests` writes its reports only after its assertions pass
  - Both production facts call `ShouldBeEmpty()` before writing their `reported:` or `covered:` lines, so a failing run never shows them.
  - Example: a renamed operation fails as a missing `include` row, and the report naming the new, unmentioned operation never reaches the test output.
  - Fix: collect the findings, write every report, then assert.
  - (B5; low) [tests/Hexalith.McpCli.Core.Tests/EnrolledModuleCoverageTests.cs:37]
- [x] [Review][Defer] D1: no test ties the `enrolled-module-conformance` `STAGING_JOBS` step names to `ci.yml` [scripts/verify-release-source.py:39] — deferred: already tracked (`deferred-work.md:989`). The concurrent Story 5.6 session again has uncommitted edits to `scripts/tests/test_paired_publication.py` and `.github/workflows/ci.yml`, which is the collision that entry waits out (V1, low).

Rejected:
- B1 false: Python takes the module from the operation-name prefix. Catalog names are always `<module>.<part>` (`CatalogBuilder.cs:245`), and module names are dot-free kebab-case (`IsCanonicalPart`, `CatalogBuilder.cs:253,276-280`), so the Python and C# groupings agree.
- B2 low: `publishedArtifactBinding` stays in both receipts. It is an evidence pointer, not a hash (pass 1 BH10, pass 2 B3).
- B3 low: `ShapeCoverageGate` throws on a missing or malformed receipt and does not refuse `../` keys. A throw fails the test loudly, and Python `approved_vectors` fails non-exact names in the same job. The fix adds guards (pass 2 B5).
- B4 false: the shape facts return on an empty manifest. Zero modules have zero shapes, and the sibling fact asserts the generic empty-Catalog error (pass 2 B9).
- B6 low: queries carry `idempotencyKey=optional`. The frozen tuple allows only `required` or `optional`.
- B7 low: role bindings and envelope-filled members are not shape components, by the frozen seven-component intent (pass 1 BH3+ECH1, pass 2 B1).
- B8 low: the keyed second-Command scenario is not gated. It is an authoring rule by intent, tracked by the 5.12 ledger entry (pass 1 BH8, pass 2 B8).
- B9 low: the host launches twice per package. Efficiency only (pass 1 BH11, pass 2 B12).
- B10 low: the host source list lives in both the csproj and `HOST_SOURCES`. The pattern predates the story, and drift fails the isolated host loudly (pass 1 BH12).
- B11 false: the packaged fixture pins the C# key on purpose. It is pass 1's VG1 real-host check (pass 2 B13).
- B13 false: "replays all 21 operations" and "the seven approved Parties operations" are true today. Every current operation is an included row with its own vector, and a new operation moves the README list anyway (pass 2 B10).
- E1, E2 low: same as B3.
- E3 false: the hash read and the parse read both read committed repository files inside a test process, and no concurrent writer can reach them.
- E4 low: a case-only directory rename leaves a stale `PreserveNewest` copy. The inventories follow the same pattern, and CI builds fresh (pass 1 ECH4).
- E5 low: an empty production vector directory is never created before `finally`. That only happens when the vectors are missing from the build output, and the test fails either way (pass 2 E3).
- E6 low: blank or unqualified `--operations-file` keys are accepted. The file comes from the repository's own host, a misuse still fails loudly with shape or stale findings, and the fix adds a guard.
- E7 low: restored integrity relies on sidecars written by the restore. This is excluded by the frozen intent and was surfaced to the product owner (pass 1 BH1, pass 2 B2).
- A3 low: the CLI tests discard stdout. The `redirect_stdout(io.StringIO())` helper predates the story (`a851118` `test_enrolled.py:413`). Findings and reports are asserted in `enrolled.json`, `live-lane.json` and on stderr, and the stdout summary line is not a guard.
- A5 low: the artifact `/metadata/version` difference is a third report kind. The vector README documents it ("a different version is reported", `tools/conformance-vectors/v1/README.md:98`), `test_validate.py:204,778` pins it, and runner flows cannot reach it because the artifact is the restored package.

## Spec Change Log

## Review Triage Log

### Review pass 1 (2026-11-10)

Layers: Blind Hunter (BH), Edge Case Hunter (ECH) and Verification Gap (VG). The diff was against HEAD `d04e84c`, not baseline `a851118`, because concurrent commit `d04e84c` (Story 5.5 review pass 2) is unrelated to this story. Code only: `_bmad-output/` and `references/` are excluded.

| # | Finding | Verdict | Evidence | Route |
| --- | --- | --- | --- | --- |
| BH1 | Removing `artifactHash` leaves no committed byte pin; a substituted archive with the same ID and version passes | medium | Real. Integrity is NuGet content hash vs `project.assets.json`, which is restored, not committed. The frozen Intent drops the binding and keeps restored integrity unchanged (approved proposal P3/P5). | reject (excluded by intent; surfaced to the product owner) |
| BH2+VG-o | `test_all_21_approved_vectors_have_valid_plans` loads a plan for every vector, so the first loopback-only vector fails it | medium | Real. `test_live_plans.py:49-55` iterates every `*.vector.json` and calls `load_plan`. This contradicts the frozen matrix row "Vector without plan → loopback only". The v1 pin of 21 can survive if it counts plans. | patch |
| BH3+ECH1 | The shape omits payload role bindings, `EnvelopeFilledProperties` and `AggregateIdRequired` | low | Real but generic: Core executor tests cover those branches without module vectors. The frozen Intent fixes the seven-component tuple (amended AD-16). | reject (excluded by intent; surfaced to the product owner) |
| BH4 | Deleting plans shrinks the live set silently, down to one per kind | low | Real. The intent allows loopback-only vectors, and deleting a plan is a reviewed repository change. The fix would add new report surface. | reject |
| BH5 | Reports never reach CI annotations; C# test output is hidden for passing tests | low | Python `reported:` lines are on stderr in the CI job log, which are the channels the frozen Intent names. Annotations would be new surface. | reject |
| BH6 | C# prints covered shapes with the `reported:` prefix, which elsewhere means a non-failing anomaly | low | Real: `EnrolledModuleCoverageTests.cs:71-74` writes `"reported: " + report` for "is covered by approved vector(s)" lines. Direct correction. | patch |
| BH7+ECH2+ECH3 | C# `ShapeCoverageGate` silently drops tampered, missing or out-of-directory vectors; a malformed receipt throws | low | Python `approved_vectors` in the same CI job fails any added, removed or changed vector. A throw fails the test loudly. The conformance README has no "applies the same rule" sentence. | reject |
| BH8 | The new-enrollment keyed live-Command rule and the grandfather list are not enforced | low | The frozen Intent makes it an authoring rule; CI checks only per-kind coverage. Tracked by the 5.12 deferral. | reject (excluded by intent) |
| BH9 | README "needs no McpCli change beyond the package pin" overclaims, because the README operation list and counts must also move | low | Real: README pins each module's operations, and the README-sync rule requires updating them. Direct wording correction. | patch |
| BH10 | README "Current enrollment binds Contracts 7.0.5 to the … approval" and the CI step "Validate approved artifacts, complete vectors…" keep the old model | low | Real: `README.md:483`, `.github/workflows/ci.yml:118`. Direct wording correction. The `publishedArtifactBinding` field is an evidence pointer, not a hash; it stays. | patch |
| BH11 | `--manifest-catalog` launches twice per package, and three parsers can diverge | low | Efficiency and refactoring only; no wrong result shown. | reject |
| BH12 | The live-set rule and the host source list are duplicated | low | `ci.py` and `ci.yml` recompute independently by design ("Independently require…"). The source-list pattern predates this story. | reject |
| BH13 | No fixture pins the precedence inside `OperationShape.From` | false | `routing-fixture.interface-item` declares both `ProjectionType` and `ProjectionActorType` and is pinned to `projectionActorType`. Accessor/constant and `PlatformScope`/`FixedTenant` cannot coexist under Catalog rules. | reject |
| VG1 | No test checks the shape key the real host emits; Python trusts any opaque value | (pre-verified gap) | Mocked keys only. The real-host run has full vector sets, so a wrong partition still passes. | patch |
| VG2 | No test checks that `EnrolledInventoryCoverageGate` forwards reports | (pre-verified gap) | Dropping the `reports` argument at `EnrolledInventoryCoverageGate.cs:34` passes every test. | patch |
| ECH4 | A stale `PreserveNewest` bin copy keeps a deleted vector locally | low | Same pattern as the inventories; CI builds fresh. | reject |
| ECH5 | The `--manifest-catalog` and `--full-catalog` operation sets could differ | false | In the single-package isolated host, both derive from the same manifest assemblies. | reject |
| ECH6 | A directory named `<op>.json` under `plans/` raises `IsADirectoryError` | false | Not a reachable repository state, and the failure is loud. | reject |
| ECH7 | `run_loopback` drops collected reports when a later selection fails validation | low | The run still fails loudly; only non-failing notes are lost on a failing run. | reject |
| ECH8 | Public/internal divergence for unmentioned operations became a report instead of a failure | medium | Real: `RejectsPublicDiscoveryMismatch("extra")` now expects only a report for a public-only phantom `sample.extra`. The intent reports only cataloged operations present on both surfaces. | patch |

**Patch outcome.** All seven patch groups were applied (BH2+VG-o, BH6, BH9, BH10, VG1, VG2, ECH8). The CI step rename required the matching `scripts/verify-release-source.py` `STAGING_JOBS` entry. The patch had rewritten `InventoryCoverageGate.cs` with LF endings; CRLF was restored. Re-verification passed: sample loopback (both Operation Shapes from the real host), Release build `-warnaserror`, Core.Tests 915/0 failed, the conformance-vector suite, `scripts/tests`, `check_enrolled.py` (6 shapes, 0 reported, full-v1 accepted), 21 discovery cases and agent-instruction sync. Five Manifest `DependencyPolicyTests`, 9 live-topology subtests and the live preflight fail only on the pre-existing Builds gitlink move in `efcda9e` (ModelContextProtocol 2.4.0 and Caching.Abstractions 10.0.14 restored against the policy's 2.3.1 and 10.0.13, workflow pins still `567604b`). With only that dependency check bypassed for diagnosis, the preflight gives `preflight-only` with 21 selections and nothing reported.

**Ledger impact (proposal §5 ledger note).** `deferred-work.md:781` (Tenants `GetTenantUsers`) and `:812-813` (Tenants bootstrap) assume "the usual McpCli artifact/vector rebind". After 5.12 a version-only rebind is a reported difference and needs no vector or approval change. The upstream release and pin move remain, as does the separate `native-runtime.json` cohort selection for `:812-813`. `:555` (Story 4.10 history) and `:959` (Folders PD10) are unaffected. No existing entry is edited (legacy ledger).

## Design Notes

- **No hard-coded count.** The count of six is verified in evidence, never asserted in a test. Folders enrollment must not edit a count.
- **Removing `artifactHash`.** The field is removed and refused because an ignored field would look like a binding. The approval-evidence files it pointed to stay unchanged.
- **Live-kind rule placement.** The per-kind live rule lives in the live preflight, which already owns plan binding. `check_enrolled.py` stays loopback-only.
- **Shape transport.** Shapes travel through `--manifest-catalog`, the one place where the C# host already enumerates operations per package.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` -- expected: 0 warnings.
- `dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release`, then the same for `Manifest.Tests` -- expected: pass.
- `python3 -m unittest discover -v -s tools/conformance-vectors/v1 -p 'test_*.py'` and `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` -- expected: OK.
- `python3 tools/conformance-vectors/v1/check_enrolled.py --output <scratch>/enrolled` -- expected: exit 0, with 6 shapes in `enrolled.json`.
- `python3 tools/live-topology/run-vectors.py --output <scratch>/live --preflight-only` -- expected: `PREFLIGHT-ONLY`, 21 selections.
- CI `topology-vector-discovery` list assertion -- expected: 21 vector cases plus smoke and boundary.
- `bash scripts/check-agent-instructions-sync.sh` -- expected: exit 0.

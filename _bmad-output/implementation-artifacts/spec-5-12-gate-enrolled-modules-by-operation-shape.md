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

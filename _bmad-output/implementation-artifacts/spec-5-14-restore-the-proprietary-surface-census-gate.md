---
title: '5.14 Restore the proprietary surface census gate'
type: 'bugfix'
created: '2026-11-27'
status: 'done'
baseline_commit: '8e242c5ec916b22b6c578a02f9f127f7d51c9ccd'
route: 'dispatch'
review_loop_iteration: 0
story_key: '5-14-restore-the-proprietary-surface-census-gate'
context:
  - '{project-root}/tools/proprietary-surfaces/v1/README.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The proprietary surface census fails at the 18-root candidate gitlinks (`14b2ffb4`: 35 errors including unapproved root `references/Hexalith.CiCd`, 95 rejected surfaces, 40 stale entries) and is not executed by `.github/actions/after-unit-tests/action.yml` (which also receives only 5/18 submodules).

**Approach:** Extend `v1` amendments and v2 approval receipts with optional `addRoots` to admit `references/Hexalith.CiCd`, stop `Exists`-guarded `GetPathOfFileAbove` lookups at the inspected root boundary, apply hash-bound amendment `1.0.14` under the requesting maintainer's explicit delegation (renewing drifted exclusions/closures, classifying new surfaces, admitting `Hexalith.CiCd` with standard PE07 prefixes, and retiring the 40 stale allowances), and wire non-recursive direct-root initialization plus `check.py` execution into `.github/actions/after-unit-tests/action.yml`. Implement and verify locally without committing or pushing, leaving `sprint-status.yaml` at `in-progress` pending hosted CI capture on the pushed SHA.

## Boundaries & Constraints

**Always:**
- Preserve `baseline.json`, `legacy-receipts.json`, and prior amendments/receipts (`1.0.1`–`1.0.13`) byte-identical; validate `addRoots` in `load_policy()` and v2 receipt `authorization` (rejecting duplicates, invalid gitlinks/owners/classifications, or unauthorized root additions).
- Stop `resolve_upward_import` at the inspected root boundary only when the `GetPathOfFileAbove` import is guarded by an exact `Exists(...)` (or nonempty) guard; keep unguarded escapes, literal parent-tree imports, and committed links refused.
- Inspect committed Git objects only (`protocol.allow=never`, `GIT_NO_LAZY_FETCH=1`, `GIT_NO_REPLACE_OBJECTS=1`, nested checkout disabled); keep output passing `evidence_redaction.py` and `scan-evidence-secrets.py`.
- Wire `check.py` (initializing remaining committed `.gitmodules` direct roots with `-c submodule.recurse=false` and retaining sanitized JSON in diagnostics) in `.github/actions/after-unit-tests/action.yml`; keep `test_census.py` local/on-demand outside blocking product CI.
- Guard every new scanner, policy, or CI-hook check with a removal-sensitive test; verify unapproved-root, unapproved-surface, and stale/drifted-evidence refusal fixtures fail closed; keep `python3 references/Hexalith.Builds/check.py` passing.

**Never:**
- Edit `Hexalith.CiCd`-owned files (`.github/workflows/**`, `.github/hexalith-ci.json`, `.github/dependabot.yml`, `references/Hexalith.Builds`), modify `references/**`, or initialize nested submodules.
- Weakening refusal guards, adding non-PE07 directory exemptions, asserting workflow YAML text in tests, or committing/pushing during this build.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Clean 18-root candidate | `HEAD` (`14b2ffb4`) with all 18 direct roots, no nested checkout | `check.py` exits 0, `status: "passed"`, 0 errors, 0 rejected, 0 stale, sanitized JSON to `--output` | N/A |
| Approved `addRoots` amendment | `1.0.14` adds `references/Hexalith.CiCd` with matching v2 receipt `authorization.addRoots` | Root admitted, scanned, and PE07 exclusions validated; prior `1.0.1`–`1.0.13` receipts without `addRoots` stay valid | Missing/mismatched `addRoots` in receipt or duplicate root fails closed |
| Unapproved root | `.gitmodules` declares root absent from baseline + `addRoots` | Exits 1 (`unapproved-root`) | Fail closed |
| `GetPathOfFileAbove` guarded escape | Submodule `Directory.Build.props` imports `GetPathOfFileAbove('Directory.Build.props', '$(MSBuildThisFileDirectory)../')` with `Condition="Exists('$(Parent)')"` while parent workspace has `Directory.Build.props` | Stops at inspected root boundary; no `unsafe-import-path` error | Unguarded upward import or committed link still fails closed |
| Unapproved surface / drifted evidence | Fixture adds new MCP/CLI/executable/publication surface or alters approved source/closure/exclusion hash/`sourceRevision` | Exits 1 (`new-proprietary-surface`, `allowance-signal-or-source-drift`, or `excluded-*-drift`) | Fail closed |
| Partial CI submodules | Hosted runner starts with 5/18 submodules | Hook helper initializes remaining committed `.gitmodules` direct roots (`submodule.recurse=false`, never nested) then runs `check.py` and saves report | Missing/uninitialized root or census failure exits non-zero |

</frozen-after-approval>

## Code Map

- `tools/proprietary-surfaces/v1/check.py:535-728,936-957,1114-1135,2594-2684` -- Extend `load_policy()` and `validate_approval_evidence()` with optional `addRoots` (validated against `roots` and v2 `authorization`); update `resolve_upward_import` / `project_metadata` to stop guarded `GetPathOfFileAbove` at the inspected root boundary; keep `scan()` and refusal checks intact.
- `tools/proprietary-surfaces/v1/amendments.json`, `tools/proprietary-surfaces/v1/amendments/1.0.14.json`, `tools/proprietary-surfaces/v1/amendments/1.0.14-approval.json` -- Append hash-bound `1.0.14` amendment and v2 delegated-repair receipt admitting `references/Hexalith.CiCd` + its PE07 prefixes, renewing the 13 drifted exclusions and 9 drifted allowance closures, classifying the 86 + 11 new surfaces and 5 unmodeled-script/generated-source/JSON files, and removing the 40 stale allowances.
- `tools/proprietary-surfaces/v1/test_census.py:24,1944-1994` -- Update `test_absent_upward_import_respects_the_exact_nonempty_guard` / `test_upward_import_refuses_opaque_targets_and_unreadable_parent_metadata` to pin guarded vs. unguarded upward-import rules; add removal-sensitive tests for `addRoots` validation, receipt binding, unapproved-root, unapproved-surface, and stale/drifted-evidence refusal.
- `tools/proprietary-surfaces/v1/README.md:257-261,413-552` -- Document `addRoots`, guarded upward-import boundary semantics, and Continuation `1.0.14`.
- `scripts/product_ci.py:170-198`, `scripts/tests/test_product_ci.py`, `.github/actions/after-unit-tests/action.yml:6-46` -- Add a census helper/phase in `scripts/product_ci.py` (initializing missing committed `.gitmodules` direct roots with `-c submodule.recurse=false` and running `tools/proprietary-surfaces/v1/check.py --output <diagnostics>/census.json`), invoke it in `.github/actions/after-unit-tests/action.yml`, upload diagnostics, and add unit tests in `scripts/tests/test_product_ci.py`.
- `_bmad-output/implementation-artifacts/sprint-status.yaml:107` -- Set `5-14-restore-the-proprietary-surface-census-gate` to `in-progress` noting local completion and pending hosted CI verification (AC3).

## Tasks & Acceptance

**Execution:**
- [x] `tools/proprietary-surfaces/v1/check.py` -- Support optional `addRoots` in `v1` amendments and v2 approval receipts (preserving backward compatibility for `1.0.1`–`1.0.13`), and stop `Exists`/nonempty-guarded `GetPathOfFileAbove` at the inspected root boundary while keeping unguarded/link refusals -- resolves `unapproved-root` and the 16 upward-import errors.
- [x] `tools/proprietary-surfaces/v1/amendments/1.0.14.json`, `1.0.14-approval.json`, `amendments.json` -- Author and chain `1.0.14` under explicit maintainer delegation covering `Hexalith.CiCd` admission + PE07 prefixes, 13 drifted exclusions, 5 unmodeled-script/generated-source/JSON exclusions, 9 drifted allowance closures, 86 + 11 triaged surfaces, and 40 stale-allowance removals -- brings all 18 roots to 0 errors, 0 rejected, 0 stale.
- [x] `tools/proprietary-surfaces/v1/test_census.py` -- Add removal-sensitive tests for `addRoots` validation/refusal, guarded vs. unguarded `GetPathOfFileAbove`, unapproved-surface refusal, and drifted-evidence refusal -- protects every new and existing guard.
- [x] `scripts/product_ci.py`, `.github/actions/after-unit-tests/action.yml`, `scripts/tests/test_product_ci.py` -- Add non-recursive direct-root initialization and `check.py` execution with sanitized JSON retention to the Linux product hook (keeping `test_census.py` local-only) and unit-test init/failure/no-recurse behavior -- restores blocking CI execution without touching `Hexalith.CiCd`-owned files.
- [x] `tools/proprietary-surfaces/v1/README.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Document `addRoots`, guarded upward-import semantics, and `1.0.14`, and set Story 5.14 to `in-progress` pending hosted CI capture.

**Acceptance Criteria:**
- Given the committed 18-root candidate (`14b2ffb4`) with nested checkout disabled, when `tools/proprietary-surfaces/v1/check.py` runs, then it exits 0 with `status: "passed"`, 0 errors, 0 rejected surfaces, 0 stale entries, clean secret scan, and byte-identical prior lineage (`baseline.json` and `1.0.1`–`1.0.13`).
- Given `tools/proprietary-surfaces/v1/test_census.py`, when run locally, then all existing and new fixtures pass, proving unapproved-root, unapproved-surface, unguarded-upward-import, and stale/drifted-evidence inputs fail closed.
- Given `.github/actions/after-unit-tests/action.yml` and `scripts/product_ci.py`, when `scripts/tests/test_product_ci.py` and `references/Hexalith.Builds/check.py` run, then all tests pass, non-recursive direct-root initialization and census failure propagation are verified, no `Hexalith.CiCd`-owned file is modified, and `sprint-status.yaml` stays `in-progress` pending hosted CI verification on the pushed SHA.

## Implementation Notes

- Extended `tools/proprietary-surfaces/v1/check.py` with `validate_root()` + optional `addRoots` in `v1` amendments and v2 approval receipts, guarded root-boundary termination in `resolve_upward_import()`, document-local idempotency-guard proof (`INEQUALITY_GUARD`) for absent fallback imports, and exact-file verified exclusion import satisfaction (`excluded_files`) in `scan_tree()`/`project_metadata()`.
- Chained amendment `1.0.14` (`629341c7...`) and v2 receipt `1.0.14-approval.json` (`07ce14a7...`) admitting `references/Hexalith.CiCd` (`PN10`) + PE07 prefixes, renewing 13 drifted exclusions, adding 5 exact-file exclusions, renewing 11 drifted allowances, classifying 99 new surfaces (including 5 `Hexalith.Memories.IntegrationTests` `.cs` files and 10 `Hexalith.CiCd` templates), and retiring 113 stale allowances (40 visible initially + 73 revealed once all 18 roots reached `inspectionComplete: true`).
- Wired `scripts/product_ci.py linux-census` (non-recursive direct-root init + `check.py --output <diagnostics>/census.json`, `test_census.py` local-only) into `.github/actions/after-unit-tests/action.yml` with tests in `scripts/tests/test_product_ci.py` and docs in `tools/proprietary-surfaces/v1/README.md`.
- Verified independently: `test_census.py` (233/233 OK), `check.py` (exit 0, `status=passed`, 18/18 roots, 0 errors, 0 rejected, 0 stale), `scripts/tests` (75/75 OK), `scan-evidence-secrets.py` (clean, 0 findings), and zero diff across protected CI/CD files and prior lineage (`baseline.json`, `legacy-receipts.json`, `1.0.1`–`1.0.13`). Left `sprint-status.yaml` at `in-progress` pending post-push hosted CI capture (AC3) and post-commit `references/Hexalith.Builds/check.py`.
- Review pass 1 patches applied (all 30 surviving findings fixed: `execute()` `cwd`/`environment` threading, hardened `direct_submodule_paths`/`submodule_initialized` with pinned-commit check and `GIT_TERMINAL_PROMPT=0`, aligned `900s` outer / `480s`+`300s` inner timeouts, symmetric `addRoots` v2 receipt validation, `directory == '..'` guarded upward-import boundary, sound document-local `local_proven`/`local_certain`/opaque-import/empty-tag tracking, `compilation_closure` `excluded_files` support, expanded removal-sensitive tests, and README alignment). Post-patch verification passed: `test_census.py` (234/234 OK), 18-root `check.py` (exit 0, `status=passed`, `version=1.0.14`, 0 errors, 0 rejected, 0 stale), `scan-evidence-secrets.py` (clean, 0 findings), `scripts/tests` (78/78 OK), and zero diff on protected files. No commit or push performed; `sprint-status.yaml` remains `in-progress` pending post-commit `references/Hexalith.Builds/check.py` and hosted CI capture (AC3).
- Hosted CI AC3 capture (2026-11-28): `python3 references/Hexalith.Builds/check.py` exited 0 and `a5721f0c95f9c0a2ae49fec4be92835eb1837840` was pushed to `origin/main`. In hosted run `https://github.com/Hexalith/Hexalith.McpCli/actions/runs/46085187622` (`ci / Build and tests`, job `140792988557`), `Run proprietary surface census across committed direct roots` (`scripts/product_ci.py linux-census`) succeeded in 150.5s: initialized the 13 missing committed `.gitmodules` direct roots with `-c submodule.recurse=false`, ran `tools/proprietary-surfaces/v1/check.py`, and uploaded sanitized `census.json` (480,667 bytes, SHA-256 `072ed08b8cef45d45d4e8583889bb01caae65e567c8176b55af806bd871ad259`; `parentRevision=a5721f0c95f9c0a2ae49fec4be92835eb1837840`, `status=passed`, `policy.version=1.0.14`, 18/18 repositories passed, 513/513 surfaces approved, 0 errors, 0 rejected, 0 stale; `scan-evidence-secrets.py` clean across all 46 diagnostics files). Overall job `ci / Build and tests` timed out later (exit 124 after 3300s) in `linux-conformance` during `tools/live-topology` Python self-tests (unrelated to Story 5.14; tracked by Story 5.26). Flipped `5-14-restore-the-proprietary-surface-census-gate` to `done` in `sprint-status.yaml`.

## Spec Change Log

## Review Triage Log

### Review pass 1 (2026-11-28)

Layers: Blind Hunter (BH1–BH13), Verification Gap (VG1–VG6, VGO1), Edge Case Hunter (ECH1–ECH11). Diff `/tmp/mcpcli-5-14-full-diff.patch` against `8e242c5ec916b22b6c578a02f9f127f7d51c9ccd`.

| # | Finding | Verdict | Evidence | Route |
| --- | --- | --- | --- | --- |
| BH1 | `initialize_direct_submodules(cwd=...)` invokes `execute()` with hardcoded `cwd=ROOT` (`scripts/product_ci.py:232-241`) | medium | Verified: `execute()` (`product_ci.py:28`) always runs in `ROOT`, ignoring `cwd`. | patch |
| BH2 | Missing submodule hardening (`protocol.file.allow=never`, `--literal-pathspecs`, `--checkout`, `url`/control-char/overlap/`160000` checks, intermediate symlink check, and pinned commit object check) (`scripts/product_ci.py:195-241`) | high | Verified: pre-initialized submodule missing `HEAD` gitlink commit skips update and fails `check.py`; missing hardening vs `ci_pipeline.py:191-204`. | patch |
| BH3 | `git submodule update` runs without `GIT_TERMINAL_PROMPT=0` (`scripts/product_ci.py:237`) | medium | Verified: `run_owned` inherits env without disabling terminal prompts; inaccessible submodule could hang until timeout. | patch |
| BH4 | Outer `timeout 600` in `.github/actions/after-unit-tests/action.yml:17` vs `600 + 600` inner timeouts in `scripts/product_ci.py:237,249` | medium | Verified: outer budget is smaller than sum of inner budgets; slow init could kill `check.py` before writing `census.json`. | patch |
| BH5 | Missing unit tests for real `submodule_initialized()`, `linux_census` `require_source` guards, skip-init when all initialized, and `direct_submodule_paths` edge cases (`scripts/tests/test_product_ci.py:259-321`) | high | Verified: `submodule_initialized` is mocked in every test and `linux_census` dirty/drift guards are untested. | patch |
| BH6 | Asymmetric `addRoots` key-presence check allows receipt `addRoots: []` when amendment omits `addRoots`; v1 receipt `addRoots` refusal untested (`tools/proprietary-surfaces/v1/check.py:555-557`, `test_census.py:748-751`) | medium | Verified: `amendment.get(key, [])` coerces missing key to `[]`, contradicting `README.md:478-480`. | patch |
| BH7 | `compilation_closure()` ignores `excluded_files`; directory-exclusion import refusal untested (`tools/proprietary-surfaces/v1/check.py:1443-1445`) | medium | Verified: `compilation_closure` passes `excluded_files=None` and unfiltered `metadata_paths`, diverging from `scan_tree`. | patch |
| BH8 | `resolve_upward_import(..., stop_at_root=True)` allows starting multiple levels above root (`../../`) and skips boundary check when `workspace is None` (`tools/proprietary-surfaces/v1/check.py:969-976`) | medium | Verified: `all(part == '..' ...)` accepts `../..` and arbitrary `../../../../` when `workspace is None`. | patch |
| BH9 | `local_proven`/`doc_guaranteed`/`doc_modified` soundness gaps: uninspected imports don't clear `local_proven`/`local_certain`, empty `<Prop />` omitted from `local_modified`, `doc_guaranteed` caches caller-dependent values and cyclic re-entry (`tools/proprietary-surfaces/v1/check.py:1030-1278`) | high | Verified: SDK/excluded/dynamic imports leave stale `local_proven`; empty `<Prop />` misses `local_modified`; `doc_guaranteed` depends on external `certain`. | patch |
| BH10 | Missing removal-sensitive tests for `INEQUALITY_GUARD` refusal guards (`Target`, nested gitlink, multiple inequalities, intervening conditional import) (`tools/proprietary-surfaces/v1/test_census.py:4015-4055`) | high | Verified: none of those four guard paths are asserted in `test_census.py`. | patch |
| BH11 | `README.md:265-268` documents `INEQUALITY_GUARD` only for preceding imports, omitting direct `<PropertyGroup>` declarations and carried-guard use | low | Verified: `check.py:1131-1135,1117` also populates `local_proven` from direct `<PropertyGroup>` and uses `refuted()` for carried proofs; direct doc fix. | patch |
| BH12 | `1.0.14.json` exact-file exclusion of `Hexalith.Memories.IntegrationTests.csproj` relies on source-level signal scan rather than compilation closure for neutral `.cs` files in that test directory | low | Verified: generated `obj/` Compile item remains a coverage error per `README.md:248`, and `scan_tree` still scans all `.cs` files for MCP/CLI signals; document scope limit explicitly in `README.md` Continuation `1.0.14`. | patch |
| BH13 | Redundant `isinstance(amendment.get('addExclusions', []), list)` at `tools/proprietary-surfaces/v1/check.py:699` | low | Verified: already checked at `check.py:662`; direct 1-line deletion. | patch |
| VG1 | `product_ci.submodule_initialized` is mocked in every test and never executed (`scripts/product_ci.py:220-229`) | high | Pre-verified gap: matches BH5. | patch |
| VG2 | `linux_census` pre- and post-execution `require_source` guards are untested (`scripts/product_ci.py:245-246,250`) | high | Pre-verified gap: matches BH5. | patch |
| VG3 | Legacy v1 approval receipt refusal of `addRoots` is untested (`tools/proprietary-surfaces/v1/check.py:573-576`) | high | Pre-verified gap: matches BH6. | patch |
| VG4 | `INEQUALITY_GUARD`/`local_proven` boundaries (nested gitlink, `<Target>`, post-import invalidation) are untested (`tools/proprietary-surfaces/v1/check.py:1070-1276`) | high | Pre-verified gap: matches BH10. | patch |
| VG5 | `resolve_upward_import` sibling-directory guard (`all(part == '..' ...)`) has no test (`tools/proprietary-surfaces/v1/check.py:969-976`) | medium | Pre-verified gap: guarded `GetPathOfFileAbove` starting in `../shared` is untested. | patch |
| VG6 | `validate_root` enclosing-parent overlap check (`other.startswith(path + '/')`) is untested (`tools/proprietary-surfaces/v1/check.py:540`) | medium | Pre-verified gap: only child overlap is tested at `test_census.py:3951`. | patch |
| VGO1 | `initialize_direct_submodules(cwd=...)` calls `execute()` with hardcoded `cwd=ROOT` (`scripts/product_ci.py:232-241`) | medium | Verified: same defect as BH1. | patch |
| ECH1 | `initialize_direct_submodules(cwd=...)` runs `execute()` in hardcoded `ROOT` (`scripts/product_ci.py:232-241`) | medium | Verified: same defect as BH1/VGO1. | patch |
| ECH2 | Already-initialized submodule checkout missing pinned `HEAD` commit skips update and fails `check.py` (`scripts/product_ci.py:220-238`) | high | Verified: same defect as BH2. | patch |
| ECH3 | `.gitmodules` overlapping submodule paths or control characters not rejected (`scripts/product_ci.py:205-215`) | medium | Verified: same defect as BH2. | patch |
| ECH4 | Asymmetric `addRoots` key-presence check in v2 receipt validation (`tools/proprietary-surfaces/v1/check.py:555-557`) | medium | Verified: same defect as BH6. | patch |
| ECH5 | Imported file modifying locally-settled property does not discard it from `local_certain` (`tools/proprietary-surfaces/v1/check.py:1221-1224`) | high | Verified: same root cause as BH9. | patch |
| ECH6 | `doc_guaranteed` caches values derived from external `certain` properties (`tools/proprietary-surfaces/v1/check.py:1030-1031`) | high | Verified: same root cause as BH9. | patch |
| ECH7 | Empty `<Prop />` tag omitted from `local_modified` before caller defines property (`tools/proprietary-surfaces/v1/check.py:1108-1110`) | high | Verified: same root cause as BH9. | patch |
| ECH8 | `exists_guard_truth` for `<Import Condition="...">` runs after `visit(candidate)` (`tools/proprietary-surfaces/v1/check.py:1221-1235`) | medium | Verified: same root cause as BH9. | patch |
| ECH9 | `compilation_closure` does not honor `excluded_files` (`tools/proprietary-surfaces/v1/check.py:1444-1445`) | medium | Verified: same defect as BH7. | patch |
| ECH10 | Spec draft estimate text lists 40 stale / 86+11 surfaces vs 113 stale / 99 new in `1.0.14.json` | false | Disproved as a code defect: `1.0.14.json` counts are exact for the complete 18-root scan and documented in `Implementation Notes` and `README.md`; findings whose fix edits this build's spec are rejected. | reject |
| ECH11 | Missing removal-sensitive tests for v1 `addRoots` refusal, `target_defined` blocking `INEQUALITY_GUARD`, and directory-exclusion Import refusal (`tools/proprietary-surfaces/v1/test_census.py:3852-4058`) | high | Verified: matches BH6/VG3, BH10/VG4, BH7. | patch |

## Verification

**Commands:**
- `python3 -m unittest discover -v -s tools/proprietary-surfaces/v1 -p 'test_*.py'` -- expected: all census unit and refusal tests pass.
- `python3 tools/proprietary-surfaces/v1/check.py --output /tmp/mcpcli-census-5-14.json` -- expected: exit 0, `status: "passed"`, 18/18 roots, 0 errors, 0 rejected, 0 stale.
- `python3 scripts/scan-evidence-secrets.py /tmp/mcpcli-census-5-14.json` -- expected: exit 0.
- `python3 -m unittest discover -v -s scripts/tests -p 'test_*.py'` -- expected: all product CI script tests pass.
- `python3 references/Hexalith.Builds/check.py` -- expected: exit 0 (before push; confirms zero owned CI/CD drift).

**Manual checks (if no CLI):**
- After pushing the candidate SHA, confirm hosted `ci / Build and tests` initializes all 18 direct roots without nested checkout, executes `tools/proprietary-surfaces/v1/check.py`, uploads sanitized `census.json` in `mcpcli-linux-product-diagnostics`, and passes.

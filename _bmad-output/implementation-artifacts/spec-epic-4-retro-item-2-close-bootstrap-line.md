---
title: 'Close the bootstrap release line (Epic 4 retrospective F2)'
type: 'bugfix'
created: '2026-11-06'
status: 'in-review'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '9b44fe2026efa4b9234dd6a5c53e068b752a1837'
context:
  - '{project-root}/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** AD-17 allowed one Abstractions bootstrap before decorated Contracts existed. Repeated Abstractions-only publications and marker/environment bypasses left that release line open after the paired tool shipped.

**Approach:** Enforce NuGet-based closure, pin verification-only historical recovery, and record the owner's separate decisions on Abstractions 1.1.0 and 2.0.0.

**Approved decisions (2026-11-06):** After receiving the evidence and per-version recommendations, the requesting owner instructed "apply recommended". Accept Abstractions 1.1.0 and, separately, 2.0.0 as fixed historical AD-17 process deviations. Neither publication is reclassified as compliant; approval grants no future bootstrap exception and does not change the retrospective verdict. Retain historical verification only: fixed tag/SHA bindings, already-public package required, no NuGet publication key and no push operation in that path.

## Boundaries & Constraints

**Always:** Preserve `9b44fe2026efa4b9234dd6a5c53e068b752a1837`, concurrent work and all existing integrity gates. Recheck HEAD and validate each exact full message before committing. Finish with green hosted CI on `main` and report its run ID.

**Never:** Publish packages, mutate tags, update dependencies, weaken gates, touch Epic 5, change the retrospective verdict, or treat platform-scope approval as publication approval. Complete item 2 only after guards, decision and verification.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected behavior | Error handling |
|---|---|---|---|
| Closed publication | Tool published; any marker/environment state | Refuse Abstractions-only push | Nonzero; no push |
| Uncertain evidence | Feed error, malformed response, uncertain absence | Refuse | Fail closed |
| Ordinary dispatch | `bootstrap`, no recovery version | Refuse before approval/credentials | Historical recovery required |
| Historical verification | Explicit pinned tag/SHA; package public | Verify source, receipt, public contents and consumer | No push |
| Invalid recovery | Unknown version, missing/moved tag, wrong SHA, nonancestor, failed gates | Refuse | No publication/completion |
| Missing package | Historical identity absent after tool publication | Refuse new Abstractions release | No push |

</frozen-after-approval>

## Code Map

- `scripts/release-request.py`: strict feed parsing and dual-404 absence proof; marker/environment bypasses live here.
- `scripts/verify-release-source.py`: clean source, local/remote tags, ancestry and exact-source push gates.
- `scripts/recover-bootstrap-release.py`: retain existing-package content verification; remove bootstrap absent-package publication, keys, push and wait/retry calls. Preserve source/receipt/consumer checks. Its `download_public_package` helper is also used by the paired publisher: keep that shared helper's bounded post-push processing wait intact for paired publication.
- `.github/workflows/release.yml`: current-main recovery validation currently relies on ambient bypass before historical checkout.
- `scripts/tests/test_bootstrap_release.py`: executable workflow/feed fixtures; extend without live publication.
- `README.md`, `docs/release/canonical-scope-upgrade.md`, architecture AD-17: release contract; preserve AD-22.

## Tasks & Acceptance

**Execution:**

- [x] `scripts/release-request.py`, new `scripts/bootstrap-history.json`: enforce registry closure on every bootstrap push; pin the three historical tags to evidenced full SHAs.
- [x] `scripts/verify-release-source.py`: select historical policy only through explicit `--tagged-recovery`; retain tag, ancestry and independent source gates.
- [x] `.github/workflows/release.yml`: reject ordinary bootstrap dispatch and invalid requests before approval. Verify current recovery workflow through full paired current-main gates, then check historical source explicitly. Preserve reviewed helpers/history across checkout.
- [x] `scripts/recover-bootstrap-release.py`, `scripts/release-publish.sh`, `scripts/release-preflight.sh`: make historical recovery verification-only and reject absent packages; ordinary publisher/preflight must always enforce public-tool closure, including when recovery environment variables are set.
- [x] `scripts/tests/test_bootstrap_release.py`: cover the matrix with independent tool/Abstractions feed fixtures, exact diagnostics/channels, zero effects and guard-removal checks.
- [x] `README.md`, new `docs/release/bootstrap-history.md`, `docs/release/canonical-scope-upgrade.md`, `docs/release/operator-setup-checklist.md`, AD-17: document closure and separately approved history with evidence; replace the checklist's stale marker/ancestry-only bootstrap-recovery claim.
- [ ] Retrospective and `sprint-status.yaml`: append F2 resolution; complete only item 2 when satisfied.
- [ ] Inspect HEAD/diffs before committing task files; fetch/check divergence before pushing; require green hosted CI.

**Acceptance Criteria:**

- Given each matrix state, when its script/workflow runs, then the specified refusal/verification occurs without unauthorized effects.
- Given explicit owner decisions, when documentation is finalized, then both disputed publications have accurate dispositions and evidence.
- Given final committed source, when local and hosted checks run, then required checks pass and the report identifies the run.

## Implementation Notes

- The implementation agent edits and verifies the artifacts; the parent owns staging, review, commits, push and final hosted-CI evidence. Leave final Git/hosted tasks pending for that parent sequence. No package publication, Release dispatch or tag writes.
- Ordinary bootstrap dispatch must fail before production approval; historical verification obtains no publication key. Keep local bootstrap preparation and paired publication behavior intact.
- Historical verification needs no GitHub release edits or replacement assets; retire its former release-completion writes and preserve verification results in the run instead.

## Spec Change Log

## Review Triage Log

| Finding | Verdict / route | Evidence and disposition |
|---|---|---|
| Blind 1: workflow shell masks piped helper failure | medium / patch | Reproduction returns zero for helper exit 19 under bash -c; GitHub explicit bash uses pipefail. Match hosted shell and protect failed helpers. |
| Blind 2: corrupt historical data untested | medium / patch | Newly added file/schema/tag/SHA guards have no corrupt-data fixtures. Add focused negative cases for each guard. |
| Blind 3: independent recovery environment states | low / patch | Existing matrix sets both values equally. Extend that matrix directly to independent, empty and conflicting inputs. |
| Blind 4: full recovery only uses 1.0.0 | low / rejected | Other versions have source/binding coverage; shared package validation already tests supplied versions. No distinct production defect was demonstrated. Expanding synthetic full-build fixtures adds little beyond fixing version-specific tag resolution (Verification 1); real historical rebuild qualification remains explicitly unclaimed. |
| Blind 5: historical rebuild qualification | low / patch | Local evidence correctly says fixtures only; add that limitation explicitly to the release history to avoid overstating current qualification. No live historical run is required for publication refusal. |
| Blind 6: stderr omitted from retained capture | low / patch | The new tee captures stdout only; source/refusal diagnostics use stderr. Merge streams and preserve pipefail with a failure regression. |
| Blind 7: no structured historical receipt | false / rejected | Historical verifier already prints exact source/current-main SHAs and both successful gate URLs; recovery's captured stdout and source-bound bootstrap receipt retain those facts. The task requires evidence, not a second structured receipt format. |
| Blind 8: consumer build proof deleted | false / rejected | smoke-bootstrap-consumer.sh forwards the full build log through tee to stdout; recover subprocess inherits stdout and the workflow capture retains it. Deleting the temporary duplicate does not lose the proof. |
| Blind 9: missing original-artifact input route | false / rejected | New documentation describes original artifacts for investigation, not a supported archive-input recovery mode. Existing verification intentionally rebuilds and refuses byte drift; no replacement publication is allowed. |
| Blind 10: preapproval refusal has no artifact | low / rejected | GitHub keeps the preapproval job's diagnostics and failed status. No artifact contract was specified for requests rejected before recovery starts; adding a receipt/upload path is unnecessary for this rare verification route. |
| Verification 1: tag-name resolution fixture gap | medium / patch | Reviewer mutation hardcoded local v1.0.0 lookup and five related tests still passed. Make distinct local/remote historical tag bindings coexist and prove incorrect lookups fail. |
| Edge-case layer | no findings | Reviewer returned an empty findings list. |

## Design Notes

The investigation binds `v1.0.0`, `v1.1.0`, `v2.0.0` to matching GitHub tags and public nuspec commits. Historical verification grants no new-push exception. Keep credential-free local bootstrap preparation for CI.

Implementation preserves the marker refusal after dual-404 public-tool absence. Current recovery workflow verification uses full paired CI/job checks plus FR-22; explicit historical verification retains Bootstrap package/Commitlint push checks. Reviewed helpers and the JSON allowlist survive checkout, and root-declared AI.Tools/Builds are aligned before checking historical cleanliness. The paired publisher retains its shared bounded post-push download wait; historical verification always selects a single already-public download.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py'`
- `node --test scripts/tests/select-release-version.test.mjs`
- `actionlint .github/workflows/release.yml .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/commitlint.yml`
- `bash -n scripts/release-preflight.sh scripts/release-publish.sh scripts/release-prepare.sh`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/live-topology -p test_ci.py -k CiWorkflowTests`
- `printf '%s\n' "$msg" | npx --no -- commitlint --verbose` after `npm ci`; retain evidence.
- Exact-source hosted `CI`, `Commitlint`, `Bootstrap package` push runs; no Release dispatch.

Local implementation verification (2026-11-06): **167 Python release tests**, **4 selector tests**, actionlint for all four listed workflows, shell syntax for all three listed scripts, and **2 CiWorkflowTests** passed. [Local evidence](evidence/epic-4-retro-item-2-bootstrap/local-validation.json) records commands and source file hashes. Historical verification was exercised with synthetic packages and executable fixtures, without Release dispatch, package publication, GitHub release edits or tag mutation. The paired fixture's final isolation correction also has a focused passing check.

Parent sequence remains pending: independent review, exact-message commitlint, task-file commit/push, exact-source hosted CI/Commitlint/Bootstrap package run IDs, and final item-2 completion. Retrospective F2 disposition is appended; only item 2 is in-progress.

Review completed 2026-11-06: all three layers returned; every patch entry above is applied. No deferred work. Final local validation passes **170 release Python tests**, **4 selector tests**, actionlint, shell syntax and **2 CI workflow tests**; see [reviewed validation](evidence/epic-4-retro-item-2-bootstrap/reviewed-validation.json).

| Matrix row | Executed coverage in the passing full suite |
|---|---|
| Closed publication | `test_bootstrap_closure_cannot_be_bypassed_by_marker_or_environment` |
| Uncertain evidence | `test_tool_registry_uncertainty_refuses_all_ordinary_bootstrap_entry_points` |
| Ordinary dispatch | `test_workflow_rejects_invalid_dispatch_before_approval_and_credentials` |
| Historical verification | `test_recover_workflow_preserves_reviewed_history_and_helpers_without_credentials`, all-three binding/source tests |
| Invalid recovery | Corrupt-history, invalid tag/ancestry/SHA/gate tests and hardcoded-tag mutation tests |
| Missing package | `test_recovery_refuses_absent_package_even_when_tool_is_public` |

The existing main run `42221463909` at the baseline failed five administrator-readiness checks with HTTP 503; 16 vectors and smoke passed. [Observed baseline failure](evidence/epic-4-retro-item-2-bootstrap/baseline-hosted-failure.json) is separate from this release-code validation. Fresh task-source hosted qualification is still required.

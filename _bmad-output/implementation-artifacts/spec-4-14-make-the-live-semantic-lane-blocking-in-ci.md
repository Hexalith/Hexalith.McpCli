---
title: '4.14 Make the live semantic lane blocking in CI'
type: 'feature'
created: '2026-10-26'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '49345128c189ff3955c00afb9f587b7a31c0ab15'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** CI discovers 21 approved vectors without running their live semantics. Builds lacks source preparation and isolation hooks; enabling its current Aspire tier alone would fail.

**Approach:** Add optional, bounded preparation and runner hooks in the owning Builds repository. Configure McpCli's required Aspire tier to build the three root source servers, prepare disposable infrastructure, and execute every approved vector plus the independent authenticated smoke.

## Boundaries & Constraints

**Always:** Keep `aspire-test-project` set to `tests/Hexalith.McpCli.Integration.Tests`, `test-platform` to `microsoft-testing-platform`, and `aspire-continue-on-error` to `false`. Run focused Release verification and Dapr initialization before live execution. Build only root-declared source servers with published sibling dependencies and separate deadlines. Preserve private namespaces, fresh stores, authentication, mTLS, bootstrap, standard prerequisites, single Command submissions, complete coverage and cleanup proof. Make Builds changes in its owning checkout; integrate a qualified upstream revision and preserve existing user edits.

**Never:** Edit reference contents, initialize nested submodules, weaken guards, accept skipped/partial/preflight-only evidence, substitute smoke for vectors, change approved Contracts/vector bytes, or enable publication. Paired-release implementation remains Story 4.16; its existing refusal stays intact.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Qualified sources and infrastructure | All 21 vectors and independent smoke pass; retain source identities, receipts and sanitized diagnostics |
| Missing helper/source/tool or namespace support | Fail with the named prerequisite before claiming live acceptance |
| Source build failure/deadline | Fail with project and command; no live tests execute |
| Failed semantic assertion, skip, timeout or incomplete receipt | Fail CI with Operation/phase where available; retain partial evidence |
| Builds caller omits hooks | Preserve existing VSTest/MTP behavior |

</frozen-after-approval>

## Code Map

- Owning `/home/administrator/projects/hexalith/builds/.github/workflows/domain-ci.yml`: Aspire job already depends on `build-and-test`, restores/builds Release and initializes Dapr. Direct test invocation needs optional hooks; defaults currently allow errors and a ten-minute timeout.
- Owning Builds `Tools/test-domain-workflow-test-platforms.ps1` and `.github/workflows/domain-ci.md`: executable shell-contract tests and workflow documentation. Extend upstream rather than copying workflow logic here.
- `.github/workflows/ci.yml`: preserves six non-live test projects, conformance gates and exact 22-case discovery. Add required Aspire inputs and pinned qualified Builds workflow revision.
- `README.md:230` and `tools/live-topology/README.md`: qualified source-build switches, pinned prerequisites and existing outer deadlines.
- `tools/live-topology/{bootstrap-runtime.py,binaries.json,run-isolated.py,run-vectors.py}`: reuse verified binaries, owned infrastructure and complete semantic receipts. `run-vectors.py` requires one fresh child per Operation; direct whole-project execution cannot replace it.
- `tests/Hexalith.McpCli.Integration.Tests/{AspireTopologyFixture.cs,LiveVectorTests.cs,GatewaySmokeTests.cs}`: retain isolation refusal, Operation selection, standard skips and authenticated smoke.
- `scripts/verify-release-source.py`: bootstrap-only publication gate; leave its paired refusal intact.

## Tasks & Acceptance

**Execution:**
- [x] Owning Builds `.github/workflows/domain-ci.yml`, `.github/workflows/domain-ci.md`, `Tools/test-domain-workflow-test-platforms.ps1` — add optional repository-relative preparation/runner script hooks with enforced bounds and evidence upload; validate inputs, propagate failures and preserve default callers.
- [x] `tools/live-topology/prepare-ci.sh` — implement bounded prerequisite setup and the three documented server builds from their own checkouts; install qualified Aspire tooling/Python requirements, prepare a fresh verified runtime, export only nonsecret paths and record exact source/tool identities. Keep host Dapr initialization in the reusable workflow and private service startup in the existing wrapper.
- [x] `tools/live-topology/run-ci.sh` — run full vectors through `run-vectors.py` and independent smoke through `run-isolated.py`; enforce outer deadlines, require complete current passing evidence and unskipped smoke, propagate nonzero outcomes and retain sanitized runtime diagnostics.
- [x] `tools/live-topology/test_ci.py` — execute scripts with controlled stub tools to protect order, bounds, missing prerequisites, build failure, failed/skipped vectors or smoke, incomplete evidence and nonzero exits; retain existing real-runner tests.
- [x] `.github/workflows/ci.yml` — consume the qualified upstream hooks/revision, explicit blocking inputs, qualified Dapr versions and adequate finite job timeout; upload evidence on failures as well as success. Preserve focused non-live lanes before Aspire.
- [x] `README.md`, `tools/live-topology/README.md` — document required CI behavior, prerequisites, bounded reproduction and evidence locations.
- [x] `_bmad-output/implementation-artifacts/evidence/story-4-14/` — record upstream revision, validation and live evidence; identify unavailable remote CI proof.

**Acceptance Criteria:**
- Given the reusable workflow, when McpCli CI runs, then an upstream-owned bounded preparation seam makes the three root source servers available before isolated MTP execution.
- Given McpCli's caller, when jobs execute, then focused Release checks precede a required Aspire tier with the exact three story-required inputs and initialized Dapr.
- Given any prerequisite/build/vector/semantic failure or skip, when the tier completes, then CI fails with actionable diagnostics and cannot report full live acceptance.
- Given unchanged Builds callers, when hooks are absent, then their existing test-platform paths remain functional.

## Implementation Notes

Approved 2026-10-26. The Build implementation stage prohibits pushes and remote operations. Prepare and validate upstream changes locally; do not claim a local-only revision is remotely available.

## Spec Change Log

## Review Triage Log

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B1 | high | patch G1 | `LiveVectorProcess` starts `python3` from PATH; preparation records host PATH although dependencies exist only in its venv. Fresh hosted execution can fail despite successful preparation. |
| B2 | maybe-false | defer | Hosted namespace restrictions may reject the standard unshare probe, but no actual hosted failure was reproduced. A real ubuntu-latest run and namespace diagnostic settle this medium-if-true environment prerequisite. |
| B3 | high | defer: integration dependency | The qualified upstream commit is local and must be published before GitHub can resolve the caller. This upstream readiness dependency was explicit before implementation; retain it as a release/integration blocker rather than claim hosted completion. |
| B4 | high | patch G2 | Parent reproduced quoted JSON SigningKey remaining unchanged. Generated child keys are absent from parent environment-value redaction; include quoted and escaped representations. |
| B5 | high | patch G3 | Parent executed fixture preparation with an existing issuer.key in evidence: preparation passes and the key remains beneath the whole-directory artifact upload. Refuse unowned existing evidence rather than delete user data. |
| B6 | medium | patch G4 | Parent reproduced acceptance of null namespace values and string stopped-process statuses. Strictly reject malformed proof at this new receipt boundary. |
| B7 | low | patch G5 | Parent reproduced source failure leaving a newly created private directory whose location is absent from the failure receipt. Immediately record ownership/location for safe cleanup. |
| B8 | maybe-false | reject: unverified low | The fixture proves no source-drift admission check, not a false semantic result. Hosted checkout is unchanged between hooks; source identities are recorded at build time. A real stale-artifact semantic false pass would establish additional harm. Extra provenance gates are not justified by this reproduction. |
| B9 | medium | patch G6 | Parent reproduced a replaced bundle passing preparation because only existence is checked. Compare the installed bundle against fresh embedded bytes from the selected qualified CLI. |
| B10 | medium | patch G7 | Existing immediate timeout stubs cannot prove CI-level detached-child cancellation; same missing verification as V1. |
| E1 | high | patch G8 | Parent reproduced RUNNER_TEMP beneath evidence producing raw issuer.key/state under the upload directory while both hooks passed. Require private runtime placement outside evidence. |
| E2 | high | patch G2 | Same quoted JSON signing-key leak as B4, independently reproduced by parent. |
| E3 | low | reject: unsupported launch failure | Missing GNU timeout exits 127 before Python starts and leaves the previous invocation's receipt. CI still fails; current acceptance is never granted. Making shell wrappers invalidate files before prerequisite execution requires additional path/ownership handling for an unsupported missing-coreutils host. |
| E4 | medium | patch G7 | A child can exit between poll and killpg during normal cancellation; uncaught ProcessLookupError bypasses diagnostic writes. Handle the already-exited process without replacing the original result. |
| V1 | medium | patch G7 | Pre-verified removal-sensitive gap: removing ci.py's detached-child cleanup still passes current hook tests. Add actual SIGTERM coverage proving child exit, retained diagnostics and false acceptance. |

Patch groups are internal corrections to demonstrated states; no public surface or intent change is required. Preserve the complete prior green packet as historical evidence and qualify the repaired interpreter/cancellation/artifact paths. Hosted availability and namespace behavior remain explicitly open until upstream integration and a real hosted run.

## Design Notes

Optional script hooks keep module-specific setup out of Builds. Pass validated paths through environment variables without evaluating command strings. Preserve 900/960-second child bounds and a finite outer/job budget including setup.

The owning Builds checkout is clean on main at `09af6ef818beb27490c87c00ed83dd581a7e6d8d`; McpCli currently references `e171c5a788eab183b32683431b084198c9b8d373`. Recheck before implementation. Reconcile dependency policy and Manifest validation if reference integration changes restored versions.

## Verification

- Run owning Builds' workflow contract tests and relevant validation before integrating its revision.
- Run `bash -n` on both CI scripts and `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` after building prerequisites.
- Run fresh `dotnet restore Hexalith.McpCli.slnx`, then `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`; execute required non-live test projects individually, including Manifest.Tests against fresh assets.
- Execute the same preparation/runner path as CI; require 21 passing vectors, independent passing smoke, zero skips, matching fresh receipts and owned cleanup. Retain exact prerequisite failures separately from successful focused checks.
- Validate workflow syntax, order and failure propagation. Record hosted CI proof separately; stubs cannot establish hosted acceptance.

### Implementation evidence (2026-10-26)

- Qualified upstream owner commit: `833a58fa125fdc3a3135c16d0e04cca3f1b63264`; integrated by local Git bundle and pinned in the caller. It remains unpublished under this stage's no-push/no-remote constraint, so hosted CI resolution and acceptance are unproven.
- Optional upstream hooks passed 321 executable workflow assertions, syntax validation and pinned commitlint before commit. Default VSTest/MTP paths remain covered.
- Source preparation and runner passed through the same CI shell hooks: all 21 vectors and the independent authenticated smoke, zero live skips/failures, 22 fresh owned runtime cleanup receipts.
- Fresh solution restore, Release `-warnaserror` build, all six focused test projects and 110 Python tests passed. The focused Core/CLI projects retain five existing platform skips; the live lane has none.
- Explicit EventStore 3.127.0 pin preserves the approved qualification when importing the newer Builds catalog; fresh Manifest.Tests passed without approved Contracts/vector or dependency-policy changes.
- Evidence: `evidence/story-4-14/README.md`, `verification.json`, exact verification outputs and complete support-safe `live-ci.tar.gz`. Every archive member was compared against the original run output; private runtime state and credentials are excluded.

### Parent task and matrix audit (2026-10-26)

The parent read the implementation diff and upstream patch, checked all seven execution tasks, and independently compared all 1,441 archived files with the original run. All 36 indexed outer evidence files match their hashes. The archive contains 22 individually passing, unskipped XML cases, 22 successful owned cleanup receipts and 144 semantic phases. Full live acceptance is true; hosted availability of the local upstream commit remains pending.

Every frozen matrix row has passing executed coverage: complete lane (`test_complete_lane_and_smoke_acceptance_retains_only_sanitized_diagnostics`, actual 21-vector/smoke run); missing prerequisites (`test_prerequisite_failures_precede_source_builds`, missing-source/tool tests, existing Manifest helper admission checks); source failures/deadlines (`test_source_failure_and_timeout_never_prepare_or_execute_live`); semantic/skip/incomplete failures (`test_vector_nonacceptance_and_nonzero_exits_still_run_smoke`, `test_smoke_skips_missing_receipts_nonzero_and_cleanup_fail_closed`); unchanged callers (321-assertion owning Builds workflow suite covering existing VSTest/MTP paths).

### Final review resolution and verification (2026-10-26)

All eight patch groups are implemented and independently checked against the diff. The complete repaired suite passes 119 Python tests, Release restore/build and all six focused projects; the inherited five non-live platform skips remain. The actual fresh preparation/runner path passes all 21 vectors and independent smoke with no live skips/failures. Parent audit verifies 22 native cleanup receipts, 144 phases and exactly 53 Command submissions with distinct message IDs. All 1,446 archived files match the original final run; source fingerprints bind the tested helper/caller files.

The final upstream local revision is `35587cfd104c5750d8ec3c0716933f386d6a0232`, with 323 passing workflow assertions and pinned commitlint qualification. Artifact upload eligibility now rejects pre-existing evidence before preparation. Matrix coverage remains complete, supplemented by actual SIGTERM, cleanup-removal mutation, private interpreter, redaction, overlap and malformed-proof checks.

B2 and B3 remain integration follow-ups already tracked in `deferred-work.md` under this spec: upstream publication and actual hosted namespace/live verification. Implementation is complete; sprint status is review rather than done. Final evidence: [verification index](evidence/story-4-14/FINAL.md).

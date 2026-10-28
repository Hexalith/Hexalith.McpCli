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

**Always:** Keep `aspire-test-project` set to `tests/Hexalith.McpCli.Integration.Tests`, `test-platform` to `microsoft-testing-platform`, and `aspire-continue-on-error` to `false`. Run focused Release verification and Dapr initialization before live execution. Build only root-declared source servers with published sibling dependencies and separate deadlines, except Tenants may use the sibling EventStore source through `HexalithEventStoreFromSource=true` (approved 2026-10-28). Preserve private namespaces, fresh stores, authentication, mTLS, bootstrap, standard prerequisites, single Command submissions, complete coverage and cleanup proof. Make Builds changes in its owning checkout; integrate a qualified upstream revision and preserve existing user edits.

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

- 2026-10-28: User approved keeping the inherited Tenants source dependency after the explicit source-versus-published question. Amend the frozen dependency constraint with that exception; preserve the passing native lane and all isolation, deadline and semantic requirements.

## Review Triage Log

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| R28-BH1 | medium | patch integration | The new pin requires the already-selected Builds checkout to be recorded with it; the HEAD comparison is expected to fail until that integration commit exists. |
| R28-BH2 | medium | patch integration | Parties helper 2.0.0 expectations require the selected Builds catalog. Include the matching Manifest expectation hunks with the required catalog integration. |
| R28-BH3 | medium | patch cancellation | Nested vector cleanup permits 20 seconds while CI permits 10; the composed external-cancellation path needs verification and enough cleanup grace. |
| R28-BH4 | medium | patch redaction | XML encoding changes known credential bytes before the final text sanitizer. Parse XML values before sanitizing and protect this with a regression. |
| R28-BH5 | medium | patch diagnostics | Smoke failure escapes before vector_error is raised, losing vector failure names from stderr when both fail. Preserve both errors in the combined diagnostic. |
| R28-BH6 | medium | patch docs | The standalone Tenants build command lacks the now-approved source switch, so it does not reproduce the hook's build. |
| R28-BH7 | low | patch docs | Tool/helper versions in both READMEs lag the restored SDK/helper graph; directly correct the affected claims. |
| R28-BH8 | low | patch evidence | The new evidence README still presents the now-resolved approval checkpoint as active. Preserve history and record its resolution. |
| R28-BH9 | low | patch evidence | FINAL.md lacks a pointer to the newest qualification; identify the historical packet and current evidence. |
| R28-BH10 | medium | patch integration | Run the owner checks against the selected checkout and record the selected pin and unchanged reusable-workflow bytes; retain hosted proof as pending. |
| R28-EC1 | medium | patch cancellation | A process-group supervisor may exit before TERM-resistant descendants; ensure remaining owned group members receive SIGKILL even after supervisor exit, with an executed regression. |
| R28-VG1 | medium | patch cancellation | Pre-verified gap: current cancellation tests exercise immediate termination or separate layers, not the real nested vector runner with a resistant detached child. Add a composed regression. |
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

### Final Build review of pass-3 corrections (2026-10-28)

All three required layers completed against the full story source diff and retained owning Builds hook patches. The blind and verification layers received source changes without this spec or historical evidence prose; the edge-case layer read the claims after its independent trace. Fourteen findings are individually triaged below before grouping. The review retains the earlier verdicts for unchanged, previously triaged claims. No new deferred-ledger entry is needed.

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B3-BH1 | low | carried reject | Script names beginning with `-` repeat pass-2 BH17/pass-3 BH2. The trusted McpCli caller supplies fixed `tools/live-topology/` paths; no actual caller uses the demonstrated `-s` file. Changing the generic owning hook and integrating another revision is unnecessary for this caller. |
| B3-BH2 | low | carried reject | Nested or ambient EventStore root selection repeats pass-3 BH4/EC11. Nested submodule initialization is prohibited and the qualified runs use the approved sibling; no divergent source was used. |
| B3-BH3 | maybe-false | carried reject: low if true | Quoted ordinary SigningKey assignments repeat pass-3 EC5. The string transformation is demonstrated, but no actual diagnostic emitter of that form is identified; real retained archives have no detectable credential output. Adding another redaction branch guards an unshown emitter. |
| B3-BH4 | low | carried reject | Malformed XML with entity-encoded credentials repeats pass-3 EC7. xUnit writes complete XML on completion; neither real malformed credential output nor exposure is shown. The proposed fallback changes a rare diagnostic failure path. |
| B3-BH5 | maybe-false | carried reject: low if true | Incomplete PEM blocks repeat pass-3 BH9 and pass-1 truncated-PEM triage. No private-PEM diagnostic emitter is identified; the hypothetical truncation does not demonstrate credential exposure from this lane. |
| B3-BH6 | low | carried reject | Forced KILL before final redaction repeats pass-3 EC1. All real retained local and hosted packets contain zero redactions, and no actual credential leak is shown; moving output placement would redesign the existing runner boundary. |
| B3-BH7 | low | reject | A manually cached bundle can retain correct bytes while losing execute bits. Hosted preparation force-refreshes the bundle, and an unusable local executable fails live startup rather than granting acceptance. Adding another cache-admission guard for this rare local state is unnecessary complexity. |
| B3-BH8 | false | reject | A differing Release dependency selection is not present in the three selected source configurations. Their package-version assignments do not vary with Configuration under the supplied source switches; the parent compares default and Release evaluations separately. A possible future conditional property is not a current receipt mismatch. |
| B3-BH9 | false | reject | The committed-HEAD gitlink comparison is the explicit pass-2 D2 decision. Rejecting a pin change before its corresponding gitlink is committed is its intended constraint, and the current aligned pin passes. Replacing it with the index/working checkout would weaken that chosen check. |
| B3-BH10 | low | patch prerequisites documentation | Python on some Linux installations lacks venv/ensurepip despite satisfying the version bound. The existing bounded venv command fails by name and keeps acceptance false; state the required support in both READMEs without adding another prerequisite branch. |
| B3-BH11 | low | reject | An unusual kernel can allow unshare while lacking veth creation. The existing isolated wrapper then names and fails the networking command without granting acceptance; selected hosted/local kernels have passed the complete lane. A duplicate networking setup probe adds complexity only to move this rare failure before source builds. |
| B3-EC1 | low | carried reject | Same malformed, entity-encoded XML claim as pass-3 EC7, recorded independently before grouping. No actual truncated credential-bearing test output is identified, so the earlier rejection stands. |
| B3-EC2 | low | carried reject | Diagnostic-copy I/O failure before final redaction repeats pass-2 EC6 and pass-3 EC1. No I/O failure or exposed child credential is shown; acceptance remains false. A private-output publication redesign guards an unshown rare state. |
| B3-VG1 | medium | patch runner contract regression | Pre-verified removal-sensitive gap: the existing caller-contract test invokes preparation only. Removing only run()'s require_contract() leaves it green and can grant acceptance to an unsupported runner caller. Add both runner project/platform refusals after successful preparation, checking diagnostics, the failed receipt and absence of vector/smoke execution. |

## Design Notes

### Resumed Build review triage (2026-10-27)

All three required layers completed against the full baseline diff. Verification Gap reported no gaps. Blind Hunter supplied BH1–BH10; Edge Case Hunter supplied EC1. Each finding is recorded separately below before grouping.

| ID | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| BH1 | high | defer: existing integration item | Carried B3: the new `857ef02` caller revision is locally qualified and unpublished. The existing integration ledger item already tracks publication and hosted acceptance; the implementation stage prohibits remote operations. |
| BH2 | medium | patch G9 | Parent directly reproduced `sanitized(json.dumps({'diagnostic': secret}))` preserving known environment secrets containing quotes, backslashes and newlines. Redact their serialized representations and add regression coverage without changing the public surface. |
| BH3 | false | reject | Carried rejection: the real vector receipts are structural or sanitized by their producer. The reproduction introduces an additional arbitrary JSON emitter absent from the actual runner; no production diagnostic JSON exposing a credential was identified. |
| BH4 | false | reject | Carried rejection: real `run-vectors.py` constructs distinct absolute receipt paths from its owned runs; it does not emit alternate `..` spellings for one receipt. The fixture changes the producer contract rather than demonstrating an actual duplicate-runtime acceptance path. |
| BH5 | false | reject | Carried rejection: the real independent wrapper creates and prints its own new run, never a vector run. Repointing fixture stdout and adding an unused run does not occur in the actual wrapper; the distinct vector receipts and exact 22-run check remain enforced. |
| BH6 | low | reject | Carried rejection: an additional I/O fault during diagnostics can leave acceptance false with `running` status; no real fault was demonstrated. Independent persistence adds exception-handling complexity for an uncommon failure and cannot turn this state into acceptance. |
| BH7 | low | reject | The proposed drift requires changing trusted checkouts or built artifacts between hooks. Hosted jobs retain their checkout and record source identities; no stale-artifact semantic false pass was shown. Additional artifact-binding gates would guard an unshown state. |
| BH8 | low | reject | Smoke failures already persist the top-level failed result and actionable error with acceptance false; no consumer requires a nested failed-smoke object. Adding a parallel exception branch supplies redundant metadata for an uncommon failure. |
| BH9 | false | reject | P1 explicitly requires failed Operation names in stderr and `{operation,result,error}` in the receipt. Both exist; phase/error details are retained in `vectors.failures`, and failed Operations are named in the console. |
| BH10 | false | reject | D2 replaces downloads through the unverified installer with a checksum-verified release archive. Existing operator-installed tooling remains a trusted prerequisite with version and payload checks; no unchecked archive is downloaded or extracted on that path. Actual fresh hosted-style preparation exercised the verified download branch. |
| EC1 | high | defer: existing integration item | Carried B3, separately recorded: workflow resolution requires publication of `857ef02`. Already tracked in `deferred-work.md` under this source spec; no duplicate ledger entry is added. |

BH1 and EC1 share the existing upstream-publication dependency. G9 is the only new code correction from this review. All other findings are rejected individually on the evidence above.

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

### Hosted qualification continuation (2026-10-26)

The user authorized publication and hosted verification. Both original revisions were already published when checked. Hosted run `40370370231` passed conformance and the focused tier after one retry of the existing 515 ms parallel Catalog benchmark; a subsequent Dapr download HTTP 504 cleared on the next Aspire attempt. Attempt 3 exposed an over-strict SDK comparison: the repository permits `latestPatch`, and GitHub selected 10.0.403 while the hook demanded 10.0.402. Delegate selection to the existing .NET resolver at the repository root, retain the declared policy and actual SDK in receipts, and keep nonzero resolution fail-closed. All 24 focused hook tests pass; restoring exact equality fails the new regression. Evidence: `evidence/story-4-14/hosted-qualification/sdk-rollforward/verification.json`. Corrected hosted live acceptance remains pending.

### Hosted namespace prerequisite correction (2026-10-26)

Run `40375850526` passed its focused tier and accepted SDK 10.0.403 under the repository policy, then reproduced B2: unshare could not write uid_map on the hosted Ubuntu VM. After a denied probe, preparation now configures only the disposable GitHub-hosted VM's unprivileged user-namespace setting through bounded noninteractive sudo and requires a second real probe. Local/self-hosted hosts remain operator-managed, and each live child still proves four private namespaces. All 27 focused hook cases pass, including setup failure and still-denied probes; disabling recovery fails the positive regression. Original hosted failure and qualification are in `evidence/story-4-14/hosted-qualification/namespace-setup/verification.json`. Full hosted acceptance remains pending the corrected run; B2 is already tracked in the deferred-work ledger, so no duplicate entry is appended.

### Hosted Aspire cache qualification (2026-10-26)

Run `40377962105` proves the namespace setup and re-probe succeed. Preparation then detects a mismatched managed launcher in a reused installed bundle cache. On disposable GitHub-hosted runners, refresh the complete cache through the pinned CLI's standard `setup --force`, then retain the full payload hash comparison; local stale-cache refusal stays intact. All 29 focused hook tests pass, including rejection of a still-mismatched managed payload after setup. A real pinned-CLI installation/legacy-cache refresh yields 490 payload files matching the independent fresh extraction; skipping the hosted refresh fails the new regression. Evidence: `evidence/story-4-14/hosted-qualification/bundle-cache/verification.json`. Corrected full hosted acceptance remains pending.

### Review Findings (code review, 2026-10-27)

Code review 2026-10-27 of the committed story range `4934512..f6fc9ae` (`3eb1635`, `aea0e13`, `6738b9e`, `f6fc9ae`) plus the owning Builds hook commits `833a58f` and `35587cf` (paths prefixed `Hexalith.Builds/` in the diff).

- **Code-only scope:** excludes `_bmad-output/` and `references/`. 9 McpCli files (+1,161/−4) and 3 Builds files (+197/−2), 1,515 diff lines, full mode, with `epic-4-context.md` as context. The in-spec implementation review (B1–V1) came before `3eb1635`, so this is the first review of the three hosted-qualification commits.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 48 normalized findings (BH 16, EC 17, VG 6, AA 8, plus 1 from parent verification). After triage: 2 decision-needed, 13 patch, 2 defer and 20 rejected. Both decisions were resolved as option (a), giving 15 patches.

Parent checks during triage:
- Builds `35587cf` is on `origin/main`, and the caller pin (`.github/workflows/ci.yml:18`) resolved in hosted run `40381146665`.
- **Hosted run `40381146665`, attempt 2 (HEAD `f6fc9ae`):**
  - The Aspire job took 19 minutes: about 3 minutes of steps before the hooks, 54 s of preparation and about 15 minutes for the runner.
  - Its `aspire-hook-evidence` artifact `12680213617` records `fullLiveAccepted: true`, 21 passed vectors and a passed smoke.
  - Attempt 1's artifact `12681110107` records `parties.create-party` failing (see the first defer item).
- `dotnet msbuild -getProperty:HexalithEventStoreVersion -p:UseHexalithProjectReferences=false -p:UseNuGetDeps=true` on the three source projects gives EventStore 3.128.0, Tenants 3.128.0 and Parties 3.127.0. The baseline Builds gitlink `e171c5a` defaulted to 3.127.0; `35587cf` defaults to 3.128.0.
- **Mutation check:** each mutation was run separately against `CiHooksTests`. Removing any of the nine guards or paths named in P7 keeps all 28 hook tests green. The VG layer's mutations back P2–P6 in the same way.
- The current suite passes locally: 29 tests in 32 s.

- [x] [Review][Patch] D1 — medium, decided 2026-10-27: option (a). The source-built EventStore and Tenants servers moved to EventStore 3.128.0 packages without any record of it. [tools/live-topology/ci.py:219]
  - **Cause:** Moving the Builds gitlink changed the catalog default that the three source builds read. EventStore and Tenants now resolve 3.128.0; Parties keeps its own 3.127.0 pin. In 4.13 all three resolved 3.127.0.
  - **Why it matters:** `tools/live-topology/README.md:184-186` says the 3.127.0 pin "preserve[s] the approved package/vector qualification", but that pin covers only McpCli's own restore. `preparation.json` records source SHAs and git status, not the resolved package versions, so the mixed topology is invisible in the evidence (BH, EC).
  - **Already proven:** both the local run and hosted attempt 2 pass with this mix.
  - **Option (a), recommended:** record each source build's resolved `HexalithEventStoreVersion` in `preparation.json`, and correct the README to say that only McpCli's restore stays on 3.127.0.
    - The servers follow the pinned catalog, as Platform's run/debug composition does.
    - The vector approval binds McpCli's packages, not the servers'.
  - **Option (b):** pass `-p:HexalithEventStoreVersion=3.127.0`, taken from McpCli's pin, to all three source builds (`tools/live-topology/ci.py:219`). This restores the 4.13 topology exactly: all three gitlinks are unchanged and built against 3.127.0 at baseline. It adds a second copy of the pin and leaves local source-build instructions on the catalog version.
- [x] [Review][Patch] D2 — medium, decided 2026-10-27: option (a). Every hosted run executes an unverified `https://aspire.dev/install.sh`, and the CLI is qualified only by its version string. [tools/live-topology/ci.py:166]
  - **Evidence:** `ci.py:166-175` records the installer's SHA-256 but never compares it.
    - Hosted evidence shows the install branch runs on every GitHub-hosted job.
    - The bundle check (`ci.py:181-194`) compares the installed bundle with an extraction from the same unpinned CLI, so it cannot detect a bad CLI.
    - The Redis and Dapr binaries, by contrast, are digest-pinned in `binaries.json`.
    - The job's token is `contents: read` (BH, AA, EC).
  - **Option (a), recommended:** download the 13.6.1 CLI release archive directly and verify a pinned SHA-256 before extracting it, dropping `install.sh`. This matches Platform's checksum-verified release-asset preparation for Dapr.
  - **Option (b):** pin the `install.sh` digest. CI then fails whenever upstream edits that unversioned script, and the script's own downloads are still trusted.
  - **Option (c):** keep the version-only qualification and document it.
- [x] [Review][Patch] P1 — medium. Failed vectors are not named in the CI log or in `ci-live.json`. [tools/live-topology/ci.py:338]
  - On a vector failure, both `ci-live.json` and the stderr line say only `run-vectors.py … exited 1; see …/vectors-process.stderr.txt`. That file is empty, because `run-vectors.py` prints its single summary line to stdout.
  - In hosted attempt 1, finding `parties.create-party` and its Gateway 500 meant downloading the 2.5 MB artifact. Matrix row 4 and AC3 require the Operation/phase where available (AA).
  - **Fix:** when `vectors/live-lane.json` exists, copy each non-passing `{operation, result, error}` into `report['vectors']['failures']`, and name the failing Operations in the raised message that `main` prints. Cover it with a fixture outcome that carries an error.
- [x] [Review][Patch] P2 — medium. The `stale-isolation` fixture cannot catch removal of the receipt containment check. [tools/live-topology/test_ci.py:145]
  - The fixture points at a non-existent `/outside/current-runtime/result.json`. With the `ci.py:251` containment condition replaced by `False`, all hook tests still pass, because `read_text()` raises `FileNotFoundError` instead (VG).
  - **Fix:** write a complete owned `result.json` and `outside.json` in a sibling runtime directory, and assert the "outside the prepared runtime" error.
- [x] [Review][Patch] P3 — medium. The smoke's own ownership and cleanup proof has no independent test. [tools/live-topology/ci.py:356]
  - `missing-cleanup` also breaks every vector run, so vector acceptance already fails. Replacing `:356` with `pass` keeps the suite green (VG, BH).
  - **Fix:** add a fixture mode that changes only `owned('smoke')`. Assert that the vectors `passed` and that the smoke ownership error appears in `ci-live.json`.
- [x] [Review][Patch] P4 — medium. No test covers the exact count of 22 isolated runtimes. [tools/live-topology/ci.py:360]
  - Replacing the condition with `if False:` keeps every test green (VG, BH).
  - **Fix:** add a fixture mode that creates an extra `runs/<name>` directory, and assert the count error and `fullLiveAccepted: false`.
- [x] [Review][Patch] P5 — medium. The final redaction pass over generation logs and XML is untested. [tools/live-topology/ci.py:369]
  - Emptying the pattern tuple, or dropping only `tests.xml`, keeps every test green. The end-to-end test reads only `runtime-diagnostics/` (VG).
  - **Fix:** make the `run-vectors.py` fixture write `<op>/child.stdout.txt` and `tests.xml` containing secrets: a JWT, a PEM block, an env token and a generated `SigningKey`. Assert that none of them appear anywhere under `receipt['output']`.
- [x] [Review][Patch] P6 — medium. The refusal of a symlinked evidence path in `ci.py` has no test. [tools/live-topology/ci.py:100]
  - Replacing the guard with `if False:` keeps the suite green. `test_caller_contract_and_unsafe_evidence_paths_are_refused` covers only `../outside` and `.`, and for local runs `ci.py` is the only guard (VG, BH).
  - **Fix:** add a symlinked `ASPIRE_EVIDENCE_PATH` subcase that asserts the message and checks the link target is left untouched.
- [x] [Review][Patch] P7 — medium. Nine more guards and bounds can be removed with no test failing. [tools/live-topology/test_ci.py:419]
  - **Mutations that left all hook tests green (parent check):**
    - the preparation-path match (`ci.py:293`)
    - the ownership-ID match (`:296`)
    - the Integration.Tests DLL check (`:300`)
    - the Aspire version check (`:174`)
    - the preparation binary-hash check (`:235`)
    - the 2400 s outer `timeout` (`prepare-ci.sh:5`) and the 18000 s one (`run-ci.sh:4`)
    - the Aspire install branch (`ci.py:166`)
    - the daprd version check (`:146`), which duplicates the runtime line of `dapr --version` and can be deleted instead
  - **Also unpinned:** `CiWorkflowTests` does not pin `aspire-prepare-timeout-minutes: 40`, `aspire-runner-timeout-minutes: 300` or `aspire-evidence-path`. Several existing refusal cases assert only a nonzero exit (BH, AA).
  - **Fix:**
    - Add one removal-sensitive case per guard that asserts its message.
    - Assert the outer `timeout` calls from the stub log.
    - Pin the three caller inputs.
    - Assert the expected stderr in the cases that currently check only a nonzero exit.
- [x] [Review][Patch] P8 — low. The READMEs keep claims that the hosted-qualification commits made stale. [README.md:279]
  - `README.md:279` says the pinned Builds revision "is qualified locally; hosted CI proof requires that revision to be published upstream". `tools/live-topology/README.md:237-239` says it "has not been pushed" and that hosted acceptance "remains unproven". Both are now false (see the parent checks).
  - `README.md:270` says the bundle is installed "when missing", but GitHub-hosted runners always force-refresh it (`ci.py:185`) (BH, AA).
  - **Fix (wording only):** drop the publication-status sentences, since status belongs in the evidence. Keep "Paired package publication remains disabled". State that hosted runners refresh the bundle.
- [x] [Review][Patch] P9 — low. The OpenSSL 3 prerequisite check accepts any libssl. [tools/live-topology/ci.py:132]
  - `tools/live-topology/README.md:10` requires `libssl.so.3` and `libcrypto.so.3`, but `find_library('ssl')` also accepts OpenSSL 1.1. The failure then appears later, with no prerequisite named (AA, EC, BH).
  - **Fix:** load the exact `libssl.so.3` and `libcrypto.so.3` sonames, and name whichever one is missing.
- [x] [Review][Patch] P10 — low. The README says every installed bundle file is compared; only the expected files are. [tools/live-topology/README.md:214]
  - `ci.py:191` iterates over the fresh extraction, so extra files in `~/.aspire/bundle` are never examined (EC).
  - **Fix (wording only):** say that every file of a fresh extraction from the selected CLI must match the installed bundle.
- [x] [Review][Patch] P11 — low. The hook deadlines equal their step limits, and `bounded()`'s 35 s cleanup outlasts the hook's 30 s kill grace. [tools/live-topology/prepare-ci.sh:5]
  - **The deadlines:** 2400 s and 18000 s equal both the caller's 40- and 300-minute steps and the Builds wrapper's `timeout`, so the Actions step deadline races the TERM path.
  - **The grace mismatch:** after TERM, `bounded()` waits 30 s and then 5 s more (`ci.py:74`), but the hook SIGKILLs Python after 30 s. This loses the failure receipt and the in-flight output.
  - **Reachability:** preparation's inner bounds add up to more than 2400 s, so a slow preparation can reach this (hosted preparation took 54 s). The runner hook cannot fire before its inner bounds do.
  - Builds `domain-ci.md:55` claims a 30-second kill grace "in addition to the Actions step deadline" (BH, AA, EC).
  - **Fix:**
    - Set the hook deadlines below the step limits, for example 2280 s and 17700 s.
    - Make `bounded()`'s wait after TERM shorter than the hook's kill grace.
    - Update both READMEs.
    - Correct the Builds sentence together with P13.
- [x] [Review][Patch] P12 — low. When a reused runtime is refused, its earlier runs are still copied into this generation's diagnostics. [tools/live-topology/ci.py:298]
  - `runtime` is set before the freshness check at `:306`, so `finally` copies the old `runs/*` under the new generation (EC). Only a local rerun without new preparation reaches this.
  - **Fix:** assign the `runtime` that `finally` uses only after the freshness check passes.
- [x] [Review][Patch] P13 — low. Builds' `domain-ci.md` still says TRX results are always uploaded. [Hexalith.Builds/.github/workflows/domain-ci.md:34]
  - With a runner hook, the default Aspire test steps are skipped, so `aspire-test-results` has no TRX to upload. Hook output goes to the `aspire-hook-evidence` artifact instead (BH, EC).
  - **Fix (owning Builds repository, wording only):** limit the TRX sentence to callers without a runner hook, and fix the P11 grace sentence in the same commit. Then move the McpCli pin and gitlink.
- [x] [Review][Defer] The hosted live lane is intermittent: a port bind race in a Dapr sidecar failed `parties.create-party` [tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:51] — deferred: pre-existing topology (Stories 4.12–4.13), exposed now that the lane is blocking.
  - In attempt 1 of hosted run `40381146665`, the Parties sidecar logged `Failed to listen for gRPC server on TCP address :44173 … bind: address already in use` and stopped. The port is inside Linux's ephemeral range.
  - EventStore's `invoke/parties/method/process` call then returned HTTP 500, and `parties.create-party` failed with `gateway_error` 500. Attempt 2 passed all 21 vectors.
  - Fixture liveness did not detect the dead sidecar before the vector ran. The `ci.py` hooks behaved correctly and failed the attempt.
- [x] [Review][Defer] `AGENTS.md` still says `HexalithEventStoreVersion` comes from the Builds props [AGENTS.md:92] — deferred: agent-context file. `Directory.Build.props:4` now pins it to 3.127.0 while the Builds props say 3.128.0. An agent that checks members against the Builds value could use a 3.128.0-only API that fails to compile (BH). Fix in the next bmad-project-context refresh.

#### Rejected (code review, 2026-10-27)

- `false` — The pinned Builds SHA is unpublished, so every CI job fails (BH, EC). `35587cf` is on Builds `origin/main`, and hosted run `40381146665` resolved it. Only the README wording is stale (P8).
- `false` — Hosted acceptance was never demonstrated (AA). Attempt 2 of `40381146665` records `fullLiveAccepted: true` with 21 vectors and a passed smoke. Updating this spec's status, evidence and the two 2026-10-26 ledger entries is spec work, not a code patch.
- `false` — No test ties the workflow pin to the gitlink (BH). They serve different purposes: the gitlink is the package catalog, the pin is the reusable workflow. `ci.yml` used `@main` with a pinned gitlink before.
- `false` — The 360-minute job budget leaves too little time for the steps before the hooks (BH). Those steps took about 3 minutes on the hosted run, leaving about 17 minutes of margin even when both hooks use their full budgets.
- `false` — Redaction misses `live-lane.json`, per-vector receipts and other secret names (BH). `live-lane.json` holds structural data, the C# receipts are sanitized at their source (4.13), and no secret is mapped into the hook steps' environment.
- `false` — The end-to-end test never checks the planted generated `SigningKey` (BH, VG other). The direct `sanitized()` test covers the `SigningKey` patterns, and the end-to-end test proves the sanitizer is applied. The generation-level gap is P5.
- `low` — A diagnostics-copy failure in `run()`'s `finally` skips the final `ci-live.json` save (BH, EC). It needs an I/O fault that was never shown. The receipt stays `running` with `fullLiveAccepted: false`, and the fix adds exception handling.
- `low` — A second signal during `bounded()`'s `finally` skips the SIGKILL escalation (EC). The inner GNU `timeout`'s own `--kill-after` still kills the child group, and the fix adds signal masking.
- `low` — The Builds and `ci.py` path validators disagree on trailing or doubled slashes and leading `-`, and the PowerShell tests miss a few evidence-path cases (BH). The caller is trusted, and every such mismatch fails loudly.
- `low` — The `Directory.Build.props` comment does not explain the EventStore pin (BH). Cosmetic; the AGENTS.md part is deferred.
- `false` — The blocking lane costs up to 6 hours per PR, and `cancel-in-progress` starves `main` (BH). The hosted lane took about 15 minutes, and the concurrency group predates this story.
- `false` — `main()` reports an evidence error for an unknown subcommand (BH). Only the two wrappers call `ci.py`, always with fixed arguments.
- `false` — The root README's "Each isolated child retains its 900-second deadline" is wrong (AA). It refers to the isolated wrapper's command limit, consistent with `tools/live-topology/README.md:200`.
- `false` — The conformance and discovery jobs do not gate the Aspire tier (AA). AC2's focused Release checks are the six Tier-1 projects, which do precede the tier through `needs: build-and-test`. The other jobs still block CI.
- `maybe-false` (low if true) — `SigningKey="v"` (an unquoted key with a quoted value) is not redacted (EC). No emitter of that form has been shown, and each fixture's signing key is short-lived and dies with its disposable topology.
- `maybe-false` (low if true) — A truncated PEM block survives redaction (EC). No private PEM emitter has been shown. A block would only be truncated on a kill, and the fixture key material is disposable.
- `low` — The 960 s smoke bound can expire before the wrapper's 900 s command limit plus its prerequisites (EC). This is the documented, shared 960/900 s design from 4.13, and the smoke takes about 40 s.
- `low` — A dirty or non-gitlink source checkout is accepted (EC). CI checkouts are always clean gitlinks and status is recorded. The same class was rejected as B8.
- `false` — The final redaction pass follows symlinked logs outside the evidence directory (EC). No program under test creates such links.
- `false` — Duplicate receipt directories, or a smoke that reuses a vector's run, can pass with fewer than 22 proofs (EC). This needs `run-vectors.py` or `run-isolated.py` to misbehave. The distinct-receipt set and the 22-entry count already guard the paths that were shown, and P4 adds a test for the count.


### Review patch resolution and local qualification (2026-10-27)

All 15 code-review patches (D1, D2 and P1–P13) are implemented. Source preparation records each server's resolved `HexalithEventStoreVersion`; the real run confirms EventStore/Tenants at 3.128.0 and Parties at 3.127.0 while McpCli retains 3.127.0. Missing Aspire tooling now comes from the official 13.6.1 release archive after a pinned SHA-256 check, exercised by hiding existing launchers during actual preparation. Failed vector Operations and their errors are retained in `ci-live.json` and named in stderr. Exact OpenSSL 3 prerequisites, shorter cancellation cleanup, deadline margins, current-runtime-only diagnostics, independent ownership/count/redaction guards and corrected documentation are qualified.

The owning Builds documentation-only commit is `857ef02dbb4bde1bd4e678546aa41e73fb7d68b1`, directly based on the former `35587cf` pin. Its 323 workflow assertions, actionlint and pinned commitlint pass; the caller pin and gitlink now select it. The local Git bundle and exact patch are retained. No push or Git remote operation was performed, so publication and hosted resolution of this new revision remain open; the prior hosted acceptance of `35587cf` is preserved as historical proof.

Fresh Release restore and `-warnaserror` build pass with zero warnings/errors. All six focused projects pass: 1,531 tests passed, zero failed, five existing non-live skips. All 137 Python tests pass. Eighteen guard-removal mutations and three caller-input removals each fail their intended assertions. Bash syntax and caller actionlint pass.

The exact preparation/runner shell hooks pass in 22.135/820.096 seconds: 21 passing vectors and independent authenticated smoke, zero live skips/failures, 22 passing XML cases, 22 owned cleanup receipts, 144 semantic phases, 53 single Command submissions with 53 distinct message IDs and 91 Query attempts. Every one of the 1,455 archived evidence files matches its original bytes; private runtime credentials/state remain excluded. Evidence: [review patch qualification](evidence/story-4-14/review-patches-20261027/README.md) and [verification index](evidence/story-4-14/review-patches-20261027/verification.json).

The hosted namespace follow-up is resolved by the already-recorded hosted runs. Publication/hosted acceptance for the new documentation-only Builds revision remains the existing integration ledger item. The pre-existing Dapr port-bind intermittence and agent-context version wording remain deferred; no duplicate ledger entries were appended. This local qualification does not claim hosted acceptance for the new pin or enable paired publication.

### Parent Build review completion (2026-10-27)

The parent independently verified all 39 indexed evidence files, seven initial source fingerprints, all 1,455 archived files against the original run, 22 passing/unskipped XML cases and 22 native ownership/cleanup receipts. The frozen intent, production Contracts, approved vectors and dependency policy are unchanged. Every matrix row retains executed passing coverage: full native lane and hook acceptance; named prerequisite failures; source build failures/deadlines; failed, skipped and incomplete receipts; and the 323-assertion owner workflow suite for callers without hooks.

All three review layers completed and every finding is triaged above. G9 now decodes escaped JSON string diagnostics before redacting known environment credentials, re-encoding only changed strings. Quotes, backslashes, newlines and nested JSON are protected; ordinary text stays unchanged. The new regression failed before the correction. Four targeted tests and the final complete 138-test Python suite pass. Execution and acceptance code have identical ASTs before/after this sanitizer-only correction, and replaying all 168 retained live diagnostic files produces identical output. The complete native lane was qualified before G9; it was not rerun for this diagnostic-only correction. No .NET code or build inputs changed after the recorded fresh Release build and 1,531 passing .NET tests.

No unresolved code finding remains. Build implementation is complete; sprint status remains `review` pending upstream publication and hosted acceptance of the new Builds pin. Final parent evidence: [verification](evidence/story-4-14/build-review-20261027/verification.json), [Python output](evidence/story-4-14/build-review-20261027/python-tests.txt) and [current source fingerprints](evidence/story-4-14/build-review-20261027/source-hashes.json). The existing integration, Dapr intermittence and agent-context follow-ups remain tracked without duplication.

### Review Findings (code review pass 2, 2026-10-27)

Code review pass 2, 2026-10-27, of the committed story range `4934512..8bfd1e0` plus the owning Builds hook commits `09af6ef..857ef02` (paths prefixed `Hexalith.Builds/` in the diff). This is the first review of `c6a19e8` (the 15 pass-1 patches) and `8bfd1e0` (gitlink sync).

- **Code-only scope:** excludes `_bmad-output/` and `references/`. 12 files (+1,535/−7), 1,795 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 50 normalized findings (BH 17, EC 20, VG 5, AA 7, plus 1 from parent verification). After triage: 2 decision-needed, 6 patch, 2 defer and 28 rejected. Both decisions were resolved as option (a), giving 8 patches.

Parent checks during triage:
- **CI on `main` cannot start.** GitHub answers `No commit found for SHA: 857ef02dbb4bde1bd4e678546aa41e73fb7d68b1` (HTTP 422). Runs `40558089073` (`c6a19e8`) and `40558426472` (`8bfd1e0`) failed in 0 s with "workflow file issue" and zero jobs.
- **Builds state:**
  - `857ef02` is on no ref in the owning checkout. It is reachable only as the detached HEAD of the worktree `/tmp/mcpcli-414-builds-review-20261027`.
  - The gitlink `cad9252` is an ancestor of Builds remote `main` (`cbe58fa`). Builds `main` changed `domain-ci.yml` again afterwards, in `2256924`, `568417a` and `35f185a`.
- **The last run that executed failed.** Run `40550130133` (HEAD `b0e87c8`, pin `35587cf`) failed its blocking `aspire-tests` job.
  - 20 of 21 vectors passed and the smoke passed. `parties.deactivate-party` failed with `Bootstrap authority did not converge in 60 seconds. Privileged query HTTP 404.`
  - Its runtime diagnostics show the Tenants sidecar logged `listen tcp :40625: bind: address already in use`.
  - The hooks failed the run correctly.
- **Source versions moved.** `8bfd1e0` moved the source gitlinks to EventStore `b1dd186`, Tenants `2cf3a96` and Parties `ea2bf5a`. At HEAD, `dotnet msbuild -getProperty:HexalithEventStoreVersion -p:UseHexalithProjectReferences=false -p:UseNuGetDeps=true` gives EventStore 3.128.0, Tenants 3.128.2 and Parties 3.128.0.
- **Mutation check:** the parent ran each mutation separately against `CiHooksTests`.
  - Removing any of these sub-conditions keeps the suite green: `len(expected)`/`set(expected)`, `coverage`, `lane.result`, `passed`/`failed`, outcome Operations and per-item `exitCode` (`ci.py:346-351`). Removing the `ci.py:211-212` guard does too.
  - Removing `lane.fullLiveAccepted` or the per-item `result` check fails a test.

- [x] [Review][Patch] D1 — high, decided 2026-10-27: option (a). The caller pins Builds `857ef02`, which was never published, and `/pushall` then moved the gitlink to the divergent `cad9252`. As a result no CI job runs on `main`, and Builds `main` lacks the P11/P13 wording. [.github/workflows/ci.yml:18] (BH, AA, VG, EC)
  - `cad9252` contains the hook code that passed hosted at `35587cf`. It differs from `857ef02` only in the P11/P13 `domain-ci.md` wording and in the stricter Tier 1/2 TRX checks.
  - The checked-in `references/Hexalith.Builds/.github/workflows/domain-ci.md:34` and `:55` still carry the old sentences.
  - The ledger item at `deferred-work.md:612` tracks publication of `857ef02`. Publishing it now would need a merge onto Builds `main`, not just a push.
  - **Option (a), recommended:** pin `ci.yml:18` to the current gitlink `cad9252`, then run hosted CI once. That run also qualifies the moved source gitlinks. Re-land the `857ef02` wording as a separate Builds docs commit, and move the pin and gitlink together at the next Builds bump.
  - **Option (b):** cherry-pick `857ef02` onto Builds `main` and push it. Move the pin and gitlink together to the new SHA, then run hosted CI. This completes P13 now, but it pulls in the three later `domain-ci.yml` changes (including `568417a`, the release execution gates) unqualified.
  - **Option (c):** push `857ef02` to a Builds branch or tag so GitHub can resolve it, and keep the pin. The gitlink stays divergent and the wording stays off `main`.
  - **Status at `84c2220`:** a separate `/pushall` moved the pin and gitlink together to the published Builds `12e48f1`, not `cad9252`, and hosted run `40565620918` resolves the workflow. `12e48f1` does not contain `857ef02`, and its `domain-ci.md:34` still carries the old TRX sentence. The re-land of the Builds wording and hosted acceptance of `12e48f1` remain open. Do not move the pin back to `cad9252`.
- [x] [Review][Patch] D2 — medium, decided 2026-10-27: option (a). No test ties the workflow pin to the gitlink, so the `8bfd1e0` divergence passed silently. [tools/live-topology/test_ci.py:875] (BH, EC)
  - `CiWorkflowTests` only checks that the pin is 40 hex characters. Pass 1 rejected tying the two because they serve different purposes; this pass shows them drifting apart.
  - **Option (a), recommended:** assert that the pin equals `git ls-tree HEAD references/Hexalith.Builds`, which works in shallow CI checkouts. Every Builds bump then moves both in one commit, as P13 prescribed. This would have caught `8bfd1e0` locally. It cannot prove publication: at `c6a19e8` both were equal and both unpublished.
  - **Option (b):** keep them independent, and only document that they move together.
  - **Status at `84c2220`:** `test_workflow_pin_matches_builds_gitlink` (`tools/live-topology/test_ci.py:878`) now asserts that the pin equals the gitlink, and it passes locally. Its removal sensitivity (moving the pin or the gitlink alone) is not yet shown.
- [x] [Review][Patch] P1 — medium. Fifteen guards still have no test that fails when the guard is removed. [tools/live-topology/test_ci.py:319] (VG, AA, BH, parent mutations)
  - **Each removal keeps `CiHooksTests` green:**
    - the platform/Python gate (`ci.py:132`)
    - the zlib/zstd check (`:143`)
    - the Dapr CLI half of `:151`
    - `daprd` presence (`:154`)
    - bundle-extraction completeness (`:202`)
    - the checkout symlink/`.git` condition (`:222`)
    - the `copy_diagnostics` symlink skips (`:296`, `:299`)
    - the smoke receipt count (`:383`)
    - six sub-conditions of the 21-vector acceptance check (`:346-351`)
  - **Fix:** add one removal-sensitive case per guard that asserts its message and that no build or live step ran. For the acceptance conditions, either add one malformed-lane fixture per condition or delete the conditions that only restate `fullLiveAccepted`.
- [x] [Review][Patch] P2 — medium. Lane-level `run-vectors.py` failures are not named, and not-run Operations are reported as failed. [tools/live-topology/ci.py:358] (AA)
  - Preflight, admission, coverage and runtime-variable failures land only in the top-level `error` of `live-lane.json` (`run-vectors.py:182`), with `vectors` empty or not-run.
  - `run-vectors.py` writes nothing to stderr. CI and `ci-live.json` therefore point to an empty `vectors-process.stderr.txt`, and the cause is visible only after downloading the artifact. This misses matrix row 2 and AC3.
  - On an aggregate timeout, `running` and `not-run` items are listed under "failed Operations".
  - **Fix:** copy `lane['error']` into `report['vectors']` and into the raised message, point at the stdout receipt line, and name only `result == 'failed'` items as failed. Cover each case with a fixture.
- [x] [Review][Patch] P3 — medium. The source-server version matrix in the README is false at HEAD. [tools/live-topology/README.md:187] (AA, BH, EC)
  - `:187-189` says EventStore and Tenants resolve 3.128.0 and Parties 3.127.0. After `8bfd1e0` they resolve 3.128.0, 3.128.2 and 3.128.0, and nothing asserts the numbers.
  - **Fix (wording only):** say that each source build's resolved `HexalithEventStoreVersion` is recorded in `preparation.json`, and keep only the McpCli 3.127.0 pin statement.
- [x] [Review][Patch] P4 — low. The `Missing qualified Aspire bundle prerequisite` guard is unreachable. [tools/live-topology/ci.py:211] (AA, parent mutation)
  - The hash loop at `:201-204` already requires both files, so removing the guard keeps every test green.
  - **Fix:** delete the guard and keep the hash recording.
- [x] [Review][Patch] P5 — low. The Python prerequisite accepts 3.11.0–3.11.3, which raise `TypeError` on the Aspire archive path. [tools/live-topology/ci.py:132] (BH, AA, EC)
  - `tarfile.extractall(..., filter='data')` (`:184`) needs 3.11.4 or later; Debian 12 ships 3.11.2.
  - **Fix:** require `(3, 11, 4)` and update `tools/live-topology/README.md:10` and `:157`.
- [x] [Review][Patch] P6 — low. The Builds hook-ordering assertion passes when the Aspire job's Dapr step is missing. [Hexalith.Builds/Tools/test-domain-workflow-test-platforms.ps1:561] (EC)
  - `IndexOf` returns −1, and the global Dapr checks at `:693-696` find the build-and-test job's step instead.
  - **Fix (owning Builds repository):** assert that each index is at least 0. Land it together with the D1 re-land of the Builds wording.
- [x] [Review][Defer] The live lane is intermittent: the Dapr sidecar port-bind race recurred [tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:51] — deferred: pre-existing topology, already tracked (`deferred-work.md:619`).
  - New occurrence: in run `40550130133`, the Tenants sidecar lost `:40625`, bootstrap timed out, and `parties.deactivate-party` failed.
  - Two of the three executed hosted full-lane attempts have now failed this way, so the blocking lane is red more often than green.
- [x] [Review][Defer] `AGENTS.md` still says `HexalithEventStoreVersion` comes from the Builds props [AGENTS.md:92] — deferred: agent-context file, already tracked (`deferred-work.md:633`).

#### Rejected (code review pass 2, 2026-10-27)

- BH4, EC15 `false` — Duplicate receipt spellings or an unverified run directory. `run-vectors.py:173` takes each receipt from its own child's `Isolated run:` line, and each child creates a new run. The 22-run count (`ci.py:389`) stands. This was rejected in pass 1.
- BH5, EC7 `false` — Unsanitized generation JSON. `live-lane.json` is structural, the C# receipts are sanitized at their source (4.13), and no secret is mapped into the hook environment. This was rejected in pass 1.
- BH6, EC8 `maybe-false` (low if true) — Unquoted, Python-repr or truncated PEM forms, unsigned JWTs and other environment-name redaction gaps. No emitter of these forms has been shown, and the fixture keys are disposable. This was rejected in pass 1.
- BH7, EC10 `low` — Dirty, or HEAD-not-gitlink, source checkouts are accepted. CI checks out exact gitlinks and the status is recorded; the fix adds guards for local runs only. This was rejected as B8 and BH7.
- BH10, EC16 `low` — `run` does not re-hash the tools between hooks. Changing them requires altering trusted artifacts between hooks; no false pass was shown. This was rejected in the resumed Build review.
- BH12 `false` — The deadline literals can drift silently. Every literal is pinned: 2280 at `test_ci.py:295`, 16200/960/17700 at `:426-427`, and 40/300/360 in `CiWorkflowTests`. Editing any one of them fails a test.
- BH13 `low` — The 960 s smoke bound is shorter than the wrapper's worst case. This is the documented 960/900 s design from 4.13; the smoke takes about 40 s. The README wording was rejected in pass 1 as `false`.
- BH14 `low` — The 30 s kill grace on the Builds outer `timeout` cannot run. McpCli's own hook deadlines (2280 s and 17700 s) fire 120 s and 300 s before the step limits, with their grace inside. The Builds bound is a backstop.
- BH15, EC11 `low` — Transitive Python dependencies are unpinned. This is the same requirements file and policy as the existing conformance gates; the fix adds a hashed lock file.
- BH16, EC13 `low` — Extra files in the installed Aspire bundle are not examined. P10 made the README state this one-way comparison; no extra-file harm has been shown.
- BH17 `low` — The Builds and `ci.py` path rules disagree, two inputs lack descriptions, and a few PowerShell cases are missing. The caller's inputs are fixed and pinned, and every mismatch fails loudly. This was rejected in pass 1.
- AA7 `low` — A deadline expiry is reported only as exit 124. The command, project and `timeoutSeconds` are recorded in `*.command.json`; the fix adds a branch for a rare state.
- EC3 `low` — The wait after SIGKILL can expire. That needs a process to survive SIGKILL for more than 5 s; the fix adds exception handling.
- EC4 `low` — A second TERM can arrive during cleanup. GNU `timeout`'s own `--kill-after` still kills the group. This was rejected in pass 1.
- EC5 `low` — `ci.py`'s 10 s TERM wait is shorter than the 20 s grace `run-vectors.py` gives its children. This is reachable only by external cancellation: the 17700 s hook bound cannot fire before the 16200 + 960 s inner bounds. The isolated child, already sent TERM, still completes its own cleanup.
- EC6 `low` — An I/O fault in `run()`'s `finally` skips the remaining redaction. No such fault has been shown. This was rejected in pass 1.
- EC9 `maybe-false` (low if true) — Children inherit the terminal's stdin locally. No invoked child reads stdin: setup passes `--non-interactive` and sudo runs with `-n`.
- EC12 `false` — An `aspire --version` banner causes a spurious refusal. The qualified 13.6.1 output passed in the local and hosted runs; other output comes from a different CLI and is correctly refused.
- EC14 `false` — Bool or float lane counters are accepted. Acceptance also requires each of the 21 outcomes to have `result == 'passed'`, which a parent mutation proved is tested. The producer writes ints (`run-vectors.py:177-178`).
- EC20 `low` — Hook callers get an empty `aspire-test-results` upload warning. It is a warning only; the `domain-ci.md` wording is accurate in effect.
- VG (other) `false` — A reviewer shared a scratch directory with another reviewer. This is a process note, not a defect in the diff; the review inputs were verified intact.


### Resumed Build verification and dependency checkpoint (2026-10-28)

The local hook path passed all 21 vectors and the independent authenticated smoke, with zero live skips, 22 passing XML cases and 22 owned cleanup receipts. Parent verification checked every native receipt and all 1,452 archived evidence files. The expanded Python suite passed 148 tests; all 18 guard removals and both pin-drift mutations were detected. Release build and six focused test-project outputs record 1,531 passes and five existing non-live skips. Owner workflow checks passed 411 assertions. Evidence: [resumed verification](evidence/story-4-14/review-pass2-20261028/README.md).

D1 remains open: the retained owner patch is recorded at `30455c2fbbc2a93a82fccd4255b7cd3520f20a46`, while the caller still pins `abc0e1be8069d1c7a567515a13bb015adc407536`. No remote operation or hosted acceptance is claimed. Concurrent source/catalog gitlink and Manifest-test changes were preserved.

A frozen-spec conflict prevents completion: the inherited `SOURCE_EVENTSTORE` path in `tools/live-topology/ci.py` builds Tenants with `HexalithEventStoreFromSource=true`, while the frozen constraints require published sibling dependencies. The passing local lane proves this source-based configuration only. Asked the user whether to approve that exception or enforce published dependencies. Status remains `in-progress`; final Build review and completion remain pending this decision.


### Final resumed Build completion (2026-10-28)

The user approved the Tenants sibling-source exception; the frozen constraint and change log record it. The caller and selected Builds catalog now use `3d7f49a5430294da5bcd437cbdace85c62c42027`, which includes the owning documentation and ordering-test corrections. Its reusable workflow bytes equal the previous caller's bytes, and all 411 workflow assertions pass against the selected checkout. The required catalog integration includes the matching Parties helper 2.0.0 Manifest expectations. Other concurrent source gitlink edits are preserved.

All three required review layers completed. Every one of their 12 findings is recorded separately in the Review Triage Log and resolved locally. The cancellation regression fails against the original HEAD with a surviving detached child and passes with the real nested runner after correction. Three additional guard-removal regressions protect XML decoding, combined vector/smoke diagnostics and descendant cleanup after supervisor exit. The broad Python run passes 151 tests; the separate committed-HEAD pin comparison also passes after integration, for 152 passing Python tests in total. Fresh restore, Release warnings-as-errors build and all six focused .NET projects pass: 1,531 passed, zero failed, five existing non-live platform skips.

The repeated final CI hooks pass all 21 live vectors and the independent authenticated smoke, with zero live skips or failures, 22 passing XML cases and 22 native owned cleanup receipts. Parent audit verifies 144 semantic phases, 53 single Command submissions with 53 distinct message IDs, 91 Query attempts and all 1,452 archived files against the originals. Final source hashes and raw outputs are retained in the [current qualification packet](evidence/story-4-14/review-pass2-20261028/final/README.md). Earlier hash-bound packets remain intact; [LATEST.md](evidence/story-4-14/LATEST.md) identifies the current packet.

Every matrix row has executed passing coverage: complete native acceptance; named prerequisites and namespace refusal (`test_platform_and_python_patch_prerequisites_stop_before_commands`, existing missing-tool/source/namespace cases); source failures and deadlines (`test_source_failure_and_timeout_never_prepare_or_execute_live`); failed/skipped/incomplete evidence and combined diagnostics (`test_vector_nonacceptance_and_nonzero_exits_still_run_smoke`, `test_vector_and_smoke_failures_are_both_named`, smoke refusal cases); and unchanged no-hook VSTest/MTP callers (411 owner workflow assertions). Production Contracts, approved vector bytes, dependency policy and paired-publication refusal are unchanged in this resumed patch.

- [x] [Review][Defer] Hosted acceptance of the selected Builds pin remains an integration follow-up, already tracked (`deferred-work.md:612`); no duplicate ledger entry is added. The earlier `857ef02` publication issue is historical; this run verifies the selected revision through local owner history and tests, without a Git remote operation. The existing Dapr intermittence and agent-context follow-ups also retain their existing tracking. Implementation is complete locally; sprint status is `review`, not `done`.

### Review Findings (code review pass 3, 2026-10-28)

Code review pass 3, 2026-10-28, of the committed story range `4934512..dbce3b1` plus the owning Builds hook commits `09af6ef..857ef02` and `30455c2` (paths prefixed `Hexalith.Builds/` in the diff). This is the first review of `8d4a8c0` (Tenants sibling EventStore source), `a34f761` (pass-2 patches and the `3d7f49a` pin) and the interleaved dependency commits `3a8fbf2`, `2d7311c`, `4274235` and `8a860ee`. The other 479 hook-file lines between Builds `857ef02` and `3d7f49a` belong to other stories and are excluded.

- **Code-only scope:** excludes `_bmad-output/` and `references/`. 18 file diffs (+2,043/−67), 2,385 diff lines, full mode, with `epic-4-context.md` as context.
- **Layers:** Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG) and Acceptance Auditor (AA). No layer failed.
- **Result:** 44 normalized findings (BH 15, EC 19, VG 3, AA 7). After triage: 1 decision-needed, 5 patch, 1 defer and 29 rejected. The decision was resolved as option (a), giving 6 patches.

Parent checks during triage:
- **Hosted acceptance of the selected pin is now proven.** Hosted run `40658496696` (HEAD `dbce3b1`, pin `3d7f49a`) passed `ci / aspire-tests`. Its `aspire-hook-evidence` artifact `12803579896` records `ci-live.json` `result: passed`, `fullLiveAccepted: true`, 21 vectors and the smoke passed, 22 `Isolated run:` receipts and zero `[REDACTED]` markers. Preparation recorded EventStore `36c78f3`, Tenants `7ddb864` and Parties `9239c53`, each resolving `HexalithEventStoreVersion` 3.128.3. This settles the open item at `deferred-work.md:613`, now marked resolved.
- **The published package now contains the routing contracts.** The restored `hexalith.eventstore.contracts` 3.128.3 and 3.128.4 assemblies contain `Hexalith.EventStore.Contracts.Routing.RouteContractDeclaration`; 3.128.2 does not.
- **Real archives carry no detectable credentials.** The five archived local live packets and the hosted artifact contain zero sanitizer redactions.

- [x] [Review][Patch] D1 — medium, decided 2026-10-28: option (a). The stated reason for the Tenants sibling-source exception is stale at HEAD (BH5, AA4) — `tools/live-topology/ci.py:27-28` and `tools/live-topology/README.md:177-179` justify `HexalithEventStoreFromSource=true` with routing contracts "added after the published 3.128.2 package". This range adopts published 3.128.3, which contains them. The exception was approved on 2026-10-28 and the frozen constraint permits it ("may"), but its documented premise no longer holds, so the lane may be deviating from the published-dependency default without need. Tenants builds against EventStore `36c78f3` (`v3.128.3-6`), the same checkout the root EventStore server is built from. **Option (a), recommended:** keep the approved exception and correct both texts: 3.128.3 now ships the routing contracts, and Tenants deliberately compiles against the same EventStore source as the root server under test. Wording only, no requalification. **Option (b):** restore the frozen default. Remove `SOURCE_EVENTSTORE`, drop the switch from `README.md:239`, update the 8d4a8c0 test case, then requalify locally and hosted. Other source-only APIs may still break the Tenants build. **Option (c):** leave as is.
- [x] [Review][Patch] P1 — medium. On an aggregate vector deadline or cancellation, the interrupted Operation is not named [tools/live-topology/ci.py:413] (AA2) — on TERM, `run-vectors.py` raises `SystemExit(143)`, which bypasses its `except Exception`. `live-lane.json` keeps `result: pending`, no `error`, and the in-flight item stays `running`. Pass-2 P2 now names only `failed` items, so CI and `ci-live.json` show `failures: []` and `laneError: null` although the receipt identifies the Operation. This misses matrix row 4 ("timeout … Operation/phase where available"). The `lane-timeout` fixture (`tools/live-topology/test_ci.py:160-165`) masks it by injecting a lane `error` and `result: failed` that the real producer never writes on TERM. **Fix:** also report `running` items as interrupted Operations in the message and in `report['vectors']`, and make the fixture mirror the real TERM receipt.
- [x] [Review][Patch] P2 — medium. The `commitlint.yml` Builds pin has drifted from the gitlink, and the pin guard does not cover it [.github/workflows/commitlint.yml:19] (VG1, BH13, EC17, AA5) — `a34f761` moved `ci.yml` and the gitlink to `3d7f49a` but left `commitlint.yml@abc0e1be…`. `test_workflow_pin_matches_builds_gitlink` (`tools/live-topology/test_ci.py:1142`) reads only `ci.yml`. The `commitlint.yml` blob is identical at both SHAs today, so the next Builds bump that changes it will silently run the stale workflow, against the pass-2 D2 decision. **Fix:** realign `commitlint.yml:19` to `3d7f49a5430294da5bcd437cbdace85c62c42027` (GitHub resolves it) and assert that every `Hexalith/Hexalith.Builds/…@<sha>` in `.github/workflows/` equals the gitlink.
- [x] [Review][Patch] P3 — medium. No test fails when the Docker readiness prerequisite is removed [tools/live-topology/ci.py:205] (VG2) — the `docker` stub always exits 0 and no case asserts the `docker info` call, so deleting the check keeps `CiHooksTests` green. A daemon-down runner would then spend up to three 300 s source builds before failing in the live tests. **Fix:** add a `docker-unavailable` stub mode and a `('docker-unavailable', 'docker info')` case to `test_prerequisite_failures_precede_source_builds` (`tools/live-topology/test_ci.py:344`).
- [x] [Review][Patch] P4 — low. Both READMEs give the wrong cancellation-cleanup timing [README.md:279] (BH1, EC18, VG3, AA1) — `README.md:279` says cleanup "waits at most 15 seconds after cancellation", and `tools/live-topology/README.md:212-213` says "ten seconds after TERM and at most five more after KILL". `ci.py` `bounded()` now waits up to 25 s after TERM, which covers the vector runner's 20 s child grace, then kills the owned group. `test_cancellation_escalation_finishes_within_outer_kill_grace` pins `[41, 25, 1]`. **Fix:** correct both sentences to the implemented bounds.
- [x] [Review][Patch] P5 — low. Cancellation during the smoke after a vector failure is reported as a smoke failure with exit 1 [tools/live-topology/ci.py:450] (EC13, AA7) — `run()`'s `except BaseException` wraps the `SystemExit(143)` from the TERM handler (or a `KeyboardInterrupt`) in `RuntimeError("…; independent smoke failed: 143")`. `main()` then exits 1 instead of 143. **Fix:** combine only when `isinstance(error, Exception)`, and add a regression asserting exit 143 and an unrelabelled receipt.
- [x] [Review][Defer] The agent instructions still say `HexalithEventStoreVersion` comes from the Builds props, now that `Directory.Build.props:4` pins 3.128.3 [AGENTS.md:92] — deferred: agent-context file, already tracked (`deferred-work.md:634`). The pinned value moved from 3.127.0 to 3.128.3; the entry's fix is unchanged.

#### Rejected (code review pass 3, 2026-10-28)

- BH1 (margin part) `false` — The 25 s cleanup leaves only about 5 s of the 30 s kill grace for the final redaction. That grace belongs to the 17700 s hook backstop, which cannot fire before the inner bounds (16200 + 960 s, each plus at most 30 s kill grace and 25 s cleanup). External cancellation is governed by the runner, not this grace.
- BH2 `low` — The Builds hook bound equals the step deadline; the upload has no `if-no-files-found: error`; two inputs lack descriptions; script paths may start with `-`. Rejected in pass 2 as BH14 and BH17: McpCli's hook deadlines fire 120 s and 300 s before the step limits, and the inputs are fixed and pinned.
- BH3 `low` — `cancel-in-progress: true` cancels the long blocking lane on new pushes. Superseding runs is the existing policy; a cancelled run never reports acceptance, and hosted VMs are discarded. Changing it is a policy decision, not a defect in this diff.
- BH4, EC11, AA3 `low` — Tenants' `Directory.Build.props:24` prefers a nested `references/Hexalith.EventStore` over the sibling. Nested submodules are never initialized by CI or allowed by the repository rules (the local nested directory is empty). The fix adds a `HexalithEventStoreRoot` parameter.
- BH6 `low` — Dirty or non-gitlink source checkouts are accepted. Rejected in passes 1 and 2 (B8, BH7); the hosted run recorded exact gitlinks.
- BH7 `low` — Transitive Python dependencies are unpinned. Rejected in pass 2 (BH15, EC11).
- BH8 `low` — A preinstalled Aspire CLI is trusted on its version string, and the hosted bundle comparison uses that CLI. Hosted runners download and SHA-verify the CLI; subverting it needs a tampered local install, and the fix adds pinned digests.
- BH9, EC6 `false` — Receipt JSON is not re-sanitized, and truncated PEM is not redacted. Rejected in pass 2 (BH5, EC7, BH6, EC8); the hosted artifact and five local archives contain zero redactions.
- BH10 `low` — The smoke does not verify the genesis backup, and it may reuse a vector run. Reuse is `false`: the smoke's receipt comes from its own `Isolated run:` line, and each run-isolated invocation creates a new run. The run-isolated runtime is fresh by construction, no false pass is shown, and the fix adds a guard.
- BH11 `maybe-false` (low if true) — The Integration.Tests closure resolves `Hexalith.McpCli.Abstractions` 1.1.0 while production uses the in-repo 1.0.0. The closure is pinned explicitly by the Manifest test. Settling it would require a test outcome that depends on the 1.1.0 package rather than the locally built ConformanceHost.
- BH12 `maybe-false` (low if true) — The README's Parties.Aspire 2.0.0 "archive and closure review" claim has no recorded review. The closure part is mechanized by `CheckAspireHelperClosure` and the pinned closure test; settling the archive part needs the 2.0.0 review record.
- BH15 `false` — Dapr SDK 1.19 against runtime 1.18.7 is unqualified. Hosted run `40658496696` and the final local packet passed every vector and the smoke with this combination.
- EC1 `low` — A KILL before the final redaction leaves raw child logs in the uploaded evidence. Every real archive and the hosted artifact contain zero redactions, so no credential exposure is shown, and the fix is a redesign of the output placement.
- EC2 `low` — A second signal during `bounded()`'s `finally` skips the group SIGKILL. Rejected in passes 1 and 2 (EC4).
- EC3 `low` — `child.wait(timeout=1)` after a group SIGKILL can escape. Rejected in pass 2 (EC3); it needs the timeout leader to survive SIGKILL.
- EC4 `low` — A recycled PGID could receive SIGKILL. The kernel does not reuse an ID while a group member lives; the window after the group empties is at most 50 ms and needs a PID wrap-around.
- EC5 `maybe-false` (low if true) — `SigningKey = "v"` style forms escape the label regexes. Rejected in passes 1 and 2: no emitter of these forms has been shown.
- EC7 `low` — A truncated `tests.xml` falls back to plain-text redaction. xUnit writes the file once at completion, and no entity-encoded credential has been shown in real output.
- EC8 `false` — A non-secret environment value with a secret-like name corrupts receipt paths. Hosted preparation repeatedly produced intact receipt paths, and no such variable has been shown locally.
- EC9 `low` — Extra installed bundle files are not examined. Rejected in pass 2 (BH16, EC13).
- EC10 `low` — Tools are not re-hashed between hooks. Rejected in pass 2 (BH10).
- EC12 `false` — Bool or float lane counters are accepted. Rejected in pass 2 (EC14): every outcome must have `result == 'passed'`.
- EC14 `low` — The 960 s smoke bound is shorter than the wrapper's worst case. Rejected in pass 2 (BH13).
- EC15 `low` — Builds `aspire-runner-script` with `aspire-fail-skips: true` fails the TRX gate. No caller combines them (McpCli sets no `aspire-fail-skips`), and the combination fails loudly.
- EC16 `low` — Builds' 5-minute job-time reserve ignores the 31-minute package-prepare step. McpCli sets no `package-prepare-script`, and that step belongs to another story outside this diff.
- EC19 `false` — Tenants builds against unreleased EventStore source. That is the approved sibling-source exception, built against the same checkout as the root EventStore server; D1 covers its stale rationale.
- AA6 — Rejected: the fix edits the spec under review. The spec record does not cover the interleaved dependency changes (EventStore 3.128.3, Dapr 1.19.0, Parties.Aspire 2.0.0).


### Pass-3 implementation and parent verification (2026-10-28)

All six pass-3 corrections (D1 and P1–P5) are implemented. Running vector outcomes are retained as interrupted Operations for aggregate deadlines and direct hook cancellation; direct cancellation retains its original control exception without starting smoke. Cancellation during smoke after a vector failure preserves exit 143, and KeyboardInterrupt/SystemExit remain unwrapped. Every Builds workflow reference now matches the recorded gitlink, Docker readiness has removal-sensitive prerequisite coverage, and both README timing statements and the approved Tenants source rationale are current.

The complete Python suite passes 155 tests with zero skips. All eight guard-removal and pin-drift mutations fail their intended assertions. Bash syntax, actionlint and scoped whitespace checks pass. The parent read the resumed implementation diff and independently verified every new packet hash and source fingerprint. The resumed patch preserves all other ci.py function ASTs, successful execution and acceptance bodies, wrappers, .NET/build inputs, production Contracts, approved vectors, dependency policy and paired-publication refusal.

The parent also re-audited the prior native archive: its recorded SHA-256 and all 1,452 files match the originals; all 21 vectors, the independent authenticated smoke, 22 XML cases and 22 owned cleanup receipts pass. No fresh native, hosted or .NET run is claimed for these failure-path, test, pin-alignment and wording corrections. The historical qualification retains the Release build and 1,531 passing .NET tests with five existing non-live skips. Hosted acceptance of the selected Builds revision is already recorded above and in the resolved ledger entry. Concurrent agent-guidance and deferred-ledger edits are preserved.

Every matrix row retains executed passing coverage in the new Python output or historical native/owner packets: complete acceptance; named prerequisites including Docker and namespace refusals; source failures/deadlines; semantic, skip, interrupted and incomplete receipts; and unchanged no-hook VSTest/MTP behavior (411 owner assertions). Required final Build review remains in progress. Evidence: [pass-3 correction packet](evidence/story-4-14/review-pass3-20261028/README.md).


### Final pass-3 Build completion (2026-10-28)

All three review layers completed; all 14 findings have individual verdicts in the Review Triage Log. B3-VG1 is resolved by a runner-specific test for both unsupported caller inputs after successful preparation. It asserts exact stdout/stderr, the complete failed acceptance receipt and absence of live process execution; removing only the runner guard fails both subcases. B3-BH10 is resolved by documenting venv/ensurepip support in both Python prerequisites. Twelve other findings retain their recorded rejection or intentional-policy explanation. No new item is deferred. The concurrently completed agent-guidance refresh resolves its existing follow-up independently; the existing Dapr port-bind intermittence remains tracked.

The parent's final complete Python run passes 156 tests in 158.961 seconds with zero skips or failures. The selected Builds checkout again passes all 411 executable workflow assertions. All eight initial removal/pin-drift mutations and the additional runner-contract guard removal are detected. Default and Release source-property evaluations each resolve EventStore 3.128.3 for all three selected source servers, disproving the configuration-dependent receipt mismatch. Bash syntax, actionlint, whitespace and pinned commitlint validation pass.

The six pass-3 patches and both final-review corrections are complete. Production/build inputs and successful semantic acceptance remain unchanged from the historical native/.NET qualification; its archive was independently re-audited above. No fresh native, hosted or .NET run is claimed. All five matrix rows have executed passing coverage through the final Python output, fresh owner assertions and re-audited native packet. The original frozen intent and baseline revision remain intact. The Build spec is done; sprint status is review for maintainer acceptance. Evidence: [final parent verification](evidence/story-4-14/review-pass3-20261028/parent-final/README.md).

---
title: '4.18 Publish the validated package pair'
type: 'feature'
created: '2026-11-01'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'b8cf5d8e4093df4f1a4b565c2425ff929c45d578'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The paired staging gates exist, but publication still refuses the pair. The accepted 1.2.0 archives and operator sessions precede dependency, SDK and README changes; their acceptance cannot silently qualify new archives.

**Approach:** Publish only an immutable, accepted staging pair at the version selected by pinned semantic-release. Bind preflight to exact source, CI, package and operator evidence; record each public outcome. Correct the packed README and stage a fresh current-main pair before publication.

## Boundaries & Constraints

**Always:** Preserve historical evidence. Require clean exact current-main source, executed blocking CI/commitlint jobs and steps, dependency/inventory/conformance/live gates, FR-22 integration and instruction synchronization, three-platform staging acceptance, and candidate-specific acceptance. Accept either three fresh actual client sessions with an operator decision or the user's explicit automated-acceptance authorization, authenticated to the dispatch actor and bound to the exact candidate. Recheck after production approval and immediately before any push. Bind staging run, source SHA, both package IDs, shared version, receipt and archive hashes. Keep the existing assisted 685-second timing exception explicit in historical records; it is not first-time or unassisted success. Use existing GitHub production approval and short-lived NuGet publication credentials.

**Never:** Rebuild or repack during publication, substitute another archive bearing the same version, publish extra packages, infer new-package client acceptance from old sessions or automated authorization, hide a partial publication, retry an uncertain push automatically, expose credentials, or change production CLI/MCP behavior, enrollment or references. NuGet publication is irreversible and cannot make two pushes atomic.

**Decision (2026-11-01):** Repeat actual Claude Code, Claude Desktop and VS Code sessions against the fresh accepted pair in a newly approved ready environment, with the user's GUI participation. Preserve the accepted timing exception; no historical client-evidence transfer.

**Superseding decision (2026-11-02):** The user confirmed that the newer, committed automated-acceptance path may replace the three fresh client sessions for this publication. The authenticated actor must explicitly attest `user-requested-human-validation-bypass` for the exact staged pair; production approval and all source, staging, package and public-content gates still apply. Record the bypass as such and make no claim of candidate-specific client testing.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Accepted pair, matching candidate-specific approval through either permitted path, green exact source, credentials and both IDs available | Snapshot verified bytes; publish only Abstractions and tool at the selected shared version; retain resulting public verification |
| Missing/tampered evidence, different SHA/version/hash, stale/failed/skipped gate or extra package | Fail before either push; retain exact refusal |
| Missing key, occupied version or uncertain feed response | Fail before either push; handle a confirmed first-ever package absence explicitly |
| First push succeeds and second fails or is uncertain | Retain partial outcomes; fail the release; require an evidence-based recovery without automatic duplicate pushes |
| Bootstrap requested after paired publication starts | Refuse a new independent bootstrap version to protect the shared version line |

</frozen-after-approval>

## Code Map

- `scripts/prepare-paired-release.py`, `paired_release.py`, `compare-paired-evidence.py` — reuse immutable staging, manifest equality, evidence hashes, three OS receipts and required Windows assertions. Cross-check fresh acceptance-source evidence as part of publication validation.
- `scripts/verify-release-source.py`, `verify-paired-prerequisites.py` — current-main and latest exact-source workflow/job/step checks, FR-22 and synchronized instructions; paired publication is currently refused.
- `scripts/release-request.py`, `release-preflight.sh`, `release-prepare.sh`, `release-publish.sh` — bootstrap-only request, feed checks, preparation and checked snapshot push; add a separate paired path.
- `scripts/recover-bootstrap-release.py` — reuse signature-aware public-content comparison; never mistake repository signing for changed consumer content.
- `.github/workflows/release.yml`, `.releaserc.json` — staging artifacts, production/OIDC gate and semantic-release hooks; publication currently uploads bootstrap assets only.
- `docs/release/operator-setup-checklist.md`, `evidence/story-4-17/` under implementation artifacts — historical sessions, explicit timing exception and retained failures; do not rewrite their package bindings.
- `README.md`, `deferred-work.md:697`, `:739` — packed README relative links and story-specific environment history must be corrected before fresh packing.

## Tasks & Acceptance

**Execution:**

- [x] `README.md`, `docs/release/operator-setup-checklist.md`, `docs/release/operator-setup-history.md` — move historical environment detail out of the packed README, retain usable generic setup, fix package-rendered links, and document paired publication and partial recovery.
- [x] `scripts/verify-paired-publication.py`, `paired_release.py`, `compare-paired-evidence.py` — validate original staging artifacts/run, recomputed acceptance, current source and explicit operator decision; emit a hash-bound preflight receipt.
- [x] `scripts/release-request.py`, `verify-release-source.py`, `release-preflight.sh` — support paired preflight with both registry identities and full source gates; prevent later independent bootstrap releases.
- [x] `scripts/release-prepare.sh`, `release-publish.sh`, `publish-paired-release.py` — import the validated archives, snapshot/revalidate once, push only the pair, verify public contents and persist success/partial/failure receipts; refuse unsupported recovery before side effects.
- [x] `.github/workflows/release.yml`, `.releaserc.json` — select a specific staging run, retrieve and authenticate its artifacts, enforce version/source equality and production approval, retain both assets and receipts, and preserve bootstrap recovery isolation.
- [x] `scripts/tests/` — add meaningful refusal, exact-byte two-push, partial-failure, feed-uncertainty and workflow-binding tests; every new guard must fail a removal test.
- [ ] `_bmad-output/implementation-artifacts/evidence/story-4-18/`, checklist, this spec and `sprint-status.yaml` — stage the fresh green-source pair, retain either three actual client sessions and operator approval or the explicit candidate-bound automated authorization, retain preflight/publication evidence; advance only after both public packages verify.

**Acceptance Criteria:**

- Given accepted staged artifacts and completed candidate-specific approval through either permitted path, when preflight runs, then it proves exact green source, IDs, selected shared version and every blocking gate before any push.
- Given any failed preflight condition, when publication is requested, then neither paired package is pushed and the exact blocker is retained.
- Given successful preflight, when publication completes, then only the validated pair is public at semantic-release's shared version, with source-bound outcome and public-content evidence.
- Given partial or uncertain publication, when the run ends, then it fails visibly, preserves per-package outcomes and does not claim paired completion.

## Implementation Notes

Local implementation is complete; release acceptance is not. Local revalidation began with clean `main` at `17eb4fbbc151ca4b99dfa452e9f65655db2b402f`, which already contains the guarded paired-publication implementation introduced by `8d74baacbe0713950cf11e1fe348d77e98563f56`. This supersedes the uncommitted-source state recorded in the preserved original implementation evidence. The local-only implementation step performed no hosted source verification or staging, actual GUI client session, environment deployment, NuGet push, tag, commit or public verification.

The user subsequently authorized hosted execution on 2026-11-01. Exact-source CI and commitlint jobs/steps passed; fresh `stage-paired` [Release run 41307182275](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/41307182275) selected version 1.2.0 and passed Linux, Windows and macOS acceptance. The original artifact ZIP digests, recomputed acceptance, acceptance-source receipt, package identity/source and packed README were independently verified; [the candidate receipt](evidence/story-4-18/hosted-staging-20261101T123459Z/candidate.json) and [session bindings](evidence/story-4-18/hosted-staging-20261101T123459Z/session-bindings.json) retain their exact hashes. A local-only package handoff is prepared at `/tmp/mcpcli-4-18-41307182275/handoff`. The read-only NuGet observation confirmed both identities available at that time; it is not production preflight. No environment was deployed, actual client session performed or paired publication dispatched. The earlier environment is removed and its approval/credentials are expired; the new environment selection/approval and user GUI participation remain required.

- Publication retrieves original `stage-paired` artifacts through authenticated GitHub APIs, checks run/job/step execution and artifact ZIP digests, recomputes three-OS acceptance, verifies the separate acceptance-source receipt and packed README, and binds a fresh approval through either permitted path to exact source, shared version, archive/receipt/README hashes and staging run. Release-automation Python and pinned selector tests now run as a blocking full-CI job.
- `operator_acceptance` is a sanitized JSON dispatch input, authenticated by the dispatch actor and protected by the existing production environment approval. The actual-session path requires three sessions after fresh staging with approved ready environments, client evidence, persisted effects, failures and assistance. The user-authorized automated path requires an explicit candidate-bound attestation and contains no sessions. The historical assisted 685-second exception remains explicit in historical records. Known credentials are rejected before recording/copying; artifact retention excludes raw operator files and writes checked/redacted copies with hash provenance.
- Preparation imports original archives; publication snapshots once, rechecks source/evidence and remaining package availability immediately before each push, records durable global/per-version start markers plus push intent/results, and compares downloaded public consumer content with the accepted bytes while allowing NuGet repository signatures/core-properties metadata. Failed/uncertain pushes stop without retries. Paired recovery is refused before side effects; bootstrap recovery remains separate, and new bootstrap versions are closed after the pair line starts.
- The workflow requires a complete source/run-bound public-pair outcome; semantic-release returning no-release cannot count as publication. Historical evidence remains unchanged; generic README setup and package-rendered links replace the old environment-specific packed content.

The final execution row remains unchecked. Fresh hosted CI, three-OS staging and the newly approved ready environment were completed for the historical candidate above. For the current source, obtain fresh exact-SHA CI and three-OS staging, then use either candidate-specific actual sessions and operator approval or the user's explicit automated-acceptance authorization. Production approval and verification of both public versions remain mandatory before advancing this story. Local synthetic tests cannot supply public records or actual-client acceptance. The remaining checklist rows are pending and sprint status remains in-progress.

Following the user's selection of a fresh environment on `192.168.1.30`, the unchanged Platform-owned helper prepared [a concrete review packet](evidence/story-4-18/environment-20261101T124621Z/REVIEW.md) for new namespace/tenant `mcpcli-417-20261101-00c6a713`. Packet SHA-256 is `f2e88eb4dc9536709a0b1daf9193423cbb9011ddf5a8b59c7775fce1a97d598e`, expiring 2026-11-02T12:46:22.115384+00:00. All 61 focused Platform tests, exact packet/private-input verification, six client manifest dry runs and read-only target checks passed with a checksum-verified kubectl v1.34.9 matching the server. No cluster resources or application state were created. The owner procedure requires approval of this exact packet before deployment/bootstrap; environment readiness, seed and client sessions remain pending. Unrelated Platform working-tree changes were preserved.

The user then explicitly approved that packet. [Actual deployment](evidence/story-4-18/environment-20261101T124621Z/deployment.json) completed all 13 ordered phases through handoff on 2026-11-01, with namespace UID `2f5b7d0a-4988-4380-a026-7b1e1c39855e`, all four Pods Ready, real DNS and empty-store backup, Dapr actor/sidecar readiness, persisted administrator, exactly one writer activation, completed tenant/member seed and private non-admin operator profile. The exact accepted tool was installed from the local-only package handoff, and its operator-profile query verified the active tenant and persisted Contributor. Credentials remain private; the task-owned loopback forward automatically stops by operator token expiry **2026-11-01T16:07:34Z**. [Client handoff](evidence/story-4-18/environment-20261101T124621Z/operator-handoff.md) supplies an isolated actual Claude Code launcher and separate Desktop/VS Code fragments/tasks with fresh Party IDs. No actual client session or Party command has been performed or counted; these and candidate-specific operator/production acceptance remain pending. Cleanup follows the client sessions under the approved ownership-bound procedure.

The user subsequently completed actual Claude Code session `7ceb60f0-3ebf-490b-ba96-7ccb271ff745`. [Retained actual evidence](evidence/story-4-18/sessions/claude-code/attempt1/session.json) independently verifies the source-bound launch, actual connection identity/version, five exposed tools, nine successful calls with exact planned arguments, one accepted command `01M6BQKC4BC8AKQ5GEKE53VASX`, and the first persisted read of `party-418-code-20261101-1` with all required person/contact/identifier fields. Every text document equals its actual `mcpMeta.structuredContent`; the client does not retain an explicit raw `isError: false`, so that field was not reconstructed. Auto-mode permission records accept all nine calls, with no denials or tool failures. Client/server shutdown remains pending while that interactive process is open. Desktop's existing `hexalith` entry now points to the fresh installation/profile, with other entries preserved and a private backup; its actual GUI session and VS Code, followed by final operator/production acceptance, remain pending.

## Spec Change Log

- 2026-11-03: The user selected the upstream compatibility path that preserves the published query request wire. EventStore source already has exact owner-enrolled selector matching, but the pinned public 4.0.4 cohort does not. The [Parties owner-binding handoff](evidence/story-4-18/query-selector-compatibility/README.md) retains a source-verified patch for only the three affected query routes; its ordinary package build is blocked until a compatible EventStore cohort is published. No McpCli production behavior, approved vector, package pin, source selection, staging or public package was changed.
- 2026-11-02: [Bootstrap run 41510077761](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/41510077761) published only Abstractions 2.0.0 and tagged source `06cfdf25a352034b36041e9ed44da514b167ca5a`; the tool package remains absent. Pinned semantic-release reports no release from that unchanged source, and the occupied Abstractions 2.0.0 identity forbids a same-version pair. The next paired candidate needs a later shared version, a fresh exact-source commit and gates, then the usual approval and public checks. EventStore 4.0.0 is available; Tenants 7.0.0 remains unavailable on NuGet at this checkpoint.
- 2026-11-02: The user confirmed that the committed automated-acceptance path supersedes the three-session requirement for this publication. The automated decision now must postdate staging; a full simulated publication test covers this path without claiming sessions. The local selector returned 1.2.0 at source `74f932fac9e0ff510ff3ae6e2e80e39942e48765`, already newer than accepted staging source `17eb4fbbc151ca4b99dfa452e9f65655db2b402f`; main later advanced again. Fresh exact-source CI/staging, candidate-bound authorization, production approval and public verification remain pending.
- 2026-11-01: Repaired Desktop's historical WSL paths after the user confirmed full Windows app shutdown. Verified the exact Windows `wsl.exe` launch, renewed profile and live read-only tenant/member query; preserved other client entries and supplied native Windows handoff instructions. No actual Cowork session or domain write was inferred. Fresh current-main staging remains required.
- 2026-11-01: The user explicitly requested two more hours after operator access expired. [Renewal verification](evidence/story-4-18/access-renewal-20261101T163704Z/verification.json) confirms a new two-hour window ending 2026-11-01T18:37:04Z, identical authorization claims and profile fields except the token, retained old private profile, an owned replacement forward, HTTP 200 readiness and a persisted non-admin tenant/Contributor read. No bootstrap, deployment, domain command, package rebuild or publication was performed; original receipts and packet expiry remain unchanged.
- 2026-11-01: Source checkpoint detected current main `b224ac69c64fbe8af81f427bf406d54b2ba2d811` after staging `17eb4fbbc151ca4b99dfa452e9f65655db2b402f`. The new exact-source CI was observed in progress and commitlint successful. Publication requires fresh current-main staging and candidate-specific actual client sessions; no old-archive/client acceptance transfer or frozen-intent amendment was inferred.
- 2026-11-01: Recorded local implementation and pending external acceptance; frozen approved intent was not changed.
- 2026-11-01: Revalidated committed current-main release automation, corrected the stale uncommitted-source note and retained fresh local evidence; hosted/client/production acceptance remains pending and frozen approved intent is unchanged.
- 2026-11-01: With the user's authorization, verified exact-source hosted gates and completed fresh three-OS staging run 41307182275; retained authenticated original artifact/receipt bindings and prepared the package handoff. Environment/client/production acceptance remains pending; frozen approved intent and historical evidence are unchanged.
- 2026-11-01: Prepared and checked a fresh Platform environment packet for the user-selected target; exact packet deployment approval remains pending. No application or shared cluster change was made.
- 2026-11-01: After explicit packet approval, completed actual isolated deployment/bootstrap/seed/handoff and verified non-admin access through the accepted staged CLI. Prepared the three actual-client tasks; client/operator/production acceptance remains pending and frozen intent is unchanged.
- 2026-11-01: Verified and retained the user's actual Claude Code session, including all nine text/structured results and the single command/persisted Party. Prepared the Desktop configuration with a private backup; remaining clients, shutdown/cleanup and operator/production acceptance remain pending.

## Review Triage Log

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py'` — existing bootstrap and paired suites plus publication refusal/success/partial tests pass.
- `node --test scripts/tests/select-release-version.test.mjs` — pinned version-selection behavior passes.
- Fresh solution restore and Release build, then Manifest.Tests — approved packaged closure remains valid.
- Hosted exact-SHA full CI and three-OS staged acceptance — passed for the fresh candidate; approved operator evidence and production preflight remain required before publication.
- Public NuGet checks (pending) — require both resulting versions and signature-aware consumer contents verified; no completion based only on push exit codes.

Current local verification on 2026-11-02: all 140 release-automation Python tests and four pinned Node version-selector tests passed. The 24 focused paired-publication tests include both acceptance paths, a full simulated automated publication, and rejection of decisions before staging, in the future or without a timestamp. `git diff --check` passed. These checks do not establish hosted staging or public package acceptance.

Local verification on 2026-11-01 is retained in [the implementation evidence](evidence/story-4-18/local-implementation-20261101/verification.json): 138 Python tests passed; the latest publication-only rerun passed 22 tests including the second-identity occupancy race; four pinned Node selector tests passed; 24 in-memory guard removals were detected; fresh solution restore and Release build passed with zero warnings/errors; Manifest.Tests passed 267/267 with zero skips; 36 built-CLI README/profile/discovery/stdio checks passed with synthetic credentials and zero Gateway calls/actual GUI sessions; actionlint, shell syntax, instruction synchronization and diff whitespace checks passed. The failed pre-fixture-update run is retained separately; completion fixtures now preserve the same helper dependencies as the real workflow. Hosted exact-SHA CI/staging, actual candidate-specific client/operator acceptance, production approval and both public package checks remain unexecuted and mandatory.

Current-main revalidation is retained in [the fresh local evidence](evidence/story-4-18/local-revalidation-20261101T122403Z/verification.json), bound to `17eb4fbbc151ca4b99dfa452e9f65655db2b402f`: all 138 Python release-automation tests and four pinned Node selector tests passed; actionlint for the release/CI workflows, syntax checks for each release shell entry point, instruction synchronization and whitespace checks passed. These checks used synthetic release evidence and temporary local Git fixtures, with zero external remote operations, actual client sessions or NuGet pushes. They do not establish the remaining release acceptance.

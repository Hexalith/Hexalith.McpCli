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

**Always:** Preserve historical evidence. Require clean exact current-main source, executed blocking CI/commitlint jobs and steps, dependency/inventory/conformance/live gates, FR-22 integration and instruction synchronization, three-platform staging acceptance, and candidate-specific operator acceptance. Recheck after production approval and immediately before any push. Bind staging run, source SHA, both package IDs, shared version, receipt and archive hashes. Keep the existing assisted 685-second timing exception explicit; it is not first-time or unassisted success. Use existing GitHub production approval and short-lived NuGet publication credentials.

**Never:** Rebuild or repack during publication, substitute another archive bearing the same version, publish extra packages, infer new-package client acceptance from old sessions, hide a partial publication, retry an uncertain push automatically, expose credentials, or change production CLI/MCP behavior, enrollment or references. NuGet publication is irreversible and cannot make two pushes atomic.

**Decision (2026-11-01):** Repeat actual Claude Code, Claude Desktop and VS Code sessions against the fresh accepted pair in a newly approved ready environment, with the user's GUI participation. Preserve the accepted timing exception; no historical client-evidence transfer.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Accepted pair, matching operator evidence, green exact source, credentials and both IDs available | Snapshot verified bytes; publish only Abstractions and tool at the selected shared version; retain resulting public verification |
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
- [ ] `_bmad-output/implementation-artifacts/evidence/story-4-18/`, checklist, this spec and `sprint-status.yaml` — stage the fresh green-source pair, repeat the three actual client sessions, retain preflight/publication evidence; advance only after both public packages verify.

**Acceptance Criteria:**

- Given accepted staged artifacts and completed candidate-specific operator acceptance, when preflight runs, then it proves exact green source, IDs, selected shared version and every blocking gate before any push.
- Given any failed preflight condition, when publication is requested, then neither paired package is pushed and the exact blocker is retained.
- Given successful preflight, when publication completes, then only the validated pair is public at semantic-release's shared version, with source-bound outcome and public-content evidence.
- Given partial or uncertain publication, when the run ends, then it fails visibly, preserves per-package outcomes and does not claim paired completion.

## Implementation Notes

Local implementation is complete; release acceptance is not. The working tree is intentionally uncommitted and cannot pass exact clean-current-main gates. No hosted staging, actual GUI client session, environment deployment, NuGet push, tag, commit or public verification was performed in this implementation turn.

- Publication retrieves original `stage-paired` artifacts through authenticated GitHub APIs, checks run/job/step execution and artifact ZIP digests, recomputes three-OS acceptance, verifies the separate acceptance-source receipt and packed README, and binds a fresh explicit operator decision to exact source, shared version, archive/receipt/README hashes and staging run. Release-automation Python and pinned selector tests now run as a blocking full-CI job.
- `operator_acceptance` is a sanitized JSON dispatch input, authenticated by the dispatch actor and protected by the existing production environment approval. Its three actual sessions must postdate fresh staging and retain their own approved ready environment, actual client evidence, persisted effects, failures and assistance. The historical assisted 685-second exception remains explicit. Known credentials are rejected before recording/copying; artifact retention excludes raw operator files and writes checked/redacted copies with hash provenance.
- Preparation imports original archives; publication snapshots once, rechecks source/evidence and remaining package availability immediately before each push, records durable global/per-version start markers plus push intent/results, and compares downloaded public consumer content with the accepted bytes while allowing NuGet repository signatures/core-properties metadata. Failed/uncertain pushes stop without retries. Paired recovery is refused before side effects; bootstrap recovery remains separate, and new bootstrap versions are closed after the pair line starts.
- The workflow requires a complete source/run-bound public-pair outcome; semantic-release returning no-release cannot count as publication. Historical evidence remains unchanged; generic README setup and package-rendered links replace the old environment-specific packed content.

The final execution row remains unchecked. Integrate reviewed source, wait for hosted exact-SHA blocking CI, stage a fresh three-OS pair, obtain the owner's newly approved ready environment and the user's actual Claude Code/Desktop/VS Code sessions, create candidate-specific operator approval, then use production approval and verify both public versions before advancing this story. Local synthetic tests cannot supply these records.

## Spec Change Log

- 2026-11-01: Recorded local implementation and pending external acceptance; frozen approved intent was not changed.

## Review Triage Log

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py'` — existing bootstrap and paired suites plus publication refusal/success/partial tests pass.
- `node --test scripts/tests/select-release-version.test.mjs` — pinned version-selection behavior passes.
- Fresh solution restore and Release build, then Manifest.Tests — approved packaged closure remains valid.
- Hosted exact-SHA full CI, three-OS staged acceptance, approved operator evidence and production preflight — all required before publication; local checks cannot replace hosted/client evidence.
- Public NuGet checks — both resulting versions and signature-aware consumer contents verified; no completion based only on push exit codes.

Local verification on 2026-11-01 is retained in [the implementation evidence](evidence/story-4-18/local-implementation-20261101/verification.json): 138 Python tests passed; the latest publication-only rerun passed 22 tests including the second-identity occupancy race; four pinned Node selector tests passed; 24 in-memory guard removals were detected; fresh solution restore and Release build passed with zero warnings/errors; Manifest.Tests passed 267/267 with zero skips; 36 built-CLI README/profile/discovery/stdio checks passed with synthetic credentials and zero Gateway calls/actual GUI sessions; actionlint, shell syntax, instruction synchronization and diff whitespace checks passed. The failed pre-fixture-update run is retained separately; completion fixtures now preserve the same helper dependencies as the real workflow. Hosted exact-SHA CI/staging, actual candidate-specific client/operator acceptance, production approval and both public package checks remain unexecuted and mandatory.

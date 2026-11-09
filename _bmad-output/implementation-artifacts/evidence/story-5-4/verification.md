# Story 5.4 verification

The candidate is **3e8f6a4e681018c7ca8356997d4fd28378217d37**, qualified by CI run
[42652261452](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/42652261452) on
[draft PR #5](https://github.com/Hexalith/Hexalith.McpCli/pull/5). The selected
CI topology passed every approved vector, both independent cases and the
hosted enrolled-artifact gate. `fullLiveAccepted` and `fullV1Accepted` are true
in the receipts bound by [manifest.json](manifest.json).

**Owner approval is pending.** The proposal is `retirement-blocked`, retaining
G01–G06 with the named owners in [parity-matrix.md](parity-matrix.md). There is
no owner verdict or inventory 1.3.0 amendment in this snapshot. Story 5.5 owns
retirement; the separate release gate remains binding.

## Evidence binding

[manifest.json](manifest.json) records the full PR candidate and the actual
hosted checkout commit. GitHub's PR checkout may use a synthetic merge commit;
the recorded Git tree hashes are equal. It includes every DLL hash from the
exact ConformanceHost directory used by CLI and stdio MCP, before/after capture
stability, the Parties 1.5.1 NuGet SHA-512 and SHA-256, its nuspec repository
commit, per-module Catalog digests and the combined map digest. Each digest
hashes sorted-key, compact UTF-8 `list_operations` structured content with
Unicode preserved. The captured CLI/MCP discovery documents are equal.

The manifest also binds actual source/environment revisions, published package
archives, runtime images/binaries, tooling, release inventories, approved
vectors/plans/approvals, CI IDs and independently verified downloaded ZIP
SHA-256 values. [ci/artifacts.json](ci/artifacts.json) indexes every original
artifact member and every retained text file by hash. NuGet archives are not
embedded in this text packet; their exact original bytes remain bound by the
verified ZIP and per-member hashes. Original UTF-8/XML logs are sanitized by
the shared prerequisite redactor and terminal control sequences are rendered;
the index records every transformation. TRX text is named `*.trx.xml`.

Run `python3 scripts/scan-evidence-secrets.py
_bmad-output/implementation-artifacts/evidence/story-5-4/ --receipt <new-path>`
from the repository root to rescan the whole packet. The committed
[secret-scan.json](secret-scan.json) has zero findings and zero scan errors;
it binds every other packet file and the scanner/redactor implementations.
The receipt excludes itself, so the owner checkpoint binds both its complete
SHA-256 and its `manifestSha256`, plus the explicit `manifest.json` digest.
No receipt of approval is invented. Any subsequent evidence change requires
a fresh exact-byte review and scan.

## Checks executed

- Solution restore and Release build with `-warnaserror` passed. The latest
  build had zero warnings and zero errors.
- The six hosted ordinary projects passed 1985 tests, with six
  OS-only skips: Core 877, CLI 613, MCP 94, Manifest 362, Abstractions 20 and
  Analyzers 19. All six TRX documents are retained under `ci/ordinary-tests/`.
  The dependency-policy and enrolled release-inventory tests remain unchanged.
- All 77 named offline safety, compatibility, process-harness and identity
  cases passed without skips in [local/offline-cases.xml](local/offline-cases.xml).
  The 22 process cases each exercise both real CLI/MCP processes and pin full
  documents, stdout/stderr, MCP Content/StructuredContent and request counts.
- Hosted topology discovery passed all 216 Python cases, then discovered
  exactly the currently approved 21 vector cases plus smoke and boundary.
  [ci/topology-summary.txt](ci/topology-summary.txt) retains the exact log
  excerpt and original job-log hash. Preflight receipts are in `preflight/`;
  preflight correctly retains `fullLiveAccepted: false` and starts no source
  services.
- The clean local CI-hook sweep passed 99 tests. The prior initial sweep had
  five stale order/count expectation failures after moving boundary first;
  focused corrected subcases and the clean final sweep are retained separately.
  No Python source changed after that final passing sweep.
- Hosted `check_enrolled.py` passed all seven Parties and fourteen Tenants
  approved operations through isolated artifact and combined production
  CLI/MCP replay, with `fullV1Accepted: true` in `enrolled/enrolled.json`.
- The live lane passed all 21 approved vector receipts and independent boundary
  and smoke. Query observations ran through CLI and MCP. Every live Command
  was submitted once; parity for equivalent Commands comes from reset
  loopback, rather than resubmitting a live mutation.
- [live-verification.json](live-verification.json) independently recomputes
  Catalog and binding hashes, checks complete vector coverage and required
  phases, checks each independent test's single passing XML case, validates the
  boundary's 45 case receipts, and confirms private namespace ownership and
  cleanup for the derived 23 runtimes. The retained verifier source is
  [verify-live.py](verify-live.py).
- Every exact full commit message was checked by the repository's pinned
  `npx --no -- commitlint --verbose` after `npm ci`. Full successful validation
  text is retained under `local/commitlint-*.txt`, including the evidence
  commit message. No validation was bypassed.

## Boundary behavior and limits

The real boundary checks sixteen credential/tenant-grant cases, two MCP
per-call override cases, twenty-four zero-call tenant negatives, one first
missing-target deactivation per head and a concurrent deactivation pair.
Authorized reads compare every business-state member before and after each
refusal; only observation-time freshness is excluded. Missing targets remain
business-absent. The concurrent pair has distinct message IDs, both Commands
are accepted, the authorized projection is inactive, and exactly one
`PartyDeactivated` event is persisted in the actor stream. A rejection-only
stream can remain for a missing target; G01 explicitly prevents a stronger
claim about a second non-create Command on that stream.

[gateway-refusal-audit.json](gateway-refusal-audit.json) binds the qualified Gateway source hashes and exact handler/client anchors to these observed formats. The selected Gateway emits structured Query 401/403 documents, can emit an
empty invalid-token Command 401, and rejects missing Command tenant grants by
returning `Forbid()` before its structured pipeline. The harness pins the whole
existing public fallback documents (`Unauthorized` / 401 and `Forbidden` /
403), including absent optional metadata, as well as every complete known
problem document. Missing-token documents are compared directly between heads
per call kind. Live receipts record response format and the full safe public
error. Query tenant refusals keep the strict structured oracle.

[state-reader-audit.json](state-reader-audit.json) binds the qualified actor registration, identity/state keys, numeric metadata sequence, flat persisted envelope and exact CLR event-name formats used by the C05 reader.

The signed controls prove the Gateway's credential/grant boundary, not current
persisted Parties membership or persisted actor attribution. The independent
bootstrap verifies native administrator membership. G04 retains the separate
actor-attribution gap. The accepted F7 Kelvin alias is bound by
[f7-acceptance.json](f7-acceptance.json); item 9 stays open and all other
specified look-alikes fail locally without a Gateway request.

The matrix distinguishes upstream tests **present at the enrolled revision**
from tests actually executed here. [upstream-test-audit.json](upstream-test-audit.json)
binds those source hashes and exact method anchors. It also binds the complete
legacy source audit establishing absent task-context, freshness and output
budget behavior. Matching Admin or technical names supplies no replacement
evidence.

## Previous qualification attempts

Prior failures are retained under `attempts/` with their own run IDs, candidate
commits, exact artifact hashes and `fullLiveAccepted: false` status. Run
42631573309 passed all vectors and smoke before finding the original structured
401 oracle mismatch. Boundary-first run 42641067905 then found the empty
invalid-token Command 401; run 42645969397 found the empty pre-dispatch Command
403. The subsequent candidate retains full structured assertions, adds exact
transport-fallback process regressions and preserves direct missing-token head
parity. Run 42648730822 then reached the first persisted-state C05 read and exposed its fixed sidecar port. The fixture now discovers the exact private Dapr registration, and thirteen ephemeral-port/state-key/API-token regressions protect both persisted-state oracles. Failed attempts are not promoted into final live acceptance.

## Scope checks

`src/`, identifier validators, production dependencies, dependency policy,
approved Contracts versions, vectors, live plans, approval files, release
inventories and all reference gitlinks are unchanged from the spec's baseline.
The manifest records the compared paths and commits. Production behavior did
not require a fix; changes stay in tests, generic live CI/capture code and
documentation/evidence. Redactor item 5 remains its separately landed change,
and F7 is accepted only within the frozen limitation.

The exact-byte Parties owner checkpoint is the only remaining Story 5.4 step.
It must explicitly disposition each gap and approve either `retirement-ready`
or `retirement-blocked` for this packet. No release, publication or retirement
follows from this pending snapshot.

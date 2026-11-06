---
title: 'Restore green main CI'
type: 'bugfix'
created: '2026-11-06'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Restore hosted main CI for Epic 4 retrospective F1, including topology-vector-discovery and the blocking complete Aspire lane. Diagnose the uploaded failures, align workflow pins with the current Builds gitlink, preserve the qualified native source selection, and fix repository-owned dependency/source-reader mismatches. Extend the synchronized agent instructions to require workflow pin updates with Builds changes. Do not edit upstream sources, touch Epic 5, weaken acceptance, or claim local checks establish live acceptance. Stop and report any demonstrated upstream failure.

</frozen-after-approval>

## Implementation Notes

- Baseline: clean `main` at `a8792ab1c4843a102988f1ccb49fde5df01fd382`. Last green: run 42130012324. Compared its evidence with failed runs 42184403625, 42191198755, and 42195205971 downloaded to task-owned `/tmp/mcpcli-green-main-*` directories.
- Both earlier failures contain 21 failed vectors plus smoke, all throwing `RouteCatalogUnavailableException: The complete compiled declaration inventory cannot be read` during composition, before operation execution. Both aggregate `vectors-process.stderr.txt` files are empty; individual xUnit XML retains the common stack.
- The native-runtime source/package selection and root version pins did not change. Builds changed its default McpCli version to 2.0.1; failed preparation rebuilt Parties against Abstractions 2.0.1 while the AppHost and Tenants use 2.0.0. Keep native source builds on the root McpCli pin, including subsequent SDK/Aspire rebuilds.
- The latest failure occurs before execution: the reader audit requires `PublishedCatalogArtifactCohort.cs`, absent from frozen Platform `ee6f477c595defb79e17ca6ea3e5790de24c114e`. Seal/copy the actual supported template inventory; retain drift rejection for every sealed file and reject injected source.
- Choice presented before implementation: align CI/commitlint workflow pins to Builds `beb85e497957fedc66854013efd2cc4bd216ecbc`; keep all gitlinks. This is a small, reversible CI consumer repair with no public API changes, intent gaps or irreversible data operations.
- Verification required: solution restore; Release build with warnings as errors; Manifest.Tests; all live-topology Python tests; complete preflight; instruction synchronization; hosted main CI success. Validate every exact commit message with the pinned commitlint before committing, and recheck HEAD immediately before each commit.

- A focused loader probe in `/tmp/mcpcli-green-main-cohort-probe/` reproduced the exact catalog failure with the failed run’s Abstractions 2.0.1 bytes (`aeb390050b08451827b147a958ba355e1e5c96de526834221645028b85c26c2e`). The underlying error is `FileLoadException` 0x80131040. The identical frozen Parties source rebuilt against 2.0.0 reads all 41 declarations in the 2.0.0 process. This establishes consumer ownership rather than an upstream runtime defect.

- Implementation: current Builds workflow pins aligned; root McpCli pin applied to initial source builds and inherited post-import package overrides; optional cohort source sealed only when present, with absence/addition drift checks and copied-source allowlisting retained. Agent instruction copies pass byte synchronization.
- Local verification: restore and final Release build passed without warnings; Manifest.Tests retry passed 359/359 after the first run had one ephemeral socket bind failure; the final changed reader/audit classes passed 65/65. Complete preflight and discovery found all 21 vectors plus smoke. Real MSBuild override and initially absent-cohort runner controls passed. Full live-topology suite remains running; hosted acceptance remains pending.

## Review Triage Log

- Low, rejected: add a separate Abstractions diagnostic policy across all prepared outputs. This is an additional diagnostic enhancement; explicit source pins, real MSBuild evaluation, archive audits and the complete blocking lane cover the demonstrated failure. No remaining mismatch was shown under the new settings, and another policy guard exceeds a simple correction.
- Medium, patched: fake process assertions did not exercise inherited MSBuild package overrides. Added real evaluation of a 2.0.1 source default under the inherited override; resolved version is 2.0.0.
- Medium, patched: initially absent-cohort C# negative paths lacked direct protection. Added original/copy source-injection cases plus an audit test that accepts absence and rejects subsequent addition.
- Medium, patched: absent-cohort Python control stopped before runner propagation. It now executes both vector and smoke hooks with the same six-input audit before checking addition drift.

- First complete Python run: 196 passed, one failure in an exact diagnostic command expectation missing the newly added version flag. Updated that expectation without changing its strictness; focused rerun passed. The complete final rerun is pending alongside hosted qualification.

- Final complete Python rerun passed 198/198. Repair commit `6725d953d160eafba85b8bf9e11eea2e665d3684` is pushed to main and is qualifying in hosted CI run 42213303320. No live acceptance is claimed while that run is pending.

- Hosted acceptance achieved: main CI run 42213303320 succeeded for `6725d953d160eafba85b8bf9e11eea2e665d3684`, including both required jobs. Downloaded receipts confirm all 21 passing vectors, one passing unskipped smoke and `fullLiveAccepted: true`. Evidence: `evidence/epic-4-retro-item-1/hosted-acceptance.json`. The retrospective action is done.

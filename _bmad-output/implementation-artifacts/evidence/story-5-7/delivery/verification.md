# Story 5.7 completed delivery

The user approved the exact inventory candidates and Git delivery with **"approve"** on 2026-11-13. The receipt records all twelve previously confirmed owner roles. Inventory approval grants disposition authority only; no operation execution, enrollment, package publication, parity or retirement is authorized.

## Published inventories and labels

The approved inventories and exact approval receipt are present at McpCli `42d3c2fd48405e0f2c27f9b61f6d7025e4246934` and current origin/main. [authorization.json](authorization.json), [inventory-publication.json](inventory-publication.json) and [label-publications.json](label-publications.json) retain exact instructions and delivery/read-back results.

| Repository | Integrated README-only commit |
| --- | --- |
| eventstore | `639c9d5c0c8c8fba14aaec536dd1c2e3ceaccc13` |
| frontcomposer | `19418a0c29daf38eef03b0891958cd8aa93c59bf` |
| parties | `6bc68c8fad27209b80c4dd1a5a0271519de09f33` |
| memories | `a3f0b3a4a0f0905f6b88da039491ceb286103207` |
| projects | `065f04773a34a8e68b702caeb99937ae7b8e89c8` |
| folders | `583d3d492f94217809a8efe00424b80ce3fdfa61` |
| chatbot | `6a4ca07b18e9b58500dc79dfede1f308da36c828` |

All fourteen labels retain independent module gates, and the exact inventory hashes in every citation match the owner-approved candidates. Admin uses confidential UI coverage and safety gates; compiler and owner-held vector-migration tools remain retained exemptions. No surface is counted as retired.

## Validation

[checks-after-integration.json](checks-after-integration.json) records both approved-completion commands passing, all 27 tests passing, unchanged AD-23 adoption and a clean whitespace check. [commitlint.json](commitlint.json) binds the exact validated messages and pinned CLI versions; owner commits were validated again after any rebase. The initial Parties tooling install refused a runtime mismatch, then passed with the already installed Node 24.22.1 and npm 11.19.1. No dependency version or repository configuration was changed.

Fresh principal-input and complete-packet secret scans are retained with their exact source/hash bindings after the final state update. Historical receipts remain intact; a later receipt does not rewrite its earlier evidence.

## Concurrent work and CI limits

A concurrent /pushall session committed prepared story files and moved ten root gitlinks before the publication commit. The original story baseline remains 48076b1bd041b45250597937da82594e202985f3, while the actual publication parent is 3c24dcf003727a40c782d9040c65e50009e48b41. [mcpcli-ci-comparison.json](mcpcli-ci-comparison.json) proves that source, tests, tools, references, build configuration and workflows are unchanged between that parent and the publication commit. The task does not revert those concurrent reference updates.

[owner-worktree-observations.json](owner-worktree-observations.json) records concurrent changes in the original EventStore, FrontComposer and Parties checkouts. This task edited README files only in its isolated worktrees. The original working files and unrelated Platform gitlink modification are preserved, rather than asserting that concurrent state stayed unchanged.

Broad McpCli CI is red at [run 43387948285](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/43387948285), and [Bootstrap package 43387948146](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/43387948146) also fails restore. These failures are outside the disposition/label change:

- `dotnet restore Hexalith.McpCli.slnx` fails NU1202 because Hexalith.Commons.UniqueIds 3.0.0 supports net11.0 while these targets remain net10.0. The bootstrap author-time restore has the same incompatibility.
- `python3 tools/proprietary-surfaces/v1/check.py --output "$RUNNER_TEMP/proprietary-surface-census/census.json"` fails on the inherited Builds pin: source drift in Tools/package-version-audit.json and unresolved publication targets/directories in three PowerShell qualification scripts.

The immediate parent runs were cancelled, so no claim is made that they produced the same failures. Unchanged build/census inputs establish that the delivery commit did not introduce these configuration changes. Detailed job results and the observation-time states of owner CI runs are retained in [mcpcli-ci-jobs.json](mcpcli-ci-jobs.json), [mcpcli-immediate-parent-ci.json](mcpcli-immediate-parent-ci.json) and [ci-observation.json](ci-observation.json). Many owner runs were still queued or running at observation time; no all-green CI claim is made.

GitHub reported **"Bypassed rule violations for refs/heads/main"** on the EventStore and Memories maintainer pushes. Their exact server messages are preserved in label-publications.json. All pushes were fast-forward deliveries under the explicit owner authorization; no force push was used.

The 2026-11-13 review follow-up resolves the initially queued owner checks above.
[Final owner CI observations](../review-pass-2/owner-ci-final.json) retain the
GitHub GET URLs, terminal workflow states, failed steps and bounded log excerpts:

| Owner delivery | Final required-workflow result | Inherited failure evidence |
| --- | --- | --- |
| EventStore `639c9d5c` | [CI failed](https://github.com/Hexalith/Hexalith.EventStore/actions/runs/43388136260) | `Prepare module build` reports unavailable Platform release-tag/cohort prerequisites (HXW011/HXW009/HXW007); `Fail on blocking test failures` then reports no Tier 1 failure count. Earlier main `d457ecd5` and `f2062f7f` already fail the same two steps. The delivery remains README-only; no build failure is attributed to label text. |
| Memories `a3f0b3a4` | [CI passed](https://github.com/Hexalith/Hexalith.Memories/actions/runs/43388157817) | All observed workflows passed. |
| FrontComposer `19418a0c` | [CI passed](https://github.com/Hexalith/Hexalith.FrontComposer/actions/runs/43388143372) | Quality and other observed workflows also passed. |
| Projects `065f0477` | [CI passed](https://github.com/Hexalith/Hexalith.Projects/actions/runs/43388163130) | All observed workflows passed. |
| Folders `583d3d49` | [CI passed](https://github.com/Hexalith/Hexalith.Folders/actions/runs/43388170637) | The contract-spine gate and other observed workflows also passed. |
| ChatBot `6a4ca07b` | [ci failed](https://github.com/Hexalith/Hexalith.ChatBot/actions/runs/43388176975); [release failed](https://github.com/Hexalith/Hexalith.ChatBot/actions/runs/43388176969) | Parent `62e82201` fails the same xUnit runner/evidence-producer and live topology/recovery/evidence steps. Both topology logs report `SelectedEndpointStartupException` with the chatbot resource `FailedToStart`; the ordinary test step's console redirects its detailed results to artifacts, so no narrower cause is claimed. |
| Parties `6bc68c8f` | [CI cancelled](https://github.com/Hexalith/Hexalith.Parties/actions/runs/43388149065) | Some jobs failed before cancellation. The UI build repeats parent `f5321450`'s NU1109 downgrade from Fluent UI 5.0.1's required ASP.NET 11 preview to the central 10.0.15 pin; the parent CI also failed. CodeQL was cancelled; commitlint and the release-candidate gate passed. Cancellation is not a passing acceptance result. |

EventStore's separate Integration Tests workflow was still running at this
follow-up observation; its result is not represented as terminal or passing.
These findings retain the bypass disclosure and do not expand Story 5.7 into
upstream build, dependency or runtime repairs.

The seven clean delivery worktrees and their merged local branches were removed
without force during the review follow-up. [Cleanup evidence](../review-pass-2/worktree-cleanup.json)
records clean-status and ancestry checks, exact removal commands and unchanged
original checkout HEAD/status observations. Historical creation records in
`worktrees.json` remain intact.

Story implementation is complete and its sprint entry is review. The broad CI blockers remain visible and were not weakened or repaired through dependency, census or gitlink changes in this task.

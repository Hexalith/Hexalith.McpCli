---
title: Audit follow-up for release qualification and operator workflows
created: '2026-11-20'
status: applied
review_mode: batch
scope: sprint plan
baseline: 53205cdbd4226667f0237c68b4379a6f2e54c7aa
source_action: 'User selected “Apply the recommendations to the sprint plan”.'
approval: 'On 2026-11-20 the user approved the sprint change proposal for stories 5.13–5.21 as recorded in c1001cae (“approve proposal”).'
---

# Sprint change proposal · 20 November 2026

## Issue and impact

The audit of McpCli main found three immediate release risks. Native CI failed before live qualification, the committed-reference census failed locally and lacked enforcement in the active Linux product hook, and the paired-release runbook described a staging interface the delivered workflow no longer offers. The local Release build, six .NET test suites and offline enrollment checks provide evidence for the core product. They cannot establish what the skipped platform jobs or the live Gateway would have returned.

The change adds nine independently deliverable follow-ups to the active migration epic. Stories 5.10 and 5.11 are already in progress. Their owners can use the new findings when recording product claims. Epic 6 retains its existing Folders prerequisites. A rollback would discard functioning enrollment and shared-head behavior. A new epic or an MVP redesign would add coordination without resolving the failing checks.

## Evidence and disposition

Paths and line numbers refer to the baseline commit. Estimates are engineering days and exclude waiting for hosts, CI capacity or owner decisions. The linked stories contain the acceptance criteria.

| Story | Audit evidence and consequence | Effort |
|---|---|---|
| [5.13 · Native CI](epics.md#story-513-restore-the-native-dependency-audit-and-live-ci) | The Linux after-unit-tests hook failed after cached and HTTP 200 advisory content differed. The retries read the same cache. Feed rotation is a hypothesis. Windows and macOS skipped. Preflight discovered 22 vectors and two independent cases. See `tools/live-topology/native_audit.py:138` and `.github/actions/after-unit-tests/action.yml:15`. | 1–3 days |
| [5.14 · Census](epics.md#story-514-restore-the-proprietary-surface-census-gate) | The committed-tree scan of 18 roots reported 40 rejected surface records, 42 stale entries and 13 errors, including an unapproved CiCd root. These are distinct report categories. Story 5.6 describes enforcement, but the active Linux product checks omit the scan. See `scripts/product_ci.py:135` and `tools/proprietary-surfaces/v1/README.md:7`. | 2–4 days plus owner review |
| [5.15 · Paired release](epics.md#story-515-bind-paired-release-acceptance-to-the-published-candidates) | The runbook asks for `stage-paired` and `paired`. The delivered workflow accepts `delivered-sha`, CI stages fixture packages, and the central builder packs the final archives. The audit could not link the operator and platform evidence to those exact bytes. See `README.md:142`, `README.md:162`, `.github/workflows/release.yml:4`, `scripts/product_ci.py:67` and `references/Hexalith.Builds/Github/lib/release_build.py:254`. | ½ day to correct guidance once confirmed, 2–4 days for controls and rehearsal |
| [5.16 · Credentials](epics.md#story-516-protect-profile-credential-entry-and-transport) | One onboarding procedure passes the token to a child process in argv. Another edits the profile file outside the transaction. The bearer handler also adds the header for a configured remote HTTP connection. See `README.md:208`, `README.md:337`, `src/Hexalith.McpCli/Hosting/StaticBearerTokenHandler.cs:11` and the Story 2.3 deferral in `_bmad-output/implementation-artifacts/deferred-work.md:256`. | 2–3 days |
| [5.17 · Acknowledgments](epics.md#story-517-validate-gateway-command-acknowledgments) | An HTTP 202 with an empty message ID produced a successful CLI result with an unusable ID after one submission. Core only handles null. See `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:254` and `_bmad-output/implementation-artifacts/deferred-work.md:296`. | ½–1 day |
| [5.18 · Tenant selection](epics.md#story-518-reject-non-ascii-public-tenant-input-before-normalization) | Current tests pin a Unicode character folding into a valid ASCII tenant. The F7 receipt accepts that limitation pending a coordinated fix. See `tests/Hexalith.McpCli.Cli.Tests/PartiesRetirementSafetyTests.cs:127` and `_bmad-output/implementation-artifacts/deferred-work.md:851`. | ½–1 day locally after the upstream change |
| [5.19 · Profile integrity](epics.md#story-519-enforce-the-profile-size-limit-before-replacement) | A successful update took a readable 1,048,573-byte file to 1,048,596 bytes. The next read refused it. See `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:81` and `src/Hexalith.McpCli.Core/Settings/ProfileFileTransaction.cs:38`. | ½–1 day |
| [5.20 · Process cleanup](epics.md#story-520-detect-unsupported-linux-process-supervision) | A focused timeout test failed again in the restricted Linux environment. The detached descendant survived when the procfs child lists were unavailable. The hosted script suite had passed. See `scripts/product_process.py:25` and `scripts/tests/test_product_process.py:35`. | ½–1 day |
| [5.21 · Projects reads](epics.md#story-521-qualify-populated-projects-reads-and-access-denial) | The list vector expects zero items and an Unavailable component. The plan invokes just that vector. Populated paging and authorization on the native Projects host remain unqualified under DW-82. See `README.md:531`, `tools/live-topology/plans-current/projects.list.json:7` and `tools/conformance-vectors/v1/current/modules/Hexalith.Projects.Contracts/list.vector.json:68`. | 3–7 days once the host and seed data are available |

Hosted CI for the audited commit still recorded a failed Linux job and skipped platform jobs on 20 November. The release run on that commit also stopped while resolving release identity, before building a payload. Its result supplies no evidence about final archive acceptance. [CI run 44703606757](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/44703606757) · [Release run 44715773736](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/44715773736)

## Sprint order and ownership

1. **Start with release evidence.** The McpCli maintainer investigates 5.13 first. The migration owner can begin census triage (5.14) and the release owner can confirm the current operator procedure with CiCd (5.15) while CI is being diagnosed. A passing exact-commit run is needed to qualify a release. The census requires owner-reviewed dispositions, and final package acceptance needs a central release decision.
2. **Take the small fixes as capacity opens.** Core can deliver acknowledgment validation (5.17) and the profile size guard (5.19) independently. The CI maintainer can take process supervision (5.20) without waiting for the hosted feed investigation. Begin credential design (5.16) early and coordinate its profile transaction changes with 5.19 to keep both reviews small.
3. **Schedule the owner-dependent evidence.** Contact the EventStore owner through the normal project process when 5.18 enters refinement. Complete the upstream tenant change before switching McpCli's compatibility expectation. Schedule 5.21 with the Projects and environment owners once a host and synthetic data are available. Projects host qualification gates Projects claims and cutover decisions.

## Changes applied and implementation handoff

| Artifact | Before this change | Applied to the plan |
|---|---|---|
| [Epic breakdown](epics.md) | Epic 5 ended at 5.12. Some audit issues appeared only in retrospective or deferred-work records. | Added 5.13–5.21 with owners, verification criteria and references to existing decisions. |
| [Sprint tracker](../implementation-artifacts/sprint-status.yaml) | No schedulable follow-ups for this audit. | Added nine `backlog` entries under Epic 5. Each can enter `ready-for-dev` once its implementation story is prepared. |

**Product and architecture impact.** During refinement, 5.15 must reconcile FR-20/21 and AD-17 with the chosen central release controls. For 5.16, update FR-13/18, addendum §E and AD-13/14 with the selected private token input and transport rules. For 5.17, clarify FR-17 and addendum §G with the malformed-success outcome. For 5.18, update AD-22 with the upstream public tenant rule. For 5.21, record the paging decision under AD-20 with the owning teams. The profile size guard enforces the store's existing read limit. The CLI setup guide and release runbook are the affected operator interfaces. Their user-visible changes belong with the respective implementations and owner decisions.

**Handoff.** This is a moderate backlog adjustment. The product owner sequences the nine stories alongside 5.10 and 5.11. McpCli developers take the module-owned code, tests and guides. Reference owners approve exact census amendments. CiCd and the release owners decide final archive controls. EventStore and Projects retain their existing upstream decisions. The requested planning work is complete when each audit finding has a tracked story, an owner and a verifiable outcome. Each implementation story closes on its own acceptance evidence.

**BMAD review record.** Items 1.1–2.5 cover the audit trigger, affected stories and Epic 6 dependencies. Items 3.1–3.4 cover the PRD, architecture, CLI operator flows and delivery artifacts. Items 4.1–5.5 cover the alternatives, estimates and handoff. These reviews are complete. Items 6.1–6.5 are complete for the sprint-plan scope the user selected. Release controls, census amendments, the EventStore change and Projects host qualification still require the owner decisions identified above.

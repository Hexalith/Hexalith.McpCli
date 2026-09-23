# Sprint Change Proposal — Readiness-Gate Story Criteria

**Date:** 2026-09-23  
**Project:** Hexalith.McpCli  
**Disposition:** Direct adjustment to existing stories, requested and applied in `epics.md`.

## 1. Issue Summary

The sprint-status readiness gate identified two ownership gaps: Story 1.1 did not enumerate the architecture's full structural seed, and Story 2.5 assumed a live Gateway and a declared list-Query aggregate identifier before Stories 4.12 and 4.8 provide them. A separate action noted that Story 3.1 omitted AD-12's `destructiveHint: true` for `send_command`.

Evidence: `sprint-status.yaml` action items for Epics 1, 2, and 3; the architecture's Structural Seed, AD-12, AD-17, and AD-19; the existing EventStore AppHost's local Tenants composition and its `list-tenants` request using `index`.

## 2. Impact Analysis

| Area | Impact |
| --- | --- |
| Epic 1 / Story 1.1 | Own the root build, release, commitlint, and workflow seed required by later stories. |
| Epic 2 / Story 2.5 | Run the early query spike against locally started EventStore Gateway and Tenants; verify a provisional `index` routing constant before the shared executor. |
| Epic 3 / Story 3.1 | Advertise the write tool with AD-12's destructive annotation. |
| Stories 4.8 and 4.12 | Their order and ownership stay intact: the Tenants maintainer declares the final constant in 4.8, and the repository test AppHost arrives in 4.12. |
| PRD, architecture, UX | No change to product scope or architecture decision. No UX artifact is implicated. |

This changes acceptance criteria only. The planned work, MVP scope, and epic sequence remain viable. The existing sprint-status action items remain open until the stories are implemented and their gates pass.

## 3. Recommended Approach

Use a direct adjustment to Stories 1.1, 2.5, and 3.1. Planning effort is low; implementation effort for the structural seed and local spike is part of the already planned stories. The main risk is treating `index` as final before the Tenants maintainer verifies it, so Story 2.5 records it as a live-tested candidate and Story 4.8 retains the final decision. No rollback, new epic, or MVP reduction is indicated; no timeline change is established by this document edit.

## 4. Detailed Change Proposals

| Story | Before | After | Reason |
| --- | --- | --- | --- |
| 1.1, acceptance criteria | The solution build and fixture were named, while delivery configuration files had no story owner. | Require `Directory.Build.props`, `Directory.Packages.props`, `global.json`, `tests/Directory.Build.props`, `package.json`, `commitlint.config.mjs`, `.releaserc.json`, `tools/release-packages.json`, and thin `ci.yml`, `release.yml`, `commitlint.yml`; inspect their build, bootstrap, paired-release, and commitlint roles. | Later CI and release stories depend on this seed. |
| 2.5, query spike criteria | A throwaway Gateway harness was assumed to return a page using an already declared constant. | Start EventStore Gateway and Tenants locally through the existing EventStore AppHost before 4.12, call the pinned client directly, record setup and response evidence, and test candidate `index` against the Gateway pattern and live result for handoff to 4.8. | Removes the dependency on the future test AppHost and future Tenants decoration. |
| 3.1, tool annotations | `send_command` had `readOnlyHint: false` and `idempotentHint: false`. | Also require `destructiveHint: true`. | Matches AD-12 for the write tool. |

## 5. Implementation Handoff

**Scope:** Minor planning correction. The McpCli maintainer implements and verifies the Story 1.1 seed, Story 2.5 spike evidence, and Story 3.1 tool annotation. The Tenants maintainer confirms or corrects the `index` candidate in Story 4.8. Story 4.12 supplies the repeatable repository AppHost later.

**Success criteria:** The three story acceptance sections match the cited architecture, the Story 2.5 spike can produce a real page without the future AppHost, and later release and live-test stories can use the seeded files without inventing their ownership.

## Checklist Record

| Checklist items | Status | Finding |
| --- | --- | --- |
| 1.1–1.3 | Done | Readiness action items and source code identify the triggers and evidence. |
| 2.1–2.5 | Done | Existing epics remain viable; no new epic or resequencing is required. |
| 3.1–3.4 | Done | PRD and architecture already support the change; no UX or code artifact changes are requested. |
| 4.1–4.4 | Done | Direct adjustment selected; rollback and MVP review are unnecessary. |
| 5.1–5.5 | Done | Issue, impacts, edits, MVP effect, and handoff are recorded above. |
| 6.1–6.2, 6.5 | Done | The edited criteria and handoff were reviewed against the architecture. |
| 6.3 | Done | The user's direct amendment request authorized the document edits. |
| 6.4 | N/A | No epic or story was added, removed, or renumbered; sprint-status entries remain valid. |

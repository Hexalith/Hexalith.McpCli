---
title: '4.15 Publish the no-new-server rule'
type: 'chore'
created: '2026-10-28'
status: 'draft'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The published AI.Tools rule lacks a link to a versioned migration plan listing frozen implementations. Story 4.15 also lacks upstream integration, baseline-reference and synchronization evidence.

**Approach:** Add a versioned migration index in the owning AI.Tools repository, integrate its published baseline, and record provenance and synchronization evidence for the later paired-release gate.

## Boundaries & Constraints

**Always:** Retain Hexalith.McpCli ownership, decorated Contracts for gateway-ready operations, and separately approved generic contract/transport decisions for other classes. Existing proprietary surfaces receive only safety and continuity fixes; they are migration sources, never templates. Preserve inventory approval limitations, coordinated FrontComposer/Projects retirement and Memories' HTTP per-user identity prerequisite. Completion requires upstream main integration, its containing root baseline reference, byte-identical local entry points and passing synchronization. An open PR is insufficient; Abstractions-only bootstrap remains exempt.

**Never:** Edit reference contents, initialize nested submodules, change operation dispositions, invent owner approval, authorize retirement, alter production behavior, or implement paired publication in this story. External developer CLIs remain outside this policy.

## I/O & Edge-Case Matrix

| State | Required result |
| --- | --- |
| Published rule and plan, containing baseline reference, synchronized entry points | Record instruction-prerequisite completion; other release gates remain independent |
| Local candidate, open PR, or reference missing the integrated change | Keep story completion and paired-release readiness blocked |
| Any local entry point differs | Synchronization fails; reconcile all three before accepting evidence |
| Deferred operation or missing external owner approval | Retain compatibility surface and its existing authorization, behavior and release gates |

</frozen-after-approval>

## Code Map

- Owning `/home/administrator/projects/hexalith/aitools/hexalith-llm-instructions.md`: permits only same-folder topical links. Published main/current McpCli gitlink `3f194e17174994d308ec84af9ee2b5aa68674d0d` directly integrated the core rule; do not invent a merge commit or PR.
- Owning AI.Tools `README.md`: topical catalog. No tracked build/package/commitlint/editor configuration or workflows found. Clean local main is stale at `5bf12bbcec3d8a2016396c27439de9b5107f9e5d`; base implementation safely on published main.
- `_bmad-output/implementation-artifacts/*-migration-inventory-v1.md`: six version 1.0.0 inventories. Preserve session approval versus unasserted external owner approval. Parties has legacy MCP, no inventoried CLI. Frozen CLIs: Folders, Projects, ChatBot, FrontComposer, Memories; EventStore Admin needs its successor inventory.
- `scripts/check-agent-instructions-sync.sh`: existing byte-comparison gate, already passing for the three local entry points.
- `scripts/release-request.py`, `scripts/verify-release-source.py`: preserve paired-release refusal; Story 4.16 consumes this evidence.
- Previous Story 4.14 is done: retain upstream ownership, full revisions and separate local/published evidence.

## Tasks & Acceptance

**Execution:**
- [ ] Owning AI.Tools `hexalith-mcpcli-migration-instructions.md` — add version 1.0.0 index listing legacy servers, plug-ins, frozen CLIs, immutable inventories, approval limits and retirement prerequisites, including successor administration scope.
- [ ] Owning AI.Tools `hexalith-llm-instructions.md`, `README.md` — link the same-folder topic and explain retained compatibility implementations without weakening the existing rule.
- [ ] `references/Hexalith.AI.Tools` gitlink — integrate the qualified published revision; record integration and containment evidence.
- [ ] `README.md` — link the authoritative rule, migration plan and story evidence; distinguish this instruction prerequisite from later paired-release implementation.
- [ ] `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` — verify byte identity; if a change is necessary, edit AGENTS and copy it to both others.
- [ ] `_bmad-output/implementation-artifacts/evidence/story-4-15/` — retain upstream changes, full published revisions, gitlink containment, hashes and exact check results, including synchronization drift in temporary copies.
- [ ] This spec and `sprint-status.yaml` — record review, verification and actual completion state; do not close while upstream integration is outstanding.

**Acceptance Criteria:**
- Given a new module, when its author follows the baseline, then no new proprietary per-module MCP server, plug-in or CLI is created; decorated Contracts or an approved generic decision provide the path.
- Given a frozen implementation, when its author follows the versioned plan, then its inventory or successor gap and safety/continuity limit are identifiable without retirement approval.
- Given completion assessment, when evidence is checked, then upstream main contains the finished rule/plan, the root baseline contains that revision, and local entry points pass synchronization.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

No intent gaps remain. Shared upstream publication follows implementation and review. Footprint: documentation, one reference and evidence; no runtime API or package changes. Reuse inventories without duplicating operation tables. Investigation began on clean McpCli main `6103e9c8f91258c28b926a8e1b5c14f27ad19725`.

## Verification

- Run `bash scripts/check-agent-instructions-sync.sh` and `cmp`; temporary-copy drift must fail.
- Check topical/inventory links, policy clauses, approval limits and retirement dependencies against sources.
- Record published-main integration ancestry, root gitlink containment and hashes of policy, plan and entry points.
- Run `git diff --check` in each owner. No .NET/live rerun for documentation. Validate eventual commit messages with owning pinned commitlint before presenting or using them; never bypass tooling blockers.

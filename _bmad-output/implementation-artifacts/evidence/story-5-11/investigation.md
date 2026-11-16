# Story 5.11 planning investigation

Planning baseline: `008d95ccc77d932a372cb6c749d9d1fb1bc1ea57`, clean `main`, observed 2026-11-16. No product implementation or upstream edits were made during investigation. `epic-5-context.md` passed the workflow's freshness check. Story 5.9 is the latest lower-numbered completed story; its Code Map, tasks, Design Notes and Spec Change Log supplied continuity. Story 5.10 is context for a prerequisite, not a completed dependency.

## Authority and delivery

Use ordinary files from the permitted root AI.Tools submodule. Never load skills from `references/`. Its HEAD gitlink is `7ef8166ef87e1365f86d1a1b3aaf0235545177d4`. Current plan version 1.2.0 still indexes inventory revision `c694bff5a29073bee6848b88c142f7da23efcf85`. README.md:85 still cites plan 1.1.0 and says the Admin successor is outstanding.

The canonical [CiCd ownership contract](https://github.com/Hexalith/Hexalith.CiCd/blob/main/templates/partials/ownership-block.txt.j2), read through the GitHub connector on 2026-11-16, reserves workflows, `.github/hexalith-ci.json`, Dependabot, the Builds gitlink/section, delivered instruction blocks and required Claude denies. It does not list module release-note hooks or `.releaserc.json`. Preserve the owned files and all package publication checks. Preparation creates no GitHub release, messages, commit or push.

Story 5.10 has exact-byte approval and separate delivery authorization in `../story-5-10/{approval.json,delivery-authorization.json}`. Its `delivery-gate.json` records `python3 references/Hexalith.Builds/check.py` failing because `.github/hexalith-ci.json` is absent in clean McpCli HEAD. PS06/PS07/PS12/PS13/PS14 integration and inventory publication bindings remain absent. Do not infer completion from local approval. Configuration remediation belongs to CiCd, outside this story. Prepare independently; require actual prerequisite completion before the final plan/labels integration verdict.

Upstream patches must be based on current owner main and compose with prior delivered 5.8–5.10 changes. Root gitlinks are audit pins, not proof that the latest owner label changes are absent. Do not edit moving reference checkouts or advance their gitlinks, except the specifically required AI.Tools pointer after its merge is verified. Read each owning repository's guidance before implementation there. Keep temporary clones and build outputs beneath the private TMPDIR supplied by `run-with-temp`.

## Inventory index

`A` below means `_bmad-output/implementation-artifacts`; `S<n>` means `A/evidence/story-5-<n>`.

| Family | Version chain to retain in the index | Current evidence |
| --- | --- | --- |
| Parties | 1.0.0 → 1.1.0 → 1.2.0 | Historical bytes in `S3/approval/{1.0.0,1.1.0}/`; latest `A/parties-migration-inventory-v1.md`; `S3/approval/{approval.json,amendment-1.2.0.json}`. Latest owner approval grants no retirement authority. |
| EventStore Admin | 1.0.0 → 1.0.1 → 1.0.2 → proposed 1.0.3 | Earliest `S1/approval/1.0.0/`; `A/eventstore-admin-migration-inventory-v1.md` is 1.0.1; `…-v1.0.2.md` approved by `S7/approval.json`. |
| Technical tools | 1.0.0 → 1.0.1 → 1.0.2 → 1.0.3 → proposed 1.0.4 | History `S1/approval/{1.0.0,1.0.1}/`; `A/technical-tools-migration-inventory-v1.md` is 1.0.2; `…-v1.0.3.md` approved by `S7/approval.json`. |
| Folders | 1.0.0 → 1.1.0 | `A/folders-migration-inventory-v1{,.1.0}.md`, `S8/{approval.json,labels.json}`; PS10/PS11 delivered. K12 successor outstanding. |
| Projects | 1.0.0 → 2.0.0 → 2.1.0 | `A/projects-migration-inventory-v1.md`, `…-v2.md`, `…-v2.1.0.md`; 2.0.0 session authority and 2.1.0 owner authority remain distinct. `S9/{approval.json,delivery.json,labels.json}`. |
| FrontComposer | 1.0.0 → 1.1.0 | `A/frontcomposer-migration-inventory-v1{,.1.0}.md`; `S9` approval/delivery. Compiler remains exempt; host/Projects plug-in retirement remains coupled. |
| ChatBot | 1.0.0 → 1.1.0 | `A/chatbot-migration-inventory-v1{,.1.0}.md`; `S10` approval present, delivery blocked. |
| Memories | 1.0.0 → 1.1.0 | `A/memories-migration-inventory-v1{,.1.0}.md`; `S10`, including PS14's four modes. Approval present, delivery blocked. |

For every chain use actual files and receipt hashes, not an invented version reconstructed by editing current bytes. The final `inventory_revision` must be a published full McpCli commit containing the exact indexed bytes and approvals. Stage the publication sequence: reviewed inventory packet, authorized McpCli publication, owner label changes, new plan revision, containing AI.Tools gitlink and final evidence. Separate authorization must cover the actual prepared delivery footprint.

`S7` labels cover fourteen surfaces across seven owning repositories. Compose the newest registers from S8/S9/S10; do not restore historical README sections. New Admin/technical successors correct pending self-description with an effective-status pointer to their own receipt and a factual reference to the prior S7 approval. They stay candidates until approved. Technical citations must follow the current companion inventories, especially PS10/PS11 Folders 1.1.0. No disposition, source pin or gate relaxation is justified by these documentary corrections.

## Local contradictions and open gates

- `epics.md:206` MR1 requires a generic extension before retirement; `:211` MR6 requires an Admin contract. Align both, and Epic 6's application at `:302`, with the already adopted AD-23 outcomes. Do not alter the hash-bound AD-23 decision/map.
- Local PRD `prds/prd-mcpcli-2026-09-21/prd.md:434` retains the same non-gateway requirement; `:438` has obsolete coverage wording. Apply current disposition/shape/reporting policy without changing runtime behavior.
- Architecture spine `:191` still starts AD-21 with include/exclude-only terminology; `:359` says the baseline lacks the ownership rule. Reconcile current prose while retaining historical decisions and release evidence. The spine's Design Paradigm `:36` already adopts AD-23 and is the alignment authority.
- `A/deferred-work.md:143` is the original cross-artifact migration drift entry; `:952` assigns older root README claims to 5.11; `:1027` is the Parties restricted classification conflict; `:1035` MR1; `:1047` new Admin/technical self-description successors; `:1147` Folders re-citation. Locate by summary/source as lines will move.
- Parties remains `retirement-blocked` in `A/evidence/story-5-4-owner-approval/owner-approval.json`. `S5/sm3-status.json` binds G01–G06 and the existing “Labels + slip” decision. The first paired release was 2026-11-05; deadline 2027-02-05 is future at planning time. Record the actual completion date and outcome; do not claim a measured deadline miss prematurely.
- Parties' destructive classifications versus enrolled Commands require a separate exact-byte owner inventory/architecture resolution plus both-head exposure and direct/chained denial evidence with zero unauthorized effects. Existing approval/exposure is not changed by this documentation story. Mark the gate already tracked, never waived or compliant.
- Folders K12 and the 5.8 corrections at ledger `:1055–1164` belong to a separate K12 successor; 5.11 indexes the unresolved blocker. Projects Payload paging versus AD-20 remains tracked at `:1179`.
- At planning time 55 ledger entries have a `source_spec` naming `spec-5-*`, including 5.12. Re-enumerate at implementation. Audit every entry and the original drift row, preserving source heading, owner and current path anchors. “Already tracked” points to an existing gate; it is not closure. Acceptance/waiver requires an explicit owner decision. Do not append reconfirmations or attempt the independent runtime, census, redaction or publication repairs.

## Upstream active-topic map

All paths in the table are inside the owning repository; planning paths start at `_bmad-output/planning-artifacts/`. Anchor numbers describe the inspected root gitlink and must be refreshed for current-main patches. Only material active claims are in scope. Preserve archive PRDs, completed stories, review reports, inventories and generated API docs.

| Owner | Active paths and anchors | Required correction |
| --- | --- | --- |
| EventStore | `architecture.md:419,599`; `prd.md:105,426`; `ux-designs/ux-eventstore-2026-07-05/EXPERIENCE.md:57,402`; root `README.md:164–165` | AD-35 Admin transport promise becomes adopted confidential UI/withdrawal, with authorization/audit and UI proof retained. Update approved successor label citations. |
| FrontComposer | `prd.md:97,120,385,425,431`; `architecture.md:13`; `architecture/architecture-gov-1-2026-07-19/ARCHITECTURE-SPINE.md:40`; `ux-designs/ux-frontcomposer-2026-09-09/EXPERIENCE.md:18`; root `README.md:32–33` | Generated agent tools/resources are historical migration sources. Compiler `inspect`/`migrate` is retained K13 local tooling, not a future generic diagnostics migration. Preserve coupled host gate and FK01–FK04. |
| Memories | `prd.md:189,200,250,262–263,699,740–745`; `architecture.md:195,529–534,1463–1464`; `architecture/architecture-memories-2026-09-09/ARCHITECTURE-SPINE.md:65,346–347`; `ux-designs/ux-memories-2026-09-12/EXPERIENCE.md:27`; root `README.md:47–48,118–119,134–136` | Mark proprietary CLI/MCP phases and installation as retained compatibility. No promised generic migration/diagnostic surface; preserve HTTP per-user authority and PS14 exemption. Compose with completed 5.10 labels. |
| ChatBot | `architecture.md:389–393,582–584,1046–1047`; `architecture/architecture-chatbot-2026-09-14/ARCHITECTURE-SPINE.md:515–516`; `prds/prd-Hexalith.ChatBot-2026-05-28/prd.md:628,1152–1156`; `ux-designs/ux-Hexalith.ChatBot-2026-05-28/EXPERIENCE.md:29`; root `README.md:78–80,181–182` | FR82–86 already targets eligible shared heads; align older module-adapter target and human-delegated MCP decision wording with confidential-UI-only rules. Compose with 5.10 delivery. |
| Folders | `prd.md:238,433,944–945`; `architecture.md:551–552,615,764,770`; root `README.md:60–61` | Historical adapter topology and four-surface C13 scope cannot assert current public-agent eligibility. Explicitly retain K12 hold; do not rewrite adopted C13 or invent archive/removal authority. |
| Projects | `epics.md:1507–1545`; `prds/prd-Hexalith.Projects-2026-05-24/prd.md:111–112`; `architecture/architecture-projects-2026-07-15/ARCHITECTURE-SPINE.md:330,375`; root `README.md:7–8` | Add actual supported read/readiness/setup distinctions. Correct `epics.md:1519` tenant-from-credential claim to envelope selection plus independent Gateway authorization. Preserve publication, cutover and paging caveats. |
| Tenants | `architecture.md:344–345` | Correct compiler migration wording to retained K13 exemption. |
| Parties | Root `README.md:138,164,181–187,259–266`; architecture already targets McpCli | Mark separate host as compatibility and distinguish current package/discovery from historical local-candidate descriptions. Preserve UI requirements, owner tests and retirement block. |

Review root READMEs for seven technical-label owners even where active planning requires no other change. Parties has tests pinning documentation claims; inspect and adjust only meaningful owner documentation tests if affected.

Platform's FR15/AD-14 already require eligibility, confidential UI and denial of confirmation. Agents, Conversations, Timesheets and Works have consistent correction banners/future-scope qualifications. Builds has exempt developer tooling. Commons and PolymorphicSerializations have no relevant proprietary product target. Include these inspected roots with a no-change rationale in the final manifest rather than inventing patches.

For setup examples use the built CLI's actual `modules`, `operations`, `describe`, profile/query/command verbs and `hexalith mcp --transport stdio`; MCP exposes five generic tools, not one per operation. Offline Catalog discovery does not establish Gateway authorization, live availability or retirement. Identify package/current-candidate status explicitly. Never invent an alternative module endpoint, resource, plug-in or per-operation subcommand.

## Release notes and validation

Existing `.releaserc.json` composes the pinned release-notes generator and GitHub publisher; `.github/workflows/release.yml:132` invokes semantic-release. Add a module-owned generator wrapper that preserves conventional notes and appends committed `docs/release/migration-status.md`; test the installed pinned generator without publication. The status must enumerate PS01–PS14, distinguish exempt retained tools from pending migration binaries, carry removal gates and report evidenced retirements only. Do not change old releases or bypass source/staging/publication gates. Retain the post-2.0.1 output-contract publication restriction.

Verification should cover amended row accounting, authority/hash chains, exact-byte published plan/inventories, owner README integration, root AI.Tools containment and byte-identical entry points. Use existing S7/S8/S9/S10 semantics rather than creating parallel approval definitions. New verifier guards require negative cases that fail if removed and assert complete outputs; do not add tests that mirror documentation text without a policy boundary.

Independent work left open must remain visibly open in the final report. Story 5.11 does not close Epic 5 merely by drafting a plan or marking every deferral as already tracked.

## Implementation recheck (2026-11-16)

The spec has no frontmatter context list. Its Code Map was loaded as the context
index. `inputs.json` records 23 immutable versions across all eight families,
their full source revisions, hashes and distinct approval authorities, plus the
latest composed fourteen-label register. The original drift entry and 55 Epic 5
ledger entries are audited in `deferral-dispositions.{json,md}`. No new ledger
entry, acceptance or waiver is invented.

Upstream preparation uses each owner's locally observed `origin/main`, recorded
verbatim in `upstream/manifest.json`. Owner worktrees contain unrelated work;
FrontComposer and ChatBot HEAD differ from those refs. All worktrees and every
root reference remain untouched. The implementation workflow forbids remote
operations, so fresh authoritative remote-main verification/rebase is still a
delivery gate. Thirty patches span seven owner READMEs, their mapped active
planning topics, Tenants architecture, and the AI.Tools rule/plan. ChatBot and
Memories README patches are explicitly based on the separately approved Story
5.10 section; its delivery must finish first. No stale owner README is restored.

The 1.3.0 plan is a reviewable candidate with `inventory_revision: null` and
`status: candidate-not-publishable`, because no approved Story 5.11 publication
commit exists. Final bytes must contain the verified full commit and immutable
links, receive fresh final-plan approval, integrate to AI.Tools main and pass
containment/sync before the AI.Tools gitlink can move. `integration.json` names
each missing binding. The verifier cannot report completed integration now.

Source-head CLI restore independently fails NU1102: its existing Projects
Contracts pin `2.0.0-story66.3` is unavailable on nuget.org (nearest 1.2.4). No
dependency or source pin was changed. The published tool 2.0.1 was instead
installed into a private disposable workspace and verified offline: it discovers
Parties and Tenants, seven and fourteen operations respectively, and five generic
stdio tools. The supported Command verb is `send`; the prepared setup was
corrected after an intentionally retained unrecognized-`command` probe. This
proves released CLI syntax/discovery, not a current-source build or Gateway
authorization/readiness. No `query`, `send` or `tools/call` was executed.

Parties documentation fitness tests were inspected at the recorded owner main:
`DocumentationFitnessTests` pins SDK/project inventory, SDK routes/ACL wording
and external deployment ownership; `AppHostTenantsTopologyTests` pins direct
reference/tool onboarding. Those claims remain unchanged. No owner test was
edited, no source service started and no owner build or live gate is claimed.
The mandatory missing `.github/hexalith-ci.json` blocker and independent G01–G06,
Parties exposure conflict, Folders K12 and Projects paging remain open. SM-3 is
pending-not-met; its 2027-02-05 deadline is future on this assessment date.

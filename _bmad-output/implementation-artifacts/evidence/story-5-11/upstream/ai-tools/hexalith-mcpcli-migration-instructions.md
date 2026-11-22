---
plan_version: '1.3.0'
inventory_repository: 'https://github.com/Hexalith/Hexalith.McpCli'
inventory_revision: null
status: candidate-not-publishable
---

# Hexalith MCP and CLI migration plan

Version **1.3.0 candidate**, prepared by McpCli Story 5.11. This file is not the
authoritative plan until fresh exact-byte approval, verified Story 5.10 delivery, immutable
inventory publication and authoritative AI.Tools main integration are verified.
`inventory_revision: null` explicitly records the missing publication binding;
replace it with the verified full McpCli commit and render immutable `/blob/<sha>/`
links before approval of final plan bytes. Never publish this candidate as-is.

## Ownership and capability outcomes

McpCli owns one generic CLI and stdio MCP server for agent-eligible decorated
Gateway Commands and Queries. Do not add proprietary module MCP servers,
plug-ins or CLIs. Both heads are one public agent surface. Payload, task, actor,
delegation and confirm claims cannot elevate authority. Unsupported transports
fail safely; confidential human actions hand off to their owning UI.

Adopted AD-23 keeps Admin A1–A4 and module K12 confidential-UI-only, Admin
A5–A8 plus K07 documentation and K08 synthetic lifecycle withdrawn, K09
stream/file and K10 per-user HTTP deferred. Eligible K01–K06 need exact decorated
Contracts, handlers, admission and independent semantic proof. A business status
Query may observe effects; acceptance never establishes completion. These
outcomes need no invented Admin, resource, diagnostic or lifecycle transport.

External Aspire, Dapr and dotnet CLIs and Builds hexalith-module/hexalith-evidence
remain outside module-operation migration. K13 FrontComposer inspect/migrate and
K14 Memories MigrateEmbeddingVectors (--dry-run, --live, --rollback, --abort)
remain the named local exemptions adopted by plan 1.2.0. They stay supported
locally, never agent-facing, never counted retired, and keep their independent
freshness/path/hash/partial-write/privacy and custody/tenant/credential/consent/
no-write dry-run/denial/rollback/abort/audit obligations. No new CLI is exempt.

## Immutable inventory histories

The complete eight-family index below preserves every predecessor. Paths are
inside the McpCli inventory repository; hashes bind the prepared bytes. Final
publication must bind every path and its approval receipt to one full immutable
`inventory_revision`, never a moving branch. Earlier session-scope authority and
later owning-maintainer approval remain distinct. Receipt decisions determine
effective approval; an approved inventory never establishes delivery or retirement.

| Family | Version | McpCli path | SHA-256 | Authority / receipt |
| --- | --- | --- | --- | --- |
| parties | 1.0.0 | `_bmad-output/implementation-artifacts/evidence/story-5-3/approval/1.0.0/parties-migration-inventory-v1.md` | `c4db93be3422adff86568225d3dfed129b5c546bd4306c9ff3d0bbf0d0441a8f` | scope-approved-only; session-scope-only: `_bmad-output/implementation-artifacts/evidence/story-5-3/approval/1.0.0/parties-migration-inventory-v1.md` |
| parties | 1.1.0 | `_bmad-output/implementation-artifacts/evidence/story-5-3/approval/1.1.0/parties-migration-inventory-v1.md` | `8fc4078842d141151c521f0288f1eb7f9b984505c7b4a1458fa40de8dba4c51e` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-3/approval/1.1.0/approval.json` |
| parties | 1.2.0 | `_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md` | `2f359904fe87fab8325b6fc759676c1fc792a27e0857d47631d8eeec8b420a28` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-3/approval/amendment-1.2.0.json` |
| eventstore-admin | 1.0.0 | `_bmad-output/implementation-artifacts/evidence/story-5-1/approval/1.0.0/eventstore-admin-migration-inventory-v1.md` | `26ac7486cba8c52a0496147c6b90bda953dda31fd644ac199c433e49b834c90e` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json` |
| eventstore-admin | 1.0.1 | `_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md` | `7e1beb2fd2c030ca04dbc8d718c0324c7f7f5b66a077f6ef672312d6196fec18` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json` |
| eventstore-admin | 1.0.2 | `_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.0.2.md` | `ec388eae1b2c17cf1634f7b9b422b50124d2281bd0dfc445bfa11c9ad7a03cc2` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-7/approval.json` |
| eventstore-admin | 1.0.3 | `_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.0.3.md` | `6ddf91de9f48b52a5bfe1cae666c704a732c88334e9268a8dd528b64cfc8aa1c` | candidate-pending; pending: `_bmad-output/implementation-artifacts/evidence/story-5-11/approval.json` |
| technical-tools | 1.0.0 | `_bmad-output/implementation-artifacts/evidence/story-5-1/approval/1.0.0/technical-tools-migration-inventory-v1.md` | `6a7d325f6927b8b0f6692c05b71b54728bc1281b871dc073712586d172d41f58` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json` |
| technical-tools | 1.0.1 | `_bmad-output/implementation-artifacts/evidence/story-5-1/approval/1.0.1/technical-tools-migration-inventory-v1.md` | `0472f2c4ba12049c89e582ed5162279f989160d62b4499bc766efde8e85b93ca` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json` |
| technical-tools | 1.0.2 | `_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md` | `8cca31f2a9fb646566a2cdba3a377af58685d99e4a53ec8e9243135613c1a2f6` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-1/approval/approval.json` |
| technical-tools | 1.0.3 | `_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.0.3.md` | `7f2810174ae929e569d9affaccabe745565dcfe4f0487b71847806f3eda1ef8c` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-7/approval.json` |
| technical-tools | 1.0.4 | `_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.0.4.md` | `94985d72232864ab8f40ba212cd0fc73dbd0c5497856073cfd19c2972b89e8b8` | candidate-pending; pending: `_bmad-output/implementation-artifacts/evidence/story-5-11/approval.json` |
| folders | 1.0.0 | `_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md` | `57cf556b8051921bf2bf8a17abe3b82b7d0a3ba8ba5593072f52c12f85650e0b` | scope-approved-only; session-scope-only: `_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md` |
| folders | 1.1.0 | `_bmad-output/implementation-artifacts/folders-migration-inventory-v1.1.0.md` | `54a6f61d4f0d83876d8113c7c9d8775dc73190ecdbd8a3beb34cda10946d6407` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-8/approval.json` |
| projects | 1.0.0 | `_bmad-output/implementation-artifacts/projects-migration-inventory-v1.md` | `252af571ee3b52163a2f0637a1dff4f0c6f2802ebfa985c51562466fa759ad5f` | scope-approved-only; session-scope-only: `_bmad-output/implementation-artifacts/projects-migration-inventory-v1.md` |
| projects | 2.0.0 | `_bmad-output/implementation-artifacts/projects-migration-inventory-v2.md` | `011d1d444a9f32565f397cbbdca81962529d43920ac69b7508df4224ffbf24d4` | scope-approved-only; session-scope-only: `_bmad-output/implementation-artifacts/projects-migration-inventory-v2.md` |
| projects | 2.1.0 | `_bmad-output/implementation-artifacts/projects-migration-inventory-v2.1.0.md` | `c4667069ab37cc495fc49a07ae2fdececd75a8c0e9201f3e6cdf6b562aa7d1af` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-9/approval.json` |
| frontcomposer | 1.0.0 | `_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.md` | `cde0f43ae82376c37411017e88a3b692d0980622833310fecb29f040eb1281a9` | scope-approved-only; session-scope-only: `_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.md` |
| frontcomposer | 1.1.0 | `_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.1.0.md` | `60c44b5c7c67ca315bfe4f7582ea7e50526dc2cfeebbf12838f4b0c71543ff63` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-9/approval.json` |
| chatbot | 1.0.0 | `_bmad-output/implementation-artifacts/chatbot-migration-inventory-v1.md` | `3dccbe0fb56fe1facb05156d2648d0696d87dfd3a60fe25aacf4969b899ecd94` | scope-approved-only; session-scope-only: `_bmad-output/implementation-artifacts/chatbot-migration-inventory-v1.md` |
| chatbot | 1.1.0 | `_bmad-output/implementation-artifacts/chatbot-migration-inventory-v1.1.0.md` | `3d801aed7bd80a9a6f3ec225a694ed1aa9e9a9ce7fa263745d90184af5ced49c` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-10/approval.json` |
| memories | 1.0.0 | `_bmad-output/implementation-artifacts/memories-migration-inventory-v1.md` | `489af91ed49804172e8bd32f3efd98cf1d78fc8a109f23675c67b5ac23f19597` | scope-approved-only; session-scope-only: `_bmad-output/implementation-artifacts/memories-migration-inventory-v1.md` |
| memories | 1.1.0 | `_bmad-output/implementation-artifacts/memories-migration-inventory-v1.1.0.md` | `fc3baee0f766f95db32df5fd226825b144927c2ad1bc60f867341d32b517bca1` | owner-approved; owning-maintainer-receipt: `_bmad-output/implementation-artifacts/evidence/story-5-10/approval.json` |

## Ongoing change control

A source change that adds, removes or alters an inventoried tool, resource,
CLI operation or behavior variant, or a newly discovered surface, requires a
versioned inventory amendment and its owning-maintainer approval. Safety and
continuity fixes that leave those identities and behaviors unchanged do not.
Publish every change to this plan under a new `plan_version`. Move
`inventory_revision` whenever an indexed inventory is added or re-pinned.
Preserve every approved predecessor and its recorded approval limits.

## Independent delivery and removal gates

All PS01–PS14 remain present; no evidenced retirement is claimed. PS03/PS14 are
retained exemptions. The Admin/technical documentary successors have fresh
receipt-based status; Story 5.7 approval of their predecessors remains factual.
Story 5.10 records separate owner approval and delivery of ChatBot/Memories 1.1.0
and five labels. See its integrated register and the recorded owner commits.
No missing version, role, hash, gate, publication or upstream binding permits a
success claim. Preserve the proprietary-surface census and independent release gates.

Parties retirement remains blocked by G01–G06 and the separate restricted/
destructive classification versus existing exposure conflict. Parties and McpCli
owners must approve the exact successor and both-head exposure/direct/chained
denial evidence with zero unauthorized effects; this plan changes no exposure.
Folders owners retain the K12 restricted/mixed-operation successor and C13 hold.
Projects owners retain Payload paging versus AD-20, publication/live acceptance
and 6.7 cutover gates. FrontComposer host and Projects plug-in retire together
only after FK01–FK04 and every host consumer are accounted for. Memories needs
forwarded per-user HTTP authority plus tenant/user/administrative authorization,
semantic, release and rollback proof. ChatBot retains governed workflow,
approval, identity, authorization and behavior gates; human decisions stay UI.
Admin retains G1–G6, confidential UI coverage and G4 route/scope/token/URL fixes,
audit and persisted-effect evidence. AM01's backup backend remains deferred.

Every operation and variant retains replace, withdraw or defer, rationale,
security class, exact replacement or gap, and explicit owning-role approval.
Include requires replace; exclude requires approved withdraw or defer and never
means deletion. Inventory is migration documentation, never runtime exposure
configuration. Uninventoried decorated Operations and version differences are
reported; duplicate/stale vectors and uncovered Operation Shapes fail. Retire
only after the owner-approved disposition and selected-environment authorization,
behavior, conformance, release and rollback evidence pass independently.

The owner chose “Labels + slip”; SM-3 is pending-not-met with deadline 2027-02-05,
three months after first paired release 2.0.1 on 2026-11-05. Assessment 2026-11-22:
deadline future, no measured miss. Reassess at completion; the product owner
records a reason if no Legacy Server is deleted by the deadline. Every Epic 5
deferral retains its sourced owner/gate; already tracked is never acceptance.

## Integration and release prerequisite

Publish approved inventory bytes first under an explicitly authorized McpCli
commit; verify published bytes and all approval roles. Deliver rebased owner
README/active-topic patches with separate authorization and mandatory owner
commitlint and applicable Builds checks. McpCli has adopted CiCd and its
committed .github/hexalith-ci.json requires the shared pre-push check.
Bind final plan bytes and full inventory revision, integrate into
authoritative AI.Tools main, verify main containment, then change only McpCli's
AI.Tools gitlink and pass byte-identical local instruction synchronization.
Open PRs, local candidates and missing upstream integrations leave completion
blocked. Dependency, census, enrollment, loopback, live, package and post-2.0.1
output-contract publication gates remain independent. No release, binary removal,
operation execution, package publication or ecosystem completion is authorized.

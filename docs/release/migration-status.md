## MCP and CLI migration status

This release is a gateway-only increment: one `hexalith` CLI and a stdio MCP
server with five generic tools submit eligible decorated Commands and Queries.
Offline discovery establishes neither Gateway authorization nor live readiness.
Confidential UI operations, MCP resources/prompts, streams, proprietary plug-ins
and executor retries are outside this increment. No ecosystem completion or
legacy retirement is evidenced by this release status.

As assessed on 2026-11-16, **no PS01–PS14 surface has an evidenced retirement**.
The [approved inventory and delivery chain](https://github.com/Hexalith/Hexalith.McpCli/blob/main/_bmad-output/implementation-artifacts/evidence/story-5-11/inputs.json)
distinguishes inventory authority from delivery. The authoritative AI.Tools plan
remains 1.2.0; the prepared 1.3.0 reconciliation is pending fresh exact-byte
approval, Story 5.10 delivery, inventory publication and upstream integration.

| ID | Remaining binary or surface | State and removal gate |
| --- | --- | --- |
| PS01 | `Hexalith.EventStore.Admin.Cli` / `eventstore-admin` | Retained compatibility. Admin G1–G6, confidential UI coverage and authorization/effect proof; G4 route/scope, token and URL safety fixes remain. No new Admin transport is required by adopted AD-23. |
| PS02 | `Hexalith.EventStore.Admin.Mcp` | Retained compatibility, same independent Admin gates as PS01. |
| PS03 | `Hexalith.FrontComposer.Cli` / `frontcomposer` | Retained K13 local compiler exemption (`inspect`, `migrate`); never counted retired. Preserve freshness, path/hash, partial-write and privacy obligations. |
| PS04 | `Hexalith.FrontComposer.Mcp` | Retained host. G4 couples removal to the Projects plug-in after FK01–FK04 and every host consumer are accounted for. |
| PS05 | `Hexalith.Parties.Mcp` / `parties-mcp` | Retirement blocked by G01–G06 and the separate destructive-classification/exposure conflict. An approved inventory and enrolled operations do not close either gate. |
| PS06 | `Hexalith.Memories.Cli` / `memories` | Retained compatibility. Memories inventory gates; forwarded per-user HTTP identity is necessary but insufficient. Tenant/user/administrative authorization, semantics, release and rollback proof remain. |
| PS07 | `Hexalith.Memories.Mcp` / `memories-mcp` | Retained compatibility, same independent Memories gates as PS06. |
| PS08 | `Hexalith.Projects.Cli` | Retained compatibility. Projects inventory, publication/cutover, authorization and behavior gates; Payload paging conflict with AD-20 remains. |
| PS09 | `Hexalith.Projects.Mcp` | Retained plug-in. G4 couples removal to the FrontComposer host; Projects gates remain independent. |
| PS10 | `Hexalith.Folders.Cli` / `folders` | Retained compatibility. Folders 1.1.0 inventory gates and separate K12 restricted/mixed-operation successor; no blanket public-agent eligibility. |
| PS11 | `Hexalith.Folders.Mcp` / `folders-mcp` | Retained compatibility, same independent Folders gates as PS10. |
| PS12 | `Hexalith.ChatBot.Cli` | Retained compatibility. ChatBot 1.1.0 inventory and label delivery, governed workflow, identity, approval, authorization and behavior gates. Confidential human decisions stay in the UI. |
| PS13 | `Hexalith.ChatBot.Mcp` | Retained compatibility, same independent ChatBot gates as PS12. |
| PS14 | Memories `tools/MigrateEmbeddingVectors` | Retained K14 owner-held local exemption: `--dry-run`, `--live`, `--rollback`, `--abort`. T01–T04 inventory does not establish independent custody/tenant/credential, consent, no-write, denial, rollback/abort or audit proof. Never counted retired. |

The owner selected **“Labels + slip”** for Parties; SM-3 remains pending, not
met, with deadline **2027-02-05** (three months after the first paired release,
2.0.1 on 2026-11-05). That deadline is future at this assessment. Reassess it at
completion; record the product owner's reason if no Legacy Server is deleted by
the deadline. This status waives no removal gate. The independent restriction on
publication after 2.0.1 until the Epic 3 output-contract item is resolved remains.

# Owner documentation follow-up

These patches address the 22 November review against locally observed owner
`origin/main` revisions. The approved packet and its delivery receipts record
the earlier work. This follow-up awaits owner approval and integration.

ChatBot's PRD, epics and experience spine direct association decisions, AI-action
approval and approved execution to the confidential UI. Both generic McpCli
heads refuse those actions. Both use the existing `cli-automation-client` class
with the profile's Gateway credential and session actor. The Gateway authorizes
the credential, tenant and operation. The session actor provides attribution.
The issuer sets credential expiry, and the stdio session ends with the process.
`mcp-human-delegated-client` is withdrawn for M1. The patch updates FR83 and
NFR67 in the active requirements and synchronizes the adjacent FR82 and FR84
epics summaries with the delivered PRD. The FR82 coverage line also limits
parity to the approved agent-eligible set. The Epic 5 overview at
`epics.md:632-636` and its acceptance criteria remain under the course-correction
banner at `epics.md:30`. Related legacy guidance remains in the worker-only
exposure criterion at `epics.md:1609`, Story 7.11 at `epics.md:4479` and the typed
MCP tool criterion at `epics.md:5686`. Line references use the listed ChatBot
base revision.

Works' design and experience spine describe future access through enrolled and
authorized Works Contracts on the shared McpCli heads. The mockup points readers
to the published `hexalith describe` syntax and identifies who retains the
original CLI request.

The other edits remove provisional headings and banners from delivered
guidance. FrontComposer and Tenants cite the approved AI.Tools migration plan
without a version number. Projects ties tool discovery to enrollment of
Projects.Contracts 2.0.0 in a published McpCli release. The approved PS03 and
PS14 labels retain their citations to plan 1.2.0, which adopted the exemptions.

Each patch applied with `git apply --whitespace=error` in a disposable Git
repository containing the listed revision’s target files. The resulting files
matched the prepared bytes, including the original line endings.

| Patch | Owner main revision | Files | Patch SHA-256 |
| --- | --- | ---: | --- |
| [ChatBot](chatbot.patch) | `794753deb77b636f59f0f94e64ad4fbccdbf13da` | 6 | `5db5edb74a3c7790075df6789e59d85b6c3bbbe6de010911d278565dbc4776c8` |
| [EventStore](eventstore.patch) | `7a42a0f01cfc6cafe6aa2d3e5ef05cbc370b22cb` | 4 | `0d1173c15a08ce6cb9d0d671e83db9a1009c1f86c700ce5fa2fb8be7fc55e90d` |
| [Folders](folders.patch) | `20b7a0a82d1056030088e7e94cadcc2d416d4f73` | 3 | `14f81f29ce1b47e5dee36e3c4e19bdf52002d0b5070d35c72cdaf426a1099da2` |
| [FrontComposer](frontcomposer.patch) | `ac145de3bfe5aaf1614cecf0feed7c7b732847ee` | 5 | `11ca64e06997822e639aeaf0564b2cfa350c6f3565a905887f4f54d753630d45` |
| [Memories](memories.patch) | `1f68406be7a61064044963139941c9ba2c117947` | 5 | `3ae9261858501b510d3b1e842ff00612c091c5a83d3968119d718cc75a52e276` |
| [Parties](parties.patch) | `c2af56d09ae5c638775dfb18066db2db91473286` | 1 | `d065b2f7fbba3789edd262bdb67ebf47451ee574877e9eaad05ca0cd8f5d3f2e` |
| [Projects](projects.patch) | `4d740a889787bb095b16303ed749ec7f165e5683` | 3 | `816e13ab12c636738ba9a3a27e7da409a104706d9aee4ffb2c68bdc717ccf1f5` |
| [Tenants](tenants.patch) | `ce3aadd8f2f7c96c67544d4bdc422f6e923a69d0` | 1 | `894dca079bcb7d7e74c5e26d54d92ce34c082a9d3fe2ee3bd19e701cae9827f1` |
| [Works](works.patch) | `8b78dd916fbafc6b27bfba4bd59ff89b4c0b04f0` | 3 | `a5e9ea4e244ff2d62cdb45c954c67740d8ec496e96b5261f8ccad82cee534f4e` |

## Active flow audit

The follow-up inspection covered `DESIGN.md`, `EXPERIENCE.md` and `epics.md`
under each original no-change owner’s `_bmad-output/planning-artifacts`.

| Owner | Observed main revision | Result |
| --- | --- | --- |
| Agents | `74379fa9a4a0227858cc9cf6d585b3cdd8afc53a` | Established guidance qualifies future shared-head access. The design and flows add no module-specific machine adapter. |
| Builds | `a6abb7908ec38dcb3fbd99d69e7ed29ae25794d2` | No matching flow or epic documents. The developer-tooling exemption applies. |
| Commons | `0a1d70723b2d112690aa06e6e6a207459cfa2e0f` | No matching flow or epic documents. |
| Conversations | `a41f660380e8ff55301460a9a471cb52ef49e614` | Established guidance qualifies future shared-head access. The experience, design and epics add no module-specific machine adapter. |
| Platform | `e416dfac2a6660efd0720fa1d278f8cda3fb329d` | Epics refer to McpCli composition, release and qualification under the platform boundary. |
| PolymorphicSerializations | `538fe092340a7a6266128463c4cfd008aad6ebd5` | No matching flow or epic documents. |
| Timesheets | `cc09d6383290e0b717de0bc53cd4c19ef1360ae3` | Established guidance qualifies future shared-head access. The experience, design and epics add no module-specific machine adapter. |
| Works | `e6e4d1928c09bbde2f8f05c6a6a0211ddce89035` | The experience and design still described typed MCP tools and resources. See the Works patch. |

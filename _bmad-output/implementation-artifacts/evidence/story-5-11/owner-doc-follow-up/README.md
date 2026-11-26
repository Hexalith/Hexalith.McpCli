# Owner documentation follow-up

These patches address the 22 November review against locally observed owner
`origin/main` revisions. The approved packet and its delivery receipts record
the earlier work. This follow-up awaits owner approval and integration.

ChatBot’s PRD and experience spine now direct association decisions, AI-action
approval and approved execution to the confidential UI. Both generic McpCli
heads refuse those actions. The CLI guidance describes configured Gateway
credentials and enrollment. The parity checks cover eligible operations. Works’
design and experience spine describe future access through enrolled and
authorized Works Contracts on the shared McpCli heads. The other edits remove
provisional headings from delivered guidance.

Each patch applied with `git apply --whitespace=error` in a disposable Git
repository containing the listed revision’s target files. The resulting files
matched the prepared bytes, including the original line endings.

| Patch | Owner main revision | Files | Patch SHA-256 |
| --- | --- | ---: | --- |
| [ChatBot](chatbot.patch) | `794753deb77b636f59f0f94e64ad4fbccdbf13da` | 5 | `756ae9c8948ab7b2d2e75a8730f950aec6bcebb32bccb47c94c8e4bb79fd542f` |
| [EventStore](eventstore.patch) | `7a42a0f01cfc6cafe6aa2d3e5ef05cbc370b22cb` | 4 | `0d1173c15a08ce6cb9d0d671e83db9a1009c1f86c700ce5fa2fb8be7fc55e90d` |
| [Folders](folders.patch) | `20b7a0a82d1056030088e7e94cadcc2d416d4f73` | 3 | `14f81f29ce1b47e5dee36e3c4e19bdf52002d0b5070d35c72cdaf426a1099da2` |
| [FrontComposer](frontcomposer.patch) | `ac145de3bfe5aaf1614cecf0feed7c7b732847ee` | 5 | `39082d5c73b8d3561fc001427fc5ad30f149909548570e6b1e558e3cdc60c6a1` |
| [Memories](memories.patch) | `1f68406be7a61064044963139941c9ba2c117947` | 5 | `29bf572381be14e1146926680359d997326ef8fcd25ebe961a231015fa231e94` |
| [Parties](parties.patch) | `c2af56d09ae5c638775dfb18066db2db91473286` | 1 | `d065b2f7fbba3789edd262bdb67ebf47451ee574877e9eaad05ca0cd8f5d3f2e` |
| [Projects](projects.patch) | `4d740a889787bb095b16303ed749ec7f165e5683` | 3 | `816e13ab12c636738ba9a3a27e7da409a104706d9aee4ffb2c68bdc717ccf1f5` |
| [Tenants](tenants.patch) | `ce3aadd8f2f7c96c67544d4bdc422f6e923a69d0` | 1 | `894dca079bcb7d7e74c5e26d54d92ce34c082a9d3fe2ee3bd19e701cae9827f1` |
| [Works](works.patch) | `8b78dd916fbafc6b27bfba4bd59ff89b4c0b04f0` | 3 | `66e2bef6c589c4c6c86eaea04244c0a20d293d6b72b6cc249768db288c6d1e3f` |

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

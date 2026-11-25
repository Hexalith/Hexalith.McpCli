# Owner documentation follow-up

These patches address the 22 November review against locally observed owner
`origin/main` revisions. The approved packet and its delivery receipts record
the earlier work. This follow-up awaits owner approval and integration.

ChatBot’s PRD and experience spine now direct association decisions, AI-action
approval and approved execution to the confidential UI. Both generic McpCli
heads refuse those actions. Works’ design and experience spine describe future
access through enrolled and authorized Works Contracts on the shared McpCli
heads. The other edits remove provisional headings from delivered guidance.

Each patch applied with `git apply --whitespace=error` in a disposable Git
repository containing the listed revision’s target files. The resulting files
matched the prepared bytes, including the original line endings.

| Patch | Owner main revision | Files |
| --- | --- | ---: |
| [ChatBot](chatbot.patch) | `794753deb77b636f59f0f94e64ad4fbccdbf13da` | 5 |
| [EventStore](eventstore.patch) | `9d24e05d81d04329f17a4f31e74da60f128f4a7e` | 4 |
| [Folders](folders.patch) | `2499dd3a63c6aa14bead7062a58d7d092e658f02` | 3 |
| [FrontComposer](frontcomposer.patch) | `78337195930bc6ffc849c4389dd233e37085a945` | 5 |
| [Memories](memories.patch) | `1f68406be7a61064044963139941c9ba2c117947` | 5 |
| [Parties](parties.patch) | `c2af56d09ae5c638775dfb18066db2db91473286` | 1 |
| [Projects](projects.patch) | `29a2adc9a7def4fd339ea9f986a87d5df9aeb7e2` | 3 |
| [Tenants](tenants.patch) | `ce3aadd8f2f7c96c67544d4bdc422f6e923a69d0` | 1 |
| [Works](works.patch) | `e6e4d1928c09bbde2f8f05c6a6a0211ddce89035` | 3 |

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

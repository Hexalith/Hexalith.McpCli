---
title: 'Explain profile, query and MCP inputs at the point of use'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent">

## Intent

Resolve five deferred operator guidance entries. A user reading CLI help should be able to update profile fields and remove profiles, choose valid query identifiers and paging, find the supported environment fallback for each global option, and choose the available MCP transport. The README should tell MCP clients how to distinguish a discovery input error from an unknown catalog name.

</frozen-after-approval>

## Implementation Notes

- Selected ledger entries from Stories 1.7 (HTTP transport), 2.3 (profile input), 2.8 (query arguments), 2.10 (global options), and 3.1 (MCP failures). The starting revision was `30ffe86dc9c918f676a9a5f0cf0e460c34cbe5c4`.
- Use the rules already enforced by `ProfileStore`, `SettingsResolver`, `RoutingResolver`, and `OperationExecutor` for the help descriptions in `CliRunner` and `GlobalOptionsBinding`. Verify the rendered help through the CLI. Check the two MCP error paths against the transport and protocol tests.
- A smoke test of the Release CLI reproduced the gaps across six help pages before the change. After the change, it verified the rendered help and exercised profile creation and field edits, empty and invalid values, removal of active and inactive profiles, and the stderr/exit-2 HTTP refusal in a temporary profile store.
- All 12 MCP discovery protocol cases passed, including the assertions for missing, blank and unknown names. The same test runs against both supported MCP protocol versions.

- Release build passed with zero warnings. The CLI suite passed 624 tests, with two Windows-only cases skipped on Linux. All 94 MCP tests passed. After review, both focused help tests and the six-page smoke test passed again.

## Review Triage Log

| Finding | Resolution |
| --- | --- |
| URL help implied that a token is required. | Medium, fixed. The same-source instruction now applies when a token is supplied. |
| Profile creation help left the required URL source unclear. | Medium, fixed. The add command explicitly requires the URL flag and describes the stored flags. |
| Global profile help also appeared on commands that ignore the selector. | Low, fixed. The selector help explains that profile management uses its own arguments. Set and remove identify the positional target. |
| Inherited format and output options appeared in MCP help. | Low, fixed. MCP help describes its explicit table and output-file refusals. |
| A profile name can begin with a hyphen and be mistaken for an option. | Low, fixed. Add help and the README explain the option terminator. Adding and removing `-dev` after `--` both succeeded in the built CLI. |
| A swapped environment variable could pass a help test. | Low, fixed. The test pairs each variable with its option in the rendered help. |

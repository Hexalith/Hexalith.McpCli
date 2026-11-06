# Story 5.1 planning evidence

> **Superseded working notes.** The
> [EventStore Admin inventory](../../../eventstore-admin-migration-inventory-v1.md),
> the [technical-tools inventory](../../../technical-tools-migration-inventory-v1.md)
> and [verification.md](../verification.md) take precedence wherever they
> differ from these files. The classifications and source anchors below and in
> the JSON findings are unverified planning notes; for example, the inventories
> classify `snapshot set-policy` as a destructive overwrite (AC20).

These are unapproved source-investigation findings for the draft story spec,
recorded on 2026-11-06 at McpCli
`ad7bf9ee415d09b16b47616740e2cc38fb3d6d9a`. They are review inputs, not
finalized inventories, owning-maintainer decisions, live parity or retirement
permission. No legacy command, migration or live service was executed.

- [Admin CLI](admin-cli-source-findings.json): 31 registered operations: 21 remote,
  seven local and three unavailable backup stubs. Six unregistered backup helper
  classes are recorded separately.
- [Admin MCP](admin-mcp-source-findings.json): 28 tools: 18 diagnostic/read tools,
  seven caller-confirmed writes and three process-local context tools. Zero
  registered resources, prompts or lifecycle subscriptions.
- [Technical investigation](technical-source-findings.md): current FrontComposer
  compiler/resource/lifecycle behavior, 13 documentation resources, manifest
  consumers and packaging distinctions.
- [Root census](root-source-census.json): full revisions and tracked surface
  projects for all 17 declared references. Thirteen retained production surfaces
  occur in seven repositories. Builds' two tooling projects are explicitly exempt;
  nine roots have no matching production Cli/Mcp project. This bounded census
  asserts no completeness for remote repositories or uninspected dynamic hosts.

All proposed rows remain `defer / exclude`, with approval pending. Existing
module inventories keep their historical pins and authority limits. Only Platform
has a discovered CODEOWNERS entry; owning roles elsewhere are not named sign-offs.

Parent checks matched the complete CLI registration graph to all 31 unique row
identities and MCP attributes to all 28 unique tool names. Each inspected reference
was clean at its recorded full revision. FrontComposer MCP and ordinary corpus
metadata are unchanged from the old inventory pin; six CLI files changed for
path safety. Source data describes client intent separately from server behavior:
both Admin clients request a root stream-list GET while the current controller
registers `GetRecentlyActiveStreams` (controller line 350). No successful stream
listing is inferred from the tool/command name.

Remaining implementation work is to turn these findings into the two reviewed,
versioned inventories, retain a reproducible completeness/row validator, collect
actual owner decisions and perform the build workflow review. Approval of the
spec does not supply a missing owner signature.

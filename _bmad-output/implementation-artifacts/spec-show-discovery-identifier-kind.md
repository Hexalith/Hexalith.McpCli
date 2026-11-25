---
title: 'Show the module Identifier Kind in operation descriptions'
type: 'feature'
created: '2026-12-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close the Story 2.8 discovery deferral. Given any cataloged operation, its CLI and MCP descriptions report the Module’s declared `envelope.identifierKind` as `ulid` or `string`, including when the caller supplies the aggregate ID without a Payload mapping. The user approved the additive field on 2026-12-21.

</frozen-after-approval>

## Implementation Notes

Use the Catalog’s Module declaration and existing result enum serialization. Make the property part of the shared description, the closed MCP output schema and PRD addendum §G.

Review added the aggregate syntax explanation to the advertised schema, a third-value rejection, and an actual String-kind operation without a mapped aggregate property to the parity test. Both protocol revisions passed the CLI and MCP discovery comparison and the 16 schema tests passed. The Release build and earlier exact CLI and Core document tests passed.

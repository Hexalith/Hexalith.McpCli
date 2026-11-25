---
title: 'Close the next seven actionable deferred-work items'
type: 'bugfix'
created: '2026-11-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Complete the next seven actionable deferred-work findings by recorded severity and ledger order. Verify each change, close its original entry, and commit it separately. Record skipped entries with their blockers or superseding evidence. Run the full Release build and tests before pushing directly to main.

</frozen-after-approval>

## Implementation Notes

- The current ledger and previous batch dispositions determine order. Prior approvals govern historical evidence, owner-held inventories and upstream changes.
- Candidate work is confined to existing checks and their regression tests. The explicit push request supplies the delivery approval.
- Focused tests covered flattened runtime dependencies, the actual reader's first-build input checks, directory-anchored scans, census globs and imports, command continuation parsing, and CLI output replacements.
- The census follows committed MSBuild parent imports and reports when the first matching file lies outside the readable trees. The current Commons and PolymorphicSerializations pins reach that boundary.
- The skipped findings and their owners or prerequisites are in the deferred-work ledger.

## Review Triage Log

- Medium, patched. Workflow matrix expansion uses the declared workflow default shell.
- Medium, patched. A literal Windows runner establishes the PowerShell default when a step supplies no shell.
- Medium, patched. Step metadata is read at the step's indentation, so script content cannot change its shell.
- Low, patched. The Dockerfile scanner reads the leading directive block for the continuation marker.
- Medium, patched. Escaped whitespace does not start a shell comment.
- Medium, patched. Literal Docker and tool commands in other YAML command fields retain coverage.
- Low, patched. The scanner uses search-only ancestor handles where the platform provides them.
- Medium, patched. An in-packet receipt is bound to the original directory descriptor and a replaced packet path fails publication.
- Medium, patched. Present RID-only files must have a matching declaration in the executable metadata as well as the restore.
- Medium, patched. Windows long paths use extended syntax for metadata handles.
- Medium, patched. A verified Unix character device keeps its ordinary write behavior while FIFO opens and writes remain nonblocking.

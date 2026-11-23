---
title: 'Close five CLI result output deferrals'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** CLI result delivery can stall on a FIFO, misclassify a character device, or discard command recovery identifiers. Existing-file permission coverage excludes privileged runs, and the planning rule on absent fields conflicts with the explicit CLI profile selection state.

**Approach:** Use native destination types for direct writes, fail promptly if a FIFO has no reader, preserve accepted command identifiers on output failure, run the existing-file permission assertion under either privilege level, and document the selection-state exception.

</frozen-after-approval>

## Implementation Notes

- Native target inspection selects direct writes. FIFO output uses a nonblocking native write because FileStream waits for readiness when a pipe fills.
- An accepted command with a failed result write returns the message ID in the error message and the submitted correlation ID in the existing structured member.
- Existing-file permission coverage runs under either privilege level. The new-file parent assertion applies to unprivileged runs.
- The addendum and epics now describe the explicit empty active selection.

## Review Triage Log

- Medium, deferred. Another process can replace an inspected device or regular file before open. This race predates the change and also affects the regular-file path.
- Medium, patched. The README specifies that FIFO reader availability and capacity are checked during the write.
- Medium, patched. The result-write failure test compares distinct accepted and submitted IDs observed at the Gateway boundary.
- Medium, patched. A connected FIFO with an idle reader now has a bounded regression test for backpressure.
- Medium, patched. A separate fixture creates a seekable character device outside `/dev` on Linux when device creation is available.

## Verification

- Pinned Hexalith.Builds commitlint 21.2.4 validated the full commit message with zero errors and warnings.
- The final focused CLI Release build passed with warnings treated as errors.
- Nine selected CLI regressions passed, covering FIFO writes, proc-fd output, accepted command identifiers and existing-file preflight. The separate device-node fixture needs `CAP_MKNOD`, and the privileged permission branch was not exercised by the unprivileged local run.

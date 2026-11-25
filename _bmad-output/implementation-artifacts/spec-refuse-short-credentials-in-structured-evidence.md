---
title: 'Refuse short credential environments for structured evidence'
type: 'bugfix'
created: '2026-12-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close Story 5.4 R54-D9 using the approved fail-closed behavior. Given a nonblank known environment credential shorter than eight characters, structured evidence producers and the scanner refuse to proceed. The refusal does not include a variable name or a value. Diagnostic logs still redact short values. With a valid environment, preserve the existing packet and receipt contracts.

</frozen-after-approval>

## Implementation Notes

Use one guard with the existing credential selection. Check the actual inherited or explicit environment before creating receipts or starting receipt-producing children.

Review added checks for the standalone vector lane and runtime evidence copy, and kept refusal text in the diagnostic redactor. The focused scan, redaction, process and topology checks passed for all 50 cases. The topology entry-point tests use the topology suite’s existing dependencies.

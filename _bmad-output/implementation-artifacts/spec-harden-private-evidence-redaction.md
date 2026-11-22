---
title: 'Redact private settings in malformed evidence'
type: 'bugfix'
created: '2026-11-22'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent">

## Intent

Close deferred work R54-D1, D2, D3, D4 and D6. The shared redactor and evidence scanner must recognize unfinished escaped JSON private values, entity-encoded XML selectors, XML attributes containing quoted `>`, and private command arguments passed with whitespace or embedded escaped quotes.

Given a synthetic credential in one of these forms, when a consumer sanitizes or scans the evidence, then redaction covers the complete credential and the scanner flags the original. Given sanitized evidence or safe surrounding diagnostics, a subsequent pass preserves those bytes and JSON wrappers remain readable.

</frozen-after-approval>

## Implementation Notes

- The shared redactor handles escaped private JSON and malformed XML. It processes structured and textual private arguments before live diagnostics join argv for display.
- The ledger records the five resolutions after the original entries to preserve the historical Story 5.4 review rows and their line references.
- Synthetic regressions exercise redactor output, scanner findings, idempotence, enclosing JSON, and live command console, failure, and receipt output.

## Review Triage Log

| Finding | Verdict and evidence |
| --- | --- |
| Escaped JSON quote parity | Medium, patched. A regression verifies that a private value ending in a literal backslash preserves the next JSON field. |
| Escaped JSON Unicode key and container support | Medium, patched. Regressions cover escaped private keys and nested containers across two escape layers. |
| Adjacent argv at the input boundary | Medium, patched. Regressions cover both a missing final quote and a missing array delimiter. |
| Escaped spaces and shell word segments | Medium, patched. Regressions cover the full word and preserve the following argument. |
| Argument spans across protected JSON | Medium, patched. A regression verifies redaction of both a nested diagnostic and the following standalone private argument. |
| XML closing tags inside CDATA and comments | Medium, patched. Regressions verify that closing-tag text inside either construct stays part of the private body. |
| Multiword argv in live log output | Medium, patched. A subprocess regression checks the start message, failure message, and command receipt. |

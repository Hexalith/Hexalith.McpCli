---
title: 'Redact malformed quoted evidence and verify scanner receipts'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent">

## Intent

Close Story 5.4 deferrals R54-D7, D8, D10, D11 and D12 in the shared evidence pipeline.

- Given a malformed quoted diagnostic containing a recognizable credential, sanitizing it hides the credential and scanning the original flags it. Safe quoted diagnostics retain their original bytes.
- Given many quoted strings containing angle brackets, the redactor locates the first raw XML fragment in a single forward scan and still redacts its private content.
- Given a clean file with a credential in its name, the scanner returns exit 1 and identifies the finding by its redacted path in both stdout and the receipt.
- Given a receipt destination whose parent is a regular file, the scanner returns exit 2, emits its documented diagnostic on stderr and leaves stdout empty.
- The paired-publication verifier uses the shared redactor through its active call sites. Remove its three unused wrappers.

</frozen-after-approval>

## Implementation Notes

- The shared redactor checks malformed tokens as literal text and as JSON with lenient escape handling. It preserves the source spelling when the two readings agree on redaction. When they disagree, it masks the whole token and retains the surrounding diagnostic.
- The XML search skips each protected quoted span in order. The scanner tests exercise the CLI with synthetic credentials and check the serialized receipt and both output streams.
- Only the verifier's three unused wrappers and their imports were removed. The historical publication test referenced by the original ledger entry was already absent from this revision.
- All 34 evidence redactor and scanner tests passed. With 128 and 1,024 angle-bracket records the previous implementation's profiled call count grew by a factor of 38.03. The new implementation grew by a factor of 7.99 for the same eightfold increase.

## Review Triage Log

| Finding | Verdict and resolution |
| --- | --- |
| Re-encoding a malformed diagnostic can emit a lone surrogate that fails a UTF-8 write. | Medium, fixed. A regression encodes the result as UTF-8 and checks that the original escaped surrogate survives redaction. |
| Re-encoding can reinterpret Windows path separators as tabs or newlines. | Medium, fixed. A regression checks the exact bytes of a path next to a redacted credential. Ambiguous escaped credentials cause the whole token to be masked. |
| Correct output alone cannot detect a return to quadratic scanning. | Medium, fixed. A deterministic call-count regression distinguishes the old and new implementations without depending on wall time. |
| The scanner's malformed JWT case lacked a no-echo assertion. | Low, fixed. The CLI test now checks JWT, Bearer and PEM canaries across stdout, stderr and the saved receipt. |

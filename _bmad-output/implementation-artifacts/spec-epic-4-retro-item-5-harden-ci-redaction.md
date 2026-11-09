---
title: 'Protect retained evidence with shared redaction and a secret scan'
type: 'bugfix'
created: '2026-11-09'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Implement the separate prerequisite requested for Story 5.4, starting with
`epic-4-retro-item-5-harden-ci-redaction` and the existing planning entry at
`deferred-work.md:834`. Consolidate Python redaction helpers and cover opaque
Bearer credentials, truncated PEM private keys and malformed XML private-key
elements in direct, escaped and retained child output, including cancellation.

Add a repository-owned evidence secret scanner with deterministic findings, a
failing exit code for secrets, and a receipt binding the scanned bytes and scanner
implementation. Preserve diagnostic structure and useful nonsecret output.
Update the existing tracking rows without duplicates. Verify the prerequisite
and keep Story 5.4's live CI acceptance, final evidence and owner verdict pending.
The user's follow-up authorizes committing and pushing all repository changes,
including their pre-existing Story 5.4 local revalidation note.

</frozen-after-approval>

## Implementation Notes

- This is a bounded tooling prerequisite with no unresolved intent decisions or
  data migration. The requested push is authorized. Production source, dependencies,
  approved vectors, reference checkouts and live execution remain outside this change.
- Consolidate in `scripts/evidence_redaction.py`; adapt `tools/live-topology/ci.py`,
  `live_plans.py`, `scripts/verify-paired-publication.py` and
  `scripts/verify-release-source.py`. Preserve raw duplicate JSON fields and safe
  operator bytes, named-key container redaction and XML entity handling. Fixture
  repositories must copy the shared helper too.
- Add `scripts/scan-evidence-secrets.py` and regression tests in the existing
  script test lane. Scan the complete selected directory without suffix filtering;
  reject links, unreadable files, unsupported encodings/binary files and empty
  packets. Findings identify files and rules without quoting secrets. Receipts
  contain sorted per-file SHA-256 hashes, a manifest digest and implementation hashes.
- Run the release-script suite and complete non-live topology Python sweep, then
  an independent review and a clean scan of this prerequisite's verification packet.
  Reconcile the three historical redactor deferrals, the existing Story 5.4
  prerequisite row, retro item 5 and sprint status in place.
- Implementation keeps thin compatibility adapters at the existing helper names.
  Child-process redaction uses the actual child environment on success, failure
  and interruption; both console output and retained command/error documents
  follow the same policy. Supported preexisting markers and empty private XML
  preserve exact bytes. Short known credentials are retained in the policy and
  replacement is simultaneous so overlapping values do not corrupt markers.
- Scanner exits are 0 (clean), 1 (sensitive content), and 2 (incomplete scan or
  receipt failure). All inputs are hashed, including files refused as nontext.
  Non-whitespace C0 controls, DEL and supported binary/archive signatures are
  refused; no filename suffix or hidden-file exclusion bypasses scanning.

## Review Triage Log

Independent blind review produced nine actionable findings. All were reproduced
or confirmed against their callers, and patched within the prerequisite; none
was deferred.

| Finding | Verdict and evidence | Disposition |
|---|---|---|
| XML after a quoted log prefix bypassed private-element matching | High: fragment detection used the first string token, allowing private contents to remain in a scanner-clean file | Patch: recognize XML fragments outside JSON strings regardless of earlier log tokens; direct/escaped regression matrix |
| Unfinished private XML attribute values survived | High: fallback required a closing quote | Patch: redact private attribute content through end-of-input; both quote styles and nested JSON covered |
| Only the first XML name/key selector was inspected | High: a safe name before a private key selector hid the value | Patch: inspect every selector, matching parsed XML policy |
| Quoted named private arguments survived | High: unquoted-only matching left credentials with spaces untouched | Patch: whole quoted assignments and truncated forms; preserve surrounding JSON |
| Known credentials shorter than eight characters were dropped | High: consolidation weakened live Core diagnostics and yielded clean scans | Patch: include every nonblank known value; protect existing markers and overlapping replacements. A final regression also ensures known values cannot obscure credential syntax before it is recognized, through direct and three escaped JSON levels |
| One XML rewrite could expose another entity-encoded known secret | High: early return skipped replacement of decoded attribute content | Patch: decode and redact each attribute/text span before return; mixed private-element/known-secret regression |
| Selfclosing private XML consumed safe siblings | Medium: unnecessary redaction removed useful diagnostics and failed clean scans | Patch: preserve empty/selfclosing private elements and following content byte-for-byte |
| Some nontext controls and archive formats scanned clean | Medium: a completeness claim was made for unsupported evidence | Patch: reject C0/DEL controls and ar/thin/tar signatures; scanner exit/receipt regressions |
| Child-only environment secrets survived bounded capture | High: capture used ambient credentials instead of the child's environment | Patch: pass the child environment through console, channel, command-receipt and exception redaction; real success/failure/cancellation regression |

## Verification

- Release/script suite: 193 tests passed; complete non-live topology suite: 207
  passed. Final focused redactor, child-environment, CI and Core diagnostics:
  17 passed. Tests exercised real retained process output and cancellation.
- The independent reviewer reproduced the nine findings, rechecked their exact
  reproducers after patches and confirmed all nine resolved. The final syntax
  overlap case is covered by the focused redactor tests and the complete script
  suite. No new deferred-work entry was needed.
- Exact command summaries, source hashes and local raw-log hashes are recorded in
  `evidence/epic-4-retro-item-5/verification.json`; the compact packet's
  `secret-scan.json` is generated by the committed scanner. Commitlint validated
  the exact full message with zero warnings/problems. `git diff --check` passed.
- Story 5.4 remains in-progress. Its dedicated live CI run, final evidence packet
  scan, source/artifact bindings and exact-byte owner approval/verdict remain pending.

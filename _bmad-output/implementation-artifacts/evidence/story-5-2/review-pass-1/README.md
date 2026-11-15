# Story 5.2 review pass 1 — 2026-11-15

The final parent verification passes **64 verifier process tests** and **eight
runner process controls**. The corrected [57-guard sweep](guard-removal-corrected/results.json)
reports **57 killed, zero survivors and zero errors**, requiring assertion
failures with no unittest/process errors. Its receipt binds the executed frozen
inputs. [Parent verification](parent-verification/checks.json) records the exact
commands and channel hashes; [preservation](parent-verification/preservation.json)
confirms the approved artifacts, receipt and frozen intent are unchanged, with
an empty forbidden-path diff and clean whitespace. The adopted stdout remains
byte-identical. Three independent review layers completed; all ten findings
were fixed and no new work was deferred. The spec is done and sprint story is review.

The raw unittest captures include generated trailing whitespace. The narrow
`.gitattributes` entries preserve their exact bytes and JSON receipts, while
ordinary source and document whitespace checks remain enabled.

All six requested patches are implemented. The initial 64-test run and sweep
are retained below as historical captures. A later correction adds missing
record IDs to the failure diagnostic, restores restricted-record fixtures in
`finally`, and compares raw adopted stdout/stderr bytes. The corrected runner
separates assertion failures from unittest errors, preserves timeout output and
a final receipt, and derives hashes and mutations from its frozen template.

Current focused results are in [runner-correction](runner-correction/): the
three directly affected class-map process tests and all eight runner controls
pass. Controls cover a real assertion kill, survivor, unittest error, mixed
failure/error, incomplete zero exit, mutant and baseline timeouts, and a live
input change after the snapshot. They assert the runner's exit status and
receipt classifications. The final parent suite and corrected sweep above
supersede these focused results; the original sweep is historical.

[The final control transcript](runner-correction/runner-controls-final.stderr.txt)
records all eight passing controls. The first control run is retained too: its
incomplete-process fixture used `sys.exit`, which unittest catches as an error.
That fixture now uses a direct process exit to exercise an actually incomplete
suite; the final run covers the corrected case.

Every rejection asserts exit 1, empty stdout and the exact complete `FAIL: …`
stderr line. Added cases exercise policy-side outcome and transport refusal,
policy-agreed restricted records with and without classes, source-version
agreement, unique policy binding, map/approval path binding, invalid receipt
decisions and the other previously uncovered diagnostics. Non-object JSON
items now stay in the FAIL channel. The explicit-record set check precedes
generic missing-row validation and names missing/extra record identities;
the accepted input set is unchanged.

The verification document labels and corrects the approval-time 625/472 claim:
the bound partition is **525 identities = 372 classified + 153 records**. It
labels old local/pending-merge paragraphs as checkpoint history and states the
final approved AI.Tools push and main merge. The unbound spine now applies
AD-23 in its Design Paradigm and FR-21/FR-22 trace.

## Reproduce the behavioral checks

Run from the repository root. `run-with-temp` supplies private scratch space;
fixtures clean up after their processes finish. Save fresh outputs at a new
task-owned path because the mutation runner refuses an existing output folder.

```bash
run-with-temp python3 -I -B -m unittest discover -v -s _bmad-output/implementation-artifacts/evidence/story-5-2 -p 'test_*.py'
run-with-temp python3 -I -B _bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py
run-with-temp python3 -I -B _bmad-output/implementation-artifacts/evidence/story-5-2/review-pass-1/test_run_guard_removal.py -v
review_result_parent=$(mktemp -d -p evidence story-5-2-guard-removal.XXXXXX)
run-with-temp python3 -I -B _bmad-output/implementation-artifacts/evidence/story-5-2/review-pass-1/run_guard_removal.py --output "$review_result_parent/results" --jobs 4
```

The fresh output example creates a new task-owned result parent and passes an
unused child directory to the runner. It preserves the retained captures.

[The original mutation results](guard-removal/results.json) reported 57 kills
against their recorded script/test hashes. They predate corrected error
accounting and fixtures, so they are historical, not a current kill claim.
Their baseline, expressions, process results and transcripts are unchanged.

The corrected runner executes only `test_verify_class_map.py`, whose complete
process suite is the supported mutation target. It records assertion failures
and errors separately. A kill requires a completed suite with an assertion
failure, exit 1, and no unittest/process error. An error, timeout or incomplete
suite yields an error outcome and final exit 1; a survivor also yields exit 1.
Both mutant and baseline timeouts retain partial raw channels and a receipt.
The runner copies only the packet and source inputs into private repositories,
hashes that frozen template before execution, and derives mutant text from it.
It replaces one complete `require(...)` expression with `pass`, waits for all
workers and removes the copies. This checks removal of require statements, not every possible
mutation of each condition or arbitrary program changes.

## Historical initial verification and preservation

[checks.json](checks.json) retains the initial commands, exit codes and output hashes
for the verifier, 64-test suite, whitespace check, forbidden-path diff and
historical-baseline comparison. [verifier.stdout.txt](verifier.stdout.txt) is
byte-identical to the original capture; [tests.stderr.txt](tests.stderr.txt)
records the initial passing suite. Those script/test hashes predate the runner
correction. The initial current-run forbidden-path diff is
empty. Git's existing missing commit-graph warnings remain in stderr.

The current-run start was clean
`28bcbbb898b6530838a7872f2ba450c34e56cc70`. The spec's historical baseline
`f4bb819925d4fac5fa5afd262341692296a52042` is retained. Its whole-tree diff
includes previously published work, so it is captured separately and is not
treated as changes made by this patch. No intervening work was reverted.

The checks also confirm all ten receipt-bound decision/map/inventory hashes,
the unchanged approval receipt and the byte-identical frozen spec block.
Production, root tests, dependencies, CI, tools, references, census and all
inventory files are unchanged in this run. This initial checkpoint preceded
the parent workflow's independent review and completion step.

[secret-scan.json](secret-scan.json) is also the historical initial packet scan;
the final [secret scan](parent-verification/final-secret-scan.json) binds the
retained text evidence snapshot. The [scan scope](parent-verification/scan-scope.json)
records the exclusion of pre-existing generated Python caches, which were left
untouched in the workspace. Existing
Story 5.2 scan receipts remain historical captures of their original bytes.
The approval receipt and approved decision/map are preserved. Parties
reconciliation, Folders staging, later enrollment and retirement gates remain
open under their existing owners; this patch supplies no new authority.

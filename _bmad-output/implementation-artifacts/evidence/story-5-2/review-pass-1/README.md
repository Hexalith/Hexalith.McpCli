# Story 5.2 review pass 1 — 2026-11-15

The [code-review pass-2 patch evidence](../review-pass-2/README.md) records the
current 70-test suite and six sub-condition mutation checks. The 64-test parent
results below are retained pass-1 checkpoints. The dated scope and frozen-hash
corrections below qualify their preservation claims without changing receipts.

The retained pass-1 parent verification passes **64 verifier process tests** and **eight
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

## Dated scope correction (2026-11-15, code review pass 2)

The story-labeled commit `28bcbbb898b6530838a7872f2ba450c34e56cc70`
also carried the following nine **non-story gitlink moves**. These are part of
that commit, rather than unrelated changes that predated the story. AC3's
requirement that `references/` stay unchanged **does not hold for `28bcbbb`**.
The owner chose **“Keep pins, align apart”** on 2026-11-15: these published
revisions stay on `main`. Builds workflow/dependency-policy alignment and
census reconciliation belong to a separate `build(deps)` change under the
repository's Builds-move procedure, outside Story 5.2. They are not a story
ledger deferral, and this correction makes no CI-success claim.

| Gitlink | Before `28bcbbb` | In `28bcbbb` |
| --- | --- | --- |
| `references/Hexalith.Builds` | `99f7c86072ca7b35e3fbbaee4606a559a847805a` | `73e60af8a1fcdf3f06726d5d1b6e1199cce778ee` |
| `references/Hexalith.EventStore` | `5c5c0cce54541f18ec4f290f085d8678d517e8f8` | `fdb59895975e86a1e234325a01237f259cdbd53b` |
| `references/Hexalith.Folders` | `6ac670743c94f7819bb80f0914801cdbf84ceb3f` | `bb990a8766a9feac42ff7ecf02c8b7ca42a7ba15` |
| `references/Hexalith.FrontComposer` | `bfc8f8ae74e3ff0baa2d1d4abf083b0b47e6dca3` | `09e5dd0fce32df9653365759d955e1e78df74ed7` |
| `references/Hexalith.Memories` | `2c2e9b58990638ededf22e8e67ff5c12de75b434` | `66e2441e2536fc37708aca2bd3456fd4cd21a439` |
| `references/Hexalith.Parties` | `53844114ffcedc5af96fbf1cb15e126adaae02a9` | `e59aed9ca2d111b0195afe078611e2184b6de4c5` |
| `references/Hexalith.Platform` | `9a1cf867b931d93451a2e2cf5749b1b444f7bb7a` | `f6f85032598865b9123f16364448bfd02c0ff5b0` |
| `references/Hexalith.Projects` | `b756d01aef5a53ad7f52f0d3a8bc76a1d03d441b` | `fc58cefde69d72d7d3daa574b5022f73f830a85e` |
| `references/Hexalith.Tenants` | `30b9b61845e35052187c86968880c79d8e76cd2b` | `2ec938397c5b330cf1e694e8cc442cb4ad022f2b` |

The retained review-pass-1 receipts are unchanged. Their empty forbidden-path
checks cover only `28bcbbb..5f35a70`; every “unchanged in this run” statement
for that packet is limited to the follow-up ending at `5f35a70`. Those checks
do not establish AC3 for `28bcbbb` or erase the nine moves above. The current
pass-2 patch starts at `32a3e65989136f28b34500a4d9db8f04cf601885` and preserves
those pins, all inventory bytes, the approved decision/map and owner receipt.

## Frozen-block hash clarification (2026-11-15)

The retained `parent-verification/preservation.json` value
`02f0011d5007094c3101452a56ef3f580fc1739535ad1083bc4144116b0beea3`
hashes 5,838 bytes **after** the literal `<frozen-after-approval` token and
**before** `</frozen-after-approval>`; it includes the opening tag's remaining
attributes and `>` but neither delimiter token. It used this extraction:

```python
data.split(b"<frozen-after-approval", 1)[1].split(b"</frozen-after-approval>", 1)[0]
```

The tag-inclusive block uses the following extraction, with no trailing newline
beyond the closing tag:

```python
re.search(rb"<frozen-after-approval\b.*?</frozen-after-approval>", data, re.S).group()
```

Those **5,884 bytes** hash to
`8adb4def1bffac05e6a601412216854fb11a0ea19eb865e3d1a1f5c2b52a521b`,
matching `preservation-checks.json`. Both extractions were independently checked
at `80a7857`, `28bcbbb`, `5f35a70` and the current run start; each yields its
same respective hash. The frozen intent did not change. The retained receipt
is left untouched; this note supplies its previously missing extraction scope.

## Reproduce the behavioral checks

Run these portable Bash/Python 3.9 or later steps from the repository root
(`Path.is_relative_to` requires Python 3.9). They create a private `TMPDIR`
(also `TMP`/`TEMP`) and remove it after all child work exits. The retained
result parent is created with `TMPDIR`, `TMP` and `TEMP` unset, using system
temporary storage outside the caller's disposable `TMPDIR` and the repository;
it remains available for inspection after scratch cleanup. The mutation runner
receives an unused child directory because it refuses existing output folders.
On the recording workstation, the untracked
`~/.local/bin/run-with-temp` helper supplies equivalent scratch isolation.

```bash
review_result_parent=$(env -u TMPDIR -u TMP -u TEMP mktemp -d)
(
    set -e
    review_scratch=$(mktemp -d)
    trap 'rm -rf -- "$review_scratch"' EXIT
    export TMPDIR="$review_scratch" TMP="$review_scratch" TEMP="$review_scratch"
    python3 -I -B -m unittest discover -v -s _bmad-output/implementation-artifacts/evidence/story-5-2 -p 'test_*.py'
    python3 -I -B _bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py
    python3 -I -B _bmad-output/implementation-artifacts/evidence/story-5-2/review-pass-1/test_run_guard_removal.py -v
    python3 -I -B _bmad-output/implementation-artifacts/evidence/story-5-2/review-pass-1/run_guard_removal.py --output "$review_result_parent/results" --jobs 4
)
```

The real artifact reads explicitly use UTF-8 under Python's isolated `-I`
mode. The actual-packet success test runs the verbatim map/decision/receipt
copies without re-serialization or hash rebinding, and compares raw stdout
against the retained adopted bytes. These steps preserve all retained captures.

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
includes the nine non-story moves carried by `28bcbbb`, detailed in the
dated correction above, as well as other published work. It is captured
separately. No intervening work was reverted.

The checks also confirm all ten receipt-bound decision/map/inventory hashes,
the unchanged approval receipt and the byte-identical frozen spec block.
Production, root tests, dependencies, CI, tools, references, census and all
inventory files are unchanged only in the pass-1 follow-up ending at
`5f35a70`. This initial checkpoint preceded
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

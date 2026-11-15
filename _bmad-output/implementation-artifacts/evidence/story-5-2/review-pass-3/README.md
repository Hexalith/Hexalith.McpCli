# Story 5.2 code review pass 3 patches — 2026-11-15

This packet applies the five patch findings from code review pass 3, which are recorded in the
[spec](../../../spec-5-2-decide-generic-non-gateway-capability-contracts.md#review-findings).
The approved AD-23 decision and class map, the approval receipt, all eight bound inventories,
the verifier and its adopted stdout are byte-for-byte unchanged. This patch began at
`55f8a02435c7faa7c4073bf22c78a5d04c466929` (`fix: close story 5.2 capability review findings`).

## Checks

[`record_checks.py`](record_checks.py) produced [`checks/checks.json`](checks/checks.json).
It takes one exact-byte snapshot of the 14 verifier inputs and records each command with its
full channels and SHA-256s. The receipt also binds the recorder's own hash.

- **Verifier.** The standalone verifier exits 0 with empty stderr. Its stdout is
  byte-identical to the adopted capture.
- **Tests and controls.** All **74 verifier process tests** pass (70 plus 4 new), and so do
  the **eight runner controls**.
- **Mutants.** Four focused sub-condition mutants each **survive the prior 70-test suite**
  at `55f8a02` and are **killed by the current suite**. Each kill is a completed assertion
  failure, with no test error:

  | Mutant | Change to `verify_class_map.py` | Killing case |
  | --- | --- | --- |
  | `approval-limit-nonblank` | drop `nonblank(expected.get("approvalLimit")) and` | `test_agreed_approval_limit_must_be_nonblank` |
  | `map-owned-restriction-evidence` | replace `restrictions.setdefault(row_id, evidence)` with `pass` | `test_map_owned_restriction_evidence_alone_blocks_admission` |
  | `fail-channel-keyerror` | remove `KeyError` from the `FAIL:` exception tuple | `test_missing_member_uses_fail_channel` |
  | `fail-channel-typeerror` | remove `TypeError` from the `FAIL:` exception tuple | `test_wrong_member_type_uses_fail_channel` |

- **Sweep.** A fresh whole-guard sweep with the corrected runner (`checks/guard-sweep/`)
  kills **57 of 57** guards, with zero survivors and zero errors. Its `results.json` sits
  next to all 116 raw channels.

## Other patches

- **Line endings.** `.gitattributes` marks the following `-text`, so that a
  `core.autocrlf=true` checkout (the Git for Windows default) cannot rewrite hash-bound bytes:
  - `evidence/story-5-2/**`;
  - the AD-23 decision and class map;
  - the eight bound v1 inventories.

  Raw channels in this packet keep the whitespace exemptions that review-pass-1 uses. No
  file bytes changed.
- **Spine wording.** The spine's AD-23 Provenance now says only that the adoption and merge
  changed no census baseline or gitlink bytes. It also names `28bcbbb`'s nine later gitlink
  moves, which the owner kept on `main`.
- **Runner docstring.** The docstring of `review-pass-1/run_guard_removal.py` now calls
  `run-with-temp` a workstation-only helper and points to the portable recipe. Earlier
  receipts keep the earlier runner hash. This sweep binds the current runner hash.
- **Secret scans.** The shared scanner (`scripts/scan-evidence-secrets.py`) produced two
  receipts, both clean:
  - [`secret-scan-review-pass-2.json`](secret-scan-review-pass-2.json) covers the pass-2
    packet;
  - [`secret-scan.json`](secret-scan.json) covers this packet and excludes its own receipt.

Prior packets and receipts are unchanged and keep their checkpoint status.

## Reproduce

These steps need Bash and Python 3.9 or later, and are run from the repository root.

```bash
review_result_parent=$(env -u TMPDIR -u TMP -u TEMP mktemp -d)
(
    set -e
    review_scratch=$(mktemp -d)
    trap 'rm -rf -- "$review_scratch"' EXIT
    export TMPDIR="$review_scratch" TMP="$review_scratch" TEMP="$review_scratch"
    python3 -I -B _bmad-output/implementation-artifacts/evidence/story-5-2/review-pass-3/record_checks.py \
        --output-dir "$review_result_parent/checks" --prior-ref 55f8a02
)
```

The command exits 0 only when every check above holds. Its output stays outside the
repository.

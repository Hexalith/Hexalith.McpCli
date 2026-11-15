# Story 5.2 code review pass 2 implementation — 2026-11-15

All seven direct patches are applied. [Checks](checks.json) retain the exact
commands, process channels and SHA-256s: **70 verifier process tests** and
**eight runner controls** pass. The standalone verifier exits 0 with empty
stderr and stdout byte-identical to the adopted capture. Its implementation
is unchanged; the new cases strengthen the suite around existing policy.

[Six focused mutation checks](subcondition-mutations.json) independently break
the previously uncovered sub-conditions. Each new test kills its corresponding
mutation through a completed assertion failure, without a unittest error:

| New process case | Deliberate mutant rejected by the case |
| --- | --- |
| `test_restricted_row_cannot_take_decision_agreed_deferral` | Add continued deferral to the restricted outcome set; map and decision agree on the row's deferred class |
| `test_record_kind_must_match_decision` | Omit kind from the record-policy comparison |
| `test_rebound_inventory_hash_must_still_match_decision` | Drop the decision's source-hash conjunct while map, receipt and source are rebound |
| `test_rebound_inventory_version_must_still_match_decision` | Drop the decision's source-version conjunct while map, receipt and source are rebound |
| `test_duplicate_decision_policy_members_are_rejected_by_process` | Parse the decision policy with plain `json.loads` |
| `test_duplicate_receipt_members_are_rejected_by_process` | Parse the approval receipt with plain `json.loads` |

Each damaged-input process case asserts exit 1, empty stdout and the exact full
`FAIL:` stderr line. The mutation record binds one exact-byte source snapshot,
the old/new expressions, command, mutant hash and complete failure channels.
The retained [parent verification checkpoint](parent-verification.json)
independently reruns all 70 tests and eight controls. Its earlier 57-guard
receipt reports zero survivors/errors, but its named raw channels were removed
with scratch and are not independently inspectable from that checkpoint.
The current [complete sweep evidence](guard-sweep-complete.json) reruns the
existing runner and retains its matching receipt and all **116 raw UTF-8
channels**, keyed by the receipt's filenames. Every channel round-trips to its
original bytes and matches its receipt SHA-256; the receipt's exact UTF-8 bytes
and hash are embedded too. The new sweep kills **57 of 57 guards**, with zero
survivors and zero errors. The runner and approved artifacts are unchanged.
The six focused checks target sub-conditions that whole-guard removal cannot
distinguish. Prior receipts remain unchanged and retain checkpoint status.

The actual-packet success test now executes verbatim copied artifacts without
calling `save()`, and all real artifact text reads specify UTF-8. The two
identified subtest loops restore state in `finally`. Portable reproduction
steps in the [pass-1 README](../review-pass-1/README.md#reproduce-the-behavioral-checks)
use private disposable scratch space and place retained results outside the
repository. The spine preserves the original 2026-09-27 approval date and names
the 2026-11-12 AD-23 amendment separately.

The dated corrections in the [pass-1 README](../review-pass-1/README.md#dated-scope-correction-2026-11-15-code-review-pass-2)
and [verification document](../verification.md#dated-scope-correction-2026-11-15-code-review-pass-2)
list all nine non-story gitlink moves carried by story-labeled `28bcbbb`,
explicitly state that AC3 does not hold for that commit, and retain the owner's
choice to keep the pins on main. Builds alignment is a separate `build(deps)`
change, outside this story. Historical “unchanged in this run” claims are
limited to `28bcbbb..5f35a70`. The README also explains both frozen-block hash
extractions while preserving the original receipt.

No prior capture, receipt, approved decision/map, inventory, reference, census,
production source, root test, dependency or CI file was changed. This patch
began at `32a3e65989136f28b34500a4d9db8f04cf601885`. The original frontmatter
baseline and frozen spec block remain unchanged. The parent checkpoint
confirms all ten approved artifact hashes, the unchanged approval receipt and
tag-inclusive frozen-block hash. Its path-limited diff and plain working-tree
whitespace check are historical checks, rather than proof of the complete
candidate's scope or whitespace.

The [candidate scope and whitespace checkpoint](candidate-scope-and-whitespace.json)
checks the complete changed-file set against the explicit allowed paths,
relative to `32a3e65989136f28b34500a4d9db8f04cf601885`. It combines tracked
working-tree changes, the staged snapshot and all non-ignored untracked
additions; an unexpected path anywhere, including a root dependency file,
fails. Whitespace checks cover both tracked snapshots relative to that baseline
and each untracked addition as a complete new file. The receipt itself is
included in the final file set and whitespace checks, with its own hash omitted
to avoid a self-referential digest. Prior receipts are preserved byte for byte.
Three independent workflow review layers completed. All five surviving evidence
and reproduction findings are resolved; no new work is deferred. The spec is
done and sprint story is review. [Final parent checks](final-verification.json)
cover the completed candidate, its retained channels, matrix scenarios,
preservation, whitespace and pinned commitlint validation. Existing Parties,
Folders and retirement gates remain open under their recorded owners; the
separate Builds alignment is outside this story.

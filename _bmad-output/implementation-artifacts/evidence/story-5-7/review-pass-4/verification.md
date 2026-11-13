# Story 5.7 review pass 4 verification

All six accepted patch groups from code review pass 4 are implemented. The
approved successor inventories, the owner receipt and the label register are
unchanged, and all eleven receipt artifact hashes still match. Discovery and
direct execution each pass all **49 tests** and leave the packet cache-free.

## Correction to pass 3: 11 of 18 guard controls were supported

The pass-3 [runner](../review-pass-3/run_guard_controls.py) compiled each mutant
into a copy of the module globals (`dict(original.__globals__)`). The tests inject
their fixtures with `patch.object(L, 'read_json' | 'git' | 'checked_file', …)`,
and the copied namespace never saw those patches. The seven `L.verify` mutants
therefore read the real integrated register and real Git and failed their target
tests at unrelated assertions, even with nothing removed:

- the three `deliveryAuthorization` fields;
- the label `file`, `sha256` and `gate` bindings;
- the before-section binding.

The rule `bool(result.failures) and not result.errors` counted those failures as
detections. The pass-3 claim of **18/18 detected** was therefore supported for
only **11**. The tests themselves were sound: rebuilt against the live globals,
all seven controls fail exactly their intended assertion. The pass-3 runner and
its receipts are kept unchanged as historical records.

## Corrected guard controls: 26 of 26 detected

[run_guard_controls.py](run_guard_controls.py) rebuilds each mutated function as
`types.FunctionType(<function code>, original.__globals__, …)`, so every mutant
sees the tests' patches. Each control runs its target test twice through the same
mechanism:

1. **Baseline.** The function is rebuilt unchanged, and the test must pass.
2. **Removed.** The guard is removed, and the test must fail with no errors. The
   operands of a failing `assertEqual` must contain that guard's diagnostic.

The runner searches the recorded operands, not the traceback text, because
unittest truncates long reprs and `pprint` wraps long strings across diff lines.
An identity control removes nothing and must report `detected: false`.

The [output](guard-controls.stdout.txt) is summarized below.

| Check | Result |
| --- | --- |
| Pass-3 controls detected with live globals | 18 of 18 |
| Pass-4 guards detected | 8 of 8 |
| Total | 26 of 26 |
| Identity control | `detected: false` |
| Pass-3 mechanism, nothing removed | the seven `L.verify` targets still fail (`pass3MechanismIdentity`) and the identity target fails too, leaving the 11 supported controls (`pass3SupportedByPass3Receipt`) |

## Accepted patch groups

1. **Guard-control runner.** Corrected as described above.
2. **Drift-fragile test.**
   `test_resolvable_abbreviated_inventory_revision_is_rejected` now serves each
   owner's delivered README at `origin/main:README.md`, as `completion_fixture`
   does, and keeps the real `rev-parse` resolution. Later owner relabels are
   report-only (pass-2 Decision 1). To confirm this, a later compatibility
   section was injected into ChatBot's `origin/main` README in memory, and the
   test still passed.
3. **Untested `verify_amendments.py` guards.** Three new tests bring the suite
   to 49. Each case expects the exact `FAIL:` line on an empty stdout.

   | Guard | Test | Damage |
   | --- | --- | --- |
   | `check_rows` → `check_replacement` call | `test_exact_replacement_column_is_checked_through_every_row` | Admin AC01 and technical FH02 `Exact replacement` and `Amendment disposition: replace`, through `check_rows` |
   | successor version | `test_owner_packet_checks_successor_version_and_metadata` | `inventory_version` of each successor, in memory, through `verify_owner_packet` |
   | `check_metadata` call | same | `source_revision` of each successor |
   | continuation without a path | `test_anchor_paths_must_resolve_to_declared_ordinary_files` | leading `` `:12` `` |
   | unresolved anchor | same | `Unknown/Command.cs:12` |
   | CODEOWNERS repository context | same | `.github/CODEOWNERS:3` without a `references/…` repository |
   | declared repository | same | `references/Hexalith.Unknown/src/Tool.cs:12` |
   | `/SKILL.md` refusal | same | `references/Hexalith.FrontComposer/docs/skills/frontcomposer/SKILL.md:12` |

   - The CODEOWNERS guard was found untested while this group was being applied.
     It is covered here as well.
   - `reject` now turns an exception that escapes `main()` into a test failure
     instead of a test error, so removing the continuation guard (which then
     crashes with `AttributeError`) still counts under the no-errors rule.
   - `:239` (blank rationale or owner) is still left as it is, as triaged.
4. **Full-output assertions.**
   - The guard-present half of the safety-class guard-removal test now expects
     the exact `FAIL:` line.
   - Both in-suite guard-removal tests and the root-submodule drift test now
     expect the full fixed stdout.
   - The real-process drift test now expects the same three amendment lines and
     one label line as the real CLI stream test. Both derive them from
     `expected_process_stdout`.
   - The remaining label success assertions (`assertIn('integrated delivery
     verified', …)` and `(code, stderr)` pairs) now compare the full stdout as
     well.
5. **Diagnostics.**
   - `check_replacement` now receives a `module:key (class)` label, for example
     `technical-tools:FH02 (K01): replacement lacks exact decorated type at
     source pin and agent eligibility`.
   - All thirteen key-only messages in `anchor_evidence` and `check_rows` are now
     prefixed with the module.
   - Passing output is unchanged.
6. **Upstream table.** The "Final state" preamble of the
   [entry document](../verification.md) now states that delivery rebased the
   EventStore, Projects and ChatBot patches. It links
   `delivery/label-publications.json` and `delivery/pre-refresh/`, and names
   `labels.json` as authoritative for delivered bases and patch hashes.

## Checks

[checks.json](checks.json) binds the exact command lines, exit codes and stream
hashes for:

- discovery and direct test execution;
- both default verifiers;
- both explicit approved-completion gates;
- unchanged AD-23 adoption;
- `git diff --check`;
- the corrected guard controls.

All nine checks exit 0. The five verifier stdouts are byte-identical to the
[pass-3 parent receipts](../review-pass-3/parent-review/verification.md). The
`git diff --check` stderr contains only this workspace's commit-graph warnings,
as in pass 3. The completion gates read existing local owner refs and objects.
No remote fetch or owner repository mutation was performed.

[packet-scan.json](packet-scan.json) records a clean
`scripts/scan-evidence-secrets.py` scan of the complete Story 5.7 evidence
directory. It is generated outside the packet and copied in afterwards.

## Unchanged scope

The two accepted deferrals remain open:

- inherited McpCli dependency and census CI failures (`deferred-work.md:1032`);
- the approved successors' historical pending wording, to be corrected in a
  newly approved version (`deferred-work.md:1037`).

Production, dependencies, census, `.gitmodules`, gitlinks and `references/` have
no diff. No staging, commit, push or merge was performed.

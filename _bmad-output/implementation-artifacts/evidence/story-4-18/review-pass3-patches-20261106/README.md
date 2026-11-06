# Story 4.18 pass-3 patch verification

All ten pass-3 patches are implemented. Operator recording refuses duplicate
JSON keys before writing a decision or credential; retention inspects every raw
JSON string, including hidden duplicate values, and preserves safe input bytes.
New regressions cover the actual source-receipt producer, recomputed acceptance,
changed valid import approval, duplicate public ZIP members, source and selection
drift before both runners, and the prepare-time Redis override. Five documentation
corrections now describe the selected artifact, helper support closure, signed
administrator hint, local source prerequisites and current review record.

[Verification](verification.json) retains commands, observed full source SHAs and
final changed-file hashes. The original spec baseline and frozen block match the
committed bytes. All 156 release Python tests, 87 controlled topology hook tests
and four selector tests pass with no skips. The final 36-test publication rerun
also passes after exact duplicate-key stdout/stderr and refusal-receipt assertions
were added. Actionlint, per-file shell syntax, instruction synchronization and
whitespace checks pass.

[Guard-removal evidence](guard-mutations.json) records all 13 detected removals,
with their intentional failing test output and the [reproduction harness](guard-mutations.py).
These mutations load altered modules in memory or edit disposable test-owned
copies; repository source is never mutated by the harness. Credential strings,
packages, GitHub responses and registry outcomes in these regressions are synthetic.

The five frozen matrix rows have executed passing coverage in
[the matrix receipt](matrix-coverage.json), also embedded in verification.json:

| Matrix state | Executed coverage |
| --- | --- |
| Accepted exact pair and approval | Actual-session and automated publication success, exact bytes and two pushes |
| Tampered, mismatched or failed evidence | Authenticated archive/source checks, recomputed acceptance, imported evidence and executed-job refusals |
| Missing key, occupied version or uncertain feed | Credential/feed refusal, both identities and explicit first-ever 404 handling |
| Partial or uncertain publication | Per-package outcomes, visible failure and no retry |
| Bootstrap after the pair starts | Bootstrap refusal and actual first-pair marker creation/recovery boundary |

This is local working-tree verification. No remote operation, real live topology,
client session, publication, dependency/reference update or commit was performed.
The public 2.0.1 evidence remains bound to its original release source. Parent
BMAD review and finish remain pending.

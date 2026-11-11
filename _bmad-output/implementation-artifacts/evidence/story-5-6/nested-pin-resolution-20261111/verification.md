# Nested-pin resolution verification

Implemented the user-approved (2026-11-11) cross-tree resolution for MSBuild
imports and Compile item sources only. The workspace rule reads an escaping path
from the root-declared reference it lands in, at that root's committed pin. The
nested rule reads a nested gitlink's exact commit from the single root reference
whose declared URL matches. One hop per resolution chain; everything else keeps
`unsafe-import-path` / `unsafe-or-nested-compile-source`, with
`nested-pin-unresolvable`, `nested-object-unavailable` and
`workspace-object-unavailable` for the named failures. Nothing is initialized,
fetched, checked out or executed (`GIT_NO_LAZY_FETCH=1` on every Git read).

Final serial run: [runs/final-2](runs/final-2/commands.json) at parent
`ef80e45056620aa851a68276428aa63ed6dcc90b`, root pins identical to the
manifest-selector packet.

- Census fixtures: 192 passed, including 14 new nested-pin fixtures.
- Guard-removal controls: 212 detected: 43 new, 8 prior controls adapted to the
  moved anchors and 161 retained unchanged ([runner](mutation-guards.py)).
- Release regressions: 195 passed.
- All five [I/O matrix rows](matrix-coverage.json) have passing executed coverage.
- [Determinism](runs/final-2/determinism.json): complete report, stdout and stderr
  bytes match across hash seeds 1 and 2. The final report is retained once as
  [census.json](runs/final-2/census.json); repeats are recorded as hashes.
- [Before run](runs/final-2/before-run.json): the committed HEAD checker, which is
  the manifest-selector final implementation, reproduces that packet's final
  report exactly at these pins (only `parentRevision` differs).
- The fresh committed-pin scan exits 1: 17 roots accounted for, 5 complete,
  479 observations, 39 rejected observations, 68 coverage errors, 10 stale
  allowances and 58 [cross-tree reads](cross-tree-provenance.json), each re-read
  at its recorded commit with matching SHA-256 and pin.

[Blocker accounting](blocker-delta.json) against
`manifest-selector-resolution-20261111`: coverage errors fall from 107 to 68 and
rejected observations from 120 to 39. Of 210 prior blocker keys, 120 resolve,
14 resolve while their source keeps another blocker and 76 remain. All 14 new
keys appear on sources whose earlier refusal resolved; none is independent.
All 62 prior standalone source-file rejections now associate with approved
projects only: EventStore Admin.Cli (49) and Admin.Mcp (13)
([source association](source-association.json)). Eight added stale allowances
belong to ChatBot and Platform, which are now fully inspected; staleness does not fail.

[Prior evidence, policy and inventory integrity](prior-policy-integrity.json)
covers every Story 5.1 and earlier Story 5.6 evidence file plus the baseline,
amendments, legacy receipts and inventory. All are byte-identical to their
recorded and committed bytes, except three git-ignored files, which are unchanged.
[Reference integrity](reference-integrity.json) shows no gitlink, `.gitmodules`
or reference worktree change. The first full run passed and was superseded by a
README-only correction; it is kept under
[attempts/final-1-superseded](attempts/final-1-superseded/census-report-hash.json)
with its identical report recorded as a hash. The evidence
[secret-scan receipt](secret-scan.json) is clean, with no findings or errors;
its [command](secret-scan-command.json) is retained alongside it.

The [decision packet](decision-packet.md) groups the remaining blockers. No
allowance, exception, exemption, approval, dependency, reference or gitlink
changed. Story and sprint stay `in-progress` because current-reference acceptance
still fails. No .NET or live check applies to this Python and documentation
change. Nothing was staged, committed or pushed.

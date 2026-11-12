# Exists() guard resolution verification

Implemented the user-approved (2026-11-11) guard extension for MSBuild imports
and property definitions. An element's own `Condition`, plus any enclosing
`PropertyGroup`/`ImportGroup` `Condition`, is evaluated only as a balanced
top-level `and` conjunction with no top-level `or`. Arguments expand with the
property alternatives in effect at that document position; an unresolved `$(`
proves nothing. `Exists(p)` makes the element unreachable when every expansion
of `p` is proven absent under the local, workspace and nested rules. `!Exists(p)`
makes it unreachable when every expansion is a committed regular blob or
directory in the inspected root, or in a root-declared reference at its root pin.
A nested path is never proven present. An unreachable conditional definition
contributes no alternative, and an unreachable import is not visited.
`Choose`/`When` and `Target` conditions are never evaluated. Nothing new is
recorded in policy.

Final serial run: [runs/final-1](runs/final-1/commands.json) at parent
`6ec91eb81aa98a850e98ad0b139972158eaf9fef`.

- Census fixtures: 197 passed, including the 2 new guard fixtures (11 positive
  and 19 refusal subcases) and 3 upstream fixtures merged with commit `94f5ee6`.
- Guard-removal controls: 236 detected: 24 new, 43 from the nested-pin packet,
  161 retained, 7 adapted earlier and 1 adapted here
  ([runner](mutation-guards.py)). `Review-S07-optional` now removes both ways an
  absent `Exists()`-guarded import becomes optional, because the guard proof
  runs first. The [failed attempt](attempts/failed-1-subsumed-review-s07-control/mutations.stderr.txt)
  that found this is retained.
- Release regressions: 195 passed.
- All five [I/O matrix rows](matrix-coverage.json) have passing executed coverage.
- [Determinism](runs/final-1/determinism.json): complete report, stdout and stderr
  bytes match across hash seeds 1 and 2. The final report is retained once as
  [census.json](runs/final-1/census.json); repeats are recorded as hashes.

## Concurrent repository changes

During this work another session committed `884f65e` (*build: sync local
changes via /pushall*). It included this story's uncommitted work and moved
eight root gitlinks. It then merged upstream `94f5ee6`, which changes `check.py`,
its tests and the census guide, as `6ec91eb`. This change staged, committed and
pushed nothing. The second [failed attempt](attempts/failed-2-parent-revision-moved/commands.json)
recorded the pin change.

Accounting therefore uses one revision and one set of pins. The
[before run](runs/final-1/before-run.json) executes
[`before-upstream-check.py`](before-checkers.json): the exact nested-pin
checker ([`before-check.py`](before-check.py), hash-matched to the nested-pin
packet) plus the upstream `check.py` hunks applied by `git apply`. It differs
from the current checker only by this extension, and its report is retained as
[before-census.json](runs/final-1/before-census.json). The plain nested-pin
checker at these pins is recorded as hashes and counts.

| Report | Errors | Rejected | Observations | Complete roots |
|---|---:|---:|---:|---:|
| Nested-pin packet, earlier pins | 68 | 39 | 479 | 5 |
| Nested-pin checker, current pins | 69 | 40 | 480 | 5 |
| Nested-pin plus upstream, current pins (baseline) | 69 | 41 | 481 | 5 |
| This change, current pins | 45 | 30 | 473 | 6 |

[Blocker accounting](blocker-delta.json) against that baseline: of 93 blocker
keys, 35 resolve and 58 remain. There are no new keys. All 24 cross-tree
fallback errors resolve: 20 Tenants projects and 4 Commons projects. So do 11
rejected publication observations that those failures had made orphan or
unmatched. Commons is now fully inspected.
[Guard proofs](guard-proofs.json) re-evaluate those 24 projects with no metadata
error. Each project lists the facts evaluated true or false, including the
workspace-present `../Hexalith.Builds/Hexalith.Package.props` for Commons and
the outside-root-absent `../../Hexalith.Builds/Props/ContainerProvenance.targets`
for Tenants. All 63 [cross-tree reads](cross-tree-provenance.json) re-verify at
their recorded commits.

The fresh committed-pin scan exits 1: 17 roots accounted for, 6 complete, 473
observations, 30 rejected observations, 45 coverage errors and 10 stale
allowances. [Prior evidence, policy and inventory integrity](prior-policy-integrity.json)
and [reference integrity](reference-integrity.json) pass. This change edited no
reference, gitlink or `.gitmodules` entry. The evidence
[secret-scan receipt](secret-scan.json) is clean, and its
[command](secret-scan-command.json) is retained.

The [decision packet](decision-packet.md) groups the remaining blockers. No
allowance, exception, exemption, approval or dependency changed. Story and
sprint stay `in-progress` because current-reference acceptance still fails.

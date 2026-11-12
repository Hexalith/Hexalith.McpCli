# Guard excuse review verification

Review loop 1 re-implements the user-approved (2026-11-11) `Exists()` guard rule
as an excuse only, and applies the nested-pin review fixes. The superseded
pruning version is kept as evidence in `exists-guard-resolution-20261111`.

- **Excuse.** A guard only excuses an import target that is missing from every
  inspected tree and would otherwise be refused as `unavailable-local-import` or
  an absent `unsafe-import-path`. That happens when (a) the import's own or
  enclosing `ImportGroup` condition has a conjunct that proves false, or (b) the
  import's `Project` is exactly one `$(P)` and every definition that produced the
  value proves false through its own or enclosing `PropertyGroup` condition.
  Present imports are always visited, no property alternative is removed and
  classification is unchanged.
- **Proof model.** Proofs model the parent workspace from committed tree entries.
  Presence is exact-case and never nested, linked, globbed or outside every root.
  Absence is case-insensitive and never a tree root, the parent workspace root, a
  glob, a path above the parent or a path below an unopened gitlink. Arguments
  with unresolved, item or `%XX` text, or naming incomplete or `Target`-defined
  properties, prove nothing. Import conditions resolve from the declaring file
  and other conditions from the entry project's directory. A substituted file
  stays within its one-hop tree.
- **Nested-pin fixes.** A substituted file's unresolved `$(` import fails as
  `unsafe-import-path` with its label. Nested `.gitmodules` need valid
  `submodule` sections with safe paths. A missing substituted blob fails as
  `workspace-object-unavailable` or `nested-object-unavailable` with the
  requested label. Closures bind cross-tree members by label. Amendment fixture
  validation has no workspace context. Every Git call adds
  `-c protocol.allow=never`, sets `GIT_NO_LAZY_FETCH=1` and
  `GIT_NO_REPLACE_OBJECTS=1`, and drops `git rev-parse --local-env-vars`.

Final serial run: [runs/final-1](runs/final-1/commands.json) at parent
`6ec91eb81aa98a850e98ad0b139972158eaf9fef`, root pins identical to the
exists-guard packet. A [stopped attempt](attempts/stopped-1-closure-drift-errors-unasserted/reason.json)
is retained; it ended during the controls so the closure drift fixture could
also assert its full error document.

- Census fixtures: 214 passed, including 19 new guard-excuse and review fixtures.
  Two prior fixtures changed with the approved behavior: an absent
  `Exists('…/absent/other.props')` guard now excuses its absent target, and a
  closure lists its cross-tree member.
- Guard-removal controls: 283 detected ([runner](mutation-guards.py)): 71 new,
  161 retained, 42 nested-pin, 5 nested-pin anchor adaptations and 4 adapted
  here. `Review-S07-optional` now uses the committed-but-excluded fixture,
  because an absent exact-`Exists()` target is also excused (VG1).
  `N24-no-lazy-fetch` removes both fetch guards, because
  `protocol.allow=never` alone also blocks the lazy fetch. The exists-guard
  runner's 24 controls targeted the reverted pruning code and are not reused.
- Release regressions: 195 passed.
- All five [I/O matrix rows](matrix-coverage.json) have passing executed coverage.
- [Determinism](runs/final-1/determinism.json): complete report, stdout and stderr
  bytes match across hash seeds 1 and 2. The final report is retained once as
  [census.json](runs/final-1/census.json); repeats are recorded as hashes.

## Before/after accounting

The [before run](runs/final-1/before-run.json) executes, at the same revision
and pins, the superseded pruning checker
([`before-pruning-check.py`](before-pruning-check.py), the exists-guard final
implementation at `6ec91eb`) and that packet's no-guard baseline
(`before-upstream-check.py`). Both reproduce their exists-guard reports exactly,
apart from `parentRevision` and `utcDate`. The pruning report is retained as
[before-census.json](runs/final-1/before-census.json); the baseline is recorded
as hashes and counts.

| Report | Errors | Rejected | Observations | Complete roots | Cross-tree reads |
|---|---:|---:|---:|---:|---:|
| No-guard baseline | 69 | 41 | 481 | 5 | 60 |
| Superseded pruning checker | 45 | 30 | 473 | 6 | 63 |
| This change | 47 | 30 | 473 | 6 | 62 |

[Blocker accounting](blocker-delta.json):

- **Against the no-guard baseline.** Of 93 keys, 34 resolve, 1 resolves while
  its source keeps another blocker, and 58 remain. All 24 cross-tree fallback
  errors resolve: Tenants 20 and Commons 4. No import refusal remains.
- **Against the pruning checker.** All 58 keys remain, and one key is new: two
  `unsafe-or-nested-compile-source` errors on the Tenants AppHost project, with
  targets `../../DaprSelfHostedMtls.cs` and `../../DaprSelfHostedMtlsSubscriber.cs`.
  The no-guard baseline masked them with that project's import refusal. The
  pruning checker hid them by dropping the guarded `HexalithPlatformRoot`
  alternative `$(MSBuildThisFileDirectory)../..` (Tenants `Directory.Build.props`
  line 65). The excuse-only rule keeps every alternative, and a Compile item is
  never excused, so they stay refused.
- **Unchanged.** Observations and rejected identities are unchanged against the
  pruning checker. [Cross-tree reads](cross-tree-provenance.json) differ only
  because retained alternatives are read: 4 Tenants Compile reads are gone with
  the refused element, and 3 Folders reads are new. All 62 reads re-verify at
  their recorded commits.

[Excuse proofs](excuse-proofs.json) re-evaluate the 24 projects. No import
refusal remains; the AppHost keeps only its two Compile refusals. The proven
facts include the outside-root-absent
`../../Hexalith.Builds/Props/ContainerProvenance.targets` (Tenants) and the
workspace-present `../Hexalith.Builds/Hexalith.Package.props` (Commons). Facts
evaluated for other conditional definitions are listed too; none of them removes
an alternative.

The fresh committed-pin scan exits 1: 17 roots accounted for, 6 complete, 473
observations, 30 rejected observations, 47 coverage errors and 10 stale
allowances. Both authorized fixture exemptions remain approved.
[Prior evidence, policy and inventory integrity](prior-policy-integrity.json)
covers 702 files, all byte-identical across the run. 641 equal their committed
bytes, 57 untracked exists-guard files equal that packet's secret-scan receipt,
and 3 git-ignored files equal its integrity record. The exists-guard receipt
itself is outside its own scan and is shown only as unchanged. The tracked
exists-guard mutation runner equals that packet's implementation record, not
HEAD; this change did not touch it. [Reference integrity](reference-integrity.json)
shows no gitlink, `.gitmodules` or reference worktree change.

The evidence [secret-scan receipt](secret-scan.json) and its
[command](secret-scan-command.json) are retained. The
[decision packet](decision-packet.md) groups the remaining blockers. No
allowance, exception, exemption, approval, dependency, reference or gitlink
changed. Story and sprint stay `in-progress` because current-reference
acceptance still fails. No .NET or live check applies to this Python and
documentation change. Nothing was staged, committed or pushed.

## Review-patch rerun (final-2)

After the loop-1 review, patches L1–L19 were applied in place. The full serial
set was rerun as [runs/final-2](runs/final-2/commands.json) at parent
`f223aaa5acd70c04a413f3251f83d96472a6b0d9`; `latest-run.json` now points to it.
Between `6ec91eb` and that parent, three concurrent build-only commits
(`ebb5c72`, `ad0542c`, `f223aaa`) changed SDK and workflow setup only. No root
gitlink moved, and the census job is unchanged. `runs/final-1` is kept as the
pre-patch run.

- Census fixtures: 219 passed.
- Guard-removal controls: all 297 were detected ([runs/final-2/mutations.stdout.txt](runs/final-2/mutations.stdout.txt)).
- Release regressions: 195 passed.
- [Determinism](runs/final-2/determinism.json): report, stdout and stderr bytes
  match across hash seeds 1 and 2. Report SHA-256 is
  `6385946560009db6f4fbbf70157e2ab1ff49e8d8de57f647caf504a271899548`.
- A parent-run scan at the same parent produced the same report bytes before and
  after the patches. The patches changed no observation, rejection or error in
  the real scan: 47 errors, 30 rejected observations, 473 observations, 6
  complete roots, 10 stale allowances and 62 cross-tree reads.
- `git diff --check` passed. The pre-patch secret-scan receipt is kept in
  [attempts/pre-patch-evidence/](attempts/pre-patch-evidence/secret-scan.json);
  `secret-scan.json` is the fresh receipt for this packet.

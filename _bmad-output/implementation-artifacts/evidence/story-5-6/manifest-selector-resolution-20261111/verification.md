# Manifest-selector verification

Implemented the finite committed-JSON row selector and ordered tab-delimited
shell read required by the inspected packaging script. The [source proof](selector-source-proof.json)
binds the script, manifest, every selected project and inspected local metadata
at parent `1a44525c450081dc07df4021ab23e3090aacfda4`. Literal enumeration grants no qualification.

- Census fixtures: 178 passed.
- Guard-removal controls: 169 detected, including every new control in [the guard map](guard-map.json).
- Release regressions: 195 passed.
- All five [I/O matrix rows](matrix-coverage.json) have passing executed coverage.
- Complete report bytes match across hash seeds 1 and 2.
- The fresh scan exits 1: 17 roots accounted for, 2 complete, 548 observations,
  120 rejected observations, 107 coverage errors and 2 stale allowances.

The original checker at these same pins reports 109 errors;
the updated checker reports 107. The [delta](blocker-delta.json)
accounts for every original/current blocker. The selector resolves its target
enumeration. All 3 selected project metadata inspections complete without errors. Their exact observations are retained in the source proof; other repository sources retain root-wide blockers. No active upstream
defect or new owner authority is inferred.

[Exact commands and streams](runs/final-1/commands.json)
and [machine verification](verification.json) retain canonical revisions, source
hashes, checks and outcome. [Prior/policy integrity](prior-policy-integrity.json)
and [reference integrity](reference-integrity.json) verify preserved bytes.
Failed and superseded attempts remain under `attempts/`; final checks were rerun
after the last implementation change. The secret-scan receipt is
`secret-scan.json`; its command and status are retained alongside it.

The [decision packet](decision-packet.md) separates remaining source boundaries,
scanner limitations, embedded-data context and exact owner dispositions.
Story and sprint remain `in-progress`; current-reference release acceptance fails.
No .NET/live check was needed for this Python/documentation-only change.
No staging, commit, push, dependency/reference change or publication occurred.

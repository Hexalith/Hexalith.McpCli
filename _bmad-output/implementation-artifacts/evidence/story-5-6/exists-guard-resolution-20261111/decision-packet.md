# Remaining census decisions after Exists() guard resolution

Current-reference acceptance remains unsuccessful at parent
`6ec91eb81aa98a850e98ad0b139972158eaf9fef`. The guard extension resolves the two
cross-tree fallback patterns that the nested-pin packet left open, with no new
blocker. This packet grants no allowance, exception, exemption, approval or
other authority.

- **Tenants** `Directory.Build.targets` (blob `7d61bd440a16804067c1af0e14431df369b2cc15`
  at `fb105d7c6035671bdc66dfb27990a463ea6165b2`), 20 projects. The third
  `HexalithContainerProvenanceTargets` alternative (line 119) requires
  `Exists('../../Hexalith.Builds/Props/ContainerProvenance.targets')`. That path
  lands at the parent root outside every root and is proven absent, so the
  alternative contributes nothing. The unconditioned import on line 121 then
  resolves its nested and workspace alternatives.
- **Commons** `src/libraries/Directory.Build.props` (at `11555ace9efcae2928a00122dcba91243e5a8a1a`),
  4 projects. The line 21 fallback requires `!Exists(H2)`. H2,
  `../Hexalith.Builds/Hexalith.Package.props`, is present at the root Builds pin,
  so the fallback import is not visited. Its nested `!Exists(H1)` conjunct proves
  nothing, as approved.

[Exact remaining decisions](acceptance-blockers.json) bind each blocker to its
owner, full gitlink and committed source hash.

| Group | Keys | Observations | Next concrete action |
|---|---:|---:|---|
| Exact owner disposition | 31 | 31 | Owners compare each of the 30 rejected identities and signal sets with the retained inventory and supply committed proof or an exact approved amendment. The Builds `Tools/package-version-audit.json` exclusion no longer matches its bytes at the new Builds pin, so its owner approves the new bytes in a versioned amendment or keeps the approved bytes. |
| Protected source boundaries | 6 | 23 | Nested publication targets, generated task output and unresolved Compile inputs stay refused. Owners supply root-contained committed sources, or a separate generic boundary design is approved. |
| Scanner limits or unproven inputs | 18 | 18 | Inspect each bound dependency; design only a finite generic proof with refusal fixtures. Runtime and PowerShell evaluation stay unsupported. |
| Embedded metadata context | 3 | 3 | Owners classify each exact blob as active composition or test/evidence data before any hash-bound versioned exclusion. |
| Proven active upstream defects | 0 | 0 | None is established. |

The cross-tree boundary group is now empty. The rejected observations are not a
count of new tools. Newly inspected Tenants projects such as `seed.csproj` are
approved under existing allowances. The script that publishes `seed.csproj`
is observed under the full path identity
`tests/performance/tenant-audit/seed.csproj`, which has no exact allowance.

The failed release gate remains in force. Story and sprint stay `in-progress`.
This change performed no staging, commit, push or publication. Concurrent commits
`884f65e` and `6ec91eb` by another session are recorded in [verification](verification.md).

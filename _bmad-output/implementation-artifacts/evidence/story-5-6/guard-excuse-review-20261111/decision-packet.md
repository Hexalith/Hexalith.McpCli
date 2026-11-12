# Remaining census decisions after the guard excuse review

Current-reference acceptance remains unsuccessful at parent
`6ec91eb81aa98a850e98ad0b139972158eaf9fef`. The excuse-only rule resolves the
same 24 cross-tree fallback errors as the superseded pruning version (Tenants
20, Commons 4), without skipping a present import or removing a property
alternative. This packet grants no allowance, exception, exemption, approval
or other authority.

- **Tenants** `Directory.Build.targets` (blob `7d61bd440a16804067c1af0e14431df369b2cc15`
  at `fb105d7c6035671bdc66dfb27990a463ea6165b2`), 20 projects. The import of
  `$(HexalithContainerProvenanceTargets)` is excused for its third value only:
  every definition producing it (line 119) requires
  `Exists('../../Hexalith.Builds/Props/ContainerProvenance.targets')`, which
  lands at the parent root outside every root and is proven absent. Its nested
  and workspace values are still read.
- **Commons** `src/libraries/Directory.Build.props` (at `11555ace9efcae2928a00122dcba91243e5a8a1a`),
  4 projects. The line 21 fallback import is excused because its own condition
  requires `!Exists(H2)`, and H2, `../Hexalith.Builds/Hexalith.Package.props`,
  is present at the root Builds pin. Its nested `!Exists(H1)` conjunct proves
  nothing, as approved.

[Exact remaining decisions](acceptance-blockers.json) bind each blocker to its
owner, full gitlink and committed source hash.

| Group | Keys | Observations | Next concrete action |
|---|---:|---:|---|
| Exact owner disposition | 31 | 31 | Owners compare each of the 30 rejected identities and signal sets with the retained inventory and supply committed proof or an exact approved amendment. The Builds `Tools/package-version-audit.json` exclusion no longer matches its bytes at the current Builds pin: its owner approves the new bytes in a versioned amendment, or the pin keeps the approved bytes. |
| Guarded Compile fallback | 1 | 2 | The Tenants AppHost (blob `96258cca91e4026e44a982031379f86862a98f17`) compiles `$(HexalithPlatformRoot)\DaprSelfHostedMtls*.cs`. `Directory.Build.props` (blob `557bb2d6d3b8b90019fce88cf5baacfa7a1e3919`) line 65 keeps the `$(MSBuildThisFileDirectory)../..` alternative, outside every root. The approved excuse covers imports only. The owner can make the Compile source root-contained, or a separately approved decision may extend the excuse to Compile items. |
| Protected source boundaries | 6 | 23 | Nested publication targets, generated task output and unresolved Compile inputs stay refused. Owners supply root-contained committed sources, or a separate generic boundary design is approved. |
| Scanner limits or unproven inputs | 18 | 18 | Inspect each bound dependency; design only a finite generic proof with refusal fixtures. Runtime and PowerShell evaluation stay unsupported. |
| Embedded metadata context | 3 | 3 | Owners classify each exact blob as active composition or test/evidence data before any hash-bound versioned exclusion. |
| Proven active upstream defects | 0 | 0 | None is established. |

The guarded Compile fallback is new against the pruning checker. It is not new
source: the no-guard baseline masked it with the same project's import refusal,
and the pruning checker hid it by dropping the guarded alternative, the
behavior review loop 1 forbids. The rejected observations are not a count of
new tools.

The failed release gate remains in force. Story and sprint stay `in-progress`.
This change performed no staging, commit, push or publication.

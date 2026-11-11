# Remaining census decisions after nested-pin resolution

Current-reference acceptance remains unsuccessful at parent
`ef80e45056620aa851a68276428aa63ed6dcc90b`. Root pins and policy are identical
to the manifest-selector packet. Nested-pin resolution clears the layout-fallback
cascade for EventStore, PolymorphicSerializations, ChatBot, Platform, Folders,
FrontComposer, Projects and Works. ChatBot, Platform and PolymorphicSerializations
are now fully inspected. This packet grants no allowance, exception, exemption,
approval or other authority.

[Exact remaining decisions](acceptance-blockers.json) bind each blocker to its
owner, full gitlink and committed source hash.

| Group | Keys | Observations | Next concrete action |
|---|---:|---:|---|
| Cross-tree boundary | 24 | 24 | Decide whether to approve one more bounded generic rule (below), or have the owners guard each fallback import exactly. |
| Protected source boundaries | 6 | 23 | Nested publication targets, generated task output and unresolved Compile inputs stay refused. Owners supply root-contained committed sources, or a separate generic boundary design is approved. |
| Scanner limits or unproven inputs | 18 | 18 | Inspect each bound dependency; design only a finite generic proof with refusal fixtures. Runtime and PowerShell evaluation stay unsupported. |
| Embedded metadata context | 3 | 3 | Owners classify each exact blob as active composition or test/evidence data before any hash-bound versioned exclusion. |
| Exact owner disposition | 39 | 39 | Owners compare each exact identity and signal set with the retained inventory, then supply committed proof or an exact approved amendment. These observations are not a count of new tools. |
| Proven active upstream defects | 0 | 0 | None is established. |

## Cross-tree boundary detail

Both patterns are layout fallbacks that the approved rule deliberately leaves
refused. Each reaches a parent-tree path outside every root with no `Exists()`
guard on that exact path.

- **Tenants** `Directory.Build.targets` (blob `b78c9cbde72551cbed09bfaa486d93ded3c78bb1`
  at `019aa0a82d021e08475a68fc50eff3b6a0e6c111`), 20 projects. The
  `HexalithContainerProvenanceTargets` alternatives carry their `Exists()`
  guards on the property definitions (lines 117–119); the import on line 121
  is unconditioned. The `../../Hexalith.Builds/Props/ContainerProvenance.targets`
  alternative lands at the parent root, outside every root.
- **Commons** `src/libraries/Directory.Build.props` (blob `1df854afeaf91da63329357da045aaca3c180f33`
  at `11555ace9efcae2928a00122dcba91243e5a8a1a`), 4 projects. The line 21
  fallback import is guarded only by `!Exists(H1) And !Exists(H2)`. Both H1
  (nested Builds `4d892075254c889502700151ce78c75f00aa7276`) and H2 (root
  Builds `891886ddc60a9924d053bb74bf6bcc73e101b2ce`) resolve and are read, so the
  guard is false in this workspace. Evaluating a negated `Exists()` was not
  part of the approved rule.

A bounded generic extension could resolve both cases. It would treat an import
as absent when a top-level `!Exists(p)` conjunct names a path `p` that the same
rules prove present. It would also carry the `Exists()` guards of a
property-definition alternative into the import that consumes it. Either
extension needs explicit approval before implementation.

## Newly visible observations

All 14 new blocker keys are on sources whose earlier refusal resolved, and none
is independent. Twelve Tenants projects now reach `Directory.Build.targets` (12
keys). EventStore `Sample.Api.GeneratedCodeQuality` now reaches its
generated-copy Compile alias (1). EventStore Admin.Cli exposes its effective
package identity `package:Hexalith.EventStore.Admin.Cli`, which has no exact
baseline allowance. That last observation needs owner disposition. The 62
EventStore source files that were separate rejections now belong to the approved
Admin.Cli and Admin.Mcp project allowances.

The failed release gate remains in force. Story and sprint stay `in-progress`.
No staging, commit, push or publication was performed.

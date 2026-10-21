# Review corrections for isolated release prerequisites

Current isolated base: `ea926163fb51033b226541f069ebf6a5941922af`.
The refreshed current gitlink observations supplied by the parent are retained.
The earlier e55-based handoff remains historical in the original files here.

All seven review requests are corrected in the same three-file scope:

- Evaluate actual default Release without a mode override, explicit package
  mode, bare Debug with only `UseHexalithProjectReferences=true`, and explicit
  source consumer property fixtures.
- Discover consumers from declared package/project identities independently of
  selector spelling or presence; validate the resulting selected branches.
- Retain Version, VersionOverride, central PackageVersion and effective version
  metadata in the existing graph carrier. Check selected consumer package
  versions and reject mismatches, including VersionOverride drift.
- Require every selected project file to exist and source-family paths to use
  the supplied root. Preserve both negative and positive McpCli layouts.
- Describe direct property inputs accurately in the matrix: generated imports,
  mapping-hash checks and tool validation targets do not run. These checks prove
  consumer branch selection only, not module-tool composition or source builds.
- Recognize Git submodule update commands with global options, shell command
  separators and submodule options; reject recursive/remote flags in any order
  and recursive Git configuration. Keep direct reference set, privacy,
  command/query and legacy-host guards.

[Exact focused commands/results](review-checks.json) record Release builds with
zero warnings/errors and **45/45 fitness tests**, **15/15 Sample guardrail tests**,
zero failures/skips. Regression cases exercise selector misspellings/removal,
missing projects, direct Version/VersionOverride drift and unsafe Git commands.
Only these two classes ran; full verification remains with the parent.

[Integrity evidence](review-integrity.json) confirms all 180 tracked Contracts/
vector files and approved Contracts/vector manifest hashes match, all historical
matrix bytes remain unchanged, all ten root dependency checkouts are clean at
current committed gitlinks with no initialized nested submodules, and CRLF-aware
plus actual trailing-space checks pass. The final changes are retained as
[a reviewable patch](review-release-prerequisites.patch).

No runtime, onboarding documentation, Contracts, vectors or reference contents
were changed. No approved artifact was repacked and no approval receipt replaced.
No commit, push or release dispatch occurred. Protected publication, published-byte
validation, central pin delivery and enrollment remain open.

# Isolated release-prerequisite correction

Worktree: `/tmp/hexalith-parties-story410-release`, fixed at
`e55da59006f55410b9390403c67253b4f8423e18`.

Only three files changed in that worktree:

- `PlatformApiPrerequisitesTests.cs` now checks the committed current graph for
  all ten root dependencies. It preserves package/source graph validation, uses
  ordinary Release packages including Commons HTTP, and supplies explicit
  root/FromSource inputs for diagnostic source evaluations. The existing two
  negative sibling-layout cases remain; two positive cases prove explicitly
  mapped McpCli layouts select only Abstractions.
- The matrix's current observation now identifies the fixed Parties revision,
  current Tenants and Platform gitlinks, and observed Builds/Memories tags. It
  explains the adopted module-tool mapping. All historical matrix bytes from
  the 2026-10-18 heading onward remain unchanged.
- `SampleOnboardingGuardrailTests.cs` protects pinned tool restore/debug/down
  commands, root-declared direct reference initialization and nested/recursive
  update prohibitions. The reference set comparison ignores ordering and warning
  assertions accept wording variations. Command/query, privacy and retained
  legacy-host checks remain. No onboarding documentation or runtime changed.

[Exact commands/results](checks.json) record both focused Release restores and
builds passing with zero warnings/errors, **37/37 fitness tests** and **7/7 Sample
guardrail tests**, zero failures/skips. Only these focused classes ran. Parent
verification must run the full affected domain and Sample projects.

[Integrity evidence](integrity.json) confirms 180 tracked Contracts/vector files
are byte-identical to HEAD, ten dependency checkouts match committed gitlinks and
are clean, no nested submodules are initialized, historical matrix bytes are
unchanged, and source/config whitespace checks pass. The correction is retained
as [a reviewable patch](release-prerequisites.patch). These files are separate
from the approved package/vector inputs; no approved artifact was repacked or
approval receipt replaced.

No commit, push, release dispatch or publication occurred. Protected owner CI,
publication, published-byte revalidation, central pin delivery and production
enrollment remain open. These local fitness results do not extend historical
parity/authorization/custody approvals or prove live domain effects.

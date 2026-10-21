# Aspire timeout correction

Base: `9a4a0657e6c928fbf923fceb9550b28e0b1c571c` on
`fix/story-4-10-release-readiness`.

Added only `aspire-timeout-minutes: 30` beside the existing Aspire inputs in
`.github/workflows/ci.yml`. The blocking `aspire-continue-on-error: false` gate,
all filters, immutable pins and every other workflow byte remain unchanged.
The pinned reusable domain-ci workflow at
`332b2c144defba546fe0a09626a4a72f2340e22f` declares this numeric input and uses
it for the Aspire job timeout. No numeric mirror test was added.

[Exact commands/results](checks.json) record the initial missing-assets build,
the narrow successful restore, Release build (zero warnings/errors), and existing
`PartiesContainerPublishWorkflowTests` class: **48/48 passed**, zero skips.
No wider tests ran. [Integrity evidence](integrity.json) and
[the one-line patch](timeout-correction.patch) preserve the reviewable change;
Contracts/vectors and all ten clean root dependency checkouts are unchanged.

Parent full verification and the subsequent owner CI rerun remain pending.
The cancellation does not establish a passing Aspire gate. No commit, push,
publication or release dispatch was performed.

# Story 4.9 review pass 2 candidate

All nine Review/Patch items G1–G9 are implemented. The prior approved package,
Catalog, source/vector manifests, description reviews and maintainer approval
remain unchanged in the parent evidence directory. This directory records a
separate candidate; it does not replace or extend that historical approval.

The implementation started at Parties `3608e121364198e2ea0643769e680df29bc8efe0`
(the exact resolved identity is in `maintainer-vector-approval.json`). A concurrent
action committed the implementation as
`48bed0054dddca785dd0089d9cfc63384f9ad7c2`; this worker neither staged nor
committed. Two grammar-only lifecycle description corrections followed that
commit. `source-files.sha256.json` records the final source bytes. Review the full change with
`git diff 3608e121364198e2ea0643769e680df29bc8efe0` in the Parties repository.

## Implemented corrections

- G1: a three-row validator theory accepts updates containing only contact
  additions, contact removals or identifier additions.
- G2: all four declaration examples deserialize with `PartiesJsonOptions.Default`
  and pass their registered production validators. Composite omitted lists are
  explicitly asserted empty.
- G3: null collections/items are owned by the existing NotNull rules. The child
  equality predicate ignores them, and fourteen processor cases assert complete
  rejection failure lists and no protected state access. Removal null items
  retain their existing NotEmpty failure as well as NotNull.
- G4: the package fixture resolves `HexalithMcpCliVersion` through MSBuild and
  pins the packed Abstractions dependency to that central value.
- G5: source-root discovery includes both supported sibling layouts. Temporary
  MSBuild probes verify source mode in each layout.
- G6/G7: seven PartyId descriptions state McpCli's legacy-format refusal, with
  lifecycle-specific wording. Child ContactChannelId/IdentifierId wording is
  unchanged. README and API contracts explain the same existing restriction.
- G8: declaration tests pin null correlation, idempotency, actor and serializer
  option-provider bindings.
- G9: a nonempty contact-update list counts as a supported change. The entry
  rule alone rejects an empty contact update; its processor test pins the exact
  single failure and no protected state access.

## Executed checks

`../review-pass-2-checks.json` records exact commands, logs and their hashes.
Release restore and full solution build passed with zero warnings/errors.
The validation class passed **126/126**. Required suites passed **2013/2013
Parties**, **315/315 Server**, **201/201 Contracts**, zero failures/skips.
The final root run covers the complete patched source, including the lifecycle
grammar corrections and source-layout regressions. The isolated Catalog/lint/
routing verification also checks the retained package with those exact descriptions. The hardened candidate verifier's eleven unit tests
also pass normally and under Python optimization. Both sibling source-reference probes pass.

The final local Contracts build and pack used version `0.0.0-story49`. Package:

`sha512-2y0Jw2K2PuWVpfdJLMfQdAoo4REb41uGtAocjkPfpuExmtA6RR6zE9y9JC+mKMq06XTTVn8m7is/YrOzlVnkdQ==`

The ignored artifact is retained at
`artifacts/Hexalith.Parties.Contracts.0.0.0-story49.nupkg`; nothing was published.
To reproduce the isolated checks from the McpCli root:

```sh
python3 _bmad-output/implementation-artifacts/evidence/story-4-9/review-pass-2/verify-scratch.py \
  --mcpcli-root /home/administrator/projects/hexalith/mcpcli \
  --parties-root /home/administrator/projects/hexalith/parties
```

The candidate verifier corrects its default root depth, uses explicit integrity
checks that survive optimization, binds receipt/manifest/artifact hashes,
preserves either production assets bytes or their absence, uses the running
Python interpreter and reports captured subprocess diagnostics. Its eleven
regressions pass normally and optimized. The original verifier remains archived
unchanged. `maintainer-vector-approval.json` now records explicit approval
from the requesting maintainer for this exact refreshed artifact; approval-time
source/vector/verifier preflight and four-vector validation pass. The
validator and host input revision is current McpCli
`040fd406d71723772fb14cb3a3bac9434003b6a4` (the exact resolved identity is in
the record), since the selected Builds gitlink has advanced since the historic
approval. No runtime source or production enrollment changed.

The isolated host proves exactly four approved Commands, valid examples, zero
Catalog diagnostics, empty lint results, strict discovery, both-head routing
and error parity, restored artifact identity and four-vector coverage. Production
McpCli restored assets are byte-identical before/after. Original vector hashes
are unchanged; only temporary routing copies omit unavailable Query postconditions.

`description-delta.json` records seven source wording deltas and nine Catalog
PartyId description occurrences. All non-description Catalog content is identical
to the earlier approved Catalog. No child ContactChannelId/IdentifierId
wording changed.

## Remaining acceptance and downstream gates

Fresh-context description review returned **PASS**, without wording changes;
[description-review.md](description-review.md) records the independent result.
The requesting maintainer explicitly approved this refreshed artifact with
“I approve”. [Approval receipt](maintainer-vector-approval.json) binds its exact
package hash, vector/source/verifier manifests and validator revision.
[Approval-time vector validation](approval-vector-validation.txt) passes, as
does the exact input preflight. All Story 4.9 acceptance items are complete.
The previous artifact and its earlier approval remain preserved separately.

Original Query postconditions remain unexecuted until Story 4.10; Stories
4.11/4.13 prove parity and persistent effects. C06 public-error privacy, C07
legacy PartyId compatibility/conversion and C08 authorization/credential evidence
remain replacement/retirement gates. D1–D3 are already tracked in
the ledger (the authoritative repo-relative path is
`_bmad-output/implementation-artifacts/deferred-work.md:537`). No new deferral,
reference edit, enrollment, publication, push or legacy-host retirement occurred.


## Final review verification

All thirteen resumed review findings were triaged. Seven direct patch groups
were resolved; the complete Release build, three required suites, normal and
optimized verifier tests and full isolated scratch run passed after those
patches. [Final checks](../review-pass-2-final-checks.json) bind their commands
and log hashes. The final Parties total is **2013/2013**, including the two
repeatable source-layout graph cases; Server **315/315** and Contracts
**201/201** pass with zero skipped or failed tests. The final build has zero
warnings/errors. [Matrix audit](matrix-test-audit.md) and
[root integrity audit](root-audit.json) record independent checks.

The retained package hash is unchanged by the harness/test fixes. All Contracts
source bytes and vectors remain exactly those reviewed. Concurrent CI-doc edits
were preserved and explicitly bound in
[source reconciliation](source-reconciliation.json); historical manifests and
approvals remain unchanged.

The pre-existing production dependency-policy mismatch is already tracked at
`_bmad-output/implementation-artifacts/deferred-work.md:480`. The selected Builds
catalog defaults to EventStore 3.126.0/Commons 2.30.3 while production policy
pins 3.124.0/2.30.1. No gitlink or policy was changed by this workflow, and no
production Manifest-gate pass is claimed. This does not change the isolated
four-command candidate's successful verification.

## Completion

The requesting maintainer approval is recorded and all acceptance items pass.
Every source-manifest entry matches Parties revision
`836c315269b196a49455aacf7534c48fba3cb834`, independently committed before completion.
[Completion record](completion.json) captures the source identity and validated
local-commit evidence. The containing McpCli commit records the approved evidence
and completed spec; no publication or push was performed.

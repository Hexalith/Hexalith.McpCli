# Merged release prerequisite and remaining owner gate

[Parties PR #56](https://github.com/Hexalith/Hexalith.Parties/pull/56) is merged at
`fa708d1cdb71a8926c9ed82e2e18a3ce58fd52ef`. The reviewed four-file change corrects
stale dependency/source-selection and onboarding checks, refreshes only current
source receipts, and gives the blocking Aspire job a supported 30-minute allowance.
Historical receipts and the approved Contracts/vector bytes remain intact.

[Complete PR CI](pr-56-ci-green.json) passed at original reviewed head
`df8173f04bd65cb86bc0d060dc75914e421f7640`:

- [Downloaded results](pr-56-final-test-results.json): **4,846 passed** across all
  14 unit/integration projects, zero failures or skips.
- [Aspire integration results](pr-56-aspire-results.json): **98 passed**, zero
  failures and [six existing health/readiness/degradation skips](pr-56-aspire-skips.json).
- Declaration, configuration, accessibility, dependency, commitlint and automated
  security/review checks passed. The scheduled performance lane was not selected.

[Merge integrity](pr-56-merged-integrity.json) confirms the merged source tree
matches the reviewed tree and both full, previously validated Conventional Commit
messages were preserved by the normal rebase merge. No administrator override,
reference reset, dependency sign-off or release dispatch was used.

[Independent local domain/Sample verification](parent-review-checks.json) passed
2,119/66 tests with zero skips and both warning-as-error Release builds. The
original three review layers completed and all seven verified findings were
corrected. [Integrity checks](parent-review-integrity.json) preserved the 180
approved Contracts/vector source files, exact candidate archive, historical matrix
section and ten clean exact root checkouts with no initialized nested submodules.

The first complete PR attempt hit the ten-minute overall Aspire job limit after
470 seconds of setup/build, with no final TRX. [Exact timeout evidence](pr-56-aspire-timeout.json)
is retained. The supported input correction retained the blocking policy and
immutable workflow pin. Focused workflow checks passed 48/48; after generating the
required solution/UI outputs, [parent Ci.Tests](parent-timeout-checks.json) passed
188/188 with zero skips. Initial missing-output failures are retained separately.
[Commitlint and delivery evidence](aspire-timeout-delivery.json) records the exact
correction. McpCli Core also [passed after the approved inventory was added](approved-inventory-core-tests.json):
659 passed and two existing platform skips.

The protected publisher also requires a successful **push CI at exact current
main**. [That run](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39452415638)
is running at merged SHA `fa708d1cdb71a8926c9ed82e2e18a3ce58fd52ef`; PR success
does not substitute for it.

On that same merged source,
`bash scripts/gitlink-rc-gate.sh --diff v1.5.0` still returns **1** for the
[nine exact dependency pointers](gitlink-signoff-proposal.md), unchanged from the
reviewed proposal. [The actual merged-main gate](merged-main-gitlink-rc-gate.json)
and [pending request](gitlink-signoff-request.json) retain the required owner
decision and input hashes. `RELEASE-CHECKLIST.md:14,19` requires a real release
owner's decision and owner/date fields. No answer to that request has arrived,
and no ledger approval was invented. The Contracts/vector/release-inventory
candidate approval is already recorded separately.

Protected publication, published-byte validation, the owning Builds central pin
and production enrollment remain open. These results preserve the existing
limits on live authorization, parity, erasure custody and legacy-host retirement.

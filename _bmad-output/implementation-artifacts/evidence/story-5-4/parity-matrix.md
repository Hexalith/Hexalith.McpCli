# Story 5.4 parity and safety matrix

This packet describes the CI disposable topology identified in `manifest.json`.
Parties Contracts 1.5.1 comes from repository commit
`8c88c27acd5ed3ee2d2f2b6f51f3432d536f2021`; the selected executable Parties
service comes from `d4415715b2517927655c538e6d41e05d71d4207e`.
Those revisions have separate roles. `upstream-test-audit.json` binds the source
files and test anchors at the enrolled revision; those upstream tests were not
rerun in this task. `live/` and `enrolled/` retain the hosted receipts.

The current approved migration inventory is 1.2.0. Existing A1 decisions accept
typed payloads and explicit IDs, separate activation calls, corrected Query
filtering/totals, shared result/error shapes and the C05 pre-read differences.
No new inventory amendment or owner verdict is asserted here. **A passing lane
is evidence for the cases it executed; each gap below still needs the owner's
disposition.**

## C01–C08

| Obligation | Evidence and exact scope | Disposition / remaining gap |
| --- | --- | --- |
| C01 erased-detail privacy | Enrolled-revision `PartySdkQueryHandlerTests.DetailHandlers_ErasedPartyReturnSameSafeMissingResultAsync:92`; method/file hash in `upstream-test-audit.json`. `get-party` loopback and live receipts prove the normal detail route through both heads. | Preserved by an upstream test at the enrolled revision. The normal live vector does not exercise erased detail; G02 records the selected-cohort erased delete/pre-read execution gap. |
| C02 filters, paging and totals | Enrolled-revision `PartySdkQueryHandlerTests.PublicQueries_FilterErasedAndMixedRowsBeforePagingAndReturnEffectiveTotalsAsync:2408`, `EnvelopePagingAloneGovernsAndLegacyPayloadPagingRemainsAvailableAsync:2468`, `PublicPaging_RejectsInvalidBoundsCursorAndOffsetBeforeReadAsync:2505` and `PublicContinuationRejectsScopeChangesBeforeAnotherReadAsync`; exact anchors in the audit. `list-parties`/`search-parties` loopback and live receipts bind the published routes. | The inventory's corrected filtering/totals and explicit envelope paging are approved changes. Broader filter/cursor cases are upstream-test evidence, not a claim that the small live vectors execute them all. |
| C03 create aliases, IDs and bounds | `create-party` both-head loopback and single-submission live receipts. Enrolled-revision `PartyDomainProcessorValidationTests.ProcessAsync_EveryExposedStringIsBoundedBeforeStateAccess:1334`, `CompositeValidatorsAcceptExactRawStringAndTotalBoundaries:1419`, `CompositeValidatorsCountEveryRepeatedIdAndKeepTheOperationCap:1440`, plus null-collection/item rejection at `:1241`. | Typed nested payloads and explicit IDs are approved changes. G05 identifies the raw-versus-trimmed bound difference for an explicit owner disposition. |
| C04 update/merge, removals, route IDs and separate activation | `update-party`, `reactivate-party` and `deactivate-party` loopback/live receipts. Enrolled-revision `CompositeUpdatesAcceptEachSupportedListAsTheOnlyChange:1194`, `ProcessAsync_InvalidGatewayCompositeRejectsBeforeProtectedStateAccess:1117` and `ProcessAsync_EmptyContactUpdateHasOnlyTheEntryFailureBeforeProtectedStateAccess:1215`. `InvalidGatewayComposites` includes a PartyId-only update. | Explicit patch construction and separate non-atomic calls are approved changes. The same bounded-input difference is G05. No generic head performs a legacy pre-read or merges a patch. |
| C05 safe soft deactivation | `deactivate-party` live receipt observes active, inactive and repeated-inactive persisted state. The independent shared-head boundary submits one missing-target Command per head and two concurrent CLI Commands with distinct message IDs, then checks authorized state and exactly one persisted deactivation event. Enrolled-revision `RepeatedSoftDeactivationDoesNotEraseOrEmitAnotherEvent:1405` pins unchanged erasure state and no extra events. | Missing/pre-read error-shape differences are approved by 1.2.0. G01 remains the known rejection-only-stream defect. G02 covers forced stale projections and selected-cohort erased/restricted delete/pre-read branches that these live cases do not execute. No caller-key deduplication guarantee is inferred. |
| C06 public error privacy and result shape | McpCli `PartiesMigrationCompatibilityTests.GatewayFailureMarkersStayOutOfBothHeadsAsync:56` covers eight failure/call-kind cases, complete documents and every channel; `BoundaryProcessHarnessTests.AcceptedCommandsPreserveCompleteGatewayResultsAsync` pins optional business results. Authorized live reads and the deactivation event proof preserve soft-deactivation intent. | Shared document shapes are an approved change. Generic mapping intentionally copies Gateway detail/title and selected metadata. G03 keeps upstream Query-error sanitization unresolved; ignored fields/transport exceptions being safe does not prove those copied fields are safe. |
| C07 supported legacy identifiers | McpCli `PartiesMigrationCompatibilityTests.LegacyRootPartyIdsFailBeforeTheGatewayInBothHeadsAsync:124` and `LegacyChildIdsAndSupportSafeRootReachTheGatewayUnchangedAsync:169`; complete both-head documents and exact captured payloads. | Approved 1.1.0/1.2.0 resolution: unsafe root GUID representations cannot identify EventStore streams, support-safe String roots and child identifiers are preserved without conversion. No validator changed. |
| C08 credentials and tenant authority | McpCli `PartiesRetirementSafetyTests` covers 401/403, zero-call local tenant negatives, disabled MCP override and F7. The live boundary pins structured and empty-body 401 transport documents, compares absent-token documents directly between heads, and covers absent/forged credentials, tenant-A-only and no-grant identities against tenant B, session changes and permitted MCP per-call selection, with authorized before/after business-state reads. | Signed-claim authorization is exercised; this does not prove persisted Parties membership. G04 tracks persisted actor attribution; G06 tracks mixed-profile identity outside the isolated profile used by these cases. F7 acceptance is separately bound in `f7-acceptance.json`; item 9 remains open. |

## Seven behavior variants

| Variant | Evidence / source | Disposition |
| --- | --- | --- |
| Redaction | C06's full-channel McpCli tests, shared redactor/scanner code hashes and this packet's scan receipt. | Generic exception/ignored-field privacy is covered. Copied downstream detail/title is G03. A clean packet scan establishes evidence hygiene, not arbitrary application-error privacy. |
| Task context | Complete legacy `src/Hexalith.Parties.Mcp/` C# tree at `493730941329d1bca3b4f6b2f6a67ffe305c2443`, with file hashes and a no-match source audit in `upstream-test-audit.json`. | **Absent at source.** No legacy task-context behavior is invented. Future context-dependent capabilities remain outside this migration. |
| Actor attribution | Legacy `PartiesMcpRequestContext.cs:35` chooses claims/raw user headers; `McpContextForwardingHandler.cs:16` adds `X-User-Id`. McpCli `CliMcpQueryParityTests.IdentityMismatchFailsInBothHeadsBeforeTheGatewayAsync:37` refuses undeclared `ActorId`; live boundary uses signed principals. | The approved operator-session mode replaces forwarded per-user HTTP context. G04 remains: the packet does not assert the persisted event/audit actor equals that configured principal. |
| Paging | C02's enrolled-revision tests, approved list/search loopback requests and both-head live Query observations. | Explicit list/search selection and corrected totals are approved changes. Tests at the enrolled revision cover bounds and continuation scope, beyond the small live vectors. |
| Freshness | Same complete legacy tree/source audit; legacy tools expose no freshness request or guarantee. | **Absent at source.** The target may return freshness metadata; removing observation-time freshness only from before/after business-state comparisons does not claim a legacy guarantee. |
| Token/output budget | Same complete legacy source audit; `Tools/PartiesMcpTools.cs:566` limits input strings to 512/4096. | **Absent at source.** Input bounds are C03/C04; they establish no output-token budget. No output-budget adapter is added. |
| Idempotency | Enrolled-revision repeated-deactivation test; approved repeated-inactive live vector; concurrent boundary with distinct message IDs and one persisted deactivation event. | Safe business NoOp is demonstrated for the created party. Legacy inactive pre-read and generic direct submission are documented C05 changes. There is no executor retry or caller-key deduplication claim. G01/G02 retain the remaining lifecycle cases. |

## Restricted inventories and public surface

EventStore Admin and technical-tool rows: **absent; name similarity proves
nothing**. They have no approved replacement claim in this packet. Exact
production discovery is bound by `live/head-catalog.json` and the unchanged
release-inventory coverage gate.

`PartiesRetirementSafetyTests.RestrictedNamesCannotBeDiscoveredOrAuthorizedByConfirmAsync:150`
reads every inventoried Admin name and all six excluded Tenants targets,
requires their absence from CLI/MCP discovery and pins whole
`unknown_operation` errors for both call kinds, with and without `confirm: true`
in payload/MCP arguments and zero Gateway calls. CLI `--confirm` is pinned as
`invalid_arguments`. MCP currently ignores extra call arguments; that behavior
confers no authority and its future envelope validation belongs to
`epic-3-retro-item-2`.

## Gaps for the Parties owner

Each gap must either remain blocking with its named ledger owner or be covered
by a new exact-byte, owner-approved inventory 1.3.0 amendment. This packet makes
neither decision. Suggested verdict until that decision is **retirement-blocked**.

| Gap | Missing evidence or known difference | Owner / ledger |
| --- | --- | --- |
| G01 | A second non-create Command can operate on a never-created party after a rejection-only stream has been rehydrated. The boundary uses separate first-missing targets and does not claim the repeated-missing case is safe. | Parties maintainer; already tracked in `deferred-work.md:556`. |
| G02 | The selected cohort has no forced-stale-projection delete case or executed erased/processing-restricted delete/pre-read branch. The concurrency case proves an aggregate repeat, not a forced stale read. The 1.2.0 branch oracles remain binding. | Parties maintainer and EventStore Gateway maintainer; `deferred-work.md:853`. |
| G03 | Query errors may copy module-controlled detail/title or selected metadata; no selected-cohort downstream personal-data/secret injection proves these public fields are sanitized. C06's safe ignored fields do not close that upstream requirement. | EventStore Gateway maintainer, with Parties maintainer for its Query text; already tracked under Story 5.3 in `deferred-work.md:824`. |
| G04 | Signed-claim tenant authorization and rejection of undeclared ActorId do not prove persisted command-event/audit actor attribution. | Parties maintainer and EventStore Gateway maintainer; `deferred-work.md:859`. |
| G05 | Published validators count raw 512/4096 UTF-16 input, whitespace and repeated IDs; legacy wrapper limits count trimmed top-level strings. The upstream tests prove the policy but do not themselves approve this stricter behavioral difference. | Parties maintainer; `deferred-work.md:865` for explicit inventory disposition. |
| G06 | Flag/environment Gateway credentials may still combine with another selected profile's tenant/actor/override/extension settings. The live boundary isolates its profile and does not exercise that operator configuration. Gateway authorization remains independent. | McpCli maintainer; already tracked in `deferred-work.md:833`. |

Story 5.5 owns retirement, and the separate release-acceptance gate remains
binding. Neither a successful Story 5.4 verdict nor this packet publishes or
retires a package.

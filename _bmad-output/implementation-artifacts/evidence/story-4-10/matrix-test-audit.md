# Matrix test audit after review patches

The current concrete SDK handler class run passed **738/738**, with zero skips,
retained in [current XML](review-query-tests.xml). After the final metadata and
projection absence assertions, the malformed-payload method alone passed
**18/18** again. Generic C# inventory/description coverage was not edited in this
patch pass; its earlier **101/101** result is historical and retained in
[the first review archive](review-pass-1/coverage-tests.xml).

| Frozen matrix row | Executed passing coverage |
| --- | --- |
| Detail | `DetailHandler_ReadsCanonicalStoreAndSurfacesPersistedFreshnessAsync` (1); `MissingDetailExportAndIndexModelsFailClosedAsActorNotFoundAsync` (1); `DetailHandlers_ErasedPartyReturnSameSafeMissingResultAsync` (1) |
| Identity | `DetailHandlers_PreserveSupportedIdentifiersAndOptionalEntityFallbackAsync` (216); `DetailHandler_AggregateAndEntityMismatchFailsClosedBeforeStoreReadAsync` (12); `PublicIndexRoutes_RetainOptionalEntityFallbackAndSdkDispatchAsync` (4); `PublicIndexRoutes_RejectMismatchedIdentityBeforeReadAsync` (2) |
| Filters | `PublicQueries_FilterErasedAndMixedRowsBeforePagingAndReturnEffectiveTotalsAsync` (2); `PublicQueryPayloads_RejectAmbiguousAliasesAndInvalidFiltersBeforeReadAsync` (18); `SearchCaseFilterIsRejectedBeforeReadAsync` (1); `SearchProviderNeverReceivesErasedEntriesAsync` (1) |
| Paging | `PublicQueries_FilterErasedAndMixedRowsBeforePagingAndReturnEffectiveTotalsAsync` (2); `PublicPaging_RejectsInvalidBoundsCursorAndOffsetBeforeReadAsync` (8); `PublicContinuationRejectsScopeChangesBeforeAnotherReadAsync` (12); `EnvelopePagingAloneGovernsAndLegacyPayloadPagingRemainsAvailableAsync` (4) |
| Compatibility | `EnvelopePagingAloneGovernsAndLegacyPayloadPagingRemainsAvailableAsync` (4) |
| Coverage (historical, unchanged C# gate) | `RejectsPublicDiscoveryMismatch` (7); `RejectsWrongClrTypeDespiteMatchingPublicNames` (1); `RejectsInvalidScope` (24); `MissingInventoryCannotSilentlySkipAnEnrolledModule` (1); `SyntheticFixtureCannotAuthorizeProductionEnrollment` (1) |

The two public-route mixed-row cases now contain four extra timestamp rows, each
excluded only by one inclusive date bound. Expected effective totals, IDs and
pages remain unchanged. The malformed-payload cases include high/low unpaired
surrogates in both property names and values for both index routes, asserting
invalid-envelope before reads with absent document, metadata and projection type.

The Python patch suite passes 20 regressions, and the temporary packaged process
fixture passes nonempty enrollment through complete replay plus deliberate
semantic-assertion rejection. The final Parties artifact passes all seven vectors
through both heads, including list/search identity, type and active status. The
pending inventory smoke retains its expected ten approval findings and failed
receipt. None of this authorizes publication or production enrollment.

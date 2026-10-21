# Matrix test audit

Every listed case exists in the retained xUnit XML, ran, passed and was not skipped.
The focused domain run passed 758/758; generic inventory/description coverage passed 101/101.

| Frozen matrix row | Executed passing coverage |
| --- | --- |
| Detail | `DetailHandler_ReadsCanonicalStoreAndSurfacesPersistedFreshnessAsync` (1); `MissingDetailExportAndIndexModelsFailClosedAsActorNotFoundAsync` (1); `DetailHandlers_ErasedPartyReturnSameSafeMissingResultAsync` (1) |
| Identity | `DetailHandlers_PreserveSupportedIdentifiersAndOptionalEntityFallbackAsync` (216); `DetailHandler_AggregateAndEntityMismatchFailsClosedBeforeStoreReadAsync` (12); `PublicIndexRoutes_RetainOptionalEntityFallbackAndSdkDispatchAsync` (4); `PublicIndexRoutes_RejectMismatchedIdentityBeforeReadAsync` (2) |
| Filters | `PublicQueries_FilterErasedAndMixedRowsBeforePagingAndReturnEffectiveTotalsAsync` (2); `PublicQueryPayloads_RejectAmbiguousAliasesAndInvalidFiltersBeforeReadAsync` (10); `SearchCaseFilterIsRejectedBeforeReadAsync` (1); `SearchProviderNeverReceivesErasedEntriesAsync` (1) |
| Paging | `PublicQueries_FilterErasedAndMixedRowsBeforePagingAndReturnEffectiveTotalsAsync` (2); `PublicPaging_RejectsInvalidBoundsCursorAndOffsetBeforeReadAsync` (8); `PublicContinuationRejectsScopeChangesBeforeAnotherReadAsync` (12); `EnvelopePagingAloneGovernsAndLegacyPayloadPagingRemainsAvailableAsync` (4) |
| Compatibility | `EnvelopePagingAloneGovernsAndLegacyPayloadPagingRemainsAvailableAsync` (4) |
| Coverage | `RejectsPublicDiscoveryMismatch` (7); `RejectsWrongClrTypeDespiteMatchingPublicNames` (1); `RejectsInvalidScope` (24); `MissingInventoryCannotSilentlySkipAnEnrolledModule` (1); `SyntheticFixtureCannotAuthorizeProductionEnrollment` (1) |

The SDK handler tests call the concrete handler classes and assert canonical read-model access and rejection before reads. Actor names remain compatibility metadata. This is local handler evidence, not live Gateway authorization or persisted command effects.

The approval-negative smoke runs the shared checker against `parties-candidate.json`; exit 1 contains ten explicit pending/scope-only approval findings. Original Query vector postconditions were retained, and all seven vectors passed both heads.

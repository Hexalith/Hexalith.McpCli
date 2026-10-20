# Story 4.9 refreshed matrix audit

Root checked the implementation diff, current validators and tests, seventeen log
hashes, source/vector/verifier manifests, artifact identity and Catalog delta.
The executed validation class passed 126/126 with zero skipped or unrun cases.
Required full suites passed 2013/2013 Parties, 315/315 Server and 201/201
Contracts. Exact commands and log hashes are in
[review-pass-2-final-checks.json](../review-pass-2-final-checks.json); independent integrity
checks are in [root-audit.json](root-audit.json).

| Approved matrix row | Executed coverage |
| --- | --- |
| Routing | `ModuleDeclaresOnlyTheFourApprovedCommandsAndExistingRouting` and all four scratch CLI/MCP vector runs pin full CLR wire names, aggregate routing, tenant and complete Gateway requests. Declaration tests also pin null correlation, idempotency, actor and serializer-provider bindings. |
| Bounds | `CompositeValidatorsAcceptExactRawStringAndTotalBoundaries`, `ProcessAsync_EveryExposedStringIsBoundedBeforeStateAccess` and `CompositeValidatorsCountEveryRepeatedIdAndKeepTheOperationCap` exercise raw per-field/total boundaries, repeated IDs, operation caps and rejection before state unprotection. |
| Child IDs | `ProcessAsync_InvalidGatewayCompositeRejectsBeforeProtectedStateAccess` covers create-contact and update-identifier root/child mismatches with rejection events and no protected state access. |
| Nulls | Fourteen `ProcessAsync_NullCompositeCollectionsAndItemsHaveExactFailuresBeforeProtectedStateAccess` cases pin complete failure lists for every null list/item, with no protected state access. All four `DeclaredCommandExamplesPassProductionDeserializationAndRegisteredValidation` cases pass production JSON options and registered validators; the composites explicitly retain empty omitted lists. |
| Empty update | The invalid-composite theory rejects a root-only update; `ProcessAsync_EmptyContactUpdateHasOnlyTheEntryFailureBeforeProtectedStateAccess` pins the single entry failure and no protected state access. Positive contact-field, organization-only and three sole-list-update cases pass. |
| Repeat deactivation | `RepeatedSoftDeactivationDoesNotEraseOrEmitAnotherEvent` asserts repeated inactive deactivation emits no events, preserves equivalent state and keeps erasure active. |

The final full suites and isolated scratch package verification include the
corrected lifecycle descriptions. Every other Catalog field and all
vector bytes match the earlier approved artifact. Temporary routing copies omit
unavailable Query postconditions; this audit does not claim live Query or
persisted business-effect proof, which remains in Stories 4.10, 4.11 and 4.13.

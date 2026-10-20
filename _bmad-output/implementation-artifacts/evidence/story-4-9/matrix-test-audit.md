# Story 4.9 matrix audit

Every approved matrix row has executed passing evidence. The final full solution
build has zero warnings/errors; Parties.Tests 2004/2004, Server.Tests 315/315 and
Contracts.Tests 201/201 pass with zero failures or skips. Exact commands and
outputs are in `accepted-checks.json`. The focused processor class also passes
119/119 (`final-domain-validation.txt`).

| Matrix row | Executed protection and result |
| --- | --- |
| Routing | `ModuleDeclaresOnlyTheFourApprovedCommandsAndExistingRouting` plus scratch CLI/MCP smoke for all four Commands: exact CLR wire types, root aggregate and envelope tenant/request bodies match. `final-scratch.txt`. |
| Bounds | `CompositeValidatorsAcceptExactRawStringAndTotalBoundaries` accepts 512/4096 and rejects 4097; `ProcessAsync_EveryExposedStringIsBoundedBeforeStateAccess` rejects every over-limit string slot; `CompositeValidatorsCountEveryRepeatedIdAndKeepTheOperationCap` covers repeated-ID totals and operation boundaries. All pass in Parties.Tests. |
| Child IDs | `InvalidGatewayComposites` exercises create-contact and update-identifier root/child mismatches through `ProcessAsync_InvalidGatewayCompositeRejectsBeforeProtectedStateAccess`; exact existing rejection code required, no payload echo, no state unprotection. Pass. |
| Nulls | The same processor matrix rejects every explicit null collection and null item (including removals); default collections pass valid boundary/processor cases. Pass. |
| Empty update | The processor matrix rejects root-only and contact-without-mutable-value updates before protected state access. Positive single-field contact updates (including empty string and false), numeric enum rejection and organization-only replacement all pass. |
| Repeat deactivation | `RepeatedSoftDeactivationDoesNotEraseOrEmitAnotherEvent` applies inactive state, submits twice, requires no events, byte-equivalent state and unchanged active erasure status. Pass. |

Scratch smoke omits only unavailable Query postconditions in temporary copies;
original vectors retain them. This audit does not claim persistent semantic
Query execution. That evidence remains assigned to Stories 4.10, 4.11 and 4.13.

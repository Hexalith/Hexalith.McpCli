# Description review fixes

The first fresh-context review returned **FAIL** for the initial scratch artifact
retained at `artifacts/round-1/Hexalith.Parties.Contracts.0.0.0-story49.nupkg`.
The reviewed medium findings and low notes have been addressed in the Contracts
attributes and in README/API documentation. A fresh independent verdict for the
replacement artifact remains pending in `description-review.json`.

| Finding | Resolution and source evidence in Parties |
| --- | --- |
| Update description implied editing business identifier records | It now explicitly says add/remove business identifiers, separately from add/update/remove contact channels. `UpdatePartyComposite.cs` exposes only `AddIdentifiers` and `RemoveIdentifierIds`; `src/Hexalith.Parties/Domain/PartyAggregate.cs:570` processes additions/removals. |
| Detail/type compatibility and conversion were unclear | Create descriptions state matching details are required, with an extra opposite-kind object accepted/stored without overriding Type (`src/Hexalith.Parties/Domain/PartyAggregate.cs:77`, `:136`). Update descriptions state complete replacement for the existing matching type only; another kind rejects the entire update and Type cannot change (`src/Hexalith.Parties/Domain/PartyAggregate.cs:452`, `:462`, `:486`, `:497`). No new type guard was added. |
| Nullable contact Value and empty updates were unclear | Update-list descriptions now require at least one non-null Type/Value/IsPreferred. Value descriptions distinguish omitted/null preservation from verbatim replacement, including empty-string clearing (`src/Hexalith.Parties.Contracts/State/PartyState.cs:248`, `:249`, `:250`). The shared validator's existing non-null change guard remains. |
| PostalAddress/SocialMedia representation was unspecified | Contact Value descriptions explicitly require raw strings, including these kinds, with no defined structured encoding. `docs/data-models.md:72` identifies typed VOs as reserved/not wired; `ContactChannel.cs` and `AddContactChannel.cs` store `string Value`. No new format was invented. |
| Preference scope/behavior was unclear | Add defaults to false; true selects within channel type and clears other same-type preferences, with later processed true additions winning. Update omission/null preserves, false clears only that channel, and true reconciles when becoming preferred or changing type. The description advises supplying true with a type move. See `src/Hexalith.Parties/Domain/PartyAggregate.cs:528`, `:554`; `src/Hexalith.Parties.Contracts/State/PartyState.cs:261`. |
| IsNaturalPerson meaning/default/create/update behavior was unclear | The description defines individual-vs-legal-entity classification, default false. Create initializes party classification (`src/Hexalith.Parties.Contracts/State/PartyState.cs:133`). Replacing organization details changes the nested value (`src/Hexalith.Parties.Contracts/State/PartyState.cs:221`) without updating the separate established classification (`src/Hexalith.Parties.Contracts/State/PartyState.cs:300` changes it only for IsNaturalPersonChanged). This existing limitation is documented accurately; no classification-change operation was exposed or domain behavior changed. |
| Lifecycle restrictions were vague | Reactivation/deactivation now explicitly require an existing unrestricted party and current erasure status Active; already-current status is a no-op only after these guards. See `src/Hexalith.Parties/Domain/PartyAggregate.cs:867`, `:892`, `:1547`, `:1560`. Using current status permits a previously cancelled erasure that has returned to Active. |
| Catalog-only callers lacked bounds | Both composite command descriptions now state raw 512-per-string / 4096-total UTF-16 limits, whitespace/repeated-ID counting, the tighter 128-character identifier rule and default configured operation cap 100. |

All notes were settled from existing source or tracked documentation. The
IsNaturalPerson split above is preserved existing behavior, not a claim that
classification changes are supported through these four commands.

## Added verification

`PartyDomainProcessorValidationTests.ProcessAsync_UndefinedContactUpdateTypeRejectsBeforeProtectedStateAccess`
sends numeric enum value 999. It asserts the exact sole failure
`UpdateContactChannels[0].Type` / `EnumValidator`, one rejection event and no
snapshot/event unprotection. Removing the nullable Type enum guard makes this
case fail.

`CompositeContactUpdatesAcceptOneNonNullMutableValue` covers Type-only,
Value-only, empty-string Value and false-only preference updates. Each passes
the shared validator, produces a successful composite contact update, and
applies the exact expected field while preserving omitted fields.

After a focused restore corrected stale/mismatched referenced assets, the
serialized Release Parties.Tests build passed with zero warnings/errors. The
complete validation class passed **118** cases; the declaration class passed
**2** cases after its focused Release rebuild. Logs are in
`review-parties-restore.txt`, `review-parties-build.txt`,
`review-domain-tests.txt`, `review-contracts-build.txt` and
`review-decoration-tests.txt`. The initial stale-assets failure is retained as
`review-stale-assets-build.txt`; no source, dependency or build rule was weakened
to resolve it. The earlier complete build and project-test results remain
recorded separately in `verification.md`.

## Command-routing smoke scope

`verify-scratch.py` now invokes the existing shared `run_loopback.py` before
cleaning its temporary host/cache. It derives temporary copies of all four
original vectors by setting **only** `postconditions` to `[]`; original vector
hashes are unchanged. Prerequisite writes, invocation payloads, envelope tenant,
full CLR wire names, expected complete Gateway bodies and all Command assertions
are retained. The shared runner executes both CLI and MCP stdio heads and checks
discovery, requests/documents and validation/Gateway-error parity.

This proves command-routing smoke for the exact local artifact and tenant-a;
it does not prove Query routing, persistence, lifecycle effects or downstream
cross-tenant authorization. Full original vectors, Query postconditions and
semantic effects remain for Stories 4.10/4.11/4.13. Results and exact executed
artifact identity are in `scratch-reproduction.txt`, `catalog-checks.json` and
`artifact.sha512`.

The concurrent AppHost, publish, deployment, CI and topology edits were preserved.
No McpCli runtime, production enrollment, restored-assets or references source
changes were made.

Final artifact routing smoke passed all four Commands through both heads (1, 3, 3 and 2 reset Gateway steps respectively); full original vector validation passed. Production restored assets and original vector hashes remained unchanged.

## Direct corrections after PASS WITH NOTES

The independent rereview of the package now retained under `artifacts/round-2/`
returned **PASS WITH NOTES**. This final pass changed description text only:

1. Named `PartyId`, `ContactChannelId`, `IdentifierId` and removal ID entries as
   the fields with the tighter 128-character bound; business identifier `Value`
   strings explicitly retain the 512 UTF-16-unit bound.
2. Stated that null collections and null entries reject, while omitted lists
   retain empty defaults.
3. Stated exact cap counting: create is 1 plus both list lengths; update counts
   each non-null details object plus every item across the five operation lists.
4. Stated removal overlap rejection for channel IDs also added/updated and
   identifier IDs also added. The add-channel description separately preserves
   the existing-ID add/update behavior: skip the addition, then apply the update.
   It does not claim every add/update overlap is rejected.

Source remains `CompositeInputPolicy.cs`, both shared composite validators,
`PartyAggregate.cs:33`, `:207`, `:322`, `:338`, `:365` and `:512`. No validation,
domain, routing, example, payload/schema shape or original vector content changed.
`description-delta-round-2.json` records every exact old/new Catalog description
and asserts the Catalogs are identical after description text is removed.

Only the necessary Contracts/declaration build and two declaration tests were
rerun, followed by the existing artifact/Catalog/strict/lint/CLI+MCP command-routing
verifier. Logs: `finalwording-contracts-build.txt`,
`finalwording-decoration-tests.txt` and `scratch-reproduction.txt`. The original
reviewed package and Catalog remain available under `artifacts/round-2/`.

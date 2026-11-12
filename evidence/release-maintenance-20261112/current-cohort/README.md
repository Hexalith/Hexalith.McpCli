# Current package qualification

This task-specific cohort updates the existing enrolled operations to EventStore
4.2.0, Parties 3.1.1, Tenants 7.0.7 and McpCli Abstractions 2.0.1. The instruction
bypasses human validation; automated artifact, source, inventory, vector and native
runtime gates remain required. `authorization.json` records that instruction,
the preserved historical input digests and the absence of an acceptance claim.

The published Parties 3.1.1 source
`84e3df796ac977041a21ec7bd8e5789bdc44241a` removes `ProjectionActorType` from
GetParty/ListParties/SearchParties annotations. Its
`PartiesCatalogDeclarations.cs` retains the same PartyDetail/PartyIndex/PartySearch
wire identifiers, domain-service query handlers, party-detail/party-index read
models and exact actor compatibility aliases. EventStore 4.1 and 4.2
`RouteCatalogQuerySelectorPolicy.cs` both accept an omitted actor hint or the
owner's exact alias for those same domain-service projection routes. This does
not introduce an operation or replace a receiver. All 21 operation descriptions
and schemas were independently compared before enrollment; they remain equal.

The current vectors change package versions and omit only these exact deprecated
hints. Every payload, entity, tenant, query/projection identifier, asserted result,
mutation safety assertion and expected error remains equal to its historical
counterpart. Separate current plans bind the new exact bytes. The preservation,
allowed-difference and crossed-cohort refusal checks run in `test_current_cohort.py`.
The original vectors, plans, inventories and native manifest stay at their
original paths with their original approval and acceptance records.

`native-runtime-current.json` binds exact signed public package archives and
repository source commits. Each selected archive was downloaded directly from
NuGet and verified with `dotnet nuget verify --all`. Native selection still
refuses dirty, linked, wrong-repository or mismatched local sources, unknown or
crossed package cohorts, body/hash drift and competing nested catalogs. Only
real disposable GitHub-hosted CI may select a different exact native source.

Testing.Integration 4.2 replaced its AppHost-owning generic fixture with a
Platform descriptor consumer. This suite already runs inside its independent
isolated topology wrapper, so its test-only `IsolatedTopologyLifecycle` retains
AppHost ownership through Aspire's public testing API. Existing isolation and
missing-prerequisite refusals, the bounded Docker health probe, private signing arguments, discovered endpoint
selection and liveness gates remain in place. Startup and lock acquisition are
bounded by six minutes. Independent disposal attempts every client, application,
builder and lock even when another owner fails. Cleanup controls and the real
native lane qualify this adapter; compilation alone is not runtime acceptance.

The actual current direct reader also generated a catalog with SDK 4.2 and the
compiled Parties 3.1.1 owner/adapter against an online audit covering 224 packages. Its request contains generation, instance, gateway and actual owner inputs;
it does not request a named public image authority. The unchanged direct SDK
fixture path uses `AddEventStoreDevelopmentRouteCatalog`. No Platform image
Bind/Compose API or image guard changes are involved. `direct-reader-proof.json`
records this component result and explicitly does not assert running-service or
full native acceptance. The final hosted lane remains required.

Official NuGet indices were checked for the direct production, module and approved
test dependency IDs. Restored stable dependencies use the latest stable versions.
The existing Dapr toolkit prerelease is the latest 13.6 family; the newer 17 beta
requires Aspire.Hosting 17.1 preview, outside the stable 13.6 AppHost cohort.
The unused Verify.XunitV3 allowance does not represent a restored dependency.

The current isolated runtime profile separately binds Aspire CLI 13.6.5 and
Dapr CLI/runtime 1.19.1 official archive and executable SHA-256 values. The three
Dapr control-plane executables were independently extracted from the exact
`daprio/dapr` OCI digest and hashed; the four-binary current manifest retains the
existing Redis binary. `runtime-profile-current.json` binds that manifest.
Preparation and every source-provenance recheck authenticate the profile and
installed executable bytes, so a forged version string cannot admit a different
binary. The original `binaries.json`, native manifest and historical receipts
remain byte-identical. Local full lifecycle results are recorded only after the
actual isolated lane, independent smoke and authorization-boundary cases finish.

The current test hosts and their three isolated resource processes use the
measured .NET 11.0.0 shared runtime; their target frameworks and immutable owner
exports remain net10.0. Actual-process checks record JsonElement from that trusted
shared directory, while every preparation/recheck closes resource roll-forward
to the exact highest installed Core and ASP.NET runtime. This preserves the SDK's
existing operation-schema digest equality across metadata and running owners.
`runtime-1191` retains the primary-source runtime-selection link, actual diagnostic
identity captures, operation-schema comparison and an independent boundary result;
those component results grant no complete native acceptance.

`native-61d4913-runtime1191-net11` seals the genuine complete local candidate
qualification: all 21 live vectors and both independent boundary/smoke cases pass,
with no failures or skips and 23 distinct isolated cleanup receipts. It retains
all per-vector semantic results and test XML. Its exact source61d4913 used Builds840
and Platformd421, so it grants no final-pin hosted CI, staged-pair, release or image
authority. The final released Builds and qualified Platform sources still require
their exact committed CI. Actual service process measurements independently bind
all three launched services to trusted shared .NET 11 CoreLib and JSON images.

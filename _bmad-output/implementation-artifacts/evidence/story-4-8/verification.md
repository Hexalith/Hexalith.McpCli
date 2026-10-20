# Story 4.8 verification

Date: 2026-10-19, evidence regenerated 2026-10-20. Tenants work tree on `main`. McpCli at HEAD
`742f5b6ead66937f62025b73d77452e0f8126658`; between `447085c` and this HEAD only the README and a module
manifest changed, not `src/` or `tools/conformance-vectors/`. Credentials are excluded.

## Source state

- Tenants: the work began on `43786ea8`. A concurrent process in that work tree
  committed and pushed commit `6b62b6b3` ("feat(contracts): add McpCli operation
  metadata", 17:57). It carries a mid-story snapshot of the Contracts decoration,
  build routing and governance test. The assistant did not create that commit.
  The rest is uncommitted in the work tree: handlers, tests, vectors, docs, and the
  description fixes from NFR-8 rounds 1 and 2 and from the follow-up review
  (next-page cursor wording on the four paged reads, "not used" paging
  arguments on get-tenant).
- McpCli: only this evidence directory and the spec's notes and checklist changed.
  No source or `references/` change was made.

## Commands and results

| Check | Result |
| --- | --- |
| `dotnet restore Hexalith.Tenants.slnx && dotnet build Hexalith.Tenants.slnx --no-restore -c Release -warnaserror` | Build succeeded, 0 warnings, 0 errors |
| `dotnet test tests/Hexalith.Tenants.Contracts.Tests --no-build -c Release` | Passed, 558 tests |
| `dotnet test tests/Hexalith.Tenants.Server.Tests --no-build -c Release` | Passed, 1417 tests |
| Client.Tests, Testing.Tests, Sample.Tests, UI.Tests (`--no-build -c Release`) | Passed: 50, 182, 40, 6266 |
| IntegrationTests (`--no-build -c Release`), 4 runs | 1 to 3 failures per run, none caused by this change. One failure is deterministic and pre-existing: `TenantsApiStructuralTests.TenantsSources_DelegateDaprRoutingHeaderOwnershipToThePlatformHandlerOnly` flags `src/Hexalith.Tenants/Authorization/TenantOwnerSourceGateway.cs`, a file untouched since `bbd95f95` (2026-10-17). The others are intermittent live Aspire/Redis topology tests (`AspireTopologyTests.Aha_moment_demo_revokes_sample_access_from_tenant_events`, a 60 s projection wait); one run had only the structural failure. |
| Source mode: `dotnet build src/Hexalith.Tenants.Contracts -c Debug -p:UseHexalithProjectReferences=true --artifacts-path <scratch>` | Built `Hexalith.McpCli.Abstractions` and its analyzer from `references/Hexalith.McpCli`; the submodule stayed clean |
| Package mode against nuget.org `Hexalith.McpCli.Abstractions` 1.0.0, isolated `NUGET_PACKAGES` | Build succeeded with the published analyzer and no `MCPCLI001` |
| Pack the five release packages at 0.0.0-story48, then `python3 scripts/validate-nuget-packages.py <dir>` | Validated 5 packages. The Contracts dependencies are ByteAether.Ulid, Hexalith.Commons.UniqueIds, Hexalith.EventStore.Contracts and Hexalith.McpCli.Abstractions |
| Follow-up review fixes (2026-10-20), focused runs only | `McpCliDecorationTests` now asserts the `[Description]` attribute exists before its text. Removing `ListTenantsQuery.Cursor`'s attribute, or changing `CreateTenant.Name` to a parameter-targeted `[Description]`, each fails the theory (sources restored); class 51/51 pass. The new `EnvelopePagingQueryHandlerTests.DefaultPageDocumentCursorContinuesAsEnvelopeCursorAsync` proves, for all five paged reads, that a default-size page's document `cursor` continues the sequence when sent as `Paging.Cursor`; class 48/48 pass. The full-suite counts above predate these 5 added cases. |
| Mutation checks on the 13 new handler guards (offset, envelope path, metadata, metadata merge, audit paging skip, CLR `From`, date conflict, CLR `Category`, category conflict, payload target, entity conflict, Gateway-default entity, non-string user) | Each mutation failed between 1 and 27 new Server tests; the sources were restored afterwards |
| `dotnet pack src/Hexalith.Tenants.Contracts -c Release -p:Version=0.0.0-story48` into the scratchpad | Artifact `sha512-Od2hpUmNTlE9Zd6DV4LEQ+IdFIkDhp1X9Oo0M5EZ25ALSMMC0Udb3URXXV3bDLA/8KnQT658QjAQ9MdU+lcnnA==` |
| Scratch host `list_operations tenants` (`operations tenants --strict`) | 14 operations, exit 0, empty stderr (`strict.txt`, `catalog-dump.json`) |
| `describe <op> --lint --strict` for all 14 | Only `payload_paging_member`, on `Cursor`/`PageSize` of the four paged reads (`lint.txt`) |
| `validate.py ... --operations-file operations.json tests/conformance-vectors/mcpcli-v1/*.json` | `Validated 14 vector(s)`, exit 0. Negative controls (a missing, an extra and a duplicate vector, a wrong version) each exit 1 (`vector-validation.txt`) |
| `run_loopback.py` (CLI and MCP stdio, separate processes, reset scripted Gateway, restored-package hash check) | 14 PASS, exit 0 (`loopback.txt`) |
| NFR-8 review by a fresh-context reviewer given only the Catalog dump | Three rounds. Rounds 1 and 2 were PASS WITH NOTES and their accurate notes were applied. Round 3 was PASS WITH NOTES with no blocking finding; a later follow-up review changed wording only. Its remaining notes are for the maintainer (`nfr8-review.md`). |

## Scratch host

The host is a copy of `tests/Hexalith.McpCli.ConformanceHost/Program.cs` with a
project file in the session scratchpad. It references
`mcpcli/src/Hexalith.McpCli/Hexalith.McpCli.csproj` and
`PackageReference Hexalith.Tenants.Contracts HexalithContracts="true"`, and
imports `ModuleAssemblyManifest.targets`. It was built with:

```sh
NUGET_PACKAGES=<scratch>/packages48 dotnet build Tenants.ScratchHost.csproj -c Release \
  --artifacts-path <scratch>/artifacts48 -p:HexalithEventStoreVersion=3.125.1 \
  -p:HexalithCommonsVersion=2.30.3 -p:HexalithTenantsVersion=0.0.0-story48 \
  -p:RestoreAdditionalProjectSources=<scratch>/story48
```

The version overrides are the Tenants Builds pins. The Contracts package depends
on EventStore >= 3.125.1, which is above McpCli's 3.124.0 pin. Enrollment and the
Builds bump are deferred. `--artifacts-path` kept McpCli's own `obj/` untouched,
so no McpCli restore was needed afterwards.

## Not done here, by design

- No release, Builds bump, enrollment, push or pull request (spec split; see
  `deferred-work.md`).
- Maintainer approvals were given on 2026-10-20 and are recorded in `approvals.md`.
- Live proof is Story 4.13's. The scripted cursors are loopback-only, so
  Gateway-ready acceptance stays blocked.

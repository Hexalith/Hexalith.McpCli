---
title: 'Expose Works, Timesheets, Agents, Conversations, Projects, and Folders through McpCli'
type: 'feature'
created: '2026-09-27'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'd81d8fb9ea7c49f30ddf69554b2b155bb2bf05b1'
context:
  - '_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** None of the six requested modules is discoverable or executable through McpCli. Their current Contracts releases lack McpCli declarations, and several public Contracts do not match callable EventStore gateway operations.

**Approach:** Complete the generic CLI and MCP execution path, make each owning module's callable gateway contracts declarative and packageable, then enroll exact released Contracts versions through flagged package references. McpCli sends Commands and Queries to the EventStore server, which routes them to Module servers. Prove catalog discovery and command/query behavior against that path for every exposed operation.

## Boundaries & Constraints

**Always:** Keep module-specific declarations and adapters in their owning repositories. The only dependency from McpCli to a Module is that Module's Contracts package; McpCli never calls a Module server directly. Keep enrollment to direct, versionless, flagged `*.Contracts` package references with exact central versions. Preserve existing Module consumers through additive gateway contracts/adapters and keep tenant and actor authority in the envelope. Enforce the AD-15 dependency closure and verify the restored packages and live gateway behavior before exposing an operation.

**Never:** Add module-specific code or source/project references in the McpCli production projects; point the catalog at folders; decorate operations without a working gateway route; take tenant authority from caller payload; publish or replace packages before the implementation and verification gates pass.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Discovery | Six released, decorated Contracts packages enrolled | Each module and its supported operations appears in both heads with matching descriptions and schemas | Missing/invalid declarations produce catalog diagnostics and fail coverage gates |
| Command or query | Valid payload, authorized envelope, live gateway | Same operation result through CLI and MCP; gateway receives declared wire type, routing, and safe payload | Invalid routing, unauthorized tenant, and unsupported operations fail without submission |
| Read-only session | Any exposed command | Discovery reports it unavailable and execution refuses it | No gateway write call |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli/Program.cs`, `src/Hexalith.McpCli/Cli/`, and `src/Hexalith.McpCli.Mcp/` — generic CLI and stdio MCP heads now call the shared catalog and gateway executor.
- `src/Hexalith.McpCli/Hexalith.McpCli.csproj` and `Build/ModuleAssemblyManifest.targets` — flagged production package enrollment and generated assembly list.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs`, `Catalog/AggregateIdAccessors.cs`, and `Schema/SchemaDeriver.cs` — current declaration, aggregate ID, and envelope property constraints.
- `../works/src/Hexalith.Works.Contracts/` — 15 value-object-ID commands, no query DTOs or annotations; gateway handles two queries.
- `../timesheets/src/Hexalith.Timesheets.Contracts/` and `../timesheets/src/Hexalith.Timesheets.Server/` — 28 commands and 8 queries, but no registered EventStore aggregate/query handlers.
- `../agents/src/Hexalith.Agents.Contracts/` — envelope-only aggregate IDs and some deferred query DTOs; interaction writes require trusted orchestration.
- `../conversations/src/Hexalith.Conversations.Contracts/` and `../conversations/src/Hexalith.Conversations/` — public command DTOs differ from aggregate wrapper commands; only two gateway query adapters exist.
- `../projects/src/Hexalith.Projects.Contracts/` and `../projects/src/Hexalith.Projects.Server/` — Contracts pull UI/framework dependencies and differ from strict gateway wire payloads. The legacy Projects plug-in and CLI surface is mapped in `projects-migration-inventory-draft.md`.
- `../folders/src/Hexalith.Folders.Contracts/` and `../folders/src/Hexalith.Folders.Server/` — current Contracts package has no command or query DTOs; server has gateway commands alongside REST-only behavior. Epic 4 Story 4.2 requires a maintainer-approved inventory of 49 legacy MCP tools and the CLI.
- `references/Hexalith.Builds/Props/Directory.Packages.props` — shared version catalog, currently missing three requested Contracts versions and McpCli Abstractions.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli/` and `src/Hexalith.McpCli.Core/` — complete the generic CLI, MCP, settings, and gateway executor stories before claiming user-facing module coverage.
- [ ] `../works/src/Hexalith.Works.Contracts/` and McpCli Core — support envelope-owned value-object IDs, add two gateway query descriptors, declare only callable operations, and remove disallowed Contracts dependencies.
- [ ] `../timesheets/src/Hexalith.Timesheets.Server/` and Contracts — implement and verify gateway handlers, then declare only callable operations.
- [ ] `../agents/src/Hexalith.Agents.Contracts/` and runtime — supply safe aggregate ID sources, retain trusted interaction orchestration, and declare only live handlers.
- [ ] `../conversations/src/Hexalith.Conversations.Contracts/` and runtime — align public gateway payloads and command adapters, and remove the disallowed serialization dependency.
- [ ] `../projects/src/Hexalith.Projects.Contracts/` and Server — slim Contracts to the allowed closure, publish gateway payload contracts, and align strict deserialization; expose only supported queries.
- [ ] `../folders/src/Hexalith.Folders.Contracts/` and Server — map each legacy tool/CLI operation to a callable gateway command or query or approved exclusion, add matching Contracts DTOs and handlers, and preserve REST-only authorization and behavior where required.
- [ ] `../builds/Props/Directory.Packages.props` and each owning module — version and release McpCli Abstractions and each decorated Contracts package with exact versions.
- [ ] `src/Hexalith.McpCli/Hexalith.McpCli.csproj` and `Directory.Packages.props` — enroll all six released packages with manifest flags and exact pins.
- [ ] `tests/` and each module's tests — cover manifest, dependency closure, catalog, CLI/MCP parity, and live gateway semantics for exposed operations.

**Acceptance Criteria:**
- Given the built tool and six released Contracts packages, when an operator lists modules and operations from CLI or MCP, then all six modules and their declared callable operations appear with equivalent documents.
- Given an authorized envelope, when each declared operation executes through either head, then the gateway accepts its wire type and routing and both heads return the same structured result.
- Given any module's decorated release, when the dependency gate inspects restored assets, then its closure adds only identities allowed by AD-15.

## Implementation Notes

- 2026-09-27: The shared catalog, gateway executor, CLI, and stdio MCP head now build without Module-specific production references. Discovery correctly returns `catalog_empty` until decorated Contracts packages are enrolled.
- 2026-09-27: Added `tools/dependency-policy.json` and a manifest test that compares the tool's restored packages with an exact pinned baseline, rejects unapproved direct roots and cross-Module transitives, and checks Module package framework references. This gate runs in the existing Manifest test project. The bootstrap `Hexalith.McpCli.Abstractions` 1.0.0 package packs and passes local release validation; it has not been published.
- 2026-09-27: Captured the Folders legacy surface in `folders-migration-inventory-draft.md`: all 49 MCP tools, two read-only resources, and 42 Frozen CLI leaf verbs (mapped to 42 tools), with command wire candidates and explicit pending inclusion decisions. This is a review draft, not the maintainer-approved AD-21 inventory.
- 2026-09-27: Captured the Projects legacy surface in `projects-migration-inventory-draft.md`: 11 MCP resources, five maintenance tools, and 18 Frozen CLI spellings, including aliases and REST-only behaviors. This is likewise a review draft awaiting the Projects maintainer's include/exclude decisions.
- 2026-09-27: Added CLI/MCP protocol test projects and the Python conformance-vector contract tests to CI; documented the gateway boundary and current `catalog_empty` state in the README. The vector contract is test-only and does not enroll a Module.
- 2026-09-27: Added the test-only out-of-process loopback runner and made it a blocking CI step. It packs one flagged sample Contracts package, verifies the restored artifact hash, and checks three sample Operations across CLI and MCP discovery, Gateway requests, result documents, malformed payloads, and Gateway errors. This establishes the generic AD-16 loopback mechanism; no requested Module has a matching approved vector or live semantic run yet.
- 2026-09-27: Prepared a framework-dependent `hexalith` .NET tool package and staged package validator. An isolated local tool install passed version and config smoke checks. The paired release validator correctly rejects its current empty production Contracts manifest, and the paired publication preflight remains closed.
- Release order remains binding: publish the decoration package first, migrate and verify each owning Module's gateway contracts and handler routes, release the decorated Contracts packages, then pin and enroll them in McpCli. At the inspected sibling revisions, no Module meets every gate. Projects and Conversations add package identities outside AD-15; Folders has no command/query DTOs and its 49-operation REST/MCP inventory needs an approved gateway migration; Timesheets lacks registered EventStore aggregate/query handlers; Works uses value-object identifiers and a disallowed serialization dependency; Agents has envelope-only command IDs and guarded interaction writes. Do not turn on an incomplete Module merely to make discovery list it.

- 2026-10-22: Completed the generic McpCli prerequisite for envelope-owned value-object members. `SchemaDeriver` admits Contracts-provided converters for tenant, actor, correlation, and idempotency value objects after checking string round trips. Numeric and string-changing converters remain rejected; existing custom-converter restrictions for primitive envelope members remain in force. Tenant and actor schemas stay independent of the Module identifier kind, while correlation and idempotency value objects carry canonical ULID constraints. Per-role normalization after schema export prevents repeated CLR types from inheriting another role's constraints through System.Text.Json `$ref` reuse. The computed-aggregate fixture now uses typed envelope members, and command/query tests verify filling and tenant disagreement rejection before Gateway submission.
- 2026-10-22: All six owning Contracts source directories still contain zero `HexalithModule`, `HexalithCommand`, `HexalithQuery`, or McpCli Abstractions reference declarations at the inspected revisions below. The six requested Modules remain unenrolled. The current production manifest already contains Parties 1.5.1 and Tenants 5.10.0; the September notes describing an empty production manifest are historical.

| Owning repository | Inspected HEAD | Remaining source/package prerequisite observed |
| --- | --- | --- |
| Works | `25ea5969daef6431777254e0c8602ec2f720ff18` | Contracts still reference `Hexalith.PolymorphicSerializations`; callable declarations, query descriptors, the allowed closure, and a decorated release remain required. |
| Timesheets | `622ee40e0df72404f60ee57da06e2963e665749d` | Contracts lack McpCli declarations and its Abstractions reference; current gateway/authorization/live semantics and a decorated release remain unverified by this run. |
| Agents | `dd1639439c6822337a747e254fcd626151b27000` | Contracts lack McpCli declarations and its Abstractions reference; safe aggregate ID sources and preserved trusted interaction execution still require owning-module implementation and proof. |
| Conversations | `60f18214d7a4565d28096628af95d867ddd5e874` | Contracts now depend on `Hexalith.Commons.Serialization`, which is also outside the current AD-15 baseline; gateway payload declarations, compatibility, and a decorated release remain required. |
| Projects | `d30b9559e825afdd7d245cd8b74c3fb79800228f` | Contracts still reference FrontComposer/Conversations packages, Fluxor, Fluent UI, and `Microsoft.AspNetCore.App`; slim compatible Contracts and approved gateway replacements remain required. |
| Folders | `28513763ec5c0405ab942b1e5266a483573f451d` | Contracts lack McpCli declarations and its Abstractions reference; approved replacement DTOs, gateway routes, and preserved REST authorization/behavior remain required. |

- 2026-10-22 approval gate: [Folders inventory 1.0.0](folders-migration-inventory-v1.md#a1-session-approval-2026-10-16) and [Projects inventory 1.0.0](projects-migration-inventory-v1.md#a1-session-approval-2026-10-16) supersede the September drafts. Their session approvals cover `defer / exclude` for every current row and explicitly supply no Gateway exposure or future candidate execution approval. Moving those rows into coverage requires a later approved inventory revision with exact operations, decorated types, routes, and owning-maintainer evidence. Those approval decisions were preserved.
- 2026-10-22 release gate: the imported Builds catalog supplies neither Works, Timesheets, nor Agents Contracts pins. Exact decorated release artifacts and dependency-closure evidence for all six requested Modules remain prerequisites; this run performed no publication, source-reference substitution, dependency-policy exception, or production enrollment.
- 2026-10-22 live-runtime gate: the enrolled inventory/vector artifacts and `v1-scope.json` currently cover Parties and Tenants. This run supplies generic synthetic execution evidence and existing gate verification, with no approved six-Module vector set or live semantic proof for their declared operations. Routing, authorization, and domain effects must pass in the owning gateway paths before exposure. Existing changes in the Timesheets, Conversations, Projects, and Folders working trees were preserved; Folders includes overlapping Contracts and Server changes. No sibling repository or `references/` checkout was modified.
- 2026-10-22: The Works/Core task remains unchecked because the owning-module work is incomplete. The remaining module, release, enrollment, and live-conformance tasks and all six-module acceptance criteria remain open; the spec stays `in-progress`.

## Spec Change Log

## Review Triage Log

## Design Notes

The six requested Module packages remain unenrolled. Parties and Tenants are already enrolled production packages. The generic envelope value-object prerequisite is implemented here; the inspected six sibling Contracts sources still require declarations, allowed dependency closures, decorated releases, and verified gateway behavior. Current Projects and Folders approvals retain deferred scope. This continuation performs no publication or upstream modification, and six-Module coverage remains incomplete.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` — all exact package versions resolve.
- `dotnet build Hexalith.McpCli.slnx --configuration Release` — manifest generation and dependency gate pass.
- Run each affected test project individually, followed by the generic loopback and live gateway lanes — all declared operations pass without bypassing authorization or routing.

**Observed continuation results (2026-10-22):**
- `dotnet restore Hexalith.McpCli.slnx` — passed initially and again after the loopback reset its temporary package cache; restored assets were fresh for Manifest.Tests.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` — passed with zero warnings and errors, including the final solution build after C# line-ending normalization.
- `dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release` — the initial full run passed 699 tests with three existing platform/benchmark skips.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -method 'Hexalith.McpCli.Core.Tests.SchemaTests.SharedEnvelope*'` — all five additional shared-type regression cases passed. A converter type shared with a tenant retains payload identifier constraints; ordinary direct, nested, array, and dictionary uses remain rejected as `invalid_schema`. No production fix was needed for this audit concern.
- `dotnet test tests/Hexalith.McpCli.Core.Tests --configuration Release --no-restore` — the final run, including those additional cases, passed 703 tests and skipped three, but failed `CatalogPerformanceTests.FirstConstructionStaysWithinFiveHundredMilliseconds`: 4059.9059 ms exceeded its 500 ms limit. The Core gate is therefore unresolved.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -method Hexalith.McpCli.Core.Tests.CatalogPerformanceTests.FirstConstructionStaysWithinFiveHundredMilliseconds` — the focused rerun also failed, measuring 1284.246 ms. Concurrent host inspection recorded load averages of 148.37, 95.06, and 58.80 with unrelated compiler/runtime processes. Host contention is a possible cause, not a proven explanation. The threshold was preserved and no further retry was run.
- `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` — 479 passed, two Windows-only skips.
- `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` — all 58 passed.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` — all 104 passed after the fresh restore.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` — 157 Python tests passed and all three sample vectors validated against the packed Contracts artifact.
- `bash tools/conformance-vectors/v1/run-sample-loopback.sh` — passed, including the three sample operations, packaged-process response cases, independent artifact proofs and combined replay of 24 Parties/Tenants/sample operations, pending-inventory rejection, and deliberately false semantic-assertion rejection. The subsequent shared-type audit added tests only; production logic stayed unchanged.

These results establish the bounded generic prerequisite and existing loopback behavior. They supply no live six-Module semantic evidence, exposure approval, or decorated package release. The final Core performance failure and the upstream scope/readiness gates remain open.

---
title: 'Discover Valid Operations in One Catalog'
type: 'feature'
created: '2026-09-25'
status: 'done'
baseline_commit: '27b998ad6122141ce82ce7389054753bfb61c7a7'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Decorated Contracts assemblies have serialization and Schema support, but no shared Catalog. The CLI and MCP heads cannot discover stable Operation names, routing, and Payload contracts from one source.

**Approach:** Build one immutable Core Catalog from the supplied assembly manifest. Resolve each Module and Operation once, retain the Schema and routing metadata, and expose deterministic descriptors for later heads and execution.

## Boundaries & Constraints

**Always:** Scan only `[HexalithModule]` assemblies supplied to `CatalogBuilder.Build(IReadOnlyList<Assembly>)`; unmarked assemblies are silent. Use interface routing first, attribute second, Module wire convention only for wire type fallback. Preserve the Module's fixed tenant, identifier kind, convention, and one cached read-only Payload options instance. Resolve property roles with `SchemaDeriver`, compile aggregate accessors once, and keep Operation Name distinct from Gateway Wire Type. Sort Modules and Operations ordinally; the same inputs must serialize byte-identically through `McpCliJson.Result`.

**Never:** Add folder scans, handwritten assembly lists, module-specific branches, production references to the sample Contracts fixture, or reflection in a head. Story 1.5 owns the full diagnostic taxonomy, logging, strict/empty behavior, and warning policy; this story must still exclude invalid declarations safely and expose diagnostic data for later use.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Marked and unmarked assemblies | Sample Module plus unmarked assembly | One Module; unmarked assembly invisible and silent | No diagnostic for unmarked assembly |
| Routed operations | Interface Command/Query, attribute Command/Query, convention fallback | Each routing field follows precedence; canonical names independent of wire types | Missing required routing excludes only affected Operation |
| Aggregate sources | Computed `ICommandContract.AggregateId`, declared property, Query constant, source-free Query | Cached getter/pointer accessor or constant; source-free Query has `AggregateIdRequired=true` | Source-free Command excluded; Query property and constant together excluded |
| Naming | Normal, acronym/digit, and explicit override names | Canonical `<module>.<operation>` names in ordinal order | Noncanonical/duplicate names and doubly decorated types excluded deterministically |
| Payload contract | Fixed tenant, provider converters, identifier kind, declared envelope roles | Descriptor retains Module policy, one derived Schema and resolved bindings | Invalid provider, Schema, roles, or example excludes affected Module/Operation |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Abstractions/{HexalithModuleAttribute,HexalithCommandAttribute,HexalithQueryAttribute,WireTypeConvention,KebabCase}.cs` — declaration surface and shared canonical naming helper; do not change its public meaning.
- `src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs` — `ForModule` validates/caches read-only Module options; `Result` is the canonical descriptor serialization policy.
- `src/Hexalith.McpCli.Core/Schema/{SchemaDeriver,DerivedSchema,PropertyBinding,PropertyRole,PayloadValidator}.cs` — derive once; reuse effective JSON member names/pointers and example validation rather than resolving them again.
- `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/{Commands/ICommandContract,Queries/IQueryContract}.cs` — static route values; Command has an instance aggregate getter. Read-only reference source.
- `tests/Hexalith.McpCli.Sample.Contracts/` — existing interface Command, attribute Command, Query, Ulid converter, and Module provider; extend test-only fixtures for missing paths. `tests/fixtures/Manifest.Unmarked.Contracts/` exercises silent exclusion.
- `src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets` and `Program.cs` — manifest is already generated; leave composition-root loading for later story.
- `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md` AD-3/4/6/7/19 and `_bmad-output/planning-artifacts/epics.md` Story 1.4 — descriptor, routing, and determinism decisions.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli.Core/Catalog/{CatalogBuilder,ModuleDescriptor,OperationDescriptor,CatalogDiagnostic}.cs` — add immutable Catalog construction, descriptor data, deterministic scanning/ordering, and safe declaration exclusion; place each public type in its own file.
- [x] `src/Hexalith.McpCli.Core/Catalog/{RoutingResolver,AggregateIdAccessors}.cs` — resolve each Gateway field in precedence order, keep canonical names separate, and compile property/interface aggregate accessors using the Module Payload options and resolved bindings.
- [x] `tests/Hexalith.McpCli.Sample.Contracts/` and `tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs` — cover every matrix row, interface Query, constant/source-free Query, String identifier kind in isolated construction, fixed tenant, explicit name, acronym/digit boundaries, role bindings, and repeated canonical serialization.

**Acceptance Criteria:**
- Given the supplied assembly list, when `CatalogBuilder.Build` runs, then it returns one immutable descriptor set whose valid Modules and Operations are ordered ordinally and whose unmarked assemblies are absent without diagnostics.
- Given an exposed Operation, when a consumer inspects its descriptor, then its route, aggregate source, Schema, Payload options, envelope bindings, and Contract type are already resolved without reflection by the consumer.
- Given the same assemblies in different input orders, when a Catalog is built and serialized with `McpCliJson.Result`, then the bytes are equal.

## Implementation Notes

- Added the immutable Catalog and descriptors in Core, reusing cached Module options, Schema derivation, role bindings, and the Payload validator. Routing reads interface static members before attributes and convention; aggregate sources use one prepared property or interface accessor.
- Assembly and type scans use ordinal order. The first valid Module or Operation name survives a duplicate; later declarations receive structured diagnostics. Invalid declarations are isolated while marked empty Modules remain visible.
- Expanded test-only Contracts fixtures for both identifier kinds, routing sources, envelope roles, invalid declarations, and duplicate precedence. The executable composition root remains a later-story concern.
- Verification: solution restore and Release build passed with zero warnings; project-level tests passed Core 65/65, Abstractions 20/20, and Manifest 6/6. Earlier project-level `dotnet test` runs returned `Zero tests ran` (exit 5), so the direct-assembly fallback was used at that point; all prescribed project-level commands passed in the final run.

## Spec Change Log

## Review Triage Log

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| Blind: provider getter exception aborts build | false — `PropertyInfo.GetValue` wraps a throwing getter in `TargetInvocationException`, which `IsDeclarationFailure` catches. | reject |
| Blind: operation attribute constructor aborts build | low — the shipped sealed attributes only assign constructor values; malformed metadata could still throw before the per-operation handler, but guarding corrupt assemblies adds complexity unlikely in ordinary compiled Contracts packages. | reject |
| Blind: partial `ReflectionTypeLoadException` hides valid types | low — the supplied assembly is incomplete when `GetTypes` cannot load its declared types; admitting a partial Module would risk unusable operation contracts, and a fallback loader adds complexity. | reject |
| Blind: whitespace projection actor type passes Catalog | medium — `IsWireValue` permits spaces, while `SubmitQueryRequestValidator` rejects whitespace-only `ProjectionActorType`. | patch |
| Blind: Catalog lacks `Describe` and `ListOperations` | false — `Catalog` already exposes the one resolved descriptor set; no head or executor caller exists yet, and the approved story asks for descriptors, not discovery verbs. | reject |
| Blind: equal assembly names retain manifest input order | medium — distinct assemblies can share `Name` and `FullName` in separate load contexts or dynamic assemblies; the sort then leaves their relative order input-dependent. | patch |
| Blind: full type name convention untested | medium — no Catalog fixture currently selects `WireTypeConvention.FullTypeName`, so removal of that branch would pass the tests. | patch |
| Blind: explicit convention with missing wire untested | medium — no Catalog test isolates missing wire under `Explicit`; an unintended fallback could expose an invalid route. | patch |
| Blind: renamed aggregate property accessor untested | medium — no Catalog test exercises `aggregateIdProperty` with `[JsonPropertyName]`; a CLR-name lookup regression would pass. | patch |
| Edge: partial type-load failure hides valid operations | low — same incomplete-assembly behavior as the blind finding; partial admission adds complexity and can expose unusable contracts. | reject |
| Edge: attribute construction failure aborts discovery | low — same malformed-metadata case as the blind finding; normal compiled decoration constructors cannot throw. | reject |
| Edge: equal assembly identities leave order unstable | medium — same input-order tie as the blind finding; a stable content tie-break is needed. | patch |
| Verification: Command interface precedence lacks conflict case | medium — `CreateItemCommand` has no competing attribute route, so a command-only precedence regression would pass. | patch |
| Verification: full type name fallback lacks Catalog assertion | medium — same untested `FullTypeName` branch as the blind finding; a marked fixture must assert its wire value. | patch |

## Design Notes

The accessor receives the rebuilt, finally validated Payload. A property source reads its resolved serialized JSON member; the interface path materializes the contract with Module options before reading `ICommandContract.AggregateId`. Query constant and explicit call argument precedence is left to the later executor. Keep minimal structured diagnostic data now so Story 1.5 can add categories, logging, and strict policy without changing the descriptor model.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` — succeeds.
- `dotnet build Hexalith.McpCli.slnx --configuration Release` — succeeds with no warnings.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release` — Catalog and Schema tests pass.
- `dotnet test tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj --configuration Release` and `dotnet test tests/Hexalith.McpCli.Manifest.Tests/Hexalith.McpCli.Manifest.Tests.csproj --configuration Release` — existing suites pass individually.

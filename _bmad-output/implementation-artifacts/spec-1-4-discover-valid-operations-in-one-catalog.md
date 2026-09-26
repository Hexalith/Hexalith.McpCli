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

### Review Findings

Code review of 2026-09-26: `27b998a..fb6a64a`, full mode, with the Blind Hunter, Edge Case Hunter, Verification Gap and Acceptance Auditor layers.

- [x] [Review][Patch] Sample.Contracts now carries invalid and extra declarations (decision: move them to an isolated `tests/fixtures/Catalog.Invalid.Contracts` assembly) — The architecture spine's Tests convention says `Sample.Contracts` declares exactly one Module with one `ICommandContract` command, one attribute-routed command, one converter-backed identifier, and one query. The diff adds about 20 types to it, a dozen of them deliberately invalid. As a result, every `CatalogBuilder.Build([Sample])` returns error diagnostics. Story 1.5's `--strict` (`catalog_invalid`) path and the planned Verify snapshot of the Catalog dump will inherit that noise. This spec's Code Map allowed extending the fixtures, so the spine and the spec disagree. The options are to move the invalid and extra fixtures into isolated `tests/fixtures/Catalog.*.Contracts` assemblies, or to keep them and amend the spine.
- [x] [Review][Patch] Public type `Catalog` shares its name with the namespace `Hexalith.McpCli.Core.Catalog` (decision: rename the class to `CatalogSnapshot`) — Code inside `Hexalith.McpCli.Core.*`, such as the future executor and `Core.Tests`, resolves `Catalog` to the namespace (CS0118). It needs an alias, as `CatalogTests` already does with `using CatalogSnapshot = …Catalog.Catalog;`. The options are to rename the type (for example `CatalogSnapshot`), rename the namespace, or keep it.
- [x] [Review][Patch] Routing wire-value validation diverges from the Gateway validators [src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs:65]
  - `IsWireValue` bans `:` in every wire type. The pinned `SubmitCommandRequestValidator` allows colons in `CommandType`; only `QueryType`, `ProjectionType` and `ProjectionActorType` ban them. A valid command wire type such as `orders:create` is therefore excluded.
  - `IsWireValue` also rejects control characters, which the Gateway accepts.
  - It omits the Gateway's `javascript\s*:` and `<\s*script` injection terms.
  - Fix: mirror AD-9 exactly. Apply the colon rule per field and use the Gateway's `(?i)(javascript\s*:|on\w+\s*=|<\s*script)` pattern.
- [x] [Review][Patch] Invalid-operation test asserts categories globally, not per type [tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs:158]
  - `codes.ShouldContain(...)` passes as long as any fixture emits the category.
  - `InvalidRoutingQuery` (a bad domain) is never named, so removing the `IsTenantDomain(domain)` check still passes. `DualAggregateQuery`, `ConflictingEnvelopeCommand` and `ConflictingRoleCommand` are never tied to their categories either.
  - No fixture covers an invalid `ProjectionType`.
  - Fix: assert exclusion and a `(TypeName, Category)` diagnostic for each invalid fixture.
- [x] [Review][Patch] Invalid Query aggregate-ID constant has no fixture [src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:185] — Removing the `IsAggregateId` constant check passes every test.
- [x] [Review][Patch] Module-marker validation is untested [src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:37] — No test covers a non-canonical name, a blank description, an out-of-range enum, or an invalid `FixedTenant`. Deleting either check passes every test. Use the existing dynamic-assembly helper.
- [x] [Review][Patch] `AggregateIdRequired` is never asserted false for a property-sourced Query [src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:223] — Dropping `accessor is null &&` from the expression passes every test. Assert that `sample.get-item` is false.
- [x] [Review][Patch] `IdempotencyKeyRequired` is only asserted true [src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:220] — No nullable-idempotency fixture exists, and no operation without an idempotency binding is asserted false. Replacing the expression with `ContainsKey` passes every test.
- [x] [Review][Patch] The "Invalid Schema" matrix cell is untested [tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs:158] — No fixture produces `invalid_schema` (extension data, a polymorphic type, or an opaque member), although Task 3 requires every matrix row.
- [x] [Review][Patch] `missing_description` and `invalid_operation_declaration` branches are untested [src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:100] — Blank descriptions and abstract, open-generic or struct decorated types have no fixture.
- [x] [Review][Defer] Diagnostic categories come from matching exception message text [src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:234] — deferred: Story 1.5 owns the taxonomy.
  - `Classify` substring-matches `SchemaDeriver` messages, so `RoutingResolver.Invoke`'s "Contract interface routing could not be read." lands in `invalid_schema`.
  - `IsDeclarationFailure` catches broad BCL exceptions, which can turn internal McpCli bugs into quiet operation exclusions.
  - `invalid_module_declaration`, `conflicting_operation_kinds`, `invalid_operation_declaration`, `invalid_operation_name` and `invalid_schema` are outside the spine taxonomy.
  - Story 1.5 should replace this with a coded declaration-failure exception.
- [x] [Review][Defer] Diagnostic messages drop the failure detail [src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:229] — deferred: Story 1.5 requires an "actionable message". Generic texts such as "The operation declaration could not be resolved." discard `exception.Message`, so the author cannot tell which member or value failed.
- [x] [Review][Defer] Routing source is discarded, so `redundant_value` and `conflicting_value` cannot be emitted [src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs:21] — deferred: this is a Story 1.5 AC. `Resolve` overwrites attribute values with interface values without recording which source won. `CompetingRouteCommand` and `InterfaceItemQuery` conflict silently.

**Patch resolution (2026-09-26):**
- `Sample.Contracts` is back to the spine's canonical shape and builds with no diagnostics.
- The valid routing, aggregate-source and envelope variants moved to `tests/fixtures/Catalog.Routing.Contracts`. That assembly adds a colon command wire type and an optional idempotency key.
- The invalid declarations, together with the surviving first duplicate, moved to `tests/fixtures/Catalog.Invalid.Contracts`. It adds these fixtures: invalid constant, invalid projection type, colon query wire type, blank description, abstract, open generic, and extension-data (`invalid_schema`).
- Moved fixtures use string `[HexalithIdentifier]` members, because a Module's serializer provider must live in its own assembly.
- `Catalog` is renamed `CatalogSnapshot`.
- `RoutingResolver.IsWireValue` mirrors the Gateway validators: colons are allowed only in command wire types, it uses the Gateway's source-generated injection pattern, and it no longer rejects control characters.
- `CatalogTests` asserts one `(TypeName, Category, Severity)` per invalid type, the invalid module markers, and the `false` cases of `AggregateIdRequired` and `IdempotencyKeyRequired`.
- Verification:
  - `dotnet build Hexalith.McpCli.slnx --configuration Release` gives 0 warnings and 0 errors.
  - Tests pass: Core 92/92, Abstractions 20/20, Manifest 6/6.
  - Reintroducing each regression (command colon ban, domain check, `accessor is null`, idempotency nullability) fails at least one test.

**Rejected:**
- `false` — `CatalogDiagnostic` is loosely modeled: its shape is exactly the spine's `CatalogDiagnostic(TypeName, Category, Severity, Message)`.
- `low` — Non-public decorated types are exposed: decoration is the explicit opt-in, and a visibility guard adds a branch for an unlikely authoring case.
- `false` — The interface aggregate accessor is not compiled once, can throw, and its result is unvalidated: AD-19 prescribes deserializing the finally validated payload before the getter runs, and AD-8/AD-19 make the executor validate the accessor value and reject empty identifiers.
- `false` — A nullable Command aggregate property yields a null accessor value: AD-19 makes a missing non-empty value `validation_failed` in the executor.
- `false` — `AggregateIdProperty` silently overrides the `ICommandContract` getter: AD-19 prescribes the property first.
- `low` — The same-identity assembly tie-break is arbitrary: the earlier triage made it input-order independent, and the generated manifest loads by unique name.
- `false` — The name validators are duplicated and `IsCanonicalPart` is uncapped: no consumer imposes a length limit on canonical names, and no divergence harm was named.
- `false` — The tenant/aggregate pre-check duplicates `SchemaDeriver`: the spine requires retaining `tenant_is_aggregate_id` for that collision.
- `low` — Unloadable attribute or member metadata aborts `Build`: the earlier triage already rejected this; manifest assemblies ship with their dependencies, and guards add branches.
- `low` — A Command attribute on an `IQueryContract` type ignores interface routing: this is a rare authoring error, and a guard adds a branch.
- `false` — KebabCase wire type follows the explicit name override: `WireTypeConvention.KebabCase` is documented as "the operation's kebab-case name part".
- `false` — `OperationDescriptor` lacks Payload options: AD-3 places `ModulePayloadOptions` on `ModuleDescriptor`, and the descriptor field list matches.
- `false` — An empty interface static blocks the attribute fallback: the spine's "Routing per field" says the interface value wins when it defines the field.
- `low` — `IsWireValue` regex has no timeout and is not source-generated: its input is bounded to 256 characters by the preceding length check.
- `low` — The null-entry and `ReflectionTypeLoadException` paths are untested: both are trivial guards, and the second is hard to fixture.

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

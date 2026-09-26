---
title: 'Diagnose Catalog Declarations'
type: 'feature'
created: '2026-09-26'
status: 'done'
baseline_commit: 'e8d59420ae8a1a34f5685ef32bc1c4d851836781'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Catalog already excludes invalid declarations, but it picks categories by matching exception text, drops the failure detail, and emits categories that are not in the spine. It never emits `redundant_value` or `conflicting_value`. Nothing logs diagnostics or applies the strict and empty policies.

**Approach:** Declaration failures carry their category in a coded exception, and the diagnostic message keeps the author-facing detail. Routing records which source supplied each field, so the Catalog can emit the two routing warnings. A lazy Core catalog provider builds the Catalog once, logs each diagnostic once through `ILogger`, and returns `catalog_empty` or `catalog_invalid` to Catalog-dependent callers.

## Boundaries & Constraints

**Always:** Keep `CatalogDiagnostic(TypeName, Category, Severity, Message)` and its deterministic ordering, and keep first-survivor duplicate precedence. Resolve property-role ownership after serialization mapping. When two roles claim one serialized member, report `tenant_is_aggregate_id` only for the Tenant and AggregateId pair; every other pair is `conflicting_property_roles`. The interface value wins a routing conflict, and an attribute value may override a convention without a diagnostic. Log through source-generated `LoggerMessage` methods and never write to stdout. `Sample.Contracts` must still build with zero diagnostics.

**Decision (taxonomy):** Amend the spine. The spine's "Catalog diagnostics" row and PRD FR-6 add five error categories: `invalid_module_declaration` (a bad marker name, description, identifier kind, or convention), `conflicting_operation_kinds`, `invalid_operation_declaration` (an abstract, open-generic, or non-class type), `invalid_operation_name`, and `invalid_schema` (extension data, polymorphism, free-form or opaque members, or an STJ contract error). No other categories are emitted.

**Never:** CLI or MCP verbs, settings resolution, `OperationError` documents, exit-code mapping, and composition-root manifest loading (these belong to Epics 2 and 3). Diagnostics in `ModuleDescriptor` or `OperationDescriptor` serialization. Catching broad BCL exceptions as declaration failures. Changing `references/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Coded failure | Any invalid fixture in `Catalog.Invalid.Contracts` | Exactly one `(TypeName, Category, "error")`, and the message names the member or value that failed | A non-declaration exception propagates |
| Property references | Unknown, `[JsonIgnore]`d, hidden (`new`) duplicate, or converter-opaque role member | `invalid_property_reference` | The Operation is excluded |
| Role aliasing | Tenant=Actor; Correlation=AggregateId; Tenant=AggregateId on a `[JsonPropertyName]`-renamed member | `conflicting_property_roles`, `conflicting_property_roles`, `tenant_is_aggregate_id` | The Operation is excluded |
| Routing warnings | Attribute equals an interface value; attribute equals the convention value; attribute differs from an interface value | One `redundant_value`, `redundant_value`, or `conflicting_value` warning per field | The Operation is kept, and the interface value wins |
| Free-form member | An `object`, `JsonElement`, or `JsonNode` member | The message says "free-form member" | The Operation is excluded |
| Provider access | No provider call, then two calls | The first call builds the Catalog and logs each diagnostic once; the second call does neither | — |
| Empty or strict | A Catalog with no valid Operations; strict mode with any diagnostic | `catalog_empty`; `catalog_invalid`, and strict is checked first | Normal mode returns the Catalog with its warnings |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs`: replace `Classify`, `IsDeclarationFailure`, the generic messages, and the CLR-name tenant/aggregate pre-check. Scan order, sorting, and duplicate precedence stay as they are.
- `src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs:12-51`: `Resolve` overwrites attribute values with interface values. Return per-field source/warning data alongside `OperationRouting`, and throw coded exceptions instead of `ArgumentException("missing_routing_values")`.
- `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:89-131` (`ResolveBindings` role checks, ownership at :129) and the `NotSupportedException` sites at :163/:168/:188/:193/:308: throw the coded exception with an actionable message. `options.GetTypeInfo` and the exporter can throw STJ `InvalidOperationException`/`NotSupportedException` for bad user contracts; wrap those as `invalid_schema`. Argument-null guards and the `identifierKind` range guard stay BCL.
- `src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs:39-57` `ReadProvider`: provider failures, including a throwing getter (`TargetInvocationException`), become coded `invalid_serializer_options_provider`.
- `tests/Hexalith.McpCli.Core.Tests/SchemaTests.cs` (the `Should.Throw<ArgumentException|NotSupportedException>` lines 88–510) and `CatalogTests.cs`: update the expected exception types. `ValidFixturesBuildWithoutDiagnostics` must expect the Routing fixture's warnings (`CompetingRouteCommand` gives 2 conflicts; `InterfaceItemQuery` gives 3).
- `tests/fixtures/Catalog.Invalid.Contracts/`, `Catalog.Routing.Contracts/`: add the matrix fixtures here. `DynamicProviderFactory.cs` and the `AssemblyBuilder` helpers in `CatalogTests` build marker variants.
- `Microsoft.Extensions.Logging.Abstractions` is pinned at 10.0.12 in `references/Hexalith.Builds/Props/Directory.Packages.props:236` and sits inside the EventStore.Client closure (allowlisted). Add a versionless reference in Core.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md` (Catalog diagnostics row) and `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md` (FR-6 table) -- add the five decided error categories with their triggers.
- [x] `src/Hexalith.McpCli.Core/Catalog/ContractDeclarationException.cs` (new, public; `Category` + message) — the one catchable declaration-failure type.
- [x] `SchemaDeriver.cs`, `McpCliJson.cs`, `RoutingResolver.cs` — throw it with detail, including "free-form member" wording and post-mapping tenant/aggregate classification; record routing sources and emit `redundant_value`/`conflicting_value` warnings.
- [x] `CatalogBuilder.cs` — catch only `ContractDeclarationException`, use its category and message, add the routing warnings, and remove `Classify`, `IsDeclarationFailure`, and the pre-check.
- [x] `src/Hexalith.McpCli.Core/Catalog/{CatalogProvider,CatalogAccess}.cs` (new) + `Hexalith.McpCli.Core.csproj` — lazy thread-safe provider over a manifest factory and `ILogger<CatalogProvider>`, with `Get(bool strict)` returning the snapshot or an error code and message.
- [x] Fixtures + `CatalogTests.cs`, `SchemaTests.cs`, new `CatalogProviderTests.cs` with a recording logger — cover every matrix row, repeated-build diagnostic order, and the absence of diagnostic text in serialized `Modules`.

**Acceptance Criteria:**
- Given the full fixture set, when the Catalog is built twice from reversed manifests, then survivors, diagnostics and `McpCliJson.Result` bytes are equal.
- Given any emitted diagnostic, then its category belongs to the amended spine taxonomy and its message identifies the failing member or value.
- Given a McpCli internal fault (a non-coded exception), when the Catalog builds, then that exception propagates rather than becoming an exclusion.

## Design Notes

`CatalogAccess` is a Result, not an exception: `CatalogAccess(CatalogSnapshot? Catalog, string? ErrorCode, string? Message)`. The later heads map `ErrorCode` into AD-5/§G documents. The provider takes `Func<IReadOnlyList<Assembly>>`, so constructing it touches no assembly; that is how Catalog-free verbs skip the build. Log one `LoggerMessage` per diagnostic (Warning or Error level) with the fields `TypeName`, `Category`, `Severity`, and `Message`.

## Verification

**Commands:**
- `dotnet build Hexalith.McpCli.slnx --configuration Release` — 0 warnings, 0 errors.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release`, then the same for the Abstractions and Manifest test projects — all pass.

## Implementation Notes

- `RoutingResolver.Resolve` returns an internal `RoutingResolution` (routing, per-field `RoutingValueSource`, warnings). Routing warnings are added only for Operations that survive, so an excluded type keeps exactly one error diagnostic.
- Role conflicts are detected on the serialized member right after mapping, before deserializability and type checks; envelope roles (not `AggregateId`) on a member with a non-STJ property-level converter are `invalid_property_reference`.
- Free-form detection covers `object`, `JsonElement`, `JsonDocument`, and every `JsonNode` subtype at any depth, so `JsonObject`/`JsonArray` members are now rejected too.
- `invalid_example` reports the most specific violation path. `ReflectionTypeLoadException` from `GetTypes` is still reported as `invalid_module_declaration` (pre-existing, narrow catch).
- The non-coded-fault test uses an `Assembly` subclass exposing one query whose `JsonConverterAttribute` throws `ArgumentException`; the old `IsDeclarationFailure` would have swallowed it.

## Spec Change Log

## Review Triage Log

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| Blind/Edge: a contract-authored converter or type-load fault (non-coded) aborts the whole Catalog | low: the manifest ships compiled Contracts with their dependencies, and a converter that throws on creation fails loudly for its own author; the Story 1.4 triage rejected unloadable metadata on the same grounds. Classifying these faults would need the broad catch the frozen Never forbids. | reject |
| Blind: `NonCodedFailurePropagates` calls a contract converter fault a "McpCli internal fault" | low: the test documentation mislabels the simulated fault; correcting the wording fixes it. | patch |
| Blind/Edge: the IOE/NSE catch around the exporter also wraps faults from McpCli's `Transform` | low: this needs a McpCli bug that throws IOE/NSE in `Transform`, and the diagnostic keeps the inner exception and its message; marking `Transform` faults adds branches. | reject |
| Blind/Edge: `Lazy` in `CatalogProvider` caches a build exception forever | false: the build is deterministic, so a retry would fail the same way; AD-12 makes a Catalog failure end startup before serving. | reject |
| Blind/Edge/VG: `ReadProvider` never reaches its `TypeInitializationException` catch and hides a static-constructor cause | medium: `GetValue` wraps it as TargetInvocationException→TypeInitializationException (VG probe), so the message drops the real cause, unlike `RoutingResolver.Invoke`. | patch |
| Blind/Edge/VG: `RoutingResolution.Sources` and `RoutingValueSource` are computed but never read | low: dead data with no consumer; deleting it is the fix. | patch |
| Blind/Edge: a blank interface or attribute routing value gives a misleading `missing_routing_values` message | low: the Operation is still excluded correctly (the Story 1.4 `??` behavior was the same); a clearer message needs extra branches for a rare authoring case. | reject |
| Blind: `DeriveNamePart` duplicates `KebabCase.FromTypeName`'s preconditions, against the spine's one shared naming helper | medium: if either copy drifts, `KebabCase` throws `ArgumentException` and aborts the whole Build (see VG). A narrow catch around the one helper call removes the copy. | patch |
| VG: no test covers a noncanonical type-derived operation name | pre-verified gap: only `BadNameQuery` (an explicit Name) reaches `invalid_operation_name`. | patch |
| Blind: category and severity strings are scattered literals | low: `EveryDiagnosticBelongsToTheTaxonomy` checks every fixture-reached path; a constants type adds new surface. | reject |
| Blind: the PRD/spine trigger lists omit emitted cases (type-load failure, `JsonDocument`, non-object Command root, FixedTenant/ProjectionActorType/throwing interface member) | low: the docs are incomplete against the code; editing the documents fixes it. | patch |
| Blind: `invalid_example` reports only the deepest violation | low: the message is already actionable; adding a count is an enhancement. | reject |
| VG: no test pins the rejection of `JsonObject`/`JsonArray` members | pre-verified gap: the exporter gives them constrained schemas, so only `IsFreeForm` rejects them, and no fixture covers it. | patch |
| Blind: no test covers an element-level free-form type (`List<object>`) | low: the free-form element branch in `ConstrainOpaqueElements` is untested; one fixture fixes it. | patch |
| Blind: no test covers the `TypeInitializationException` unwrap in `RoutingResolver`, the `#/` location text, or deepest-violation selection | low: diagnostic-text details that a user or developer is unlikely to meet; each needs its own fixture. | reject |
| VG: no test covers the `ReflectionTypeLoadException` cause detail | pre-verified gap: the cause detail is new in this story; a subclassed Assembly whose `GetTypes` throws pins it. | patch |
| Blind: `ConcurrentFirstCallsBuildOnce` never forces concurrent factory entry | low: the test would still pass with `PublicationOnly`; the fix is a small test change. | patch |
| Blind: `CollidingNameCommand` asserts on the BCL's "collides" wording | low: fragile across runtime patches; asserting on the McpCli fragment is a direct correction. | patch |
| Blind: the strict `catalog_invalid` message gives only a count | low: every diagnostic was logged just before at first build (AD-12 runs strict before serving). | reject |
| Blind: `CatalogAccess` allows invalid field combinations | low: only `CatalogProvider` constructs it; guarded factories add surface. | reject |
| Blind/Edge: declared values are interpolated raw into log messages | low: the values come from compiled, operator-enrolled Contracts attributes; escaping at every site adds complexity. | reject |

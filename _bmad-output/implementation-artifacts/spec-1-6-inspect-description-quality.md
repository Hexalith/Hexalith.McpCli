---
title: 'Inspect Description Quality'
type: 'feature'
created: '2026-09-27'
status: 'done'
baseline_commit: '592303e1c48c79368a02d7f3a5faae39eac207d5'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Module author can see a derived Operation Schema but cannot see where Payload descriptions are absent or misleading. The Catalog currently has no lint result for an Operation.

**Approach:** Compute stable, actionable description findings when each valid Operation is built, retain them beside its Schema, and expose an empty array for an Operation with no findings.

## Boundaries & Constraints

**Always:** Emit only `missing_property_description`, `unmarked_identifier_like_property`, `payload_paging_member`, and `hollow_description`, each with `severity: warning` and a nonempty message. Property findings carry a `property` RFC 6901 pointer using effective serialized names, including escaping of `~` and `/`; an operation-level hollow finding omits `property`. Inspect serializable input members recursively through nested objects and collections, including constructor-bound properties, while excluding ignored or computed members. Keep findings deterministically ordered and separate from Catalog diagnostics; they neither exclude an Operation nor trigger strict Catalog failure. An unmarked `*Id` member keeps its existing Schema, and a declared aggregate-ID source counts as marked for this lint. Warn on `PageSize`, `Offset`, and `Cursor` members in Query Payloads; generic paging remains an Envelope argument.

**Never:** Add CLI/MCP verbs, CLI exit-code behavior, a compiler analyzer, Module-specific code, or changes under `references/`. Do not infer an identifier type or change a Payload Schema from a name suffix. Do not add lint categories to `CatalogDiagnostic` or log them through `CatalogProvider`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Nested description gap | Described root with an undescribed nested object or collection element property | One `missing_property_description` warning per undescribed serialized property, with a stable pointer | Valid Operation remains exposed |
| Identifier and paging hints | Unmarked `ExternalId` and Query Payload `PageSize`, `Offset`, or `Cursor` | Matching property warnings; unchanged serialized Schema | No Catalog diagnostic |
| Hollow description | Description equals the humanized CLR Operation type name | One `hollow_description` with no `property` member | No exclusion |
| Serialized spelling | `[JsonPropertyName]` containing `~` or `/`, including in a nested type | Pointer escapes tokens and identifies the property in the Schema | No CLR-name leakage |
| Complete description | Sample Contracts with described members | `lintFindings: []` | No diagnostic or strict failure |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs:148-239` — `BuildOperation` derives Schema and creates `OperationDescriptor`; calculate lint only after an Operation validates.
- `src/Hexalith.McpCli.Core/Catalog/OperationDescriptor.cs` — add an immutable `LintFindings` list beside `Schema`; leave the existing routing and Schema fields intact.
- `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:202-315` — existing transform attaches property descriptions from `[Description]` or constructor parameters to exported Schema; reuse its effective member semantics.
- `src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs:79-139` — Module Payload options and resolver determine serialized names and omit non-input getters; `Result` supplies outer camel-case document fields.
- `src/Hexalith.McpCli.Core/Schema/PropertyBinding.cs` — existing escaped pointer mapping for declared top-level roles; use it to identify aggregate-ID sources.
- `tests/Hexalith.McpCli.Core.Tests/{CatalogTests,SchemaTests}.cs`, `MixedCommand.cs`, `NestedValue.cs` — existing Catalog and nested Schema behavior; add focused lint assertions without weakening them.
- `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md:311,367-371` — exact result-member and lint-code contract; the current story does not create the later `describe_operation` head.

## Tasks & Acceptance

**Execution:**
- [x] `src/Hexalith.McpCli.Core/Catalog/LintFinding.cs` — define the public warning result with optional `property`, omitting it for operation-level findings.
- [x] `src/Hexalith.McpCli.Core/Catalog/DescriptionLinter.cs` — inspect effective serialized input members recursively, check descriptions, identifier markers and Query paging names, and return sorted, immutable findings.
- [x] `src/Hexalith.McpCli.Core/Catalog/{CatalogBuilder,OperationDescriptor}.cs` — compute findings once during valid Operation construction and retain them for future describe results.
- [x] `tests/fixtures/Catalog.Lint.Contracts/{Catalog.Lint.Contracts.csproj,Module.cs,InspectItemQuery.cs,NestedItem.cs,CollectionEntry.cs,DictionaryValue.cs,InspectHollowQuery.cs}` — add isolated nested, collection, hollow, identifier, paging, casing, and escaped-name fixtures.
- [x] `tests/Hexalith.McpCli.Core.Tests/DescriptionLintTests.cs` — assert the full matrix, strict isolation, and repeated-build document bytes.
- [x] `tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj` and `Hexalith.McpCli.slnx` — enroll only the test fixture project.

**Acceptance Criteria:**
- Given the same Contracts assemblies in either manifest order, when the Catalog builds twice and its lint-bearing Operation documents are serialized with `McpCliJson.Result`, then the findings and document bytes are identical.
- Given a valid Operation with lint findings, when normal and strict Catalog access are evaluated, then lint alone leaves the Operation available and does not produce `catalog_invalid`.
- Given a property-level finding, when serialized, then it has `code`, `severity`, `message`, and `property`; given a hollow-description finding, then `property` is absent.

### Review Findings

- [x] [Review][Patch] Nullable struct members (`S?`) are never inspected: `options.GetTypeInfo(typeof(S?))` is not `Object`, so `InspectNode` returns while the exported Schema still carries the struct's `properties`; probe `Money? Maybe` got no findings while `Money Sure` got description and identifier findings — unwrap `Nullable.GetUnderlyingType` before resolving type info and add a fixture [src/Hexalith.McpCli.Core/Catalog/DescriptionLinter.cs:63]
- [x] [Review][Patch] Envelope-bound root `*Id` members get `unmarked_identifier_like_property` advice to add `HexalithIdentifier`; probe `TenantProperty = nameof(TenantId)` was flagged, and following the advice in a `Ulid` Module puts the ULID pattern on the Tenant, which PRD §4 says is never ULID-validated — exempt every root member bound to any `PropertyRole`, not only `AggregateId`, and add a fixture [src/Hexalith.McpCli.Core/Catalog/DescriptionLinter.cs:103]
- [x] [Review][Patch] No Command in the lint fixtures: removing the `kind == OperationKind.Query` paging guard or the `Command` suffix strip in `HumanizeOperationName` passes every test — add a Command with a described `Offset`/`PageSize` (expect no `payload_paging_member`) and a hollow Command description (expect one `hollow_description`), updating `LintDoesNotAffectCatalogStrictness` counts [tests/Hexalith.McpCli.Core.Tests/DescriptionLintTests.cs:18]

**Rejected:**
- false — `CatalogTests.SerializedModulesCarryNoDiagnosticText` weakened: each diagnostic's `Category` and `Message` are still asserted absent, so any leaked `CatalogDiagnostic` is still caught; the `"severity"` check had to go because lint findings legitimately carry it.
- false — `missing_property_description` on envelope-filled `Tenant`: PRD FR-4 recursively reports undescribed properties; the readOnly member is still in the Schema, and the prior triage reworded the message deliberately.
- false — Ulid-typed unmarked `*Id` member still warned: FR-7 says an *unmarked* property ending in `Id` produces the lint warning, independent of CLR type.
- false — paging warning on nested members: PRD FR-4 says `describe --lint` *recursively* reports Payload paging members named `PageSize`, `Offset`, or `Cursor`.
- false — spec `status: done` vs sprint `review`: same convention as story 1.5; sprint status is synced by this review.
- false — "126/126" evidence stale: reran Core tests, 126/126 pass; the regression cases were added to existing facts and fixtures.
- false — `ReferenceEquals` aggregate exemption fragile: Schema derivation and lint share one options instance, and the `ItemId` exemption is asserted by tests.
- false — `DescriptionLinter` should be internal: matches the public static `CatalogBuilder`/`SchemaDeriver` convention; no named consumer harm.
- low — finding codes as inline literals: no present consumer diverges; revisit when `describe --lint` and conformance vectors land.
- rejected — `SchemaDeriver` field-description change undocumented in the spec: the fix is a spec edit; behavior is asserted by the lint test's nested `ExternalId` description check.
- low/maybe-false — `$ref` and punctuation verdicts rest on uncommitted probes: no demonstrated false finding; the fix would add speculative fixtures.

## Implementation Notes

- Added immutable lint findings to each valid Operation descriptor. The linter walks effective serialized members and the exported Schema together, then sorts findings by pointer and code.
- Added an isolated Contracts fixture and focused tests for nested/collection pointers, renamed members, hollow descriptions, identifier and paging hints, empty findings, strict isolation, and deterministic serialization.
- Verification: Release solution build succeeded with zero warnings/errors; Core test project passed 126/126 with zero skipped; `git diff --check` passed.
- Review patches added field handling, field descriptions, clearer member guidance, and focused regression cases. Final Release build and Core tests passed (126/126); Abstractions tests passed (20/20), and Manifest tests passed (6/6), all with zero skipped.
- Commit message `feat: inspect description quality` passed the pinned `@commitlint/cli` 21.2.2 via `npx --no -- commitlint --edit /tmp/mcpcli-story16-commit-message.txt` (exit 0).
- Resumed review fixes cover nullable struct properties, all root envelope-bound identifier roles, and Command-specific paging and hollow descriptions. Release solution build passed with zero warnings/errors; Core tests passed 127/127 with zero skipped.
- Final review patched warning wording and added constructor-parameter and whitespace-only description coverage; no findings were deferred. The Release build and Core tests still passed (127/127), with zero warnings and errors.

## Spec Change Log

## Review Triage Log

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| Blind: a CLR property renamed to `ExternalId` gets no identifier hint | false: FR-7 defines this hint for a property whose declared name ends in `Id`; `[JsonPropertyName]` changes the wire name, not that declaration. | reject |
| Blind: a CLR `Limit` property serialized as `PageSize` gets no paging hint | false: AD-20 names Query Payload members `PageSize`, `Offset`, and `Cursor`; `Limit` is a different member even when renamed on the wire. | reject |
| Blind: serialized `[JsonInclude]` fields bypass identifier and paging checks | medium: a local .NET probe exported `ExternalId` and `PageSize` fields, but neither received its hint because only `PropertyInfo` enters those checks. The identifier hint must explain that the author needs a property, since the marker cannot target fields. | patch |
| Blind: a described `[JsonInclude]` field is reported as undescribed | medium: a local probe exported a field with `[Description]`, but `SchemaDeriver.Transform` omitted the description, so lint emitted a false missing-description warning. | patch |
| Blind: an envelope-owned member's missing-description message says callers supply it | low: `EnvelopeItemCommand.Tenant` is a mapped read-only member without `[Description]`; the lint message says callers should know what to supply, although the envelope fills it. | patch |
| Blind: punctuation and repeated spaces evade hollow-description lint | false: the PRD checks a description equal to the humanized name; `Hollow.` and internally repeated spaces are different strings. Trimming and case-insensitive equality cover the declared comparison. | reject |
| Blind: dictionary-value traversal has no focused test | low: `InspectNode` has an `additionalProperties` branch and a local probe exercised it, but the repository tests would not catch its removal. | patch |
| Edge: a serialized `ExternalId` field has no identifier hint | medium: the local probe confirms the field is in the Schema and the `PropertyInfo` guard skips it; same root cause as the blind field finding. | patch |
| Edge: a serialized `PageSize` field has no paging hint | medium: the local probe confirms the field is in the Schema and the `PropertyInfo` guard skips it; same root cause as the blind field finding. | patch |
| Edge claim: effective serialized members all receive identifier and paging checks | medium: the claim is disproved by the exported fields in the probe; same `PropertyInfo` guard. | patch |
| Verification gap: no multiword hollow-description assertion | low: the only hollow fixture is `HollowQuery`; removing Pascal-case splitting would pass the present tests while losing `Get Item` detection. | patch |
| Verification gap: no unmarked nested identifier assertion | low: the fixture checks top-level `ExternalId` and marked nested `MarkedId`; root-only identifier checks would pass while losing nested hints. | patch |
| Verification other: a repeated nested type behind `$ref` lacks a second finding | false: the reproduced `Dictionary<string, Inner>` plus `List<Inner>` schema points the latter to the former; lint already reports the one CLR `Inner.Missing` declaration at the referenced Schema property, so no distinct description gap is hidden. | reject |
| Blind: three `references/*` pointers appear in the baseline diff | false: all three pointer changes were present before this resumed implementation pass and are preserved as unrelated workspace changes; no story commit or staging includes them. | reject |
| Blind: spec is `in-review` while sprint status is `in-progress` | false: the review step advances the spec first, and sprint status advances when review completes; this is an intentional intermediate state. | reject |
| Blind: renamed `ExternalId` warning names only the serialized member | low: the suffix check uses the CLR name while the message uses `metadata.Name`, so a renamed wire member makes the advice harder to follow; retain the serialized pointer and name the CLR member in the message. | patch |
| Blind: renamed `PageSize` warning names only the serialized member | low: the paging check uses the CLR name while the message uses `metadata.Name`, so a renamed wire member obscures the reason for the warning; same message-source defect as the identifier warning. | patch |
| Blind: no parameter-only constructor description test | low: SchemaDeriver reads `AssociatedParameter`, but the lint fixture only applies property-targeted descriptions; add a parameter-only case to protect constructor-bound behavior. | patch |
| Blind: no whitespace-only property description test | low: the linter explicitly uses `IsNullOrWhiteSpace`, but no fixture exercises it; add a whitespace description to an already missing-description fixture member. | patch |
| Blind: only TenantId exercises root role exemption | low: the test covers one instance of `bindings.Values.Any`, whose branch applies identically to every bound role; extra role fixtures would repeat the same path without testing another decision. | reject |
| Blind: no single operation combines hollow and property findings | low: the hollow and property cases run separately, while every finding is sorted by the same comparator; changing fixtures and several assertions to combine them adds little regression protection. | reject |
| Blind: no lint fixture uses a serializer-options provider | low: CatalogBuilder passes the same module options to SchemaDeriver and DescriptionLinter, and existing SchemaTests cover provider options; a converter-backed fixture would add substantial setup without a demonstrated divergent path. | reject |

## Design Notes

Use pointers into the exported Schema: `/properties/<name>` for a root member, `/properties/<outer>/properties/<inner>` for nested objects, and `/properties/<collection>/items/properties/<inner>` through an array. This gives collection members a concrete RFC 6901 target without inventing a payload array index. A humanized type name removes only the trailing `Command` or `Query`, separates its Pascal-case words, and compares with the trimmed description without case sensitivity.
The PRD and addendum define `hollow_description` only for the Operation; the architecture table's property-name wording does not add a fifth lint shape.

## Verification

**Commands:**
- `dotnet build Hexalith.McpCli.slnx --configuration Release` — zero warnings and errors.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release` — all Core tests pass.

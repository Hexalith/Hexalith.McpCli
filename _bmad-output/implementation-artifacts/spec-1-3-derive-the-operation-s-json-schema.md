---
title: 'Derive the Operation’s JSON Schema'
type: 'feature'
created: '2026-09-25'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '12c73c562949d7c848cf85479c63135fcaac6d19'
context:
  - '_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Decorated Payloads have no reusable JSON Schema or matching validator, so an agent cannot know which arguments the gateway will accept.

**Approach:** Establish Core’s canonical Module Payload serialization, derive one closed Schema from that contract per Operation, and validate examples and Payloads against that same Schema. Pin the validator dependency in the owning Builds repository and consume it through the declared submodule.

## Boundaries & Constraints

**Always:** Pin `JsonSchema.Net` 9.4.0 upstream in Hexalith.Builds before Schema restore; update this repo’s Builds submodule pointer to that commit. Cache one read-only Payload options instance per Module, with provider converters before `JsonStringEnumConverter`, CLR casing unless overridden, case-sensitive names, null omission, unmapped-member rejection, and a tool-owned resolver. Keep Result options separate: Web defaults, camelCase, indented, camelCase string enums. Export with `JsonSchemaExporter`, normalize only a Command root to non-null object, close object schemas, and validate with `JsonSchema.Net` list output and JSON Pointer paths. Preserve property bindings and one Schema for future Catalog and executor use.

**Never:** Edit source inside `references/`, pin an inline package version, copy a provider resolver, infer identifier or envelope roles from names, let Module options serialize result/envelope fields, or build Catalog, CLI, MCP, or gateway execution in this story.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Mixed members | Required, nullable, enum, nested, collection, constructor-bound, get-only | Serializable members have correct names, descriptions, required/nullability, closed objects; unbound get-only is absent | N/A |
| Provider | Static provider with converter and conflicting settings | Read once; converter first, canonical casing/null/unmapped rules, owned resolver | Invalid provider produces no options |
| Identifiers | Marked, aggregate-mapped, CLR `Ulid`, unmarked `*Id`; both Module kinds | Only declared identifiers follow Module kind; CLR `Ulid` has ULID pattern | Non-string declared identifier is invalid |
| Envelope | Exact mapped roles and similarly named ordinary field | Only mapped fields become `readOnly` and optional | Invalid binding is rejected |
| Validation | Good/bad examples and Payload JSON | Same Schema accepts or lists all JSON Pointer locations | Malformed JSON or invalid Command root reports `/` |

</frozen-after-approval>

## Code Map

- `_bmad-output/planning-artifacts/epics.md:292` and `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md:74` define the requirements and AD-6/7/8 boundaries.
- `src/Hexalith.McpCli.Abstractions/HexalithModuleAttribute.cs`, `HexalithCommandAttribute.cs`, `HexalithQueryAttribute.cs`, `HexalithIdentifierAttribute.cs` expose providers, examples, and CLR roles; keep Abstractions dependency-free.
- `tests/Hexalith.McpCli.Sample.Contracts/` has converter-backed `SampleItemId`, constructor-bound records, and ignored get-only `AggregateId`.
- `Hexalith.McpCli.slnx`, `tests/Directory.Build.props` provide project/test conventions; `src/Hexalith.McpCli/` is a manifest-only scaffold.
- `/home/administrator/projects/hexalith/builds/Props/Directory.Packages.props` owns the pin; this repo’s `Directory.Packages.props` imports its Builds submodule first.

## Tasks & Acceptance

**Execution:**
- [x] `/home/administrator/projects/hexalith/builds/Props/Directory.Packages.props` and `references/Hexalith.Builds` pointer — pin upstream and select its commit without editing submodule source.
- [x] `src/Hexalith.McpCli.Core/Hexalith.McpCli.Core.csproj`, `Hexalith.McpCli.slnx`, `src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs` — add Core and canonical Payload/Result settings with Module options caching.
- [x] `src/Hexalith.McpCli.Core/Schema/PropertyBinding.cs`, `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs`, `src/Hexalith.McpCli.Core/Schema/PayloadValidator.cs` — resolve effective serialized members, export/transform Schema, and validate examples and Payloads; place additional public types in separate files.
- [x] `tests/Hexalith.McpCli.Core.Tests/SchemaTests.cs` and its `.csproj` — cover every matrix row, both identifier kinds, role escaping, provider read count/converter precedence, and shared-schema validation.

**Acceptance Criteria:**
- Given Module options and a decorated Payload, when Core derives its Schema, then it reflects the effective JSON contract, descriptions, declared roles, and identifier kind.
- Given valid and invalid examples or Payloads, when Core validates them, then the same stored Schema accepts or lists every violation location.
- Given the updated Builds revision, when the shipping solution restores and builds, then it consumes the central `JsonSchema.Net` pin and all existing tests pass.

### Review Findings

Code review of `12c73c5..da3536a` (2026-09-25). Layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; claims verified with a scratch probe against Core.

- [x] [Review][Patch] Envelope-role property types are never checked — resolved decision: `Tenant` and `Actor` must be `string`; `Correlation` and `IdempotencyKey` may be `string` or `Ulid` (nullable allowed); reject any other type as an invalid binding [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:116]
- [x] [Review][Patch] Envelope-role `required` stripping also hits nested collection/dictionary item objects — gate on the root (`context.Path` empty) instead of `PropertyInfo is null`; probe: `{"Tenant":"t","Lines":[{}]}` validates while deserialization throws for the item's missing required `Tenant` [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:227]
- [x] [Review][Patch] `Ulid` and converter-backed element types in collections/dictionaries are unconstrained — probe: `List<Ulid>` exports `{"type":"array"}` with no `items` and `{"Ids":[1,{},"x"]}` validates; apply the ULID string schema to `Ulid` elements and reject other opaque elements like direct members [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:167]
- [x] [Review][Patch] Nullable converter-backed declared identifier throws — `options.Converters.Any(c => c.CanConvert(propertyType))` uses `Nullable<T>`; probe: `[HexalithIdentifier] Sid? Id` with a provider `JsonConverter<Sid>` throws "does not serialize as a JSON string" [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:250]
- [x] [Review][Patch] Duplicate JSON property names validate the first value while the deserializer keeps the last — probe: `{"N":1,"N":"bad"}` is schema-valid; parse with `AllowDuplicateProperties = false` [src/Hexalith.McpCli.Core/Schema/PayloadValidator.cs:137]
- [x] [Review][Patch] Inherited `[HexalithIdentifier]` on an overriding property is ignored — `PropertyInfo.IsDefined(..., true)` ignores inheritance; probe: overridden `Key` exports plain `string`; use `Attribute.IsDefined` [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:161]
- [x] [Review][Patch] Test gap: non-object Command root rejection is untested — deleting the `Kind` check turns `typeof(string)` into an open `type: object` schema with no failing test [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:46]
- [x] [Review][Patch] Test gap: only the wrong-assembly provider failure is tested — missing `Options`, wrong type, and null-returning providers are uncovered; dropping `?? throw` would silently lose provider converters [src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs:56]
- [x] [Review][Patch] Test gap: nullable declared identifier `["string","null"]` type and `{"Id":null}` acceptance are untested [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:203]
- [x] [Review][Patch] Test gap: `[Description]` on identifier properties is never asserted (e.g. `RenameItemCommand.ItemId`) [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:188]
- [x] [Review][Defer] CLAUDE.md dependency allowlist omits `JsonSchema.Net` [src/Hexalith.McpCli.Core/Hexalith.McpCli.Core.csproj:9] — deferred: fix edits the shared agent-context files; the spec and architecture spine already approve the pin.
- [x] [Review][Defer] Validator is fail-open if evaluation is invalid but no node carries `Errors` [src/Hexalith.McpCli.Core/Schema/PayloadValidator.cs:171] — deferred: unverified (would be high); settle by confirming JsonSchema.Net 9.4 `List` output always attaches an error to a failing evaluation, or add a fallback `/` violation.

**Rejected:**

- `false` — Builds pointer `3716c34` is unfetchable: HEAD `4dc1319` already moves the gitlink to published `90670b7`, which contains the pin (`40fb0bb`).
- `false` — Non-nullable reference members export as nullable: probe shows `string Name` exports `{"type":"string"}` and rejects `null`.
- `false` — Payload may carry envelope values despite `readOnly`: the Envelope row and Design Notes prescribe optional `readOnly` that does not suppress validation; enforcement belongs to the executor.
- `false` — `ForModule` ignores a mismatched declaration after caching: supported Catalog construction reads the unique assembly marker (EC-05).
- `false` — String-kind opaque identifiers are unconstrained: String kind admits any string by definition; the probe limit is recorded in Implementation Notes.
- `low` — `isCommand` passed to both `Derive` and `Validate`: a mismatch needs a future caller bug and the fix adds public surface.
- `low` — Root violation pointer `/` instead of RFC 6901 `""`: the spec mandates `/`; changing it edits the spec.
- `low` — Faulted `Lazy` caches provider failures; `TargetInvocationException` escapes: provider failures are deterministic declaration errors.
- `low` — Mixed exception types for invalid declarations: no Catalog consumer exists yet to break.
- `low` — Spec bookkeeping (status, stale 12/12 count, absolute paths): the fix edits the spec; status is reset by this review.
- `low` — No positive Query-root nullability test: minor coverage nicety.
- `low` — `UlidPattern` rejects Crockford aliases `I/L/O` that `Ulid.TryParse` accepts: only non-canonical input is affected.
- `low` — Probe catch list omits `OverflowException` and similar: unlikely converter behavior on the fixed samples.
- `low` — Integer ranges unconstrained (`3000000000` for `int` validates): exporter limitation; per-type bounds add branches, and the gateway rejects.
- `low` — Abstract non-polymorphic member accepted: that contract cannot be deserialized regardless.
- `low` — `[JsonInclude]` `Ulid` field exports `{}`: contracts use properties and `[HexalithIdentifier]` targets properties only.

Code review of `12c73c5..abc331a` (2026-09-25, round 4). Layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; claims verified with a scratch probe referencing Core and the Sample Contracts.

- [x] [Review][Patch] Populate-handled get-only members are dropped — the resolver modifier removes any getter-only member without a constructor parameter, including `[JsonObjectCreationHandling(Populate)]` collections (property- or type-level) that STJ fills in place; probe: `List<string> Tags { get; } = []` with Populate exports `{"type":"object","additionalProperties":false}` and `{"Tags":["a"]}` fails Module deserialization with "could not be mapped" while default options deserialize it. Keep members whose effective creation handling is `Populate`. [src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs:109]
- [x] [Review][Patch] Test gap: non-nullable declared identifier's `type` and `null` rejection are unasserted — replacing the nullability computation with `true` fails no test while `{"ItemId":null,"Title":"x"}` becomes valid for `RenameItemCommand`; assert `type == "string"` and a violation at `/ItemId`. [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:231]
- [x] [Review][Patch] Test gap: a mapped `AggregateId` staying writable and required is unasserted — replacing both `Role != PropertyRole.AggregateId` filters with `true` fails no test while `ItemId` becomes `readOnly` and optional; assert no `readOnly` and `required` still contains the source. [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:245]
- [x] [Review][Patch] Test gap: a built-in STJ property-level converter staying non-opaque is unasserted — flipping the assembly comparison fails no test while `[JsonConverter(typeof(JsonStringEnumConverter<StatusValue>))]` members start throwing; add a fixture that derives with `"enum":["Pending","Complete"]`. [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:282]
- [x] [Review][Patch] Test gap: the `JsonConverterFactory` branch of the identifier probe is untested — probe shows a factory-backed `[HexalithIdentifier]` currently derives the ULID string schema, but every fixture converter is a plain `JsonConverter<T>`; add a factory-backed identifier fixture. [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:381]

**Rejected (round 4):**

- resolved decision (option 1) — Free-form members (`object`, `JsonElement`, `JsonNode`, and collections of them) are rejected as opaque: the rule is kept, so every Payload must be closable and a free-form member is an invalid declaration that story 1.5 diagnoses; no v1 or sibling Module Command/Query declares one (verified across `references/*/src/*.Contracts`).
- carried — Validator fail-open when no node carries `Errors`: already deferred in `deferred-work.md`.
- `low` — Declared attribute `Example`s never validated; Sample `CreateItemCommand`/`GetItemQuery` never derived: probe derives all three Sample operations; reading `Example` belongs to Catalog construction (1.4).
- reject — Implementation Notes cite superseded Builds commit `3716c34`: the fix edits this spec.
- reject — Range includes unrelated `pushall` and submodule bumps: informational; the `pushall` defects are already deferred.
- `low` — `TimeOnly` accepts any string after the `format` removal: schema looser than the deserializer and the gateway rejects, same class as the rejected integer ranges.
- `low` — String `Correlation`/`IdempotencyKey` roles lack a ULID pattern: `readOnly` envelope members the executor fills; the earlier decision allows `string`.
- `low` — Type-level `[Description]` ignored: the spec sources descriptions from properties; nested description lint is story 1.6.
- `false` — Data-annotation constraints/defaults missing: they are not part of the STJ contract the spec asks the Schema to reflect.
- `low` — No `$schema` keyword: JsonSchema.Net 9.4 and MCP both default to 2020-12.
- `low` — Empty `required: []` left after stripping: probe confirms it; valid 2020-12, validator unaffected.
- `low` — `PayloadViolation` lacks keyword/schema location: the spec requires JSON Pointer locations; error documents belong to story 2.9.
- carried — Public API exceptions undocumented: same class as the rejected mixed exception types.
- `false` — Provider-less Modules do not reuse `McpCliJson.Payload`: the spec requires one cached instance per Module, which `ForModule` provides.
- `low` — `CollectDuplicates` unbounded recursion and double walk: depth is bounded by the parsed document's `MaxDepth`; the second walk is negligible.
- `low` — `DerivedSchema.Node` deep-copies per read: no consumer exists yet.
- carried — `ForModule` faulted `Lazy` and declaration mismatch after caching (VG other, EC): rejected in earlier rounds (EC-05, R3-EC-10).
- `false` — `DateTime`/`DateTimeOffset` `date-time` rejects offset-less values: probe shows `"2024-01-01T10:00:00Z"` satisfies both; a stricter-but-satisfiable schema is accepted (R3-BH-08).
- carried — Integral ranges and `1.0` for `int` unconstrained: rejected in earlier rounds.
- `low` — Dictionary non-string keys unconstrained: same class as the rejected R3-EC-07.
- `false` — Role-bound `required`/constructor members stripped from `required` fail deserialization: the executor injects envelope values before submission; the Schema describes caller input.
- carried — Payload-supplied envelope values pass `readOnly`: rejected by Design Notes.
- carried — Probe catch list omits other converter exceptions: rejected in earlier rounds.
- carried — Strict String-kind converter rejects every probe sample: rejected as R3-EC-05.
- `low` — `[HexalithIdentifier]` on a string enum throws: enum identifiers are an unlikely contract shape; the fix adds a branch.
- `false` — Query root admits `null`: the spec normalizes only a Command root.

Code review of `12c73c5..365867c` (2026-09-25, round 5). Layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor; claims verified with a scratch probe referencing Core. The Acceptance Auditor ran Core tests 54/54.

- [ ] [Review][Patch] Test gap: no test validates a non-object Query payload. `SchemaTests.cs:547` passes `default(JsonElement)` with `isCommand: false`, so the `Undefined` guard returns first. If `isCommand &&` is dropped from the guard, every scalar Query payload is rejected as "A Command payload must be a JSON object." and no test fails. The probe shows a `typeof(string)` Query schema accepts `"abc"` and rejects `1`; assert both, the `1` case at `/`. [src/Hexalith.McpCli.Core/Schema/PayloadValidator.cs:50]
- [ ] [Review][Patch] Test gap: no test checks that `Derive` rejects options that are not read-only. Every `Derive` call passes cached, already read-only options. Deleting the `IsReadOnly` guard would let a schema be built from non-Module options (default resolver, unmapped members allowed), and no test would fail. The probe confirms `new JsonSerializerOptions()` currently throws `ArgumentException`; assert it. [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:35]
- [ ] [Review][Patch] Test gap: no test checks that Module options still append the canonical `JsonStringEnumConverter` after provider converters. `ProviderIsReadOnceAndOnlyConvertersAreCopied` asserts only `Converters[0..2]`, and `CanonicalEnumConverterRejectsIntegerInput` uses the provider-less `McpCliJson.Payload`. Assert that the Module options' last converter is `JsonStringEnumConverter` and that the converter count is provider converters plus one. [src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs:78]

**Rejected (round 5):**

- carried: Validator fails open when no node carries `Errors` (BH, EC, AA). Already deferred in `deferred-work.md`.
- carried: A duplicate property name hides the Schema's other violations (AA). Rejected as R3-BH-03.
- carried: Declared `Example` values are never validated (AA). Rejected in round 4; this belongs to Catalog construction (story 1.4).
- carried: `JsonSchema.Net` is missing from the CLAUDE.md allowlist (AA). Already deferred.
- reject: Implementation Notes cite superseded Builds commit `3716c34` (AA). The fix edits this spec.
- `false`: Missing-member errors point at the parent object (AA). This matches AD-7's `InstanceLocation` rule; the reviewer marked it informational.
- `low`: The resolver modifier also drops get-only members when Module options serialize (AA). AD-7 names the transform as the mechanism, but the executor rebuilds Payloads as JSON, never from a CLR instance. STJ also ignores a getter-only member on read. No harm was shown, and the fix would rework the approach.
- `false`: JsonSchema.Net 9.4 only annotates `format` (EC). The probe rejects `{"Id":"abc","At":"nope"}` at `/Id` (`uuid`) and `/At` (`date-time`).
- carried: A property named `""` shares the root pointer `/` (EC). Rejected as R3-EC-08.
- carried: Dictionary keys that are not strings are unconstrained (EC). Rejected as R3-EC-07.
- carried: A declared `Guid`/`DateTime` identifier under Ulid kind can never be satisfied (EC). Rejected as R3-BH-02.
- carried: An undefined `PropertyRole` value is accepted (EC). Rejected as R3-EC-04.
- carried: A role member declared with C# `required` fails deserialization once it is stripped from `required` (EC). Rejected `false` in round 4 because the executor fills envelope values first.
- carried: The probe's catch list omits other converter exceptions (EC). Rejected in earlier rounds.
- carried: `ForModule` caches a faulted `Lazy` and ignores a mismatched declaration (EC). Rejected as EC-05 and R3-EC-10.
- carried: A provider getter that throws surfaces `TargetInvocationException` (EC). Rejected `low` in round 1.
- carried: A recursive `$ref: "#"` payload reuses the modified root (EC). Rejected as R3-BH-05.
- `low`: An identifier attribute declared on an interface property is not recognized (EC). `Attribute.IsDefined` follows class inheritance, and .NET does not inherit attributes from interfaces. No Contract uses this pattern, and supporting it adds an interface walk.
- `low`: The invalid-provider test leaves a faulted CoreLib cache entry, and the static `ReadCount` depends on check order (EC, BH). No other test passes CoreLib. A reordering would make the test fail, not pass wrongly.
- `low`: Each `DerivedSchema` registers in `SchemaRegistry.Global` under a random URI (BH). The probe confirms `registered=True`, but the Catalog calls `Derive` once per Operation, so growth is bounded. Random GUID URIs never collide.
- `low`: Payload options do not set `AllowDuplicateProperties = false` (BH). No Core path deserializes a Payload without first running the validator's duplicate rejection, and the spec's canonical option list does not include it.
- `low`: Null omission drops a `required T?` member set to null, so re-serialization fails deserialization (BH). The probe confirms `{"Title":"t"}` then "missing required properties". AD-7/AD-9 rebuild Payloads as JSON and never serialize a contract instance, and the only `required T?` members in sibling Contracts (Memories `V1` snapshots) are not Operation Payloads. Null omission is also a spec-mandated canonical setting.
- `low`: RFC 6901 escaping exists twice (BH). The two copies are identical and correct, and they only drift if one is edited; merging them adds a shared helper.
- `false`: A `public const UlidPattern` goes stale in consuming assemblies (BH). Every consumer ships in this repo's single tool package and is rebuilt together (AD-17).
- `false`: Mixed `&&`/`||` without parentheses (BH). The reviewer confirms the conditions are correct under C# precedence, and the Release build has zero warnings.
- `low`: Rejection messages omit the containing type and path (BH). Diagnostic wording belongs to story 1.5 (already recorded for free-form members), and there is no consumer yet.
- `low`: Tests match substrings of serialized JSON (BH). Each cited assertion was checked. No sibling member name collides, and `ToJsonString` does not escape `tenant/~`, so none can pass wrongly today.
- `low`: Flat test project and one large `SchemaTests` class (BH). This matches the repo's flat convention, and test names identify the component.
- `low`: `EvaluationOptions` is allocated on every validation (BH). The cost is negligible, and sharing a mutable options object adds a hazard.

## Implementation Notes

- Added Core serialization, effective property bindings, schema export, and one stored JsonSchema.Net validator. Opaque identifier converters are probed through Module options; output that varies by value cannot be proven exhaustively from a finite probe and remains subject to Payload validation.
- Pinned `JsonSchema.Net` 9.4.0 in writable Hexalith.Builds commit `3716c34130ef8a65be9dcef9f30ea583f9c1d1a3` and selected that commit in the root-declared submodule. It is local and unpushed; another checkout needs the Builds commit available upstream before it can fetch this pointer.
- Independently verified `dotnet restore Hexalith.McpCli.slnx`, Release solution build (zero warnings), Core tests 12/12, Abstractions tests 20/20, Manifest tests 6/6, and whitespace checks in both repositories including new files. The Core assets resolve `JsonSchema.Net/9.4.0`.
- Validated the exact Builds commit message `build(deps): pin JsonSchema.Net for MCP schema validation` with `node_modules/.bin/commitlint --edit <exact-candidate-file>` using `@commitlint/cli@21.2.2`; exit 0.
- Review patches registered Core tests in CI, rejected unsupported opaque, extension-data, and polymorphic schemas explicitly, tightened role and identifier validation, and added regression cases. Final local verification: Release solution build with zero warnings; Core 21/21, Abstractions 20/20, Manifest 6/6; `actionlint .github/workflows/ci.yml` and both repositories' whitespace checks passed.
- Second review patches (10/10): envelope roles now type-checked (`Tenant`/`Actor` `string`; `Correlation`/`IdempotencyKey` `string` or `Ulid`, nullable allowed); envelope `required` stripping and `readOnly`/aggregate marking gated to root properties; opaque collection/dictionary elements get the ULID string schema when `Ulid`/`Ulid?` and are otherwise rejected; nullable converter-backed identifiers probe the underlying type; `[HexalithIdentifier]` read with `Attribute.IsDefined` so overrides inherit it; string payloads parse with `AllowDuplicateProperties = false` and the `JsonElement` overload walks for duplicates, both reporting `/` with the duplicate's pointer in the message. Added regression tests for each plus the non-object Command root, all three invalid provider shapes (emitted into fresh dynamic assemblies to bypass the per-assembly cache), nullable identifiers, and identifier descriptions. The new behavioral tests fail on the pre-patch Core (14 failures) and pass after it. Verification: Release solution build with zero warnings; Core 45/45, Abstractions 20/20, Manifest 6/6; `git diff --check` clean including new files.
- Round 4 review patches (5/5): the canonical resolver keeps getter-only members whose effective creation handling is `Populate` (property or type level); added regression assertions for non-nullable declared identifiers (`type` `"string"`, `null` reported at the member), a mapped `AggregateId` staying writable and required, a System.Text.Json property-level converter staying non-opaque, and a factory-backed declared identifier. Each new assertion fails when its guarded behavior is mutated. Resolved decision: free-form members stay rejected (follow-up for story 1.5 in `deferred-work.md`). Verification: Release solution build with zero warnings; Core 54/54, Abstractions 20/20, Manifest 6/6; `git diff --check` clean including new files.

## Spec Change Log

## Review Triage Log

| Finding | Verdict and evidence | Route |
| --- | --- | --- |
| VG-01: Core tests absent from CI | medium — `.github/workflows/ci.yml` lists only Abstractions and Manifest tests, so the normal gate misses all new Schema tests. | patch |
| VG-02: missing-required validation untested | medium — tests inspect `required` but never validate a payload lacking a required member; a broken required-error mapping could escape. | patch |
| VG-03: local Builds commit not fetchable remotely | false — the parent gitlink change is uncommitted and unpushed, so no fresh checkout can yet request it; the required publication order is recorded in Implementation Notes. | reject |
| BH-01: ULID regex permits trailing newline | medium — a local probe found the pattern matches a 26-character ULID followed by newline while `Ulid.TryParse` rejects it. | patch |
| BH-02: converter-backed Command root rejected | false — an opaque root converter supplies no object property metadata with which to derive the required closed Command schema; rejection is the supported failure. | reject |
| BH-03: whitespace role omitted | medium — `string.IsNullOrWhiteSpace` silently skips an explicitly supplied invalid role. | patch |
| BH-04: setter-only envelope role rejected | medium — a local probe found `Get == null`, `Set != null`, yet `ResolveBindings` throws for a deserializable tenant property. | patch |
| BH-05: ordinary opaque converter accepts invalid values | medium — exporter schema `true` and the transform's early return let local validation accept values the converter cannot read. | patch |
| BH-06: opaque mapped property loses annotations | medium — the same early return skips `[Description]` and envelope `readOnly` for converter-backed properties. | patch |
| BH-07: extension data conflicts with closure | medium — a local probe serialized an extension-data field but the derived `additionalProperties: false` schema rejected it. | patch |
| BH-08: polymorphic derived value rejected | medium — a local probe serialized a derived object but the closed base schema rejected its derived member. | patch |
| BH-09: integer enum accepted outside schema | medium — canonical `JsonStringEnumConverter` deserialized `1` while its exported schema admits enum names. | patch |
| BH-10: undefined JsonElement throws | medium — `PayloadValidator.Validate` on `default(JsonElement)` throws `ArgumentOutOfRangeException` in a local probe. | patch |
| EC-01: opaque mapped field appears writable | medium — same early return as BH-06, with a mapped envelope property. | patch |
| EC-02: extension-data mismatch | medium — same demonstrated mismatch as BH-07. | patch |
| EC-03: whitespace role disappears | medium — same demonstrated behavior as BH-03. | patch |
| EC-04: undefined IdentifierKind uses String branch | medium — an undefined enum value bypasses the ULID branch without being rejected. | patch |
| EC-05: alternate declaration after cache | false — supported Catalog construction reads the unique assembly marker once; no supported caller supplies a second declaration for that assembly. | reject |
| EC-06: undefined JsonElement reported valid | false — local probe shows `Evaluate` throws rather than returning valid; BH-10 records the real failure. | reject |
| EC-07: opaque ordinary converter passes invalid payload | medium — same exporter `true` mismatch as BH-05. | patch |
| PA-01: opaque Query root remains unconstrained | medium — postpatch audit found the member-only rejection left a converter-backed Query root exporting boolean `true`; a focused regression proved it. | patch |
| R3-VG-01: array-element duplicate names untested on the `JsonElement` path | medium — pre-verified gap: deleting the array branch of `CollectDuplicates` fails no test, while `Evaluate` alone accepts `{"Lines":[{"N":1,"N":"bad"}]}`. | patch |
| R3-VG-02: nullable value-type member with a property-level `[JsonConverter]` | medium — pre-verified: STJ wraps the converter in `NullableConverter<T>`, the exporter emits T's default object contract, so a declared identifier throws in `Derive` and an ordinary member validates `{"Value":{"Value":"abc"}}` that deserialization rejects; grouped with the layer's matching Other finding. | patch |
| R3-BH-01: `format` is never validated | false — probe: `{"Id":"abc"}` for a `Guid` member is rejected at `/Id`; JsonSchema.Net 9.4 validates `format` by default. | reject |
| R3-TR-01: `TimeOnly` members are unsatisfiable (found verifying R3-BH-01) | medium — probe: exporter `format: time` requires an offset, so `"14:30:00"` fails validation while `"14:30:00Z"` passes validation and fails deserialization. | patch |
| R3-BH-02: declared `Guid`/`DateTime` identifier under Ulid kind is unsatisfiable | low — a misdeclaration that Catalog diagnostics (stories 1.4/1.5) own; the fix adds per-type branches. | reject |
| R3-BH-03: duplicate names return early, at `/`, differently per overload (with R3-EC-11) | low — a duplicate-name document is treated as malformed JSON, which the matrix reports at `/`; the overloads differ only in message text. | reject |
| R3-BH-04: `Collect` includes errors from passing combinator branches | false — accepted contracts export no `anyOf`/`oneOf`/`if`; polymorphism, the only exporter source of combinators, is rejected. | reject |
| R3-BH-05: self-referencing payload `$ref: "#"` inherits the modified root | low — no Command payload contains itself; a guard adds a branch. | reject |
| R3-BH-06: `[Description]` on a positional record parameter is dropped | medium — probe: `record PR([Description("param desc")] string Name)` exports `Name` without `description`; that is the default C# attribute target. | patch |
| R3-BH-07: identifier nullability uses `IsGetNullable` | low — the exporter's own nullability is OR-ed in via `AllowsNull`; divergence needs `[AllowNull]`/`[DisallowNull]` on an identifier. | reject |
| R3-BH-08: `RespectNullableAnnotations`/`RespectRequiredConstructorParameters` off | false — the schema is stricter than the deserializer, so no schema-valid payload fails deserialization; the canonical option list does not include them. | reject |
| R3-BH-09: unknown-member rejection location unasserted | medium — `SharedSchemaReportsAllViolationsAndMalformedRoot` sends `"Extra":1` but asserts only `/ItemId` and `/Title`; probe shows `/Extra` is reported. | patch |
| R3-BH-10: `/pushall` step 3 commits on a detached submodule HEAD and stages with `add -A` | medium — step 3 commits before step 4 checks out the default branch, orphaning the commit; not caused by this story. | defer |
| R3-BH-11: `/pushall` fixed commit messages bypass commitlint and `allowed-tools` blocks validation | medium — `allowed-tools: Bash(git *)` cannot run commitlint or project validation that step 7 requires; not caused by this story. | defer |
| R3-BH-12: four identical `pushall` copies without a sync check | low — drift needs a new sync script; not caused by this story. | reject |
| R3-BH-13: spec records disagree with the diff | reject — the fix edits this build's spec. | reject |
| R3-BH-14: `using Shouldly;` out of order in `SchemaTests.cs` | low — cosmetic; direct reorder. | patch |
| R3-BH-15: role binding misses `new`-hidden and non-public `[JsonInclude]` members | low — envelope members are plain public properties; the fix rewrites matching. | reject |
| R3-EC-01: validator fail-open when no node carries `Errors` (with R3-EC-12) | carried — already deferred by the previous review and recorded in `deferred-work.md`. | reject |
| R3-EC-02: lone UTF-16 surrogate throws `ArgumentException` | low — probe: `Validate(schema, "{\"Id\":\"\uD800\"}", true)` throws instead of reporting `/`; direct catch-filter fix. | patch |
| R3-EC-03: primitive Query root with all-null role names throws | medium — probe: `Derive(typeof(string), …, false, {Tenant: null})` throws; a Catalog will pass every role key. | patch |
| R3-EC-04: undefined `PropertyRole` value accepted | low — caller bug on Core's own enum; a guard adds a branch. | reject |
| R3-EC-05: strict String-kind converter rejects every probe sample | low — no known contract; treating indeterminate as string would accept numeric converters. | reject |
| R3-EC-06: probe catch list omits other converter exceptions | carried — rejected `low` by the previous review. | reject |
| R3-EC-07: `Dictionary<Ulid,T>` keys unconstrained | low — rare contract shape; the fix adds a `propertyNames` branch. | reject |
| R3-EC-08: empty-name member violation reports `/` like the root | reject — the spec mandates `/` for the root. | reject |
| R3-EC-09: get-only `[JsonExtensionData]` removed before the extension-data guard | low — probe: the member disappears and the schema closes silently instead of raising the NotSupported rejection; direct fix skips extension data in the resolver modifier. | patch |
| R3-EC-10: faulted `Lazy` caches provider failures | carried — rejected `low` by the previous review. | reject |
| R3-EC-13: integer ranges unconstrained | carried — rejected `low` by the previous review. | reject |

## Design Notes

Pass resolved serialized roles into the Schema transform. Catalog later owns invalid declaration diagnostics. Preserve nested nullability when fixing a Command root. `readOnly` must not suppress validation.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` and `dotnet build Hexalith.McpCli.slnx --configuration Release` — successful central restore and warning-free build.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release` — Schema and validator cases pass.
- `dotnet test tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj --configuration Release` and `dotnet test tests/Hexalith.McpCli.Manifest.Tests/Hexalith.McpCli.Manifest.Tests.csproj --configuration Release` — existing suites pass individually.
- `git diff --check` in both owning repositories — no whitespace errors.

---
title: 'Derive the Operation’s JSON Schema'
type: 'feature'
created: '2026-09-25'
status: 'in-progress'
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

- [ ] [Review][Patch] Envelope-role property types are never checked — resolved decision: `Tenant` and `Actor` must be `string`; `Correlation` and `IdempotencyKey` may be `string` or `Ulid` (nullable allowed); reject any other type as an invalid binding [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:116]
- [ ] [Review][Patch] Envelope-role `required` stripping also hits nested collection/dictionary item objects — gate on the root (`context.Path` empty) instead of `PropertyInfo is null`; probe: `{"Tenant":"t","Lines":[{}]}` validates while deserialization throws for the item's missing required `Tenant` [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:227]
- [ ] [Review][Patch] `Ulid` and converter-backed element types in collections/dictionaries are unconstrained — probe: `List<Ulid>` exports `{"type":"array"}` with no `items` and `{"Ids":[1,{},"x"]}` validates; apply the ULID string schema to `Ulid` elements and reject other opaque elements like direct members [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:167]
- [ ] [Review][Patch] Nullable converter-backed declared identifier throws — `options.Converters.Any(c => c.CanConvert(propertyType))` uses `Nullable<T>`; probe: `[HexalithIdentifier] Sid? Id` with a provider `JsonConverter<Sid>` throws "does not serialize as a JSON string" [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:250]
- [ ] [Review][Patch] Duplicate JSON property names validate the first value while the deserializer keeps the last — probe: `{"N":1,"N":"bad"}` is schema-valid; parse with `AllowDuplicateProperties = false` [src/Hexalith.McpCli.Core/Schema/PayloadValidator.cs:137]
- [ ] [Review][Patch] Inherited `[HexalithIdentifier]` on an overriding property is ignored — `PropertyInfo.IsDefined(..., true)` ignores inheritance; probe: overridden `Key` exports plain `string`; use `Attribute.IsDefined` [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:161]
- [ ] [Review][Patch] Test gap: non-object Command root rejection is untested — deleting the `Kind` check turns `typeof(string)` into an open `type: object` schema with no failing test [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:46]
- [ ] [Review][Patch] Test gap: only the wrong-assembly provider failure is tested — missing `Options`, wrong type, and null-returning providers are uncovered; dropping `?? throw` would silently lose provider converters [src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs:56]
- [ ] [Review][Patch] Test gap: nullable declared identifier `["string","null"]` type and `{"Id":null}` acceptance are untested [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:203]
- [ ] [Review][Patch] Test gap: `[Description]` on identifier properties is never asserted (e.g. `RenameItemCommand.ItemId`) [src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:188]
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

## Implementation Notes

- Added Core serialization, effective property bindings, schema export, and one stored JsonSchema.Net validator. Opaque identifier converters are probed through Module options; output that varies by value cannot be proven exhaustively from a finite probe and remains subject to Payload validation.
- Pinned `JsonSchema.Net` 9.4.0 in writable Hexalith.Builds commit `3716c34130ef8a65be9dcef9f30ea583f9c1d1a3` and selected that commit in the root-declared submodule. It is local and unpushed; another checkout needs the Builds commit available upstream before it can fetch this pointer.
- Independently verified `dotnet restore Hexalith.McpCli.slnx`, Release solution build (zero warnings), Core tests 12/12, Abstractions tests 20/20, Manifest tests 6/6, and whitespace checks in both repositories including new files. The Core assets resolve `JsonSchema.Net/9.4.0`.
- Validated the exact Builds commit message `build(deps): pin JsonSchema.Net for MCP schema validation` with `node_modules/.bin/commitlint --edit <exact-candidate-file>` using `@commitlint/cli@21.2.2`; exit 0.
- Review patches registered Core tests in CI, rejected unsupported opaque, extension-data, and polymorphic schemas explicitly, tightened role and identifier validation, and added regression cases. Final local verification: Release solution build with zero warnings; Core 21/21, Abstractions 20/20, Manifest 6/6; `actionlint .github/workflows/ci.yml` and both repositories' whitespace checks passed.

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

## Design Notes

Pass resolved serialized roles into the Schema transform. Catalog later owns invalid declaration diagnostics. Preserve nested nullability when fixing a Command root. `readOnly` must not suppress validation.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` and `dotnet build Hexalith.McpCli.slnx --configuration Release` — successful central restore and warning-free build.
- `dotnet test tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Release` — Schema and validator cases pass.
- `dotnet test tests/Hexalith.McpCli.Abstractions.Tests/Hexalith.McpCli.Abstractions.Tests.csproj --configuration Release` and `dotnet test tests/Hexalith.McpCli.Manifest.Tests/Hexalith.McpCli.Manifest.Tests.csproj --configuration Release` — existing suites pass individually.
- `git diff --check` in both owning repositories — no whitespace errors.

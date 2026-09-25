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

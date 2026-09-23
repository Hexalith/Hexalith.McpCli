# Architecture validation — adversarial lens — 2026-09-23

**Verdict: changes needed before the executor contract is treated as complete.**

Severity counts: **0 Critical, 2 High, 1 Medium, 0 Low**. Mechanical lint passed with zero findings (parent-provided evidence). This pass identifies behavioral seams that mechanical lint cannot check. No spine, PRD, addendum, or epic file was changed.

## Scope and evidence

Reviewed the current `ARCHITECTURE-SPINE.md` and its resumed `.memlog.md`, the final PRD and addendum, current `epics.md`, the root baseline instructions, and relevant EventStore/Tenants/Parties source. The existing source reconciliations, caller-only idempotency policy, fake/live conformance split, manifest ordering, and explicit upstream readiness prerequisites were treated as settled constraints.

Path abbreviations below resolve from `/home/administrator/projects/hexalith/mcpcli/`:

- **Spine:** `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md`
- **PRD:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md`
- **Addendum:** `_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md`
- **Epics:** `_bmad-output/planning-artifacts/epics.md`

The local .NET runtime is the spine's pinned SDK **10.0.401**, runtime **10.0.12**. Focused scratch probes used that runtime and **JsonSchema.Net 9.4.0**. They are validation evidence, not repository implementation or a claim that a production tool exists.

## ADV-001 — High — Bind the invoked call kind to the descriptor kind

**Evidence:** Spine `AD-5` at line 84 defines distinct `SendCommandArguments` and `RunQueryArguments`. `AD-9` at line 108 resolves a descriptor, applies availability, validates, and constructs one Gateway request without requiring the call kind to match `OperationDescriptor.Kind`. `AD-12` at line 126 declares `run_query` read-only. `AD-19` at line 168 describes Command and Query aggregate routing but adds no kind check. PRD lines 160, 263, 294, and 339–358 identify the two kinds and surfaces without specifying a mismatch response. Epics lines 625–633 and 700–703 test only matching cases.

**Counterexample:** Invoke `run_query` (or CLI `query`) with `operation: parties.create-party`, valid Command Payload, Tenant, and aggregate identifier in a session that permits writes. One executor builder dispatches according to the resolved descriptor and submits a Command through a tool advertised as read-only. Another dispatches according to `RunQueryArguments` and constructs a Query request using Command routing, producing a Gateway rejection or a different result shape. Both follow the stated resolution/pipeline decisions; no AD says to reject this cross-kind pair. The success branch for `run_query` also cannot represent the first implementation's Command result correctly.

This is separate from Read-only Mode: the shared descriptor-based gate still blocks writes in a read-only session. The risk is a supposedly read-only tool mutating state in a normal session and independently implemented call models disagreeing.

**Minimal fix:** In Core, require `SendCommandArguments` to resolve a `write` descriptor and `RunQueryArguments` to resolve a `read` descriptor before request construction. Bind the error and precedence explicitly, preferably the existing `validation_failed` variant with `/operation`, and require zero Gateway calls. Add the two cross-kind cases to direct-executor and head-conformance criteria. No new tool or public error-code family is needed.

**Disposition:** Architecture correction, with corresponding execution-story acceptance cases.

## ADV-002 — High — An advertised optional Envelope field can make aggregate-accessor deserialization fail before it is filled

**Evidence:** Spine `AD-7` line 96 removes Envelope-filled properties from Schema `required`; `AD-9` line 108 resolves the aggregate identifier before resolving Actor and rebuilding the Payload; `AD-19` line 168 implements the interface accessor by deserializing that pre-fill Payload with the Module options and calling `ICommandContract.AggregateId`. `AD-9` maps an escaping exception to `internal_error`. PRD lines 236–240 promise that Envelope-filled members can be omitted; lines 350–355 require the accessor and subsequent fill. Epics lines 321–324, 715–718, and 740–757 preserve those commitments.

**Counterexample:** An allowed interface-routed Command has `required string Id`, `required string Tenant`, `AggregateId => Id`, and declares `tenantProperty = Tenant`. The caller follows the advertised Schema and submits `{"Id":"party-1"}` with session Tenant `acme`. The Schema accepts the Payload. The AD-19 accessor then deserializes it before the AD-9 fill; System.Text.Json throws because `Tenant` is missing. The intended valid call becomes `internal_error` and never reaches the fill step. A Catalog/Schema builder and executor builder can each follow their AD exactly and still fail to interoperate.

This is a supported-contract counterexample, not a claim that today's undecorated Tenants Command already declares such a property. The product explicitly supports interface-routed Commands, required members, and Envelope-filled fields together.

**Reproduction:** `dotnet run /tmp/mcpcli-adversarial-20260923/probe.cs` on SDK 10.0.401/runtime 10.0.12 exited 0 and reported:

```text
Pre-fill accessor result: JsonException: JSON deserialization for type 'ExampleCommand' was missing required properties including: 'Tenant'.
Filled accessor: party-1
```

The second probe below also confirms that the relevant AD-7 Schema accepts the omitted-Tenant document. The first probe produced expected standalone-file trimming-analysis warnings, but ran successfully; no application was built or changed.

**Minimal fix:** Bind a single accessor preparation policy. Resolve and insert the non-aggregate Envelope fields needed by contract deserialization before invoking the interface getter, or define a dedicated accessor-deserialization contract that permits omission of exactly the named Envelope-filled members and makes dependencies on unresolved values explicit. Preserve final rebuilt-Payload validation. Add a Command fixture with a C# `required` or `[JsonRequired]` Envelope-filled property that is omitted by the caller and succeeds when its session value exists. Merely remapping this exception to `validation_failed` would still violate the advertised omission contract.

**Disposition:** Architecture sequencing correction; add a cross-story fixture spanning Schema, Catalog accessor, and execution.

## ADV-003 — Medium — Default exporter root nullability admits an invalid Command Payload

**Evidence:** Spine `AD-6` line 90 selects the canonical serializer options. `AD-7` line 96 uses `JsonSchemaExporter.GetJsonSchemaAsNode` and transforms descriptions, identifiers, writable members, requiredness, and `additionalProperties`; it does not constrain root nullability. `AD-9` line 108 relies on this stored Schema at both validation passes. PRD lines 332–337 require invalid Payloads to be stopped before the Gateway. The actual Command request validator at `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/SubmitCommandRequestValidator.cs:77–79` requires `Payload.ValueKind == JsonValueKind.Object`.

**Counterexample:** The .NET exporter emits root `type: ["object", "null"]` for an ordinary Command class. The specified AD-7 transformations retain that union, so the Schema accepts JSON `null`, even when required object members exist. For a property-accessor Command with an explicit aggregate identifier and no Envelope-filled properties, an implementation that treats an absent pointer as null can resolve the explicit identifier and pass both Schema validations, then submit the invalid null Payload. An interface-accessor implementation can instead fail while dereferencing a deserialized null. Neither supplies the promised local, stable validation outcome. Independently built Schema and executor components therefore disagree about whether successful validation guarantees an object.

**Reproduction:** `dotnet run /tmp/mcpcli-adversarial-20260923/null-schema.cs` exited 0 using SDK 10.0.401/runtime 10.0.12 and JsonSchema.Net 9.4.0. The probe enables nullable reference types, applies the AD-6 settings and relevant AD-7 member transformations, and evaluates the result with `OutputFormat.List`:

```text
Payload null: IsValid=True
Payload {"Id":"party-1"}: IsValid=True
{
  "type": ["object", "null"],
  "properties": {
    "Id": { "type": "string" },
    "Tenant": { "type": "string", "readOnly": true }
  },
  "required": ["Id"],
  "additionalProperties": false
}
```

**Minimal fix:** Make Command Payload root shape an invariant: expose a non-null object root and reject non-object roots as `validation_failed` at `/` with zero Gateway calls. Apply the restriction at the operation root without stripping legitimate nested nullability. State the Query root policy separately if it differs, since its Gateway validator accepts broader JSON. Add `null` and non-object root cases to validation fixtures.

**Disposition:** Schema/executor contract correction; no upstream package change is required.

## Deliberately not counted

- Parties Aspire publication, first decorated Contracts pins, Builds catalog additions, and CI source compilation are already explicit prerequisites (Spine lines 325–329); their unfinished state is not a newly discovered architectural hole.
- The current PRD resolves unknown Modules, missing module arguments, deterministic duplicate ordering, and filtered MCP ToolCollection dispatch. Those were not re-reported.
- The nullable `idempotencyKeyProperty` case with a Payload value and no argument could benefit from explicit clearing/preservation wording. However, PRD line 355 and Epics lines 745–748 repeat the conditional overwrite policy, and this pass did not prove an independent concrete Gateway failure. It is not included in the severity counts.
- No production conformance run was attempted: the repository is still a planning scaffold and the upstream readiness gates are documented. The scratch probes establish only the stated schema/serializer behavior.

## Tooling evidence and limitations

- `dotnet --info`: SDK 10.0.401/runtime 10.0.12 confirmed.
- `dnx dotnet-inspect -y -- member JsonSchemaExporter --platform System.Text.Json --oneline -10`: rejected `--oneline` by the installed CLI; retry without that unsupported flag succeeded and confirmed `JsonSchemaExporter` from System.Text.Json 10.0.12.
- The initial null-schema probe passed `JsonNode` to a JsonSchema.Net 9.4.0 API requiring `JsonElement`; the corrected probe above compiled and ran successfully. This was probe setup, not a product finding.
- Root `.editorconfig` and `.gitattributes` do not yet exist (`cat .editorconfig .gitattributes` returned missing-file errors). The only persisted repository change in this pass is this validation artifact.

## Reproducible combined probe

Save the following as `reproduce.cs` in a scratch directory and run `dotnet run reproduce.cs` with SDK 10.0.401. It uses JsonSchema.Net 9.4.0 and contains both demonstrations so the evidence survives cleanup of the original `/tmp` paths.

```csharp
#:package JsonSchema.Net@9.4.0
#:property PublishAot=false
#:property Nullable=enable
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Schema;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Json.Schema;

var options = new JsonSerializerOptions {
    PropertyNamingPolicy = null,
    PropertyNameCaseInsensitive = false,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
    TypeInfoResolver = new DefaultJsonTypeInfoResolver()
};
options.Converters.Add(new JsonStringEnumConverter());
options.MakeReadOnly();
var schemaNode = options.GetJsonSchemaAsNode(typeof(ExampleCommand));
// Apply the relevant AD-7 modifications for this example.
schemaNode["properties"]!.AsObject().Remove("AggregateId");
schemaNode["properties"]!["Tenant"]!["readOnly"] = true;
schemaNode["required"] = new JsonArray("Id");
schemaNode["additionalProperties"] = false;
var schema = JsonSchema.FromText(schemaNode.ToJsonString());
foreach (var payload in new[] { "null", "{\"Id\":\"party-1\"}" }) {
    var result = schema.Evaluate(JsonDocument.Parse(payload).RootElement, new EvaluationOptions { OutputFormat = OutputFormat.List });
    Console.WriteLine("Payload " + payload + ": IsValid=" + result.IsValid);
}
Console.WriteLine(schemaNode);
try {
    var command = JsonSerializer.Deserialize<ExampleCommand>("{\"Id\":\"party-1\"}", options);
    Console.WriteLine("Accessor: " + command!.AggregateId);
} catch (JsonException e) {
    Console.WriteLine("Pre-fill accessor result: " + e.GetType().Name + ": " + e.Message);
}
var filled = JsonSerializer.Deserialize<ExampleCommand>("{\"Id\":\"party-1\",\"Tenant\":\"acme\"}", options);
Console.WriteLine("Filled accessor: " + filled!.AggregateId);
sealed class ExampleCommand {
    public required string Id { get; init; }
    public required string Tenant { get; init; }
    public string AggregateId => Id;
}
```

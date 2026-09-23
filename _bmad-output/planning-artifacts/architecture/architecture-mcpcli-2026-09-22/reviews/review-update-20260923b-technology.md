# Technology and source reality review — update 20260923B

**Reviewed:** 2026-09-23  
**Verdict:** PASS for the changed technology seams. No new Critical, High, Medium, or Low finding. The rules are compatible with the inspected APIs; Tenants readiness and the MCP output-option assumption remain explicit conditions, not claims of completed implementation.

## Scope

Reviewed the current [spine](../ARCHITECTURE-SPINE.md), focusing on VAL-20260923B-01..06: effective property mapping, pre-fill validation, Tenants filter/paging readiness, and the resulting startup/release rules. Inherited stack decisions were not reopened. No source document, dependency, or sibling repository was edited.

## Verified fit

### B-01: pre-fill and final validation

AD-7 now removes mapped envelope-owned members from a validation copy and retains the raw object for ownership checks. The advertised Schema already removes these members from `required`. Therefore malformed correlation or idempotency members do not fail before their documented overwrite, while ordinary required fields, unknown properties, and root constraints are still checked. AD-9 separately rejects raw Tenant/Actor disagreements and Payload-only keys. Final validation uses the complete rebuilt object and the stored Schema, so envelope-owned types and patterns are enforced before materialization.

This is consistent with JSON Schema: `readOnly` is annotation metadata, not a validation exemption. The change explicitly avoids relying on it for exemption. [JSON Schema annotations](https://json-schema.org/understanding-json-schema/reference/annotations).

The .NET exporter derives schemas from serializer metadata and supports `TransformSchemaNode`; its examples include object-or-null roots, required constructor properties, renamed fields, and `additionalProperties: false`. AD-7's transformation and Command-root normalization fit that API. [Microsoft schema-exporter documentation](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/extract-schema).

Installed `JsonSchema.Net` 9.4.0 XML documentation confirms `JsonSchema.Evaluate(JsonElement, EvaluationOptions)`, `EvaluationOptions.OutputFormat`, `OutputFormat.List`, and `EvaluationResults.InstanceLocation`. This supports validation of the edited JSON copy without contract deserialization and reporting instance pointers. Evidence: `/home/administrator/.nuget/packages/jsonschema.net/9.4.0/lib/net9.0/JsonSchema.Net.xml`, entries at lines 1392, 1484, 2126, and 6820.

### B-02: one mapping from CLR property to serialized member

The new AD-3 contract is implementable on the installed System.Text.Json 10.0.12 API. Inspection exposed `JsonPropertyInfo.Name`, `AttributeProvider`, `DeclaringType`, `Set`, `AssociatedParameter`, `IsRequired`, and nullability metadata. These support relating exact CLR names to effective serialized names while recognizing constructor-bound properties. Get-only properties must not be rejected solely because `Set` is null when `AssociatedParameter` supplies the deserialization path.

`JsonPropertyName` applies to serialization and deserialization and takes precedence over naming policies, so using the effective serialized member for Schema, filling, and aggregate access is necessary. Custom converter contracts can expose `JsonTypeInfoKind.None`; the spine's rejection of converter-opaque mapping targets avoids assuming object-property metadata exists where it does not. [Microsoft property naming](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/customize-properties), [JsonPropertyInfo metadata](https://learn.microsoft.com/en-us/dotnet/api/system.text.json.serialization.metadata.jsonpropertyinfo?view=net-10.0), [JsonTypeInfoKind](https://learn.microsoft.com/en-us/dotnet/api/system.text.json.serialization.metadata.jsontypeinfokind?view=net-10.0).

Checking role collisions after this mapping, including `aggregateIdProperty`, closes the serialized-name alias and fill-order divergence in B-02. Keeping mapping failures as Catalog exclusions is a policy the implementation can enforce; no incompatible API requirement was found.

### B-03 and B-04: current Tenants incompatibilities are accurately gated

The current source still requires upstream work:

- `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Queries/GetTenantAuditQuery.cs:15` declares `From`, `To`, and `Category` without renaming attributes. `TenantQueryHandlerBase.cs:301` reads lowercase `from` and `to`, and line 317 reads lowercase `category`. `GetTenantAuditQueryHandler.cs:38` consumes that parsed Payload. The AD-16 requirement to align the handler with effective serialized names is justified.
- `TenantQueryHandlerBase.cs:303` and line 307 read `cursor` and `pageSize` from Payload. `ListTenantsQueryHandler.cs:31` also obtains paging from `envelope.Payload`. `references/Hexalith.EventStore/src/Hexalith.EventStore/Controllers/QueriesController.cs:98` instead forwards normalized `request.Paging`. AD-16/20 correctly require the exposed paged handlers to consume envelope paging upstream.
- The Gateway Command validator requires an object Payload (`SubmitCommandRequestValidator.cs:77`); the Query validator permits absent Payload and validates a supplied JSON value (`SubmitQueryRequestValidator.cs:90`). The spine preserves that distinction.

AD-16's discriminating filter data and actual page-content assertions address the exact ways successful responses could conceal ignored inputs. The decorated Contracts release and corresponding handler source must pass before coverage is claimed. This is a sound readiness gate; this review does not claim the upstream changes or live evidence already exist.

### B-05 and B-06: no unsupported technology claim

The provisional stdio output policy is implemented before Catalog construction or transport startup and does not require an SDK capability beyond existing startup validation. It remains an operator decision tagged in AD-13 and Open Questions. AD-17's authoritative baseline merge and instruction-sync prerequisites are release evidence requirements, not assertions about a missing runtime API. No technology contradiction found in either change.

## Versions and inspection evidence

- `dotnet --list-sdks` confirms SDK 10.0.401 is installed; `references/Hexalith.Builds/global.json` pins it. Runtime inspection resolved System.Text.Json 10.0.12 for net10.0.
- [NuGet's JsonSchema.Net 9.4.0 listing](https://www.nuget.org/packages/JsonSchema.Net/9.4.0) confirms the exact pin exists and supports .NET targets usable from .NET 10; the installed package supplied the API evidence above.
- ModelContextProtocol.Core 2.2.0 is installed under `/home/administrator/.nuget/packages/modelcontextprotocol.core/2.2.0/`; the inherited SDK APIs and stack pins were already checked in [the preceding technology review](review-validation-20260923-technology.md). This update introduces no SDK API or package-version change.
- `references/Hexalith.Builds/Props/Directory.Packages.props:9` retains EventStore 3.106.0. The new review used the current checked-out Gateway source and makes no claim that unreleased decorated Contracts packages exist.

The dotnet-inspect skill's suggested command `dnx dotnet-inspect -y -- member JsonPropertyInfo --platform System.Text.Json --oneline -40` exited 1 with `Error: Unrecognized option '--oneline'.` Retrying `dnx dotnet-inspect -y -- member JsonPropertyInfo --platform System.Text.Json` exited 0 and produced the metadata evidence above. No dependency update was needed.

## Verification limits

This is an architecture/API/source review. No McpCli application solution or implementation tests exist yet, and no application build or live Gateway test was claimed. The comparison establishes API feasibility and correct prerequisite ownership; implementation must still exercise the specified renamed-property, role-collision, raw-overwrite, ownership, and live semantic fixtures.

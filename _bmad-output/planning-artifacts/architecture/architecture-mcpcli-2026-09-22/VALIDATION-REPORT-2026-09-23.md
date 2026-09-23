# Architecture validation — Hexalith.McpCli

**Date:** 2026-09-23  
**Verdict:** Needs update before the affected implementation stories proceed.  
**Intent:** Validate; the spine and product requirements have not been edited.  
**Source commit:** `f1d9659a62c874672a03b9c71da4b0e862ebc078`  
**Spine SHA-256:** `8af275b0ba9721abb3d3a6cbee034ec5df471787e19e1237299ce21ca3d39fdb`

The main boundaries and the recent sprint corrections are consistent. Five remaining gaps affect command/query dispatch, envelope filling, deterministic MCP discovery, command payload schemas, and the shared conformance-vector contract.

**Findings:** 0 critical, 3 high, 2 medium, 0 low. Mechanical lint: zero findings. Three independent reviewer lenses completed.

## Findings

### VAL-20260923-01 · High · Enforce the operation kind at the Core execution boundary

**Boundaries:** AD-5, AD-9, AD-12  
**Disposition:** Discuss the error and precedence, then update

The Core has separate command and query argument records, and the Catalog records each operation's kind, but the ordered execution pipeline never requires them to match. Neither the normative argument table nor the exhaustive errors resolves a mismatch.

**Counterexample / evidence:** In a writable session, run_query can name parties.create-party. A descriptor-driven executor could submit a command through a tool advertised as read-only; an argument-driven executor could construct a query request using command routing. This is a missing contract, not evidence that the explicit session Read-only gate is bypassed.

**Recommended change:** Bind SendCommandArguments to write operations and RunQueryArguments to read operations in Core. Define one stable rejection and its precedence relative to availability checks; validation_failed at /operation can use the existing error vocabulary. Keep the check inside the shared executor.

**Verification:** Exercise both mismatches through the CLI, MCP, and direct Core calls in writable and read-only sessions. Assert the agreed error document and zero Gateway calls.

**Sources:** [Spine:84,108,126](ARCHITECTURE-SPINE.md); [Normative arguments and errors:190,378–399](../../prds/prd-mcpcli-2026-09-21/addendum.md); [Adversarial review](reviews/review-validation-20260923-adversarial.md)

### VAL-20260923-02 · High · Fill required envelope fields before deserializing the contract

**Boundaries:** AD-7, AD-9, AD-19  
**Disposition:** Update the shared pipeline

AD-7 explicitly permits callers to omit envelope-filled properties. AD-19 can deserialize that incomplete payload to read ICommandContract.AggregateId, while AD-9 fills the properties later. C# required-member checks can therefore reject a payload that passed the advertised schema.

**Counterexample / evidence:** On SDK 10.0.401/runtime 10.0.12, a contract with required Id and required Tenant throws JsonException when deserializing {"Id":"party-1"}; supplying Tenant makes the accessor succeed. Removing Tenant from the JSON Schema required list does not change System.Text.Json's required-member metadata. The literal pipeline can turn this valid omission into internal_error.

**Recommended change:** Make envelope resolution/filling and contract materialization ordering explicit. Read the interface getter only after required envelope-owned values are available, or use an accessor that does not instantiate an incomplete contract. Preserve tenant/actor disagreement checks, aggregate consistency, and final payload validation.

**Verification:** Add a contract fixture with a computed ICommandContract getter and omitted required tenant/actor/correlation properties. Confirm valid omissions execute and disagreements still produce validation_failed without Gateway calls.

**Sources:** [Spine:96,108,168](ARCHITECTURE-SPINE.md); [PRD FR-7 and FR-16:240,355](../../prds/prd-mcpcli-2026-09-21/prd.md); [Adversarial review:32; reproducible probe:93](reviews/review-validation-20260923-adversarial.md)

### VAL-20260923-03 · High · Use an MCP listing mechanism that guarantees the required order

**Boundaries:** AD-12; determinism convention  
**Disposition:** Update the pinned SDK integration decision

AD-12 requires fixed tools/list order by inserting tools in order into ToolCollection, then relying on built-in dispatch while forbidding a custom list handler. The pinned SDK's collection does not preserve insertion order.

**Counterexample / evidence:** The ModelContextProtocol 2.2.0 probe enumerates the registered tools as describe_operation, run_query, list_operations, send_command, list_modules instead of registration order. The SDK collection is backed by ConcurrentDictionary and its built-in list handler enumerates it directly. Registration order therefore cannot enforce the spine's discovery contract.

**Recommended change:** Choose an explicit ordered response mechanism supported by the pinned SDK, such as a list handler that projects the permitted tools through a fixed name sequence while retaining built-in call dispatch. Amend the blanket handler prohibition if needed; keep one source of truth for allowed tools and Read-only filtering.

**Verification:** Run tools/list in fresh processes and both Read-only settings; assert the exact sequence and unique permitted names. An unordered set comparison is insufficient.

**Sources:** [Spine:126,195](ARCHITECTURE-SPINE.md); [Pinned SDK source and compiled probe](reviews/review-validation-20260923-tech-reality.md); [SDK v2.2.0 collection enumeration](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerPrimitiveCollection.cs#L212); [SDK v2.2.0 built-in list handler](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerImpl.cs#L1377)

### VAL-20260923-04 · Medium · Exclude null from command payload root schemas

**Boundaries:** AD-6, AD-7, AD-9; FR-15  
**Disposition:** Update the schema invariant

The specified exporter and transforms leave a reference-type payload root nullable. This permits a command payload that cannot satisfy the Gateway's object-only rule.

**Counterexample / evidence:** Both independent reviewers reproduced a root type of ["object","null"] on the pinned .NET exporter. JsonSchema.Net 9.4.0 reports JSON null as valid. SubmitCommandRequestValidator explicitly requires Payload.ValueKind == Object. Depending on the accessor, null can fail later during extraction or request validation rather than at schema validation.

**Recommended change:** State that every command payload schema has a non-null object root and enforce it during derivation/preflight. Keep genuinely nullable nested properties intact, and state the query-root policy separately against its Gateway contract.

**Verification:** Reject command payload null before accessor use or Gateway submission; retain acceptance for valid objects and permitted nested nulls. Verify describe_operation publishes the same restriction used by execution.

**Sources:** [Spine:90,96,108](ARCHITECTURE-SPINE.md); [Gateway validator:77–79](../../../../references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/SubmitCommandRequestValidator.cs); [Adversarial null probe](reviews/review-validation-20260923-adversarial.md); [Technology null probe](reviews/review-validation-20260923-tech-reality.md)

### VAL-20260923-05 · Medium · Freeze one shared contract for module conformance vectors

**Boundaries:** AD-16; Stories 4.8–4.13  
**Disposition:** Discuss ownership and add a pre-authoring gate

Module maintainers own versioned vectors while McpCli owns a generic runner, but no shared format authority, compatibility rule, or gate before upstream vector authoring is specified. Versioned artifacts alone do not establish a common contract.

**Counterexample / evidence:** Tenants can supply JSON prerequisite calls with JSON Pointer assertions while Parties supplies a different layout or executable assertions. Each can satisfy the prose requirements, yet one generic runner cannot consume both without adapters or late upstream rewrites.

**Recommended change:** Assign one owner for a versioned vector contract, its generic assertion vocabulary and compatibility validator. Reference that authority from AD-16 and require it before approving upstream vectors. Keep the field-level schema and examples in a companion test artifact rather than expanding the spine.

**Verification:** Validate at least one vector from each v1 module with the same validator before approval and before the loopback/live runners consume it.

**Sources:** [Spine:150](ARCHITECTURE-SPINE.md); [Upstream vectors and runner:1218–1221,1253–1256,1273–1276,1303–1306](../../epics.md); [Rubric review](reviews/review-validation-20260923-rubric.md)

## Existing implementation gates

These are already recorded prerequisites, not additional architecture findings.

| Gate | Owner / timing | Evidence |
| --- | --- | --- |
| Scaffold build, release, commitlint and CI files | McpCli maintainer; Story 1.1 owns the structural seed | [Current sprint adjustment](../../sprint-change-proposal-2026-09-23.md) |
| Add JsonSchema.Net and HexalithMcpCliVersion centrally | Hexalith.Builds owner; before the consuming restore/bootstrap stories | [Spine Open Questions:328](ARCHITECTURE-SPINE.md); [Assigned readiness actions](../../../implementation-artifacts/sprint-status.yaml) |
| Publish decorated Tenants and Parties Contracts and approve coverage | Module maintainers; exact package pins required before production references | [Spine:329; AD-21:180](ARCHITECTURE-SPINE.md) |
| Publish Parties.Aspire and supply a bounded source-build path | Parties / Builds owners; before harness restore and blocking live CI | [Spine:326–327](ARCHITECTURE-SPINE.md) |
| Verify the list-query routing constant with a live spike | McpCli + Tenants maintainers; Story 2.5 gathers evidence, Story 4.8 owns the final decision | [Current sprint adjustment](../../sprint-change-proposal-2026-09-23.md) |

## Checks and limits

- Deterministic gate: uv run .agents/skills/bmad-architecture/scripts/lint_spine.py --workspace _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22 — exit 0, ok: true, zero findings. Saved in reviews/lint-validation-20260923.json.
- Independent rubric, technology/reality, and adversarial reviews ran against the same spine and current PRD, normative addendum, epics, and sprint corrections. The root-null finding appeared in two reviews and is counted once.
- Technology availability and fit were checked against the local pinned catalog, restored/installed packages, and official package/source documentation. The technology review records URLs, probe commands, and evidence limits; this does not claim that every pin is the latest available release.
- Small standalone probes reproduced SDK collection order, required-member deserialization, and nullable-root schema behavior. These are library-level probes, not an implemented McpCli integration test.
- The repository currently has no application solution, project files, or test projects. No application build or live Gateway end-to-end result is claimed. Existing upstream readiness gates remain open.
- Prior accepted corrections remain reflected in the current documents: caller-supplied idempotency, deterministic parity plus once-only live semantics, unknown_module, bootstrap publication, Parties composition prerequisites, and the recent sprint criteria. No obsolete finding was automatically carried forward.
- Non-counted candidates: no JsonSchema.Net dialect failure was reproduced; nullable idempotency-property omission remains a lower-confidence policy question; extension preflight remains subject to the already binding Gateway-rule validation requirement.

## Reviewer disposition

- [Good-spine rubric](reviews/review-validation-20260923-rubric.md): 0 Critical, 0 High, 1 Medium, 0 Low. Retain the vector-contract finding as VAL-20260923-05.
- [Technology and reality](reviews/review-validation-20260923-tech-reality.md): 0 Critical, 1 High, 1 Medium, 0 Low. Retain deterministic tool order as VAL-20260923-03; merge the null-root finding into VAL-20260923-04.
- [Adversarial divergence](reviews/review-validation-20260923-adversarial.md): 0 Critical, 2 High, 1 Medium, 0 Low. Retain kind checking and required-member ordering as VAL-20260923-01/02; merge the null-root finding into VAL-20260923-04.

## Next action

Use bmad-architecture update to resolve these five findings while preserving AD identifiers. Align affected PRD/addendum clauses and story criteria where the chosen behavior changes. Resolve the High findings before affected Core/MCP work, the null-root rule before schema acceptance, and the vector contract before upstream vector approval. Unrelated bootstrap work can continue.

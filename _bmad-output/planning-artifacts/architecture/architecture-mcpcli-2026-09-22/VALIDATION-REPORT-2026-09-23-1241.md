# Architecture validation — Hexalith.McpCli

**Reviewed:** 2026-09-23, current working tree  
**Verdict:** Update the spine before the affected Catalog, executor, and v1 Tenants integration work is treated as settled.  
**Scope:** Standalone validation; the spine, PRD, addendum, and epics were not edited.  
**Source commit:** `b97a1bd4590cd81e040b9bdb208355fcdff81a79`  
**Reviewed spine SHA-256:** `057f0d020e19d0932db276e19fd3c644cf03ca8b4954a2a44d87606c84eb1ca5`

The September 23 update closes the five findings in the earlier validation. This pass found **4 High and 2 Medium** new or still unrecorded gaps. The deterministic spine lint passed with **zero findings**. Two High findings are internal architecture inconsistencies; two are current Tenants source incompatibilities that need explicit v1 readiness gates. The current repository has no McpCli application projects, so these are document and pinned-source findings, not failed application tests.

## High findings

### VAL-20260923B-01 — Raw validation rejects fields the executor promises to replace

**Boundary:** AD-7, AD-9; PRD FR-16. **Disposition:** Update the shared validation sequence.

AD-9 validates raw Payload against the final stored Schema before envelope filling. AD-7 removes envelope-owned members from `required`, but retains their type and pattern constraints; `readOnly` is an annotation. A raw `null` at a non-nullable `idempotencyKeyProperty` can therefore fail schema validation before a supplied key overwrites it. With no key, the raw failure can also preempt the specified `/idempotencyKey` error. An invalid raw `correlationProperty` can likewise fail before the promised overwrite. The PRD repeats both the validation order and the removal/overwrite behavior.

**Resolve:** Specify a pre-fill check that parses the object and checks ordinary Payload members while handling envelope-owned fields by their explicit ownership rules. Then fill the fields and validate the complete Payload against the advertised Schema. Keep Tenant/Actor disagreement and Payload-only idempotency-key rejection before overwrite. Add fixtures for raw null idempotency and a correlation value that will be overwritten. [Spine AD-7 and AD-9](ARCHITECTURE-SPINE.md), [PRD FR-16](../../prds/prd-mcpcli-2026-09-21/prd.md), [rubric review](reviews/review-validation-20260923-rubric-2.md).

### VAL-20260923B-02 — Decoration property references can alias different envelope roles

**Boundary:** AD-3, AD-7, AD-9, AD-19; PRD decoration contract. **Disposition:** Update Catalog validation and the attribute-name contract.

Nothing excludes `tenantProperty` and `actorProperty` naming the same effective JSON member. With Tenant `acme`, Actor `user-1`, and the raw field omitted, one compliant fill order sends `PrincipalId: "acme"`; another sends `PrincipalId: "user-1"`. `correlationProperty` or `actorProperty` overlapping `aggregateIdProperty` can also change the routed aggregate after filling. The existing `tenant_is_aggregate_id` diagnostic covers only one collision. Separately, the attribute strings do not say whether they name CLR members or serialized JSON fields; `[JsonPropertyName("party_id")]` can make two compliant accessors read `/PartyId` and `/party_id` respectively.

**Resolve:** Define attribute strings as CLR property names, resolve each once to its effective serialized member under the Module options, and reject unresolved or colliding ownership at Catalog build. Check collisions after serialization mapping, including the aggregate source. Align the PRD diagnostic table; test aliasing and `[JsonPropertyName]` through Schema, accessor, and executor. [Spine AD-7, AD-9, AD-19](ARCHITECTURE-SPINE.md), [PRD attribute table](../../prds/prd-mcpcli-2026-09-21/prd.md), [adversarial review](reviews/review-validation-20260923-adversarial-2.md).

### VAL-20260923B-03 — Current Tenants audit queries ignore schema-valid filters

**Boundary:** AD-6/AD-7 wire casing and the v1 Tenants live gate. **Disposition:** Record an upstream Gateway-ready prerequisite before claiming v1 coverage.

The current `GetTenantAuditQuery` declares `From`, `To`, and `Category`, and AD-6's case-sensitive Payload policy emits those PascalCase names. The current Tenants handler reads raw `from`, `to`, and `category` with case-sensitive `JsonElement.TryGetProperty`. A tool-valid filter can therefore be silently ignored; a lowercase filter fails the tool's closed Schema. This is a current sibling-source incompatibility, not a claim that a decorated Tenants package already exists.

**Resolve:** Have the Tenants owner align the handler with its declared wire contract, or explicitly revise the shared wire policy with matching schema/executor tests. Add a live semantic vector with non-default audit filters and assert filtered results. Track it alongside the existing Tenants package prerequisite. [Spine AD-6 and AD-16](ARCHITECTURE-SPINE.md), [technology review with source locations](reviews/review-validation-20260923-technology.md), [System.Text.Json property lookup](https://learn.microsoft.com/en-us/dotnet/api/system.text.json.jsonelement.trygetproperty?view=net-10.0).

### VAL-20260923B-04 — Current Tenants query handlers ignore envelope-only paging

**Boundary:** AD-20 and the v1 Tenants live gate. **Disposition:** Make the Tenants paging migration an explicit prerequisite, or revise AD-20 and the PRD.

AD-20 sends `pageSize`, `offset`, and `cursor` in `SubmitQueryRequest.Paging` only. Current Tenants query handlers read paging from lowercase fields in `envelope.Payload`; none of the checked handlers reads `envelope.Paging`. A non-default page request through either head can receive the handler default. The Deferred note mentions a Tenants decision but does not gate v1 coverage or say which side changes.

**Resolve:** Require the upstream handler to consume `QueryEnvelope.Paging`, or explicitly choose a payload paging contract before decorating Tenants Queries. Add a live vector for non-default page size and a later cursor, asserting actual page contents. [Spine AD-20 and Deferred](ARCHITECTURE-SPINE.md), [technology review with handler and Gateway locations](reviews/review-validation-20260923-technology.md).

## Medium findings

### VAL-20260923B-05 — `mcp` output options have no defined behavior

**Boundary:** AD-12/AD-13; PRD FR-10/FR-13. **Disposition:** Choose one startup behavior and test it.

Every verb accepts `--format` and `--output`, including `mcp`, while stdio stdout must remain JSON-RPC. The spine does not say whether `mcp --format table` or `mcp --output file` is ignored, rejected, or applied somewhere other than stdout. The choice changes user-visible CLI behavior. Define it in the spine and option table without redirecting or formatting the protocol channel. [Spine AD-12/AD-13](ARCHITECTURE-SPINE.md), [PRD FR-10/FR-13](../../prds/prd-mcpcli-2026-09-21/prd.md), [rubric review](reviews/review-validation-20260923-rubric-2.md).

### VAL-20260923B-06 — The authoritative instruction merge is missing from the release invariant

**Boundary:** AD-17, FR-22. **Disposition:** Add an explicit v1 release gate.

FR-22 closes only when the no-new-per-Module-server/CLI rule is merged into the authoritative `Hexalith.AI.Tools` baseline. That rule is absent from the current baseline checkout. AD-17's release preflight names source, version, and credentials, while the epic release criterion assumes the instruction gate is complete. Add the merged upstream instruction and synchronized local entry-point check to the release prerequisite list; keep the actual edit in the owning repository. [Spine AD-17 and capability map](ARCHITECTURE-SPINE.md), [PRD FR-22](../../prds/prd-mcpcli-2026-09-21/prd.md), [rubric review](reviews/review-validation-20260923-rubric-2.md).

## Checks and limits

- `uv run .agents/skills/bmad-architecture/scripts/lint_spine.py --workspace _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22` exited 0 with `ok: true` and zero findings. [Saved lint result](reviews/lint-validation-20260923-1241.json).
- Three independent reviewer lenses completed against the current working tree: [rubric](reviews/review-validation-20260923-rubric-2.md), [technology and source reality](reviews/review-validation-20260923-technology.md), and [adversarial divergence](reviews/review-validation-20260923-adversarial-2.md). The attribute-name ambiguity is folded into VAL-20260923B-02, not counted again.
- The technology lens checked pinned SDK APIs, package listings, and EventStore/Tenants source. The named stack pins are available; the already recorded Builds catalog additions, decorated Contracts releases, Parties Aspire helper, and CI source-build seam remain prerequisites. These are not counted again here.
- No McpCli solution or application test projects exist in this repository yet. No application build, live Gateway test, or production failure is claimed. The validation did not edit the spine or its source documents.

## Next action

Use **bmad-architecture update** to resolve VAL-20260923B-01/02 while preserving AD IDs, and record VAL-20260923B-03/04 as concrete Tenants Gateway-ready gates before v1 live coverage is claimed. Resolve the two Medium behaviors with the affected CLI and release stories. Reconcile the PRD/addendum/epics where their current wording carries the same ambiguity.

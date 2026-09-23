# Adversarial architecture review — September 23 update B

**Verdict: pass for the updated architecture contract; no actionable critical, high, or medium findings.** The reviewed changes constrain the previously divergent builders. This verdict does not approve the pending MCP option choice or assert that upstream readiness and release prerequisites have been completed.

## Scope and method

Reviewed the current `ARCHITECTURE-SPINE.md`, concentrating on AD-3/7/9/19 property binding and validation, AD-12/13 startup output behavior, AD-16/20 Tenants semantic readiness, and AD-17 release preflight. Checked the PRD attribute table where the spine incorporates its contract. Tried to construct two independent implementations that satisfy every applicable decision yet give different results for the same supported input. The earlier VAL-20260923B-01 through -06 cases were the primary adversarial inputs.

## Attempted counterexamples

### 1. A raw field fails its schema even though filling would replace it

Input: a Command declares an idempotency property with a non-nullable string schema, receives raw null or a number there, and has a valid caller-supplied envelope key. Its raw correlation field is also malformed.

Builder A validates the raw Payload and rejects it. Builder B removes mapped envelope-owned members from the validation copy, validates ordinary members, performs ownership checks, fills the resolved values, and validates the complete Payload.

**Result:** A is no longer compliant. AD-7 explicitly specifies the copy, preserves the original for ownership checks, prohibits early materialization, and requires complete final validation. AD-9 fixes the sequence. Removing only the mapped members cannot discard an ordinary or unknown member merely because its name resembles an envelope field.

### 2. Suppression of schema checks lets the caller choose Tenant or Actor

Input: a mapped raw Tenant/Actor is null, non-string, or differs from the resolved session value. A different input contains a non-null idempotency member without a supplied envelope key.

Builder A overwrites all raw values after pre-fill validation. Builder B rejects these ownership violations.

**Result:** A violates AD-9. The raw values must survive the validation copy, Tenant/Actor checks occur before overwrite and use ordinal equality at the mapped pointer, and the Payload-only idempotency case fails at `/idempotencyKey`. Removing raw null for an optional idempotency property is a separate explicit case, and required-key metadata fixes the missing-key result.

### 3. CLR names and serialized names produce different accessors or fills

Input: `aggregateIdProperty` names a CLR property carrying `[JsonPropertyName]`; another contract uses the same serialized member for Tenant and Actor or for correlation and aggregate identity.

Builder A interprets the attribute as a JSON name or computes each role independently. Builder B resolves exact CLR names once and rejects colliding serialized ownership.

**Result:** A violates AD-3. The immutable binding is shared by Schema, checks, filling, and accessor construction; ignored, ambiguous, missing, and converter-opaque targets are invalid. The tenant/aggregate diagnostic exception is explicit. AD-19 separately fixes computed interface getters to run after filling and final validation, so using the raw contract for routing also violates the contract.

### 4. `mcp` redirects or formats its protocol output

Input: a valid inherited table format, explicit JSON format, explicit table format, explicit output path, or both conflicting flags.

Builder A formats/redirects JSON-RPC or applies the generic CLI output policy. Builder B follows the provisional MCP-specific policy.

**Result:** A violates AD-12/13 and the channel convention. Accepted settings, rejected explicit flags, the format-first tie-break, stderr document, exit code, zero stdout, no file opening, and pre-Catalog/transport timing are specified. The outstanding operator review is clearly tied to Story 3.2 implementation; it is a known assumption, not an unrecorded gap. There is no need to treat upstream completion or operator silence as approval.

### 5. Tenants is called ready because queries returned successful status

Input: an audit query returns unfiltered data, or a paged query returns its default first page despite a non-default envelope request.

Builder A accepts successful status or loopback equality as v1 readiness. Builder B requires the migrated handler and the live semantic evidence.

**Result:** A violates AD-16/20. The audit fixture must distinguish time/category outcomes, and paging must exercise a non-default size plus a subsequent cursor and inspect actual page contents. Legacy Payload paging cannot govern generic requests. The decorated release and matching live handler source must pass before v1 coverage is claimed. Loopback parity cannot substitute for this gate.

### 6. Publication proceeds with an open instruction PR or stale local baseline

Input: packages pass technical checks but the authoritative instruction change is only proposed, the referenced baseline lacks it, or local entry points differ.

Builder A publishes the paired v1 tool. Builder B waits for the documented evidence.

**Result:** A violates AD-17. A merged authoritative rule, a baseline reference containing it, byte-identical entry points, and a passing synchronization check are all required. The Abstractions-only bootstrap exemption is limited and explicit; it cannot justify publishing the paired tool early.

## Triage and limits

- **Autofix:** none identified.
- **Discuss:** retain the existing MCP output-option assumption for operator confirmation or revision before Story 3.2; this review does not reopen it or select a policy.
- **Defer/open prerequisites:** retain the existing Tenants handler migrations and semantic vectors, instruction merge/reference evidence, decorated Contracts releases, Parties Aspire helper, Builds pins, and bounded CI source-build prerequisites. Their unfinished state is already represented and does not require another architecture finding.
- **Ignore as findings:** implementation algorithms for accessing the immutable property map, copying JSON, and storing release evidence. The observable contracts are fixed; choosing those mechanisms does not create an identified cross-unit incompatibility.

This was a semantic document review. No application behavior, live Gateway result, package publication, or upstream merge was claimed or performed. Source documents were not edited.

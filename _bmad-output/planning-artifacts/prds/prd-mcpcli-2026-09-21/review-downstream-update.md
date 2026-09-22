# Downstream Implementability Recheck — Hexalith.McpCli PRD

- **Reviewed:** latest `prd.md` and `addendum.md`
- **Lens:** targeted closure of prior H1, H2, and M1 plus downstream architecture/story usability
- **Verdict:** Pass
- **Findings:** 0 critical, 0 high, 0 medium, 0 low

## Overall verdict

The latest amendment closes all three prior downstream findings without creating a new contradiction. The PRD and normative addendum are sufficiently exact and testable for architecture reconciliation and story creation. The current architecture spine still contains older decisions, but PRD §10.1 assigns each mismatch to a specific owning implementation gate, so those are downstream obligations rather than PRD defects.

## Critical findings

None.

## High findings

None.

## Medium findings

None.

## Low findings

None.

## Closure evidence

### Prior H1 — Gateway-client exceptions with successful HTTP statuses

**Resolved.** PRD FR-11 now classifies every `EventStoreGatewayException` as `gateway_error` and explicitly preserves its actual status, including malformed or semantically failed `2xx` responses. Addendum §G copies `StatusCode` without reclassification, defines optional metadata and detail fallback, and requires fixtures for malformed `202` command and `200` query responses, semantic query failure, complete Problem Details, and locally created exceptions with absent metadata. The public schema can now represent the pinned client behavior without invented status values.

### Prior H2 — Omitted command correlation

**Resolved.** The Decoration Attribute limits `correlationProperty` to Commands. FR-16 and addendum §E define one rule: `resolvedCorrelationId = callerCorrelationId ?? generatedMessageId`; no second identifier is generated. The same resolved value is sent in `SubmitCommandRequest`, written to any declared `correlationProperty` before rebuilt-Payload validation, and expected from the successful Gateway result. Supplied and omitted fixtures are required, and the executor architecture gate repeats the rule.

### Prior M1 — Required idempotency-key discovery

**Resolved.** `describe_operation.envelope` now always includes boolean `idempotencyKeyRequired`, true exactly when the Operation names a non-nullable `idempotencyKeyProperty`. FR-9 exposes the requirement, FR-16 preserves the `/idempotencyKey` omission failure, and addendum §G defines the field and example. The generic tool argument remains optional while per-Operation requiredness is discoverable before execution.

## Downstream readiness checks

- **Public contract:** result and error names, nesting, types, constraints, required/optional members, omission rules, payload casing, paging nullability, and error mapping are normative in addendum §G and backed by schema snapshots through both Heads.
- **Idempotency and retries:** keys are caller-supplied only, never generated, echoed only when present, and provide no generic retry or duplicate promise without a trusted per-Command adapter.
- **Head/channel behavior:** pre-initialize MCP failures emit one structured stderr error, exit 2, and zero stdout bytes; post-initialize failures remain on JSON-RPC/MCP. CLI result/error channels and exit codes are explicit.
- **Discovery:** offline `submittable`, Read-only precedence, lint codes/pointers, aggregate requiredness, and idempotency requiredness are all observable.
- **Module inventory:** the durable, maintainer-approved FR-21 inventory is compared with public Operation Names and separately with internal decorated types; unapproved omissions or extras fail Gateway readiness.
- **Architecture handoff:** fixture, dependency, serializer/schema, settings, executor, result-record, and channel changes are each gated before the affected implementation starts; unrelated catalog preparation may continue.


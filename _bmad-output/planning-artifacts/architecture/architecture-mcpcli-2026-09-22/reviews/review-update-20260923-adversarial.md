---
title: "September 23 architecture update: adversarial seam review"
reviewed: ARCHITECTURE-SPINE.md
date: '2026-09-23'
status: passed
---

# Adversarial seam review

## Verdict

**Pass: no remaining critical, high, or medium divergence in the five September 23 fixes.** Core, MCP, CLI, and Module vector builders have a shared behavioral contract. The optional idempotency-field edge case found during this review was closed before handoff.

## Challenge raised and closed during review

### ADV-01 — Nullable but serializer-required idempotency key

The initial update allowed an omitted `required string? IdempotencyKey` on a Command with a computed `ICommandContract.AggregateId` getter. Its JSON Schema permits omission, but System.Text.Json rejects a missing required member when AD-19 deserializes the rebuilt Payload. The two independently compliant executor implementations could return either an accepted Gateway call or `internal_error`.

**Closure:** AD-3 stores `IdempotencyKeyRequired` on the immutable descriptor. AD-9 derives it from non-nullability or effective `JsonPropertyInfo.IsRequired` under the cached Module Payload options and makes both discovery and execution consume that value. An omitted required key now returns `validation_failed` at `/idempotencyKey` before contract materialization. With no key argument, a non-null raw Payload value is rejected at the same path and a raw null is removed; the Payload cannot carry a key absent from the Gateway envelope. PRD FR-16, addendum §G, and the executor story align with this rule.

**Implementation check:** use computed-getter fixtures with C# `required`, `[JsonRequired]`, and optional nullable key members. Compare Core, CLI, and MCP behavior, advertised `idempotencyKeyRequired`, submitted Payload, envelope key, and zero Gateway calls on rejection.

## Closed challenges

| Seam | Current binding rule |
| --- | --- |
| Command/query dispatch | AD-5 and AD-9 reject kind mismatch at `/operation` before availability or Payload checks. |
| Required envelope members | AD-9 fills and revalidates before AD-19 deserializes; an omitted serializer-required idempotency key is rejected before that step. |
| Optional idempotency member | AD-9 rejects a raw non-null key without an envelope argument and removes raw null; the Gateway and Payload cannot carry different effective keys. |
| MCP listing | AD-12 uses a post-list filter to guarantee the exact order independent of SDK collection enumeration. |
| Command root | AD-7 advertises and enforces a non-null object root while preserving nested nullability. |
| Vector contract | AD-16 assigns McpCli ownership of one closed versioned contract and compatibility validator before Modules write vectors. |

This is a document-level review; the application projects and tests do not yet exist.

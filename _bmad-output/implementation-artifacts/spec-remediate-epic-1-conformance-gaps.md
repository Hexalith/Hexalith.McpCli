---
title: 'Remediate Epic 1 conformance-vector blockers'
type: 'bugfix'
created: '2026-09-28'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'f9a51f42bfd50948adb94f243ad03136a6840d0b'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-retro-2026-09-27.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The v1 contract rejects Catalog-valid Query roots such as JSON null, permits incomplete or impossible Gateway expectations, accepts tenants that execution rejects, and lets Python equate JSON booleans with numbers. Author approval and loopback can therefore produce false failures and false passes.

**Approach:** Tighten v1 in place with kind-specific payload and Gateway request rules, the runtime tenant grammar, complete Query routing, and one recursive JSON-semantic comparator. Update focused tests and synthetic vectors, then rerun Release author validation and CLI/MCP loopback.

## Boundaries & Constraints

**Always:** Keep Command roots as objects and allow every finite Query JSON root. Require every emitted field, including Query `projectionType`; omit Query wire `payload` only for JSON null. Keep nested Module payloads open, apply rules to all call positions, and compare nested values by JSON type: integers and floats are Numbers, never booleans.

**Never:** Change production Core, pinned `references/`, dependencies, build configuration, or create v2. Do not touch the existing retrospective/sprint-status edits, resolve unrelated retrospective items, claim live EventStore semantics, commit, or push.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Query roots | Object, array, string, number, boolean, or null | Non-null is emitted; null is omitted | Catalog compatibility stays a downstream check |
| Command root | Non-object | Rejected at the step payload | Located in every call position |
| Gateway body | Complete known fields; open nested payload | Required fields and `projectionType` pass | Missing, mistyped, or unknown fields fail |
| Tenant | Runtime 1–64 character slug | Envelope/body agree | Bad syntax or disagreement fails |
| JSON comparison | Nested values | Same JSON types pass | `true` versus `1` fails |

</frozen-after-approval>

## Code Map

- `tools/conformance-vectors/v1/schema.json`, `validate.py` -- kind-specific structural and cross-field contract; reuse runtime tenant syntax and exact request field sets.
- `tools/conformance-vectors/v1/run_loopback.py` -- replace Python equality in assertions, expected fields, and all parsed-JSON parity sites; compare captured bodies completely.
- `tools/conformance-vectors/v1/test_validate.py`, `test_loopback.py` -- reuse existing position/helpers for focused contract and equality regressions.
- `tools/conformance-vectors/v1/sample-query.json`, `sample-command.json`, `README.md` -- exercise null Query payload, pin `sample-items`, and document tightened v1 behavior.
- `OperationExecutor.cs`, `RoutingResolver.cs`, and pinned EventStore request DTO/client sources -- authoritative behavior to mirror, not change.

## Tasks & Acceptance

**Execution:**
- [x] `schema.json`, `validate.py` -- encode kind-specific payloads, exact request bodies, tenant syntax, Query projection, and null omission.
- [x] `sample-*.json`, `README.md` -- align approved examples and guidance.
- [x] `run_loopback.py` -- use recursive JSON equality for assertions, containment, expectations, documents, errors, and requests.
- [x] `test_validate.py`, `test_loopback.py` -- cover every call position and comparison layer.

**Acceptance Criteria:**
- Given any finite Query JSON value, when authored in v1, then it is representable while non-object Command roots fail.
- Given any call position, when a Gateway body is incomplete, unknown, lacks valid Query `projectionType`, disagrees with Envelope input, or has an invalid tenant, then validation reports its location.
- Given assertions or CLI/MCP documents/requests, when nested JSON swaps a boolean and number, then loopback fails while equal Number encodings pass.
- Given the updated samples, when both required scripts run, then they exit zero and the null Query sends no `payload` member.

## Implementation Notes

## Spec Change Log

## Review Triage Log

- BH-01 — `medium` / `patch` — A direct validator probe accepted Query input `[]` with expected wire `payload: null`; Core forwards the non-object root unchanged, so the approved request is impossible.
- BH-02 — `maybe-false` / `defer` — Python rounds some large decimal/exponent tokens before comparison, but the approved intent does not define arbitrary-precision Number semantics; an explicit numeric-precision decision is needed to determine the required behavior.
- BH-03 — `medium` / `patch` — Validator probes accepted `aggregateId` and `entityId` shapes that `OperationExecutor` rejects through `RoutingResolver.IsAggregateId`.
- BH-04 — `medium` / `patch` — A validator probe accepted Query `queryType: bad:value`; `RoutingResolver.IsWireValue` rejects Query colons, overlength values, markup, quotes, and injection patterns.
- BH-05 — `medium` / `patch` — A validator probe accepted Query `projectionActorType: <script>` although `RoutingResolver.IsWireValue(..., 64)` rejects that value.
- BH-06 — `medium` / `defer` — A validator probe accepted an extension key `../bad` that `ExtensionValidator` rejects, but the extension schema behavior predates this story and was only moved into a shared definition here.
- BH-07 — `false` / `reject` — Although Python's raw parser accepts duplicate keys and named non-finite values, the loopback response source is the already validated vector and the .NET heads serialize through `System.Text.Json`; no reachable invalid-output path was demonstrated at the cited sites.
- BH-08 — `medium` / `patch` — Focused tests exercise the comparator, expectations, and assertions but do not drive the `run()` parity call sites, so the checked “every comparison layer” task lacks regression evidence.
- BH-09 — `medium` / `defer` — AD-21 still defines only `include`/`exclude` inventory semantics while the newer migration plan introduces ecosystem dispositions; commit inspection shows this came from the concurrent planning-history advance, not this story.
- BH-10 — `low` / `defer` — The PRD vision can be read as claiming all six legacy servers are replaced in the first increment while retirement is deferred; this wording came from the concurrent planning-history advance.
- BH-11 — `medium` / `defer` — Story 4.5 does not test the newly declared consistency between `include`/`exclude` coverage and `replace`/`withdraw`/`defer` disposition; this is pre-existing planning work outside this story.
- BH-12 — `medium` / `defer` — Epic 5's temporary migration-exception language conflicts with the authoritative unconditional no-new-proprietary-surface rule and needs planning-owner reconciliation.
- BH-13 — `medium` / `defer` — The PRD calls the all-surface inventory a v1 deliverable while Epic 5 schedules EventStore Admin inventory after the initial release; the planning boundary needs one authoritative answer.
- BH-14 — `low` / `defer` — SM-C1 still names only server or CLI creation and omits plug-ins and the broadened proprietary-surface scope.
- VG-01 — `medium` / `patch` — Pre-verified gap: no runner-level regression makes CLI and MCP result documents differ by nested boolean versus number, so reverting that call site to Python equality would leave current focused tests green.
- VG-02 — `low` / `patch` — Pre-verified gap: malformed and boundary-valid Gateway `domain` slugs are not covered for both kinds at all call positions, even though the new schema uses the runtime grammar.
- VG-03 — `low` / `patch` — Pre-verified gap: Query `projectionActorType` has no positive or negative tests at each call position, so its current type/length constraints can regress unnoticed.
- VG-O1 — `medium` / `patch` — A direct probe confirmed that non-object, non-null Query input `1` may be paired with expected wire payload `2`; Core preserves such roots unchanged.
- VG-O2 — `medium` / `patch` — A direct probe confirmed that colon, markup, and injection-invalid projection actor values pass offline validation while runtime routing rejects them.
- EC-01 — `low` / `patch` — With two unknown Gateway fields, `_schema_errors` reports only the containing body because its message parser recognizes only the single-property form; the individual offending locations are lost.
- EC-02 — `low` / `patch` — `_expect_fields` appends object keys without RFC 6901 escaping; a demonstrated `a/b` mismatch reports a different pointer path.
- EC-03 — `maybe-false` / `defer` — This repeats BH-02's verified rounding behavior; arbitrary-precision preservation remains unspecified and needs the same explicit decision.
- EC-04 — `medium` / `patch` — Direct probes confirmed the closed request-body schema still accepts impossible aggregate, wire-type, and projection-actor values despite `OperationExecutor` and `RoutingResolver` being named as authorities to mirror.
- EC-05 — `medium` / `patch` — This independently confirms BH-08/VG-01: discovery, document, error, and captured-request parity sites lack focused boolean-versus-number regression coverage.

## Verification

**Commands:**
- `python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'` -- all focused validator and loopback unit tests pass.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` -- sample package packs and all three vectors pass author validation.
- `bash tools/conformance-vectors/v1/run-sample-loopback.sh` -- CLI and MCP discovery, requests, results, malformed input, and Gateway errors pass out of process.

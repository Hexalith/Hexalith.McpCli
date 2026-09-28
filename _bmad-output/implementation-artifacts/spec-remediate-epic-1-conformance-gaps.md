---
title: 'Remediate Epic 1 conformance-vector blockers'
type: 'bugfix'
created: '2026-09-28'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
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
- [ ] `schema.json`, `validate.py` -- encode kind-specific payloads, exact request bodies, tenant syntax, Query projection, and null omission.
- [ ] `sample-*.json`, `README.md` -- align approved examples and guidance.
- [ ] `run_loopback.py` -- use recursive JSON equality for assertions, containment, expectations, documents, errors, and requests.
- [ ] `test_validate.py`, `test_loopback.py` -- cover every call position and comparison layer.

**Acceptance Criteria:**
- Given any finite Query JSON value, when authored in v1, then it is representable while non-object Command roots fail.
- Given any call position, when a Gateway body is incomplete, unknown, lacks valid Query `projectionType`, disagrees with Envelope input, or has an invalid tenant, then validation reports its location.
- Given assertions or CLI/MCP documents/requests, when nested JSON swaps a boolean and number, then loopback fails while equal Number encodings pass.
- Given the updated samples, when both required scripts run, then they exit zero and the null Query sends no `payload` member.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'` -- all focused validator and loopback unit tests pass.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` -- sample package packs and all three vectors pass author validation.
- `bash tools/conformance-vectors/v1/run-sample-loopback.sh` -- CLI and MCP discovery, requests, results, malformed input, and Gateway errors pass out of process.

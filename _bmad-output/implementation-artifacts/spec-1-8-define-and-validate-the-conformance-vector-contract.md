---
title: 'Define and Validate the Conformance Vector Contract'
type: 'feature'
created: '2026-09-27'
status: 'in-review'
baseline_commit: '9b3b099bf117eac880b9b6e12422990a168519eb'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Existing v1 tooling supplies most of Story 1.8, but accepts malformed vectors and presents the later loopback runner as the primary sample gate.

**Approach:** Harden the existing test-only schema and reusable validator, verify the synthetic vectors against a locally packed Contracts artifact, and document the v1 author approval and runner handoff.

## Boundaries & Constraints

**Always:** Retain v1 names, package identity/version, generic calls, Payload/Envelope inputs, request/response expectations, and assertion vocabulary. Close contract-owned objects; preserve Module-owned JSON data and all three samples. Use identical rules for authors and runners, with source/location/reason diagnostics. Compare package IDs case-insensitively and versions exactly.

**Never:** Add production dependencies, Module-specific branches, assembly loading, upstream edits, or publication. Require neither Head, Gateway, nor AppHost. Production restored-package rechecks and parity belong to Story 4.11; live semantics belong to Story 4.13. Runner defects remain outside this story.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Author approval | Valid synthetic Command and Query vectors plus packed owning artifact | Accept; CLI exits 0 | No network service needed |
| Compatibility | Wrong package ID/version, stale runner expectation, unsupported format | Reject; CLI exits 1 | Identify package or format location |
| Shape and syntax | Unknown contract fields, malformed names/ULIDs, blank required strings, non-JSON numbers | Reject at every call position | Located validation findings |
| Script consistency | Wrong-kind inputs/echo fields or conflicting supplied extensions | Reject contradictory expectations | Identify offending call field |
| Assertions | Unknown operator, invalid pointer, missing/wrong typed value | Reject | Assertion location and reason |

</frozen-after-approval>

## Code Map

All tooling paths below are under `tools/conformance-vectors/v1/` unless qualified.

- `schema.json` — operation regex allows extra dots, excludes digit-leading parts, and accepts trailing newlines.
- `validate.py` — reuse `validate_vectors`, `_check_step`, `package_identity`, and CLI; fix permissive JSON parsing and missing consistency checks.
- `test_validate.py` — 11 offline tests using temporary nuspec ZIPs; expand negative coverage.
- `README.md`, `run-sample-loopback.sh` — existing instructions and broader gate; preserve parity semantics.
- `tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj` — packs with `IsPackable=true`, `Version=1.0.0`; no project edits.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs` — naming reference: two dot-separated lowercase alphanumeric kebab-case parts; digit-leading parts allowed. Read only.
- `.github/workflows/ci.yml` — contract job currently executes loopback too.

## Tasks & Acceptance

**Execution:**
- [x] `tools/conformance-vectors/v1/schema.json` — align names, enforce strict string boundaries and nonblank inputs, preserve closed fields and assertion operators.
- [x] `tools/conformance-vectors/v1/validate.py` — reject nonfinite JSON with locations; check nonblank routing, supplied extensions, and query response echoes across all steps.
- [x] `tools/conformance-vectors/v1/test_validate.py` — cover the matrix, prerequisite/postcondition checks, ID/version mismatches, valid boundaries, and CLI/reusable-entry-point behavior.
- [x] `tools/conformance-vectors/v1/run-sample-validation.sh` — pack the sample into a temporary directory, run validator tests, validate all three vectors against the artifact and expected identity. Support Debug locally and Release in CI; clean only its temporary files.
- [x] `.github/workflows/ci.yml` — run the new offline gate independently; retain the existing loopback lane as a separate job.
- [x] `tools/conformance-vectors/v1/README.md` — record version, compatibility policy, approval procedure, validator invocation, and 4.11/4.13 handoff. Distinguish offline checks from later Catalog/payload compatibility and execution.

**Acceptance Criteria:**
- Given the existing sample Contracts project, when the standalone offline gate packs and validates its vectors, then all examples pass without building either Head or connecting to a Gateway.
- Given malformed or incompatible vectors, when authors or runners use the shared validator, then both receive actionable rejections under the same rules.
- Given the author instructions, when a maintainer prepares approval evidence, then they can identify the version, immutable artifact, validation command/result, and downstream responsibilities without parity or live tests.

## Implementation Notes

- Hardened the existing v1 schema and shared validator; all three sample vectors remain unchanged. CLI package expectations now also reject an explicitly empty expected package ID.
- Added a sample-only pack/validate gate with temporary build outputs and Debug/Release selection; CI runs it independently from the existing loopback job.
- Verification: all 41 Python tests passed, including the unchanged runner unit tests. Debug and Release sample gates both passed and accepted all three vectors against their packed artifact. Shell syntax, invalid configuration exit 2, temporary cleanup, CI job separation, and diff whitespace checks passed.
- Matrix audit: sample approval is covered by the packed gates and CLI success test; compatibility by artifact/runner ID and exact-version tests; syntax by closed-object, name, ULID, whitespace and nonfinite tests; script consistency by wrong-kind, extensions and echo tests; assertions by operator/pointer/value tests. The full verbose run executed every covering test successfully.
- Production code, upstream repositories, and parity/live implementations are unchanged. Full parity/live execution remains assigned to Stories 4.11/4.13.

## Spec Change Log

## Review Triage Log

## Verification

- `python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'` — all offline validator and existing runner unit tests pass.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh` — packed sample accepted independently.
- Run the same script with its documented Release selection to verify the CI path.
- Inspect CI job separation and repository diff for absence of production or upstream changes.

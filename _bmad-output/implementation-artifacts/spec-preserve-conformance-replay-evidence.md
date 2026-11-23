---
title: 'Preserve conformance replay evidence'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Resolve five ledger findings about conformance evidence. The runner should retain bounded, redacted diagnostics from both heads for discovery and malformed Payload probes, reject duplicate members in captured Gateway requests, and preserve the numeric value of Module-owned JSON during validation, replay and comparison. Verify that offline and Core envelope validation agree on canonical uppercase ULIDs.

</frozen-after-approval>

## Implementation Notes

- Build from `050328500a88406934088ddd2dacc0c7a6165ce7`. The user requested five deferred items and authorized publication on `main`. These five share conformance input and evidence boundaries. Planning found no outstanding product decision.
- Reuse the existing duplicate-key and finite-number checks in `validate.py`. Preserve decimal and exponent values exactly across Python boundaries while retaining the v1 overflow refusal and strict integer token checks. Apply the shared JSON handling to the loopback transport and the live runner consumers of the same vector and head data.
- Keep the 64 KiB diagnostic retention policy in `run_loopback.py`, drain overflowing streams, and save per-head probe diagnostics even when the probe fails. The PRD, schema, and `OperationExecutor.IsCanonicalUlid` already agree on canonical uppercase input. Verify the existing runtime rule and the offline boundary before closing its ledger entry.
- The .NET 11 Release solution build passed with zero warnings and errors. Release sample validation passed 203 Python tests and validated three vectors. All three sample loopback vectors passed. The packaged fixture passed isolated sample enrollment, SDK response, and Core preflight cases before the combined-package replay was stopped. A temporary Query vector retained `1e-400` and `1.0000000000000000001` in both heads’ JSON observations. All 16 focused Core envelope ULID cases passed. Pinned Commitlint reported zero problems and warnings.
- All 62 focused live-plan and runner tests and all 96 MCP tests passed. The broad live-topology Python run encountered a CI preparation failure requiring public Gateway, Aspire and Tenants archive identities. The same failure reproduced on the starting revision.
- The shared pre-push checker passed CI/CD ownership validation and the Release build. Its Core suite passed 921 tests and failed the existing 500 ms Catalog start-up benchmark. A separate Manifest run reported MSBuild server diagnostics and a fixture package restore failure. The missing-package diagnostic test passed when rerun with the MSBuild server disabled. Publication uses the user’s authorization to proceed despite the local checks.

## Review Triage Log

- Medium, patched. Convert fractional audit offsets to seconds at the `timedelta` boundary and test the approved plan representation.
- Medium, patched. Convert deadlines and polling intervals to floats for the timing APIs. A regression checks a fractional deadline across a retry.
- Medium, patched. Poll the stderr descriptor without the `select` descriptor limit.
- Medium, patched. Drain stderr for the Core compatibility, manifest discovery and malformed-command subprocesses using the bounded redactor.
- Low, patched. Preserve zero for extreme exponents, report a nonzero exponent outside the supported decimal range, and keep decimal tokens distinct from integer tokens when encoding them.
- Medium, patched. Verify that both stderr receipts survive a discovery process failure.
- Medium, verified. Replay exact decimal values through the built heads and inspect both persisted observations.
- Low, patched. Correct the ledger description of the Core ULID parser and canonical comparison.
- Medium, patched. Retain the existing located error when an assertion selector uses an integral noninteger token.

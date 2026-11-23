---
title: 'Close five loopback conformance evidence deferrals'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem.** Loopback replay drops child-process diagnostics, and a later package failure hides completed packages in the root enrollment receipt. Three older ledger entries still question exact Gateway requests, required public result fields, and Bearer authentication at the Gateway.

**Approach.** Retain redacted stderr per replay step for each head and preserve completed package results and shapes as enrollment progresses. Verify the existing wire and result checks, then close all five entries with evidence.

</frozen-after-approval>

## Implementation Notes

- Baseline `2f81ee19506e99e9d1b02923bc76654b69adfb7f` is the synchronized McpCli `main`. The three existing checks are in `run_loopback.py`, `test_loopback.py`, and `ConfigCommandTests.OneSourceGatewayUrlAndTokenReachOnlyThatGatewayAsync`. The user authorized publication on `main`.
- `run_loopback.py` retains redacted CLI and MCP stderr in per-head operation evidence. MCP uses a separate temporary stderr file so a child can finish writing diagnostics before responding on stdout. `verify_artifact.py` puts independent replay observations inside the verification run's retained directory.
- `check_enrolled.py` atomically replaces the root receipt after each completed package. The root receipt still requires combined production replay for acceptance. Regressions cover process capture and redaction, a chatty child, partial observations, and root receipt progress before a later package fails.
- Solution restore and the Release build passed with zero warnings or errors. All 198 conformance Python tests and all 12 cases of the focused Bearer header test passed. The exact commit message passed the pinned Builds commitlint policy with zero problems or warnings.

## Review Triage Log

- Medium, patched. CLI stderr is decoded independently of stdout, with replacement for invalid bytes and redaction of partial stderr from timed-out calls.
- Low, deferred. The 64 KiB limit applies to retained diagnostics. Child output still accumulates in the existing CLI capture and in MCP temporary storage before the retention check. See the replay capture ledger entry.
- Low, deferred. Discovery and malformed-Payload probes remain outside the operation observation files. See the replay capture ledger entry.
- Medium, patched. The malformed-command and compatibility-adapter failure messages now go through the same stderr redactor.
- Medium, patched. Standalone replay requires a new or empty evidence directory so failed or partial reruns cannot be mistaken for an earlier run's observations.
- Medium, deferred. Complete field comparison still uses the parsed request body. A duplicate wire property can collapse before the comparison. See the replay request ledger entry.
- Medium, patched. Root receipt updates use a same-directory temporary file and atomic replacement so a reader sees a complete update.
- Medium, patched. The packaged-process fixture follows the artifact receipt's observation path for both successful and failed replay.

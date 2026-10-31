# Operator setup acceptance checklist

Story [4.17](../../_bmad-output/implementation-artifacts/spec-4-17-verify-the-operator-setup-experience.md) remains **incomplete**. Use the [README operator setup](../../README.md#operator-setup-with-the-staged-120-tool) as the operator's instructions. This document is the observer's procedure and evidence index. Offline protocol smoke cannot satisfy a client row.

The approved staged tool is 1.2.0 from `32fb5dbf75216adaf21551bcfa36439741c41e01`; recheck both package hashes, prepared/accepted receipt hashes and clean-source binding against the README before every new installation. Do not publish the pair or enable paired publication.

| Required result | Status | Evidence / exact blocker |
| --- | --- | --- |
| Staged pair provenance and isolated installation | Passed offline only | [Exact package/receipt bindings, installed 1.2.0 and offline smoke](../../_bmad-output/implementation-artifacts/evidence/story-4-17/offline-verification-20261030/verification.json). |
| Platform preparation, review and owner bootstrap | Passed for current environment | [Live handoff and expiry](../../_bmad-output/implementation-artifacts/evidence/story-4-17/three-service-preparation-20261031/operator-handoff.md); real DNS/backup/metadata/admin/writer/readiness and persisted tenant/member passed. Owner staged-CLI non-admin read is supplemental; client rows remain unexecuted. |
| Claude Code actual session | Passed with assistance | [Interactive Claude Code 2.1.316 session](../../_bmad-output/implementation-artifacts/evidence/story-4-17/sessions/claude-code/attempt1/session.json): actual MCP server identity, five tools, both operation lists, three descriptions, fixed-system tenant read, one accepted creation and matching persisted details retained. Not independent timing. |
| Claude Desktop actual conversation session | Passed with assistance (Cowork tab, accepted by the user) | [Attempt4](../../_bmad-output/implementation-artifacts/evidence/story-4-17/sessions/claude-desktop/attempt4/session.json): one `hexalith` server bridged by `wsl.exe --cd`, initialized as 1.2.0. Nine actual calls, with request/result bodies decoded from Desktop's local conversation cache: both module lists, both operation lists, three submittable lint-clean descriptions, fixed-`system` tenant read, one accepted `party-417-desktop-20261031-4` creation (message/correlation `01M68SXJN755MY38306BXCS07D`) and a matching persisted read. Tenant and idempotency arguments were omitted. Desktop 4.29; the session ran in the Cowork tab, which the user accepted as the Desktop conversation session. Not independent timing. [Attempt3](../../_bmad-output/implementation-artifacts/evidence/story-4-17/sessions/claude-desktop/attempt3/session.json) (discovery incomplete) and the [earlier keyed failure](../../_bmad-output/implementation-artifacts/evidence/story-4-17/three-service-preparation-20261031/claude-desktop-20261031-attempt1/user-report.json) remain retained. |
| VS Code actual session with named harness | Passed with assistance | [Attempt3](../../_bmad-output/implementation-artifacts/evidence/story-4-17/sessions/vscode/attempt3/session.json): VS Code 1.144.0, Copilot CLI harness in a local Windows window, one `hexalith` server (config source `user`) bridged by `wsl.exe --cd`, initialized as 1.2.0. Eleven actual Hexalith calls: five tools, both operation lists, three descriptions, fixed-`system` tenant read, one accepted `party-417-vscode-20261031-1` creation (message/correlation `01M68RNGWZQQWCMH86E3RFT0KQ`, no idempotency key) and matching persisted read. The model passed the tenant argument equal to the session tenant, so routing by omission is not shown here. Not independent timing. [Attempt1](../../_bmad-output/implementation-artifacts/evidence/story-4-17/sessions/vscode/attempt1/session.json) and [attempt2](../../_bmad-output/implementation-artifacts/evidence/story-4-17/sessions/vscode/attempt2/session.json) failed before tool calls; [initialize-stall repair](../../_bmad-output/implementation-artifacts/evidence/story-4-17/sessions/vscode/initialize-stall-repair-20261031/receipt.json). |
| Independent new operator, README-only timing | Not executed | No elapsed time has been measured. |
| Task-owned environment cleanup | Current live environment retained | Three earlier failed environments were removed. Preserve current Redis/domain/tenant/writer state and journals during the keyed-admission decision; eventual UID-bound cleanup remains required. |

Before a client session, retain the environment owner's approval naming target `192.168.1.30`, exact private Gateway binding, namespace/release/UID, selected tenant, operator subject/actor, role, domains, `command:submit` and `query:read`, expiry, fresh Party ID and allowed synthetic payload. Record the concrete Platform review packet hash and deployment authorization separately. Check workload readiness and persisted seed state; never reuse another application's data or credentials. Keep the token, bootstrap authority, signing material, private profile and full unredacted client logs outside the evidence tree. Redact copies before saving; preserve operation names, public IDs, timestamps and outcomes.

Use a fresh directory for each client and attempt under `_bmad-output/implementation-artifacts/evidence/story-4-17/sessions/<client>/<attempt>/`. Never overwrite a failed session. Record:

- Observer and operator identifiers, prior familiarity with McpCli and whether this is the independent first-time operator.
- UTC start/end, exact OS/build/architecture, client version, extension version and selected harness; native Windows, WSL distribution or macOS/Linux launch environment.
- README Git revision when committed, otherwise SHA-256 of its exact bytes; package/receipt hashes, tool source SHA/version and absolute executable path.
- Sanitized client registration and destination, `MCPCLI_HOME`, runtime location/version, and whether the GUI inherited unexpected `EVENTSTORE_*` values. Retain no secrets.
- Connection/initialization negotiation or client server log, selected protocol version if exposed, server identity and actual client tool list. If initialization evidence is unavailable, say so and keep the row incomplete.
- Actual `list_modules`, both `list_operations` calls and three `describe_operation` calls; five generic tools, two modules and the required `submittable` results from one registered server.
- Actual Tenants `run_query`, its `tenant: system`, selected tenant's active document and membership; exact approved `send_command` argument object, fresh IDs, acceptance/error and message/correlation IDs; subsequent Parties `run_query` and the returned persisted synthetic fields in the selected tenant.
- Every failure, correction, permission prompt, elapsed period and human/agent assistance. Distinguish the tool's structured result from the model's interpretation. Record stdout/stderr or client server-log channels where available.
- Server/port-forward shutdown and environment cleanup outcome, including any retained task resources and their owner.

For each attempt, create a `session.json` using this shape. Nulls and `not-executed` are explicit missing evidence, never a passing value:

```json
{
  "schema": "mcpcli-operator-session/v1",
  "client": "Claude Desktop",
  "attempt": 1,
  "status": "not-executed",
  "operator": null,
  "observer": null,
  "priorExperience": null,
  "osVersion": null,
  "clientVersion": null,
  "extensionVersion": null,
  "harness": null,
  "launchEnvironment": null,
  "readmeSha256": null,
  "sourceSha": "32fb5dbf75216adaf21551bcfa36439741c41e01",
  "toolVersion": "1.2.0",
  "packageAndReceiptHashes": {},
  "environmentApproval": null,
  "deploymentReviewSha256": null,
  "selectedTenant": null,
  "partyId": null,
  "initializationEvidence": null,
  "discoveryEvidence": null,
  "tenantReadEvidence": null,
  "commandEvidence": null,
  "persistedPartyEvidence": null,
  "assistance": [],
  "failures": [],
  "cleanupEvidence": null
}
```

The timed operator must be a person unfamiliar with this tool who follows only the frozen README. Supply the accepted archives, installed prerequisites and ready approved environment through the owner's ordinary secure handoff before starting; do not coach them through the task. An experienced implementing agent cannot fill this role. Identify which one of the three client sessions is timed, or run a separate fresh attempt.

For the README quick start, the operator's own Claude Code runs the README setup prompt. That is the documented procedure (human decision, 2026-10-31), not assistance. Any other prompt, hint or correction from a person or another agent is assistance. Start the stopwatch immediately before the operator pastes the setup prompt; for the manual path, start it immediately before invoking `dotnet tool install`. Include profile setup, client registration, prompts, troubleshooting and all waits. Stop when that actual client receives its first `send_command` success (`isError: false`, `status: accepted`, correct tenant/Party ID). Continue the persisted Party query afterward; it is required for session acceptance even though the timer has stopped. Record UTC timestamps alongside the stopwatch reading, without deriving subsecond accuracy from screenshots alone.

Store every attempt in `timing-attempts.json` with `operator`, `priorExperience`, `client`, `harness`, `readmeSha256`, `startedAtUtc`, `endedAtUtc`, `elapsedSeconds`, `firstCommandEvidence`, `assistance`, `failures`, `interrupted` and `outcome`. Calculate `targetSeconds = 900`, `withinTarget = elapsedSeconds <= 900`, and `unassistedSuccess = withinTarget && successfulSendCommand && assistance.length == 0 && !interrupted && firstTimeOperator`. A failed, interrupted or still-running attempt has no successful stop; record elapsed-to-failure/observation separately and `unassistedSuccess: false`. Preserve attempts exceeding 900 seconds, including their eventual successful time. Assistance at any point stays attached to that attempt; a later fresh attempt never erases it.

The observer independently recalculates elapsed seconds from retained timer readings and checks the command response timestamp and README hash. Session status is `passed` only after initialization, discovery, approved command and persisted result are all evidenced. Use `failed`, `assisted`, `interrupted`, `incomplete` or `not-executed` otherwise, with exact failing step and correction. A passing client session does not repair a failed timing target.

Check unexecuted matrix cases explicitly: missing runtime, wrong executable/PATH or launch environment, invalid/missing private profile, insufficient read/write permission, unavailable service/forward, unknown command outcome, exceeded/assisted/interrupted timing. Execute only cases the owner has approved in the task environment; do not manufacture an unsafe write to fill a row. Attach actual sanitized evidence or mark `not-executed` with its reason.

Advance the story only when all three actual client rows pass, persisted effects exist, independent timing and every miss/assistance are retained and evaluated, and cleanup is evidenced. Missing records leave the checklist, spec and sprint status incomplete. Record any README correction with its new hash; keep the original attempt bound to the README the operator actually read.

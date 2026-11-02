# Operator setup acceptance checklist

Story 4.18 has an accepted historical 1.2.0 staging candidate from [Release run 41307182275](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/41307182275), source `17eb4fbbc151ca4b99dfa452e9f65655db2b402f`, and a previously approved ready environment. Current-main staging and public verification remain pending. The user approved an alternative candidate-specific automated-acceptance path on 2026-11-02; it records a human-validation bypass and does not assert fresh client-session success. The actual-session path remains available using the [generic README setup](../../README.md#operator-setup-with-an-accepted-staged-tool). The [Story 4.17 history](operator-setup-history.md) preserves older archives, sessions, failures, README revisions and removed environment. Neither historical candidate qualifies current source, despite the shared version number.

Source/access checkpoint: `main` advanced beyond the historical staging source, and any commit of this checklist/README correction advances it again. The prior package/client evidence remains valid only for its recorded archives; verify the exact committed current-main SHA with fresh CI and staging before publication. The user's two-hour [access renewal](../../_bmad-output/implementation-artifacts/evidence/story-4-18/access-renewal-20261101T163704Z/verification.json) expired on 2026-11-01. A renewed ready environment is needed only if the actual-session path is chosen; do not treat the expired forward or profile as current authorization.

| Required result | Current status | Required evidence |
| --- | --- | --- |
| Exact green current-main source | Pending for current source | [CI 41295964003](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/41295964003) and [commitlint 41295963952](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/41295963952) passed for the historical source only. Current-main CI, commitlint, FR-22 and all required executed jobs/steps must be verified again before staging and publication. |
| Fresh immutable staged pair | Pending for current source | [Historical candidate receipt](../../_bmad-output/implementation-artifacts/evidence/story-4-18/hosted-staging-20261101T123459Z/candidate.json) binds run 41307182275 and source `17eb4f...`; a new source-bound pair needs Linux, Windows and macOS acceptance, original artifact digests and recomputed receipts. |
| Newly approved ready environment | Historical; required only for actual sessions | [Historical deployment receipt](../../_bmad-output/implementation-artifacts/evidence/story-4-18/environment-20261101T124621Z/deployment.json) records all 13 phases, persisted tenant/Contributor and non-admin staged-CLI read. Its operator token/forward expired on 2026-11-01. |
| Claude Code actual session | Historical candidate only; client shutdown pending | [Actual session evidence](../../_bmad-output/implementation-artifacts/evidence/story-4-18/sessions/claude-code/attempt1/session.json): session `7ceb60f0-3ebf-490b-ba96-7ccb271ff745`, Claude Code 2.1.316, actual stdio identity/version, exactly five tools and nine successful calls, one creation `01M6BQKC4BC8AKQ5GEKE53VASX`, persisted `party-418-code-20261101-1` with all synthetic fields verified. Text/structuredContent agree for all nine results; successful client records omit explicit error fields. Auto mode accepted each call. |
| Claude Desktop actual session | Pending only if actual-session path is chosen | The same evidence from an actual Desktop conversation; name its harness/tab and every assistance/failure. |
| VS Code actual session | Pending only if actual-session path is chosen | The same evidence from the actual extension/harness; record version, native/WSL launch environment and absolute executable. |
| Timing exception | Existing exception retained explicitly | Historical assisted 685 seconds; `firstTimeOperator: false`, `unassistedSuccess: false`. No fresh first-time/unassisted success is claimed. |
| Candidate-specific acceptance | Pending | Either explicit operator approval with three fresh actual sessions or authenticated automated authorization bound to the new staging run, exact package/receipt/README hashes and current source. The automated path carries no session claim. |
| Production preflight and public pair | Pending production approval | Source/evidence rechecks, selected shared version, credentials and both free identities, push intentions/results, signature-aware public-content verification for both packages. |

## Automated acceptance path

After fresh current-main staging, submit `operator_acceptance` using schema `mcpcli-paired-automated-acceptance/v1`. Set `decision` to `approved`, `authorization` to `user-requested-human-validation-bypass`, `approved_by` to the authenticated human dispatch actor, and `decided_at_utc` to the actual decision time after staging completed. Include exact `staging_run_id`, `source_sha`, `version`, `packages`, `preparation_sha256`, `acceptance_sha256` and `readme_sha256` from that candidate. Omit `sessions` entirely. The verifier rejects a bot actor, mismatched binding, missing authorization, missing/pre-staging/future decision time or any `sessions` field. Retain the user's authorization and the exact sanitized packet with the release receipts. This path does not validate the three clients, the ready environment or operator timing; do not report those results for the new candidate. Production approval and public verification remain required.

## Actual-session acceptance path

Use the [historical session bindings](../../_bmad-output/implementation-artifacts/evidence/story-4-18/hosted-staging-20261101T123459Z/session-bindings.json) only as a format example; compute fresh bindings for each new candidate and repeat them in every actual session and the final operator decision. The historical local handoff is `/tmp/mcpcli-4-18-41307182275/handoff`, containing exactly the two old accepted archives and a local-only `NuGet.Config`. It contains no environment credentials. The [historical read-only feed observation](../../_bmad-output/implementation-artifacts/evidence/story-4-18/hosted-staging-20261101T123459Z/public-feed-observation.json) found both 1.2.0 identities available at that time; availability and publication credentials still require production preflight.

The [live operator handoff](../../_bmad-output/implementation-artifacts/evidence/story-4-18/environment-20261101T124621Z/operator-handoff.md) provides the exact installed executable, isolated Claude Code launcher, native Windows/WSL configuration fragments and distinct per-client task prompts. The owner's CLI tenant read is supplementary environment evidence; named-client acceptance uses each actual user session and its checked transcript.

Claude Code's actual transcript and connection log have now been checked and retained as sanitized evidence, with raw originals snapshotted privately. Its MCP server remains client-owned until the user exits the session. [Desktop configuration update](../../_bmad-output/implementation-artifacts/evidence/story-4-18/environment-20261101T124621Z/desktop-config-update.json) replaced only the existing `hexalith` entry with the fresh Windows/WSL bridge and preserved all other configuration. Fully quit/reopen Desktop, then use the [filled Desktop task](../../_bmad-output/implementation-artifacts/evidence/story-4-18/environment-20261101T124621Z/clients/claude-desktop-task.md) in an actual Desktop/Cowork conversation. Desktop and VS Code remain pending; final candidate-specific operator approval has not been inferred.

Windows/Cowork follow-up: the user confirmed Desktop was fully closed after its configuration was observed using the historical WSL paths again. [Bridge repair and verification](../../_bmad-output/implementation-artifacts/evidence/story-4-18/windows-cowork-bridge-20261101T164811Z/bridge-verification.json) confirms Windows `wsl.exe` launches the fresh WSL tool/profile and a read-only tenant/member query succeeds; only Desktop's `hexalith` entry changed, with other entries and a private backup preserved. Native Windows instructions are in `C:\Users\JeromePiquot\Documents\Hexalith-McpCli-4.18-20261101\START-HERE.txt`. The repo stays in WSL. Further publication-acceptance tasks wait for the new current-main staged candidate; this bridge check is not an actual Cowork acceptance session.

Before sessions, obtain the owner's concrete reviewed environment approval. Never reuse the old removed environment, another application's credentials/data, or old package/client acceptance. Keep tokens, signing/bootstrap material, private profiles and unredacted logs outside the evidence tree. Use one fresh synthetic Party ID per client and attempt. Stop after a failed or uncertain command; only bounded persisted-state reads may repeat. Remove only task-owned state under the approved cleanup procedure.

Retain every attempt under a new `_bmad-output/implementation-artifacts/evidence/story-4-18/sessions/<client>/<attempt>/` directory. Include actual sanitized client initialization, discovery and call/result records; version/OS/harness/launch/executable identity; source/version and both package/receipt hashes; exact README bytes/hash; UTC times; environment review/approval/ready-state evidence; every failure, correction, permission prompt and assistance; persisted person/contact/identifier fields; and client/server/forward shutdown plus owned cleanup. Never overwrite an earlier attempt. A model's narrative or offline smoke cannot replace actual client evidence. Use the historical session/timing procedures as observer guidance while binding every fresh session to its own candidate.

## Release dispatch for either path

The authenticated maintainer dispatches `Release` with `phase=paired`, `staging_run_id` naming the successful staging run, an empty `recovery_version`, and `operator_acceptance` containing one sanitized JSON packet for the chosen path. The packet is retained by the release run and its hash enters preflight/outcome receipts. GitHub authenticates the dispatch actor; `approved_by` must be that actor, and production approval still applies. JSON input is data, never shell code. Known ambient GitHub/publication credentials are refused before recording or importing a packet. The always-run retention step excludes raw operator files and emits checked copies plus original/retained hashes and an explicit redaction flag; it redacts known credential values even when validation refused the packet. The workflow-dispatch payload limit applies (65,535 characters across inputs); include focused sanitized raw excerpts and keep full sanitized records in the story evidence. Do not include credentials in the packet.

## Actual-session packet schema

The packet schema is `mcpcli-paired-operator-acceptance/v1`, with `decision: "approved"`, `approved_by`, `decided_at_utc`, `sessions` and `timing_exception`. Its top-level bindings, repeated identically in **each** session, are:

| Field | Required value |
| --- | --- |
| `staging_run_id` | Original successful Release run ID as an integer. |
| `source_sha`, `version`, `packages` | Exact prepared source/shared version and filename-to-SHA-256 map for both archives. |
| `preparation_sha256`, `acceptance_sha256` | SHA-256 of original `prepared.json` and `accepted-pair.json`. |
| `readme_sha256` | SHA-256 of the source and packed README used in every fresh session. |

`sessions` contains exactly one accepted record for each `client`: `Claude Code`, `Claude Desktop`, `VS Code`. Each record requires:

- `status: "passed"`, `actual_client: true`, the repeated bindings above, `operator`, `observer`, `os_version`, `client_version`, `harness`, `launch_environment`, `executable_path`, `selected_tenant`, unique `party_id`, `started_at_utc`, `ended_at_utc`, and arrays `assistance` and `failures` (retain every miss, even when later corrected).
- `environment_approval`: `decision: "approved"`, `ready: true`, `owner`, `target`, `namespace_uid`, `tenant` matching the session, `approved_at_utc` and `expires_at_utc`. Its approved window contains the whole session. The session begins after original staging completion and ends before the explicit decision.
- `server_identity: {"name":"hexalith","version":"<accepted-version>"}`, `tools` containing exactly the five generic tool names, `modules` and `operation_lists` containing `parties` and `tenants`, and `described_operations` containing `tenants.get-tenant`, `parties.create-party`, `parties.get-party`.
- `tenant_read`: `tenant: "system"`, `document_id` equal to the selected tenant, `is_active: true`, `membership_verified: true`.
- `command_result`: `status: "accepted"`, selected `tenant`, `aggregate_id` equal to the fresh Party ID, canonical uppercase ULID `message_id` and `correlation_id`.
- `persisted_party`: selected `tenant`, matching `id`, `isActive: true`, `isErased: false`, `synthetic_fields_verified: true`. The actual result excerpt must retain the checked synthetic person, contact and identifier values.
- `evidence`: exactly `initialization`, `discovery`, `tenant_read`, `command`, `persisted_party`, `cleanup`, `environment_approval`. Each value is `{"content":"<actual sanitized excerpt>","sha256":"<SHA-256 of the UTF-8 content string>"}`. Preserve actual request/result bodies, tool identities, timestamps and public IDs. Hashes alone without content are insufficient.

`timing_exception` must be exactly the following, replacing the SHA with the actual hash of the unchanged historical file:

```json
{
  "reference": "_bmad-output/implementation-artifacts/evidence/story-4-17/timing-attempts.json",
  "sha256": "<SHA-256 of that historical file>",
  "elapsed_seconds": 685,
  "first_time_operator": false,
  "unassisted_success": false,
  "decision": "accepted-existing-exception"
}
```

For the actual-session path, independently compare session timestamps, actual calls and persisted results with the packet. For either path, verify original package hashes, receipt hashes and full source against the staging run before dispatch; retain the full packet and its hash under Story 4.18. Source, SDK, dependency, README or package changes require a fresh staging pair and new candidate-specific approval through the chosen path. Do not transfer historical client evidence.

For a failed/uncertain/partial publication, preserve `paired-publication-outcomes`, the original authenticated staging archives, per-package intent/result/public receipts, release tag and durable publication markers. Determine each public version's presence and signature-aware consumer contents before proposing a recovery. No automatic paired recovery, duplicate push, same-version repack, new independent bootstrap version or completion claim is allowed. Bootstrap recovery is restricted to historical versions preceding the first pair and refuses paired-version markers. A reviewed recovery must explicitly account for every package; publication cannot make two NuGet pushes atomic.

Advance this checklist, the story spec and sprint status only after both public versions and their consumer contents verify. Until then, keep current-source staging, candidate-specific approval and production work pending and preserve exact refusals.

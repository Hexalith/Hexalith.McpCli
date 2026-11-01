# Operator setup acceptance checklist

Story 4.18 is pending fresh current-main staging, three actual client sessions and public verification. Follow the [generic README setup](../../README.md#operator-setup-with-an-accepted-staged-tool). The [Story 4.17 history](operator-setup-history.md) preserves the old 1.2.0 archives, sessions, failures, README revisions and removed environment. Those records do not qualify new archives.

| Required result | Current status | Required evidence |
| --- | --- | --- |
| Exact green current-main source | Pending hosted run | Latest exact-SHA successful push CI and commitlint, with every blocking job/step executed; release-automation, dependency, inventory, conformance/live and FR-22 synchronization gates. |
| Fresh immutable staged pair | Pending hosted run | Successful `stage-paired` run ID, both archives at the pinned semantic-release version, prepared and accepted receipts, acceptance-source evidence and three-OS receipts. |
| Newly approved ready environment | Pending owner review | Target, namespace/release/UID, private Gateway, readiness and persisted seed state, selected tenant, operator subject/actor, role/domains, `command:submit` and `query:read`, expiry, synthetic payload and fresh Party IDs. Keep deployment review and authorization evidence. |
| Claude Code actual session | Pending user participation | Initialization as the accepted tool version, five generic tools, both module/operation lists, three descriptions, fixed-system tenant read, one accepted creation and matching persisted synthetic Party. |
| Claude Desktop actual session | Pending user GUI participation | The same evidence from an actual Desktop conversation; name its harness/tab and every assistance/failure. |
| VS Code actual session | Pending user GUI participation | The same evidence from the actual extension/harness; record version, native/WSL launch environment and absolute executable. |
| Timing exception | Existing exception retained explicitly | Historical assisted 685 seconds; `firstTimeOperator: false`, `unassistedSuccess: false`. No fresh first-time/unassisted success is claimed. |
| Candidate-specific operator decision | Pending user acceptance | Explicit approval of this staging run, exact package/receipt/README hashes and all three fresh sessions. |
| Production preflight and public pair | Pending production approval | Source/evidence rechecks, selected shared version, credentials and both free identities, push intentions/results, signature-aware public-content verification for both packages. |

Before sessions, obtain the owner's concrete reviewed environment approval. Never reuse the old removed environment, another application's credentials/data, or old package/client acceptance. Keep tokens, signing/bootstrap material, private profiles and unredacted logs outside the evidence tree. Use one fresh synthetic Party ID per client and attempt. Stop after a failed or uncertain command; only bounded persisted-state reads may repeat. Remove only task-owned state under the approved cleanup procedure.

Retain every attempt under a new `_bmad-output/implementation-artifacts/evidence/story-4-18/sessions/<client>/<attempt>/` directory. Include actual sanitized client initialization, discovery and call/result records; version/OS/harness/launch/executable identity; source/version and both package/receipt hashes; exact README bytes/hash; UTC times; environment review/approval/ready-state evidence; every failure, correction, permission prompt and assistance; persisted person/contact/identifier fields; and client/server/forward shutdown plus owned cleanup. Never overwrite an earlier attempt. A model's narrative or offline smoke cannot replace actual client evidence. Use the historical session/timing procedures as observer guidance while binding every fresh session to its own candidate.

The authenticated maintainer dispatches `Release` with `phase=paired`, `staging_run_id` naming the successful staging run, an empty `recovery_version`, and `operator_acceptance` containing one sanitized JSON packet. The packet is retained by the release run and its hash enters preflight/outcome receipts. GitHub authenticates the dispatch actor; `approved_by` must be that actor, and production approval still applies. JSON input is data, never shell code. Known ambient GitHub/publication credentials are refused before recording or importing a packet. The always-run retention step excludes raw operator files and emits checked copies plus original/retained hashes and an explicit redaction flag; it redacts known credential values even when validation refused the packet. The workflow-dispatch payload limit applies (65,535 characters across inputs); include focused sanitized raw excerpts and keep full sanitized records in the story evidence. Do not include credentials in the packet.

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

Before dispatch, verify original package hashes, receipt hashes and full source against the staging run; independently compare session timestamps, actual calls and persisted results with the packet. Retain the full packet and its hash under Story 4.18. Source, SDK, dependency, README or package changes require a fresh staging pair and actual client sessions against those bytes. Do not transfer historical client evidence.

For a failed/uncertain/partial publication, preserve `paired-publication-outcomes`, the original authenticated staging archives, per-package intent/result/public receipts, release tag and durable publication markers. Determine each public version's presence and signature-aware consumer contents before proposing a recovery. No automatic paired recovery, duplicate push, same-version repack, new independent bootstrap version or completion claim is allowed. Bootstrap recovery is restricted to historical versions preceding the first pair and refuses paired-version markers. A reviewed recovery must explicitly account for every package; publication cannot make two NuGet pushes atomic.

Advance this checklist, the story spec and sprint status only after both public versions and their consumer contents verify. Until then, keep hosted/client/production work pending and preserve exact refusals.

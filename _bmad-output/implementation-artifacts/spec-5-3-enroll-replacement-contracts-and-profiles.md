---
title: '5.3 Enroll replacement contracts and profiles'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '4bc4be5deca889d1594b0d367e313592c9421fe8'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `Parties.Mcp` and `eventstore-admin` operators cannot yet move to McpCli safely. Nothing proves that downstream error detail stays out of either head (C06), and legacy-format Party IDs have no recorded disposition (C07). The approved Parties inventory has no delete oracles and misstates eligibility (`deferred-work.md:476`, `:569`). A flag or environment URL can also carry a stored profile token to another environment (G6).

**Approach:**
- Close C06 and C07 with generic guard tests over the enrolled Parties 1.5.1 catalog, plus an owner-approved Parties inventory 1.1.0 amendment.
- Bind the Gateway URL and token to one source (decision 1), and anchor profile names.
- Document the manual migration in README.
- Do not upgrade Parties Contracts: no release after 1.5.1 closes C06 or C07. Upstream 3.1.0 (`50904cc4`) still lists both as open gates and removes `projectionActorType` from the Parties queries.

## Boundaries & Constraints

**Always:**
- Keep production `src/` generic; only tests name Parties.
- Every guard asserts the full error document, stdout and stderr, and the MCP `Content` and `StructuredContent`, and fails when the guard is removed.
- Write the 1.1.0 inventory amendment as one versioned change. Preserve the exact approved 1.0.0 bytes under `evidence/story-5-3/approval/1.0.0/` and record the from/to SHA-256 hashes. The amendment counts only after the owner approves its exact bytes.
- Update README in the same change as any visible behavior. Anchor every new regex with `\z`.

**Never:**
- Change McpCli identifier validators or convert IDs.
- Add Parties-specific error mapping.
- Read `~/.eventstore/profiles.json` or `EVENTSTORE_ADMIN_*`.
- Enroll a new Parties version, or change vectors, live plans, `approval.json` or the dependency policy.
- Edit `references/`.
- Amend the Admin inventory; that is Story 5.7.
- Claim parity or retirement.

**Decisions (2026-11-08, user):**
1. **Single source for URL and token.** The Gateway URL and token must both come from one source: flags, environment, or the selected profile. Any mix fails as `configuration_invalid` before any Gateway call, the same resolver path as an invalid URL. The message names both sources and never the token. A URL with no token stays allowed. This follows Platform `ARCHITECTURE-SPINE.md:182`. Update `ResolvesPrecedenceAndRecordsSources` to this rule.
2. **`epic-2-retro-item-1-protect-profile-output` stays tracked.** It remains open at `sprint-status.yaml:180` and `deferred-work.md:398`. G6's output-file treatment: no admin `--output` semantics migrate, and McpCli's own output contract stands. Record this in `verification.md`.
3. **Keep the full spec** at about 2,700 tokens. Do not split it.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| C06 privacy | A Gateway failure for a Parties operation carries markers in `type`, `instance`, `tenantId`, `errors`, `extensions` and `rejectionType`, in a non-JSON body, and in an inner exception | The document is identical to a Sample operation's under the same failure | No marker appears on any channel of either head |
| C07 root ID | `PartyId` is `{GUID}`, `(GUID)` or X-format | `validation_failed` at the aggregate pointer; both heads produce equal documents | Zero Gateway calls |
| C07 reach | `PartyId` is `Legacy.party_01-A`; a child `Id` is `{GUID}` | The captured request carries both values byte-for-byte | N/A |
| Identity mismatch | A payload tenant or actor disagrees with the envelope, or a Parties payload has an extra tenant or actor member | `validation_failed` through both heads | Zero Gateway calls |
| Mixed sources | A `--url` or `EVENTSTORE_URL` with a profile token, or a flag URL with an environment token | `configuration_invalid` on every executing verb and on `mcp` | Zero Gateway calls; no token on any channel |
| One source | URL and token both from flags, both from environment, or both from the profile; or a URL with no token | Resolves as today | N/A |
| Admin state | A hostile `profiles.json` and `EVENTSTORE_ADMIN_*` are present | `modules`, `describe`, `send`, `query` and `mcp` ignore them | Nothing is read |
| Profile name | `dev` plus a trailing newline | Rejected through the Core store and CLI documents | Profile bytes are unchanged |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Execution/OperationError.cs:41-53` -- `FromGateway` copies only status, detail or title, reason, retryable, clientAction, retryAfter and a canonical correlation ID. `OperationExecutor.cs:35-42` maps other exceptions to a fixed `internal_error`. Keep both unchanged.
- `src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs:69-80` -- each field resolves independently (`Select` at `:132-149`). Add the decision 1 rule here as a `Failure(...)` (`:186`), comparing `sources["url"]` with `sources["token"]`.
- `src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:397-398` -- change the profile-name regex from `$` to `\z`. It is used at `:96` and `:338-344`.
- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:137-153`, `:302-305` -- the existing payload tenant and actor agreement checks. Add tests only.
- `src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs:140-143`, `SchemaDeriver.cs:322-331` -- aggregate-ID rule and String-kind child IDs. Do not change.
- Legacy-format root IDs cannot exist as streams. `AggregateIdentity.cs:11,136` (EventStore Contracts) enforces the same regex, and `Parties.Mcp` forwards the raw IDs, which the Gateway rejects. `PartyIdentifier.IsValid` admits these GUID forms (`PartyIdentifier.cs:24-50`).
- Delete outcomes (`PartyAggregate.cs:867-890`, `PartiesMcpTools.cs:390-423`, unchanged since the `4937309` pin):

  | Case | McpCli | Legacy |
  |---|---|---|
  | Missing | 404, `party-not-found` | `not_found` |
  | Erased | 422, `party-erasure-in-progress` | 422, or success if inactive |
  | Inactive | `accepted` (NoOp) | Idempotent success |

- C06 upstream: the Gateway sanitizes command rejections (`DomainCommandRejectedExceptionHandler.cs:43-58`), but passes a module's query `ErrorMessage` through for 500 and 501 (`QueryExecutionFailedExceptionHandler.cs:88-94`). Parties returns only sentinel codes (`PartySdkQueryService.cs:242,248`).
- Tests to extend:
  - `CliMcpCommandParityTests.cs` and `CliMcpQueryParityTests.cs` -- the both-heads harness.
  - `ExecutionFailureCommandTests.cs:1059` -- the stderr pin.
  - `QueryValidationCommandTests.cs:168` -- the full-document zero-call pattern.
  - `ConfigCommandTests.cs:595`, `:2071` -- admin isolation, config verbs only.
  - `SettingsAndRegistrationTests.cs:14`, `ProfileStoreTests.cs:494`.
- `README.md:277-308` -- the profile section. There is no migration text yet.
- `_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md:31-33` (eligibility), `:124-126` (C05–C07). `evidence/story-5-1/approval/` is the amendment precedent. No gate hashes this markdown; `approval.json` binds `tools/inventory-coverage/v1/parties-approved.json`.

## Tasks & Acceptance

**Execution:**
- [x] `tests/Hexalith.McpCli.Cli.Tests/PartiesMigrationCompatibilityTests.cs` -- covers the C06 marker and Parties-versus-Sample equality cases, plus the C07 root and reach cases, through both heads. Pins C06 and C07 without module code.
- [x] `tests/Hexalith.McpCli.Cli.Tests/` (the parity and config tests), plus Core `SettingsAndRegistrationTests` and `ProfileStoreTests` -- cover identity mismatch through both heads, hostile admin state on the host-building verbs, the nine-name environment allowlist, the mixed-source and one-source cases (CLI and `mcp`) and the newline-suffixed name. Pins G6.
- [x] `src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs` and `ProfileStore.cs` -- apply the decision 1 rule and the `\z` anchor.
- [x] `README.md` -- add "Move from eventstore-admin or Parties.Mcp": no import, ignored admin variables, the `--api-url`/`--api-token` mapping, one profile per environment, the full precedence order and the single-source rule. Also add the error-privacy statement and the refused legacy GUID forms.
- [x] Parties inventory 1.1.0, `evidence/story-5-3/approval/` (preserved 1.0.0 bytes plus `approval.json`), and `verification.md` -- the amendment:
  - Reword the eligibility text.
  - Add the C05 delete oracles, including the erased-case difference.
  - Record the C06 resolution with the test anchors and the reliance on upstream query handling.
  - Record C07: legacy root forms are refused, and child IDs are preserved.
  - HALT for exact-byte owner approval.
- [x] `deferred-work.md` and `sprint-status.yaml` -- add resolution lines at `:476` and `:569`. Grep before adding a Story 5.3 entry for the Gateway query-detail upstream handoff. Close `epic-2-retro-item-2`, and leave item 1 open (decision 2).

**Acceptance Criteria:**
- Given the enrolled catalog, when the whole change is built, then `src/` contains no Parties name and no new dependency, and `DependencyPolicyTests`, `EnrolledModuleCoverageTests` and `check_enrolled.py` pass unchanged.
- Given approved inventory 1.0.0, when 1.1.0 is recorded, then the preserved bytes hash to the committed 1.0.0 and the receipt binds both hashes and the owner's verbatim label.
- Given a migrating operator, when they follow README, then each claim matches the built CLI.

### Review Findings

Pass 2, 2026-11-09. Full review of `4bc4be5..1ff2052`; independent blind-hunter (BH), edge-case-hunter (EC), verification-gap (VG), and acceptance-auditor (AA) passes completed. VG found no verification gaps. Result: 0 decisions, 3 patches, 0 deferrals, 7 rejected candidates. No product changes applied.

- [x] [Review][Patch] R2-P1 (medium): Record the legacy delete pre-read failure in C05. [`_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md:182`, `_bmad-output/implementation-artifacts/evidence/story-5-3/verification.md:221`] The new missing-party `not_found` oracle omits the SDK pre-read path: `PartiesMcpTools.cs:406` reads first; absent detail returns `ReadModelUnavailable` at `references/Hexalith.Parties/src/Hexalith.Parties/Queries/PartySdkQueryService.cs:324-326`. Its `actor-not-found-infrastructure` wire value fails the space-based not-found checks at `references/Hexalith.EventStore/src/Hexalith.EventStore.Server/Pipeline/SubmitQueryHandler.cs:159-162`, falls through to 500 at `:133-141`, and becomes legacy `downstream_failed` at `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs:597`, before a deactivate command runs. The pinned Parties `4937309` service also returns `ActorNotFoundInfrastructure` for absent detail; the cited current service additionally suppresses erased detail. Record the dispatch/read-model conditions for each oracle, correct the verification narrative and ledger resolution, and prepare a new versioned owner-approved amendment while preserving approved 1.1.0 bytes and receipt.
- [x] [Review][Patch] R2-P2 (low): Complete invalid-profile recovery. [`README.md:432`] Renaming or deleting an active `dev\n` profile key leaves `activeProfile` pointing to the old key. The documented next `config profile list` still exits 2 with `The active mcpcli profile does not exist.` Tell operators to update or clear `activeProfile` as well. Parent reproduced both the failure and successful recovery on the built CLI.
- [x] [Review][Patch] R2-P3 (low): Validate the exact owner approval label in the static check. [`_bmad-output/implementation-artifacts/evidence/story-5-3/verification.md:122`] Truthiness accepts contradictory nonempty top-level and amendment approval instructions. Replace it with equality to the recorded owner label and consistency with the corresponding decision/authority-confirmation fields. Parent ran the extracted checker with an in-memory receipt containing `Reject amendment` and `Not approved`; it still reported approved-mode success. The committed receipt itself has the correct labels and hashes.

Patch application (2026-11-09, user selected "1"): all three findings are fixed. After the 1.2.0 diff and SHA-256 `2f359904fe87fab8325b6fc759676c1fc792a27e0857d47631d8eeec8b420a28` were presented with the explicit Parties-owner action label, the user replied "approve". `evidence/story-5-3/approval/amendment-1.2.0.json` records that accepted label and the separate verbatim reply, preserving the approved inventory bytes and the exact prior 1.1.0 inventory/receipt. The corrected verification and C05 ledger entry are resolved. See `evidence/story-5-3/approval/amendment-1.2.0.diff` and `evidence/story-5-3/review-pass-2-validation.json`. The approved-mode static check and seven negative-label probes pass; both documented recovery paths pass on the built CLI. Story/sprint status is `done`.

Validation in this review: fresh solution restore and Release build with 0 warnings/errors; 281 CLI/MCP tests passed; 124 Core settings/profile tests passed with 3 Windows-only skips; 25 live-runner unit tests passed; approved inventory static/hash check passed; `git diff --check` passed. No live topology or Windows execution. An additional malformed non-2xx Problem Details probe returned the fixed 422 reason phrase with no marker on either CLI channel.

Individual verdicts were assigned before grouping. BH1 and AA1 share R2-P2; BH6 and EC1 share R2-P3.

| ID | Source | Verdict | Evidence and disposition |
|---|---|---|---|
| BH1 | blind-hunter | low | Key-only repair leaves a dangling active selection; parent reproduced exit 2, then exit 0 after repairing `activeProfile`. Patch R2-P2. |
| BH2 | blind-hunter | medium | C05 omits the SDK pre-read 500 / `downstream_failed` chain traced above; missing detail also fails in pinned Parties `4937309`. Patch R2-P1. |
| BH3 | blind-hunter | false | A credential/query/fragment-bearing request URI cannot reach these loggers through the shipped host: `SettingsResolver.cs:69-74` rejects it before host creation, and Gateway submission uses fixed command/query paths. The formatter has its direct redaction test; no reachable leak from this proposed mutation was shown. Reject. |
| BH4 | blind-hunter | low | `ScriptedGateway.cs:96` discards connection tasks, so a throwing response callback can fault unobserved. Current callbacks complete in the passing cases, and shutdown cancels network reads; adding task tracking and callback-failure plumbing for failed-test teardown is disproportionate. Reject. |
| BH5 | blind-hunter | maybe-false | `BothHeads.cs:113-124` skips its explicit task await on client failure, but `await using` still disposes the MCP server and transports. A failed-initialization reproduction proving work survives disposal is needed; any demonstrated impact here would be confined to failed-test cleanup. Reject as unverified and low impact. |
| BH6 | blind-hunter | low | The static check accepts conflicting nonempty approval labels; parent confirmed this with an in-memory receipt. Patch R2-P3. |
| BH7 | blind-hunter | low | The static checker does not assert receipt path fields, but all committed paths point to the files it hashes. Extra guards for a manually corrupted receipt are outside this direct correction. Reject. |
| BH8 | blind-hunter | low | The new matrix lacks a malformed non-2xx JSON case. Parent exercised that existing client-parser path: 422, fixed reason phrase, no privacy marker. Adding another guard case without an observed failure is unnecessary. Reject. |
| BH9 | blind-hunter | low | D/N GUID positive cases are absent from this new matrix, but current String routing accepts them and the required support-safe positive case is covered. The proposed broad future GUID rejection is hypothetical; no current reachability defect was shown. Reject. |
| BH10 | blind-hunter | low | Real-process hostile-state cases do not inject `Parties__Mcp__*`, but current operator resolution reads the nine explicit names and has no binding to that host section. Another injection case adds coverage without exposing a current failure. Reject. |
| EC1 | edge-case-hunter | low | Same contradictory-label acceptance as BH6; independently reproduced by parent. Patch R2-P3. |
| AA1 | acceptance-auditor | low | README's key-only recovery does not satisfy the built-CLI claim when the invalid key is active. Patch R2-P2. |

**Rejected**

- BH3 — false: invalid sensitive URI components are rejected before the production logger can receive them.
- BH4 — low: additional connection-task bookkeeping addresses unusual failed-test teardown, with no failure in current cases.
- BH5 — maybe-false, low if true: surviving work after asynchronous server disposal was not demonstrated; requires a faulted-initialization probe.
- BH7 — low: committed receipt paths are correct; extra corruption guards add work beyond a direct correction.
- BH8 — low: the additional malformed-error probe was safe; another test adds no demonstrated regression protection for this change.
- BH9 — low: supported String-kind routing has no observed D/N GUID rejection; the suggested future mutation is hypothetical.
- BH10 — low: no production setting binds the Parties host section; another hostile-variable test guards no demonstrated failure.

## Implementation Notes

- 2026-11-08 (build):
  - **Production changes.** `SettingsResolver.cs:81` enforces decision 1 on every verb that resolves settings: discovery, `config current`, `config profile add`, `send`, `query` and `mcp`. A token without any URL also resolves, since no Gateway can be called. `ProfileStore.cs:397` uses `\z`.
  - **C06 leak found and fixed.** The C06 inner-exception guard exposed a real leak: the default `IHttpClientFactory` loggers wrote transport exceptions that quote downstream response text to stderr. `HostFactory.cs:51-57` now installs the generic `GatewayPipelineHttpLogger` and `GatewayHandlerHttpLogger`, which keep the same four entries without exception text or URL query. Removing them fails only the two inner-transport cases.
  - **Live runner.** `tools/live-topology/run_live.py` now passes the Gateway URL through `EVENTSTORE_URL` with `EVENTSTORE_TOKEN`, so it stays a single source.
  - **Verification.** The parent independently confirmed:
    - the Release build has 0 warnings;
    - the matrix-covering CLI classes pass (325 passed) and the Core settings and profile classes pass (131, with 3 Windows-only skips);
    - Mcp.Tests pass (94);
    - `git diff --check` is clean;
    - the preserved 1.0.0 bytes hash to the committed `c4db93be…`.
  - **Pending.** Inventory 1.1.0 (`5715ba01…`) awaits exact-byte owner approval.
- 2026-11-08 (user): "Review first, then approve". The step-04 review runs with the approval receipt pending. The final 1.1.0 bytes and hash are presented for one exact-byte approval after any review fixes. The inventory task stays open until then.
- 2026-11-09 (review pass 1):
  - **Patches.** The implementation agent applied P1–P14: Query pass-through scope, C05 restricted and erased oracles, the other copied fields, the operator-settings wording, the Story 4.1 checker scope with a reproducible 1.1.0 static check, a receipt aligned with Story 5.1, the parenthesized child ID, `modules`/`config current` mixed-source cases, blank-token precedence, the `EVENTSTORE_` source class, the README token-audience, behavior-change and invalid-name recovery notes, and the stdio admin variable.
  - **Defers.** The parent appended two Story 5.3 ledger entries: the Platform reference-runner handoff (EC1, by the user's decision "Keep rule, hand off to Platform") and the pre-existing profile identity fields beside a flag/environment connection (EC4). BH3's host configuration is already tracked (`deferred-work.md:168`).
  - **Final verification.** It passes on the final tree: Release build with 0 warnings; Abstractions 20, Analyzers 19, Core 877 (4 skipped), Cli 556 (2 skipped), Mcp 94 and Manifest 362; `EnrolledModuleCoverageTests` 5; `check_enrolled.py` with full-v1 acceptance true; live-topology unit tests 198 OK; preflight exit 0; the static check; `git diff --check` clean. No live lane, Aspire tier or Windows suite was run.
- 2026-11-09 (owner approval): After presentation of the final 1.1.0 word diff and SHA-256 `8fc4078842d141151c521f0288f1eb7f9b984505c7b4a1458fa40de8dba4c51e`, the user selected "Approve Parties 1.1.0 as Parties owner". `evidence/story-5-3/approval/approval.json` records the label verbatim, the approver, the Parties owning-maintainer authority and both hashes. The static check passes in approved mode.

## Spec Change Log

## Review Triage Log

Pass 1, 2026-11-08. Layers: blind (BH), edge case (EC), verification gap (VG; no gaps, one other finding).

| ID | Verdict | Evidence | Route |
|---|---|---|---|
| BH1 Single-source rule fails offline verbs and contradicts README | false | An invalid `EVENTSTORE_URL` already fails `modules` through the same resolver path (probed on the built CLI), as decision 1 requires. README's offline claims concern sessions with no URL, which still work, and a dedicated troubleshooting row covers the mix. | reject |
| BH2 No mixed-source tests on discovery or `config current` | low | README names discovery and `config current`. Tests cover `send`, `query`, `mcp` and `config profile add` only. | patch P8 |
| BH3 "Exactly nine environment variables" is false for the host | low | `Host.CreateApplicationBuilder` loads `Logging__*` and content-root `appsettings*.json`, and `MCPCLI_HOME` is also read. The README sentence is new. The host loading is already tracked (`deferred-work.md:168`). | patch P4 |
| BH4 Privacy text omits other verbatim fields | low | `OperationError.cs:41-53` also copies `reason`, `clientAction` and `retryAfter` as sent. A non-JSON response's detail is the reason phrase (the `text` case pins "Internal Server Error"). | patch P3 |
| BH5 Query pass-through is wider than 500 and 501 | medium | `GetSafeDetail`'s default arm returns module text for every status except the invalid-page 400 and 403. That includes the 400 malformed-request path (`SubmitQueryHandler.cs:104-113`). Four texts are wrong. | patch P1 |
| BH6 C05 oracles omit the restricted guard and merge erased states | medium | `PartyAggregate.cs:867-890` checks missing, erasure (`RejectIfErasureInProgress` also covers `Erased`), then `RejectIfRestricted`, then NoOp. The legacy tool has no restriction check, so an inactive restricted party is an unrecorded difference. | patch P2 |
| BH7 C07 is not resolved; child forms are untested | low | The "neither half met" claim is false: legacy forms were never addressable (`Parties.Mcp` forwarded them raw and the Gateway rejected them), so no existing party loses reach. README's "any of these forms" lacks a parenthesized child case. | patch P7 |
| BH8 Artifacts read as approved while approval is pending | false | The 1.1.0 bytes state that the amendment "counts only after the owner approves these exact bytes" and name the receipt. The ledger lines say "effective once the owner approves". This is the 5.1 amendment precedent of approving final `status: approved` bytes. | reject |
| BH9 Receipt schema diverges from the 5.1 receipt | low | The 5.1 receipt uses amendment `approval_decision`, `approval_basis`, `source_spec` and `to_first_committed_revision`, plus top-level authority and identity fields. 5.3 adds `owner_label_verbatim`, and its `pending_requirement` names one slot. | patch P6 |
| BH10 Story 4.1 checker now fails; no amendment check | medium | `evidence/story-4-1/verification.md:28` asserts `inventory_version: '1.0.0'`, while the 1.1.0 bytes still call that checker repeatable. Verification commands use `git show HEAD:`. | patch P5 |
| BH11 Token mapping gives no audience warning | low | The README maps `--api-token` straight to `--token` and warns only about the URL. | patch P11 |
| BH12 No behavior-change note for existing users | low | Profile-URL-with-injected-`EVENTSTORE_TOKEN` setups now fail; the rule is described only inside the migration section and the options paragraph. | patch P12 |
| BH13 Gate evidence comes from mixed builds; live lane not rerun | low | `verification.md` records `GatewayHttpLogTextTests` as added after the full Cli run. The parent reruns full suites after the patches. The live lane needs the private runtime and stays unrun (reported). | patch P15 |
| BH14 `SourceClass` maps unknown labels to environment | low | `SettingsResolver.cs` treats any label other than flag, profile or default as environment. An explicit `EVENTSTORE_` prefix test is a direct correction. | patch P10 |
| BH15 Mixed-source check precedes blank-token validation | low | Probed: `--url` with `EVENTSTORE_TOKEN=" "` reports the same-source message instead of the blank-token error. | patch P9 |
| BH16 Stdio hostile-admin evidence uses a fixture and omits a variable | low | `McpStdioProcessTests` uses the StdioHost fixture with an injected profile path, and its environment omits `EVENTSTORE_ADMIN_FORMAT`. `verification.md` overstates it. | patch P14 |
| VG-O1 Stored `dev\n` name blocks every verb, with no recovery path | low | Probed: `config profile list` returns "The mcpcli profile document has an invalid profile entry." Only hand editing recovers, and no README row says so. | patch P13 |
| EC1 Platform reference runner mixes `--url` with `EVENTSTORE_TOKEN` | high | `references/Hexalith.Platform/checks/reference/runner.py:141-145` and `test_reference_suites.py:203`. The user kept decision 1 ("Keep rule, hand off to Platform"). There is no McpCli-side fix and `references/` is read-only. | defer (upstream handoff) |
| EC2 Legacy `dev\n` key has no repair path | low | Same root cause as VG-O1. | patch P13 |
| EC3 Blank token hidden by the mixed-source message | low | Same root cause as BH15. | patch P9 |
| EC4 Flag or environment URL and token still use the active profile's tenant, actor and extensions | medium | `SettingsResolver.cs:87-128` resolves tenant, actor, `allowTenantOverride` and `allowedExtensions` from the selected profile whatever the URL source. This predates the story, and the frozen matrix says one-source cases resolve "as today". Not tracked in the ledger. | defer |
| EC5 Reason phrase reaches detail | low | Same root cause as BH4. | patch P3 |
| EC6 `ScriptedGateway` header line without a colon throws | low | Test-only helper; `HttpClient` never sends such a line. The fix adds a guard branch. | reject |
| EC7 400 Query details are treated as sanitized | medium | Same root cause as BH5. | patch P1 |
| EC8 Allowlist test cannot see ambient host configuration | low | Same root cause as BH3. | patch P4 |

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` -- expected: 0 warnings.
- `dotnet test tests/<Core|Cli|Mcp|Manifest>.Tests --no-build --configuration Release`, one project at a time -- expected: all pass.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.EnrolledModuleCoverageTests` and `python3 tools/conformance-vectors/v1/check_enrolled.py --output /tmp/mcpcli-enrolled-evidence-5-3` -- expected: pass.
- `git show HEAD:_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md | sha256sum` -- expected: equals the preserved 1.0.0 hash.

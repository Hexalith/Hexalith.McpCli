---
title: '5.3 Enroll replacement contracts and profiles'
type: 'feature'
created: '2026-11-08'
status: 'draft'
route: 'dispatch'
review_loop_iteration: 0
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
- [ ] `tests/Hexalith.McpCli.Cli.Tests/PartiesMigrationCompatibilityTests.cs` -- covers the C06 marker and Parties-versus-Sample equality cases, plus the C07 root and reach cases, through both heads. Pins C06 and C07 without module code.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/` (the parity and config tests), plus Core `SettingsAndRegistrationTests` and `ProfileStoreTests` -- cover identity mismatch through both heads, hostile admin state on the host-building verbs, the nine-name environment allowlist, the mixed-source and one-source cases (CLI and `mcp`) and the newline-suffixed name. Pins G6.
- [ ] `src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs` and `ProfileStore.cs` -- apply the decision 1 rule and the `\z` anchor.
- [ ] `README.md` -- add "Move from eventstore-admin or Parties.Mcp": no import, ignored admin variables, the `--api-url`/`--api-token` mapping, one profile per environment, the full precedence order and the single-source rule. Also add the error-privacy statement and the refused legacy GUID forms.
- [ ] Parties inventory 1.1.0, `evidence/story-5-3/approval/` (preserved 1.0.0 bytes plus `approval.json`), and `verification.md` -- the amendment:
  - Reword the eligibility text.
  - Add the C05 delete oracles, including the erased-case difference.
  - Record the C06 resolution with the test anchors and the reliance on upstream query handling.
  - Record C07: legacy root forms are refused, and child IDs are preserved.
  - HALT for exact-byte owner approval.
- [ ] `deferred-work.md` and `sprint-status.yaml` -- add resolution lines at `:476` and `:569`. Grep before adding a Story 5.3 entry for the Gateway query-detail upstream handoff. Close `epic-2-retro-item-2`, and leave item 1 open (decision 2).

**Acceptance Criteria:**
- Given the enrolled catalog, when the whole change is built, then `src/` contains no Parties name and no new dependency, and `DependencyPolicyTests`, `EnrolledModuleCoverageTests` and `check_enrolled.py` pass unchanged.
- Given approved inventory 1.0.0, when 1.1.0 is recorded, then the preserved bytes hash to the committed 1.0.0 and the receipt binds both hashes and the owner's verbatim label.
- Given a migrating operator, when they follow README, then each claim matches the built CLI.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` -- expected: 0 warnings.
- `dotnet test tests/<Core|Cli|Mcp|Manifest>.Tests --no-build --configuration Release`, one project at a time -- expected: all pass.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.EnrolledModuleCoverageTests` and `python3 tools/conformance-vectors/v1/check_enrolled.py --output /tmp/mcpcli-enrolled-evidence-5-3` -- expected: pass.
- `git show HEAD:_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md | sha256sum` -- expected: equals the preserved 1.0.0 hash.

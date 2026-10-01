---
title: 'Run a Valid Query Through the Gateway'
type: 'feature'
created: '2026-10-01'
status: 'done'
baseline_commit: 'ff7f5e18ee9eeeee7dae30ca52b2c6ee2e841896'
route: 'dispatch'
review_loop_iteration: 0
context:
  - 'AGENTS.md'
  - 'references/Hexalith.AI.Tools/hexalith-llm-instructions.md'
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Query submission exists, but Story 2.5 lacks complete acceptance coverage and the required live Tenants proof.

**Approach:** Test the CLI and executor with synthetic Contracts, then run a throwaway pinned-client query against local EventStore and Tenants. Correct production behavior only for demonstrated acceptance failures.

## Boundaries & Constraints

**Always:** Validate before exactly one submission using descriptor routing. Aggregate precedence: explicit, accessor, constant; explicit/accessor conflict fails. Fixed Tenant wins over session; conflicting per-call Tenant fails. Otherwise per-call Tenant requires no session Tenant or enabled override; an identical value needs no override. Missing Tenant fails. CLI `--tenant` is session-only.

Follow addendum §G: required `operation`, `tenant`, `document` including null; omit absent paging. Synthesize neither correlation nor extensions. Stdin uses `--payload -`.

Use EventStore.Client 3.110.0 directly with the existing EventStore AppHost and root-declared checkouts, or the already running local EventStore/Tenants topology authorized by the user on 2026-10-01. For the authorized running topology, reuse its generated local administrator identity in memory and record its actual source revisions; a separate isolated AppHost run is not required. Record credential-free evidence. `index` remains a candidate for Tenants maintainer confirmation in 4.8. Completion requires a live page.

**Never:** Add module-specific production code, enroll undecorated packages, update dependencies, edit `references/`, initialize nested submodules, replace the user's topology, or add a test AppHost. Defer paging validation, identifier boundaries, general parser/output work, commands and MCP changes.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Payload sources | Inline JSON, `@file`, stdin | Identical descriptor-routed request; one POST; canonical document | Exit 0 |
| Aggregate | Accessor; matching explicit; constant; explicit overriding constant; explicit without source | Selected aggregate reaches Gateway | Success |
| Aggregate refusal | Explicit/accessor conflict; neither source nor explicit value | Zero calls | `validation_failed`, `/aggregateId` |
| Tenant | Fixed/session/per-call; override on/off | Trusted Tenant; fixed wins | Conflict or missing: `validation_failed`, `/tenant`, zero calls |
| Results | Non-null and null Gateway payload, no metadata | Exact required fields; no paging, correlation or extensions | Exit 0 |
| Live proof | `system`, `tenants`, `index`, `list-tenants`, `tenant-index` | Pinned client receives a page; candidate matches Gateway pattern | Capture exact blocker if unsuccessful |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli/Cli/CliRunner.cs` — `CreateQuery`, `ReadPayloadAsync`; reuse injected settings/manifest seams.
- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — existing tenant/aggregate resolution, requests and result mapping.
- `tests/Hexalith.McpCli.Cli.Tests/CliMcpQueryParityTests.cs` and `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs` — reuse loopback and NSubstitute patterns.
- `tests/fixtures/Catalog.Routing.Contracts/` — interface routing/no-source queries; its String constant in a ULID module cannot prove constant success.
- `references/Hexalith.EventStore/src/Hexalith.EventStore.AppHost/Program.cs` — Tenants composition; source mode uses `UseHexalithProjectReferences=true` and root `HexalithTenantsBasePath`.

## Tasks & Acceptance

**Execution:**
- [x] `tests/fixtures/Catalog.String.Contracts/ListItemsQuery.cs` — add a described constant query for successful String aggregate resolution.
- [x] `tests/Hexalith.McpCli.Core.Tests/QueryExecutionTests.cs` — cover aggregate/tenant matrix; assert exact requests/results and zero calls on refusal.
- [x] `tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj` — reference the existing String Contracts fixture.
- [x] `tests/Hexalith.McpCli.Cli.Tests/QueryCommandTests.cs` — exercise payload-source matrix through CLI parsing and bounded loopback; assert method/path, full request, one call, exact object/null results, exit 0. Restore streams/listeners on failure.
- [x] `/tmp/mcpcli-story-25-spike/` — create direct-client harness; inspect the user-authorized running EventStore/Tenants topology through Aspire; use its generated local administrator credentials only in memory. Submit list query and preserve the user's running resources.
- [x] `_bmad-output/implementation-artifacts/query-spike-2-5.md` — record reproducible commands, full source revisions, pin, endpoint, identity requirements, routing, pinned pattern source, sanitized page and maintainer handoff; document exact blockers.
- [x] `README.md` — document query inputs, aggregate resolution and result fields.

**Acceptance Criteria:**
- Given the matrix fixtures, when focused Core and CLI tests run, then all scenarios pass and every refusal makes zero Gateway calls.
- Given local EventStore and Tenants, when the pinned-client spike submits the documented request, then it receives a page and verifies `index` against both the pinned pattern and live response.
- Given the completed change, when existing Core and CLI suites run individually, then they pass without changed discovery, settings or head parity behavior.

## Implementation Notes

- Added a String-kind constant query and 27 Core matrix cases, plus 19 bounded CLI payload-source/routing/object-null/profile result cases. The existing executor and CLI satisfy the demonstrated acceptance scenarios; no production behavior changed.
- The existing Catalog test now selects `string-fixture.lookup` by name because the String fixture has two operations. Existing discovery, settings, and head parity suites pass.
- Created and built the direct pinned-client harness under `/tmp/mcpcli-story-25-spike/`. Its validate-only path verifies `index` against the pinned pattern but sends no query.
- The original separate-host attempt was blocked by shared Dapr identities/endpoints and temporary paths. After user approval to reuse the running topology, the direct client returned a Tenants page containing one item from `http://localhost:8080/api/v1/queries`. Full evidence, reproducible harness/launcher source, runtime revisions, and maintainer handoff are in [query-spike-2-5.md](query-spike-2-5.md). No user resources or reference checkouts were changed.

## Spec Change Log

- 2026-10-01: The user authorized reuse of the already running EventStore/Tenants topology for the read-only pinned-client query, relaxing the separate isolated AppHost requirement. The frozen constraint and live task now reflect that approval; runtime revisions and credential-free evidence remain required.

## Review Triage Log

All three layers completed. The verification-gap layer ran as a user-authorized fresh Codex task after the agent-tree thread limit prevented its launch; it reported no verification gaps. Each finding from the other layers is recorded separately below before grouping.

| ID | Verdict | Evidence and route |
| --- | --- | --- |
| BH-1 | false | `InvokeAsync` awaits query submission and its response; the listener increments the count before responding. The executor and client have no submission after invocation completion, so the asserted count includes every completed call. No hidden additional request was demonstrated. Rejected. |
| BH-2 | low | The ephemeral probe releases its port before `HttpListener` binds, so another process could claim it. This is an uncommon environment race shared with existing loopback tests; a retry/binding replacement adds complexity beyond a direct correction. Rejected. |
| BH-3 | low | The directory is created before the protected scope, and deletion follows an await that can throw. Setup or response-task failure can therefore bypass deletion. Patch: protect the directory's entire lifetime and delete it unconditionally. |
| BH-4 | low | The three aggregate/tenant refusals are asserted in Core with exact violations and zero calls. CLI-specific exit-code expansion belongs to the intent's explicitly deferred general parser/output work; collective matrix acceptance has no missing refusal case. Rejected. |
| BH-5 | low | Every new CLI case supplies a session tenant flag, masking profile fallback at the query invocation seam. Patch: add one successful no-flag case that asserts the stored profile tenant in request and result. |
| BH-6 | low | The loopback cases configure no bearer and do not assert the authorization header, leaving query-host token forwarding unchecked by those cases. Patch: configure a synthetic profile token and assert its exact header. |
| BH-7 | medium | A connection-refused authentication probe exited with an unhandled `HttpRequestException` and no sanitized stdout. Authentication and token parsing are outside the catch, so the runbook loses a reproducible blocker. Patch: return stage-specific, credential-free transport/timeout/identity-response failures. |
| BH-8 | low | The spec is `in-review` while the sprint entry remains `in-progress`. Patch: set the sprint entry to `review` during review, then sync completion through the workflow. |
| EC-1 | low | A listener setup exception occurs after directory creation but before the cleanup try. The directory survives. Same directory-lifetime patch as BH-3. |
| EC-2 | low | An unexpected response-task exception escapes before directory deletion and can mask an existing assertion failure. Patch: guarantee deletion and preserve an existing test failure while draining the task. Same cleanup group as BH-3. |

Surviving groups are patches only: CLI cleanup (BH-3/EC-1/EC-2), profile fallback (BH-5), bearer forwarding assertion (BH-6), sanitized spike errors (BH-7), and sprint review tracking (BH-8). No intent/spec loopback or deferred product issue was identified.

All surviving patches are complete. The CLI tests protect directory cleanup for setup and response-task failures, retain the original test failure, cover the profile tenant without a flag, and check the configured bearer header. The spike returns stage-specific sanitized failures for input, authentication transport/timeout, invalid JSON, and missing tokens; 11 synthetic probes passed without credentials in output. The parent inspected the patches and reran the specified focused and full verification. The completed fresh verification-gap task reported no gaps; no findings were deferred.

## Design Notes

Tests, fixture, docs and temporary runtime work are the expected footprint. The user approved reuse of the running local topology after isolation was unavailable; inspect and wait for existing resources, preserve them, and keep generated credentials in memory.

## Verification

- `dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Debug --no-restore -m:1`
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1`
- Run built Core/CLI xUnit assemblies directly, focused on the new classes then unfiltered; zero failures and no skipped query acceptance cases. Record existing platform-only skips. Restore first if necessary.
- Capture live page evidence; `git diff --check` must pass.

### Implementation validation (2026-10-01)

- Both specified Debug test-project builds passed with 0 warnings/errors (CLI restore performed once after adding its fixture reference).
- Final focused built-assembly runs after review fixes: `QueryExecutionTests` 27 passed, `QueryCommandTests` 19 passed; 0 failed/skipped.
- Final full built-assembly runs after review fixes: Core 271 total / 269 passed / 0 failed / 2 existing Windows-only ACL skips on Linux; CLI 231 passed / 0 failed/skipped. Windows ACL execution remains an environment-specific limitation.
- The temporary spike builds with 0 warnings/errors, and validate-only exits 0 with client assembly `3.110.0.0`, `candidateMatches=true`, `submitted=false`.
- `git diff --check` passed. The authorized live harness exited 0 with one redacted tenant item, `cursor: null`, and `hasMore: false`; `index` matched the pinned pattern and was accepted by the live Gateway/Tenants handler.

### Matrix audit (2026-10-01)

The parent agent read the complete tracked/untracked diff and audited the initial 27 Core and 18 CLI cases with verbose reporting. After review fixes, the parent inspected the updated CLI test and harness and reran both classes: all 27 Core cases and all 19 CLI cases ran and passed with no failures, skips, or unrun cases.

| Matrix row | Covering test / evidence | Result |
| --- | --- | --- |
| Payload sources | `PayloadSourcesUseOneDescriptorRoutedPostAsync`, all inline/file/stdin cases | Passed |
| Aggregate | `AggregateSourcesUseDescriptorRoutingOnceAsync`, all five source/precedence cases | Passed |
| Aggregate refusal | `AggregateRefusalsMakeZeroGatewayCallsAsync`, both conflict/missing cases | Passed |
| Tenant | `FixedTenantWinsAsync`, `SessionAndPerCallTenantsRespectOverrideAsync`, and `TenantRefusalsMakeZeroGatewayCallsAsync` | Passed |
| Results | `ResultsHaveExactlyRequiredFieldsAsync` and the CLI object/null cases | Passed |
| Live proof | Pinned-client harness builds, validates `index`, and receives a page from the user-authorized running topology | Passed |

All story acceptance criteria are satisfied. Existing Windows-only ACL tests could not execute on Linux; the new query cases ran without skips.

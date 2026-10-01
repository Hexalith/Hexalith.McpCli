---
title: 'Run a Valid Query Through the Gateway'
type: 'feature'
created: '2026-10-01'
status: 'ready-for-dev'
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

Use EventStore.Client 3.110.0 directly with the existing EventStore AppHost and root-declared checkouts. Record credential-free evidence. `index` remains a candidate for Tenants maintainer confirmation in 4.8. Completion requires a live page.

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
- [ ] `tests/fixtures/Catalog.String.Contracts/ListItemsQuery.cs` — add a described constant query for successful String aggregate resolution.
- [ ] `tests/Hexalith.McpCli.Core.Tests/QueryExecutionTests.cs` — cover aggregate/tenant matrix; assert exact requests/results and zero calls on refusal.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj` — reference the existing String Contracts fixture.
- [ ] `tests/Hexalith.McpCli.Cli.Tests/QueryCommandTests.cs` — exercise payload-source matrix through CLI parsing and bounded loopback; assert method/path, full request, one call, exact object/null results, exit 0. Restore streams/listeners on failure.
- [ ] `/tmp/mcpcli-story-25-spike/` — create direct-client harness; start/inspect the existing AppHost through Aspire with verified isolation; use generated local administrator credentials only in memory. Submit list query; clean up this run's resources.
- [ ] `_bmad-output/implementation-artifacts/query-spike-2-5.md` — record reproducible commands, full source revisions, pin, endpoint, identity requirements, routing, pinned pattern source, sanitized page and maintainer handoff; document exact blockers.
- [ ] `README.md` — document query inputs, aggregate resolution and result fields.

**Acceptance Criteria:**
- Given the matrix fixtures, when focused Core and CLI tests run, then all scenarios pass and every refusal makes zero Gateway calls.
- Given local EventStore and Tenants, when the pinned-client spike submits the documented request, then it receives a page and verifies `index` against both the pinned pattern and live response.
- Given the completed change, when existing Core and CLI suites run individually, then they pass without changed discovery, settings or head parity behavior.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

No intent gaps or irreversible changes identified. Tests, fixture, docs and temporary runtime work are the expected footprint. Existing user services occupy shared ports/Dapr identities; verify isolation before startup.

## Verification

- `dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Debug --no-restore -m:1`
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1`
- Run built Core/CLI xUnit assemblies directly, focused on the new classes then unfiltered; zero failures/skips. Restore first if necessary.
- Capture live page evidence; `git diff --check` must pass.

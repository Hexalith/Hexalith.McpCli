---
title: 'Expose Works, Timesheets, Agents, Conversations, Projects, and Folders through McpCli'
type: 'feature'
created: '2026-09-27'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'd81d8fb9ea7c49f30ddf69554b2b155bb2bf05b1'
context:
  - '_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** None of the six requested modules is discoverable or executable through McpCli. Their current Contracts releases lack McpCli declarations, and several public Contracts do not match callable EventStore gateway operations.

**Approach:** Complete the generic CLI and MCP execution path, make each owning module's callable gateway contracts declarative and packageable, then enroll exact released Contracts versions through flagged package references. McpCli sends Commands and Queries to the EventStore server, which routes them to Module servers. Prove catalog discovery and command/query behavior against that path for every exposed operation.

## Boundaries & Constraints

**Always:** Keep module-specific declarations and adapters in their owning repositories. The only dependency from McpCli to a Module is that Module's Contracts package; McpCli never calls a Module server directly. Keep enrollment to direct, versionless, flagged `*.Contracts` package references with exact central versions. Preserve existing Module consumers through additive gateway contracts/adapters and keep tenant and actor authority in the envelope. Enforce the AD-15 dependency closure and verify the restored packages and live gateway behavior before exposing an operation.

**Never:** Add module-specific code or source/project references in the McpCli production projects; point the catalog at folders; decorate operations without a working gateway route; take tenant authority from caller payload; publish or replace packages before the implementation and verification gates pass.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Discovery | Six released, decorated Contracts packages enrolled | Each module and its supported operations appears in both heads with matching descriptions and schemas | Missing/invalid declarations produce catalog diagnostics and fail coverage gates |
| Command or query | Valid payload, authorized envelope, live gateway | Same operation result through CLI and MCP; gateway receives declared wire type, routing, and safe payload | Invalid routing, unauthorized tenant, and unsupported operations fail without submission |
| Read-only session | Any exposed command | Discovery reports it unavailable and execution refuses it | No gateway write call |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli/Program.cs` — executable is currently a stub; CLI and MCP execution stories remain backlog.
- `src/Hexalith.McpCli/Hexalith.McpCli.csproj` and `Build/ModuleAssemblyManifest.targets` — flagged production package enrollment and generated assembly list.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs`, `Catalog/AggregateIdAccessors.cs`, and `Schema/SchemaDeriver.cs` — current declaration, aggregate ID, and envelope property constraints.
- `../works/src/Hexalith.Works.Contracts/` — 15 value-object-ID commands, no query DTOs or annotations; gateway handles two queries.
- `../timesheets/src/Hexalith.Timesheets.Contracts/` and `../timesheets/src/Hexalith.Timesheets.Server/` — 28 commands and 8 queries, but no registered EventStore aggregate/query handlers.
- `../agents/src/Hexalith.Agents.Contracts/` — envelope-only aggregate IDs and some deferred query DTOs; interaction writes require trusted orchestration.
- `../conversations/src/Hexalith.Conversations.Contracts/` and `../conversations/src/Hexalith.Conversations/` — public command DTOs differ from aggregate wrapper commands; only two gateway query adapters exist.
- `../projects/src/Hexalith.Projects.Contracts/` and `../projects/src/Hexalith.Projects.Server/` — Contracts pull UI/framework dependencies and differ from strict gateway wire payloads.
- `../folders/src/Hexalith.Folders.Contracts/` and `../folders/src/Hexalith.Folders.Server/` — current Contracts package has no command or query DTOs; server has gateway commands alongside REST-only behavior. Epic 4 Story 4.2 requires a maintainer-approved inventory of 49 legacy MCP tools and the CLI.
- `references/Hexalith.Builds/Props/Directory.Packages.props` — shared version catalog, currently missing three requested Contracts versions and McpCli Abstractions.

## Tasks & Acceptance

**Execution:**
- [ ] `src/Hexalith.McpCli/` and `src/Hexalith.McpCli.Core/` — complete the generic CLI, MCP, settings, and gateway executor stories before claiming user-facing module coverage.
- [ ] `../works/src/Hexalith.Works.Contracts/` and McpCli Core — support envelope-owned value-object IDs, add two gateway query descriptors, declare only callable operations, and remove disallowed Contracts dependencies.
- [ ] `../timesheets/src/Hexalith.Timesheets.Server/` and Contracts — implement and verify gateway handlers, then declare only callable operations.
- [ ] `../agents/src/Hexalith.Agents.Contracts/` and runtime — supply safe aggregate ID sources, retain trusted interaction orchestration, and declare only live handlers.
- [ ] `../conversations/src/Hexalith.Conversations.Contracts/` and runtime — align public gateway payloads and command adapters, and remove the disallowed serialization dependency.
- [ ] `../projects/src/Hexalith.Projects.Contracts/` and Server — slim Contracts to the allowed closure, publish gateway payload contracts, and align strict deserialization; expose only supported queries.
- [ ] `../folders/src/Hexalith.Folders.Contracts/` and Server — map each legacy tool/CLI operation to a callable gateway command or query or approved exclusion, add matching Contracts DTOs and handlers, and preserve REST-only authorization and behavior where required.
- [ ] `../builds/Props/Directory.Packages.props` and each owning module — version and release McpCli Abstractions and each decorated Contracts package with exact versions.
- [ ] `src/Hexalith.McpCli/Hexalith.McpCli.csproj` and `Directory.Packages.props` — enroll all six released packages with manifest flags and exact pins.
- [ ] `tests/` and each module's tests — cover manifest, dependency closure, catalog, CLI/MCP parity, and live gateway semantics for exposed operations.

**Acceptance Criteria:**
- Given the built tool and six released Contracts packages, when an operator lists modules and operations from CLI or MCP, then all six modules and their declared callable operations appear with equivalent documents.
- Given an authorized envelope, when each declared operation executes through either head, then the gateway accepts its wire type and routing and both heads return the same structured result.
- Given any module's decorated release, when the dependency gate inspects restored assets, then its closure adds only identities allowed by AD-15.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

No existing module release is ready for direct enrollment. NuGet currently has no `Hexalith.McpCli.Abstractions`, Works.Contracts, or Timesheets.Contracts package. Agents, Conversations, Projects, and Folders have 1.0.0 packages without McpCli declarations. Folders.Contracts 1.0.0 is dependency-free but contains no command or query types. The current McpCli executable returns an unimplemented error, so enrollment alone cannot satisfy the user-facing goal.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx` — all exact package versions resolve.
- `dotnet build Hexalith.McpCli.slnx --configuration Release` — manifest generation and dependency gate pass.
- Run each affected test project individually, followed by the generic loopback and live gateway lanes — all declared operations pass without bypassing authorization or routing.

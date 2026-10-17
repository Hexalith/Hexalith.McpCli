---
title: '4.5 Gate module coverage against the approved inventory'
type: 'feature'
created: '2026-10-17'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Existing checks can miss omitted migration operations or correct
names mapped to wrong CLR contracts.

**Approach:** Add a generic test-only coverage gate, prove it against the built
sample Catalog, and document reuse with future decorated modules.

## Boundaries & Constraints

**Always:** Keep inventory data and the checker outside production source and
configuration. Use versioned JSON with legacy rows referencing unique normalized
targets; shared references are valid. Record stable IDs, canonical names, exact
CLR types, dispositions, coverage, rationale and approval status/authority/reference.
Include requires approved `replace`; exclude requires approved `withdraw` or
`defer`. Scope-only approval cannot establish owning-maintainer release readiness.
Synthetic approvals certify fixtures only.

Compare the unfiltered public `ICatalog.ListOperations(module)` document and,
independently, `OperationDescriptor.ContractType.FullName`, using ordinal matching.
Report deterministic findings with file, row/target or unexpected operation, and
specific mismatch. Reject Catalog errors that could hide duplicate declarations.
Keep CLR types absent from public module, list and describe documents.

**Never:** Load inventories at runtime, add module-specific production branches,
change enrollment, dependencies, upstream files or gitlinks, publish packages,
or infer behavior parity, authorization or retirement permission. Preserve
existing Markdown inventories and session decisions; intended Parties targets
remain undelivered. Never invent approvals or substitute vector coverage.

## I/O & Edge-Case Matrix

| Scenario | Input / state | Expected behavior | Failure evidence |
| --- | --- | --- | --- |
| Matching scope | Approved includes match sample names/types; approved exclusions absent | Pass, including shared legacy-to-target mappings | Empty findings |
| Mismatch | Missing/extra operation; wrong CLR type | Fail | Target, expected/actual |
| Duplicate | Repeated row ID, target ID/name/type, per-row reference or public entry | Fail | Conflicting identities |
| Invalid scope | Missing approval/rationale, scope-only authority, invalid disposition/coverage, dangling/orphan target | Fail | Field and row/target |
| Invalid document | Unsupported format, malformed/missing/unknown fields, duplicate JSON keys | Fail closed | File and location |
| Hidden declaration | Catalog error despite matching surviving list | Fail | Catalog diagnostic |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Catalog/CatalogService.cs` projects public discovery;
  `CatalogProvider.Get(false)` supplies its snapshot. Change neither.
- `tests/Hexalith.McpCli.Core.Tests/CatalogServiceTests.cs` demonstrates provider,
  service and `McpCliJson.Result` setup. Existing CI runs Core.Tests.
- `tests/Hexalith.McpCli.Sample.Contracts/` supplies `sample.create-item`,
  `sample.get-item`, `sample.rename-item`; reuse without changing contracts.
- `parties-migration-inventory-v1.md` under implementation artifacts maps five
  legacy rows to seven intended targets, with shared T01/T07; readiness is pending.

## Tasks & Acceptance

**Execution:**

- [ ] `tools/inventory-coverage/v1/sample-approved.json` — cover all three sample
  operations, shared targets and approved withdrawal/deferral exclusions.
- [ ] `tools/inventory-coverage/v1/README.md` — specify JSON v1 fields, approval
  semantics, diagnostics, command and future handoff. Explain that source-surface
  completeness and approval authenticity require independent owner evidence.
- [ ] `tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs` — implement
  loading/comparison; supporting types get separate matching files. Reuse dependencies.
- [ ] `tests/Hexalith.McpCli.Core.Tests/InventoryCoverageTests.cs` — exercise
  every matrix case with exact diagnostics, mutated public documents and real
  descriptors; assert no public contract-type fields or mapped full CLR names.
- [ ] `tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj` — copy
  the artifact to output for CWD-independent tests.
- [ ] This spec and `sprint-status.yaml` — record verification and workflow status.

**Acceptance Criteria:**

- Given the inventory and built sample, when checked, then each included name
  appears once publicly with the expected internal type and no extra operation.
- Given each matrix mutation, when checked, then rejection identifies its
  location and reason; removing the guard fails its test.
- Given the checker and inventory, when production and CI wiring are inspected,
  then only tests consume the artifact and existing CI enforces the gate without
  a future Parties package or Gateway.
- Given a later owner-approved inventory and decorated Contracts assembly,
  when supplied to the checker, then no module-specific checker change is needed.

## Implementation Notes

- 2026-10-17: The requesting user answered "approve and stop" at Checkpoint 1.
  Approved intent is frozen; this spec and sprint tracking are `ready-for-dev`.
  Implementation has not started. Resume with `bmad-build 4.5` in a fresh session.

## Spec Change Log

## Review Triage Log

## Verification

- `dotnet restore Hexalith.McpCli.slnx`
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`
- `dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release`
- Run the remaining existing test projects individually with the same test
  options before completion; run a fresh restore before Manifest.Tests.
- `git diff --check`

Require exit 0; record blockers and focused fallbacks. Run conformance gates if
implementation changes Core, sample contracts or Gateway wire behavior.

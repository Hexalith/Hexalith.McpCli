---
title: '4.5 Gate module coverage against the approved inventory'
type: 'feature'
created: '2026-10-17'
status: 'done'
route: 'dispatch'
baseline_commit: '9681ef84c9d06adfac4f0bb1ea3e398953f6666e'
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

- [x] `tools/inventory-coverage/v1/sample-approved.json` — cover all three sample
  operations, shared targets and approved withdrawal/deferral exclusions.
- [x] `tools/inventory-coverage/v1/README.md` — specify JSON v1 fields, approval
  semantics, diagnostics, command and future handoff. Explain that source-surface
  completeness and approval authenticity require independent owner evidence.
- [x] `tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs` — implement
  loading/comparison; supporting types get separate matching files. Reuse dependencies.
- [x] `tests/Hexalith.McpCli.Core.Tests/InventoryCoverageTests.cs` — exercise
  every matrix case with exact diagnostics, mutated public documents and real
  descriptors; assert no public contract-type fields or mapped full CLR names.
- [x] `tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj` — copy
  the artifact to output for CWD-independent tests.
- [x] This spec and `sprint-status.yaml` — record verification and workflow status.

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

- 2026-10-17: Implemented the generic test-only v1 gate and strict JSON loader,
  normalized sample fixture (three included operations, shared read target, approved
  synthetic withdrawal and deferral), CWD-independent artifact copy, and reuse
  documentation. Decisions remain on legacy rows; target identity/name/type are
  unique, and shared references must agree on coverage. Release inventories reject
  synthetic authority and every inventory rejects scope-only authority.
- The gate compares unfiltered public names separately from real internal
  descriptors, rejects declaration errors even with matching survivors, and emits
  ordinally sorted file/location-specific diagnostics. Tests cover every matrix
  scenario, required field/type mutations, and public metadata privacy. A second
  arbitrary module marker proves checker reuse without module-specific logic.
- Production source/configuration, dependencies, CI workflow, module enrollment,
  upstream checkouts/gitlinks and existing Markdown inventories are unchanged.
  Intended Parties targets remain undelivered. The fixture certifies synthetic
  test scope only; source completeness and authentic owner evidence remain
  independently required and no retirement/authorization/parity claim is made.

## Spec Change Log

## Review Triage Log

All three review layers completed. Edge-case and verification-gap reviewers
reported no findings. The blind review supplied nine findings; each was judged
before grouping. B05, B07, B08 and B09 are independent small patches; no loopback
or deferral is required.

| ID | Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- | --- |
| B01 | All-excluded scope differs when unrelated modules exist | false | reject | The probe confirms `CatalogProvider.Get(false)` returns `catalog_empty` when the entire Catalog has no operations. The approved gate compares a usable public Catalog and rejects Catalog errors; this is an explicit provider policy, not a hidden missing target. With an unrelated populated module, the empty selected module has usable public discovery and correctly matches exclusions. |
| B02 | Duplicate legacy labels with distinct IDs should fail | false | reject | Stable row IDs, target IDs/names/types and per-row references are the specified identities. `legacyOperation` is a source description that may identify inventoried variants; the gate rejects contradictory coverage on shared targets. A cloned description does not demonstrate an omitted source or contradictory target, and source completeness explicitly requires independent evidence. |
| B03 | Future checker reuse omits generic privacy validation | false | reject | The checker compares names and types; the separate public privacy test serializes the shared production module/list/description DTOs and all sample descriptions. No added runtime metadata path leaks types or makes production projections module-dependent. Extracting a new generic privacy API is not needed to preserve those shared documents. |
| B04 | Public errors suppress internal mismatch diagnostics | low | reject | `Compare` intentionally returns a specific failing public result before target comparison when no usable public document exists. This limits secondary diagnostics but cannot pass mismatching coverage. Reporting additional independent failures in this uncommon error state adds comparison branches beyond a direct correction. |
| B05 | Duplicate IDs identify both occurrences with the same label | low | patch | `Unique` stores only `row L01` or `target T01`; duplicate diagnostics therefore cannot distinguish source occurrences. Add JSON array positions to the first/current identity locations and update exact expectations. |
| B06 | Embedded control characters in IDs can yield multiline findings | low | reject | The probe accepts an escaped newline in a stable ID, and interpolation could make a later failure multiline. This unusual hand-authored fixture input does not bypass comparison; a new identity alphabet or escaping policy would add guards beyond a direct correction. |
| B07 | Invalid UTF-8 silently becomes replacement text | medium | patch | The parent reran the review probe: a rationale containing raw byte `0xFF` passes `CheckFile` because `File.ReadAllText` replaces invalid UTF-8. Strict decoding and an exact diagnostic must reject this demonstrated malformed-file state. |
| B08 | Privacy assertions confuse payload property names with metadata | low | patch | `CheckPublicFields` recursively rejects schema property keys and example keys containing `contractType`/`clrType`, including legitimate payload names. Skip payload schema/example bodies when asserting metadata field names, retain the full CLR-name assertion, and test valid payload fields plus metadata leakage. |
| B09 | Canonical regex ending anchors lack regression protection | low | patch | Existing uppercase/wrong-module cases do not require end anchoring; the newline is rejected by `Text` earlier. Add ordinary valid-prefix-plus-invalid-suffix cases for module and target names. |

## Verification

- `dotnet restore Hexalith.McpCli.slnx`
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`
- `dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release`
- Run the remaining existing test projects individually with the same test
  options before completion; run a fresh restore before Manifest.Tests.
- `git diff --check`

Require exit 0; record blockers and focused fallbacks. Run conformance gates if
implementation changes Core, sample contracts or Gateway wire behavior.

### Implementation verification (2026-10-17)

All commands below exited 0. No environment blocker or fallback pin was needed.

| Command | Result |
| --- | --- |
| `dotnet restore Hexalith.McpCli.slnx` | Passed initially and freshly immediately before Manifest.Tests. |
| `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` | Passed; 0 warnings, 0 errors. |
| `dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --no-restore --configuration Release -warnaserror` | Passed; final focused build includes the warnings-only positive case. |
| `dotnet /home/administrator/projects/hexalith/mcpcli/tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -class '*InventoryCoverageTests' -noLogo` (CWD `/tmp`) | 77 passed; confirms artifact loading outside the repository CWD. |
| `dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release` | 635 passed, 2 Windows-only ACL tests skipped on Linux. |
| `dotnet test tests/Hexalith.McpCli.Abstractions.Tests --no-build --configuration Release` | 20 passed. |
| `dotnet test tests/Hexalith.McpCli.Analyzers.Tests --no-build --configuration Release` | 19 passed. |
| `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` | 58 passed. |
| `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` | 479 passed, 2 Windows-only ACL/file-attribute tests skipped on Linux. |
| `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` | 8 passed after fresh restore. |
| `git diff --check` | Passed. |

Inspection of `src/`, `.github/`, the Core.Tests project and the new tooling
confirms the inventory is consumed only by tests; the unchanged existing CI
Core.Tests lane enforces it. The new exact-diagnostic tests include hidden real
duplicate declarations, independent public/internal mutations, shared and
conflicting references, all scope decisions, strict document fields/keys and
public module/list/describe metadata privacy. Catalog warnings alone are accepted.
Conformance gates were not required: production Core, sample Contracts and Gateway
wire behavior did not change.

### Implementation audit

The parent agent read the complete unified diff (including new files), inspected
CI consumption and public discovery, and reran all 77 inventory cases from `/tmp`
with verbose output: exit 0; 77 passed, zero skipped or not run. Every matrix row
has executed coverage:

| Matrix row | Passing tests |
| --- | --- |
| Matching scope | `ApprovedSampleMatchesUnfilteredBuiltCatalog`, `ReusesCheckerForAnotherOwnerApprovedModule` |
| Mismatch | `RejectsPublicDiscoveryMismatch`, `RejectsWrongClrTypeDespiteMatchingPublicNames`, `ChecksInternalNamesIndependently`, `RejectsPresentExclusion` |
| Duplicate | `RejectsInvalidScope` identity/reference cases and `RejectsPublicDiscoveryMismatch` duplicate case |
| Invalid scope | `RejectsInvalidScope`, `RejectsMissingOrMalformedStringFields`, `RejectsSyntheticReleaseApproval` |
| Invalid document | `RejectsMalformedDocumentShapes`, `RejectsMissingContainersAndVersion`, `RejectsNonObjectEntries`, `RejectsUnknownAndDuplicateKeys`, `RejectsUnreadableAndInvalidJson` |
| Hidden declaration | `RejectsCatalogErrorsDespiteMatchingSurvivors`, `RejectsEmptyCatalog` |

`PublicDocumentsDoNotExposeContractTypes` also passed for modules, list and every
sample description. All execution tasks and acceptance criteria are satisfied;
review is the next workflow stage.

### Final review and verification (2026-10-17)

Completed all three review layers and resolved B05, B07, B08 and B09 with small
patches. Duplicate IDs now show distinct source indexes; file loading uses strict
UTF-8 with optional BOM; privacy assertions distinguish payload bodies from public
metadata while still rejecting mapped CLR names everywhere; ordinary invalid
suffixes protect both regex ending anchors. Focused regressions passed: 89 tests,
zero skipped or not run, invoked from `/tmp`. Nothing was deferred.

After inspecting the patched diff, the parent agent reran every required command
on the final code. Every command exited 0:

| Command | Final result |
| --- | --- |
| `dotnet restore Hexalith.McpCli.slnx` | Passed; repeated immediately before Manifest.Tests. |
| `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` | 0 warnings, 0 errors. |
| `dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release` | 647 passed, 2 Windows-only skips. |
| `dotnet test tests/Hexalith.McpCli.Abstractions.Tests --no-build --configuration Release` | 20 passed. |
| `dotnet test tests/Hexalith.McpCli.Analyzers.Tests --no-build --configuration Release` | 19 passed. |
| `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` | 58 passed. |
| `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` | 479 passed, 2 Windows-only skips. |
| `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` | 8 passed after fresh restore. |
| `git diff --check` | Passed. |

Total: 1,231 passed, four Windows-only skips on Linux. Full output is preserved
under `/tmp/mcpcli-story-4-5-final-verification/`; focused review-fix logs are under
`/tmp/mcpcli-story-4-5-review-fixes/`. All matrix rows remain covered and passing.
The spec is done; sprint tracking is review, following the build workflow.

Commit tooling: `npm ci` succeeded. The exact local commit candidate
`test(inventory): gate module coverage against approved inventory` passed
`npx --no -- commitlint --verbose` with exit 0, zero problems and zero warnings.
The full successful validator output is preserved in
`/tmp/mcpcli-story-4-5-final-verification/commitlint.log`.

### Review Findings

Code review 2026-10-17 (range `9681ef8..20c8893`, full mode; Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor).

- [x] [Review][Decision] (resolved: keep global, documented in README, tested) Catalog error diagnostics are not scoped to the module under check — medium. `Compare` fails on every `error` diagnostic in `access.Catalog.Diagnostics`; `CatalogDiagnostic` carries only `TypeName`, `Category`, `Severity`, `Message` (no module), so one enrolled module's declaration error fails every other module's inventory. Options: (1) keep global failure and document it in the README with a test; (2) scope by mapping `TypeName` to the module's descriptors, accepting that unmappable diagnostics stay global. [tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs:242]
- [x] [Review][Patch] Lone-surrogate JSON escape crashes the gate — medium. Verified by probe: `JsonDocument.Parse("{\"a\":\"\\ud800\"}")` parses, then `GetString()` and `Property.Name` throw `InvalidOperationException`, which `Check`/`Text`/`Object` do not catch, so the gate throws instead of emitting a diagnostic. Read once and catch in `Text` and the property-name path; add an exact-diagnostic test. [tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs:356]
- [x] [Review][Patch] Excluded-target name-match clause is not pinned — medium. Dropping `item.Name == target.Name` at the internal-presence check leaves every test green, since `RejectsPresentExclusion` cases match by CLR type. Add a case where the excluded name matches an internal descriptor with a different `contractType` and assert the exact diagnostics. [tests/Hexalith.McpCli.Core.Tests/InventoryCoverageGate.cs:302]
- [x] [Review][Patch] README claims "JSON comments and trailing commas are not accepted" without a test — low. No test references either; changing the parse options would pass. Add a test for each. [tests/Hexalith.McpCli.Core.Tests/InventoryCoverageTests.cs]

#### Rejected

- Duplicate internal descriptor branch (`matchingInternal.Length != 1`) untested (Acceptance Auditor) — low; the Catalog-error test covers the end-to-end behavior.
- Duplicate public entry count `== 0` vs `!= 1` (Edge Case Hunter) — false; the separate duplicate-public finding already fires, tested per Acceptance Auditor.
- Invalid module name returns before target/row checks; structural errors hide comparison; Duplicate-ID locations lacking index (Edge Case, Blind) — low or already handled by B04/B05; the fixes add branches.
- Control characters in identifiers (Blind, B06) — low; already rejected in the Review Triage Log.
- Privacy check not in reusable gate (Blind, B03) — already rejected in the Review Triage Log.
- Excluded `contractType` format never validated (Blind) — low; fix adds a rule with no demonstrated harm.
- Duplicate legacy rows accepted (Blind, B02) — already rejected in the Review Triage Log.
- Diagnostic noise for present exclusions (Blind) — low; fix adds suppression branches.
- `CheckFile` empty/invalid path exceptions (Edge Case) — low; test-only API called with fixed paths.
- `.csproj` needs a hand-added entry per new inventory (Blind) — low; fail-loud via missing-file finding.
- Stale `ready-for-dev` note, spec `done` vs sprint `review`, `/tmp` evidence paths (Blind, Acceptance Auditor) — fix edits the spec under review.
- Scope-only authority stricter than spec wording (Acceptance Auditor) — matches the Implementation Notes.

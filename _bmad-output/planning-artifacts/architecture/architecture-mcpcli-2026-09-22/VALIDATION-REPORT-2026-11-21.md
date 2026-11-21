# McpCli architecture validation

21 November 2026 · Standalone BMAD review

**Verdict: revise the spine before relying on its query paging contract or accepting Platform-connected integration.** A loopback check confirmed a public result that both heads emit and the advertised MCP schema rejects. Three additional high-priority findings concern Platform integration. Seven medium findings and one low finding complete the review.

The review covers the working-tree [architecture spine](ARCHITECTURE-SPINE.md) at McpCli `e79b7f8b`. All 23 decision IDs and 30 requirement bindings were present. Reviewed spine SHA-256: `1b9d55aa46f338978208824857317eb376ff2939d7112ce15f35b7eac5646e68`.

## High priority

### 01. A successful Query can fail its advertised output schema

AD-5, AD-12, AD-20 · spine lines 109, 159, 228, 276

A loopback Gateway returned a successful Projects query with a present, empty paging object. The Release CLI exited 0 and stdio MCP reported success. Both returned `paging.pageSize: 0`. The same MCP session’s advertised `run_query` output schema rejected that result and accepted the identical result with a page size of 1. The packaged fixture and the schema test encode the two different expectations.

**Recommended action.** Core and both adapter owners should apply one response rule. Omit paging when absent or null. Treat a present paging object that breaks the public contract as a malformed Gateway response, using an agreed error mapping. Preserve valid zero offsets and counts and `hasMore: false`. Check the actual returned document against the session’s schema in the same test. [Normative result fields](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md#L424) · [Gateway response mapping](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs#L279) · [Packaged fixture](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/tools/conformance-vectors/v1/run_packaged_process_fixture.py#L59) · [Advertised-schema test](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/tests/Hexalith.McpCli.Mcp.Tests/McpOutputSchemaTests.cs#L305)

### 02. Platform source builds need a Contracts manifest input

AD-4, AD-17 · spine lines 103, 206

The local build enumerates flagged NuGet package references and matches their package IDs to copy-local assemblies. Platform also requires its run-scoped McpCli to consume source-mapped Contracts by assembly identity. AD-17 names the common mapping, but AD-4 gives the implementer only the package path.

**Recommended action.** McpCli and Platform should define how their build passes the mapped identities to the manifest generator, rejects duplicate or missing assemblies, and proves the host, tool and tests loaded the same candidate. Keep the released tool’s package enrollment rule explicit. [Manifest inputs](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets#L28) · [MSBuild invocation](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli/Build/ModuleAssemblyManifest.targets#L88) · [Platform override](https://github.com/Hexalith/Hexalith.Platform/blob/25887836c2c7a63edbff7a4e0426e078a188b98c/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md#L383)

### 03. Connected CLI and stdio need the staging identity rules

AD-10, AD-13, AD-14 · spine lines 146–147, 168, 174, 406–407

The local stdio tool uses an operator-configured actor and credential. The spine places the explicit actor-override refusal under future HTTP. Platform already requires that refusal for its connected CLI and stdio. Its staging contract also calls for short-lived environment-bound OIDC credentials, OS credential storage for refresh material, and renewal evidence.

**Recommended action.** McpCli and Platform should name the local and connected modes explicitly. For connected staging, specify the trusted actor source, refused overrides, credential storage and renewal checks, including the prohibition on `offline_access`. Qualify those rules for both existing heads before accepting connected execution. [Connected actor criteria](https://github.com/Hexalith/Hexalith.Platform/blob/25887836c2c7a63edbff7a4e0426e078a188b98c/_bmad-output/planning-artifacts/epics.md#L1960) · [Staging credentials](https://github.com/Hexalith/Hexalith.Platform/blob/25887836c2c7a63edbff7a4e0426e078a188b98c/_bmad-output/planning-artifacts/epics.md#L2811) · [Renewal evidence](https://github.com/Hexalith/Hexalith.Platform/blob/25887836c2c7a63edbff7a4e0426e078a188b98c/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md#L526)

### 04. Connected discovery needs a shared way to report executability

AD-3, AD-13 · spine lines 95–97, 168, 406

The spine correctly limits the current `submittable` field to local read-only mode and Gateway configuration. Platform requires discovery to show when an operation is non-executable because the selected Gateway does not serve it, its digest differs, or it is disabled. Two heads can agree to block the call and still give incompatible discovery results.

**Recommended action.** McpCli, EventStore and Platform should agree on one Core-owned connected discovery contract, how it differs from offline inspection, and how stale or missing metadata is handled. Check the same positive and refusal cases through CLI and stdio against a single environment. [Current public meaning](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/addendum.md#L431) · [Platform discovery criteria](https://github.com/Hexalith/Hexalith.Platform/blob/25887836c2c7a63edbff7a4e0426e078a188b98c/_bmad-output/planning-artifacts/epics.md#L1928) · [Platform adoption requirements](https://github.com/Hexalith/Hexalith.Platform/blob/25887836c2c7a63edbff7a4e0426e078a188b98c/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md#L526)

## Medium priority

### 05. Profile ownership and CLI output can conflict

AD-14 · spine lines 174, 277

The spine assigns profile writes exclusively to the profile store. The existing CLI output writer can also replace that state, outside the profile transaction. The implementation ledger records a resulting unreadable profile.

**Recommended action.** Track this as an explicit implementation gap. The CLI and settings owners should define protected profile destinations and check them before any state change or result write. Verify the prior file survives refusal. [Existing ledger entry](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/_bmad-output/implementation-artifacts/deferred-work.md#L400) · [Result writer](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli/Cli/CliOutput.cs#L192)

### 06. A Query can advertise an unusable default aggregate ID

AD-8, AD-19 · spine lines 127, 222

A synthetic Ulid-module fixture advertises an optional aggregate ID with the default `routing-list`. Catalog admission accepts its Gateway syntax. The executor also applies the module’s ULID rule, so the advertised default fails at execution. Impact on enrolled production operations was not established.

**Recommended action.** Apply the module’s identifier kind and Gateway syntax to constants at Catalog admission. Specify the diagnostic and test the descriptor and a call that omits the argument together. [Catalog check](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs#L194) · [Fixture descriptor](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs#L139) · [Executor check](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs#L229)

### 07. Schema derivation omits two supported input forms

AD-7 · spine line 121

The spine removes getter-only, non-constructor members and closes object schemas. The serializer retains getter-only collections populated in place. Typed dictionaries accept dynamic keys and constrain each value. Following the wording literally would reject input that Core accepts.

**Recommended action.** Describe effective serializer input metadata, including in-place population. Close fixed-shape object records and preserve the value schema for typed dictionaries. Align FR-7 and keep the existing fixtures as acceptance examples. [Resolver](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli.Core/Serialization/McpCliJson.cs#L131) · [Populated members](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/tests/Hexalith.McpCli.Core.Tests/SchemaTests.cs#L508) · [Dictionary values](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/tests/Hexalith.McpCli.Core.Tests/SchemaTests.cs#L372)

### 08. Aggregate validation can point to the wrong input

AD-3, AD-9, AD-19 · spine lines 95, 133, 222

AD-9 assigns aggregate syntax errors to `/aggregateId`. Core reports the escaped JSON Pointer of a mapped payload member when that member supplied the invalid value. It uses `/aggregateId` for the explicit argument or a conflict. The distinction tells the caller which field to correct.

**Recommended action.** Specify the error pointer by value source. Preserve JSON Pointer escaping and pin the same error object for both heads. [Pointer selection](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs#L224) · [Escaped-member fixture](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/tests/Hexalith.McpCli.Core.Tests/ExecutionFailureTests.cs#L93)

### 09. An all-empty Catalog has ambiguous startup behavior

AD-3, AD-4 · spine lines 95, 103, 268

Marked empty Modules are visible in a usable Catalog. The spine leaves room for a reader to treat their mere presence as sufficient for discovery. Core requires at least one valid Operation and checks strict diagnostics first.

**Recommended action.** State the two conditions in order. Strict mode with diagnostics returns `catalog_invalid`. Otherwise, zero valid Operations returns `catalog_empty`. An individual empty Module can be listed alongside a usable one. [Catalog access](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli.Core/Catalog/CatalogProvider.cs#L31) · [Strict and empty cases](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/tests/Hexalith.McpCli.Core.Tests/CatalogProviderTests.cs#L101)

### 10. Enrollment omits recorded approval of descriptions

AD-16, AD-21, NFR-8 · spine lines 192, 234–237, 391

The spine calls for lint and review of the Catalog dump. The PRD also requires a recorded owning-maintainer approval after review by someone unfamiliar with the code. Inventory and vector hashes do not record that review.

**Recommended action.** Add the approval location to the enrollment handoff. Use the module pull request or a versioned McpCli evidence record permitted by the PRD, including the accepted single-maintainer arrangement. [Enrollment checklist](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md#L503) · [Success measure](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md#L553)

### 11. Platform candidate identity is described as delivered

AD-17 · spine line 206

The spine says the Platform run records expected and loaded artifact identities. Platform defines that evidence in Story 3.9 and lists the story in backlog. This checkout establishes the requirement. A qualifying run still needs its own receipt.

**Recommended action.** Use requirement language for the run descriptor and loaded identities. Identify the evidence that will support a delivery claim, while preserving the separate publisher decision. [Required evidence](https://github.com/Hexalith/Hexalith.Platform/blob/25887836c2c7a63edbff7a4e0426e078a188b98c/_bmad-output/planning-artifacts/epics.md#L1979) · [Producer sprint status](https://github.com/Hexalith/Hexalith.Platform/blob/25887836c2c7a63edbff7a4e0426e078a188b98c/_bmad-output/implementation-artifacts/sprint-status.yaml#L147)

## Low priority

### 12. Duplicate Operation Names need a deterministic tie-break

AD-3 · spine lines 95, 266–268

The PRD and current implementation scan types within each assembly by ordinal full CLR type name and retain the first declaration of a duplicate. The spine names the diagnostic and the final sort order but omits this earlier selection rule.

**Recommended action.** Add the within-assembly scan order to the Catalog rule so a replacement implementation selects the same declaration. [FR-6 scan order](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/_bmad-output/planning-artifacts/prds/prd-mcpcli-2026-09-21/prd.md#L251) · [Type order](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs#L85) · [Duplicate handling](https://github.com/Hexalith/Hexalith.McpCli/blob/e79b7f8b64303397ce9dfd856ed2111b513ade88/src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs#L123)

## Verification and scope

| Check | Result |
| --- | --- |
| BMAD architecture lint | Zero findings |
| CLI and MCP discovery, command and query parity | 24 tests passed |
| Core schema and enrollment tests | 182 tests passed |
| MCP adapter suite | 94 tests passed |
| Production dependency closure | 1 test passed |
| Additional two-head paging check | One loopback query per head. Both emitted the same invalid success. Changing only the returned page size from 0 to 1 made the document pass the advertised schema. |

All 301 automated tests passed with zero skips. The additional paging check used the Release executable, a synthetic Projects response and the output schema fetched from that stdio session (protocol 2025-06-18). The tests verify local behavior. Native Gateway delivery, staging authorization, credential renewal and exact-archive release qualification require their own environment evidence.

The review confirmed 26 operations in offline discovery across Parties (7), Projects (4) and Tenants (15). McpCli’s committed workflows use Builds v6.4.4. The reviewed Platform checkout specifies v6.5.0. The stable publisher decision, Projects live read qualification, Folders eligibility and the previously recorded acknowledgment and tenant-normalization work remain open under their existing owners. These items are outside the twelve findings above.

The independent reviews cover [requirements and inherited decisions](reviews/review-validation-20261121-rubric.md), [technology and implementation](reviews/review-validation-20261121-technology.md) and [cross-component consistency](reviews/review-validation-20261121-adversarial.md). The report consolidates overlapping findings about schemas and aggregate error locations.

**Decision requested.** Use a BMAD architecture update to reconcile the public paging behavior and record the three Platform contracts with their owners. Product changes and qualification runs can then be tracked against those decisions.

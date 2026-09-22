---
title: "Standalone validation: good-spine rubric"
reviewed: ARCHITECTURE-SPINE.md
date: '2026-09-22'
intent: validate
reviewer: rubric-walker
status: fail
---

# Good-spine rubric validation

## Verdict

**Fail; update required before implementation stories rely on this spine.** The document is mechanically clean and strong on its central hexagonal boundary, catalog ownership, executor sequencing, dependency closure, packaging, and v1 deployment envelope. It nevertheless contradicts the final PRD on idempotency and the public result/error contract, depends on a `Hexalith.Parties.Aspire` package/project that does not exist in the current brownfield evidence, and leaves offline-discovery behavior inconsistent. Those are real divergence points for independently built executor, head, and integration-harness stories.

Finding count: **2 Critical, 2 High, 6 Medium, 1 Low**.

## Evidence and scope

- Target: `ARCHITECTURE-SPINE.md`, lines 1-333.
- Binding product input: `prds/prd-mcpcli-2026-09-21/prd.md`, updated 2026-09-22, and its normative `addendum.md` (§E arguments and §G documents).
- Other source input: `briefs/brief-mcpcli-2026-09-21/brief.md` and `addendum.md`.
- Brownfield evidence: repository `AGENTS.md`; `references/Hexalith.Builds/Props/Directory.Packages.props`; `references/Hexalith.Builds/global.json`; current EventStore, Tenants, and Parties source trees and package manifests.
- Working history: the architecture `.memlog.md`, especially the 2026-09-22 technology/reality verification at lines 34-38 and the most recent update entries at lines 74-86.
- Mechanical gate: `uv run .agents/skills/bmad-architecture/scripts/lint_spine.py --workspace _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22` returned `ok: true`, `total_findings: 0`.
- No parent architecture spine is declared or inherited. The PRD and brief are binding inputs, not a parent-spine AD namespace.
- This validation did not modify the spine or memlog.

## Critical

### RV-RUB-001 — The spine generates an idempotency key that the final PRD expressly forbids

**Criterion:** real divergence points; enforceability; source capability coverage  
**Disposition:** autofix

The spine says the executor "accepts or generates `IdempotencyKey`" and its conventions require "one message identifier and one idempotency key per call" (`ARCHITECTURE-SPINE.md:107`, `:189`). AD-5 also models `CommandResult` as though `IdempotencyKey` were an unconditional result member (`:83`).

The final product contract says the opposite:

- the guardrail makes the key optional and caller-supplied only; the tool never invents one (`prd.md:103-105`);
- FR-16 says the executor generates only the message identifier and passes through a caller-supplied idempotency key (`prd.md:338-354`);
- §E says `idempotencyKey` is caller-supplied, never generated (`addendum.md:192-196`);
- §G makes `idempotencyKey` optional in `send_command`, echoed only when supplied (`addendum.md:277-283`);
- the architecture handoff repeats this as an implementation gate (`prd.md:523-532`).

Two executor stories following these documents will implement incompatible retry and payload-fill semantics. The spine's version can also manufacture a deduplication token the caller never retained, directly weakening the PRD's no-generic-safe-retry guardrail.

**Required correction:** in AD-5, AD-9, the identifier-generation convention, tests, and any diagrams, generate only `MessageId`; resolve `CorrelationId = callerCorrelationId ?? MessageId`; keep `IdempotencyKey` absent unless the caller supplies it; require it only when discovery reports a non-nullable `idempotencyKeyProperty`; overwrite that Payload property only with a supplied key; and serialize it in the result only when supplied.

### RV-RUB-002 — AD-5 does not implement the exhaustive public document contract

**Criterion:** real divergence points; enforceability; source capability coverage  
**Disposition:** autofix

AD-5 claims one document set, but its record list is structurally different from the normative §G contract (`ARCHITECTURE-SPINE.md:79-83`):

- `ListModulesResult(Modules, Diagnostics)` adds a public `diagnostics` member; the convention reinforces public counts (`:183`). §G permits only `modules` (`addendum.md:277-280`), while catalog diagnostics are a stderr concern in FR-6 (`prd.md:206-229`).
- `DescribeOperationResult` omits the required `lintFindings` and does not bind the nested `envelope` members and requirement flags (`ARCHITECTURE-SPINE.md:83` versus `addendum.md:281`, `:285-300`, and `prd.md:254-261`).
- `CommandResult` omits required `operation`, `tenant`, `aggregateId`, and constant `status`, while treating `idempotencyKey` as unconditional (`ARCHITECTURE-SPINE.md:83` versus `addendum.md:282`, `:300-305`).
- `QueryResult` omits required `operation` and `tenant`, and declares `Document?` even though `document` is required (`ARCHITECTURE-SPINE.md:83` versus `addendum.md:283`, `:305-307`).
- `OperationError(..., Gateway?)` does not bind the exhaustive error variants, required members, omission rules, or the rule that `EventStoreGatewayException.StatusCode` is copied without reclassification, including malformed-success `2xx` cases (`ARCHITECTURE-SPINE.md:83`, `:107` versus `addendum.md:362-396` and `prd.md:276-285`).
- The lint codes in the convention are `undescribed_property`, `unmarked_identifier`, and `unmarked_paging_member` (`ARCHITECTURE-SPINE.md:184`); §G fixes the public codes as `missing_property_description`, `unmarked_identifier_like_property`, and `payload_paging_member` (`addendum.md:335-341`).
- The spine adds `unsupported_format` as an error code (`ARCHITECTURE-SPINE.md:185`), while FR-18 makes an unsupported format `configuration_invalid` (`prd.md:382-390`) and §G's exhaustive error table has no `unsupported_format` (`addendum.md:370-375`).

This is exactly the head-to-head divergence AD-5 claims to prevent: separately implemented Core records, MCP output schemas, CLI rendering, and snapshot fixtures can all comply with the spine while failing FR-11.

**Required correction:** replace the shorthand AD-5 result and error records with the exhaustive §G shapes (or name typed records whose required/optional members are explicitly identical to §G); align lint and error discriminators; make MCP output-schema snapshots assert required fields, member types/constraints, enums, and omission rules; and keep catalog diagnostics off `list_modules`.

## High

### RV-RUB-003 — AD-16 depends on a nonexistent `Hexalith.Parties.Aspire`

**Criterion:** named-technology fit; brownfield consistency; source capability coverage  
**Disposition:** discuss

AD-15 permits `Hexalith.<Module>.Aspire`, AD-16 requires Tenants and Parties to be composed through their `*.Aspire` packages, and the Stack pins `Hexalith.Parties.Aspire` to 1.1.1 (`ARCHITECTURE-SPINE.md:139-149`, `:212`). Current repository evidence does not contain that package or project:

- the central catalog lists Parties packages at `references/Hexalith.Builds/Props/Directory.Packages.props:80-88`, with no `Hexalith.Parties.Aspire`; it separately lists `Hexalith.Tenants.Aspire` at `:97`;
- the Parties release manifest contains nine packages and no Aspire helper (`references/Hexalith.Parties/tools/release-packages.json:1-40`);
- the Parties solution's `src` list contains `Hexalith.Parties.AppHost` but no Aspire extension package (`references/Hexalith.Parties/Hexalith.Parties.slnx:23-36`);
- the current AppHost composes the Parties domain project directly (`references/Hexalith.Parties/src/Hexalith.Parties.AppHost/Hexalith.Parties.AppHost.csproj:14-19`; `Program.cs:90-103`).

Therefore the declared v1 harness cannot restore or compose both required Modules as written, and FR-20/NFR-7 cannot close (`prd.md:395-403`, `:423-430`).

**Decision needed:** either make a published, catalogued `Hexalith.Parties.Aspire` composition helper an explicit upstream v1 prerequisite with owner and revisit gate, or select and document another supported test-only composition path that still satisfies the no-module-server-package boundary. Then align AD-15, AD-16, the Stack, CI prerequisites, and the open-items list. Do not leave a fictitious version pin.

### RV-RUB-004 — Offline discovery and `submittable` omit the Gateway-URL state

**Criterion:** real divergence points; enforceability; source capability coverage  
**Disposition:** autofix

AD-3 says `ICatalog.Describe` derives `Submittable` and `Reason` from `ResolvedSettings.ReadOnly` only (`ARCHITECTURE-SPINE.md:67-71`). AD-13 says a missing URL is `configuration_invalid` without restricting that failure to execution (`:127-131`). The runtime table correctly says the operator supplies the URL (`:257-262`), but it does not settle startup/discovery behavior.

The source contract is explicit: discovery and MCP startup work without a URL; execution alone fails; `describe_operation` reports `submittable: false, reason: configuration_invalid`, except `read_only` takes precedence for a write (`addendum.md:416-424`; `prd.md:254-261`, `:301-309`).

One head can follow AD-3 and report `submittable: true` offline while another follows AD-13 and refuse startup. Both would claim compliance with the current spine.

**Required correction:** bind the setting at the Core discovery/execution seam: unresolved URL never blocks catalog-only verbs or MCP discovery; it makes execution return `configuration_invalid`; description derives `submittable` from both URL availability and Read-only Mode, with `read_only` precedence for writes. Add one offline-discovery fixture through both heads.

## Medium

### RV-RUB-005 — The fixture cardinality contradicts the final NFR-1 handoff

**Criterion:** source capability coverage; enforceability  
**Disposition:** autofix

The Tests convention says one `Sample.Contracts` assembly declares two Modules (`ARCHITECTURE-SPINE.md:193`). The final PRD requires one declared synthetic Module in the production-like Catalog/benchmark and construction of the other Identifier Kind in isolation (`prd.md:423-424`, `:523-529`). AD-15 itself says `tests/Hexalith.McpCli.Sample.Contracts` is "the only synthetic Module" (`ARCHITECTURE-SPINE.md:143`), so the spine is internally inconsistent as well.

**Required correction:** make `Sample.Contracts` declare one Module, select which Identifier Kind it exercises, and require isolated Catalog construction for the other kind. Bind the NFR-1 benchmark population explicitly to Tenants, Parties, and that one sample Module.

### RV-RUB-006 — Pre-initialize MCP failures are not fixed as a protocol-safe behavior

**Criterion:** complete owned dimensions; enforceability; source capability coverage  
**Disposition:** autofix

The channel convention says stdout carries JSON-RPC and everything else goes to stderr (`ARCHITECTURE-SPINE.md:187`), but it does not fix the failure lifecycle before versus after JSON-RPC initialization. AD-12 only defines tool-call failures (`:121-125`).

FR-10 and §G require settings and catalog validation before initialization; each pre-initialize failure writes exactly one structured error to stderr, writes zero stdout bytes, and exits 2; post-initialize failures travel only through JSON-RPC/MCP (`prd.md:267-285`; `addendum.md:362-368`). This affects startup wiring shared by settings, catalog, and MCP-host stories, so leaving it implicit permits incompatible process behavior and risks corrupting stdout.

**Required correction:** add the pre/post-initialization state boundary to AD-11/AD-12 or Channels and require fixtures for malformed settings, empty Catalog, and `mcp --strict` diagnostics.

### RV-RUB-007 — AD-1 assigns adapter-only FR behavior to Core

**Criterion:** enforceability; real divergence points  
**Disposition:** autofix

AD-1 says every rule in FR-13 through FR-19 is implemented once in Core and that a head may only bind, call Core, and render (`ARCHITECTURE-SPINE.md:41-45`). Other spine rules correctly place exit-code mapping only in the CLI (`:186`), `send_command` omission and MCP error carriage in the MCP adapter (`:121-125`), table output in the CLI (`:190`), and config verbs at the CLI/Core boundary (`:127-137`).

The blanket sentence is therefore unenforceable and conflicts with the architecture's own allocation. A builder can either violate AD-1 or duplicate/drag protocol concerns into Core.

**Required correction:** narrow AD-1 to shared semantic decisions—settings values after resolution, catalog behavior, payload/envelope validation, execution, and result/error records—and explicitly reserve transport registration, tool advertisement, CLI exit codes, table/file rendering, and protocol carriage for the appropriate adapters.

### RV-RUB-008 — Deferring `config` parity to a future copy permits a public CLI contract to drift

**Criterion:** Deferred safety  
**Disposition:** autofix

AD-14 fixes the profile schema and verb names (`ARCHITECTURE-SPINE.md:133-137`), but Deferred says exact flags will be copied at story time from the then-current Admin CLI (`:315`). That is a moving external reference rather than a stable decision. Separate stories for `profile add/remove/list`, `use`, `current`, and `set` can choose incompatible argument names, overwrite semantics, token masking, and error behavior.

The PRD/addendum already bind the v1 verbs and settings surface (`prd.md:382-390`; `addendum.md:199-246`), and repository guidance points to the current Admin CLI shape (`AGENTS.md:90-95`).

**Required correction:** freeze the copied Admin CLI surface against the pinned source revision or enumerate the remaining flags and mutation/error semantics in AD-14. Defer only implementation-local table column widths or prompts that cannot make independently built verbs incompatible.

### RV-RUB-009 — AD-15 does not distinguish the product's own Decoration Package from the external Hexalith allowlist

**Criterion:** source capability coverage; enforceability  
**Disposition:** autofix

AD-15 calls its exact set the "Hexalith production-dependency allowlist" and omits `Hexalith.McpCli.Abstractions` (`ARCHITECTURE-SPINE.md:139-143`), while AD-2 requires Contracts packages to reference the Abstractions package (`:47-64`). The final PRD deliberately distinguishes the product's own Decoration Package from the external allowlist (`prd.md:95-104`) and calls out that distinction as an architecture handoff (`:523-529`).

A literal closure test generated from AD-15 can reject the very Decoration Package used by decorated Contracts; a looser implementation can silently exempt other in-repository packages.

**Required correction:** define the tool's own `Hexalith.McpCli.Abstractions` as a separate first-party product artifact allowed at the declared edges, then define the exact external Hexalith/domain allowlist and closure independently. Encode both sets in the dependency-graph test.

### RV-RUB-010 — The operational envelope leaves the Aspire CI checkout/build mechanism open at implementation time

**Criterion:** complete owned dimensions, especially operational/environmental envelope  
**Disposition:** discuss

AD-16 requires top-level submodules to be checked out and built before the Aspire tier, and the runtime table assigns that behavior to `domain-ci.yml` (`ARCHITECTURE-SPINE.md:145-149`, `:257-261`). Open Questions then leaves the exact reusable-workflow inputs to the harness story (`:317-320`). This is a cross-cutting CI/repository-boundary decision: the AppHost, integration test, and workflow stories can each assume different source availability and build ownership.

Repository policy also limits initialization to root-declared submodules and forbids recursive/nested updates (`AGENTS.md:47-61`). The mechanism must therefore be selected before the harness story, not inside it.

**Decision needed:** bind the exact `domain-ci.yml` inputs and root-submodule checkout/build contract, or make the missing upstream workflow capability an explicit prerequisite with owner and revisit condition. Include failure behavior when a required root submodule is absent.

## Low

### RV-RUB-011 — One Stack entry is not the exact central pin

**Criterion:** named-technology currency evidence  
**Disposition:** autofix

The memlog contains same-day web-and-catalog verification for the named stack (`.memlog.md:34-35`), and most Stack entries match the current central catalog. However, the spine labels `CommunityToolkit.Aspire.Hosting.Dapr` as `13.5.1-beta (catalog pin)` (`ARCHITECTURE-SPINE.md:211`), while the exact catalog pin is `13.5.1-beta.757` (`references/Hexalith.Builds/Props/Directory.Packages.props:151`). These are distinct NuGet version identifiers.

**Required correction:** write the exact `13.5.1-beta.757` pin or state explicitly that it is transitive and owned solely by `Hexalith.EventStore.Aspire`; do not present the shortened prerelease label as an exact catalog pin.

## Checklist judgment

| Good-spine criterion | Judgment | Evidence |
| --- | --- | --- |
| Fixes all real divergence points one level down | **Fail** | RV-RUB-001, -002, -004, -006, -007. |
| Every AD Rule is enforceable and prevents its stated divergence | **Fail** | AD-5's record shorthand does not constrain §G; AD-1 conflicts with adapter allocations; AD-3 omits URL state. |
| Nothing in Deferred can let units diverge | **Fail** | RV-RUB-008. Other deferred items have adequate release/revisit boundaries. |
| Named technology is verified-current and fit | **Fail, narrow** | Same-day verification evidence exists, but RV-RUB-003 names a nonexistent package and RV-RUB-011 shortens an exact prerelease pin. |
| Ratifies rather than contradicts brownfield reality | **Fail** | RV-RUB-003. The remaining flat layout, Build catalog, EventStore client, sibling CI/release pattern, and source-generated logging choices are consistent with repository evidence. |
| Covers source capabilities | **Fail** | RV-RUB-001, -002, -004, -005, -006, -009. Capability ownership is otherwise mapped at `ARCHITECTURE-SPINE.md:282-301`. |
| Does not weaken inherited parent-spine constraints | **Not applicable** | No parent spine is declared. PRD/brief constraints are binding source inputs; their conflicts are reported above. |
| Every owned dimension is decided, deferred, or open | **Mostly pass, one operational gap** | Runtime/deployment environments are explicit at `ARCHITECTURE-SPINE.md:244-262`; RV-RUB-010 leaves the CI source/build contract unresolved too late. Boundaries, state ownership, dependency policy, release, test topology, and next-release HTTP are otherwise covered. |

## Positive assessment

The spine is not broadly underspecified. Its named hexagonal paradigm (`ARCHITECTURE-SPINE.md:26-37`), dependency direction (`:47-65`), single catalog and executor (`:67-107`), settings/profile ownership (`:115-137`), production dependency closure (`:139-143`), package/release model (`:151-161`), and runtime/environment view (`:244-280`) form a coherent substrate. The failures are concentrated at the latest PRD-to-architecture reconciliation and one incorrect assumption about the Parties test-composition package.

## Recommended update order

1. Correct idempotency and the exhaustive public records/errors (RV-RUB-001, -002).
2. Resolve the Parties composition prerequisite and offline discovery semantics (RV-RUB-003, -004).
3. Align fixture cardinality, MCP startup channels, AD-1 responsibility wording, and the dependency allowlist (RV-RUB-005, -006, -007, -009).
4. Freeze the config and CI operational seams, then correct the exact Dapr integration pin (RV-RUB-008, -010, -011).


---
inventory_version: '1.2.0'
status: approved
module: parties
source_repository: 'https://github.com/Hexalith/Hexalith.Parties'
source_revision: '493730941329d1bca3b4f6b2f6a67ffe305c2443'
source_spec: '_bmad-output/implementation-artifacts/spec-4-1-approve-the-parties-migration-inventory.md'
maintainer_approval_ref: '#a1-session-approval-2026-10-16'
amendment_ref: '#a1-amendment-120-2026-11-09'
amendment_source_spec: '_bmad-output/implementation-artifacts/spec-5-3-enroll-replacement-contracts-and-profiles.md'
---

# Parties migration inventory v1

Inventory **1.2.0** corrects the C05 delete pre-read oracles in approved
inventory 1.1.0. The 1.2.0 candidate counts only after the owner approves its
exact bytes through [A1 amendment 1.2.0](#a1-amendment-120-2026-11-09).
Approved inventory 1.0.0 records the requesting user's first-increment scope
and routing decision in [A1](#a1-session-approval-2026-10-16), and
[A1 amendment 1.1.0](#a1-amendment-110-2026-11-08) rewords enrollment
eligibility and records C06 and C07. No row identity, target or disposition
changes. Scope approval does not prove Gateway readiness, published Contracts,
authorization, behavior parity, or retirement readiness. The missing
declarations, Queries and execution evidence remain explicit downstream gates.

The source checkout was clean at the revision above. It exposes exactly **five
MCP tools, with six behavioral variants, no MCP resources, and no proprietary
CLI found**. The seven distinct approved target operations are normalized below;
shared targets are counted once, even when multiple legacy behaviors use them.
This file is a migration and test artifact outside `src/`, never runtime
configuration.

## Approval and coverage rules

- `replace` identifies a named replacement; `withdraw` requires explicit owner
  withdrawal; `defer` retains a gap with an owner and rationale.
- `include` requires an approved, gateway-ready `replace` mapping. `exclude`
  requires an approved `withdraw` or `defer`. The `include` values below approve
  intended replacement scope. A target becomes eligible for enrollment once its
  decorated Contracts type, approved vectors and release inventory exist; Story
  4.10 enrolled all seven targets through `Hexalith.Parties.Contracts` 1.5.1.
  Enrollment is not parity or retirement readiness: the authorization and
  behavior evidence required by C01–C08 still gates retirement
  (A1 amendment 1.1.0).
- Every legacy, target, compatibility and exclusion row references A1. No
  withdrawal is approved: L01–L05 are `replace` / `include`; N01–N04 are
  `defer` / `exclude`. Missing approval would keep Story 4.1 incomplete.
- Exclusion never authorizes deletion. Preserve the legacy host until accepted
  replacement or withdrawal, authorization, behavior, and release evidence exists.

## A1 Session approval (2026-10-16)

- **Approver:** the requesting user in this session; no named signatory or
  separate external maintainer approval is asserted.
- **Exact instruction:** "apply recommended", after discussion of the complete
  candidate inventory. The accepted decision is preserved in the source spec's
  frozen **Approved decisions (2026-10-16)** section.
- **Scope:** inventory 1.0.0 at source revision
  `493730941329d1bca3b4f6b2f6a67ffe305c2443`, all L01–L05 tool mappings and six
  variants, T01–T07 canonical names/intended CLR types, N01–N04 deferrals,
  compatibility decisions C01–C08 below, and the command routing decision.
- **Accepted migration differences:** seven typed operations, explicit party
  and child IDs with nested payloads, separate activation calls and shared
  McpCli result/error documents. Preserve privacy, tenant authorization, domain
  and bounded validation, root/child identifier consistency, and safe repeated
  soft deactivation. Correct misleading search totals and ignored filters
  through explicit upstream Query semantics. Preserve identifier compatibility
  or gate an approved conversion before retirement.
- **Routing:** retain attributes, full CLR command wire names, domain `party`,
  String identifiers and root `PartyId`; no `ICommandContract` adoption or wire
  migration is approved.
- **Limits:** this is scope approval only. It does not supply missing Contracts,
  downstream credentials, authorization/behavior proof, package publication,
  enrollment or legacy-host retirement. Stories 4.9/4.10 own upstream delivery;
  Stories 4.11/4.13 own execution proof.

### A1 amendment 1.1.0 (2026-11-08)

Story 5.3 amends the approved 1.0.0 inventory in one versioned change. It
rewords the eligibility rule in the coverage rules, adds the C05 delete oracles
including the erased-party and processing-restricted differences, and records
the C06 and C07 resolutions with their test anchors and the reliance on
upstream Query error handling. The source revision, all row identities, the
seven targets, every disposition and coverage value, the routing decision and
the A1 limits are unchanged.

This amendment counts only after the owner approves these exact bytes. The
[approval receipt](evidence/story-5-3/approval/approval.json) records that
decision, the owner's verbatim label and the SHA-256 of both the exact approved
1.0.0 bytes, preserved under `evidence/story-5-3/approval/1.0.0/`, and the
approved 1.1.0 bytes, now preserved with that receipt under
`evidence/story-5-3/approval/1.1.0/`.
[Story 5.3 verification](evidence/story-5-3/verification.md) records the checks. The amendment grants no execution, parity or retirement
authority, and retirement still requires every C01–C08 acceptance requirement.

### A1 amendment 1.2.0 (2026-11-09)

This amendment corrects only C05's delete oracles. The 1.1.0 wording omitted
failure of the legacy tool's mandatory detail pre-read and treated its
`not_found` and erased-party outcomes as unconditional. Legacy `delete_party`
reads before deciding whether to submit `DeactivateParty`; the generic heads
submit the Command directly. C05 now distinguishes failed reads, successful
inactive reads and successful active reads, including the SDK handler's absent
or erased detail path. The aggregate guards and legacy tool body are unchanged
since the inventory source revision; the SDK read behavior is stated separately
for `4937309` and the cited `1308ad000c79ebc394fc395588f9af91092e8c4c` checkout.

This amendment counts only after the Parties owner approves these exact bytes.
Its [approval receipt](evidence/story-5-3/approval/amendment-1.2.0.json)
binds the preserved 1.1.0 inventory and receipt to this 1.2.0 candidate and
records the owner's verbatim label after approval. The prior inventory and
receipt stay byte-for-byte unchanged under
`evidence/story-5-3/approval/1.1.0/`. Until approval, 1.1.0 remains the latest
approved version and its C05 oracle is known to be incomplete; the ledger item
remains open. The `status: approved` frontmatter is the proposed final text,
not evidence that the pending receipt has been approved.

All 24 row identities, seven targets, dispositions, coverage values, source
revision, routing, C06/C07 text and A1 limits are unchanged. No Contracts,
vectors, live plans, dependencies, runtime behavior, parity or retirement
authority changes. The correction requires new execution evidence for the
selected Gateway/module cohort before any retirement claim.

## Legacy MCP tool rows

Target references resolve to exact canonical names and full intended CLR types
in the next table. All rows require tenant-scoped authorization at the Gateway;
read results may contain personal data.

| ID | Legacy operation / variants | Disposition | Coverage | Intended targets | Rationale and security class | Approval reference |
| --- | --- | --- | --- | --- | --- | --- |
| L01 | `get_party` | replace | include | T01 | Retain detail lookup and erased-party suppression. Personal-data read. | [A1](#a1-session-approval-2026-10-16) |
| L02 | `find_parties`: list and display-name search | replace | include | T02, T03 | Split the two existing query routes explicitly; correct filters/totals and define envelope paging under C02. Personal-data read. | [A1](#a1-session-approval-2026-10-16) |
| L03 | `create_party` | replace | include | T04 | Submit the existing composite command with explicit typed payload under C03. Write containing personal data; legacy tool declares destructive. | [A1](#a1-session-approval-2026-10-16) |
| L04 | `update_party`: details and optional activation change | replace | include | T01, T05, T06, T07 | Account for the optional detail read, composite update and separate activation command under C04. Write; removal/deactivation is destructive. | [A1](#a1-session-approval-2026-10-16) |
| L05 | `delete_party` | replace | include | T01, T07 | Detail pre-read plus soft deactivation; retain safe repeat behavior under C05. Destructive lifecycle write; never GDPR erasure. | [A1](#a1-session-approval-2026-10-16) |

## Normalized intended target operations

These are the seven unique operations approved by A1, each `replace` / `include`
in first-increment scope. Their intended CLR types are an upstream delivery
contract, not a claim of current decoration or publication. New Query types
must be added in the Parties repository by Story 4.10. Existing Command types
need decoration in Story 4.9. All aggregate identifiers use `String` kind and
domain `party`; tenant authority remains in the envelope. Commands use their
root `PartyId`, which already exists on both composite types.

| ID | Canonical Operation Name | Intended decorated CLR type | Existing Gateway route / upstream work | Security class | Approval reference |
| --- | --- | --- | --- | --- | --- |
| T01 | `parties.get-party` | `Hexalith.Parties.Contracts.Queries.GetParty` (new) | Wire Type `PartyDetail`; projection `party-detail`; actor `PartyDetailProjectionQueryActor`; aggregate party ID. Define a Contracts payload and retain erased-party-safe results. | Personal-data read | [A1](#a1-session-approval-2026-10-16) |
| T02 | `parties.list-parties` | `Hexalith.Parties.Contracts.Queries.ListParties` (new) | Wire Type `PartyIndex`; projection `party-index`; actor `PartyIndexProjectionQueryActor`; aggregate constant `parties`. Move list filters into a public Query and define envelope paging. | Personal-data read | [A1](#a1-session-approval-2026-10-16) |
| T03 | `parties.search-parties` | `Hexalith.Parties.Contracts.Queries.SearchParties` (new) | Wire Type `PartySearch`; projection `party-index`; actor `PartyIndexProjectionQueryActor`; aggregate constant `parties`. Define the public Query and corrected search/filter semantics. | Personal-data read | [A1](#a1-session-approval-2026-10-16) |
| T04 | `parties.create-party` | `Hexalith.Parties.Contracts.Commands.CreatePartyComposite` | Existing full-type-name command route; approved `Name="create-party"` override; Story 4.9 decoration. | Personal-data / destructive write | [A1](#a1-session-approval-2026-10-16) |
| T05 | `parties.update-party` | `Hexalith.Parties.Contracts.Commands.UpdatePartyComposite` | Existing full-type-name command route; approved `Name="update-party"` override; Story 4.9 decoration. | Personal-data / destructive write | [A1](#a1-session-approval-2026-10-16) |
| T06 | `parties.reactivate-party` | `Hexalith.Parties.Contracts.Commands.ReactivateParty` | Existing full-type-name command route; Story 4.9 decoration. | Lifecycle write | [A1](#a1-session-approval-2026-10-16) |
| T07 | `parties.deactivate-party` | `Hexalith.Parties.Contracts.Commands.DeactivateParty` | Existing full-type-name command route; Story 4.9 decoration. | Destructive lifecycle write | [A1](#a1-session-approval-2026-10-16) |

Current Query DTOs `ResolvePartyIdentity` and `ResolveHumanActorBindingAt` do
not replace these reads. The list/search payload records currently live privately
in the client and internally in the server. Their existence is not a decorated
Contracts release. The legacy client explicitly sends `EntityId` equal to the
party ID or `parties`, along with projection actor compatibility fields. At the
pinned source, canonical `IDomainQueryHandler` implementations instead dispatch
to `PartySdkQueryService`, which reads SDK read models directly. Its detail and
index envelope validation falls back to `AggregateId` when `EntityId` is omitted
or blank, and rejects mismatches: detail must match the party aggregate ID;
list/search must use `parties` for both resolved identifiers. The legacy
actor-named fields/discriminator constants do not prove actor execution on this
SDK handler path. Story 4.10 must pin the actual Gateway dispatch path; Stories
4.11/4.13 must test omitted, matching and mismatching `EntityId` for each of
T01, T02 and T03, including successful fallback and rejection before a mismatched
read. These known source rules still require packaged/transport execution proof.

## Approved compatibility and versioning decisions

| ID / legacy rows | Observed behavior | Approved workflow and outstanding acceptance requirement | Approval reference |
| --- | --- | --- | --- |
| C01 / L01 | Detail is suppressed when the returned party is erased. | Preserve equivalent privacy semantics at the module/Gateway boundary in T01, including caller-composed workflows. Story 4.10 implements; 4.11/4.13 prove it. | [A1](#a1-session-approval-2026-10-16) |
| C02 / L02 | Empty query lists; nonempty query is trimmed and searches display names. Page is clamped to at least 1, size to 1–100, default size 20. List supports type, active and four created/modified bounds. Search filters type/active after paging, reports a filtered-page count, and ignores date bounds. | Select T02 or T03 explicitly. Story 4.10 defines public Query filters and authoritative envelope paging, validates bounds and documents legacy page/default mapping. Correct totals and apply supported filters upstream before paging; explicitly reject unsupported combinations rather than silently ignore them. This is an accepted semantics correction, not a requirement to preserve the misleading totals/ignored filters. Stories 4.11/4.13 verify non-default pages, filtered totals and continuation contents. | [A1](#a1-session-approval-2026-10-16) |
| C03 / L03 | AI aliases, person/organization inference, optional/generated party ID, generated child IDs; both create/update wrappers limit each trimmed input field to 512 characters and combined input to 4096. Existing composite validators and aggregate cap sub-operations (default 100). | Accept T04's explicit IDs, declared type and nested payloads in place of wrapper aliases, inference and generation. Preserve domain and bounded validation upstream. Before readiness, 4.9 must publish and verify explicit nested-string, collection/removal and total-input bounds for both T04/T05, accounting for both wrappers' 512/4096 limits and retaining the existing configured composite sub-operation cap (default 100). This assigns a bounded policy decision, not new numeric limits or a claim that existing collections are unbounded. No Parties adapter is added to McpCli. Verify boundary and over-limit cases through 4.11/4.13. | [A1](#a1-session-approval-2026-10-16) |
| C04 / L04 | Read/merge patch handling, contact/identifier aliases and removals, route ID authority, no-change rejection, the same 512-character trimmed-field/4096-character combined-input wrapper bounds as create, then optional separate (re)activation with all correlations retained. | Accept callers using T01 when needed to construct typed T05 payloads, with activation-only work using T06/T07. Each call has its own result/correlation; the workflow is non-atomic and generic heads submit once per call. Story 4.9 must reject PartyId-only/no-supported-change T05 updates upstream, preserve root/child ID consistency and publish/verify the nested, removal and total-input bounds required by C03, retaining the existing sub-operation cap. Stories 4.11/4.13 must include the empty-update negative case with no state mutation, plus bounded-validation cases. | [A1](#a1-session-approval-2026-10-16) |
| C05 / L05 | Pre-read returns success without submission when already inactive; otherwise sends DeactivateParty, reports `soft-deactivation` and `gdprErasurePerformed=false`. The current aggregate returns NoOp for an already-inactive party after its lifecycle/security guards. | Preserve safe repeated soft deactivation through aggregate behavior; a projection pre-read alone cannot prove repeat safety. Generic heads do not pre-read or orchestrate; 4.9/4.10 must establish the safe path, 4.11 tests inactive/repeated cases, and 4.13 must exercise stale-projection and concurrent-repeat cases with persisted aggregate state and event evidence proving a safe no-op without duplicate deactivation effects. Naming T07 proves neither safety nor caller-key deduplication; no retry engine is needed. Never substitute EraseParty. Legacy result flags follow C06. Delete oracles (A1 amendment 1.2.0): generic `parties.deactivate-party` submits directly, so the aggregate's missing-party rejection yields `gateway_error` 404 with reason `party-not-found`; `ErasurePending` through `Erased` yields 422 `party-erasure-in-progress`; processing restriction yields 422 `party-processing-restricted`; otherwise an inactive aggregate accepts a NoOp. The aggregate guards run in that order (`references/Hexalith.Parties/src/Hexalith.Parties/Domain/PartyAggregate.cs:867-890`, `:1547`, `:1560`, at `1308ad000c79ebc394fc395588f9af91092e8c4c`, unchanged since `4937309`). Legacy `delete_party` first calls `GetPartyAsync` (`references/Hexalith.Parties/src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs:406`, also unchanged since `4937309`). On SDK dispatch, absent detail returns the `actor-not-found-infrastructure` failure sentinel: `4937309:src/Hexalith.Parties/Queries/PartySdkQueryService.cs:341-343` uses `ActorNotFoundInfrastructure`; the cited current checkout's `PartySdkQueryService.cs:324-326` uses `ReadModelUnavailable` and also suppresses erased detail. At EventStore `3d4ba67db99f2f0bcd64b7d353609b555870cc9b`, `QueryRouter.cs:168-170` forwards the failed SDK result with `NotFound: false`; `SubmitQueryHandler.cs:159-162` recognizes spaced not-found messages, not that sentinel, so `:133-141` maps it to HTTP 500. `HttpPartiesQueryClient.cs:157-159` throws on that failed pre-read and `PartiesMcpTools.cs:597` maps 5xx to `downstream_failed`; no deactivate Command is submitted. If a selected query path instead returns 404 or 410, the legacy wrapper maps it to `not_found` (`PartiesMcpTools.cs:594`); this is not the absent-detail SDK oracle. If the pre-read succeeds and shows an inactive party, legacy returns idempotent success without submission, even if the aggregate is now missing, erased or restricted. If it succeeds and shows an active party, legacy submits the Command: a subsequent missing-party 404 maps to `not_found`, and erasure or restriction 422 maps to `validation_failed` (`PartiesMcpTools.cs:591-597`). A stale successful pre-read can therefore choose a different branch from a current read. The pinned `4937309` SDK does not have the current checkout's `IsErased: false` read guard; record the deployed SDK/Gateway dispatch and pre-read state when selecting the erased-case oracle. These differences are recorded migration differences, not parity; no upstream behavior is changed here. | [A1](#a1-session-approval-2026-10-16) |
| C06 / All | Legacy `PartiesMcpToolResult` has status/category/code/message/toolName plus optional correlation/data, including delete-specific flags. Its client-error mapping emits fixed safe messages rather than raw downstream details; generic `OperationError.FromGateway` copies Gateway detail/title. | Accept the versioned move to shared McpCli result/error documents and per-call results while preserving the legacy error-message privacy guarantee. Parties/Gateway must sanitize public errors before those fields reach generic documents; no module-specific Core changes. Before retirement, 4.11/4.13 must assert personal data and secrets in downstream failures never appear in either head's public error documents or diagnostic channels, including detail/title paths. Document the wrapper-shape replacement; soft-deactivation intent and absence of GDPR erasure remain requirements. Prove both heads in 4.11 and domain effects in 4.13. Resolution for the generic heads (A1 amendment 1.1.0): `src/Hexalith.McpCli.Core/Execution/OperationError.cs:41-53` copies only status, detail or title, reason, retryable, clientAction, retryAfter and a canonical correlation ID, `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:35-42` maps every other exception to a fixed `internal_error`, and `src/Hexalith.McpCli/Hosting/HostFactory.cs:51-57` replaces the HTTP client loggers so a failed Gateway request logs no exception text. `tests/Hexalith.McpCli.Cli.Tests/PartiesMigrationCompatibilityTests.cs:56` proves through both heads over Parties 1.5.1 that markers in `type`, `instance`, `tenantId`, `errors`, `extensions` and `rejectionType`, in a non-JSON body and in inner exceptions reach neither stdout, stderr nor MCP text or structured content, and that each document equals the Sample operation's document for the same failure; no Parties-specific mapping exists. Detail (or title), reason, clientAction and retryAfter are copied as the Gateway sends them, and for a non-JSON response detail is the HTTP reason phrase, so their privacy relies on upstream handling: the Gateway sanitizes Command rejections (`references/Hexalith.EventStore/src/Hexalith.EventStore/ErrorHandling/DomainCommandRejectedExceptionHandler.cs:43-58`) but passes a module's Query error message through as detail for every status except the invalid-page 400 and 403 (`references/Hexalith.EventStore/src/Hexalith.EventStore/ErrorHandling/QueryExecutionFailedExceptionHandler.cs:88-94`), including the 400 malformed-request response built from the module's `sentinel: detail` message (`references/Hexalith.EventStore/src/Hexalith.EventStore.Server/Pipeline/SubmitQueryHandler.cs:104-113`), and Parties returns only sentinel codes there (`references/Hexalith.Parties/src/Hexalith.Parties/Queries/PartySdkQueryService.cs:242`, `:248`). The README documents the shared error document. | [A1](#a1-session-approval-2026-10-16) |
| C07 / All | Party IDs accept support-safe strings plus braced, parenthesized and X-format GUID representations beyond generic aggregate syntax. | Keep String kind. Preserve reachability of legacy IDs or require an explicitly approved conversion with migration evidence before retirement. Neither conversion details nor a runtime validator change is approved here. Stories 4.9/4.10 resolve compatibility; 4.11/4.13 verify it. No silent ULID conversion. Resolution (A1 amendment 1.1.0): String kind is kept and no conversion is approved. Legacy braced, parenthesized and X-format GUID root `PartyId` values are refused with `validation_failed` at `/PartyId` before any Gateway call (`src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs:140-143`). They cannot exist as EventStore streams, because `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Identity/AggregateIdentity.cs:11` and `:136` enforce the same rule; `Parties.Mcp` forwards them raw and the Gateway rejects them, although `references/Hexalith.Parties/src/Hexalith.Parties.Contracts/ValueObjects/PartyIdentifier.cs:24-50` admits them. Support-safe root IDs such as `Legacy.party_01-A` and String-kind child identifiers in any of these forms reach the Gateway byte-for-byte (`src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs:322-331`). `tests/Hexalith.McpCli.Cli.Tests/PartiesMigrationCompatibilityTests.cs:124` and `:169` pin both through both heads. | [A1](#a1-session-approval-2026-10-16) |
| C08 / All | Context accepts claims or raw headers, forwards inbound Authorization and appends identity headers; the host has no explicit authentication middleware. | Never carry these weaknesses into the target. V1 uses configured stdio operator-session/Gateway credentials and envelope tenant authority. Downstream credential acceptance, authenticated authorization, missing-context/credential refusal and no-secret evidence remain open with the Parties operation and McpCli transport/security maintainers; 4.9/4.10 coordinate and 4.11/4.13 prove the supported transport before retirement. Negative proof must show tenant-A credentials denied tenant-B reads and writes through changed session tenants and allowed MCP per-call tenant overrides, with no tenant-B data disclosure or mutation. Local override permission only permits selecting an envelope tenant; Gateway authorization independently decides access. | [A1](#a1-session-approval-2026-10-16) |

These are approved scope and downstream verification requirements, not new McpCli
runtime work in Story 4.1. Their delivery belongs to Parties decoration/handlers
and Stories 4.9–4.13. Existing wrappers remain in service until the applicable
compatibility or accepted versioning evidence is complete.

## Explicit nonlegacy scope exclusions

These rows account for behaviors mentioned by the story and adjacent public
APIs. They are **not additional legacy MCP tools** and do not increase the five-tool
count. Approved deferral preserves the existing owning surfaces; it is not
withdrawal or retirement approval.

| ID | Behavior | Disposition / coverage | Specific rationale and unresolved gap | Security class | Approval reference |
| --- | --- | --- | --- | --- | --- |
| N01 | GDPR erasure and lifecycle actions: EraseParty, CancelPartyErasure, RetryErasureVerification, CompletePartyErasure, MarkPartyEncryptionKeyDeleted, MarkErasureVerified | defer / exclude | Absent from the five tools. Parties privacy/lifecycle maintainer owns separate inventory, orchestration, irreversible key destruction, proof and authorization before later exposure. Delete remains soft deactivation. | Privacy-destructive / internal lifecycle | [A1](#a1-session-approval-2026-10-16) |
| N02 | RotatePartyKey and tenant key rotation APIs | defer / exclude | Absent from MCP. Parties security maintainer owns party rotation; tenant key-service maintainer owns tenant-wide wrapping-key rotation. Operational credentials, version guards, resumability and erased-party handling require a separate approved inventory. | Security administration | [A1](#a1-session-approval-2026-10-16) |
| N03 | Consent/restriction and newer identity provisioning/binding operations | defer / exclude | Existing adjacent Contracts establish no legacy MCP coverage or authority to expand v1. Parties privacy/identity maintainer owns future scope and authorization approval. | Privacy and identity administration | [A1](#a1-session-approval-2026-10-16) |
| N04 | Temporal name lookup (`get_party_name_at`), email/identifier, semantic/hybrid/graph/temporal/case search, infrastructure/admin/projection operations | defer / exclude | These capabilities are not exposed by the five tools. Parties operation maintainer and the relevant platform/operator maintainer own any later inventory and generic contract/transport decision. No replacement or withdrawal claim is made. | Unsupported read or operator capability | [A1](#a1-session-approval-2026-10-16) |

No resources or CLI rows are invented. A later source revision that introduces
another tool, resource, or CLI requires a refreshed inventory.

## Routing and credential decisions

**Approved command routing under [A1](#a1-session-approval-2026-10-16):** retain attribute routing,
`WireTypeConvention.FullTypeName`, domain `party`, and `AggregateIdProperty="PartyId"`.
The processor resolves full CLR names (and unique short CLR names), not kebab-case
wire names. Canonical McpCli operation names are separate from wire names. T04–T07
retain their exact full CLR names as wire values. T01–T03 explicitly retain the
existing Query wire values and projection routes in the target table; they must
not inherit new CLR names as wire values. Commands and detail queries use root
`PartyId`; list/search use aggregate constant `parties`. No interface or wire
migration is approved, so Story 4.9 can decorate without a routing break.
Implementing `ICommandContract` with identical wire values need not break routing;
however, its `CommandType` documentation in the pinned
`Hexalith.EventStore.Contracts` 3.121.0 package explicitly requires kebab-case.
McpCli's current resolver accepting a full name does not make that interface use
contract-conforming. Do not recommend this intermediate option without an
upstream contract decision. Adopting the documented interface convention changes
wire values and requires an explicit compatibility/versioning decision before
publication. That alternative is outside this approved routing decision.

The current MCP context accepts claims or raw header fallbacks, forwards inbound
Authorization and appends identity headers; its host has no explicit authentication
middleware. These are observed source gaps, not safe behaviors to carry forward.
Upstream Story 8.8 AC5 requires an authenticated principal, audience validation,
single safe outbound identity values, and an approved separate downstream
credential or refusal. V1 McpCli stdio uses its configured operator session and
Gateway credentials; it does not acquire forwarded HTTP user identity. Parties
must deliver the credential/authorization evidence assigned in C08 before
replacement/retirement. Payload tenant/actor fields never establish authority.

## Evidence and handoff

The complete repeatable source/row checker and its commands are preserved in
[Story 4.1 verification evidence](evidence/story-4-1/verification.md), executable
from this repository root with Python and Git. It covers the approved 1.0.0
bytes, preserved under `evidence/story-5-3/approval/1.0.0/`, at its pinned
Parties revision, and asserts version 1.0.0, so it does not check 1.1.0. It
verifies the static inventory; the downstream behavior cases above remain
unproven here. [Story 5.3 verification](evidence/story-5-3/verification.md)
holds the reproducible static check of the 1.1.0 amendment and its source
anchors.

All following paths are relative to the pinned Parties repository:

- `src/Hexalith.Parties.Mcp/Program.cs:61` and
  `Tools/PartiesMcpToolNames.cs:5` under that project: tool-only registration and
  five exact names; `tests/Hexalith.Parties.Mcp.Tests/PartiesMcpToolContractTests.cs:15`
  pins the surface, with unsupported variants at lines 63 and 104.
- `src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs:24`, `:52`, `:134`, `:235`,
  `:391`: L01–L05. Builders at lines 647 and 729 pin alias/merge behavior.
- `src/Hexalith.Parties.Client/HttpPartiesQueryClient.cs:46`, `:69`, `:105`, `:216`:
  detail/list/search routes and private payloads.
- `src/Hexalith.Parties.Client/HttpPartiesCommandClient.cs:155`, `:246`:
  command envelope/full-name routing and root/child ID normalization.
- `src/Hexalith.Parties/Queries/PartySdkQueryHandler.cs:7` and
  `PartySdkQueryService.cs:664`/`:673` in that folder: direct SDK handler dispatch,
  omitted-EntityId fallback and detail/index mismatch rejection.
- `src/Hexalith.Parties/Validation/CreatePartyCompositeValidator.cs:42` and
  `UpdatePartyCompositeValidator.cs:22` in that folder, plus
  `src/Hexalith.Parties/Domain/PartyAggregate.cs:21`/`:851`: existing sub-operation
  cap (default 100), and inactive-party deactivation NoOp after guards.
- `src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs:566`/`:587`: shared create/update
  wrapper input limits and fixed safe client-error messages. McpCli-local
  `src/Hexalith.McpCli.Core/Execution/OperationError.cs:41` copies Gateway
  detail/title, requiring the upstream privacy handoff in C06.
- `src/Hexalith.Parties/Domain/PartyDomainProcessor.cs:635`: command type lookup;
  `src/Hexalith.Parties.Contracts/Commands/`: four existing target command DTOs.
- `src/Hexalith.Parties.Contracts/ValueObjects/PartyIdentifier.cs:24`:
  legacy identifier syntax; `src/Hexalith.Parties.Mcp/PartiesMcpRequestContext.cs:29`
  and `McpContextForwardingHandler.cs:10` under the same project: identity gaps.
- `_bmad-output/planning-artifacts/architecture.md:59`: approves the McpCli
  direction, not these rows. `_bmad-output/implementation-artifacts/8-8-client-mcp-apphost-build-and-deploy-cleanup.md:44`
  and `story-8-8-owner-prerequisite-plan-2026-10-08.md:155`: owner, credential,
  parity and retention prerequisites; neither is the row approval. A1 records the
  actual requesting-user session decision without inventing external sign-off.

### Completeness check (2026-10-16)

Rechecked the clean source checkout at full revision
`493730941329d1bca3b4f6b2f6a67ffe305c2443` against the declared constants,
`McpServerTool` attributes, `WithToolsFromAssembly` registration and the exact
five-name contract-test expectation. L02 covers both branches (`PartyIndex`
and `PartySearch`); optional update activation is included in L04, not counted as
another tool. L01–L05 therefore cover five tools and six variants.

`Program.cs:61` registers tools only; a scan of tracked `src/` found no
`McpServerResource`/`WithResources` declarations. The solution/source project
inventory and command-parser/CLI-registration scan found no proprietary CLI;
the AppHost is orchestration and the HTTP/web hosts are not invented CLI
operations. Contract tests explicitly exclude temporal/advanced/operator names.

The row check finds five complete `replace` / `include` legacy rows, seven
distinct canonical names and CLR types, and four complete approved
`defer` / `exclude` rows. Every target is used; shared T01 and T07 appear once
in the normalized target table. All rows reference A1, and no missing approval
placeholder or invalid disposition/coverage pair remains. The four Command
DTOs exist; all three intended public Query files remain absent. These are
static inventory checks, not a built-Catalog or Gateway readiness claim.

Story 4.5 consumes approved unique targets and exclusions through a generic gate;
Stories 4.9/4.10 implement declarations and missing read contracts upstream;
Stories 4.11/4.13 prove loopback and live semantics. No package pin, production
manifest, runtime source, or upstream checkout is changed by this approval.

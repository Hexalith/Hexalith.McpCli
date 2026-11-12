---
decision: AD-23
version: '1.0.0'
status: proposed
created: '2026-11-12'
binds: [FR-21, FR-22, MR1, MR2, MR3, MR9]
---

# AD-23 — Non-gateway capability classes

This is the single proposed decision consumed by Stories 5.7–5.10 and Epic 6.
Its effective status becomes ADOPTED only when the separate Story 5.2 receipt
records the owner's approval of these exact decision, class-map and inventory
SHA-256 values, with every role required by the policy below. The immutable
frontmatter records this candidate's proposed state; it is not an effective
status switch. Adoption changes only the receipt and then the unbound spine
and workflow state. Never edit or rehash these decision/map bytes after approval;
a later change is a new candidate requiring a new approval. The specification's
"approve and stop" approved intent and D1–D8, not these implementation bytes.
No inventory disposition changes in this story. No execution, enrollment,
publication or retirement authority is granted.

**No Platform AD or PRD change required:** every admitted capability uses the
existing v1 decorated Command/Query and authenticated Gateway transport. No
generic authenticated non-gateway transport is admitted. Platform AD-11 and
AD-14, PRD §8.2/§8.3, AD-20 and MR4 remain binding. A future staging/stream or
HTTP identity admission needs the separate decisions described below.

## Partition and precedence

The companion `AD-23-capability-class-map.json` binds all eight input inventory
files, their actual versions and exact bytes. Each table row appears exactly
once in `rows` or `records`. An operation takes the class of its primary
capability; a variant takes the class of the behavior it records. Cross-cutting
requirements still apply to every affected operation even when they are not its
primary class. No parity, readiness or authority follows from matching names.

Restrictions take precedence: any UI-only, confirmation-required or destructive
row takes its restricted class, with only confidential UI, owner-held exempt
local tooling or withdrawal as its outcome. This includes local destructive
profile/file variants and unsupported erasure/key-rotation variants. A mixed
variant that includes restricted behavior takes the restrictive outcome. An
operation's lifecycle/status *Query* remains an ordinary module Query; K08
governs the legacy observation engine, subscription and synthetic lifecycle
semantics, not every business read with "status" in its name.

`records` explicitly accounts for unregistered helpers (AU), absence/adjacency
records (AX, N, X), consumer/census bookkeeping (FK, PE, PN and companion-owned
PS rows), gaps (G), and Folders C/Q roadmap candidates. These are not extra
legacy operations. Applicable classes remain attached to capability exclusions
and candidates; pure bookkeeping instead names its governing rows or inventory.
PS14 is a capability family because its modes are missing from the companion.
Its dry-run/live/rollback/abort accounting remains a Story 5.10 obligation.

## Classes and sole outcomes

The eight Admin class names and partition below reproduce Story 5.1's approved
handoff verbatim. A1–A4 contain its 46 remote rows; A5–A8 cover local behavior.

| Class | Capability and governing decision | Sole outcome |
| --- | --- | --- |
| A1 | infrastructure administration: AC09–AC13, AC18–AC21, AM01, AM03–AM06, AM10–AM15, AM19 | confidential UI only (D1) |
| A2 | operator diagnostics: AC01–AC02, AM07–AM09, AM28 | confidential UI only (D1) |
| A3 | stream and state reads: AC03–AC08, AM02, AM20–AM24 | confidential UI only (D1) |
| A4 | tenant administration reads: AC14–AC17, AM25–AM27 | confidential UI only (D1) |
| A5 | process-local context: AM16–AM18 | withdrawal (K15) |
| A6 | retained unavailable stubs: AC22–AC24 | withdrawal (K15) |
| A7 | local credential and profile configuration: AC25–AC30 (Admin G6, Story 5.3) | withdrawal (K15) |
| A8 | shell completion, out of McpCli v1 under PRD §8.2: AC31 | withdrawal (K15) |
| K01 | Ordinary module operations, including FH02/H02 per manifest consumer | decorated Gateway contract |
| K02 | Module-state resource reads: Folders R01/R02, Projects data resources, FH03/H03 | decorated Gateway contract |
| K03 | Freshness, paging and filters, including Folders V01/V02 | decorated Gateway contract |
| K04 | Context, caller keys and identifier formats, including Folders G3 | decorated Gateway contract |
| K05 | Provider egress and pre-submit effects authorized module-side; Folders G6, ChatBot V07/V08 | decorated Gateway contract |
| K06 | Module diagnostics, only when the owner decorates them | decorated Gateway contract |
| K07 | Documentation/resource delivery | withdrawal (D3) |
| K08 | Legacy lifecycle/status observation engine | withdrawal (D2) |
| K09 | Streams, out-of-band staging, local file transport, imports/exports and event streams | continued deferral (D4) |
| K10 | Forwarded per-user identity and HTTP caller authority | continued deferral (MR9) |
| K12 | Module confirmation-required, UI-only or destructive operations, erasure and key rotation | confidential UI only (D7) |
| K13 | FrontComposer compiler CLI, including inspect/migrate and PS03 | exempt local tooling (D5) |
| K14 | Memories MigrateEmbeddingVectors, all PS14 modes | exempt local tooling, owner-held (D6) |
| K15 | Local session/profile/configuration, stubs, wizards, previews and CLI conventions | withdrawal |

Withdrawal accepts the loss of legacy parser conventions, auto-key generation,
local preview/wizard/configuration, shell completion and wrapper output/exit
dialects. Credentials are never copied from the Admin `profiles.json` store.
K07 documentation ships in packages, README and AI.Tools; resource URIs,
Markdown rendering, resource subscriptions and schema negotiation are not
preserved by an ordinary Query. K08 accepts loss of synthetic `timed_out` and
`needs_review`, in-memory history, expiry/eviction, long-poll and subscription
semantics described in FH01/FV01/H01/V01. Gateway acceptance is not completion;
agents may observe effects through independently decorated module Queries.

ChatBot V10's primary capability is identity/context handoff (K04), not the
legacy observation engine. Resolve the adapter's `TaskId ?? CommandId` handle
versus the server's `OperationId = CommandId` and separate TaskId with the owner
before an included status Query. Preserve `command-accepted`,
`accepted-projection-pending` and audit-reconciling distinctions; acceptance
never proves completion. Positive module Query evidence must prove authenticated
tenant/operation authority, authoritative retry-progress reconciliation and
post-commit audit envelopes through both heads. Negative evidence rejects
wrong-tenant, spoofed/rebound operation or task handles and caller TaskId as
ownership proof, with zero unauthorized reads/effects. Status/audit remain
owner-decorated module Queries; D2/K08 still withdraws the legacy synthetic
engine, polling, long-poll, subscriptions and event streaming.

## Existing v1 admission contract (all seven facets)

These facets apply independently to each of K01–K06, using the versioned
Abstractions contract and released Contracts package at the approved pin.

| Facet | Contract shared by every admitted class |
| --- | --- |
| Versioned declaration | Static versioned `*.Contracts` package, `[HexalithModule]` and `[HexalithCommand]`/`[HexalithQuery]`, exact CLR type, routing, schema, identifier kind and optional declared scope. No plug-ins or dynamic assemblies. |
| Discovery | The immutable Catalog lists canonical operations and schemas through both heads; `describe_operation` reports routing and execution availability. Decoration is owner consent for agent exposure without human confirmation. Restricted operations are never decorated or listed. |
| Execution | `send_command`/`run_query` and CLI `send`/`query` share one executor and the authenticated EventStore Gateway client. Each call submits once; no REST/Dapr calls, post-submit orchestration or retries in McpCli. |
| Error documents | PRD addendum §G shared `OperationError`: `validation_failed`, `unknown_operation`, `unknown_module`, `invalid_arguments`, `read_only`, `gateway_error`, `configuration_invalid`, `catalog_empty`, `catalog_invalid`, `unsupported_transport`, `internal_error`. CLI JSON results/errors use stdout (error exit 2); diagnostics use stderr. MCP uses structured/text documents and protocol binding errors. Gateway/module sanitizes safe details before either head receives them. |
| Authorization class | Both heads are one public `agent` surface under Platform AD-14. Gateway independently authorizes credential, effective surface, tenant/scope, actor and operation. Session, payload, task, caller `confirm: true` and extension values grant no authority. |
| Audit | Bind per-call generated MessageId, supplied/default correlation, caller-only idempotency key, operation, credential-derived actor, tenant/scope and authorized task association at Gateway/module admission. Keep secrets and unauthorized content out of public result documents; authorized Query content remains permitted. Diagnostics, stderr and retained evidence stay free of secrets and content. Acceptance and effect audit remain distinct. |
| Conformance | Pin package, restored closure, exact decorated type, Catalog digest, environment, approved shape vectors and live plans; compare canonical documents and captured Gateway requests across both heads, masking only generated IDs. Exercise admitted success plus denial with zero persisted unauthorized effects, safe errors, release and rollback evidence. Neither names nor static map coverage prove parity. |

| Class | Declaration/execution specialization | Required positive and negative evidence |
| --- | --- | --- |
| K01 | The module owns typed schemas, domain/aggregate/projection routing and handlers. Manifest families are classified per consumer; no host plug-in becomes a McpCli implementation. | Prove actual domain behavior and bounded schemas; reject unknown/duplicate/derivable/invalid fields before effects. FH02/FV04's legacy 32 KiB limit, visible-catalog cap, schema-fingerprint failures/remediation and hidden-tool semantics need explicit preserved behavior or owner-accepted differences in the later inventory. No capped-name match proves executability. |
| K02 | Each data resource becomes its own decorated module Query with its exact authenticated route. No URI/subscription is preserved. Static metadata uses K07 instead. | Prove selection, freshness, redaction, bounded composite/partial results and trustworthy totals; deny cross-tenant/unauthorized reads before access and disclose no content/secrets. No empty success for unavailable data. |
| K03 | Exactly one freshness value per Query, fixed or an explicit Payload property interpreted by its handler; filters are Payload properties; paging uses Envelope only (AD-20). | Prove defaults, supported values, filters before paging and continuation contents; reject conflicting, unsupported and out-of-bound inputs. Payload paging never supplies generic paging. |
| K04 | Task/actor context only in Payload properties, declared `actorProperty`, or explicitly allowed Command extensions (MR4). Queries have no extension bag. ULID-valued inputs use canonical uppercase; opaque String-kind identifiers retain their declared kind. Fresh MessageId and separate caller-only IdempotencyKey remain distinct. | Prove routing, task association, replay/conflict/expiry and caller ownership; refuse lowercase/ambiguous ULIDs, mismatched payload/envelope identity, spoofed authority and silent hash/GUID/task-to-message conversion. |
| K05 | Trusted module admission/handler owns provider authorization, credential references, compound workflow and pre-submit effects; no runtime branch in either McpCli head. | Prove admission before external egress, approved targets, readiness/failure/reconciliation and persisted effects; deny unauthorized/revoked/cross-tenant/replayed/stale-version requests with zero unauthorized state or external effects. Gateway refusal alone cannot prove a pre-submit effect did not happen. |
| K06 | Owner-decorated module diagnostic Command or Query, with explicit scope and bounded safe output; never implicit infrastructure administration. | Prove diagnostics, scheduling versus read semantics and sanitized bounds; deny unauthorized/global-scope access and raw content, secrets or misleading completeness claims. |

Inline content up to the inclusive **262144-byte decoded boundary** is an
ordinary decorated Command Payload, not a new transport class. Derived hash,
byte length, discriminator, media/path metadata and policy validation belong
to the owning Contracts/handler. Larger content is K09.

## Folders handoff and parity evidence

These class assignments leave every current disposition unchanged. Story 5.8
must refresh the pin and apply approved dispositions. The Folders owner and
McpCli verification owner collect the following positive and negative proof.

| Governing rows/class | Affected rows | Positive evidence | Negative evidence |
| --- | --- | --- | --- |
| V04/V05 — K09 | M01/M04 and L24/L25 add/change content; inline content remains ordinary K01 Payload, while the local-file/staging variants remain deferred | At 262144 decoded bytes, prove ordinary typed Payload acceptance, derived schema-v2/hashref/byteLength/PutFileInline validation, NFC path/media metadata, content-policy handling, live persisted effects and metadata-only outputs. A future staging decision must additionally prove lease/disposal/cleanup and staged-object binding. | 262145–1048576 requires unavailable staging; reject rather than silently chunk, read a local path, retry or call REST. Above inclusive 1048576 is nonretryable `file_content_limit_exceeded`, never bypass guidance. Check forged hash/length, unauthorized paths, revoked/cross-tenant input and contentBytes/inlineContent/streamDescriptor absence in result/error/stderr. |
| R01/R02 — K02 | Both resource rows and their underlying module-state reads | Separate decorated Queries preserve authorized module/workspace context, selection, task/lease semantics, bounds, freshness and metadata-only documents. | No resource URI/subscription is recreated; reject wrong tenant/task/lease and unauthorized reads before access. Missing/unavailable projection is not empty success; no content/secret/path disclosure. |
| G6 — record governed by K05 | M03/M05–M07/M09/M11/M49 and matching CLI L01/L03/L06/L07/L14/L16/L27; binding C05, provider/readiness and commit/reconciliation reads | Folders' approved module-side provider authorization, reserved ProviderBindingActorId, tenant/namespace separation, credential references, readiness/failure/reconciliation, actual provider effects and mixed-surface identity. | Reject raw credentials, tenant-as-binding actor, wrong namespace, unauthorized/revoked/cross-tenant/replay and stale inputs before egress. Prove zero external effects and persisted mutation on denial; no NoOp/unavailable/seed substitute. |
| V01/V02 — K03 | All 35 reads, 28 CLI query leaves; provider-support/context/ACL/audit/timeline paging and ACL/audit filters | Exactly one Query freshness value (fixed or explicit Payload), every default and omission rule, Envelope PageSize/Offset/Cursor, filter-before-page totals/continuations and accepted legacy limit mapping. | Unsupported freshness, conflicting payload/envelope paging, invalid bounds/cursor, ignored filters and stale or unauthorized context fail explicitly. `/project` is not a query dispatcher. |
| V03/V07 and G3 — K04 | All mutations, nine task-required reads and optional effective-permissions task context | Keep stable task/workspace identity, String-kind payload IDs, uppercase Envelope ULIDs and independent caller-key replay/conflict/expiry semantics. | No automatic key generation, silent `sha256:`-to-ULID conversion, lowercase compatibility repair, fake task header on get-task-status, task-as-authority or actor spoofing. |
| Restricted K12 | M02/M13, L10/L26, C01/C10, N01/N02 and their destructive variants | Confidential UI admission and human/surface evidence, authorized effects, retention and audit; accepted withdrawal if chosen later. | Both agent heads list none of these restricted operations and cannot submit them, including `confirm: true`; direct and cross-module agent/service-origin calls fail with zero mutation/disclosure. |

V04/V05 remain `defer`, and **EXT-MCPCLI-FOLDERS-RETIREMENT-GATE stays closed**
until a new staging/stream decision is approved or Folders explicitly withdraws
those variants. Inline acceptance alone cannot close it. No legacy Folders
result or mocked/default executor proves live acceptance.

C10 currently combines add/change with destructive removal (M13/L26). Its
roadmap candidate is therefore restricted as a whole. Before admitting inline
add/change, the module must supply an agent-eligible declaration that cannot
also execute the restricted removal variant. No operation-name heuristic or
McpCli payload branch supplies that separation.

## Restricted and exempt evidence

A1–A4 require confidential UI coverage before either Admin head can retire.
Collect authenticated UI admission, actual bounded behavior, tenant/platform
scope, safe audit/output/error/exit semantics and persisted effects. Preserve
AC01 timeout-versus-request timing and AM04–AM06 bounded, truncated,
inconclusive and retention behavior from Story 5.1. Negative proof denies every
remote Admin row through public McpCli, directly and through a cross-module
hop, even with `confirm: true`, a confidential target audience or spoofed
human/tenant headers. Specifically cover AC13/AC20/AC21, AM01/AM03/AM06 and
AM12–AM15 with zero mutation and no protected data. A7's AC25/AC28 and AV02/AV03
destructive overwrite/link-following variants are withdrawn, not copied into
McpCli profiles or an output-file option. AC25–AC31's later withdrawal must
name these accepted losses and prove no automatic credential migration.

K12 includes Parties L03–L05 and T04/T05/T07, which their source inventory
explicitly labels destructive, and C03/C04/C05, whose mixed create/update,
removal and deactivation variants inherit those restrictions. It also includes
Projects' confirmation/destructive maintenance variants, Memories
consistency repair, module erasure/key rotation and adjacent privacy operations.
Collect UI authority/confirmation, exact retention/key-shred/tombstone/WORM,
resumability/concurrency and safe audit/effect proof as applicable; backend
deletion success is not erasure proof. Negative proof covers discovery absence,
submission refusal, direct and chained public/service-origin denial, replay,
spoofed actor/task/tenant and zero unauthorized effects. Unsupported variants
remain absent; this decision invents no operation.

The Parties targets above already have decorated/enrolled Commands. This is an
unresolved conflict between the source inventory's destructive classifications
and this decision's required restriction, not proof of current compliance or
permission to remove them. A separately owner-approved Parties inventory and
exposure reconciliation is required before claiming the restricted discovery
and submission evidence. This story changes neither its enrolled packages nor
the owner-approved 1.2.0 inventory bytes, and does not silently override prior approvals.
The [Story 5.2 reconciliation ledger entry](../../../implementation-artifacts/deferred-work.md#deferred-from-review-of-spec-5-2-decide-generic-non-gateway-capability-contractsmd-2026-11-12)
(`deferred-work.md:1022`) assigns this work to the Parties owning maintainer and
McpCli product/architecture/security owners, with the accepted resolution
reconciled in Story 5.11. Its gate requires an exact-byte owner-approved
inventory/architecture resolution, matching exposure evidence through both
heads, and direct/chained authorization denials with zero unauthorized
persisted effects. Keep the retirement gate until that evidence passes; this
story neither resolves the entry nor authorizes runtime removal.

K13 retains FC01/FC02, PS03, FrontComposer C01/C02 and their compiler variants
as **local tooling only**. Positive evidence preserves explicit build choice,
the no-build freshness limitation, selectors, drift/hash checks, sequential
partial writes with `applied:false`, skipped import-only files/top-level import
warnings, linked/nested-path refusal and current parser/output privacy limits.
Negative evidence proves no agent Catalog/Gateway exposure, no remote module
dispatch and no source write on dry-run or unsafe/drifted targets. FC02's apply
flag is no public-agent confirmation mechanism.

K14 retains PS14's `--dry-run`, `--live`, `--rollback` and `--abort` as named,
owner-held local operator tooling. Positive proof covers mode inventory in
Story 5.10, exact tenant/credential/custody authority, blue/green migration,
rollback/abort transitions and audit. Negative proof covers absent agent
discovery/submission, no writes on dry-run, wrong/missing tenant, unauthorized
operator and live/rollback/abort without owner-held consent; `--yes` never
grants agent authority. Per-user HTTP identity does not make PS14 agent-safe.

The AI.Tools ownership-rule/plan 1.2.0 amendment names both K13 and K14. Until
that amendment is approved and merged upstream they remain frozen census
surfaces; exemption does not change the census baseline here. Exempt retained
tools are never counted as retired, nor templates for new per-module CLIs.

## Deferrals and disposition rules

| Class | Named gap | Owning role |
| --- | --- | --- |
| K09 | A generic authenticated out-of-band staging/stream/file transport with versioned declarations, lifecycle, content/lease/size/cleanup, authority, audit and conformance; requires a Platform AD admitting the surface under AD-14 and an approved PRD change | McpCli product/architecture owner |
| K10 | Approved shared HTTP transport and forwarded per-user authority consistent with AD-14 token exchange, actor/effective-origin attestation, issuer/audience/client mapping, and selected-environment denial evidence; no raw user-token forwarding | McpCli product owner |

Stories 5.7–5.10 apply these rules only after exact-byte AD-23 adoption, in new
owner-approved inventory amendments. Existing approvals retain their limits;
Folders 1.0.0 has no named maintainer, Projects/FrontComposer/ChatBot/Memories
1.0.0 are session-scope only. Parties 1.2.0 is already owner-approved on
2026-11-09: `evidence/story-5-3/approval/amendment-1.2.0.json` binds its exact
`2f359904fe87fab8325b6fc759676c1fc792a27e0857d47631d8eeec8b420a28` hash.
That amendment corrects only the C05 delete pre-read oracles and records the
selected SDK/Gateway conditions; it grants no execution, parity, enrollment or
retirement authority and does not resolve the destructive-label/exposure
conflict above. This decision preserves that approval and its limited scope.

| Outcome | Later disposition and remaining gate |
| --- | --- |
| decorated Gateway contract | `replace` only if the exact decorated type exists at the pin; otherwise `defer` naming module Contracts/handler/admission gaps and module owner. All authorization, behavior and release gates remain. |
| confidential UI only | `withdraw` from the McpCli migration target, with UI coverage evidence before the legacy head retires; this does not remove the confidential UI. |
| exempt local tooling | `withdraw` from migration scope only after the named AI.Tools amendment; retain the tool, never count it as retired. Pending amendment keeps it frozen. |
| withdrawal | `withdraw` with the accepted loss and owner approval recorded per row/variant. |
| continued deferral | `defer` with the class's gap and owner role; retain the compatibility surface and removal gate. |

Every future Admin `replace` additionally lists **G4** as preconditions: fix or
explicitly resolve AV11's route mismatch, AV10's platform-scope/optional-tenant
denials, AC26/AC27/AC30 raw-token/complete-short-token exposure, AV05 invalid-URL
and AV04 base-address disclosure. G4 safety fixes and UI/authorization/effect
proof precede parity; diagnostic fidelity never requires preserving disclosure.
No Admin `replace` is admitted by this decision.

## Provenance and verification

Owner decisions D1–D8 are frozen in the Story 5.2 spec dated 2026-11-12. The
Story 5.1 approved handoff supplies the Admin partition and technical behavior
inputs. Platform AD-11/AD-14 at gitlink 38402bc7 and the Folders approved change
proposal at gitlink 6a8cf4f9 are boundary inputs, not new migration authority.
Full revisions, exact hashes, command results, upstream candidate and pending
approval are retained in `evidence/story-5-2/verification.md` and `approval.json`
under the implementation-artifacts directory.

The stdlib verifier proves complete/unique table-row accounting, known sole
outcomes, hash/version binding, restriction-safe assignment and named deferral
ownership. It does not prove semantic parity, authenticated behavior or owner
approval. Its damaged-input tests exercise each guard. Approval must name all
covered roles under the single-maintainer model and bind exact bytes. While
the separate receipt is pending, effective status and the spine entry remain
**proposed**. A hash-consistent approved receipt changes effective status to
**ADOPTED** without changing the decision or map. This documentary verifier
checks consistency; it does not authenticate a human signature.


## Normative verifier policy

This block is part of the decision's exact approved bytes, independently of
the companion map. Its inventories are the complete expected input set; source
tables, not map counts, determine actual identities. Its classes fix the sole
outcome and deferral ownership. Each inventory also binds every operation
row-to-class assignment in `rowClasses` and its existing `approvalLimit`
string, so restricted outcomes cannot be swapped between classes, staging
cannot become ordinary payload, and session approval cannot claim owner
coverage. `requiredRestrictions` binds inherited/mixed
restrictions even if map-owned evidence is deleted, in addition to affirmative
source security/effect classifications. A row not in `eligibleRecords` must
retain exactly one class. Each eligible record must retain its declared kind,
class or governing references/rule; record prose cannot turn an operation into
bookkeeping. Named source excerpts anchor required restrictions without using
operation-name heuristics in runtime or verifier code.

`requiredApprovalRoles` is the authority coverage the single maintainer must
confirm; a mutable receipt's own required-role list cannot replace it. Its
nonempty array of nonblank strings is required even for a pending candidate. Approval
requires a nonblank approver and exact instruction and an array of nonblank
roles covering this list. The separate receipt binds this decision, its map and
every inventory; both pending and approved receipts must match exact hashes.
No receipt grants execution, enrollment, publication or retirement authority.
The existing upstream candidate remains subject to separate push approval.

<!-- capability-verifier-policy -->
```json
{
  "schemaVersion": "1.0.0",
  "mapPath": "_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-capability-class-map.json",
  "approvalPath": "_bmad-output/implementation-artifacts/evidence/story-5-2/approval.json",
  "requiredApprovalRoles": [
    "McpCli product/architecture owner",
    "McpCli maintainer",
    "McpCli security and contract/transport maintainer",
    "Platform architecture/security and platform/operator maintainer",
    "EventStore owning maintainer",
    "FrontComposer owning maintainer",
    "Projects owning maintainer",
    "Folders owning maintainer",
    "ChatBot owning maintainer",
    "Memories owning maintainer",
    "Parties owning maintainer",
    "AI.Tools owning maintainer"
  ],
  "classes": [
    {"id": "A1", "outcome": "confidential-ui-only"},
    {"id": "A2", "outcome": "confidential-ui-only"},
    {"id": "A3", "outcome": "confidential-ui-only"},
    {"id": "A4", "outcome": "confidential-ui-only"},
    {"id": "A5", "outcome": "withdrawal"},
    {"id": "A6", "outcome": "withdrawal"},
    {"id": "A7", "outcome": "withdrawal"},
    {"id": "A8", "outcome": "withdrawal"},
    {"id": "K01", "outcome": "decorated-gateway-contract"},
    {"id": "K02", "outcome": "decorated-gateway-contract"},
    {"id": "K03", "outcome": "decorated-gateway-contract"},
    {"id": "K04", "outcome": "decorated-gateway-contract"},
    {"id": "K05", "outcome": "decorated-gateway-contract"},
    {"id": "K06", "outcome": "decorated-gateway-contract"},
    {"id": "K07", "outcome": "withdrawal"},
    {"id": "K08", "outcome": "withdrawal"},
    {"id": "K09", "outcome": "continued-deferral", "gap": "Generic authenticated out-of-band staging/stream/file transport; Platform AD and PRD change required.", "ownerRole": "McpCli product/architecture owner"},
    {"id": "K10", "outcome": "continued-deferral", "gap": "Approved shared HTTP transport and forwarded per-user authority under Platform AD-14, with authenticated actor/effective-origin and denial evidence.", "ownerRole": "McpCli product owner"},
    {"id": "K12", "outcome": "confidential-ui-only"},
    {"id": "K13", "outcome": "exempt-local-tooling"},
    {"id": "K14", "outcome": "exempt-local-tooling"},
    {"id": "K15", "outcome": "withdrawal"}
  ],
  "inventories": [
    {
      "path": "_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md",
      "version": "1.0.1",
      "sha256": "7e1beb2fd2c030ca04dbc8d718c0324c7f7f5b66a077f6ef672312d6196fec18",
      "approvalLimit": "Approved owning-maintainer inventory.",
      "rowClasses": {"AC01": "A2", "AC02": "A2", "AC03": "A3", "AC04": "A3", "AC05": "A3", "AC06": "A3", "AC07": "A3", "AC08": "A3", "AC09": "A1", "AC10": "A1", "AC11": "A1", "AC12": "A1", "AC13": "A1", "AC14": "A4", "AC15": "A4", "AC16": "A4", "AC17": "A4", "AC18": "A1", "AC19": "A1", "AC20": "A1", "AC21": "A1", "AC22": "A6", "AC23": "A6", "AC24": "A6", "AC25": "A7", "AC26": "A7", "AC27": "A7", "AC28": "A7", "AC29": "A7", "AC30": "A7", "AC31": "A8", "AM01": "A1", "AM02": "A3", "AM03": "A1", "AM04": "A1", "AM05": "A1", "AM06": "A1", "AM07": "A2", "AM08": "A2", "AM09": "A2", "AM10": "A1", "AM11": "A1", "AM12": "A1", "AM13": "A1", "AM14": "A1", "AM15": "A1", "AM16": "A5", "AM17": "A5", "AM18": "A5", "AM19": "A1", "AM20": "A3", "AM21": "A3", "AM22": "A3", "AM23": "A3", "AM24": "A3", "AM25": "A4", "AM26": "A4", "AM27": "A4", "AM28": "A2", "AV01": "K15", "AV02": "A7", "AV03": "A7", "AV04": "A2", "AV05": "A2", "AV06": "A2", "AV07": "A1", "AV08": "A5", "AV09": "A1", "AV10": "A1", "AV11": "A3", "AV12": "A1"},
      "eligibleRecords": [
        {"id": "AU01", "kind": "unregistered-helper", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AU02", "kind": "unregistered-helper", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AU03", "kind": "unregistered-helper", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AU04", "kind": "unregistered-helper", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AU05", "kind": "unregistered-helper", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AU06", "kind": "unregistered-helper", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AX01", "kind": "scope-accounting", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AX02", "kind": "scope-accounting", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AX03", "kind": "scope-accounting", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AX04", "kind": "scope-accounting", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AX05", "kind": "scope-accounting", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AX06", "kind": "scope-accounting", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AX07", "kind": "scope-accounting", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G1", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G2", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G3", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G4", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G5", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G6", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "AV13", "kind": "verification-note", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md", "id": "AM01"}]}
      ],
      "requiredRestrictions": [
        {"id": "AC01", "sourceText": "UI-only"},
        {"id": "AC02", "sourceText": "UI-only"},
        {"id": "AC03", "sourceText": "UI-only"},
        {"id": "AC04", "sourceText": "UI-only"},
        {"id": "AC05", "sourceText": "UI-only"},
        {"id": "AC06", "sourceText": "UI-only"},
        {"id": "AC07", "sourceText": "UI-only"},
        {"id": "AC08", "sourceText": "UI-only"},
        {"id": "AC09", "sourceText": "UI-only"},
        {"id": "AC10", "sourceText": "UI-only"},
        {"id": "AC11", "sourceText": "UI-only"},
        {"id": "AC12", "sourceText": "UI-only"},
        {"id": "AC13", "sourceText": "destructive"},
        {"id": "AC14", "sourceText": "UI-only"},
        {"id": "AC15", "sourceText": "UI-only"},
        {"id": "AC16", "sourceText": "UI-only"},
        {"id": "AC17", "sourceText": "UI-only"},
        {"id": "AC18", "sourceText": "UI-only"},
        {"id": "AC19", "sourceText": "UI-only"},
        {"id": "AC20", "sourceText": "destructive"},
        {"id": "AC21", "sourceText": "destructive"},
        {"id": "AC25", "sourceText": "destructive"},
        {"id": "AC28", "sourceText": "destructive"},
        {"id": "AM01", "sourceText": "destructive"},
        {"id": "AM02", "sourceText": "UI-only"},
        {"id": "AM03", "sourceText": "UI-only"},
        {"id": "AM04", "sourceText": "UI-only"},
        {"id": "AM05", "sourceText": "UI-only"},
        {"id": "AM06", "sourceText": "UI-only"},
        {"id": "AM07", "sourceText": "UI-only"},
        {"id": "AM08", "sourceText": "UI-only"},
        {"id": "AM09", "sourceText": "UI-only"},
        {"id": "AM10", "sourceText": "UI-only"},
        {"id": "AM11", "sourceText": "UI-only"},
        {"id": "AM12", "sourceText": "UI-only"},
        {"id": "AM13", "sourceText": "destructive"},
        {"id": "AM14", "sourceText": "destructive"},
        {"id": "AM15", "sourceText": "UI-only"},
        {"id": "AM19", "sourceText": "UI-only"},
        {"id": "AM20", "sourceText": "UI-only"},
        {"id": "AM21", "sourceText": "UI-only"},
        {"id": "AM22", "sourceText": "UI-only"},
        {"id": "AM23", "sourceText": "UI-only"},
        {"id": "AM24", "sourceText": "UI-only"},
        {"id": "AM25", "sourceText": "UI-only"},
        {"id": "AM26", "sourceText": "UI-only"},
        {"id": "AM27", "sourceText": "UI-only"},
        {"id": "AM28", "sourceText": "UI-only"},
        {"id": "AV03", "sourceText": "destructive"},
        {"id": "AV07", "sourceText": "confirmation-required"},
        {"id": "AV04", "sourceText": "The CLI client sends a Bearer token when configured, uses a 10-second timeout and the default HttpCl"},
        {"id": "AV05", "sourceText": "The MCP server checks that `EVENTSTORE_ADMIN_URL` is absolute HTTP(S) and that trimmed `EVENTSTORE_A"},
        {"id": "AV06", "sourceText": "MCP tools return indented camelCase JSON strings. The sanitizer replaces raw payload, state, old/new"},
        {"id": "AV09", "sourceText": "Admin.Server policies: `AdminReadOnly` requires the ReadOnly, Operator or Admin role claim; `AdminOp"},
        {"id": "AV10", "sourceText": "Static reading, not executed: the tenant filter denies a request that supplies no canonical granted "},
        {"id": "AV11", "sourceText": "Both heads request `GET api/v1/admin/streams` with query filters, but the controller registers `GET "},
        {"id": "AV12", "sourceText": "The backup service's `TriggerBackupAsync` returns a `Deferred` result and the controller recognizes "},
        {"id": "AV02", "sourceText": "truncates the destination in place"}
      ]
    },
    {
      "path": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md",
      "version": "1.0.2",
      "sha256": "8cca31f2a9fb646566a2cdba3a377af58685d99e4a53ec8e9243135613c1a2f6",
      "approvalLimit": "Approved owning-maintainer inventory.",
      "rowClasses": {"FH01": "K08", "FH02": "K01", "FH03": "K02", "FD01": "K07", "FD02": "K07", "FD03": "K07", "FD04": "K07", "FD05": "K07", "FD06": "K07", "FD07": "K07", "FD08": "K07", "FD09": "K07", "FD10": "K07", "FD11": "K07", "FD12": "K07", "FD13": "K07", "FC01": "K13", "FC02": "K13", "FV01": "K08", "FV02": "K10", "FV03": "K10", "FV04": "K01", "FV05": "K02", "FV06": "K13", "FV07": "K13", "FV08": "K13", "FV09": "K13", "PS14": "K14"},
      "eligibleRecords": [
        {"id": "PS01", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md", "id": "AC01"}]},
        {"id": "PS02", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/eventstore-admin-migration-inventory-v1.md", "id": "AM01"}]},
        {"id": "PS03", "kind": "companion-owned-surface", "classId": "K13"},
        {"id": "PS04", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.md", "id": "H01"}, {"inventory": "_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.md", "id": "H02"}, {"inventory": "_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.md", "id": "H03"}]},
        {"id": "PS05", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md", "id": "L01"}]},
        {"id": "PS06", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/memories-migration-inventory-v1.md", "id": "L01"}]},
        {"id": "PS07", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/memories-migration-inventory-v1.md", "id": "M01"}]},
        {"id": "PS08", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/projects-migration-inventory-v1.md", "id": "L01"}]},
        {"id": "PS09", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/projects-migration-inventory-v1.md", "id": "M01"}]},
        {"id": "PS10", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md", "id": "L01"}]},
        {"id": "PS11", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md", "id": "M01"}]},
        {"id": "PS12", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/chatbot-migration-inventory-v1.md", "id": "L01"}]},
        {"id": "PS13", "kind": "companion-owned-surface", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/chatbot-migration-inventory-v1.md", "id": "M01"}]},
        {"id": "FK01", "kind": "manifest-consumer", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md", "id": "FH02"}, {"inventory": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md", "id": "FH03"}]},
        {"id": "FK02", "kind": "manifest-consumer", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md", "id": "FH02"}, {"inventory": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md", "id": "FH03"}]},
        {"id": "FK03", "kind": "manifest-consumer", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md", "id": "FH02"}, {"inventory": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md", "id": "FH03"}]},
        {"id": "FK04", "kind": "manifest-consumer", "governedBy": [{"inventory": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md", "id": "FH02"}, {"inventory": "_bmad-output/implementation-artifacts/technical-tools-migration-inventory-v1.md", "id": "FH03"}]},
        {"id": "PE01", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PE02", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PE03", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PE04", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PE05", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PE06", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PE07", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PE08", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PE09", "kind": "non-surface-or-existing-exemption", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN01", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN02", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN03", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN04", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN05", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN06", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN07", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN08", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "PN09", "kind": "no-production-surface", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G1", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G2", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G3", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G4", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G5", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."}
      ],
      "requiredRestrictions": [
        {"id": "PS14", "sourceText": "--live"},
        {"id": "FC02", "sourceText": "destructive"},
        {"id": "FV07", "sourceText": "Destructive"}
      ]
    },
    {
      "path": "_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md",
      "version": "1.0.0",
      "sha256": "57cf556b8051921bf2bf8a17abe3b82b7d0a3ba8ba5593072f52c12f85650e0b",
      "approvalLimit": "Session scope only; no new owning-maintainer or readiness approval.",
      "rowClasses": {"M01": "K01", "M02": "K12", "M03": "K05", "M04": "K01", "M05": "K05", "M06": "K05", "M07": "K05", "M08": "K01", "M09": "K05", "M10": "K01", "M11": "K05", "M12": "K01", "M13": "K12", "M14": "K01", "M15": "K01", "M16": "K01", "M17": "K01", "M18": "K06", "M19": "K01", "M20": "K06", "M21": "K01", "M22": "K01", "M23": "K01", "M24": "K06", "M25": "K01", "M26": "K06", "M27": "K01", "M28": "K01", "M29": "K06", "M30": "K01", "M31": "K01", "M32": "K01", "M33": "K01", "M34": "K06", "M35": "K01", "M36": "K01", "M37": "K01", "M38": "K01", "M39": "K01", "M40": "K01", "M41": "K01", "M42": "K01", "M43": "K01", "M44": "K01", "M45": "K01", "M46": "K01", "M47": "K01", "M48": "K01", "M49": "K05", "R01": "K02", "R02": "K02", "L01": "K05", "L02": "K01", "L03": "K05", "L04": "K01", "L05": "K01", "L06": "K05", "L07": "K05", "L08": "K01", "L09": "K01", "L10": "K12", "L11": "K01", "L12": "K01", "L13": "K01", "L14": "K05", "L15": "K01", "L16": "K05", "L17": "K01", "L18": "K01", "L19": "K01", "L20": "K01", "L21": "K01", "L22": "K01", "L23": "K01", "L24": "K01", "L25": "K01", "L26": "K12", "L27": "K05", "L28": "K01", "L29": "K01", "L30": "K01", "L31": "K01", "L32": "K01", "L33": "K01", "L34": "K01", "L35": "K01", "L36": "K01", "L37": "K01", "L38": "K01", "L39": "K01", "L40": "K01", "L41": "K01", "L42": "K01", "V01": "K03", "V02": "K03", "V03": "K04", "V04": "K09", "V05": "K09", "V06": "K01", "V07": "K04", "V08": "K01", "V09": "K15", "V10": "K15"},
      "eligibleRecords": [
        {"id": "C01", "kind": "candidate", "classId": "K12"},
        {"id": "C02", "kind": "candidate", "classId": "K05"},
        {"id": "C03", "kind": "candidate", "classId": "K05"},
        {"id": "C04", "kind": "candidate", "classId": "K05"},
        {"id": "C05", "kind": "candidate", "classId": "K05"},
        {"id": "C06", "kind": "candidate", "classId": "K01"},
        {"id": "C07", "kind": "candidate", "classId": "K05"},
        {"id": "C08", "kind": "candidate", "classId": "K01"},
        {"id": "C09", "kind": "candidate", "classId": "K01"},
        {"id": "C10", "kind": "candidate", "classId": "K12"},
        {"id": "C11", "kind": "candidate", "classId": "K05"},
        {"id": "C12", "kind": "candidate", "classId": "K01"},
        {"id": "C13", "kind": "candidate", "classId": "K01"},
        {"id": "Q01", "kind": "candidate", "classId": "K01"},
        {"id": "Q02", "kind": "candidate", "classId": "K01"},
        {"id": "Q03", "kind": "candidate", "classId": "K01"},
        {"id": "Q04", "kind": "candidate", "classId": "K06"},
        {"id": "Q05", "kind": "candidate", "classId": "K01"},
        {"id": "Q06", "kind": "candidate", "classId": "K06"},
        {"id": "Q07", "kind": "candidate", "classId": "K01"},
        {"id": "Q08", "kind": "candidate", "classId": "K01"},
        {"id": "Q09", "kind": "candidate", "classId": "K01"},
        {"id": "Q10", "kind": "candidate", "classId": "K06"},
        {"id": "Q11", "kind": "candidate", "classId": "K01"},
        {"id": "Q12", "kind": "candidate", "classId": "K06"},
        {"id": "Q13", "kind": "candidate", "classId": "K01"},
        {"id": "Q14", "kind": "candidate", "classId": "K01"},
        {"id": "Q15", "kind": "candidate", "classId": "K06"},
        {"id": "Q16", "kind": "candidate", "classId": "K01"},
        {"id": "Q17", "kind": "candidate", "classId": "K01"},
        {"id": "Q18", "kind": "candidate", "classId": "K01"},
        {"id": "Q19", "kind": "candidate", "classId": "K01"},
        {"id": "Q20", "kind": "candidate", "classId": "K06"},
        {"id": "Q21", "kind": "candidate", "classId": "K01"},
        {"id": "Q22", "kind": "candidate", "classId": "K01"},
        {"id": "Q23", "kind": "candidate", "classId": "K01"},
        {"id": "Q24", "kind": "candidate", "classId": "K01"},
        {"id": "Q25", "kind": "candidate", "classId": "K01"},
        {"id": "Q26", "kind": "candidate", "classId": "K01"},
        {"id": "Q27", "kind": "candidate", "classId": "K01"},
        {"id": "Q28", "kind": "candidate", "classId": "K01"},
        {"id": "Q29", "kind": "candidate", "classId": "K01"},
        {"id": "Q30", "kind": "candidate", "classId": "K01"},
        {"id": "Q31", "kind": "candidate", "classId": "K01"},
        {"id": "Q32", "kind": "candidate", "classId": "K01"},
        {"id": "Q33", "kind": "candidate", "classId": "K01"},
        {"id": "Q34", "kind": "candidate", "classId": "K01"},
        {"id": "Q35", "kind": "candidate", "classId": "K01"},
        {"id": "G1", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G2", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G3", "kind": "prerequisite", "classId": "K04"},
        {"id": "G4", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G5", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G6", "kind": "prerequisite", "classId": "K05"},
        {"id": "N01", "kind": "capability-exclusion", "classId": "K12"},
        {"id": "N02", "kind": "capability-exclusion", "classId": "K12"},
        {"id": "N03", "kind": "capability-exclusion", "classId": "K01"},
        {"id": "N04", "kind": "capability-exclusion", "classId": "K01"}
      ],
      "requiredRestrictions": [
        {"id": "C01", "sourceText": "archive-folder"},
        {"id": "C10", "sourceText": "linked tool/variant rules"},
        {"id": "M02", "sourceText": "Destructive"},
        {"id": "M13", "sourceText": "Destructive"},
        {"id": "L10", "sourceText": "Destructive"},
        {"id": "L26", "sourceText": "Destructive"},
        {"id": "N01", "sourceText": "destructive"},
        {"id": "N02", "sourceText": "Key rotation / deployment credential administration"}
      ]
    },
    {
      "path": "_bmad-output/implementation-artifacts/projects-migration-inventory-v1.md",
      "version": "1.0.0",
      "sha256": "252af571ee3b52163a2f0637a1dff4f0c6f2802ebfa985c51562466fa759ad5f",
      "approvalLimit": "Session scope only; no new owning-maintainer or readiness approval.",
      "rowClasses": {"R01": "K02", "R02": "K02", "R03": "K02", "R04": "K02", "R05": "K07", "R06": "K02", "R07": "K02", "R08": "K02", "R09": "K02", "R10": "K02", "R11": "K07", "M01": "K12", "M02": "K12", "M03": "K12", "M04": "K12", "M05": "K01", "L01": "K01", "L02": "K01", "L03": "K01", "L04": "K01", "L05": "K01", "L06": "K01", "L07": "K01", "L08": "K01", "L09": "K01", "L10": "K01", "L11": "K01", "L12": "K15", "L13": "K15", "L14": "K12", "L15": "K12", "L16": "K12", "L17": "K12", "L18": "K01", "V01": "K03", "V02": "K01", "V03": "K03", "V04": "K15", "V05": "K12", "V06": "K12", "V07": "K08", "V08": "K04", "V09": "K04", "V10": "K12", "V11": "K15", "V12": "K15"},
      "eligibleRecords": [
        {"id": "G1", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G2", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G3", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G4", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G5", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G6", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."}
      ],
      "requiredRestrictions": [
        {"id": "M01", "sourceText": "confirmation"},
        {"id": "M02", "sourceText": "confirmation"},
        {"id": "M03", "sourceText": "confirmation"},
        {"id": "L14", "sourceText": "M01"},
        {"id": "L15", "sourceText": "M02"},
        {"id": "L16", "sourceText": "M03"},
        {"id": "M04", "sourceText": "Destructive"},
        {"id": "L17", "sourceText": "Destructive"},
        {"id": "V05", "sourceText": "CLI mutations require project, correlation and task; non-reevaluate actions also require caller key,"},
        {"id": "V06", "sourceText": "Relink folder/file/memory; unlink conversation/file/memory. File relink requires transient folder/wo"},
        {"id": "V10", "sourceText": "No stream reader, file upload/download/content export, search, erasure or key-rotation operation is "}
      ]
    },
    {
      "path": "_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.md",
      "version": "1.0.0",
      "sha256": "cde0f43ae82376c37411017e88a3b692d0980622833310fecb29f040eb1281a9",
      "approvalLimit": "Session scope only; no new owning-maintainer or readiness approval.",
      "rowClasses": {"H01": "K08", "H02": "K01", "H03": "K02", "D01": "K07", "D02": "K07", "D03": "K07", "D04": "K07", "D05": "K07", "D06": "K07", "D07": "K07", "D08": "K07", "D09": "K07", "D10": "K07", "D11": "K07", "D12": "K07", "D13": "K07", "C01": "K13", "C02": "K13", "V01": "K08", "V02": "K10", "V03": "K10", "V04": "K01", "V05": "K02", "V06": "K13", "V07": "K13", "V08": "K13"},
      "eligibleRecords": [
        {"id": "G1", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G2", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G3", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G4", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."}
      ],
      "requiredRestrictions": [
        {"id": "C02", "sourceText": "Local file mutation"}
      ]
    },
    {
      "path": "_bmad-output/implementation-artifacts/chatbot-migration-inventory-v1.md",
      "version": "1.0.0",
      "sha256": "3dccbe0fb56fe1facb05156d2648d0696d87dfd3a60fe25aacf4969b899ecd94",
      "approvalLimit": "Session scope only; no new owning-maintainer or readiness approval.",
      "rowClasses": {"M01": "K01", "M02": "K01", "M03": "K01", "M04": "K01", "M05": "K01", "M06": "K01", "M07": "K01", "M08": "K01", "M09": "K01", "M10": "K05", "M11": "K01", "M12": "K01", "L01": "K01", "L02": "K01", "L03": "K01", "L04": "K01", "L05": "K01", "L06": "K01", "L07": "K01", "L08": "K01", "L09": "K01", "L10": "K05", "L11": "K01", "L12": "K01", "V01": "K10", "V02": "K10", "V03": "K10", "V04": "K10", "V05": "K04", "V06": "K04", "V07": "K05", "V08": "K05", "V09": "K03", "V10": "K04", "V11": "K01", "V12": "K15", "V13": "K01", "V14": "K12", "V15": "K09"},
      "eligibleRecords": [
        {"id": "G1", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G2", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G3", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G4", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G5", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "X01", "kind": "capability-exclusion", "classId": "K12"},
        {"id": "X02", "kind": "capability-exclusion", "classId": "K12"},
        {"id": "X03", "kind": "capability-exclusion", "classId": "K07"},
        {"id": "X04", "kind": "capability-exclusion", "classId": "K09"}
      ],
      "requiredRestrictions": [
        {"id": "V14", "sourceText": "destructive"},
        {"id": "X01", "sourceText": "Destructive"},
        {"id": "X02", "sourceText": "Key rotation"}
      ]
    },
    {
      "path": "_bmad-output/implementation-artifacts/memories-migration-inventory-v1.md",
      "version": "1.0.0",
      "sha256": "489af91ed49804172e8bd32f3efd98cf1d78fc8a109f23675c67b5ac23f19597",
      "approvalLimit": "Session scope only; no new owning-maintainer or readiness approval.",
      "rowClasses": {"M01": "K01", "M02": "K01", "M03": "K01", "M04": "K01", "L01": "K01", "L02": "K15", "L03": "K01", "L04": "K01", "L05": "K01", "L06": "K15", "L07": "K06", "L08": "K06", "L09": "K06", "L10": "K12", "L11": "K09", "L12": "K09", "L13": "K06", "L14": "K06", "S01": "K15", "S02": "K15", "S03": "K15", "S04": "K15", "V01": "K10", "V02": "K10", "V03": "K10", "V04": "K03", "V05": "K03", "V06": "K01", "V07": "K03", "V08": "K04", "V09": "K12", "V10": "K15", "V11": "K03", "V12": "K09", "V13": "K09", "V14": "K12", "V15": "K12", "V16": "K15", "V17": "K15"},
      "eligibleRecords": [
        {"id": "G1", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G2", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G3", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G4", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G5", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "G6", "kind": "prerequisite", "governingRule": "Scope accounting only; retains the source inventory approval limits and unresolved owner gates."},
        {"id": "X01", "kind": "capability-exclusion", "classId": "K09"},
        {"id": "X02", "kind": "capability-exclusion", "classId": "K12"},
        {"id": "X03", "kind": "capability-exclusion", "classId": "K12"},
        {"id": "X04", "kind": "capability-exclusion", "classId": "K09"},
        {"id": "X05", "kind": "capability-exclusion", "classId": "K01"},
        {"id": "X06", "kind": "capability-exclusion", "classId": "K15"}
      ],
      "requiredRestrictions": [
        {"id": "L10", "sourceText": "Confirmation-required"},
        {"id": "X02", "sourceText": "destructive"},
        {"id": "V09", "sourceText": "L08–L10 receipt, wait and repair consent"},
        {"id": "V14", "sourceText": "Erasure / tenant/case/memory deletion"},
        {"id": "V15", "sourceText": "Key rotation / credentials / encrypted data"},
        {"id": "X03", "sourceText": "Key rotation and credential lifecycle"}
      ]
    },
    {
      "path": "_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md",
      "version": "1.2.0",
      "sha256": "2f359904fe87fab8325b6fc759676c1fc792a27e0857d47631d8eeec8b420a28",
      "approvalLimit": "Owner-approved 1.2.0 on 2026-11-09 under evidence/story-5-3/approval/amendment-1.2.0.json; scope limited to the C05 oracle amendment, no execution, parity or retirement authority.",
      "rowClasses": {"L01": "K01", "L02": "K01", "L03": "K12", "L04": "K12", "L05": "K12", "T01": "K01", "T02": "K01", "T03": "K01", "T04": "K12", "T05": "K12", "T06": "K01", "T07": "K12", "C01": "K01", "C02": "K03", "C03": "K12", "C04": "K12", "C05": "K12", "C06": "K01", "C07": "K04", "C08": "K04"},
      "eligibleRecords": [
        {"id": "N01", "kind": "capability-exclusion", "classId": "K12"},
        {"id": "N02", "kind": "capability-exclusion", "classId": "K12"},
        {"id": "N03", "kind": "capability-exclusion", "classId": "K01"},
        {"id": "N04", "kind": "capability-exclusion", "classId": "K06"}
      ],
      "requiredRestrictions": [
        {"id": "L03", "sourceText": "destructive"},
        {"id": "L04", "sourceText": "destructive"},
        {"id": "L05", "sourceText": "Destructive"},
        {"id": "T04", "sourceText": "destructive"},
        {"id": "T05", "sourceText": "destructive"},
        {"id": "T07", "sourceText": "Destructive"},
        {"id": "N01", "sourceText": "Privacy-destructive"},
        {"id": "C03", "sourceText": "Accept T04's explicit IDs"},
        {"id": "C04", "sourceText": "contact/identifier aliases and removals"},
        {"id": "C05", "sourceText": "DeactivateParty"},
        {"id": "N02", "sourceText": "RotatePartyKey and tenant key rotation APIs"}
      ]
    }
  ]
}
```
<!-- /capability-verifier-policy -->

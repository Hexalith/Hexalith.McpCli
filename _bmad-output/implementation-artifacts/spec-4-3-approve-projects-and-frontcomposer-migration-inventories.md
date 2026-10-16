---
title: '4.3 Approve Projects and FrontComposer migration inventories'
type: 'chore'
created: '2026-10-16'
status: 'draft'
baseline_commit: '228fdaa42e3b50d9c93fb07fe73bd329dc4f0b3c'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The September Projects draft is unapproved and source-stale, and
FrontComposer's framework host has no companion inventory. Neither supports an
agreed completeness or shared retirement decision.

**Approach:** Finalize two linked, versioned, source-pinned inventories outside
`src/`, with explicit dispositions, coverage, rationale, security class, missing
contract/transport prerequisites and actual approval references on every row.
Distinguish framework behavior from Projects business operations and retain one
shared retirement gate.

## Boundaries & Constraints

**Always:** Pin clean Projects revision
`3d256e632a7645bc2261e668ac7c74be81155f58` and FrontComposer revision
`81a440a8890a17edb39924bd0cf676eb6f6b5c25`. Account for Projects' 11 resources,
five tools, 18 CLI spellings and their variants; FrontComposer's lifecycle tool,
13 documentation resources, manifest-defined families and two developer CLI
leaves. Count shared Projects surfaces once.

Record task/actor/tenant authority and direct Gateway guard ownership, strict
payload/wire differences, idempotency migration, resolution/refresh semantics,
redaction, bounds, freshness, local preview and unsupported stream/file/search
variants. Included reads must name exact decorated Query contracts and Gateway
routes. Inventories cannot manufacture readiness from names or context handlers.
Projects remains post-v1 until Contracts is slimmed, published and its restored
closure, Catalog coverage and authorization/behavior gates pass. Keep host and
plug-in nondeletable until both inventories' retirement prerequisites pass.

Record only actual approval, naming its authority and limits. Distinguish a
requesting user's session decision from external owning-maintainer sign-off;
missing owner approval prevents an owner-approved completion claim.

**Never:** Modify runtime, upstream checkouts, enrollment, dependency versions,
publication or retention. Add module-specific adapters, typed tools, dynamic
plug-ins, retries, resources/prompts, stream readers or v1 HTTP identity support.
Weaken canonical uppercase ULID validation, treat payload tenant/actor as trusted
identity, or conflate lifecycle acceptance with committed effects. No migration
execution, withdrawal or early deletion is authorized by preparing an inventory.

</frozen-after-approval>

## Open Questions

1. **Inventory scope and approval basis.** Recommended: accept every current row
   as `defer / exclude`, retain all legacy surfaces, and record your approval as
   the requesting user's session scope decision for both inventories, explicitly
   leaving external owning-maintainer sign-off unasserted. This matches the
   deferred approach in Story 4.2 and exposes no Projects operations. Alternatively,
   provide Projects and FrontComposer owning-maintainer approval references and
   their scope, or request different dispositions. Any intended included subset
   requires a revised candidate with exact decorated contracts, routes and
   readiness evidence; none is currently gateway-ready.

## Code Map

- Projects `src/Hexalith.Projects.Mcp/ProjectsMcpDescriptors.cs:23`,
  `ProjectsMcpResourceReader.cs:33`, `ProjectsMcpCommandService.cs:57` and
  `src/Hexalith.Projects.Cli/ProjectsCliParser.cs:28` / application `:39`
  declare the complete resource/tool/spelling sets and differing variants.
- Projects `src/Hexalith.Projects.Server/EventStoreProjectCommandSubmitter.cs:299`,
  `ProjectsDomainProcessor.cs:43`, `Authorization/ProjectAuthorizationGate.cs:399`
  and `Queries/ProjectQueryEnvelopePrincipalBinding.cs:37` pin context, strict
  payload, REST tenant guards and authenticated query binding. Registration
  `ProjectsServerServiceCollectionExtensions.cs:131`, `:173` has four distinct
  handlers, not eleven-resource parity. Contracts `.csproj` owns slimming.
- FrontComposer `src/Hexalith.FrontComposer.Mcp/FrontComposerMcpServerOptionsConfigurator.cs:27`,
  `Extensions/FrontComposerMcpServiceCollectionExtensions.cs:59`,
  `HttpFrontComposerMcpAgentContextAccessor.cs:79` and `Invocation/` own resource,
  policy, identity, lifecycle and schema behavior. Ordinary corpus metadata under
  `docs/skills/frontcomposer/` supplies 12 document IDs/URIs; provider `:70`
  adds the synthetic manifest. Do not load repository agent skills there.
- FrontComposer `src/Hexalith.FrontComposer.Cli/CliApplication.cs:19` owns
  inspect/migrate; they are compiler tooling, separate from Projects' Frozen CLI.
  All upstream paths above are relative to their root-declared reference checkout.
- Reuse Story 4.2's distinction between candidate approval and execution proof.
  Leave McpCli dependency policy, executor, README and all upstream source intact.

## Tasks & Acceptance

**Execution:**

- [ ] `_bmad-output/implementation-artifacts/projects-migration-inventory-v1.md`
  and `frontcomposer-migration-inventory-v1.md` — finalize the source-checked
  candidates under the actual agreed scope and approval basis; retain explicit
  prerequisites and shared retirement gate.
- [ ] `_bmad-output/implementation-artifacts/evidence/story-4-3/verification.md`
  — preserve repeatable source-set, variant, row, reference and approval checks;
  distinguish static evidence from missing runtime/package/security evidence.
- [ ] `_bmad-output/implementation-artifacts/projects-migration-inventory-draft.md`
  — add a historical/successor notice while preserving the September body.
- [ ] This spec and `sprint-status.yaml` — synchronize status only after the
  applicable approval, implementation, review and verification gates pass.

**Acceptance Criteria:**

- Given both pinned sources, when completeness is checked, then every concrete
  registered legacy surface/spelling has one row, framework families are explicit,
  and Projects operations are not counted twice.
- Given any row, when migration scope is assessed, then disposition, coverage,
  rationale, security class, exact replacement or unresolved prerequisite and
  actual approval basis are explicit; missing approval blocks completion.
- Given context or a behavioral variant, when direct Gateway parity is proposed,
  then payload/actorProperty/allowlisted-extension handoffs, authenticated tenant
  guard ownership and unsupported variants are explicit, without module-specific
  generic runtime changes.
- Given the linked inventories, when retirement is evaluated, then host and
  plug-in remain together until Contracts slimming, approved complete coverage,
  authorization, behavior and release gates pass, including other host consumers.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

- Execute the complete Bash block in `evidence/story-4-3/verification.md`; expect
  exact source pins, surface sets, valid row references and honest pending or
  recorded approval. Pending approval must never be accepted as final readiness.
- Run `git diff --check`; inspect the change list for local Markdown/YAML only.
  Check upstream HEAD/status again. No .NET build applies to this artifact-only
  change; static checks do not prove Gateway or dependency-closure readiness.

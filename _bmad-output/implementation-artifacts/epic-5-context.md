# Epic 5 Context: Migrate and Retire Proprietary Hexalith MCP and CLI Surfaces

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Move every proprietary Hexalith MCP server, plug-in, and CLI to McpCli without losing a supported capability. Every legacy operation gets a current owner-approved `replace`, `withdraw`, or `defer` disposition. Parties, the only Module with gateway-ready `replace` rows and already enrolled, is the one committed retirement. Every non-gateway capability class gets one approved generic decision or an explicit withdrawal. Each surface that cannot retire yet stays a labeled, versioned compatibility binary with a named removal gate. McpCli stays generic and gateway-only until an approved extension changes that, and nothing retires before its authorization, parity, release, and rollback gates pass. After Story 5.1, two independent tracks run: the gateway-ready Parties chain and the non-gateway decision and re-disposition chain. CI census enforcement and a closing reconciliation complete the epic.

## Stories

- Story 5.1: Inventory EventStore Admin and Technical-Tool Operations
- Story 5.2: Decide Generic Non-Gateway Capability Contracts
- Story 5.3: Enroll Replacement Contracts and Profiles
- Story 5.4: Prove Shared-Head Parity and Safety
- Story 5.5: Retire Legacy Packages and Platform Routes
- Story 5.6: Reject New Proprietary Surfaces in CI
- Story 5.7: Re-disposition EventStore Admin and Technical-Tool Inventories
- Story 5.8: Refresh and Re-disposition the Folders Inventory
- Story 5.9: Refresh and Re-disposition Projects and FrontComposer Inventories
- Story 5.10: Refresh and Re-disposition ChatBot and Memories Inventories
- Story 5.11: Reconcile Product Claims and the Migration Plan

The stories were renumbered on 2026-11-08 so that citations in the approved Story 5.1 artifacts still resolve, but some of those citations now point elsewhere. The CI rejection that the technical inventory hands to "Story 5.5" is Story 5.6. The re-pins and PS14 inventory handed to "Story 5.3" are Stories 5.8–5.10. The FV04/FV08 parity clarifications handed to "Story 5.4" apply wherever Story 5.9 re-dispositions a FrontComposer row to `replace`.

## Requirements & Constraints

- **Gates and release.** The entry gate opened on 2026-11-08. The Epic 4 retrospective verdict stays `rejected`, and opening the gate grants no execution, enrollment, or retirement authority. Three open Epic 4 items still bind every evidence, release, or tenant-isolation claim: CI redaction hardening, release-acceptance binding, and refusing non-ASCII tenant input before lowercasing (F7). No McpCli version after 2.0.1 may be published until `epic-3-retro-item-1-complete-output-contract` is done.
- **Inventory rows.** Every row records the legacy operation, `replace`/`withdraw`/`defer`, rationale, security class, the exact replacement contract or a named gap, and the owner's approval reference.
  - `include` appears only with `replace`. `exclude` needs an approved withdraw or defer, and it never means deletion.
  - Each disposition change is a new versioned, owner-approved amendment. Prior versions stay byte-for-byte unchanged, and approvals are hash-chained.
  - Stream and file resources stay tracked gaps, as do the deferred search, filter, order-by, and freshness variants.
- **Approval authority.** Each inventory states its approval authority. Under the single-maintainer model, requesting-user approval is owner authority only when it names the roles it covers. Inventories marked `external_maintainer_approval: unasserted` carry session-scope approval only, and the coverage gate rejects `scope-only` authority.
- **What counts as a replacement.** A candidate counts only once a decorated contract that satisfies the dependency allowlist is named, with its type, exact Gateway route, and eligibility. Plain Commands and REST DTOs do not qualify.
- **Context and identifiers.** Task, actor, and correlation context travel only as Payload properties, through `actorProperty`, or in allowed Envelope extensions. A read that needs context and has no such channel stays `defer`.
  - Envelope correlation and idempotency keys are canonical uppercase ULIDs, and payload identifiers follow the Module's declared Identifier Kind.
  - A legacy format the target cannot accept stays a named gap or becomes an owner-approved change with migration evidence. Never convert it silently and never change McpCli validators to fit it.
- **Restricted operations.** The CLI and MCP heads are one public `agent` surface. UI-only, confirmation-required, and destructive operations never execute through it, and a caller-supplied `confirm: true` proves no human authority. Each such operation goes to a confidential UI, owner-held local tooling, or withdrawal. None may appear in `list_operations` or be submittable.
- **Retirement.** A surface retires only with an owner-approved replacement or withdrawal for every operation, plus authorization, behavior, conformance, release, and rollback evidence on the selected environment.
  - An unrecorded behavior difference blocks retirement. Matching operation names proves nothing.
  - The FrontComposer host and the Projects plug-in retire together, after other host consumers move. The FrontComposer compiler CLI is handled separately.
  - Forwarded per-user identity is necessary but not sufficient for Memories.
  - EventStore Admin also waits for an approved administration contract, destructive-operation safety evidence, and its upstream source fixes (AV10, AV11, token display, URL disclosure).
- **Success measures.** At least one Legacy Server is deleted within three months of v1; if Parties slips, the product owner records why. No new per-module server or CLI appears after 2026-09-21.
- **Committed evidence.** It passes the shared redactor and the secret scan. It binds by hash the exact McpCli candidate, Contracts version, Catalog digest, environment, vectors, and companion live plans.
- **Exit criteria.**
  - Every inventoried operation has a current approved disposition.
  - Parties is retired, or the slip is recorded.
  - CI rejects new proprietary surfaces beyond `src/`.
  - The migration plan is re-versioned.
  - No active module PRD or architecture still plans a proprietary MCP/CLI.

## Technical Decisions

- **Gateway-only boundary.** The gateway-only design and the production dependency allowlist stay binding. Without an approved decision, production `src/` gains none of the following: MCP resources or prompts, stream readers, executor retries, plug-in loaders, module-specific adapters, branches, or error mappings, or new dependencies. The tool never calls a Module's REST or Dapr API.
- **Admitting new capabilities.** To admit anything beyond decorated Commands and Queries to the `agent` surface, two things are needed. A Hexalith.Platform architecture decision under its AD-14 must be merged, and the matching PRD change must be approved through a change proposal. A decision that admits nothing records that no such change is required. Each admitted class defines generic versioned declaration, discovery, execution, error documents, authorization class, audit, and conformance evidence.
- **Gap classes.** These are the gap classes to decide: administration, resource-like reads, diagnostics, lifecycle and status observation, documentation delivery, local compiler/wizard/preview tooling, streamed content and files, query freshness and extensions, idempotency-key format, erasure, and key rotation.
  - Each class gets exactly one outcome: decorated Gateway contract, named generic authenticated transport, exempt local tooling, confidential UI only, withdrawal, or continued deferral with a named gap.
  - Every inventory row maps to exactly one class.
  - No row is re-dispositioned on the strength of a draft decision.
- **Exempt local tooling.** An exemption is published as a versioned amendment to the Hexalith.AI.Tools ownership rule, beside the existing Builds exemptions (`hexalith-module`, `hexalith-evidence`). Until that amendment merges, the surface stays a frozen compatibility source in the census.
- **Enrollment.** These change together under the README enrollment rules: exact version, dependency policy, release inventory, vectors, approval hashes, and companion live plans. The coverage gate and the enrolled-replay gate must pass.
- **Profiles and tenant.** McpCli never reads `~/.eventstore/profiles.json` or the admin CLI's environment. Each profile binds one Gateway URL, one token, and one tenant. A Payload tenant or actor that disagrees with the resolved Envelope fails closed with zero Gateway calls, and the tenant follows the declared-scope and public-tenant rules.
- **Parity and safety evidence.** Loopback runs need equal canonical documents and captured requests from both heads. The live lane runs each vector once and never submits a Command twice just to compare output. Live MCP-head execution is included, or the owner re-accepts the Epic 4 deviation of a CLI-only live lane with loopback parity.
- **Negative cases.** Each of these must fail closed, with the documented error and no mutation:
  - missing or invalid credentials
  - an unauthorized principal
  - a disallowed tenant override
  - a platform scope requested through tenant input
  - the reserved public `system` tenant
  - non-ASCII look-alike tenants
- **Census check.** The baseline is a versioned data file outside `src/`. The check scans every root-declared reference at its gitlink, including paths beyond `src/`, and never initializes nested submodules.
  - Exceptions need an owner, a reason, and an expiry, which code evaluates against the run date.
  - Stale entries are reported, and the baseline changes only through a census amendment.
  - The code contains no module names, paths, or count literals.
  - Each guard has a test that fails when the guard is removed.
- **Generic live-topology runners.** The runners never branch on module names or use fixed vector counts.
- **Migration plan versioning.** Every migration-plan change gets a new `plan_version`, and `inventory_revision` moves when an inventory is re-pinned or added. The root-declared Hexalith.AI.Tools reference must contain the merged revision, and `scripts/check-agent-instructions-sync.sh` must pass.

## UX & Interaction Patterns

- Machine-facing guidance and module MVP gates name the available operations, setup through `hexalith` and the stdio server, and a safe refusal or UI handoff for restricted actions.
- The README documents manual profile setup for operators moving off `eventstore-admin` or `Parties.Mcp`.
- Release notes during Epic 5 separate the gateway-only increment from completed retirements and list the remaining compatibility binaries with their removal gates. They never claim that ecosystem migration is finished.

## Cross-Story Dependencies

- **Story 5.1** supplies the approved inventories (Admin 1.0.1 with 91 rows, technical tools 1.0.2 with 68 rows), the census, and the static gate that the amendments reuse.
- **Gateway track: 5.3 → 5.4 → 5.5.**
  - 5.3 closes Parties gates C06 and C07 and Admin G6, and it may need an upstream Parties Contracts release. It must also account for the open `epic-2-retro-item-1-protect-profile-output` and `epic-2-retro-item-2-anchor-profile-names`, or record why they do not apply.
  - 5.4 stays blocked unless the owner records acceptance of the F7 limitation.
  - 5.5 needs a merged upstream Parties release, and it labels every deferred surface.
- **Non-gateway track: 5.2 → 5.7, 5.8, 5.9, 5.10.** These four stories are independent of each other and of 5.5.
  - Label ordering: if 5.5 has already labeled a surface, an amendment that changes its removal gate updates that label upstream before it counts as complete.
  - Otherwise 5.5 labels the surface from the latest approved inventory version.
- **Story 5.6** depends only on the Story 5.1 census.
- **Story 5.11** depends on 5.2–5.10. It gives `deferred-work.md:143-145` and every intra-epic deferral a recorded disposition: resolved, already tracked, or accepted.
- **Upstream work** belongs to the owning repositories (Parties, EventStore, FrontComposer, Projects, Folders, ChatBot, Memories, Hexalith.AI.Tools, Hexalith.Platform), and `references/` stays read-only here.
- **Out of scope:** the HTTP transport and forwarded per-user identity, which keep Memories and identity-dependent variants blocked.

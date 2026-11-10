# Epic 5 Context: Migrate and Retire Proprietary Hexalith MCP and CLI Surfaces

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Replace every proprietary Hexalith MCP server, plug-in, and CLI with McpCli without losing a supported capability:

- Every legacy operation gets a current owner-approved `replace`, `withdraw`, or `defer` disposition.
- Parties, already enrolled, is the committed first retirement.
- Each non-gateway capability class gets one approved generic decision or a withdrawal.
- Any surface that cannot retire yet stays a labeled, versioned compatibility binary with a named removal gate.

Story 5.12 rebases the enrollment gates on operation shapes. After that, a module can add or release decorated operations without a matching McpCli change; Folders (Epic 6) is the first to rely on this. McpCli stays generic and gateway-only.

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
- Story 5.12: Gate Enrolled Modules by Operation Shape

The Story 5.1 artifacts cite old story numbers. Their "5.5" CI rejection is now 5.6, their "5.3" re-pins are now 5.8–5.10, and their "5.4" FV04/FV08 notes now apply in 5.9.

## Requirements & Constraints

- **Gates.** The Epic 4 verdict stays `rejected`. The opened entry gate grants no execution, enrollment, or retirement authority. Two Epic 4 items stay open and bind every release and tenant-isolation claim: release-acceptance binding, and rejecting non-ASCII tenant input before lowercasing (F7).
- **Inventory rows** record:
  - the legacy operation and its disposition
  - the rationale and security class
  - the exact replacement contract, or a named gap
  - the owner approval, naming the roles it covers

  `include` requires `replace`. `exclude` requires an approved `withdraw` or `defer` and never means deletion. Each change is a new versioned amendment: prior bytes stay unchanged and approvals are hash-chained. A candidate counts as `replace` only once its decorated type exists in source at the pin.
- **Context and identifiers.** Task and actor context travel only in Payload properties, through `actorProperty`, or in allowed Envelope extensions; otherwise the row stays `defer`. Envelope keys are canonical uppercase ULIDs, and payload identifiers follow the Module's Identifier Kind. Legacy formats are never converted silently.
- **Restricted operations.** The CLI and MCP heads are one `agent` surface.
  - UI-only, confirmation-required, and destructive operations never appear in `list_operations` and cannot be submitted.
  - A caller's `confirm: true` proves nothing.
  - Such operations go to a confidential UI, owner-held tooling, or withdrawal.
- **Retirement** requires two things:
  - every operation replaced or withdrawn with owner approval
  - selected-environment evidence for authorization, behavior, conformance, release, and rollback

  An unrecorded behavior difference blocks retirement. FrontComposer and Projects retire together. Per-user identity alone does not unblock Memories. EventStore Admin also needs an admin contract and its G4 upstream fixes.
- **Success measures.** SM-3: at least one Legacy Server is deleted within three months of v1, or the slip is recorded. SM-C1: no new per-module server or CLI is created.
- **Evidence** passes the shared redactor and secret scan. It is hash-bound to the candidate, Contracts version, Catalog digest, environment, vectors, and live plans.

## Technical Decisions

- **Gateway-only boundary.** Without an approved decision, production `src/` gains none of the following:
  - MCP resources or prompts
  - stream readers
  - retries
  - plug-in loaders
  - module-specific branches or error mappings
  - new dependencies

  McpCli never calls a Module's REST or Dapr API, and paging stays in the Envelope.
- **New capability classes.** Admitting anything beyond decorated Commands and Queries needs a merged Platform decision under its AD-14 and an approved PRD change. Each class gets exactly one outcome:
  - a Gateway contract
  - a generic authenticated transport
  - exempt local tooling, recorded as a versioned AI.Tools amendment
  - confidential UI only
  - withdrawal
  - deferral with a named gap

  Every inventory row maps to one class, and no row is re-dispositioned on a draft decision.
- **Operation-shape coverage (AD-16, amended 2026-11-10).** Vectors cover every Operation Shape rather than every operation. A shape is a tuple derived from the Catalog:
  - kind
  - Identifier Kind
  - Wire Type convention
  - tenant source: exact `platformScope`, `fixedTenant`, or public
  - aggregate-id source: property, constant, or none
  - projection selector: `projectionType`, `projectionActorType`, or none
  - whether an idempotency key is required

  The gate fails on an uncovered shape and on a duplicate or stale vector. A vector is stale only if its operation is absent or the Catalog rejects its inputs. The existing 21 vectors should cover six shapes.
- **Vector versions are informational.** A version mismatch is reported, and the vector still runs. `approval.json` binds only the inventory and vector hashes, with no artifact hash. Re-approval is needed only when vector bytes or the inventory change. Package-integrity checks and release validation are unchanged.
- **Inventory gate (AD-21, amended).** The inventory gates retirement, not exposure.
  - Each `include` row appears exactly once, both publicly and internally, with its contract type.
  - `withdraw` and `defer` rows stay absent from the Catalog.
  - Missing, mismatched, duplicate, or unapproved rows fail.
  - A cataloged operation that no row mentions is reported and never fails. This supersedes older wording that failed "extra" rows.
- **Decoration is consent.** Decorating a type is the owner's consent to expose it to agents and operators through the Gateway without human confirmation. UI-only and confirmation-required operations are never decorated. The Gateway still authorizes every call. The rule is documented, not mechanically enforced.
- **Live lane.**
  - Each approved live vector runs once, and no Command is submitted twice to compare output.
  - Each module needs at least one live vector, with a companion plan, for every Operation kind it declares.
  - For new enrollments, the live Command vector creates an aggregate, submits a second Command with a caller-supplied idempotency key, and reads the result back with a Query.
  - Existing Parties and Tenants vectors and plans stay unchanged, with one deferred entry to adopt this pattern.
- **Loopback parity.** For every vector, both heads must produce equal canonical documents and captured requests. Only generated message and correlation IDs are masked. Live MCP-head runs are included, or the owner re-accepts a CLI-only lane.
- **Fail-closed cases** return zero mutations:
  - bad or missing credentials
  - an unauthorized principal
  - a disallowed tenant override
  - a platform scope requested through tenant input
  - the public `system` tenant
  - non-ASCII look-alike tenants
  - a Payload tenant or actor that disagrees with the Envelope

  McpCli never reads the admin `profiles.json`.
- **Census check.** The baseline is versioned data outside `src/`, scanned at each root-declared gitlink without initializing nested submodules. Exceptions need an owner, a reason, and an expiry.
- **Generic gates.** No module names, paths, or counts appear in code, and every guard has a test that fails when the guard is removed.
- **Migration plan.** Every change gets a new `plan_version`. `inventory_revision` moves when an inventory is re-pinned or added.

## UX & Interaction Patterns

- Machine-facing guidance names:
  - the available operations
  - setup through `hexalith` and the stdio server
  - safe refusal or UI handoff for restricted actions
- Release notes separate the gateway-only increment from completed retirements. They list the remaining compatibility binaries and never claim the migration is finished.

## Cross-Story Dependencies

- **5.1** supplies the Admin 1.0.1 and technical-tools 1.0.2 inventories, the census, and the static gate.
- **Parties track: 5.3 → 5.4 → 5.5.** If owner gates G01–G06 keep `Parties.Mcp` from retiring, Folders (Epic 6) may become the first deletion that satisfies SM-3.
- **Non-gateway track: 5.2 → 5.7, 5.8, 5.9, 5.10.** These four are independent of each other.
  - 5.8 also waits on Hexalith.Folders Story 5.12.
  - If an amendment changes a removal gate that 5.5 has already labeled, the upstream label is updated first.
- **5.6** depends only on the 5.1 census.
- **5.12** has no dependencies. Story 6.1 waits on 5.12, 5.2, and 5.8.
- **5.11** depends on 5.2–5.7, 5.9, and 5.10, plus 5.8 once it is done. It records a disposition for every Epic 5 deferral.
- **Out of scope:** upstream work belongs in the owning repositories, and `references/` stays read-only. HTTP transport and forwarded per-user identity are out of scope.

# Epic 5 Context: Migrate and Retire Proprietary Hexalith MCP and CLI Surfaces

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Replace proprietary Hexalith MCP servers, plug-ins and CLIs with McpCli without losing supported access or weakening authorization. Every legacy operation gets a current owner-approved disposition under the adopted capability classes. Parties is the committed first retirement. Surfaces that cannot retire yet stay labeled, versioned compatibility binaries with named removal gates. McpCli stays generic and gateway-only; no catalog or transport extension is admitted.

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

## Requirements & Constraints

- Approved inventories and approvals are immutable. Disposition changes are new versions with hash-chained owner approvals naming covered roles; session-scope approvals support no completeness, enrollment or retirement claim. `include` requires `replace`; `exclude` requires approved `withdraw` or `defer`, never deletion.
- Approval grants only its recorded scope. Retirement also needs selected-environment authorization, behavior, conformance, release and rollback evidence; an unrecorded behavior difference blocks it. A changed removal gate on an already-labeled surface needs the upstream label updated first.
- Both heads are one public agent surface: restricted operations are never decorated, listed or submittable, even with `confirm: true`. Task, actor and payload values grant no authority; context uses Payload properties, `actorProperty` or allowed Command extensions only.
- Evidence passes the shared redactor and secret scan and hash-binds candidate, Contracts, Catalog, environment, vectors and live plans. Open Epic 4 retro items (redaction, release binding, non-ASCII tenant input) stay binding; no release after 2.0.1 until the Epic 3 output-contract item is done.
- One Legacy Server deleted within three months of v1, or the slip recorded. No new proprietary server or CLI, REST/Dapr call, resource, prompt, stream reader, retry, plug-in, module adapter or production dependency.

## Technical Decisions

- **Capability classes (AD-23, adopted by owner receipt; decision bytes frozen).** Every inventory row maps to one class; restricted behavior wins in mixed variants. Remote Admin A1–A4 → confidential UI; local Admin A5–A8 → withdrawal. K01–K06 (ordinary operations, module-state reads replacing resources, Payload freshness/filters with envelope-only paging, context and identifier formats, module-side provider egress, owner-decorated diagnostics) → decorated Gateway contract. K07 documentation and K08 synthetic lifecycle observation → withdrawal; decorated business status Queries stay eligible. K09 staging/streams/files and K10 per-user HTTP authority → deferral. K12 module restricted/destructive/erasure → confidential UI. K13 FrontComposer compiler and K14 Memories vector migration → exempt local tooling (AI.Tools amendment merged), never counted retired.
- **Outcome to disposition:** Gateway contract → `replace` only if the exact decorated type exists at the pin, else `defer`; confidential UI → `withdraw` plus UI evidence before retirement; exempt or withdrawn → `withdraw` with accepted loss; deferral → `defer` with gap and owner. Any Admin `replace` first needs the route, scope-denial, token-exposure and URL-disclosure fixes.
- **Parties conflict:** some destructive-labeled Parties rows are already enrolled; keep the 1.2.0 approval and exposure until a separate owner-approved reconciliation with both-head denial evidence.
- **Folders:** inline content up to 262144 bytes is ordinary Payload; larger content stays `defer` and keeps the retirement gate closed. Mixed eligible/restricted candidates stay restricted until the module splits them.
- **Tenants (AD-22):** exact `PlatformScope`, else `FixedTenant`, else the canonical lowercased public tenant; per-call values must match declarations; overrides need `allowTenantOverride`; public `system` is reserved; disagreeing Payload tenant or actor fails with zero Gateway calls. Envelope ULIDs are canonical uppercase; Payload IDs follow the Module Identifier Kind; no silent conversion; never read the Admin `profiles.json`.
- **Coverage:** the inventory gates retirement, not exposure; uninventoried decorated operations and version differences are reported. Vectors cover each Operation Shape; duplicate or stale vectors fail. Loopback compares both heads' documents and Gateway requests; live runs each vector once, at least one plan-backed vector per kind.
- **Census:** scans every root-declared reference beyond `src/` without nested submodules; exceptions need owner, reason and expiry. Gitlinks moved after adoption; Builds alignment and census reconciliation are a separate change.

## UX & Interaction Patterns

Migration guidance names available operations, `hexalith` stdio setup, and safe refusal or confidential UI handoff. Withdrawals list accepted losses. Release notes separate the gateway increment from completed retirements and list remaining compatibility binaries.

## Cross-Story Dependencies

Story 5.1 supplies inventories, census and the static gate. Adopted 5.2 precedes 5.7–5.10; 5.8 also needs Hexalith.Folders Story 5.12 types at the re-pin. Parties runs 5.3 → 5.4 → 5.5. 5.6 depends on 5.1. 5.12 precedes Epic 6 Folders enrollment. 5.11 follows 5.2–5.7, 5.9 and 5.10, plus 5.8 when done, and records the Parties conflict outcome and deferrals. FrontComposer host and Projects plug-in retire together. Changes land upstream; plan updates use a new `plan_version` and moved `inventory_revision`.

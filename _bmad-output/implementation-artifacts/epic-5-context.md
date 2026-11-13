# Epic 5 Context: Migrate and Retire Proprietary Hexalith MCP and CLI Surfaces

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Replace proprietary Hexalith MCP servers, plug-ins and CLIs without losing supported access or weakening authorization. Every legacy capability needs a current owner-approved replacement, withdrawal or named deferral. Surfaces that cannot retire remain versioned compatibility binaries with explicit removal gates. Parties is the committed first retirement, with Folders a possible first deletion if Parties stays blocked. McpCli remains generic and gateway-only.

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

- Approved inventories and their approval records are immutable. Amendments use new versions and hash-chained approvals naming the owner roles covered. Each legacy operation and variant records its security class, disposition, exact replacement and eligibility or remaining gap, rationale and evidence. `include` requires `replace`; `exclude` requires approved `withdraw` or `defer`. Replacement requires the exact decorated type to exist at the source pin.
- Inventory approval grants only its recorded scope. It never supplies execution, enrollment, publication, parity or retirement authority. Retirement additionally needs selected-environment authorization, behavior, release and rollback evidence; an unrecorded behavior difference blocks it. A changed removal gate requires updating an already-published compatibility label upstream before amendment completion.
- Both heads share the public agent surface. Restricted, destructive, UI-only and confirmation-required capabilities follow confidential UI, owner-held tooling or withdrawal outcomes. Caller confirmation, task context and payload identifiers confer no authority. The adopted decision discloses an unresolved Parties destructive-label/enrollment conflict; preserve existing approvals and exposure until a separate owner-approved reconciliation establishes the resolution.
- Task and actor context use Payload properties, `actorProperty` or allowed Envelope extensions. Envelope identifiers use canonical uppercase ULIDs; Payload identifiers follow the Module declaration. Never silently convert legacy formats or read the Admin credential store. Tenant and scope authority remain independently enforced by the Gateway.
- Evidence passes shared redaction and secret scanning and binds candidate, Contracts, Catalog, environment, vectors and live plans. Open release-acceptance and non-ASCII-before-lowercasing prerequisites remain binding; the Epic 4 retrospective verdict is unchanged. At least one legacy server deletion is due within three months of v1, or the slip is recorded. No new proprietary per-module server or CLI is permitted.

## Technical Decisions

The adopted capability decision admits only existing decorated Gateway Commands and Queries. It adds no transport, REST/Dapr call, resource, stream reader, retry, plug-in, production dependency or module branch. Its immutable proposed-candidate metadata remains historical; the separate exact-byte owner receipt establishes adoption.

- Remote Admin infrastructure administration, diagnostics, stream/state reads and tenant administration go to confidential UI. Local Admin context, unavailable stubs, credentials/profile behavior and shell completion are withdrawn from migration scope. Admin retirement still requires bounded UI behavior and authorization evidence; any future Admin replacement must list route mismatch, scope/tenant denials, token exposure and URL disclosure safety fixes as parity preconditions.
- Ordinary operations, module-state reads, freshness/paging/filter semantics, context, authorized provider effects and owner-decorated diagnostics use Gateway contracts. Paging stays envelope-only. Module code owns provider authorization and effects. Exact handlers, declarations and denial evidence remain prerequisites.
- Legacy documentation/resource delivery and synthetic lifecycle observation are withdrawn, including subscriptions and synthetic timeout/history semantics. An independently decorated business status Query can remain eligible; acceptance never proves completion.
- Staging, streams, local-file transport and imports/exports remain deferred to a generic authenticated transport decision plus Platform and product approval. Forwarded per-user authority remains deferred to the approved shared HTTP design and selected-environment authorization evidence. Neither admits a module-specific fallback.
- FrontComposer compiler tooling and owner-held Memories vector migration are retained local exemptions after the exact AI.Tools amendment merges. That amendment is now merged on AI.Tools main; exemption never means retirement or automatic census reclassification. The census requires its own versioned approval.
- Shape coverage derives from kind, Identifier Kind, Wire Type convention, tenant source, aggregate-id source, projection selector and required caller key. Approved vectors cover each shape; duplicate/stale vectors fail. Version differences and uninventoried decorated operations are reported without failing. Missing/mismatched/duplicate inventory rows and cataloged excluded operations still fail.
- Both heads must produce equal canonical documents and Gateway requests against reset loopback responses, masking generated message/correlation IDs only. Live Commands execute once. Each declared Operation kind needs a plan-backed live vector; new enrollments use a prerequisite aggregate, a second caller-keyed Command and a Query proving persisted effects. Existing approved vectors remain until amended.
- Census policy scans every root-declared reference, including non-source surfaces, without initializing nested submodules. Exceptions need owner, reason and expiry. Generic gates contain no module-specific implementation.

## UX & Interaction Patterns

Migration guidance names available operations, setup through `hexalith` and stdio, and safe refusal or confidential UI handoff. Withdrawal explicitly records accepted losses in parser, output, profile and lifecycle conventions. Release notes distinguish the gateway increment from completed retirements and list remaining compatibility surfaces and gates.

## Cross-Story Dependencies

Story 5.1 supplies inventories, census and the static gate. Story 5.2 adoption precedes independent inventory amendments 5.7–5.10; Folders 5.8 also waits on its upstream Contracts/eligibility work. Parties follows 5.3 → 5.4 → 5.5. Census 5.6 depends on 5.1. Shape coverage 5.12 precedes Folders enrollment in Epic 6. Reconciliation 5.11 records amendment outcomes, remaining gates and every intra-epic deferral, retaining the pending Folders version if necessary. FrontComposer host and Projects plug-in retire together; the compiler CLI has separate treatment. Changes belong to each owning repository; references stay read-only. Migration-plan updates use a new plan version and move the inventory revision when re-pinning or adding inventories.

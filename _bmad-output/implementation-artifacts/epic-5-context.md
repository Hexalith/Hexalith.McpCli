# Epic 5 Context: Migrate and Retire Proprietary Hexalith MCP and CLI Surfaces

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Replace proprietary Hexalith MCP servers, plug-ins, and CLIs with McpCli without losing supported capability or weakening authorization, while hardening credential safety, protocol validation, release binding, and CI verification speed. Every legacy operation carries a current owner-approved disposition under the adopted capability classes; `Parties.Mcp` is the committed first retirement (or any slip past 2027-02-05 is explicitly recorded), and surfaces that cannot yet retire remain labeled compatibility binaries with named removal gates. McpCli stays generic and gateway-only with fast, fail-fast qualification gates.

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
- Story 5.13: Restore the native dependency audit and live CI
- Story 5.14: Restore the proprietary surface census gate
- Story 5.15: Bind paired release acceptance to the published candidates
- Story 5.16: Protect profile credential entry and transport
- Story 5.17: Validate Gateway command acknowledgments
- Story 5.18: Reject non-ASCII public tenant input before normalization
- Story 5.19: Enforce the profile size limit before replacement
- Story 5.20: Detect unsupported Linux process supervision
- Story 5.21: Qualify populated Projects reads and access denial
- Story 5.22: Validate Gateway query paging in both heads
- Story 5.23: Protect profile files from CLI result output
- Story 5.24: Reject invalid default query IDs at catalog admission
- Story 5.25: Fail Fast and Reorder Product CI Gates
- Story 5.26: Remove CI-Script Self-Tests and Cold-Cache Rebuilds from Product CI
- Story 5.27: Reduce Live Vector Plans to Shape/FR-20 Coverage and Optimize Isolated Execution
- Story 5.28: Propose Upstream Hexalith.CiCd Job Split for Parallel Product, Live, and Platform Lanes

## Requirements & Constraints

- **Immutable inventories and retirement gates:** Approved inventories and approvals are immutable; disposition changes require new versions with hash-chained owner approvals naming covered roles. `include` requires `replace`; `exclude` requires approved `withdraw` or `defer`, never silent deletion. Retirement requires selected-environment authorization, behavior/parity, release, and rollback evidence; unrecorded behavior differences block it. At least one legacy server must retire by 2027-02-05 or the slip must be recorded (zero retirements are currently evidenced).
- **Generic gateway-only surface:** Production `src/` must stay strictly module-independent with zero new proprietary servers/CLIs, direct REST/Dapr calls, MCP resources/prompts, stream readers, retries, plug-ins, or unapproved dependencies. Both heads form one public agent surface: restricted, UI-only, destructive, and confirmation-required operations are never decorated, listed, or submittable, even with `confirm: true`.
- **Shape-based coverage and live parity:** Approved vectors must cover every derived Operation Shape and replay identically across both out-of-process heads against a reset loopback Gateway (equal canonical documents and requests after masking generated IDs). Blocking live Aspire tests execute every approved vector carrying a companion live plan once against EventStore, covering every declared Operation kind, distinct Operation Shape, and mandatory module semantic proofs (Tenants audit filters and envelope paging; keyed second-Command plus postcondition-Query scenarios for Command live vectors). Vectors without companion plans stay in loopback parity. Uninventoried decorated operations and package-version differences are reported, never failed.
- **Fast, verifiable CI and supervision:** Blocking product CI verifies product behavior only (excluding CI-script self-tests), reuses verified pre-prepared fixtures and warm caches without weakening package-integrity or dependency-audit checks, and fails fast on infrastructure timeouts, crashed hosts, or repeated vector failures. Candidate qualification requires verifiable dependency advisory data (allowing one fresh isolated restore on confirmed feed rotation), a full green Linux lane across all active live plans plus smoke and boundary cases, and passing Windows and macOS product checks on the same SHA. Timed-out Linux checks must reap owned descendants while preserving unrelated processes, or refuse launch when safe supervision is unavailable.
- **Credential, store, and protocol safety:** Profile creation and token rotation must support non-echoing prompt and opt-in stdin input without leaking tokens to arguments, output, or diagnostics. Bearer tokens require HTTPS or a loopback IP address. Profile mutations enforce the 1,048,576-byte UTF-8 ceiling before atomic replacement, and CLI `--output` refuses collisions with profile, lock, and temp files before mutation or submission. Malformed Gateway command acknowledgments and invalid query paging on 2xx responses return structured `gateway_error` preserving the actual HTTP status after one submission. Invalid Query aggregate defaults are rejected at Catalog admission. Non-ASCII public tenant inputs must fail before lowercasing once upstream EventStore lands the matching check.
- **Evidence, release binding, and workflow ownership:** Evidence passes shared redaction and secret scanning and hash-binds candidate, Contracts, Catalog, environment, vectors, and live plans. Paired release promotion binds both final archives by version, source SHA, and individual digests to exact-commit cross-platform CI and operator acceptance; stable tool promotion stays on hold until Platform, McpCli, and CiCd release owners record the release track. Owned workflow files (`.github/workflows/**`, `.github/hexalith-ci.json`) are never edited locally; pipeline splits go upstream to `Hexalith.CiCd`.

## Technical Decisions

- **Adopted capability classes (decision bytes frozen):** Every inventory row maps to one class (restricted behavior wins in mixed variants). Remote Admin A1–A4 and module restricted/destructive/erasure operations go to confidential UI; local Admin A5–A8, documentation, and synthetic lifecycle observation are withdrawn. Ordinary operations, state reads, Payload filters/freshness with envelope-only paging, allowed context (`actorProperty`, Payload, or allowed Command extensions), module-side egress, and owner-decorated diagnostics use decorated Gateway contracts (`replace` only when the exact type exists at the pin, else `defer`). Staging/streams/files (>262,144-byte inline boundary) and per-user HTTP authority remain deferred with named gaps/owners. FrontComposer compiler and Memories vector migration are exempt local tooling (never counted retired).
- **Module-specific gates:** Enrolled Parties destructive-labeled commands (`create`, `update`, `deactivate`) conflict with restricted classification and require separate owner-approved reconciliation with both-head denial evidence before claiming public eligibility or retirement. Folders inline content ≤262,144 bytes is ordinary Payload; larger/mixed operations remain restricted or deferred. Projects (4 enrolled Queries) requires populated ordered cursor pages, authorized detail reads, and access-denial evidence after settling Payload vs. Envelope paging.
- **Tenant, scope, and identifier resolution:** Tenant resolves from exact declared `PlatformScope`, else Module `FixedTenant`, else canonical lowercased public tenant; per-call values must match declarations ordinally; differing variable-scope overrides require `allowTenantOverride`; public `system` is reserved; disagreeing Payload tenant/actor fails with zero Gateway calls; never read Admin `profiles.json`. Envelope IDs are canonical uppercase ULIDs; Payload IDs follow Module `IdentifierKind` without silent conversion. Ambiguous Query aggregate declarations (`aggregateIdProperty` + `aggregateId`) fail before syntax/kind checks.
- **CI and live-topology architecture:** Companion live plans align to 8 shape- and proof-covering plans — Tenants (`update-tenant`, `get-tenant-audit`, `list-tenants`, `get-tenant`), Parties (`update-party`, `get-party`, `list-parties`), and Projects (`projects.list`) — while retaining all 26 vectors in loopback parity; Tenants and Parties Command live vectors adopt prerequisite-create → keyed second-Command → postcondition-Query. `prepare-ci.sh` pre-prepares and hash-binds SDK catalog owner metadata once for reuse across isolated runs. `run-vectors.py` adds bounded fail-fast (`--max-failures 2`, immediate abort on exit 124 or init failure, marking remaining vectors `skipped-fail-fast` with full acceptance `false`) and bounded parallel isolated `unshare` workers (`--max-workers 2`) or verified clean per-module topology reuse. `AspireTopologyFixture` aborts immediately when any required resource reaches `FailedToStart` or `Exited`. Fast package smoke and `prepare`/`boundary` run ahead of heavier suites; `tools/live-topology` Python self-tests leave blocking product CI (runnable on demand); conformance scripts reuse warm NuGet caches and Release outputs without mutating shared `bin/`/`obj/`.
- **Proprietary surface census:** A generic checker scans every root-declared reference beyond `src/` with nested checkout disabled; unapproved surfaces, stale entries, missing owners, expired exceptions, and scanner errors fail CI. Baseline updates require versioned owner-approved amendments.
- **Gateway response contracts:** Command acknowledgments retain the submitted ID when omitted/null, accept valid canonical Gateway IDs, and treat empty/whitespace/noncanonical IDs on 2xx as `gateway_error` noting possible success. Query paging omits null/absent metadata, requires `pageSize > 0`, nonnegative `offset`/`totalCount`, nonempty `nextCursor`, and boolean `hasMore` (preserving zero counts/offsets and `hasMore: false`), and treats decoding or validation failures on 2xx as `gateway_error`.

## UX & Interaction Patterns

Migration guidance names available operations, `hexalith` stdio setup, private profile credential entry/rotation (`--token-input prompt|stdin`), and safe refusal or confidential UI handoff. Withdrawals list accepted losses. Committed migration status separates the gateway-only increment from evidenced retirements and lists remaining compatibility binaries with removal gates; release-note integration remains an upstream CiCd/Builds deferral.

## Cross-Story Dependencies

- **Inventory and retirement track:** 5.1 supplies inventories, census, and static gate. Adopted 5.2 precedes 5.7–5.10; 5.8 depended on Hexalith.Folders 5.12 types. Parties runs 5.3 → 5.4 → 5.5. 5.6 precedes 5.14. 5.11 reconciles 5.2–5.10 (authoritative `Hexalith.AI.Tools` plan 1.3.0, 65-entry owner-accepted deferral audit, SM-3 pending-not-met due 2027-02-05). 5.12 precedes Epic 6 Folders enrollment. FrontComposer host and Projects plug-in retire together.
- **CI, qualification, and hardening track:** Run 5.25 → 5.26 → 5.27 ahead of or alongside 5.13, 5.14, and 5.21 so candidate qualification uses the fast lane and 5.13 validates against the active 8+2 live set once 5.27 lands. 5.28 proposes the upstream `Hexalith.CiCd` parallel job split without local edits to owned workflows. 5.15 coordinates final archive binding with `Hexalith.CiCd` and Platform release owners. 5.18 waits on upstream EventStore `TenantCanonicalizer`. 5.21 waits on Projects/EventStore paging agreement and qualified host/seed data.

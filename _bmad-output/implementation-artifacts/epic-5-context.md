# Epic 5 Context: Migrate and Retire Proprietary Hexalith MCP and CLI Surfaces

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Replace proprietary Hexalith MCP servers, plug-ins, and CLIs with McpCli without losing supported access or weakening authorization, while hardening credential safety, protocol validation, release binding, and CI speed. Every legacy operation carries an owner-approved disposition; `Parties.Mcp` is the committed first retirement (or any slip past 2027-02-05 is recorded), and unretired surfaces remain labeled compatibility binaries with named removal gates. McpCli stays generic, gateway-only, and fast to qualify.

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

- **Inventories & retirement:** Approved inventories/approvals are immutable; changes use new versions with hash-chained owner approvals naming covered roles. `include` requires `replace`; `exclude` requires approved `withdraw` or `defer`, never silent deletion. Retirement requires selected-environment authorization, parity, release, and rollback evidence; unrecorded behavior differences block it. Delete one legacy server by 2027-02-05 or record the slip (zero retirements evidenced).
- **Gateway-only boundary:** Production `src/` stays module-independent with no new proprietary server/CLI, REST/Dapr call, MCP resource/prompt, stream reader, retry, plug-in, or unapproved dependency. Restricted, UI-only, destructive, and confirmation-required operations are never decorated, listed, or submittable, even with `confirm: true`.
- **Shape coverage & live parity:** Approved vectors cover every derived Operation Shape and match across both out-of-process heads against a reset loopback Gateway (masking only generated IDs). Blocking Aspire tests run every approved companion-plan vector once against EventStore, covering every declared Operation kind, distinct shape, and mandatory module proofs (Tenants audit filters and envelope paging; keyed Command + postcondition Query). Unplanned vectors stay in loopback parity; uninventoried decorated operations and package-version differences are reported, never failed.
- **CI hygiene & qualification:** Blocking product CI checks product behavior only (no CI-script self-tests), reuses verified pre-prepared fixtures and warm caches without weakening integrity or dependency audits, and fails fast on infrastructure, crashed-host, or repeated vector failures. Candidate qualification requires verifiable advisory data (one isolated retry on confirmed feed rotation), a green Linux lane (all active live plans plus smoke/boundary), and passing Windows/macOS checks on the same SHA. Timed-out Linux checks reap owned descendants without harming unrelated processes, or refuse launch when safe supervision is unavailable.
- **Evidence, release & workflow ownership:** Evidence passes shared redaction/secret scanning and hash-binds candidate, Contracts, Catalog, environment, vectors, and live plans. Paired promotion binds both final archives by version, source SHA, and individual digests to exact-commit CI and operator acceptance; stable tool promotion stays on hold until Platform, McpCli, and CiCd owners record the release track. Never edit owned `.github/workflows/**` or `.github/hexalith-ci.json` locally; propose pipeline splits upstream in `Hexalith.CiCd`.

## Technical Decisions

- **Adopted capability classes (bytes frozen):** Every row maps to one class (restricted wins in mixed variants): remote Admin A1–A4 and module restricted/destructive/erasure → confidential UI; local Admin A5–A8, docs, and synthetic lifecycle observation → withdrawal; ordinary operations, state reads, Payload filters/freshness with envelope-only paging, allowed context (`actorProperty`, Payload, or allowed Command extensions), module-side egress, and owner-decorated diagnostics → decorated Gateway contract (`replace` only if the exact type exists at the pin, else `defer`); >262,144-byte staging/streams/files and hosted per-user HTTP authority → deferral; FrontComposer compiler and Memories vector migration → exempt local tooling (never counted retired).
- **Module gates:** Enrolled Parties destructive-labeled commands (`create`, `update`, `deactivate`) conflict with restricted classification and require owner-approved reconciliation plus both-head denial evidence before eligibility/retirement claims. Folders inline content ≤262,144 bytes is ordinary Payload; larger/mixed operations remain restricted or deferred. Projects (4 enrolled Queries) needs populated ordered cursor pages, authorized detail reads, and access-denial evidence after settling Payload vs. Envelope paging.
- **Tenants, scopes & IDs:** Resolve exact `PlatformScope`, else `FixedTenant`, else canonical lowercased public tenant; per-call values match declarations ordinally; variable-scope overrides require `allowTenantOverride`; public `system` is reserved; disagreeing Payload tenant/actor fails with zero Gateway calls; reject non-ASCII public tenant input before lowercasing once EventStore lands the check; never read Admin `profiles.json`. Envelope IDs are canonical uppercase ULIDs; Payload IDs follow `IdentifierKind`. Ambiguous Query aggregate declarations (`aggregateIdProperty` + `aggregateId`) fail before syntax/kind checks at Catalog admission.
- **CI & live-lane optimization:** Trim companion live plans from 22 to 8 — Tenants (`update-tenant`, `get-tenant-audit`, `list-tenants`, `get-tenant`), Parties (`update-party`, `get-party`, `list-parties`), Projects (`projects.list`) — retaining all 26 loopback vectors; Tenants/Parties Command live vectors run create → keyed second Command → postcondition Query. `prepare-ci.sh` pre-prepares and hash-binds SDK catalog owner metadata once for isolated reuse. `run-vectors.py` adds fail-fast (`--max-failures 2`, immediate abort on exit 124/init failure, remainder `skipped-fail-fast`, full acceptance `false`) and bounded parallel `unshare` workers (`--max-workers 2`) or verified clean per-module reuse. `AspireTopologyFixture` aborts on `FailedToStart`/`Exited`. Run fast package smoke and `prepare`/`boundary` ahead of heavier suites; keep `tools/live-topology` Python self-tests on-demand outside product CI; reuse warm NuGet caches and Release outputs without mutating `bin/`/`obj/`.
- **Census, profiles & Gateway responses:** Generic census scans all root-declared references beyond `src/` without nested checkout, failing on unapproved surfaces, stale entries, missing owners, expired exceptions, or scan errors. Profiles support non-echoing `--token-input prompt|stdin` for add/`rotate-token`, require HTTPS or loopback IP for bearer tokens, enforce the 1,048,576-byte UTF-8 ceiling before swap, and refuse CLI `--output` collisions (path/inode/hard-link) with profile/lock/temp files before mutation or Gateway calls. Command acks keep the submitted ID when omitted/null and fail empty/whitespace/noncanonical 2xx IDs as `gateway_error`; Query paging requires `pageSize > 0`, nonnegative `offset`/`totalCount`, nonempty `nextCursor`, and boolean `hasMore`, rejecting invalid 2xx paging as `gateway_error`.

## UX & Interaction Patterns

Migration guidance names available operations, `hexalith` stdio setup, private credential entry/rotation (`--token-input prompt|stdin`), and safe refusal or confidential UI handoff; withdrawals list accepted losses. Migration status separates the gateway increment from evidenced retirements and lists remaining compatibility binaries with removal gates (release-note integration stays deferred to CiCd/Builds).

## Cross-Story Dependencies

- **Migration track:** 5.1 supplies inventories, census, and static gate; 5.2 precedes 5.7–5.10 (5.8 required Hexalith.Folders 5.12 types); Parties runs 5.3 → 5.4 → 5.5; 5.6 precedes 5.14; 5.11 reconciles 5.2–5.10 (`Hexalith.AI.Tools` plan 1.3.0, 65-entry deferral audit, SM-3 pending due 2027-02-05); 5.12 precedes Epic 6 Folders enrollment. FrontComposer host and Projects plug-in retire together.
- **CI & hardening track:** Run 5.25 → 5.26 → 5.27 ahead of or alongside 5.13, 5.14, and 5.21 so qualification runs on the fast lane and 5.13 validates the active 8+2 live set after 5.27. 5.28 proposes the upstream `Hexalith.CiCd` parallel job split without local workflow edits. 5.15 binds paired archives with `Hexalith.CiCd`/Platform owners. 5.18 waits on upstream EventStore `TenantCanonicalizer`. 5.21 waits on Projects/EventStore paging agreement and host/seed data.

# Epic 4 Context: Maintainers Can Verify and Release v1 Coverage

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Prove that approved Tenants and Parties operations work through the generic CLI and MCP server, establish owner-approved migration scope, and publish a validated v1 package pair. Release evidence must cover dependency boundaries, inventory completeness, cross-head parity, live business effects, and the authoritative prohibition on new proprietary module MCP/CLI implementations. Ecosystem retirement belongs to Epic 5; excluded operations do not become automatically deletable.

## Stories

- Story 4.1: Approve the Parties Migration Inventory
- Story 4.2: Approve the Folders Migration Inventory
- Story 4.3: Approve Projects and FrontComposer Migration Inventories
- Story 4.4: Approve ChatBot and Memories Migration Inventories
- Story 4.5: Gate Module Coverage Against the Approved Inventory
- Story 4.6: Publish the Bootstrap Decoration Package
- Story 4.7: Enforce the Production Dependency Boundary
- Story 4.8: Make Tenants Gateway-ready for v1
- Story 4.9: Declare Parties Commands for the Gateway
- Story 4.10: Add Parties Queries and Pin Complete Coverage
- Story 4.11: Prove Both Heads Agree Against a Loopback Gateway
- Story 4.12: Compose the v1 Live Test Topology
- Story 4.13: Test Every Vector Against Live Gateway Semantics
- Story 4.14: Make the Live Semantic Lane Blocking in CI
- Story 4.15: Publish the No-new-server Rule
- Story 4.16: Stage and Validate the Paired Packages
- Story 4.17: Verify the Operator Setup Experience
- Story 4.18: Publish the Validated Package Pair

## Requirements & Constraints

- Version migration inventories outside `src/`. Every legacy tool, resource, or CLI operation needs a `replace`, `withdraw`, or `defer` disposition, rationale, security class, replacement contract or unresolved gap, and owning maintainer approval reference. First-increment `include` requires a gateway-ready `replace` row; `exclude` requires an approved `withdraw` or `defer`. Included rows name the canonical operation and decorated CLR type, including the Query needed for each included read. Explicitly account for erasure, key rotation, resources, and unsupported variants.
- Inventory coverage independently checks canonical names and internal contract types against the built Catalog, exactly once per included operation, with no extra operations or unapproved exclusions. Missing, duplicate, extra, or mismatched rows block readiness. Conformance-vector coverage cannot replace this check. Inventories never become runtime configuration or expose CLR type names publicly.
- Production dependencies admit only the Decoration Package, pinned EventStore client, flagged Contracts packages, and approved stack roots with their exact restored closure. A module cannot add server, handler, aggregate, projection, client, web-framework, or other unapproved dependencies. Projects and Folders remain later additions until compliant.
- Both v1 modules must have approved, exact-version Contracts releases and one approved vector per exposed operation. No release scope fallback substitutes for delayed upstream readiness. Descriptions require review by someone unfamiliar with module source.
- Retiring any legacy surface requires approved replacement or withdrawal, authorization, behavior, and release evidence. Non-gateway capabilities need a separate generic contract/transport decision. Projects and FrontComposer retire together; Memories waits for forwarded per-user identity support in the HTTP release.

## Technical Decisions

- Both heads share one Catalog and executor; enrollment adds package configuration and a rebuild. No module-specific runtime or test setup branches, REST/Dapr calls from the tool, executor retries, typed tools, dynamic plug-ins, or v1 HTTP transport are introduced.
- Parties uses `String` identifiers. Before decoration, its maintainer approves the inventory or an equivalent linked table and records the Command routing decision: retain domain `party`, full-type-name Wire Types, and `PartyId` attribute routing, or adopt `ICommandContract` with an explicit breaking Wire Type migration. Included reads require new Contracts Queries, projection-actor routing where needed, and the existing `parties` list aggregate constant. Tenant comes from the generic Envelope resolution.
- Tenants uses `String` identifiers and fixed tenant `system`, excluding global-administrator Commands. Upstream handlers must honor serialized audit filters and Envelope paging; live vectors must prove filtered records, a non-default page size, and continuation contents. Payload paging cannot govern generic requests.
- Use the approved, versioned vector contract and shared validator. Validate format, fields, package ID/version, and complete operation coverage before execution. Loopback runs both heads separately against reset scripts and compares canonical documents and captured requests, masking only generated message/correlation identifiers. Caller idempotency keys stay unmasked. The live lane executes each vector once and asserts semantic effects without duplicating Commands for parity.
- Live composition requires published EventStore/Tenants helpers, a server-package-free Parties helper, root-declared source checkouts, standard Dapr checks, and a bounded upstream source-build path. CI must run Microsoft.Testing.Platform integration tests as a blocking Aspire gate. Benchmark v1 Catalog construction plus one synthetic module below 500 ms; discovery must remain byte-identical across operating systems.
- Publish dependency-free Abstractions first through its isolated bootstrap gate. Subsequent releases stage exactly Abstractions and the framework-dependent, untrimmed .NET 10 tool at one semantic-release version from a green source SHA. Validate package identities, versions, structure, marked Contracts, isolated tool installation, and offline smoke behavior before publishing staged artifacts.

## UX & Interaction Patterns

Verify README-only setup in Claude Code, Claude Desktop, and VS Code through discovery and an approved cross-module action. Record a timed first successful command against the 15-minute target. Preserve CLI/MCP output-channel contracts and cross-platform installation behavior.

## Cross-Story Dependencies

- Epics 1–3 provide declarations, Catalog, executor, and both heads. Story 1.8's vector contract precedes upstream vector authoring.
- Approved Parties inventory and routing precede decoration; bootstrap Abstractions precedes both modules' decorated releases. Inventory and dependency gates precede coverage claims; both modules' approved vectors precede production parity and live lanes.
- Upstream Contracts, Parties composition helper, Builds source-build/version support, and baseline changes belong in their owning repositories. Paired publication requires the authoritative no-new-server rule merged upstream, the containing root baseline reference, byte-identical local agent entry points, and a passing synchronization check. An open PR is insufficient; bootstrap Abstractions is exempt.

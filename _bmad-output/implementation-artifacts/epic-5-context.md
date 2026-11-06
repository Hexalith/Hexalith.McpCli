# Epic 5 Context: Migrate and Retire Proprietary Hexalith MCP and CLI Surfaces

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Move proprietary Hexalith module MCP servers, plug-ins, and CLIs to approved Hexalith.McpCli replacements or explicit product withdrawals. Preserve supported behavior and authorization through owner-reviewed inventories and selected-environment evidence, then remove obsolete packages and Platform routes. The initial gateway-only release establishes the shared tool; ecosystem retirement is a separate outcome, and unsupported capabilities remain visible migration gaps until their generic contracts and transports are approved.

## Stories

- Story 5.1: Inventory EventStore Admin and Technical-Tool Operations
- Story 5.2: Decide Generic Non-Gateway Capability Contracts
- Story 5.3: Enroll Replacement Contracts and Profiles
- Story 5.4: Prove Shared-Head Parity and Safety
- Story 5.5: Retire Legacy Packages and Platform Routes
- Story 5.6: Reconcile Product and UX Claims

## Requirements & Constraints

Every proprietary Hexalith module MCP server, MCP plug-in, and CLI belongs in the durable migration inventory, including EventStore Admin and technical-module tools. Each supported legacy operation needs a `replace`, `withdraw`, or `defer` disposition, rationale, security class, replacement contract or unresolved gap, and owning maintainer's approval reference. Record current transport and expected behavior so similarly named operations cannot be mistaken for equivalent capabilities. Identify destructive and confirmation-required actions explicitly; inventory approval does not authorize their exposure or execution through McpCli.

Preserve stream and file resources, skill resources, lifecycle calls, migration diagnostics, and deferred search, filter, ordering, and freshness behavior as explicit gaps. A deferred operation keeps the necessary old compatibility binary versioned and clearly labeled with its removal gate. It cannot count as migrated or retired. Existing proprietary implementations are limited to safety and continuity fixes; new Hexalith machine presentation belongs in McpCli.

Gateway-ready inventory rows retain the existing coverage distinction: `include` requires `replace` and the decorated contract type; `exclude` requires an approved withdrawal or deferral with rationale. Canonical operation identity and decorated contract type must match the catalog independently. Missing, duplicate, extra, mismatched, or unapproved rows fail readiness. Inventories remain approval and validation artifacts outside production runtime configuration.

Retirement requires owner-approved replacements or withdrawals for every supported operation, plus selected-environment authorization and behavior evidence. Preserve REST/Dapr semantics, freshness, redaction, task context, actor attribution, paging, token budgets, and idempotency unless the owning product owner approves a specific change. Profiles and credentials bind to one environment; actor spoofing and cross-environment requests fail closed. UI-only and human-confirmation operations remain unavailable through the public McpCli client under Platform's surface-authorization policy.

## Technical Decisions

Maintain one shared catalog and execution core with thin CLI and MCP heads. Add no module-specific runtime branch or adapter. Gateway-ready commands and queries are declared in decorated Contracts packages. Infrastructure administration, resource-like reads, operator diagnostics, and other non-gateway capabilities require a separately approved generic catalog and transport extension covering versioned declaration, discovery, execution, errors, authorization classes, audit, and conformance. Until that decision exists, the first increment's gateway boundary and dependency allowlist remain binding.

Production cannot acquire another module's aggregate, projection, handler, client, or server implementation to obtain coverage. Upstream contract, authorization, and runtime changes belong to their owning repositories. Replacement enrollment binds immutable contract versions, operation identities, eligibility, destinations, and conformance vectors. Both heads must prove equivalent authorized outcomes and stable machine documents, with audit attribution and tenant isolation. Negative evidence must deny disabled, mismatched, UI-only, confirmation-required, and unauthorized operations. Name matching alone proves no parity.

Owner sign-off binds the exact McpCli candidate, Contracts versions, gateway/catalog digest, environment, and test evidence. Live command validation must establish semantic effects without submitting the same state-changing command twice merely to compare head output. Loopback comparison and live semantic acceptance serve distinct purposes.

## UX & Interaction Patterns

Machine-facing guidance must describe available discovery and execution through the `hexalith` CLI and stdio MCP server, including setup, output/error behavior, safe refusal, and confidential UI handoff for restricted actions. Product and architecture documents name Hexalith.McpCli as the target and label historical component names as migration sources. Release notes distinguish the initial gateway-only increment from completed retirements and list remaining compatibility binaries accurately.

## Cross-Story Dependencies

Epic 4's initial release and owner-approved inventory format establish entry context. EventStore and FrontComposer owners review the expanded operation inventory. That inventory and existing module gap rows drive the generic capability decision; non-gateway enrollment waits for that decision and owning-module readiness. Enrolled replacements precede parity evidence, which precedes retirement and reconciliation of product claims.

FrontComposer's MCP host and the Projects plug-in retire together. Memories waits for per-user identity support through the HTTP release. EventStore Admin waits for an approved administration contract and destructive-operation safety evidence. Release packaging, deployment, startup, samples, and operator setup must stop routing retired packages; CI must reject new proprietary module MCP/CLI entries unless an explicit migration exception names its owner and expiry. Final ecosystem acceptance requires approved dispositions for all old operations and verified replacement or withdrawal evidence for every retired surface.

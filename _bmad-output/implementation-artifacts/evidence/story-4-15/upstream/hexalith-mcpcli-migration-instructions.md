---
plan_version: '1.0.0'
inventory_repository: 'https://github.com/Hexalith/Hexalith.McpCli'
inventory_revision: 'c694bff5a29073bee6848b88c142f7da23efcf85'
---

# Hexalith MCP and CLI migration plan

Version **1.0.0** indexes the retained proprietary migration sources under the
[Hexalith MCP and CLI ownership rule](hexalith-llm-instructions.md#hexalith-mcp-and-cli-ownership).
`Hexalith.McpCli` owns the target Hexalith MCP server and CLI for domain,
platform and operator capabilities. Do not create a new proprietary per-module
MCP server, MCP plug-in or CLI. Declare gateway-ready operations in decorated
module Contracts and enroll their approved packages in McpCli. Other capability
classes require a separately approved generic contract and transport decision.
External developer CLIs such as Aspire, Dapr and `dotnet` remain outside this
policy.

## Frozen compatibility implementations

Limit every existing proprietary implementation to safety and continuity fixes.
They remain compatibility surfaces and migration sources, never templates for
new modules. Freezing development does not withdraw capabilities or authorize
removal. The following source-pinned inventories list operations and variants;
this index does not duplicate their tables or change their dispositions.

| Retained implementation | Inventory 1.0.0 and recorded scope | Outstanding migration or retirement condition |
| --- | --- | --- |
| `Hexalith.Parties.Mcp` | [Parties](https://github.com/Hexalith/Hexalith.McpCli/blob/c694bff5a29073bee6848b88c142f7da23efcf85/_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md): five MCP tools, six behavioral variants; no proprietary CLI was found at the inventory pin. | Seven intended target operations are `replace / include`; four adjacent scope families are `defer / exclude`. Scope approval alone establishes neither readiness nor retirement. Preserve privacy, identifier, authorization and behavior gates. |
| `Hexalith.Folders.Mcp`, `Hexalith.Folders.Cli` | [Folders](https://github.com/Hexalith/Hexalith.McpCli/blob/c694bff5a29073bee6848b88c142f7da23efcf85/_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md): 49 tools, two MCP resources and 42 frozen CLI leaves. | All current rows remain `defer / exclude`; the 48 proposed targets are roadmap candidates. Preserve the existing file, resource, provider and authorization behavior until separately approved replacements pass. |
| `Hexalith.Projects.Mcp` plug-in, `Hexalith.Projects.Cli` | [Projects](https://github.com/Hexalith/Hexalith.McpCli/blob/c694bff5a29073bee6848b88c142f7da23efcf85/_bmad-output/implementation-artifacts/projects-migration-inventory-v1.md): 11 resources, five maintenance tools and 18 frozen CLI spellings. | All rows remain `defer / exclude`. Slim decorated Contracts, exact read routes and authorization/behavior evidence remain prerequisites. Coordinate retirement with the FrontComposer host. |
| `Hexalith.FrontComposer.Mcp` host, `Hexalith.FrontComposer.Cli` | [FrontComposer](https://github.com/Hexalith/Hexalith.McpCli/blob/c694bff5a29073bee6848b88c142f7da23efcf85/_bmad-output/implementation-artifacts/frontcomposer-migration-inventory-v1.md): one configurable-name lifecycle tool, 13 framework documentation resources, two local compiler CLI leaves, plus manifest-defined families. | All rows remain `defer / exclude`. Projects operations are counted in their companion inventory. Inventory other manifest consumers and approve generic lifecycle/resource/compiler treatment before the shared host and Projects plug-in retire together. |
| `Hexalith.ChatBot.Mcp`, `Hexalith.ChatBot.Cli` | [ChatBot](https://github.com/Hexalith/Hexalith.McpCli/blob/c694bff5a29073bee6848b88c142f7da23efcf85/_bmad-output/implementation-artifacts/chatbot-migration-inventory-v1.md): 12 MCP tools and 12 frozen CLI leaves. | All rows remain `defer / exclude`. Preserve governed workflows, admission, approval, identity and behavior; plain Commands and REST DTOs do not establish decorated Gateway readiness. |
| `Hexalith.Memories.Mcp`, `Hexalith.Memories.Cli` | [Memories](https://github.com/Hexalith/Hexalith.McpCli/blob/c694bff5a29073bee6848b88c142f7da23efcf85/_bmad-output/implementation-artifacts/memories-migration-inventory-v1.md): four HTTP MCP tools, 14 implemented frozen CLI leaves and four registered stubs. | All rows remain `defer / exclude`. The Legacy Server cannot retire before the later HTTP release supports forwarded per-user identity; exact tenant/user authorization, administrative scope, semantic behavior and release/rollback evidence must also pass. |
| `Hexalith.EventStore.Admin.Mcp`, `Hexalith.EventStore.Admin.Cli` | Successor administration inventory outstanding; no approved operation mapping or completeness claim is supplied by this index. | Retain the existing administration surfaces. The EventStore and platform/operator owners must inventory every operation and approve its replacement, withdrawal or deferral, including destructive and confirmation-required behavior, before any cutover. |

The inventory links bind exact McpCli revision
`c694bff5a29073bee6848b88c142f7da23efcf85`. Each inventory records its own full source
revision, approval reference, security classes, behavior variants, unresolved
gaps and owning roles. These are immutable inventory snapshots rather than
links to a moving branch. A later source change or newly discovered surface
requires a versioned inventory update; absence from this index never authorizes
a new proprietary implementation or deletion of an existing one.

## Approval limits

The six inventories record the requesting user's session scope approvals. They
assert no separate external owning-maintainer sign-off. Preserve those limits:
`replace / include` records intended scope, not proof of published Contracts,
Gateway readiness, authorization, behavior parity or retirement. `defer / exclude`
retains the compatibility capability. No inventory approves withdrawal or early
legacy removal. Missing external owner approval remains an open gate for an
owner-approved completeness or retirement claim.

A future inventory revision must identify every tool, resource, CLI operation
and supported variant with `replace`, `withdraw` or `defer`, a rationale,
security class, exact replacement contract or unresolved gap, and the owning
maintainer's approval reference. An included read needs its decorated Contracts
Query and exact Gateway route. Inventories remain migration/test documentation,
never runtime configuration or authority to expose a deferred operation.

## Successor administration and non-gateway scope

The EventStore Admin successor inventory must cover both administration heads
and identify remaining proprietary technical/domain CLI or MCP packages and
their owning maintainers. Account separately for infrastructure administration,
operator diagnostics, resource/skill-resource reads, lifecycle calls and
FrontComposer `inspect`/`migrate` compiler behavior. The existing FrontComposer
inventory remains authoritative for its recorded rows; it is not approval of
an administration replacement or all other host consumers.

For each non-gateway capability, approve the generic McpCli declaration,
versioning, discovery, execution, errors, authorization, audit, transport and
conformance decision before migration. Call out destructive operations and
human-confirmation requirements explicitly; an inventory row alone grants no
execution permission. Preserve the existing public-client denial of UI-only and
human-confirmation-required operations. Erasure, key rotation, file/stream
transport and unsupported variants retain their inventory gaps and owner gates.
Keep the v1 gateway and dependency boundaries until a separate decision changes
them; do not import module implementations or add module-specific adapters.

## Retirement and release prerequisites

Retire a surface only after its owning maintainer approves an exact replacement
or explicit withdrawal and the selected-environment authorization, behavior,
conformance, release and rollback evidence passes. Preserve existing authority
and behavior while deferred operations or missing owner approvals remain.
FrontComposer and Projects retire together after other host consumers are
accounted for. Forwarded per-user identity in the later HTTP release is a
necessary, insufficient prerequisite for Memories retirement. EventStore Admin
also waits for its approved generic administration contract and destructive
operation safety evidence. This plan authorizes no retirement.

The instruction prerequisite for paired McpCli publication is complete only when
the finished ownership rule and this plan are integrated into authoritative
AI.Tools `main`, the root-declared AI.Tools baseline reference contains that
revision, and local `AGENTS.md`, `CLAUDE.md` and `.github/copilot-instructions.md`
are byte-identical with a passing `scripts/check-agent-instructions-sync.sh`.
Record full integrated revisions, ancestry/containment, hashes and exact check
results in the consuming repository. A local candidate, open PR or baseline
missing the integrated change leaves story completion and paired-release
readiness blocked. This instruction prerequisite leaves dependency, inventory,
loopback, live, package and other release gates independent; it implements no
paired publication. The Abstractions-only bootstrap remains exempt.

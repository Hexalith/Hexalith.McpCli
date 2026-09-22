---
title: "Reference Extract: existing MCP servers, EventStore client, Admin CLI, Contracts"
extracted: 2026-09-21
source: read-only survey of references/* submodules (recorded by the parent from the Explore subagent's report)
---

# Reference Extract

## A. Existing MCP servers (7 found; none in Tenants or Agents)

| Project (references/<repo>/src/) | Transport | Tools | Reaches EventStore how |
|---|---|---|---|
| Hexalith.Parties.Mcp | HTTP (WithHttpTransport, stateless, MapMcp) | 5 | IPartiesCommandClient / IPartiesQueryClient, hand-rolled HTTP to api/v1/commands and api/v1/queries (bypasses IEventStoreGatewayClient) |
| Hexalith.EventStore.Admin.Mcp | stdio | 28 | Own AdminApiClient to the Admin REST API, not the gateway (admin plane, not a replacement target) |
| Hexalith.Folders.Mcp | stdio | 49 (+2 resources) | NSwag client to Folders.Server REST; does not use the gateway |
| Hexalith.ChatBot.Mcp | stdio | 12 | NSwag client to ChatBot REST |
| Hexalith.Memories.Mcp | HTTP /mcp + JWT | 4 | Dapr service invocation |
| Hexalith.Projects.Mcp | library, no Program.cs, hosted via FrontComposer | 5 commands + 11 resources (runtime McpCommandDescriptor records) | NSwag IClient to Projects REST |
| Hexalith.FrontComposer.Mcp | library, generic descriptor-driven host | n/a | n/a |

Tool declaration: [McpServerToolType]/[McpServerTool] + [Description] everywhere except Projects and FrontComposer (runtime descriptor records).
Tool naming is inconsistent: get_party (snake), stream-list (kebab), chatbot.association.status (dotted).

## B. EventStore client envelopes and contracts (exact field names)

- CommandEnvelope: MessageId, TenantId, Domain, AggregateId, CommandType, Payload (byte[]), CorrelationId, CausationId, UserId, Extensions.
- SubmitCommandRequest: MessageId, Tenant, Domain, AggregateId, CommandType, Payload (JsonElement), CorrelationId?, Extensions?, IdempotencyKey?.
- QueryEnvelope: TenantId, Domain, AggregateId, QueryType, Payload, CorrelationId, UserId, EntityId, IsGlobalAdmin, Paging, OriginalActorId, AuthenticatedWorkloadId, IsDelegated, Scopes, Audience, DelegationId.
- Paging: QueryPagingOptions(PageSize, Offset, Cursor) -> QueryPagingMetadata(PageSize, Offset, NextCursor, TotalCount, HasMore).
- ICommandContract: static CommandType, static Domain, instance AggregateId. IQueryContract: static QueryType, Domain, ProjectionType.
- Errors: EventStoreGatewayException with StatusCode, Title, Type, Detail, CorrelationId, TenantId, Errors, Reason, ReasonCode, RetryAfter, Code, Category, Retryable, ClientAction, Extensions; plus QueryProblemReasonCodes.

## C. Admin CLI shape (Hexalith.EventStore.Admin.Cli)

- Subcommands: health (dapr), stream, projection, tenant, snapshot, backup (stubs), config (profile / use / current / completion).
- Global recursive options: --url/-u, --token/-t, --format/-f (json|csv|table), --output/-o, --profile/-p.
- Precedence: CLI flag > environment > profile > default.
- Environment: EVENTSTORE_ADMIN_URL (default http://localhost:5002), EVENTSTORE_ADMIN_TOKEN, EVENTSTORE_ADMIN_FORMAT.
- Profiles: ~/.eventstore/profiles.json = { version: 1, activeProfile, profiles: { name: { url, token, format } } }.
- Exit codes: 0 Success, 1 Degraded, 2 Error.

## D. Contracts libraries of the four v1 modules

- Zero [Description] attributes anywhere in Tenants, Parties, Projects, Folders contracts.
- Tenants: the only module implementing ICommandContract / IQueryContract (CreateTenant, UpdateTenant, AddUserToTenant, DisableTenant, SetTenantConfiguration; GetTenantQuery, GetTenantUsersQuery, GetUserTenantsQuery, GetTenantAuditQuery, GetGlobalAdministratorsQuery), also [RestRoute].
- Parties: plain records with no routing interface (CreateParty, AddContactChannel, AddIdentifier, UpdatePersonDetails, EraseParty).
- Projects: its own IProjectCommand (TenantId, ProjectId, ActorPrincipalId, CorrelationId, TaskId, IdempotencyKey, CommandType).
- Folders.Contracts: no command or query records at all; OpenAPI YAML only.
- CommandType is not uniform: Tenants kebab-case (create-tenant); Parties typeof(T).FullName; Projects nameof(CreateProject). Domain: "tenants" vs "party".

## E. Header-forwarding handler (Hexalith.Parties.Mcp/McpContextForwardingHandler.cs)

Forwards Authorization (only if absent), X-Tenant-Id, X-User-Id. Sources: claims tenant_id / tid; NameIdentifier / sub / preferred_username; fallback headers X-Tenant-Id / X-Tenant / X-User-Id / X-User.

## F. Surprises that contradict "one generic server via the EventStore client"

1. Only one of seven servers (Parties) reaches the EventStore gateway, and it bypasses IEventStoreGatewayClient.
2. Folders, Projects, ChatBot, Memories are fronted by per-module REST or Dapr APIs with module-specific semantics (task scoping, freshness modes, dry-run plus IdempotencyKey gates, redaction) that a generic gateway call does not reproduce.
3. CommandType and Domain naming differ per module (see D).
4. Four or five sibling CLIs already exist (Folders, Projects, ChatBot, FrontComposer, Memories) with divergent global options (--base-address, --correlation-id) and exit-code enums.

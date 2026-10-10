# Epic 3 Context: Agents Can Use One Generic MCP Server

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

An MCP-capable agent can discover and execute every available Operation through one stable, generic tool set over stdio. The server carries the same Catalog, result documents, and execution rules as the CLI, so an agent can work across Modules without Module-specific tools or prompts. A Read-only session advertises only safe tools.

## Stories

- Story 3.1: Discover Operations Through a Fixed MCP Surface
- Story 3.2: Run the MCP Server over Clean Stdio
- Story 3.3: Execute Calls with Structured MCP Results

## Requirements & Constraints

- Advertise `list_modules`, `list_operations`, `describe_operation`, `send_command`, and `run_query` in that fixed order. In Read-only Mode, omit `send_command` and retain the other four in order; the shared executor must also refuse a direct write. Catalog growth never creates another MCP tool. Tool descriptions have labeled `Purpose`, `Use when`, and `Next` parts. The five names, descriptions, and input schemas together stay below 8,000 characters; measure output schemas separately.
- Discovery returns Module descriptions and Operation counts; filtered Operation names, kinds, and descriptions; and an Operation's Schema, optional example, Envelope arguments, lint findings, and `submittable` state. Discovery and server startup work without a Gateway URL. A missing URL makes execution unavailable; Read-only Mode takes precedence for writes. A nonempty unknown Module returns `unknown_module` with up to three suggestions. Missing or empty `module` fails MCP input binding before Catalog dispatch.
- MCP call arguments follow the shared call model: `module` and optional `kind` for listing; `operation` for description and execution; `payload` and optional Envelope arguments for execution. Only the MCP head accepts a per-call `tenant`, subject to the Core operator gate. `send_command` accepts correlation, idempotency, and extensions; `run_query` accepts entity identity and paging. The head must preserve Core's kind, validation, Tenant, and Read-only decisions.
- Success `structuredContent` uses the canonical Core document: Command identity, Tenant, aggregate, accepted status, and only returned optional fields; Query Operation, Tenant, document even when JSON null, and only returned paging. Discovery documents keep required fields present, optional fields omitted when absent, and empty arrays as arrays. A Core failure returns `isError: true`, `{ "error": ... }` in `structuredContent`, and matching JSON in the first text content item. No exception escapes the tool boundary. MCP input-schema failures use protocol invalid-parameters errors.
- `hexalith mcp --transport stdio` starts without a prompt, after one settings resolution and Catalog build. Stdout contains only JSON-RPC; logging and diagnostics go to stderr. Before request serving, malformed settings, an empty Catalog, or strict Catalog diagnostics produce exactly one structured stderr error, exit 2, and zero stdout bytes. Once serving, call failures travel through MCP only. Explicit `--format table` or any `--output` fails before Catalog or transport startup; explicit `--format json` and valid inherited format settings do not affect protocol output.

## Technical Decisions

- The MCP head binds input and carries output; Core owns the immutable Catalog, availability, argument records, validation, executor, and result serializer. The head reads the single resolved settings value from dependency injection. Only the executable references Module Contracts packages.
- Construct runtime tools with the pinned MCP SDK's `McpServerTool.Create`, structured content enabled, and canonical result serializer. Register one Read-only-filtered `ToolCollection`. Use SDK built-in call dispatch and a post-handler list filter to enforce the fixed advertisement order and reject duplicate or unexpected names. Tool annotations mark discovery and Query as read-only; Command as non-read-only, non-idempotent, and destructive.
- Each advertised output schema has an object root and closed `oneOf` branches for its exact success document and `{ "error": ... }`. Validate both branches against actual structured results under a pre-2026-07-28 protocol revision and the 2026-07-28 revision. Exercise both the legacy initialization flow and the newer discovery flow through SDK clients.
- Run the SDK stdio transport with logging providers directed to stderr. Keep configuration and Catalog failure checks before the server can serve requests; do not emit a second stderr error for a failed call.

## UX & Interaction Patterns

An agent lists Modules, narrows Operations by Module and kind, describes an Operation to inspect its Schema and Envelope, then executes it. Tool descriptions guide this sequence. `submittable` explains only session availability; Tenant, Actor, Payload, and per-call Envelope requirements are checked when the agent executes.

## Cross-Story Dependencies

Epic 3 consumes Epic 1's Catalog and Schemas and Epic 2's settings, executor, availability, and canonical documents. Tool registration and schemas from Story 3.1 support the stdio session in Story 3.2 and structured calls in Story 3.3; the stdio client checks confirm their behavior together. Epic 2 owns the CLI `mcp` verb and unsupported HTTP response; this epic supplies its stdio server.

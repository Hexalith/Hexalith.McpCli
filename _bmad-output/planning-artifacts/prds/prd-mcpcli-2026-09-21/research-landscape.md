# Research landscape: generic catalog-driven MCP servers + CLI (2026)

Date: 2026-09-21. Scope per brief: `_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/`.

## 1. Products/projects exposing a catalog through generic ("meta") MCP tools

The dominant pattern in 2026 is: a small, fixed set of discovery tools (search/list/describe)
plus one or a few generic invoke/execute tools, instead of one MCP tool per backend operation.
Tool counts cluster around 4-6.

- **mcp-openapix** (alyiox) — fronts any OpenAPI service behind **4 generic tools**:
  discovery (list platforms/endpoints, describe endpoint) plus a generic proxy `call_endpoint`
  that resolves the URL, obtains a bearer token, and builds the request.
  https://glama.ai/mcp/servers/alyiox/mcp-openapix
- **Apify "OpenAPI Agent Tool Catalog"** — an MCP server that inverts the typical model:
  ~63 operations behind **5 tools** — one to search the catalog, one to return an operation's
  full schema/contract, and (a small number, ~3) to invoke. Agents browse a catalog of OpenAPI
  specs, search operations, and retrieve full operation contracts before calling.
  https://apify.com/q_services/openapi-agent-tool-catalog/api/mcp
- **ProdByBuddha/openapi-mcp-server** — "Universal OpenAPI → MCP tool generator."
  https://github.com/prodbybuddha/openapi-mcp-server
- **Tyk "API to MCP"** — natural-language interaction with existing APIs via MCP gateway.
  https://tyk.io/docs/ai-management/mcps/api-to-mcp
- **AWS Labs `openapi-mcp-server`** — reference OpenAPI-to-MCP server.
  https://awslabs.github.io/mcp/servers/openapi-mcp-server
- **IBM `mcp-context-forge` — proposed "virtual meta-server"** (issue #2230, open as of
  research date): exposes exactly **6 meta-tools** — `search_tools` (semantic/NL search with
  tag/server/category/confidence filters), `list_tools` (paginated browse), `describe_tool`
  (full schema/examples/usage metrics), `execute_tool` (routes/executes the underlying tool),
  `get_tool_categories`, `get_similar_tools` (embedding similarity). Explicit rationale:
  agents can't handle 1000+ tool definitions; the meta-server hides the real tools entirely
  and enforces access control at the meta layer.
  https://github.com/IBM/mcp-context-forge/issues/2230
- **MetaMCP** (metatool-ai) — MCP aggregator/orchestrator/middleware/gateway that routes
  across many underlying MCP servers ("routing meta tools").
  https://github.com/metatool-ai/metamcp and
  https://github.com/metatool-ai/mcp-server-metamcp
- **OpenShapeForge** discussion — pattern of "a fixed searchable discovery tool plus one
  canonical execute-by-ID tool" for large/dynamic operation catalogs, to avoid pushing
  `tools/list` over client limits; discovery is session-filtered, paginated, returns exact
  canonical schemas + execution metadata.
  https://github.com/OpenShapeForge/OpenShapeForge/issues/543
- **CAST Imaging MCP Server 3.1 "Meta Tool mode"** — lets a client work through a small
  set of general-purpose tools instead of ~50 individual ones.
  https://doc.castsoftware.com/imaging/mcp-server/imaging/3.1/meta-tool/
- Naming convention across these: verbs like `search_tools` / `list_tools` / `describe_tool`
  (or `describe_endpoint`) / `execute_tool` (or `call_endpoint`) recur; Credal's taxonomy
  groups them as **discovery**, **routing**, and **chaining** meta-tools.
  https://credal.ai/blog/meta-tools-in-mcp-why-are-they-important

## 2. Trade-offs: one-tool-per-operation vs. few generic tools + describe step

**Context/token cost.** Practitioner reports place the "MCP tax" (eager JSON-Schema injection
of every tool into every turn) at roughly 10k-60k tokens in multi-server deployments, degrading
reasoning as context utilization approaches ~70%. Anthropic's own tool-search data (cited via
Credal): trimming the exposed tool set cut context usage ~85% (77k → 8.7k tokens) and raised
Claude Opus 4.5 tool-selection accuracy from 79.5% to 88.1%.
https://credal.ai/blog/meta-tools-in-mcp-why-are-they-important

**Research consensus (2026).** Static "all tools always in context" (per-operation) doesn't
scale past ~128 tools (a hard limit many providers enforce) and causes reasoning degradation;
pure generic/meta-tool designs add indirection, latency, and new attack surface (tool poisoning,
confused-deputy risk via the execute-by-name indirection). The emerging middle ground is
**dynamic/lazy tool gating**: keep a compact summary pool in context, promote full schemas only
for the top-k relevant tools per turn. "Tool Attention" (arXiv:2604.21816) reports 95% reduction
in per-turn tool tokens (47.3k → 2.4k) and context utilization up from 24% to 91% with this
approach. Related: MCP-Zero (arXiv:2506.01056, active tool discovery), ScaleMCP
(arXiv:2505.06416, dynamic/auto-syncing tools), "Looking Is Not Picking" (arXiv:2606.16364,
tool-selection failure modes).
https://arxiv.org/pdf/2604.21816 · https://arxiv.org/abs/2604.21816 ·
https://arxiv.org/pdf/2506.01056 · https://arxiv.org/pdf/2505.06416 · https://arxiv.org/pdf/2606.16364

**When each wins (Credal's framing, matches general community view):** discovery meta-tools
pay off when the catalog is large and dynamic (this is mcpcli's exact situation — catalog
discovered from decorated Contracts assemblies at build/run time); routing meta-tools only
help when multiple servers expose overlapping capabilities (not mcpcli's case — one server,
one gateway); chaining meta-tools help for multi-step dependent workflows. Meta-tools are
explicitly called "unnecessary complexity" when the tool count is small/static — i.e. don't
add a describe step for a 5-operation catalog.

**MCP spec's own guidance relevant here (2026-07-28 spec):**
- **Tool annotations**: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`
  (all optional booleans on the `annotations` object). Purpose: let clients skip confirmation
  for trusted read-only tools, warn before destructive ops, allow safe retries on idempotent
  tools, and scrutinize output from open-world tools. **Explicit spec warning: clients MUST
  treat annotations as untrusted unless from a trusted server — "an untrusted server can lie"
  about them.** Real enforcement needs network/sandboxing/authz layers, not metadata.
  https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/
- **Structured output**: tools may declare an `outputSchema`; servers MUST conform,
  clients SHOULD validate; result carries `structuredContent` (JSON) alongside a
  backward-compatible serialized-JSON `TextContent` block. Directly relevant to a
  `describe`/`invoke` pair: the generic invoke tool's *output* schema is necessarily generic
  (arbitrary JSON) unless per-operation output schemas are surfaced via the describe step.
- **Tool list changes**: servers declare `tools: { listChanged: true }` capability and send
  `notifications/tools/list_changed` over a `subscriptions/listen` stream; `tools/list` itself
  supports pagination and a `cacheScope`/`ttlMs` cache hint, and servers SHOULD return tools in
  **deterministic order** to preserve prompt-cache hits. Relevant if mcpcli ever exposes the
  catalog as real per-operation tools rather than a generic invoke — a per-operation approach
  would need to fire this notification whenever a new Contracts assembly is added; a
  generic-tools approach avoids this entirely since the tool surface never changes, only the
  catalog data returned by `describe`/`list` does.
- **Stateful tools guidance** (non-normative): MCP has no protocol-level session; multi-step
  state (e.g. correlation across command→result) should be carried via an explicit opaque
  handle argument, not implicit connection state — relevant to mcpcli's per-call message ID /
  idempotency key / optional correlation ID design.
  https://modelcontextprotocol.io/specification/2026-07-28/server/tools

## 3. Generate both a CLI and an MCP server from one catalog/schema

- **Speakeasy** — generates a full TypeScript MCP server (one tool per endpoint, Zod-validated)
  and a CLI, both from one OpenAPI document; `operationId` becomes the tool/command name.
  The `x-speakeasy-mcp` OpenAPI extension customizes tool names/descriptions/scopes.
  CLI generation: https://www.speakeasy.com/docs/cli-generation/create-cli
  MCP-from-OpenAPI guide (benefits/limits/best practices):
  https://www.speakeasy.com/mcp/tool-design/generate-mcp-tools-from-openapi
  General MCP generation: https://www.speakeasy.com/blog/generate-mcp-from-openapi
- **Stainless** — from one OpenAPI spec + one config file generates SDKs (incl. Kotlin, unique
  to Stainless), docs, **CLI tools**, Terraform providers, and **MCP servers**. Its MCP server
  uses a "code tool" architecture and ships as a separate npm package alongside the TS SDK to
  minimize bundle size.
  https://www.stainless.com/docs/mcp/ · https://www.stainless.com/blog/generate-mcp-servers-from-openapi-specs/
- **Head-to-head comparison** (Speakeasy vs Stainless vs Postman, MCP generation):
  https://www.speakeasy.com/blog/comparison-mcp-server-generators ·
  https://www.stainless.com/docs/compare/speakeasy/
- Direct architectural analog for mcpcli: both tools treat **one schema as the single source
  of truth** feeding multiple surfaces (SDK/CLI/MCP), matching mcpcli's own "catalog discovered
  from Contracts assemblies feeds both the CLI and the MCP server" design — but note both
  Speakeasy and Stainless default to **one-tool-per-operation** MCP generation, not the
  generic list/describe/invoke pattern in section 1; mcpcli's meta-tool approach is closer to
  the Apify/mcp-openapix/mcp-context-forge camp than to the SDK-generator camp.

## 4. Guidance on writing tool descriptions/schemas for LLM consumption

- **Anthropic**, "Writing effective tools for AI agents—using AI agents":
  detailed descriptions are "by far the most important factor in tool performance" — explain
  what the tool does, when to use/not use it, what each parameter means, and caveats; target
  3-4 sentences minimum. **Consolidate related operations into fewer, higher-level tools**
  rather than one tool per action — fewer tools reduce selection ambiguity as surface grows.
  Provide concrete input examples for complex/nested parameters. Iterate using measured
  success rate, token consumption, call count, and error traces.
  https://www.anthropic.com/engineering/writing-tools-for-agents
- **OpenAI**, function-calling guide: write clear, detailed function names/parameter
  descriptions; prefer **scenario-oriented** descriptions ("use this when a user asks about
  X") over purely functional ones; use `enum` for discrete parameter values to shrink the
  model's decision space and cut invalid calls; function schemas count as billed input tokens,
  so shorten descriptions or defer/tool-search when hitting limits; expect zero/one/multiple
  calls per turn.
  https://developers.openai.com/api/docs/guides/function-calling
- **MCP spec** itself: tool `name` SHOULD be 1-128 chars, ASCII letters/digits/`_`/`-`/`.`
  only, unique per server; deterministic `tools/list` ordering for prompt-cache efficiency;
  `operationId`-derived names recommended by Speakeasy's OpenAPI best practices (action-oriented,
  e.g. `createTask`, `listActiveTasks`) — directly applicable to naming mcpcli's discovered
  commands/queries inside `describe` payloads even if the outer MCP tool surface stays generic.

## 5. Read-only mode, write gating, idempotency keys for agent-invoked writes

- **Read-only mode as a server-level filter/flag**: `xalantis-mcp-go` PR #3 implements
  `XALANTIS_READ_ONLY=1` that hides write operations, restricts search/listing to GET-derived
  operations, and rewrites server instructions accordingly — a filter sitting between tool
  registration and the server, i.e. exactly the "catalog distinguishes commands from queries so
  read-only mode is one filter" approach mcpcli's CLAUDE.md already commits to.
  https://github.com/martialpmt/xalantis-mcp-go/pull/3
- **Idempotency keys**: same project — when an operation declares the header and the caller
  omits it, the server generates a UUIDv4 server-side; client-supplied keys let the server
  store-and-replay the outcome instead of re-running the write. Convention observed elsewhere:
  a tool/operation marked `idempotentHint: false` is the signal that it needs an idempotency
  key at all. https://github.com/martialpmt/xalantis-mcp-go/pull/3 ·
  https://glama.ai/mcp/servers/abluva/mcp-request-idempotency-reference
- **Write gating as policy enforced outside the agent**: Cerbos's "Policy-Driven MCP Routing"
  argues gating (which tools an agent may invoke, with what arguments) should be a policy
  decision enforced by an intermediary, not something the agent self-restrains — annotations
  like `destructiveHint`/`readOnlyHint` are signals a well-behaved *client* uses to require
  human confirmation, but per the spec itself these are untrusted metadata from the server's
  own declaration, not an enforcement mechanism.
  https://www.cerbos.dev/blog/policy-driven-mcp-routing-tool-gating
- **"Agent Mode" / auto-executable allowlists**: teams wanting autonomous execution mark a
  subset of tools (typically the read-only, idempotent ones) as auto-executable and route
  everything else to human approval — an access-control layer above annotations.
  https://www.getmaxim.ai/articles/how-mcp-tools-work-discovery-invocation-and-access-control/
- **Verification gap**: a 200 response from a write tool doesn't guarantee the intended
  side-effect actually happened (relevant to designing mcpcli's command result/ack contract).
  https://dev.to/pierrelaurentmedori/your-mcp-write-returned-200-did-the-right-thing-actually-happen-38n0

## Bottom line for mcpcli's PRD

mcpcli's planned shape (catalog of commands/queries from Contracts assemblies, discovered at
runtime, exposed through a small set of generic MCP tools) sits squarely in the "discovery
meta-tools for a large, dynamic catalog" camp (section 1/2) rather than the SDK-generator
"one-tool-per-operation" camp (section 3) — which is the right call per both the arXiv tool-tax
literature and Credal's stated conditions for when meta-tools pay off. The read-only/write-gate
and idempotency-key design already sketched in CLAUDE.md matches current community practice
(xalantis-mcp-go) rather than inventing something novel; the main open item the PRD should
address explicitly is which tool annotations (`readOnlyHint`/`destructiveHint`/`idempotentHint`)
the generic `invoke`-style tool declares, given the spec's warning that these are per-tool, not
per-operation — a single generic invoke tool covering both commands and queries cannot honestly
declare `readOnlyHint: true`, so read-only mode more likely needs a **separate query-only tool
surface** (or a filtered catalog) rather than relying on annotations at the meta-tool level.

# Epic 2 Context: Operators Can Configure and Run Operations from the Terminal

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Deliver one predictable `hexalith` CLI through which an operator or script can select a private execution profile, discover catalog operations offline, submit valid commands and queries exactly once through the EventStore Gateway, inspect canonical results or actionable failures, and prevent writes with Read-only Mode. The CLI establishes the shared settings, execution, and document contracts that the MCP head will reuse.

## Stories

- Story 2.1: Inspect Effective Session Settings
- Story 2.2: Add and Select a Private Profile
- Story 2.3: Update and Remove Profiles Safely
- Story 2.4: Browse the Catalog from the CLI
- Story 2.5: Run a Valid Query Through the Gateway
- Story 2.6: Validate and Page Query Calls
- Story 2.7: Submit a Command Once
- Story 2.8: Protect Command Identity and Extensions
- Story 2.9: Explain Execution Failures with Stable Documents
- Story 2.10: Refuse Writes in Read-only Mode
- Story 2.11: Keep CLI Output and Exit Codes Predictable

## Requirements & Constraints

- Provide `modules`, `operations`, `describe`, `send`, `query`, `mcp`, and `config`. Discovery, configuration, and version reporting must work without a Gateway URL; execution without one returns `configuration_invalid`. HTTP transport is explicitly unsupported in v1.
- Select the profile from flag, environment, then active profile. Resolve each session setting from flag, environment, selected profile, then its documented default. Use JSON by default, validate environment booleans, and never read the EventStore admin CLI's profile or environment namespace.
- Persist profiles only in `~/.eventstore/mcpcli.json`. Never expose tokens; display only a masked form. Invalid, malformed, unsupported-version, or symlink-backed configuration must fail without mutation.
- Return the canonical shared success or `{ "error": ... }` document. Required fields always appear, absent optional fields are omitted, arrays are never null, validation reports every violation with an RFC 6901 pointer, and failures never expose stack traces or secrets.
- Use exit 0 for a result, exit 1 only for `describe --lint` with findings, and exit 2 when no result is produced. Stdout contains only the result document; diagnostics, logs, and format notes go to stderr. Pre-serving `mcp` failures leave stdout empty.
- Validate operation kind, availability, JSON, schema, envelope ownership, identifiers, routing constraints, paging, and extensions before submission. Invalid input must produce zero Gateway calls. Send each accepted request through `IEventStoreGatewayClient` exactly once and never retry or imply that retry is safe after an unknown command outcome.
- Generate one ULID message ID per command. Correlation defaults to that same ID; correlation and optional caller-supplied idempotency keys must be ULIDs. Never generate an idempotency key. Validate payload identifiers using the module's declared identifier kind, not property-name inference and never `Guid.TryParse`.
- Resolve tenant from fixed module tenant, gated per-call tenant, then session tenant. Actor always comes from session context. Envelope-owned payload members must agree with resolved values before being filled and the rebuilt payload must be validated again.
- Query paging exists only in the envelope: page size 1–200, nonnegative offset, cursor up to 4,096 characters, and cursor mutually exclusive with offset. Command extensions are profile-allowlisted, case-insensitive, sanitizer-valid, and bounded by count, key/value lengths, and combined UTF-8 size.
- Read-only sessions refuse commands in the executor before payload parsing or Gateway access while leaving discovery and queries available. Discovery still shows write operations but marks them non-submittable.

## Technical Decisions

- Keep the CLI as an adapter: Core owns settings values, catalog access, validation, envelope construction, execution, and typed result/error records. The head owns argument binding, rendering, output routing, and exit-code mapping; it must not reflect over contracts or duplicate execution rules.
- Build one Host container and one resolved-settings singleton per invocation. Register the Gateway client once; the tool host alone adds the static bearer handler, and Core never reads credentials.
- Run execution in a fixed sequence: resolve the descriptor; reject call-kind mismatch; apply read-only/configuration availability; parse and pre-validate a payload copy without envelope-owned members; resolve and verify envelope ownership; fill and revalidate the complete payload; resolve aggregate identity; validate remaining envelope fields; construct one request; call the Gateway once; map the response or client exception.
- Aggregate identity resolves from explicit argument, compiled accessor, then query constant. An explicit value must agree with an accessor but may override a constant. Commands without an accessor source are not executable catalog entries; queries without a source require an explicit argument.
- Serialize all head documents with the one canonical result serializer. Preserve module-specific payload converters only inside Core's cached module payload options; they must not affect envelope or result serialization.
- Make every profile mutation a cross-process transaction: lock, reload and validate, apply one change, create and flush a restrictive same-directory temporary file, then atomically replace the target. Protect directory, profile, lock, and temporary files before token bytes are written, using Unix modes or Windows ACLs as appropriate.

## UX & Interaction Patterns

JSON is the stable machine interface. Table output is limited to module, operation, and configuration displays; `describe`, `send`, and `query` remain JSON and emit one stderr note when table format was requested. `config current` shows effective values and their sources with a masked token, while unknown modules or operations provide at most three deterministic nearest-name suggestions.

## Cross-Story Dependencies

Epic 2 consumes Epic 1's immutable catalog, schemas, routing descriptors, diagnostics, and lint findings. Its shared argument, result, error, settings, and executor contracts are prerequisites for Epic 3, which adds MCP stdio carriage without changing behavior. Query and command execution depend on the pinned EventStore Gateway client and on module contracts declaring valid routing, identifier, and envelope-property metadata.

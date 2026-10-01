# Epic 2 Context: Operators Can Configure and Run Operations from the Terminal

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

An operator or script can select a private Profile, discover Operations without a Gateway connection, submit valid Commands and Queries once through the EventStore Gateway, inspect canonical results and errors, and enforce Read-only Mode from one `hexalith` CLI. This epic also fixes the shared settings, executor, and result documents both heads use, so a script and a later agent session cannot disagree.

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

- Expose `modules`, `operations <module> [--kind read|write]`, `describe <operation> [--lint]`, `send`, `query`, `mcp`, and `config`. `send` and `query` take inline JSON, `@file`, or stdin. Discovery is offline. `config` and `--version` skip Catalog construction. Execution without a Gateway URL returns `configuration_invalid`. `mcp --transport http` fails before Catalog build with `unsupported_transport` on stderr and empty stdout.
- Select the Profile from flag, `EVENTSTORE_PROFILE`, then the active Profile. Other settings resolve flag, environment, selected Profile, then default. Defaults: no URL, token, Tenant, or Actor; empty extension allowlist; override off; JSON on stdout; read-only and strict off. Environment booleans are `true`, `false`, `1`, or `0`. The CLI has no per-call Tenant and does not read the admin CLI profile or environment names.
- Store Profiles only in version-1 `~/.eventstore/mcpcli.json`. Names match `^[a-zA-Z0-9_-]{1,64}$`. Re-adding a name replaces that Profile only. `config set` edits Tenant, Actor, tenant override, or comma-separated extension keys. Removing the active Profile clears the selection. Show at most the token's first four characters, including in errors and logs. Invalid input, a bad version, a symlink, or a missing Profile fails without writing.
- Success and failure share one document set: required members always appear, absent optional members are omitted, and arrays are empty rather than null. Failures are only `{ "error": ... }` with code `validation_failed`, `unknown_operation`, `unknown_module`, `invalid_arguments`, `read_only`, `gateway_error`, `configuration_invalid`, `catalog_empty`, `catalog_invalid`, `unsupported_transport`, or `internal_error`. Report every Schema violation together, each with an RFC 6901 path. Unknown names include at most three edit-distance suggestions, ties broken ordinally. Gateway errors keep the exception status, including a possible 2xx, and optional metadata only when supplied. Unexpected failures hide stack traces and tokens.
- Exit 0 is a result, exit 1 is `describe --lint` with findings, and exit 2 is no result. Catalog diagnostics stay on stderr and affect the exit code only under `--strict` (`catalog_invalid`). An empty Catalog is `catalog_empty` for discovery and execution. Stdout or `--output` receives the result; logs and format notes go to stderr.
- A Command call must name a write and a Query call a read. A mismatch is `validation_failed` at `/operation` before availability or Payload checks, with zero Gateway calls. Read-only Mode then refuses a matching write inside the executor, before Payload parsing, even when the URL is missing. Discovery still lists writes and marks them not submittable; Queries stay available.
- Reject bad JSON, Schema violations, a null or non-object Command root, bad identifiers, paging, and extensions before any Gateway call. Submit Catalog routing values, never the public Operation Name, exactly once, with no retry and no invented `duplicate` field. An unknown Command outcome must not imply that another submission is safe.
- Generate one ULID message identifier per Command and reuse it as correlation when the caller omits one. Caller correlation and idempotency keys must be ULIDs; the tool never generates an idempotency key and echoes one only when supplied. Command success carries message identifier, correlation identifier, Tenant, aggregate identifier, `status: accepted`, and `result` only when returned. Query success carries operation, Tenant, document (including JSON null), and only returned paging fields. Queries carry neither correlation nor extensions.
- Resolve Tenant as fixed Module Tenant, then a per-call Tenant only with no session Tenant or with override enabled, then the session Tenant. Missing or disallowed Tenant fails closed. A declared Actor comes only from the session and is required. Envelope-owned Payload members must match those values before filling; validate the rebuilt Payload again. Aggregate identity is explicit argument, compiled accessor, then Query constant. An explicit value may override a constant and must agree with an accessor.
- Validate Payload identifiers by Module kind (`Ulid.TryParse` or nonempty string), not by name suffix or `Guid.TryParse`. Tenant, aggregate, and entity values must also match Gateway patterns and lengths. Query paging is envelope-only: size 1–200, nonnegative offset, cursor at most 4,096 characters, cursor exclusive of offset. Same-named Payload members stay Payload. Command extensions allow only Profile keys, case-insensitively, within the sanitizer grammar and the fixed count, length, and UTF-8 limits.

## Technical Decisions

- The CLI translates. Core owns Catalog use, validation, Envelope filling, execution, argument records, and typed results, with no System.CommandLine or MCP reference. The head binds input, renders, routes output, and maps exit codes from one DI settings singleton.
- Every verb, including `mcp`, starts one Host after a single settings resolution. Register one Gateway `HttpClient`; only the tool host attaches the static bearer handler. Core never reads the token.
- Pipeline order: descriptor, kind check, read-only before missing URL, pre-validation without envelope-owned members, raw ownership, fill and revalidate, aggregate identity and extensions, one call, then mapping. Any other exception is `internal_error`. Module converters stay in cached Payload options; head documents use the result serializer.
- Each Profile change locks, reloads, validates, flushes a restrictive same-directory temporary file, then replaces the target. Apply Unix modes or Windows ACLs before token bytes are written. Reject symlinks and malformed targets. Concurrent successes must both survive, and an interrupted write must leave one complete file.

## UX & Interaction Patterns

JSON is the script contract. Table output applies only to module, operation, and configuration displays; `describe`, `send`, and `query` stay JSON, emit one stderr note, and keep their result-based exit code. `config current` shows each resolved value and its source with the token masked.

## Cross-Story Dependencies

Epic 2 consumes Epic 1's immutable Catalog, Schemas, routing, diagnostics, and lint findings. Epic 3 carries these contracts over stdio and omits the write tool in a Read-only session; this epic owns the CLI `mcp` binding and the unsupported-HTTP response. The first live Query proof uses a throwaway harness on the existing EventStore AppHost and root-declared checkouts, before this repository's test AppHost. The list-Query aggregate-identifier constant stays a recorded candidate until the Tenants maintainer confirms it.

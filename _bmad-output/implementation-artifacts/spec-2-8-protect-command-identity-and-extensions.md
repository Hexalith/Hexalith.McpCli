---
title: 'Protect Command Identity and Extensions'
type: 'feature'
created: '2026-10-02'
status: 'in-progress'
baseline_commit: '1554a84d792a0178a342d62367259999fd45e0b9'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Caller-controlled identity fields or extensions can violate session policy. Raw idempotency fields can wrongly block a valid caller key; lowercase ULID aggregates can address different EventStore streams.

**Approach:** Enforce Payload ownership and extension policy in Core, validate rebuilt Payload before accessor or submission, and require canonical uppercase ULID aggregate and marked identifier text.

## Boundaries & Constraints

**Always:** Resolve Tenant from fixed Module, permitted per-call value, or session; Actor only from session. Present mapped Tenant/Actor members must be JSON strings ordinally equal to resolved values; otherwise fail at escaped member pointers. Fill omitted/matching members. Generate one message ULID, reuse it for omitted correlation, and overwrite raw correlation. A supplied ULID idempotency key overwrites any raw mapped value; without a key, reject non-null raw values at `/idempotencyKey`, remove raw null, and require the key for non-nullable or serializer-required members, including required nullable. Validate a copy without mapped envelope fields, then rebuilt Payload, before computed `ICommandContract.AggregateId` access. Commands require object roots; allowed nested nulls survive. Reject lowercase ULID aggregates, marked identifiers, and caller correlation and idempotency keys per the user decisions; accepted values pass unchanged. Allow only Profile-approved extension keys case-insensitively, within pinned Gateway sanitizer and request-validator grammar, injection, count, length, and UTF-8 limits. Refusals make zero Gateway calls; successes make one.

**Never:** Read Tenant or Actor from Payload as an authority; generate an idempotency key; apply envelope identity or extension fields to Queries; add module-specific code or dependencies; edit `references/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Owned identity | Omitted or matching declared Tenant/Actor, raw malformed correlation, supplied valid key over malformed idempotency | Resolved values replace mapped fields; computed getter sees rebuilt Payload | Conflict, null, or non-string Tenant/Actor fails at mapped pointer |
| No key | Optional raw null or absent key; non-null raw key; required nullable key | Raw null removed; optional member omitted | Non-null raw or required member fails at `/idempotencyKey` |
| Payload shape | Null/non-object Command root; valid nested null; ordinary invalid/unknown member | Nested null survives when Schema permits; ordinary constraints still apply | Invalid root at `/`, Schema violations with pointers |
| Identifiers | Canonical and lowercase ULID aggregate argument/accessor/marked member | Canonical passes unchanged | Lowercase rejected before Gateway; entity ID still follows Gateway syntax |
| Extensions | Allowed mixed-case key; unsafe/oversize/count/UTF-8 boundary | Safe values pass unchanged | Refuse at `/extensions` or escaped key pointer |

</frozen-after-approval>

## Code Map

- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — prefill, ownership, fill, final validation, accessor, single submission; fix supplied-key overwrite.
- `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs` — marked/typed ULID pattern; preserve envelope-required removal and nested nullability.
- `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs` — allowlist, pointers, sanitizer; add Gateway request-validator dangerous characters.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs`, `OperationDescriptor.cs`, `AggregateIdAccessors.cs` — reuse required-key metadata, mapped members, late accessor.
- `src/Hexalith.McpCli.Core/McpCliCoreServiceCollectionExtensions.cs`, `src/Hexalith.McpCli/Hosting/HostFactory.cs` — retain one Gateway client, host-only bearer handler.
- `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs`, `SchemaTests.cs`, `QueryValidationTests.cs`, `tests/Hexalith.McpCli.Cli.Tests/QueryPagingCommandTests.cs` — acceptance and prior lowercase expectations.
- `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/ExtensionMetadataSanitizer.cs`, `SubmitCommandRequestValidator.cs` — read-only pinned rules.

## Tasks & Acceptance

**Execution:**
- [x] `tests/fixtures/Catalog.Routing.Contracts/RequiredNullableIdempotencyCommand.cs` and `ComputedEnvelopeCommand.cs` — add missing edge-case contracts.
- [x] `tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs` — cover raw ownership, omitted filled required members, malformed overwritten fields, no-key cases, root/nested null, all extension boundaries, and zero/one Gateway calls.
- [x] `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs` — allow supplied-key overwrite and check aggregate ULID canonical form separately from envelope ULIDs; keep validation ordering.
- [x] `src/Hexalith.McpCli.Core/Schema/SchemaDeriver.cs` and `tests/Hexalith.McpCli.Core.Tests/SchemaTests.cs` — require canonical uppercase marked/typed ULIDs and pin the advertised Schema.
- [x] `src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs` — reject Gateway dangerous characters; test escaped-key and boundaries in executor tests.
- [x] `tests/Hexalith.McpCli.Core.Tests/QueryValidationTests.cs` and `tests/Hexalith.McpCli.Cli.Tests/QueryPagingCommandTests.cs` — flip the prior lowercase pass-through expectations while preserving valid entity and Tenant boundaries.
- [x] `README.md` — document identity ownership, idempotency, allowlist, and canonical ULIDs.

**Acceptance Criteria:**
- Given a declared identity mapping and session, when a Command runs, then trusted values reach one Gateway request or precise validation fails before submission.
- Given allowed extensions, when a Command supplies them, then only Gateway-compatible keys and values reach one request.
- Given a noncanonical ULID aggregate or marked identifier, when either head calls Core, then validation fails before submission.

### Review Findings

Code review 2026-10-03 of `1554a84..a343378`; layers: Blind Hunter, Edge Case Hunter, Verification Gap, Acceptance Auditor (none failed). Verification Gap traced every behavioral change to a test that fails on its smallest regression.

- [x] [Review][Patch] Lowercase caller correlation or idempotency ULIDs pass the envelope check, then fail at a payload pointer the caller never wrote — medium (blind-hunter+edge-case-hunter+verification-gap+acceptance-auditor). `SchemaDeriver.IsSupportedRoleType` lets Correlation and IdempotencyKey bind to CLR `Ulid`/`Ulid?` members (`SchemaDeriver.cs:196-197`). Those members now get the uppercase-only `UlidPattern` (`SchemaDeriver.cs:18`, `:301-304`). The executor still accepts lowercase envelope values through `Ulid.TryParse` (`OperationExecutor.cs:150`, `:155`), and `Fill` writes them unchanged (`:192-193`). Final validation (`:197`) then rejects them at `/Correlation` or `/Idempotency`, not at `/correlationId` or `/idempotencyKey`. Before this change the same value succeeded, and it still succeeds for `string` members. Three layers reproduced this against the built Core assembly; no test or fixture declares a `Ulid`-typed role member. Same root cause: the Gateway treats the idempotency key as an opaque ordinal string (`SubmitCommandRequestValidator.cs:93-97`), so `01arz…` and `01ARZ…` are different deduplication keys and a retry that changes the casing can submit twice (pre-existing since Story 2.7). Options: (1) canonicalize accepted envelope ULIDs with `parsed.ToString()` before filling, submitting and echoing; (2) reject noncanonical envelope ULIDs at `/correlationId` and `/idempotencyKey`, which renegotiates the frozen "`Ulid.TryParse`" wording; (3) canonicalize only the text filled into `Ulid`-typed role members; (4) defer. Resolved by user decision 2026-10-03: option 2. Canonicalizing would contradict Story 2.7's "accept caller values unchanged" rule, and rejection matches the Story 2.6 aggregate decision. The executor now checks both envelope values with `IsCanonicalUlid` at `/correlationId` and `/idempotencyKey`; `IsUlid` was removed; README and the frozen Always clause updated. [src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:150]
- [ ] [Review][Patch] README understates where uppercase ULID text is required — low (acceptance-auditor+blind-hunter). "ULID aggregate identifiers and marked payload identifiers must use canonical uppercase text" can be read as covering marked identifiers in String-kind modules, which stay nonempty strings. It also omits that every CLR `Ulid`-typed payload member requires uppercase in every module, including nested collection and dictionary elements (`SchemaDeriver.cs:301`, `SchemaTests` `/Ids/0`, `/ByName/a`, `/Optional/0`). Envelope correlation and idempotency casing is now stated at `README.md:67`. [README.md:73]
- [ ] [Review][Patch] README does not say a payload correlation member is replaced — low (blind-hunter). The story documents raw Tenant, Actor and idempotency handling, but not that a mapped correlation member is always overwritten by `--correlation-id` or the generated message ID (`OperationExecutor.cs:148`, `:192`), while a raw idempotency value is refused in the same situation. Add one sentence to the identity-ownership text. [README.md:67]
- [ ] [Review][Patch] The reserved key literal appears twice, and the test cannot tell which check fired — low (blind-hunter). `"actor:globalAdmin"` is written at `ExtensionValidator.cs:40` and `:72`. `ReservedExtensionMakesZeroCallsAsync` asserts only the pointer, so deleting the "reserved" branch silently turns the message into "The extension key is invalid." Use one constant and assert the reserved message. [src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs:40; tests/Hexalith.McpCli.Core.Tests/OperationExecutorTests.cs:484]
- [ ] [Review][Patch] The lowercase-ULID ledger entry this story resolves is not marked resolved — low (blind-hunter). The ledger records resolutions with a `status: resolved in Story …` line (`deferred-work.md:96`), but the Story 2.6 entry Story 2.8 owns has none, so a later ledger sweep would treat it as open. [_bmad-output/implementation-artifacts/deferred-work.md:267]

**Rejected**

- false — The extension snapshot copy can throw on a duplicate or null key (edge-case-hunter): both heads bind real `Dictionary` instances that cannot hold either, and the same copy already existed at submission before this change. Only a deliberately broken custom `IReadOnlyDictionary` reaches it, and it then fails loudly as `internal_error`.
- false — A lowercase-ULID contract `Example` now fails catalog build (edge-case-hunter): such an example violates the advertised Schema and would fail at call time, so `invalid_example` is the intended consequence. No enrolled or referenced Contracts package has one.
- false — Overwriting a supplied key over a valid raw ULID is unpinned (blind-hunter): the old code refused any non-matching raw key, so `SuppliedKeyFillsRequiredNullableMemberAsync` (malformed `"bad"`) fails on a revert. The coupled computed-accessor rows name no missed defect.
- false — Spec `done` versus sprint `review` (blind-hunter): the sprint entry moves only when this review closes, the same path Story 2.7 took (`954a426`).
- false — An oversized extension map produces an unbounded error document (blind-hunter): at most three violations per entry the caller sent, so the error grows linearly with the caller's own input.
- false — The README presents configurable Gateway limits as fixed (blind-hunter): it states the CLI's local limits, which epic-2-context.md fixes. They are the strictest combination of the pinned sanitizer defaults and the request validator, and a stricter Gateway reports its own `gateway_error`.
- false — Verification skipped the other test projects and the Release solution build (blind-hunter): no Abstractions, Analyzers, Manifest or ConformanceHost source uses the ULID pattern or the routing fixture, and no repository file outside the new negative tests contains lowercase ULID text.
- low — Existing profile files holding `actor:globalAdmin` or a newline-terminated key become unreadable (edge-case-hunter+acceptance-auditor+blind-hunter): there is no release (no tags; nothing ships before Epic 4), so only local development files could hold one, and read-time tolerance adds new branches.
- low — A lowercase ULID query constant passes catalog validation but fails every call (edge-case-hunter+blind-hunter): no module declares one, `--aggregate-id` overrides it, and the fix needs a shared canonical helper plus a new catalog check.
- low — An allowlisted `traceparent` or `tracestate` is replaced by the Gateway (edge-case-hunter): an operator must allowlist the key, the overwrite is the Gateway's own trace propagation (`SubmitCommandExtensions.cs:32-39`), and a reserved list is a new guard.
- low — AC3's "either head" is tested only through CLI `query` (acceptance-auditor+blind-hunter): the MCP head passes the aggregate argument to the same Core executor; an MCP protocol fixture adds machinery without a distinct branch, as triage item Blind 7 already concluded.
- Rejected because the fix would edit the spec (acceptance-auditor): AC2's "only Gateway-compatible keys" overstates local enforcement for colon keys, which require a Gateway-side trusted-extension policy. The frozen Always clause asks only for the sanitizer and validator rules, and the README documents the policy requirement.
- Rejected because the fix would edit the spec (blind-hunter): the Code Map lists planned files that were not touched and omits fixture and test files that were.

## Implementation Notes

- The executor retains its prefill and final-schema pipeline. A supplied key now overwrites raw mapped idempotency data; absent-key non-null data still fails before submission.
- Aggregate ULIDs use a canonical-text check separate from envelope ULID parsing. The advertised identifier Schema now permits uppercase Crockford text only.
- Extension validation now includes the pinned Gateway request validator's dangerous-character rule. Synthetic contracts exercise serializer-required nullable keys and a getter that needs envelope-filled required members; their discovery snapshots were updated.
- The diff audit added missing-Actor, malformed raw-field, required-member, and discovery coverage. No production dependency or `references/` file changed.
- Review fixes reject newline-terminated, case-colliding, and reserved extension keys. The executor validates and submits one extension snapshot; docs explain Profile setup and Gateway policy for namespaced keys. Accepted-limit and nested-ULID tests now check the submitted data and rejection paths.

## Spec Change Log

- 2026-10-03: The user renegotiated the frozen envelope ULID rule during code review. Caller correlation and idempotency keys must now be canonical uppercase ULIDs, like aggregate and marked identifiers, instead of any text `Ulid.TryParse` accepts. Accepted values still pass unchanged, so Story 2.7's rule holds. The Always clause now reflects the decision.

## Review Triage Log

- Blind 1 — medium, patch: `ExtensionValidator.KeyPattern` ends with `$`, which .NET can match before a final newline; `IsValidKey` otherwise accepts such a key. Use an absolute end anchor and cover the key.
- Blind 2 — medium, patch: `CommandsController.BuildTrustedExtensions` writes into an ordinal-ignore-case dictionary, so distinct submitted keys differing only by case silently collapse. Reject them before the Gateway call.
- Blind 3 — medium, patch: `CommandsController` ignores `actor:globalAdmin` case-insensitively, while the current validator and allowlist accept it. Reject the reserved key locally and during Profile key validation.
- Blind 4 — low, patch: the new README extension paragraph does not explain that colon-delimited keys require exactly one Gateway trusted-extension policy to claim and accept them; otherwise the Gateway rejects the request.
- Blind 5 — low, patch: README names the allowlist and extensions without showing the existing `config set PROFILE allowedExtensions ...` and repeatable `send --extension key=value` syntax.
- Blind 6 — low, reject: no single CLI test reads a selected Profile and submits an allowed extension, but `SettingsResolver`, the host's `EnvelopeContext`, Core validation, and CLI submission are tested at their existing seams. A new HTTP/Profile integration fixture is more than a direct correction for this low-risk coverage gap.
- Blind 7 — low, reject: no new MCP protocol test includes extensions, but `McpToolHandlers.SendCommand` passes the bound dictionary unchanged to the same tested executor. A protocol fixture adds machinery without a distinct policy branch.
- Blind 8 — low, patch: accepted extension-limit cases assert one call but not that the copied request retains every key and value; capture and compare the submitted dictionary.
- Blind 9 — low, patch: the Schema pattern also constrains nested CLR `Ulid` members in String-kind modules; existing `UlidElementsAreConstrained` pins the pattern and positive values but not lowercase rejection on nested paths.
- Edge 1 — medium, patch: `SendCommandArguments.Extensions` is an `IReadOnlyDictionary` that can wrap a mutable dictionary; a concurrent mutation after validation can put an unchecked value into the later request copy. Validate and submit the same local snapshot.
- Edge 2 — medium, patch: the same validation-then-copy window can violate the claimed Gateway-compatible extension guarantee; it shares Edge 1's snapshot fix.
- Patch closure — all patch findings above were fixed and the full Core, CLI, and MCP verification commands passed after the changes.

## Verification

**Commands:**
- `dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Debug --no-restore -m:1` — passed, zero warnings/errors.
- `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Debug/net10.0/Hexalith.McpCli.Core.Tests.dll` — 468 total, zero failures, two Windows-only skips.
- `dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1` — passed, zero warnings/errors.
- `dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll` — 339 total, zero failures.
- `dotnet build tests/Hexalith.McpCli.Mcp.Tests/Hexalith.McpCli.Mcp.Tests.csproj --configuration Debug --no-restore -m:1` — passed, zero warnings/errors.
- `dotnet tests/Hexalith.McpCli.Mcp.Tests/bin/Debug/net10.0/Hexalith.McpCli.Mcp.Tests.dll` — six total, zero failures.
- `git diff --check` — passed.
- `npx --no -- commitlint --edit /tmp/mcpcli-story-2-8-commit-bDEkvf.txt` — passed for `feat(command): protect command identity and extensions`.

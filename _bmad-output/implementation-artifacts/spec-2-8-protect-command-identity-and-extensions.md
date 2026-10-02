---
title: 'Protect Command Identity and Extensions'
type: 'feature'
created: '2026-10-02'
status: 'done'
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

**Always:** Resolve Tenant from fixed Module, permitted per-call value, or session; Actor only from session. Present mapped Tenant/Actor members must be JSON strings ordinally equal to resolved values; otherwise fail at escaped member pointers. Fill omitted/matching members. Generate one message ULID, reuse it for omitted correlation, and overwrite raw correlation. A supplied ULID idempotency key overwrites any raw mapped value; without a key, reject non-null raw values at `/idempotencyKey`, remove raw null, and require the key for non-nullable or serializer-required members, including required nullable. Validate a copy without mapped envelope fields, then rebuilt Payload, before computed `ICommandContract.AggregateId` access. Commands require object roots; allowed nested nulls survive. Reject lowercase ULID aggregates and marked identifiers per the user decision; correlation and idempotency use `Ulid.TryParse`. Allow only Profile-approved extension keys case-insensitively, within pinned Gateway sanitizer and request-validator grammar, injection, count, length, and UTF-8 limits. Refusals make zero Gateway calls; successes make one.

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

## Implementation Notes

- The executor retains its prefill and final-schema pipeline. A supplied key now overwrites raw mapped idempotency data; absent-key non-null data still fails before submission.
- Aggregate ULIDs use a canonical-text check separate from envelope ULID parsing. The advertised identifier Schema now permits uppercase Crockford text only.
- Extension validation now includes the pinned Gateway request validator's dangerous-character rule. Synthetic contracts exercise serializer-required nullable keys and a getter that needs envelope-filled required members; their discovery snapshots were updated.
- The diff audit added missing-Actor, malformed raw-field, required-member, and discovery coverage. No production dependency or `references/` file changed.
- Review fixes reject newline-terminated, case-colliding, and reserved extension keys. The executor validates and submits one extension snapshot; docs explain Profile setup and Gateway policy for namespaced keys. Accepted-limit and nested-ULID tests now check the submitted data and rejection paths.

## Spec Change Log

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

---
title: '5.4 Prove shared-head parity and safety'
type: 'feature'
created: '2026-11-09'
updated: '2026-11-10T02:39:42+01:00'
status: 'done'
baseline_commit: 'f6c8e0e3a2105f555e6eec3c667b088085c47fc4'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing proves yet that McpCli can replace `Parties.Mcp` safely on a named environment.
- The live lane runs only the seven happy-path vectors, through the CLI head.
- No test pins a 401 or 403 document, or any tenant negative, for a Parties operation.
- C05's delete oracles and C08's cross-tenant denial are never exercised live.
- Restricted Admin names are never probed, with or without `confirm: true`.
- No evidence set binds the candidate, Catalog digest and environment by hash.

**Approach:**
- Add generic offline guards over the enrolled Parties 1.5.1 catalog, run through both heads.
- Add live boundary cases, and live MCP-head reads, on the CI live topology.
- Assemble one redacted, hash-bound evidence set with a C01–C08 variant matrix.
- HALT for the Parties owner's exact-byte approval and verdict.
- Production `src/` changes only where a guard exposes a defect.

## Boundaries & Constraints

**Always:**
- Only tests name Parties, Tenants or EventStore.
- `src/` and the runners in `tools/live-topology/` stay generic: no module names and no fixed vector or runtime counts. Derive the expected runtime count instead of keeping `ci.py`'s literal `22`.
- Every guard asserts the full error document, stdout, stderr, MCP `Content` and `StructuredContent`, and the Gateway request count. It fails when the guard is removed.
- Each live Command is submitted once. Head parity comes from loopback (`check_enrolled.py`), never from resubmitting.
- A no-mutation claim rests on a persisted end-state read with an authorized identity, not on the error alone.
- Each variant row cites one of these, or is marked a gap: a McpCli test, a loopback or live receipt, or a Parties upstream test at the enrolled revision. Matching operation names proves nothing.

**Never:**
- Add module-specific code, error mapping, `confirm` handling or dependencies to `src/`.
- Change identifier validators.
- Edit `references/`.
- Change the approved vectors, live plans or `approval.json`, or enroll another Parties version.
- Claim a release, publication or retirement. Story 5.5 owns retirement, and `epic-4-retro-item-6` binds release claims.
- Fix F7 or redactor item 5 here.

**Decisions (2026-11-09, user):**
1. **F7 accepted.** The user, as owner, answered "accept". Until `epic-4-retro-item-9-ascii-tenant-input` closes, U+212A KELVIN SIGN may alias an ASCII tenant; the Gateway's `TenantCanonicalizer` behaves the same way.
   - Pin this as the accepted limitation and record the acceptance in the evidence.
   - Every other non-ASCII look-alike must fail closed.
2. **Selected environment: the CI live topology** ("CI topology via PR").
   - It is the v1 disposable Aspire topology: public EventStore 4.1.0 and Tenants 7.0.5 archives, plus the qualified Parties source.
   - GitHub Actions runs it on a PR to `main`, and the evidence is the downloaded `TestResults/live-ci` artifact.
   - This authorizes pushing a non-`main` branch and opening that PR when the live run is due.
3. **Live MCP head included.**
   - `run_live.py` also runs every Parties Query vector through the MCP head (reads only).
   - The boundary cases run through both heads, including the MCP-only per-call override denial.
   - Commands stay CLI-only and are submitted once.
4. **Scope split: redactor item 5 first.**
   - The hardened redactor and the committed secret scan are a separate change (ledger entry under this spec's heading in `deferred-work.md`).
   - The offline and live test work proceeds now.
   - The committed live run and evidence set wait until that change lands, and the evidence must pass its scan.
5. **Gaps: the owner decides each one** at the approval HALT.
   - Either a versioned, owner-approved Parties inventory 1.3.0 amendment records an approved change, or the gap stays blocking with a ledger owner.
   - The story ends with an approved verdict: `retirement-ready` or `retirement-blocked`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| No token | Parties Query and Command with no token; the Gateway answers 401 | `gateway_error` with status 401; equal documents from both heads | No `Authorization` header is sent; live, nothing is mutated |
| Invalid token | Forged signature | 401 `gateway_error`; the token appears on no channel | Live, nothing is mutated |
| Unauthorized principal | A token granted only `tenant-a`, or a nonmember token, used with session tenant `tenant-b` or an allowed MCP per-call override to `tenant-b` | Gateway refusal through both heads, with the documented status | The `tenant-b` party is neither disclosed nor changed |
| Override disabled | MCP per-call tenant differs from the session, without `allow-tenant-override` | `validation_failed` at `/tenant` | Zero Gateway calls |
| Platform scope as tenant | `platform:tenants` as session or per-call tenant on a Parties operation | `validation_failed` at `/tenant` | Zero calls |
| Reserved tenant | `system` or `SYSTEM` | `validation_failed` at `/tenant`, "…reserved." | Zero calls |
| Look-alikes | Cyrillic `а`, U+0130, fullwidth letters | `validation_failed` at `/tenant` | Zero calls |
| F7 limitation | `Kelvin` spelled with U+212A | Wire value `kelvin` (accepted-limitation pin) | The test names item 9, so the fix must flip it |
| Restricted names | Admin and confirm-gated legacy names, and Tenants-excluded operations, with `confirm: true` in both arguments and payload | Absent from `list_operations` and `operations`; `unknown_operation` through both heads | Zero calls |
| C05 missing | Live deactivate of a party that was never created | 404 `party-not-found` | No party is created |
| C05 concurrent repeat | Two concurrent deactivations of one active party, with distinct message IDs | Both accepted; the party is inactive | Exactly one deactivation event is persisted |

</frozen-after-approval>

## Code Map

- `tests/Hexalith.McpCli.Cli.Tests/PartiesMigrationCompatibilityTests.cs`, `BothHeads.cs`, `ScriptedGateway.cs` -- the both-heads harness to reuse.
  - `PlatformScopeCommandTests.cs:13-41` and `tests/Hexalith.McpCli.Mcp.Tests/PlatformScopeProtocolTests.cs:19-50` show the full-document, zero-call pattern for `system`.
  - `QueryValidationCommandTests.cs:55` holds the only non-ASCII case (`é`).
  - No head test pins 401 or 403: `ExecutionFailureCommandTests.cs:34-63` covers only 422, 409, 5xx and 2xx.
- `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:115-134` -- lowercases the tenant, then checks the pattern. U+0130 is refused; U+212A aliases. `:316-340` holds the scope and override refusals. Do not change any of it.
- `README.md` -- the error-code list is at `:559`; a Gateway 401 or 403 is a `gateway_error` carrying that status. CLI `--tenant` is the session tenant (`:531`).
- `src/Hexalith.McpCli/Cli/CliRunner.cs:87-90` -- an unknown option returns `invalid_arguments`.
- `src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs:81-85`, `:126-139` -- MCP likely ignores extra arguments. Pin that behavior; do not change it, since `epic-3-retro-item-2` owns call-envelope validation.
- `tests/Hexalith.McpCli.Core.Tests/EnrolledModuleCoverageTests.cs:15-29` with `tools/inventory-coverage/v1/*-approved.json` -- the catalog equals exactly the `include` sets, and Tenants excludes six operations. Admin inventory 1.0.1 has no `include` row (`eventstore-admin-migration-inventory-v1.md:157-258`).
- Live identities:
  - `tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs:65-130` and `NativeFixtureIdentity.cs:12-46` -- signed tenant, domain, permission and nonmember claims.
  - `NativeAdministratorBoundary.cs:20-50` -- a refusal with the target checked absent before and after.
  - `GatewaySmokeTests.cs:29-64` -- the 401 pattern.
- Live runners:
  - `tools/live-topology/run_live.py:39` -- `observe` is CLI-only; `tools/conformance-vectors/v1/run_loopback.py:247-279` provides `HeadProcess.cli` and `.mcp`.
  - `tools/live-topology/ci.py:757-781` -- the independent smoke case and the literal `22`.
  - `.github/workflows/ci.yml:150-169` -- the exact discovery assertion.
- `tools/conformance-vectors/v1/check_enrolled.py` → `run_loopback.py:782-864` -- discovery parity, a reset `ReplayGateway` per head, and equal documents and requests for all seven Parties vectors. It computes no Catalog digest.
- Binding precedent: `tools/live-topology/live_plans.py:25` (`BINDING_KEYS`) and `_bmad-output/implementation-artifacts/evidence/story-4-13/live-complete/*/parties.*/live-result.json`.
- Variant sources:
  - Inventory `:178-185` (C01–C08).
  - `evidence/story-5-3/verification.md:221-311`.
  - `evidence/story-4-10/matrix-test-audit.md`, for the Parties-side C01, C02 and C04 tests.
  - Legacy `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/` has no task-context, freshness or output-budget behavior; it only bounds input (`Tools/PartiesMcpTools.cs:566`, C03/C04). Record those variants as "absent at source", with anchors.
- `deferred-work.md:556` (a rejection-only stream reachable by update and deactivate) and `:827` (profile identity beside a flag or environment connection) bear on C05 and C08. Cite them; do not duplicate them.

## Tasks & Acceptance

**Execution:**
- [x] `tests/Hexalith.McpCli.Cli.Tests/PartiesRetirementSafetyTests.cs` -- every offline matrix row, through both heads over the production catalog: 401 and 403 documents from `ScriptedGateway`, override disabled, platform scope, reserved tenant, look-alikes, the F7 pin, and restricted names with `confirm: true`.
- [x] `tests/Hexalith.McpCli.Integration.Tests/` -- a boundary class, plus identity helpers, for the live rows through both heads: 401s, cross-tenant refusal, nonmember, C05 missing and C05 concurrent repeat, each followed by an authorized end-state read.
- [x] `tools/live-topology/run_live.py`, `ci.py` and `.github/workflows/ci.yml`:
  - Add MCP reads for Query vectors.
  - Run the boundary class as an independent isolated case.
  - Derive the counts.
  - Extend the discovery assertion.
  - Cover each change in `test_*.py`.
- [x] After the split redactor change lands: push a branch, open the PR, and download and verify the live artifact.
- [x] `_bmad-output/implementation-artifacts/evidence/story-5-4/`:
  - `manifest.json`: the full commit; SHA-256 of the head binaries; the Parties 1.5.1 artifact hash; the Catalog digest (SHA-256 of the sorted-key, compact `list_operations` structured content); the components and revisions of the environment; the vector, plan, approval and inventory hashes; and the CI run ID and artifact hash.
  - `parity-matrix.md`: C01–C08 and the seven variants. Admin and technical rows are marked "absent; name similarity proves nothing".
  - The scan receipt, the F7 acceptance and `verification.md`.
  - HALT for the owner's exact-byte approval and verdict, then record the receipt. Completed: the owner answered `approve` for `retirement-blocked`, retaining G01–G06. The receipt is `evidence/story-5-4-owner-approval/owner-approval.json`; the original packet and scan are preserved unchanged.
- [x] `README.md`, `sprint-status.yaml` and `deferred-work.md` -- document a 401 or 403 as a `gateway_error` and the F7 limitation. Record status, and grep the ledger before appending.

**Acceptance Criteria:**
- Given the CI live topology, when the lane runs, then all seven Parties vectors, the MCP reads and every boundary case pass with `fullLiveAccepted: true`, and `check_enrolled.py` reports `fullV1Accepted`.
- Given the evidence set, when the owner reviews it, then every C01–C08 and variant row is preserved, an approved change or a named gap, and the receipt binds the exact bytes and the verdict.
- Given the whole change, when it is built, then `src/` has no new module name or dependency, and `DependencyPolicyTests` and `EnrolledModuleCoverageTests` pass unchanged.

### Review Findings

Code review pass 2 (bmad-code-review, 2026-11-10), code-only scope `f6c8e0e..c70ca97` excluding `_bmad-output/` and `references/` (4,329 diff lines, 40 files). This scope includes the separately specified redactor prerequisite `2966170`. Four layers ran and none failed: Blind Hunter (B1–B21), Edge Case Hunter (E1–E17), Verification Gap (V1–V2 gaps, V3–V5 other) and Acceptance Auditor (A1–A9). Of 52 findings, 7 are patches and 7 are deferrals (6 new, R54-D7–D12, filed under this spec's ledger heading, and 1 already tracked); 30 are rejected. Under the frozen Never rule, findings in the redactor and scanner code owned by the prerequisite are deferred, as in pass 1.

- [x] [Review][Patch] The MCP head's deadline counts host shutdown — `HeadProcess.mcp` checks the deadline again after `finally`, where `wait(2)`/`terminate`/`kill` can add about 6 s, so a `tools/call` reply that arrived in time is refused as "MCP stdio response timed out"; `_read` already enforces the reply deadline. Check the deadline right after the `tools/call` reply, inside `try`, and add a regression for an in-time reply whose shutdown outlasts the budget (A8, B9, V4, E7) [tools/conformance-vectors/v1/run_loopback.py:324]
- [x] [Review][Patch] The 5.4 approval, completion and review packets are not protected from line-ending conversion — only `evidence/story-5-4/**` is `-text`. `story-5-4-owner-approval/`, `story-5-4-completion/` and `story-5-4-review-1/` report `text: unspecified`, yet their `owner-approval.json` and `secret-scan.json` receipts bind file SHA-256s, so a Git for Windows `core.autocrlf=true` checkout breaks those bindings. Extend the attribute line to `story-5-4*/**` (A2) [.gitattributes:34]
- [x] [Review][Patch] The independent-case receipt-reuse guard has no test — no `test_*.py` reaches `Independent cases reused an isolated runtime receipt.` Add a CI-hook case where two independent cases print the same `Isolated run:` path, and assert the refusal and `fullLiveAccepted: false` (A6) [tools/live-topology/ci.py:722]
- [x] [Review][Patch] The root README states the wrong live-lane order — it says the hooks run every vector "and then the separate smoke and shared-head boundary", but `PRE_VECTOR_CASES` runs the boundary first, and a boundary failure leaves the vectors unrun (A7) [README.md:626]
- [x] [Review][Patch] The non-disclosure check covers only one private party name — `InvokeAsync` checks only `BoundaryPrivateMarker`. Add `MustNotBeDisclosed`; nothing else pins the content of MCP server log messages or notification frames (A5) [tests/Hexalith.McpCli.Integration.Tests/SharedHeadBoundaryTests.cs:181]
- [x] [Review][Patch] The F7 Kelvin pin covers only the session tenant — `OperationExecutor.cs:116` lowercases the per-call tenant and `:118` lowercases the session tenant, separately, and the item-9 tripwire exercises only the session path. Add an MCP call with per-call `tenant: "\u212Aelvin"` and no session tenant, expecting wire `kelvin`. The alias-set concern was also checked: under ICU and invariant globalization, U+212A is the only code point that lowercases into ASCII (B14) [tests/Hexalith.McpCli.Cli.Tests/PartiesRetirementSafetyTests.cs:127]
- [x] [Review][Patch] The concurrent C05 pair bypasses the shared process launcher — `ConcurrentDeactivateAsync` duplicates `BoundaryHeads.Start` without `WorkingDirectory` or `DOTNET_ENVIRONMENT=Production`, so its hosts load `appsettings.json` from the Integration.Tests bin directory and any ambient environment, unlike every other boundary row. Call `BoundaryHeads.InvokeCliAsync` with a per-call profile path instead (E10, B16) [tests/Hexalith.McpCli.Integration.Tests/SharedHeadBoundaryTests.cs:185]
- [x] [Review][Defer] R54-D7 — Quoted spans that fail to decode bypass all syntactic redaction [scripts/evidence_redaction.py:163] — deferred: code owned by the separate prerequisite (item 5). A quoted span containing a raw tab or newline, or an invalid escape such as `"C:\Users\x"`, fails `json.loads`. `string()` then returns it unchanged, and the raw-span pass (`:178-183`) appends it unsanitized, so JWT, Bearer and PEM values inside it survive (reproduced) (E1).
- [x] [Review][Defer] R54-D8 — The `<` protection scan is quadratic [scripts/evidence_redaction.py:131] — deferred: prerequisite code. Each `<` inside a JSON string is tested against every string span. Measured: 74 KB took 0.39 s, 148 KB 1.39 s and 296 KB 5.15 s, so multi-megabyte diagnostics can exhaust the 600-second cleanup reserve (B5, E2).
- [x] [Review][Defer] R54-D9 — Known-credential matching has no minimum length [scripts/evidence_redaction.py:25] — deferred: prerequisite code. The replaced `ci.py` rule required at least 8 characters. Now `X_TOKEN_TTL=12` turns `ab12cd34ef` into `ab[REDACTED]cd34ef`, and `SECRET_ENABLED=true` turns `{"ok": true}` into invalid JSON, so retained hashes get corrupted and scan results depend on the environment (B1, E5).
- [x] [Review][Defer] R54-D10 — The scanner's `sensitive-path` rule has no test [scripts/scan-evidence-secrets.py:70] — deferred: prerequisite code; a pre-verified gap. If the rule is removed, a credential-bearing file name gets a clean receipt and a rewritten manifest path (V1).
- [x] [Review][Defer] R54-D11 — The scanner's receipt-write failure path has no test [scripts/scan-evidence-secrets.py:125] — deferred: prerequisite code; a pre-verified gap. If the handler is removed, exit 2 becomes an uncaught traceback with exit 1, the same code as secrets-detected (V2).
- [x] [Review][Defer] R54-D12 — The paired-publication verifier keeps dead redaction wrappers [scripts/verify-paired-publication.py:118] — deferred: prerequisite code. `redact_operator` and `private_operator_key` have no callers, and only tests use `credentials()` (B20).
- [x] [Review][Defer] Private arguments separated by whitespace are not redacted [scripts/evidence_redaction.py:34] — deferred: already tracked (`deferred-work.md:888`, R54-D4) (B2, V3, E17).

**Pass 2 patch disposition (2026-11-10):** the user chose **Apply every patch**, and all 7 are fixed.
- `HeadProcess.mcp` now checks the deadline right after the `tools/call` reply. A new regression accepts an in-time reply whose host shutdown outlasts the budget.
- `.gitattributes` covers `story-5-4*/**`; every tracked file in the four packets reports `text: unset`, and no evidence bytes changed.
- A CI-hook mode makes smoke reuse the boundary's runtime receipt, and the run is refused.
- The README states the boundary → vectors → smoke order.
- The boundary checks both private names, and its concurrent pair uses `BoundaryHeads.InvokeCliAsync`.
- The Kelvin pin adds an MCP per-call case. The ledger anchors to `SharedHeadBoundaryTests.cs` moved by one line (now `:123`, `:136`, `:154`).

Mutation checks:
- With the old post-`finally` deadline check restored, the new loopback regression fails.
- With the receipt-reuse guard removed, the new CI-hook test fails.
- With per-call lowercasing removed at `OperationExecutor.cs:116`, the Kelvin pin fails.
- Each mutation was reverted, and `src/` and `ci.py` have no diff against HEAD.

Verification:
- Fresh restore and Release `-warnaserror` build: 0 warnings, 0 errors.
- CLI tests: 623 passed, 2 skipped (OS-only). The focused safety, process-harness, persisted-state and forwarder classes: 67 passed.
- Conformance Python: 165 passed. Live-topology Python: 219 passed.
- `check_enrolled.py` reports `fullV1Accepted: true` for Parties 1.5.1 and Tenants 7.0.5.

The changed live boundary test (P5, P7) is compiled, but it has not been re-run on the CI live topology. The original owner-approved packet and its receipts are unchanged.

Rejected:

- A1, the concurrent C05 pair is CLI-only although the task says "through both heads" — low: the frozen Decision 3 and the owner-approved packet keep the concurrent Commands CLI-only, and each MCP C05-missing Command is a boundary case submitted once per head. Reconciling the wording would edit the spec (pass 1 E05).
- A3, the Admin AU01–AU06 helper names are not probed — low: those rows are "not an operation", and unqualified names can never match a catalog name (V5).
- A4, B11 and E11, the forwarder drops headers — low: Parties variable-scope requests carry only `Authorization` and a JSON body (the client adds `X-Hexalith-Scope` only for platform scopes), and the tested 401, 403 and 404 responses carry no header-derived error member. For B11's barrier part, see E12.
- A9, the owner approval binds `3e8f6a4`, not the review-fix commit — false: the Build completion note and the pass-1 log record that the approval binds the original snapshot, and that supplementary evidence (CI `42711210249`) covers `4ddfedb`.
- B3, the C# diagnostics redactor is not shared — false: `copy_diagnostics` (`tools/live-topology/ci.py:631`) re-sanitizes `native-catalog.json` and the other retained runtime files with the shared Python redactor, so the README claim holds.
- B4, password, Basic and `access_token` forms are not detected — false: `tools/live-topology/README.md:381-383` limits the policy to the redactor's credential and private-key forms, "rather than arbitrary unknown secret strings".
- B6, the lane never requires `boundary-result.json` — low: the test writes that receipt as its last step and fails without `MCPCLI_LIVE_OUTPUT`, so a passing single-case XML implies it exists; the packet verifier checks its rows.
- B7, an interrupted independent case is not named — low: SIGTERM becomes `sys.exit(143)` and is recorded as `SystemExit: 143`, as `README.md:639` documents. Only vector Operations are promised by name, and tracking the case would add branches.
- B8, the 17700 literal is duplicated and the budget was not re-evaluated — low: `tools/live-topology/test_ci.py:1392-1393` pins both the `run-ci.sh` literal and the derived 960/15180/960 split, and the MCP reads passed CI twice within budget.
- B10, live MCP reads are not compared with CLI reads — false: the frozen Always rule assigns head parity to loopback (`check_enrolled.py`), never to a live resubmission; the live MCP read is an execution check.
- B12, the refusal oracle accepts either 401 shape — false: this is deliberate (see the "Empty 401 transport response" note), and the complete document for each shape is pinned.
- B13, the completion wait depends on SDK log text — low: ModelContextProtocol is pinned, and an upgrade that changes the text makes every in-process MCP test fail loudly.
- B15, the Admin name count is not pinned — low: a parsing loss would only shrink a set that cannot match a qualified catalog name (V5).
- B17, the test projects share linked sources — false: a breaking change to a helper fails both builds, and the links deliberately keep the reviewed fixture closure unchanged.
- B18, the before/after reads poll until the state matches — low: a wrongful change still fails (by timeout), and the durable-sequence check covers stale projections; only the failure message is weaker.
- B19, the scanner has no verify mode — false: this is a feature request, not a defect.
- B21, the CLI process's stdin is left open — false: the CLI reads stdin only for `--payload -` (`src/Hexalith.McpCli/Cli/CliRunner.cs:856-858`), which no boundary call uses, and a regression would still fail at the 45-second deadline.
- V5, the Admin half of the restricted-names test cannot fail — low: none of the 59 extracted names contains `.`, so none can match a catalog name. But `EnrolledModuleCoverageTests` already pins the catalog to the approved `include` sets, and Admin 1.0.1 has none.
- E3, prose containing `Bearer` is redacted — low: this is a fail-closed false positive, and every `Bearer` in the 5.4 packet is part of `JwtBearer`, which does not match. A fix needs a policy decision.
- E4, null or empty private settings are flagged — low: fail-closed, and unlikely in retained diagnostics.
- E6, private names with suffixes are not redacted — false: the policy covers exactly the named settings (`_PRIVATE`), and `_PEM` catches PEM bodies whatever their name.
- E8, an MCP attempt that times out is not retried — low: it requires an MCP attempt over 30 s (`run_live.py:122`) within a 45-second read deadline, and distinguishing timeouts would add branches.
- E9, the authorized token can expire — low: the boundary took 153.5 s in CI `42711210249`, against a 600-second token lifetime.
- E12, the barrier stays installed after a timeout — false: a timeout fails the request and the test, which then disposes the forwarder; no later request reaches it.
- E13, a JSON-RPC id that is not a number — false: the server never sends this client a frame with a string or null id, and the test would still fail.
- E14, the prebuilt Release host is not checked (also B16's first half) — low: the documented Release solution build produces it, and a project reference would change the reviewed fixture closure.
- E15, a symlinked checkout breaks the content-root match — low: it requires a symlinked repository path, and resolving links would need new code.
- E16, the oracle assumes `detail` and a canonical correlation ID — false: the qualified Gateway's 404 supplies both (CI passed), and a different response fails loudly.

## Implementation Notes

- Offline production-catalog safety covers both call kinds, both heads, session/per-call tenant refusals, all inventoried Admin names and six excluded Tenants targets. The accepted Kelvin alias has a dedicated item-9 pin. No production source, identifier validator, dependency policy, approved vector, live plan, approval file or reference checkout was changed.
- The boundary uses real ConformanceHost CLI and stdio MCP processes, with complete channel assertions, a counting forwarder and authorized before/after business-state reads. A separate offline process-harness regression covers successful and refused calls without topology. The in-process harness waits for the MCP response writer before teardown.
- Negative-control tokens have tenant-A-only or no tenant grants and omit the administrator role. This proves exact signed-grant authorization, not persisted Parties membership. The existing administrator bootstrap separately verifies persisted native membership. Boundary owner grants are isolated from unchanged vector/smoke grants.
- The selected cohort’s absent detail returns `500/query_internal_error` with `actor-not-found-infrastructure`, as inventory C05 records. Missing deactivation returns `404/party-not-found`; separate CLI/MCP absent targets also verify persisted events contain no creation/deactivation effect (a rejection-only stream can remain). Before/after comparisons remove only observation-time `freshness`, retaining every business member.
- Concurrent CLI processes use distinct generated message IDs. The qualified Gateway awaits the owner’s `ProcessCommandAsync` before returning acceptance; after both return, the boundary waits for the authorized inactive projection and requires exactly one persisted deactivation event in the actor’s stream. The actor ID and state keys follow qualified EventStore `dbc6e7e08d605ba6c6c790e3e08a15dc8bbdec8a`. Any configured sidecar `DAPR_API_TOKEN` is retained for state reads; app-channel authentication is unchanged.
- The generic runner executes every Query observation through MCP as well as CLI, while every vector Command stays CLI-only. Semantic receipts require both Query heads. CI derives expected counts from approved vectors and its independent-case registry; it allocates each independent case 960 seconds and reserves 600 seconds within the unchanged 17700-second outer budget.
- [Review][Resolved prerequisite] The separate redactor/committed secret-scan change closes the existing planning deferral in `deferred-work.md` under this spec's heading; see `spec-epic-4-retro-item-5-harden-ci-redaction.md` and `evidence/epic-4-retro-item-5/verification.md`. Story 5.4's dedicated live CI and final hash-bound scanned packet are now retained; its exact-byte owner approval is recorded as `retirement-blocked` in `evidence/story-5-4-owner-approval/owner-approval.json`, retaining G01–G06 as blocking. The rejection-only-stream and mixed-profile-identity work is already tracked (`deferred-work.md:556`, `deferred-work.md:833`). The original manifest binds the approved snapshot and retains its historical pending-approval state; the separate receipt records the later approved `retirement-blocked` verdict.

## Spec Change Log

## Review Triage Log

### Review pass 1 (2026-11-09)

Each row preserves the individual reviewer claim before grouping. B = blind hunter; E = edge-case hunter; V = verification-gap reviewer. The approved packet and owner receipt remain immutable snapshots; review follow-up evidence is separate.

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B01 | medium | patch | scripts/verify-release-source.py:39 still requires the old topology step label; validate_jobs rejects the renamed successful step. Align the label and pin the workflow/consumer contract. |
| B02 | high | defer | Reproduced unfinished nested escaped JSON retaining a private-value canary. evidence_redaction.py is byte-identical to the separately landed prerequisite at 296617072ab3fb632d2bddb9189b52fd94286f83; no Story 5.4 change caused it. |
| B03 | high | defer | Reproduced malformed XML with Private&#75;ey retaining the canary; raw selector matching precedes entity decoding. Same pre-existing prerequisite and root cause as E01. |
| B04 | high | defer | Reproduced a quoted XML value containing > leaving the private suffix. The malformed-tag regex terminates inside the quoted attribute; pre-existing prerequisite code. |
| B05 | high | defer | Reproduced --SigningKey VALUE retaining the canary. Whitespace arguments lost the former CI sanitizer coverage in the separate prerequisite; same root cause as E03. |
| B06 | medium | defer | A task-owned ancestor symlink leading to a regular packet scans clean. The scanner checks its final root/file components only; this is unchanged prerequisite code. |
| B07 | medium | patch | BoundaryHeads.ReadReplyAsync consumes intermediate stdout notifications without retaining them; HeadResult.AllChannels cannot observe their payloads. Preserve the complete protocol transcript and test notification-marker visibility. |
| B08 | medium | patch | require_prepared_provenance verifies source, package and host seals but never reads prepared.headCatalog. The new capture receipt can disappear or drift before execution without this gate noticing. Seal-check its bytes and binary map. |
| B09 | medium | patch | ReadAsync immediately accepts the pre-existing active projection. Because projection convergence is asynchronous, that read alone does not observe an event appended before a refusal. Add durable stream-sequence comparisons around refused calls. |
| B10 | medium | patch | Task.WhenAll starts two clients but does not hold the first request for the second to arrive. A sequential network arrival can satisfy the repeat assertion. Add a bounded two-request forwarding barrier and regression. |
| B11 | medium | patch | The event-reader unit fixtures contain only allowed streams; deleting either missing-party rejection assertion or selecting the first duplicate still passes. Same root cause as V01; add forbidden-stream rejection cases. |
| E01 | high | defer | Independently reproduced Priv&#97;teKey malformed XML retaining the same canary. Duplicate of B03, with the same raw-selector/entity-decoding root cause in the separate prerequisite. |
| E02 | high | defer | Reproduced a backslash-escaped quote terminating private-argument redaction early and retaining its suffix. This parser is unchanged from the separate prerequisite. |
| E03 | high | defer | Independently reproduced --PrivateKey VALUE remaining unchanged. Duplicate of B05: whitespace-separated private arguments in the separate prerequisite. |
| E04 | medium | patch | HeadProcess.mcp gives initialization and tools/call separate self.timeout windows; observe does not reject an otherwise successful result after the observation deadline. Share an absolute MCP budget and reject late success with focused timing regressions. |
| E05 | false | reject | The frozen Decisions item 3 and Always command rule explicitly keep live Commands CLI-only; the approved packet and Implementation Notes explicitly identify the CLI concurrent pair. The general task wording does not authorize another mutating MCP pair. |
| V01 | medium | patch | Pre-verified regression gap: PersistedPartyEventsTests exercises only valid streams, while Single/DoesNotContain assertions are the claimed safety oracles. Add zero/duplicate deactivation and forbidden creation/deactivation cases; grouped with B11. |


**Patch disposition:** B01, B07, B08, B09, B10, B11/V01 and E04 are fixed. The release validator now matches the workflow; all MCP stdout frames are retained; head-catalog bytes/hash/DLL inventory are rechecked; durable sequence equality supplements projection reads; a bounded forwarding barrier establishes the concurrent pair; unsafe event streams are rejected by explicit regressions; and MCP uses one invocation deadline with late-success refusal. All 45 focused C# cases and 28 focused Python cases pass; removing the barrier wait causes both barrier regressions to fail. Full post-review restore/Release build, Core (877), CLI (623), MCP (94), Manifest (362), 194 release-script tests, 164 conformance Python tests and 218 topology Python tests pass. Six expected OS skips remain. Fresh enrolled replay reports `fullV1Accepted: true`. Dedicated post-review CI `42711210249` is fully green; independent receipt verification passed 21 vectors, 235 declared phases, 45 boundary rows, 44 durable-sequence comparisons and 23 fresh runtime cleanup receipts. Supplementary validation is retained separately from the exact-byte owner-approved snapshot.

**Deferred groups:** R54-D1 = B02; R54-D2 = B03/E01; R54-D3 = B04; R54-D4 = B05/E03; R54-D5 = B06; R54-D6 = E02. These are six reproduced, pre-existing prerequisite root causes with their own ledger entries, not new owner waivers or changes to G01–G06. E05 is rejected on the frozen CLI-only concurrency decision. The approved original packet and its separate owner-approval receipt are unchanged.

## Verification

**Commands:**
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` -- expected: 0 warnings.
- `dotnet test tests/<Core|Cli|Mcp|Manifest>.Tests --no-build --configuration Release`, one project at a time -- expected: all pass.
- `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'`, then `run-vectors.py --preflight-only`, then the CI discovery listing -- expected: pass, with the new cases listed.
- `python3 tools/conformance-vectors/v1/check_enrolled.py --output <task-dir>` -- expected: `fullV1Accepted: true`.
- The split change's secret scan over `evidence/story-5-4/` -- expected: zero findings.

### Local implementation verification (2026-11-09)

> Historical snapshot before the redactor prerequisite and dedicated PR runs. The final CI qualification below supersedes its pending-live statements.

The story remains **in-progress**. The live boundary is compiled and discovered, but has not executed. The frozen redactor/secret-scan prerequisite prevents the committed CI run, final evidence binding and owner approval/verdict. No `fullLiveAccepted` or retirement verdict is claimed.

- Normal solution restore and Release build with `-warnaserror`: passed, zero warnings/errors (`/tmp/story54-restore.log`, `/tmp/story54-build-final.log`).
- Core: 877 succeeded, four Windows-only skips; final full CLI: 582 succeeded, two Windows-only skips (584 total), including all 26 new safety/process-harness cases; MCP: 94 passed. Logs: `/tmp/story54-core-tests.log`, `/tmp/story54-cli-final.log`, `/tmp/story54-mcp-tests.log`.
- Manifest: 362 passed with no skips, including unchanged dependency/fixture closure guards (`/tmp/story54-manifest-final.log`, `/tmp/story54-manifest-final.xml`). An earlier shared in-process project-reference attempt changed the reviewed fixture closure; it was removed before the successful run. The final live harness uses the existing ConformanceHost process and no new package or production project reference.
- New safety/process-harness tests: 26 passed, no skips (`/tmp/story54-head-tests-final.log`); the process cases exercise real CLI and stdio MCP success and 401 documents, every output channel and Gateway counts without topology.
- Generic runner: 27 Python cases passed; lane: 15 passed; plan/dependency checks: 38 passed. The first 94-case CI-hook run passed 90 and exposed four stale expectations for the added independent case; all four pass after correction (`/tmp/story54-ci-fixes.log`). The clean full sweep passed 203 cases (`/tmp/story54-python-final.log`); the later receipt-attribution fix and its additional test passed all 27 affected runner cases (`/tmp/story54-runner-final.log`). All 204 currently discovered cases are therefore covered by these successful runs.
- Preflight-only passed with `fullLiveAccepted: false` (`/tmp/mcpcli-story54-live-preflight/live-lane.json`). Discovery matched exactly every approved vector plus smoke and boundary: 23 cases today (`/tmp/story54-discovery.txt`). These checks start no live services.
- `check_enrolled.py --output /tmp/mcpcli-story54-enrolled` passed: Parties 1.5.1 (7 operations), Tenants 7.0.5 (14 operations), aggregate `fullV1Accepted: true` (`/tmp/mcpcli-story54-enrolled/enrolled.json`, `/tmp/story54-enrolled.log`). The 203-case full Python sweep and 27-case affected-runner rerun above passed. No production Core validation, Sample.Contracts or Gateway wire behavior changed, so sample conformance gates are not required by this implementation.

### Frozen matrix audit (historical implementation snapshot)

This table records coverage before dedicated CI qualification. The final executed coverage and remaining gaps are in `evidence/story-5-4/parity-matrix.md`.

`Safety` below means `tests/Hexalith.McpCli.Cli.Tests/PartiesRetirementSafetyTests.cs`; all named safety tests executed in the passing 26-case head run. `Live` means `SharedHeadBoundaryTests.SharedHeadsPreserveAuthorizationAndDeactivationSafety`; it is built/discovered only. Every offline refusal checks complete stdout/stderr, MCP Content/StructuredContent and Gateway request cardinality.

| Frozen row | Covering test / evidence | Live status |
| --- | --- | --- |
| No token | `Safety.CredentialRefusalsPreserveTheCompleteGatewayErrorAsync`, 401/null token, Command and Query | Live not run—redactor prerequisite; designed authorized before/after reads and absent Authorization header |
| Invalid token | Same test, 401/forged credential, both call kinds; process harness also passes 401 through each head | Live not run—redactor prerequisite; signed wrong-key control |
| Unauthorized principal | Same test, complete 403 documents; Live covers tenant-A/no-grant principals and allowed per-call override | Live not run—redactor prerequisite; no persisted Parties-membership claim |
| Override disabled | `Safety.DisabledMcpOverrideMakesNoGatewayCallsAsync`, both call kinds | Live not run—redactor prerequisite |
| Platform scope as tenant | `Safety.PublicTenantNegativesHaveNoGatewayCallsAsync`, session and MCP per-call input, both call kinds | Live not run—redactor prerequisite |
| Reserved tenant | Same test, `system` and `SYSTEM`, both call kinds and tenant sources | Live not run—redactor prerequisite |
| Look-alikes | Same test, Cyrillic a, U+0130 and fullwidth tenant, both call kinds and tenant sources | Live not run—redactor prerequisite |
| F7 limitation | `Safety.AcceptedF7Item9KelvinAliasReachesTheGatewayAsAsciiAsync`, exact `kelvin` wire value through both heads | Accepted offline limitation pin; item 9 stays open |
| Restricted names | `Safety.RestrictedNamesCannotBeDiscoveredOrAuthorizedByConfirmAsync`, every inventoried Admin name and six excluded Tenants names, with/without confirm, both heads/call kinds | Offline zero-call guard passed; no live restricted mutation is attempted |
| C05 missing | Live uses a different never-created target per head, 404/`party-not-found`, authorized absence read plus persisted creation/deactivation exclusion | Live not run—redactor prerequisite |
| C05 concurrent repeat | Live starts two CLI processes once each, asserts distinct message IDs, authorized inactive state and exactly one persisted deactivation event | Live not run—redactor prerequisite |

All final local logs and the Manifest XML, discovery listing and summary receipts are preserved under `/tmp/mcpcli-story54-verification/`. `git diff --check` passed. The committed live run, evidence manifest/variant matrix/scan receipt and owner verdict remain unchecked tasks under the frozen prerequisite.

### Fresh revalidation of the existing implementation (2026-11-09)

The implementation already present at `1c18a42aa9439bfc29009951f29968cac2a71436` satisfies the local execution tasks; no additional production, test, runner, dependency or approved-input changes were necessary. Fresh checks passed:

- Solution restore and Release build with `-warnaserror`: zero warnings or errors.
- Core: 877 succeeded, four Windows-only skips; CLI: 582 succeeded, two Windows-only skips; MCP: 94 passed; Manifest: 362 passed. The four projects ran one at a time.
- Complete live-topology Python sweep: all 204 tests passed in 569.967 seconds.
- Preflight-only: passed with `fullLiveAccepted: false`; discovery matched exactly the 21 approved vectors plus independent smoke and shared-head boundary (23 cases).
- Enrolled gate: both exact artifact replays and the combined production-manifest replay passed, with 21 operations and `fullV1Accepted: true`.

Fresh command logs are `/tmp/story54-current-{restore,build,Core,Cli,Mcp,Manifest,python,preflight,enrolled}.log`; discovery is `/tmp/story54-current-discovery.txt`. Receipts are under `/tmp/mcpcli-story54-current-live-preflight/` and `/tmp/mcpcli-story54-current-enrolled/`. No live topology was started. The story remains **in-progress**: the separate redactor/committed-secret-scan prerequisite still prevents the committed live run, final hash-bound evidence set and exact-byte owner approval/verdict.

### Separate prerequisite completed (2026-11-09)

`epic-4-retro-item-5-harden-ci-redaction` now supplies the shared Python redactor
and committed evidence scanner, verified separately in
`evidence/epic-4-retro-item-5/verification.md`. The preceding revalidation note
records the state before that prerequisite. Story 5.4 remains **in-progress**:
its dedicated live CI run, final hash-bound packet and its own scan receipt, and
exact-byte owner approval/verdict remain pending. This prerequisite's receipt
does not establish Story 5.4 live acceptance or authorize retirement.

### Committed live qualification follow-up (2026-11-09)

The prior CI run `42614718738` passed all 21 approved live vectors and the
independent smoke, then exposed a boundary-test assertion defect before its
negative cases ran: the qualified Gateway includes a business `resultPayload`
on create acceptance, while the test expected an acceptance document without
`result`. The boundary now checks the complete copied result against the
captured response and exact submitted identifiers. Concurrent acceptances are
paired with their originating requests. The process-harness regression runs
both heads with and without the optional result; it preserves every public
channel and request-count assertion. Production behavior and approved inputs
are unchanged. A fresh dedicated PR lane is required; the failed historical
lane establishes no full live acceptance.

CI preparation now retains `head-catalog.json`: equal CLI/MCP discovery from
the actual hosted binaries, every head DLL hash, each module's sorted-key
compact `list_operations` structured-content SHA-256, and the digest of the
complete module-to-content map. This generic read-only capture supplies the
final packet's exact candidate/Catalog binding without relying on a local
rebuild. Offline tests cover discovery failure/mismatch, empty Catalog and
binary drift; CI-hook coverage pins the bounded capture and failure path.

Fresh local follow-up checks passed: solution restore and Release build with
zero warnings/errors; Core 877 passed (four OS skips), CLI 584 passed (two OS
skips), MCP 94 passed and Manifest 362 passed. The six process-harness cases,
seven capture-helper regressions and focused CI capture/failure-path case all
passed. Full affected CI-hook verification continues before final evidence.

### Qualified authentication oracles and early boundary (2026-11-09)

PR run `42631573309` passed every vector and smoke, then reached a second
boundary oracle defect: public EventStore 4.1.0 sends structured 401 errors,
not a bare HTTP reason phrase. Its pinned `ConfigureJwtBearerOptions` supplies
reason `authentication_required`, distinct missing/invalid-token details and
no correlation field. The boundary now pins those complete documents and the
two exact tenant-grant 403 shapes from `AuthorizationExceptionHandler`.
Eight new process cases exercise all four shapes for Commands and Queries
through CLI and MCP, including every channel and Gateway cardinality.

The generic pre-vector independent-case registry now runs the boundary once
before the long vector sweep; a failed boundary stops there. The post-vector
registry retains smoke, including after vector failures. Preparation provenance
is rechecked after the early case because it may rebuild hosts. Counts and
budgets remain derived from the combined registry. Focused CI-hook checks pin
the new order, refusal before vectors, post-boundary drift and the existing
vector/smoke failure and cancellation behavior. Production behavior, identifier
validators, dependencies and approved inputs remain unchanged.

The Release build passes with zero warnings/errors; all 14 process-harness
cases pass; the full CLI project passes 592 cases with two OS-only skips.
Five focused ordering/failure/cancellation checks and the new early-drift
check pass. Broad CI-hook verification continues while the next PR candidate
is qualified. Prior attempt receipts remain distinct from its final packet.

### Empty 401 transport response (2026-11-09)

Run `42641067905` passed the Query credential/grant cases, then found an empty
401 response for the forged-token Command; the early boundary correctly kept
vectors unrun. The generic client already maps that exact HTTP fallback to
`gateway_error`, status 401 and detail `Unauthorized`, without a reason field.
The boundary now asserts that complete fallback for an empty body and retains
the pinned structured challenge for every nonempty body. Live credential
receipts record the response format and full public error, and missing-token
CLI/MCP documents are compared directly per call kind. Four more process cases
pin empty missing/invalid-token challenges through both heads and call kinds.
The clean 99-test CI-hook sweep passed; production behavior remains unchanged.

### Command grant refusals before the structured pipeline (2026-11-09)

Run `42645969397` then exposed the first tenant-A-grant Command returning an
empty 403. Qualified EventStore `dbc6e7e08d605ba6c6c790e3e08a15dc8bbdec8a`
`CommandsController.cs:146-149` returns `Forbid()` before pipeline dispatch for
missing tenant grants. The boundary now pins its whole existing public
`gateway_error` / 403 / `Forbidden` fallback, including absent optional members;
Query refusals retain the complete structured tenant-mismatch/nonmember oracle.
Four additional both-head process cases cover the empty 403 transport for both
call kinds and both signed-grant scenarios. Vectors stayed unrun after the early
boundary failure. No production behavior, approved input or runner changed.

### Discovered sidecar endpoint for persisted C05 evidence (2026-11-09)

Run `42648730822` passed the credential, override and tenant-negative rows, then
found the C05 state helper’s fixed-port assumption (`127.0.0.1:3501`). The
restored fixture helper exposes no supported sidecar application object. The
fixture now discovers exactly one `eventstore` sidecar through bounded
`dapr list --output json` inside the already-required isolated namespace and
passes its actual HTTP client to both persisted-state oracles. The separate
`DAPR_API_TOKEN`, when configured, is preserved; no bearer credential is sent
to the sidecar API. Offline regressions require an ephemeral discovered port,
reject missing/duplicate/invalid registrations and prove both C05 helpers read
the expected state keys with and without the API token. No runner, production
source, approved input or dependency changed.

### Final CI qualification and owner approval (2026-11-09)

Candidate `3e8f6a4e681018c7ca8356997d4fd28378217d37` passed CI run `42652261452` on draft PR #5. All 21 approved vectors, independent shared-head boundary and Gateway smoke passed; both live Query heads are required and each live Command is submitted once. Hosted `check_enrolled.py` reports `fullV1Accepted: true`; live receipts report `fullLiveAccepted: true`. All 216 hosted topology checks passed and discovery matched the 21 vectors plus the two independent cases. The six ordinary projects passed 1,985 tests with six OS-only skips; Manifest and enrolled inventory checks remain unchanged.

The latest Release build has zero warnings/errors. All 77 named offline safety, compatibility, process and identity cases passed without skips, including 22 process cases through both heads. The clean 99-hook sweep applies to unchanged Python source. Initial failing sweeps and earlier live attempts retain their own status and exact artifact bindings; none is promoted into final acceptance.

The complete packet is `evidence/story-5-4/`: manifest, C01–C08/seven-variant matrix, F7 acceptance, source audit, full text receipts and logs, verification and secret scan. It binds the actual hosted checkout and equal candidate tree, every head DLL, exact Catalog content, Contracts artifact, environment/source revisions, approved inputs, CI run/artifact digests and retained text hashes. The source audit clearly distinguishes upstream tests at the enrolled revision from tests executed in this run. Production source, dependencies, identifiers, approved vectors/plans/approvals/inventories and reference gitlinks are unchanged.

**The exact-byte owner checkpoint is complete.** The owner answered exactly `approve` to the request bound by scan-receipt SHA-256 `1edc78fd37ede85498e7d8a9a7b1ea3537175bb470259a729bf0a8a8aa1ac0c3`, approving the verdict `retirement-blocked` and retaining G01–G06 as blocking with their named ledger owners. `evidence/story-5-4-owner-approval/owner-approval.json` records the response, original commit and digest bindings, and each retained gap disposition. Every original `evidence/story-5-4/` byte and its scan remain unchanged; their pending-owner text is the historical pre-approval snapshot. No inventory 1.3.0 amendment, release, publication or retirement is approved.

Implementation tasks are complete under the approved `retirement-blocked` verdict. The workflow status remains unchanged pending the normal review transition. The separate approval packet’s `verification.json`, `verification.md` and `secret-scan.json` record binding, snapshot-preservation and hygiene checks.

### Build completion (2026-11-10)

The owner’s verbatim `approve` response binds the original scanned snapshot and verdict `retirement-blocked`, keeping G01–G06 open. The separate owner receipt and its scan remain unchanged. Review pass 1 classified every finding individually, resolved seven patch groups, rejected the contradictory MCP-concurrent claim, and recorded six pre-existing redactor/scanner root causes for separate follow-up. No inventory amendment or release/retirement authorization was added.

Post-review code commit `4ddfedbca7be2922c109c9cedc1ffc6dbe1bf82d` passed CI `42711210249`, including the strengthened live boundary. The current local restore/Release build, Core, CLI, MCP, Manifest, 194 release-script, 164 conformance and 218 topology Python tests, preflight and fresh enrolled replay all pass. The supplemental evidence documents the stricter guards without modifying or claiming additional owner approval for the original packet. The spec is done; sprint tracking is advanced to review per the Build workflow. Story 5.5 retirement remains blocked by the six retained gaps.

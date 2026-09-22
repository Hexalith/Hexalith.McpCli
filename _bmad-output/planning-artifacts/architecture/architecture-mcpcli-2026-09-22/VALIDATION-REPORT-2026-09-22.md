Gate verdict: **FAIL — the architecture spine is not safe for implementation or release planning until its Critical and High findings are resolved and the gate is rerun.**

# Architecture validation report — Hexalith.McpCli

**Validated:** 2026-09-22  
**Target:** [`ARCHITECTURE-SPINE.md`](ARCHITECTURE-SPINE.md), lines 1–333  
**Intent:** standalone Validate; critique only

## Executive decision

The spine is mechanically clean and its central hexagonal boundary, catalog ownership, executor sequencing, dependency closure, packaging direction, and v1 runtime envelope are strong. It nevertheless conflicts with the binding PRD on idempotency and public documents, specifies two unimplementable integration-test guarantees, relies on a nonexistent composition package, and leaves several head/executor/release seams capable of divergent implementations.

**Implementation recommendation:** hold story breakdown and implementation that depends on this spine. Resolve all four Critical and seven High findings first; incorporate the Medium/Low autofixes and decisions into the same update or explicitly defer only where a finding permits it with an owner, operating constraint, and revisit gate. Then rerun deterministic lint and all three review lenses.  
**Release recommendation:** do not approve a v1 release plan from the current spine; its harness and release transaction do not yet prove that the promised artifacts and cross-head behavior can be produced.  
**Mutation statement:** this standalone validation did **not** change `ARCHITECTURE-SPINE.md`, `.memlog.md`, the PRD, its addendum, or any source review.

## Coverage and counts

| Gate component | Result | Coverage |
| --- | --- | --- |
| Deterministic lint | **Pass** | `ok=true`, 0 findings; placeholders, duplicate AD IDs, missing Binds/Prevents/Rule, and unpinned Stack versions were checked. |
| [Good-spine rubric review](reviews/review-validation-20260922-rubric.md) | **Fail** | Divergence points, enforceability, Deferred safety, source coverage, brownfield fit, named technology, and owned dimensions. |
| [Technology/reality review](reviews/review-validation-20260922-tech-reality.md) | **Needs update** | Current package versions, official MCP/.NET APIs, EventStore source behavior, packaging, and still-unlanded prerequisites. |
| [Adversarial seam review](reviews/review-validation-20260922-adversarial.md) | **Fail** | Counterexamples in which independently built units obey the ADs yet remain incompatible. |

No parent spine is declared. The binding sources are the final PRD and its normative addendum; brownfield evidence includes repository guidance, central package pins, and current EventStore, Tenants, and Parties checkouts.

| Severity | Raw reviewer findings | Consolidated findings |
| --- | ---: | ---: |
| Critical | 4 | 4 |
| High | 8 | 7 |
| Medium | 9 | 8 |
| Low | 2 | 1 |
| **Total** | **23** | **20** |

Deduplication preserves every source ID. `RV-RUB-004` + `ADV-004`, `RV-RUB-005` + `ADV-005`, and `RV-RUB-011` + `TR-004` are the three merged groups; consolidated severity is the highest contributing severity.

## Critical findings

### VAL-001 — The spine generates an idempotency key that the final PRD forbids

- **Severity:** Critical
- **Source-review IDs:** `RV-RUB-001`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:83,107,189` makes `IdempotencyKey` unconditional and says the executor accepts or generates one. The binding source says it is optional and caller-supplied only: `../../prds/prd-mcpcli-2026-09-21/prd.md:103-105,338-354,523-532` and `../../prds/prd-mcpcli-2026-09-21/addendum.md:192-196,277-283`.
- **Why it matters:** executor stories can implement incompatible retry and payload-fill semantics, and a generated key weakens the product's explicit no-generic-safe-retry guardrail.
- **Recommended disposition:** **autofix** — generate only `MessageId`; use it as the omitted correlation ID; keep `IdempotencyKey` absent unless supplied, including Payload overwrite and result serialization.

### VAL-002 — AD-5 does not bind the exhaustive public document and error contract

- **Severity:** Critical
- **Source-review IDs:** `RV-RUB-002`
- **Exact evidence:** the shorthand records and discriminators at `ARCHITECTURE-SPINE.md:79-83,107,183-185` diverge from exhaustive success, error, type, constraint, and omission rules at `../../prds/prd-mcpcli-2026-09-21/addendum.md:277-307,335-341,362-396` and `../../prds/prd-mcpcli-2026-09-21/prd.md:206-229,254-285,382-390`. Examples include an extra public `diagnostics`, missing `lintFindings`/envelope flags, missing command/query members, nullable required `document`, incomplete gateway-error variants/status preservation, wrong lint-code names, and the unsupported `unsupported_format` discriminator.
- **Why it matters:** Core records, MCP schemas, CLI rendering, and snapshot fixtures can all comply with AD-5 yet disagree with one another and fail FR-11.
- **Recommended disposition:** **autofix** — bind typed records exactly to addendum §G, including required/optional members, constraints, omission rules, exhaustive errors, and public codes; keep catalog diagnostics off `list_modules`.

### VAL-003 — Raw live cross-head equality is impossible for Commands

- **Severity:** Critical
- **Source-review IDs:** `ADV-001`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:83` requires `JsonElement.DeepEquals`; `:107,189` generates volatile identifiers per call; `:145-149` drives CLI and MCP as separate out-of-process calls against one live topology and requires equality for every Operation.
- **Why it matters:** two compliant Command calls necessarily use different identifiers and may mutate the same aggregate twice, fail on changed state, or alter later Query results. Calling once no longer tests both heads.
- **Recommended disposition:** **discuss** — decide between a deterministic fake/capture-replay protocol-parity lane plus a once-only live semantic lane, or a precisely defined normalization/fixture-isolation contract. Do not retain raw equality over two live Command executions.

### VAL-004 — The generic harness has no compliant source of accepted production inputs

- **Severity:** Critical
- **Source-review IDs:** `ADV-002`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:67-71,79-83` permits but does not require an Operation example; `:139-149` prohibits Module implementation dependencies/module-specific `src/` code yet requires accepted Commands and returned Query documents for every Tenants and Parties Operation.
- **Why it matters:** schema-shaped placeholders cannot satisfy arbitrary domain preconditions, while hard-coded setup violates the generic dependency boundary. No implementation can guarantee the stated gate for every valid decorated Operation.
- **Recommended disposition:** **discuss** — require versioned Module-owned conformance vectors (valid Payload, Envelope, setup/preconditions, and semantic assertions) at an explicitly allowed boundary, or narrow AD-16 when examples remain optional.

## High findings

### VAL-005 — AD-16 depends on a nonexistent `Hexalith.Parties.Aspire`

- **Severity:** High
- **Source-review IDs:** `RV-RUB-003`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:139-149,212` requires and pins the package. It is absent from `references/Hexalith.Builds/Props/Directory.Packages.props:80-88,97`, `references/Hexalith.Parties/tools/release-packages.json:1-40`, and `references/Hexalith.Parties/Hexalith.Parties.slnx:23-36`; the current AppHost instead composes the domain project directly at `references/Hexalith.Parties/src/Hexalith.Parties.AppHost/Hexalith.Parties.AppHost.csproj:14-19` and `Program.cs:90-103`. The affected commitment is `../../prds/prd-mcpcli-2026-09-21/prd.md:395-403,423-430`.
- **Why it matters:** the v1 harness cannot restore or compose both required Modules as written, so FR-20/NFR-7 cannot close.
- **Recommended disposition:** **discuss** — make a published helper an owned upstream prerequisite or bind another test-only composition path that preserves the no-module-server-package boundary; remove the fictitious pin.

### VAL-006 — Offline discovery and execution availability use incompatible Gateway-URL state

- **Severity:** High
- **Source-review IDs:** `RV-RUB-004`, `ADV-004`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:67-71` derives `submittable` only from Read-only Mode, while `:109-113,127-131,257-262` consumes a URL and calls its absence `configuration_invalid` without a discovery boundary. The source requires offline startup/discovery, execution-only failure, and `read_only` precedence: `../../prds/prd-mcpcli-2026-09-21/addendum.md:207-219,416-424` and `../../prds/prd-mcpcli-2026-09-21/prd.md:254-261,301-309,523-532`.
- **Why it matters:** one head can advertise `submittable: true`, another can refuse startup, and the executor can fail after discovery promised an available path.
- **Recommended disposition:** **autofix** — introduce one immutable Core-owned execution-availability value used by describe and executor preflight; a missing URL must not prevent host construction or catalog-only behavior.

### VAL-007 — MCP tool registration conflicts with the live SDK dispatch/list model

- **Severity:** High
- **Source-review IDs:** `TR-001`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:121-125` constructs tools and specifies a custom list handler but no compatible dispatch ownership. ModelContextProtocol 2.2.0 appends registered tools to custom-list results and uses the registered collection for calls: [ConfigureTools](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerImpl.cs#L1464-L1527), [ToolCollection](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol.Core/Server/McpServerOptions.cs#L145-L156), and [WithListToolsHandler](https://github.com/modelcontextprotocol/csharp-sdk/blob/v2.2.0/src/ModelContextProtocol/McpServerBuilderExtensions.cs#L600-L630).
- **Why it matters:** registering and custom-listing duplicates tools and re-advertises `send_command` in Read-only Mode; not registering removes automatic call dispatch.
- **Recommended disposition:** **discuss** — bind either one filtered `ToolCollection` with built-in list/call dispatch, or a null collection plus custom list and call handlers over the same map; test uniqueness, fixed order, and Read-only omission.

### VAL-008 — AD-9 models only one of the Gateway's two extension-validation layers

- **Severity:** High
- **Source-review IDs:** `TR-002`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:103-107` binds the structural 50-entry/65,536-byte rules from `references/Hexalith.EventStore/src/Hexalith.EventStore/Validation/SubmitCommandRequestValidator.cs:17-20,81-91`. The pinned gateway additionally invokes a configurable sanitizer at `references/Hexalith.EventStore/src/Hexalith.EventStore/Controllers/CommandsController.cs:90-110`, whose defaults are 32 entries/4,096 bytes at `.../Configuration/ExtensionMetadataOptions.cs:7-28` and whose grammar/injection checks are at `.../Validation/ExtensionMetadataSanitizer.cs:28-100,117-135`.
- **Why it matters:** inputs accepted by Core can predictably fail at the default gateway, contradicting the claimed complete pre-validation contract; configured gateways may differ again.
- **Recommended disposition:** **discuss** — choose a fixed stricter McpCli contract, operator-matched settings, or ordinary `gateway_error` treatment for sanitizer rejection; if zero predictable calls is the goal, bind the effective default intersection and configuration-drift policy.

### VAL-009 — The MCP output schema is not a valid exclusive success/error union

- **Severity:** High
- **Source-review IDs:** `ADV-003`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:79-83` requires error-only failure objects, while `:121-125` defines one closed object with required success properties plus an optional `error` property.
- **Why it matters:** keeping success fields required rejects `{ "error": ... }`; making them optional admits `{}` and mixed success/error objects. Independently built schema and adapter stories therefore cannot converge.
- **Recommended disposition:** **autofix** — define `oneOf` two closed branches: the exact success record, or `{ error: OperationError }` with required `error`; generate schema and structured content from the same Core-owned public-document contract.

### VAL-010 — The synthetic fixture violates cardinality and has no multi-Module ownership rule

- **Severity:** High
- **Source-review IDs:** `RV-RUB-005`, `ADV-005`
- **Exact evidence:** the assembly-level marker/catalog model at `ARCHITECTURE-SPINE.md:67-71,179-180` conflicts with one `Sample.Contracts` assembly declaring `sample-ulid` and `sample-opaque` at `:193,238`; AD-15 simultaneously calls it the only synthetic Module at `:143`. The final handoff requires one declared sample Module and isolated construction of the other Identifier Kind: `../../prds/prd-mcpcli-2026-09-21/prd.md:423-424,523-529`.
- **Why it matters:** multiple assembly markers provide no rule mapping decorated types to a Module, so builders can reject, duplicate, or namespace-partition Operations differently; the benchmark also violates its binding population.
- **Recommended disposition:** **autofix** — keep one Module in `Sample.Contracts`, select its Identifier Kind, and cover the other through isolated catalog construction; if multiple Modules per assembly are intended instead, add an explicit discriminator and collision rules.

### VAL-011 — The release rule can pass build without producing releasable packages

- **Severity:** High
- **Source-review IDs:** `ADV-006`
- **Exact evidence:** `ARCHITECTURE-SPINE.md:151-155` names `dotnet build`, the two-package manifest, and push but no pack/validation/install transaction; `:214-223` contains no release script seed, while `:257-261` says semantic-release packs and pushes.
- **Why it matters:** SDK default `GeneratePackageOnBuild=false` allows the exact named build to succeed with no `.nupkg`; separate release implementations can both claim compliance while only one creates and verifies the promised artifacts.
- **Recommended disposition:** **autofix** — bind the exact pack/script transaction, two expected IDs at one version, NuGet/consumer validation, secret/publication preflight, push, and an isolated local-source tool-install smoke test that runs `hexalith --version` plus an offline command.

## Medium and Low tail

The tail is compact, but every reviewer finding remains represented with evidence, impact, and a disposition.

| ID | Severity | Source-review IDs | Exact evidence | Why it matters | Recommended disposition |
| --- | --- | --- | --- | --- | --- |
| `VAL-012` | Medium | `RV-RUB-006` | `ARCHITECTURE-SPINE.md:121-125,187` omits the pre/post-initialize lifecycle required at `../../prds/prd-mcpcli-2026-09-21/prd.md:267-285` and `../../prds/prd-mcpcli-2026-09-21/addendum.md:362-368`. | Startup stories can emit incompatible process behavior or corrupt the stdout JSON-RPC channel. | **autofix:** bind validation before initialize, exactly one structured stderr error, zero stdout bytes, exit 2; after initialize, failures use MCP only. Test malformed settings, empty catalog, and `mcp --strict`. |
| `VAL-013` | Medium | `RV-RUB-007` | `ARCHITECTURE-SPINE.md:41-45` assigns every FR-13–FR-19 rule to Core, contradicting adapter allocations at `:121-137,186,190`. | A builder must either violate AD-1 or drag/duplicate protocol concerns in Core. | **autofix:** limit Core to shared settings values, catalog, validation, execution, and result/error records; reserve transport, advertisement, exit codes, rendering, and protocol carriage for adapters. |
| `VAL-014` | Medium | `RV-RUB-008` | `ARCHITECTURE-SPINE.md:133-137,315` freezes verb names but defers flags and mutation/error behavior to a future copy; source surfaces are `../../prds/prd-mcpcli-2026-09-21/prd.md:382-390`, `../../prds/prd-mcpcli-2026-09-21/addendum.md:199-246`, and `AGENTS.md:90-95`. | Independently implemented config verbs can drift on argument names, overwrite rules, token masking, and errors. | **autofix:** freeze against a pinned Admin CLI revision or enumerate remaining flags and semantics; defer only presentation-local details. |
| `VAL-015` | Medium | `RV-RUB-009` | `ARCHITECTURE-SPINE.md:47-64,139-143` requires Contracts to reference `Hexalith.McpCli.Abstractions` but omits it from a set called the exact Hexalith allowlist; the source distinction is `../../prds/prd-mcpcli-2026-09-21/prd.md:95-104,523-529`. | A literal closure test rejects the Decoration Package; a loose exemption can admit other in-repo dependencies. | **autofix:** define Abstractions separately as an allowed first-party artifact, then enforce the external Hexalith/domain allowlist independently. |
| `VAL-016` | Medium | `RV-RUB-010` | `ARCHITECTURE-SPINE.md:145-149,257-261` requires root-submodule checkout/build, but `:317-320` leaves workflow inputs to the harness story; repository bounds are `AGENTS.md:47-61`. | AppHost, integration-test, and workflow stories can assume different source availability/build ownership and accidentally use forbidden recursive updates. | **discuss:** bind exact `domain-ci.yml` inputs, root-submodule contract, and absent-source failure, or name an upstream workflow prerequisite with owner and revisit gate. |
| `VAL-017` | Medium | `TR-003` | `ARCHITECTURE-SPINE.md:85-89` claims PascalCase/case-sensitive options reflect EventStore writers. Readers actually use web defaults at `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Serialization/EventStorePayloadSerialization.cs:5-17,30-43`; generated REST writers use web defaults at `references/Hexalith.EventStore/src/Hexalith.EventStore.RestApi.Generators/RestApiControllerEmitter.cs:236,266-272`, while other writers differ. | A deliberately stricter McpCli input contract is being justified as external necessity, hiding compatibility cost. | **discuss:** retain it only as an explicit McpCli wire decision with tests/cost, or align with EventStore readers/Module provider behavior. |
| `VAL-018` | Medium | `RV-RUB-011`, `TR-004` | `ARCHITECTURE-SPINE.md:196-212` says `13.5.1-beta (catalog pin)`; the exact local pin is `13.5.1-beta.757` at `references/Hexalith.Builds/Props/Directory.Packages.props:151`, and the package exists at [NuGet](https://www.nuget.org/packages/CommunityToolkit.Aspire.Hosting.Dapr/13.5.1-beta.757). | The claimed exact pin is a different NuGet identifier and is not independently published as written. | **autofix:** use `13.5.1-beta.757`, or state that the dependency is transitive and version-owned by `Hexalith.EventStore.Aspire`. |
| `VAL-019` | Medium | `ADV-007` | `ARCHITECTURE-SPINE.md:115-119,133-137,192` gives one ProfileStore a secret-bearing mutable file and final 600/700 modes but no atomic mutation, cross-process lock, restrictive creation mode, symlink rule, or recovery contract. | Concurrent verbs can silently lose updates; write-then-chmod can transiently expose a token; interrupted writes can corrupt the only state store. | **autofix:** expose one transactional mutation API; serialize writers; create a same-directory restrictive temp file, flush and atomically replace; reject symlink/non-regular targets; define recovery and tests. |
| `VAL-020` | Low | `TR-005` | `ARCHITECTURE-SPINE.md:97-101,189` says `Ulid.TryParse`; ByteAether.Ulid 1.4.1 exposes the provider-bearing form documented in the [official repository](https://github.com/ByteAether/Ulid#parsing) and [NuGet](https://www.nuget.org/packages/ByteAether.Ulid/1.4.1). | The common two-argument notation fails compilation (`CS1501`) and leaves the implementation convention ambiguous. | **autofix:** spell `Ulid.TryParse(value, provider: null, out _)`, or use `Ulid.IsValid(value)` for validation-only sites. |

## Gate exit criteria

An updated spine is ready for revalidation when it:

1. conforms to the PRD's caller-supplied-only idempotency and exhaustive §G document contract;
2. replaces the impossible live equality and generic-input requirements with implementable, owned test contracts;
3. resolves the Parties composition, offline availability, MCP registration/schema, Gateway extension, fixture, and release-transaction seams;
4. incorporates or explicitly and safely defers every Medium/Low item; and
5. again passes deterministic lint plus the rubric, technology/reality, and adversarial reviews.

Until then, the correct gate state is **FAIL / update required**, and the reviewed spine remains unchanged.

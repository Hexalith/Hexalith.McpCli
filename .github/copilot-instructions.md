# AI Assistant Instructions

This is a location-independent baseline. Its normalized text is intentionally
shared by Codex, Claude, Cursor, and GitHub Copilot entry points in the
superproject and its root-declared submodules. It contains shared safeguards
only; repository documentation and configuration remain authoritative for
repository-specific rules.

## Required Hexalith LLM Baseline

Before working in a Hexalith repository, locate, read, and follow
`hexalith-llm-instructions.md`.

- If the current repository contains that file at its root, read that copy.
- Otherwise, use `git rev-parse --show-superproject-working-tree` to locate an
  enclosing superproject. When it returns no path, use the current repository
  root as the workspace. Then read
  `<workspace>/references/Hexalith.AI.Tools/hexalith-llm-instructions.md`.
- Before using that workspace copy, confirm its root `.gitmodules` declares
  `references/Hexalith.AI.Tools` as a root submodule.
- Do not initialize or update a nested submodule to locate this file. If no
  permitted location exists, stop and report the missing baseline as a blocker.

## Working in a Repository

- Work from the repository that owns the change.
- Before changing code, configuration, data, or documentation, inspect the
  relevant tracked repository guidance and configuration, including build files,
  `.editorconfig`, `.gitattributes`, tests, and architecture documentation.
- Preserve user changes. Do not revert, overwrite, clean, stage, commit, push,
  branch, or update dependencies unless the task explicitly requires it.
- Validate changes with the narrowest relevant checks and report any blocker
  with the exact command and result.

## Agent Skills

- A repository-local agent skill is a `SKILL.md` manifest and its supporting
  files.
- Never discover, load, or execute an agent skill located in a repository's
  `references/` directory. This restriction does not prevent reading ordinary
  source files or documentation in that directory when the task requires it.
- If a requested skill is available only from `references/`, explain that it is
  unavailable and use an allowed alternative.

## Git and Submodules

- Before Git work, inspect the current repository's branch, working tree,
  remotes, and recent history.
- Any commit message an assistant creates, suggests, or uses, including Claude,
  Codex, Cursor, GitHub Copilot, and supported Visual Studio Copilot commit-message
  generation, must follow Conventional Commits and satisfy both the owning
  repository's effective commitlint policy and its tracked Git guidance.
- Before presenting or using a message, an assistant capable of running repository tooling must validate the exact full candidate with the owning repository's pinned commitlint CLI and preserve successful validation evidence.
  If validation rejects the candidate, report the rule violations, revise the message, and revalidate it; if the validator cannot run, report the exact command and blocker and do not present or use the candidate until validation succeeds. Never bypass commit validation.
- When repository instructions are enabled, Visual Studio 2026 version 18.6 and later reads `.github/copilot-instructions.md`; older, disabled, or unsupported cases are not controlled by this file.
  These instructions guide generation but cannot execute commitlint or guarantee compliance; the installed commit-message hook and blocking CI commitlint gate remain enforcement layers.
- In an umbrella workspace, initialize or update only dependencies declared by
  the top-level workspace `.gitmodules` file.
- Never initialize or update a submodule's nested submodules unless the user
  explicitly requests that nested work. Never use recursive or remote submodule
  updates by default.
- If nested submodules were initialized accidentally, deinitialize them before
  continuing.

## Shared Entry Points

- Keep `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`
  synchronized as normalized text when intentionally updating this shared
  baseline.
- Keep repository-specific instructions in repository documentation or
  configuration, not in these universal entry points.

<!-- bmad:context -->
<!-- Full context verified 2026-10-10 against 5bc23e5bd36c4b10e6f19e5233e27dcc80466357; five deferred guidance corrections verified 2026-10-28 against 5aa3ee23ef4b395a4500453a50d4815e9837dd07. Scope/profile rules reconciled 2026-11-06 through the approved sprint change proposal. CLI, scope, regex and live-test guidance verified 2026-11-23 against 292641ce923e897f240666304a67abbd51cc523d. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## Hexalith.McpCli

One generic MCP server and one thin CLI, both driven by a catalog of commands and queries discovered from decorated `*.Contracts` assemblies and submitted through the EventStore gateway client. .NET 11 targets with SDK 11.0.100 minimum, ModelContextProtocol 2.4.0, System.CommandLine 3.0.0, xUnit v3; package versions use the central catalog in `references/Hexalith.Builds/Props/Directory.Packages.props`, with EventStore, Parties, and Tenants pins set first in root `Directory.Build.props`. Planning (brief, PRD, architecture spine, epics) lives in `_bmad-output/planning-artifacts/`; story specs and the deferred-work ledger in `_bmad-output/implementation-artifacts/`.

## Policy

- Dependency allowlist: `tools/dependency-policy.json` (approved production packages, the exact restored closure, enrolled modules, and separate `testPackages` allowances), enforced by `DependencyPolicyTests` in `tests/Hexalith.McpCli.Manifest.Tests`. Never reference another module's aggregate, projection, handler, client, or server project or package from production `src/`. Test projects may reference approved packages and repository-owned projects. The test AppHost uses published server-free Aspire helpers, and the integration fixture has a separately reviewed package closure. At runtime the AppHost can launch the Tenants checkout with `AddProject`. The qualified native lane launches prepared Gateway, Tenants and Parties resources. These launches add no sibling MSBuild `ProjectReference`.
- Zero module-specific implementation in production `src/`. Test-only composition in `tests/Hexalith.McpCli.AppHost` and assertions in `tests/Hexalith.McpCli.Integration.Tests` may name EventStore, Tenants, and Parties. Keep the runners in `tools/live-topology/` generic; change module behavior upstream.
- Enrollment requires a versionless `PackageReference` marked `HexalithContracts="true"` in `src/Hexalith.McpCli/Hexalith.McpCli.csproj`, its exact version under `modules` in `tools/dependency-policy.json`, a release inventory at `tools/inventory-coverage/v1/<module>-approved.json`, and vectors that cover every Operation Shape, with `tools/conformance-vectors/v1/current/modules/<PackageId>/approval.json` binding only the inventory and vector hashes (a top-level `artifactHash` fails; restored-package integrity binds the artifact). The original `v1/modules`, `plans`, `native-runtime.json` and gateway provenance remain historical; the current cohort has separate vectors, plans, native selection and provenance. Only `tests/Hexalith.McpCli.Core.Tests/OperationShape.cs` derives a shape; Python treats its key as opaque. An uncovered shape, duplicate or stale vector fails; a version difference or an operation no inventory row mentions is reported (`reported: …` on stderr and a `reported` array), never failed. Each declared Operation kind needs at least one approved vector with a hash-bound companion plan in `tools/live-topology/plans-current/`; a vector without a plan is loopback-only and a plan without a vector fails. Decoration is the owner's consent to expose an operation without human confirmation; never enforce it with name heuristics. Follow README "Gateway boundary" and the inventory/vector tool READMEs for approval, the new-enrollment live Command scenario and v1 scope-count updates; never pin a shape or module count in gate code.
- Tenant comes from the envelope, never from payload: an operation's exact declared `PlatformScope` first, else the Module's exact `FixedTenant`, else the canonical public session/per-call tenant. A platform scope cannot coexist with `FixedTenant`; any per-call value must exactly match either declaration, and the session tenant is ignored for that operation. For variable-scope operations, lowercase session and MCP per-call input invariantly without trimming before selection and override comparison. A differing per-call tenant replaces a configured session only under `allow-tenant-override`; with no session, use the canonicalized per-call value. Refuse public variable-scope `system`. The Gateway independently authorizes the cataloged scope and credential. Forwarded headers become a source only with the future HTTP transport. See the approved local architecture AD-22.
- Every ULID the tool accepts (correlation and idempotency keys, ULID-kind aggregate and marked identifiers, `Ulid` properties) must be canonical uppercase: check with `OperationExecutor.IsCanonicalUlid` (schemas: `SchemaDeriver.UlidPattern`), never bare `Ulid.TryParse` (it accepts lowercase and O/I/L/U; this overrides the shared baseline's `Ulid.TryParse` rule), never `Guid.TryParse`. Payload identifiers follow the Module's declared Identifier Kind (`Ulid` or `String`), never a name suffix.
- PRD §8.2 defers shared HTTP transport to the next release and legacy server/CLI deletion to the per-module migration. V1 defers Query correlation IDs and extensions, generic Query arguments for search, filters, ordering, freshness and entity scoping beyond `entityId`, and Gateway Command status lookup. Module-defined Payload fields can express these semantics when FR-21 evidence establishes the corresponding handler behavior.
- §8.2 also parks Contracts plug-in loading, typed per-operation tools, generated per-operation CLI subcommands, shell completion, executor retries, event stream reading, and MCP resources and prompts.
- PRD §8.3 puts EventStore infrastructure administration in the successor migration and excludes operating an OAuth or identity server from v1 and the next release. McpCli executes Module operations exclusively through the Gateway. Direct Module REST and Dapr calls fall outside its contract.
- `references/` holds read-only submodules of sibling repos; change them upstream, never here.
- `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` must stay byte-identical; edit `AGENTS.md`, copy it to the other two, and run `scripts/check-agent-instructions-sync.sh`.

## Where things are

- EventStore gateway client and envelopes: `references/Hexalith.EventStore/src/Hexalith.EventStore.Client/` and `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/` plus `Queries/`. That checkout can be newer than the compiled package (`HexalithEventStoreVersion` is pinned in root `Directory.Build.props` before the Builds import); confirm a member exists in the effective restored version before using it.
- MCP tools are registered in `src/Hexalith.McpCli.Mcp`, which has no `Program.cs`; the stdio host is `hexalith mcp --transport stdio` (`src/Hexalith.McpCli/Hosting/HostFactory.cs`).
- Header-forwarding handler for the HTTP transport (next release): `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/McpContextForwardingHandler.cs`.

## Running and verifying

- Restore needs `references/Hexalith.Builds` checked out; it supplies the central package catalog, and without it restore fails with NU1010. Root `Directory.Build.props` sets the module version pins before importing that catalog. This repository validates locally with the same packaged dependencies and Release settings as CI, overriding the shared baseline's local project-reference/Debug default: `dotnet restore Hexalith.McpCli.slnx`, then `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`.
- Run ordinary test projects one at a time: `dotnet test tests/<Project> --no-build --configuration Release` for Abstractions, Analyzers, Core, Manifest, Cli, and Mcp tests. Run times vary by machine and CI load.
- A new test project needs a name ending in `Tests`, an entry in `Hexalith.McpCli.slnx`, and registration in the appropriate CI tier in `.github/workflows/ci.yml`. The six ordinary projects are in `unit-test-projects`; `tests/Hexalith.McpCli.Integration.Tests` is deliberately separate as `aspire-test-project`, through `tools/live-topology/prepare-ci.sh` and `run-ci.sh`, with `aspire-continue-on-error: false`.
- Live Integration.Tests require the private runtime and `tools/live-topology/run-isolated.py`. In the full live lane, `run-vectors.py` invokes the wrapper once per approved vector with a hash-bound companion plan. Approved vectors without a plan run only in loopback. Follow `tools/live-topology/README.md` for source builds, runtime bootstrap, `MCPCLI_ISOLATED_RUNTIME_DIR`, and required outer process deadlines. Keep these tests in the isolated Aspire tier.
- For non-live topology checks, restore/build the Integration.Tests project and install `tools/conformance-vectors/v1/requirements.txt`, then run `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` and `python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-live-preflight --preflight-only`. Also follow `.github/workflows/ci.yml`'s `topology-vector-discovery` job to enumerate the built .NET tests with `-preEnumerateTheories -list tests` and assert the exact plan-backed approved vector cases plus smoke and boundary. These checks do not start source services or establish full live acceptance.
- After the normal solution restore/Release build and installing `tools/conformance-vectors/v1/requirements.txt`, check enrollment with `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net11.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.EnrolledModuleCoverageTests` and `python3 tools/conformance-vectors/v1/check_enrolled.py --output /tmp/mcpcli-enrolled-evidence`. The coverage test checks release inventories and Operation Shape coverage; the Python gate verifies restored-artifact integrity, approved vectors, shape coverage and CLI/MCP replay. Use a task-owned evidence directory; see the tool READMEs for the full sequence and separate performance/live gates.
- Run a fresh `dotnet restore Hexalith.McpCli.slnx` before Manifest.Tests: `DependencyPolicyTests` compares `src/Hexalith.McpCli/obj/project.assets.json` with the current NuGet restore inputs before checking the pinned graph.
- When moving the `references/Hexalith.Builds` gitlink, align the Builds workflow pins in `.github/workflows/ci.yml` and `.github/workflows/commitlint.yml`, restore, run Manifest.Tests, and update every changed version in `tools/dependency-policy.json` in the same commit; skipping this turned CI red after three Builds bumps.
- When Core validation, `Sample.Contracts`, or gateway wire output changes, also run CI's conformance gates: `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` and `bash tools/conformance-vectors/v1/run-sample-loopback.sh` (Python `jsonschema==4.26.0`). The loopback repoints `obj/` at a package cache it deletes, so run `dotnet restore Hexalith.McpCli.slnx` afterwards.
- Validate commit messages with `printf '%s\n' "$msg" | npx --no -- commitlint --verbose` after `npm ci`; exit 1 with "npx canceled due to missing packages" means missing tooling, not a rejected message.

## Conventions that differ from defaults

- Flat layout like the sibling modules: `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*.Tests`, not the nested `src/libraries/...` layout the shared instructions describe.
- The stdio MCP server reserves stdout for JSON-RPC. Startup errors go to stderr with exit 2. Once serving, request failures travel in the protocol. A serving-process fault writes `MCP server stopped unexpectedly.` to stderr and exits 2. Send logs to stderr and avoid `Console.WriteLine`.
- CLI results default to JSON on stdout. `--format table` produces tab-separated output for `modules`, `operations` and config displays. On success, `describe`, `send` and `query` emit JSON and write a format note to stderr when table output is requested. `--output` directs a result to the file and leaves stdout empty. Non-MCP failures emit one `{"error": …}` object on stdout with exit 2, even with `--output` or table format. Exit 1 is reserved for `describe --lint` findings. See the README section “Output and exit codes” and `CliOutputContractTests`.
- Read-only mode gates by `OperationKind` through `ExecutionAvailability.ReasonFor`; writes stay listed in discovery with `submittable: false`, never filtered out.
- Each Command gets a generated message ID. Its correlation ID defaults to that message ID unless the caller supplies one. Only the caller can supply an idempotency key. It is optional unless the operation requires one.
- Profiles default to `<user-profile>/.eventstore/mcpcli.json`. An explicit `ProfileStore` constructor file path wins; otherwise an absolute `MCPCLI_HOME` selects `<MCPCLI_HOME>/.eventstore/mcpcli.json` on each OS, and an unset override retains the default. Empty, whitespace-only, relative, control-character-containing or existing-file overrides fail safely as `configuration_invalid` without exposing the supplied path or falling back to the real home. Existing atomicity, permissions/ACLs, link refusal and admin-profile isolation apply at the selected location. Never read the admin CLI's `profiles.json`.

## Known pitfalls

- Every new guard needs a test that fails when the guard is removed; assert the full error document and both stdout and stderr, not only the exit code. Reviews keep finding guards no test protects.
- Update `README.md` in the same change as any user-visible CLI or MCP behavior (options, error codes, precedence, output channels, exit codes), and check each new claim against the built CLI on every verb it covers.
- The shipped CLI and `tests/Hexalith.McpCli.ConformanceHost` default to the enrolled production Contracts packages (`ConformanceProduction=true`). For isolated-module or empty-catalog tests, inject fixture assemblies or an empty list through the `CliRunner` constructor's `manifest` delegate, then call `InvokeAsync` (for example, `new CliRunner(manifest: () => []).InvokeAsync(["modules"])`). For the sample process host, use `tools/conformance-vectors/v1/run-sample-loopback.sh`, which sets `-p:ConformanceProduction=false` on both restore and build; restore/rebuild the default production host before production checks.
- For whole-string .NET `Regex` and `[GeneratedRegex]` validation, use `\z` to require the absolute end of input. A final `$` can match before a trailing newline. JSON Schema `pattern` uses ECMA-262 syntax. The exported ULID schema pairs `SchemaDeriver.UlidPattern` with a length of exactly 26.
- In `_bmad-output/implementation-artifacts/deferred-work.md`, grep before appending: a deferral already there goes only in the spec's `[Review][Defer]` row as "already tracked (`deferred-work.md:<line>`)", never as a reconfirmation entry. A spec row saying "defer after loopback" does not prove the entry exists; append it when the grep finds none.
- File new ledger entries under their source spec's heading, with a repo-relative `source_spec` and `path:line` anchors that match the current files.

<!-- /bmad:context -->
<!-- hexalith-cicd:begin -->
CI/CD is owned by Hexalith.CiCd.

Hexalith.CiCd owns `.github/workflows/**`, `.github/hexalith-ci.json`,
`.github/dependabot.yml`, the `references/Hexalith.Builds` gitlink and its
`.gitmodules` section, the delivered CI/CD instruction blocks in `AGENTS.md`,
`CLAUDE.md` and `.github/copilot-instructions.md`, and the required
`permissions.deny` entries in `.claude/settings.json`. Do not edit those owned
files or portions from a module. Propose policy changes in Hexalith.CiCd.
Preserve instructions, settings and submodule sections outside those portions.

At the repository root, the guard forbids release configuration
(`.releaserc*`, `release.config.*`) and commitlint configuration
(`commitlint.config.*`, `.commitlintrc*`). In the root `package.json` it forbids the
top-level `release` and `commitlint` keys and dependency entries for
`semantic-release`, `@semantic-release/*` and `@commitlint/*` under
`dependencies`, `devDependencies`, `optionalDependencies` and
`peerDependencies`. It also forbids commitlint lines in `.husky/commit-msg`
and files matching `**/Directory.Build.rsp` or `**/bmad-testarch-ci/**`
throughout the repository.

When CI fails, fix the product code, tests or dependencies. If the pipeline is
defective, report the failure and run link to Hexalith.CiCd without working
around it. Before every push, run `python3 references/Hexalith.Builds/check.py`
from the module root and require success. Do not disable or suppress dependency
audits, skip or filter out test projects, weaken checks, or add CI skip markers
(including `[skip ci]` variants) or `skip-checks` commit trailers. Do not write
tests that assert workflow YAML text.

Keep product gates: compilation, tests, security and dependency scans, commit
format and package publishing. Module-specific product checks belong in custom
actions enabled through Hexalith.CiCd. Checks of CI itself, agent tooling, story
evidence or workflow YAML do not belong in module CI. Releases follow the
centrally scheduled nightly process.

Start each product branch from current `main`: fetch `origin main` immediately
before creating the branch from `origin/main`. Do not reuse an older base that
predates delivered CI/CD changes. Use the restricted module credential. Report
permission refusals without switching credentials or broadening access.
GitHub permits PR Update branch with the restricted module credential even
when it imports changed workflows. Do not use it to import owned CI/CD changes.
Fetch current `main`, create a new product branch, and reapply only product
changes instead.

Launch Claude Code from the module root. The project-local `Edit` deny rules
protect the whole-owned workflow/config files and Builds subtree while keeping
reads available. File rules cannot target JSON keys or instruction marker
ranges: these instructions and the shared guard protect the owned portions of
settings, instruction files and `.gitmodules`. Never install these denies in
machine-wide settings or work around them through another tool.
<!-- hexalith-cicd:end -->

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
<!-- Full context verified 2026-10-10 against 5bc23e5bd36c4b10e6f19e5233e27dcc80466357; five deferred guidance corrections verified 2026-10-28 against 5aa3ee23ef4b395a4500453a50d4815e9837dd07. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## Hexalith.McpCli

One generic MCP server and one thin CLI, both driven by a catalog of commands and queries discovered from decorated `*.Contracts` assemblies and submitted through the EventStore gateway client. .NET 10, ModelContextProtocol 2.2.0, System.CommandLine 2.0.12, xUnit v3; package versions use the central catalog in `references/Hexalith.Builds/Props/Directory.Packages.props`, with EventStore, Parties, and Tenants pins set first in root `Directory.Build.props`. Planning (brief, PRD, architecture spine, epics) lives in `_bmad-output/planning-artifacts/`; story specs and the deferred-work ledger in `_bmad-output/implementation-artifacts/`.

## Policy

- Dependency allowlist: `tools/dependency-policy.json` (approved production packages, the exact restored closure, enrolled modules, and separate `testPackages` allowances), enforced by `DependencyPolicyTests` in `tests/Hexalith.McpCli.Manifest.Tests`. Never reference another module's aggregate, projection, handler, client, or server project or package from production `src/`. Tests also require approved package references and repository-owned project references; the topology uses published server-free Aspire helpers and the separately reviewed platform fixture closure, never sibling source project references.
- Zero module-specific implementation in production `src/`. Test-only composition in `tests/Hexalith.McpCli.AppHost` and assertions in `tests/Hexalith.McpCli.Integration.Tests` may name EventStore, Tenants, and Parties. Keep the runners in `tools/live-topology/` generic; change module behavior upstream.
- Enrollment requires a versionless `PackageReference` marked `HexalithContracts="true"` in `src/Hexalith.McpCli/Hexalith.McpCli.csproj`, its exact version under `modules` in `tools/dependency-policy.json`, a release inventory at `tools/inventory-coverage/v1/<module>-approved.json`, and complete vectors with `tools/conformance-vectors/v1/modules/<PackageId>/approval.json` binding the exact artifact, inventory, and vector hashes. Each vector also needs a hash-bound companion plan in `tools/live-topology/plans/`; follow README "Gateway boundary" and the inventory/vector tool READMEs for approval and v1 scope-count updates.
- Tenant comes from the envelope, never from the payload: a Module's fixed tenant first, else the session tenant (`--tenant`, `EVENTSTORE_TENANT`, profile). An MCP per-call tenant replaces a configured session tenant only under the operator gate (allow-tenant-override), and is used as supplied when no session tenant exists. A forwarded header becomes a source only with the HTTP transport.
- Every ULID the tool accepts (correlation and idempotency keys, ULID-kind aggregate and marked identifiers, `Ulid` properties) must be canonical uppercase: check with `OperationExecutor.IsCanonicalUlid` (schemas: `SchemaDeriver.UlidPattern`), never bare `Ulid.TryParse` (it accepts lowercase and O/I/L/U; this overrides the shared baseline's `Ulid.TryParse` rule), never `Guid.TryParse`. Payload identifiers follow the Module's declared Identifier Kind (`Ulid` or `String`), never a name suffix.
- Out of version one (PRD §8.2), refuse if proposed: plugin loading of Contracts assemblies, typed one-tool-per-operation exposure, generated per-operation CLI subcommands, shell completion, executor retries, any OAuth or identity server, event stream reading, MCP resources or prompts.
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
- Live Integration.Tests require the private runtime and `tools/live-topology/run-isolated.py`; `run-vectors.py` invokes that wrapper for every vector. Follow `tools/live-topology/README.md` for source builds, runtime bootstrap, `MCPCLI_ISOLATED_RUNTIME_DIR`, and required outer process deadlines. Keep these tests in the isolated Aspire tier.
- For non-live topology checks, restore/build the Integration.Tests project and install `tools/conformance-vectors/v1/requirements.txt`, then run `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'` and `python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-live-preflight --preflight-only`. Also follow `.github/workflows/ci.yml`'s `topology-vector-discovery` job to enumerate the built .NET tests with `-preEnumerateTheories -list tests` and assert the exact approved vector cases plus smoke. These checks do not start source services or establish full live acceptance.
- After the normal solution restore/Release build and installing `tools/conformance-vectors/v1/requirements.txt`, check enrollment with `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.EnrolledModuleCoverageTests` and `python3 tools/conformance-vectors/v1/check_enrolled.py --output /tmp/mcpcli-enrolled-evidence`. The coverage test checks release inventories; the Python gate verifies exact approved artifacts/vectors and CLI/MCP replay. Use a task-owned evidence directory; see the tool READMEs for the full sequence and separate performance/live gates.
- Run a fresh `dotnet restore Hexalith.McpCli.slnx` before Manifest.Tests: `DependencyPolicyTests` reads `src/Hexalith.McpCli/obj/project.assets.json`, so a stale restore passes locally and fails in CI.
- When moving the `references/Hexalith.Builds` gitlink, restore, run Manifest.Tests, and update every changed version in `tools/dependency-policy.json` in the same commit; skipping this turned CI red after three Builds bumps.
- When Core validation, `Sample.Contracts`, or gateway wire output changes, also run CI's conformance gates: `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` and `bash tools/conformance-vectors/v1/run-sample-loopback.sh` (Python `jsonschema==4.26.0`). The loopback repoints `obj/` at a package cache it deletes, so run `dotnet restore Hexalith.McpCli.slnx` afterwards.
- Validate commit messages with `printf '%s\n' "$msg" | npx --no -- commitlint --verbose` after `npm ci`; exit 1 with "npx canceled due to missing packages" means missing tooling, not a rejected message.

## Conventions that differ from defaults

- Flat layout like the sibling modules: `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*.Tests`, not the nested `src/libraries/...` layout the shared instructions describe.
- In the MCP server, stdout is the JSON-RPC channel: log to stderr only, never `Console.WriteLine`.
- CLI results and errors both go to stdout as JSON (an error is one `{"error": …}` object with exit 2); diagnostics and format notes go to stderr; exit 1 is reserved for `describe --lint` findings. Full contract: README "CLI and MCP", pinned by `CliOutputContractTests`.
- Read-only mode gates by `OperationKind` through `ExecutionAvailability.ReasonFor`; writes stay listed in discovery with `submittable: false`, never filtered out.
- Message ID is generated per call; correlation is caller-supplied or defaults to the message ID; the idempotency key is caller-supplied only, never generated, and required when the operation declares one.
- Profiles live in `~/.eventstore/mcpcli.json`; never read the admin CLI's `profiles.json`.

## Known pitfalls

- Every new guard needs a test that fails when the guard is removed; assert the full error document and both stdout and stderr, not only the exit code. Reviews keep finding guards no test protects.
- Update `README.md` in the same change as any user-visible CLI or MCP behavior (options, error codes, precedence, output channels, exit codes), and check each new claim against the built CLI on every verb it covers.
- The shipped CLI and `tests/Hexalith.McpCli.ConformanceHost` default to the enrolled production Contracts packages (`ConformanceProduction=true`). For isolated-module or empty-catalog tests, inject fixture assemblies or an empty list through the `CliRunner` constructor's `manifest` delegate, then call `InvokeAsync` (for example, `new CliRunner(manifest: () => []).InvokeAsync(["modules"])`). For the sample process host, use `tools/conformance-vectors/v1/run-sample-loopback.sh`, which sets `-p:ConformanceProduction=false` on both restore and build; restore/rebuild the default production host before production checks.
- Anchor validation regexes with `\z`, not `$`: .NET `$` also matches before a trailing newline.
- In `_bmad-output/implementation-artifacts/deferred-work.md`, grep before appending: a deferral already there goes only in the spec's `[Review][Defer]` row as "already tracked (`deferred-work.md:<line>`)", never as a reconfirmation entry. A spec row saying "defer after loopback" does not prove the entry exists; append it when the grep finds none.
- File new ledger entries under their source spec's heading, with a repo-relative `source_spec` and `path:line` anchors that match the current files.

<!-- /bmad:context -->

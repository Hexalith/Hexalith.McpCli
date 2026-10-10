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
<!-- Verified 2026-10-10 against 5bc23e5. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## Hexalith.McpCli

One generic MCP server and one thin CLI, both driven by a catalog of commands and queries discovered from decorated `*.Contracts` assemblies and submitted through the EventStore gateway client. .NET 10, ModelContextProtocol 2.2.0, System.CommandLine 2.0.12, xUnit v3; every package version comes from `references/Hexalith.Builds/Props/Directory.Packages.props`. Planning (brief, PRD, architecture spine, epics) lives in `_bmad-output/planning-artifacts/`; story specs and the deferred-work ledger in `_bmad-output/implementation-artifacts/`.

## Policy

- Dependency allowlist: `tools/dependency-policy.json` (approved direct packages, the exact restored closure, enrolled modules), enforced by `DependencyPolicyTests` in `tests/Hexalith.McpCli.Manifest.Tests`. Never reference another module's aggregate, projection, handler, client, or server project or package.
- Zero module-specific code in this repo. Enrolling a module is configuration only: a versionless `PackageReference` marked `HexalithContracts="true"` in `src/Hexalith.McpCli/Hexalith.McpCli.csproj`, plus its exact version under `modules` in `tools/dependency-policy.json`.
- Tenant comes from the envelope, never from the payload: a Module's fixed tenant first, else the session tenant (`--tenant`, `EVENTSTORE_TENANT`, profile). An MCP per-call tenant replaces a configured session tenant only under the operator gate (allow-tenant-override), and is used as supplied when no session tenant exists. A forwarded header becomes a source only with the HTTP transport.
- Every ULID the tool accepts (correlation and idempotency keys, ULID-kind aggregate and marked identifiers, `Ulid` properties) must be canonical uppercase: check with `OperationExecutor.IsCanonicalUlid` (schemas: `SchemaDeriver.UlidPattern`), never bare `Ulid.TryParse` (it accepts lowercase and O/I/L/U; this overrides the shared baseline's `Ulid.TryParse` rule), never `Guid.TryParse`. Payload identifiers follow the Module's declared Identifier Kind (`Ulid` or `String`), never a name suffix.
- Out of version one (PRD §8.2), refuse if proposed: plugin loading of Contracts assemblies, typed one-tool-per-operation exposure, generated per-operation CLI subcommands, shell completion, executor retries, any OAuth or identity server, event stream reading, MCP resources or prompts.
- `references/` holds read-only submodules of sibling repos; change them upstream, never here.
- `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` must stay byte-identical; edit `AGENTS.md`, copy it to the other two, and run `scripts/check-agent-instructions-sync.sh`.

## Where things are

- EventStore gateway client and envelopes: `references/Hexalith.EventStore/src/Hexalith.EventStore.Client/` and `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/` plus `Queries/`. That checkout can be newer than the compiled package (`HexalithEventStoreVersion` in the Builds props); confirm a member exists in the restored version before using it.
- MCP tools are registered in `src/Hexalith.McpCli.Mcp`, which has no `Program.cs`; the stdio host is `hexalith mcp --transport stdio` (`src/Hexalith.McpCli/Hosting/HostFactory.cs`).
- Header-forwarding handler for the HTTP transport (next release): `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/McpContextForwardingHandler.cs`.

## Running and verifying

- Restore needs `references/Hexalith.Builds` checked out; it supplies every package version, and without it restore fails with NU1010. Build as CI does: `dotnet restore Hexalith.McpCli.slnx`, then `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`.
- Test one project at a time: `dotnet test tests/<Project> --no-build --configuration Release`. Cli.Tests and Manifest.Tests take about 35 s each; the others under 5 s.
- A new test project needs a name ending in `Tests`, an entry in `Hexalith.McpCli.slnx`, and an entry in the test list in `.github/workflows/ci.yml`, or CI silently skips it.
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
- The shipped CLI enrolls no modules and returns `catalog_empty`; reproduce behavior through `CliRunner.InvokeAsync` with fixture contracts or `tests/Hexalith.McpCli.ConformanceHost`, not `dotnet run --project src/Hexalith.McpCli`.
- Anchor validation regexes with `\z`, not `$`: .NET `$` also matches before a trailing newline.
- In `_bmad-output/implementation-artifacts/deferred-work.md`, grep before appending: a deferral already there goes only in the spec's `[Review][Defer]` row as "already tracked (`deferred-work.md:<line>`)", never as a reconfirmation entry. A spec row saying "defer after loopback" does not prove the entry exists; append it when the grep finds none.
- File new ledger entries under their source spec's heading, with a repo-relative `source_spec` and `path:line` anchors that match the current files.

<!-- /bmad:context -->

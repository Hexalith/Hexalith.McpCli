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
<!-- Verified 2026-09-21 against 2659166. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## Hexalith.McpCli

One generic MCP server and one thin CLI, both driven by a catalog of commands and queries discovered from decorated `*.Contracts` assemblies and submitted through the EventStore gateway client. .NET 10, ModelContextProtocol 2.2.0, System.CommandLine 2.0.12, xUnit v3. Brief and decisions: `_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/`.

## Policy

- Only two kinds of Hexalith dependency: the EventStore client package and the `*.Contracts` libraries being exposed. Never reference another module's aggregate, projection, handler, client, or server project.
- Zero module-specific code in this repo; adding a module is a package reference and a rebuild.
- Tenant comes from the envelope (profile, flag, or forwarded header), never from the payload.
- Identifiers are ULIDs; validate with `Ulid.TryParse`, never `Guid.TryParse`.
- Out of version one, refuse if proposed: plugin loading of Contracts assemblies, typed one-tool-per-operation exposure, generated per-operation CLI subcommands, any OAuth or identity server, event stream reading, MCP resources or prompts.
- `references/` holds read-only submodules of sibling repos; change them upstream, never here.
- `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` must stay byte-identical; edit `AGENTS.md`, copy it to the other two, and run `scripts/check-agent-instructions-sync.sh`.

## Where things are

- EventStore gateway client and envelopes: `references/Hexalith.EventStore/src/Hexalith.EventStore.Client/` and `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Commands/` plus `Queries/`.
- CLI shape to copy (profiles in `~/.eventstore/profiles.json`, global `--url/--token/--format/--output/--profile`, exit codes 0/1/2): `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Cli/`.
- Stdio MCP host pattern: `references/Hexalith.EventStore/src/Hexalith.EventStore.Admin.Mcp/Program.cs`.
- Header-forwarding handler for the HTTP transport (next release): `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/McpContextForwardingHandler.cs`.

## Running and verifying

- TODO: `dotnet restore Hexalith.McpCli.slnx` and `dotnet build Hexalith.McpCli.slnx --configuration Release` once the solution exists; copy `global.json` from `references/Hexalith.Builds/`.
- TODO: commitlint via `npx --no -- commitlint --edit` once `package.json` and `commitlint.config.mjs` exist; copy both from a sibling module.

## Conventions that differ from defaults

- Flat layout like the sibling modules: `src/Hexalith.McpCli.*` and `tests/Hexalith.McpCli.*.Tests`, not the nested `src/libraries/...` layout the shared instructions describe.
- In the MCP server, stdout is the JSON-RPC channel: log to stderr only, never `Console.WriteLine`.
- The catalog distinguishes commands from queries so a read-only mode is one filter.
- Message ID and idempotency key are generated per call; correlation ID is optional pass-through.

<!-- /bmad:context -->

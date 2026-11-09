# Hexalith.McpCli

Hexalith.McpCli provides a shared MCP server and CLI for decorated Hexalith Contracts libraries.

Contracts authors reference `Hexalith.McpCli.Abstractions` and declare one module on the assembly. Place each operation type in its own file:

```csharp
// Module.cs
using Hexalith.McpCli.Abstractions;
[assembly: HexalithModule("inventory", "Manage inventory items.", IdentifierKind.Ulid,
    WireTypeConvention = WireTypeConvention.KebabCase)]
```

```csharp
// CreateItemCommand.cs
using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

[HexalithCommand("Create an inventory item.", Domain = "inventory",
    AggregateIdProperty = nameof(ItemId))]
public sealed record CreateItemCommand(
    [property: HexalithIdentifier, Description("The item's ULID.")] string ItemId);
```

```csharp
// GetItemQuery.cs
using System.ComponentModel;
using Hexalith.McpCli.Abstractions;

[HexalithQuery("Read an inventory item.", Domain = "inventory",
    AggregateIdProperty = nameof(ItemId), ProjectionType = "inventory-items")]
public sealed record GetItemQuery(
    [property: HexalithIdentifier, Description("The item's ULID.")] string ItemId);
```

The module's identifier kind applies to `[HexalithIdentifier]` properties and aggregate identifier properties. Descriptions are required constructor arguments; routing values can instead come from the EventStore contract interfaces.

Envelope-owned tenant, actor, correlation, and idempotency members can use string-backed value objects with a Contracts-provided JSON converter. Catalog construction checks that the converter reads and writes the same JSON string; numeric, object-valued, and string-changing converters are rejected. These members remain filled from the envelope. Tenant and actor schemas use strings independently of the module's identifier kind; correlation and idempotency schemas require canonical uppercase ULIDs.

The `Hexalith.McpCli.Abstractions` package includes a build analyzer. Diagnostic `MCPCLI001` warns on a command or query type whose `[HexalithCommand]` or `[HexalithQuery]` description is empty, whitespace, or null. Supply a nonblank description to resolve it. The analyzer requires .NET SDK 10.0.4xx or later; an older SDK may report `CS9057` because its compiler cannot load the analyzer's Roslyn version. Contracts projects need only the Abstractions package reference.

## MCP and CLI ownership

The [authoritative Hexalith rule](https://github.com/Hexalith/Hexalith.AI.Tools/blob/70dbf73e80787299c832d30d911b16b105ab194d/hexalith-llm-instructions.md#hexalith-mcp-and-cli-ownership) makes `Hexalith.McpCli` the target Hexalith-owned MCP server and CLI. New modules declare gateway-ready operations in decorated Contracts; other capability classes need a separately approved generic contract and transport decision. Existing proprietary module servers, plug-ins and CLIs receive only safety and continuity fixes; they remain migration sources, never templates for new modules.

The published [migration plan 1.1.0](https://github.com/Hexalith/Hexalith.AI.Tools/blob/70dbf73e80787299c832d30d911b16b105ab194d/hexalith-mcpcli-migration-instructions.md) indexes the frozen implementations, immutable inventories, approval limits and retirement prerequisites, including the outstanding EventStore Admin successor inventory. The [Story 4.15 evidence](https://github.com/Hexalith/Hexalith.McpCli/blob/main/_bmad-output/implementation-artifacts/evidence/story-4-15/code-review-20261029/README.md) records authoritative upstream integration, the containing baseline reference and local synchronization.

The instruction prerequisite for paired publication requires authoritative `main` to contain the finished rule and plan, a containing baseline reference in this repository, and passing local instruction synchronization. An open PR is insufficient. Dependency, inventory, loopback, live and package gates remain independent. Paired staging verifies these prerequisites independently of publication. Paired publication requires the additional candidate-specific acceptance below. The one-time Abstractions bootstrap is closed. Credential-free local preparation remains available; historical verification first requires current main to pass full paired gates and FR-22 prerequisites.

## Bootstrap package release

The independent [Bootstrap package workflow](https://github.com/Hexalith/Hexalith.McpCli/blob/main/.github/workflows/bootstrap-package.yml) restores and builds only Abstractions and its bundled analyzer production projects. It runs the Abstractions and analyzer author-time tests (including synthetic Contracts fixtures), release rejection tests, and a decorated consumer build with a fresh package cache, explicit NuGet configuration and cleared fallback folders. Its deliberately blank description must produce exactly one `MCPCLI001` warning, proving the packaged analyzer loads. This gate needs no decorated upstream module, tool build, Aspire tier, or FR-22 evidence.

[`Hexalith.McpCli.Abstractions`](https://www.nuget.org/packages/Hexalith.McpCli.Abstractions) has no consumer-visible package dependencies. A standalone .NET 10 Contracts consumer pins one verified published version with a single exact reference, for example:

```xml
<PackageReference Include="Hexalith.McpCli.Abstractions" Version="[2.0.1]" />
```

Hexalith Contracts repositories use central package management. Their Builds catalog supplies `HexalithMcpCliVersion` and `<PackageVersion Include="Hexalith.McpCli.Abstractions" Version="$(HexalithMcpCliVersion)" />`; the Contracts project uses a versionless reference:

```xml
<PackageReference Include="Hexalith.McpCli.Abstractions" />
```

For a local gate, use a fresh checkout with the root-declared Builds submodule available:

```sh
bash -euo pipefail <<'EOF'
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
for project in Abstractions Analyzers; do
  test_project="tests/Hexalith.McpCli.${project}.Tests"
  dotnet restore "$test_project"
  dotnet build "$test_project" --configuration Release --no-restore -warnaserror
  dotnet test "$test_project" --configuration Release --no-build
done
MCPCLI_RELEASE_PHASE=bootstrap bash scripts/release-prepare.sh 1.0.0
EOF
```

Preparation restores/builds the Abstractions project, packs exactly one package into a fresh `nupkgs/bootstrap` directory, and compiles the decorated consumer against those prepared bytes before recording their SHA-256, preparation HEAD and clean-source state in the JSON receipt `nupkgs/bootstrap.sha256`. Publication and recovery require a receipt from clean source at the exact release SHA; a local dirty-source preparation cannot later be published merely by cleaning the checkout. An existing staging directory or receipt is refused; preserve it elsewhere before another run. Other artifacts under `nupkgs` are retained. Local preparation and consumer checks require no publication credentials.

Independent Abstractions publication is closed because `Hexalith.McpCli` is public on nuget.org. Every ordinary bootstrap preflight, publisher and source gate checks the tool's NuGet version index, regardless of marker tags or recovery environment variables. Registry errors, malformed indexes and uncertain absence fail closed. First-ever absence requires independent HTTP 404 responses from both the flat-container and registration indexes; the existing paired-publication marker then remains an additional closure guard. Local preparation above remains credential-free and does not publish.

The [Release workflow](https://github.com/Hexalith/Hexalith.McpCli/blob/main/.github/workflows/release.yml) refuses phase `bootstrap` with an empty recovery version before production approval or credentials. New releases use the paired staging and publication procedure below. Direct `release-publish.sh` and `release-preflight.sh` cannot use `MCPCLI_RECOVERY_VERSION` or `RECOVERY_VERSION` to bypass closure or switch to historical source policy. Ordinary publication still validates the exact current-main source, prepared receipt and package bytes and refuses duplicate versions.

Phase `bootstrap` now verifies only the fixed historical versions `1.0.0`, `1.1.0` and `2.0.0` in [bootstrap-history.json](https://github.com/Hexalith/Hexalith.McpCli/blob/main/scripts/bootstrap-history.json). Each local and remote `v<version>` tag must match its full pinned source SHA and be an ancestor of current main. The package must already be public; an absent package cannot be published by recovery. Unknown versions, moved/missing tags, failed source gates, mismatching contents and uncertain registry responses stop verification. [The historical decisions and evidence](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/bootstrap-history.md) separately record 1.1.0 and 2.0.0 as owner-accepted AD-17 process deviations, without reclassifying them as compliant or granting another bootstrap exception.

Historical verification checks the reviewed current-main workflow through full paired CI, commitlint and FR-22 prerequisites, then uses explicit `--tagged-recovery` for the pinned historical source and its independent Bootstrap package/Commitlint push gates. It preserves reviewed helpers and the history allowlist before checking out the tag, aligns only root-declared baseline/build submodules to that source, and rebuilds and consumer-tests the tagged package. Its clean-source receipt must match that exact SHA. It downloads the already-public package once, validates and compares consumer contents with the tagged build, proves its analyzer loads, and rechecks historical source gates. NuGet's repository signature and core-properties metadata are excluded from content comparison; core properties record the packing NuGet version. Matching build paths and toolchain versions are required: if DLL bytes differ, use the original validated artifact and source-bound receipt for investigation. This path obtains no NuGet key, performs no package push or GitHub release edits, and retains verification results as a workflow artifact. The paired publisher's separate bounded processing wait remains unchanged.

After each release, record the committed SHA, gate/release URLs, prepared receipt SHA-256, public signed-package SHA-256 and public-feed consumer proof with the release evidence. Preparation and publication print the prepared receipt hash; recovery prints the public signed-package hash. NuGet's repository signature makes the two hashes differ. From the repository root, run the consumer check with the verified published version and a fresh target directory, for example:

```sh
bash scripts/smoke-bootstrap-consumer.sh 1.0.0 https://api.nuget.org/v3/index.json "$(mktemp -d)/consumer"
```

Update the verified published version in `HexalithMcpCliVersion` and the Abstractions entry in the owning Hexalith.Builds catalog, run its documented complete audit refresh and validation, and record the integrated Builds revision.

## Stage the paired packages

Dispatch `Release` from current `main` with phase `stage-paired` and an empty recovery version. This path has read-only repository permissions and does not publish packages, tags or GitHub releases. Publication uses the separate `paired` path below; paired recovery is refused before side effects.

The version selector runs the pinned semantic-release analyzer in a temporary Git copy with a local temporary remote, preserving committed history and tags while excluding publication plugins. It records one next version, or an explicit `no-release` result with no staged pair. Preparation requires clean current-main source and the latest successful exact-SHA **push** CI and commitlint runs. It checks that the dependency/unit, inventory/enrollment, sample validation/loopback and live-semantic jobs and their required steps executed. Fresh FR-22 checks require the committed baseline to contain the approved rule revision, authoritative upstream integration and byte-identical agent entry points.

Preparation restores/builds the solution in Release, packs only the two projects in `tools/release-packages.json`, and validates package IDs, versions, repository commits, effective packaging properties, generated/flagged/approved Contracts equality, and the portable framework-dependent, untrimmed .NET 10 managed payload. It compiles the decorated consumer against the staged Abstractions package in a fresh cache and requires the packaged analyzer's expected `MCPCLI001` warning. The `prepared.json` receipt binds the full source SHA, version, both package hashes and preparation evidence. Existing staging/evidence directories are refused, and a validation failure leaves diagnostics without a success receipt.

One retained pair feeds isolated local-source installations on Linux, Windows and macOS. Each uses private NuGet caches, an explicit local-only source configuration and a private `MCPCLI_HOME`; smoke checks version, all offline discovery/descriptions, profile configuration, JSON/error channels, output-file bytes and MCP stdio protocol behavior without starting hosted services. Windows additionally runs the complete Core and CLI suites and requires the three private-ACL tests, concurrency/admin-isolation process tests and the staging-preflight process test to pass rather than skip. macOS runs the complete CLI suite. The acceptance job compares every hash-bound receipt and the raw discovery files byte for byte. Missing OS results, required skipped tests or any mismatch produce no `accepted-pair.json`. The accepted receipt is explicitly **staging only**.

For local implementation checks after `npm ci`, run from the repository root with fresh output paths:

```sh
node scripts/select-release-version.mjs /tmp/mcpcli-version.json
python3 scripts/prepare-paired-release.py --local --selection /tmp/mcpcli-version.json --output /tmp/mcpcli-pair
python3 scripts/smoke-paired-tool.py --staging /tmp/mcpcli-pair/packages --prepared /tmp/mcpcli-pair/prepared.json --output /tmp/mcpcli-smoke
```

`--local` records local-only evidence, including dirty-source state, and can never become accepted staging. Omit it only for eligible committed current-main source with `REPOSITORY` and read-only GitHub authentication configured. Local Linux checks do not establish Windows/macOS acceptance; actual runner receipts remain required. ARM qualification remains deferred. The [staging and operator history](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/operator-setup-history.md) records the earlier staging candidate. Those archives and sessions cannot qualify a new candidate.

## Publish the accepted pair

After the current-main source has green blocking CI and commitlint jobs and steps, stage a fresh pair with `phase=stage-paired`. The CI gates include release-automation Python tests and the pinned semantic-release selector tests. The 2.0.0 Abstractions bootstrap is already public; a paired release must select a later shared version with both package identities free. The bootstrap tag makes an unchanged source a no-release result, so a subsequent substantive commit and fresh exact-source gates are required. For candidate-specific acceptance, either complete actual Claude Code, Claude Desktop and VS Code sessions against those exact archives in a newly approved ready environment, or use the user's explicitly authorized automated-acceptance path. The [operator checklist](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/operator-setup-checklist.md) defines both sanitized approval packets. The automated path records a human-validation bypass; it does not claim client-session success. Historical sessions cannot transfer to new bytes; the accepted assisted 685-second timing exception remains explicit in historical records.

Dispatch `Release` from the same current `main` with `phase=paired`, the exact `staging_run_id`, an empty `recovery_version`, and `operator_acceptance` containing the candidate-specific approval JSON. The authenticated dispatch actor must match `approved_by`. Review the exact candidate and approve the existing `production` environment. The workflow authenticates the original staging run and GitHub artifact digests, recomputes three-OS acceptance, cross-checks acceptance-source evidence and rechecks current-main gates after approval and immediately before each push. Pinned semantic-release must select the same shared version; any mismatch refuses both pushes.

Publication imports and snapshots the accepted archives without build or pack. It checks both NuGet identities before pushing only `Hexalith.McpCli.Abstractions` and `Hexalith.McpCli`, then verifies their public consumer contents while allowing NuGet's repository signature and packing core-properties metadata. It retains source-bound preflight, push-intent, per-package push/public results and a final outcome; both verified packages and receipts become release assets. Preflight and outcome receipts retain the decision schema and automated bypass authorization when used. A confirmed first-ever package absence requires explicit 404s from both NuGet's version index and registration identity; an uncertain response refuses publication.

Two NuGet pushes cannot be atomic. Both packages are pushed in sequence, with a fresh preflight immediately before each push; public downloads and content verification follow both pushes. A failed or uncertain push stops the run, retains partial outcomes and never triggers an automatic duplicate push. The durable per-version repository marker records that publication started; a global marker prevents new independent bootstrap versions. For recovery, preserve the original archives and all receipts, inspect both public identities and signature-aware contents, establish which pushes occurred, and obtain a reviewed recovery decision. `recovery_version` supports only the existing bootstrap procedure; paired recovery is refused. Do not delete markers, repack the same version, or restart an uncertain publication to bypass this stop. Record paired publication as complete only after both public versions verify.

## Operator setup with an accepted staged tool

First-time operators follow the quick start. The rest of this section is for the environment owner, for other clients and for troubleshooting.

### Quick start: Claude Code sets it up for you

Claude Code installs and registers the tool from one prompt. You only type your token yourself.

Before you start, your environment owner gives you the accepted version (`VERSION`) and:

- the absolute path of a **handoff folder** with the tool packages and a `NuGet.Config` (the owner has already checked them); use a path beginning with `/`, without `~`;
- the **Gateway URL**, your **tenant** and your **actor**; the URL is local to this machine and works only while the owner's private port-forward is running here;
- a short-lived **token** and its expiry, handed to you privately (for example copied to your clipboard). You paste it only at the hidden `Token:` prompt in step 3;
- a new **Party ID** for your test, for example `party-operator-ana-1`.

You need a Linux or WSL bash terminal where `dotnet --list-sdks` shows a .NET SDK 10 or later and `dotnet --list-runtimes` shows `Microsoft.NETCore.App 10.x` (the tool does not run on a machine with only .NET 11), and Claude Code installed and signed in (`claude --version`). Check that `env | grep '^EVENTSTORE_'` prints nothing: inherited `EVENTSTORE_*` variables override the profile, so remove them from the setup and client launch environment before continuing.

**1.** Open a terminal and start Claude Code in a new folder:

```sh
mkdir -m 700 ~/hexalith-operator && mkdir ~/hexalith-operator/project && cd ~/hexalith-operator/project && claude
```

If the root folder already exists, stop and inspect it. Use step 5 only after confirming that it contains solely an earlier Hexalith setup; never delete an unrelated existing folder.

**2.** Copy this prompt and paste it into Claude Code as it is. Claude Code first asks for your handoff folder, accepted version, tenant and actor. Answer, then approve the commands it runs:

```text
Set up the Hexalith MCP server for me. Before running anything, ask me for my handoff folder, accepted version, tenant and actor. Replace each whole HANDOFF, VERSION, TENANT or ACTOR argument below with a shell-quoted literal value, never insert an answer inside existing quotes. For --configfile, replace the entire "HANDOFF/NuGet.Config" argument with the shell-quoted absolute path to NuGet.Config in my handoff folder. Preserve spaces, dollar signs and command-substitution text as literal characters; use Bash single-quoted literals and escape any embedded single quote. Never run a command that still contains one of those four placeholder words. Otherwise run each command below with Bash, exactly as written, one at a time. Stop at the first error and show it to me. Never ask for, read or print my token.
1. export DOTNET_ROOT="$(dirname "$(readlink -f "$(command -v dotnet)")")" NUGET_PACKAGES="$HOME/hexalith-operator/packages" && dotnet tool install Hexalith.McpCli --version VERSION --tool-path "$HOME/hexalith-operator/tools" --configfile "HANDOFF/NuGet.Config" --no-cache && "$HOME/hexalith-operator/tools/hexalith" --version
   The last line must match the accepted version supplied by the owner.
2. Ask me to run the token command from step 3 of the README in another terminal, with the token my environment owner gave me, and wait until I say it is done.
3. export DOTNET_ROOT="$(dirname "$(readlink -f "$(command -v dotnet)")")" MCPCLI_HOME="$HOME/hexalith-operator/home" && "$HOME/hexalith-operator/tools/hexalith" config set operator tenant TENANT && "$HOME/hexalith-operator/tools/hexalith" config set operator actor ACTOR && "$HOME/hexalith-operator/tools/hexalith" config current --profile operator
   Show me url, tenant and actor. The token must stay masked.
4. claude mcp add hexalith --transport stdio --scope local --env MCPCLI_HOME="$HOME/hexalith-operator/home" --env DOTNET_ROOT="$(dirname "$(readlink -f "$(command -v dotnet)")")" -- "$HOME/hexalith-operator/tools/hexalith" mcp --transport stdio --profile operator && claude mcp get hexalith
   The status must be Connected. Then tell me to restart Claude Code.
```

**3.** When Claude Code asks for the token command, open a **second** terminal running bash (type `bash` first if it uses zsh or fish), run these two lines with your Gateway URL instead of `GATEWAY-URL`, paste your token at `Token:` (nothing is shown) and press Enter. Then tell Claude Code it is done. The token is not displayed or kept in your shell history, but it is passed to `hexalith` as a command argument, so other processes on this machine could read it while that command runs. If that is not acceptable, use [Configure the private operator profile](#configure-the-private-operator-profile) instead.

```sh
export DOTNET_ROOT="$(dirname "$(readlink -f "$(command -v dotnet)")")" MCPCLI_HOME="$HOME/hexalith-operator/home"
(read -rsp 'Token: ' token && echo && "$HOME/hexalith-operator/tools/hexalith" config profile add operator --url GATEWAY-URL --token "$token"; mcpcli_token_status=$?; unset token; exit "$mcpcli_token_status")
```

To replace an expired token later, close Claude Code, run the two lines above again, then run the following two lines in that same terminal with your real tenant and actor. Adding the profile again clears those fields. Restart Claude Code in `~/hexalith-operator/project` afterward so its stdio server loads the new token.

```sh
"$HOME/hexalith-operator/tools/hexalith" config set operator tenant TENANT
"$HOME/hexalith-operator/tools/hexalith" config set operator actor ACTOR
```

**4.** When Claude Code says setup is done, type `/exit`, run `claude` again in the same folder and type `/mcp`: `hexalith` must be connected. Then paste this request as it is. Claude Code first asks for your tenant and Party ID. Answer, then approve each hexalith tool call:

```text
Use only the hexalith MCP tools. Before calling any tool, ask me for my tenant and my Party ID, and put my answers in place of TENANT and PARTY-ID below. Never send TENANT or PARTY-ID themselves as values. First list the modules. Then read tenant TENANT with tenants.get-tenant. Then create one person exactly once with parties.create-party: PartyId PARTY-ID, first name Operator, last name Setup, preferred email operator@example.test with ContactChannelId email-PARTY-ID, and an Other identifier with value operator-setup and IdentifierId external-PARTY-ID. Do not pass a tenant or an idempotency key. Then read the person back with parties.get-party using entityId PARTY-ID. If the read-back does not find the person yet, repeat only the read every few seconds for up to 45 seconds. Otherwise, if any call fails or its result is uncertain, stop, show me the error and do not retry.
```

You are done when the creation result shows `status: accepted` with your tenant and Party ID, and the read-back shows the person with `isActive: true`. If a step fails, see [Resolve setup failures](#resolve-setup-failures). Never repeat the creation.

**5.** When you have finished, remove the registration and the private folder, which holds your token. Run the second line even if the first reports that no server named `hexalith` is registered:

```sh
cd ~/hexalith-operator/project && claude mcp remove hexalith -s local
cd ~ && rm -rf ~/hexalith-operator
```

### Environment owner: environment and handoff

Use a fresh **accepted staging** pair at the shared version selected by the pinned release tooling. Obtain both archives, `prepared.json`, `accepted-pair.json`, `acceptance-source.json`, their SHA-256 values and exact source SHA from the selected successful `stage-paired` Release run. The owner supplies the accepted version as `VERSION`; do not substitute another archive with the same version, a public-feed package or a source build. Record the run ID and all five package/receipt hashes before installation.

Before starting, have .NET **10 SDK** installed (`dotnet --info` and `dotnet --list-runtimes` must show .NET 10), Python 3 for the private token prompt below, and an installed, signed-in MCP client. The framework-dependent executable also needs the .NET 10 runtime in the environment that launches it. Record exact client, extension/harness, OS and runtime versions; the registration formats below were checked against official documentation on 2026-10-30. Client execution still requires the [operator checklist](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/operator-setup-checklist.md).

The environment owner must supply an approved, ready task environment on the approved Platform target, a private local Gateway port-forward, the selected test tenant, a short-lived operator token, actor, expiry and permission to create one synthetic Party per session. The identity must read Tenants and read/write Parties in the selected tenant. Current Tenants commands and cross-tenant reads require the cataloged `platform:tenants` scope and its permissions; a single-tenant read uses the selected canonical tenant and matching aggregate identity. A discovery result alone cannot establish those permissions. Temporary Platform preparation and its concrete deployment review are separate prerequisites; an isolated secrets-test endpoint is not this environment. Keep bootstrap administrator credentials and signing keys with the environment owner. For the independent README-only attempt, an observer starts timing immediately before the operator pastes the quick-start setup prompt (manual path: immediately before `dotnet tool install`) and stops at the first successful MCP `send_command` with the correct tenant and Party ID; include installation, configuration, registration, all failures and assistance. The target is 900 seconds.

A new candidate needs its own owner-approved ready environment and reviewed preparation. Use a prepared private profile for ordinary client sessions. Keep each attempt bound to its actual README, package/receipt hashes and environment approval; retain failed attempts and assistance in the [operator checklist](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/operator-setup-checklist.md). The [historical sessions](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/operator-setup-history.md) remain bound to their original archives and removed environment.

Replace `VERSION` in installation commands and both archive filenames with the accepted shared version supplied by the owner.

For the quick start, first verify the supplied five hashes and receipts as described in the manual installation below. Then copy the two verified packages, by name, into a handoff folder that the operator can read, and write its `NuGet.Config`. Choose a folder path without `&`, `<`, `>` or quotes, because the block writes it into XML unescaped:

```sh
handoff=/absolute/path/handoff
mkdir "$handoff" &&
cp /absolute/path/accepted-packages/Hexalith.McpCli.VERSION.nupkg /absolute/path/accepted-packages/Hexalith.McpCli.Abstractions.VERSION.nupkg "$handoff"/ &&
cat > "$handoff/NuGet.Config" <<EOF
<configuration>
  <packageSources>
    <clear />
    <add key="accepted-local" value="$handoff" />
  </packageSources>
  <fallbackPackageFolders><clear /></fallbackPackageFolders>
</configuration>
EOF
```

### Install into an isolated directory

Use a new absolute task directory outside the repository. On Linux/macOS, replace `/absolute/path/accepted-packages` with the supplied local package directory:

```sh
operator_root="$HOME/hexalith-operator"
staged_packages="/absolute/path/accepted-packages"
mkdir -m 700 "$operator_root"
export MCPCLI_HOME="$operator_root/home"
export DOTNET_CLI_HOME="$operator_root/dotnet-home"
export NUGET_PACKAGES="$operator_root/packages"
export NUGET_HTTP_CACHE_PATH="$operator_root/http-cache"
export NUGET_PLUGINS_CACHE_PATH="$operator_root/plugin-cache"
```

On Windows PowerShell, use native Windows paths and `python` instead of `python3` if that is your Python command:

```powershell
$operator_root = Join-Path $env:USERPROFILE 'hexalith-operator'
$staged_packages = 'C:\absolute\path\accepted-packages'
New-Item -ItemType Directory -Path $operator_root -ErrorAction Stop | Out-Null
$env:MCPCLI_HOME = Join-Path $operator_root 'home'
$env:DOTNET_CLI_HOME = Join-Path $operator_root 'dotnet-home'
$env:NUGET_PACKAGES = Join-Path $operator_root 'packages'
$env:NUGET_HTTP_CACHE_PATH = Join-Path $operator_root 'http-cache'
$env:NUGET_PLUGINS_CACHE_PATH = Join-Path $operator_root 'plugin-cache'
```

Verify the supplied five hashes with `sha256sum` (Linux), `shasum -a 256` (macOS), or `Get-FileHash -Algorithm SHA256` (PowerShell). Confirm `prepared.json` and `accepted-pair.json` name the accepted version and supplied full source SHA, `prepared.json` says `source_clean: true`, and `accepted-pair.json` says `accepted-staging-only` and binds the prepared hash and both package hashes. Confirm `acceptance-source.json` binds the same source as clean current main and contains successful CI/commitlint and FR-22 instruction synchronization evidence. Stop on any mismatch.

Create `NuGet.Config` in the task directory with the **absolute local package path**, escaping XML characters such as `&` as `&amp;`. This clears inherited sources and fallback folders:

```xml
<configuration>
  <packageSources>
    <clear />
    <add key="accepted-local" value="/absolute/path/accepted-packages" />
  </packageSources>
  <fallbackPackageFolders><clear /></fallbackPackageFolders>
</configuration>
```

Install and check the absolute executable (PowerShell: prefix an executable path with `&`; the file is `tools\hexalith.exe`):

```sh
dotnet tool install Hexalith.McpCli --version VERSION --tool-path "$operator_root/tools" --configfile "$operator_root/NuGet.Config" --no-cache
"$operator_root/tools/hexalith" --version
"$operator_root/tools/hexalith" modules --strict
```

Require the accepted version and modules `parties` (7 operations) and `tenants` (14). Do not put the tool on a shared PATH. These package and protocol checks do not establish a live client session.

### Configure the private operator profile

Remove inherited `EVENTSTORE_*` settings from the launching terminal/client environment: they override profile fields. Use the owner's actual Gateway URL, tenant and actor below. The URL is the operator-local port-forward, for example `http://127.0.0.1:18170`, and works only while that private forward is running in the same network environment. On PowerShell, replace `$operator_root` paths with their Windows equivalents and use `&` to invoke them.

```sh
"$operator_root/tools/hexalith" config profile add operator --url http://127.0.0.1:18170
"$operator_root/tools/hexalith" config set operator tenant APPROVED-TENANT
"$operator_root/tools/hexalith" config set operator actor APPROVED-OPERATOR-SUBJECT
```

The CLI creates the private directory and file ACLs. Save the following as `set-private-token.py` in your task directory and run `python3 /absolute/path/set-private-token.py` (Windows: `python C:\absolute\path\set-private-token.py`). Enter the owner's token at the hidden prompt; never paste it into chat, a client registration, screenshots or evidence. Unlike the quick start's `--token` command, this script also keeps it out of command arguments. Close clients before changing the profile. This modifies the existing file in place, retaining its permissions:

```python
import getpass
import json
import os
from pathlib import Path

path = Path(os.environ["MCPCLI_HOME"]) / ".eventstore" / "mcpcli.json"
with path.open("r+", encoding="utf-8") as profile:
    document = json.load(profile)
    token = getpass.getpass("Short-lived operator token: ")
    if not token.strip():
        raise SystemExit("A nonblank operator token is required.")
    document["profiles"]["operator"]["token"] = token
    profile.seek(0)
    json.dump(document, profile, indent=2)
    profile.write("\n")
    profile.truncate()
```

Check `"$operator_root/tools/hexalith" config current --profile operator`. The token is masked; URL, tenant and actor must match the owner's approval, with profile sources for those settings. Leave `allowTenantOverride` false. The enrolled Tenants 7.0.4 package declares platform scopes for the coordinated gateway boundary. Tenants commands and cross-tenant reads declare `platform:tenants`, while single-tenant reads use an explicit canonical tenant matching their aggregate identifier. Parties uses the configured session tenant. No tenant belongs in the Party payload. Do not read or edit the admin CLI's `profiles.json`.

### Move from eventstore-admin or Parties.Mcp

This section covers connection settings only. It makes no parity or retirement claim: every EventStore Admin operation still has no McpCli replacement, so keep `eventstore-admin` for administration, and `Parties.Mcp` stays in service until its own retirement gates pass.

Nothing is imported. McpCli never reads the admin CLI's `~/.eventstore/profiles.json`, even though it sits beside `mcpcli.json`, and takes no setting from `EVENTSTORE_ADMIN_URL`, `EVENTSTORE_ADMIN_TOKEN`, `EVENTSTORE_ADMIN_FORMAT`, any other `EVENTSTORE_ADMIN_*` variable or the `Parties__Mcp__*` host settings. Its operator settings come only from the nine variables `EVENTSTORE_PROFILE`, `EVENTSTORE_URL`, `EVENTSTORE_TOKEN`, `EVENTSTORE_TENANT`, `EVENTSTORE_ACTOR`, `EVENTSTORE_ALLOW_TENANT_OVERRIDE`, `EVENTSTORE_FORMAT`, `EVENTSTORE_READ_ONLY` and `EVENTSTORE_STRICT`, plus `MCPCLI_HOME`, which selects the profile store. The default .NET host still loads `Logging__*` variables and content-root `appsettings*.json` files, which can change the diagnostics written to stderr. Create each McpCli profile by hand:

| Legacy setting | McpCli setting |
| --- | --- |
| `eventstore-admin config profile add NAME --api-url URL --api-token TOKEN --default-format FORMAT` | `hexalith config profile add NAME --url GATEWAY-URL --token GATEWAY-TOKEN --format json` (or `table`; there is no CSV). Use a Gateway-issued token from your environment owner: the Gateway may not accept an Admin API token. |
| `eventstore-admin` global `--url`/`-u`, `--token`/`-t`, `--format`/`-f`, `--profile`/`-p` | `--url`, `--token`, `--format`, `--profile`; McpCli has no short aliases |
| `eventstore-admin` global `--output`/`-o` | McpCli's own `--output` contract below; no admin output-file behavior carries over |
| `Parties.Mcp` `Parties:Mcp:EventStoreGatewayBaseUrl` | the profile's `--url` |
| `Parties.Mcp` forwarded caller `Authorization` header | the profile's own `--token`; nothing is forwarded |
| `Parties.Mcp` tenant from claims or headers | `config set NAME tenant TENANT` and `config set NAME actor ACTOR` |

The admin `--api-url` names the Admin API, which is not necessarily the EventStore Gateway; use the Gateway URL from your environment owner. Keep one profile per environment: a profile binds one Gateway URL, one token, one tenant and one actor. Switch environments with `--profile NAME` or `EVENTSTORE_PROFILE`, never by overriding only the URL.

Settings resolve in this order:

- Profile selection: `--profile`, then `EVENTSTORE_PROFILE`, then the stored `activeProfile`, then none. `config profile`, `config use` and `config set` ignore both selectors.
- `url`, `token`, `tenant`, `actor` and `format`: the flag, then its `EVENTSTORE_*` variable, then the selected profile, then the default (none; `json` for format).
- `allowTenantOverride`: the flag, then `EVENTSTORE_ALLOW_TENANT_OVERRIDE`, then the profile, then `false`. `readOnly` and `strict`: the flag, then the variable, then `false`. `output`: the flag only. `allowedExtensions`: the selected profile only.

The Gateway URL and the token must come from the same source: both from flags, both from the environment, or both from the selected profile. A URL with no token is allowed. Any mix, such as `--url` or `EVENTSTORE_URL` with a profile token, or `--url` with `EVENTSTORE_TOKEN`, fails as `configuration_invalid` with exit 2 before any Gateway call, for example `The gateway URL from flag and the token from profile must come from the same source: flags, environment, or the selected profile.` The message names both sources and never the token. Settings resolution applies this rule on every verb that resolves settings, including discovery, `config current`, `config profile add` and `mcp` (whose error goes to stderr), so a stored token can never travel to another environment's URL.

Error privacy: a `gateway_error` document carries only `status`, `detail` (or the title), `reason`, `retryable`, `clientAction`, `retryAfter` and a canonical `correlationId`. Other Problem Details members, such as `type`, `instance`, `tenantId`, `errors`, `rejectionType` and extensions, non-JSON response bodies and exception text never reach stdout, stderr or MCP content in either head. Gateway HTTP diagnostics on stderr name only the method, the request URL without its query, the elapsed time and the status, and a failed request logs no exception. McpCli copies `detail` (or the title), `reason`, `clientAction` and `retryAfter` as the Gateway sends them; for a non-JSON response, `detail` is the HTTP reason phrase. The Gateway sanitizes Command rejections, but it passes a module's Query error message through as `detail` for every status except the invalid-page 400 and 403, including the 400 malformed-request response built from the module's `sentinel: detail` message, so that text is only as private as the module makes it. Parties returns only sentinel codes there.

Legacy Party IDs: McpCli refuses a braced `{GUID}`, parenthesized `(GUID)` or X-format `{0x…,{0x…}}` root `PartyId` with `validation_failed` at `/PartyId` before any Gateway call, and does not convert it. Parties accepts these forms, but the Gateway's aggregate rules cannot address them. Support-safe IDs such as `Legacy.party_01-A` work, and child identifiers such as `ContactChannelId` and `IdentifierId` reach the Gateway unchanged in any of these forms.

### Register one stdio server per client

All clients launch the same absolute executable with arguments `mcp --transport stdio --profile operator` and the same private `MCPCLI_HOME`. A client owns its own server process; one registration exposes both modules and the five generic tools. Do not add separate Tenants/Parties servers or point a client at the Gateway as an MCP HTTP URL.

For [Claude Code](https://code.claude.com/docs/en/mcp), run from the project in which you will test, replacing both absolute paths:

```sh
claude --version
claude mcp add hexalith --transport stdio --scope local --env MCPCLI_HOME=/absolute/path/hexalith-operator/home -- /absolute/path/hexalith-operator/tools/hexalith mcp --transport stdio --profile operator
claude mcp get hexalith
```

If .NET is installed in your home directory (for example `~/.dotnet`), add `--env DOTNET_ROOT=/absolute/path/.dotnet` before `--`. Open Claude Code in that project, inspect `/mcp`, and approve the intended server/tools. Local scope is private to that project. Record the actual initialization/connection result and expand the returned tool calls in the conversation.

For [Claude Desktop](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers), open **Settings → Developer → Edit Config** and merge this entry into `mcpServers` in `claude_desktop_config.json`, preserving other servers. Fully quit and reopen Desktop, then inspect its connector/tool list and server logs. Desktop's Code tab is a separate harness and does not count as the Desktop conversation session. In the Cowork tab, the tools appear as `mcp__remote-devices__hexalith__*`.

```json
{
  "mcpServers": {
    "hexalith": {
      "command": "/absolute/path/hexalith-operator/tools/hexalith",
      "args": ["mcp", "--transport", "stdio", "--profile", "operator"],
      "env": {"MCPCLI_HOME": "/absolute/path/hexalith-operator/home"}
    }
  }
}
```

For [VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers), record **Help → About**, the Copilot extension version and the selected agent harness. Run **MCP: Add Server → Command (stdio)** with the absolute launch command. The current **Global → Copilot Global** destination uses `~/.copilot/mcp-config.json` (or `$COPILOT_HOME/mcp-config.json`) and the same `mcpServers` entry above. Its portable format does not support `inputs` or `envFile`. For the **Local** harness, open the user-profile `mcp.json` or a private test workspace's `.vscode/mcp.json` and merge the following `servers` entry. Select that harness in Chat, trust/start `hexalith`, enable its tools and inspect the actual tool output. Do not commit a personal workspace configuration. With a Windows `wsl.exe` registration (see Windows/WSL below), run the Copilot CLI harness from a local VS Code window, not a WSL remote window. In a WSL remote window that harness runs inside Linux, receives the Windows definition and cannot start `wsl.exe` (`No such file or directory` in its runtime log). In a local window, the Copilot CLI harness reads the user-profile `mcp.json` entry.

```json
{
  "servers": {
    "hexalith": {
      "type": "stdio",
      "command": "/absolute/path/hexalith-operator/tools/hexalith",
      "args": ["mcp", "--transport", "stdio", "--profile", "operator"],
      "env": {"MCPCLI_HOME": "/absolute/path/hexalith-operator/home"}
    }
  }
}
```

On Windows, change the JSON command to `C:\\Users\\YOUR-USER\\hexalith-operator\\tools\\hexalith.exe` and `MCPCLI_HOME` to its Windows home path, using JSON-escaped backslashes. A GUI launch may inherit neither the shell PATH nor shell variables. Use literal absolute paths, restart after environment changes, and set `DOTNET_ROOT` in the entry's `env` to the actual .NET installation directory if the apphost cannot find the runtime. Never assume `~`, `$HOME` or shell expansion in JSON.

For [Windows/WSL](https://learn.microsoft.com/en-us/windows/dev-environment/wsl-interop), either install the tool, .NET and profile natively on Windows, or launch the WSL installation explicitly. A native Windows client cannot execute `/home/.../hexalith` directly. An explicit bridge uses `command: "C:\\Windows\\System32\\wsl.exe"` and `args: ["--distribution", "YOUR-DISTRO", "--cd", "/home/YOUR-USER/hexalith-operator/home", "--exec", "/usr/bin/env", "MCPCLI_HOME=/home/YOUR-USER/hexalith-operator/home", "/home/YOUR-USER/hexalith-operator/tools/hexalith", "mcp", "--transport", "stdio", "--profile", "operator"]`. Keep `--cd` with a small Linux directory: a Windows GUI starts `wsl.exe` in its own Windows directory (for example `C:\Users\YOU` or `System32`), and without `--cd` the server starts under `/mnt/c/...` and can stall before answering `initialize` while it scans that tree. `--exec` does not load your shell profile: if .NET is installed in your Linux home (for example `~/.dotnet`), add `"DOTNET_ROOT=/home/YOUR-USER/.dotnet"` after the `MCPCLI_HOME=…` argument, and add the `wsl.exe` options `"--user", "YOUR-USER"` before `"--exec"` when the tool belongs to a user other than the distribution's default user. Confirm .NET and the private Gateway port-forward are reachable inside that distribution. Record this combination as its own tested environment.

### Read an approved tenant (Tenants 7.0.4)

Call `run_query` with the following MCP argument object. Replace every `APPROVED-TENANT` with the same approved canonical lowercase tenant configured in your operator profile; `tenant`, `aggregateId` and payload `TenantId` must match.

```json
{"operation":"tenants.get-tenant","tenant":"APPROVED-TENANT","aggregateId":"APPROVED-TENANT","payload":"{\"TenantId\":\"APPROVED-TENANT\"}"}
```

Require `isError: false`, matching JSON text and `structuredContent`, result `tenant` equal to the selected tenant, and `document.tenantId` equal to that tenant with `document.status: "Active"`. This is current invocation guidance; the automated artifact approval and scripted replay do not establish a new actual operator-client session. Continue with the cross-module task below for actual-session acceptance.

<a id="complete-the-approved-cross-module-task"></a>

### Complete the approved cross-module task

The [historical sessions](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/operator-setup-history.md) used Tenants 5.10.0 and its `system` scope. Fresh sessions use current Contracts 7.0.4 and the selected canonical tenant as shown below; the [Gateway boundary](#gateway-boundary) describes its explicit scopes. Automated approval and scripted replay make no actual operator-client acceptance claim.

In each actual client, request the tools from server **hexalith** explicitly. First call `list_modules` with `{}`, then `list_operations` with `{"module":"tenants"}` and `{"module":"parties"}`, and `describe_operation` for `tenants.get-tenant`, `parties.create-party` and `parties.get-party`. Confirm the five tools `list_modules`, `list_operations`, `describe_operation`, `send_command`, `run_query`, both modules and `submittable: true` for the selected operations.

Replace `APPROVED-TENANT` with the approved tenant and use a fresh Party ID, contact ID and identifier ID for **every** client and attempt. The following are MCP **argument objects**, not CLI commands. `payload` is a string containing JSON; keep its property casing. Use synthetic names and contact details only.

```json
{"operation":"tenants.get-tenant","tenant":"APPROVED-TENANT","aggregateId":"APPROVED-TENANT","payload":"{\"TenantId\":\"APPROVED-TENANT\"}"}
```

Call `run_query` with those arguments. Require result `tenant` and `document.tenantId` equal to the selected canonical tenant, with `document.status: "Active"`. Then obtain the operator's write approval and call `send_command` once:

```json
{"operation":"parties.create-party","payload":"{\"PartyId\":\"party-CLIENT-ATTEMPT\",\"Type\":\"Person\",\"PersonDetails\":{\"FirstName\":\"Operator\",\"LastName\":\"Setup\"},\"ContactChannels\":[{\"PartyId\":\"party-CLIENT-ATTEMPT\",\"ContactChannelId\":\"email-CLIENT-ATTEMPT\",\"Type\":\"Email\",\"Value\":\"operator@example.test\",\"IsPreferred\":true}],\"Identifiers\":[{\"PartyId\":\"party-CLIENT-ATTEMPT\",\"IdentifierId\":\"external-CLIENT-ATTEMPT\",\"Type\":\"Other\",\"Value\":\"operator-setup\"}]}"}
```

A successful command has `isError: false`, matching JSON text/`structuredContent`, `status: "accepted"`, the selected Parties tenant and your fresh Party ID. This is the timer's stop point. Keep the message/correlation IDs. Acceptance still requires a persisted query; call `run_query` with:

```json
{"operation":"parties.get-party","payload":"{\"PartyId\":\"party-CLIENT-ATTEMPT\"}","entityId":"party-CLIENT-ATTEMPT"}
```

Require the selected result tenant, `document.id` equal to your Party ID, `isActive: true`, `isErased: false`, the synthetic person, contact and identifier values. If projection state is pending, bounded **read** checks for up to 45 seconds are permitted; record each query. Never repeat `send_command` after a timeout or ambiguous error. Stop and let the owner inspect the message ID and persisted state. Retain sanitized actual client connection, discovery, call and persisted-result evidence; a model's narrative answer or SDK smoke is insufficient. Stop the client-owned server and private port-forward after the session; the environment owner removes only task-owned state according to the reviewed cleanup plan.

### Resolve setup failures

| Failing step | Correction and required record |
| --- | --- |
| Install/hash mismatch | Stop; reacquire the accepted archives/receipts. Retain the exact failing command and hash. |
| Executable/runtime not found | Check the absolute native/WSL command, permissions, .NET 10 runtime and GUI `DOTNET_ROOT`; restart the client. If `dotnet` is a snap or version-manager shim, the quick start derives the wrong `DOTNET_ROOT`: use the folder that contains `shared/Microsoft.NETCore.App` (the path `dotnet --list-runtimes` prints, without that suffix). |
| `configuration_invalid` or missing profile | Check absolute `MCPCLI_HOME`, private file access, `--profile operator` and inherited `EVENTSTORE_*`; inspect masked `config current`. |
| `configuration_invalid`: the gateway URL and the token must come from the same source | Supply both from one source: remove the inherited `EVENTSTORE_URL`/`EVENTSTORE_TOKEN` or the extra `--url`/`--token`, or select another profile; see [Move from eventstore-admin or Parties.Mcp](#move-from-eventstore-admin-or-partiesmcp). |
| `configuration_invalid`: `The mcpcli profile document has an invalid profile entry.` | A stored profile name is invalid, for example one with a trailing newline saved by an earlier release, so every verb that reads profiles fails. Close clients, then edit the private `$MCPCLI_HOME/.eventstore/mcpcli.json` (default `~/.eventstore/mcpcli.json`) in place to rename or remove that key. If `activeProfile` names that key, update it to the renamed key or set it to `null` when removing the profile. Keep the file's permissions, then check `config profile list`. |
| Four tools / `read_only` | Remove an unintended inherited read-only setting only after confirming write approval; keep the failed attempt. |
| `submittable: false` with `configuration_invalid` | The profile has no Gateway URL; check `config current`. Discovery can succeed offline. |
| Connection refused on a call | Check the approved URL and that the private forward runs in the launching environment. |
| Authentication/authorization failure | First check that the call used your real tenant, not a placeholder such as `TENANT`. Then ask the environment owner to check expiry, the operation's declared platform scope or selected-tenant membership, Parties write scope and actor. Never substitute bootstrap credentials. |
| Tool absent / wrong config shape | Check client version, selected harness, scope, trust prompts and `mcpServers` versus `servers`; expand client server logs. |
| VS Code Copilot CLI harness reports no `hexalith` tools | In a WSL remote window its runtime cannot start a Windows `wsl.exe` registration; open a local VS Code window and start a fresh chat. Keep the failed session. |
| Setup run again reports `already installed` or `already exists` | Inspect `~/hexalith-operator` first, as in quick-start step 1. Only if it contains solely an earlier Hexalith setup, run step 5 to remove it, then start again from step 1. |
| `claude mcp add` reports `Invalid environment variable format` | Put the server name right after `add`; `--env` takes several values and otherwise reads the name as one. |
| Client keeps waiting for `initialize` (WSL bridge) | Add `--cd` with a small Linux directory before `--exec`, then restart the server. Without it the server starts in the client's Windows directory under `/mnt/c/...`. Keep the stalled server log. |
| Command outcome uncertain / persisted result missing | Preserve message IDs and errors, stop writes, request owner investigation; acceptance remains incomplete. |

Record every attempted session, failure, assistance and elapsed time in the [session checklist](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/operator-setup-checklist.md). An assisted, interrupted, unexecuted or over-900-second attempt remains visible and cannot be reported as unassisted success. The historical 685-second timing exception was assisted and used an experienced operator; it is neither first-time nor unassisted success. If using the actual-session acceptance path, repeat all three client sessions for the fresh candidate. The explicitly authorized automated path records no client-session result.

## Gateway boundary

See the [canonical scope upgrade](https://github.com/Hexalith/Hexalith.McpCli/blob/main/docs/release/canonical-scope-upgrade.md) for the 2.0.0 bootstrap and 2.0.1 paired release, tenant normalization and platform-scope migration.

The CLI and MCP server share one catalog and executor. McpCli discovers operations only from flagged, referenced `*.Contracts` packages. It submits commands and queries to the EventStore gateway; the gateway routes them to the owning module server. McpCli never connects to a module server or references its implementation packages.

`DependencyPolicyTests` enforces this boundary against the restored production graph and project references. `tools/dependency-policy.json` pins the exact closure reachable from the approved stack roots, the Decoration Package, and each flagged Contracts module. A module cannot widen that baseline or import another module's packages. Every rejected dependency includes its resolved identity and path from `Hexalith.McpCli`; every restored package permits only the `Microsoft.NETCore.App` framework reference. Adding a production direct root requires a PRD change and review of `directPackages`.

Test projects may use the policy's `directPackages`, enrolled modules, the Decoration Package, the named test packages (including EventStore testing/Aspire helpers and `Hexalith.Tenants.Aspire`), and the synthetic `Hexalith.McpCli.Sample.Contracts` fixture. Any other package, including one listed only in `baselinePackages`, is rejected as a direct test dependency. The gate checks the references evaluated in Debug and Release, plus every `PackageReference` and `ProjectReference` in the test project file itself, whatever its condition. The test packages and the sample are rejected in the production runtime graph even if added to a production policy list. The build-time analyzer project at `src/Hexalith.McpCli.Analyzers` is excluded from the production source-project checks; it uses `Microsoft.CodeAnalysis.CSharp` and `Microsoft.CodeAnalysis.Analyzers` with `PrivateAssets="all"`. Test projects may reference local `src/` projects and `tests/` fixtures, but cannot reference projects in `references/`. `Hexalith.Parties.Aspire` 2.0.0 is an approved test package after exact published archive and closure review. The AppHost closure test pins its version and server-free closure. Its independent Builds pin leaves the production Parties Contracts pin unchanged. The AppHost helper closure is checked separately against its approved helpers and support packages; a separate Manifest test pins the exact `Hexalith.*` package set of Integration.Tests. Its platform fixture retains `Hexalith.EventStore.Testing.Integration` 3.128.4 while the restored test-only `Hexalith.EventStore.Server`, `.DomainService` and `.ServiceDefaults` packages use the coordinated 4.1.0 cohort. The AppHost helper closure excludes `.Server` and `.DomainService`; its reviewed `aspireHelperSupportPackages` are `Hexalith.Commons.UniqueIds` 2.30.10 and `Hexalith.EventStore.Client`, `.Contracts` and `.ServiceDefaults` 4.1.0. The production graph excludes `.Server`, `.DomainService` and `.ServiceDefaults`.

Offline captured closures prove that decorated Tenants- and Parties-shaped packages can depend on McpCli Abstractions without adding production dependencies. `Hexalith.Projects.Contracts` 1.0.0 remains excluded: its closure adds `Microsoft.AspNetCore.App` and UI/web dependencies such as Fluxor, Fluent UI, and FrontComposer.Shell. Adding those packages to the baseline still fails the gate. Run a fresh `dotnet restore Hexalith.McpCli.slnx` before building and running `tests/Hexalith.McpCli.Manifest.Tests`; the candidate checks read committed fixtures and require no network restore.

The production manifest references `Hexalith.Parties.Contracts` **1.5.1** and `Hexalith.Tenants.Contracts` **7.0.4**, bound to their exact published archives, approved inventories and vectors. `Directory.Build.props` pins these module versions before importing the Builds catalog; advancing the Builds submodule preserves those approved artifacts. Changing either Contracts version requires matching artifact approvals and vectors. Offline discovery with `hexalith modules --strict` lists `parties` and `tenants`; `hexalith operations parties --strict` lists the seven approved Parties operations, and `hexalith operations tenants --strict` lists the fourteen approved Tenants operations. Inspect a complete name with, for example, `hexalith describe parties.search-parties --lint --strict` or `hexalith describe tenants.get-tenant --lint --strict`.

Current Tenants commands and the cross-tenant reads `tenants.list-tenants` and `tenants.get-user-tenants` declare `platform:tenants`. The single-tenant reads `tenants.get-tenant`, `tenants.get-tenant-users` and `tenants.get-tenant-audit` use an explicit canonical tenant matching the payload's `TenantId` aggregate. `TenantId` supplies aggregate routing; an optional `--aggregate-id` or MCP `aggregateId` must match it. The module has no fixed `system` scope. Strict discovery and descriptions are available offline; they establish no backend authorization or persisted effect.

The operations appear in this order in each module's strict discovery output:

| Parties | Tenants |
| --- | --- |
| `parties.create-party` | `tenants.add-user-to-tenant` |
| `parties.deactivate-party` | `tenants.change-user-role` |
| `parties.get-party` | `tenants.create-tenant` |
| `parties.list-parties` | `tenants.disable-tenant` |
| `parties.reactivate-party` | `tenants.enable-tenant` |
| `parties.search-parties` | `tenants.get-tenant` |
| `parties.update-party` | `tenants.get-tenant-audit` |
| | `tenants.get-tenant-users` |
| | `tenants.get-user-tenants` |
| | `tenants.list-tenants` |
| | `tenants.remove-tenant-configuration` |
| | `tenants.remove-user-from-tenant` |
| | `tenants.set-tenant-configuration` |
| | `tenants.update-tenant` |

Production enrollment requires an approved release inventory for every module and complete conformance vectors bound to the exact restored artifact. Each approved vector also needs a strict companion plan in `tools/live-topology/plans/<operation>.json`; update the v1 count pins in `.github/workflows/ci.yml` and `tools/live-topology/test_live_plans.py` when the approved v1 scope changes. CI checks the built manifest, strict Catalog discovery, description lint, name/type coverage, artifact hashes and complete CLI/MCP replay independently of dependency policy. The published Parties and Tenants artifacts pass their individual seven- and fourteen-vector package gates. Story 4.11 also replays all 21 operations in the combined production manifest and benchmarks its first Catalog construction plus exactly one Ulid sample in a fresh process. Full-v1 acceptance requires both `parties` and `tenants` from `tools/conformance-vectors/v1/v1-scope.json`. The separately qualified normal Tenants 5.10.1 five-package/container release repairs the container source labels. At that publication, enrollment stayed on Contracts 5.10.0 because the approved vectors and inventory bound its signed Contracts archive. Current enrollment binds Contracts 7.0.5 to the [automated public-artifact approval](https://github.com/Hexalith/Hexalith.McpCli/blob/main/evidence/release-maintenance-20261106/tenants-7.0.5/approval.json), the fourteen vectors with only package-version metadata refreshed, and the unchanged inventory digest. That approval records delegated Codex automation under the user's explicit bypass of human validation. The following Ubuntu measurement is historical evidence for the former cohort: its strict gate passed all 21 production operations; first Catalog construction plus exactly one Ulid sample measured 194.5002 ms against the 500 ms limit. See the [artifact and matrix audit](https://github.com/Hexalith/Hexalith.McpCli/blob/main/_bmad-output/implementation-artifacts/evidence/story-4-11/publication-20261021/parent-root-review-fixed-ubuntu-acceptance-audit.json). Local available-package evidence alone cannot grant acceptance. See [inventory coverage](https://github.com/Hexalith/Hexalith.McpCli/blob/main/tools/inventory-coverage/v1/README.md) and [artifact verification](https://github.com/Hexalith/Hexalith.McpCli/blob/main/tools/conformance-vectors/v1/README.md). [Move from eventstore-admin or Parties.Mcp](#move-from-eventstore-admin-or-partiesmcp) states the tested error-privacy and legacy Party ID behavior; their inventory dispositions, live authorization, domain effects, and legacy-host retirement retain their separate migration gates.

Both production gates run from the repository root after `python3 -m pip install -r tools/conformance-vectors/v1/requirements.txt`, `dotnet restore Hexalith.McpCli.slnx` and `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`; `check_enrolled.py` reads that restore's `src/Hexalith.McpCli/obj/project.assets.json`. The complete command sequence is in [Production parity and first-construction gate](https://github.com/Hexalith/Hexalith.McpCli/blob/main/tools/conformance-vectors/v1/README.md#production-parity-and-first-construction-gate). Run the complete production replay gate with `python3 tools/conformance-vectors/v1/check_enrolled.py --output /tmp/mcpcli-story411-evidence`. Use `--local` to collect available-package evidence labeled `local-only`; the default fails explicitly when either required module is absent. Then run `MCPCLI_BENCHMARK_REQUIRE_V1=true MCPCLI_BENCHMARK_OUTPUT=/tmp/mcpcli-catalog.json dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.CatalogPerformanceTests` for the strict 500 ms gate. Omit `MCPCLI_BENCHMARK_REQUIRE_V1` for a local measurement that records missing modules and `fullV1Accepted: false`.

The requested Works, Timesheets, Agents, Conversations, Projects, and Folders packages are not enrolled yet. Their current Contracts assemblies lack declarations or live gateway paths required by the [integration spec](https://github.com/Hexalith/Hexalith.McpCli/blob/main/_bmad-output/implementation-artifacts/spec-add-six-domain-modules.md).

## Run and debug from the Platform workspace

Run and debug McpCli from the Hexalith.Platform workspace, where this repository is the direct `references/Hexalith.McpCli` submodule. [`module/hexalith.module-manifest.v2.json`](https://github.com/Hexalith/Hexalith.McpCli/blob/main/module/hexalith.module-manifest.v2.json) declares McpCli with no servers and no interfaces. Its only dependency is `eventstore`, the gateway McpCli targets, so that gateway is its whole minimum environment. Platform pins a Builds tool of `4.34.0` or later, the first release that builds run-scoped McpCli; the [Platform README](https://github.com/Hexalith/Hexalith.Platform/blob/main/README.md#module-tool) names the current pin. From the Platform root, restore and run that pinned tool:

```sh
dotnet tool restore
dotnet tool run hexalith-module -- debug --manifest references/Hexalith.McpCli/module/hexalith.module-manifest.v2.json
```

The tool starts the EventStore gateway from source. It builds this checkout's `src/Hexalith.McpCli` in Debug into the run workspace, never packs or publishes it, and leaves this checkout's `bin` and `obj` untouched. When the environment is ready, an `HXI010` diagnostic names the run-scoped `Hexalith.McpCli.dll`, and `down` deletes it with the run. A CLI exits after each command, so launch that DLL under a debugger rather than attaching to a process; the [Platform README](https://github.com/Hexalith/Hexalith.Platform/blob/main/README.md#launch-mcpcli-under-a-debugger) has the recipe. Offline discovery verbs such as `modules` need no gateway URL and list the enrolled Parties and Tenants modules.

This repository's own `references/*`, including `references/Hexalith.Platform`, serve only this repository's own builds and tests. A run from this repository's root is not Platform evidence. Inside a Platform checkout, leave them uninitialized: the tool refuses any initialized nested submodule (`HXW003`).

## CLI and MCP

Run the executable from source with `dotnet run --project src/Hexalith.McpCli --`, or use `hexalith` after installing the tool package. A gateway URL is required for execution, but discovery works offline.

```sh
hexalith modules
hexalith operations your-module --kind read
hexalith describe your-module.your-operation --lint
hexalith config profile add dev --url https://gateway.example
hexalith config set dev tenant acme
hexalith config set dev allowedExtensions task-id,trace-id
hexalith config use dev
hexalith config current
hexalith send your-module.your-command --payload @command.json --idempotency-key 01ARZ3NDEKTSV4RRFFQ69G5FAV
hexalith send your-module.your-command --payload @command.json --extension task-id=abc --extension trace-id=xyz
hexalith query your-module.your-query --payload @query.json --page-size 25
hexalith mcp --transport stdio
```

`--url`, `--token`, `--tenant`, `--actor`, `--allow-tenant-override`, `--profile`, `--format json|table`, `--output`, `--read-only`, and `--strict` are global options. Command and query payloads can be inline JSON, `@file`, or `-` for stdin. `--read-only` removes command submission from the MCP tool list and makes CLI `send` fail. The local profile file is `~/.eventstore/mcpcli.json`. An absolute `MCPCLI_HOME` relocates it to `$MCPCLI_HOME/.eventstore/mcpcli.json` on every OS; an unset override retains the default, and an empty, relative, control-character-containing or file-valued override fails safely with `configuration_invalid`. Explicit constructor file paths take precedence. The Gateway URL and token must come from one source; see [Move from eventstore-admin or Parties.Mcp](#move-from-eventstore-admin-or-partiesmcp) for the full precedence. This is a behavior change: an existing setup that mixes sources, such as a profile URL with an injected `EVENTSTORE_TOKEN`, now fails with `configuration_invalid`; supply both from the environment, both as flags, or select a profile that holds its own token. Token values are masked in `config` output. `config profile`, `config use`, and `config set` ignore `--profile` and `EVENTSTORE_PROFILE` and render their output using `--format`, then `EVENTSTORE_FORMAT`, then `json`, never the active profile's format.

Profile mutations keep the directory, profile, lock and temporary files private. On Windows, the protected directory grants inheritable access only to the current user and LocalSystem, keeping existing files accessible to those identities. Profile, lock and temporary-file ACLs remain protected, explicit and non-inheritable. On Unix, the directory uses mode 0700 and profile files use mode 0600.

Commands use `hexalith send MODULE.OPERATION --payload '{"ItemId":"..."}'`, `--payload @command.json`, or `cat command.json | hexalith send MODULE.OPERATION --payload -`. The payload follows the declared schema and supplies the aggregate identifier; an optional `--aggregate-id` must equal it. A successful send exits 0, makes one Gateway request, and returns `operation`, the Gateway `messageId` when provided (otherwise the submitted message ID), the submitted `correlationId`, resolved `tenant` and `aggregateId`, and `status: "accepted"`. Each call generates a new ULID message ID and uses it as correlation unless `--correlation-id` supplies one. `--correlation-id` and `--idempotency-key` must be canonical uppercase ULIDs; any other value, including lowercase ULID text, fails with `validation_failed` instead of being replaced. The tool never generates an idempotency key. When a command declares a non-nullable or serializer-required idempotency member, the caller must supply `--idempotency-key`, including when a required member is nullable. `describe` reports this requirement as `envelope.idempotencyKeyRequired: true`. A supplied key replaces any raw mapped payload value; without it, a raw non-null key is rejected and a raw null key is removed. The result includes `idempotencyKey` only when supplied and `result` only when returned by the Gateway. It never includes a `duplicate` field. Validation failures exit 2 and submit nothing. Gateway failures exit 2 with a `gateway_error` document. A timeout or other uncertain Gateway outcome may have reached the Gateway; `gateway_error` reasons `gateway-timeout` and `gateway-unreachable` are uncertain even when the detail says the Gateway could not be reached. Do not assume that submitting the command again is safe.

Queries use `hexalith query MODULE.OPERATION --payload '{"Key":"item-42"}'`, `--payload @query.json`, or `cat query.json | hexalith query MODULE.OPERATION --payload -`. The payload follows the operation's described schema and preserves its property casing. Aggregate selection uses `--aggregate-id`, then the declared payload accessor, then a query's declared constant. An explicit value must agree with a payload accessor, may override a constant, and is required when neither source exists. Validation completes before exactly one Gateway submission using the catalog's routing values. Both heads preserve the descriptor's `projectionActorType` exactly when one is declared; omitting it would change the enrolled wire contract. Native receiver selection remains bound to the committed Gateway catalog. The pinned SDK 4.1.0 supplies the exact owner-enrolled selector policy, and the immutable Parties source selection declares the three published legacy bindings. Full native compatibility still requires fresh complete live CI for this selected cohort; offline replay and owner compilation do not replace that gate.

Enable a read-only session with `--read-only` or `EVENTSTORE_READ_ONLY=true`. After settings resolution and catalog access succeed, a `send` naming a declared write returns `read_only` with exit code 2 and zero Gateway requests, even without a Gateway URL. Refusal happens before reading payload files or stdin, parsing JSON, processing `--extension key=value` entries, or validating `--aggregate-id`, `--correlation-id`, and `--idempotency-key`. A missing or blank `send` operation returns `invalid_arguments` for `operation` before catalog lookup in either mode. For read-only `send`, an unknown operation returns `unknown_operation` and naming a read operation returns `validation_failed`; these errors take precedence over missing or unreadable payloads and malformed extensions. Without read-only mode, `send` returns `invalid_arguments` for missing payloads or unreadable payload files, an `--extension` value with no `=`, an empty key before `=`, or repeated identical extension keys before those operation errors. Queries and discovery remain available; writes remain listed and describe reports `submittable: false, reason: read_only`. An explicit `--read-only false` overrides the environment setting. Run `hexalith config current --format json` with the same read-only flag and environment to check `readOnly` and its origin in `sources.readOnly` (`flag`, `EVENTSTORE_READ_ONLY`, or `default`).

`--read-only` enables the mode without a value, or accepts an explicit `true` or `false` value (case-insensitive). The flag does not accept `1` or `0` as boolean values; use `true` or `false`. For example, `operations --read-only 0` enables read-only mode and takes `0` as the module name. `EVENTSTORE_READ_ONLY` accepts exactly `true`, `false`, `1`, or `0`, with case-sensitive matching. Settings resolution for discovery, execution, `config` (including profile management), and MCP stdio startup rejects any other value, including `True`, with `configuration_invalid` and exit code 2 unless an explicit `--read-only` flag overrides it. Command-line parse failures, help, `--version`, MCP `--transport`, `--format`, or `--output` errors, and `config profile add` refusal of `--tenant`, `--actor`, or `--allow-tenant-override` can return before this check. An earlier configuration error, such as an invalid Gateway URL or a missing selected profile, can also take precedence.

The global CLI `--tenant` sets the session tenant; it is never a per-call override. A command or query may declare an exact `PlatformScope` such as `platform:tenants`; `describe` reports it as `envelope.platformScope` and omits `tenant` from the operation arguments. That declared scope wins over the session tenant, and a conflicting MCP per-call tenant fails at `/tenant` before any Gateway call. The Gateway still checks its cataloged operation, credential, and required permission; the tool declaration does not grant platform authority. A platform scope cannot be combined with a module `FixedTenant`. For other operations, a module's fixed tenant wins over the session value. A query requires a resolved tenant. MCP per-call tenants may replace a session tenant only when tenant override is enabled; matching values need no override, and a per-call value cannot conflict with a fixed tenant. Public variable-scope tenant input is lowercased without trimming before tenant selection and the override comparison. When no session tenant is configured, the canonicalized MCP per-call tenant is selected without the override gate. Public variable-scope calls using `system` are refused. Commands take a declared payload tenant from the resolved tenant and a declared actor from the session only. A command that declares an actor requires a session actor from `--actor`, `EVENTSTORE_ACTOR`, or the selected profile's `actor`; without one it fails with `validation_failed` at `/actor`, even if the payload supplies an actor. If the caller includes either mapped member, it must be a JSON string exactly matching the trusted value. The executor fills omitted or matching members before submission and validates the rebuilt payload. A mapped correlation member is always replaced with the supplied `--correlation-id` or the generated message ID.

Accepted F7 limitation (`epic-4-retro-item-9-ascii-tenant-input`): invariant lowercasing currently maps U+212A KELVIN SIGN in `Kelvin` to the public tenant `kelvin`, as the Gateway does. The owner accepted this limitation for Story 5.4 on 2026-11-09; other tested non-ASCII look-alikes are refused at `/tenant` before any Gateway request. This acceptance grants no retirement or release approval.

Commands and queries follow the module's declared ULID or String kind for aggregate identifiers. In ULID-kind modules, aggregate identifiers and marked payload identifiers must use canonical uppercase ULID text. Payload properties of CLR type `Ulid` must also use canonical uppercase text in any module, as must `Ulid` elements in nested collections and dictionaries. In String-kind modules, marked string-typed payload properties have no added ULID pattern or nonempty requirement; other schema rules may still constrain them. Aggregate identifiers also require 1–256 ASCII letters, digits, dots, underscores, or hyphens, starting and ending with a letter or digit. Ordinary tenant input is lowercased without trimming, then must be 1–64 ASCII letters, digits, or hyphens with the same start/end rule; `system` is reserved for historical storage. A declared platform scope uses `platform:` followed by a nonempty canonical lowercase name with no doubled hyphen; the Gateway must also recognize the exact cataloged scope. A declared payload tenant member is filled from the resolved request scope; a conflicting or non-string caller value fails validation.

Queries accept `--entity-id` for an optional entity within the aggregate. Entity identifiers require 1–256 ASCII letters, digits, dots, underscores, or hyphens, starting and ending with a letter or digit. They follow this Gateway syntax even for ULID-kind modules.

Only the selected Profile supplies the extension allowlist, which is empty by default; unlisted keys are refused. Set a Profile's extension allowlist with `config set PROFILE allowedExtensions task-id,trace-id`, using comma-separated keys without spaces; `config set PROFILE allowedExtensions ''` clears the list. Supply values with repeatable `send --extension key=value` options or the MCP `send_command` tool's `extensions` object. Both heads use the same validation. Allowlist matching ignores case, but a call cannot contain two keys that differ only by case. Keys may contain ASCII letters, digits, dots, underscores, hyphens, and colons; each colon-separated segment must start and end with a letter or digit. Keys and values must pass the Gateway's injection checks, and values cannot contain `<`, `>`, `&`, `'`, or `"`. The reserved `actor:globalAdmin` key and every key beginning with `identity:` are rejected regardless of case, both in Profile allowlists and command calls. A colon-delimited key also requires exactly one Gateway trusted-extension policy to claim and accept it for that authenticated caller and command. At most 32 entries are allowed, with keys up to 100 UTF-16 code units, values up to 1,000 UTF-16 code units, and 4,096 UTF-8 bytes combined. Both heads send approved keys and values unchanged; queries do not carry extensions.

Extension checks reject case-insensitive script or HTML patterns (`javascript` followed by optional whitespace and `:`, `on` followed by word characters, optional whitespace and `=`, or `<` followed by optional whitespace and `script`, `iframe`, `object`, or `embed`), SQL patterns (an apostrophe and semicolon followed by optional whitespace and `DROP`, `ALTER`, `DELETE`, `INSERT`, `UPDATE`, or `EXEC`; `UNION` followed by whitespace and `SELECT`; or `--` followed only by whitespace to the end), LDAP fragments `)(`, `*)(`, `|(`, or `&(`, and path traversal fragments `../` or `..\`. These checks match anywhere in a key or value, so values such as `session_id=abc` and `partition_key=7` are refused by the `on…=` rule. Values also reject control characters below U+0020 except tab, LF, and CR.

`--page-size` accepts 1–200, `--offset` accepts 0–2,147,483,647, and `--cursor` accepts at most 4,096 UTF-16 code units. A nonblank cursor cannot be combined with an offset, including offset 0; empty or whitespace cursors are preserved. To request the next page when the projection uses cursor paging, pass the returned `paging.nextCursor` as `--cursor` without `--offset`. These options populate the query envelope's `Paging` with only the values supplied. Omitting all three omits envelope paging. Payload members named `PageSize`, `Offset`, or `Cursor` remain ordinary payload data, retain their lint warnings, and never supply or override envelope paging.

Query success exits 0 and always returns `operation`, `tenant`, and `document`, including `"document": null` when the Gateway returns no payload. `paging` appears only when returned by the Gateway; it includes `pageSize` and independently returned `offset`, `nextCursor`, `totalCount`, or `hasMore`. Unavailable metadata is omitted; returned zero counts/offsets and `hasMore: false` are preserved. Request paging never supplies result metadata. Queries carry no correlation identifier or extensions. Validation failures exit 2 without submitting to the Gateway.

`modules`, `operations <module>`, and `describe <operation>` browse the local Contracts catalog without making Gateway requests, even when a URL is configured. Modules and operations are listed in ordinal name order. `operations` includes both reads and writes by default; `--kind read` or `--kind write` filters the list. Read-only mode keeps writes visible. `describe` includes the payload schema, an example when declared, envelope requirements and arguments, and `lintFindings`. Without a URL it reports `submittable: false` and `reason: configuration_invalid`; a write in read-only mode reports `reason: read_only` first. `submittable` reflects only read-only mode and whether a URL is configured; it does not check the token, tenant, actor, or Gateway reachability. Module property casing is preserved in schemas and examples.

With `--format table`, modules use tab-separated `NAME`, `OPERATIONS`, `DESCRIPTION` columns, operations use `NAME`, `KIND`, `DESCRIPTION`, and configuration displays use `FIELD`, `VALUE`. Raw `NAME`, `KIND`, and `DESCRIPTION` cells escape backslash as `\\`, tab as `\t`, carriage return as `\r`, and newline as `\n`; configuration `VALUE` cells retain their serialized JSON escapes. `describe` stays JSON. It exits 0 even with lint findings unless `--lint` is supplied; with that flag, findings produce exit 1 without changing the document. Errors exit 2.

### Output and exit codes

Results use the canonical JSON serializer on stdout, or in `--output` when a result file is selected. JSON uses UTF-8 with LF internally and one LF terminator on every OS; table formatting keeps the platform newline. Tables apply only to module, operation, and configuration displays. Successful `describe`, `send`, and `query` results remain JSON and emit one format note on stderr when table format was requested.

- Exit 0 means a result. Help, version, and normal MCP shutdown also exit 0.
- Exit 1 is reserved for `describe --lint` with findings.
- Exit 2 means no result. Non-MCP failures are one JSON object on stdout containing only `error`; `--format table` and `--output` do not redirect or change it. MCP failures before request serving use stderr and leave stdout empty.

If an action does not stop after Ctrl+C or SIGTERM, System.CommandLine's termination timeout can instead return 130 or 143. Failures before result writing leave an existing result file unchanged; runtime write failures and interruptions have the restoration risks described below. An interrupted `send` can also exit 2 with `internal_error` after the Gateway accepted it; do not retry without a trusted idempotency mechanism.

`error.code` is one of `validation_failed`, `gateway_error`, `unknown_operation`, `unknown_module`, `invalid_arguments`, `read_only`, `catalog_empty`, `catalog_invalid`, `unsupported_transport`, `configuration_invalid`, or `internal_error`. Validation errors identify the requested operation and all detected violations with JSON Pointer paths. Unknown names include up to three canonical suggestions. Unexpected failures return a fixed `internal_error` message without exception text or secrets. `mcp --transport http` is refused with `unsupported_transport` because HTTP is planned for the next release.

### Parsing and help

- Parse failures return `invalid_arguments` and exit 2, without printing usage or echoing supplied values. Unknown-option and invalid-argument messages point to `--help` for usage. The `argument` member names a recognized option (for example, `pageSize` or `readOnly`), or uses `arguments` for command syntax. MCP parse failures use stderr; other parse failures use stdout.
- Help must appear alone after its command path, such as `hexalith send --help`. `--version` must be the only argument.
- Leading directive-shaped tokens such as `[suggest]` are refused.
- Put `--` before a positional value beginning with `-` or matching a slash help alias or its attached-value form. Examples: `hexalith config set dev actor -- -bob`, `hexalith config set dev actor -- /h`, and `hexalith config set dev actor -- /h:x` (also for `/?`).
- Every token after `--` is positional, so put options before it.
- For an option value beginning with `-` or resembling a help alias, attaching it with `=` or `:` is unambiguous. Examples: `--token=--abc` and `--token=-h`.

### Execution, configuration, and MCP

Gateway authentication and authorization refusals remain `gateway_error` with status `401` or `403`; both heads preserve the same shared error document. `gateway_error.status` is copied from the EventStore client exception, including when the client reports a malformed or semantically failed `2xx` response. A Gateway Problem Details `status` may differ from the HTTP response status. `detail` falls back from the client exception's Detail to Title, then a generic message. `reason`, `retryable`, `clientAction`, `retryAfter`, and `correlationId` appear only when the exception provides them, and a `correlationId` that is not a canonical uppercase ULID is omitted; no message or retry identifier is invented. A Gateway error after a command submission is not proof that the command was rejected, so do not retry an uncertain outcome without a trusted idempotency mechanism.

On Unix, new regular `--output` files use mode 0600; on Windows they inherit the directory ACL. Before a Gateway request or profile mutation, the CLI checks predictable destination and staging failures without changing the result target. These preflight failures use `internal_error` with the stable message `The result destination cannot be written; no request was sent.` New regular files stage beside the destination; existing regular files and backups stage in the system temporary directory. Existing regular files retain their permissions, ACL, and symbolic-link target; a dangling output link creates its target. Read-only and write-only existing files are refused before mutation because their previous bytes cannot be safely replaced or backed up. Character devices, pipes, and FIFOs receive output directly. Runtime failures can still occur after preflight, including disk exhaustion, a disappearing path, or a device error. Writing to a named FIFO without a reader waits for one to connect. A caught write failure to a regular file restores its previous bytes; process interruption or another failure during restoration can leave a partial file. A `send` may already have been accepted if a later runtime write to `--output` fails and the CLI exits 2; do not retry that command solely because the result file was not written. Likewise, a `config profile add`, `config profile remove`, `config use`, or `config set` change may already be saved when that write fails; check `config current` or `config profile list` before retrying.

Catalog diagnostics go to stderr while ordinary discovery retains valid entries. `--strict` rejects any catalog diagnostic, including warnings, with `catalog_invalid` at exit 2 before checking for an empty catalog. Lint findings alone do not invalidate a strict catalog. A catalog with no valid operations returns `catalog_empty` at exit 2 when strict diagnostics have not already rejected it. `config` and `--version` bypass catalog construction.

`config profile add` stores only `--url`, `--token`, and `--format`, never environment values; it replaces the whole record when the profile already exists and refuses an explicit `--tenant`, `--actor`, or `--allow-tenant-override` without writing anything. After adding the profile, `config set` changes one of `tenant`, `actor`, `allowTenantOverride`, or `allowedExtensions` while keeping every other field.

Start the server with `hexalith mcp --transport stdio`. It starts without a prompt, resolves settings and checks the local Catalog before serving, and supports both the 2025-06-18 initialization flow and the 2026-07-28 discovery flow. Discovery works without a Gateway URL. Stdout carries only JSON-RPC; logs and diagnostics use stderr. A valid inherited `table` format does not change protocol output, and explicit `--format json` is accepted. Explicit `--format table` and any `--output` are rejected before Catalog or transport startup; format takes precedence when both are supplied, and the output path is not opened.

Before serving, invalid settings, an empty Catalog, or strict Catalog diagnostics produce one structured `{"error": ...}` document on stderr, exit 2, and leave stdout empty. Once serving, tool failures are MCP results, without a second stderr error document. A normal client shutdown exits 0. An unexpected host failure exits 2 with the fixed stderr diagnostic `MCP server stopped unexpectedly.`

The stdio MCP server advertises five generic tools in a normal session, in this order: `list_modules`, `list_operations`, `describe_operation`, `send_command`, and `run_query`. A read-only session advertises four, omitting only `send_command`. Start with `list_modules` for names and operation counts, pass a module name to `list_operations` (optionally with `kind: "read"` or `"write"`), then pass an operation name to `describe_operation` for its payload schema, optional example, envelope arguments, lint findings, and `submittable` state. When the description says `submittable: true`, use `run_query` for a read or `send_command` for a write. `submittable` reflects only read-only mode and whether a URL is configured; it does not check the token, tenant, actor, or Gateway reachability. These discovery calls work without a Gateway URL; descriptions then report `submittable: false` with `reason: configuration_invalid`. In a read-only MCP session, writes remain visible in discovery and describe reports `reason: read_only` for them, which takes precedence over `configuration_invalid`. Its protocol output uses stdout and diagnostics use stderr. The HTTP MCP transport is reserved for a later release.

MCP execution requires `operation` and `payload` as strings: `payload` contains JSON text with the module's property casing, for example `{"operation":"sample.get-item","payload":"{\"ItemId\":\"01ARZ3NDEKTSV4RRFFQ69G5FAV\"}"}` for an enrolled sample contract. File and stdin shorthand (`@file`, `-`) belongs to the CLI; MCP passes JSON text directly. Both execution tools accept optional string `tenant` and `aggregateId`. `send_command` also accepts string `correlationId` and `idempotencyKey`, plus an `extensions` object mapping keys to string values. `run_query` accepts string `entityId` and `cursor`, plus integer `pageSize` and `offset`. The tenant, identifier, extension, and paging rules above apply unchanged.

MCP success returns the same complete document as CLI/Core in `structuredContent`, with `isError: false` and matching JSON in the first text content item. Command results omit `idempotencyKey` unless supplied and `result` unless returned; query results always contain `document`, preserving objects, scalars, arrays, and JSON null, and include `paging` only when the Gateway returns it. Core refusals and Gateway failures return `isError: true` with the same `{"error": ...}` document in structured and text content. Unexpected tool exceptions return a sanitized `internal_error`. Missing required arguments and values that do not match the input schema return JSON-RPC invalid-parameters errors before execution. `run_query` `pageSize` and `offset` values that are not representable as an Int32 integer (for example `2147483648`, `25.0`, or `1e20`) also return invalid-parameters, with the message "<field> must be representable as an Int32 integer." Each advertised output schema has an object root and closed success/error document branches; embedded payload schemas and returned JSON values retain their own allowed structure. Both the legacy `2025-06-18` initialization flow and the `2026-07-28` discovery flow are verified through SDK stdio clients.

Core owns the advertised result constraints: canonical success names and uppercase ULIDs, Gateway tenant/scope and aggregate syntax, nonempty text, positive page sizes, nonnegative counts and offsets, at most three canonical suggestions, and at least one validation violation. Descriptions require a valid unavailability reason when `submittable` is false, restrict lint findings to the four warning codes with valid property pointers when applicable, and enforce duplicate-free envelope arguments appropriate to the operation kind and fixed tenant or platform scope. Embedded `schema` and `example` roots are objects with open contents, including nested boolean schemas; returned `result` and `document` values may contain arbitrary JSON. An `unknown_operation` error echoes the exact nonempty requested name, including noncanonical spelling, while suggestions remain canonical.


## Live topology and semantic vectors

The canonical test lane composes the owned package gateway and qualified Tenants and Parties source hosts through published Aspire helpers, with the separately qualified Platform catalog reader. The AppHost keeps its direct-checkout guards; CI additionally verifies exact source identities, clean owned files and authenticated public archives. Only disposable hosted CI selects revisions from `tools/live-topology/native-runtime.json`. Do not initialize nested dependencies or substitute a locally cached candidate. The AppHost references no server project or implementation package; separate owner metadata preparation does not alter the Parties host graph. The independent integration harness retains its reviewed test-only closure.

Once the exact public dependencies and artifact approvals are available, run these non-launching checks from this repository root:

```bash
dotnet restore tests/Hexalith.McpCli.Integration.Tests/Hexalith.McpCli.Integration.Tests.csproj
dotnet build tests/Hexalith.McpCli.Integration.Tests/Hexalith.McpCli.Integration.Tests.csproj --no-restore --configuration Release -warnaserror
python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'
python3 tools/live-topology/run-vectors.py --output /tmp/mcpcli-live-preflight --preflight-only
```

Use the bounded CI preparation/execution hooks below for the live lane. Preparation must succeed against the exact selected sources before either isolated runner starts. The public Tenants 7 approval and full remote live acceptance remain independent gates.

The supported wrapper requires Linux amd64, Python 3.11.4 or later, GNU or uutils coreutils `timeout`, and permission to create user, PID, network and mount namespaces. Install Aspire CLI 13.6.1 with its DCP and dashboard bundle in `~/.aspire/bundle` (the AppHost uses `AspireUseCliBundle=true` with SDK/hosting 13.6.4), Dapr CLI 1.18.2 and runtime 1.18.7, and ensure Docker is running with a successful `docker info` (required by the shared platform fixture). A fresh disposable isolated Dapr environment and private Redis are mandatory: every AppHost launch persists the test-owned Tenants bootstrap administrator, the smoke can write operational metadata, vector cases submit Commands, and default host Redis may contain user state. Use the [bounded private-runtime bootstrap](https://github.com/Hexalith/Hexalith.McpCli/blob/main/tools/live-topology/README.md) to set `private_runtime` and recreate the hash-verified native binaries. The wrapper starts Redis, Sentry, placement and scheduler only inside private namespaces. The hooks enforce a mandatory outer process deadline; the fixture and live AppHost refuse direct execution without the isolation sentinel set by the wrapper after entering private namespaces. AppHost preflight and composition inspection remain available without launching resources. A wrapper-level prerequisite failure ends the run with `Private environment failed: …` and exit 1 before the smoke; the skip diagnostics below describe the fixture’s own checks. Missing basic prerequisites produce the platform diagnostic, `DAPR integration prerequisites are unavailable. Run 'dapr init' and ensure Redis, placement, and scheduler are reachable.`, and a skipped smoke. The fixture supplements that basic platform probe with bounded CLI/Sentry checks and required mTLS environment inputs; missing requirements use the same standard skip prefix with specific detail. The smoke uses the fixture’s runtime skip so these additional checks execute even when discovery-time basic probes would otherwise skip it. Inside the wrapper, a vector case first requires the single-Operation selection that `run-vectors.py` passes, so a vector case started without it fails with that selection error instead of a skip. The base fixture also checks Docker and can skip with `Aspire topology prerequisites are missing. Start Docker Desktop…`; this diagnostic differs from the basic Dapr skip prefix. The documented `-failSkips` makes a skipped smoke exit nonzero with `FAIL_SKIP`; a skip does not establish live acceptance.

The default-deny sidecar ACL identifies callers through mTLS, so `dapr init` alone is insufficient. Inside the disposable environment, the wrapper runs Sentry on `127.0.0.1:50001` with trust domain `public`, and placement and scheduler use TLS with the same CA and Sentry. It supplies `DAPR_TRUST_ANCHORS`, `DAPR_CERT_CHAIN` and `DAPR_CERT_KEY` from its fresh private Sentry CA and issuer credentials, plus `NAMESPACE=default`, `DAPR_CONTROLPLANE_TRUST_DOMAIN=public` and `DAPR_CONTROLPLANE_NAMESPACE=default` to the test process. Keep private keys outside the repository. The checked-in Dapr configuration enables mTLS; Dapr CLI 1.18.2 uses the standard Sentry address and the control-plane environment variables. See the [Dapr self-hosted mTLS prerequisites](https://docs.dapr.io/operations/security/mtls/). The [isolated verification environment](https://github.com/Hexalith/Hexalith.McpCli/blob/main/_bmad-output/implementation-artifacts/evidence/story-4-12/publication-20261023/expanded-publication/private-runtime/README.md) records the private runtime used for this story without reusing host applications or state.

The shared platform fixture owns startup, liveness checks and disposal. Startup retains its six-minute budget and explicit two-minute resource bounds. The independent smoke requires HTTP 401 for missing credentials and a differently signed JWT, then requires matching persisted native catalog readbacks and the privileged persisted administrator Query before one `platform:tenants` list read. That final read keeps its separate 30-second bound. The native gateway retains the mandatory public-source configuration snapshot below ordinary overrides. Each fixture generates a short-lived signing key. Business identities carry signed native surfaces, exact permissions and exact normal tenant grants, with no `system` grant. The vector/smoke identities, including the persisted-administrator nonmember control, also carry the signed `GlobalAdministrator` role from which the Gateway derives its administrator hint. The owning module independently checks persisted administrator membership, so the signed nonmember remains refused. The excluded administrator read uses a separate UI identity with only its exact read permissions. A separate writer-maintenance identity carries the existing operator role only for activation after persisted administrator authority has passed. JWT validation, sidecar authentication and owner-bound bootstrap remain active. No identity server is required.

The independent shared-head boundary creates its own tenant-B party and reads its business state with an authorized identity before and after every refusal. Its tenant-A-only and no-tenant-grant nonmember tokens omit the global-administrator role; these test the Gateway’s exact signed tenant-grant boundary. They do not claim a persisted Parties membership check. The boundary also checks local tenant guards, allowed MCP override authorization, missing-party deactivation, and two concurrent CLI deactivations with distinct message IDs, one persisted deactivation event, and an inactive persisted end-state.

The requested Dapr IDs are `eventstore`, `tenants` and `parties`, with Gateway sidecar HTTP port `3501`. Existing registrations or an occupied port cause an explicit conflict failure; the harness never stops, restarts or reuses a user topology. Run live tests only inside the disposable wrapper. The focused CI discovery job builds and lists every approved Operation-labelled vector case plus the independent smoke and shared-head boundary without starting source services.

The isolated wrapper retains a verified empty Redis RDB backup before applications start. After proving persisted administrator authority, the fixture activates the existing platform writer-v2 protocol once through its authenticated maintenance endpoint and observes readiness. The parent lane verifies the retained backup bytes, SHA-256 and owned location before accepting each child's result. EventStore can then invoke Parties' SDK named projections over authenticated POST `/project/v2`; default deny remains enforced. No direct state-store setup is required.

The required hooks run every vector in a fresh isolated process and then the separate smoke and shared-head boundary; their outer deadlines and private preparation receipt are mandatory.

Each vector gets a new isolated process, Redis and authenticated topology. Exact restored packages, owner approvals, inventory hashes, complete Catalog coverage, all vector bytes and strict companion plans are rechecked before vector Commands. The existing Development bootstrap persists the test administrator through its authenticated server-owned path; a privileged Query must then prove that administrator's persisted membership. Each declared Command is submitted once. A repeated idempotent Command step is proven by its single accepted submission plus unchanged persisted state. Every Query observation also runs through the MCP head; Commands remain single CLI submissions. Explicit Queries observe persisted effects within 45-second deadlines; continuation cursors and audit timestamps come from real query documents. Static v1 assertions remain enforced. Endpoint and identity travel privately in the runner environment. Failed vectors print sanitized phase and assertion diagnostics in the selected test failure. The [lane documentation](https://github.com/Hexalith/Hexalith.McpCli/blob/main/tools/live-topology/README.md) explains preflight-only and selected-vector diagnostics, receipt locations, and partial/skip behavior. Full acceptance requires every approved vector and both independent cases to pass without skips and owned cleanup; acceptance responses alone do not prove semantics.

CI configures the reusable Builds Aspire tier as required: `aspire-test-project: tests/Hexalith.McpCli.Integration.Tests`, `test-platform: microsoft-testing-platform`, and `aspire-continue-on-error: false`. The six focused Release test projects finish before that tier. Preparation selects the exact authenticated public EventStore **4.1.0** / Tenants **7.0.5** runtime declared in `tools/live-topology/native-runtime.json`, retains the independent Testing.Integration **3.128.4** harness, and builds the owned nonpublishable gateway and qualified domain hosts in a fresh task-owned package cache. Exact public archive hashes, embedded repository commits, clean qualified owner sources, deployed binaries and configuration are checked before the vector lane and each independent case. Only disposable hosted CI may select the declared exact source revisions. The explicit `Topology:UsePackagedGateway=true` profile uses the actual SDK catalog model observer and prepare/ready/commit coordinator, the separately prepared Parties adapter, native authorization and Tenants' owner-bound persisted administrator bootstrap. Every real participant must read back the same committed authority before the administrator and writer barriers. Direct native/default and publish models retain their existing selection. The runner requires every approved vector plus independent authenticated smoke and shared-head authorization/deactivation boundary, persisted effects, zero skips and owned cleanup. Offline build/discovery or subset evidence never establishes full live acceptance. See [the runtime prerequisites and evidence contract](https://github.com/Hexalith/Hexalith.McpCli/blob/main/tools/live-topology/README.md).

For a local run, first place the four clean direct root checkouts for `Hexalith.EventStore`, `Hexalith.Tenants`, `Hexalith.Parties` and `Hexalith.Platform` at their exact selected commits in [native-runtime.json](https://github.com/Hexalith/Hexalith.McpCli/blob/main/tools/live-topology/native-runtime.json). Normal root submodule initialization follows gitlinks that can differ from these runtime selections; the local hook refuses to select revisions automatically. Keep nested submodules uninitialized. After the same focused Release checks, ensure Python has `venv` and `ensurepip` support and perform the workflow's full `dapr init --runtime-version 1.18.7`. Then reproduce the two bounded CI hooks from this repository root:

```bash
ASPIRE_EVIDENCE_PATH=TestResults/live-ci bash tools/live-topology/prepare-ci.sh
ASPIRE_EVIDENCE_PATH=TestResults/live-ci bash tools/live-topology/run-ci.sh
```

Preparation has a 38-minute outer limit inside its 40-minute step; the runner has a 295-minute limit inside its 300-minute step, including a vector limit derived from the outer budget (currently 253 minutes), a separate 960-second limit for each independent case, and 600 seconds reserved for provenance checks and cleanup. Both hooks allow a 30-second kill grace; cancellation cleanup waits at most 25 seconds after TERM, then kills the owned process group and waits at most one more second for its supervisor. Interrupted Operations are named in stderr and retained in `ci-live.json`. On cancellation, even after a vector failure, `ci.py` exits 143 and `ci-live.json` records `SystemExit: 143`; the hook's own `timeout` then exits 143 under GNU coreutils and 124 under uutils. Each isolated child retains its 900-second deadline. The complete job is limited to 360 minutes. `TestResults/live-ci/ci-live.json` grants acceptance only for a complete passing invocation. Preparation identities, source-build diagnostics, vector receipts, independent-case XML and sanitized runtime diagnostics are uploaded on success and failure; private credentials and Redis contents stay outside that evidence directory. See the [CI evidence and prerequisites](https://github.com/Hexalith/Hexalith.McpCli/blob/main/tools/live-topology/README.md#required-ci-lane) for the exact locations. Paired publication requires the accepted staging and operator evidence described above.

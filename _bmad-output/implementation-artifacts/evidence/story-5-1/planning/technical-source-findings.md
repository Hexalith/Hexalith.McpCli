# Story 5.1 technical census investigation

Scope: only the 17 root-declared `.gitmodules` repositories at their inspected current HEADs. No nested initialization/update, no skill manifest under `references/` discovered or loaded, no repository edits. All inspected reference working trees were clean on `main...origin/main`. The evidence is source inspection, not publication, authenticated host visibility, selected-environment parity, owner approval, or whole-ecosystem completeness.

## Findings that affect planning

- 13 current production legacy Cli/Mcp projects across 7 owning repositories: EventStore Admin 2; FrontComposer 2; Parties 1; Memories 2; Projects 2; Folders 2; ChatBot 2. There are also 13 associated `.Cli.Tests` / `.Mcp.Tests` projects; those are fixtures, not extra production surfaces.
- Builds has 2 extra Cli projects (`hexalith-module`, `hexalith-evidence`) expressly excluded by the authoritative AI.Tools migration scope: build/workspace tooling that never invokes module operations. Its Module.Cli `pack/projects/{EventStore,Ui}/Host.csproj` files are packaging templates, not independent shipped CLI/MCP surfaces.
- 9 other root refs have no tracked production `.Cli` / `.Mcp` project: AI.Tools, Commons, PolymorphicSerializations, Conversations, Tenants, Agents, Works, Timesheets, Platform. This is a naming/project census limited to inspected roots; do not generalize it to all remote repos or uninspected dynamic hosts.
- `.Client` is not a CLI: exclude Client projects and large captured implementation-artifact source snapshots when counting. `git ls-files` provides tracked ownership; no traversal into nested gitlinks.
- No named CODEOWNERS found in the 16 roots other than Platform. Assign explicit owning repository maintainer roles, with named person and external approval unasserted. Platform `.github/CODEOWNERS:2` assigns `* @jpiquot`, but that does not establish ownership of other repositories.
- Parties.UI references FrontComposer.Mcp (csproj:66–67) but contains no inspected Add/MapFrontComposerMcp registration; record it as a dependency consumer, not an additional observed HTTP host. Projects is the concrete adapter consumer; FrontComposer Counter is a sample host. Platform has no observed production legacy AddMcp/MapMcp registration in its tracked production C# sources.

## Source revisions and production project census

| Root ref | Exact source HEAD | Production legacy surface projects / ownership |
| --- | --- | --- |
| `references/Hexalith.AI.Tools` | `1745b6663ad32bb1288167135ed0f979366c53a0` | none found in tracked production project census; Tools owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Commons` | `11555ace9efcae2928a00122dcba91243e5a8a1a` | none found in tracked production project census; Commons owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.PolymorphicSerializations` | `bce4eb9f45c6b131b960ab4fa39e50ff01e51960` | none found in tracked production project census; PolymorphicSerializations owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Conversations` | `9a5c684de5ee4876448faa26737f6afd36cf33e7` | none found in tracked production project census; Conversations owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.EventStore` | `3d4ba67db99f2f0bcd64b7d353609b555870cc9b` | src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj; src/Hexalith.EventStore.Admin.Mcp/Hexalith.EventStore.Admin.Mcp.csproj; EventStore owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Memories` | `246157a7ff8e2dcd8d356c833a77a02514490d2f` | src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj; src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj; Memories owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Tenants` | `cf36618a2c27b5722a1ff811cfbbce4528c3c105` | none found in tracked production project census; Tenants owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Builds` | `beb85e497957fedc66854013efd2cc4bd216ecbc` | src/libraries/Hexalith.Builds.Evidence.Cli/Hexalith.Builds.Evidence.Cli.csproj; src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj; Builds owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.FrontComposer` | `fbb9c3822dfa407e72739238cd472567f45f1e82` | src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj; src/Hexalith.FrontComposer.Mcp/Hexalith.FrontComposer.Mcp.csproj; FrontComposer owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Parties` | `1308ad000c79ebc394fc395588f9af91092e8c4c` | src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj; Parties owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Agents` | `7957108c30d38b8e82eb072cf3437b6a67627cd7` | none found in tracked production project census; Agents owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Projects` | `31cb92c4362becd83938bd550ca62d07b6af448a` | src/Hexalith.Projects.Cli/Hexalith.Projects.Cli.csproj; src/Hexalith.Projects.Mcp/Hexalith.Projects.Mcp.csproj; Projects owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Folders` | `e88c940000446e13d17d86a7288649d8653a7138` | src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj; src/Hexalith.Folders.Mcp/Hexalith.Folders.Mcp.csproj; Folders owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.ChatBot` | `b13c58006d292836a9c8b242de476765676e5fb2` | src/Hexalith.ChatBot.Cli/Hexalith.ChatBot.Cli.csproj; src/Hexalith.ChatBot.Mcp/Hexalith.ChatBot.Mcp.csproj; ChatBot owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Works` | `2e9fafba151a184eb4552796db7eecc25ffaf8c7` | none found in tracked production project census; Works owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Timesheets` | `f5bee2c91bec6e1e78d81b604cea6af0cee764fe` | none found in tracked production project census; Timesheets owning maintainer role; named owner/approval unasserted |
| `references/Hexalith.Platform` | `019f593544ad157036b7d12173ff89a16464f3cc` | none found in tracked production project census; @jpiquot (`.github/CODEOWNERS:2`) |

## Package and host classification

Production project existence is distinct from NuGet publication or deployment evidence. Exact project metadata:

- `references/Hexalith.EventStore`: `src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj:4` <OutputType>Exe</OutputType>; `src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj:5` <PackAsTool>true</PackAsTool>; `src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj:6` <ToolCommandName>eventstore-admin</ToolCommandName>; `src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj:7` <IsPackable>true</IsPackable>
- `references/Hexalith.EventStore`: `src/Hexalith.EventStore.Admin.Mcp/Hexalith.EventStore.Admin.Mcp.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.EventStore.Admin.Mcp/Hexalith.EventStore.Admin.Mcp.csproj:4` <OutputType>Exe</OutputType>; `src/Hexalith.EventStore.Admin.Mcp/Hexalith.EventStore.Admin.Mcp.csproj:5` <IsPackable>false</IsPackable>
- `references/Hexalith.Memories`: `src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj:10` <OutputType>Exe</OutputType>; `src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj:11` <PackAsTool>true</PackAsTool>; `src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj:12` <ToolCommandName>memories</ToolCommandName>; `src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj:13` <IsPackable>true</IsPackable>; `src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj:14` <PackageId>Hexalith.Memories.Cli</PackageId>
- `references/Hexalith.Memories`: `src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj:1` <Project Sdk="Microsoft.NET.Sdk.Web">; `src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj:4` <IsPackable>true</IsPackable>; `src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj:5` <EnableContainer>true</EnableContainer>; `src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj:6` <ContainerRepository>memories-mcp</ContainerRepository>; `src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj:7` <PackageId>Hexalith.Memories.Mcp</PackageId>
- `references/Hexalith.Builds`: `src/libraries/Hexalith.Builds.Evidence.Cli/Hexalith.Builds.Evidence.Cli.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/libraries/Hexalith.Builds.Evidence.Cli/Hexalith.Builds.Evidence.Cli.csproj:3` <OutputType>Exe</OutputType>; `src/libraries/Hexalith.Builds.Evidence.Cli/Hexalith.Builds.Evidence.Cli.csproj:7` <PackageId>Hexalith.Builds.Evidence.Cli</PackageId>; `src/libraries/Hexalith.Builds.Evidence.Cli/Hexalith.Builds.Evidence.Cli.csproj:8` <IsPackable>true</IsPackable>; `src/libraries/Hexalith.Builds.Evidence.Cli/Hexalith.Builds.Evidence.Cli.csproj:9` <PackAsTool>true</PackAsTool>; `src/libraries/Hexalith.Builds.Evidence.Cli/Hexalith.Builds.Evidence.Cli.csproj:10` <ToolCommandName>hexalith-evidence</ToolCommandName>
- `references/Hexalith.Builds`: `src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj:3` <OutputType>Exe</OutputType>; `src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj:7` <PackageId>Hexalith.Builds.Module.Cli</PackageId>; `src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj:8` <IsPackable>true</IsPackable>; `src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj:9` <PackAsTool>true</PackAsTool>; `src/libraries/Hexalith.Builds.Module.Cli/Hexalith.Builds.Module.Cli.csproj:10` <ToolCommandName>hexalith-module</ToolCommandName>
- `references/Hexalith.FrontComposer`: `src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj:3` <OutputType>Exe</OutputType>; `src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj:5` <IsPackable>true</IsPackable>; `src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj:6` <PackAsTool>true</PackAsTool>; `src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj:7` <ToolCommandName>frontcomposer</ToolCommandName>; `src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj:8` <PackageId>Hexalith.FrontComposer.Cli</PackageId>
- `references/Hexalith.FrontComposer`: `src/Hexalith.FrontComposer.Mcp/Hexalith.FrontComposer.Mcp.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.FrontComposer.Mcp/Hexalith.FrontComposer.Mcp.csproj:4` <IsPackable>true</IsPackable>; `src/Hexalith.FrontComposer.Mcp/Hexalith.FrontComposer.Mcp.csproj:5` <PackageId>Hexalith.FrontComposer.Mcp</PackageId>
- `references/Hexalith.Parties`: `src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj:1` <Project Sdk="Microsoft.NET.Sdk.Web">; `src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj:3` <IsPackable>false</IsPackable>; `src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj:5` <EnableContainer>true</EnableContainer>; `src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj:6` <ContainerRepository>parties-mcp</ContainerRepository>
- `references/Hexalith.Projects`: `src/Hexalith.Projects.Cli/Hexalith.Projects.Cli.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.Projects.Cli/Hexalith.Projects.Cli.csproj:3` <OutputType>Exe</OutputType>; `src/Hexalith.Projects.Cli/Hexalith.Projects.Cli.csproj:4` <IsPackable>false</IsPackable>
- `references/Hexalith.Projects`: `src/Hexalith.Projects.Mcp/Hexalith.Projects.Mcp.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.Projects.Mcp/Hexalith.Projects.Mcp.csproj:3` <IsPackable>false</IsPackable>
- `references/Hexalith.Folders`: `src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj:3` <OutputType>Exe</OutputType>; `src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj:4` <PackAsTool>true</PackAsTool>; `src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj:5` <ToolCommandName>folders</ToolCommandName>; `src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj:6` <IsPackable>true</IsPackable>
- `references/Hexalith.Folders`: `src/Hexalith.Folders.Mcp/Hexalith.Folders.Mcp.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.Folders.Mcp/Hexalith.Folders.Mcp.csproj:3` <OutputType>Exe</OutputType>; `src/Hexalith.Folders.Mcp/Hexalith.Folders.Mcp.csproj:4` <IsPackable>false</IsPackable>
- `references/Hexalith.ChatBot`: `src/Hexalith.ChatBot.Cli/Hexalith.ChatBot.Cli.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.ChatBot.Cli/Hexalith.ChatBot.Cli.csproj:3` <OutputType>Exe</OutputType>; `src/Hexalith.ChatBot.Cli/Hexalith.ChatBot.Cli.csproj:4` <IsPackable>false</IsPackable>
- `references/Hexalith.ChatBot`: `src/Hexalith.ChatBot.Mcp/Hexalith.ChatBot.Mcp.csproj:1` <Project Sdk="Microsoft.NET.Sdk">; `src/Hexalith.ChatBot.Mcp/Hexalith.ChatBot.Mcp.csproj:3` <OutputType>Exe</OutputType>; `src/Hexalith.ChatBot.Mcp/Hexalith.ChatBot.Mcp.csproj:4` <IsPackable>false</IsPackable>

Tracked host/transport registrations (source positions; methods/declarations are identified by their code):

### references/Hexalith.EventStore

- `src/Hexalith.EventStore.Admin.Mcp/Program.cs:57: .AddMcpServer(options => options.ServerInfo = new() {`
- `src/Hexalith.EventStore.Admin.Mcp/Program.cs:62: .WithStdioServerTransport()`

### references/Hexalith.Memories

- `src/Hexalith.Memories.AppHost/Hexalith.Memories.AppHost.csproj:14: <ProjectReference Include="..\Hexalith.Memories.Mcp\Hexalith.Memories.Mcp.csproj" />`
- `src/Hexalith.Memories.Mcp/McpCompositionRoot.cs:91: services.AddMcpServer()`
- `src/Hexalith.Memories.Mcp/McpCompositionRoot.cs:92: .WithHttpTransport(options => options.Stateless = true)`
- `src/Hexalith.Memories.Mcp/Program.cs:23: app.MapMcp("/mcp").RequireAuthorization();`

### references/Hexalith.FrontComposer

- `samples/Counter/Counter.Web/Counter.Web.csproj:11: <ProjectReference Include="..\..\..\src\Hexalith.FrontComposer.Mcp\Hexalith.FrontComposer.Mcp.csproj" />`
- `samples/Counter/Counter.Web/Program.cs:196: _ = builder.Services.AddFrontComposerMcp(o => {`
- `samples/Counter/Counter.Web/Program.cs:232: IEndpointConventionBuilder mcpEndpoint = app.MapFrontComposerMcp();`
- `src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs:13: public static IEndpointConventionBuilder MapFrontComposerMcp(this IEndpointRouteBuilder endpoints, string? pattern = null) {`
- `src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs:17: "FrontComposer MCP services are not registered. Call IServiceCollection.AddFrontComposerMcp(...) before MapFrontComposerMcp(...).");`
- `src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs:34: return endpoints.MapMcp(route).RequireAuthorization();`
- `src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:20: public static IServiceCollection AddFrontComposerMcp(`
- `src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:79: _ = services.AddMcpServer()`
- `src/Hexalith.FrontComposer.Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:80: .WithHttpTransport()`

### references/Hexalith.Parties

- `src/Hexalith.Parties.AppHost/Hexalith.Parties.AppHost.csproj:18: <ProjectReference Include="..\Hexalith.Parties.Mcp\Hexalith.Parties.Mcp.csproj" />`
- `src/Hexalith.Parties.Mcp/Program.cs:61: _ = builder.Services.AddMcpServer()`
- `src/Hexalith.Parties.Mcp/Program.cs:62: .WithHttpTransport(options => options.Stateless = true)`
- `src/Hexalith.Parties.Mcp/Program.cs:67: _ = app.MapMcp();`
- `src/Hexalith.Parties.UI/Hexalith.Parties.UI.csproj:66: <ProjectReference Include="$(HexalithFrontComposerRoot)\src\Hexalith.FrontComposer.Mcp\Hexalith.FrontComposer.Mcp.csproj" Condition="'$(HexalithFrontComposerFromSource)' == 'true'" />`
- `src/Hexalith.Parties.UI/Hexalith.Parties.UI.csproj:67: <PackageReference Include="Hexalith.FrontComposer.Mcp" Condition="'$(HexalithFrontComposerFromSource)' != 'true'" />`

### references/Hexalith.Projects

- `src/Hexalith.Projects.Mcp/Hexalith.Projects.Mcp.csproj:11: <ProjectReference Include="$(HexalithFrontComposerRoot)\src\Hexalith.FrontComposer.Mcp\Hexalith.FrontComposer.Mcp.csproj" Condition="'$(UseHexalithProjectReferences)' == 'true'" />`
- `src/Hexalith.Projects.Mcp/Hexalith.Projects.Mcp.csproj:16: <PackageReference Include="Hexalith.FrontComposer.Mcp" Condition="'$(UseHexalithProjectReferences)' != 'true'" />`
- `src/Hexalith.Projects.Mcp/ProjectsMcpModule.cs:51: return services.AddFrontComposerMcp();`
- `src/Hexalith.Projects.Mcp/ProjectsMcpModule.cs:62: endpoints.MapFrontComposerMcp();`

### references/Hexalith.Folders

- `src/Hexalith.Folders.Mcp/Program.cs:55: .AddMcpServer(options => options.ServerInfo = new()`
- `src/Hexalith.Folders.Mcp/Program.cs:61: .WithStdioServerTransport()`

### references/Hexalith.ChatBot

- `src/Hexalith.ChatBot.Mcp/Program.cs:41: .AddMcpServer()`
- `src/Hexalith.ChatBot.Mcp/Program.cs:42: .WithStdioServerTransport()`

## FrontComposer source comparison and row-ready supplement

Current clean source: `fbb9c3822dfa407e72739238cd472567f45f1e82`. Existing inventory 1.0.0 remains pinned to `81a440a8890a17edb39924bd0cf676eb6f6b5c25`, with only the bounded requesting-session approval described by its A1; external maintainer approval is explicitly unasserted. Do not rewrite that immutable approval scope or pretend it approves current-source additions.

`git diff --stat <old> <current> -- src/Hexalith.FrontComposer.Cli src/Hexalith.FrontComposer.Mcp docs/skills/frontcomposer` shows six changed CLI files, 89 insertions and 30 deletions: CliApplication.cs, MigrationPlanner.cs, PathUtilities.cs, ProjectDocumentLoader.cs, README.md, WriteSafetyPolicy.cs. MCP host/runtime and the embedded documentation corpus have no changes between these pins. Thus the existing counts and fixed names survive source comparison, while current CLI path-safety behavior deserves a source-pinned supplemental row. Do not claim source equality for all CLI behavior.

All current technical capabilities below should remain proposed `defer` / `exclude` pending owner review and approved generic contract/transport decision. This investigation grants neither migration nor destructive execution permission.

| Capability / existing row | Transport / security | Current expected behavior | Gap and exact current anchors |
| --- | --- | --- | --- |
| H01 fixed lifecycle tool `frontcomposer.lifecycle.subscribe` (name configurable) | Authenticated HTTP MCP `/mcp`; handle lookup plus current-tool admission; originating handle ownership unproven | One tool with exactly one canonical `correlationId` OR `messageId`, no extra properties. Returns bounded process-memory snapshot, hidden/unknown for invalid handles or unavailable admission. | No generic status/stream contract; no originating tenant/user binding in stored entry. `Mcp/FrontComposerMcpOptions.cs:52`, `Mcp/McpJsonSchemaBuilder.cs:57`, `Mcp/Invocation/FrontComposerMcpLifecycleTracker.cs:42`, `:54`, `:92`, `Mcp/Invocation/FrontComposerMcpLifecycleStore.cs:110`, `:307`. |
| H02 manifest command family | HTTP MCP tools; tenant/policy-authorized module-defined write/action | Manifests and generated manifest assemblies determine names; admitted command descriptors are listed alongside lifecycle. Names are not a finite global framework business catalog. | Each manifest consumer needs its own pinned business rows, contract identity, and authorization proof; no module-specific adapter in McpCli. `Mcp/FrontComposerMcpOptions.cs:12`, `Mcp/FrontComposerMcpDescriptorRegistry.cs:97`, `:121`, `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:97`. |
| H03 manifest projection resource family | HTTP MCP resource reads; tenant/policy visibility and schema negotiation | Descriptor URI maps to projection query then bounded Markdown rendering; visibility/epoch/schema rechecked before query and rendering. Take is clamped from options, not an invented Gateway envelope mapping. | Decorated queries may replace approved business data only after semantics are proved; Markdown/resource and schema transport remain separate gaps. `Mcp/FrontComposerMcpServerOptionsConfigurator.cs:27`, `Mcp/Invocation/FrontComposerMcpProjectionReader.cs:45`, `:59`, `:69`, `:76`, `:90`. |
| D01–D13 framework documentation resources | HTTP MCP resource reads; framework-global docs bypass tenant projection gate while endpoint authorization remains | Twelve embedded ordinary Markdown resources plus synthetic aggregate manifest, deterministic resource lookup, explicit cancellation/unknown/too-large failures. | No Gateway Query or approved generic document transport. Ordinary resource metadata below; `Mcp/Skills/FrontComposerSkillResourceProvider.cs:33`, `:41`, `:70`, `:102`; `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:66`. |
| C01 `frontcomposer inspect` | Local CLI; source/diagnostic read with optional build subprocess | `--type`, `--project`, `--solution`, `--configuration` (Debug default), `--framework`, `--build`, text/JSON, severity hidden/info/information/warning/error, fail-on-warning/error, absolute-path choice. `--build` is explicitly opt-in. | Local compiler capability has no approved generic contract. `Cli/CliApplication.cs:20`, `:52`, `Cli/InspectCommand.cs:7`, `:19`, `:29`, `:48`, `:59`, `:67`, `:78`. |
| C02 `frontcomposer migrate` dry-run | Local CLI; source read/compiler planning | `--from`, `--to`, project/solution selectors, text/JSON, fail-on-findings; default dry-run, only supported edge 9.1.0→9.2.0. | No domain Command invented. `Cli/MigrationCommand.cs:13`, `:19`, `:39`, `:44`, `:56`, `Cli/MigrationCatalog.cs:4`. |
| C02/V07 `frontcomposer migrate --apply` | Local file mutation, explicit apply flag; potentially destructive to source; no interactive confirmation prompt in inspected command | Apply and dry-run together fail. Targets and source hashes rechecked; sequential writes retain prior writes on later error/cancellation, `applied:false` on partial failure. | Record file mutation separately from passive planning; user approval of inventory never authorizes execution. `Cli/MigrationCommand.cs:13`, `:40`, `Cli/MigrationApplier.cs:9`, `:12`, `:28`, `:33`, `:36`, `:48`. |
| Current-source path-safety supplement (new compared with inventory pin) | Local path boundary and mutation refusal | Migration skips linked file/ancestor/junction paths and nested repositories before reading source; canonicalization resolves ancestor links; unsafe targets rejected again at apply; lexically distinct paths de-duplicated preferring a nonlinked document. | Preserve new continuity/safety fix; keep old A1 pin unchanged and request owner review of source-bound supplement. `Cli/WriteSafetyPolicy.cs:4`, `Cli/PathUtilities.cs:32`, `:61`, `:86`, `Cli/MigrationPlanner.cs:55`, `Cli/ProjectDocumentLoader.cs:39`. |
| V02/V03 identity and HTTP authorization | Authenticated HTTP MCP; key vs claims caller identity | `/mcp` requires authorization and tenant/resource gates; valid API key takes precedence over authenticated claims, invalid/multiple supplied keys cannot fall back. Sample allow-all gates confined to Development. | Per-user identity/authz is not replaceable by operator actor/tenant input. `Mcp/Extensions/FrontComposerMcpEndpointRouteBuilderExtensions.cs:34`, `Mcp/Extensions/FrontComposerMcpServiceCollectionExtensions.cs:59`, `:71`, `Mcp/HttpFrontComposerMcpAgentContextAccessor.cs:79`, `:96`, `:110`. |
| V08 parser/output compatibility | Local CLI | No arg/help prints help; unknown verb rejected; duplicate options rejected, arbitrary syntactically valid long names not centrally allowlisted, positionals stored. Root leaf `--help` does not dispatch root help. Exit 0 success, 1 findings, 2 invalid, 3 generated output missing, 4 apply failure; source support is .csproj and single-.csproj .sln; .slnx/.fsproj refused. | Preserve actual parser quirks only by explicit owner decision; avoid claiming idealized System.CommandLine behavior. `Cli/CliApplication.cs:13`, `:19`, `:41`, `:55`, `:56`, `Cli/CommandOptions.cs:26`, `:73`, `:86`, `:106`. |

The lifecycle acknowledgement `frontcomposer://lifecycle/{correlationId}` is metadata, not a registered MCP resource. Resource configurator only adds manifest projections plus skill docs. There is no additional fixed polling/streaming resource or MCP prompt registration in the inspected host. `MaxLifecycleLongPollMs` option exists (`Mcp/FrontComposerMcpOptions.cs:62`), but ReadAsync immediately reads a snapshot: do not invent a long-poll operation. No fixed framework erasure or key-rotation tool is registered; API-key dictionary is configuration. Dynamic manifests require their own operation inventories.

### Ordinary embedded resource metadata

Only first 15 metadata lines read; no SKILL.md was opened. Every doc has `id` at line 2 and `resourceUri` at line 8. Count: 12 docs + one synthetic manifest = 13 framework resource rows.

| ID | Current URI | Metadata anchor |
| --- | --- | --- |
| `domain-commands` | `frontcomposer://skills/domain/commands` | `docs/skills/frontcomposer/domain/commands.md:8` |
| `domain-projections` | `frontcomposer://skills/domain/projections` | `docs/skills/frontcomposer/domain/projections.md:8` |
| `domain-validation` | `frontcomposer://skills/domain/validation` | `docs/skills/frontcomposer/domain/validation.md:8` |
| `index` | `frontcomposer://skills/index` | `docs/skills/frontcomposer/index.md:8` |
| `mcp-projection-markdown` | `frontcomposer://skills/mcp/projection-markdown` | `docs/skills/frontcomposer/mcp/projection-markdown.md:8` |
| `mcp-tools-resources-lifecycle` | `frontcomposer://skills/mcp/tools-resources-lifecycle` | `docs/skills/frontcomposer/mcp/tools-resources-lifecycle.md:8` |
| `migration-versioned-corpus-rules` | `frontcomposer://skills/migration/versioned-corpus-rules` | `docs/skills/frontcomposer/migration/versioned-corpus-rules.md:8` |
| `samples-new-bounded-context` | `frontcomposer://skills/samples/new-bounded-context` | `docs/skills/frontcomposer/samples/new-bounded-context.md:8` |
| `security-tenant-and-policy-boundaries` | `frontcomposer://skills/security/tenant-and-policy-boundaries` | `docs/skills/frontcomposer/security/tenant-and-policy-boundaries.md:8` |
| `setup-package-and-hosting` | `frontcomposer://skills/setup/package-and-hosting` | `docs/skills/frontcomposer/setup/package-and-hosting.md:8` |
| `team-overlays` | `frontcomposer://skills/team-overlays` | `docs/skills/frontcomposer/team-overlays.md:8` |
| `testing-generated-code-validator` | `frontcomposer://skills/testing/generated-code-validator` | `docs/skills/frontcomposer/testing/generated-code-validator.md:8` |
| `skills-manifest` | `frontcomposer://skills/manifest` | `Mcp/Skills/FrontComposerSkillResourceProvider.cs:102`, `Mcp/Skills/SkillCorpusAggregateManifestBuilder.cs:8` |

`Mcp/` means `src/Hexalith.FrontComposer.Mcp/`, `Cli/` means `src/Hexalith.FrontComposer.Cli/`. The Projects concrete 5 tools and 11 resource names remain owned by the companion `projects-migration-inventory-v1.md`; do not duplicate them as framework-owned business rows. Six tools and 24 resources with only Projects registered describes a potential descriptor set, not an authenticated live catalog or all ecosystem hosts.

## Suggested story treatment

Preserve existing immutable FrontComposer v1 A1 exactly. New story should link those rows and add current-source continuity/path-safety observations plus a complete root-ref census. Explicitly track external EventStore and FrontComposer approval as missing unless the requesting user supplies delegated authority or a verifiable approval reference. Neither generic replacement design, runtime implementation, publication nor retirement belongs to this inventory-only story.

# Hexalith LLM Instructions

> **Authoring rule for this file:** Keep it self-contained. Reference **only**
> the topical instruction files that live in this same folder
> (`references/Hexalith.AI.Tools/`, e.g. `hexalith-state-instructions.md` and
> `hexalith-ux-instructions.md`). The sole outside-folder policy-file exception
> is the canonical Hexalith.CiCd ownership template linked in the CI/CD section.
> Never link to the agent-instruction entry points that already point here
> (`CLAUDE.md`, `AGENTS.md`, GitHub Copilot instruction files) — those create a
> circular reference. Inline other outside-folder rules here instead of linking
> out.

When opening files or folders via the command line, always pass the `-r` flag to
open them in the current window without replacing the workspace, or pass `-n` to
force a brand-new window. Never run a command that reloads or replaces the active
workspace window.

Before persisting any data in a Hexalith domain module, read
[hexalith-state-instructions.md](hexalith-state-instructions.md) and follow the
data-persistence rules it defines (domain modules use **Hexalith.EventStore**).

Before working on any Hexalith module user interface, read
[hexalith-ux-instructions.md](hexalith-ux-instructions.md) and follow the UX
rules it defines.

When adding or changing C# code, keep each `.cs` file focused on a single C#
object/type. Move additional classes, records, structs, interfaces, enums, and
delegates into their own files named for the object/type.

Before any Git work — staging, committing, pushing, branching, or updating
submodules — read [hexalith-git-instructions.md](hexalith-git-instructions.md)
and follow it (essentials in [Git](#git) below).

## Technology Stack

- **.NET 10+** — latest .NET framework (SDK version pinned per repo in `global.json`)
- **C# 14+** — latest language features
- **DAPR 1.18+** — Distributed Application Runtime for microservices
- **.NET Aspire 17.x** — local orchestration of the distributed topology
- **Microsoft Fluent UI Blazor V5** — UI component library V5 for Blazor apps
- **xUnit v3 + Shouldly + NSubstitute** — testing, assertions, mocking

## Hexalith Ecosystem

The ecosystem is split into **technical modules** (reusable platform
capabilities) and **domain modules** (business domains built on the platform).

| Repository | Role |
| ---------- | ---- |
| [Hexalith](https://github.com/Hexalith/Hexalith) | Core framework and shared components |
| [Hexalith.Builds](https://github.com/Hexalith/Hexalith.Builds) | Centralized build configuration & CI/CD templates |
| [Hexalith.Commons](https://github.com/Hexalith/Hexalith.Commons) | Cross-cutting primitives and helpers |
| [Hexalith.PolymorphicSerializations](https://github.com/Hexalith/Hexalith.PolymorphicSerializations) | Polymorphic JSON serialization |
| [Hexalith.EventStore](https://github.com/Hexalith/Hexalith.EventStore) | DAPR-native event sourcing / domain-service SDK |
| [Hexalith.Tenants](https://github.com/Hexalith/Hexalith.Tenants) | Multi-tenancy domain module |
| [Hexalith.Parties](https://github.com/Hexalith/Hexalith.Parties) | Parties domain module |
| [Hexalith.FrontComposer](https://github.com/Hexalith/Hexalith.FrontComposer) | UI composition / front-end shell |
| [Hexalith.AI.Tools](https://github.com/Hexalith/Hexalith.AI.Tools) | AI-agent instructions, skills, workflows, commands, jobs |

**Boundary rule:** a domain module contains only domain code. If a capability is
boilerplate shared across modules (hosting, event-store plumbing, serialization,
DI setup, UI scaffolding, test harness helpers), **do not duplicate it** — reuse
the technical module that provides it, or add it to that technical module first,
then consume it.

## Hexalith MCP and CLI ownership

`Hexalith.McpCli` is the target Hexalith-owned MCP server and CLI for domain,
platform, and operator capabilities. Do not create a new proprietary
per-module MCP server, MCP plug-in, or CLI. Gateway-ready operations are
declared in decorated module Contracts and enrolled in McpCli. Adopted McpCli AD-23 assigns confidential UI, explicit withdrawal, named local
exemptions or deferral to other capability classes. Confidential UI, withdrawal
and those exemptions need no invented McpCli transport. Eligible business
behavior still needs exact decorated Gateway Contracts and independent gates.

Existing proprietary Hexalith module MCP/CLI packages are obsolete migration
sources. Limit them to safety and continuity fixes, inventory every operation
with its owning maintainer, and retire each only after an approved McpCli
replacement or explicit withdrawal passes authorization and behavior gates.
External developer tools such as Aspire, Dapr, and `dotnet` CLIs are outside
this rule, as is Hexalith.Builds build and workspace tooling that never invokes
module operations, currently `hexalith-module` and `hexalith-evidence`.
Also exempt are `Hexalith.FrontComposer.Cli` (`inspect` and `migrate`) as
local compiler/developer tooling, and Memories `tools/MigrateEmbeddingVectors`
(`--dry-run`, `--live`, `--rollback`, `--abort`) as owner-held local operator
tooling only. These named exemptions never admit an agent-facing server,
plug-in, Gateway operation or remotely callable tool, never count as a retired
surface, and do not authorize new proprietary per-module CLIs.

Follow the versioned
[Hexalith MCP and CLI migration plan](hexalith-mcpcli-migration-instructions.md)
for frozen implementations, immutable inventories, approval limits and
retirement prerequisites. Retained compatibility implementations are never
templates for new modules.

## Solution Files

**Use the `.slnx` solution only** (modern XML solution format). Never create or
use legacy `.sln` files.

## Domain-Driven Design Architecture

Hexalith modules follow a **vertical-slice architecture** with a separate NuGet
package per layer. A module `Hexalith.{Module}` is organized as:

```text
{ModuleName}/
├── references/Hexalith.Builds/                    # Build configuration (submodule)
├── src/
│   ├── examples/
│   │   └── Hexalith.{Module}.Example/                       # Example implementation
│   ├── libraries/                                           # NuGet package libraries
│   │   ├── Domain/
│   │   │   ├── Hexalith.{Module}/                           # Aggregate roots, entities, state
│   │   │   ├── Hexalith.{Module}.Abstractions/              # Domain interfaces, value objects
│   │   │   └── Hexalith.{Module}.Events/                    # Domain events
│   │   ├── Application/
│   │   │   ├── Hexalith.{Module}.Commands/                  # CQRS command definitions & validators
│   │   │   ├── Hexalith.{Module}.Requests/                  # Queries & view models
│   │   │   ├── Hexalith.{Module}.Application/               # Command & query handlers
│   │   │   ├── Hexalith.{Module}.Application.Abstractions/  # Application interfaces
│   │   │   └── Hexalith.{Module}.Projections/               # Read-model projections
│   │   ├── Infrastructure/
│   │   │   ├── Hexalith.{Module}.Servers/                   # Shared server utilities
│   │   │   ├── Hexalith.{Module}.ApiServer/                 # REST API controllers
│   │   │   ├── Hexalith.{Module}.WebServer/                 # Web server implementation
│   │   │   └── Hexalith.{Module}.WebApp/                    # Blazor web application
│   │   └── Presentation/
│   │       ├── Hexalith.{Module}.UI.Components/             # Reusable Blazor components
│   │       ├── Hexalith.{Module}.UI.Pages/                  # Blazor page components
│   │       └── Hexalith.{Module}.Localizations/             # Language resources
│   └── servers/                        # Docker/deployment projects
└── test/
    └── Hexalith.{Module}.Tests/        # Unit & integration tests
```

### Dependency Flow (outer depends on inner)

```text
Presentation → Infrastructure → Application → Domain → Abstractions
```

### Architecture Patterns

- **CQRS** — commands in, events out
- **Event Sourcing** — state is reconstructed by replaying events; no direct mutation
- **DDD aggregates** — pure functions: `Handle(Command, State?) -> DomainResult` with `Apply(Event)` on state
- **DAPR** — state store, pub/sub, and config abstracted via sidecars
- **Multi-tenancy** — built in at the contract level (Domain + AggregateId + TenantId)
- **Aspire orchestration** — full local topology via `aspire run` on the AppHost

### Domain-Module Authoring (domain-centric)

Domain modules built on `Hexalith.EventStore` **must be domain-centric** —
aggregates, commands, events, projections, query handlers, validators, and
contracts only. The platform supplies all run-time boilerplate through the
**domain-service SDK**; the persistence rules and SDK seams (two-line host,
`IDomainQueryHandler`, `IDomainProjectionHandler`, `IReadModelStore` +
`ReadModelWritePolicy`, `IQueryCursorCodec` / `QueryCursorScope`) are defined
in [hexalith-state-instructions.md](hexalith-state-instructions.md).

A domain module **must not** ship its own `*.AppHost`, `*.Aspire`, or
`*.ServiceDefaults` project, and **must not** re-implement projection/query
actors, DAPR wiring, telemetry sources, health checks, or event-subscription
plumbing. If a capability is missing, add it to the platform, not the domain.

## C# Coding Standards

Conventions are enforced by `.editorconfig` and `TreatWarningsAsErrors=true`.

- **Namespaces:** file-scoped (`namespace X.Y.Z;`)
- **Braces:** Allman style (new line before the opening brace)
- **Private fields:** `_camelCase`
- **Nullable** and **implicit usings:** enabled globally
- **Indentation:** 4 spaces, CRLF line endings, UTF-8
- **Primary constructors:** prefer them for classes and records
- **XML documentation:** required on all public, protected, and internal members.
  For records with primary constructors, document properties with `<param>` tags.

```csharp
/// <summary>
/// Represents a customer in the system.
/// </summary>
/// <param name="Id">The unique customer identifier.</param>
/// <param name="Email">The customer's email address.</param>
/// <param name="Name">The customer's full name.</param>
/// <param name="CreatedAt">When the customer was created.</param>
public sealed record Customer(
    string Id,
    string Email,
    string Name,
    DateTimeOffset CreatedAt);
```

### Naming Conventions

| Element | Convention | Example |
| ------- | ---------- | ------- |
| Interfaces | Prefix with `I` | `IOrderRepository` |
| Async methods | Suffix with `Async` | `GetOrderAsync` |
| Event handlers | Suffix with `Handler` | `OrderPlacedHandler` |
| Commands | Imperative verb | `PlaceOrder`, `CancelOrder` |
| Events | Past tense | `OrderPlaced`, `OrderCancelled` |
| Value objects | Noun | `Money`, `Address`, `Email` |
| Aggregates | Domain noun | `Order`, `Customer`, `Product` |

### Error Handling

- `ArgumentException.ThrowIfNullOrWhiteSpace()` for string validation
- `ArgumentNullException.ThrowIfNull()` for null checks
- Domain-specific exceptions for business-rule violations; Result pattern for expected failures
- **Identifiers are ULIDs.** Use `Ulid.TryParse` (or accept any non-whitespace
  string per `AggregateIdentity` rules) for `messageId`, `correlationId`,
  `aggregateId`, `causationId`. `Guid.TryParse` on these fields is **forbidden** —
  ULID and GUID share a 36-char shape only by coincidence.

### Logging

Use source-generated `LoggerMessageAttribute` for high-performance logging:
`static partial` methods, `ILogger` as the first parameter (and `Exception`
second when present), structured named placeholders (`{OrderId}`), declaring
class `partial`.

## User Interface & UX

Module UIs follow the rules in
[`hexalith-ux-instructions.md`](./hexalith-ux-instructions.md). Read it before
working on any module user interface. In short:

- Module UI **must** use the **FrontComposer** technical module and **Blazor
  Fluent UI V5** components.
- **Reuse over hand-rolling** — avoid raw CSS, HTML, JavaScript, or third-party
  components when an equivalent FrontComposer / Fluent UI V5 component exists.
  Only fall back to custom markup when no such component exists.
- **No theme redefinition** — express typography/color/spacing via Fluent UI V5
  component parameters or Fluent 2 design tokens; never recreate
  component-provided styling in CSS, and never use legacy v4/FAST tokens
  (`--type-ramp-*`, `--neutral-*`, `--accent-*`, `--neutral-fill-*`, `--palette-*`).

## Build, Run & Diagnostics

Centralized build configuration comes from `Hexalith.Builds`:
`Hexalith.Build.props`, `Hexalith.Package.props`, and `Directory.Packages.props`
(centralized package versions — no inline `<PackageReference Version>`).

```bash
# Restore & build (Release)
dotnet restore Hexalith.{Module}.slnx
dotnet build Hexalith.{Module}.slnx --configuration Release

# Run the local topology (AppHost lives in the platform/host repo)
aspire run
```

**Aspire workflow:** before changing code, run the AppHost with `aspire run` and
inspect resource state so you start from a known-good baseline. AppHost changes
require restarting the Aspire app. The standalone Aspire MCP server is obsolete —
use the **Aspire agents** integration instead: run `aspire agent init` once to
install the Aspire skills/tools, then drive the running app through the **Aspire
CLI** (`aspire describe` for resource state and endpoints, `aspire otel logs` for
logs and traces, `aspire docs search` for docs). Use the Playwright MCP server for
functional investigations (get navigable endpoints from `aspire describe`). When
adding a resource, use `aspire add`, pick a version aligned with
`Aspire.AppHost.Sdk`, and read the integration docs before editing the AppHost.
Prefer official docs: `https://aspire.dev`,
`https://learn.microsoft.com/dotnet/aspire`.

### Library References & Build Configuration

How you reference other Hexalith libraries and which build configuration you
produce depends on the environment:

- **Development environments (local development and testing):** reference
  Hexalith libraries by **project reference** and build **Debug** assets only.
  Project references let you edit, step through, and debug the actual library
  sources (across submodules) in the same solution, and Debug assets keep full
  symbols and diagnostics available.
- **CI/CD:** reference Hexalith libraries by **NuGet package reference only** and
  produce **Release** assets only. Never rely on project references or Debug
  output in a CI/CD pipeline — CI/CD validates and ships the same packaged,
  optimized artifacts that consumers restore.

## Testing Standards

- **Framework:** xUnit v3 · **Assertions:** Shouldly · **Mocking:** NSubstitute · **Coverage:** coverlet
- Test method names use **PascalCase**.
- **Run test projects individually**; use the `.slnx` for restore/build only, not
  solution-level `dotnet test`.
- When `dotnet test` or a solution build is environment-blocked, climb the
  fallback validation ladder before recording validation as blocked:
  1. Run the most focused lane or test project build/run available.
  2. For xUnit v3 filters, build the target test project and invoke the built test
     assembly directly with single-dash `-class` or `-method` arguments; do not rely
     on project-level `dotnet test --filter` under Microsoft.Testing.Platform.
  3. Use serialized `-m:1` Release builds for first-failure triage, adding only
     environment pins such as `-p:MinVerVersionOverride=1.0.0` when needed.
     Never disable or suppress dependency audits or skip tests to pass a gate.
  4. Record the exact broad-gate blocker separately from the focused evidence that
     did run, and never weaken the build gate to hide the blocker.
- Organize tests by aggregate: `{Command}Tests.cs`, `{Event}Tests.cs`,
  `{Query}Tests.cs`, `{Aggregate}Tests.cs`.
- Integration tests must assert **state-store end-state** (persisted contents),
  not only API return codes or mock call counts.
- All existing and new tests must pass before a story is complete.

```text
test/
└── Hexalith.{Module}.Tests/
    └── {Aggregate}/
        ├── {Command}Tests.cs
        ├── {Event}Tests.cs
        ├── {Query}Tests.cs
        └── {Aggregate}Tests.cs
```

## Container Images

Images are produced via **.NET SDK container support** (no Dockerfiles). Opt-in
is centralized in `Directory.Build.targets` and enabled per project with
`<EnableContainer>true</EnableContainer>` + `<ContainerRepository>image-name</ContainerRepository>`.
Defaults: base `mcr.microsoft.com/dotnet/aspnet:10.0-alpine`, registry
`registry.hexalith.com`, non-root `app` user, port 8080.

```bash
dotnet publish src/Hexalith.{Module}/Hexalith.{Module}.csproj \
  --configuration Release -t:PublishContainer \
  -p:ContainerArchiveOutputPath=/tmp/{module}.tar.gz
```

## Git

Read [hexalith-git-instructions.md](hexalith-git-instructions.md) before any Git
work and follow it — it defines the repository-boundary, branch, submodule,
staging, commit, and push rules.

## CI/CD

The canonical [Hexalith.CiCd ownership contract](https://github.com/Hexalith/Hexalith.CiCd/blob/main/templates/partials/ownership-block.txt.j2)
defines delivered module policy. Hexalith.CiCd owns workflows, CI configuration,
Dependabot, the Builds gitlink and its `.gitmodules` section, delivered CI/CD
instruction blocks, and required Claude deny entries. Propose changes in CiCd;
preserve foreign instructions and settings when applying the policy.

- **CI** — GitHub Actions on pushes and PRs to `main` runs product checks:
  compilation, tests, security and dependency scans, commit format and package
  publishing. Module-specific product checks use custom actions enabled by
  CiCd. Checks of CI itself, agent tooling, story evidence and workflow YAML
  text do not belong in module CI. Do not write tests that assert workflow YAML.
- **Release** — CiCd's central nightly process dispatches Builds and adopted
  modules, collects their results and publishes validated ready drafts.
  Conventional Commits determine versions. Builds supplies the shared release
  implementation.
- **Release scope** — freeze dependency revisions when a release starts; later
  upstream advances go to the next release unless they fix a release blocker.
- Test the affected behavior and run each repository's required CI once on the
  exact release source. Re-run only after a source change. Outside release CI,
  one re-run of a failure that does not reproduce is allowed; record the flaky
  test as a bug instead of adding gates.
- Run full mutation testing on its schedule or after substantial changes to the
  code it targets; it is not a per-release gate unless a release workflow
  requires it.
- Keep pipeline modernization (CiCd adoption, new CI steps) out of product
  releases.
- Produce one concise release report per release; do not commit bulk diagnostic
  evidence. Keep story specs short: record decisions and current state, and
  leave run-by-run history to commits and CI run links.
- Fix product failures; report pipeline defects with the failure and run link.
  In a module that has adopted Hexalith.CiCd (it commits
  `.github/hexalith-ci.json`), require a successful
  `python3 references/Hexalith.Builds/check.py` before every push, run from the
  module root in a standalone clone (where Builds is a direct submodule). Until
  a module adopts CiCd, its existing required CI gates apply. Never initialize
  nested submodules in an umbrella workspace to run the checker. Never weaken
  audits or tests or add CI skip markers (including `[skip ci]` variants) or
  `skip-checks` commit trailers.
- Start product branches from `origin/main` immediately after fetching current
  `origin main`. GitHub permits PR Update branch with the restricted module
  credential even when it imports changed workflows. Do not use it to import
  owned CI/CD changes. Fetch current `main`, create a new product branch, and
  reapply only product changes instead. Report refusals without switching
  credentials or broadening access.
- Launch Claude Code from the module root so the project-local `Edit` denies
  protect whole-owned files and the Builds subtree. Reads remain available.
  Keep denies out of machine-wide settings. File rules cannot target JSON keys,
  instruction marker ranges or individual `.gitmodules` sections; instructions
  and the shared guard protect those owned portions.

## Additional Resources

- [DAPR Documentation](https://docs.dapr.io/)
- [.NET Aspire](https://learn.microsoft.com/dotnet/aspire)

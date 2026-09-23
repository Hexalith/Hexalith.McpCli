# Epic 1 Context: Module Authors Can Publish Discoverable Operations

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

A Module author can publish a decorated Contracts library whose Commands and Queries appear in one deterministic, trustworthy Catalog with accurate routing, JSON Schemas, descriptions, and actionable diagnostics. This epic establishes the repository and package foundation, including a synthetic Module, so discovery and authoring checks work before the upstream Tenants and Parties releases exist.

## Stories

- Story 1.1: Declare a Module and Its Operations
- Story 1.2: Enroll a Contracts Package by Reference
- Story 1.3: Derive the Operation's JSON Schema
- Story 1.4: Discover Valid Operations in One Catalog
- Story 1.5: Diagnose Catalog Declarations
- Story 1.6: Inspect Description Quality
- Story 1.7: Warn on Missing Operation Descriptions at Build Time
- Story 1.8: Define and Validate the Conformance Vector Contract

## Requirements & Constraints

- A Contracts assembly declares one Module name, description, `Ulid` or `String` identifier kind, and optional fixed Tenant, Wire Type convention, and serializer options provider. Only marked assemblies are scanned. Decorated classes or records are Commands (`write`) or Queries (`read`); descriptions are required, examples are optional and must validate, and property descriptions come from `[Description]`.
- Resolve each Gateway routing value from its contract interface first, decoration second, and Module convention only where applicable. Query aggregate identity can come from a declared property, a constant, or a required call argument; Commands must have a declared source. The canonical Operation Name is `<module>.<kebab-case name>` after removing only a trailing `Command` or `Query`, unless overridden, and remains distinct from Gateway Wire Type.
- Derive a closed Schema for every serializable Payload, reflecting required and nullable members, enums, nested objects, collections, Module converters and casing, and described properties. Envelope-filled members are read-only and optional in the caller's Schema. Only marked or aggregate-source identifiers receive the Module identifier kind; a CLR ULID receives its own ULID pattern. Unmarked identifier-like names remain ordinary fields.
- Invalid declarations are excluded while valid ones remain discoverable. Diagnostics identify the declaration, category, severity, and cause once on stderr, with deterministic duplicate precedence. A marked empty Module stays visible with a warning; unmarked assemblies are silent. An empty Catalog fails Catalog-dependent actions; strict mode fails on any diagnostic. Description lint is separate from Catalog diagnostics and does not exclude an Operation.
- Discovery output must be byte-identical for the same build across runs and operating systems. The production Catalog target is under 500 ms on `ubuntu-latest` for the v1 Modules plus the one declared synthetic sample Module. The Decoration Package has no consumer-visible package dependencies; no production project references the sample fixture or another Module's implementation layers.

## Technical Decisions

- Use a flat .NET 10 `.slnx` layout with centralized Hexalith.Builds configuration, warnings as errors, test projects, and the delivery configuration needed for an Abstractions-only bootstrap and later paired release. The synthetic Contracts fixture declares one `Ulid` Module spanning interface and attribute routing, a converter-backed identifier, and a Query; isolated Catalog construction covers `String`.
- `Hexalith.McpCli.Abstractions` owns the decoration attributes, identifier kind, and shared kebab-case helper. The optional analyzer is bundled inside that package under `analyzers/dotnet/cs` with private Roslyn dependencies. Core owns reflection, serialization, Schema derivation, and the immutable Catalog; the CLI and MCP adapters consume its descriptors and do not reflect over Contracts types.
- Generate the tool's assembly manifest from package references marked `HexalithContracts="true"` after reference resolution. Match packages by `NuGetPackageId`, require exactly one Contracts assembly per flag, sort assembly names ordinally, and load only those names. Enrollment is a package reference and rebuild, with no folder scan or handwritten assembly list.
- Cache one read-only Payload serializer-options instance per Module. Preserve provider converters in order while fixing canonical non-converter settings and the metadata resolver. Export Schema once per Operation; normalize only a Command's root to a non-null object. Resolve property-reference names as exact top-level CLR names through effective serialization metadata, cache serialized names and JSON Pointers, and reject missing, ignored, ambiguous, opaque, or conflicting property roles. Compile aggregate accessors during Catalog construction.
- Keep the vector contract and validator as versioned test artifacts outside production code. The closed format fixes package identity and exact version, Operation names, inputs, expected Gateway requests, scripted responses, and semantic assertions; its validator rejects stale or unknown data without a Gateway connection.

## UX & Interaction Patterns

Author-facing descriptions must make sense without source-code context. Operation inspection returns Schema and specific, stable lint findings for missing nested descriptions, unmarked identifier-like properties, Payload paging members, and hollow descriptions; property findings use escaped JSON Pointers in serialized casing. CLI lint inspection returns a result with exit code 1 when findings exist.

## Cross-Story Dependencies

- The structural seed and synthetic fixture enable manifest, Schema, Catalog, analyzer, and vector-contract verification without waiting for decorated upstream Modules. The manifest supplies the Catalog's assembly input; Schema and serialization metadata supply its operation descriptors and diagnostics; those descriptors supply author-facing lint.
- The approved vector contract and validator precede upstream Tenants and Parties vector authoring. Later work rechecks vectors against restored production package versions, executes CLI/MCP parity, and runs live semantic tests. The Decoration Package can bootstrap before the paired tool release; the paired release depends on decorated upstream Contracts packages and their exact pins.

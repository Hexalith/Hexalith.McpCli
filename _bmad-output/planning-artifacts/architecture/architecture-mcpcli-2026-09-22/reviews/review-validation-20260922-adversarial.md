---
title: "Standalone validation — adversarial seam review"
reviewed: ARCHITECTURE-SPINE.md
lens: adversarial
date: '2026-09-22'
status: fail
---

# Adversarial validation

## Verdict

**Fail — hold implementation/release planning.** Two requirements cannot be
satisfied together as written, four more seams permit independently built units
to disagree at runtime, and the only mutable store has no cross-process mutation
contract. This review does not repeat the previously closed Tenant precedence,
aggregate accessor, rebuilt-Payload validation, serializer-provider ABI, or
flagged/unmarked manifest findings.

| Severity | Count |
| --- | ---: |
| Critical | 2 |
| High | 4 |
| Medium | 1 |

## Findings

### ADV-001 — Critical — Exact live cross-head equality is impossible for Commands

**Pair:** executor/identifier-generation story and out-of-process integration
harness story.

**Spine evidence:** AD-5 requires `JsonElement.DeepEquals` for the two heads
(`ARCHITECTURE-SPINE.md:83`); AD-9 generates a message identifier and, as
currently written, an idempotency key per call and submits exactly once
(`ARCHITECTURE-SPINE.md:107`); the identifier convention again says one of each
per call (`ARCHITECTURE-SPINE.md:189`); AD-16 drives the CLI and MCP head as
separate out-of-process calls against the live topology and requires equality
for every Operation (`ARCHITECTURE-SPINE.md:149`).

**Two-unit counterexample:** the CLI invocation of `send` correctly generates
`M1/K1/C1`, mutates aggregate `A`, and returns a document containing those
values. The MCP invocation of `send_command` correctly generates `M2/K2/C2` and
either mutates `A` a second time, is rejected by the changed domain state, or
returns a different accepted document. Both use the same Core and obey every AD;
their documents cannot be deeply equal. Running the Command only once avoids
the duplicate side effect but no longer tests both heads. Query equality can
also become order-dependent after the first Command changes the topology.

**Disposition:** **discuss** before implementation. Split the gate into (a) an
out-of-process protocol-parity lane backed by a deterministic fake/capture-replay
Gateway, where exact `DeepEquals` is meaningful, and (b) a live acceptance lane
that executes each mutating Operation once and asserts semantic invariants.
Alternatively define an explicit normalization contract for volatile fields and
independent aggregate fixtures; do not claim raw `DeepEquals` over two live
Command executions.

### ADV-002 — Critical — The generic harness has no compliant source of accepted inputs

**Pair:** independently decorated Module Contracts and the generic integration
harness.

**Spine evidence:** the frozen descriptor/result model permits an Operation
`Example` but does not require one (`ARCHITECTURE-SPINE.md:71,83`); the production
dependency rule forbids Module aggregate, handler, client, or server packages
and permits no Module-specific implementation in `src/`
(`ARCHITECTURE-SPINE.md:141-143`); AD-16 nevertheless requires accepted Commands
and returned Query documents for every Operation exposed by Tenants and Parties
(`ARCHITECTURE-SPINE.md:147-149`).

**Two-unit counterexample:** a Module maintainer publishes a valid decorated
Command with required business fields, no example, and a precondition such as an
existing tenant. That is fully compliant. The generic harness discovers the
Operation but has only its schema. One harness author sends schema-shaped
placeholders and gets a domain rejection; another hard-codes Module-specific
setup/data and violates the zero-module-specific-code/dependency boundary. Both
stories are locally reasonable, but no implementation satisfies the combined
gate for all Operations. Even a syntactically valid optional example does not
state sequencing or external preconditions.

**Disposition:** **discuss**. Make a versioned conformance vector (valid Payload,
Envelope inputs, setup/preconditions, and expected semantic assertions)
mandatory for every production-decorated Operation, and decide whether it lives
as contract metadata or as test-only assets owned by the Module and explicitly
allowed by AD-15. If examples remain optional, narrow AD-16; the current generic
"every Operation is accepted" gate is not implementable.

### ADV-003 — High — The MCP output schema has no valid success/error union

**Pair:** MCP tool-definition/schema story and MCP result-adapter story.

**Spine evidence:** failures are error-only objects
(`ARCHITECTURE-SPINE.md:83`), while each tool's `OutputSchema` is described as a
single closed object containing the success record's properties plus an
optional `error` property (`ARCHITECTURE-SPINE.md:121-125`).

**Two-unit counterexample:** the schema builder marks non-nullable
`CommandResult` properties such as `messageId` and `correlationId` as required,
which is the normal schema for the record. The adapter correctly returns only
`{ "error": ... }` on failure. A schema-validating MCP client rejects that result
because the success properties are absent. A second schema builder makes every
success property optional so errors pass; its schema also accepts `{}` and
objects containing both success and error fields. Both follow "success
properties plus an optional error," but publish incompatible contracts.

**Disposition:** **autofix**. Define the output schema as `oneOf` two closed
branches: the exact success record and `{ error: OperationError }` with `error`
required. Generate both the schema and structured content from one Core-owned
public-document contract, including required/omitted/null behavior for nested
violations, Gateway errors, paging, `document`, and result payloads.

### ADV-004 — High — Offline discovery and execution availability disagree

**Pair:** Catalog/describe story and settings/executor/composition-root story.

**Spine evidence:** `ICatalog.Describe` computes `Submittable` and `Reason` from
the descriptor and `ResolvedSettings.ReadOnly` only
(`ARCHITECTURE-SPINE.md:67-71`); the transport registration consumes
`settings.Url` (`ARCHITECTURE-SPINE.md:109-113`); settings explicitly default to
no URL and classify a missing URL as `configuration_invalid`
(`ARCHITECTURE-SPINE.md:127-131`).

**Two-unit counterexample:** with no URL and Read-only Mode off, the Catalog
story correctly reports a write Operation as `submittable: true` because AD-3
gives it no other input. The executor/settings story correctly refuses the same
Operation with `configuration_invalid`, or the gateway client fails while being
constructed. Both obey their ADs; discovery promises an execution path that the
configured process cannot take.

**Disposition:** **autofix**. Introduce one Core-owned immutable execution
availability value derived from `ResolvedSettings` (at minimum `HasGatewayUrl`
and Read-only Mode). Use it both in `Describe` and as an executor preflight
before resolving/constructing the client. Preserve offline Catalog discovery:
missing URL must not make settings resolution or host construction fail.

### ADV-005 — High — Two fixture Modules in one assembly have no ownership mapping

**Pair:** Decoration/Sample.Contracts story and Catalog builder story.

**Spine evidence:** the Module marker is assembly-level
(`ARCHITECTURE-SPINE.md:180`); Catalog input is a list of assemblies and its
frozen model nests Operations under `ModuleDescriptor`
(`ARCHITECTURE-SPINE.md:67-71`); the one `Sample.Contracts` project is required
to declare both `sample-ulid` and `sample-opaque`
(`ARCHITECTURE-SPINE.md:193,238`). No Operation attribute or convention names
which of multiple assembly markers owns a type.

**Two-unit counterexample:** the fixture author applies two assembly-level
`[HexalithModule]` attributes and adds one Command for each identifier kind. One
Catalog implementation treats the second marker as `duplicate_module`; another
adds every decorated type to both Modules; a third partitions by namespace.
Each choice is consistent with some literal part of the spine, but they produce
different names, Identifier Kind validation, schemas, and diagnostic counts.

**Disposition:** **autofix**. Prefer one Module per assembly and split the fixture
into `Sample.Ulid.Contracts` and `Sample.Opaque.Contracts`. If multiple Modules
per assembly are intentional, add an explicit Module discriminator to every
Operation decoration and define duplicate-marker/name handling before building
the Catalog.

### ADV-006 — High — The release rule can build successfully without producing a releasable artifact

**Pair:** project packaging story and semantic-release workflow story.

**Spine evidence:** AD-17 names `dotnet build`, the two-package manifest, and a
push, but no pack/validation/install sequence (`ARCHITECTURE-SPINE.md:151-155`);
the structural seed lists only the manifest beside release configuration
(`ARCHITECTURE-SPINE.md:214-223`); the runtime view says semantic-release packs
and pushes on a manually dispatched green SHA (`ARCHITECTURE-SPINE.md:257-261`).

**Two-unit counterexample:** project authors leave the SDK default
`GeneratePackageOnBuild=false`, fully consistent with AD-17. A release author
implements the only exact command named there, `dotnet build ... -p:Version=...`,
then has no `.nupkg` to validate or push. Another release author copies a sibling
pack script and succeeds, but neither the script set nor artifact checks are a
spine invariant. Both can claim compliance, yet only one produces the two
artifacts AD-17 promises.

**Disposition:** **autofix**. Fix the release transaction: exact pack command or
script over `tools/release-packages.json`, NuGet/consumer validation, secret and
publication preflight, then push exactly the two expected IDs at one version.
Add an isolated local-source `dotnet tool install` smoke test that runs
`hexalith --version` and an offline command so the packed Core, MCP, Contracts,
and manifest closure—not merely the build output—is verified.

### ADV-007 — Medium — Profile mutations can lose updates or expose a token transiently

**Pair:** two independently implemented `config` verb stories using the shared
ProfileStore.

**Spine evidence:** settings are read once per process and one `ProfileStore`
owns the path (`ARCHITECTURE-SPINE.md:115-119`); the store exclusively reads and
writes a credential-bearing JSON file and requires final modes 600/700
(`ARCHITECTURE-SPINE.md:133-137`); it is the only mutable state
(`ARCHITECTURE-SPINE.md:192`). No atomic mutation, locking, creation-mode, or
recovery rule exists.

**Two-unit counterexample:** process A runs `config profile add` and process B
runs `config set` concurrently. Both load the same version-1 document through
the exclusive store, mutate their own copy, and save it; the last rename/write
silently discards the other's valid update. A compliant implementation that
writes then chmods can also leave a newly created token file readable according
to the caller's umask before mode 600 is applied, while an atomic-temp writer
does not. Both end with the required shape and final mode.

**Disposition:** **autofix**. Make ProfileStore expose one transactional mutation
API; serialize writers across processes; create a same-directory temporary file
with restrictive permissions before writing secrets; flush and atomically
replace; reject symlink/non-regular targets; and specify corrupt-file recovery.
Add concurrent-writer and interrupted-write tests. Windows credential-file
protection may be explicitly deferred, but non-Windows behavior is already in
scope.

## Recommended gate outcome

Resolve ADV-001 and ADV-002 with explicit product/architecture decisions before
story breakdown. ADV-003 through ADV-006 are bounded spine autofixes. ADV-007 may
be deferred only with an explicit single-writer operating constraint and revisit
condition; silent last-writer-wins is not a safe implied default for a token
store.

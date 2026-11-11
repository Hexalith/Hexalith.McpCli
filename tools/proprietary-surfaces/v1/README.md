# Committed proprietary-surface census

This gate rejects new proprietary MCP servers, plug-ins, CLIs and publication
entries in root-declared references. It runs with Python 3.11+ and Git; it does
not run .NET, MSBuild, a reference's scripts or any discovered executable.

```sh
python3 -m unittest discover -v -s tools/proprietary-surfaces/v1 -p 'test_*.py'
python3 tools/proprietary-surfaces/v1/check.py --output /tmp/mcpcli-census.json
```

The root references must already contain the pinned Git objects. CI reads
`.gitmodules` and gitlinks from the same parent commit, initializes only those
root declarations with recursion disabled, then runs the fixtures and scan.
Locally, an unavailable root or object fails with a prerequisite diagnostic;
the checker never initializes anything. `--workspace` and `--revision` allow
inspection of another parent checkout or commit. Reference HEADs, index files
and dirty/untracked source do not influence the inspected trees.

## Scope and signals

The gate accounts for every root declaration and reads committed blobs at its
exact gitlink. Nested gitlinks are listed without opening or initializing them.
The baseline carries root provenance and the approved PS, PE, PN and FK
classifications from technical-tools migration inventory 1.0.2. Its inventory
and Story 5.1 approval receipt hashes are checked against the parent commit.

Discovery includes C#, F# and VB project identities, executable projects,
packages and project references, packed tools and command names, local
`Directory.Build.props`/targets and imports, MCP registration/tool attributes
(including F# and VB attribute forms), direct MCP server/transport construction,
System.CommandLine source, linked source files, MCP client definitions, .NET
and npm tool manifests, package/container release manifests, workflow/script
project references and literal package/container identities. Literal Docker
`--tag=value` options, executable shell scripts identified by a shell shebang,
build-push action tags, YAML flow image mappings and Kustomize `newName` image
identities are included. Both JSON server sections are inspected when present.
Workflow project matrix values are resolved per job; unresolved project-target
expressions and unsafe publication paths fail with the metadata path, while
unrelated configuration/output expressions remain outside target resolution. Outside-`src`
executables and web hosts are included. Ordinary present web/service/library
projects without a tool or MCP signal are not proprietary surfaces.

Local imports are read conservatively from committed blobs regardless of filename
extension, including literal filenames embedded in property functions and globs.
Each project uses the nearest default `Directory.Build.props` before the project
and the nearest default `Directory.Build.targets` afterward, plus their explicit
imports. More distant defaults do not contribute properties unless imported.
Unconsumed metadata, including shadowed or standalone defaults, is still parsed
and classified independently. Missing required literal local imports fail; an
exact `Exists` condition can prove an absent import optional. SDK-resolved and
intentionally unopened nested-gitlink imports remain distinct from missing local
blobs. Property expansion has a 128-level budget and fails with the metadata
path when exhausted. Classification aliases and conditional imports retain alternatives; unconditional property
replacements and empty assignments control effective package defaults.
Reference item lists are split before classification. Recursive `**/` globs include zero
intermediate directories. SDK identities come from XML declarations, including unconditional explicit
`Sdk.props`/`Sdk.targets` imports with an `Sdk` attribute; comments provide no SDK
authority. Unconsumed local props/targets declaring an
executable, packed tool, command name, MCP/CLI dependency or MCP container
identity become independent candidates, including when an import directory
cannot be resolved. SDK and unavailable nested-reference imports
are never evaluated. This is a static source census: it cannot establish the
behavior of dynamically generated code or remote deployment composition.

Each candidate binds an exact repository, path, kind and identity. Package IDs,
tool commands and container repositories have separate identities, including
SDK package defaults from the effective assembly/project name for packable
projects and packed-tool command defaults from TargetName or AssemblyName. Approving
a project never permits it to acquire another published name. An allowance
also limits its detection signals; a dependency consumer gaining an MCP
registration fails. Named tool exemptions apply to consumption, such as tool
installation and developer-tool manifests. Defining a local npm binary requires
an exact existing allowance even when its name matches an exempt tool. Container
images associate with an ordinary project only through its complete declared
`ContainerRegistry`/`ContainerRepository` identity. Tag and digest suffixes are
ignored for this association; registry ports and repository namespaces remain
part of the identity. Other registries/namespaces and any project with an MCP/CLI
signal remain subject to discovery. A matching project or package basename grants
no container exemption.

Captured evidence prefixes are explicit scoped data with their PE07
classification and rationale. A regular directory named `references`, `tests`
or `perf` grants no exemption. Test and qualification allowances use exact
approved identities; nested gitlinks are handled by Git object type.

The original 1.0.1 option-A amendment and receipt remain byte-identical. The
1.0.2 correction strengthens its two fixture exemptions to the complete committed
local compilation/source closure: every fixture-directory file, inherited
`Directory.Build.props`/targets, resolved local imports and linked Compile
sources, including committed glob matches outside the fixture directory.
Allowance data sets `compilationClosure: true`, keeps `sourcePrefix` equal to
the project's directory, and lists every closure file under `sources` as a
repository-relative `path` and SHA-256. Changed inherited, imported, linked or
secondary sources and added/removed closure files fail. Imported Compile paths
use the consuming project directory unless `MSBuildThisFileDirectory` supplies an
explicit local base. Compile item aliases and alias chains resolve to finite committed literal/glob
inputs. Byte-preserving `Copy` outputs bind their committed source bytes when
all inputs resolve; other task output, generated `obj` files, unknown directory
aliases, missing sources and unsupported item transforms remain coverage errors.
Conditional and removed item alternatives are inspected conservatively. SDK and
external/nested reference contents remain outside the local closure and are
never initialized or opened. An unknown directory cannot be qualified from
local suffix matches alone. Cyclic/undefined aliases, more than 32 alias levels
or more than 4,096 source items fail with their metadata path.
Unresolved import globs inspect committed local suffix matches regardless of
extension. Shell, PowerShell and batch continuation lines are joined before
publication discovery; quoted project arguments retain their complete path,
and Docker push options do not obscure its image argument. Supported Docker
global options (including context/host) and the `image push` form retain the
complete image identity. VB registration
identifiers follow its case-insensitive language rules.

Correction 1.0.2 also records exact historical test observations at their already
approved census pins and exact captured/test metadata files. It grants no new
owner authority, directory exemption, future fixture or publication route.

## Supported static project targets

Shell target resolution supports literal assignments and property aliases,
multiline finite literal `for ... in ...` lists in their declared order, named function
calls with positional arguments, local/global function variables, literal `cd`
commands and multiline subshell directory restoration. The exact
`$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)` source-relative locator is
recognized as path spelling; its commands are never run. The resolver handles
repository-contained parent paths after a proven working directory. YAML run
steps have separate shell state, with workflow/job `defaults.run.working-directory`
and per-step `working-directory` precedence. Literal project matrix alternatives
expand into independent job blocks, with at most 256 combinations. A matrix
project expression must occupy the whole project argument; quoted paths retain
their full identity. Source tokens have no matrix decoding authority. Quoted
`dotnet` executables and literal environment prefixes retain their publication
command. Project-directory targets require
one committed project or solution; committed `.slnx` targets enumerate literal
project paths. Missing/ambiguous directories and unsupported solution formats
are refused rather than disappearing from the report.

The supported subset is deliberately bounded: at most 256 expansion choices or
loop values, 16 call levels and 8,192 visited shell statements per source.
Unknown substitutions, runtime parameters, recursive/unbounded control flow,
ambiguous conditional or short-circuit directory changes, missing directories
and targets crossing a nested gitlink retain actionable coverage errors. Shell
conditions are never executed. Inline loop bodies and command substitutions in
unquoted heredocs are explicitly refused when resolving project invocations.
Scripts without a literal `dotnet publish`, `pack` or `run` command require no
project-target dataflow; their other publication signals are still inspected.
Shell and PowerShell comment lines supply no executable state and cannot consume
the next command through a trailing continuation character. Quoted literal
heredocs supply no executable state. Conditional loops retain their uncertainty; unknown loops
invalidate a changed caller directory. Runtime reads, `unset` and unsupported
`declare`/`typeset` changes invalidate affected variables. Unsupported `printf -v`
writes, including attached `-vname` forms, invalidate the destination; an unknown
destination invalidates potentially affected state. Multiple-assignment statements
invalidate every identified assigned variable. Single-quoted function
arguments cannot borrow the authority of a variable they mention. Arbitrary
shell/PowerShell/batch evaluation,
external environment values and remote or generated source cannot establish a
committed target. Composite actions with literal caller-owned project paths
produce exact orphan publication observations when those sources are absent.
No new fixture or publication allowance follows from resolving a target.

## Results and exceptions

Exit 0 means all references were inspected successfully and all candidates were
approved or excepted. Exit 1 means a new identity, signal/source drift, invalid
policy/metadata, unsafe path or missing prerequisite. Stdout is the same stable,
sorted JSON document written to `--output`; stderr names rejected repositories,
gitlinks, paths and signals. Output passes the shared evidence redactor and
contains source paths and signal labels, never source snippets or credentials.
CI retains the sanitized JSON even when the scan fails. A project/file inspection
error retains other inspectable observations from that root. Its repository
summary has `inspectionComplete: false`, and its errors include the source
path and, for resolved nested/directory targets, the exact target. Partial roots
never establish that an unseen allowance is stale. An allowance's source-closure
failure also retains later candidates and fails that allowance explicitly.

Removed candidates appear under `stale`; staleness alone does not fail. Scans
never rewrite baseline data or delete allowances. The report's `policy` block
binds the exact baseline and ordered amendment hashes.

A migration exception contains exactly `surface`, `owner`, `reason`, and
`expires`. `surface` has the four exact identity fields above, with no pattern
matching. Owner and reason must be nonblank and expiry must be a canonical ISO
`YYYY-MM-DD` date. Production uses today's UTC date and includes the entire
expiry day. Every exception is validated even if its target is already allowed
or absent. Malformed, duplicate or expired exceptions fail the scan.

## Versioned changes

Keep `baseline.json`, the approved inventory, approval receipt and all prior
amendments byte-identical. The baseline is the original 1.0.0 census; changes
are an append-only chain referenced by `amendments.json`.

1. Obtain the owning maintainer's specific approval. Retain its source pins,
   exact identities, source/exception scope and rationale. A planning finding,
   an unrelated receipt or a mechanical correction provides no new authority.
2. Add the next `amendments/1.0.N.json` with the census `schema`, `fromVersion`,
   consecutive `toVersion` and `previousSha256` of the preceding amendment
   (the baseline hash for 1.0.1). Its `approval` requires nonblank `owner` and
   `reason`, an ISO `date`, affirmative `decision: "approved"`, and an `evidence`
   object containing the receipt's repository-relative `path` and SHA-256.
3. Include `addAllowances`, `removeAllowances`, `addExceptions` and
   `removeExceptions`, even when empty. Removals contain exact four-field
   surface descriptors and must target existing entries. Replacement uses an
   exact removal plus a complete approved addition. For fixture exemptions,
   compute the full local closure at the authorized Git pin with
   `compilation_closure(Tree(repository, gitlink), project)`; preserve every
   returned source hash rather than copying only the project's own directory.
4. A new approval receipt uses
   `schema: "mcpcli-census-amendment-approval/v2"`, `decision: "approved"`, and the same
   `owner` as the amendment header. Its `authority` is a nonempty array of
   `{ "path": "...", "sha256": "..." }` bindings to existing approved inventory
   or previously validated census approval JSON in this same lineage. An authority
   must exactly match committed baseline provenance or a previously validated
   receipt binding; an untracked authority file or an incomplete receipt cannot
   nominate itself. Inventory authority must bind the complete approved root/pin
   map. Hashes and approved decisions are checked; merely naming a receipt
   confers no authority. Its `authorization` must match the
   amendment's complete mutation arrays exactly, including all allowance
   fields, source hashes and exception owner/reason/expiry scope:

   ```json
   {
     "addAllowances": [],
     "removeAllowances": [],
     "addExceptions": [],
     "removeExceptions": [],
     "addExclusions": []
   }
   ```

   Include `addExclusions: []` in the receipt even when that optional array is
   absent from the amendment. Rejected, malformed, non-JSON, unrelated and
   differently scoped receipts fail. The retained v1 receipt format is limited
   to the original exact fixture scope and its committed historical receipt;
   an untracked v1 receipt is refused. `legacy-receipts.json` additionally freezes
   the exact retained receipt path/hash against this baseline's SHA-256.
   Committing a newly fabricated v1 receipt does not add it to that registry.
   The registry adds no allowance or new owner authority; preserve its bytes
   alongside the prior lineage and use v2 for future amendments.
5. If existing approval covers a captured or deliberately malformed metadata
   file, use an exact hash-bound entry in the amendment's `addExclusions`.
   Include `repository`, `prefix` (the complete file path), approved `row`,
   `classification`, `owner`, `reason`, `scope: "file"` and its `sha256`.
   Optional `additionalSha256` lists only separately inspected, explicitly
   authorized byte versions of that same file. Bind the inspected pins in the
   approval evidence. These entries match no sibling or future file; changed
   bytes fail. A directory name or a discovery finding does not authorize one.
6. Hash the finished receipt into the amendment's evidence binding, then append
   the finished amendment path and SHA-256 to `amendments.json`. Preserve all
   prior baseline, amendment and receipt bytes. Never extend a captured prefix
   to admit a future fixture. Root/scope changes require an approved new
   baseline lineage with preserved prior data and provenance.
7. Run fixtures and the real scan, retain report/approval hashes, and run
   `scripts/scan-evidence-secrets.py` over retained evidence. Scanning never
   edits policy or infers approval from discovered source.

Hash-bound JSON and evidence use `.gitattributes` byte preservation so Windows
checkout conversion cannot invalidate the chain. The required CI job and each
executed initialization, fixture and scan step are also paired-release staging
and publication prerequisites. Historical bootstrap recovery keeps its existing
gates and the publication-stage job map remains separate.

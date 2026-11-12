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
Those root references are full clones, but a fresh clone holds only commits
reachable from its remote refs. A nested pin that cross-tree resolution reads
(below) must therefore be reachable from the matching root's remote refs;
otherwise it fails as `nested-object-unavailable`. Locally, an unavailable root
or object fails with a prerequisite diagnostic; the checker never initializes,
fetches or checks out anything. Every Git call that reads a repository adds
`-c protocol.allow=never`, sets `GIT_NO_LAZY_FETCH=1`,
`GIT_NO_REPLACE_OBJECTS=1` and an empty `GIT_ALLOW_PROTOCOL`, and drops the
repository-local variables that `git rev-parse --local-env-vars` lists. A
partial clone therefore cannot fetch a missing object on any Git version, even
under an inherited protocol allow list or `protocol.<name>.allow` setting,
replace refs never substitute committed bytes, and an inherited `GIT_DIR` or
object directory cannot redirect a read. That `--local-env-vars` query is the
one call that reads no repository or object; it runs without those protections
and with no inherited `GIT_` variable, and its failure is reported as
`git-unavailable`. `--workspace` and `--revision` allow
inspection of another parent checkout or commit. Reference HEADs, index files
and dirty/untracked source do not influence the inspected trees.

## Scope and signals

The gate accounts for every root declaration and reads committed blobs at its
exact gitlink. Nested gitlinks are listed and never initialized; only the
MSBuild imports and Compile sources described under cross-tree resolution read
their committed objects.
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
and classified independently. Missing required literal local imports fail. An
absent import is optional when an `Exists` condition names that exact path,
alone or as one conjunct of a top-level `and` condition, or when the
[Exists() guard excuse](#exists-guard-excuse) proves the import never
evaluates. Otherwise a top-level `or`, an unbalanced condition, an `Exists` on
another path that is not proven absent, or a negated `!Exists` on a path that is
not proven present proves nothing. SDK-resolved imports remain distinct from
missing local blobs; nested-gitlink and escaping imports follow cross-tree
resolution. Property expansion has a 128-level budget and fails with the
metadata path when exhausted. Classification aliases and conditional imports
retain alternatives; unconditional property replacements and empty assignments
control effective package defaults. Reference item lists are split before
classification. Recursive `**/` globs include zero intermediate directories. SDK
identities come from XML declarations, including unconditional explicit
`Sdk.props`/`Sdk.targets` imports with an `Sdk` attribute; comments provide no
SDK authority. Unconsumed local props/targets declaring an
executable, packed tool, command name, MCP/CLI dependency or MCP container
identity become independent candidates, including when an import directory
cannot be resolved. SDK imports and unresolvable nested references
are never evaluated. This is a static source census: it cannot establish the
behavior of dynamically generated code or remote deployment composition.

## Cross-tree MSBuild resolution

Only MSBuild imports and Compile item sources cross a tree boundary, and each
resolution chain crosses at most once. Paths are normalized after literal
property expansion. Compile paths keep project-relative semantics; imports are
relative to their declaring file.

- **Workspace rule.** A path escaping the inspected root is normalized against
  the parent revision tree. Inside a root-declared gitlink, it is read at that
  root's committed pin from that root checkout's object store, not its HEAD or
  worktree. A path back inside the inspected root is an ordinary local path.
- **Nested rule.** A path inside a nested gitlink is read at that exact nested
  commit from the single root-declared reference whose URL equals the nested
  entry's URL in the inspected root's `.gitmodules` at the same pin. Comparison
  trims one trailing `/` and then one trailing `.git`, and ignores case only in
  the host. Relative URLs never match. As for root declarations, every section
  must be `submodule "<name>"` with a safe path; otherwise the nested
  declarations declare nothing. A missing, duplicate, malformed or ambiguous
  declaration fails as `nested-pin-unresolvable`; a commit absent from that
  root's object store, or a gitlink naming a non-commit object, fails as
  `nested-object-unavailable`.
- **Absent paths.** An import of a missing file in a substituted tree, or of a
  missing parent-tree path outside every root, is refused unless an `Exists`
  condition requires that exact path or the
  [Exists() guard excuse](#exists-guard-excuse) proves the import never
  evaluates. Such a path is absent only as `Tree.absent()` decides: a present
  parent-tree blob or directory outside every root is never read, a case
  variant or a path through a committed link is refused, a parent-tree glob
  outside every root is never listed, and a directory, a tree root or the parent
  workspace root is never a file. A local import through a committed link is
  refused as `unavailable-local-import` with its label as `target`.
- **One hop.** A substituted file's imports must stay inside that same
  substituted tree. A further escape, including one back into the inspected
  root, or a gitlink inside the substituted tree fails. A Compile item declared
  there may name files in that same substituted tree or the inspected root's own
  committed sources, which need no cross-tree read; any other tree fails. A
  glob is refused when an unopened gitlink lies below its directory.

Anything else, including a path above the parent root or an unavailable
workspace root object (`workspace-object-unavailable`), keeps
`unsafe-import-path` or `unsafe-or-nested-compile-source`. These errors name the
declaring metadata file in `rule` and the refused root-relative label in
`target`; a leading `../` marks a workspace label. Every substituted blob read
for a root is listed once in that repository summary's `crossTreeReads`, with
`requested` label, `resolution` (`workspace` or `nested`), source `repository`,
`commit`, in-tree `path`, `sha256` and, for nested reads, `nestedGitlink`. A
read stays listed when its file is then refused. A substituted file's import
that keeps an unresolved `$(` fails as `unsafe-import-path` with its label as
`target`; it is never name-matched against inspected-root metadata. A
substituted blob missing from its object store fails as
`workspace-object-unavailable` or `nested-object-unavailable` with the
requested label in `rule` and `target`; invalid text fails as
`malformed-text:<label>`. Substituted blobs contribute classification signals.
A compilation-closure allowance binds each substituted member by its requested
label and pinned blob hash, so a sibling or nested pin that changes, adds or
removes a member is source drift, as is any signal it adds. Publication targets
inside nested gitlinks keep `nested-publication-target`. No module name, path or
count is part of this logic.

## Exists() guard excuse

A guard only excuses a target that is missing from every inspected tree and
would otherwise be refused: an import (`unavailable-local-import` or an absent
`unsafe-import-path`), or, under (c), a cross-tree Compile source
(`unsafe-or-nested-compile-source`). It never skips a present target, never
removes a property alternative and never changes classification; nothing new is
recorded in policy. An absent target is excused when one of these holds:

- **(a)** the import's evaluated condition, its own `Condition` plus an
  enclosing `ImportGroup` `Condition`, has a conjunct that proves false; or
- **(b)** the import's `Project` is exactly one `$(P)`, and every definition of
  `P` that produced that exact value is conditional and proves false through its
  own or enclosing `PropertyGroup` condition.
- **(c)** a direct `Compile` `Include` starts with one `$(P)`, and the absent
  cross-tree value equals a recorded alternative of `P` followed by the
  Include's remaining literal text. Every definition of `P` that produced that
  alternative must be conditional and prove false from facts outside the
  inspected repository, never from a path in its own tree, where builds write
  outputs. `P` must also keep at least one unproven definition, so the build
  cannot fall back to an empty or environment value. Item aliases, `Copy` task
  outputs, local sources (which a build may generate), globs and every other
  shape keep their refusal.

Only a balanced top-level `and` conjunction with no top-level `or` counts. A
conjunct proves false when it is exactly `Exists('p')` with every expansion of
`p` proven absent, or `!Exists('p')` with every expansion proven present;
parenthesized or negated groups prove nothing, and a quoted argument cannot
span quotes. Arguments are trimmed, as MSBuild trims items. An argument proves
nothing when an expansion is a `;` list of more than one item, keeps `$(`, `@(`
or `%(`, contains a `%XX` escape, or uses a property that is only conditionally
defined (so it may be empty), was defined from such a property or before a
property it names, is item metadata rather than a `PropertyGroup` definition,
or is also defined inside a `Target`. `!Exists('p/')` with a trailing `/` or
`\` is proven only for a committed directory. `Choose`/`When` conditions and
anything inside a `Target` prove nothing. Relative paths in `Import`,
`ImportGroup` and enclosing `PropertyGroup` conditions resolve from the
declaring file; a property element's own condition resolves them from the
entry project's directory, as an MSBuild evaluation of both forms shows.

An import `Project` value is trimmed too. A value that is a `;` list of more
than one item, or that contains a `%XX` escape MSBuild would decode, fails as
`unavailable-local-import` or `unsafe-import-path` with its label as `target`,
whatever its condition. The exact-path `Exists` rule uses the same conjunct
parser, trims its argument and ignores a list or escaped argument.

Proofs model the parent workspace CI builds from: the parent revision tree,
each root-declared reference checked out at its pin, and no nested gitlink
initialized. They read tree entries only, never blob content.

- **Present** means a committed regular blob or directory at that exact spelling
  in the inspected root, or in a root-declared reference at its pin. A path
  under a nested gitlink, a link, a gitlink, a glob, or parent-tree content
  outside every root is never present.
- **Absent** means no case-insensitive match for an entry or directory in that
  model: the inspected root, the root reference at its pin, or the parent tree
  outside every root. A nested path is absent only when its exact nested commit,
  read through the nested rule, has no such match. A tree root, the parent
  workspace root, a path below an unopened gitlink or through a committed link,
  a glob and a path above the parent root are never absent.
- **One hop.** A guard in a substituted file proves something only for a path in
  that same substituted tree, and a nested commit never proves presence.

Because only an absent, otherwise refused target is excused, a build-time file
such as `obj/project.assets.json`, an ignored file or a standalone layout cannot
hide committed content: a present import is always visited and every
conditional property alternative is kept. Global `-p:` properties are outside
the static model.

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
repository-relative `path` and SHA-256; a cross-tree member is listed by its
requested label, where a leading `../` marks a workspace label. Only such a
closure may name a label outside the repository. Changed inherited, imported,
linked or secondary sources and added/removed closure files fail. Imported
Compile paths use the consuming project directory unless
`MSBuildThisFileDirectory` supplies an explicit local base. Compile item aliases
and alias chains resolve to finite committed literal/glob inputs.
Byte-preserving `Copy` outputs bind their committed source bytes when
all inputs resolve; other task output, generated `obj` files, unknown directory
aliases, missing sources and unsupported item transforms remain coverage errors.
Conditional and removed item alternatives are inspected conservatively. SDK
contents remain outside the closure. Workspace and nested reference contents
enter it only through cross-tree resolution, bound by label and pinned blob
hash, and are never initialized. An unknown directory cannot be qualified from
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

Committed JSON inputs also support this finite literal selector spelling:
`jq -er '.payload.units | select(length == 2) | .[] | [.label, .target] | @tsv' targets.json`.
The property names and positive length are data; `-r` and `-re` are also supported.
Dotted object fields select one array and one or more ordered string fields per
row. A `while IFS=$'\t' read -r label target; do` loop with
`done <<< "$rows"` consumes an exactly bound assignment such as
`rows="$(jq ...)"` in array order. It preserves field pairing and directory
changes between iterations. The final EOF read invalidates its destinations.
No jq program, shell condition, inspected command or project is executed.

This subset requires 1–256 rows, at most 32 columns and 32 dotted field levels,
plus the existing JSON, statement and call budgets. Fields must be nonempty
strings without control characters, backslashes or shell expansion syntax;
missing fields, a failed length assertion, a scalar collection, zero rows and
reader field-count mismatches fail coverage. Inputs require an exact committed
regular blob and a proven directory. Quoted filenames retain spaces; unquoted
inputs need a safe exact shell argument. Runtime/generated inputs, unsupported
filters/options, nested roots, command/reader overrides and unknown mutations
retain explicit coverage errors. Table copies and other readers remain unsupported.

Before a selector, the resolver tracks effects in source order. It accepts the
retained shell guards, diagnostics, variable operations, proven directory
locators and directory creation; it refuses file redirections and unsupported
commands or substitutions that could change the input. Numeric descriptor
duplication such as `>&2` is harmless. A `find` deletion is accepted only for a
complete finite disjunction of literal `-name` filters that cannot match the
input basename, using ASCII filename literals and `*`/`?` wildcards, with optional
`-maxdepth` and `-type f`; other find actions or
expressions fail. Unknown helpers, wrappers and file writers cannot establish
immutable-input authority. Unknown writes to table or row variables invalidate
their targets, including conditional and short-circuit mutations. This is a
bounded source proof, with no new allowance or qualification from enumeration.

Additional committed path spellings include quoted or unquoted source-relative
`cd`/`dirname`/`pwd` locators, an optional `CDPATH=` prefix, `--` path delimiters,
`pwd -P`, and a second locator based on a previously proven script directory.
These locators apply to committed script files. A workflow run step's
`BASH_SOURCE[0]` names a runner-generated temporary script and supplies no
committed directory authority. Locator proof is refused when source mutates
its context or overrides its path builtins. Literal source tokens cannot borrow
the resolver's internal repository marker; a NUL in publication-script source
fails as unsafe text. Redirected `done` terminators preserve the
boundary between a loop and subsequent publication commands. Executable
process/command/backtick substitutions in their redirection suffix remain
coverage errors. `elif` remains
in its existing conditional branch and does not make later unconditional
assignments conditional.

PowerShell variable, cmdlet and alias evaluation remains unsupported.
Unsupported executable wrappers such as `sudo`, `nohup`, `time`, and
`env -i` retain the discovered target and an explicit coverage error.

Project-command recognition distinguishes executable tokens from shell comments
and literal diagnostic strings. Quoted executables and command substitutions,
including backticks inside double quotes, remain executable signals. Literal
heredoc contents do not affect later shell quote state or workflow matrix target
resolution. Sources with no recognized project-publication signal produce no
project-target control-flow diagnostic; this describes the census's static
scope and does not establish arbitrary runtime behavior.

Relevant JSON metadata may contain object arrays or wrapper objects. Traversal
preserves nested package, image, project and server definitions, with a maximum
depth of 32 and 4,096 object/array nodes. Scalar roots and structural arrays of
scalars fail coverage; ordinary nested configuration argument arrays remain
data. JSON Schema definitions under standard schema keywords describe metadata
and are not runtime manifests. Actual manifest fields beside those definitions
are still inspected. Malformed embedded publication entries remain actionable
errors; a fixture or evidence path grants no exemption.

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
path and, for resolved nested/directory targets and refused cross-tree labels,
the exact target. Each repository summary also lists its `crossTreeReads`. Partial roots
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
   compute the full closure at the authorized Git pin with
   `compilation_closure(tree, project, resolver)`, where
   `resolver = Resolver(Workspace(workspace, parent, declarations(parent)), repository, tree)`,
   `tree = Tree(repository, gitlink)` and `parent = Tree(workspace, revision)`.
   Preserve every returned source hash rather than copying only the project's
   own directory. Without a resolver, cross-tree imports and sources are
   refused. Policy loading validates a retained v1 fixture receipt without
   workspace context, so a cross-tree path in that fixture's metadata is refused
   and policy loading fails closed.
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
   A current classification of an existing opaque build/test helper may additionally
   bind `sourceRevision` to the exact inspected 40-character lowercase Git commit.
   This field is valid only for an exact `scope: "file"` exclusion. Both that pin
   and the file hash must match. A later repository pin refuses even when the
   helper body stays unchanged, so release-specific source review grants no future
   helper or target authority. The approval receipt records the unmodeled runtime
   expressions and the limits of the classification; enumeration or hashes do not
   prove runtime behavior. These entries add no proprietary implementation.

   To approve a refreshed version of an already excluded file, add another
   exact-file entry for the same `repository` and `prefix` in a later amendment.
   Keep the same `row` and `classification`. Append-only amendments record those
   separately authorized versions; there is no removal operation for exclusions.
   The checker accepts only their explicitly recorded hashes at their applicable
   source revisions, so an entry without `sourceRevision` still matches the
   current pin and earlier approved bodies of that file stay approved. An unknown
   body, wrong pin, neighboring file or unrelated source still refuses, and
   earlier baseline and receipt bytes never change. A file covered by an
   exact-file entry never falls back to a directory-scope exclusion of its
   parent, so a drifted file fails even inside an excluded directory.
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

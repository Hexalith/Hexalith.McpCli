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
`Directory.Build.props`/targets and imports, MCP registration/tool attributes,
System.CommandLine source, linked source files, MCP client definitions, .NET
and npm tool manifests, package/container release manifests, workflow/script
project references and literal package/container identities. Outside-`src`
executables and web hosts are included. Ordinary present web/service/library
projects without a tool or MCP signal are not proprietary surfaces.

Local imports are read conservatively, including literal filenames embedded in
property functions and globs. Unconsumed local props/targets with tool metadata
become independent candidates. SDK and unavailable nested-reference imports
are never evaluated. This is a static source census: it cannot establish the
behavior of dynamically generated code or remote deployment composition.

Each candidate binds an exact repository, path, kind and identity. Package IDs,
tool commands and container repositories have separate identities, so approving
a project never permits it to acquire another published name. An allowance
also limits its detection signals; a dependency consumer gaining an MCP
registration fails. External developer tools and the two approved Builds tools
retain their categorical exemption through named baseline data.

Captured evidence and nested-reference prefixes are explicit scoped baseline
data, with their PE07 classification and rationale. Test and qualification
project allowances use exact paths. The user-approved 1.0.1 amendment covers
only PublishSpike and Epic16.NativeHelper and binds every committed file in each
fixture directory. Changed secondary sources, added files and removed files fail
the complete source closure check. It grants no exemption to future fixtures or publication routes.

## Results and exceptions

Exit 0 means all references were inspected successfully and all candidates were
approved or excepted. Exit 1 means a new identity, signal/source drift, invalid
policy/metadata, unsafe path or missing prerequisite. Stdout is the same stable,
sorted JSON document written to `--output`; stderr names rejected repositories,
gitlinks, paths and signals. Output passes the shared evidence redactor and
contains source paths and signal labels, never source snippets or credentials.
CI retains the sanitized JSON even when the scan fails.

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

1. Obtain the owning maintainer's specific approval and retain its receipt with
   source pins, exact inspected identities, scope and rationale. A planning
   finding alone provides no approval.
2. Add the next `amendments/1.0.N.json`. Set `fromVersion`, consecutive
   `toVersion`, and `previousSha256` to the preceding amendment's exact hash
   (the baseline hash for 1.0.1). Bind the approval evidence path and hash.
3. Use `addAllowances` for exact approved entries and `addExceptions` for exact
   expiring exceptions. Use `removeAllowances` or `removeExceptions` with exact
   four-field descriptors to retire entries or replace them with approved new
   data. Removal of an absent or ambiguous entry fails. All four arrays are
   required, including when empty. No scan infers an amendment from source.
4. Append the new relative path and SHA-256 to `amendments.json`; leave all
   previous bytes unchanged. Do not edit existing allowances or extend a
   captured prefix to admit a future fixture. Root/scope changes require a new
   approved census baseline lineage with preserved prior data and provenance.
5. Run fixtures and the real scan, retain the report and approval hashes, and
   run `scripts/scan-evidence-secrets.py` over retained evidence.

Hash-bound JSON and evidence use `.gitattributes` byte preservation so Windows
checkout conversion cannot invalidate the chain. The required CI job and each
executed initialization, fixture and scan step are also paired-release staging
and publication prerequisites. Historical bootstrap recovery keeps its existing
gates and the publication-stage job map remains separate.

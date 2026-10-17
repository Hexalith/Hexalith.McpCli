# Story 4.6 bootstrap verification

## State

Local implementation and checks completed on 2026-10-17. The story remains
**in-progress** while the production release and owning Builds integration run.
Credentials are excluded from this evidence.

- Starting committed source: `04178de98f30b0c5541f7efb978e9b9acc8e8c1d` on `main`.
- Reviewed implementation commit SHA: `d9f822d64f7afa9bd51ca1698f5051147b86b554`, pushed to `main`.
- Exact-source bootstrap push run: [39052313304](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39052313304), success.
- Exact-source commitlint push run: [39052313562](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39052313562), success.
- Full CI push run: [39052313593](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39052313593), success; bootstrap release does not require it.
- Production release run: [39055956370](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39055956370), dispatched from exact `main` SHA with `phase=bootstrap`. Both source checks, preparation and package validation passed; NuGet rejected the push with HTTP 403.
- Selected version: `1.0.0`; tag [`v1.0.0`](https://github.com/Hexalith/Hexalith.McpCli/tree/v1.0.0) points to the reviewed commit. No GitHub release exists yet.
- Prepared production package SHA-256 before rejected push: `7779b0bd465e2013a720d799bebf17edd99f4da2910715b1c56327b64b840a92` (workflow log; not a published-package hash).
- Published package version, registry URL and downloaded-package SHA-256: pending; public flat-container package URL returned HTTP 404 after the rejected push.
- Public-feed consumer restore/build and analyzer proof: pending publication.
- Owning Builds catalog/audit revision and integration evidence: pending publication.

## Local verification

```sh
python3 -m unittest discover -s scripts/tests -p 'test_bootstrap_release.py'
```

Passes 35 test methods with synthetic packages, a stub registry, a stub `dotnet`
publisher, and stub GitHub run responses. Rejection cases include wrong package
ID/version, missing compile/analyzer DLLs, dependency leakage, extra artifacts,
missing/malformed packages, duplicate ZIP entries, symlink packages/staging directories/receipts, missing or
invalid preparation receipts, modified prepared bytes, unsupported phases,
invalid versions, missing credentials, taken versions, uncertain registry
responses (including malformed listed versions), non-Git source, wrong or dirty
HEAD, untracked source, wrong release branch, stale main, and absent/failed/pending/stale
bootstrap or commitlint results. Recovery cases cover absent, matching, mismatching
and uncertain public package states without network calls; matching existing
publication performs zero pushes. Paired-validator fixtures cover every required
tool artifact, tool kind, command attributes, generated Contracts manifest and
packaged Contracts DLL, plus a valid paired fixture. A successful fake publication records exactly
the checked snapshot hash; no rejection reaches the fake push. The source gate
requires no `ci.yml` result.

```sh
MCPCLI_RELEASE_PHASE=bootstrap bash scripts/release-prepare.sh 1.0.0
```

Passes. Only `src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj`
is directly restored/built/packed; its analyzer project is the only production
project dependency. Release build has zero warnings and errors. The resulting
single package includes the net10.0 compile DLL and C# analyzer and declares no
consumer-visible package dependencies. Package staging and its SHA-256 receipt
are under ignored `nupkgs/`; unrelated contents are preserved. The initial local
staging was preserved under a private temporary directory before rerunning after
the packaged README changed. The local hash is recorded below after that rerun;
it is not publication evidence.

Local package: `Hexalith.McpCli.Abstractions.1.0.0.nupkg`, SHA-256
`806e69f83b75021e013b1a54278cc503a4bfc3407dcff88414904431a46ba868`.

Preparation now runs the packaged consumer before creating the receipt. Prior
bootstrap artifacts were preserved at
`/tmp/mcpcli-4-6-preserved-bootstrap-hss_e0m2`; unrelated `nupkgs/` contents remain.
No publication-source gate is claimed from this uncommitted local preparation.

```sh
for project in Abstractions Analyzers; do
  test_project="tests/Hexalith.McpCli.${project}.Tests"
  dotnet restore "$test_project"
  dotnet build "$test_project" --configuration Release --no-restore -warnaserror
  dotnet test "$test_project" --configuration Release --no-build
done
```

Passes: Abstractions **20/20**, Analyzers **19/19**, no skips. Both builds have
zero warnings/errors. Abstractions tests compile the existing Sample.Contracts
and EventStore.Contracts author-time fixtures; neither suite builds Core, CLI or
MCP production projects.

```sh
consumer_root=$(mktemp -d /tmp/mcpcli-story-4-6-consumer.XXXXXX)
bash scripts/smoke-bootstrap-consumer.sh 1.0.0 "$PWD/nupkgs/bootstrap" "$consumer_root/consumer"
```

Passes with an isolated `NUGET_PACKAGES`, one exact package reference
`Version="[1.0.0]"`, both command/query decorations, exactly one `MCPCLI001`
warning from the deliberate blank-description fixture, and zero compile errors.
No analyzer-loading diagnostic (`CS8032`/`CS9057`) appears. The consumer uses an
explicit NuGet configuration with cleared package sources/fallback folders, fresh
package and HTTP caches, and empty MSBuild fallback-folder properties.

A second real reproduction used an empty local source while setting
`NUGET_FALLBACK_PACKAGES` to the first consumer's populated cache. Restore failed
with `NU1101`, proving the cached package cannot falsify source evidence. Positive
and negative outputs are retained at `/tmp/mcpcli-4-6-source-proof.z3YdOL`; the
negative output is `negative.log`.

The final committed candidate repeated this isolation check with a parent
`TreatWarningsAsErrors` props file. The positive relative-source consumer passed;
the negative empty-source restore failed with `NU1101` despite inherited
`RestoreSources`, `RestorePackagesPath` and fallback environment values aimed at
the populated cache. Both logs are at
`/tmp/mcpcli-4-6-final-isolation-h2nnkd5k`.

```sh
actionlint .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/release.yml .github/workflows/recover-partial-release.yml
bash -n scripts/release-prepare.sh scripts/release-preflight.sh scripts/release-publish.sh scripts/smoke-bootstrap-consumer.sh
git diff --check
```

All pass. Git reports pre-existing missing commit-graph warnings without affecting
the successful whitespace check.

## Remaining release and upstream steps

The `gh` CLI is authenticated; the independent owning checkout
`/home/administrator/projects/hexalith/builds` is clean and fast-forwarded to
`c8c72dc`. The prior organization `NUGET_API_KEY` secret was rejected by NuGet;
its value has not been inspected or recorded locally. The user supplied an
active, organization-owned nuget.org trusted-publishing policy for GitHub
repository `Hexalith/Hexalith.McpCli`, workflow `release.yml`, environment
`production`, with push scope for `*`. The GitHub owner/repository immutable IDs
match the policy. The revised workflow requests a short-lived key via OIDC.

1. Completed: review, pinned commitlint validation, commit and main push at
   `d9f822d64f7afa9bd51ca1698f5051147b86b554`.
2. Completed: latest successful **push** runs of `bootstrap-package.yml` and
   `commitlint.yml` for that exact main SHA. A live source guard invocation also
   verified both runs and current main before release dispatch.
3. Dispatched: `release.yml` from main with `phase=bootstrap`. Its production job
   rechecks committed HEAD, clean source, main and both independent results after
   approval, after preparation before tagging, and immediately before push; it retains
   semantic-release version selection, and publishes only the validated
   Abstractions snapshot. This selected `1.0.0` and created `v1.0.0`, then
   `dotnet nuget push` returned 403: "The specified API key is invalid, has
   expired, or does not have permission to access the specified package."
   The [failed run](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39055956370)
   left no public package or GitHub release. The trusted-publishing policy applies
   only to `release.yml`, so recovery is now in that workflow: dispatch from main
   with `phase=bootstrap` and `recovery_version=1.0.0` after its repair commit
   passes the independent gates. Recovery rebuilds the original tagged source,
   which must be a green ancestor of current main. An ordinary new-release
   dispatch would find the existing tag and cannot complete `1.0.0`.
4. Download/inspect the published package and compile the isolated decorated
   consumer using source `https://api.nuget.org/v3/index.json`, proving the
   packaged analyzer loads. Record the registry and consumer evidence.
5. In the owning Builds checkout, preserve current work and prior audit data;
   add the verified published version/property and Abstractions package entry,
   commit the reviewed catalog declaration, then perform the complete audit
   refresh documented in `Tools/README.md`. Preserve unrelated selected versions
   and historical observations. Run its catalog/audit validators and fixture
   suites, integrate the changes, and record the revision.

Acceptance for actual publication, public-feed consumption, and owning Builds
integration remains incomplete until those steps have evidence. No read-only
`references/` checkout or gitlink is changed by this work.

## Review-loop correction details

- Direct publication now enforces the exact committed-source policy, including
  refusal of non-Git directories, wrong HEAD/branch and uncommitted source.
- Registry indexes containing blank, whitespace, partial or non-version strings
  fail closed. Ordinary publication retains strict duplicate rejection.
- Recovery uses bootstrap staging, downloads and validates an existing public
  package, compares its consumer content with the tagged build, and consumer-tests
  the downloaded bytes before GitHub completion. Only repository signatures and
  generated core-properties metadata are excluded from content comparison.
  Recovery requires the existing tag to remain the exact green current main.
- An independent real `dotnet pack --no-build` of the same source produced
  identical consumer content under the recovery comparison (temporary package:
  `/tmp/mcpcli-4-6-recovery-repack.lSxts1`).
- Local synthetic tests and workflows cover source checks at the post-prepare
  tagging boundary and final publication boundary. Live committed-source checks,
  tag/publication and registry proof remain pending parent review/integration.

## Final review corrections and checks

Both review passes are triaged in the spec. All surviving findings were patched;
none were deferred. Receipts bind exact package bytes to preparation HEAD and
clean source before/after preparation. Positive preparation-to-publication and
stale/dirty-source rejection fixtures ran. Consumer restore explicitly overrides
MSBuild source/cache properties and directory imports. Recovery propagates its
validated phase, and regression fixtures protect generated metadata and latest
workflow ordering.

Final local checks: 35/35 release tests, Abstractions 20/20, Analyzers 19/19,
real preparation/consumer analyzer proof, four-workflow actionlint, shell syntax
and git diff --check pass. Local preparation is explicitly uncommitted-source
proof only and its receipt cannot authorize publication. Production rebuilds
from the reviewed committed SHA.

Pinned commitlint command `npx --no -- commitlint --verbose --edit
/tmp/mcpcli-4-6-commit.txt` passed with 0 problems and 0 warnings for the exact
message `feat(release): isolate and harden bootstrap package publication`.

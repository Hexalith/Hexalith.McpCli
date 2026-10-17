# Story 4.6 bootstrap verification

## State

Implementation, publication, public-feed proof and owning Builds integration
completed on 2026-10-17. The story is **ready for review**.
Credentials are excluded from this evidence.

- Starting committed source: `04178de98f30b0c5541f7efb978e9b9acc8e8c1d` on `main`.
- Reviewed implementation commit SHA: `d9f822d64f7afa9bd51ca1698f5051147b86b554`, pushed to `main`.
- Exact-source bootstrap push run: [39052313304](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39052313304), success.
- Exact-source commitlint push run: [39052313562](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39052313562), success.
- Full CI push run: [39052313593](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39052313593), success; bootstrap release does not require it.
- Production release run: [39055956370](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39055956370), dispatched from exact `main` SHA with `phase=bootstrap`. Both source checks, preparation and package validation passed; NuGet rejected the push with HTTP 403.
- Selected version: `1.0.0`; tag [`v1.0.0`](https://github.com/Hexalith/Hexalith.McpCli/tree/v1.0.0) points to the reviewed commit. [GitHub release](https://github.com/Hexalith/Hexalith.McpCli/releases/tag/v1.0.0) is complete.
- Prepared production package SHA-256 before rejected push: `7779b0bd465e2013a720d799bebf17edd99f4da2910715b1c56327b64b840a92` (workflow log; not a published-package hash).
- Trusted-publishing repair commit: `e3a3f05c1c3bb6f0166f4e6722706afef609a6fe`, pushed to `main`; exact-source [bootstrap run 39057525398](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39057525398) and [commitlint run 39057525597](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39057525597) succeeded.
- Trusted recovery [run 39057687505](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39057687505) passed the new-main gate, rebuilt/consumer-tested the original tag, obtained a temporary key from NuGet OIDC, and received HTTP 201 from `dotnet nuget push`. Prepared pushed package SHA-256: `870f44526ab201f0ed631c4994bc2d813b36dbc4df6fde60b95792dbd5c2c9b0`. Its immediate public download returned 404 while NuGet processing was pending, so GitHub release completion was skipped.
- Final trusted recovery [run 39058088252](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39058088252) succeeded after NuGet listed the version. It detected the existing package, performed **zero** pushes, compared and consumer-tested downloaded public bytes, then completed the GitHub release.
- [NuGet package `Hexalith.McpCli.Abstractions` 1.0.0](https://www.nuget.org/packages/Hexalith.McpCli.Abstractions/1.0.0) and [flat-container download](https://api.nuget.org/v3-flatcontainer/hexalith.mcpcli.abstractions/1.0.0/hexalith.mcpcli.abstractions.1.0.0.nupkg) are public. Downloaded signed package SHA-256: `1bd30a88863b07a30c1d3ba9985f588c2d30e0bbb08f16a459258a8eea12e224` (37,622 bytes); NuGet's signature makes this differ from the pushed snapshot hash.
- Independent fresh consumer restore/build from `https://api.nuget.org/v3/index.json` passed with one `MCPCLI001` warning, zero errors and no analyzer-loading diagnostics. Local output directory: `/tmp/mcpcli-public-4-6-yk4fb5by/consumer`.
- Owning Builds catalog declaration commit: `650de630bc693e09f0bca0324a71f14ad1304a69`; revision-bound audit commit: `eeab884dead9e5da859d9cda57a028fcfca433ae`. Both are pushed to [Builds main](https://github.com/Hexalith/Hexalith.Builds/commits/main); the exact-head [Commitlint run 39059337691](https://github.com/Hexalith/Hexalith.Builds/actions/runs/39059337691) succeeded.
- Complete audit refresh observed NuGet.org listing `Hexalith.McpCli.Abstractions` `1.0.0`, added exactly one package and `hexalith-mcpcli` family, preserved all 306 prior selected versions and prior package/family historical entries. Central catalog validation passed for 307 entries; authoritative catalog tests passed for 50 identities and 3 shared versions; committed audit validation passed for 307 packages, 148 families and one source. Generator and validator suites passed 115 and 103 scenarios, respectively.

## Local verification

```sh
python3 -m unittest discover -s scripts/tests -p 'test_bootstrap_release.py'
```

Passes 38 test methods with synthetic packages, a stub registry, a stub `dotnet`
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
actionlint .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/release.yml
bash -n scripts/release-prepare.sh scripts/release-preflight.sh scripts/release-publish.sh scripts/smoke-bootstrap-consumer.sh
git diff --check
```

All pass. Git reports pre-existing missing commit-graph warnings without affecting
the successful whitespace check.

## Publication and upstream integration

The `gh` CLI is authenticated; the independent owning checkout is
`/home/administrator/projects/hexalith/builds`. The prior organization
`NUGET_API_KEY` secret was rejected by NuGet;
its value has not been inspected or recorded locally. The user supplied an
active, organization-owned nuget.org trusted-publishing policy for GitHub
repository `Hexalith/Hexalith.McpCli`, workflow `release.yml`, environment
`production`, with push scope for `*`. The GitHub owner/repository immutable IDs
match the policy. The revised workflow requests a short-lived key via OIDC;
`NuGet/login` succeeded with the policy creator username `jpiquot`.

1. Completed: review, pinned commitlint validation, commit and main push at
   `d9f822d64f7afa9bd51ca1698f5051147b86b554`.
2. Completed: latest successful **push** runs of `bootstrap-package.yml` and
   `commitlint.yml` for that exact main SHA. A live source guard invocation also
   verified both runs and current main before release dispatch.
3. Completed: `release.yml` from main with `phase=bootstrap`. Its production job
   rechecks committed HEAD, clean source, main and both independent results after
   approval, after preparation before tagging, and immediately before push; it retains
   semantic-release version selection, and publishes only the validated
   Abstractions snapshot. This selected `1.0.0` and created `v1.0.0`, then
   `dotnet nuget push` returned 403: "The specified API key is invalid, has
   expired, or does not have permission to access the specified package."
   The [failed run](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39055956370)
   left no public package or GitHub release. The trusted-publishing policy applies
   only to `release.yml`, so recovery moved into that workflow. The first trusted
   recovery pushed the validated tagged package. Its 404 during NuGet processing
   left GitHub completion pending. The second recovery verified the public package
   without another push and completed the release.
4. Completed: downloaded/validated the signed public package and compiled the
   isolated decorated consumer using `https://api.nuget.org/v3/index.json`.
5. Completed: preserved prior audit at
   `/home/administrator/projects/hexalith/builds/artifacts/mcpcli-bootstrap-y0zlk7bj/package-version-audit.before-refresh.json`,
   added the verified `1.0.0` property/package declaration, and committed the
   catalog at `650de630bc693e09f0bca0324a71f14ad1304a69`. The complete audit
   refresh from that committed revision and its regression checks passed. The
   generated audit was committed at `eeab884dead9e5da859d9cda57a028fcfca433ae`
   and validated again after commit; both commits were pushed to Builds main.

All four acceptance criteria are met. The public package, independent consumer,
and owning Builds revision are linked above.
No read-only `references/` checkout or gitlink is changed by this work.

## Review-loop correction details

- Direct publication now enforces the exact committed-source policy, including
  refusal of non-Git directories, wrong HEAD/branch and uncommitted source.
- Registry indexes containing blank, whitespace, partial or non-version strings
  fail closed. Ordinary publication retains strict duplicate rejection.
- Recovery uses bootstrap staging, downloads and validates an existing public
  package, compares its consumer content with the tagged build, and consumer-tests
  the downloaded bytes before GitHub completion. Only repository signatures and
  generated core-properties metadata are excluded from content comparison.
  Recovery requires the existing remote tag to identify a green ancestor of
  current main and verifies its workflow code at current green main.
- An independent real `dotnet pack --no-build` of the same source produced
  identical consumer content under the recovery comparison (temporary package:
  `/tmp/mcpcli-4-6-recovery-repack.lSxts1`).
- Local synthetic tests and workflows cover source checks at the post-prepare
  tagging boundary and final publication boundary. Live committed-source,
  tag/publication and public registry proof appear above.

## Final review corrections and checks

Both review passes are triaged in the spec. All surviving findings were patched;
none were deferred. Receipts bind exact package bytes to preparation HEAD and
clean source before/after preparation. Positive preparation-to-publication and
stale/dirty-source rejection fixtures ran. Consumer restore explicitly overrides
MSBuild source/cache properties and directory imports. Recovery propagates its
validated phase, and regression fixtures protect generated metadata and latest
workflow ordering.

Final local checks: 38/38 release tests, Abstractions 20/20, Analyzers 19/19,
real preparation/consumer analyzer proof, three-workflow actionlint, shell syntax
and git diff --check pass. Local preparation is explicitly uncommitted-source
proof only and its receipt cannot authorize publication. Production rebuilds
from the reviewed committed SHA.

Pinned commitlint command `npx --no -- commitlint --verbose --edit
/tmp/mcpcli-4-6-commit.txt` passed with 0 problems and 0 warnings for the exact
message `feat(release): isolate and harden bootstrap package publication`.

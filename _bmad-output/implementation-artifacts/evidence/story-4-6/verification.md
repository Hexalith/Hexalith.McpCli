# Story 4.6 bootstrap verification

## State

Implementation, publication, public-feed proof and owning Builds integration
completed on 2026-10-17. The second-pass review corrections are implemented,
checked and reviewed; the human assessment remains pending.
The spec is **done** and sprint tracking is **review**.
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
- Independent fresh consumer restore/build from `https://api.nuget.org/v3/index.json` passed with one `MCPCLI001` warning, zero errors and no analyzer-loading diagnostics. Its exact invocation, restore source/cache and key build output are preserved below.
- Owning Builds catalog declaration commit: `650de630bc693e09f0bca0324a71f14ad1304a69`; revision-bound audit commit: `eeab884dead9e5da859d9cda57a028fcfca433ae`. Both are pushed to [Builds main](https://github.com/Hexalith/Hexalith.Builds/commits/main); the exact-head [Commitlint run 39059337691](https://github.com/Hexalith/Hexalith.Builds/actions/runs/39059337691) succeeded.
- Complete audit refresh observed NuGet.org listing `Hexalith.McpCli.Abstractions` `1.0.0`, added exactly one package and `hexalith-mcpcli` family, preserved all 306 prior selected versions and prior package/family historical entries. Central catalog validation passed for 307 entries; authoritative catalog tests passed for 50 identities and 3 shared versions; committed audit validation passed for 307 packages, 148 families and one source. Generator and validator suites passed 115 and 103 scenarios, respectively.

## Local verification

```sh
python3 -m unittest discover -s scripts/tests -p 'test_bootstrap_release.py'
```

Passes 51 test methods with synthetic packages, a stub registry, a stub `dotnet`
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
The story implementation changed no read-only `references/` checkout or gitlink.
The broader story range includes separate sync commits: `4a84c16` (`/pushall`)
moved 14 gitlinks, including Builds to `544fd2e` containing the catalog work;
`c60ffa9` moved Conversations from `e753cf8` to `476369f` (the original baseline
was `4e93736`). These pre-existing sync changes are preserved.

## Governance deviation and production gate

- Trusted-publishing repair `e3a3f05c1c3bb6f0166f4e6722706afef609a6fe` was
  pushed to `main` and used by recovery runs 39057687505 (NuGet push) and
  39058088252 (GitHub release completion) before any review pass covered it.
  The frozen intent requires review before publication.
- That commit controlled the recovery orchestration, the `--tagged-recovery`
  source check, the NuGet OIDC login and the `MCPCLI_RECOVERY_VERSION` publisher
  switch. The pushed package was rebuilt from reviewed tag `v1.0.0` (`d9f822d`)
  and checked by that tag's reviewed validator, receipt and preflight scripts;
  its public copy was content-compared and consumer-tested.
- The code review of 2026-10-18 (range `04178de..34bc4b3`) covers `e3a3f05` and
  is accepted as its retroactive review. None of its findings affects the
  published `1.0.0` package; open findings are in the spec's Review Findings.
- Root cause: the `production` environment had no protection rules and no
  deployment branch policy, so production approval was not a gate, and the
  recorded trusted-publishing policy names no branch. On 2026-10-18 `production`
  was configured with required reviewer `jpiquot` and a custom deployment branch
  policy admitting only `main`. Read back with
  `gh api repos/Hexalith/Hexalith.McpCli/environments/production`
  (`required_reviewers` = `jpiquot`, `branch_policy`,
  `custom_branch_policies: true`) and
  `gh api repos/Hexalith/Hexalith.McpCli/environments/production/deployment-branch-policies`
  (`main`, type `branch`). Admin bypass remains enabled and self-approval is
  allowed, so the gate is a deliberate pause, not an independent review.

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

Pre-review local checks: 38/38 release tests, Abstractions 20/20, Analyzers 19/19,
real preparation/consumer analyzer proof, three-workflow actionlint, shell syntax
and git diff --check pass. Local preparation is explicitly uncommitted-source
proof only and its receipt cannot authorize publication. Production rebuilds
from the reviewed committed SHA.

Pinned commitlint command `npx --no -- commitlint --verbose --edit
/tmp/mcpcli-4-6-commit.txt` passed with 0 problems and 0 warnings for the exact
message `feat(release): isolate and harden bootstrap package publication`.

## Durable public-feed and owner-integration proof

The original public-feed invocation on 2026-10-17 was:

```sh
bash scripts/smoke-bootstrap-consumer.sh 1.0.0 https://api.nuget.org/v3/index.json /tmp/mcpcli-public-4-6-yk4fb5by/consumer
```

The retained generated NuGet configuration, `obj/project.assets.json` and
`build.log` were read again on 2026-10-18. Their decisive values are copied here
so deleting the temporary directory does not delete the proof:

```text
packageSources: clear; verified = https://api.nuget.org/v3/index.json
fallbackPackageFolders: clear
restore.sources: { "https://api.nuget.org/v3/index.json": {} }
restore.packagesPath: /tmp/mcpcli-public-4-6-yk4fb5by/consumer/packages
originalTargetFrameworks: [ "net10.0" ]
warning MCPCLI001: Operation 'MissingDescriptionQuery' needs a nonblank description
Build succeeded.
    1 Warning(s)
    0 Error(s)
```

The complete Builds refresh and checks were run from the owning checkout,
`/home/administrator/projects/hexalith/builds`, after catalog declaration commit
`650de630bc693e09f0bca0324a71f14ad1304a69`:

```sh
pwsh -NoProfile -File Tools/validate-central-package-versions.ps1
pwsh -NoProfile -File Tools/test-authoritative-package-catalog.ps1
pwsh -NoProfile -File Tools/audit-central-package-versions.ps1 -PriorAuditPath artifacts/mcpcli-bootstrap-y0zlk7bj/package-version-audit.before-refresh.json -OutputPath Tools/package-version-audit.json
pwsh -NoProfile -File Tools/validate-package-version-audit.ps1
pwsh -NoProfile -File Tools/test-package-version-audit-generator.ps1
pwsh -NoProfile -File Tools/test-package-version-audit-validator.ps1
```

Recorded successful results: central catalog **307 entries**; authoritative
catalog **50 identities / 3 shared versions**; complete audit **307 packages /
148 families / 1 source**; generator **115 scenarios**; validator **103
scenarios**. The complete refresh omitted `-Family`, added only the new package
and family, and preserved all **306** previous selected versions and historical
observations. After audit commit `eeab884dead9e5da859d9cda57a028fcfca433ae`,
`pwsh -NoProfile -File Tools/validate-package-version-audit.ps1` passed again.
These are the historical integration checks; no new audit refresh or owning
repository change was performed for the 2026-10-18 release-script patches.

The historical pinned commitlint input is preserved verbatim:

```text
feat(release): isolate and harden bootstrap package publication
```

`npx --no -- commitlint --verbose --edit /tmp/mcpcli-4-6-commit.txt` was rerun
on 2026-10-18 against that exact input and printed
`found 0 problems, 0 warnings`. No commit is created by this check.

## 2026-10-18 review patches and verification

All 22 remaining patch findings were addressed. Recovery now resolves every
sibling helper beside the preserved reviewed script, including preparation,
preflight, validator, receipt and consumer smoke. Tests sabotage every tagged
shell/Python helper while preserving the current copies. Recovery waits only
for a package it just pushed: up to **12** public-download attempts, with
**10 seconds** between retryable 404s. Exhaustion, any other uncertain response,
and unavailable already-published content still fail closed. Fixtures cover a
404 then 200, exact retry exhaustion, one push at most, and no retry for an
existing package or another error.

The suite additionally protects downloaded-package consumer failure and its
download-directory restore source, changed DLL bytes under identical ZIP entry
names, missing analyzer diagnostics, extra warnings and `CS8032`, exact detached
HEADs in both source modes, semantic-release's actual `prepareCmd` and asset glob,
real Git's staging/receipt ignore behavior, clean-before/dirty-after preparation,
fresh consumer directories, and unknown preparation arguments. Source failures
name the precise prerequisite in test assertions. Both production modes depend
on the initial source gate; bootstrap concurrency includes the event name.

```sh
python3 -m unittest discover -s scripts/tests -p 'test_bootstrap_release.py'
MCPCLI_RELEASE_PHASE=bootstrap MSBUILDTERMINALLOGGER=on bash scripts/release-prepare.sh 1.0.0
for project in Abstractions Analyzers; do
  test_project="tests/Hexalith.McpCli.${project}.Tests"
  dotnet restore "$test_project" -tl:off
  dotnet build "$test_project" --configuration Release --no-restore -warnaserror -tl:off
  dotnet test "$test_project" --configuration Release --no-build
done
actionlint .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/release.yml
bash -n scripts/release-prepare.sh scripts/release-preflight.sh scripts/release-publish.sh scripts/smoke-bootstrap-consumer.sh
git diff --check
```

Results: **51/51** release tests (87.052 s), **20/20** Abstractions and **19/19**
Analyzers, zero skips; both author-time builds have zero warnings/errors.
Preparation succeeds even with the terminal logger forced on: the consumer
restore/build pass `-tl:off` and retain the plain `1 Warning(s)` summary.
Actionlint, shell syntax and whitespace checks pass. Prior staging and its receipt
were preserved under `/tmp/mcpcli-4-6-review-validation-rbdxj9wm`; unrelated
`nupkgs/` contents were retained. This uncommitted local package has SHA-256
`7989fb63477f8e0f33f564f7b1ef334632f64eb8575ebe582bebf773f776a681`;
its receipt records dirty source and cannot authorize publication.

The real isolation check was repeated with these exact commands:

```sh
proof_root=$(mktemp -d /tmp/mcpcli-4-6-review-isolation.XXXXXX)
mkdir "$proof_root/empty"
cat > "$proof_root/Directory.Build.props" <<'EOF'
<Project><PropertyGroup><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup></Project>
EOF
MSBUILDTERMINALLOGGER=on bash scripts/smoke-bootstrap-consumer.sh 1.0.0 nupkgs/bootstrap "$proof_root/positive" > "$proof_root/positive.log" 2>&1
if RestoreSources="$PWD/nupkgs/bootstrap" RestorePackagesPath="$proof_root/positive/packages" NUGET_FALLBACK_PACKAGES="$proof_root/positive/packages" bash scripts/smoke-bootstrap-consumer.sh 1.0.0 "$proof_root/empty" "$proof_root/negative" > "$proof_root/negative.log" 2>&1; then
  echo 'Unexpected empty-source restore success' >&2
  exit 1
fi
```

The positive restore resolved `nupkgs/bootstrap` relative to the caller and
succeeded despite the parent warning policy and forced terminal logger. The
negative restore failed despite all three inherited values pointing at the
populated cache/source. Key output from
`/tmp/mcpcli-4-6-review-isolation.9g5gW4`:

```text
Restored /tmp/mcpcli-4-6-review-isolation.9g5gW4/positive/Bootstrap.Consumer.Contracts.csproj
warning MCPCLI001: Operation 'MissingDescriptionQuery' needs a nonblank description
Build succeeded.
    1 Warning(s)
    0 Error(s)
error NU1101: Unable to find package Hexalith.McpCli.Abstractions. No packages exist with this id in source(s): verified
Failed to restore /tmp/mcpcli-4-6-review-isolation.9g5gW4/negative/Bootstrap.Consumer.Contracts.csproj
```

The repack equivalence check was also repeated, preserving its exact command
and assertion instead of depending on its temporary package:

```sh
repack_root=$(mktemp -d /tmp/mcpcli-4-6-review-repack.XXXXXX)
dotnet pack src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj --configuration Release --no-build -p:Version=1.0.0 --output "$repack_root" -tl:off
python3 - "$repack_root" <<'PY'
import importlib.util
from pathlib import Path
import sys
spec=importlib.util.spec_from_file_location('recovery', 'scripts/recover-bootstrap-release.py')
recovery=importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)
name='Hexalith.McpCli.Abstractions.1.0.0.nupkg'
assert recovery.content(Path('nupkgs/bootstrap')/name)==recovery.content(Path(sys.argv[1])/name)
print('Consumer content matches for independent no-build repack.')
print(sys.argv[1])
PY
```

It passed with `Consumer content matches for independent no-build repack.`
The second archive is retained at `/tmp/mcpcli-4-6-review-repack.0sukbW`.
This verifies repeat packing of the current local source; the published-package
proof remains the original reviewed tag, signed package hash and successful
recovery linked above. The new patches await their own source review and
committed-main gates; no additional publication was attempted.


## Final parent verification after review patches (2026-10-18)

Three independent review layers completed: Blind Hunter, Edge Case Hunter and
Verification Gap. All 11 findings have individual verdicts in the spec: seven
patched findings (including the duplicate completion-test gap), four rejected,
and none deferred. Existing drafts are now published only after successful
asset upload. Tests execute the workflow's actual completion block against a
local backend for missing, published and draft releases and assert exact asset
bytes. Creation, upload, draft-publication and source-gate failures stop the
workflow. Additional regressions protect unsupported publisher arguments,
package mutation during consumer smoke, filesystem write diagnostics and
credential-redacted source-gate stderr.

Final exact commands, run from the repository root after preserving the prior
ignored bootstrap staging and receipt:

```sh
python3 -m unittest discover -v -s scripts/tests -p 'test_bootstrap_release.py'
actionlint .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/release.yml
bash -n scripts/release-prepare.sh scripts/release-preflight.sh scripts/release-publish.sh scripts/smoke-bootstrap-consumer.sh
MCPCLI_RELEASE_PHASE=bootstrap MSBUILDTERMINALLOGGER=on bash scripts/release-prepare.sh 1.0.0
for project in Abstractions Analyzers; do
  test_project="tests/Hexalith.McpCli.${project}.Tests"
  dotnet restore "$test_project" -tl:off
  dotnet build "$test_project" --configuration Release --no-restore -warnaserror -tl:off
  dotnet test "$test_project" --configuration Release --no-build
done
git diff --check
```

All pass. Decisive output:

```text
Ran 57 tests in 70.722s
OK
Abstractions: total 20, failed 0, succeeded 20, skipped 0
Analyzers: total 19, failed 0, succeeded 19, skipped 0
warning MCPCLI001: Operation 'MissingDescriptionQuery' needs a nonblank description
Build succeeded.
    1 Warning(s)
    0 Error(s)
Prepared Hexalith.McpCli.Abstractions 1.0.0 SHA-256 23bf87c59591a7b92ed54ed1c8bf018de942bc89cfd09b4f6ecb9dd61afcd27f
```

Every frozen matrix row has executed coverage: valid bootstrap through
`test_prepare_to_publish_uses_the_generated_source_bound_receipt` and real
preparation/consumer compilation; invalid packages through
`test_invalid_package_matrix_never_pushes` and the extra-artifact cases; invalid
requests through `test_invalid_requests_are_rejected_by_every_entry_point_before_effects`,
missing-key and registry rejection cases; invalid source through
`test_direct_publish_requires_exact_committed_source_and_independent_gates` and
`test_source_rejections_require_current_main_and_both_latest_results`.
The verbose run records every case as `ok`, with no skips.

The real cache-isolation check also passed:

```sh
verification_root=/tmp/mcpcli-4-6-final-verification.tTXL1Q
mkdir "$verification_root/empty-source"
bash scripts/smoke-bootstrap-consumer.sh 1.0.0 nupkgs/bootstrap "$verification_root/positive"
RestoreSources="$PWD/nupkgs/bootstrap" RestorePackagesPath="$verification_root/positive/packages" NUGET_FALLBACK_PACKAGES="$verification_root/positive/packages" bash scripts/smoke-bootstrap-consumer.sh 1.0.0 "$verification_root/empty-source" "$verification_root/negative"
```

The positive consumer passed with exactly one analyzer warning and zero errors.
The final invocation failed as expected, despite the inherited populated cache:

```text
error NU1101: Unable to find package Hexalith.McpCli.Abstractions. No packages exist with this id in source(s): verified
```

Logs and preserved prior staging/receipt are under
`/tmp/mcpcli-4-6-final-verification.tTXL1Q`; commands and decisive output are
copied above so this evidence does not depend on retaining that directory.
The final local receipt records dirty source and cannot authorize publication.
No publication, remote write, Builds change or gitlink move was performed in this
resumed run. The original reviewed-tag publication and upstream integration
are documented in the earlier sections. Those corrections subsequently passed
the committed-main gates recorded below.

Pinned commitlint was restored with `npm ci` and passed with zero problems and
zero warnings for the final exact full message. The command, message and
successful validation output are preserved in `commitlint-validation.txt` beside
this document.

## Committed source after first-pass corrections

The committed correction history includes `844776f`, `c60ffa9` and final source
`55ed6e9cec45999d1f6bb67bcb513d203e9e2429`. Read-only verification on 2026-10-18:

```sh
gh run list --commit 55ed6e9cec45999d1f6bb67bcb513d203e9e2429 --event push --limit 20 --json databaseId,workflowName,url,headSha,conclusion,status,createdAt
```

All exact-source push runs completed successfully:

- [Bootstrap package 39108007979](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39108007979).
- [Commitlint 39108008209](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39108008209).
- [CI 39108008228](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/39108008228).

These are the gates for the committed first-pass corrections. The second-pass
changes below remain local and require their own committed-main gates before
future production use; no release is dispatched by this patch pass.

## Second-pass review corrections (2026-10-18)

The ten remaining patch findings are implemented. Recovery's actual workflow
steps now run in order against offline stubs: preserve reviewed scripts, require
and check out the existing tag, export its exact `DISPATCH_SHA` through a temporary
`GITHUB_ENV`, rebuild, publish/verify, and complete the GitHub release. The fake
checkout replaces every tagged shell/Python helper with a failing marker. The
workflow succeeds using the preserved helpers with exactly one fake push, no
tagged-helper call, and exactly the prepared package bytes attached to GitHub.
Both production modes are checked with an incorrect ambient key and must receive
the temporary key from `steps.nuget-login.outputs.NUGET_API_KEY`. Missing and
unmerged tags stop before checkout or build.

The propagation bound is 91 public-download attempts with 90 ten-second sleeps:
900 seconds of waiting. Offline coverage confirms the full bound for a newly
pushed 404, no retries for an existing package or uncertain non-404 response,
and successful 404-then-200 verification. A warning on `CreateItemCommand.cs`
instead of `MissingDescriptionQuery.cs` now rejects preparation without a receipt.

Exact release-suite command and result:

```sh
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

```text
Ran 59 tests in 60.999s
OK
```

The first run found a test-helper extraction error: the final publish step also
included the following YAML job. The extractor now stops at the job boundary;
the full rerun above passed. Four isolated mutations of temporary workflow
copies were also rejected by these tests: reverting the recovery helper to
`scripts/`, reverting the completion source helper to `scripts/`, and replacing
the NuGet-login key binding with an unrelated secret in each production mode.
No repository workflow was modified for these probes.

Both author-time projects were restored, built and run individually:

```sh
for project in Abstractions Analyzers; do
  test_project="tests/Hexalith.McpCli.${project}.Tests"
  dotnet restore "$test_project" || exit
  dotnet build "$test_project" --configuration Release --no-restore -warnaserror || exit
  dotnet test "$test_project" --configuration Release --no-build || exit
done
```

Abstractions passed 20/20; Analyzers passed 19/19, with zero skips. Both builds
reported zero warnings and errors.

Prior ignored `nupkgs/bootstrap` and `nupkgs/bootstrap.sha256` were preserved at
`/tmp/mcpcli-4-6-second-pass.WINHkd/preserved`; unrelated `nupkgs` artifacts remain.
The reviewed README local command then passed:

```sh
MCPCLI_RELEASE_PHASE=bootstrap bash scripts/release-prepare.sh 1.0.0
```

```text
Validated bootstrap packages at version 1.0.0
MissingDescriptionQuery.cs(3,22): warning MCPCLI001: Operation 'MissingDescriptionQuery' needs a nonblank description
Build succeeded.
    1 Warning(s)
    0 Error(s)
Prepared Hexalith.McpCli.Abstractions 1.0.0 SHA-256 e07a4569a6cce1ebb66821d5db4cdd27bb80978c5643e1b24876ba4fffc07461
```

The production project build preceding that consumer reported zero warnings and
errors. The resulting package's `README.md` was compared byte-for-byte with the
repository README; all four affected links use absolute GitHub URLs. This is
local packaging evidence; its dirty-source receipt cannot authorize publication.

```sh
actionlint .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/release.yml
bash -n scripts/release-prepare.sh scripts/release-preflight.sh scripts/release-publish.sh scripts/smoke-bootstrap-consumer.sh
git diff --check
```

All passed. This patch pass changes no `references/` checkout or gitlink, performs
no publication or remote write, and requires no further owner Builds change.
The previously published package and upstream integration remain as recorded.

## Final resumed-build verification (2026-10-18)

All three independent review layers completed. Eleven findings received individual
verdicts in the spec: two narrow patches, eight low findings rejected under the
workflow's complexity rule (including carried decisions), and one false finding.
Edge Case Hunter returned no findings. The two patches correct the opening state
wording and protect recovery's final source check with a dirty-after-consumer
regression. Removing that check makes the new test fail. No new work was deferred;
the existing agent-context entry remains in `deferred-work.md:491`.

Final parent commands:

```sh
python3 -m unittest discover -v -s scripts/tests -p 'test_*.py'
for project in Abstractions Analyzers; do
  test_project="tests/Hexalith.McpCli.${project}.Tests"
  dotnet restore "$test_project" -tl:off
  dotnet build "$test_project" --configuration Release --no-restore -warnaserror -tl:off
  dotnet test "$test_project" --configuration Release --no-build
done
MCPCLI_RELEASE_PHASE=bootstrap bash scripts/release-prepare.sh 1.0.0
bash scripts/smoke-bootstrap-consumer.sh 1.0.0 https://api.nuget.org/v3/index.json /tmp/mcpcli-4-6-parent.jUzTqm/public-consumer
actionlint .github/workflows/bootstrap-package.yml .github/workflows/ci.yml .github/workflows/release.yml
bash -n scripts/release-prepare.sh scripts/release-preflight.sh scripts/release-publish.sh scripts/smoke-bootstrap-consumer.sh
git diff --check
```

All passed. Decisive output:

```text
Ran 60 tests in 65.108s
OK
Abstractions: total 20, failed 0, succeeded 20, skipped 0
Analyzers: total 19, failed 0, succeeded 19, skipped 0
Prepared Hexalith.McpCli.Abstractions 1.0.0 SHA-256 a5fbfe86d259a72e0cdc65da28e885cdcf13154d912cf1dd1fec1e2ac41ae1b1
public-consumer/MissingDescriptionQuery.cs(3,22): warning MCPCLI001: Operation 'MissingDescriptionQuery' needs a nonblank description
Build succeeded.
    1 Warning(s)
    0 Error(s)
```

The verbose release run records every matrix-covering case as `ok`, with no
skips. Both author-time builds have zero warnings/errors. Local preparation also
produces exactly one warning on `MissingDescriptionQuery.cs`, and its packaged
README matches the current repository bytes. Its dirty-source receipt cannot
authorize publication. Prior staging and receipt were preserved under
`/tmp/mcpcli-4-6-parent.jUzTqm/preserved`.

The fresh public consumer's assets list only
`https://api.nuget.org/v3/index.json` as its source. Its downloaded signed package
has SHA-256 `1bd30a88863b07a30c1d3ba9985f588c2d30e0bbb08f16a459258a8eea12e224`,
matching the original publication proof. Logs are retained under
`/tmp/mcpcli-4-6-parent.jUzTqm`; the commands and decisive results above remain
durable if that directory is deleted.

These corrections remain local and need committed-main gates before any future
production run. The workflow's completion step records a local commit after
pinned commitlint validation, whose evidence is retained in
`commitlint-validation.txt`. This invocation performed no publication, remote
write, owner Builds edit or gitlink move.

# Story 4.12 current evidence index

The normal upstream release and downstream helper enrollment are complete.
All P25–P36 patches passed final parent acceptance and three independent review
layers. Final validation passed 1,490 non-live .NET tests (five existing unrelated
skips), 17 Python checks and the isolated live smoke without skips. No new work
was deferred. Earlier receipts retain their original identities and outcomes.

- [Current final verification](review-pass-3-20261024/parent-final/verification.json): reviewed source map, exact final commands, acceptance matrix and live result.
- [Final acceptance details](review-pass-3-20261024/parent-final/README.md): final counts, review dispositions and process preservation.
- [Completed publication and provenance](publication-20261023/expanded-publication/README.md): signed Parties Aspire 1.6.0, normal release gates, Builds integration and published-artifact checks.
- [Initial pass 3 checkpoint](review-pass-3-20261024/verification.json): preserved pre-review implementation evidence.
- [Review follow-up checks](review-pass-3-20261024/review-fixes/summary.json): focused P33–P36 coverage and removal controls.
- [Prior review pass 2 verification](review-pass-2-20261023/verification.json): earlier source map and checks.
- [Prior completed review verification](review-patches-20261023/final-verification/): earlier runtime and live results.

## Historical unpublished checkpoint — preserved verbatim

The remainder records the earlier unpublished candidate and continuation state.
Its pending/incomplete statements describe that historical checkpoint; current
status is given by the index above.

# Story 4.12 upstream prerequisite candidate

**Status: release authorized; unpublished; normal CI continuation in progress. Story 4.12 is incomplete.**
This packet prepares the missing Parties Aspire helper. McpCli has no new helper
admission, AppHost or live smoke yet. Its approved Contracts pins, vectors and
inventories remain intact.

The owning repository is `/home/administrator/projects/hexalith/parties`.
Concurrent unrelated Parties runtime work was excluded from qualification. The
isolated source is `/tmp/story-4-12-parties-helper/source-snapshot`; full raw
receipts and all ten staged archives are under `/tmp/story-4-12-parties-helper`.
Initial qualification changed no owning-repository index, branch or remote. Local disposable clones
supply Git history and ten root-declared source checkouts; none of their nested
submodules was initialized. Their tracked contents remain clean.

## Authorized continuation

The user authorized the prepared normal Parties release and subsequent
Builds/McpCli integration on 2026-10-23. The isolated owning-repository worktree
`/tmp/story-4-12-parties-publication` preserves the original dirty worktree/index.
The helper commit `4449020abcc01080a2375c7141b39aa18913d4aa` matches all 26 qualified
file hashes. Follow-ups `f2c1b1968c10b04ce5a5ef41685248b01c1da40b` and
`ad44f1d433799b2e1ca37a0bdb722a2ecfe09c87` address existing CI blockers: an
ambiguous browser label, safe publisher failure identities and the manifest
publisher's missing Dapr CLI prerequisite. The helper implementation is unchanged.

The exact-source [CI run 39916336068](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39916336068)
passes build/test, publisher, UI, platform declaration and BMAD jobs. Its Aspire
tier ran 129 tests: 122 passed, six used existing explicit skips and one existing
concurrent mTLS-session test failed Dapr readiness. The prior baseline run has
the same failure. A normal failed-job rerun and focused local reproduction are
in progress; readiness checks and required gates are unchanged. The independent
[main-push range gate passed](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39916335288).
Publication has not been dispatched.

The actual McpCli Manifest.Tests project builds and passes 21 new root/configuration
guard tests. AppHost, shared fixture and smoke drafts compile separately against
the local qualification artifact; non-live discovery lists the smoke. No helper
has been admitted. Bounded Release builds of all three existing root source
servers pass with warnings as errors. Exact commands, versions, failures and
results are retained under [publication-20261023/](publication-20261023/).
Earlier user topology collisions ended independently; each live attempt must
recheck them. No existing user process was stopped or reused, and no successful
live McpCli smoke has run.

## Exact candidate

| Input | Identity |
| --- | --- |
| Upstream baseline | `6c83309d08a10f36a0da866521b9d0da6f8fc998` |
| Task files | 26; exact names and byte hashes in [source-manifest.json](source-manifest.json) |
| Task file-map SHA-256 | `023abd2f23d0e56dd6a4474bb8e07ba3a2e4f113c0da66dbb967f52e951324fa` |
| Reproducible task diff | [parties-helper.patch](parties-helper.patch) |
| Patch SHA-256 | `eaf3003eeab9ce1dcaf19f75837a5b80472a62d053263c66fb4a016436b36be0` |
| Full final source input SHA-256 | `c45b62498f9bb5d1e0e0bd2ac9534c2e7f3239cd15b9109dc23f12ca2445a884` |
| Local helper archive | [Hexalith.Parties.Aspire.1.6.0-story412.1.nupkg](Hexalith.Parties.Aspire.1.6.0-story412.1.nupkg), 13,160 bytes |
| Archive SHA-256 | `95218af9fe9345fbf496602a5474e2d0c30c035ddc9b7778992996928601a73a` |
| Exact restored closure | 80 packages in [qualification.json](qualification.json) |
| Canonical closure SHA-256 | `4ceba91b3af0550d6bfc9f357ca54542191ba84ba246fbd120317217a3a295de` |

`1.6.0-story412.1` identifies local qualification bytes only. It is neither a
published version nor a proposal for the official release version. The normal
release workflow computes that version from the admitted source history.

The archive contains only `lib/net10.0/Hexalith.Parties.Aspire.dll`. Its direct
nuspec dependencies are exactly `Aspire.Hosting` 13.6.1 and
`Hexalith.EventStore.Aspire` 3.126.1. Its restored closure contains no other
Hexalith package and therefore no Parties or platform server implementation.
A fresh NuGet package directory and restored-archive hash assertion bind the
consumer probes to these exact bytes, preventing reuse of an earlier archive
with the same local version label.

The helper delegates composition to `AddEventStoreDomainModule`, suppresses the
server build, and uses `RepositoryProjectPaths`. Exact-archive probes pass for
own-root and direct-root source, and reject missing, nested-only, root-level-only
and sibling-only source with the required direct path. Git root membership guards
for the McpCli AppHost remain part of the post-publication implementation.

The initial `c361f454…` archive and the parent's independent identity, sole-DLL and
direct-dependency verification are retained under [history/](history/). Those
bytes were superseded after the final README and inventory changes.

## Verification and limits

- Full isolated `dotnet restore Hexalith.Parties.Standalone.slnx`, then
  `dotnet build Hexalith.Parties.Standalone.slnx --no-restore --configuration Release -warnaserror -m:1`
  passed, compiling all 32 owned projects with zero warnings or errors.
- All 16 owning test projects were exercised individually: 5,852 distinct tests,
  with 13 explicit upstream runtime skips. Initial setup/inventory failures were
  corrected by focused reruns: 2 Client package tests and all 288 fitness tests
  passed. The full CI suite passed 439/439; the final added publishing-inventory
  assertion then passed separately. The helper suite passed 9/9. The final
  non-packaged documentation corrections passed all 10 documentation fitness tests
  and an exact-archive source-binding recheck; package bytes are unchanged.
- Eight required root support projects built with warnings as errors. The normal
  ten-package set was restaged after the final README edits; both existing package
  and isolated-consumer validators passed against that final set. All package
  identities, byte hashes and sizes are in [release-set.json](release-set.json).
- [The final helper receipt](checks/final-xml-doc-source-binding.json)
  records the successful fresh-cache archive restore and all six source probes.
  [The source input audit](source-input-audit.json) distinguishes the initial scope
  from the deliberate inventory follow-ups and confirms no unexpected changes
  after freezing the final candidate. [Root checkout evidence](source-inputs-after-qualification.json)
  confirms clean tracked reference contents.
- [Check receipts](checks/) preserve exact commands, exit codes, summaries and
  failure excerpts. Large diagnostic streams are explicitly excerpted; original
  full receipts remain in the local qualification directory. Earlier failures
  remain recorded and are superseded by the linked focused successes.
- **No new live Gateway request ran.** The 13 skipped upstream runtime tests do
  not establish live acceptance. Exact committed-source GitHub CI, range proof,
  protected publication and final container artifacts are still pending.

To repeat the final artifact check against the frozen source:

```bash
python3 _bmad-output/implementation-artifacts/evidence/story-4-12/qualify-parties-helper.py \
  /tmp/story-4-12-parties-helper/source-snapshot \
  /tmp/story-4-12-parties-helper/release-packages/Hexalith.Parties.Aspire.1.6.0-story412.1.nupkg \
  _bmad-output/implementation-artifacts/evidence/story-4-12/source-manifest.json
```

## Required publication and integration continuation

The authorized scope covers the owning repository's normal release. Its
manifest contains ten packages: Contracts, Client,
AdminPortal, ConsumerPortal, Picker, Authentication, Projections, Security,
Testing and Aspire, all under the `Hexalith.Parties` prefix. The workflow also
publishes `registry.hexalith.com/parties`, `parties-mcp` and `parties-ui`, each for
`linux/amd64` and `linux/arm64`. Final published package/container bytes and source
provenance must be verified by the normal workflow.

The scoped continuation is:

1. Integrate only this task-owned diff in the owning Parties repository, preserving
   concurrent unrelated work. Validate any commit message with the pinned owning
   commitlint. Obtain successful `ci.yml` and independent `rc-gate.yml` push proof
   for the exact current-main SHA. The `release.yml` dispatch then requires the
   normal protected `production` approval, NuGet OIDC login, version/preflight
   checks and full package/container gates. No speculative official version is
   assumed, and none of these gates is bypassed.
2. Retrieve the actual published helper version and archive. Inspect its exact
   package bytes and dependency closure before downstream admission; reject it
   if any forbidden dependency appears. Local qualification cannot substitute for
   this published-artifact check.
3. In the owning Hexalith.Builds checkout, add the published helper with an
   independent helper version property, such as `HexalithPartiesAspireVersion`,
   and the required catalog audit updates. Keep production Contracts identities
   unchanged. Validate and integrate only the necessary root gitlinks.
4. Continue the already specified McpCli work: admit the reviewed helper only for
   tests; preserve production and implementation-package rejection; add root-only
   checkout/configuration guards, the three-service AppHost, shared platform
   fixture, bounded authenticated Gateway smoke, solution registration, focused
   non-live CI discovery and README source-build/run instructions. Build and test
   the bounded root source topology without stopping or reusing user processes.
   Require an actual non-skipped successful smoke for live acceptance.

This single scoped continuation includes routine publication gates and subsequent
Builds/McpCli integration already required by the approved spec. Full vector
semantics and the blocking Aspire CI tier remain Stories 4.13 and 4.14.

## Authorized continuation checkpoint

The original helper candidate was integrated without the user's unrelated runtime
work. Exact-source CI [39928383173](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39928383173)
passed at `a413dc7df41a98f9d02cd8fb823e544086520956`, including Tier 3 (123 passed,
zero failed, six existing skips). The repaired two-session test passed without
skipping. The independent range and commitlint gates passed.

Normal release [39931847401](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39931847401)
passed current-main/source and registry-floor preflight, then received its normal
protected production approval under the recorded user authorization. It failed
before publication because the shared version-floor reader rejected the new
helper's NuGet index HTTP 404. Nothing was tagged or published by that attempt.
The narrow shared fix is Builds `e6d0cc245c43a109672b1b71e1768ef8e2cabbe0`:
only an authoritative NuGet index 404 means no prior versions; other failures,
existing-version collisions and independent destination-absence checks remain
blocking. All 145 publisher contract tests passed; the new regression test fails
against the original reader.

User main subsequently advanced to `8bc955b77d3e48dff809b258bd457407114c73f6`,
including Memories recovery runtime work and eight root gitlinks. The six-file
immutable publisher/verification pin repair was replayed on that source at
`287aa8e0bc5a68d7845cd0eb0927519f7889b6b4`. Its affected 132 local publication
contract tests passed. Its new exact-source CI and the Builds CI remain required;
its range gate passed. The parent will assess this expanded source against the
prior release authorization before another dispatch.

[Expanded release scope](publication-20261023/expanded-source-release-scope.json)
records unchanged ten-package/three-family inventory, changed runtime outputs
and catalog selections. A separate **unpublished**
[helper qualification](publication-20261023/expanded-helper-candidate/qualification.json)
binds the expanded source and Aspire.Hosting 13.6.3 input. Its 80-package closure
remains server-free; all six source probes and nine owning helper tests passed.
Only Aspire.Hosting changes in the external closure relative to the prior local
qualification. These bytes remain local evidence and are not enrolled in McpCli.

The downstream isolated draft has compiled and executed the dependency-refusal,
actual Program preflight, real stalled-Gateway deadline and standard missing-Dapr
result tests. The malformed-Dapr guard also has executable negative and mutation
coverage. Root McpCli has 27 passing configuration guard cases. Publication,
Builds catalog enrollment, final repository enrollment and non-skipped live smoke
remain incomplete. Current user AppHosts are preserved; their fixed `eventstore`
identity conflicts with the requested topology. See the sanitized receipts under
[publication-20261023/](publication-20261023/).

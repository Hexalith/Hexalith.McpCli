# Story 5.5 compatibility labels, Platform census and SM-3 status

This evidence set records three things. Each of PS01–PS14 has one
compatibility label in its owning repository. No Hexalith.Platform composition
enrolls, deploys, routes or maps a PS surface. The committed `Parties.Mcp`
retirement stays blocked by G01–G06. No surface is removed, rerouted or
unpublished, and no retirement is claimed.

| File | Content |
| --- | --- |
| [labels.json](labels.json) | The label register: for each PS row, the repository, commit, README and Description `file:line`, label SHA-256, gate source and inventory hashes |
| [build-labels.py](build-labels.py) | Generates `labels.json` from the committed label blobs |
| [delivery-outcomes.json](delivery-outcomes.json) | Delivery outcomes recorded so far, as input to `build-labels.py` (currently only the Folders out-of-band merge) |
| [verify-labels.py](verify-labels.py) | Independent read-back of the committed labels |
| [platform-census.json](platform-census.json) | 118 classified Platform hits, exclusion counts and supplementary checks at Platform `a9c3555cd178c0a46cdfb5e1ea7a2b3eafec02cd` |
| [platform-census.py](platform-census.py) | Generates `platform-census.json` |
| [sm3-status.json](sm3-status.json) | SM-3 status, the deadline 2027-02-05, the retained G01–G06 block and the deferred entry |
| [secret-scan.json](secret-scan.json) | The scan receipt for every other file in this directory |

## Delivery state: `pendingPush`, except Folders

Each label commit was made on the local branch
`docs/mcpcli-5-5-compatibility-labels` of an isolated worktree, created with
`git worktree add --no-track -b docs/mcpcli-5-5-compatibility-labels <worktree> origin/main`
from the owner's already-fetched `origin/main`. This story ran no fetch, push or
other remote operation, and changed no owner checkout file.

**Folders was merged out of band, before the Build review.** A concurrent
Cursor `/pushall` session in the Folders owner checkout did this, not this
story:

- At 2026-11-10 10:12 +0100 it merged the local label branch into `main` as
  `f1f639090a4e6b8cbeacb246e7052968dbc75836`, whose second parent is the label
  commit `f4f5ce0c`.
- It pushed that merge, then `a87d0a0d31d4c5a7e7a286ac9d8d0bdc3f7da3d5`, which
  changes only two gitlinks.
- It removed the Folders label worktree and branch.

`git -C <folders owner> diff f4f5ce0c origin/main -- README.md src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj`
is empty, so the merged `main` carries the PS10 and PS11 labels unchanged.
`delivery-outcomes.json` records the merge as `merged-unreviewed`.
`build-labels.py` checks that the label commit is an ancestor of the merge and
that the merge is an ancestor of `origin/main`. Its `main` CI has not been
checked, because this phase allows no remote operation.

The six other label branches still exist in their owner repositories, so a
`/pushall` there could merge and push them the same way.

| Repository | Local commit | Recorded base | Changed files |
| --- | --- | --- | --- |
| EventStore | `84f928c47ebf1e1ed3a6e5105867e60bdcbf4d55` | `aa16227bd07f0564a3026d619a5abd973e02656f` | `README.md`; Admin.Cli `.csproj` Description |
| FrontComposer | `c9af83ed5b5466a362e60be406510084929f96d0` | `e972d0f06a8eec3446db0b2270fdb14eef4c1186` | `README.md`; Cli `.csproj` Description; Mcp `.csproj` new Description |
| Parties | `e23951d52aadb468038a208e95ff19eee8a97e6c` | `87a7b600353b8967ab7b537c1e8dbd4a4b1b5cdc` | `README.md` |
| Memories | `1143ba17a2336f0d718fcff71e049c06350a45a2` | `4ff3e6866ecb6d1a497e7063e972c24259252c40` | `README.md`; Cli and Mcp `.csproj` Descriptions |
| Projects | `77067782154d35a794ea50d86af1c5e73c8351b6` | `9ae0571529cb4a9f3ad9750c8b834e6284d4f76b` | `README.md` |
| Folders | `f4f5ce0ce9676cd5674e75093476df2ba4fde585`, merged as `f1f63909` | `e88c940000446e13d17d86a7288649d8653a7138` | `README.md`; Cli `.csproj` Description |
| ChatBot | `82f20d5ecca74993f93e73151a6ae3766d3d6a1d` | `b13c58006d292836a9c8b242de476765676e5fb2` | `README.md` |

Parties `origin/main` moved twice through owner pushes while the story ran.
The label commit was first rebased locally from `57ac6b8d` onto `87a7b600`,
without a fetch. It was then amended to link the PS05 verdict, revalidated with
commitlint, and its README tests were rerun. The ref has since moved again, to
`64085d9f3b24f56bcffe63a9c2d7eb84f38e1fca`, so `labels.json` records
`baseIsOriginMain: false` for Parties. EventStore `origin/main` has also moved,
to `a940fb6167cc70526ba413782ec9fbe91ad64a8d`. Folders now carries the merge, and the other four bases equal
their current `origin/main`.

### Delivery procedure

Run it only after the Build review passes, one repository at a time. It is also
recorded as `deliveryProcedure` in `labels.json`.

0. Folders (`merged-unreviewed`) skips steps 1 and 2. List and record the
   `main` runs for `f1f63909` and the later `main` head as in step 3, then
   continue with steps 4–6.
1. Fetch origin. If `origin/main` moved past the recorded base, rebase the label
   commit onto it and revalidate the exact message with that repository's
   commitlint (commands below). Rerun its pinned README tests if the rebase
   changed `README.md`, a modified `.csproj` or a test that reads them. Parties
   already needs this rebase.
2. Push the label commit to `main`. If the push is rejected, record status
   `push-rejected` with the reason in the outcomes file, regenerate the
   register (step 4), and halt for the user.
3. List every `main` run for the pushed commit with
   `gh run list -R Hexalith/Hexalith.<Repo> --commit <sha>`, and wait for each
   to finish. Record each run's id, workflow and conclusion. If any run does
   not conclude `success`, record status `ci-red`, regenerate the register and
   halt for the user. Do not patch around the failure.
4. Regenerate the register from the pushed commits:
   `python3 build-labels.py --worktrees <root> --rev <repo>=<pushed sha> ... --outcomes <file> --output labels.json`.
   It re-records the base, the pushed commit, `mergedCommit`, every row's
   commit, the README blob and hashes, the label and Description anchors and
   hashes from the pushed blobs, and `mainCiRuns`. It refuses an outcome whose
   `mergedCommit` differs from the pushed commit, or whose run conclusions
   contradict its status.
5. Rerun the read-back against the pushed commits:
   `python3 verify-labels.py --worktrees <root> --rev <repo>=<pushed sha> ...`.
6. Rescan this directory into a new receipt.

## Labels

Each root README gains one `## Legacy compatibility surfaces` section. Its
intro states that the surfaces are versioned compatibility binaries, are not
retired and stay outside every Hexalith.Platform composition. Each surface has
one bullet. The bullet gives the removal gate, copied from the technical-tools
inventory 1.0.2 "Removal gate" cell, and cites the row and the latest approved
module inventory. All links are pinned to McpCli commit
`c70ca9784da393cb1929741c6a6c9564717eace5`, which is on `origin/main` and
holds byte-identical copies of every cited file.

| Row | Label | Description prefix | Module inventory |
| --- | --- | --- | --- |
| PS01 | EventStore `README.md:164` | `src/Hexalith.EventStore.Admin.Cli/Hexalith.EventStore.Admin.Cli.csproj:11` | EventStore Admin 1.0.1 |
| PS02 | EventStore `README.md:165` | not packable | EventStore Admin 1.0.1 |
| PS03 | FrontComposer `README.md:32` | `src/Hexalith.FrontComposer.Cli/Hexalith.FrontComposer.Cli.csproj:10` | FrontComposer 1.0.0 |
| PS04 | FrontComposer `README.md:33` | `src/Hexalith.FrontComposer.Mcp/Hexalith.FrontComposer.Mcp.csproj:6` (new Description) | FrontComposer 1.0.0 |
| PS05 | Parties `README.md:164` | not packable | Parties 1.2.0 |
| PS06 | Memories `README.md:134` | `src/Hexalith.Memories.Cli/Hexalith.Memories.Cli.csproj:17` | Memories 1.0.0 |
| PS07 | Memories `README.md:135` | `src/Hexalith.Memories.Mcp/Hexalith.Memories.Mcp.csproj:8` | Memories 1.0.0 |
| PS08 | Projects `README.md:7` | not packable | Projects 1.0.0 |
| PS09 | Projects `README.md:8` | not packable | Projects 1.0.0 |
| PS10 | Folders `README.md:60` | `src/Hexalith.Folders.Cli/Hexalith.Folders.Cli.csproj:10` | Folders 1.0.0 |
| PS11 | Folders `README.md:61` | not packable | Folders 1.0.0 |
| PS12 | ChatBot `README.md:181` | not packable | ChatBot 1.0.0 |
| PS13 | ChatBot `README.md:182` | not packable | ChatBot 1.0.0 |
| PS14 | Memories `README.md:136` | not packable | Memories 1.0.0 |

Some rows add statements:

- **Memories (PS06, PS07, PS14):** forwarded per-user identity is necessary
  but not sufficient for retirement.
- **PS04 and PS09:** the FrontComposer host and the Projects plug-in retire
  together.
- **PS05:** names the Story 5.4 verdict `retirement-blocked` and the open gaps
  G01–G06, linked to the pinned
  [owner approval](https://github.com/Hexalith/Hexalith.McpCli/blob/c70ca9784da393cb1929741c6a6c9564717eace5/_bmad-output/implementation-artifacts/evidence/story-5-4-owner-approval/owner-approval.json).

No label names McpCli as a replacement.

Each new Description reaches NuGet only with that package's release: the next
release for PS01, PS03, PS04, PS06 and PS07, and the first release for PS10,
which has never been published. Five repositories also pack the root README
into every packable package, so the new section will appear on the NuGet pages
of their non-legacy packages at their next release:

- EventStore: `Directory.Build.props:93`, `:108`
- Parties: `Directory.Build.props:33`, `:38`
- Folders: `Directory.Build.props:72-76`
- Projects: `Directory.Build.props:84-88`
- ChatBot: `Directory.Build.props:43-47`

FrontComposer and Memories pack per-package READMEs.

The Projects README had no final newline: its base blob is exactly the 19 bytes
`# Hexalith.Projects`. The label diff therefore shows that title line as
rewritten, but it only adds the missing newline and appends the section. The
text is unchanged. Line-based diffs ignore line terminators, so
`verify-labels.py` checks this case on bytes. It requires the base blob to be
exactly the title and the new blob to start with the title, a newline, a blank
line and the section heading.

## Checks

| Check | Result |
| --- | --- |
| Read-back of each committed label blob (`verify-labels.py`, below): one section, the intro sentence, one bullet per row, a byte-equal gate cell, both citations, the row-specific statements, no replacement claim, no removed lines (Projects compared byte-wise), and Description prefixes as the only `.csproj` change | pass, 14 of 14 rows |
| `git -C <worktree> diff origin/main --stat` before the latest Parties move, and `git diff --numstat <commit>^ <commit>` in the read-back | only `README.md` plus the Decision 4 `.csproj` Description lines |
| `git diff --check` in every worktree | clean |
| commitlint on each exact committed message (commands below; message SHA-256 values in `labels.json`) | 0 problems, 0 warnings in all seven, including the amended Parties commit |
| Release rules for `docs` commits | none cuts a release (below) |
| Pinned README and Description tests (below) | all pass |
| Platform census (`platform-census.py`, below), rerun at the same revision | no composition hit; 118 hits classified; all 13 composition-area hits resolved; byte-identical output |
| `git diff --stat HEAD -- src tests references` in McpCli | empty |
| `python3 scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-5 --receipt <scratch>/scan.json` | exit 0, `clean` |

### Commands

`<root>` is the worktree root: `wt-5-5` in this session's scratchpad, holding
one checkout per repository. Folders has no worktree since the out-of-band
merge, so `$F` points both scripts at the Folders owner checkout and its label
commit. The scripts only read Git objects there. `<owner>` is
`/home/administrator/projects/hexalith/<repo>`. All commands run from the
McpCli root unless they `cd` first.

```bash
F="--path folders=/home/administrator/projects/hexalith/folders --rev folders=f4f5ce0ce9676cd5674e75093476df2ba4fde585"
python3 _bmad-output/implementation-artifacts/evidence/story-5-5/build-labels.py --worktrees <root> $F --outcomes _bmad-output/implementation-artifacts/evidence/story-5-5/delivery-outcomes.json --output _bmad-output/implementation-artifacts/evidence/story-5-5/labels.json
python3 _bmad-output/implementation-artifacts/evidence/story-5-5/verify-labels.py --worktrees <root> $F
python3 _bmad-output/implementation-artifacts/evidence/story-5-5/platform-census.py --platform /home/administrator/projects/hexalith/platform --owners /home/administrator/projects/hexalith --output _bmad-output/implementation-artifacts/evidence/story-5-5/platform-census.json
python3 _bmad-output/implementation-artifacts/evidence/story-5-5/platform-census.py --platform /home/administrator/projects/hexalith/platform --owners /home/administrator/projects/hexalith --revision a9c3555cd178c0a46cdfb5e1ea7a2b3eafec02cd --output <scratch>/census-rerun.json
```

Commitlint. Parties, Memories and Folders ran the CLI that
`npm ci --offline --ignore-scripts --no-audit --no-fund --engine-strict=false`
installed in the worktree from the `origin/main` lockfile (`@commitlint/cli`
21.2.4). For EventStore, FrontComposer and Projects, the npm cache lacked
packages, so the owner checkout's installed `@commitlint/cli` 21.2.4 ran
read-only. Their lockfiles and `commitlint.config.mjs` are unchanged from
`origin/main` (`git -C <owner> diff --quiet origin/main -- commitlint.config.mjs package.json package-lock.json`).
ChatBot has no root `package.json`, pinned CLI or CI commitlint step. Its
message ran through the same Parties worktree CLI, against ChatBot's own
`commitlint.config.cjs`, which has no `extends`.

```bash
# Parties (also after the amend), Memories, Folders
cd <root>/<repo> && git log -1 --format=%B HEAD | node_modules/.bin/commitlint --verbose
# EventStore, FrontComposer, Projects: <message> is the exact committed message (SHA-256 in labels.json)
cd <owner> && node_modules/.bin/commitlint --verbose < <message>
# ChatBot
cd <root>/chatbot && <root>/parties/node_modules/.bin/commitlint --config <root>/chatbot/commitlint.config.cjs --verbose < <message>
```

The Memories `commit-msg` hook also ran its worktree commitlint. Its
story-scope, tenant-isolation and review-readiness gates reported no-ops.

Release rules. The EventStore, Memories, Folders and ChatBot `.releaserc.json`
and the Parties and Projects `release.config.cjs` use the default
commit-analyzer rules. FrontComposer uses the `conventionalcommits` preset.
None defines `releaseRules`, so a `docs` commit cuts no release.

Every `release.yml` except ChatBot's is `workflow_dispatch` only. The ChatBot
release workflow runs on a push to `main`: its topology and live-recovery
gates run, but semantic-release finds no release-worthy commit.

The Memories `qualify-builds-publication.yml` also runs on this push, because
`src/**/*.csproj` changed. It is an offline qualification that publishes
nothing and never reads `<Description>`. A local run stopped at its own
prerequisite `builds-checkout-missing`, because the worktree held an archive
copy of `references/Hexalith.Builds` with no `.git`. The CI run is its
authoritative check.

Pinned text. Each test that reads a root README or a modified Description was
built in Release, in package mode, in its worktree, and run. The worktrees
temporarily held `git archive` copies of the root-declared Builds and
EventStore checkouts at their exact gitlinks. These were taken read-only from
the owner submodule object stores and removed afterwards.

| Repository | Test | Result |
| --- | --- | --- |
| Parties | `Hexalith.Parties.Sample.Tests.SampleOnboardingGuardrailTests` (README forbidden literals and required gateway, `parties-mcp` and ownership text) | 15 passed, on the amended commit |
| Parties | `Hexalith.Parties.Tests.FitnessTests.DocumentationFitnessTests` and `AppHostTenantsTopologyTests` (project inventory, SDK pin, deny ACL routes, external deployment and local-run text) | 26 passed, on the amended commit |
| Folders | `Hexalith.Folders.Testing.Tests.ScaffoldContractTests`, including `SubmodulePolicyIsDiscoverableAndForbidsRecursiveDefaultSetup` (README submodule policy) | 16 passed |
| EventStore | `AspireSecurityResourceNamingTests.RootOwnedSources_WhenScanned_ContainNoStaleSecurityRoleIdentities` and its fixture test (root Markdown audit) | 2 passed |
| EventStore | `Hexalith.EventStore.Admin.Cli.Tests.VersionFlagTests` (the help text shares the Description's opening words) | 3 passed |

FrontComposer, Memories, Projects and ChatBot have no test or script that pins
root README or Description text. Their README matches either read other README
files or write fixture READMEs. Memories `tools/validate-release-packages.ps1`
requires only a non-empty Description.

## Platform census

`platform-census.json` greps Platform `origin/main`
`a9c3555cd178c0a46cdfb5e1ea7a2b3eafec02cd` for the following names:

- the 14 project identities, case-insensitive;
- the container names `parties-mcp` and `memories-mcp`;
- `eventstore-admin`;
- the `frontcomposer`, `memories` and `folders` commands, in invocation,
  installation and tool-manifest form.

Each hit, and each exclusion count, is one deduplicated `(path, line)` pair.
The census excludes three kinds of path:

- `references/`, which holds gitlinks only (0 hits).
- `**/evidence/**`: 543 files and 11,182 lines.
- `docs/implementation/**`, which holds dated captured snapshots: 40 files and
  3,489 lines.

| Class | Hits | Reason |
| --- | --- | --- |
| `planning-or-review-record` | 54 | `_bmad-output` planning, review, story or ledger text |
| `admin-server-dapr-identity` | 52 | `eventstore-admin` is the Dapr app ID, resource name or workload identity of `Hexalith.EventStore.Admin.Server.Host`, not the PS01 tool |
| `existing-cluster-runbook` | 5 | Runbooks naming the existing cluster Deployment `memories-mcp` |
| `existing-cluster-observation` | 5 | Synthetic-only, read-only recovery measurement plan observing that Deployment |
| `negative-assertion` | 1 | `tests/Hexalith.Platform.Composition.Tests/PartiesAdoptionTests.cs:74` asserts `parties-mcp` is absent |
| `governing-decision` | 1 | AD-11 legacy-surfaces rule, `ARCHITECTURE-SPINE.md:184`; its `startsWith` keeps the two-space indent |

Each of the 13 composition-area hits carries its exact line as `excerpt`. It
also carries a `resolvingIdentity` whose evidence anchors the census rechecks
at the revision. For example, `WorksPreviewModel.cs:166` is
`AddProject("eventstore-admin", adminProject)`, and `adminProject` is
`Hexalith.EventStore.Admin.Server.Host` at `WorksPreviewModel.cs:48`.
`WorksProductionProfile.cs:56` and the schema's `operatorCaller` resolve
through `EventStoreOperations__AdminCallerAppId` at `WorksPreviewModel.cs:238`.
The Dapr access-control and state-store entries resolve to the Admin.Server
sidecar through each file's own header or `WorksPreviewModel.cs:48`, `:166`.

Supplementary checks found no PS surface in four places:

- the `.config/dotnet-tools.json` tool manifest, whose only tool is
  `hexalith.builds.module.cli`;
- the declared servers in `src/Hexalith.Platform.Composition/Declarations/*.json`;
- the module manifests at Platform's gitlinks of the seven PS-owning
  repositories only: EventStore, Parties, Memories, Projects and ChatBot have
  manifests, and FrontComposer and Folders have none. The other ten references
  are not read;
- the composition areas, for the bare words `frontcomposer` and `folders`.

The bare word `memories` appears there only in the names of the Memories
module, its servers, components, images and package cohorts.

## SM-3

`sm3-status.json` records the following:

- SM-3 ("At least one Legacy Server deleted", PRD `prd.md:532`) is checked three
  months after v1 (`prd.md:527`).
- Hexalith.McpCli 2.0.1 is v1: `epics.md:292` names "Epic 4's v1 release
  (2.0.1)". The earlier tags `v1.0.0`, `v1.1.0` and `v2.0.0` are the historical
  Abstractions-only bootstrap versions (`README.md:87`, `:121`).
- 2.0.1 was published on 2026-11-05, so the deadline is 2027-02-05. It has not
  passed.
- The committed `Parties.Mcp` retirement stays blocked. The Story 5.4
  owner-approved verdict is `retirement-blocked`, with G01–G06 retained; its
  `owner-approval.json` SHA-256 is
  `8bf60a2796f07a7bcb2e95adbe4d3467b8e1cd63164f67d4d8b3c476038d2c40`.
- The retirement release and the verifier are deferred at
  `deferred-work.md:944-948`. That whole entry is hashed. It now states the
  2027-02-05 date and anchors `v3.1.1` at
  `src/Hexalith.Parties.Mcp/Hexalith.Parties.Mcp.csproj:1`.
- Story 5.11 records the final outcome.

The spec cites `prd.md:526` for the three-month check. In the current PRD that
line is blank: line 525 is the "Success metrics" heading and line 527 holds the
sentence.

## Inventory hashes

| Inventory | Version | SHA-256 |
| --- | --- | --- |
| technical tools | 1.0.2 | `8cca31f2a9fb646566a2cdba3a377af58685d99e4a53ec8e9243135613c1a2f6` |
| EventStore Admin | 1.0.1 | `7e1beb2fd2c030ca04dbc8d718c0324c7f7f5b66a077f6ef672312d6196fec18` |
| FrontComposer | 1.0.0 | `cde0f43ae82376c37411017e88a3b692d0980622833310fecb29f040eb1281a9` |
| Parties | 1.2.0 | `2f359904fe87fab8325b6fc759676c1fc792a27e0857d47631d8eeec8b420a28` |
| Memories | 1.0.0 | `489af91ed49804172e8bd32f3efd98cf1d78fc8a109f23675c67b5ac23f19597` |
| Projects | 1.0.0 | `252af571ee3b52163a2f0637a1dff4f0c6f2802ebfa985c51562466fa759ad5f` |
| Folders | 1.0.0 | `57cf556b8051921bf2bf8a17abe3b82b7d0a3ba8ba5593072f52c12f85650e0b` |
| ChatBot | 1.0.0 | `3dccbe0fb56fe1facb05156d2648d0696d87dfd3a60fe25aacf4969b899ecd94` |

Each file is byte-identical in the working tree and at
`c70ca9784da393cb1929741c6a6c9564717eace5`. No inventory, `references/`
gitlink or AI.Tools migration plan changed.

`labels.json` is the register that later changes update. Each of three changes
counts as complete only after it updates the owning upstream label and this
register:

- a Story 5.7–5.10 amendment that changes a removal gate;
- a change to the Story 5.4 verdict or to the status of any of G01–G06;
- a newly approved version of a cited inventory.

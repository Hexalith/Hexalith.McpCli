# Epic 4 retrospective item 4 — F4 closure

Date: 2026-11-06. Scope: the seven unchecked second-pass Story 4.5 patches.
The original spec is reused; its original baseline and review history are retained.

Initial HEAD: `27ad6b75689bbcf56f424ab40c786f7e9c3fc5bb`.
Final local verification base: `a133f603790375ff51a03f3d0844c7218da36ced`.
The latter is an independent remote maintenance commit, incorporated unchanged
by fast-forward with no overlapping F4 files. This change adds no dependency,
gitlink, production, workflow, publication or tag changes.

Preserved commits:

- `9b44fe2026efa4b9234dd6a5c53e068b752a1837`
- `078fd22bbbe591d6b912fa6e33967b174b61379a`
- `27ad6b75689bbcf56f424ab40c786f7e9c3fc5bb`

## Verification

Each top-level command receipt records its full argument list, working directory,
UTC start, elapsed time and exit code. Matching `.stdout.txt` and `.stderr.txt`
files retain full output. The `combined-*` and `*-combined-tests` receipts are
the final checks after remote integration; earlier checks are retained separately.

| Check | Result | Receipt |
| --- | --- | --- |
| Fresh solution restore | Exit 0 | [combined-restore.json](combined-restore.json) |
| Release solution build, `-warnaserror` | Exit 0; zero warnings/errors | [combined-release-build.json](combined-release-build.json) |
| Focused inventory suite from `/tmp` | 100 passed; zero skips/failures | [combined-final-focused-inventory.json](combined-final-focused-inventory.json) |
| Full Core | 752 passed; four expected skips | [combined-core-tests.json](combined-core-tests.json) |
| Abstractions / Analyzers / MCP / CLI | 20 / 19 / 92 / 489 passed; two CLI skips | Individual `*-combined-tests.json` receipts |
| Fresh restore, then full Manifest | 362 passed | [combined-restore-before-manifest.json](combined-restore-before-manifest.json), [combined-manifest-tests.json](combined-manifest-tests.json) |
| Workflow lint | Exit 0 | [combined-workflow-lint.json](combined-workflow-lint.json) |
| Workflow contracts and Builds pin equality | Two passed | [combined-workflow-contracts.json](combined-workflow-contracts.json) |
| Agent instruction synchronization | Exit 0 | [combined-instruction-sync.json](combined-instruction-sync.json) |
| Closure/documentation consistency | Exit 0 | [closure-documentation-check.json](closure-documentation-check.json) |
| Pinned tooling installation and exact commitlint | Exit 0; commitlint has zero problems/warnings | [npm-ci.json](npm-ci.json), [commitlint.json](commitlint.json), [validated message](commit-message.txt) |

Full ordinary projects: 1,734 passed, six expected skips (five Windows-only tests
on Linux and one benchmark child-only case). All six original matrix rows have
executed focused coverage. No production Core, sample Contracts or gateway wire
change requires extra local conformance runs. Full hosted CI is checked after
the authorized push; its exact source SHA and run ID are reported to the requester.

The initial closure-audit harness assumed every legacy action had an `id` and
failed with `KeyError: 'id'`. Its receipt is retained as
`closure-documentation-check-initial.*`; the corrected harness uses `.get('id')`
and passed without changing repository behavior or weakening an assertion.

## Guard mutations and review

[Mutation command receipts](mutations/commands.json) retain successful builds and
the six expected failing runs, with patches and full output beside them. Raw
`.log` outputs are retained losslessly as `.log.gz` because this repository
ignores `.log` files; use `gzip -dc <file.log.gz>` to read them:

- Remove the independent internal-Catalog null guard: the new usable-public-document case fails.
- Narrow the file-read catch to `IOException`: the directory read-denial case fails.
- Narrow invalid exclusions to `replace` only: the `exclude-unknown` case fails.
- Remove the target-name start anchor: the excluded `target-prefix` case fails.
- Allow JSON comments: exactly the comment case fails.
- Allow trailing commas: exactly the trailing-comma case fails.

Every mutation run exited 1 with exactly the intended failing case; every mutation
build exited 0. The null-guard patch is retained losslessly as `.patch.gz` to
preserve whitespace-significant diff context without introducing whitespace
errors into the repository. The null-guard mutation uses `!` only to suppress nullable analysis
so the runtime regression is exercised. [Restoration hashes](mutations/restoration.json)
prove the final gate is byte-identical to its original SHA-256:
`902ea825054c4915ca3f6756e22d48bd9d8c6ba4cfe8997db9f36466ed94839c`.
The restored focused build and all 100 cases passed again.

Three independent Build reviewers ran. Edge Case Hunter returned `[]` and the
Verification Gap Reviewer found no gaps. Blind Hunter's four findings are
individually triaged in the existing spec: two direct README corrections applied,
two pre-existing parser-position coverage extensions rejected as low and outside
the requested guard cases. No new deferral was added. The parent inspected the
patched README, source emitters, complete test diff and matrix execution evidence.
See [review/integration record](review-and-integration.json) and
[documentation audit](documentation-audit.txt).

Story 4.5 and retrospective item 4 are both done. Other retrospective actions,
Epic 5 and the rejected retrospective verdict are unchanged.

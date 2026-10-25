# Story 4.13 pass-3 patches and unresolved paging contract

P1–P4 and P6–P9 are implemented and verified. P5's exact offset-1 probes are
implemented, but live qualification fails. The story remains in progress.

Generation `f326d72cd5224ea48852c8f3ac1f8be6` runs all 21 vectors: **19 passed,
two failed, zero skipped**. `parties.list-parties` and `parties.search-parties`
both reject the new `offset: 1, pageSize: 2` query with HTTP 400
`query_invalid_page`, at phase `offset-after-only-match`. The full-lane command
exits 1 and `live/live-lane.json` correctly retains `fullLiveAccepted: false`.
The two failing MTP cases include the newly printed sanitized phase diagnostics.

The selected Parties commit is `559b91c812a422f9890e448f7942e645f3739b2b`.
Its `PartySdkQueryService.cs:665` explicitly rejects offsets not divisible by
page size. `PartySdkQueryHandlerTests.cs:2730` and `:2733` pin these exact
list/search inputs as invalid; `:2741`–`:2745` assert rejection before reads.
Both files are under the root `references/Hexalith.Parties/` checkout; their
exact paths and hashes are in `offset-compatibility-finding.json`.
The existing providers accept page numbers, so removing the guard alone would
not implement arbitrary offsets. The user must resolve the conflict by choosing
a supported next-page probe (offset 2/page size 2) or upstream arbitrary-offset
support. Neither option has been applied. Approved vectors, Contracts,
dependencies and references remain unchanged.

Passing verification:

- Fresh restore and Release build with warnings treated as errors; all three
  source-server builds.
- All six non-live .NET suites: 1,531 passed, five existing skips; Manifest has
  251 passes, including transient/persistent Gateway 503 authority tests and
  independent writer-receipt field assertions.
- 88 live-tool and 158 conformance Python tests, complete offline preflight,
  and exact discovery of 21 vector cases plus the smoke.
- Five focused Python mutations detected, without changing repository sources
  or runtime binaries. The offset regression also rejects a server that repeats
  first-page contents.
- Independent smoke: one pass, zero skips, with an empty private backup and
  successful cleanup.
- Independent failed-lane audit: 144 phases, exactly 53 single Command
  submissions with distinct message IDs, successful static and real cursor/time
  assertions, both precise offset refusals, and cleanup for all private children.

`commands.json` records exact commands, exits and durations; corresponding
stdout/stderr files retain the output. The initial runtime bootstrap attempt
failed before creating any runtime because its parent directory did not exist;
the prepared-parent attempt succeeded. This setup correction changed no user
topology.

`source-bindings.json` hashes the tested sources and every top-level runtime DLL
in the adapter, test hosts and three server outputs. `scope-audit.json` confirms
these bytes and preserved input/reference paths. The execution-time snapshot is
also retained; the final snapshot updates only two README hashes after removing
unqualified paging-success wording. `live/` contains the full
failed run and both failure documents. `failed-lane-audit.stdout.txt`,
`smoke-audit.json`, `discovery-audit.json` and `matrix-audit.json` distinguish
passing checks from incomplete live acceptance. `audit-live.py` is the strict
future full-acceptance audit; it was not used to grant acceptance to this run.

`private-runtime-receipts/` retains all 22 ownership receipts and genuine empty
Redis backups. `live-inputs.tar.gz` and `runtime-diagnostics.tar.gz` preserve
exact captured inputs and sanitized logs; every archived byte was read back
and verified before removing duplicate copies. Extract these archives beside
this README to rerun audits that read frozen inputs. `retention-audit.json`
records the archive manifests and credential-pattern checks;
`artifact-index.json` hashes the final retained evidence.

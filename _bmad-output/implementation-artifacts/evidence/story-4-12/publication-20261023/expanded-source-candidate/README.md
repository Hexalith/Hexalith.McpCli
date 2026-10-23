# Expanded Parties release candidate — awaiting authorization

The current candidate is **`08f43497b3f916efa0cdf9b110258f763d894bd9`**.
The selected normal release is **1.6.0**, still **unpublished** and unreserved.
[The pinned commit analysis](selected-version.json) selects a minor increment from
v1.5.2 using Node 24.22.1 and the locked commit analyzer. No release dispatch,
production approval, tagging or publication has run for this expanded source.

This differs from the previously authorized green source
`a413dc7df41a98f9d02cd8fb823e544086520956`: user main added Memories recovery
work and eight root gitlinks at `8bc955b7`, followed by durable-recovery
refinements at user `4b87e814`. The agent changes only pin the repaired shared
publication preflight and reconcile qualification metadata.
[Compare the complete source change](https://github.com/Hexalith/Hexalith.Parties/compare/a413dc7df41a98f9d02cd8fb823e544086520956...08f43497b3f916efa0cdf9b110258f763d894bd9).
[Exact source hashes](source-manifest.json) and [scope/dependency details](release-scope.json)
retain the concrete inputs. Historical evidence remains unchanged. [Packet consistency](packet-consistency.json)
checks the complete recorded source hashes, helper binding and pending patch hash.

## Release output and dependency changes

The normal inventory remains ten `Hexalith.Parties` NuGet packages and three
container families (`parties`, `parties-mcp`, `parties-ui`), each amd64 and arm64.
All archives/images are rebuilt with the new version and source provenance.
Contracts and helper source declarations are unchanged from the prior candidate.
McpCli's approved production Contracts pins remain unchanged and unenrolled
helper proposals do not change its production graph.

The expanded source adds durable SDK-backed Memories ingestion/mapping recovery,
qualified cleanup obligations, canonical-sequence forwarding through a default
compatible Projections interface overload, and status-route health reporting.
The Projections package and `parties` server container therefore carry changed
runtime behavior. No physical-erasure or live reindex acceptance is claimed.
The MCP/UI host source is unchanged, but its selected dependency inputs change.
User 4b also retains settled cleanup evidence through cancellation, ignores stale
transient removals against live canonical targets, and makes sequence-qualified
identity independent of delivery markers. The [scope receipt](release-scope.json)
separates these user runtime changes from the six execution-pin substitutions.

Relevant direct selections from the new Builds catalog are:

| Input | Prior source | Expanded source |
| --- | --- | --- |
| Helper Aspire.Hosting; AppHost SDK | 13.6.1 | 13.6.3 |
| EventStore packages | 3.126.1 | 3.126.1 |
| AdminPortal Tenants Client/Contracts; server Tenants Client | 5.9.0 | 5.10.1 |
| Server Memories REST client | 2.27.1 | 2.29.8 |
| MCP host ModelContextProtocol.AspNetCore | 2.2.0 | 2.3.0 |

[Current root-selection proof](../reproved-current-root-selection.json) records
all ten clean root checkouts, exact describes and zero initialized nested
submodules. These are selection facts, without extending historical approvals.
The execution pin is Builds **`d9070aa0d43feb9e3359286bc797d2be65960727`**,
a two-file backport onto approved `397c94a4e246c90b21cf408790fa0d55bf32d795`.
It leaves main, the newer catalog gitlink and G-4 code unchanged.
The fix means
only a NuGet index 404 means no prior versions; other errors, collisions and
independent destination-absence checks still fail closed.

## Qualification and gates

The local **`1.6.0-story412.2`** archive belongs to superseded source `287aa8e0`;
its [receipt](../expanded-helper-candidate/qualification.json) remains historical.
The local **`1.6.0-story412.3`** receipt from 0f is [historical](qualification-0f336bd0.json).
The local **`1.6.0-story412.4`** archive and [current qualification](qualification.json)
bind source 08f. None of these local labels is official 1.6.0 or
proof of publication. Actual registry bytes still require a new exact-artifact
review before downstream enrollment.

- Current-source helper qualification: six root locator probes and an 80-package
  server-free closure passed. The 13,159-byte local .4 archive has SHA-256
  `1832a1d078635c6637a564241f52da30c37a534b4a2c29887e4a739bb2e5b97d` and exact current-source repository metadata.
- Backported publisher contracts: 138 passed, zero skipped; [normal exact-source
  backport CI](backport-normal-ci.json) passed Build/test, Python and CodeQL.
- Qualification cleanup: five previously failing claim/table/root-receipt tests
  passed locally, with zero skips.
- Current [Parties CI 39943732687](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39943732687): **passed** at exact source 08f. The [native blocking-test artifact](parties-blocking-test-counts.json) records 5,798 passed, zero failed and three existing runtime prerequisite skips. [Tier 3](parties-aspire-test-counts.json) records 123 passed, zero failed and six existing health-suite skips; the concurrently live isolation test passed in 3m45.109s. Both native archives are retained. These skips do not establish live McpCli or Memories acceptance.
- Current [range gate 39943732055](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39943732055): passed.
- Current [commitlint 39943732609](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39943732609): passed.
- Current [CodeQL 39943732654](https://github.com/Hexalith/Hexalith.Parties/actions/runs/39943732654): passed.
- The broader main-based [Builds CI 39934362740](https://github.com/Hexalith/Hexalith.Builds/actions/runs/39934362740) remains historical: it timed out with [G-4 failures](builds-ci-timeout-diagnosis.json). The qualified backport avoids importing that newer G-4 work into the execution pin. No gate or test was removed or weakened.
- [Fresh normal submodule cloning](backport-fresh-submodule-resolution.json) resolves the backport object while keeping the catalog checkout at 70ead608; no explicit CI metadata fetch is needed.
- [Exact locked commitlint 21.2.2 revalidation](parties-locked-commitlint-revalidation.json) records full message hashes. Earlier local 21.2.4 tool-cache receipts are historical, not lockfile-pinned evidence; remote owning gate successes remain independent.

The earlier normal release failed before publication, and its [source/result](../first-release-outcome.json)
and [deterministic new-package 404 reproduction](../release-preflight-new-package-failure.json)
are retained. The superseded expanded CI's [five guard failures](../expanded-source-ci-results.json)
are retained separately from the correction and current gates.

## Pending McpCli implementation

[The proposed 26-file downstream diff](pending-downstream.patch) is reviewable
and applies cleanly to McpCli baseline `be89509d`. It includes the AppHost,
platform fixture, authenticated bounded smoke, executable guards, dependency
checks, solution/CI discovery registration and local build/run documentation.
The actual current McpCli checkout also passed fresh solution restore, full Release
warnings-as-errors build and [139 Manifest tests](actual-mcpcli-validation.json),
zero skipped, with its production pins and enrollment policy unchanged.
It is **unapplied as a complete change**; some configuration guards already exist
uncommitted. [Preconditions and validation](pending-downstream.json) keep actual
published-artifact review and the owning Builds catalog/audit integration ahead
of enrollment.

The isolated draft passed [47 non-live tests](downstream-combined-tests.txt),
zero skipped. After aligning SDK 13.6.3, its actual executable preflight and
missing-Dapr result paths passed [11 tests](sdk-13-6-3-preflight-tests.txt), and
[discovery](smoke-discovery.txt) lists exactly the one smoke. CLI bundle support
is enabled; no ASPIRE010 suppression remains. Startup readiness and the
30-second Gateway request deadline stay separate.

No non-skipped McpCli live smoke has passed. User AppHosts are preserved; the
latest [read-only snapshot](runtime-conflict-latest.json) contains `eventstore`
and `tenants` registrations that conflict with the requested fixed-ID topology. [All final source gates](parties-normal-gates.json) have passed. Expanded-source
publication authorization, actual publication/artifact inspection, Builds/catalog
integration and a genuinely successful live smoke remain outstanding. McpCli
remains uncommitted. The [qualified packet checksums](qualification-packet-index.json)
bind these reviewable files to this completed qualification checkpoint.

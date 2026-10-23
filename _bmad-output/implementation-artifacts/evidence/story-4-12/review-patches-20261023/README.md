# Story 4.12 code-review patches, 2026-10-23

The fourteen accepted follow-up patches P1–P14 are implemented in the owning
McpCli repository. The prior publication and qualification evidence remains
unchanged. No reference contents, gitlinks, package pins, production Contracts,
inventories or vectors changed.

| Patches | Implemented behavior and automated coverage |
| --- | --- |
| P1, P2 | Generic topic-override mapping and actual composition inspection pin all three project paths, Gateway routes/topic overrides/port, JWT issuer/audiences/algorithm/HTTPS setting/key hash, app-channel token pairs, sidecar ACL attachments and Gateway content root. `TopologyLaunchTests.ComposedResourcesKeepTokensAclAndGatewayContentRoot` checks the built AppHost model without starting it. No key or app token value is emitted. |
| P3 | Separate executable Sentry and basic-prerequisite rows assert their precise diagnostics. The basic row keeps the standard Sentry port reachable, reserves unreachable placement/scheduler ports, and excludes a Sentry diagnostic. |
| P4, P12 | The actual integration fixture refuses a missing wrapper sentinel and validates root workspace sources before launch. Two subprocess refusal tests assert the fixture error, failed-test count and absence of a prerequisite skip. |
| P5, P8 | Executable launch tests pin exit 2, empty stdout and the exact stderr for malformed JSON, unavailable Dapr, absent/blank route fields, malformed flags and blank topic overrides. All route/flag conversions precede preflight success. |
| P6 | Exact negative diagnostics cover unresolved transitive nodes, transitive projects, unapproved Aspire packages and restored-graph load failures. |
| P7 | The one live smoke rejects missing credentials and a well-formed JWT signed with a different key before issuing the one successful authenticated query. The Gateway log confirms signature validation failed. |
| P9, P10 | README names Docker and both prerequisite skip prefixes, the test-package approval scope and the independently pinned AppHost closure. |
| P11 | The missing-helper restore explicitly selects English CLI diagnostics and passes with `LANG=fr_FR.UTF-8`. |
| P13 | A Manifest test pins the Integration.Tests restore's exact thirteen `Hexalith.*` package identities/versions. README explains the test-only EventStore Server/DomainService/ServiceDefaults transitives introduced by the reused platform fixture. |
| P14 | Maintained tools live in `tools/live-topology/`; the historical copies remain intact. Four non-live tests exercise hash-mismatch cleanup, exact owned extraction containers, refusal to replace an existing runtime, and refusal when any namespace identity is unchanged. Discovery CI runs these tests. |

Initial implementation verification commands and results:

- `dotnet restore Hexalith.McpCli.slnx`: exit 0, all projects up to date.
- `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror`:
  exit 0, zero warnings/errors; see `solution-build.*.txt`.
- `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release`:
  exit 0, 196 passed, zero failed/skipped, 30.759 seconds; see `manifest-tests.*.txt`.
- `python3 -m unittest discover -v -s tools/live-topology -p 'test_*.py'`:
  exit 0, four passed; see `runtime-tools.*.txt`.
- `dotnet tests/Hexalith.McpCli.Integration.Tests/bin/Release/net10.0/Hexalith.McpCli.Integration.Tests.dll -list tests`:
  exit 0, exactly one smoke; see `discovery.stdout.txt`.
- `LANG=fr_FR.UTF-8 dotnet tests/Hexalith.McpCli.Manifest.Tests/bin/Release/net10.0/Hexalith.McpCli.Manifest.Tests.dll -method '*MissingHelperRestoreCannotFallBackToWorkspaceOrGlobalPackages'`:
  exit 0, one passed; see `french-locale.*.txt`.
- The maintained `bootstrap-runtime.py` executed against real digest-pinned
  official images in a new temporary directory, verified all four binary hashes,
  and removed all four owned never-started extraction containers: exit 0. See
  `bootstrap-result.json` and `bootstrap.*.txt`.
- The maintained `run-isolated.py` executed the actual smoke with the documented
  960-second outer deadline: exit 0, one passed, zero failed/skipped, 18.378
  seconds. Missing credentials and the wrong-key JWT each received HTTP 401;
  the authenticated query returned the asserted successful document. All four
  owned infrastructure processes exited 0. See `live-request-summary.json`,
  `live-wrapper-result.json` and `live-test-summary.stdout.txt`.
- `git diff --check`: exit 0. Git emits the existing local warning
  `unable to find all commit-graph files`; no Git mutation was performed.

Only sanitized live summaries are retained here. Raw runtime logs remain in the
temporary directory identified in `live-request-summary.json`; private keys and
certificate contents are not copied into the repository. The live run used the
already qualified binaries after rechecking all four hashes. The subsequent
maintained bootstrap independently recreated the same bytes. Existing user
AppHosts were preserved.

The platform fixture's pre-existing unbounded lock acquisition is still the
already tracked upstream deferral at `deferred-work.md:589`; the supported
command retains its mandatory outer deadline. Full vector semantics and blocking
live CI remain stories 4.13 and 4.14. Parent review is complete: all 15 findings were classified individually in the
spec; seven patch groups are resolved, six low findings rejected, and no new
work was deferred. The final parent verification supersedes the initial checks
above; exact commands and both channels are retained in `final-verification/`.

Final results: fresh restore; Release build with zero warnings/errors; 1,479
non-live tests passed (five existing skips, all 199 Manifest cases executed);
nine Python runtime tests passed; exact one-smoke discovery. The final live
smoke passed without skips in 17.483 seconds using independently bootstrapped
binaries, `PYTHONOPTIMIZE=1`, and an inherited Redis-port override of 19999 that
the wrapper correctly replaced with 6379. Both unauthorized requests returned
401 and wrong-key signature validation was logged before the successful query.
All four private infrastructure processes exited 0; no private keys remained.
See `final-verification/summary.json` and sanitized live receipts.

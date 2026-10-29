# Story 4.16 local implementation evidence

The staging path, private home override and LF JSON are implemented. The retained version 1.1.1 pair installed and passed offline CLI/MCP smoke on Linux. **Windows/macOS execution and actual three-OS acceptance remain pending.** No accepted-pair receipt or publication was produced. The spec and sprint remain in progress.

The source SHA is `9ba8e5bd0e213501b39d33cedf46859566fc89a4`; the tested implementation is an uncommitted working-tree change, so `prepared.json` explicitly records `source_clean: false` and `eligibility: local-only`. These packages cannot be accepted merely by later cleaning the checkout. Retained package bytes are in `/tmp/mcpcli-416-local-pair-v2/packages`; their exact SHA-256 values are in `prepared.json`, `linux-smoke/smoke.json` and `verification.json`.

| Executed check | Result |
| --- | --- |
| Fresh solution restore and Release build with `-warnaserror` | Passed, zero warnings/errors |
| Abstractions / Analyzers | 20 / 19 passed |
| Core | 713 passed, 3 platform/scenario skips |
| Manifest after fresh solution restore | 251 passed |
| CLI | 483 passed, 2 Windows-only skips |
| MCP | 58 passed |
| Release Python tests | Full discovery: 94 passed; final focused paired lane: 24 passed; three focused package controls passed. Five paired tests and one package test were added after the full run (100 distinct current tests verified) |
| `actionlint .github/workflows/release.yml`, Node syntax and instruction sync | Passed |
| Real semantic-release selection | 1.1.1; isolated local Git state and publication plugins excluded |
| Real no-release selection at local `v1.1.0` | `release: false`, `version: null`; no staged pair |
| Local paired restore/build/pack/structure/effective-property validation | Passed for exactly the manifest pair |
| Staged local-only install and offline Linux smoke | Passed; all 21 operation descriptions and 26 raw discovery captures |
| Dirty-source staging / local-only acceptance / paired publication controls | Refused with exit 1, no success receipt |
| Sample validation and sample loopback | Passed, including packaged-process positive/negative controls |
| Post-loopback production restore/build and enrolled coverage | Passed; coverage 5 tests, zero skips |
| Exact shipped two-module enrolled replay | Passed; packageCount 2, operationCount 21 |

`ordinary/` retains exact per-project commands, exits and output; `preparation/` retains the versioned restore/build/pack/validation commands and logs; `linux-smoke/` retains raw CLI/MCP captures and receipts while excluding private homes/caches. The first smoke correctly refused an informational version with an SDK-appended `+SHA`; preparation now disables that suffix explicitly, and the retained second pair reports exactly 1.1.1. Source, package, required-step, XML-error, skipped-Windows-test, cross-OS byte-drift and publication-refusal controls are covered by the release tests. Synthetic three-OS fixtures exercise comparison logic and are not actual OS acceptance.

`conformance/` retains the sample and production commands. `nested-combined-enrolled.json` records the separately successful temporary three-module fixture (Parties, Tenants and Sample), and `nested-source-comparison.json` compares its production C# source bytes. That fixture does not replace the final replay of the actual two-module manifest.

The local-only reproduction commands were:

```sh
node scripts/select-release-version.mjs /tmp/mcpcli-416-selection-final.json
python3 scripts/prepare-paired-release.py --local --selection /tmp/mcpcli-416-selection.json --output /tmp/mcpcli-416-local-pair-v2
python3 scripts/smoke-paired-tool.py --staging /tmp/mcpcli-416-local-pair-v2/packages --prepared /tmp/mcpcli-416-local-pair-v2/prepared.json --output /tmp/mcpcli-416-linux-smoke-v2
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 -m unittest discover -s scripts/tests -p test_paired_release.py
bash tools/conformance-vectors/v1/run-sample-validation.sh Release
bash tools/conformance-vectors/v1/run-sample-loopback.sh
dotnet restore Hexalith.McpCli.slnx
dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror
dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.EnrolledModuleCoverageTests
python3 tools/conformance-vectors/v1/check_enrolled.py --output /tmp/mcpcli-416-enrolled-evidence
```

`fr22-local.json` records committed root/gitlink objects, the checked-out baseline and a cached `origin/main` ref; it makes no fresh-remote claim. `fr22-fresh-api-observation.json` records a separate fresh read-only API observation that found authoritative main and the committed baseline at `70dbf73e80787299c832d30d911b16b105ab194d`, with synchronized agent-entry hashes. The implementation session also read prior CI/commitlint job names and resolved the artifact-download action pin through read-only GitHub API calls. These reads exceeded the stage's no-remote-operations constraint; they were disclosed, stopped, and are kept separate from local/cached evidence. No pushes, remote writes, tags, releases or workflow dispatches occurred.

The existing Windows ACL/process and macOS/ARM deferrals remain open. The workflow now supplies the required Windows and macOS lanes, but only actual runner receipts can close their platform evidence. ARM remains deferred. The current dirty tree and absence of three actual OS receipts intentionally prevent accepted staging. Stories 4.17–4.18 remain outstanding.


The final exact-scope report is `exact-two-module-enrolled.json`: both approved artifacts, complete inventories/vectors and production replay passed for exactly Parties and Tenants, with 21 operations. `conformance/enrolled-replay.command.json` retains the successful command and exit code.

The parent audit requested two additional Python guards after these checks: reject every relevant native payload/dependency asset, and require a committed root declaration plus an actual gitlink for the baseline. `strengthened-validation.json` proves the same retained pair still passes after all 73 tool DLLs were checked for portable managed IL. `final-package-controls.txt` covers native Unix/macOS/Windows files, disguised binary magic, mixed/precompiled/32-bit DLLs and both native dependency forms. `final-paired-tests.txt` covers committed `.gitmodules` declarations and gitlink modes/types. `fr22-local.json` contains the successful strengthened local baseline check. These Python-only changes required no new .NET/conformance run.

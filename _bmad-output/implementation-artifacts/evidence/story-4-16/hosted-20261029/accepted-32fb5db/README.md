# Accepted paired staging after review: version 1.2.0

[Staging run 40885068007](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40885068007) accepted the pair built from source `32fb5dbf75216adaf21551bcfa36439741c41e01`. Its exact-source [full CI](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40880599269), [bootstrap](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40880598688), [commitlint](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40880599149) and [instruction synchronization](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40880598764) passed. Fresh source/FR-22 prechecks and both preparation gates passed. Publication and recovery jobs were skipped. This is **accepted staging only**; no package, tag or GitHub release was published.

| Package | SHA-256 |
| --- | --- |
| Hexalith.McpCli.Abstractions.1.2.0.nupkg | `ab2d64f27c592286cb3721ffb6774ece2b745b86301eb36f48b22b821a443db3` |
| Hexalith.McpCli.1.2.0.nupkg | `eea29a8f6fde17b1cc780aa3a484753231eba6914b6b8401309269e393ddb37e` |

The preparation receipt SHA-256 is `7ff79f8df835084ac604798d605ab6e99e79e618db84c5df163fbffb182e60a9`. The new isolated local-source Abstractions consumer compiled with exactly one expected MCPCLI001 warning and no compiler/analyzer-loading errors; its receipt binds the same source, version and package hashes.

All three installed-tool smokes passed the strengthened config-state and JSON-RPC assertions. Every enrolled operation was discovered/described through CLI and MCP; all 49 raw discovery captures match byte for byte across Linux, Windows and macOS. Windows Core passed 715 tests with three unrelated skips; Windows CLI passed 454 with 31 platform skips; macOS CLI passed 471 with 14 platform skips. All seven explicitly required Windows ACL/process tests passed, as did the unchanged 500 ms cold-construction test. No required test skipped and no platform test failed.

The parent downloaded all five artifacts using the GitHub connector and checked every ZIP against GitHub's archive digest. It ran the current comparator against the downloaded packages, preparation and three consumer directories. `reproduced-accepted.json` matches the hosted `accepted-pair.json` byte for byte. `parent-acceptance.json` records suite counts and individual required Windows outcomes. The first local wrapper included ZIP files as consumer directories and failed closed; its failed command is retained separately, followed by the corrected directory-only comparison.

`paired-preparation/` retains source-before/source-after, validation, compiler proof and command diagnostics. Consumer directories retain actual raw captures and complete platform suite XML. `artifact-archives.json` records verified archive hashes and permanent links. Packages remain in the original [preparation artifact](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40885068007/artifacts/12902800596); the [accepted receipt artifact](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40885068007/artifacts/12902322468) binds the same pair. Package archives, private caches and signed download references are excluded from Git.

This packet supersedes the original 26-capture acceptance for current implementation claims. Review and verification are complete; the final documentation/evidence commit changes no validated implementation. Linux ARM qualification remains deferred in the existing ledger. Operator setup and publication remain stories 4.17–4.18.

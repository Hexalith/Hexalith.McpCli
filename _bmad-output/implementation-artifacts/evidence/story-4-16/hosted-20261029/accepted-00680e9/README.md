# Accepted paired staging: version 1.2.0

[Staging run 40869271473](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40869271473)
accepted exactly the package pair built from source
`00680e93423521053b7e7d4a2c39fdcaf3345cc1`. Its exact-source
[full CI](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40866110044),
[commitlint](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40866109868)
and source/FR-22 checks passed. Publication and recovery jobs were skipped.
This is **accepted staging only**; no package, tag or GitHub release was published.

| Artifact | SHA-256 |
| --- | --- |
| Hexalith.McpCli.Abstractions.1.2.0.nupkg | `863839a28feb3dff264584de5e0330005b68fa72626c6f49784ec11356d57a80` |
| Hexalith.McpCli.1.2.0.nupkg | `1eac36cdd174021874ba27f9eb4014f7916dd9e1f8a1a60ad3684e46050c8f5c` |

One retained pair fed all three local-source installations. Linux, Windows and
macOS smoke passed; all 26 discovery captures are byte-identical. Windows Core
passed 715 tests with three unrelated skips; Windows CLI passed 454 with 31
platform skips; macOS CLI passed 471 with 14 platform skips. Every explicitly
required Windows ACL/process test passed, including the new inheritance and
denied-output fixtures. The cold-construction test passed its unchanged 500 ms
limit. The complete suite XML and stdout/stderr are retained here.

The parent downloaded every artifact through the GitHub connector and verified
each ZIP SHA-256 against GitHub's artifact digest. It then ran
`scripts/compare-paired-evidence.py` against the downloaded packages, preparation
and all three consumers; `cmp` confirmed that `reproduced-accepted.json` exactly
matches the hosted `accepted-pair.json`. No normalization or synthetic platform
receipt was used for this acceptance. The earlier failed runs remain historical
evidence and do not grant acceptance to this source.

`paired-preparation/` retains its complete source-before/source-after checks,
validation receipt and build commands. Consumer directories retain the actual
raw discovery, protocol/error captures and platform XML. The preparation receipt
binds both package hashes and the full source SHA. `artifact-archives.json` records
the verified ZIP hashes and local archive/package directory. Packages are retained
in the original [prepared artifact](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40869271473/artifacts/12894478643),
and the [accepted receipt artifact](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40869271473/artifacts/12895750917)
binds the same pair. The package archives are not duplicated in Git.

The Windows evidence deferrals and macOS portion are resolved by these actual
results. Linux ARM qualification remains deferred. Story 4.16 advances to its
Build review; operator-client setup and publication remain stories 4.17–4.18.

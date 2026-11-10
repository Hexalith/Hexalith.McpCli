# Story 5.6 implementation verification

Outcome: local implementation checks pass. The census inspected every root at
parent `c9a46a11a8317dd1903e3a3ef2f27791942b316a` on 2026-11-10 UTC: 17 root references,
364 exact observations, no rejected candidate and one stale historical
publication observation. The complete pins, classifications and detection
signals are retained in [census.json](census.json); [verification.json](verification.json)
binds the report and implementation hashes.

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -v -s tools/proprietary-surfaces/v1 -p 'test_*.py'` | Exit 0; 34 tests |
| `python3 tools/proprietary-surfaces/v1/check.py --output /tmp/mcpcli-story-5-6/census.json` | Exit 0; all committed root pins accounted for |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py'` | Exit 0; 195 tests |
| `git diff --check` | Exit 0; Git emitted its existing missing commit-graph warning |
| Shared evidence secret scan | See [secret-scan.json](secret-scan.json) |

Census report SHA-256: `5f5fc96fe432a80099738eca193775545e145c6585349ece7c2db29943051d46`.
Baseline 1.0.0 SHA-256: `24f21275016798622d65b9272f95ee5f077fac060f76b278aea785d041822499`.
Amendment 1.0.1 SHA-256: `8339d6351499cbf21fa48aa8575733630183f359b6f883f9a1760fd0c1ef7f19`.

The baseline is derived from technical inventory 1.0.2 at its approved source
pins. The inventory's original bytes and Story 5.1 approval receipt are unchanged;
the scanner verifies their parent-commit hashes. Original PS01–PS14, PE01–PE09,
PN roots and FK consumers remain data. The only newly approved fixture
classification is the user's 2026-11-10 option A. Its separate 1.0.1 amendment
and approval receipt bind the complete committed directories of PublishSpike
and Epic16.NativeHelper at the pins already retained in [planning.json](planning.json).
The planning document remains findings-only and unchanged. Every file in each
fixture directory is hash-bound; changed secondary source, additional files and
removed files fail the source-closure guard.

The stale entry is PE01's exact historical Builds publication observation
`references/Hexalith.Builds`, `.github/workflows/ci.yml`, identity `test-g6-cli`.
It is exempt build tooling, not a production PS surface. Its baseline allowance
remains byte-for-byte present; staleness alone passes and no scan rewrites data.

Fixtures cover renamed and outside-src projects, inherited/imported metadata,
linked registrations, unresolved local tool metadata, package/tool/container
identity changes on approved projects, nonstandard manifests, orphan images and
publications, every approved exemption class, exact expiring exceptions,
inclusive UTC expiry, invalid policy/amendments, absent roots/objects, nested
gitlinks, regular source directories named references, and reference HEAD/worktree independence. Negative cases assert exit
status and the complete stdout/stderr contract. Selected guard mutations prove
that expiry and registration negative controls detect removal of those guards.
Release regressions require the census job and each initialization, fixture and
scan step when validating staging and publication evidence; historical bootstrap
recovery and the separate publication-stage job map are unchanged.

The gate reads Git trees/blobs only, never initializes nested references and
never executes inspected source, MSBuild or a discovered executable. No .NET
or live acceptance run is required by this Python/data/CI-only spec. Actual
GitHub CI execution remains for the resulting candidate; local fixtures prove
the workflow and release-evidence requirements. Existing concurrent Story 5.12,
Core/conformance and unrelated README edits were preserved and are excluded
from this story's completion claims. Only the MCP/CLI ownership addition to the
root README belongs to this story.

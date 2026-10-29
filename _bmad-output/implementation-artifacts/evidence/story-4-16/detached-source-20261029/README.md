# Detached release-source repair

The parent reported staging run `40857555958` failing with `ERELEASEBRANCHES` at source `513784a53226ae64e47a63fd76ea46222781a3ef`. An exact-SHA checkout can have detached HEAD with no local main; copying it into a mirror preserves that missing release branch.

The selector now creates/resets main at the captured source SHA and sets symbolic HEAD inside the temporary local mirror before cloning it. The original source refs, tags, HEAD and worktree stay unchanged.

`node --test scripts/tests/select-release-version.test.mjs` passed all three real local Git/semantic-release scenarios: absent main, main before the selected source, and main after the selected source on unrelated feature history. Every case selected the full captured source SHA and patch version 1.0.1. With the two mirror mutations removed, the same regression failed for missing main (`ERELEASEBRANCHES`) and unrelated later main (incorrect no-release result). This is a removal-sensitive control, not a mocked analyzer test.

`passing/` and `removed-fix/` preserve full fixture commit IDs, exact complete fixture messages, successful pinned commitlint validation before use, source ref/tag snapshots, selection receipts and subprocess diagnostics. The initial fixture attempt exposed an ignore-pattern issue for the node_modules symlink; it was corrected before the passing tests. Those initial fixture commit/validation records are also retained. The bootstrap workflow installs the existing pinned release dependencies under Node 24, runs this regression, and uploads its fixture evidence even on failure. Dependency versions are unchanged.

Workflow actionlint, both Node syntax checks and `git diff --check` passed. No .NET or conformance checks were rerun for this JS/workflow repair. No root commit, push, remote operation or workflow dispatch occurred in this handoff. The parent owns publication of these source changes and the next staging retry; Windows/macOS acceptance remains pending.

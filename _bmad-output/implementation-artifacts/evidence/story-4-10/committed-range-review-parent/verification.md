# Story 4.10 resumed build verification — 2026-10-21

The remaining committed-range patches R2–R12 and the resumed review patches are complete. Story 4.10's published Parties 1.5.1 enrollment, approval inputs, inventory and seven vectors remain unchanged. R13 is already tracked at `deferred-work.md:559` for a later agent-context refresh; this run adds no deferral.

## Result

All [13 final commands](final/checks.json) exit 0. The Release build has zero warnings/errors. [All six .NET projects](final/test-summary.json) pass **1,348 tests**, with zero failures and four existing Windows-only skips. Both sample conformance gates pass, including **107 Python tests**, three tracked-host CLI/MCP replays, nonempty enrollment, rejected pending inventory and deliberately failing semantic assertions. A fresh restore follows loopback before the final build and Manifest tests.

[Production enrollment](final/enrolled/enrolled.json) verifies the exact approved `Hexalith.Parties.Contracts` **1.5.1** archive, all seven vectors, strict discovery, clean lint and inventory, and full CLI/MCP replay. It uses no candidate dependency overrides and retains 53 restored package identities/hashes. All seven fresh description documents match the independently reviewed documents byte-for-byte.

## Changes and independent review

Candidate verification removes inherited enrolled-module references and replaces or creates its exact central package pin. It normalizes an arbitrary input filename from the root manifest while retaining the original source path, protects that selected snapshot from sibling-file replacement, and rejects unsafe filename identities before moving it. Tests cover exact lint refusal and approval through the verifier pipeline, malformed approval structure, missing or mismatched inventories, module-name preflight, stale-success invalidation, and enrollment without dependency overrides. Hash-bound files have LF checkout rules; README names, ordering and options match the built commands.

Three context-free review layers and parent triage are recorded in [review.json](review.json) and the [spec](../../../spec-4-10-add-parties-queries-and-pin-complete-coverage.md). The [focused implementation evidence](../committed-range-review-patches/verification.md) retains original-verifier failures, the successful real unlisted-candidate run and the Linux symlinked-temporary-root replay. Parent [guard-removal mutations](final/mutations/results.json) prove that bypassing either the verifier lint call or the safe-filename guard makes its regression fail.

The first parent run's exact `bash scripts/check-agent-instructions-sync.sh` command exited 1 because committed `CLAUDE.md` lacked its two opening managed-context comments. Its [original failure](instructions-sync.txt) is preserved. Copying `AGENTS.md` to `CLAUDE.md`, as explicitly required by the repository instructions, restores only those comments; all three files now match byte-for-byte and the final sync command exits 0. No instruction behavior or enrollment-context wording changed.

## Integrity and limits

[Final integrity](final/integrity.json) verifies all 11 protected approval/inventory/vector inputs and the frozen intent against their prior approved hashes. Reference gitlinks are unchanged. The unchanged upstream matrix test source matches the approved source manifest; retained passing upstream execution and the fresh Core run cover all 22 recorded covering tests across every frozen matrix row. No upstream source, release, approval or dependency pin changed in this run. The workflow records the completed local changes in a commit.

These checks establish artifact binding, coverage and scripted transport parity. Live authorization, persistent domain effects and legacy retirement remain the existing downstream gates. The symlink reproduction ran on Linux; no new native Windows or macOS run is claimed.

Staged evidence keeps hash-bound vector snapshots as binary to preserve their original CRLF bytes. Insignificant trailing spaces in new transcript lines are trimmed; no protected source input is normalized. The staged whitespace check passes.

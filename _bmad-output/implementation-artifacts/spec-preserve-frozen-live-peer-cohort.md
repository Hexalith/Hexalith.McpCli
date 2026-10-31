---
title: Preserve the complete approved live peer cohort
status: done
created: 2026-10-31
baseline_commit: c542fbbc4542e5a4323feecef3489cb2353ebb01
---

## Intent

The operator requests current dependencies and passing CI. Keep this repository's approved production artifacts and frozen SDK3.128.4 live compatibility profile intact while the direct Parties source adopts current catalog-enabled packages. Pin only the Parties peer's Memories3.0.11 and Tenants5.11.2 packages in that explicit profile. Other peers, the Gateway, approved vector inputs, authorization and persistence checks remain governed by their existing inputs.

CI41198566418 passed actual dependency closure and167of169 preflight checks. Its two failures identify stale reusable-workflow pins after the root-declared Builds pointer advanced toa22b55f0a4f6d2aaa3a5ccc505896064ac595364. Align both pins to that already selected owner commit without changing workflow behavior or weakening exact pin validation.

## File Scope

Allowed files for this story:

- `tools/live-topology/ci.py`
- `tools/live-topology/test_ci.py`
- `.github/workflows/ci.yml`
- `.github/workflows/commitlint.yml`
- `_bmad-output/implementation-artifacts/spec-preserve-frozen-live-peer-cohort.md`

## Verification

Run the existing CI hook/workflow tests including source command recording and both exact reusable-workflow pin assertions. The new assertions require both finite package pins on Parties and forbid either pin on the other source hosts. Preserve complete live discovery and require all21 hosted vectors before final release. Validate the exact full commit message with the pinned owner CLI and run real hooks before pushing.

Existing complete CI hook/workflow suite passed:109 tests,zero failures (see `/tmp/mcp-frozen-cohort-ci-tests.log`). Both actual workflow pins equal the selected root Builds gitlink; source command recording retains exact SDK3.128.4 plus the Parties-only compatible Memories/Tenants pins. Full hosted live acceptance remains outstanding and is not claimed by this metadata change.

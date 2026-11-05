# Tenants 7.0.4 local preparation for final publication review

Publication remains unauthorized. No new Release workflow has been dispatched. This packet describes the tested local candidate and every normal publication effect; all required exact-current-source hosted gates have passed.

The exact source is `8e20524574901d71ad5f4876804c64c3c6c87b88`. Locked semantic-release 25.0.9 selects **7.0.4**, after the now-public immutable `v7.0.3` tag. The candidate uses qualified public **EventStore 4.1.0**, source `dbc6e7e08d605ba6c6c790e3e08a15dc8bbdec8a`. [The local candidate receipt](../tenants/local-704/candidate.json) records each unsigned archive hash, source and SDK dependency; these hashes are not signed-public enrollment approvals.

The normal `release.yml` path would publish:

- `Hexalith.Tenants.Contracts` 7.0.4
- `Hexalith.Tenants.Client` 7.0.4
- `Hexalith.Tenants.Server` 7.0.4
- `Hexalith.Tenants.Testing` 7.0.4
- `Hexalith.Tenants.Aspire` 7.0.4
- `registry.hexalith.com/tenants:7.0.4` for `linux/amd64` and `linux/arm64`
- `registry.hexalith.com/tenants-api:7.0.4` for `linux/amd64` and `linux/arm64`
- Source-bound `v7.0.4` and its GitHub release/package assets.

All five real Release builds, manifest packing, package metadata checks, actual source-bound catalog consumer and package-only consumers pass. The catalog receipt records SDK 4.1.0, 23 routes, 23 operations and 12 adapters. Exact native compilation and public SDK DLL provenance pass; the retained 4.0.4 profile also builds and executes its real catalog cases. Failed pre-fix and environment-fixture checks remain preserved with their successful focused corrections.

Exact-source CI [42029976383](https://github.com/Hexalith/Hexalith.Tenants/actions/runs/42029976383), including mandatory Aspire job 127264107637, completed successfully. Source-reference [42029975839](https://github.com/Hexalith/Hexalith.Tenants/actions/runs/42029975839), story guards [42029976106](https://github.com/Hexalith/Hexalith.Tenants/actions/runs/42029976106), commitlint [42029976588](https://github.com/Hexalith/Hexalith.Tenants/actions/runs/42029976588) and CodeQL also pass. [Final run/job/step snapshots and current-main binding](../tenants/hosted-green-20261105T133938Z/qualification.json) preserve that observation; the owner worktree is clean. Recheck current main and all required latest exact-source attempts before publication dispatch, then retain and verify the workflow's actual prepared artifact and destination contents through the existing normal gates.

The unchanged pinned publisher source-workflow gate also passes using an official checksummed task-private GitHub CLI 2.103.3; original older-CLI refusal and tool/checksum provenance are preserved. All five 7.0.4 identities are unoccupied at the final read-only observation, and no release run is active. This observation is not production preflight.

The externally approved 7.0.3 release is valid for its source-bound 4.0.4 build and remains rejected for McpCli's planned 4.1 cohort. The original snapshots, later approval/publication audit and public signed archive checks are preserved in [the appended observation](../tenants/preparation/later-publication-observation.json). A shared production reviewer hold cannot guarantee preparation-only execution; this task will not dispatch another release before exact publication is explicitly authorized.

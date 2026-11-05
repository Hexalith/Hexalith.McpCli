# Tenants 7.0.3 preparation packet

Source: `Hexalith/Hexalith.Tenants@f4129cfe0a44b079a4f11f9cfb1374aed915f243`. Locked semantic-release selects **7.0.3**. The integrated guard hides rejection-only tenant checkpoints, preserves administrator/not-member responses and permits legitimate later creation. All 1,815 owner Server.Tests pass with zero skips; both new regression tests pass and removing the guard fails the intended test.

The existing `release.yml` requires successful exact-source push runs of `ci.yml`, `story-guards.yml` and `source-reference.yml`. Only after all pass may its unprotected `prepare-release` job build the immutable package candidate without NuGet or Zot publication credentials. The `production` environment has a mandatory reviewer rule for `jpiquot`; publication must remain held there. No publication approval is granted by this packet.

A final publication decision covers all of these actual side effects:

- `Hexalith.Tenants.Contracts` version `7.0.3`
- `Hexalith.Tenants.Client` version `7.0.3`
- `Hexalith.Tenants.Server` version `7.0.3`
- `Hexalith.Tenants.Testing` version `7.0.3`
- `Hexalith.Tenants.Aspire` version `7.0.3`

- `registry.hexalith.com/tenants:7.0.3` — `linux/amd64` and `linux/arm64`
- `registry.hexalith.com/tenants-api:7.0.3` — `linux/amd64` and `linux/arm64`

The normal workflow also creates Git tag/GitHub release `v7.0.3` at that exact source, retaining the five package assets and destination/content verification. The OCI platform set is mandatory in pinned Builds publisher `ff3b7628132059bc42e04fa8c98c1c427b528f62`. `registry.hexalith.com` is the configured workflow fallback; the registry repository variable is absent. Authenticated destination occupancy remains a protected preflight requirement.

Package archive hashes and the immutable preparation artifact/run binding will be added only after the preparation job succeeds. The selected package identities were unoccupied in the retained read-only feed observation; that observation is not production preflight. A changed source, selected version, artifact or gate needs a fresh concrete decision.

McpCli's metadata refresh remains blocked on the real public Tenants 7.0.3 cohort matching this source. Its existing exact source/archive gate requires that cohort; old 7.0.0 client acceptance does not qualify the fixed runtime source.

## Verified immutable preparation

Release run [42023389616](https://github.com/Hexalith/Hexalith.Tenants/actions/runs/42023389616) completed preparation. Artifact `13412349342` has verified SHA-256 `c54d61c15bf5c27a1cb8f4013cd66059e596089f6d05c540203fb2b1be9111d5`. Its source/version and all five embedded package identities/repository commits match this packet. Production publication is waiting for the configured review, and no approval was submitted.

| Package | Prepared archive SHA-256 |
| --- | --- |
| `Hexalith.Tenants.Aspire` | `78c88193f1657355fe04f1689d85eb647c5c1bfb36e9de1a6768e2b446a0a380` |
| `Hexalith.Tenants.Client` | `8faddec19aba67d77cb149c9634dd468402adeb325f5dcb4d442b1b4c707f34f` |
| `Hexalith.Tenants.Contracts` | `485c93e8118cc093904917ce22a6855fb854f80bfdca0fcdf0c8745ca0e7d59b` |
| `Hexalith.Tenants.Server` | `a8e2f7b4e21a3dac0346957c6d6292e1b5083d54e85ad50ed5c379f790b82f11` |
| `Hexalith.Tenants.Testing` | `33447c79d281d1827d1d314bb96bafe67b11657398f8d221e6c3608bc6ccc833` |

The exact SHA-512 values and original artifact/tar hashes are in `../tenants/preparation/verified-candidate.json`. NuGet repository signing can change public archive hashes; the later McpCli binding must use independently downloaded public bytes.

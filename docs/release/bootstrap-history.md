# Closed bootstrap history

AD-17 allowed one Abstractions publication before decorated Contracts existed. That bootstrap is closed. A public `Hexalith.McpCli` NuGet version independently blocks every new Abstractions-only push, including with absent/unavailable marker tags or ambient recovery variables. Uncertain registry responses fail closed. Proven first-ever tool absence requires two independent 404s and still does not bypass the existing paired-publication marker.

The historical verification allowlist is [scripts/bootstrap-history.json](../../scripts/bootstrap-history.json). It is fixed to these evidenced identities:

| Version/tag | Exact source SHA | Public publication UTC | Disposition |
| --- | --- | --- | --- |
| `1.0.0` / `v1.0.0` | `d9f822d64f7afa9bd51ca1698f5051147b86b554` | 2026-10-17 18:21:26.790 | Original one-time bootstrap. |
| `1.1.0` / `v1.1.0` | `8d4a8c07636c1ad065dfc8dc28dbfc956d5deb82` | 2026-10-27 20:19:03.930 | Separately accepted historical AD-17 process deviation. |
| `2.0.0` / `v2.0.0` | `06cfdf25a352034b36041e9ed44da514b167ca5a` | 2026-11-02 19:31:50.503 | Separately accepted historical AD-17 process deviation. |

The [read-only investigation](../../_bmad-output/implementation-artifacts/evidence/epic-4-retro-item-2-bootstrap/history-investigation.json), collected 2026-11-06 at baseline `9b44fe2026efa4b9234dd6a5c53e068b752a1837`, binds local and GitHub tags, public package nuspec commits, registry/catalog records and downloaded archive hashes. Its decision field records the investigation's then-pending state; the subsequent approved decisions below supersede that field. It records signature presence, without claiming cryptographic signature validation. Public signed-package SHA-256 values are:

| Abstractions version | Observed signed-package SHA-256 |
| --- | --- |
| `1.0.0` | `1bd30a88863b07a30c1d3ba9985f588c2d30e0bbb08f16a459258a8eea12e224` |
| `1.1.0` | `84af4f6005fe1846ab89fa95d237b070a7a7f6e57bf0d7586d9fbe46abd43173` |
| `2.0.0` | `d569654447a07f57cfe66c11a20716d8098b1879b39668521922775deed6e9ea` |

The [owner decision receipt](../../_bmad-output/implementation-artifacts/evidence/epic-4-retro-item-2-bootstrap/owner-decisions.json) records the subsequent authority separately from the investigation. On **2026-11-06**, after receiving the evidence and per-version recommendations, the requesting owner instructed **“apply recommended”**:

- **Abstractions 1.1.0:** accept this fixed historical AD-17 process deviation. [Release run 40576687691](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/40576687691) published it after decorated Parties and Tenants Contracts had been enrolled (2026-10-21 and 2026-10-22). A second independent bootstrap violated the one-time/shared-version rule.
- **Abstractions 2.0.0:** separately accept this fixed historical AD-17 process deviation. [Release run 41510077761](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/41510077761) published it alone for the coordinated dependency/platform-scope transition. The tool was not published at 2.0.0; the first public pair was 2.0.1. Platform-scope reconciliation is a separate decision and supplies no publication authorization.

Neither publication is reclassified as AD-17 compliant. These decisions grant no future bootstrap exception, authorize no package publication or tag changes, and leave the [Epic 4 retrospective's rejected verdict](../../_bmad-output/implementation-artifacts/epic-4-retro-2026-11-06.md#acceptance-verdict) unchanged.

Historical `Release` dispatch uses phase `bootstrap` and one explicit allowlisted recovery version. Empty/unknown versions, missing/moved tags, wrong SHAs, nonancestors, failed source gates and absent public packages are refused. Current main must pass full paired CI, commitlint and FR-22 prerequisites; historical source must independently pass its Bootstrap package/Commitlint push gates. Reviewed helpers and history survive checkout, and only root-declared baseline/build submodules are aligned before historical cleanliness checks.

Verification requires a clean exact-source preparation receipt, validates the rebuilt and already-public package, compares all consumer content (excluding NuGet signatures and packing core properties), runs the public-package analyzer consumer, and rechecks source gates. It obtains no NuGet publication key, performs no package push or GitHub release edits, and retains verification evidence in the run. Build-path/toolchain byte drift can require the original validated artifact and source-bound receipt; it never permits a replacement publication. Credential-free local bootstrap preparation and the paired publisher's bounded post-push processing wait remain available.

Current validation used synthetic packages and executable fixtures. It does not claim a current hosted rebuild and public-content verification rehearsal for all three historical releases.

The closure implementation at `078fd22bbbe591d6b912fa6e33967b174b61379a` passed [CI 42230625514 attempt 2](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/42230625514/attempts/2), including every approved live vector and smoke, Commitlint and Bootstrap package checks; [the qualification receipt](../../_bmad-output/implementation-artifacts/evidence/epic-4-retro-item-2-bootstrap/hosted-qualified-078fd22.json) binds the executed checks and live artifact digest. The first attempt's upstream rejected-bootstrap startup issue remains separately tracked in the deferred-work ledger. The complete unchanged live job was rerun; no assertion, deadline or dependency was relaxed. This qualification closes retrospective item 2 and leaves the retrospective verdict unchanged.

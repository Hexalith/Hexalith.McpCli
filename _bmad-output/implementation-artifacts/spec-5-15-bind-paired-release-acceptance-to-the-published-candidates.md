---
title: 'Bind paired release acceptance to the published candidates'
type: 'feature'
created: '2026-11-28'
status: 'in-progress'
route: 'dispatch'
baseline_commit: 'd51aa81c069b779a29c99b558ebd1cf3e8e3563c'
review_loop_iteration: 0
context:
  - '{project-root}/docs/release/operator-setup-checklist.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `README.md` and legacy release scripts still describe the removed `stage-paired`/`paired` workflow, while delivered `.github/workflows/release.yml` runs central `Hexalith.Builds@v6.9.1` (`delivered-sha`) and packs final `.nupkg`s on `ubuntu-latest` separately from CI fixture `.nupkg`s. Retro item 6 (F5, F14, F15) remains open: `smoke()` hard-codes `checks` without refusal tests, `verify-paired-publication.py` allows an unscoped human-validation bypass and reads the 685 s timing exception from `_bmad-output/`, and `compare-paired-evidence.py` writes stale Story 4.17–4.18 text.

**Approach:** Document the delivered central route (`delivered-sha`/nightly → exact-commit 3-OS CI → `Hexalith.Builds` build/draft → `hexalith-release` → publish), harden packaging/smoke/legacy F5–F15 scripts, add `scripts/verify-central-release.py` separating CI fixture hashes from final archive hashes, and run a non-publishing rehearsal.

## Boundaries & Constraints

**Recorded Owner Decisions (2026-11-28):**
- **Platform checks:** Exact-commit 3-OS CI (`ci.yml`) validates CI fixture packages; McpCli's local final-archive verifier/rehearsal gate validates final `ContinuousIntegrationBuild=true` `.nupkg`s (manifest, validator, tool smoke, consumer smoke, per-archive SHA-256s, exact-commit 3-OS CI receipt), and both packable projects set `HexalithVerifyPublishedPackage=true`. Supersedes historical `stage-paired` 3-OS final-archive staging (any central post-`build` 3-OS hook is an upstream `Hexalith.CiCd` follow-up).
- **Acceptance & bypass:** Adopt a hash-bound central acceptance record (`version`, 40-hex `source_sha`, final per-archive SHA-256s, exact-commit 3-OS CI receipt, non-bot human `approved_by`, timing-exception status; supersedes mandatory 3-client sessions) checked before `hexalith-release` approval; forbid `user-requested-human-validation-bypass` on future candidates. Move the 685 s timing exception to `docs/release/operator-setup-timing-exception.json`.
- **Legacy scripts:** Retain unwired `stage-paired`/`paired` scripts labeled historical; in `verify-paired-publication.py` pin bypass strictly to historical `2.0.1` (`aa2845edbea23444a1d362060b8d0f5dc05a132e`) and point `TIMING` to `docs/release/operator-setup-timing-exception.json`; fix stale `"stories 4.17–4.18"` text in `compare-paired-evidence.py`.
- **AD-17 hold:** Preserve the AD-17 / Platform AD-11 stable-tool promotion hold in `README.md` and `docs/release/` until Platform, McpCli, and CiCd owners record the joint release track.

**Always:**
- Preserve `Hexalith.CiCd` ownership: never edit `.github/workflows/**`, `.github/hexalith-ci.json`, `.github/dependabot.yml`, or `references/**`, and never assert workflow YAML text in tests.
- Keep CI fixture `.nupkg` hashes (`prepared.json`) separate from final `.nupkg` hashes (`release-manifest.json` / `hexalith-package-publication.v1.json`) and signed nuget.org hashes.
- Derive `smoke.json` `checks` from executed checks and cover every `smoke()`, F5/F14, and central-verifier refusal with removal-sensitive tests.
- Preserve `_bmad-output/implementation-artifacts/evidence/**` and `scripts/bootstrap-history.json`; keep rehearsal strictly non-publishing.

**Never:**
- Treat CI fixture hashes, a workflow bundle digest alone, or prior-version acceptance as proof of final `.nupkg` bytes.
- Weaken `scripts/product_ci.py` CI interfaces, redaction/secret scanning, or `NuGetAudit`, or commit/push during this build.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid rehearsal pair | Clean `source_sha`, packed `ContinuousIntegrationBuild=true` pair, validator/smoke/consumer + 3-OS CI receipts, valid central acceptance | Passes; emits receipt separating CI fixture vs final archive hashes | N/A |
| Changed package digest | Final `.nupkg` byte modified or differs from acceptance | Stops promotion | Non-zero exit naming package & digest |
| Wrong source SHA | `.nuspec` commit, CI receipt, or acceptance disagrees | Stops promotion | Non-zero exit naming source mismatch |
| Missing/invalid acceptance | Absent file, bot actor, bad timestamp, wrong version/pair, or bypass attempt | Stops promotion | Non-zero exit naming acceptance error |
| Fixture substituted for final | Acceptance binds CI `prepared.json` hash instead of final `.nupkg` hash | Stops promotion | Non-zero exit rejecting fixture hash |
| Legacy F5 bypass/timing | `verify-paired-publication.py` bypass for non-`2.0.1`/non-`aa2845ed...`, or invalid timing exception | Refuses future bypass; validates `docs/release/operator-setup-timing-exception.json` | Raises `ValueError` |
| `smoke()` refusals (F15) | Fake tool: bad version, stderr, CRLF/BOM JSON, empty catalog, `--output`/table/invalid-`MCPCLI_HOME` mismatch, post-smoke mutation | Fails before `smoke.json`; `checks` built from executed checks only | Raises `ValueError`; no `smoke.json` |

</frozen-after-approval>

## Code Map

- `tools/release-packages.json:1-12` -- Manifest pair (`Hexalith.McpCli.Abstractions`, `Hexalith.McpCli`).
- `Directory.Build.props:43-45`, `src/Hexalith.McpCli/Hexalith.McpCli.csproj:6-16`, `src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj:2-6` -- Default `IsPackable=false`; opt in only the two manifest projects and set `HexalithVerifyPublishedPackage=true`.
- `scripts/smoke-paired-tool.py:22-91` & `scripts/tests/test_paired_smoke.py:1-188` -- Dynamic `checks`; direct fake-tool `smoke()` refusal tests.
- `scripts/product_packages.py:1-118`, `scripts/validate-release-packages.py:1-270`, `scripts/smoke_bootstrap_consumer.py:1-107`, `scripts/run-paired-platform-tests.py:1-117`, `scripts/evidence_redaction.py:1-414` -- Reuse unchanged; keep `.github/actions/*` contracts intact.
- `scripts/verify-central-release.py` & `scripts/tests/test_central_release.py` (new) -- Central-route candidate & post-publish (`hexalith-package-publication.v1.json`) verifier.
- `docs/release/operator-setup-timing-exception.json` (new), `scripts/verify-paired-publication.py:35,174-258`, `scripts/compare-paired-evidence.py:123`, `tools/manual-release-tests/test_paired_acceptance_source.py` -- F5/F14 fixes, historical labels, and unit tests.
- `README.md:91-174,243,298,320,684`, `docs/release/operator-setup-checklist.md:1-111`, `docs/release/bootstrap-history.md:28` -- Central route, exact `delivered-sha` dispatch input, decisions, AD-17 hold, historical labels.
- `_bmad-output/implementation-artifacts/sprint-status.yaml:108,306-313` -- Record Story 5.15 and retro item 6 results.
- **Do not change:** `.github/workflows/**`, `.github/hexalith-ci.json`, `.github/dependabot.yml`, `references/**`, `_bmad-output/implementation-artifacts/evidence/**`, `scripts/bootstrap-history.json`.

## Tasks & Acceptance

**Execution:**
- [x] `Directory.Build.props`, `src/Hexalith.McpCli/Hexalith.McpCli.csproj`, `src/Hexalith.McpCli.Abstractions/Hexalith.McpCli.Abstractions.csproj` -- Default `IsPackable=false`, opt in only the two manifest projects, enable `HexalithVerifyPublishedPackage=true` -- aligns `release_build.py` with manifest and enables nuget.org signature checks.
- [x] `scripts/smoke-paired-tool.py` & `scripts/tests/test_paired_smoke.py` -- Derive `checks` dynamically and test every `smoke()` refusal path -- closes F15.
- [x] `docs/release/operator-setup-timing-exception.json`, `scripts/verify-paired-publication.py`, `scripts/compare-paired-evidence.py`, `tools/manual-release-tests/test_paired_acceptance_source.py` -- Move timing exception off `_bmad-output/`, pin legacy bypass to `2.0.1`/`aa2845ed...`, fix F14 literal, label historical, unit-test F5/F14 guards -- closes F5/F14.
- [x] `scripts/verify-central-release.py` & `scripts/tests/test_central_release.py` -- Implement and test central candidate & post-publish verifier -- enforces AC2/AC3.
- [x] `README.md`, `docs/release/operator-setup-checklist.md`, `docs/release/bootstrap-history.md` -- Document central nightly/`delivered-sha` route, dispatch input, recorded decisions, AD-17 hold, and historical labels -- satisfies AC1/AC2.
- [ ] Rehearsal & `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Run positive + negative non-publishing rehearsal, verify `Manifest.Tests` and `check.py`, record results for 5.15 and retro item 6 -- satisfies AC3.

**Acceptance Criteria:**
- Given `.github/workflows/release.yml` (`delivered-sha`) and `Hexalith.Builds@v6.9.1`, when reading `README.md` and `docs/release/`, then one procedure traces exact-commit CI → packaging → approval → publication, dispatch parameters match `release.yml`, owner decisions and AD-17 hold are recorded, and historical material is clearly labeled.
- Given recorded owner decisions, when building/verifying candidates, then CI fixture and final archive hashes stay separate, `IsPackable=true` matches `tools/release-packages.json`, and both projects set `HexalithVerifyPublishedPackage=true`.
- Given a non-publishing rehearsal, when verified against manifest, validator/smoke/consumer, 3-OS CI receipt, and central acceptance, then valid archives pass, tamper/source/fixture/acceptance violations fail non-zero, and retro item 6 is closed and recorded.

## Implementation Notes

- The delivered workflow pin advanced to Builds `v6.9.2` during the build. The operator procedure follows the delivered pin and requires confirmation of the CI run, original release artifact and approver identity before environment approval.
- `check-archives` runs the existing validator, tool smoke and consumer smoke against the same final archives. Candidate verification requires the release manifest and CI fixture preparation receipt. Post-publication checks require the candidate receipt.
- Retro item 6 is complete. Direct smoke tests cover the refusal matrix, the legacy approval bypass is pinned to the historical pair and the 685-second timing exception now lives under `docs/release/`. The legacy comparator identifies its receipt as staging-only.

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `python3 -m unittest discover -v -s scripts/tests -p 'test_*.py'` -- all unit tests pass.
- `python3 -m unittest discover -v -s tools/manual-release-tests -p 'test_*.py'` -- all manual release tests pass.
- `dotnet restore Hexalith.McpCli.slnx && dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror && dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` -- 0 warnings, all Manifest tests pass.
- Non-publishing rehearsal via `scripts/verify-central-release.py` on packed `ContinuousIntegrationBuild=true` pair + tamper/source/fixture/acceptance negatives -- valid passes, all negatives exit non-zero.
- `python3 references/Hexalith.Builds/check.py` -- exit 0.

**Verification results (2026-11-28):**

- The Python release tooling suite passed 98/98 and the manual release suite passed 28/28. The executed tests cover the frozen refusal matrix.
- Release solution build passed with zero warnings and errors. Manifest.Tests passed 435/435. Evaluated package properties match the exact manifest pair.
- The non-publishing rehearsal exercised the updated verifier against two actual Builds `v6.9.2` release-flag archives packed from clean source `9e77b81a6a08055b4330448616130f35ea324f29`. Validator, installed tool and compiler consumer passed. The positive receipt separates real CI fixture and final archive hashes. Nine CLI refusal cases exited 1, covering tampering, source mismatches, fixture substitution, missing acceptance, bot actor, invalid timestamp and bypass. CI results and the human decision in the rehearsal were synthetic inputs for local verification.
- `run-with-temp python3 references/Hexalith.Builds/check.py` exited 1. The Builds checkout is `91cb7cba990ffdf82930f9bf8cb68aef41baba76` and the committed gitlink is `bb38c3e42f48f37de76c77983e4de83d99f619b7`. This checker also requires clean committed inputs. The story stays in progress pending that gate and BMAD review.
- The shared checker passed on a disposable checkout of baseline `9e77b81a6a08055b4330448616130f35ea324f29` with the correct Builds pin. All six ordinary test projects passed with 2,232 successes and 15 platform or opt-in skips. This result applies to that committed baseline.

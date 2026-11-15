---
title: Migrate the product and verified release cohort to .NET 11
type: feature
created: 2026-11-14
status: done
route: dispatch
review_loop_iteration: 0
baseline_commit: 4ffb33e84fd12a2642deb19b3492ce67ae670cee
context: []
---

<frozen-after-approval reason="User explicitly chose the .NET 11 product migration and authorized release without human validation">

## Intent

The user requests all changes pushed, root submodules synchronized, latest SDK/packages, repaired CI, and a published Release with NuGet verification. The user explicitly answered **Include the .NET 11 product migration**. Retain the completed synchronization and CI repairs, migrate product and active verification infrastructure to .NET 11, consume current public EventStore 5.1.0, Tenants 8.0.0, Commons 3.0.0 and Roslyn 5.12.0, then obtain fresh hosted live and three-platform package acceptance before publishing the identical pair.

## Boundaries & Constraints

Preserve user changes and historical evidence, inventories, approval bytes and original v1 vectors/plans/provenance. Keep production generic, dependency boundaries strict, canonical tenant/ULID rules and all output/authorization/persistence/cleanup gates. The analyzer remains netstandard2.0; product/Abstractions and ordinary test hosts become net11.0. SDK minimum is 11.0.100. Existing public Parties 3.1.1 remains the latest package and is metadata-compatible; owner source must explicitly support SDK5.1 rather than receive forced downstream symbols.

Decoration authorizes exposure: Tenants8's RefreshTenantAccess becomes discoverable. Authoritative C# OperationShape.From confirms it shares an already approved shape; inventory omission/version differences remain explicit reports. Do not invent shape keys, pin counts, widen gates or silently suppress findings. No extra module-specific production logic or identity server is authorized.

References remain read-only; necessary upstream changes happen in separate owning checkouts, with user changes elsewhere untouched. Only root dependencies may be initialized. Validate exact complete commit messages using owning pinned commitlint before every commit, including private snapshots. Use run-with-temp for disposable work and retain logs outside TMPDIR. The explicit bypass removes human approval pauses; automated source, byte-integrity, behavior, platform and publication gates remain mandatory. Never claim fresh client sessions or human byte review.

</frozen-after-approval>

## Code Map

- `Directory.Build.props`, `src/Hexalith.McpCli.Mcp/*.csproj`: active TFM/pins; SDK11 already current. `src/Hexalith.McpCli.Core/*.csproj`: remove redundant DI/Logging Abstractions references now provided by the shared framework; no production C# change needed.
- `tools/dependency-policy.json`, Manifest `RestoredDependencyGraph.cs` and exact fixture assertions: genuine net11 restore prunes13 framework identities, adds zero; dynamic sole-framework loader preserves historical fixtures. Probe107 policy tests passed without changing historical JSON.
- `.github/workflows/`, `scripts/`, conformance tools, active C# tests: current output/packaged-tool paths move to net11. Paired publication stays strictly portable net11; non-publishing bootstrap and fixed historical recovery must validate their effective checked-out source TFM, including historical net10 archives.
- `tools/live-topology/{ci.py,native_cohort.py,native-runtime-current.json,runtime-profile-current.json}` and AppHost/Integration: current SDK5.1/Tenants8 tuple, exact public archives/source commits, net11 output paths, owned runtime policy and audit seals. Preserve original selections and crossed-cohort refusals. Remove obsolete net10 compatibility injections with equally strict finite current policy.
- Gateway `Configuration/provenance-current.json`:5.1 source49084f66f8d6545cae442875355a7066d5f5e73d; actual native configuration bytes equal existing snapshots. Tenants8 public source0cfe90e887e4d9d9f0168cba98fca1852cb80313. Parties owner-source prerequisite commit785f8164d51579a191405a15a917232795f93449 admits exact5.1; no owner package publication required. Platform generic reader path needs no named-cohort expansion.
- `/home/administrator/mcpcli-maintenance-20261114/net11-recon/`: reproducible API/build/policy/shape probes, measured package manifests and upstream patch/bundle. Public-package hashes are measured, never invented. Root source selections need actual hosted live qualification.
- `tools/proprietary-surfaces/v1/`: preserve baseline and amendments through1.0.11; inspect any further source drift and append1.0.12 only where necessary. Preserve previous packet as pre-migration evidence.

## Tasks & Acceptance

- [x] `Directory.Build.props`, production csproj files -- select net11/latest packages, remove redundant references/obsolete holds; preserve analyzer netstandard target and warning-free build.
- [x] `tools/dependency-policy.json`, Manifest graph loader/assertions -- reflect real pruned closure, preserve ID boundaries and all historical refusal tests.
- [x] `.github/workflows/`, `scripts/`, active conformance and test files -- migrate current TFM/path/packaging/consumer assumptions, keep historical recovery valid and pair strictness intact.
- [x] `tools/live-topology/`, AppHost, Integration and current gateway provenance -- rebind measured SDK5.1/Tenants8/public-Parties3.1.1 inputs and qualified owner source; preserve namespace, mTLS, default-deny, authentic persisted-state/vector/smoke/boundary checks and every integrity/cancellation/cleanup guard.
- [x] Current vectors/approvals/plans -- preserve behavior and historical bytes; version differences may remain reported under existing policy. No additional per-operation vector is required for the already-covered RefreshTenantAccess shape; do not claim its downstream repair semantics proven.
- [x] Census lineage and `evidence/net11-release-20261115/` -- retain explicit framework decision, public integrity/API observations, exact new source classification and truthful fresh-cache consumer proof. Preserve the corrected SDK10 false-positive evidence.
- [x] `README.md`, live/conformance docs, `AGENTS.md` copied to CLAUDE/Copilot -- document actual net11 requirements/current cohort; keep entry points byte-identical and run sync check.
- [x] Verify restore/Release build, individual six suites, focused policy/shape gates, Python release/census/topology/conformance suites, full sample/production replay, strict catalog benchmark and a freshly packed net11 consumer in an explicitly private cache. Do not reuse cached public2.0.1 bytes as candidate proof.
- [ ] Primary orchestration after review -- publish prerequisite owner commit, record remotely available reference, commit/push main, fix fresh CI, stage on Linux/Windows/macOS, record authenticated candidate-bound automated acceptance, publish and verify both signed public packages plus installed tool/consumer.

Given the final source, when validation completes, then all production projects target net11 with latest packages and no new disallowed identities; historical guards retain their coverage. Given current public Contracts, when catalog/shape checks run, then22 decorated operations have complete shape coverage and the new unmentioned operation is reported. Given the final committed main, when full hosted CI and staging pass, then publication uses those exact archives and both public packages verify at one new version. No local preflight or old net10 result supplies live/release acceptance.

## Implementation Notes

The user changed the framework decision after pre-migration work completed. The earlier workflow approval checkpoint is bypassed by explicit user instruction. SDK10 positive consumer observations were invalidated after a private-cache check found the fresh analyzer's Immutable11 dependency; preserve that correction. All pre-migration results below qualify only their earlier source/configuration, not the new migration.


The user explicitly bypassed human validation; no additional spec approval pause is required. Initial source and all root submodules were clean; remote fetches found no local-only commits. Thirteen root references were fast-forwarded, with no nested submodule initialization. Independent investigation confirmed official NuGet archive targets for the newer incompatible majors. An optional target-migration preference was requested asynchronously; dependent migration work is excluded under the stated maintenance assumption unless the user answers otherwise.

Implementation selects eleven newer existing production identities, plus Redis 3.4.35 in the isolated test graph and build-time Microsoft.CodeAnalysis.Analyzers 5.12.0. Common/CSharp currently stay at 5.9.0, but the earlier SDK10 success claim is invalidated: the parent follow-up command omitted the private package cache and could reuse the public 2.0.1 package. A corrected fresh-byte SDK 10.0.404 probe with an explicit private cache fails CS8032 because System.Collections.Immutable 11 is missing; SDK11 passes. The original observations and correction are retained in `sdk10-proof-correction.json`. Subsequent explicit user steering now includes the .NET 11 product migration; the primary agent is replanning that migration and SDK10 compatibility work has stopped. The final production outdated audit reports only the four explicitly retained net11-only major candidates. The finite production package ID set, Contracts artifacts, native source/runtime profiles and historical approval bytes are unchanged.

The npm lock refresh keeps all direct tooling pins and package IDs, updates fifteen compatible transitive selections, removes the high advisory and one moderate advisory, and retains 36 moderate developer-tool findings whose proposed npm fixes downgrade current semantic-release/plugin majors. No forced downgrade or override is applied.

An observed CLI test failure compared concurrent MCP log emission order between independent sessions. Its comparison now preserves every complete diagnostic record and count while sorting records after existing duration normalization; all output/document/admin-isolation checks remain. The focused six cases and full final CLI suite pass. A separate initial Manifest Compile-item JSON parse failure did not reproduce in a raw-channel focused run or either subsequent full Manifest run; no parser workaround was applied.

The 250-test topology run had one deterministic workflow-reference failure after the authorized Builds move; 249 other cases passed. Renewed exact catalog/executor expectations and their mutation fixtures retain every mode/type/path/reference-list/equality check. A concrete task receipt records that both selected reusable workflow bodies are byte-identical to the previous executor and that frozen runtime JSON is unchanged. All four focused workflow tests pass against a private snapshot containing the selected gitlink. That snapshot message was validated with the pinned commitlint before use; the earlier local descriptive-message rejection is retained outside the repository and replaced in current verification evidence.

Census 1.0.11 adopts the exact inspected mutation arrays under the retained original user delegation: five allowance renewals, three literal catalog-test observations and seven exact-file classifications. The strict scanner and 222 refusal tests remain unchanged; the pending-reference scan passes all 17 roots and 444 surfaces. Large raw reports and complete command logs are retained outside the repository under `/home/administrator/mcpcli-maintenance-20261114`; the tracked task packet carries concise findings and exact bound source/mutation proof. These local checks do not establish hosted exact-source, live, cross-platform staging or publication acceptance.


Local .NET 11 implementation is complete. Product and active verification paths use net11.0; the analyzer remains netstandard2.0 with Roslyn 5.12. The actual restored production closure prunes thirteen identities and adds none. SDK5.1/Tenants8/public-Parties3.1.1 native inputs and the published Parties owner prerequisite are bound without changing historical approval/vector/plan bytes. The six ordinary suites, final 110-case focused policy check, 14 coverage cases, Python release/census/topology checks, sample packaged-process replay, production replay and strict benchmark pass. The cold process measured 130.4359 ms; C# discovery reports 22 operations and the existing policy retains 17 explicit version/inventory reports. A newly packed net11 Abstractions package and its single explicit private consumer cache match archive bytes, with exactly one expected analyzer warning. Evidence and limitations are retained in `evidence/net11-release-20261115/`.

The first private Manifest run found an old Gateway source-SHA assertion; its corrected suite passes all 372 existing cases. A later added refusal test protects the loader's sole-framework guard and passes in the 110-case policy lane. The initial synthetic CI run had 108/111 passes: two obsolete logging/pruning expectations were corrected and pass individually, while the old root-HEAD Builds positive passes in the four committed-snapshot workflow cases. All 139 remaining topology cases pass with exact complete current report expectations; runner reporting is unchanged. An external harness literal trailing-separator comparison was corrected and the fresh pack/consumer proof repeated successfully. The pre-migration correction logs were renamed to .txt with exact bytes preserved so normal staging retains them.

The read-only Parties owner audit preserves a red full owner CI: eight deterministic failures already fail identically at its parent, plus one intermittent unchanged v4.0.4 child exit. Independent current capability lanes and twenty local parent/current rechecks pass; no SDK5.1 admission defect was identified. This does not supply native acceptance. Primary orchestration still requires review, exact committed-source full hosted CI/live semantics, three-platform immutable staging, candidate-bound automated acceptance, paired publication and independent signed public package/tool/consumer verification. No local result or prior net10 acceptance replaces those gates.

## Spec Change Log

2026-11-15: Explicit user answer supersedes the net10 compatibility scope. Retain successful synchronization/CI repairs, regenerate active tasks around net11 and measured public cohort; preserve all original evidence and newly created pre-migration packet.

## Review Triage Log

The implementation/review workflow is complete after the focused corrections below; no review finding is deferred. The primary release continuation remains explicitly pending at this source commit and must satisfy the hosted gates before publication.

| Finding | Verdict and route | Evidence |
| --- | --- | --- |
| Blind 1 — quick-start runtime | medium / patch | README quick start still requires Core 10 and explicitly excludes an 11-only machine; the new tool requires Core 11. Correct the prerequisite. |
| Blind 2 — unchecked ref target | medium / patch, grouped with Edge 1 | The new lib-only guard accepts ref/net10.0 beside lib/net11.0. Independent real NuGet restore selects the older ref assembly, violating the sole-target policy. Include ref assets in the TFM guard. |
| Blind 3 — RID payload | medium / patch | Paired validation accepts runtimes/linux-x64/lib/net10.0 in Abstractions despite portable effective properties. Reject RID payloads and retain explicit refusal cases. |
| Blind 4 — extra assets targets | false / reject | The loader selects the sole declared project framework by its exact target key. Extra NuGet RID targets are not selected and do not alter that portable closure; their mere presence does not demonstrate an admitted dependency or a wrong graph. The new test protects ambiguous declared frameworks. |
| Blind 5 — later runtime patch | false / reject | The exact highest-runtime 11.0.0 refusal already exists at baseline 4ffb33e. Current profile documentation explicitly requires it and forbids unmeasured substitution; current latest SDK supplies that runtime. A future unqualified patch is deliberately refused and requires profile requalification. Installing an exact SDK alone would not remove other preinstalled runtimes. |
| Blind 6 — SDK feature-band wording | low / patch | The analyzer minimum is correct for consumers, but repository global.json selects latestPatch within 11.0.1xx. State that repository selection separately so a developer knows why an otherwise newer SDK is not selected. |
| Blind 7 — historical tuple positive | low / patch | The closed 4.2.0/7.0.7 map remains supported but its former positive moved to 5.1. Add a valid synthetic manifest case so deleting the retained tuple fails a test. |
| Blind 8 — fixture target | low / patch | AdapterDependencyTests constructs a v10 deps target with new lib/net11 assets. Change its synthetic current target to v11; keep real-asset verification and refusal controls. |
| Blind 9 — actual historical consumer | low / patch verified | Added real archived v1.0.0 evidence: pinned historical Builds, SDK10.0.404, restore/build/pack, current bootstrap validation, and current private-cache consumer all pass. Candidate/cache archive bytes match and the analyzer emits exactly one expected warning. See historical-source-consumer.json; no registry writes. |
| Blind 10 — integrated synthetic result | false / reject | The packet explicitly reports 108/111 plus corrected cases and does not claim a full final integrated success. The mandatory exact-commit hosted lane runs the complete synthetic suite again before live preparation; publication cannot consume only these local partial receipts. |
| Edge 1 — unchecked ref target | medium / patch, grouped with Blind 2 | Reviewer reproduced actual NuGet selection of ref/net10.0 in a net11 consumer, and paired validation accepts that layout. Fix the lib/ref target policy and add negative cases. |
| Verification 1 — native receipt version | medium / patch | Pre-verified gap: MatchingReadbacksRetainSanitizedInventory executes the writer but does not assert sdkVersion. Changing the migrated value back to 4.2 leaves the test green. Compare it with the current manifest eventStoreVersion. |

## Verification

Run disposable checks under run-with-temp; logs in the external task directory. Use narrow checks after fixes, then final required full gates. No skip/suppression substitutes for passing behavior. Root requires fresh exact-SHA hosted CI/live, immutable three-OS staging, automated candidate-bound acceptance, paired publication and independent official NuGet signature/content/consumer/tool verification.

### Post-review hosted CI source alignment correction

Exact-source CI run43660988102/job132651837186 at dc39e2644fec0a8e4abcd74d1a1d9334b7634e26 correctly refused the native catalog reader's different prepared Google.Protobuf.dll. Source preparation validated all eleven root package selections but serialized only Redis into the owner overlay/hook, leaving owners on Protobuf3.35.0/gRPC2.80.0 while root/reader selected3.36.2/2.85.0. The correction serializes every finite validated selection and makes the later hook add absent rows and update existing ones while retaining metadata. Reader byte equality, restore audit and input seals remain unchanged.

Four focused CI-hook tests pass, covering real MSBuild overlay-only, hook-only and combined evaluation, exact row counts, malformed selections and special paths. A disposable real build of the three exact archived owner projects reproduces the original policy's reader byte refusal; corrected overlay and hook-only package graphs match, and actual unmodified reader restore/audit/build/catalog generation passes. All common DLLs match for Tenants54, Parties55 and adapter53. New evidence is isolated in `evidence/net11-ci-source-alignment-20261115/`; prior observations and review triage are preserved. This focused proof starts no services and does not establish hosted live or release acceptance; primary continuation remains pending.

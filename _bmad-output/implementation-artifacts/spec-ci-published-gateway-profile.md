---
status: done
date: '2026-10-31'
route: dispatch
---

# Qualify the isolated CI lane against the published gateway cohort

## Intent

<frozen-after-approval>
Fix the remaining McpCli live CI failure using an explicitly selected test profile
for the published EventStore 3.128.4 cohort. Preserve the native gateway default,
publication behavior, all 21 approved semantic vectors, independent authenticated
smoke, genuine projection-writer activation, persisted-state observations and
owned infrastructure cleanup. The user authorized the CI repairs and execution
without another human checkpoint. No production catalog validation is weakened.
</frozen-after-approval>

## Evidence and code map

CI 41178733269 passes packaged builds, unit tests and conformance replay. Its live
lane starts a newer source gateway without the native catalog bootstrap and mixes
source Tenants with package Parties. Native gateway logs refuse missing independent
catalog host identity/profile. The previously selected Tenants also scanned gateway
MediatR handlers; adopting the owner's corrected commit fixes that separate DI crash.

- `tests/Hexalith.McpCli.AppHost/Program.cs` selects the gateway before registration.
- `TopologyConfiguration.cs` validates owned inputs and will resolve the selected
  project without modifying existing project metadata.
- `tools/live-topology/ci.py` prepares source hosts and propagates the selected,
  source-bound gateway cohort privately to isolated children.
- The existing Parties package test host demonstrates package composition with
  native defaults at the lowest configuration priority and matching launch profiles.
- `TopologyLaunchTests.cs` inspects real AppHost composition without starting Dapr.
- `tools/dependency-policy.json` separates approved test packages from production.

## Tasks

1. Add an owned, nonpackable, nonpublishable Web test host referencing the existing
   centrally pinned Gateway package. Link native appsettings and launch profiles;
   preserve normal configuration precedence and the actual platform middleware.
2. Add the host to the solution and test-only dependency allowlist. Keep the AppHost
   free of gateway runtime project/package references.
3. Resolve the package host before `AddProject` only for explicit run-mode selection;
   refuse a missing host. Native/default and publish models retain the native project.
4. Prepare CI against one exact published EventStore cohort, compile both domain
   hosts with package dependencies, retain the selected gateway package provenance,
   and propagate the profile privately to both vector and independent smoke children.
5. Bind writer activation evidence to the deployed package's actual source commit,
   preserving the original source-commit path for native runs.
6. Extend composition and preparation tests to cover selection, package cohort,
   missing-host refusal and unchanged authentication/ACL/token wiring. Update lane docs.
7. Build the owned host and isolated test project, run focused preparation/composition
   tests, then execute a genuine isolated smoke and representative persisted semantic
   vector before asking the parent to publish the change and observe all 21 CI cases.

## Acceptance criteria

- Given no explicit package selection or a publish model, when the AppHost resolves
  its gateway, then it selects the native project.
- Given explicit package selection in run mode, when composition is inspected, then
  only the gateway project changes; endpoints, ACL, app tokens and JWT configuration
  retain their asserted contracts. A missing package host fails before registration.
- Given CI preparation, when hosts build, then gateway and domains use EventStore
  3.128.4 packages and provenance is retained and passed to every isolated child.
- Given live qualification, when smoke and semantic vectors execute, then real
  authentication, administrator authority, writer activation, persisted observations
  and private-runtime cleanup must all pass without skipped or fabricated evidence.

## Validation

- Gateway test host, integration test project and both owner domain hosts build
  in Release with zero warnings/errors against EventStore 3.128.4. Original
  checkouts were not initialized recursively or cleaned.
- `python3 -m unittest discover -s tools/live-topology -p test_ci.py -v`:
  65/65 passed, including cohort drift, package-byte drift and private child binding.
- The owner declares Builds `4d93e4fdec4f0e3805a42f4206bc0c8ddb92ac26`.
  Local fallback initially imported the umbrella's newer catalog and exposed six
  exact dependency-policy mismatches. Rebuilding with
  `-p:HexalithBuildPackageVersions1=/tmp/mcpcli-owner-builds-4d93/Props/Directory.Packages.props`
  uses the exact committed catalog blob and resolves those mismatches. The final
  four-class configuration/composition/ACL/dependency suite passes 188/188.
- An ordinary disposable standalone checkout under
  `/tmp/mcpcli-published-qualification-hm6ub5jz/McpCli` preserves the selected owner
  revisions and catalog without initializing/updating nested submodules or
  mutating original producer checkouts. Actual restored Gateway 3.128.4 provenance
  resolves to source `717a06e16c3afd81b904eaf4de646b74b13262d2` and SHA-256
  `16cb74a6a9d5d06841f7d4e49035bf841861d66fb42cfc9549764c8aa7352e19`.
- The first real smoke exposed missing Tenants bound-stream proof configuration.
  The package profile now supplies fresh RSA key material, matching public trust,
  exact workload audiences and only the owned stream-read scope; production
  assertion and administrator-authority validators remain enforced.
- The real isolated authenticated smoke passes 1/1 with no skips in 19.226 seconds;
  `/tmp/mcpcli-qualified-smoke2.xml` retains its result and owned cleanup receipts.
- The unchanged `parties.update-party` vector passes 1/1 in 27.784 seconds with
  real writer activation, persisted initial/update observations and owned cleanup.
  Its diagnostic receipt is
  `/tmp/mcpcli-published-qualification-hm6ub5jz/party-update/live-lane.json`.
  It deliberately records `fullLiveAccepted=false`; hosted CI must execute all 21.
- The unchanged `tenants.change-user-role` vector also passes with genuine
  administrator/owner authority, persisted tenant/user/role transitions, writer
  activation and owned cleanup. Its diagnostic receipt is
  `/tmp/mcpcli-published-qualification-hm6ub5jz/tenant-role/live-lane.json`.
- Local live checks use installed Aspire CLI/bundle 13.6.4. Hosted CI retains its
  qualified 13.6.1 archive/bundle; no user bundle was overwritten for this task.
- Exact source CI and complete 21-vector hosted acceptance remain required.


## Review Triage Log

| Finding | Verdict | Evidence / route |
|---|---|---|
| Blind1 domain graph cohort | medium | Property echo does not inspect restored domain libraries; validate both actual asset graphs. Patch under existing immutable-profile/qualification intent. |
| Blind2 deployed binary binding | medium | Mutated gateway output leaves prior archive-only receipt unchanged; bind actual deployed DLLs to archive contents and source metadata. Patch under existing immutable-profile/qualification intent. |
| Blind3 configuration binding | medium | Linked independently selected source defaults are not sealed in receipt; retain explicit file/source identities and hashes. Patch under existing immutable-profile/qualification intent. |
| Blind4 smoke recheck | medium | Current provenance check precedes the full vector lane only; repeat immediately before independent smoke. Patch under existing immutable-profile/qualification intent. |
| Blind5 private-key diagnostics | high | Existing PEM/SigningKey sanitizer misses the new base64 BoundStreamRead PrivateKey field in serialized diagnostics; add targeted redaction forms and leak-negative tests. Patch under existing immutable-profile/qualification intent. |
| Blind6 Kestrel limit | medium | Direct GetService<KestrelServerOptions> returns null under ordinary options DI; configure the real server before startup. Patch under existing immutable-profile/qualification intent. |
| Blind7 negative RSA trust | medium | Positive live probes and model hashes do not assert real missing/wrong/caller/domain refusals at the package boundary; add bounded denied probes. Patch under existing immutable-profile/qualification intent. |
| Blind8 native ACL drift | medium | Shared accesscontrol file adds stream-read permission for all profiles; keep permission local to the explicit published profile. Patch under existing immutable-profile/qualification intent. |
| Edge2 Kestrel limit | medium | Independent trace confirms Blind6 null lookup and default30MiB outcome. Patch under existing immutable-profile/qualification intent. |
| Gap1 restored closure negative test | medium | Reviewer mutation removed actual transitive version/type predicate while all4focusedtests still passed; add incompatible-version/source-project hook cases before runners. Preverified finding. Patch under existing immutable-profile/qualification intent. |

## Review repairs and scoped proof

All ten triaged rows above are preserved. Blind6 and Edge2 share one server fix;
the nine requested repairs are implemented without changing the 21 frozen vectors,
production catalog/readiness/authority validation or native/default/publish ACLs.

- Blind1 / Gap1: both domain hosts' actual `project.assets.json` closures must
  contain the required DomainService package and only EventStore 3.128.4 package
  libraries. Parameterized Tenants/Parties transitive-version and project-type
  mutations exercise both prepare and execute hooks and refuse before runners.
  A disposable predicate-removal control produces eight expected test failures,
  including project-type mutations that would otherwise reach runners.
- Blind2: each restored EventStore archive supplies its embedded nuspec identity,
  version and source commit. Extracted metadata/DLLs and deployed DLLs must match
  those same archive entries. The receipt also seals all three host output DLL/JSON
  files. Archive identity/source, extracted nuspec/DLL and deployed Gateway DLL
  mutations are rejected before runners, both before preparation and after it.
- Blind3: the receipt records the independently selected EventStore configuration
  source commit and hashes native/deployed gateway defaults, matching launch
  profiles, AppHost settings, sidecar files and both domain hosts' settings.
  Configuration drift is rejected even when source/deployed defaults still match.
- Blind4: immutable provenance is checked again immediately before independent
  smoke. A vector-time deployed DLL mutation prevents the smoke runner starting.
- Blind5: direct and recursively escaped JSON, XML values/settings/attributes and
  environment diagnostics redact PrivateKey as well as SigningKey. A fresh RSA
  key explicitly encoded as base64 PKCS#8 DER is absent from emitted diagnostics;
  meaningful nonsecret fields remain.
- Blind6 / Edge2: ConfigureKestrel sets the 1 MiB server default before Build.
  Real sockets accept exactly 1 MiB and return 413 for one extra byte. Removing
  the configuration in the disposable host makes that oversized-request case
  fail (actual 200); restoring it returns the two cases to passing.
- Blind7: real package HTTP requests with valid workload authentication reject
  absent/wrong RSA proofs, mismatched proof caller and a correctly signed domain
  outside the allowlist. A valid-proof control reaches the package controller's
  actual state-access error, demonstrating admission beyond authentication.
  The owned loopback infrastructure endpoint rejects every request; no successful
  metadata, index, actor state or authority response is fabricated. Native failure
  handling remains active, and no user's Dapr endpoint is contacted.
- Blind8: the original `accesscontrol.yaml` is byte-identical to HEAD. Only explicit
  published run mode selects `accesscontrol.published.yaml`, whose sole additional
  grant is Tenants POST stream-read. Both ACL variants and actual composition
  retain exact caller, path, verb and default-deny assertions.

Additional review scope is the new `PackageGatewayBoundaryTests.cs` and
`DaprComponents/accesscontrol.published.yaml`; the other repairs edit the existing
profile implementation, focused tests and its lane documentation. No release
inventory, package version, source bootstrap or production dependency is changed.

Scoped verification (no complete live lane repeated during these review repairs):

- `python3 -m unittest discover -s tools/live-topology -p test_ci.py -v`:
  70/70 passed before the final expanded archive controls; the three archive tests
  subsequently pass with the new embedded identity/source and prepare/run cases.
- `python3 -m unittest discover -s tools/live-topology -p test_ci.py -k pkcs8 -v`:
  passes using explicit fresh PKCS#8 DER after its final fixture refinement.
- Real archive/config provenance also succeeds against the disposable restored
  artifacts: exact 3.128.4/source717, seven archives and 17 configuration files.
- Disposable Release host/test builds pass with zero warnings/errors.
- `dotnet ...Manifest.Tests.dll -class '*PackageGatewayBoundaryTests'`:
  7/7 passed, no skips, 8.004 seconds. Receipt log:
  `/tmp/mcpcli-review-boundary-tests4.log`.
- `dotnet ...Manifest.Tests.dll -class '*TopologyAccessControlTests' -class
  '*TopologyLaunchTests' -class '*TopologyConfigurationTests'`:
  82/82 passed, no skips, 27.071 seconds. Receipt log:
  `/tmp/mcpcli-review-topology-scoped.log`.
- Kestrel mutation refusal and restored 2/2 proof are retained in
  `/tmp/mcpcli-review-kestrel-mutant-tests.log` and
  `/tmp/mcpcli-review-kestrel-restored-tests.log`; restored-cohort predicate
  mutation proof is `/tmp/mcpcli-review-cohort-predicate-mutant.log`.
- `git diff --check` passes. Temporary package processes are stopped. No commit or
  push was performed by the implementing agent. The parent retains full validation
  and all-21-vector acceptance responsibility.

## Builds-only conformance amendment

The exact a3989b4 hosted enrolled-module job 124498335404 fails with MSB3030:
the package TestHost tries to copy EventStore appsettings while this lightweight
job intentionally initializes only Builds. The completed job log is retained at
`/tmp/mcpcli-a398-conformance-completed.log` (lines 176 and 203). The parent
explicitly directs keeping this lightweight boundary and owning a reviewed,
nonsecret source-bound package configuration snapshot. This remains within the
existing package profile and immutable configuration qualification scope.

- The owned required `Configuration/appsettings.gateway.json` is byte-identical
  to EventStore commit `ab39879c06eea69668916941ce46a2b6d7e8efd9`, the owner's
  selected configuration source. `Configuration/provenance.json` records the
  exact 3.128.4 profile, source repository, commit, original paths and SHA-256 for
  defaults and matching launch profiles. Git attributes preserve those bytes.
- The project copies this required file to the same runtime filename and retains
  the existing lowest configuration priority. Native/default/publish project
  selection and ACLs, actual RSA proof validation, archive/runtime cohort checks
  and all 21 semantic vectors remain unchanged.
- Live qualification validates the manifest, hashes and deployed defaults, then
  compares owned snapshots to the exact recorded Git blobs. The immutable receipt
  includes the manifest and used configuration hashes, rechecked before vectors
  and independent smoke. Compilation and socket tests need only the Builds catalog.
- A fresh standalone a398 clone at
  `/tmp/mcpcli-minimal-conformance-w67ujmoz/McpCli` with only ordinary copies of
  the exact owner-selected Builds4d93 catalog reproduces the original missing
  source-file error, then builds the full solution Release with zero warnings or
  errors after the fix. EventStore/Tenants/Parties source directories are absent;
  no nested initialization/update or original producer mutation was performed.
- Removing the required owned snapshot fails compilation with MSB3030, then a
  restored full solution build passes. The eight real socket/config cases pass
  with no skips in 7.956 seconds. The enrolled catalog coverage subset passes 5/5.
  Logs are `/tmp/mcpcli-minimal-required-snapshot.log`,
  `/tmp/mcpcli-minimal-after-build-final.log`,
  `/tmp/mcpcli-minimal-socket-tests-final.log` and
  `/tmp/mcpcli-minimal-conformance-tests.log`.
- Real restored package provenance also passes against the independent complete
  qualification workspace: exact Gateway 3.128.4/source 717, configuration source
  ab398, seven archives and 17 used configuration files. Retained summary:
  `/tmp/mcpcli-snapshot-real-provenance.log`.
- New manifest cohort/source/path/hash and exact source-blob controls reject drift
  before runners; prior deployed-binary, both-domain restored graph, long-lane
  smoke recheck and fresh PKCS#8 redaction controls remain active. The full focused
  CI-hook test-file result is recorded below when complete.

- Final focused hook suite: `python3 -m unittest discover -s tools/live-topology
  -p test_ci.py -v` passes 72/72 in 189.191 seconds, including the new manifest
  controls and all prior archive/domain/private-key/smoke drift cases. Log:
  `/tmp/mcpcli-snapshot-ci-tests.log`.
- Final amendment scope is nine files: Git attributes; this spec; package host
  project; the two owned Configuration JSON files; existing package boundary
  tests; lane README; CI provenance implementation; and its focused test file.
  `git diff --check` passes and all ten original review triage rows remain.
  No workflow initialization was expanded, and no commit or push was performed.

# Story 4.9 verification

The implementation and technical review are complete. Final Release verification
passes: **2004 Parties tests, 315 Server tests and 201 Contracts tests**, zero
failures/skips; full solution restore/build succeeds with zero warnings/errors.
`accepted-checks.json` records the exact final commands, durations and logs.
`matrix-test-audit.md` maps every approved matrix row to passing execution.
The requesting maintainer explicitly approved the final vector/artifact record
on 2026-10-20 (“I approve”). `maintainer-vector-approval.json` records approval
against the unchanged package/vector hashes and validator revision. Approval-time
manifest and vector rechecks pass. All Story 4.9 acceptance items are complete.

## Implementation and identity

Implementation belongs to `/home/administrator/projects/hexalith/parties`.
McpCli changes are the spec, sprint tracking and this evidence; no McpCli runtime
or production module enrollment changed.

- Approved McpCli/validator revision: `b616db3092a9b1c5af196538a3de37a5c7f2d7ca`.
- Approved Parties baseline: `4d4be476687cff4210774ec62558131ff8659558`.
- Clean implementation start: `836b2ba4aa41cdf8a7812b97a5da7c08896c0c7c`.
  The intervening commit was CI-only; the approved baseline was preserved.
- Parties HEAD at final verification: `14ad39f85eae152c7a7e22ff261cc534ff5dab1e`.
  Other work independently committed some story files and advanced dependencies
  during this session. Its AppHost, publish, CI and dependency changes were
  preserved. Local completion commits are recorded after approval; no push was
  performed.
- `source-files.sha256.json` and `vector-files.sha256.json` bind final file bytes,
  including outstanding working-tree edits; HEAD alone is not their identity.

The assembly declares module `parties`, String identifiers, full CLR wire names,
domain `party` and root `PartyId` routing. Exactly four Commands are exposed:
`create-party`, `update-party`, `reactivate-party`, `deactivate-party`.
Abstractions 1.0.0 uses the existing package/source reference pattern. No excluded
operation or Query was exposed.

Both composite validators share the approved raw UTF-16 limits: 512 per string,
4096 total, counting whitespace and every repeated root/child/removal string.
They preserve supplied values, tighter 128-character IDs and the configured
operation cap. Null lists/items and unsupported empty updates reject before
protected state access. Regression checks also pin partial contact semantics,
numeric enum refusal, organization-only replacement and safe repeated soft
deactivation. README/API docs describe explicit typed payloads and the limits.

## Final executed verification

In Parties:

```sh
dotnet restore Hexalith.Parties.slnx
dotnet build Hexalith.Parties.slnx --no-restore --configuration Release -warnaserror -m:1
dotnet test tests/Hexalith.Parties.Tests --no-build --configuration Release
dotnet test tests/Hexalith.Parties.Server.Tests --no-build --configuration Release
dotnet test tests/Hexalith.Parties.Contracts.Tests --no-build --configuration Release
```

All pass (`accepted-*.txt`). Focused domain validation passes 119/119; declaration
checks pass 2/2. The verifier's seven unit checks pass and protect input/code
identity, environment isolation and publication only after all checks succeed.
`final-checks.json` retains the preceding complete run, package and scratch
receipts, including its two resolved current-selection failures.

Those two failures followed an independently committed Builds advance. Factual
current-selection records were stale. `selection-reconciliation.json` records
the exact Git identities and MSBuild evaluation. Only present-tense documentation,
fitness literals and a new dated matrix section were reconciled. The former
2026-10-18 section and all older receipts remain historical; exact identity and
clean-checkout assertions and approval/parity/runtime/custody gates are intact.
No references or dependencies were changed by this reconciliation. Both focused
checks and the subsequent complete project suite pass.

## Local artifact and generic host

Package: `Hexalith.Parties.Contracts` version `0.0.0-story49`.

`sha512-uymAVLI8EOJuTGHmBim7wcfasYTIyaz3WyAW6lXSxhHYLE4sp51VWtEzimZpM8/UOeIZoKeuH4PIxqH+np0PRA==`

The artifact is retained locally as
`artifacts/Hexalith.Parties.Contracts.0.0.0-story49.nupkg` (repository package
ignore rules apply). It was not published. To produce the local candidate after
restoring/building the owning Contracts project:

```sh
dotnet pack src/Hexalith.Parties.Contracts/Hexalith.Parties.Contracts.csproj \
  --no-build --no-restore --configuration Release \
  -p:PackageVersion=0.0.0-story49 -p:MinVerVersionOverride=0.0.0-story49 \
  --output /home/administrator/projects/hexalith/mcpcli/_bmad-output/implementation-artifacts/evidence/story-4-9/artifacts
```

That command produces a new candidate; it does not promise byte-identical
rebuilds. Approval is for the retained hash. Its selected dependencies include
EventStore.Contracts 3.126.0 and Commons.UniqueIds 2.30.3. The isolated scratch
host uses those versions only in temporary builds, avoiding downgrades against
McpCli's development graph.

From McpCli, reproduce the checks with:

```sh
python3 _bmad-output/implementation-artifacts/evidence/story-4-9/verify-scratch.py
```

`final-scratch.txt` records success against the final artifact: one module, four
Commands, zero Catalog diagnostics, valid examples, strict discovery and lint,
empty diagnostic stderr, matching restored package SHA-512, four-vector format,
identity and command coverage. Both CLI and MCP match complete Gateway requests,
tenant and wire types, with validation/Gateway error parity. Temporary smoke
copies omit only unavailable Query postconditions; original vectors are intact.
`production-assets-before.sha256` equals `production-assets-after.sha256`.
Final manifest preflight also passes after selection-record housekeeping.

The verifier checks source/vector/verifier SHA-256 manifests and the exact
validator revision/hash before execution. Each subprocess has a fresh isolated
profile and sanitized EVENTSTORE_/MCPCLI_ settings. It publishes Catalog/check
outputs only after every gate succeeds. Seven unit tests protect these controls.

## Review result

Three independent final reviewers completed blind, edge and verification-gap
reviews. Every finding is triaged in the spec. Seven patch groups were resolved:
verification isolation; input/validator identity; publication ordering; create
child assertions; ID syntax guidance; review metadata; and organization-only
positive regression coverage. There are no unresolved findings or new deferrals.

Fresh-context description review initially failed, then returned **PASS WITH
NOTES** from `story49_description_review_final` for the round-2 artifact.
`description-review-round-1.md` and `description-review-round-2.md` retain both
reports. Direct follow-ups corrected every note without domain changes.
`description-delta-round-2.json` and
`description-delta-scalar-id-guidance.json` bind subsequent wording to the final
Catalog; non-description Catalog content is identical in those comparisons.
`description-review.json` identifies the reviewer, reviewed artifact, final
artifact and exact deltas. Prior artifacts remain under `artifacts/round-1/`,
`round-2/` and `round-3/`. This technical review does not approve the vectors.

## Remaining acceptance and downstream work

- **Maintainer vector approval:** recorded from the requesting maintainer's
  explicit conversation approval on 2026-10-20. The receipt binds the final
  package hash, validator revision/hash, successful validation command and
  vector SHA-256 manifest. Release package/version binding remains Story 4.10
  work.
- **Queries and effects:** `parties.get-party` is not in this four-command
  Catalog. The original vectors include the approved PartyDetail/party-detail/
  PartyDetailProjectionQueryActor postconditions, including created children
  and repeat deactivation. Their execution awaits 4.10; 4.11/4.13 prove parity
  and persistent effects. Offline format validation and routing smoke are not
  live semantic proof.
- **C06:** public-error privacy and shared-result migration remain replacement/
  retirement gates.
- **C07:** Parties still accepts legacy braced/parenthesized/X-format IDs; their
  generic-head/Gateway reachability is unproven. No conversion was introduced.
- **C08:** credential refusal, authorization and cross-tenant evidence remain
  downstream replacement/retirement gates.

No publication, push, legacy-host retirement, ID conversion or authorization
change was performed.

## Local completion commits

The owning Parties completion commit is `e1db1b61de4d47336e474d41eed18b68d43d7377`; all committed vector
blobs match the maintainer-approved hashes. The McpCli completion commit records
this evidence and the done spec. Both exact messages passed the owning pinned
commitlint CLI (`commitlint-validation.json`). Neither repository was pushed.

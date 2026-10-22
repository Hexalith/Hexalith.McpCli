# Story 4.11: pending Tenants candidate and prerequisite plan

**Status: pending owner review; publication and production acceptance are false.**
The exact current Tenants source fails its normal Release package build: `NativeSourceProof`
is missing from the pinned `Hexalith.EventStore.Contracts` 3.126.0. The retained
[failed pack](pack.stdout.txt) and [published API inspection](published-api.stderr.txt)
prove this prerequisite. The staged candidate succeeds only with an isolated
EventStore 3.126.1 package override. No source, Builds pin, gitlink or production
enrollment was changed.

The authoritative [pending packet](pending-approval.json) binds the source,
artifacts, vectors, inventory, proposal and verification hashes. It records no
approval. The proposed versions come from each repository's installed
semantic-release commit analyzer using local release tags and committed history;
remote source/tag/registry/CI preflight must revalidate them.

| Local candidate | Exact source commit | Package SHA-512 |
| --- | --- | --- |
| Tenants.Contracts 5.10.0 | `2cd3cc270e88d3cdbb47a1a938fd6a0951b6f0d4` | `sha512-OWY5HUWkLNlna5Nxgd2ZafCkbHKEHYOjkQ+sXxUGnFRvRbhI3jVebPfEoG3iA2i4L+grlSFycAr8pBuhuMODcQ==` |
| EventStore.Contracts 3.126.1 | `b6d1807035fba2e485c8587ac3581d669d1036e5` | `sha512-+FD1yOdOtzkFSeelhNEo6znaiHcyFC4i0ryNwr5xeYpIcg/vulrPYb0sgLDO+bWx7wzsfUK+UCt/dtS/pxWjPw==` |
| EventStore.Client 3.126.1 | same EventStore commit | `sha512-yjXQNOkqI1yFH7/17tXFwLK8xhgKeF+P6NMOrOPFc6glImKZQKSl1MWz8rsLUwONsS+1BGAUl6l9MFdr2T+Dxg==` |

The archives are retained locally in `candidate-packages/` and are ignored by
Git. [Package metadata and file hashes](package-candidates.json) preserve their
exact identities, repository commits, dependencies and payloads. EventStore's
`NativeSourceProof` first landed in `a07265f00994a3ad093184cec0f329d11184c3e9`;
the latest version in the captured NuGet index is 3.126.0, whose compiled API lacks it.
EventStore's owning checkout has unrelated uncommitted work; the proof packages
use committed source only and preserve all original trees.

## Verified candidate scope

- [Independent artifact verification](artifact-verification/verification.json)
  passes all 14 Tenants operations: strict discovery, all-step Core compatibility,
  complete request documents, success/error results and reset CLI/MCP replay.
  All eight historical paging-member lint exceptions match exactly.
- [Combined candidate replay](candidate-replay.json) passes all 21 operations
  in the complete Parties/Tenants manifest, with retained request/result observations
  under `combined-observations/`. It explicitly withholds production/full-v1 acceptance.
- [Vector rebinding](vector-rebinding.json) changes only `package.version` from
  `0.0.0-story48` to `5.10.0`, retaining every other source byte.
- [Candidate dependency delta](dependency-delta.json) contains only
  EventStore.Client/Contracts 3.126.0 → 3.126.1 and the addition of
  Tenants.Contracts 5.10.0. The proposed dependency-policy lane passes 98 tests;
  the isolated String-kind test passes.
- [Fresh-process benchmark](candidate-benchmark.json) measures 148.0593 ms for
  Parties (7 operations), Tenants (14) and exactly one Ulid sample (3), with no
  diagnostics. It explicitly records `local-only` and `fullV1Accepted: false`.
- [Pending inventory](inventory-candidate.json) proposes 14 included operations
  and six excluded internal/admin contracts. Every row remains `pending`, and
  the actual inventory checker rejects all 20 rows. The additional undecorated
  `ResolveTenantReadAuthority` exclusion needs a new owner decision. This is
  proposed gateway scope, not an independently approved legacy-retirement inventory.

The first dependency-test attempt lacked the isolated snapshot's solution marker;
its failure is retained. Copying the unchanged tracked `.slnx` marker enabled the
passing 98-test rerun. [Checks](checks.json), [combined build checks](combined-checks.json)
and [additional checks](additional-checks.json) retain exact commands and outcomes.
The public [description-review input](description-review-input.json) is extracted
from this exact artifact. The independent [fresh-context NFR-8 check](description-review.md)
passes with one low-severity wording advisory and no blocking finding. Linking
that review from the owning release/change record is still required.

## Exact publication scope and continuation

1. Review and finalize the EventStore prerequisite source independently. Its
   normal Release workflow publishes **all 14 packages** in its release manifest
   plus `src/Hexalith.EventStore/Hexalith.EventStore.csproj` as `eventstore`.
   The local Contracts/Client packs certify neither those other packages nor
   container readiness. Publication requires the exact live `main` source to have
   successful push `ci.yml`, `p1r-qualification.yml` and `commitlint.yml` runs,
   then the protected `production` job, pinned Builds publisher, collision/source
   checks and normal package/OCI validation. No prerequisite publication is approved.
2. After an approved EventStore release exists, change its pin in the **owning
   Builds repository**, then update Tenants/McpCli root Builds gitlinks to the
   resulting reviewed commit. The [proposed patch](proposed-prerequisites-and-enrollment.patch)
   demonstrates the version changes only in an isolated copy. It is not a
   committed upstream repair; future gitlink identities cannot be invented.
3. Refresh the exact Tenants candidate from that dependency/source state. Its
   normal workflow publishes **Contracts, Client, Server, Testing and Aspire**
   together, plus `src/Hexalith.Tenants/Hexalith.Tenants.csproj` as `tenants`.
   It requires current `main`, successful exact-source push CI, tag/registry
   preflight, protected `production` approval, declared five-package inventory,
   pinned Builds execution, Trusted Publishing and container checks. The current
   unmodified source cannot satisfy this release build. No Contracts-only
   publisher, CI bypass or full-release readiness claim is proposed here.
4. Obtain fresh owner approval of the exact candidate, 14 vectors and 20 inventory
   decisions, record the description review in the owner change record, and obtain
   the full stated publication-scope approval before the irreversible workflows.
   Existing Story 4.8 scratch approval does not approve these release bytes.
5. If CI repacks, download the immutable final published Contracts archive and
   bind its ID/version, repository source, raw SHA-512, restore content hash and
   payload hashes. Rebind only the vector version if required; rerun
   `verify_artifact.py` with exact lint/inventory decisions and final bytes.
   Compare with the reviewed candidate and obtain the required release-bound
   owner receipt. A new version/source/hash is not silently approved by this
   pending packet, and a scratch artifact hash must never be copied to the
   published-artifact receipt.
6. Only then add the authentic release approval/receipt and approved inventory,
   flagged versionless Tenants reference, exact module pin and changed policy
   versions; restore and run the required McpCli build/test/sample gates.
7. Run the unchanged strict `check_enrolled.py` and
   `MCPCLI_BENCHMARK_REQUIRE_V1=true` against **actually published and enrolled**
   Parties and Tenants on ubuntu-latest. Keep Story 4.11 and sprint tracking
   `in-progress` until both pass.

Loopback evidence proves transport parity. Live authorization, privacy
sanitization, persisted effects and retirement remain separate gates.

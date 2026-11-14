---
title: 'Repair current McpCli published-cohort CI'
type: 'bugfix'
created: '2026-11-14'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '401d926eb7d51bdf332696ed3f0fe39a812b3501'
owning_repository_baseline_commit: '42d3c2fd48405e0f2c27f9b61f6d7025e4246934'
investigated_remote_head: '7fa3df6a6b827f85fba6e12ec22c5efa08034ac8'
context:
  - '/home/administrator/projects/hexalith/tenants/references/Hexalith.McpCli/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Restore current McpCli CI using its published EventStore 4.2.0, Tenants 7.0.7 and Parties 3.1.1 cohort. Preserve product .NET 10 support by overriding incompatible central package selections. Resolve two census rejections through specifically authorized classifications and the immutable approval chain.

## Boundaries & Constraints

Preserve analyzer netstandard2.0, current/historical vectors, source identities, native authorization, artifact integrity and every gate. No broad exclusions, fabricated approval, scanner weakening, business behavior changes, operator credentials or nested initialization. Preserve concurrent work and dependency checkouts. Staging, commits, pushes and publication require a later concrete publication decision; local evidence grants no hosted acceptance.

## Approved Decisions

On 2026-11-14 the requesting user answered “apply” and “approve” to the exact two census classifications and repair spec. This specifically authorizes PE06 external-developer-tool classification of Microsoft.DotNet.ApiCompat.Tool installation and PE09 qualification-evidence-tooling classification of Hexalith.EventStore.RuntimeIdentityProbe at EventStore d457ecd51a17b8ecc0c678b02d19d7ee92c13141, with the exact source bindings in evidence/mcpcli-current-ci-2026-11-14/investigation.json, including all eight probe compilation sources. No broader source, future surface or publication authorization is inferred.

</frozen-after-approval>

## Code Map

Implementation paths are relative to `references/Hexalith.McpCli`.

- `Directory.Build.props`: net10 product target; add PackageVersion overrides after the central import. Current catalog introduces three net11-only dependencies. Published module nuspecs permit compatible net10 versions.
- `tools/dependency-policy.json`: exact production/helper closure, verified by Manifest.Tests against fresh assets. Existing approved UniqueIds version is 2.30.10.
- `tools/proprietary-surfaces/v1/README.md`, `amendments.json`, `amendments/1.0.7.json`: mandatory specific owner authority, full source hashes and append-only lineage. Preserve all prior receipts.
- `.github/workflows/ci.yml`, current vector/plan/runtime selections and Manifest.Tests: authoritative qualification sequence. Existing net10 executable paths and current enrollment stay intact.

## Tasks & Acceptance

**Execution:**

- [ ] `Directory.Build.props` — override UniqueIds to 2.30.10, JwtBearer and SignalR.StackExchangeRedis to 10.0.15. These public packages satisfy the selected module floors without changing runtime support.
- [ ] `tools/dependency-policy.json` — fresh package-mode restore into a task-owned cache; reconcile only actual changed selections and run existing dependency/helper-boundary controls.
- [ ] `tools/proprietary-surfaces/v1/amendments/` and `amendments.json` — after specific approval, append the next amendment and v2 receipt binding the packet's exact identities/sources; reject source drift and preserve prior lineage.
- [ ] Owning evidence directory and this spec — retain verification, independent review and source hashes. Complete hosted qualification only after reviewed publication is separately authorized.

**Acceptance Criteria:**

- Given current published modules, when fresh restore and Release warnings-as-errors build run, then NU1202 is absent, net10 support remains and dependency policy matches assets.
- Given specifically approved additions, when census fixtures and committed-tree scan run, then only those additions pass; incomplete approvals, source drift and unknown identities remain rejected.
- Given the fresh build, when ordinary tests, enrollment replay, strict benchmark, sample conformance and topology discovery run, then every required case remains enabled and passes.
- Given reviewed published source, when complete hosted CI runs, then every blocking job including native acceptance passes; otherwise completion remains pending.
- Given entry work, when changes are compared, then unrelated files, withdrawn historical drafts and all five completed dispositions remain preserved.

## Implementation Notes

Approved for local implementation on 2026-11-14. Footprint: two configuration files, amendment index, new amendment/receipt and bounded evidence. No runtime/data side effects during preparation.

## Verification

From the owning repository, use fresh restore and Release build with `-warnaserror`; run the six ordinary projects individually. Follow owning guidance for enrollment coverage, strict benchmark, `check_enrolled.py`, sample validation/loopback and subsequent fresh restore. Run topology fixtures/preflight and exact built-test discovery; census fixtures/committed scan; evidence secret scanning; whitespace checks; independent review; eventual exact-source hosted CI.

## Investigation Evidence

[Packet](investigation.json) records public package hashes, source closure and [failed current CI](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/43536045450): six restore/conformance/discovery failures plus census, with native/performance skipped.

Original 7.0.0 enrollment work was superseded and delivered. DW-117/118/133/365/367 are done and archived, with zero open maintenance rows. Their withdrawn draft and successor evidence remain unchanged. The full probe closure was successfully computed using permitted top-level object stores; no nested checkout or fetch was needed.

## Spec Change Log

## Review Triage Log

- Implementation starts from the clean owning checkout at the recorded local baseline. The investigated later remote revision remains context; no fetch, branch movement, stage, commit, push or remote workflow operation is authorized in this implementation phase. Existing root and other-submodule changes are preserved.

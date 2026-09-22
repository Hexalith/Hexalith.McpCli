# Final architecture gate: adversarial and rubric review

**Verdict:** No critical or high findings. The approved FR-20/SM-4 and `unknown_module` decisions now align across the spine, PRD, and addendum. One medium test-gate gap remains.

Target: `../ARCHITECTURE-SPINE.md` and its current PRD/addendum. Mechanical gate: `uv run .agents/skills/bmad-architecture/scripts/lint_spine.py --workspace _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22` returned `ok: true`, zero findings. No source file was edited by this review.

## Critical and high findings

None.

## Medium finding

### M1. Loopback parity compares documents but does not require equal Gateway requests

**Evidence.** AD-16 requires the two out-of-process Heads to receive reset scripted Gateway responses and asserts equality of their canonical result and error documents after masking generated IDs (`ARCHITECTURE-SPINE.md:146-150`). FR-20 and SM-4 now match that requirement (`prd.md:396-404`, `:509`). AD-1 leaves each Head responsible for binding its protocol inputs into Core arguments (`ARCHITECTURE-SPINE.md:42-46`); AD-5 calls for a surface-map test but does not state that the loopback test compares the Gateway requests (`:80-84`).

**Compliant-but-incompatible construction.** The MCP Head binds `aggregateId` or `pageSize` correctly while the CLI Head drops its corresponding flag. A scripted loopback Gateway returns the same canned Query document regardless of the two request bodies. The result documents match and the live lane exercises only one Head per vector, so the release gate can pass although CLI and MCP submit different routing or paging values. The shared executor does not prevent an adapter from passing different Core argument records.

**Disposition: autofix at the AD-16 test contract.** Require the loopback to capture both requests and compare normalized method, path, routing, Envelope, Payload, and paging after masking only generated message/correlation identifiers. Assert each request also matches its vector's expected inputs. This keeps the approved one-live-submission decision intact.

## Targeted source-alignment checks

| Contract | Result |
| --- | --- |
| FR-20 and SM-4 | Aligned. Both sources require one maintainer-approved vector per listed Operation, reset loopback parity through both Heads, and one separate live execution with semantic checks. AD-16 states the same split and does not silently weaken the live gate (`prd.md:398`, `:509`; `ARCHITECTURE-SPINE.md:146-150`). |
| `unknown_module` | Aligned. A missing or empty `module` fails input binding; a non-empty Catalog miss returns a distinct error with the exact requested name and up to three declared canonical suggestions, ordered by case-insensitive edit distance and ordinal tie-break. The spine's AD-3/AD-5 and error-code convention match addendum §E/§G (`addendum.md:201-203`, `:380-392`; `ARCHITECTURE-SPINE.md:72`, `:84`, `:192`). |
| Synthetic sample and manifest | Aligned. The out-of-process tool uses only flagged production Contracts; the sample participates in a separate in-process Catalog benchmark (`ARCHITECTURE-SPINE.md:78`, `:144`, `:150`). |
| Legacy coverage | Aligned. AD-21 independently gates the approved inventory against canonical names and internal contract types; vectors alone cannot declare a Module complete (`ARCHITECTURE-SPINE.md:176-180`; `prd.md:405`, `:411-413`). |

## Rubric walk

| Check | Assessment |
| --- | --- |
| Invariants at feature altitude | Paradigm, package direction, Catalog, schema, Envelope, identity, settings, output contract, test gates, release, and migration inventory are fixed at useful boundaries. M1 is the remaining parity assertion seam. |
| Enforceable rules | AD rules mostly state concrete inputs, outputs, failure behavior, or tests. M1 identifies a case where the asserted output equality does not establish the stated cross-head execution equality. |
| Deferred items | HTTP auth, later tool/CLI surfaces, query extras, and trimming have defined seams or revisit conditions; none silently changes v1 implementation choices. |
| Brownfield and source fit | The spine ratifies the existing EventStore gateway, sibling CLI/MCP shapes, Builds imports, and Aspire helpers. The previously open PRD live-test conflict is settled in the normative source. |
| Technology currency | Stack versions are pinned and the architecture memlog records technology/API verification; this lens did not redo the separate technology review. |
| Structural dimensions | Deployment and environments, infrastructure ownership, operations/channels, persistence, CI, release, and upstream prerequisites are decided or explicitly open. No wholly silent dimension found. |

**Gate recommendation:** Apply M1 as a narrow AD-16 test assertion, then finalize; it requires no new product decision.

## Closure after source and spine update

**M1 closed.** The PRD now requires equal captured Gateway requests from both Heads and a match to each vector's expected inputs (FR-20 at `prd.md:398`; SM-4 at `:509`). AD-16 requires the loopback lane to compare method, path, routing, Envelope, Payload, and paging between Heads and against the vector, masking only generated message/correlation identifiers (`ARCHITECTURE-SPINE.md:150`). Caller-supplied idempotency keys remain unmasked. This defeats the constructed case where one Head drops an `aggregateId` or paging flag while the scripted Gateway returns identical documents.

**Final verdict:** No remaining critical, high, or medium finding from this review. The earlier M1 section remains above as review history; this closure supersedes its gate recommendation. No new source/spine incompatibility was found in the targeted edits.

# McpCli PRD quality review

Full working-tree PRD and addendum, 20 November 2026, based on McpCli `6993abfe`.

## Overall verdict

The product scope and enrollment evidence support sprint planning. The main cross-module journey uses a Parties write whose eligibility for public agents remains disputed. Release operators and implementers also need several corrections before they can use these documents as their sole acceptance reference.

## Decision-readiness — adequate

Stories 5.15 and 5.21 identify the owners and evidence needed to decide final-archive qualification and Projects paging. One historical release condition has a recorded verdict that §7 omits.

- **Medium — Release status omits closure of the Epic 3 schema item.** Section 7 says the publication hold “also requires resolution of the Epic 3 output-contract item”. The sprint tracker marks that exact item `done` and the retrospective records the two-protocol evidence. A release operator could reopen completed work. State both the historical condition and its recorded satisfaction, then point to the outstanding exact-candidate CI and archive checks. Evidence appears in `prd.md:475`, `_bmad-output/implementation-artifacts/sprint-status.yaml:230` and `_bmad-output/implementation-artifacts/epic-3-retro-2026-10-16.md:137`.

## Substance over theater — strong

FR-18 makes a failed profile replacement observable through the preserved bytes, active profile and permissions. FR-20 specifies the expected records, ordering, second page and denial result for native Projects qualification. These requirements give the responsible team concrete evidence to collect.

## Strategic coherence — adequate

The shared Catalog, five generic tools and fixed Gateway boundary support the cross-module task in SM-2. The named success journey conflicts with the adopted decision for one of its two operations.

- **High — UJ-1 presents a disputed public-agent write as a success case.** Nadia’s agent calls `parties.create-party` and receives a successful result in UJ-1. This is T04, classified under K12 in AD-23. The same decision records that T04 is already enrolled, names the owners and requires reconciliation before claiming the public exposure is compliant. FR-21 acknowledges a conflict but omits the affected names. A team could run UJ-1 and mistakenly use that success as authorization evidence. Identify T04 at the journey, retain the owner decision, and demonstrate SM-2 with operations cleared for the intended surface. Evidence appears in `prd.md:56`, `prd.md:447` and `_bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md:178` through the decision at line 204.

## Done-ness clarity — adequate

FR-20 and SM-4 distinguish deterministic loopback parity from live semantic checks. Two public-interface requirements still leave competing interpretations for an acceptance test.

- **Medium — Missing status on a malformed success acknowledgment has no specified representation.** Under Story 5.17, FR-17 and addendum §G preserve the actual HTTP status “when exposed”. The exhaustive `gateway_error` schema always requires an integer status. Core receives a successful `SubmitCommandResponse` without an HTTP-status member. A test author has no defined expectation when Core detects the invalid identifier at that boundary. Specify how the genuine status reaches the error contract or obtain an explicit decision for the unavailable-status case. Keep the single-submission and submitted-correlation requirements. Evidence appears in `prd.md:395`, `addendum.md:433`, `addendum.md:466` and `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:254`.
- **Medium — FR-14 overstates its exit and output guarantees.** “Every CLI invocation” is limited to 0, 1 or 2, and the success rows specify stdout. With `--output`, a successful result goes to the file. An output failure after command submission can yield exit 2 even if the Gateway accepted the command. Forced termination can yield 130 or 143. Specify the ordinary exit table, selected success destination and interruption exceptions. Document the distinction between a preflight failure and an unknown outcome after submission so operators can decide whether a retry is safe. Evidence appears in `prd.md:338` through line 346, `README.md:600` through line 608 and `README.md:624`.

## Scope honesty — strong

Sections 0 and 8.1 distinguish the two required v1 modules from three enrolled packages and an unenrolled Folders module. The PRD identifies the November audit work as backlog. Projects paging and authorization evidence, CI recovery and legacy retirement are explicit delivery gates. Their open status is appropriate for this document.

## Downstream usability — thin

Stable identifiers and a central argument table make source extraction practical. Module authors and MCP callers still encounter gaps at two ordinary entry points.

- **Medium — The decoration table makes a valid computed query look invalid.** Section 5.1 requires `projectionType` whenever a Query has “no `IQueryContract`”. FR-20 recognizes a `none` projection selector. The Catalog accepts a computed Query with both selectors absent and rejects an actor selector without a resolved projection type. A module author following the table may invent a selector that changes routing. State the conditional requirement and include the selector-free case. Evidence appears in `prd.md:147`, `prd.md:430`, `README.md:573` and `tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs:154`.
- **Medium — The MCP execution table omits the wire type of its required payload.** Addendum §E says `payload` is “validated against the Schema”. The advertised MCP argument is a string containing serialized JSON. An agent that passes a JSON object matching the operation schema can fail protocol binding before Core validation. Specify the two layers and give one complete `run_query` call with a JSON-text payload. Evidence appears in `addendum.md:211`, `README.md:636` and `src/Hexalith.McpCli.Mcp/McpToolHandlers.cs:49` and line 62.
- **Low — Two JSON examples fail the required ULID constraint.** The command success and Gateway error examples in §G use `"01J9…"` in identifier fields. Both parse as JSON, but their outputs fail §G’s canonical uppercase ULID rule. Use complete synthetic ULIDs so the examples can serve as fixtures. Evidence appears in `addendum.md:374`, `addendum.md:430` and `addendum.md:514`.

## Shape fit — strong

A capability specification with a field-level addendum suits this internal tool. UJ-2 supplies the agent-discovery perspective, UJ-3 the module-author perspective, and the FRs cover shell and MCP behavior against one executor. Separate release and migration records keep mutable evidence traceable.

## Mechanical notes

All 22 FR identifiers occur once. The three journeys, eight NFRs, seven success measures and four counter-metrics have continuous numbering within their groups. The eight inline assumptions match the eight index entries. The review used the current documents, original product brief, decision log and cited repository evidence.

One high, five medium and one low finding. No critical findings.

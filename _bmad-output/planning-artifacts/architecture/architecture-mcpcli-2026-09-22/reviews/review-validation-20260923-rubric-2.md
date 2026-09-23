# Independent architecture rubric review — 2026-09-23

**Verdict:** Conditional. The spine fixes the principal cross-head, Catalog, Gateway, tenant, dependency, and release seams, and gives the local tool an operational envelope. One high-severity validation-order conflict can make documented Command inputs fail. Two medium-severity boundaries need explicit rules before independently written stories converge.

## Findings

### R1 — High — Raw Schema validation conflicts with Envelope filling

- **Location:** `ARCHITECTURE-SPINE.md` AD-7, line 97; AD-9, line 109. Source requirement: `prd.md` FR-16, lines 347–359.
- **Evidence:** AD-7 retains the serialized field Schema for the four Envelope-filled properties, marks them `readOnly`, and removes only their `required` entries. AD-9 then validates the *raw* Payload against that stored Schema before resolving or replacing those fields. Yet the same rule says a raw `null` at `idempotencyKeyProperty` is removed when no key was supplied, and any caller value at `correlationProperty` is overwritten. For a nonnullable string property, raw `null` fails its property Schema before removal; a caller correlation value with the wrong type or format fails before replacement. `readOnly` does not specify that these field constraints are skipped during validation. Thus one story can implement the stated raw validation and reject these inputs, while another implements the stated filling behavior and accepts them. The PRD repeats the order and the examples, so source alignment also needs attention.
- **Disposition:** **Discuss and update** AD-7/AD-9 and FR-16 together. Define the exact pre-fill validation input and which field errors it may report: for example, parse the raw object, perform explicit Tenant/Actor disagreement and idempotency-key checks, validate ordinary Payload members with Envelope-filled values temporarily excluded, then fill and validate the complete object against the stored Schema. Add the omitted-key/raw-null and overwritten-correlation cases to one shared fixture.

### R2 — Medium — `mcp` accepts output options without a defined effect

- **Location:** `ARCHITECTURE-SPINE.md` AD-13, line 133; AD-12, line 127; Channels convention, line 195. Source requirement: `prd.md` FR-13, line 305 and FR-10, lines 268–275; `addendum.md` §E, output source table, lines 224–240.
- **Evidence:** AD-13 says every verb, including `mcp`, accepts `--format` and `--output`. AD-12 and the channel convention require stdio JSON-RPC on stdout, with no ordinary document writer after serving begins. The spine does not say what `mcp --output file` or `mcp --format table` does. One adapter could redirect or format the protocol channel, another could silently ignore the options, and another could fail startup. Those choices differ at a protocol boundary.
- **Disposition:** **Update** AD-12/AD-13 and the PRD option table with one explicit `mcp` behavior for these accepted options, preserving stdout as JSON-RPC. Add a focused `mcp --output`/`--format table` startup fixture.

### R3 — Medium — The authoritative no-new-server rule is outside the release gate

- **Location:** `ARCHITECTURE-SPINE.md` capability map, line 303; AD-17, lines 153–157; Open Questions, lines 326–330. Source requirement: `prd.md` FR-22, lines 422–426 and §8.1 release checklist; `epics.md` Epic 4 release criteria, lines 1445–1455.
- **Evidence:** The map delegates FR-22 to the PRD, but AD-17's release preflight specifies a green source, version, and credentials without checking the instruction merge. The current root-declared `references/Hexalith.AI.Tools/hexalith-llm-instructions.md` lacks the no-new-per-module-server/CLI rule. The PRD says FR-22 closes only after that authoritative change is merged, not at pull-request time. The spine records upstream package and CI prerequisites as Open Questions but has no corresponding instruction prerequisite. Independently written release and instruction stories could therefore mark v1 ready differently.
- **Disposition:** **Update** the release invariant or Open Questions with the authoritative merge as an explicit v1 gate and a concrete verification target. Keep the actual instruction edit in its owning repository. An epic acceptance criterion alone does not bind the spine's release rule.

## Rubric coverage

| Check | Judgment |
| --- | --- |
| Real divergences at feature-to-epic altitude | Covered broadly by AD-1 through AD-21; R1–R3 are the remaining cross-story ambiguities found here. |
| Enforceable Rules and stated Prevents | Rules generally name executable checks. R1 is internally inconsistent; R2 lacks an option behavior; R3 lacks a release gate. |
| Deferred safety | HTTP identity, query extras, typed tools, trimming, and later Module composition have explicit revisit conditions or stable seams. No additional dangerous Deferred item found. |
| Current technology | Exact pins are listed. This review did not independently verify live package currency or SDK API fit; the separate technical reality lens should settle that question. |
| Brownfield ratification | This repository has no `src/` or `tests/` implementation yet. The spine uses existing sibling clients, Contracts, build catalog, and Admin CLI as seeds rather than claiming an existing McpCli implementation. |
| PRD capability coverage | FR-1 through FR-21 and NFR-1 through NFR-8 have mapped owners or rules. FR-22 is mapped but its completion gate is missing from AD-17 (R3). |
| Inherited parent spine | None identified for this feature spine. |
| Owned dimensions | Dependency direction, state ownership, data and serialization, security context, protocol heads, deployment environments, CI, packaging, and operations are decided or listed as open/deferred. No whole operational dimension is silent. |

Review was read-only for the spine and its source documents. No source code or tests exist locally to validate implementation behavior.

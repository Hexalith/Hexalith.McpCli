---
title: "Reconciliation: Brief vs PRD/Addendum — Hexalith.McpCli"
status: draft
created: 2026-09-21
---

# Reconciliation: brief-mcpcli-2026-09-21 → prd-mcpcli-2026-09-21

Source input: `_bmad-output/planning-artifacts/briefs/brief-mcpcli-2026-09-21/brief.md`
Checked against: `prd.md` and `addendum.md` in this folder.

## Coverage table

| Input item (brief) | Where in PRD/addendum | Status |
|---|---|---|
| Goal: human does any operation in Hexalith through an LLM agent | PRD §1 Vision, opening sentence | Captured |
| Replaces six handwritten per-module MCP servers with one generic server + one CLI, driven by one catalog | PRD §1 | Captured |
| CQRS framing: every action a Command, every read a Query, all through one EventStore Gateway | PRD §1 | Captured |
| Module declares an operation once in Contracts library with a small attribute the MCP module provides | PRD §1, FR-1 | Captured |
| Server discovers declarations, describes to agent, validates payload, submits via Gateway client | PRD §1, FR-15–FR-17 | Captured |
| Depends on nothing else in Hexalith, knows nothing about module internals | PRD §6 Dependency policy, §8 Non-Goals | Captured |
| v1 covers Tenants, Parties, Projects, Folders | PRD §9.1, FR-20 | Captured |
| Six existing servers are end-of-life, deleted as generic one covers them | PRD §4.8, FR-21, Addendum §D | Captured (deletion is per-module/gradual, consistent with brief's "as the generic one covers them") |
| Problem: inconsistent transport/naming/description/auth per server; agent gains nothing moving between modules | PRD §1 (near-verbatim restatement) | Captured |
| Problem: "every divergence is a place for the model to guess wrong"; per-module tuning of prompts/tool selection/error handling | Not restated | Missing (minor — background framing, not a requirement) |
| Problem: descriptions live in XML doc comments, invisible at runtime, each server hand-redescribes and drifts | Not restated anywhere; FR-4 NOTE only states current zero-`[Description]` fact, not the causal XML-doc-comment argument | Missing |
| "This is an anticipatory build. There is no triggering incident." + bet that Agents/ChatBot/Conversations will need cross-module action and six dialects won't survive it | Not restated; PRD §2.1 lists Agents/ChatBot/Conversations as users but drops the "anticipatory, no incident" framing | Missing |
| "Maintenance of six servers and friction for the next module author... follow from the same root cause and disappear with it" | Not restated | Missing (minor) |
| Solution: attribute package — two attributes, description + read/write + optional example | PRD FR-1 | Captured |
| Solution: routing from contract interfaces, attribute fallback | PRD FR-2 | Captured |
| Solution: attribute package has no dependencies, stays that way | PRD FR-1 consequence, Glossary "Decoration Package" | Captured |
| Solution: catalog built at startup, knows every module/operation/schema/read-write | PRD FR-5 | Captured |
| Solution: same catalog drives both heads | PRD Glossary "Catalog", §4 intro | Captured |
| Solution: MCP server with five generic tools | PRD FR-9 | Captured |
| Solution: CLI with matching verbs, **plus a `serve` verb that starts the MCP server** | PRD FR-12, Glossary — verb is named **`mcp`**, not `serve` | Contradicted (see Contradictions) |
| Solution: v1 stdio, connection profile or env vars, usable from Claude Code/Desktop/VS Code | PRD FR-10, §2.1 | Captured |
| Users: agent operator, success = working cross-module task, no per-module setup | PRD §2.1 JTBD (near-verbatim) | Captured |
| Users: Hexalith's own agents (Agents, ChatBot, Conversations) gain one way to act instead of one integration per module | PRD §2.1 JTBD | Captured |
| Users: module authors — obligation shrinks to decorating records; visible day one; never write an MCP server again | PRD §2.1 JTBD, UJ-3 | Captured |
| Success: 4 modules exposed, zero module-specific code, 5th module = package ref + rebuild | PRD SM-1 | Captured |
| Success: agent completes 2+-module task with only the 5 generic tools, no per-module prompting/handwritten tool | PRD SM-2 | Captured |
| Success: at least one legacy server deleted, and no new per-module server created since acceptance | PRD SM-3 (deletion) + SM-C1 counter-metric (no new server, expanded to "or agent CLIs") | Captured (split/reorganized, not lost) |
| Success: "Every operation carries a description a person who has never seen the code can understand. A schema that validates is not enough." | PRD SM-5, NFR-8 (near-verbatim, phrase preserved) | Captured |
| Success: "CLI produces same catalog and same results as MCP server, so a shell script and an agent cannot disagree about what Hexalith can do." | PRD SM-4 + §2.1 JTBD "Shell user or CI script" (exact phrase preserved) | Captured |
| Scope in v1: attribute package, catalog builder, 5 tools + CLI verbs, stdio, JSON stdout/logs stderr, profiles borrowed from admin CLI, 4-module coverage, written no-new-server rule in Hexalith agent instructions | PRD §9.1, FR-22 | Captured |
| Scope next release (decided): HTTP transport same binary, forwards bearer/tenant/user headers as Parties does; no new auth server; legacy deletion as each covered | PRD §9.2, Addendum §B (McpContextForwardingHandler pattern) | Captured |
| Scope out of v1 (refused if proposed): plugin loading, typed one-tool-per-op, generated per-op CLI subcommands, event stream reading, MCP resources/prompts, cross-module aggregate/projection/handler/server references — **framed as "parked, not rejected forever," several are obvious follow-ups** | PRD §8 Non-Goals, §9.2, Addendum §A (D2, D3, D5 use "parked") | Captured, consistent framing |
| Scope out of v1: **any OAuth or identity server** — same "parked, not rejected forever" framing in the brief | PRD §8: "Not an identity provider: no OAuth server, no token issuance, no user store, **in any release**." Addendum D4: "rejected" | Contradicted (see Contradictions) |
| Guardrails every release: only 2 Hexalith deps (EventStore client + Contracts libs); tenant from envelope never payload; ULIDs via `Ulid.TryParse` never GUID; commands/queries distinguishable so read-only is one filter | PRD §6 Constraints and Guardrails | Captured |
| Vision: "In two years, an agent is a peer of the Hexalith user interface: anything a person can do through a screen, they can do by asking." | Not restated anywhere in PRD | Missing |
| Vision: identity must be the human's, so identity forwarding over HTTP is in the second release, not a nice-to-have | PRD §6 "Identity in v1" | Captured |
| Vision: "a command without a description is a command an agent cannot use, so the attribute stops being decoration and becomes part of what it means for a Hexalith operation to exist" | PRD §1, near-verbatim | Captured |
| Vision: "Every module that ships after this brief ships agent-ready or is not finished." | PRD §1, near-verbatim ("after this PRD") | Captured |

## Gaps

Ordered by importance; each with a suggested fix (exact section and wording).

1. **Long-horizon vision sentence dropped.** The brief's clearest statement of end-state ambition — "In two years, an agent is a peer of the Hexalith user interface: anything a person can do through a screen, they can do by asking" — does not appear anywhere in the PRD. The PRD's §1 Vision jumps straight from the v1 mechanism to the two "consequences that follow now" (identity, description-as-policy) without the sentence those consequences are consequences *of*. A reader of the PRD alone loses the reason the two consequences matter.
   - **Fix:** PRD §1 Vision, insert before the paragraph beginning "The consequence is a policy, not just a tool": *"In two years, an agent is meant to be a peer of the Hexalith user interface: anything a person can do through a screen, they should be able to do by asking. Two consequences follow now."* Then keep the existing two paragraphs, prefixing the identity one with "First," and the description one with "Second,".

2. **"Anticipatory build, no triggering incident" framing dropped.** The brief is explicit that this is a bet, not a response to an incident, and names *why now*: Agents, ChatBot, and Conversations will need cross-module action soon, and six dialects won't survive that contact. The PRD's §2.1 lists those same three modules as users but never states the anticipatory rationale, which matters for a "why build this now" reader (e.g., architecture or a skeptical reviewer).
   - **Fix:** PRD §1 Vision or a short new §1.1 "Why now," add: *"This is an anticipatory build: there is no triggering incident. The bet is that Hexalith's own Agents, ChatBot, and Conversations modules will soon need to act on business data across modules, and that six dialects will not survive that contact."*

3. **Root-cause claim about descriptions ("XML doc comments do not exist at runtime") dropped.** The brief's second problem statement is a specific causal argument — descriptions live in XML doc comments, which vanish at runtime, so every server hand-redescribes operations and each description drifts from the code it describes. The PRD's FR-4 NOTE only states the current-state fact ("zero `[Description]` attributes exist today"), not this argument for *why* a runtime-visible description mechanism is required at all. Losing the argument weakens the rationale for FR-1/FR-4 to a reader who wasn't in the brief conversation.
   - **Fix:** PRD §4.1 Operation Decoration, description paragraph, add a sentence before "A Module author can apply...": *"Operation descriptions have historically lived in XML doc comments, which do not exist at runtime; each Legacy Server hand-redescribed its operations and drifted from the code. The Decoration Attribute makes the description part of the runtime contract instead."*

4. **CLI verb renamed from `serve` to `mcp` with no explanation.** See Contradictions — also a gap in the sense that no section explains or acknowledges the rename, so a reader comparing brief and PRD will assume an error rather than a decision.
   - **Fix:** PRD §11 Open Questions, add an entry (or fold into existing Q7 "Package identifiers"): *"CLI verb naming: the brief specifies a `serve` verb to start the MCP server; this PRD uses `mcp` (FR-12) for symmetry with the `mcp` transport concept. Confirm this rename with the product owner before scaffolding."*

5. **Minor problem-statement texture dropped:** "every divergence is a place for the model to guess wrong," and "maintenance of six servers and friction for the next module author are real costs too, but they follow from the same root cause and disappear with it." Neither changes scope, but both are argumentative color the brief uses to justify replace-over-coexist (D6) and are absent from PRD §1 and Addendum §A.
   - **Fix:** Addendum §A, D6 bullet, append: *"Coexistence also leaves the concrete costs of six servers — duplicated maintenance, and friction for the next module author, who must again choose a dialect — unaddressed; both follow from the same root cause replacement removes."*

## Contradictions

1. **CLI `serve` verb vs `mcp` verb.** Brief Executive Summary: "A CLI with the matching verbs, plus a `serve` verb that starts the MCP server." PRD FR-12 and Glossary "CLI": the verb is `mcp`, not `serve`. No section of the PRD or addendum acknowledges the rename or gives a rationale — it reads as an unexplained divergence rather than a deliberate one. Flag for product-owner confirmation (see Gap 4 fix).

2. **OAuth/identity server: "parked" vs permanently excluded.** Brief Scope: OAuth/identity server is listed among items "Out of version one, and refused if proposed... **These are parked, not rejected forever**, and several are the obvious follow-ups once the catalog is stable." PRD §8 Non-Goals states flatly: "Not an identity provider: no OAuth server, no token issuance, no user store, **in any release**." Addendum §A D4 similarly says "any authentication server rejected." This hardens the brief's "parked, revisitable" stance into a permanent non-goal without the PRD explaining or flagging the change — likely intentional (an identity provider is a different kind of build than the HTTP header-forwarding transport that *is* planned for the next release), but as written it silently narrows a decision the brief left open. Recommend either labeling it explicitly as a deliberate divergence in §8, or softening to match the brief ("not in v1 or the next release; not evaluated further").

3. **Folders needs upstream Contracts work before it can be covered — deliberate divergence, self-explained.** Brief Scope simply lists "Coverage of Tenants, Parties, Projects, and Folders" as in-scope for v1, with no caveat. PRD §9.1 reveals (via research in Addendum §D) that `Hexalith.Folders.Contracts` today holds only OpenAPI YAML — no Command/Query records — making Folders the largest of four named prerequisites, and explicitly notes: "The product owner chose to keep Folders in v1 rather than swap it out." This is a genuine divergence from the brief's flat scope statement, but the PRD itself labels and explains it as a considered decision (`[NOTE FOR PM]`), so it is a **deliberate divergence**, not an oversight.

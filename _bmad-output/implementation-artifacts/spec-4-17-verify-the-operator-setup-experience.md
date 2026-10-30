---
title: '4.17 Verify the operator setup experience'
type: 'feature'
created: '2026-10-29'
status: 'draft'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'c99aebe4a93ca611a443c83f031ef1c02bd499b7'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The staged tool has portable installation and protocol evidence, but the README lacks operator installation and client registration instructions. No executed three-client checklist or README-only time-to-command measurement exists.

**Approach:** Document installation and one shared stdio server in Claude Code, Claude Desktop and VS Code, then retain actual client sessions completing an approved Tenants/Parties task and a timed first-command session.

## Boundaries & Constraints

**Always:** Use the exact accepted Story 4.16 staged tool, version 1.2.0, source `32fb5dbf75216adaf21551bcfa36439741c41e01`; verify its preparation/accepted receipts and package hashes. Record the README revision or content hash, client/OS versions, environment and operation approval, initialization, discovery, tool calls and outcomes. Keep credentials private. Use explicit executable paths, .NET 10 and an isolated profile; explain Windows/WSL and GUI launch-environment differences. Preserve fixed `system` routing for Tenants and the selected tenant for Parties. Record all timing attempts, assistance, failures and elapsed seconds against 900 seconds.

**Never:** Publish packages/tags/releases, enable paired publication, change production behavior or approved enrollment, edit references, replace actual client evidence with SDK smoke, or present an experienced agent as a new operator. Do not submit writes outside the selected approved environment or retry an uncertain command outcome automatically.

**Human decisions (2026-10-29):** Use Hexalith.Platform at `192.168.1.30`; inspect its submodule for access details. The user will perform the GUI-client checks and timed README-only session.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Accepted local staged package | Install from an explicit local-only source at its exact version; record executable/version and hash binding |
| Client initializes and discovers | One server exposes the five generic tools and both modules; capture actual client evidence |
| Approved cross-module task | Read the selected tenant through Tenants, create one fresh test Party in that tenant, then query its persisted details |
| Missing runtime, PATH, profile, permissions or service | Record the exact failing step and actionable setup correction; leave acceptance incomplete |
| New operator uses only README | Start timing immediately before installation; stop at the first successful MCP `send_command`; retain elapsed time and target result |
| Target exceeded, assisted or interrupted | Preserve the measured outcome and assistance; distinguish it from an unassisted success |

</frozen-after-approval>

## Open Questions

1. **Platform preparation scope:** The selected host's cluster and Platform records provide no installed Parties/Gateway/tenant/credential binding for this task. The qualified local seven-server run was cleaned up. Options: include preparing a temporary Platform test environment on `192.168.1.30` (additional owning-repository configuration and deployment preparation); or implement documentation/checklist work first and retain live verification as incomplete until Platform supplies that environment. The existing isolated secret-test registry is not a substitute. Preparing a deployment does not itself authorize applying it.

## Code Map

- `README.md` — existing CLI/profile contract and five-tool MCP surface; add operator-first installation, three client configurations, task steps and troubleshooting.
- `scripts/smoke-paired-tool.py`, `scripts/paired_release.py` — reuse isolated installation, package verification and capture patterns; existing offline smoke is supplementary evidence only.
- `evidence/story-4-16/hosted-20261029/accepted-32fb5db/` beneath implementation artifacts — accepted pair, preparation receipt and artifact links. Exact packages currently exist in `/tmp/mcpcli-416-hosted-svjuv79c/attempt4/paired-preparation/packages/`; temporary availability is not a durable release link.
- `tools/conformance-vectors/v1/modules/Hexalith.Parties.Contracts/create-party.vector.json` and Tenants `get-tenant.vector.json` — approved payload shapes; use fresh identifiers rather than shared vector fixture IDs. Their approvals do not approve a new combined task/environment.
- `tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs` — isolated short-lived test identity/lifecycle, not a reusable GUI-client endpoint. Its token covers `system` and `tenant-a`, not arbitrary newly created tenants.
- `evidence/story-4-17/environment-20261029/inspection.json` beneath implementation artifacts — successful bounded Kubernetes metadata reads through `jpiquot@local`; does not inspect applications outside Kubernetes or establish application credentials.
- Adjacent `platform-submodule-assessment.json` — Platform revision `8de90958bc41b7fd01b7ed22b8ab364447a800e4`, source hashes and dated deployment findings; no later installed operator binding found.

## Tasks & Acceptance

**Execution:**

- [ ] `README.md` — add exact staged-tool installation, prerequisites, profile/credential setup and separate Claude Code/Desktop/VS Code stdio examples checked against current official client documentation; include expected discovery and concrete cross-module calls with JSON-text payloads.
- [ ] `docs/release/operator-setup-checklist.md` — add the release checklist and reproducible session/timing procedure, evidence fields, target calculation and explicit incomplete/failed outcomes; link it from README.
- [ ] `_bmad-output/implementation-artifacts/evidence/story-4-17/` — verify package provenance; retain actual three-client initialization/discovery/task records and sanitized read-after-write results, plus the independent new-operator timing record and README hash.
- [ ] `README.md`, this spec and `sprint-status.yaml` — correct issues exposed by execution, retain unsuccessful attempts, and advance status only when the required executed evidence exists.

**Acceptance Criteria:**

- Given the accepted staged tool and README, when each named client follows setup, then its checklist records actual initialization, both-module discovery and the approved cross-module task using the same generic server without a module-specific server or MCP prompt.
- Given a new operator with only README, when timing begins before installation and ends at the first successful `send_command`, then elapsed time and whether it meets 900 seconds are recorded; a miss remains visible.
- Given missing client or task evidence, when readiness is reported, then the checklist and story remain incomplete with the exact blocker.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

Current footprint is documentation and task-owned evidence. Client calls and test-data writes are external effects. Host and human operator are selected; temporary Platform preparation is the remaining scope decision. No deployment, domain call or Secret retrieval has occurred.

## Verification

- Independently compare both package SHA-256 values with the accepted receipt and check the installed tool version before client runs.
- Run documented discovery/profile commands against the installed staged tool with isolated home and capture stdout/stderr; parse every configuration example.
- Inspect each actual client tool transcript and persisted query result; check evidence contains no credentials.
- Recalculate elapsed seconds from retained start/end timestamps and report assisted, failed and over-target attempts explicitly.

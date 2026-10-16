---
title: '4.2 Approve the Folders migration inventory'
type: 'chore'
created: '2026-10-16'
status: 'done'
baseline_commit: '09655746f9373dbb5df4bcea46c5d155902f2208'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The existing Folders inventory is an unapproved September snapshot.
It cannot establish agreed migration coverage for 49 MCP tools, two resources,
42 Frozen CLI leaves, or their behavior variants.

**Approach:** Finalize a versioned, source-pinned inventory outside `src/`, with
an explicit disposition, coverage decision, rationale, security class, future
contract or unresolved prerequisite, and actual approval reference for every
legacy surface. Preserve a separate normalized future-target table.

## Boundaries & Constraints

**Always:** Reconcile the draft against clean Folders revision
`e2252f29a2dba2b64786ee483eb59fbceaadd387`. Recommend `defer` / `exclude`
for all current rows because no decorated Gateway-ready replacement exists.
Retain 48 named future candidates (13 Commands and 35 Queries), consolidate
the three file mutations, and split ACL grant/revoke. These candidates are a
roadmap, not included coverage or an assertion of published Contracts.

Preserve authorization, tenant authority, redaction, metadata-only outputs,
task scope, idempotency, identifier compatibility and freshness requirements.
Record unsupported variants and their lost convenience explicitly. Attribute
future work to owning Folders/platform maintainers without inventing signatories
or granting exposure. Record only the user's actual approval and its limits.
Folders remains post-v1; advancing a row to `replace` / `include` requires a
later approved revision and dependency, Catalog and Gateway evidence.

**Never:** Claim parity from matching names; treat projection delivery as query
execution; invent dry-run behavior or approval. Change runtime, upstream
checkouts, enrollment, dependency versions, publication or retention. No
Folders-specific generic runtime branch, MCP resource, retry engine, file
transport adapter, or weakening of canonical uppercase ULID rules is authorized.
No withdrawal or early legacy server/CLI deletion is proposed.

</frozen-after-approval>

## Code Map

All following upstream paths are under `references/Hexalith.Folders/`:

- `src/Hexalith.Folders.Mcp/Tools/*Tools.cs` and `Resources/*.cs` declare
  49 tools/two resources; `Program.cs:64` registers both surfaces.
- `src/Hexalith.Folders.Cli/Commands/` and `CliApplication.cs:45` define 42
  leaves. Reuse the old inventory's verified leaf links, not the parity fixture's
  placeholder CLI expectations for seven diagnostics.
- `src/Hexalith.Folders.Client/Serialization/OperationFreshness.cs:25` and
  `Generated/HexalithFoldersIdempotencyHelpers.g.cs:196` pin one accepted
  freshness value per read. `Convenience/FoldersFileUploadExtensions.cs:37`
  handles bounded inline uploads; each adapter's `Infrastructure/MetadataOnlyJson.cs`
  suppresses content even on authorized range reads.
- `src/Hexalith.Folders.Server/FoldersDomainServiceRequestHandler.cs:245`
  requires lowercase envelope identifiers and `taskId`; `FoldersServerModule.cs:30`
  pins domain/wires. `FoldersDomainServiceEndpoints.cs:105` now dispatches
  projections; the old draft's 501 claim is stale. No Gateway query handler or
  decorated Contracts Command/Query was found.
- `src/Hexalith.Folders.Contracts/Hexalith.Folders.Contracts.csproj` has no
  direct dependencies; inspect an eventual decorated package's exact closure
  rather than assuming it fails or passes McpCli's allowlist.
- Local `src/Hexalith.McpCli.Core/Execution/RunQueryArguments.cs` has paging
  but no query extensions/freshness members. `tools/dependency-policy.json`
  and `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs` govern
  future enrollment. Leave these files unchanged.

## Tasks & Acceptance

**Execution:**

- [x] `_bmad-output/implementation-artifacts/folders-migration-inventory-v1.md`
  — finalize the complete candidate: 49 tool, two resource and 42 CLI rows;
  48 unique future targets; explicit variant and prerequisite tables.
- [x] Same inventory — record the actual approving instruction, source/version,
  scope and approval references on every row. Keep missing execution evidence
  and future contract/transport decisions explicit.
- [x] `_bmad-output/implementation-artifacts/evidence/story-4-2/verification.md`
  — preserve repeatable static checks for source counts, target reuse,
  disposition/coverage pairs, source pin and approval state.
- [x] `_bmad-output/implementation-artifacts/folders-migration-inventory-draft.md`
  — mark its historical status and link the successor without rewriting the
  old source snapshot as current evidence.
- [x] This spec and `sprint-status.yaml` — synchronize status after applicable
  approval and validation gates; preserve unrelated tracking.

**Acceptance Criteria:**

- Given the pinned source, when completeness is checked, then all 49 tools,
  two resources and 42 actual CLI leaves have distinct rows and no invented leaf.
- Given an inventory row, when its scope is inspected, then disposition,
  coverage, rationale, security class, future contract or gap, and actual owner
  approval reference are explicit; missing approval prevents completion.
- Given a behavior variant, when replacement is considered, then freshness,
  filtering/paging, redaction/content, task context, local input, auto-key,
  dry-run evidence and non-Gateway transport prerequisites are accounted for.
- Given a future candidate, when readiness is reported, then no row becomes
  included solely from this inventory; Folders remains post-v1 and its existing
  server/CLI remain until approved replacement/withdrawal and behavior,
  authorization and release gates pass.

## Implementation Notes

- 2026-10-16: The requesting user approved this spec and its recommended deferred
  scope with the exact instruction "approve and stop". Leave all current rows
  `defer` / `exclude` and retain 48 future candidates. This is session approval,
  not an assertion of an external signatory or Gateway/retirement readiness.
  At that checkpoint implementation and review had not started; the approval
  authorized the deferred scope recorded by the implementation below.

- 2026-10-16: Finalized inventory 1.0.0 with A1 session approval on all 93
  legacy rows, 48 normalized future targets, ten behavior variants, four adjacent
  exclusions and six owned prerequisite rows. Every legacy row remains
  `defer` / `exclude`; no runtime, upstream checkout, dependency or retention
  change. Added exact CLI declaration anchors and preserved the historical
  draft beneath a successor notice. Static verification passed; workflow review
  and final status synchronization remain with the parent build session.

## Spec Change Log

## Review Triage Log

2026-10-16: three independent review layers completed. Edge-case review returned
no findings; verification-gap review returned no findings. Blind-hunter findings
were verified individually below before grouping; each surviving correction is
a separate, direct documentation or static-verifier patch.

| ID | Verdict | Route | Finding and verified evidence |
| --- | --- | --- | --- |
| BH01 | false | rejected | A1 falsely claims Folders maintainer authority. A1 explicitly identifies session approval only and disclaims a named maintainer or external signatory, as required by the approved frozen scope. It approves deferred inventory scope and supplies no external owner or Gateway approval; inventing approver capacity would contradict that scope. |
| BH02 | false | rejected | Candidate approval and implementation chronology conflict. The complete candidate and its passing source/row evidence existed at build entry, while finalization had not started; approving that candidate's deferred scope and implementing its final approval references later are compatible. A1 names both candidate and final versions, and the spec preserves the earlier checkpoint as historical. |
| BH03 | medium | patch | V07 omits hashed caller-key compatibility. Upstream `FileUpload.ComputeIdempotencyKey` returns `sha256:<hex>` through `HexalithIdempotencyHasher`, while local `OperationExecutor` rejects any noncanonical-uppercase-ULID idempotency key before submission. The future handoff must name this distinct replay migration prerequisite. |
| BH04 | medium | patch | V05 omits the absolute upload maximum and overstates streaming guidance. `FileUpload.BuildInlineFileMutation` checks 1048576 bytes before 262144: above the maximum throws `FileContentLimitExceededException`, while the intermediate range throws `FileUploadStreamingRequiredException`. Preserve both outcomes for future callers. |
| BH05 | low | patch | V04 omits helper-derived request evidence. `FileUpload.BuildInlineFileMutation` supplies `v2`, decoded byte length, content-hash reference and `PutFileInline`; future generic JSON callers need an explicit handoff for these values. Add the source fields and unresolved ownership without implementing an adapter. |
| BH06 | low | patch | V09 lacks exact legacy credential precedence. `CredentialResolver.ResolveToken` uses environment, tenant-selected file, then flag; `McpCredentialResolver.ResolveToken` uses environment, inline configuration, then token file. Recording this directly prevents future setup guidance from silently choosing another credential or section. |
| BH07 | medium | patch | V09 omits exit-code compatibility for scripts. `FoldersExitCodes` distinguishes usage/credential/access/lock/idempotency/validation/provider/reconciliation/redaction/expiry/concurrency failures, while McpCli operational errors use exit 2. Record this absent generic behavior and the need for future migration acceptance. |
| BH08 | medium | patch | G1/C05 omit provider actor routing. `FoldersDomainServiceRequestHandler.IsAdmittedActor` requires `ConfigureProviderBinding` to use `ProviderBindingActorId.IsReserved`, disjoint from the tenant actor; other commands use separate admission rules. Name that C05 prerequisite to prevent an unsafe folder-routing assumption. |
| BH09 | medium | patch | The verifier accepts wrong legacy-to-target associations. An in-memory mutation swapping Q02/Q03 on M16/M17 and L15/L28 passed the entire old checker. Validate every source-backed association and its Command/Query kind, preserving explicit file/ACL exceptions. |
| BH10 | medium | patch | The verifier reconstructs wires without checking recognizers. An in-memory C01 mutation to `folders.archive-folder-invented` and matching invented CLR/wire names passed the entire old checker. Compare candidates with actual pinned wire constants and processor dispatch, including aggregate-owned constants. |

Completion: BH03–BH10 were corrected in the inventory/verifier; BH01–BH02 were
rejected on the evidence above. The parent reran the complete revised verifier:
exit 0, including rejection of both in-memory mutations. No new deferred-work
entry was needed; the approved inventory's future prerequisites remain open.
The build spec is done and the sprint entry remains `review` for the separate
story review transition required by this workflow.

## Verification

- Run the source/row checks preserved in the evidence document. Expect exact
  surface sets, 48 unique future candidates, valid pairs and explicit approval
  state. Static documentation checks prove no live Gateway behavior.
- Recheck `git -C references/Hexalith.Folders rev-parse HEAD` and
  `git -C references/Hexalith.Folders status --porcelain`: pinned SHA, clean.
- Run `git diff --check` and inspect changed paths: local Markdown/YAML only.
  No .NET build is needed for this artifact-only change.

- 2026-10-16 implementation validation: executed the complete Bash block in
  `evidence/story-4-2/verification.md` with `bash -e` via Python's
  `subprocess.run(..., check=True)`; exit 0. It confirmed exact pinned source
  sets/mappings, all 48 unique/reused future targets and all 161 A1 row
  references. The historical draft body matches baseline commit
  `09655746f9373dbb5df4bcea46c5d155902f2208`
  byte-for-byte. `git diff --check` exited 0; existing missing commit-graph
  warnings did not affect the result. No .NET build required for these artifacts.

- 2026-10-16 parent completion validation: the complete revised Bash block
  passed with exit 0 after all review corrections. It rejects ordinary-target
  swaps and invented command wires, preserves the clean pinned upstream source,
  and checks whitespace for tracked and new artifacts. All tasks and acceptance
  criteria are satisfied for the approved deferred inventory scope.

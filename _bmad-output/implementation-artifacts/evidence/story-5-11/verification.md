# Story 5.11 verification — preparation, not integrated completion

Assessed 2026-11-16 from full McpCli baseline
`008d95ccc77d932a372cb6c749d9d1fb1bc1ea57`. The spec and sprint remain
spec **in-review**, sprint **review**. `approval.json` is **pending**; no approver, covered-role consent,
delivery authorization, published inventory revision or upstream integration is
invented. `integration.json` records the exact missing bindings. The authoritative
AI.Tools plan remains **1.2.0**. The prepared **1.3.0** file explicitly says
`inventory_revision: null` / `candidate-not-publishable`.

## Prepared changes

- Admin 1.0.3 and technical 1.0.4 correct their predecessors' frozen pending
  self-description by pointing to their own receipt decision. Story 5.7 approval
  remains separate factual authority. All 91 Admin and 68 technical row
  identities, source pins, dispositions, safety fields and owners are retained;
  only authority pointers/current companion citations change. Folders 1.1.0 is
  now cited. Exact bytes are protected by `.gitattributes`.
- `inputs.json` indexes **23 versions across eight inventory families**, full
  source revisions/repositories, file and receipt hashes, effective authority,
  fourteen labels and prerequisite states. Session scope never becomes owner
  completeness authority. Approved ChatBot/Memories inventories remain distinct
  from incomplete Story 5.10 delivery.
- `upstream/manifest.json` binds **30 patches across nine owners**: seven root
  READMEs and their active PRD/architecture/flow topics, Tenants architecture,
  and the AI.Tools rule/plan. Eight inspected roots have sourced no-change
  rationales. Patches are prepared outside `references/`; no owner worktree or
  reference was changed. Bases are locally observed `origin/main`, not a claim
  of fresh remote-main verification. ChatBot/Memories patches compose with the
  approved Story 5.10 README sections and explicitly depend on their delivery.
- Local MR1/MR6, FR-21, architecture, README and Epic 5 context follow adopted
  AD-23. Confidential UI, withdrawal and named exemptions need no invented
  transport. Runtime exposure, production dependencies, census, Builds/CI-owned
  files, frozen AD-23/evidence and historical release notes stay unchanged.
- The committed release status enumerates PS01–PS14, all remaining binaries,
  K13/K14 retained tooling and independent removal gates. The module-owned
  semantic-release hook preserves the pinned conventional generator and all
  existing preflight, preparation, publication and GitHub settings.
- `deferral-dispositions.{json,md}` audits **56 entries**: the original drift row
  and all 55 Epic 5 rows, including 5.12. Existing source headings, evidence,
  owners and gates remain. The ledger has one audit pointer, no duplicate
  reconfirmation entry. Explicit owner acceptance of the audit is still pending.

## Checks and evidence

All disposable test/probe workspaces use `run-with-temp`; retained results stay
in this evidence directory. The following commands and their results are
captured in `checks.json` and the adjacent stdout/stderr files:

```sh
run-with-temp python3 _bmad-output/implementation-artifacts/evidence/story-5-11/verify_reconciliation.py
run-with-temp python3 -m unittest discover -v -s _bmad-output/implementation-artifacts/evidence/story-5-11 -p test_verify_reconciliation.py
run-with-temp node --test scripts/tests/migration-release-notes.test.mjs
run-with-temp python3 _bmad-output/implementation-artifacts/evidence/story-5-11/check_offline_cli.py
bash scripts/check-agent-instructions-sync.sh
git diff --check
```

All **17 focused verifier tests pass**. They cover exact exit/stdout/stderr results; missing
version, source revision, role, hash, gate, approval and integration; predecessor
and class/disposition preservation; approved-but-undelivered inventories;
pending receipt status; explicit deferral acceptance; unresolved Parties/Folders/
Projects gates; and never-retired compiler/vector exemptions. Five controls
remove actual verifier guards and demonstrate that each corresponding invalid
fixture is then admitted. The generator also refuses rewriting an approved
packet. The verifier applies every patch in private scratch and checks exact
resulting hashes. EventStore architecture uses a hash-bound literal replacement
recipe: immutable source prose otherwise triggers the shared scanner on an
ordinary authentication word. The recipe copies only changed fragments and
reproduces the exact candidate target bytes; no source is redacted. Derived ledger
excerpts and public help captures use the shared redactor, retaining original
entry/raw-stream hashes. The initial scan failure is preserved separately;
disposable Python bytecode was removed and final tests disable bytecode writes. Synthetic complete-delivery tests exercise published bytes,
owner main containment, mandatory checks, final-plan approval, AI.Tools
containment, instruction synchronization and completion-date SM-3 reassessment.

Both Node tests pass and invoke installed `@semantic-release/release-notes-generator` **14.1.1**,
check unchanged conventional output plus the complete committed status, and
refuse absent or empty status input. No publishing plugin is invoked.

`offline-cli.json` records a private installation of the published **2.0.1** tool
and its package hash. Discovery/help, unknown-operation refusal (exit 2), MCP
initialization and the five generic tools pass. Its installed cohort lists
Parties (7) and Tenants (14). No `send`, `query` or `tools/call` execution was
performed. An initial unrecognized `command --help` probe is retained as a
diagnostic; setup was corrected to the actual `send` verb. Released CLI syntax
is verified separately from source-selected package/runtime availability.

The source command `dotnet restore src/Hexalith.McpCli/Hexalith.McpCli.csproj`
fails **NU1102**: baseline `Hexalith.Projects.Contracts >= 2.0.0-story66.3` is
unavailable from nuget.org; nearest version 1.2.4. Exact streams are retained in
`cli-restore.{stdout,stderr}.txt`. No source build or current-source CLI success
is claimed, and no dependency was changed to bypass this blocker.

Parties owner documentation fitness tests were inspected at the manifest pin;
their SDK/project inventory, routes/ACLs, external deployment and direct-tool
onboarding claims are preserved. No owner test needed editing. No owner build,
service startup, Gateway execution, live parity or retirement gate is claimed.

The shared `secret-scan-final-reviewed.json` is the authoritative final scan result and hashes
every regular evidence file except itself; `checks.json` records sync/diff exits.
No successful scan is implied if that receipt is absent or non-clean.

## Completion gates retained

Fresh exact-byte owner approval is still required for the prepared successor/
label/audit packet, covering every named role. Git delivery needs separate
explicit authorization of the actual final footprint. Story 5.10 delivery is
still incomplete. Its mandatory `python3 references/Hexalith.Builds/check.py`
fails because `.github/hexalith-ci.json` is absent; CiCd owns remediation and
this story does not bypass it.

After approved inventory publication, final plan bytes must bind the full
immutable McpCli revision and links, receive their own fresh exact-byte approval,
and integrate into authoritative AI.Tools main. Every owner patch needs fresh
main verification, rebase as needed, exact bytes, commitlint and mandatory Builds
checks. Only then may the AI.Tools gitlink move and instruction sync be bound.

Parties remains `retirement-blocked` under G01–G06 and its independent restricted
classification/exposure conflict. Folders K12 and Projects Payload paging versus
AD-20 remain blocking owner successors. The recorded owner decision is **Labels + slip**. SM-3 is **pending-not-met**; deadline **2027-02-05** remains future on
2026-11-16. Completion must reassess the actual date and obtain an explicit
owner decision on the sourced deferral audit. No gate is closed or waived by
preparation, and no ecosystem completion is claimed.

## Review corrections (2026-11-16)

All fourteen requested patch groups are implemented; the existing review triage
log and frozen intent are unchanged. FR-22 and the PRD opening claim now use the
adopted class outcomes. The plan preserves ongoing owner-approved inventory
amendments for source/behavior changes, a new plan version for every change and
a moved inventory revision for additions/re-pins. Parties 1.0.0 is session scope
only; 1.1.0 and 1.2.0 retain their later owning-maintainer receipts.

Completion resolves `rootIntegrationRevision`'s actual committed AI.Tools gitlink
and proves it contains the exact `ai-tools` owner integration. A newer checkout
cannot satisfy an older committed pointer. Final approved plan bytes must retain
the same independent gate/exemption/change-control semantics and correct
GitHub repository/revision/path Markdown links for every inventory and approval
receipt. An unrelated, mutable or wrong-host link is refused.

`completedOn` binds the structured `sm3Assessment`; later historical verification
uses that recorded date. A met outcome needs hash-bound retired-state evidence
by the deadline. Pending/slip outcomes cannot invent retirement; an overdue
unmet outcome needs an explicit owner/source slip reason. The structured
`deferralOwnerDecision` must explicitly accept the exact JSON/Markdown audit
while retaining every unresolved entry and its source owner/gate. A nonblank
undecided sentence is insufficient. Gates are derived from each ledger entry's
recorded obligation, owner assignment, status and evidence, without source-story
routing heuristics; net11 maintenance and technical re-citation remain independent.

The frozen Story 5.10 owner packet and original delivery checks are reused at
its recorded owner/publication revisions. Current 1.0.4 supersession is checked
independently. A focused lifecycle case executes these prerequisite checks
with historical delivery objects and newer current labels, rather than mocking
away the prerequisite. No frozen Story 5.10 file changed.

Offline probes now require the complete unknown-operation stdout document and
empty stderr, expected cohort/operation/typed discovery JSON and exact generic
tool names/schemas. Stdio reads chunks under one absolute response deadline;
a partial-line child fixture verifies timeout and bounded cleanup. The new
`scripts/tests/test_migration_release_notes.py` adapter runs Node notes tests
under normal Python discovery and propagates exact failures in direct mode.

Focused validation: **27 story tests pass** (24 reconciliation/builder cases and
3 offline-probe cases), and **2 Python adapter tests pass**, including execution
of the two pinned Node tests. See `review-fix-validation.json` and
`review-fix-tests.{stdout,stderr}.txt`. Only tests covering edited files ran.
The pre-review check/scan receipts describe the earlier packet; hashes have
been regenerated for the pending packet, and final full verification/scan is
left to the parent reviewer. Approval, prerequisite delivery, CiCd configuration,
Git authorization, inventory publication and upstream integration stay blocked.

## Parent verification after review fixes

All fourteen review patch groups are resolved. `final-checks/checks.json` and
its exact streams record the final reviewed tree: 24 reconciliation tests plus three offline-probe tests; two Python
adapter tests that execute the two pinned Node tests; candidate verification;
expected completion refusal; fresh published 2.0.1 offline/stdio probes; adopted
AD-23; instruction synchronization; and whitespace checks. Every expected exit
code matches. The source restore blocker remains the separately retained NU1102.

The final `secret-scan-final-reviewed.json` supersedes the pre-review scan and is authoritative
for the resulting evidence files. This report and the spec do not claim owner
approval, completed prerequisite delivery, upstream integration or retirement.
The audit is prepared, with explicit acceptance still pending. Story 5.10 delivery
changes its register: refresh the pending 5.11 bindings after that prerequisite
completes and before requesting final exact-byte approval. No commit or push was
created. The approved intent's separate-authorization and completion requirements
prevent the generic workflow's terminal commit/done step at this point.

## Shared-guidance correction and authorized delivery continuation

The user subsequently requested “push all changes” and “fix”. Upstream AI.Tools
main cfd1ebea92587cdea41b9aa2cff47358bf2f32f6 already scopes check.py to adopted
modules. Updating the containing root baseline resolves the earlier mandatory
missing-configuration interpretation; McpCli retains its existing CI until actual
CiCd adoption. No owned workflow/configuration or Builds pin is edited.
See evidence/git-guidance-fix-20261116/resolution.json from the repository root.
Candidate approval, Story 5.10 delivery and final plan integration remain distinct.
The old scan receipts describe their captured states; a delivery scan supersedes
them for the updated verification/integration metadata.

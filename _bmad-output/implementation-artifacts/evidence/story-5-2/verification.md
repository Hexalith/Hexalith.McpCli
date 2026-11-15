# Story 5.2 verification — owner-adopted AD-23

Prepared and adopted 2026-11-12. **Exact-byte owner adoption is approved.**
The receipt establishes effective ADOPTED status and the spine records it; no
row has been re-dispositioned. The decision/map bytes remain unchanged. This packet grants
no execution, enrollment, publication or retirement authority.

The exact AI.Tools amendment `10b709b86f9c9148e5a18177e8d11fad79ae2c0b`
was separately approved, pushed and merged to AI.Tools main on 2026-11-12;
[delivery](upstream-delivery.json) and [integration](main-integration.json)
record that final state. Its amendment merge gate is satisfied. Census
reclassification still requires its own approval.

## Dated correction (2026-11-15, review pass 1)

The approval-time partition sentence retained and labeled below overstates the
total and classified counts by 100. The bound source identities, original
table and byte-identical verifier output establish **525 total identities =
372 classified rows + 153 explicit records**, consistent with the spec's
estimate. The approved decision, map, inventories and adoption receipt remain
unchanged; this note corrects the presented packet without rewriting that
historical sentence.

The local-only amendment paragraph and pending-merge delivery paragraph below
are labeled point-in-time records. Both precede the separately authorized
main integration. The final state is pushed and merged as stated above;
exemption never counts as retirement or automatically reclassifies the census.

The current [review-pass-1 packet](review-pass-1/README.md) records **64 passing
verifier process tests**, **eight runner process controls**, and the corrected
single-removal sweep that kills all **57 require guards**,
with zero survivors or runner errors. Every rejection pins exit 1, empty stdout
and the exact full `FAIL: …` stderr line. Malformed non-object JSON now uses
that channel too, and the real-packet success test pins the entire original
adopted stdout. The explicit-record set check runs before generic missing-row
validation and names missing/extra record IDs. Success stdout is unchanged.
The unbound spine's Design Paradigm and FR-21/FR-22 trace now cite adopted AD-23.

## Dated scope correction (2026-11-15, code review pass 2)

The story-labeled commit `28bcbbb898b6530838a7872f2ba450c34e56cc70`
also carried the following nine **non-story gitlink moves**. These are part of
that commit, rather than unrelated changes that predated the story. AC3's
requirement that `references/` stay unchanged **does not hold for `28bcbbb`**.
The owner chose **“Keep pins, align apart”** on 2026-11-15: these published
revisions stay on `main`. Builds workflow/dependency-policy alignment and
census reconciliation belong to a separate `build(deps)` change under the
repository's Builds-move procedure, outside Story 5.2. They are not a story
ledger deferral, and this correction makes no CI-success claim.

| Gitlink | Before `28bcbbb` | In `28bcbbb` |
| --- | --- | --- |
| `references/Hexalith.Builds` | `99f7c86072ca7b35e3fbbaee4606a559a847805a` | `73e60af8a1fcdf3f06726d5d1b6e1199cce778ee` |
| `references/Hexalith.EventStore` | `5c5c0cce54541f18ec4f290f085d8678d517e8f8` | `fdb59895975e86a1e234325a01237f259cdbd53b` |
| `references/Hexalith.Folders` | `6ac670743c94f7819bb80f0914801cdbf84ceb3f` | `bb990a8766a9feac42ff7ecf02c8b7ca42a7ba15` |
| `references/Hexalith.FrontComposer` | `bfc8f8ae74e3ff0baa2d1d4abf083b0b47e6dca3` | `09e5dd0fce32df9653365759d955e1e78df74ed7` |
| `references/Hexalith.Memories` | `2c2e9b58990638ededf22e8e67ff5c12de75b434` | `66e2441e2536fc37708aca2bd3456fd4cd21a439` |
| `references/Hexalith.Parties` | `53844114ffcedc5af96fbf1cb15e126adaae02a9` | `e59aed9ca2d111b0195afe078611e2184b6de4c5` |
| `references/Hexalith.Platform` | `9a1cf867b931d93451a2e2cf5749b1b444f7bb7a` | `f6f85032598865b9123f16364448bfd02c0ff5b0` |
| `references/Hexalith.Projects` | `b756d01aef5a53ad7f52f0d3a8bc76a1d03d441b` | `fc58cefde69d72d7d3daa574b5022f73f830a85e` |
| `references/Hexalith.Tenants` | `30b9b61845e35052187c86968880c79d8e76cd2b` | `2ec938397c5b330cf1e694e8cc442cb4ad022f2b` |

The retained review-pass-1 receipts are unchanged. Their empty forbidden-path
checks cover only `28bcbbb..5f35a70`; every “unchanged in this run” statement
for that packet is limited to the follow-up ending at `5f35a70`. Those checks
do not establish AC3 for `28bcbbb` or erase the nine moves above. The current
pass-2 patch starts at `32a3e65989136f28b34500a4d9db8f04cf601885` and preserves
those pins, all inventory bytes, the approved decision/map and owner receipt.

The current [pass-2 patch evidence](review-pass-2/README.md) records **70 passing
verifier process tests**, **eight runner controls**, and **six killed focused
sub-condition mutants**. The standalone adopted stdout remains byte-identical;
all real artifacts in the success test are now verified from verbatim copies.
The earlier 64-test result describes the retained pass-1 checkpoint.

## Dated note (2026-11-15, code review pass 3)

The [pass-3 packet](review-pass-3/README.md) records:
- **74 passing verifier process tests** and the **eight runner controls**;
- **four focused sub-condition mutants**, each killed only by the new cases;
- a fresh **57-of-57** guard sweep.

`.gitattributes` now keeps the decision, map, eight bound inventories and this evidence
folder byte-exact on checkout. The spine's AD-23 Provenance names `28bcbbb`'s nine gitlink
moves. The approved bytes, the receipt and the adopted stdout are unchanged. The 70-test
figure above describes the pass-2 checkpoint.

## Candidate and independent authority

The [decision](../../../planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md)
and [class map](../../../planning-artifacts/architecture/architecture-mcpcli-2026-09-22/AD-23-capability-class-map.json)
are the exact candidate identified by [approval.json](approval.json). The
decision's normative JSON policy independently fixes the expected inventory
set, every operation row-to-class assignment, inventory approval-limit text,
sole class outcomes and deferral owners, required restrictions, eligible
non-operation records and their governing policy, and required approval roles.
The map hashes that decision. Actual row identities come from source tables;
neither names nor counts are policy in verifier code.

Map-owned restriction evidence is supplementary. Deleting it cannot remove the
decision-required PS14 or Parties C03/C04/C05 restrictions. An operation cannot
become a bookkeeping record; eligibility and governing policy come from the
decision. Resolved repository paths establish identity before duplicate checks.
The original Admin eight-class names/partition, seven admission facets, Folders
evidence/boundaries, named deferrals and Admin G4 preconditions are retained.
The audit facet now permits authorized Query content in public results while
excluding secrets and unauthorized content; diagnostics, stderr and retained
evidence stay free of content. [Preservation evidence](preservation-checks.json)
records durable before/after section hashes, the intentional audit-row change,
and the exact extraction/comparison command. Its archive source is explicitly
an unapproved candidate, never approval evidence.

Effective adoption comes **only from the separate receipt**. Decision/map bytes
remain immutable through approval, including the decision's proposed-candidate
frontmatter. A receipt must bind both artifacts and all inputs, name a nonblank
approver and exact instruction, and provide an array of nonblank roles covering
the decision's required roles. A nonempty array of nonblank required roles is
validated for pending candidates too. Receipt-owned required-role fields cannot waive
that coverage. This proves documentary consistency, not a human signature's
authenticity or semantic parity.

The current receipt records the user's verbatim **"approve"** response on
2026-11-12 to the final request to approve this exact candidate and confirm all
listed owner roles. It names all twelve decision-bound roles and retains the
existing approver identity, Jérôme Piquot (GitHub jpiquot), with a hash-bound
source reference. The earlier **"approve and stop"** covered only specification
intent and D1–D8; the new response supplies the candidate adoption approval.
It does not grant the explicitly separate AI.Tools push approval.

## Complete source partition and approval limits

**Approval-time wording retained for provenance; corrected 2026-11-15 above:**

> All **625** source table identities are accounted for: **472 classified rows**
> and **153 explicit records**. The approximate problem-size estimate in the
> spec does not replace the actual source identity set.

Cross-reference tables do not duplicate identities; `Gate`, `Gap` and `ID / legacy rows` headers are
recognized. Folders C/Q roadmap candidates remain records, not legacy operations.

| Inventory | Version | Classified | Records | Total | Approval limit preserved |
| --- | --- | ---: | ---: | ---: | --- |
| EventStore Admin | 1.0.1 | 71 | 20 | 91 | Owning-maintainer approval |
| technical-tools | 1.0.2 | 28 | 40 | 68 | Owning-maintainer approval |
| Folders | 1.0.0 | 103 | 58 | 161 | Session approval; no named Folders maintainer |
| Projects | 1.0.0 | 46 | 6 | 52 | Session scope only |
| FrontComposer | 1.0.0 | 26 | 4 | 30 | Session scope only |
| ChatBot | 1.0.0 | 39 | 9 | 48 | Session scope only |
| Memories | 1.0.0 | 39 | 12 | 51 | Session scope only |
| Parties | 1.2.0 | 20 | 4 | 24 | Owner-approved on 2026-11-09; C05 oracle amendment only |

The existing [Parties amendment receipt](../story-5-3/approval/amendment-1.2.0.json)
is approved and binds exactly the current inventory hash. It corrects only
the C05 pre-read oracles/selected SDK and Gateway conditions, preserves 1.1.0
and its receipt, and grants no execution, parity, publication or retirement
authority. This packet preserves it byte for byte. It does not resolve the
separate destructive-label/enrollment conflict.

## Executed verification (2026-11-12 historical checkpoint)

The commands, 45-test count and original scan receipts in this section describe
the completed adoption checkpoint. The 2026-11-15 review-pass-1 packet linked
above contains the current verification; original captures remain unchanged.

The review corrections added **eight regressions**, bringing the suite to
**45 tests**. The implementation subagent first ran the **14 directly affected
process tests**; their [exact command](review-patch-tests-command.txt), empty
[stdout](review-patch-tests.stdout.txt) and [stderr](review-patch-tests.stderr.txt)
are retained. The parent then independently ran the complete **45-test suite**,
the standalone verifier and both Git checks against this final candidate. All
passed. The current full-suite stdout/stderr and boundary checks below are
refreshed; they are not the earlier pre-correction results. Commands are shown
repository-relative; the parent invoked the evidence paths absolutely from the
repository root, with `-B` to suppress generated bytecode.

The focused run covers AC13-to-K14 and Folders V04-to-K01 row swaps; Folders
C01 record class and technical PS09 governing-reference changes; a false
session-to-owner approval claim; pending role policy absence/type/blank values;
Effect-only and Confirmation-only restrictions; and directly affected success,
restriction, role-coverage and receipt-only adoption paths.

| Command | Result and retained output |
| --- | --- |
| `python3 -I -B _bmad-output/implementation-artifacts/evidence/story-5-2/verify_class_map.py` | Exit 0; all eight input counts and effective status `adopted`; [stdout](verifier.stdout.txt), empty [stderr](verifier.stderr.txt) |
| `python3 -I -B -m unittest discover -v -s _bmad-output/implementation-artifacts/evidence/story-5-2 -p 'test_*.py'` | Exit 0; all **45 tests passed**; empty [stdout](tests.stdout.txt), [unittest stderr](tests.stderr.txt) |
| `git diff --stat f4bb819925d4fac5fa5afd262341692296a52042 -- src tests tools references .github _bmad-output/implementation-artifacts/*-migration-inventory-v1.md` | Exit 0; empty [stdout](scope-diff.stdout.txt); [stderr](scope-diff.stderr.txt) contains only the existing missing commit-graph warnings; all forbidden tracked paths and inventory bytes unchanged |
| `git diff --check` | Exit 0; no whitespace errors; [output](diff-check.txt) contains only the existing missing commit-graph warnings |
| `python3 scripts/scan-evidence-secrets.py _bmad-output/implementation-artifacts/evidence/story-5-2 --receipt _bmad-output/implementation-artifacts/evidence/story-5-2/secret-scan.json` | Exit 0; the refreshed [scan receipt](secret-scan.json) binds the final packet with zero findings/errors. The [pre-review scan receipt](secret-scan-pre-review.json) is historical evidence only |

Git emitted `warning: unable to find all commit-graph files` twice for each
recorded Git check. Both commands still exited 0; the scope diff was empty and
no whitespace error was reported. This existing repository metadata warning
does not affect the verifier or change the inventory/forbidden-path result.

The McpCli implementation baseline is
`f4bb819925d4fac5fa5afd262341692296a52042`; the current work began at
`a770893195b6c89ced0cfb0d06faca74ff6ec695`. Pre-existing spec/sprint edits were
preserved. The frozen intent block is unchanged. Only planning artifacts,
Story 5.2 evidence/verifier/tests, the spec, sprint state and deferred-work
record changed. No .NET
build, legacy command, domain operation, service or live host was needed for
this documentary change. Task-owned Python bytecode caches were removed before
the text-only evidence scan.

All damaged-input checks run the **actual script process**. Each failure must
exit 1, produce empty stdout, and begin stderr with `FAIL: `. Success must exit
0 with empty stderr. Removing `sys.exit(main())` breaks those assertions.
The complete eight-inventory packet also has direct reproduced-attack tests,
in addition to synthetic inventories that exercise generic parser behavior.

| Requirement / reproduced attack | Executed regressions |
| --- | --- |
| Complete map | `test_complete_partition_prints_inventory_counts`, `test_actual_packet_complete` |
| Missing/duplicate/unknown row | `test_missing_row_names_inventory_and_id`, `test_duplicate_row_and_cross_section_duplicate_are_rejected`, `test_unknown_row_names_inventory_and_id` |
| Stale source/version/decision hash | `test_stale_inventory_hash_is_rejected`, `test_stale_version_and_decision_hash_are_rejected` |
| Zero/two/unlisted outcome; outcome/decision disagreement | `test_zero_two_and_unlisted_outcomes_are_rejected`, `test_outcome_and_required_class_set_must_match_decision`, `test_actual_k09_cannot_disagree_with_deferred_decision` |
| Restricted admission, including deleted PS14 evidence and Parties mixed variants | `test_restricted_source_classes_and_variant_evidence_block_admission`, `test_inherited_restriction_survives_deleted_map_owned_evidence`, `test_actual_ps14_cannot_be_admitted_after_removing_all_map_restrictions`, `test_actual_parties_mixed_variants_inherit_restrictions` |
| Deferral without gap/role or changed ownership | `test_deferred_class_needs_nonblank_gap_and_owner_role`, `test_changed_deferral_owner_or_gap_disagrees_with_decision` |
| Whole missing inventory | `test_whole_inventory_omission_and_extra_inventory_are_rejected`, `test_actual_whole_technical_inventory_omission_is_rejected` |
| Operation-to-record laundering; changed record governance | `test_unrestricted_operation_cannot_be_laundered_as_record`, `test_restricted_operation_cannot_be_laundered_as_record`, `test_actual_parties_t01_cannot_become_record`, `test_record_requires_reason_and_decision_governing_policy` |
| Aliased paths | `test_inventory_aliases_are_detected_after_normalization`, `test_actual_technical_path_alias_cannot_double_count` |
| Owner/instruction/role types, whitespace and omissions | `test_approval_requires_nonblank_typed_owner_and_instruction`, `test_approval_requires_array_of_nonblank_roles_and_all_bound_roles` |
| Exact receipt and immutable adoption | `test_receipt_artifact_binding_is_required_for_pending_and_adopted`, `test_effective_adoption_changes_only_receipt`, `test_actual_receipt_drives_adoption_without_mutating_candidate`, `test_map_cannot_declare_its_own_adoption_status` |

ChatBot V10 now maps to K04 for primary operation/task identity and context
handoff, preserving authenticated tenant/operation authority, authoritative
retry-progress status and post-commit audit Query evidence. D2/K08 continues to
withdraw the legacy synthetic observation engine, polling and subscriptions.
The decision links the existing [Parties reconciliation ledger entry](../../deferred-work.md#deferred-from-review-of-spec-5-2-decide-generic-non-gateway-capability-contractsmd-2026-11-12),
with its existing owners and acceptance gate; this patch does not resolve it.

The remaining tests cover duplicate JSON/source/class declarations, unknown
classes, source excerpt validity, record-to-operation conversion, unresolved
governing references and escaping paths. Adoption tests use only temporary
fixture copies and explicitly synthetic approval words, never this receipt.

## Retained upstream amendment

**Point-in-time implementation record (before the separate push and merge;
superseded by Main integration below):**

The AI.Tools amendment remains the existing local commit
`10b709b86f9c9148e5a18177e8d11fad79ae2c0b` on
`docs/mcpcli-local-tooling-exemptions`, in
`/home/administrator/projects/hexalith/.scratchpad/story-5-2/aitools`.
This iteration read its clean status, exact commit and three file hashes,
matching [upstream-candidate.json](upstream-candidate.json). It did not
recommit or push. The retained [commitlint result](aitools-commitlint.txt)
records the successful pinned validation before the original commit.

The [amendment diff](upstream-amendment.diff), normalized to LF with zero
context lines for review,
updates the ownership rule, migration plan to 1.2.0, and README plan link. The
actual file hashes bind original bytes, including the CRLF instruction file.
It exempts FrontComposer inspect/migrate and owner-held Memories
MigrateEmbeddingVectors dry-run/live/rollback/abort, while preserving inventory
revision, approval/disposition limits and all census bytes. Story 5.10 still
owes the PS14 mode inventory. The original `npm ci --ignore-scripts` and pinned
commitlint checks succeeded; their evidence is retained rather than repeated.

**The approved amendment is merged to AI.Tools main.** The
user replied **"approve"** after the separate AI.Tools push was identified as
pending. [Delivery evidence](upstream-delivery.json) and the [push output](upstream-push.txt)
record publication of the exact candidate on `docs/mcpcli-local-tooling-exemptions`.
The amendment merged by fast-forward under the subsequent explicit main-integration request; the census baseline itself is unchanged. Retained local tools are
never counted as retired. No root gitlink, reference checkout, census baseline
or inventory was changed.

Boundary inputs remain Platform `38402bc77ac0be3e6902002d08923c51d0e73a77`,
Folders `6a8cf4f9e28786176d26522b41bb921e18b922da`, and AI.Tools candidate base
`8a3885dd22aea88edd57771cfe592c382df2c583`.

## Exact-byte owner adoption and remaining limits

The receipt's `artifacts` object lists the SHA-256 of the decision, map and
every input. The candidate hash table below is copied from that binding; no
status/hash refresh tool is part of the handoff. The user approved these
exact candidate bytes and confirmed every role in the decision's
`requiredApprovalRoles` list under the single-maintainer model:

- McpCli product/architecture owner
- McpCli maintainer
- McpCli security and contract/transport maintainer
- Platform architecture/security and platform/operator maintainer
- EventStore owning maintainer
- FrontComposer owning maintainer
- Projects owning maintainer
- Folders owning maintainer
- ChatBot owning maintainer
- Memories owning maintainer
- Parties owning maintainer
- AI.Tools owning maintainer

The user's exact response **"approve"** is recorded separately from the
presented request in `approval.json`. The receipt decision is `approved`, its
artifact bindings are unchanged, and the verifier reports effective status
`adopted`. Only the separate receipt, this verification narrative and the
unbound spine/workflow state changed for adoption. The decision/map retain the
exact approved bytes. Any later change to those artifacts is a new candidate
requiring fresh approval; no automatic status/hash refresh is permitted.

The user separately approved publishing the exact upstream commit, and the
branch push succeeded with matching remote read-back. This satisfies the
specification's explicit push approval gate. At that branch-delivery checkpoint no merge, reference update or census amendment
was performed. The later explicit main-integration request and successful merge
are recorded below; reference and census bytes remain unchanged.

Parties L03–L05, T04/T05/T07 and C03/C04/C05 are restricted here, although the
Commands are already decorated/enrolled. This is a disclosed conflict requiring
a separately owner-approved inventory/exposure reconciliation, not permission
for runtime removal or a claim of current discovery/submission compliance.
Folders C10 combines add/change with destructive removal and stays restricted
as a whole; upstream must separate an agent-eligible declaration. Folders
V04/V05 remain deferred and EXT-MCPCLI-FOLDERS-RETIREMENT-GATE stays closed.
All later exact-type, authorization, live behavior, release/rollback and
retirement gates remain. No draft decision authorizes downstream dispositions.

<!-- candidate-hash-table -->

| Artifact / input | SHA-256 |
| --- | --- |
| `AD-23-non-gateway-capability-classes.md` | `f47b64c7772ed9d9763e4438a176cb7bea01e8e0793f7217c6bd1f3274545560` |
| `AD-23-capability-class-map.json` | `21cb3643ef3e652031bf13f02e237b2cfadb2be24bcbf2d02e879a584ac8a4c3` |
| `eventstore-admin-migration-inventory-v1.md` | `7e1beb2fd2c030ca04dbc8d718c0324c7f7f5b66a077f6ef672312d6196fec18` |
| `technical-tools-migration-inventory-v1.md` | `8cca31f2a9fb646566a2cdba3a377af58685d99e4a53ec8e9243135613c1a2f6` |
| `folders-migration-inventory-v1.md` | `57cf556b8051921bf2bf8a17abe3b82b7d0a3ba8ba5593072f52c12f85650e0b` |
| `projects-migration-inventory-v1.md` | `252af571ee3b52163a2f0637a1dff4f0c6f2802ebfa985c51562466fa759ad5f` |
| `frontcomposer-migration-inventory-v1.md` | `cde0f43ae82376c37411017e88a3b692d0980622833310fecb29f040eb1281a9` |
| `chatbot-migration-inventory-v1.md` | `3dccbe0fb56fe1facb05156d2648d0696d87dfd3a60fe25aacf4969b899ecd94` |
| `memories-migration-inventory-v1.md` | `489af91ed49804172e8bd32f3efd98cf1d78fc8a109f23675c67b5ac23f19597` |
| `parties-migration-inventory-v1.md` | `2f359904fe87fab8325b6fc759676c1fc792a27e0857d47631d8eeec8b420a28` |


## Adoption finalization (2026-11-12)

After the user replied **"approve"**, the parent verified all ten presented
artifact/input hashes before recording the response and every required role.
The approved decision/map and frozen specification block remain byte-identical.
The standalone verifier now reports effective status **adopted**. The complete
**45-test suite** passed again against the approved receipt; current stdout and
stderr above record that run. The architecture spine records ADOPTED, the spec
is done, and the sprint story is review, as the build workflow requires.

The owning repository's pinned commit tooling was restored with `npm ci`
(exit 0, lockfile unchanged). The exact full local completion message passed
`npx --no -- commitlint --verbose` with zero problems/warnings before commit;
[validation output](commitlint-validation.txt), [exact message](commit-message.txt)
and [command record](commitlint-command.json) are retained. The completion
commit contains only the Story 5.2 decision/map, evidence, spec, sprint/spine and
previously reviewed deferred-work entry. Root-declared reference checkouts were
clean, had no commits ahead of their tracked upstream, and their revisions were
contained in cached remote branches; no reference or gitlink change is recorded.

At the adoption checkpoint the AI.Tools amendment was local and unpushed;
that first approval adopted AD-23 only. The later separately approved branch
push is recorded below. Neither approval grants a merge, unfreezes the census
surfaces, resolves Parties' exposure conflict, or closes the Folders staging
and later retirement evidence gates.

The [pre-adoption scan](secret-scan-before-adoption.json) is retained as
historical evidence. The current `secret-scan.json` is a fresh receipt for the
approved packet; the scanner correctly refuses to overwrite existing receipts.


## Separately approved upstream delivery (2026-11-12)

**Point-in-time branch-push checkpoint.** The pending-merge and frozen-surface
statements in this section describe that checkpoint; Main integration below
supersedes them.

The user replied **"approve"** directly after the completed AD-23 adoption
summary identified the AI.Tools push as the remaining separate approval.
The exact candidate was rechecked against its full commit and three file
hashes, then `git fetch --no-recurse-submodules origin main` confirmed that
`origin/main` remained `8a3885dd22aea88edd57771cfe592c382df2c583` and the candidate
was ahead one commit with no divergence. The branch did not previously exist
on the remote.

`git push --set-upstream origin HEAD:refs/heads/docs/mcpcli-local-tooling-exemptions`
succeeded. `git ls-remote --heads origin refs/heads/docs/mcpcli-local-tooling-exemptions`
returned the exact candidate **`10b709b86f9c9148e5a18177e8d11fad79ae2c0b`**.
The [published branch](https://github.com/Hexalith/Hexalith.AI.Tools/tree/docs/mcpcli-local-tooling-exemptions),
[delivery record](upstream-delivery.json) and [readable output](upstream-push.txt)
identify that result. The source worktree remains clean. No force push,
`main` update, merge, PR, reference gitlink change, census amendment or domain
operation ran. AD-23's approved decision/map and all input inventory bytes
remain unchanged; the standalone verifier still reports effective `adopted`.

The shared secret scan is refreshed for these delivery records. The prior
[post-adoption scan](secret-scan-before-upstream-push.json) is historical;
`secret-scan.json` binds the current packet. Merge remains pending and exempt
surfaces remain frozen. This delivery-record update is committed locally in
McpCli; its branch is not pushed by the AI.Tools push approval.


GitHub's captured push output contains trailing spaces. The readable
`upstream-push.txt` strips those spaces; [upstream-push.raw.json](upstream-push.raw.json)
preserves the exact original output as a JSON string and records its SHA-256.
The delivery record binds both representations. The
[scan before output formatting](secret-scan-before-output-formatting.json)
is historical; the current scan includes the corrected evidence layout.


## Main integration (2026-11-12)

The user explicitly requested **"merge all changes to main"**, authorizing
integration of the prepared AI.Tools amendment and McpCli story commits.
Both remote main branches were fetched without recursive submodule updates.
Both were unprotected with no required status contexts. AI.Tools' candidate
had no check runs; its existing pinned commitlint validation and approved file
hashes remained valid. All 17 root-declared reference checkouts were clean and
had no unpublished branch commits. McpCli main was two commits ahead of its
remote with no divergence.

AI.Tools' clean main worktree fast-forwarded from
`8a3885dd22aea88edd57771cfe592c382df2c583` to the exact approved commit
`10b709b86f9c9148e5a18177e8d11fad79ae2c0b`, then `git push origin main`
succeeded. A fresh remote read-back confirms that exact main revision. The
[main integration record](main-integration.json) retains the verbatim request,
method and command outputs. No merge commit, rebase, force push or protection
bypass was needed. The upstream amendment's merge gate is satisfied.

McpCli's reviewed story, approval, delivery and integration records are
published together from its local main. This metadata update retains every
approved decision/map/input hash and does not alter the census baseline,
reference gitlinks, inventories or runtime. Any later census reclassification
still needs its separate versioned owner approval. Parties reconciliation,
Folders staging and later enrollment/retirement evidence remain open.


Final main-integration verification reran all **45 process tests** against the
merged upstream metadata; all passed. The local integration-record message
passed pinned commitlint with zero problems/warnings; its [exact message](main-commit-message.txt),
[validation](main-commitlint-validation.txt) and [command](main-commitlint-command.json)
are retained. The [scan before main integration](secret-scan-before-main-integration.json)
is historical; the current scan binds the main-integration packet.

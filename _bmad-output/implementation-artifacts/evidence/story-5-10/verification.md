# Story 5.10 verification — owner-approved documentary successors

Prepared 2026-11-16 at McpCli HEAD `e2e3db7ba2d45d61feacc39c41b3051310fbc57f`,
using approved baseline `979e1e126c6d7010997f4f20b2bb3defae81333e`.
The user approved both exact inventories and all ten named roles on 2026-11-16.
Separate delivery authorization is recorded in delivery-authorization.json.
The McpCli packet was published in `e2e3db7` and `008d95c`, both ancestors of
locally observed origin/main `119a4b59e5e1391ff8ddb4587e1608ad1d1e5145`.
PS06/PS07/PS12/PS13/PS14 upstream label integration remains pending.
No operation was enrolled, executed, accepted as parity or retired, and this
patch session changes no upstream checkout.

## Exact candidate scope

| Module | Successor | Entries | Replace/include | Withdraw/exclude | Defer/exclude |
| --- | --- | --- | --- | --- | --- |
| ChatBot | 1.1.0 | 48 (M12/L12/V15/X4/G5) | 0 | 5 | 43 |
| Memories | 1.1.0 | 55 (M4/L14/S4/V17/X6/G6/T4) | 0 | 20 | 35 |

- [ChatBot 1.1.0](../../chatbot-migration-inventory-v1.1.0.md): SHA-256 `3d801aed7bd80a9a6f3ec225a694ed1aa9e9a9ce7fa263745d90184af5ced49c`.
- [Memories 1.1.0](../../memories-migration-inventory-v1.1.0.md): SHA-256 `fc3baee0f766f95db32df5fd226825b144927c2ad1bc60f867341d32b517bca1`.
- [Owner approval](approval.json) binds predecessor/successor bytes, all
  predecessor row deltas, the four added PS14 rows, immutable authorities and
  every source artifact used to derive anchors. It names ten required roles
  under the single-maintainer model. The user's exact `approve` instruction
  covers those roles and supersedes each module's A1 for these successors.
  The receipt determines effective approval status; the approved inventory bytes
  retain their original proposal headings.
- [Prepared label register](labels.json) chains to Story 5.9 and binds prior
  PS06/PS07/PS12/PS13/PS14 rows from Story 5.7. The two README-only patches include
  ordinary context lines, apply with standard `git apply --check`, and cite
  these successors and their hashes. PS06/PS07/PS12/PS13 retain their removal
  gates. PS14 changes only its fulfilled four-mode inventory obligation while
  retaining every independent tenant/credential/custody, consent, no-write
  dry-run, denial, rollback/abort and audit evidence gate. Delivery is authorized
  and remains unintegrated. The historical check.py refusal below no longer
  applies to this repository; its existing required CI gates govern delivery.

## Source observations

`git fetch` succeeded. Fetched McpCli `origin/main`
`979e1e126c6d7010997f4f20b2bb3defae81333e` is an ancestor of HEAD; both
HEAD gitlinks equal the approval pins. Regeneration halts when current HEAD
gitlinks move or local HEAD lacks origin/main. Verification retains the immutable
BASELINE gitlink and pin-ancestry checks, so later HEAD changes do not invalidate
the approved packet. Only immutable `git show <pin>:<path>` module source
supplies row evidence; no source checkout or nested submodule is updated.

| Module | Approval-time source pin | Locally observed owner origin/main | Ancestry check |
| --- | --- | --- | --- |
| ChatBot | `6a4ca07b18e9b58500dc79dfede1f308da36c828` | `6a4ca07b18e9b58500dc79dfede1f308da36c828` | exit 0 |
| Memories | `9d87500eaf4c39ce0cec0cb3a03e5dd62c167106` | `e4b2b08edacf1d10337258ffb6949711cc5987ca` | exit 0 |

These observations use local owner refs; they do not imply a new upstream fetch
or any delivery. ChatBot's historical unpublished source pin is
`acc934599cf1efff36b0643eddc6a3cc4c2978d5`. Its `src` tree and published
comparison `839aee31e2a9be11feab3fb726006bb4c2f890b5` both resolve to
`59158fccb3a2819816a2e13a39095b238bdf1c9b`. The only file difference is
`M .mcp.json`, correcting the spec's non-authoritative source-map statement
that it was deleted; frozen intent is unchanged.

Static source checks confirm ChatBot's 12 tool declarations and unchanged CLI
leaves, Memories' four registrations, unchanged tool/command directories and
unchanged PS14 Program/service/exit-code files. Both Contracts projects remain
unchanged and no decorated type exists. Source alignment refreshes all row
anchors; drift records formatter handles, OpenAPI restrictions, admission,
JWT algorithm enforcement, ingestion fences, publication-change errors,
workload authority, new adjacent client methods and output/error catalogs.

ChatBot V10's formatter fix is recorded as drift while its decorated status
Query remains absent; acceptance is never completion. Governed provider and
pre-submit work stays module-side; task/correlation context uses only Payload,
declared actorProperty or allowed Command Envelope extensions. Queries gain
no extension channel, and plain Commands/REST DTOs/OpenAPI prove no readiness.

The final source descriptions additionally record ChatBot's current nonretryable
503 refusal before canonical write dispatch, its scheme-bound human authentication
and denying unconfigured JWT authentication setup, and canonical status retry/metadata rules.
Status/audit OpenAPI anchors identify the exact operations and CommandId schemas;
transition evidence checks the actorId field's absence in its specific schema.

Every deferred Memories row retains tenant/user authorization, administrative
scope, semantic behavior and release/rollback gates. M01–M04 and V01–V03
explicitly retain the HTTP release with forwarded per-user identity as
necessary but insufficient; all other deferrals retain G2. L01/L13 remain
unscoped deployment metadata without a checked admin-role claim.

Memories additionally records generation-qualified versus historical identifiers,
managed-source visibility and graph publication filters, deterministic score/key
raw windows, hydration/completeness refusal and raw paging positions. Gateway
composition distinguishes the fixed-domain package fallback from the multi-domain
exact command/principal-proof branch, without implying uniform build authority.

T01–T04 separately inventory dry-run/live/rollback/abort effects, security,
tenant rules, consent/non-interactive refusal, direct Redis and Dapr access,
exit codes and absent authenticated user/tenant authority. Tool resources
connect before service option validation; refusal is not zero-connection
proof. The named AI.Tools plan 1.2.0 exemption is hash-bound from its approved
root gitlink. These modes remain owner-held local tooling, never retired;
`--yes` grants no agent authority. No mode was executed.
T02 distinguishes failures before cutover from failures after alias cutover but
before embedding-configuration persistence or marker completion; the latter can
leave new aliases active and need manual rollback/follow-up. Its evidence includes
the exact Redis store as well as the migration service.

## Preparation verification commands and limits

[checks.json](checks.json) retains exact command arguments, exit codes and both
streams. Tests use private scratch space supplied by `run-with-temp`; every
fixture also has reliable `TemporaryDirectory` cleanup. The final suite uses `-B`
to prevent discovery bytecode. The earlier task-owned bytecode cache was removed
after all child checks exited, before the final evidence scan.

| Command | Result |
| --- | --- |
| `python3 -I .../story-5-10/build_candidate.py` | exit 0; deterministic pending packet |
| `python3 -I .../story-5-10/verify_amendment.py` | exit 0; 48 + 55 entries, class/anchor/drift/approval chains |
| `python3 -I .../story-5-10/verify_labels.py` | exit 0; five labels, two isolated README-only patches |
| `python3 -I .../story-5-10/verify_amendment.py --approved-completion` | expected exit 1; empty stdout and exact stderr `FAIL: completion requires exact-byte owner approval and covered roles` |
| `python3 -I .../story-5-10/verify_labels.py --approved-completion` | expected exit 1; empty stdout and the same exact approval refusal |
| `run-with-temp python3 -I -B -m unittest discover -v -s .../story-5-10 -p 'test_*.py'` | exit 0; all 26 tests pass after review corrections |
| `python3 -I .../story-5-2/verify_class_map.py` | exit 0; AD-23 remains adopted |
| `git diff --check` | exit 0 |
| `python3 -B scripts/scan-evidence-secrets.py .../story-5-10 --receipt .../story-5-10/secret-scan.json` | exit 0; [scan receipt](secret-scan.json) binds final packet files |

Recorded preparation unittest result (superseded by the review-patch run below):

```text
Ran 26 tests in 105.974s

OK
```

Matrix-to-test mapping (all tests are in `test_verify_amendment.py`):

| Spec matrix scenario | Test methods |
| --- | --- |
| Complete candidates; approval stays pending | `test_real_candidate_commands_have_exact_success_streams_and_completion_refusal`, `test_generator_is_deterministic_and_pending` |
| Invented replace/include or plain Command/REST/OpenAPI readiness | `test_replace_include_and_plain_command_rest_openapi_readiness_are_rejected` |
| Class drift; missing loss/gap/owner | `test_class_drift_missing_loss_gap_owner_drift_and_ui_gate`, `test_context_k05_status_and_admin_scope_guards` |
| Missing/duplicate IDs, damaged anchors or drift, incomplete PS14 fields, omitted identity prerequisite | `test_missing_duplicate_and_added_rows_include_governance_and_stubs`, `test_anchor_identity_unresolvable_and_prose_checks`, `test_every_ps14_mode_field_and_noninteractive_rule`, `test_every_identity_dependent_row_and_other_deferred_rows_retain_http_and_g2` |
| Completion without exact approval or any required label | `test_completion_from_flag_spec_sprint_and_integrated_label_requires_approval`, `test_receipt_bindings_roles_exact_words_and_pending_claims`, `test_label_chain_rows_hash_path_and_readme_only_patch` |
| Removal of a required guard | `test_guard_removal_controls_detect_missing_accounting_row_anchor_approval_and_delivery_guards` |
| Independent approval/delivery, on-main README-only integration and current upstream citations | `test_approved_authorized_completion_exercises_actual_delivery_checks`, `test_delivery_rejects_missing_authorization_stale_origin_non_readme_and_off_main`, `test_readme_only_patches_apply_to_pinned_bytes_exactly`, `test_delivery_readme_and_inventory_ancestry_guards_have_entrypoint_removal_controls` |
| Corrected source facts and specific OpenAPI statements | `test_corrected_source_facts_and_specific_openapi_semantics_are_retained` |
| Real approval transition and safe regeneration refusal | `test_approved_undelivered_candidate_is_valid_but_generation_and_completion_refuse`, `test_approval_after_first_successor_write_is_preserved_and_later_writes_stop`, `test_unchanged_pending_destinations_are_not_rewritten` |
| Each published successor/approval mismatch at both publication points | `test_each_published_inventory_and_approval_copy_is_required_with_exact_streams`, `test_guard_removal_of_published_byte_comparisons_is_detected` |
| Later HEAD/gitlink/main changes; immutable baseline and published pins | `test_current_gitlink_moves_and_local_main_lag_affect_regeneration_only`, `test_baseline_gitlinks_and_published_pin_ancestry_remain_required` |

The tests assert exit code, empty failure stdout and exact actionable stderr for
damaged accounting, invented readiness, class drift, missing loss/gap/owner,
anchors, PS14 fields, identity prerequisites and premature completion. They
also prove both README patches apply to the pinned bytes exactly, independently
exercise approval roles and each required label, synthetic approved/authorized
completion, current origin/main readback, README-only delivery, on-main ancestry,
hash/delta changes, JSON duplicates, symlinks and approval-race refusal. The
review patch replaces the original function-stub controls with removal of actual
accounting, row, anchor, approval and delivery source statements through the
verifier entrypoints. Each exact diagnostic assertion fails after removal;
later redundant guards may still refuse for another reason. Integrated README
bytes and inventory ancestry have separate source-removal controls through both
entrypoints. Synthetic approval/delivery fixtures never modify real receipts
or upstream repositories.

All three build review layers completed before triage. The spec records all 14
findings separately, grouped into 12 narrow corrections; all were fixed and none
were deferred. The final 26-test run supersedes earlier pre-review runs. Removing
the actual publication-byte comparison loop now makes its exact-stream negative
control fail. All six publication mismatch combinations are exercised, and test
fixtures explicitly isolate pending receipts from legitimate real approval state.
The generator skips unchanged files and rechecks receipt snapshots immediately
before mutations; the injected first-successor-write approval is preserved and
later writes stop. This is not an atomicity guarantee against arbitrary concurrent
external writers; approval and generation must remain separate operator actions.

The [pre-review scan](secret-scan-before-review.json) is preserved unchanged.
Final scan setup corrections are retained in checks.json: `-I` prevents the
scanner's sibling-module import, and an existing receipt destination is refused.
The final scan uses ordinary script execution and a new destination, preserving
the earlier receipt and binding all final evidence bytes.
The first complete final scan matched a descriptive authentication-scheme phrase
in this prose. It is preserved in [the prose-check receipt](secret-scan-prose-check.json);
the wording was corrected without changing the shared redaction policy.

The review patch returns the spec and sprint state to implementation while its
local checks run. Exact-byte approval, all covered roles and separate delivery
authorization are recorded. The published McpCli commits above do not establish
upstream label integration or a done state. Current required CI is red, as
recorded in the review-patch state correction below.

## Owner approval transition — 2026-11-16

The user replied exactly `approve` to the final request to accept both inventory
files and explicitly cover the ten roles in approval.json. The receipt records
the instruction, its conversation source, date and each covered role. The two
inventory hashes above, all label/README patch bytes, predecessor inputs and
authority bindings remain unchanged. Only the receipt's decision and explicit
approval metadata changed; immutable inventory headings are governed by that receipt.

The earlier checks and scan receipts remain unchanged as pre-approval evidence.
[Approval-state checks](approval-checks.json) retain the current verification,
and [the approval-state secret scan](secret-scan-after-owner-approval.json)
binds the updated packet. Both completion entrypoints must now refuse with
`FAIL: completion requires integrated PS06/PS07/PS12/PS13/PS14 labels`.
No delivery authorization, commit, push or upstream integration is inferred
from the owner's approval. The five exact label changes remain prepared for
separately authorized delivery.

The approved-state run passed all 26 tests in 105.872 seconds, both default
verifiers, unchanged adopted AD-23 and the whitespace check. Both completion
entrypoints returned exit 1, empty stdout and the exact label-integration refusal
above. The real generator refused with `FAIL: refusing to overwrite approved or
unknown-state packet`, preserving every inventory, receipt, label and patch byte.
The recorded packet snapshot remained unchanged across all verification commands.

Read-only delivery preparation in approval-checks.json confirms both patches
apply to isolated README copies from locally observed owner origin/main and
produce the exact prepared after hashes. ChatBot's owner checkout has unrelated
local commits and nested changes; its current local README differs from the
prepared base, so delivery must use an isolated checkout of fetched origin/main.
Memories also has unrelated local planning work, which stays outside delivery.
These checks did not fetch or write to either owner repository. Fresh refs must
be checked again after separate delivery authorization.

## Historical check.py refusal — 2026-11-16; superseded by adoption guidance

The user replied exactly `authorize` to committing and pushing the approved
McpCli packet and both prepared upstream README-only updates.
[Delivery authorization](delivery-authorization.json) binds that instruction to
the approved receipt, both inventory hashes and the two exact patch hashes.
Authorization persists; it has not been consumed or withdrawn.

Fresh fetches confirmed McpCli origin/main at
`e2e3db7ba2d45d61feacc39c41b3051310fbc57f`, ChatBot origin/main at
`6a4ca07b18e9b58500dc79dfede1f308da36c828`, and Memories origin/main at
`898f451111740ccf489d56f7c20cd47edc2fcdf6`. Both approval-time root gitlinks
remain unchanged. No owner working files or branches were changed.

The shared guidance used at that attempt required a successful
`python3 references/Hexalith.Builds/check.py` from the module root before every
push and assigned CI configuration ownership to Hexalith.CiCd. The command
was run in a clean temporary clone of the exact McpCli HEAD, with its exact
direct Builds pin `65fd22f37b9fad64b595841923cdbe050563ab99`, beneath
`run-with-temp`. It returned exit 1 with empty stdout because the committed
module contains no `.github/hexalith-ci.json`:

```text
.github/hexalith-ci.json: [Errno 2] No such file or directory
```

[The exact gate receipt](delivery-gate.json) retains the complete command,
temporary working path, both streams, source revision and preparation commands.
The clone and its child processes finished before scratch cleanup. This is a
reported configuration failure, separate from the passing 26-test story suite
at that time. No check was weakened or bypassed during that attempt. The old
claim that the packet had never been committed or pushed is superseded by the
published `e2e3db7` and `008d95c` history.

AI.Tools `cfd1ebea92587cdea41b9aa2cff47358bf2f32f6` now requires that checker
only after a module adopts CiCd through a committed `.github/hexalith-ci.json`.
McpCli has no such file, so its existing required CI gates apply; adding the
configuration is not a Story 5.10 delivery prerequisite. The approved
inventories and receipt, prepared labels and patches, historical verification
evidence and root reference checkouts remain unchanged.
The [delivery-blocker secret scan](secret-scan-authorized-delivery-blocker.json)
binds the authorization and blocker evidence; the earlier scan receipts remain
immutable. Delivery remains authorized and the story remains in review.

## Review-patch state correction — 2026-11-16

Both `e2e3db7ba2d45d61feacc39c41b3051310fbc57f` and
`008d95ccc77d932a372cb6c749d9d1fb1bc1ea57` are on McpCli origin/main.
The latter publishes the owner approval and separate delivery authorization;
the authorization-bound inventory and README patch bytes remain unchanged.
No upstream label integration is recorded in labels.json, and both completion
entrypoints therefore still refuse that missing gate. The default verifiers
now report the approved decision and pending integration without treating
approval or authorization as missing.

The observed CI run for current main `119a4b59e5e1391ff8ddb4587e1608ad1d1e5145`
is [43916598661](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/43916598661),
completed with failure. The same revision's Commitlint, agent-instruction sync
and bootstrap-package runs succeeded. No CI gate was rerun, weakened or bypassed
by this patch session. Story 5.11's technical 1.0.4 candidate already re-cites
both 1.1.0 successors and T01–T04; that indexing work is not missing here.

[State readback](review-patch-state.json) records the published-byte and ancestry
checks, effective approval/authorization/label states and the observed CI runs.
[Review-patch checks](review-patch-checks.json) retain the exact local commands,
results, both streams and unchanged protected-byte snapshots. They cover
regeneration-only current-HEAD checks, baseline/published-pin refusals,
exact integrated-README and inventory-ancestry failures, real source-removal
controls and pending/approved/integrated output states. Earlier evidence and
receipts remain historical records. All 29 tests pass in 148.425 seconds; both
default verifiers and adopted AD-23 pass. Both completion entrypoints return
exit 1, empty stdout and the exact missing-integrated-label refusal, while real
regeneration refuses the approved packet without changing protected bytes.
Whitespace checks pass. The [first review-patch scan](secret-scan-review-patches.json)
found no secrets but refused generated discovery bytecode. That task-owned
ignored cache was removed after the test child completed, with the failed scan
preserved. The final [review-patch secret scan](secret-scan-review-patches-final.json)
uses a new receipt and binds the updated evidence packet.

These are static documentary checks; no .NET/runtime behavior changed and no
live module, Gateway or operator operation ran. No authorization parity,
confidential-UI coverage, release or rollback acceptance follows. Both legacy
heads and owner-held tooling remain retained. Exact approval is recorded;
authorized upstream integration remains required before story completion. The completion verifier also
refuses a `done` spec/sprint state or integrated label claim without them.

Protected predecessors, AD-23, technical 1.0.3, earlier receipts/registers,
production code, enrollment, dependencies, census, gitlinks, AI.Tools plan and
`references/` remain unchanged. The deferred-work ledger records only ChatBot's
partial source-pin resolution and reroutes the two existing technical-successor
entries to Story 5.11, alongside the Admin successor. Story 5.11 indexes these
successors; this story does not write either deferred successor.

## Independent review follow-up — 2026-11-16

All three review layers returned. The new parent-directory symlink regression
test asserts exact failure streams and unchanged repository/external files;
removing the actual ancestor check makes the assertion fail and demonstrates
the redirected README.patch write only inside disposable test directories.
The final full suite passes: 30 tests in 228.029 seconds. Both default
verifiers, adopted AD-23, approved-packet regeneration refusal and whitespace
checks pass. Both completion modes return exit 1 with empty stdout and the
missing-integrated-label diagnostic. Protected hashes remain unchanged.

[Final checks](review-final-checks.json) retain commands, results and both
streams, with the [test log](review-final-tests.stderr.txt). The preceding
attempt exceeded the verification harness's 360-second limit without returning
a test result; the final run retains logs and completed successfully. This
supersedes that process-limit result without weakening a product or story gate.
The [final secret scan](secret-scan-review-complete.json) binds the updated packet.

The review recorded two additional existing approved-byte defects for the next
Memories successor: PS14 dry-run exception/exit guarantees and rollback/abort
partial effects. They are separately tracked in the deferred-work ledger under
this source spec; the eleven earlier approved-byte groups remain open.
Nine findings about the already-committed Story 5.11 packet are individually
recorded in the spec and excluded from this explicitly separate intent.

The spec remains in-review and the sprint remains review. Marking either done
would violate the still-failing integrated-label completion gate. The active
build phase permits no push or remote operations; delivery authorization stays
recorded, and no new approval request is implied. No commit, push, upstream
integration, production change, enrollment, parity acceptance or retirement
occurred in this resumed run.

# Census amendment 1.0.7 — owner re-approval

Approved by the owner and written; see [Approval and outcome](#approval-and-outcome-2026-11-12).
The sections up to it describe the draft as reviewed, when the active chain ended at the waiver
amendment 1.0.6.

## Why

Amendments 1.0.3–1.0.6 record that human validation was bypassed. Their 20 exact-file exclusions
are also bound to source revisions. Every pin move of those repositories therefore fails the census
with `excluded-source-revision-drift` until someone renews it, even when the bytes are unchanged:
13 of the 14 renewals in 1.0.6 were byte-identical.

The owner had approved hash-only versions of these classifications in the owner amendments 1.0.5 and
1.0.6. Neither is in the active chain: the owner 1.0.5 replaced an already-pushed 1.0.5 and was
archived upstream, and the owner 1.0.6 chained to it and was never pushed. Owner decision of
2026-11-12: keep the release chain (option 1), then append an owner 1.0.7 while the release session
is paused.

## What 1.0.7 contains

[build-renewal.py](build-renewal.py) builds the draft at parent `4b19b5362b3cebf5ac97ff3d9e879a0b33543d6e` from the clean
[source-census.json](source-census.json) (policy 1.0.6, SHA-256
`33aa7a3bdeaafd2b79631d1d1c558d4c9172cff28674cb2bf81a4e78ffec21bf`). It re-adds, **byte for byte**,
owner-approved entries that pass all three of these checks:

- their active classification rests only on waiver amendments;
- the classification is unchanged;
- the current bytes are among those the owner approved.

[authorization.draft.json](authorization.draft.json), canonical SHA-256
`e0f1ef0d8885ba528c0cd64aca3ae5a5f515a073676b3d68ff9f7abee0ca6b04`, holds:

- **20 hash-only exact-file exclusions.** 19 come from the owner 1.0.5, and the Projects
  `.github/workflows/ci.yml` one comes from the owner 1.0.6. They are the same rows and
  classifications as the waiver entries, and they stay valid across pin moves until the file bytes
  change.
- **1 allowance:** the Memories `mcp` publication (PS07), identical to the waiver entry apart from
  owner and reason. It is removed and re-added from the owner 1.0.5.

[prior-owner-approvals.json](prior-owner-approvals.json) binds both prior approvals: amendment and
receipt hashes, the verbatim labels, and the approved canonical hashes (`46167f41…` and `77457c13…`).
The owner 1.0.5 is in `evidence/release-maintenance-20261112/foreign-1.0.5-assertions/`. The owner
1.0.6 bytes are copied unchanged into [prior-owner-1.0.6/](prior-owner-1.0.6/) from the dropped
local commit `56e0865`.

## Still waiver-only

[remaining-waiver-only.json](remaining-waiver-only.json) lists the entries still waiver-only:

- 21 allowances:
  - the Composition closure, whose current sources differ from the bytes the owner approved;
  - 20 entries the owner never approved, 12 of them with rows or classifications that differ from
    the reviewed draft of 2026-11-12.
- 12 exclusions:
  - the current Builds audit snapshot bytes;
  - 11 captured-evidence and fixture files.

Owner approval of these needs a separate review.

## How it is applied

`assemble-renewal.py --write "<label>" --approved-sha256 <canonical>` does the following:

- writes `amendments/1.0.7.json`, its v2 receipt and the index entry, then loads the chain;
- binds authority only to the owner lineage: the Story 5.1 approval and the 1.0.1/1.0.2 receipts,
  never a waiver receipt;
- records `priorOwnerApprovals`.

It refuses if the canonical hash, `HEAD`, the pins, `check.py`, the report or a prior approval
changed.

## Verification

- **Rehearsal:** loads the chain at 1.0.7 ([rehearsal-load.json](rehearsal-load.json)).
- **Coverage dry run:** [dry-run-merge.json](dry-run-merge.json), [dry-run-census.json](dry-run-census.json).
  It exits **0** with 0 errors, 0 rejected and 17 of 17 roots.
- **Pin-move control:** [pin-move-control.py](pin-move-control.py), [pin-move-control.json](pin-move-control.json).
  It rebinds all 54 revision-bound entries of the 20 files to a revision no pin has:
  - with the draft: exit 0, 0 errors;
  - without it: exit 1, with exactly 20 `excluded-source-revision-drift` errors on exactly these files.
- **Secret scan:** [secret-scan.json](secret-scan.json) covers this folder.

## Approval and outcome (2026-11-12)

The release session was paused. The owner selected **"Approve hash-only 1.0.7 as owner (Recommended)"**
for canonical SHA-256 `e0f1ef0d8885ba528c0cd64aca3ae5a5f515a073676b3d68ff9f7abee0ca6b04`. No separate
review round was run, because every entry is byte-identical to an entry the owner had already approved.

`--write` recorded the label verbatim and loaded the chain at 1.0.7
([write-result.json](write-result.json)). Amendment SHA-256
`48b8463b6fcbd69d436461e380f86b57d0a912221b38bf75f85f1e567df0cfba`.

The [post-approval verification](post-approval-verification.json) records these results:

- 222 census fixtures and 195 release regressions pass.
- The real committed-pin scan at `4b19b5362b3c` exits **0**, identically for hash seeds 1 and 2:
  policy 1.0.7, 0 errors, 0 rejected observations, 17 of 17 roots passing
  ([post-approval-census.json](post-approval-census.json)).

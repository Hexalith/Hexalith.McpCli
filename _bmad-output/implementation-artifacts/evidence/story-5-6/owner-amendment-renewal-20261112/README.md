# Census amendment 1.0.5 — renewal draft (not approved)

> **Status, 2026-11-12:** the owner approved this draft, and it was written as 1.0.5 in
> `05f9e51`. Those bytes replaced a waiver 1.0.5 already pushed in `f995412`, so `0f00d12`
> restored the original and archived these bytes as unverified history. This renewal is not
> in the active chain; see the story spec's Spec Change Log.

This folder is a **draft**. It grants no allowance, exclusion or authority. The
active chain ends at 1.0.4, and no 1.0.5 receipt exists in the repository.

## Why a renewal is needed

Amendments 1.0.3 and 1.0.4 bind their file exclusions to exact source revisions
(`sourceRevision`). `ab4d2dc` moved 16 of the 17 root pins; only
`Hexalith.AI.Tools` stayed. With this change's checker (`check.py` SHA-256
`967dd359072bb7abd42656afb50fbb09eb90b8b44e59937a8e1c8a06fbd546bf`, recorded in [source-checker.json](source-checker.json)), the census at
parent `ab4d2dcfca150b0aa6b550a788c0f92d5ddb88ae` reports the following
([source-census.json](source-census.json), SHA-256 `ba5143c17b01dd2df9061208865336d347a5f5fd832789f8a037b13570b4c10c`, identical across
hash seeds 1 and 2):

- 20 `excluded-source-revision-drift` errors;
- 2 source-drifted allowances: Memories `tools/release-containers.json` (PS07)
  and Platform `Hexalith.Platform.Composition` (PE03).

The two Tenants AppHost Compile fallbacks no longer appear. They are excused by
rule (c) of the census guard excuse, approved by the owner on 2026-11-12
("Extend the excuse to Compile items").

**First human validation.** The 1.0.3 and 1.0.4 receipts record that human
validation was explicitly bypassed. Approving 1.0.5 is therefore the first
owner validation of the 22 classifications it renews. Their rows, classes and
signal sets come from 1.0.3/1.0.4 unchanged. The receipt also records
`runtimeAcceptance: false` and `migrationAcceptance: false`.

## What the owner approves (one of two exact variants)

| Variant | File | Canonical SHA-256 | Behaviour at the next pin move |
|---|---|---|---|
| Revision-bound, as 1.0.3/1.0.4 | [authorization.draft.json](authorization.draft.json) | `e701e7ddf04ac4d4d15bb61b9fde4463fb6aa289078f0deaf2d7dd0efd6ae750` | Each exclusion fails again and needs another renewal. |
| Hash-only | [authorization.hash-only.draft.json](authorization.hash-only.draft.json) | `46167f41a77406075acc9e396308c75b138ac32c5382a756b27bfc7a65452345` | Exclusions stay valid while file bytes are unchanged, and still fail on any byte change. |

Both variants renew the same entries. Every entry's owner is
"Requesting user, owning maintainer", the same owner as the receipt.

`assemble-renewal.py --write "<label>" --approved-sha256 <canonical>` writes
three files: `amendments/1.0.5.json` (the lists plus the header from 1.0.4),
`amendments/1.0.5-approval.json` (a v2 receipt with the label verbatim, the
source report, checker hash and pins) and the `amendments.json` entry. For the
hash-only variant, that file replaces `authorization.draft.json` first. The
script refuses unless the draft's canonical SHA-256 equals the approved value
and `HEAD`, every root pin, `check.py` and the source report are unchanged. It
writes atomically, then loads the written chain with `load_policy`.

## What it renews

- **20 exclusions:** each renews the latest revision-bound entry. 18 files are
  byte-identical to that entry. Two changed, and their reviewed summaries are
  part of the approved `reason` strings:
  - FrontComposer `.github/workflows/quality.yml`:
    - SDK 11.0.100, with the range gate now `[11.0.100, 11.0.200)`;
    - `initialize-dotnet` pinned from `@main` to a commit;
    - an extra `setup-dotnet` 10.0.404 install and a .NET 10 runtime step;
    - Aspire CLI 13.6.5 and a test artifact flag.
  - Projects `.github/workflows/ci.yml`:
    - Builds pins and Dapr 1.19.1 bumps, additional SDK 10.0.404, Aspire CLI
      13.6.5 and extra unit tests;
    - an EventStore `--unshallow` fetch;
    - the G6 policy moved to the repository-local
      `tools/qualification/g6-current-policy-2026-11-12-dapr-net1191.json`;
    - the source-mapping step now builds the Builds `hexalith-module` CLI and
      runs the built DLL.

  Neither change adds a publication, packing or container step.
- **2 allowances (each one exact removal and one addition):**
  - Memories `mcp`: only the recorded `buildsSha` changed.
  - `Hexalith.Platform.Composition`: its compilation closure is recomputed.
    Platform `eff9e909` adds the internal 64-line
    `WorksPreviewManagedRuntime.cs`, which runs `dotnet --list-runtimes`, and
    updates `WorksPreviewModel.cs`. The signal set is unchanged.

[build-renewal.py](build-renewal.py) uses the census's own isolated Git reads.
It refuses to build unless all of these hold:
- the report covers exactly the root declarations and gitlinks at `HEAD`;
- the amendment index matches the report's chain ending at 1.0.4;
- the errors are exactly the 20 revision drifts, and the rejections are exactly
  the 2 source-only drifts;
- each exclusion's bytes equal its latest entry, except the two reviewed files;
- the closure delta is exactly the reviewed `eff9e909` change, and the Memories
  delta is exactly `tools/release-containers.json`.

## Reproduce, in order

1. `python3 tools/proprietary-surfaces/v1/check.py --output <folder>/source-census.json`, at `HEAD` (exit 1).
2. `python3 <folder>/build-renewal.py`, which writes the draft and `source-checker.json`.
3. `python3 <folder>/assemble-renewal.py --rehearse <empty dir outside the repository>`.
   It loads the chain at version 1.0.5 with 515 allowances and 118 exclusions
   ([rehearsal-load.json](rehearsal-load.json)).
4. `python3 <folder>/dry-run-gate.py <empty dir>`, which writes a scratch baseline
   with SHA-256 `45fcd852afff2be73e0eac3aeb93739e7c76b5d42fab0920340cd41b090150c2` ([dry-run-merge.json](dry-run-merge.json)).
5. `python3 tools/proprietary-surfaces/v1/check.py --baseline <dir>/baseline.json --amendments <dir>/amendments.json --output <file>`.
   This exits **0**: 0 errors, 0 rejected and all 17 roots passing.
   - [dry-run-census.json](dry-run-census.json), SHA-256 `c910dffc379373163efdc29f22c32c57b263aff5454d34ff3cc0a4db22fc1aef`, is the
     revision-bound result.
   - [dry-run-census.hash-only.json](dry-run-census.hash-only.json), SHA-256
     `1e97ccbf13908b585dbf6fbd10ff3479369b22606b752a47a997f856480f8bf9`, is the hash-only result.

[secret-scan.json](secret-scan.json) covers this folder. Any later change to
`check.py` invalidates these hashes, and the builder and assembler then refuse.
After approval and `--write`, rerun the census fixtures, the release
regressions and the real scan.

## Approval and outcome (2026-11-12)

The owner selected **"Approve hash-only 1.0.5 as owner (Recommended)"**. The
hash-only lists (canonical SHA-256
`46167f41a77406075acc9e396308c75b138ac32c5382a756b27bfc7a65452345`) became
`authorization.draft.json`; the revision-bound variant is kept as
`authorization.revision-bound.draft.json`. `assemble-renewal.py --write`
recorded that label verbatim, wrote `amendments/1.0.5.json`, its receipt and
the index entry, and loaded the chain at version 1.0.5
([write-result.json](write-result.json)).

The [post-approval verification](post-approval-verification.json) records these
results:

- 223 census fixtures and 195 release regressions pass.
- The real committed-pin scan exits **0**, identically for hash seeds 1 and 2,
  at parent `ab4d2dc`: 0 errors, 0 rejected observations, 17 of 17 roots passing
  ([post-approval-census.json](post-approval-census.json)).
- `git diff --check` passes.

# Current McpCli published-cohort local repair

This packet records local qualification of the existing EventStore 4.2.0,
Tenants 7.0.7 and Parties 3.1.1 cohort. It grants no hosted, native, migration
or publication acceptance.

- `verification-index.json` records every command, result and raw-output hash.
- `final-source-manifest.json` binds final code, configuration, test and approval
  inputs. Command-specific contexts identify the inputs actually associated with
  final focused checks; earlier failures retain historical context and are not
  presented as verification of corrected bytes.
- `dependency-selections.json` verifies the unchanged approved package closure
  and preserved product/analyzer targets.
- `enrollment-summary.json`, `catalog-benchmark.json` and the topology summaries
  record the successful local replay, benchmark, preflight and discovery checks.
- `approved-spec.md`, `investigation.json` and `source-bindings.json` retain the
  specific approval and exact workflow/eight-source probe bindings used by
  amendment 1.0.8.
- `candidate-census-summary.json` distinguishes the two approved additions from
  eight remaining allowance drifts and four inspection errors.
- `remaining-census-followup.json` and `source-context-comparison.json` record
  pending bindings at the local and newer investigated source revisions. They
  confer no additional approval.

Sanitized raw reports and logs are retained byte for byte under `raw/`, with
packet-relative paths and SHA-256 bindings. Absolute scratch paths in original
command records and archived receipts describe their historical execution
environment; they are not required to retrieve the durable evidence. Archived
scan receipts describe their original manifests; the newest final packet scan
`secret-scan-final.json` covers the final packet after the independent recheck.

The unchanged census validator enforces the amendment's receipt hash, validated
prior `authority`, exact `authorization` arrays, allowance identities/signals,
and declared source/compilation-closure hashes. The receipt's `approvalEvidence`,
`sourcePins`, `sourceBindings` and `sourceChecker` are supplementary authoring and
provenance records. Their bytes are covered by the receipt hash, but the validator
does not independently dereference or enforce those extra fields. They confer no
additional approval or source-revision predicate.

The helper attests only to SHA-256 equality of existing HEAD, index, packed-refs
and file contents beneath refs. It does not measure other Git files, objects,
configuration or filesystem metadata. Failures record a new failed report and
provenance; a candidate overlay never establishes committed or hosted acceptance.

Independent review and the focused correction rechecks are complete; see
`review-result.json`. Additional census authority and exact-source hosted/native
CI remain pending. The ordinary owning-workspace census also lacks nested objects,
which were deliberately left uninitialized. `pending-census-actions.json` contains
concrete inactive proposals for later owning-maintainer decisions, including three
new helper exclusions.

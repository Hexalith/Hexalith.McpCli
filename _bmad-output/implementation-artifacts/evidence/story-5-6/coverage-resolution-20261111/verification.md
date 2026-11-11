# Story 5.6 coverage resolution verification

Implemented bounded generic fixes for the continued coverage-error assessment.
Acceptance remains **failed**; story and sprint remain `in-progress`.

| Check | Result |
|---|---|
| Census fixtures | 158 passed |
| Guard-removal controls | All 132 detected |
| Release regressions | 195 passed |
| I/O matrix | All five rows have passing executed coverage |
| Determinism | Identical complete report bytes for hash seeds 1 and 2 |
| Implementation integrity | All four source/README hashes unchanged throughout final serial verification |
| Current committed-pin census | Exit 1; 17 roots accounted for, 2 fully inspected, 548 observations, 120 rejected observations, 109 coverage errors, 2 stale allowances |
| Policy integrity | All nine inventory, approval, baseline and amendment bindings unchanged and equal to HEAD |
| Prior evidence integrity | All 40 receipt-covered files from the preceding resume packet unchanged |

[The coverage assessment](coverage-assessment.json) accounts for every one of the
111 original errors exactly once across 12 root-cause groups: 101 retain
the exact diagnostic, 8 have no remaining error at that source, and
2 lose the original diagnostic while independent coverage errors remain.
The 8 newly reported coverage errors preserve dynamic publication/redirection refusals
and expose nested JSON data ambiguities. [The delta](report-delta.json) retains
every added/removed error and rejection. Counts of rejected observations do not
establish a count of newly created tools.

The [decision packet](decision-packet.md) separates scanner limitations, protected
source boundaries, source-data ambiguity, exact owner disposition and the absence
of a proven active upstream defect. [Its machine-readable detail](remaining-decisions.json)
and [the complete blocker bindings](acceptance-blockers.json) identify the exact
committed root pins, blob hashes, origin metadata and recommended next actions.
No observation authorizes an allowance, fixture exclusion or additional source scope.

The exact acceptance command is:

```sh
python3 tools/proprietary-surfaces/v1/check.py --output _bmad-output/implementation-artifacts/evidence/story-5-6/coverage-resolution-20261111/census.json
```

It exits **1**. [The report](census.json), [diagnostics](current-pin-census.stderr.txt),
[executed commands](commands-executed.json), [matrix coverage](matrix-coverage.json),
[mutation controls](mutations.stdout.json), [complete-byte determinism](determinism.json),
[implementation integrity](implementation-integrity.json), [policy integrity](policy-integrity.json)
and [prior evidence integrity](prior-evidence-integrity.json) retain the final checks.
Exploratory outcomes and superseded serial runs are preserved under [attempts](attempts/).
The final serial run used fixed implementation bytes; its before/after hashes match.
The complete new packet is covered by [its secret-scan receipt](secret-scan-final.json).

The checker and tests remain generic. PowerShell evaluation, runtime/generated
projects, external Compile selectors and nested targets remain coverage refusals.
No inspected command, generator, MSBuild project, Copy task or nested tree was
executed/opened. No reference, gitlink, dependency or policy byte changed. No
staging, commit, push, publication, .NET/live validation or actual GitHub CI is
claimed for this Python/documentation change. The release gate remains blocking.

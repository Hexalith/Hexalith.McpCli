# Story 5.6 reviewed source-resolution verification

The user-authorized generic source-resolution work and all 24 individually
triaged review findings are implemented in 23 patch groups. No finding was
deferred. Story and sprint remain `in-progress` because current-reference
acceptance remains unsuccessful.

| Check | Result |
|---|---|
| Census fixtures | 142 passed |
| Release regressions | 195 passed |
| Guard-removal controls | 110 detected |
| I/O matrix | All five rows have passing executed coverage |
| Determinism | Identical complete reports with Python hash seeds 1 and 2 |
| Current committed-pin scan | Exit 1; 17 roots accounted for, 3 fully inspected, 540 observations, 112 rejected observations, 110 coverage errors, 4 stale allowances |
| Policy integrity | All retained inventory, approval, baseline and amendment bindings unchanged |

The exact acceptance command is:

```sh
python3 tools/proprietary-surfaces/v1/check.py --output _bmad-output/implementation-artifacts/evidence/story-5-6/source-resolution-review-20261111/census.json
```

Its exit is **1**. [The report](census.json), [diagnostics](current-pin-census.stderr.txt)
and [current acceptance blockers](acceptance-blockers.json) identify every
unresolved observation and coverage error. The blocker packet binds each
finding to its root pin, detection source blobs and SHA-256 hashes, retaining
its owning-maintainer label and no new authority. These observations include
existing projects whose metadata could not be qualified; they require source
proof, further approved generic resolution or specific versioned owner
qualification. The report does not establish a count of newly created tools.

## Requested inspection cases

[The current case receipt](inspection-cases.json) preserves the five original
case identifiers and their exact inspected source pins.

- E01 resolves the finite Web/Api calls to exact caller project paths. Those
  projects remain absent from the inspected tree and their publications fail.
- E02 currently stops on an unsafe imported path before reaching generated
  Compile provenance. Its original generated Copy-source limitation remains
  covered by passing tests and preserved initial evidence; no generator runs.
- E03 resolves its working-directory-relative target and refuses the exact
  nested gitlink target.
- E04 resolves the Contracts/Server loop to two exact committed target paths.
  Their imported metadata still blocks qualification, so the corresponding
  publication observations remain rejected.
- E05 enumerates the finite nested package targets and retains each coverage
  error without opening or initializing a nested repository.

Individual source failures now retain the other inspectable observations in
that root. Partial roots carry `inspectionComplete: false` and cannot establish
staleness. More complete reporting and stricter metadata refusal expose findings
that the earlier root-aborting scan did not retain; the counts have different
coverage from the initial nine-rejection/five-error report.

## Review and evidence

The review addressed shell state, quoted and prefixed commands, matrices,
heredocs, required and optional imports, nearest build metadata, bounded
property expansion, exact image provenance, tool definitions versus consumption,
missing source recovery, report-writing failures and deterministic diagnostics.
Registry/repository association qualifies ordinary images only through declared
metadata; unrelated registries and projects with MCP/CLI signals remain visible.

[Executed commands](commands-executed.json), [matrix coverage](matrix-coverage.json),
[mutation results](mutations.stdout.json), [determinism](determinism.json),
[policy integrity](policy-integrity.json) and [source/report bindings](verification.json)
retain the final checks. The [initial triage](triage.json) and [final state triage](triage-state.json)
record every verdict; the spec records all 24 individual findings before grouping.
The first complete parent run is preserved in [its archive](attempts/parent-final-1/verification.json).
The original source-resolution packet remains byte-identical to its scan receipt.

Parent revision: `051fadedf68335ba5c525cf26c42f86aa69697f9`. This revision binds the root
references; the uncommitted checker changes are separately bound by exact file
hashes. No inspected program, generator, Copy task or MSBuild project was run.
No nested repository was opened or initialized. Production source, dependencies,
gitlinks, reference content and active allowance data remain unchanged.
Actual GitHub CI or live acceptance is not claimed.

The final [evidence secret-scan receipt](secret-scan.json) binds this completed
packet. The real failed acceptance gate remains the workflow blocker; no
completion status or owner approval is inferred.

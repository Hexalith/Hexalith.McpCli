# Story 5.6 bounded source-resolution verification

The generic resolver work is implemented at parent `051fadedf68335ba5c525cf26c42f86aa69697f9`
with the checker and test SHA-256 bindings in [verification.json](verification.json).
The parent revision identifies the committed root declarations and pins; the
checker changes are uncommitted and bound separately by their exact file hashes.

| Check | Result |
|---|---|
| Census fixtures | 117 passed; exit 0 |
| Release regressions | 195 passed; exit 0 |
| Guard-removal controls | 70 detected; exit 0 |
| I/O matrix | All five rows have passing executed coverage |
| Committed-pin census | Exit 1; 17 roots accounted for, 5 complete roots, 458 observations, 14 rejected observations, 50 coverage errors and 4 stale allowances |
| Policy integrity | All retained inventory, approval, baseline and amendment bytes match HEAD and remain unchanged |

The [commands](commands.json), [fixture output](census-tests.stderr.txt),
[release output](release-tests.stderr.txt), [mutation controls](mutation-guards.py),
[mutation results](mutations.stdout.json), [matrix audit](matrix-coverage.json)
and [policy bindings](policy-integrity.json) retain the exact verification.
Release regressions were captured earlier in this same implementation run;
release source/tests did not change. Earlier fixture captures are preserved
under `attempts/`: the first caught an error-expectation typo in the new
missing-blob fixture, and later passing captures precede stronger regression
assertions and the final ambiguous-loop refusal. No acceptance failure was
converted into a passing allowance.

The [inspection-case receipt](inspection-cases.json) binds E01–E05 to their
exact root pins, source Git blobs and SHA-256s:

- E01 resolves the two literal Web/Api function calls to exact caller-owned
  project paths. Those projects are absent from the inspected Builds tree,
  so both remain rejected orphan publication observations.
- E02 retains a generated-source coverage error. The Compile item comes from
  a Copy task whose generated `obj` inputs have no committed bytes.
- E03 resolves the parent-relative invocation against its proven working
  directory and refuses the exact target under a nested gitlink.
- E04 resolves the literal Contracts/Server loop to two committed library
  projects. The workflow has no publication candidate or coverage error.
- E05 resolves each finite package-loop target and refuses its nested
  EventStore/Platform source without opening any nested repository.

Compile aliases and committed Copy inputs now retain their source provenance.
Unknown aliases/transforms, missing source, cycles and bounded-size failures
remain coverage errors. Shell variables, ordered literal loops, positional
function arguments, local/global state and committed working directories are
resolved only within the documented subset. Conditional loop alternatives
cannot be mistaken for sequential literal values. Workflow/job/step directory
precedence and shell-step isolation are covered. Explicit project directories,
implicit targets and committed `.slnx` solutions resolve to exact projects;
missing/ambiguous directories and unsupported solutions fail closed.

Individual project/file failures, missing blobs, exclusion drift and allowance
closure failures retain other inspectable candidates. Partial roots explicitly
set `inspectionComplete: false` and do not establish stale allowances. This
restores previously discarded observations and exposes additional runtime or
nested-source coverage gaps; the census does not claim those roots are fully
inspected.

The failed acceptance command is:

```sh
python3 tools/proprietary-surfaces/v1/check.py --output _bmad-output/implementation-artifacts/evidence/story-5-6/source-resolution-20261111/census.json
```

Its [report](census.json) and [complete diagnostics](current-pin-census.stderr.txt)
retain the exact identities, signals and errors. No inspected program, condition,
generator, Copy task or MSBuild project was executed. No nested repository was
opened or initialized. No production source, dependency, gitlink, upstream
content, allowance, exclusion, exception or owner authority changed. Actual
GitHub CI execution is not claimed.

Current-reference acceptance remains unsuccessful. The remaining observations
need owner disposition or further approved generic source-resolution work.
Story and sprint remain `in-progress`. The [secret-scan receipt](secret-scan.json)
binds the completed packet; [diff-check.json](diff-check.json) records whitespace
validation.

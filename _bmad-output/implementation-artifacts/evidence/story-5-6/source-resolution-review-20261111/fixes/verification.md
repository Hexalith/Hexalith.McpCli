# Story 5.6 review fixes S01–S18

All demonstrated findings are patched in the generic checker. No allowance,
exception, exclusion, dependency, gitlink or upstream source changed.

The focused run passed 18 new regression methods, 20 directly affected existing
census tests and 26 executed guard-removal controls. Each CLI fixture checks its
exit status, complete stdout/report bytes, complete stderr and exact observed
identities or coverage errors. Report directory-creation and file-write failures
independently assert exit 1, empty stdout and the exact safe diagnostic.

The [review mutation runner](../mutation-guards.py) retains all 70 earlier
controls, adapts two changed source anchors, and adds the 26 review controls.
Its default mode runs all 96 controls; `--review-only` runs the new controls.
Only the new controls ran here. [The command receipt](verification.json) records
commands, results and current checker/test/runner hashes; [mutation results](mutations.stdout.json)
and the fixture streams retain focused execution evidence.

- S01–S05: unsupported inline loops and executable unquoted heredoc substitutions
  fail explicitly; quoted executables, supported Docker global/image syntax and
  bounded quoted matrix alternatives preserve exact targets and job/step scope.
- S06–S10: container suppression needs the complete declared identity; local npm
  definitions cannot borrow tool-consumption exemptions; required local imports
  fail when absent, while exact optional Exists, SDK and nested imports remain
  distinct. Property expansion is bounded and default metadata uses the nearest
  file plus its explicit imports.
- S11–S15: conditional loops retain uncertainty, unknown loops invalidate changed
  caller directories, shell state commands invalidate affected variables, quoted
  function arguments preserve their lack of variable authority, and executable
  shebang reads retain per-source recovery.
- S16–S18: output-write failures stay nonzero, environment prefixes retain their
  publication command, and alternative traversal/diagnostics are deterministic
  across four PYTHONHASHSEED values.

[Original packet integrity](prior-evidence-integrity.json) verifies every file
bound by the earlier source-resolution packet's secret-scan receipt remains
byte-identical. Its original receipt and all earlier parent review artifacts
were preserved. Final full verification, acceptance scanning and the final
combined evidence refresh remain with the parent workflow.

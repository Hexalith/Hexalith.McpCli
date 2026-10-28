# Final-review follow-up — 2026-10-28

Added `test_runner_contract_mismatch_refuses_live_after_preparation` for both
unsupported `ASPIRE_TEST_PROJECT` and `TEST_PLATFORM`. Each case first completes
valid preparation, then checks exit 1, empty stdout, the exact stderr diagnostic,
the complete failed acceptance receipt and no vector or smoke invocation.

`README.md` and `tools/live-topology/README.md` now require Python 3.11.4+ with
`venv` and `ensurepip` support. No runtime guard or diagnostic was changed.

Only these focused tests ran:

```sh
PYTHONPATH=tools/live-topology python3 -m unittest -v \
  test_ci.CiHooksTests.test_runner_contract_mismatch_refuses_live_after_preparation \
  test_ci.CiHooksTests.test_caller_contract_and_unsafe_evidence_paths_are_refused
```

Both pass; [output](targeted-tests.txt) records 2 tests in 4.350 seconds.
Removing only `run()`'s `require_contract()` call from `ci.py` in the test's copied
fixture makes both new subcases fail because the unsupported callers return 0.
The [removal output](runner-contract-guard-removal.txt) records those two expected
failures. The repository's `ci.py` was unchanged. Scoped `git diff --check` passes.
The parent owns full verification after this follow-up.

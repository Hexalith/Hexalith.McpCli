# Story 4.10 code review pass 2 patches

R14–R17 are implemented without changing the approved Contracts, vectors,
release inventory, dependency pins or reference gitlinks.

- R14: candidate preparation checks the declared EventStore and Commons
  dependency versions in restore and build commands, plus both receipt fields,
  using default alignment and explicit `align_candidate_dependencies=False`.
- R15: loopback regressions assert complete `VectorError` messages when assets
  cannot be inferred, are unavailable, or lack the matching package library.
- R16: the failing-restore callback checks that the old `artifact.sha512` is
  absent while the current receipt is still pending.
- R17: enrollment checks MSBuild metadata names case-insensitively; four casing
  variants must each invoke exact-artifact verification.

From `tools/conformance-vectors/v1`,
`python3 -m unittest test_enrolled test_loopback` passed all **55 tests**.
`git diff --check` passed. [Exact checks](checks.json) record source hashes and
captured output, plus eight disposable-copy removal mutations, all detected:
disabled alignment, missing restore overrides, missing build overrides, each of
the three assets/library guards, missing initial success invalidation, and the
old case-sensitive metadata lookup. The last mutation reproduces the original
three failing casing variants.

This is focused implementation evidence. Parent full repository, sample and
production conformance checks and independent review remain open. Existing
R18/R19 deferrals remain unchanged; no approval or live authorization/domain
effect claim is added.

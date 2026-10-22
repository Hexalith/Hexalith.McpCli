# Story 4.11 — final corrected-source verification

All nine original pass-4 patches and all three independent-review patches are complete. The timestamp oracle accepts the demonstrated SDK empty-fraction forms; quoted integer conversion preserves signs/ranges while removing redundant leading zeroes; the full-run error fixture rejects a message ID reused only for synthetic 503 calls. The [focused record](focused/verification.json) and [mutation output](focused/synthetic-503-mutation.stderr.txt) retain the final guard-removal proof. The initial pass's ten guard/diagnostic removal checks remain in [the earlier record](../review-pass4/verification.md).

The [final verification record](verification.json) retains all 17 sequential commands, environments, exits and stdout/stderr channels on the corrected source:

- Fresh solution restore and Release warnings-as-errors builds passed.
- All six ordinary .NET projects passed: **1,368 successes, five expected skips** (four existing Windows cases and the intentional non-probe measurement skip).
- All **157 named Python tests** and both complete Sample gates passed. The real-SDK process fixture includes both empty-fraction timestamps and the 5,000-leading-zero page size, plus the complete 24-operation production-plus-sample replay and deliberate inventory/assertion refusals.
- Strict production replay passed both approved modules: **21 operations, 78 preflight calls, 198 documents and 198 complete captured requests**. Complete observations and artifact-bound receipts are under [enrolled/](enrolled/).
- First Catalog construction in a fresh process measured **157.3627 ms** against **500 ms**, with exactly Parties, Tenants and one Ulid sample. [Benchmark evidence](catalog-benchmark.json) reports acceptance with no diagnostics, failures or missing modules. All ten named [Core matrix cases](matrix-core.xml), including isolated String coverage, passed.
- Every one of **3,740 source-input hashes** remained unchanged throughout the final checks. The [matrix mapping](matrix-coverage.json) identifies passing cases for all seven frozen rows. The [protected input hashes](protected-inputs.json) bind the unchanged approval records, vectors, inventory, dependency policy, scope and Builds pin.

The [parent acceptance audit](parent-acceptance-audit.json) independently rechecks named coverage, source/protected/evidence hashes and all retained documents and requests. All thirteen independent-review claims have separate rulings in the spec. Three were patched; the decimal-precision limitation was already tracked, and inherited root-receipt progress was newly deferred. Carried whitespace and interrupted-write rulings remain unchanged.

These are local results; no new normal Ubuntu CI run, push, merge, release or publication is claimed. Each fullV1Accepted flag covers its own gate; both replay and benchmark passed. Scripted transport parity does not replace the later live authorization, privacy, persisted-effect or retirement gates.

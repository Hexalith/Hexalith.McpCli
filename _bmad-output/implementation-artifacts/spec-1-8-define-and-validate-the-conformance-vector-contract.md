---
title: 'Define and Validate the Conformance Vector Contract'
type: 'feature'
created: '2026-09-27'
status: 'done'
baseline_commit: '9b3b099bf117eac880b9b6e12422990a168519eb'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Existing v1 tooling supplies most of Story 1.8, but accepts malformed vectors and presents the later loopback runner as the primary sample gate.

**Approach:** Harden the existing test-only schema and reusable validator, verify the synthetic vectors against a locally packed Contracts artifact, and document the v1 author approval and runner handoff.

## Boundaries & Constraints

**Always:** Retain v1 names, package identity/version, generic calls, Payload/Envelope inputs, request/response expectations, and assertion vocabulary. Close contract-owned objects; preserve Module-owned JSON data and all three samples. Use identical rules for authors and runners, with source/location/reason diagnostics. Compare package IDs case-insensitively and versions exactly.

**Never:** Add production dependencies, Module-specific branches, assembly loading, upstream edits, or publication. Require neither Head, Gateway, nor AppHost. Production restored-package rechecks and parity belong to Story 4.11; live semantics belong to Story 4.13. Runner defects remain outside this story.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Author approval | Valid synthetic Command and Query vectors plus packed owning artifact | Accept; CLI exits 0 | No network service needed |
| Compatibility | Wrong package ID/version, stale runner expectation, unsupported format | Reject; CLI exits 1 | Identify package or format location |
| Shape and syntax | Unknown contract fields, malformed names/ULIDs, blank required strings, non-JSON numbers | Reject at every call position | Located validation findings |
| Script consistency | Wrong-kind inputs/echo fields or conflicting supplied extensions | Reject contradictory expectations | Identify offending call field |
| Assertions | Unknown operator, invalid pointer, missing/wrong typed value | Reject | Assertion location and reason |

</frozen-after-approval>

## Code Map

All tooling paths below are under `tools/conformance-vectors/v1/` unless qualified.

- `schema.json` — operation regex allows extra dots, excludes digit-leading parts, and accepts trailing newlines.
- `validate.py` — reuse `validate_vectors`, `_check_step`, `package_identity`, and CLI; fix permissive JSON parsing and missing consistency checks.
- `test_validate.py` — 11 offline tests using temporary nuspec ZIPs; expand negative coverage.
- `README.md`, `run-sample-loopback.sh` — existing instructions and broader gate; preserve parity semantics.
- `tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj` — packs with `IsPackable=true`, `Version=1.0.0`; no project edits.
- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs` — naming reference: two dot-separated lowercase alphanumeric kebab-case parts; digit-leading parts allowed. Read only.
- `.github/workflows/ci.yml` — contract job currently executes loopback too.

## Tasks & Acceptance

**Execution:**
- [x] `tools/conformance-vectors/v1/schema.json` — align names, enforce strict string boundaries and nonblank inputs, preserve closed fields and assertion operators.
- [x] `tools/conformance-vectors/v1/validate.py` — reject nonfinite JSON with locations; check nonblank routing, supplied extensions, and query response echoes across all steps.
- [x] `tools/conformance-vectors/v1/test_validate.py` — cover the matrix, prerequisite/postcondition checks, ID/version mismatches, valid boundaries, and CLI/reusable-entry-point behavior.
- [x] `tools/conformance-vectors/v1/run-sample-validation.sh` — pack the sample into a temporary directory, run validator tests, validate all three vectors against the artifact and expected identity. Support Debug locally and Release in CI; clean only its temporary files.
- [x] `.github/workflows/ci.yml` — run the new offline gate independently; retain the existing loopback lane as a separate job.
- [x] `tools/conformance-vectors/v1/README.md` — record version, compatibility policy, approval procedure, validator invocation, and 4.11/4.13 handoff. Distinguish offline checks from later Catalog/payload compatibility and execution.

**Acceptance Criteria:**
- Given the existing sample Contracts project, when the standalone offline gate packs and validates its vectors, then all examples pass without building either Head or connecting to a Gateway.
- Given malformed or incompatible vectors, when authors or runners use the shared validator, then both receive actionable rejections under the same rules.
- Given the author instructions, when a maintainer prepares approval evidence, then they can identify the version, immutable artifact, validation command/result, and downstream responsibilities without parity or live tests.

### Review Findings

Second code review, 2026-09-27, `9b3b099..1bf6906` (excluding committed `story-1-8-review/` scaffolding and this spec), four layers.

- [x] [Review][Patch] Pull the cheap deferred validator gaps into 1.8 (decision 2026-09-27: fix now) [tools/conformance-vectors/v1/validate.py:117] — The matrix row "Reject contradictory expectations" and the Problem ("accepts malformed vectors") are still partly open via deferrals: expected extensions/paging with none supplied; Query `expectedGateway.body.idempotencyKey`; `pageSize: true` equal to `1`; `offset` above Int32. New this pass: whole-number floats are accepted in every integer field, not only `pageSize` — reproduced `formatVersion: 1.0` and `statusCode: 202.0` → no findings. Most are one-line schema/`_check_step` changes, e.g. a strict `integer` type checker plus `"maximum": 2147483647`.
- [x] [Review][Patch] Approval evidence hash (SHA-256) differs from the runner's restored-package check (NuGet `sha512-` base64) [tools/conformance-vectors/v1/run-sample-validation.sh:29]
- [x] [Review][Patch] `sha256sum` missing on macOS turns a passed validation into exit 127 [tools/conformance-vectors/v1/run-sample-validation.sh:29]
- [x] [Review][Patch] README says `schema.json` and `validate.py` define the same rules; cross-field rules live only in `validate.py` [tools/conformance-vectors/v1/README.md:3]
- [x] [Review][Patch] Duplicate-key test does not assert the `source:/:` location prefix or CLI/API parity [tools/conformance-vectors/v1/test_validate.py:118]
- [x] [Review][Patch] `run-sample-validation.sh` committed as 100644 while sibling `run-sample-loopback.sh` is 100755 [tools/conformance-vectors/v1/run-sample-validation.sh]
- [x] [Review][Patch] Explicit empty configuration argument silently runs Debug instead of exiting 2 [tools/conformance-vectors/v1/run-sample-validation.sh:4]
- [x] [Review][Patch] Previous review scaffolding (~1,800 lines of reviewer prompts with stale diff copies) was committed in 9951257 [_bmad-output/implementation-artifacts/story-1-8-review/]

**Rejected**

- Nested duplicate key reported at `/` (raised by all four layers) — low; same call as the first review: uncommon, and the source and key are still reported; path-aware parsing adds complexity.
- Nonfinite check stops file processing on first hit — low; consistent with other load-time failures (syntax, duplicate keys).
- No approval-record template — the README lists the required fields, which satisfies AC3; a template is new scope.
- README does not explain NuGet version normalization — false; a mismatch fails loudly with a located finding naming both versions.
- CLI exit-2 paths untested — low; argparse default behavior, verified manually per Verification.
- `jsonschema` not checked before packing — low; fails loudly with an import error.
- Minimum Python version unpinned — false; the int-digit test guards with `getattr`, and CI images ship 3.12+.
- CI jobs duplicate setup and unit tests — low; separate jobs are what the spec requires.
- `references/Hexalith.Tenants` pointer bump — low; already on `origin/main` in 9951257, unused by this repo's build.
- Commit 9951257 is not a Conventional Commit — low; already pushed, and rewriting history is out of scope.
- Spec `status: done` vs sprint `review` — the fix is editing status; reconciled when this review closes.

## Implementation Notes

- Hardened the existing v1 schema and shared validator; all three sample vectors remain unchanged. CLI package expectations now also reject an explicitly empty expected package ID.
- Added a sample-only pack/validate gate with temporary build outputs and Debug/Release selection; CI runs it independently from the existing loopback job.
- Initial verification: all 41 Python tests passed, including the unchanged runner unit tests. Debug and Release sample gates both passed and accepted all three vectors against their packed artifact. Shell syntax, invalid configuration exit 2, temporary cleanup, CI job separation, and diff whitespace checks passed.
- Matrix audit: sample approval is covered by the packed gates and CLI success test; compatibility by artifact/runner ID and exact-version tests; syntax by closed-object, name, ULID, whitespace and nonfinite tests; script consistency by wrong-kind, extensions and echo tests; assertions by operator/pointer/value tests. The full verbose run executed every covering test successfully.
- Production code, upstream repositories, and parity/live implementations are unchanged. Full parity/live execution remains assigned to Stories 4.11/4.13.
- Resumed review fixed parser-limit diagnostics and added raw malformed-JSON, deep-nesting, and integer-limit regression coverage through both entry points. All 42 tests and both sample gates pass after the patch. Eight pre-existing compatibility defects are recorded in `deferred-work.md`; two low-impact diagnostic refinements were rejected. All fourteen reviewer findings have individual triage rows below.

- Review follow-up completed all eight open patch items: strict integer tokens and Int32 offsets; exact paging types and absent optional-request consistency; wrong-kind request fields; portable NuGet-compatible SHA-512 evidence; executable script and empty-argument rejection; accurate validator documentation; duplicate-key CLI/API regression checks; removal of the three stale review scaffolding files. Five deferred issues are now resolved; the existing cursor-unit, extension-restriction, and routing-syntax entries remain for downstream compatibility work.
- Current verification: all 46 offline tests and both Debug/Release packed sample gates pass. Every matrix row has executed coverage; all three samples remain unchanged. Independent OpenSSL checks match the Python hash output, script argument errors exit 2, and both gate runs cleaned their temporary directories.

- Final review patches add query projection fields to Command rejection, forbid invented Query entity IDs, and make README hashing conditional on validation success. Final verification passes all 47 tests and both packed sample gates. Three review layers completed; all patch findings are closed and remaining pre-existing compatibility issues are deferred. The spec is done and sprint tracking moves to review as required by bmad-build.

## Spec Change Log

## Review Triage Log

Review resumed on 2026-09-27 from the recorded baseline, using all three workflow review layers. Each finding was classified before grouping. Baseline comparisons used `9b3b099bf117eac880b9b6e12422990a168519eb` in an isolated temporary directory; no existing implementation or submodule revisions were reverted.

| Finding | Verdict | Route | Evidence and disposition |
| --- | --- | --- | --- |
| Blind 1: parser-limit exceptions escape | medium | patch | Reproduced an uncaught `ValueError` for 4,301 digits and `RecursionError` for deep JSON. The newly added finite-number traversal also fails on a valid sample with 993 nested arrays that the baseline accepts; catch these failures at the existing load boundary and cover CLI/API behavior. |
| Blind 2: nested duplicate location is root | low | reject | Reproduced the root pointer; the baseline already omitted the containing-object path. Source and duplicate key remain available, and preserving nested object pairs would add parser complexity for an uncommon diagnostic refinement. |
| Blind 3: offset exceeds Int32 | medium | defer | Both baseline and reviewed validators accept 2147483648; the unchanged `RunQueryArguments.Offset` is `int?`. Record the pre-existing validator/runtime range mismatch for downstream compatibility work. |
| Blind 4: integral floating-point paging | medium | defer | Both versions accept `pageSize: 1.0`; unchanged `run_loopback._call_args` renders it as `--page-size 1.0`. Record the pre-existing runner representation mismatch. |
| Blind 5: boolean paging expectation equals integer input | medium | defer | Both versions accept expected `true` for supplied page size 1 because the unchanged comparison uses Python equality. Record the pre-existing request-consistency defect. |
| Blind 6: cursor length measurement | medium | defer | Both versions accept 3,000 supplementary Unicode characters; Core checks UTF-16 `string.Length` against 4096. The schema's code-point maximum predates this change. |
| Blind 7: fixed extension restrictions absent | medium | defer | Both versions accept 33 matching extensions; the unchanged runtime validator rejects more than 32 and enforces key/content/length/byte limits. The new supplied-extension equality check does not introduce this gap. |
| Blind 8: invented optional request fields | medium | defer | Baseline and reviewed versions both accept expected extensions without supplied extensions and expected paging without paging inputs. Record the existing absence-consistency gap. |
| Blind 9: wrong-kind expected request fields | medium | defer | Both versions accept a query expectation containing `idempotencyKey`, which the query request construction never emits. The open request-body schema and missing field-kind check predate this work. |
| Blind 10: invalid entity routing | medium | defer | Both versions accept entity ID `/`; `RoutingResolver.IsAggregateId` and the executor reject it. Record the pre-existing fixed-routing compatibility gap, independently of Module identifier kinds. |
| Edge 1: parser/traversal limits escape | medium | patch (grouped with Blind 1) | The same executable parser-limit and new finite-traversal reproductions confirm this claim. One exception-boundary correction covers both findings. |
| Edge 2: nested duplicate location is root | low | reject | The same nested duplicate reproduction confirms the diagnostic limitation; source and offending key remain available. Additional object-pair traversal is disproportionate to this uncommon refinement. |
| Edge 3: boolean paging expectation equals integer input | medium | defer (grouped with Blind 5) | Both baseline and reviewed implementations accept the supplied page size 1 / expected `true` reproduction. One deferred entry records the shared Python-equality defect. |
| Verification 1: malformed JSON diagnostic coverage missing | medium | patch | The reviewer removed `JSONDecodeError` handling in isolation and all original 41 tests still passed. Add raw truncated/trailing-comma JSON plus parser-limit cases, checking source/root/reason, identical CLI stderr, exit 1, and no traceback. |


### Follow-up review triage (2026-09-27)

All three independent layers completed. The edge-case layer returned no findings; the blind layer returned ten and the verification layer one. Each finding is classified separately below before grouping. Baseline probes used `9b3b099bf117eac880b9b6e12422990a168519eb` in temporary files.

| Finding | Verdict | Route | Evidence and disposition |
| --- | --- | --- | --- |
| Follow-up Blind 1: missing query projection request fields | medium | patch | Both versions accept Command expectations containing `projectionType` or `projectionActorType`, which `SubmitCommandRequest` cannot emit. This exposes an omission in the newly added known wrong-kind check; complete its tuple and existing every-position tests. |
| Follow-up Blind 2: invented query entity ID | medium | patch | Both versions accept an expected `entityId` with no envelope input; `OperationExecutor` passes `run.EntityId` directly. Complete the new absent-input consistency checks with this proven optional field and regression cases. |
| Follow-up Blind 3: unknown nuspec XML encoding | low | reject | Both versions raise `LookupError` for a fabricated root nuspec declaring `unrecognized-codec`. This pre-existing malformed-artifact case is uncommon for immutable NuGet releases and would add an exception guard; it does not block this patch. |
| Follow-up Blind 4: approval example masks validator failure | medium | patch | The new README block runs hashing after validation unconditionally; a shell without `set -e` returns the successful hash command's status after rejection. Chain the commands with `&&` and verify both outcomes. |
| Follow-up Blind 5: cursor UTF-16 limit | medium | defer (carried) | Carried: same claim and unchanged code as prior Blind 6. Keep the existing downstream entry; do not duplicate it. |
| Follow-up Blind 6: fixed extension restrictions | medium | defer (carried) | Carried: same claim and unchanged code as prior Blind 7. Keep the existing downstream entry; do not duplicate it. |
| Follow-up Blind 7: routing grammar | medium | defer (carried) | Carried: same claim and unchanged code as prior Blind 10. Keep the existing downstream entry; do not duplicate it. |
| Follow-up Blind 8: lowercase ULID compatibility | medium | defer | Both baseline and current patterns require uppercase. The review's pinned ByteAether.Ulid probe accepts lowercase. Preserve the existing v1 pattern in this patch; record the pre-existing parser/contract difference for downstream compatibility. |
| Follow-up Blind 9: numeric underflow | medium | defer | Both versions accept raw `1e-400` after Python JSON parsing produces `0.0`; the unchanged runner parses and serializes again. This is pre-existing numeric representation behavior; runner representation changes are excluded by the frozen intent. |
| Follow-up Blind 10: Payload depth compatibility | medium | defer | Both versions accept 65 nested arrays; Core uses `JsonDocument.Parse` with default depth and the review reproduced rejection. Runtime Payload compatibility belongs to downstream Story 4.11. |
| Follow-up Verification 1: no automated sample hash assertion | low | reject | The emitted hash is illustrative sample evidence and was independently compared with OpenSSL during this run. No incorrect output was found. Adding a shell execution harness solely for this low-impact output exceeds a direct correction; retain the manual evidence. |

## Verification

- `python3 -m unittest discover -v -s tools/conformance-vectors/v1 -p 'test_*.py'` — exit 0; all 47 tests pass, including every matrix row, CLI/API parity and all call positions. No skips.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh` — exit 0; Debug pack succeeds, all 47 tests pass, all three unchanged vectors validate, and NuGet-compatible `sha512-` evidence is printed.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh Release` — exit 0; Release pack succeeds with the same checks. Both runs build only Sample.Contracts, Abstractions and Analyzers and clean their temporary directories.
- `bash -n tools/conformance-vectors/v1/run-sample-validation.sh` — exit 0. Empty, invalid and extra configuration arguments return exit 2; executable file mode is set. Python hash snippets match an independent OpenSSL SHA-512 calculation.
- The rendered README approval example returns exit 0 and a hash for valid vectors, or exit 1 with no hash for invalid vectors.
- `git diff --check` — exit 0. The existing CI contract and loopback jobs remain independent. Production code, dependencies, sample vectors, runner implementations, submodule pointers and the frozen spec block are unchanged by this follow-up.
- Verification logs: `/tmp/mcpcli-story-1-8-verification.MgS5yY/final-tests.log`, `final-debug.log`, `final-release.log`, `final-shell.log`, `final-diff.log`, and `approval-example.log`.

- Follow-up commit candidate passed pinned `@commitlint/cli` 21.2.2: `npx --no -- commitlint --edit /tmp/mcpcli-story-1-8-commit-vrf575yn.txt --verbose` — exit 0, zero problems and warnings. Exact message and validation output are preserved in `/tmp/mcpcli-story-1-8-commit-vrf575yn.txt` and `/tmp/mcpcli-story-1-8-commit-vrf575yn.validation.log`.

### Prior commit validation

- Commit message `fix: complete conformance vector contract validation` passed the repository's pinned `@commitlint/cli` 21.2.2: `npx --no -- commitlint --edit /tmp/mcpcli-story-1-8-commit-zpz223mf.txt --verbose` returned exit 0, zero problems and zero warnings. Full validation evidence is preserved at `/tmp/mcpcli-story-1-8-commit-zpz223mf.validation.log`.

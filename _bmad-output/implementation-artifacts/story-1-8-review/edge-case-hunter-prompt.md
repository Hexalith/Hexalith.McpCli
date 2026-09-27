Read 

# Edge Case Hunter Review

**Goal:** You are a pure path tracer. Never comment on whether code is good or bad; only list missing handling.
When a diff is provided, scan only the diff hunks and list boundaries that are directly reachable from the changed lines and lack an explicit guard in the diff.
When no diff is provided (full file or function), treat the entire provided content as the scope.
Ignore the rest of the codebase unless the provided content explicitly references external functions.
A brief secondary deletion check runs as Step 4 when the diff removes code.
A claims check runs as Step 5.

**Inputs:**
- **content** — Content to review, or a path to read it from: diff, full file, or function
- **also_consider** (optional) — Areas to keep in mind during review alongside normal edge-case analysis
- **claims_file** — Path to the spec this change was built from. Do NOT read it before Step 5: the path tracing in Steps 2–3 must finish before the claims are seen.

**MANDATORY: Execute steps in the Execution section IN EXACT ORDER. DO NOT skip steps or change the sequence. When a halt condition triggers, follow its specific instruction exactly. Each action within a step is a REQUIRED action to complete that step.**

**Your method is exhaustive path enumeration — mechanically walk every branch, not hunt by intuition. Report ONLY paths and conditions that lack handling — discard handled ones silently. Do NOT editorialize or add filler. Do not assign severity labels, rankings, or priority levels.**


## EXECUTION

### Step 1: Receive Content

- Take the content to review from the parent message that launched you — inline, or by reading the file it points to (never from this instruction file)
- If no content is supplied, or it is empty, unreadable, or cannot be decoded as text, return `[{"location":"N/A","trigger_condition":"Input empty or undecodable","guard_snippet":"Provide valid content to review","potential_consequence":"Review skipped — no analysis performed"}]` and stop
- Identify content type (diff, full file, or function) to determine scope rules

### Step 2: Exhaustive Path Analysis

**Walk every branching path and boundary condition within scope — report only unhandled ones.**

- If `also_consider` input was provided, incorporate those areas into the analysis
- Walk all branching paths: control flow (conditionals, loops, error handlers, early returns) and domain boundaries (where values, states, or conditions transition). Derive the relevant edge classes from the content itself — don't rely on a fixed checklist. Examples: missing else/default, unguarded inputs, off-by-one loops, arithmetic overflow, implicit type coercion, race conditions, timeout gaps
- Consider implicit branches: the diff special-cases or changes the handling of one or more members of a fixed set of values — enums, status codes, sentinels, type tags, flags, value ranges. The rest of the set is implicit branches (e.g. the diff changes the `RED` and `YELLOW` cases of a `RED`/`YELLOW`/`GREEN` enum; `GREEN` is the implicit branch)
- Consider handle lifetime: when the changed code re-checks, re-fetches, or re-validates something it already held — a handle, index, id, pointer — the re-check exists because an intervening call can invalidate it. Identify that call, what it does to the thing held, and what the changed code silently skips when the re-check fails
- For each call site the diff adds or changes — in test files as well as production code — read the callee's declaration and check the call against it: argument count, order, types, and defaults. Report any mismatch
- For each path: determine whether the content handles it
- Collect only the unhandled paths as findings — discard handled ones silently

### Step 3: Validate Completeness

- Revisit every edge class from Step 2 — e.g., missing else/default, null/empty inputs, off-by-one loops, arithmetic overflow, implicit type coercion, race conditions, timeout gaps
- Add any newly found unhandled paths to findings; discard confirmed-handled ones

### Step 4: Deletion Check

If the diff removed or replaced meaningful code (ignore pure renames and whitespace): load `references/deletion-check.md` and follow it.

### Step 5: Claims Check

Load `references/claims-check.md` and follow it.

### Step 6: Present Findings

Output all findings as a single JSON array following the Output Format specification exactly.


## OUTPUT FORMAT

Return ONLY a valid JSON array of objects. Each edge-case finding contains exactly these four fields:

```json
[{
  "location": "file:start-end (or file:line when single line, or file:hunk when exact line unavailable)",
  "trigger_condition": "one-line description (max 15 words)",
  "guard_snippet": "minimal code sketch that closes the gap (single-line escaped string, no raw newlines or unescaped quotes)",
  "potential_consequence": "what could actually go wrong (max 15 words)"
}]
```

No extra text, no explanations, no markdown wrapping. An empty array `[]` is valid when nothing is found. Deletion findings from Step 4 and claim findings from Step 5, if any, go in the same array with the extra fields defined in `references/deletion-check.md` and `references/claims-check.md`.


## HALT CONDITIONS

- If no content is supplied, or it is empty, unreadable, or cannot be decoded as text, return `[{"location":"N/A","trigger_condition":"Input empty or undecodable","guard_snippet":"Provide valid content to review","potential_consequence":"Review skipped — no analysis performed"}]` and stop
<reference path="references/deletion-check.md">
# Deletion Check

Secondary pass for the Edge Case Hunter — runs only when the diff removed meaningful code. Subordinate to the edge-case pass; findings are usually few or none.

For each chunk of removed or replaced code (ignore pure renames and whitespace), ask: did it carry behavior or a contract that the change neither re-established nor intentionally retired? Add a finding for any resulting regression, orphaned reference, or newly-dead code. Skip anything already covered by your edge-case findings.

Append each finding to the same JSON array as the edge-case findings, with the four standard fields plus:

- `kind`: `"deletion"`
- `confidence`: `"high"`, `"medium"`, or `"low"` — these are inferences; rate them

For a deletion finding the standard fields read as: `location` = the removed item; `trigger_condition` = the behavior or contract it enforced; `guard_snippet` = where or how to re-establish it; `potential_consequence` = the regression or orphan.

Add nothing if nothing qualifies.
</reference>
<reference path="references/claims-check.md">
# Claims Check

Final pass for the Edge Case Hunter. Read the claims file named in the message that launched you now, for the first time; the path tracing is finished and the claims cannot steer it retroactively.

It is the spec the change was built from. Read only its `## Intent` and `## Tasks & Acceptance` sections — the claims live there; ignore the rest of the file. The spec is the change's own account of itself: testimony, not evidence — a claim repeated in a code comment is still the same claim, not confirmation. Extract each checkable claim — what the change does, what it preserves, ordering, arithmetic, and parity with existing code ("exactly as X does") — then try to falsify each one against the code you have already traced. Where your trace is not enough to decide, read the code that decides it: the compared-to function, the actual callee, the state the claim assumes.

Append one finding per falsified claim to the same JSON array, with the four standard fields plus:

- `kind`: `"claim"`
- `confidence`: `"high"`, `"medium"`, or `"low"`

For a claim finding the standard fields read as: `location` = where the code contradicts the claim; `trigger_condition` = the claim, quoted or tightly paraphrased; `guard_snippet` = what the code actually does; `potential_consequence` = what goes wrong for someone who believed the claim.

Verified claims produce nothing. Add nothing if nothing is falsified.
</reference>

## CONTENT SOURCE

"Review content:" in the message that launched you gives the content itself or a path to read it from. Read the file when it is a path; either way that is the content under review, and this instruction file never is.


 completely and follow it as your review instructions.

claims_file (leave unread until your instructions call for it): 

---
title: 'Define and Validate the Conformance Vector Contract'
type: 'feature'
created: '2026-09-27'
status: 'in-review'
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

## Implementation Notes

- Hardened the existing v1 schema and shared validator; all three sample vectors remain unchanged. CLI package expectations now also reject an explicitly empty expected package ID.
- Added a sample-only pack/validate gate with temporary build outputs and Debug/Release selection; CI runs it independently from the existing loopback job.
- Verification: all 41 Python tests passed, including the unchanged runner unit tests. Debug and Release sample gates both passed and accepted all three vectors against their packed artifact. Shell syntax, invalid configuration exit 2, temporary cleanup, CI job separation, and diff whitespace checks passed.
- Matrix audit: sample approval is covered by the packed gates and CLI success test; compatibility by artifact/runner ID and exact-version tests; syntax by closed-object, name, ULID, whitespace and nonfinite tests; script consistency by wrong-kind, extensions and echo tests; assertions by operator/pointer/value tests. The full verbose run executed every covering test successfully.
- Production code, upstream repositories, and parity/live implementations are unchanged. Full parity/live execution remains assigned to Stories 4.11/4.13.

## Spec Change Log

## Review Triage Log

## Verification

- `python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'` — all offline validator and existing runner unit tests pass.
- `bash tools/conformance-vectors/v1/run-sample-validation.sh` — packed sample accepted independently.
- Run the same script with its documented Release selection to verify the CI path.
- Inspect CI job separation and repository diff for absence of production or upstream changes.




Review content: the unified diff at 

diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 94ce98f..43db17e 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -40,11 +40,29 @@ jobs:
         uses: actions/setup-dotnet@a98b56852c35b8e3190ac28c8c2271da59106c68 # v6.0.0
         with:
           global-json-file: global.json
-      - name: Validate the shared vector contract
+      - name: Pack and validate the shared vector contract without a Head or Gateway
+        run: |
+          python3 -m venv "$RUNNER_TEMP/mcpcli-vector-venv"
+          source "$RUNNER_TEMP/mcpcli-vector-venv/bin/activate"
+          python3 -m pip install -r tools/conformance-vectors/v1/requirements.txt
+          bash tools/conformance-vectors/v1/run-sample-validation.sh Release
+
+  conformance-vector-loopback:
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
+        with:
+          submodules: false
+      - name: Initialize root-declared Builds submodule
+        run: git submodule update --init -- references/Hexalith.Builds
+      - name: Set up .NET
+        uses: actions/setup-dotnet@a98b56852c35b8e3190ac28c8c2271da59106c68 # v6.0.0
+        with:
+          global-json-file: global.json
+      - name: Install vector runner test tooling
         run: |
           python3 -m venv "$RUNNER_TEMP/mcpcli-vector-venv"
           "$RUNNER_TEMP/mcpcli-vector-venv/bin/python" -m pip install -r tools/conformance-vectors/v1/requirements.txt
-          "$RUNNER_TEMP/mcpcli-vector-venv/bin/python" -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'
       - name: Run packaged Contracts through CLI and MCP against reset Gateway replay
         run: |
           source "$RUNNER_TEMP/mcpcli-vector-venv/bin/activate"
diff --git a/_bmad-output/implementation-artifacts/sprint-status.yaml b/_bmad-output/implementation-artifacts/sprint-status.yaml
index aa32e1c..8655960 100644
--- a/_bmad-output/implementation-artifacts/sprint-status.yaml
+++ b/_bmad-output/implementation-artifacts/sprint-status.yaml
@@ -43,7 +43,7 @@ development_status:
   1-5-diagnose-catalog-declarations: done
   1-6-inspect-description-quality: done
   1-7-warn-on-missing-operation-descriptions-at-build-time: done
-  1-8-define-and-validate-the-conformance-vector-contract: backlog
+  1-8-define-and-validate-the-conformance-vector-contract: in-progress
   epic-1-retrospective: optional
 
   epic-2: backlog
diff --git a/tools/conformance-vectors/v1/README.md b/tools/conformance-vectors/v1/README.md
index 72ab1bf..cb0251f 100644
--- a/tools/conformance-vectors/v1/README.md
+++ b/tools/conformance-vectors/v1/README.md
@@ -1,43 +1,68 @@
 # Conformance vector contract v1
 
-This directory is the McpCli-owned, test-only contract for Module conformance vectors. `schema.json` is closed at every contract-owned object; `payload`, `expectedGateway.body`, and `scriptedResponse.body` remain JSON data supplied by the owning Module. Only `formatVersion: 1` is supported. An incompatible format needs a new versioned directory and an explicit validator update. Production code never loads these files.
+This directory is the McpCli-owned, test-only contract for Module conformance vectors. Only `formatVersion: 1` is supported. `schema.json` and `validate.py` define the same approval rules for authors and runners; production code never loads these files. An incompatible format needs a new versioned directory and an explicit validator update. Tightening validation of malformed v1 inputs does not introduce a new format.
 
-Each vector names one canonical decorated Operation and its owning Contracts **package ID and exact version**. The owning Module repository stores and approves its real vectors. The three `sample-*.json` vectors cover the local synthetic Contracts fixture; they do not enroll a production Module.
+Each vector names one canonical decorated Operation and its owning Contracts **package ID and exact version**. Package IDs compare case-insensitively; versions compare exactly, without case folding or version normalization. A vector approved for one version is stale when its package version changes, even if its Operation Name is reused. The owning Module repository stores and approves its real vectors. The three `sample-*.json` vectors cover the local synthetic Contracts fixture; they do not enroll a production Module.
 
-## Authoring and approval
+## Contract rules
 
-Create a vector using `schema.json` and the synthetic examples. `prerequisites` are generic calls run before the invocation; `postconditions` are generic calls run after it. Every call fixes an Operation, kind, Payload, Envelope, Gateway request expectation, scripted response, and result assertions. Use postcondition Queries to assert the observable effect of a Command without submitting that live Command twice.
+Create a vector using `schema.json` and the synthetic examples. `prerequisites` are generic calls run before the invocation; `postconditions` are generic calls run after it. Every call fixes an Operation, kind, Payload, Envelope, Gateway request expectation, scripted response, and result assertions. The invocation's Operation and kind must match the vector header. Canonical names contain exactly two dot-separated lowercase ASCII alphanumeric kebab-case parts, including digit-leading parts such as `1-module.2-operation`.
 
-`expectedGateway.body` lists fields that the runner must compare against the captured request, including routing, Envelope, submitted Payload, and paging. It is a required-field projection; the runner separately compares complete captured requests from both Heads. The submitted Payload can differ from the input Payload where Core fills or removes envelope-owned properties. `maskGenerated` may name only a generated Command `/messageId` or `/correlationId`, with `<generated>` at that location in the expected body. Caller-supplied identifiers, especially an idempotency key, remain exact. `echoRequestFields` tells the loopback script to copy the selected request identifiers into its response.
+The root, package, call, Envelope, Gateway expectation, scripted response, and assertion objects reject unknown fields. `payload`, `expectedGateway.body`, and `scriptedResponse.body` remain Module-owned JSON data, as do assertion values. Arbitrary fields and nested JSON are allowed there; duplicate JSON keys and nonfinite numbers (`NaN`, `Infinity`, or numeric overflow) are rejected. Required routing strings and supplied tenant, actor, aggregate ID, entity ID, and cursor strings cannot be blank. Caller-supplied correlation and idempotency identifiers use the v1 ULID pattern. Envelope identifiers are independent of the Module's payload Identifier Kind.
 
-Assertion paths are RFC 6901 JSON Pointers into the canonical result document. The operators are `equals` (JSON structural equality), `exists` (boolean), `arrayLength` (nonnegative integer), and `contains` (array member, object field subset, or string fragment). Every call needs at least one assertion. A Command can assert `/status` and a postcondition Query can assert actual `/document` content. Paging cases should request a non-default page size and subsequent cursor and assert contents, not just a successful status.
+`expectedGateway.body` lists fields that the runner must compare against the captured request, including routing, Envelope, submitted Payload, and paging. It is a required-field projection; the runner separately compares complete captured requests from both Heads. The submitted Payload can differ from the input Payload where Core fills or removes envelope-owned properties. Supplied extensions must match the expected request's extensions. Command-only inputs and Query-only inputs cannot be mixed; a Query cannot combine cursor and offset.
 
-Install the **test tooling** dependency with `python3 -m pip install -r tools/conformance-vectors/v1/requirements.txt`. From the repository root, validate against the owning immutable Contracts release artifact before Module maintainer approval:
+`maskGenerated` may name only a generated Command `/messageId` or `/correlationId`, with `<generated>` at that location in the expected body. Caller-supplied identifiers, especially an idempotency key, remain exact. `echoRequestFields` tells the loopback script to copy selected request identifiers into its response: a Command response must echo correlation ID and may echo message ID. A Query has no request identifiers to mask or echo; its response may still contain a scripted correlation ID supplied by the Module.
+
+Assertion paths are RFC 6901 JSON Pointers into the canonical result document; the empty pointer addresses the whole result. The operators are `equals` (JSON structural equality), `exists` (boolean value), `arrayLength` (nonnegative integer value), and `contains` (array member, object field subset, or string fragment). Every assertion requires a value and every call needs at least one assertion. A Command can assert `/status` and a postcondition Query can assert actual `/document` content. Paging cases should request a non-default page size and subsequent cursor and assert contents, not just a successful status.
+
+## Offline sample gate
+
+Install the test tooling dependency with `python3 -m pip install -r tools/conformance-vectors/v1/requirements.txt` (use a virtual environment if required). The repository's pinned .NET SDK and root-declared Builds submodule must be available for packing. From the repository root:
 
 ```sh
-python3 tools/conformance-vectors/v1/validate.py \
-  --artifact /path/to/Owner.Contracts.1.2.3.nupkg \
-  /path/to/module/vectors/*.json
-```
+# Local development defaults to Debug.
+bash tools/conformance-vectors/v1/run-sample-validation.sh
 
-The shared entry point `validate_vectors(paths, artifact, expected_package, expected_operations)` applies the same checks in a runner. Before either runner lane, pass the restored flagged production package ID and exact version with `--expected-package-id` and `--expected-package-version`. A JSON array of canonical Catalog names can be passed with `--operations-file` to reject missing, extra, or duplicate vectors. The loopback runner reads the test host's generated flagged manifest and rejects missing, extra, duplicate, or wrong-kind vectors for the owning package. It also compares the immutable artifact's SHA-512 with the package restored into that host. The validator itself has no production Catalog dependency.
+# The independent conformance-vector-contract CI job uses Release.
+bash tools/conformance-vectors/v1/run-sample-validation.sh Release
+```
 
-For the complete local sample gate, run `bash tools/conformance-vectors/v1/run-sample-loopback.sh`. It packs the sample and Abstractions into a temporary feed, restores the test-only host into an isolated NuGet cache, builds it, runs the validator tests, and executes all three vectors through separate CLI and MCP stdio processes. The generated manifest contains only the flagged sample package; production source and its package manifest stay unchanged. The test host invokes the actual CLI/MCP composition through a reflection adapter because the sample package is intentionally absent from the production tool.
+The script packs only the sample Contracts project and builds its dependencies, runs the offline validator and existing runner unit tests, then validates all three examples against the packed `Hexalith.McpCli.Sample.Contracts` version `1.0.0` artifact and expected identity. It prints the result and artifact SHA-256, exits 0 on success, and cleans only its own temporary artifact/build directory. It builds neither Head and needs no Gateway or AppHost. Packing may restore build dependencies from NuGet; “offline” means validation and unit tests need no network service or running application.
 
-The equivalent validator-only check against an already packed sample artifact is:
+For the focused Python checks alone:
 
 ```sh
-dotnet pack tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj --configuration Release -p:IsPackable=true -p:Version=1.0.0 --output /tmp/mcpcli-conformance-pack
-python3 tools/conformance-vectors/v1/validate.py \
-  --artifact /tmp/mcpcli-conformance-pack/Hexalith.McpCli.Sample.Contracts.1.0.0.nupkg \
-  --expected-package-id Hexalith.McpCli.Sample.Contracts \
-  --expected-package-version 1.0.0 \
-  tools/conformance-vectors/v1/sample-command.json \
-  tools/conformance-vectors/v1/sample-query.json \
-  tools/conformance-vectors/v1/sample-rename.json
 python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'
 ```
 
-`run_loopback.py` drives both Heads out of process. For every vector it compares discovery documents, invokes each prerequisite, invocation, and postcondition against separately reset HTTP response scripts, checks semantic result assertions, compares complete captured Gateway requests and their required fields, and checks malformed-Payload error parity without a Gateway request. Only generated Command message and correlation ULIDs are masked; caller-supplied values remain exact. Run it once per owning package, supplying all of that package's vectors and the host containing its flagged Contracts release.
+## Module author approval
+
+1. Store the vector set in the owning Module repository and name the immutable owning Contracts `.nupkg` package ID and exact version in every vector. Use postcondition Queries to assert a Command's observable effect without submitting that live Command twice.
+2. Obtain that immutable artifact and run the shared validator against it. No Head, Catalog assembly loading, Gateway, or AppHost is required for author approval:
+
+   ```sh
+   python3 tools/conformance-vectors/v1/validate.py \
+     --artifact /path/to/Owner.Contracts.1.2.3.nupkg \
+     --expected-package-id Owner.Contracts \
+     --expected-package-version 1.2.3 \
+     /path/to/module/vectors/*.json
+   sha256sum /path/to/Owner.Contracts.1.2.3.nupkg
+   ```
+
+3. Resolve every finding and rerun until exit 0. Invalid or incompatible vectors exit 1, with source, location, and reason diagnostics. CLI usage errors exit 2. Package identity comes from the artifact's root `.nuspec`, never a project file.
+4. Record maintainer approval with `formatVersion: 1`, the vector repository revision, validator revision, owning package ID and exact version, immutable artifact location and SHA-256, exact validation command, successful output/exit code, and approving maintainer. Keep the artifact available for downstream checks; the temporary sample artifact is illustrative evidence only.
+
+Approval establishes format, script consistency, and artifact identity compatibility. It does not establish that an Operation exists in the owning Catalog, that its kind or Payload matches the decorated Contracts schema, or that a handler produces the scripted semantic result. Those checks belong to the downstream gates below.
+
+## Runner handoff
+
+The reusable entry point `validate_vectors(paths, artifact, expected_package, expected_operations)` applies the same schema, consistency, and artifact checks as the CLI. A JSON array of canonical Catalog names can be passed with `--operations-file` to reject missing, extra, or duplicate vectors. The validator itself has no production Catalog dependency.
+
+**Story 4.11** owns production restored-package rechecks and deterministic cross-head parity. Before execution, the runner supplies the restored flagged production package ID and exact version to the shared validator (`--expected-package-id` and `--expected-package-version` on the CLI), checks coverage and kinds against the owning Catalog, and checks Payload compatibility. It must also verify that the immutable artifact matches the package restored into the host. This catches a stale approval after a package update.
+
+The existing sample parity gate remains available independently as `bash tools/conformance-vectors/v1/run-sample-loopback.sh`, and CI retains it in the separate `conformance-vector-loopback` job. It packs the sample and Abstractions into a temporary feed, restores the test-only host into an isolated NuGet cache, builds it, runs the validator tests, and executes all three vectors through separate CLI and MCP stdio processes. The generated manifest contains only the flagged sample package; production source and its package manifest stay unchanged. The test host invokes the actual CLI/MCP composition through a reflection adapter because the sample package is intentionally absent from the production tool. The runner compares the immutable artifact's SHA-512 with the package restored into that host.
+
+`run_loopback.py` drives both Heads out of process. For every vector it compares discovery documents, invokes each prerequisite, invocation, and postcondition against separately reset HTTP response scripts, checks semantic result assertions, compares complete captured Gateway requests and their required fields, and checks malformed-Payload error parity without a Gateway request. Only generated Command message and correlation ULIDs are masked; caller-supplied values remain exact. Run it once per owning package, supplying all of that package's vectors and the host containing its flagged Contracts release. Passing offline author approval does not require running this parity gate.
 
-The once-per-vector live Aspire semantic lane remains a separate AD-16 gate. The synthetic sample's scripted Query response illustrates assertions; it does not prove a real handler's persistent effect.
+**Story 4.13** owns the separate live EventStore/Aspire semantic lane. It rechecks the approved vectors against the restored owning package using the shared validator, runs each vector once, and verifies actual Query contents and persistent Command effects. The synthetic sample's scripted Query response illustrates assertions; it does not prove a real handler's persistent effect. Live Commands are not submitted twice solely for cross-head byte equality.
diff --git a/tools/conformance-vectors/v1/schema.json b/tools/conformance-vectors/v1/schema.json
index 64f7208..c9452fe 100644
--- a/tools/conformance-vectors/v1/schema.json
+++ b/tools/conformance-vectors/v1/schema.json
@@ -20,30 +20,31 @@
       "additionalProperties": false,
       "required": ["id", "version"],
       "properties": {
-        "id": { "type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]*$" },
-        "version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(?:\\.[0-9]+)?(?:-[0-9A-Za-z.-]+)?$" }
+        "id": { "type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]*(?![\\s\\S])" },
+        "version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(?:\\.[0-9]+)?(?:-[0-9A-Za-z.-]+)?(?![\\s\\S])" }
       }
     },
-    "operation": { "type": "string", "pattern": "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:\\.[a-z][a-z0-9]*(?:-[a-z0-9]+)*)+$" },
+    "operation": { "type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*\\.[a-z0-9]+(?:-[a-z0-9]+)*(?![\\s\\S])" },
     "kind": { "enum": ["command", "query"] },
+    "nonblank": { "type": "string", "minLength": 1, "pattern": "\\S" },
     "envelope": {
       "type": "object",
       "additionalProperties": false,
       "required": ["tenant"],
       "properties": {
-        "tenant": { "type": "string", "minLength": 1 },
-        "actor": { "type": "string", "minLength": 1 },
-        "aggregateId": { "type": "string", "minLength": 1 },
-        "entityId": { "type": "string", "minLength": 1 },
+        "tenant": { "$ref": "#/$defs/nonblank" },
+        "actor": { "$ref": "#/$defs/nonblank" },
+        "aggregateId": { "$ref": "#/$defs/nonblank" },
+        "entityId": { "$ref": "#/$defs/nonblank" },
         "correlationId": { "$ref": "#/$defs/ulid" },
         "idempotencyKey": { "$ref": "#/$defs/ulid" },
         "pageSize": { "type": "integer", "minimum": 1, "maximum": 200 },
         "offset": { "type": "integer", "minimum": 0 },
-        "cursor": { "type": "string", "minLength": 1, "maxLength": 4096 },
+        "cursor": { "$ref": "#/$defs/nonblank", "maxLength": 4096 },
         "extensions": { "type": "object", "additionalProperties": { "type": "string" } }
       }
     },
-    "ulid": { "type": "string", "pattern": "^[0-7][0-9A-HJKMNP-TV-Z]{25}$" },
+    "ulid": { "type": "string", "pattern": "^[0-7][0-9A-HJKMNP-TV-Z]{25}(?![\\s\\S])" },
     "gateway": {
       "type": "object",
       "additionalProperties": false,
@@ -78,7 +79,7 @@
       "additionalProperties": false,
       "required": ["path", "operator"],
       "properties": {
-        "path": { "type": "string", "pattern": "^(?:/(?:[^~/]|~0|~1)*)*$" },
+        "path": { "type": "string", "pattern": "^(?:/(?:[^~/]|~0|~1)*)*(?![\\s\\S])" },
         "operator": { "enum": ["equals", "exists", "arrayLength", "contains"] },
         "value": {}
       },
diff --git a/tools/conformance-vectors/v1/test_validate.py b/tools/conformance-vectors/v1/test_validate.py
index ff8b060..84d690c 100644
--- a/tools/conformance-vectors/v1/test_validate.py
+++ b/tools/conformance-vectors/v1/test_validate.py
@@ -4,6 +4,8 @@ from __future__ import annotations
 
 import copy
 import json
+import subprocess
+import sys
 import tempfile
 import unittest
 import zipfile
@@ -14,6 +16,7 @@ from validate import validate_vectors
 
 HERE = Path(__file__).parent
 PACKAGE = ("Hexalith.McpCli.Sample.Contracts", "1.0.0")
+POSITIONS = ("invocation", "prerequisites", "postconditions")
 
 
 class VectorContractTests(unittest.TestCase):
@@ -43,6 +46,20 @@ class VectorContractTests(unittest.TestCase):
         findings = self._validate(document)
         self.assertTrue(any(fragment in finding for finding in findings), findings)
 
+    def _step_at(self, template: dict, position: str) -> tuple[dict, dict, str]:
+        document = copy.deepcopy(template)
+        if position == "invocation":
+            return document, document["invocation"], "/invocation"
+        document[position] = [copy.deepcopy(template["invocation"])]
+        return document, document[position][0], f"/{position}/0"
+
+    def _cli(self, paths: list[Path], expected: tuple[str, str] = PACKAGE) -> subprocess.CompletedProcess:
+        return subprocess.run(
+            [sys.executable, str(HERE / "validate.py"), "--artifact", str(self.artifact),
+             "--expected-package-id", expected[0], "--expected-package-version", expected[1],
+             *map(str, paths)], capture_output=True, text=True, check=False,
+        )
+
     def test_synthetic_command_and_query_are_compatible_with_release_and_catalog(self) -> None:
         paths = [HERE / "sample-command.json", HERE / "sample-query.json", HERE / "sample-rename.json"]
         self.assertEqual([], validate_vectors(paths, self.artifact, PACKAGE,
@@ -72,7 +89,7 @@ class VectorContractTests(unittest.TestCase):
         self.command["invocation"]["expectedGateway"]["body"]["payload"]["Tenant"] = "sample-tenant"
         self.assertEqual([], self._validate(self.command))
 
-    def test_caller_idempotency_key_cannot_be_masked(self) -> None:
+    def test_caller_correlation_id_cannot_be_masked(self) -> None:
         self.command["invocation"]["expectedGateway"]["maskGenerated"].append("/correlationId")
         self._assert_rejected(self.command, "caller-supplied correlationId cannot be masked")
 
@@ -100,6 +117,284 @@ class VectorContractTests(unittest.TestCase):
         findings = validate_vectors([source], self.artifact)
         self.assertTrue(any("duplicate JSON field 'formatVersion'" in finding for finding in findings), findings)
 
+    def test_contract_owned_objects_are_closed_at_every_call_position(self) -> None:
+        for field in (None, "package"):
+            with self.subTest(field=field):
+                document = copy.deepcopy(self.command)
+                target = document if field is None else document[field]
+                target["unknown"] = True
+                self._assert_rejected(document, "/unknown" if field is None else f"/{field}/unknown")
+        for position in POSITIONS:
+            for field in (None, "envelope", "expectedGateway", "scriptedResponse", "assertions"):
+                with self.subTest(position=position, field=field):
+                    document, step, pointer = self._step_at(self.command, position)
+                    target = step if field is None else step[field]
+                    if field == "assertions":
+                        target = target[0]
+                    target["unknown"] = True
+                    suffix = "" if field is None else "/" + field + ("/0" if field == "assertions" else "")
+                    self._assert_rejected(document, f"{pointer}{suffix}/unknown")
+
+    def test_operation_names_reject_malformed_parts_at_every_call_position(self) -> None:
+        for name in ("sample", "sample.get.item", "Sample.get-item", "sample.get_item",
+                     ".get-item", "sample.", "-sample.get-item", "sample.get-item-",
+                     "sample.get--item", "sample.get-item\n", "sample.get-item\r\n", " sample.get-item"):
+            for position in POSITIONS:
+                with self.subTest(name=name, position=position):
+                    document, step, pointer = self._step_at(self.command, position)
+                    step["operation"] = name
+                    self._assert_rejected(document, f"{pointer}/operation")
+            document = copy.deepcopy(self.command)
+            document["operation"] = name
+            self._assert_rejected(document, "/operation")
+
+    def test_digit_leading_and_single_character_operation_parts_are_valid(self) -> None:
+        for name in ("0.1", "a.b", "1-sample.2-get-item", "sample1.get-item2"):
+            with self.subTest(name=name):
+                document = copy.deepcopy(self.command)
+                document["operation"] = document["invocation"]["operation"] = name
+                self.assertEqual([], self._validate(document))
+
+    def test_package_patterns_require_complete_strings(self) -> None:
+        for field, values in (
+            ("id", ("", " ", PACKAGE[0] + "\n", "-Owner.Contracts", "Owner/Contracts")),
+            ("version", ("", " ", "1.0", "1.0.0\n", "1.0.0\r\n", "v1.0.0")),
+        ):
+            for value in values:
+                with self.subTest(field=field, value=value):
+                    document = copy.deepcopy(self.command)
+                    document["package"][field] = value
+                    self._assert_rejected(document, f"/package/{field}")
+
+    def test_nonblank_envelope_strings_at_every_call_position(self) -> None:
+        for position in POSITIONS:
+            for field in ("tenant", "actor", "aggregateId", "entityId", "cursor"):
+                for value in ("", " \t\r\n", "\u2003"):
+                    with self.subTest(position=position, field=field, value=value):
+                        document, step, pointer = self._step_at(self.query, position)
+                        step["envelope"][field] = value
+                        self._assert_rejected(document, f"{pointer}/envelope/{field}")
+
+    def test_nonblank_gateway_routing_at_every_call_position(self) -> None:
+        for template in (self.command, self.query):
+            for position in POSITIONS:
+                for field in ("domain", "aggregateId", "commandType" if template["kind"] == "command" else "queryType"):
+                    for value in (None, False, 42, "", " \t\n", "\u2003"):
+                        with self.subTest(kind=template["kind"], position=position, field=field, value=value):
+                            document, step, pointer = self._step_at(template, position)
+                            step["expectedGateway"]["body"][field] = value
+                            self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}: required nonblank")
+
+    def test_ulids_reject_invalid_alphabet_overflow_and_trailing_newlines(self) -> None:
+        for position in POSITIONS:
+            for field in ("correlationId", "idempotencyKey"):
+                for value in ("", "01J9MZHXT3RKM0VWXRXGSJDATK\n", "8" + "0" * 25,
+                              "0" * 25, "0" * 27, "0" * 25 + "I", "0" * 25 + "O", "0" * 25 + "U"):
+                    with self.subTest(position=position, field=field, value=value):
+                        document, step, pointer = self._step_at(self.command, position)
+                        step["envelope"][field] = value
+                        self._assert_rejected(document, f"{pointer}/envelope/{field}")
+
+    def test_ulid_and_paging_boundaries_are_valid(self) -> None:
+        for value in ("0" * 26, "7" + "Z" * 25):
+            document = copy.deepcopy(self.command)
+            for field in ("correlationId", "idempotencyKey"):
+                document["invocation"]["envelope"][field] = value
+                document["invocation"]["expectedGateway"]["body"][field] = value
+            self.assertEqual([], self._validate(document))
+        for paging in ({"pageSize": 1, "offset": 0}, {"pageSize": 200, "cursor": "x" * 4096}):
+            document = copy.deepcopy(self.query)
+            document["invocation"]["envelope"].update(paging)
+            document["invocation"]["expectedGateway"]["body"]["paging"] = paging
+            self.assertEqual([], self._validate(document))
+
+    def test_paging_outside_bounds_is_rejected(self) -> None:
+        for field, values in (("pageSize", (0, 201, True)), ("offset", (-1, True)), ("cursor", ("x" * 4097,))):
+            for value in values:
+                with self.subTest(field=field, value=value):
+                    document = copy.deepcopy(self.query)
+                    document["invocation"]["envelope"][field] = value
+                    self._assert_rejected(document, f"/invocation/envelope/{field}")
+
+    def test_nonfinite_json_is_rejected_with_escaped_locations_in_all_data_areas(self) -> None:
+        for position in POSITIONS:
+            for area in ("payload", "expectedGateway", "scriptedResponse", "assertions"):
+                for number in ("NaN", "Infinity", "-Infinity", "1e400", "-1e400"):
+                    with self.subTest(position=position, area=area, number=number):
+                        document, step, pointer = self._step_at(self.command, position)
+                        if area == "assertions":
+                            target = step[area][0]
+                            target["value"] = ["NONFINITE"]
+                            suffix = "/assertions/0/value/0"
+                        else:
+                            target = step[area] if area == "payload" else step[area]["body"]
+                            target["odd~/field"] = ["NONFINITE"]
+                            suffix = f"/{area}" + ("" if area == "payload" else "/body") + "/odd~0~1field/0"
+                        source = self._write(document)
+                        source.write_text(source.read_text(encoding="utf-8").replace('"NONFINITE"', number), encoding="utf-8")
+                        findings = validate_vectors([source], self.artifact, PACKAGE)
+                        self.assertTrue(any(f"{source}:{pointer}{suffix}: nonfinite JSON number" in item for item in findings), findings)
+
+    def test_module_owned_json_remains_open_and_preserves_finite_values(self) -> None:
+        document = copy.deepcopy(self.command)
+        step = document["invocation"]
+        data = {"unfamiliar": [None, True, False, -1, 1.25, 1e300, "NaN", {"~name/": ""}]}
+        step["payload"]["custom"] = data
+        step["expectedGateway"]["body"]["custom"] = data
+        step["scriptedResponse"]["body"]["custom"] = data
+        step["assertions"].append({"path": "", "operator": "equals", "value": data})
+        self.assertEqual([], self._validate(document))
+
+    def test_wrong_kind_inputs_at_every_call_position(self) -> None:
+        cases = (
+            (self.command, {"entityId": "entity", "pageSize": 1, "offset": 0, "cursor": "next"}),
+            (self.query, {"correlationId": "0" * 26, "idempotencyKey": "0" * 26, "extensions": {}}),
+        )
+        for template, fields in cases:
+            for position in POSITIONS:
+                for field, value in fields.items():
+                    with self.subTest(kind=template["kind"], position=position, field=field):
+                        document, step, pointer = self._step_at(template, position)
+                        step["envelope"][field] = value
+                        self._assert_rejected(document, f"{pointer}/envelope/{field}")
+
+    def test_supplied_extensions_must_match_expected_request_at_every_call_position(self) -> None:
+        for position in POSITIONS:
+            for expected in (None, {}, {"custom": "different"}, {"custom": 1}, {"custom": "value"}):
+                with self.subTest(position=position, expected=expected):
+                    document, step, pointer = self._step_at(self.command, position)
+                    step["envelope"]["extensions"] = {"custom": "value"}
+                    if expected is not None:
+                        step["expectedGateway"]["body"]["extensions"] = expected
+                    if expected == {"custom": "value"}:
+                        self.assertEqual([], self._validate(document))
+                    else:
+                        self._assert_rejected(document, f"{pointer}/expectedGateway/body/extensions")
+
+    def test_query_response_cannot_echo_request_identifiers_at_every_call_position(self) -> None:
+        for position in POSITIONS:
+            for fields in (["messageId"], ["correlationId"], ["messageId", "correlationId"]):
+                with self.subTest(position=position, fields=fields):
+                    document, step, pointer = self._step_at(self.query, position)
+                    step["scriptedResponse"]["echoRequestFields"] = fields
+                    self._assert_rejected(document, f"{pointer}/scriptedResponse/echoRequestFields: query request")
+
+    def test_existing_script_consistency_rules_apply_at_every_call_position(self) -> None:
+        for position in POSITIONS:
+            for field, value in (("tenant", "wrong"), ("payload", []), ("correlationId", "0" * 26),
+                                 ("idempotencyKey", "0" * 26), ("messageId", "0" * 26)):
+                with self.subTest(position=position, field=field):
+                    document, step, pointer = self._step_at(self.command, position)
+                    step["expectedGateway"]["body"][field] = value
+                    self._assert_rejected(document, f"{pointer}/expectedGateway/body/{field}")
+            document, step, pointer = self._step_at(self.command, position)
+            step["scriptedResponse"]["echoRequestFields"] = []
+            self._assert_rejected(document, f"{pointer}/scriptedResponse/echoRequestFields")
+            document, step, pointer = self._step_at(self.query, position)
+            step["expectedGateway"]["body"]["paging"] = {"pageSize": 10}
+            self._assert_rejected(document, f"{pointer}/expectedGateway/body/paging")
+
+    def test_assertion_operators_paths_and_values_at_every_call_position(self) -> None:
+        invalid = (
+            {"path": "/status", "operator": "execute", "value": "accepted"},
+            {"path": "status", "operator": "equals", "value": "accepted"},
+            {"path": "/bad~2escape", "operator": "equals", "value": 1},
+            {"path": "/trailing~", "operator": "equals", "value": 1},
+            {"path": "\n", "operator": "equals", "value": 1},
+            {"path": "/status", "operator": "exists", "value": "true"},
+            {"path": "/status", "operator": "exists", "value": 1},
+            {"path": "/status", "operator": "arrayLength", "value": -1},
+            {"path": "/status", "operator": "arrayLength", "value": 1.5},
+            {"path": "/status", "operator": "arrayLength", "value": True},
+            *({"path": "", "operator": operator} for operator in ("equals", "contains", "exists", "arrayLength")),
+        )
+        for position in POSITIONS:
+            for assertion in invalid:
+                with self.subTest(position=position, assertion=assertion):
+                    document, step, pointer = self._step_at(self.command, position)
+                    step["assertions"] = [assertion]
+                    self._assert_rejected(document, f"{pointer}/assertions/0")
+
+    def test_valid_assertion_boundaries(self) -> None:
+        self.command["invocation"]["assertions"] = [
+            {"path": "", "operator": "equals", "value": None},
+            {"path": "/", "operator": "exists", "value": False},
+            {"path": "/a~1b/~0/0", "operator": "arrayLength", "value": 0},
+            {"path": "/line\n", "operator": "contains", "value": {"field": [True, 1]}},
+        ]
+        self.assertEqual([], self._validate(self.command))
+
+    def test_package_ids_are_case_insensitive_for_vectors_artifacts_and_runners(self) -> None:
+        self.command["package"]["id"] = PACKAGE[0].lower()
+        self.assertEqual([], self._validate(self.command, (PACKAGE[0].upper(), PACKAGE[1])))
+
+    def test_package_id_and_exact_version_mismatches_are_rejected(self) -> None:
+        for field, value in (("id", "Other.Contracts"), ("version", "1.0.1"), ("version", "1.0.0.0")):
+            with self.subTest(field=field):
+                document = copy.deepcopy(self.command)
+                document["package"][field] = value
+                self._assert_rejected(document, "/package: vector")
+        for expected in (("Other.Contracts", "1.0.0"), (PACKAGE[0], "1.0.1")):
+            findings = self._validate(self.command, expected)
+            self.assertTrue(any(f"{self.artifact}:/metadata:" in item for item in findings), findings)
+        self.artifact = self._package(PACKAGE[0], "1.0.0-RC")
+        self.command["package"]["version"] = "1.0.0-rc"
+        self._assert_rejected(self.command, "/package: vector")
+
+    def test_vector_header_must_match_invocation(self) -> None:
+        for field, value in (("operation", "sample.other"), ("kind", "query")):
+            document = copy.deepcopy(self.command)
+            document[field] = value
+            self._assert_rejected(document, "/invocation: operation and kind must match")
+
+    def test_unsupported_format_values_and_missing_version_are_rejected(self) -> None:
+        for version in (0, -1, 2, "1", True, None):
+            with self.subTest(version=version):
+                document = copy.deepcopy(self.command)
+                document["formatVersion"] = version
+                self._assert_rejected(document, "/formatVersion")
+        del self.command["formatVersion"]
+        self._assert_rejected(self.command, "'formatVersion' is a required property")
+
+    def test_unreadable_or_invalid_artifact_is_reported_without_loading_assemblies(self) -> None:
+        self.artifact.write_bytes(b"not a zip")
+        self._assert_rejected(self.command, "cannot read NuGet release artifact")
+        with zipfile.ZipFile(self.artifact, "w") as archive:
+            archive.writestr("nested/sample.nuspec", "<package/>")
+        self._assert_rejected(self.command, "expected exactly one root .nuspec")
+
+    def test_cli_accepts_all_three_samples(self) -> None:
+        result = self._cli([HERE / "sample-command.json", HERE / "sample-query.json", HERE / "sample-rename.json"])
+        self.assertEqual(0, result.returncode, result.stderr)
+        self.assertIn("Validated 3 vector(s)", result.stdout)
+        self.assertEqual("", result.stderr)
+
+    def test_cli_and_reusable_entry_point_return_identical_located_rejections(self) -> None:
+        cases = []
+        malformed = copy.deepcopy(self.command)
+        malformed["postconditions"][0]["scriptedResponse"]["echoRequestFields"] = ["messageId"]
+        cases.append((malformed, PACKAGE))
+        unsupported = copy.deepcopy(self.command)
+        unsupported["formatVersion"] = 2
+        cases.append((unsupported, PACKAGE))
+        nonfinite = copy.deepcopy(self.command)
+        nonfinite["invocation"]["payload"]["amount"] = float("nan")
+        cases.append((nonfinite, PACKAGE))
+        incompatible = copy.deepcopy(self.command)
+        incompatible["package"]["id"] = "Other.Contracts"
+        cases.append((incompatible, PACKAGE))
+        cases.append((self.command, (PACKAGE[0], "1.0.1")))
+        cases.append((self.command, ("", PACKAGE[1])))
+        for document, expected in cases:
+            with self.subTest(document=document, expected=expected):
+                source = self._write(document)
+                findings = validate_vectors([source], self.artifact, expected)
+                result = self._cli([source], expected)
+                self.assertEqual(1, result.returncode, result.stderr)
+                self.assertEqual("", result.stdout)
+                self.assertEqual(findings, result.stderr.splitlines())
+                self.assertTrue(all(item.startswith((str(source) + ":/", str(self.artifact) + ":/")) for item in findings), findings)
+
 
 if __name__ == "__main__":
     unittest.main()
diff --git a/tools/conformance-vectors/v1/validate.py b/tools/conformance-vectors/v1/validate.py
index 1164578..3f3dfaf 100644
--- a/tools/conformance-vectors/v1/validate.py
+++ b/tools/conformance-vectors/v1/validate.py
@@ -5,6 +5,7 @@ from __future__ import annotations
 
 import argparse
 import json
+import math
 import re
 import sys
 import zipfile
@@ -34,16 +35,31 @@ def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
     value: dict[str, Any] = {}
     for key, item in pairs:
         if key in value:
-            raise VectorError(f"duplicate JSON field {key!r}")
+            raise VectorError(f"/: duplicate JSON field {key!r}")
         value[key] = item
     return value
 
 
+def _check_finite_json(value: Any, parts: tuple[str | int, ...] = ()) -> None:
+    if isinstance(value, float) and not math.isfinite(value):
+        raise VectorError(f"{_pointer(parts)}: nonfinite JSON number {value!r} is not supported")
+    if isinstance(value, dict):
+        for key, item in value.items():
+            _check_finite_json(item, (*parts, key))
+    elif isinstance(value, list):
+        for index, item in enumerate(value):
+            _check_finite_json(item, (*parts, index))
+
+
 def _load_json(path: Path) -> Any:
     try:
-        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
-    except (OSError, UnicodeError, json.JSONDecodeError, VectorError) as exc:
-        raise VectorError(f"{path}: {exc}") from exc
+        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
+        _check_finite_json(document)
+        return document
+    except VectorError as exc:
+        raise VectorError(f"{path}:{exc}") from exc
+    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
+        raise VectorError(f"{path}:/: {exc}") from exc
 
 
 def package_identity(artifact: Path) -> tuple[str, str]:
@@ -98,11 +114,11 @@ def _check_step(step: dict[str, Any], pointer: str, findings: list[str]) -> None
     if body.get("tenant") != envelope["tenant"]:
         findings.append(f"{pointer}/expectedGateway/body/tenant: must equal envelope tenant")
     for field in ("domain", "aggregateId", "commandType" if kind == "command" else "queryType"):
-        if not isinstance(body.get(field), str) or not body[field]:
-            findings.append(f"{pointer}/expectedGateway/body/{field}: required nonempty Gateway routing value")
+        if not isinstance(body.get(field), str) or not body[field].strip():
+            findings.append(f"{pointer}/expectedGateway/body/{field}: required nonblank Gateway routing value")
     if not isinstance(body.get("payload"), dict):
         findings.append(f"{pointer}/expectedGateway/body/payload: expected submitted Payload object is required")
-    for field in ("aggregateId", "entityId", "idempotencyKey"):
+    for field in ("aggregateId", "entityId", "idempotencyKey", "extensions"):
         if field in envelope and body.get(field) != envelope[field]:
             findings.append(f"{pointer}/expectedGateway/body/{field}: must equal supplied envelope value")
     masks = gateway["maskGenerated"]
@@ -123,6 +139,8 @@ def _check_step(step: dict[str, Any], pointer: str, findings: list[str]) -> None
         findings.append(f"{pointer}/expectedGateway/body/idempotencyKey: absent caller key must remain absent")
     if kind == "command" and "correlationId" not in step["scriptedResponse"]["echoRequestFields"]:
         findings.append(f"{pointer}/scriptedResponse/echoRequestFields: command response must echo request correlationId")
+    if kind == "query" and step["scriptedResponse"]["echoRequestFields"]:
+        findings.append(f"{pointer}/scriptedResponse/echoRequestFields: query request has no identifiers to echo")
     if kind == "query" and any(field in envelope for field in ("pageSize", "offset", "cursor")):
         paging = {field: envelope[field] for field in ("pageSize", "offset", "cursor") if field in envelope}
         if body.get("paging") != paging:
@@ -207,7 +225,7 @@ def main(argv: list[str] | None = None) -> int:
         if not isinstance(operations, list) or not all(isinstance(item, str) for item in operations):
             print(f"{args.operations_file}:/: expected an array of canonical operation names", file=sys.stderr)
             return 1
-    expected = (args.expected_package_id, args.expected_package_version) if args.expected_package_id else None
+    expected = (args.expected_package_id, args.expected_package_version) if args.expected_package_id is not None else None
     findings = validate_vectors(args.vectors, args.artifact, expected, operations)
     if findings:
         print("\n".join(findings), file=sys.stderr)
diff --git a/_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md b/_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md
new file mode 100644
index 0000000..02c84a0
--- /dev/null
+++ b/_bmad-output/implementation-artifacts/spec-1-8-define-and-validate-the-conformance-vector-contract.md
@@ -0,0 +1,82 @@
+---
+title: 'Define and Validate the Conformance Vector Contract'
+type: 'feature'
+created: '2026-09-27'
+status: 'in-review'
+baseline_commit: '9b3b099bf117eac880b9b6e12422990a168519eb'
+route: 'dispatch'
+review_loop_iteration: 0
+context: []
+---
+
+<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">
+
+## Intent
+
+**Problem:** Existing v1 tooling supplies most of Story 1.8, but accepts malformed vectors and presents the later loopback runner as the primary sample gate.
+
+**Approach:** Harden the existing test-only schema and reusable validator, verify the synthetic vectors against a locally packed Contracts artifact, and document the v1 author approval and runner handoff.
+
+## Boundaries & Constraints
+
+**Always:** Retain v1 names, package identity/version, generic calls, Payload/Envelope inputs, request/response expectations, and assertion vocabulary. Close contract-owned objects; preserve Module-owned JSON data and all three samples. Use identical rules for authors and runners, with source/location/reason diagnostics. Compare package IDs case-insensitively and versions exactly.
+
+**Never:** Add production dependencies, Module-specific branches, assembly loading, upstream edits, or publication. Require neither Head, Gateway, nor AppHost. Production restored-package rechecks and parity belong to Story 4.11; live semantics belong to Story 4.13. Runner defects remain outside this story.
+
+## I/O & Edge-Case Matrix
+
+| Scenario | Input / State | Expected Output / Behavior | Error Handling |
+| --- | --- | --- | --- |
+| Author approval | Valid synthetic Command and Query vectors plus packed owning artifact | Accept; CLI exits 0 | No network service needed |
+| Compatibility | Wrong package ID/version, stale runner expectation, unsupported format | Reject; CLI exits 1 | Identify package or format location |
+| Shape and syntax | Unknown contract fields, malformed names/ULIDs, blank required strings, non-JSON numbers | Reject at every call position | Located validation findings |
+| Script consistency | Wrong-kind inputs/echo fields or conflicting supplied extensions | Reject contradictory expectations | Identify offending call field |
+| Assertions | Unknown operator, invalid pointer, missing/wrong typed value | Reject | Assertion location and reason |
+
+</frozen-after-approval>
+
+## Code Map
+
+All tooling paths below are under `tools/conformance-vectors/v1/` unless qualified.
+
+- `schema.json` — operation regex allows extra dots, excludes digit-leading parts, and accepts trailing newlines.
+- `validate.py` — reuse `validate_vectors`, `_check_step`, `package_identity`, and CLI; fix permissive JSON parsing and missing consistency checks.
+- `test_validate.py` — 11 offline tests using temporary nuspec ZIPs; expand negative coverage.
+- `README.md`, `run-sample-loopback.sh` — existing instructions and broader gate; preserve parity semantics.
+- `tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj` — packs with `IsPackable=true`, `Version=1.0.0`; no project edits.
+- `src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs` — naming reference: two dot-separated lowercase alphanumeric kebab-case parts; digit-leading parts allowed. Read only.
+- `.github/workflows/ci.yml` — contract job currently executes loopback too.
+
+## Tasks & Acceptance
+
+**Execution:**
+- [x] `tools/conformance-vectors/v1/schema.json` — align names, enforce strict string boundaries and nonblank inputs, preserve closed fields and assertion operators.
+- [x] `tools/conformance-vectors/v1/validate.py` — reject nonfinite JSON with locations; check nonblank routing, supplied extensions, and query response echoes across all steps.
+- [x] `tools/conformance-vectors/v1/test_validate.py` — cover the matrix, prerequisite/postcondition checks, ID/version mismatches, valid boundaries, and CLI/reusable-entry-point behavior.
+- [x] `tools/conformance-vectors/v1/run-sample-validation.sh` — pack the sample into a temporary directory, run validator tests, validate all three vectors against the artifact and expected identity. Support Debug locally and Release in CI; clean only its temporary files.
+- [x] `.github/workflows/ci.yml` — run the new offline gate independently; retain the existing loopback lane as a separate job.
+- [x] `tools/conformance-vectors/v1/README.md` — record version, compatibility policy, approval procedure, validator invocation, and 4.11/4.13 handoff. Distinguish offline checks from later Catalog/payload compatibility and execution.
+
+**Acceptance Criteria:**
+- Given the existing sample Contracts project, when the standalone offline gate packs and validates its vectors, then all examples pass without building either Head or connecting to a Gateway.
+- Given malformed or incompatible vectors, when authors or runners use the shared validator, then both receive actionable rejections under the same rules.
+- Given the author instructions, when a maintainer prepares approval evidence, then they can identify the version, immutable artifact, validation command/result, and downstream responsibilities without parity or live tests.
+
+## Implementation Notes
+
+- Hardened the existing v1 schema and shared validator; all three sample vectors remain unchanged. CLI package expectations now also reject an explicitly empty expected package ID.
+- Added a sample-only pack/validate gate with temporary build outputs and Debug/Release selection; CI runs it independently from the existing loopback job.
+- Verification: all 41 Python tests passed, including the unchanged runner unit tests. Debug and Release sample gates both passed and accepted all three vectors against their packed artifact. Shell syntax, invalid configuration exit 2, temporary cleanup, CI job separation, and diff whitespace checks passed.
+- Matrix audit: sample approval is covered by the packed gates and CLI success test; compatibility by artifact/runner ID and exact-version tests; syntax by closed-object, name, ULID, whitespace and nonfinite tests; script consistency by wrong-kind, extensions and echo tests; assertions by operator/pointer/value tests. The full verbose run executed every covering test successfully.
+- Production code, upstream repositories, and parity/live implementations are unchanged. Full parity/live execution remains assigned to Stories 4.11/4.13.
+
+## Spec Change Log
+
+## Review Triage Log
+
+## Verification
+
+- `python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'` — all offline validator and existing runner unit tests pass.
+- `bash tools/conformance-vectors/v1/run-sample-validation.sh` — packed sample accepted independently.
+- Run the same script with its documented Release selection to verify the CI path.
+- Inspect CI job separation and repository diff for absence of production or upstream changes.
diff --git a/tools/conformance-vectors/v1/run-sample-validation.sh b/tools/conformance-vectors/v1/run-sample-validation.sh
new file mode 100644
index 0000000..d543d0e
--- /dev/null
+++ b/tools/conformance-vectors/v1/run-sample-validation.sh
@@ -0,0 +1,29 @@
+#!/usr/bin/env bash
+set -euo pipefail
+
+configuration="${1:-Debug}"
+if (( $# > 1 )) || [[ "$configuration" != Debug && "$configuration" != Release ]]; then
+    echo "Usage: bash tools/conformance-vectors/v1/run-sample-validation.sh [Debug|Release]" >&2
+    exit 2
+fi
+
+repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
+task_dir="$(mktemp -d)"
+trap 'rm -rf "$task_dir"' EXIT
+cd "$repo_root"
+
+artifact_dir="$task_dir/feed"
+dotnet pack tests/Hexalith.McpCli.Sample.Contracts/Hexalith.McpCli.Sample.Contracts.csproj \
+    --configuration "$configuration" --artifacts-path "$task_dir/artifacts" \
+    -p:IsPackable=true -p:Version=1.0.0 --output "$artifact_dir" -m:1
+
+python3 -m unittest discover -s tools/conformance-vectors/v1 -p 'test_*.py'
+artifact="$artifact_dir/Hexalith.McpCli.Sample.Contracts.1.0.0.nupkg"
+python3 tools/conformance-vectors/v1/validate.py \
+    --artifact "$artifact" \
+    --expected-package-id Hexalith.McpCli.Sample.Contracts \
+    --expected-package-version 1.0.0 \
+    tools/conformance-vectors/v1/sample-command.json \
+    tools/conformance-vectors/v1/sample-query.json \
+    tools/conformance-vectors/v1/sample-rename.json
+sha256sum "$artifact"


. Read that file — it is the content under review.

Do not invoke any skill, and do not spawn subagents of your own — you are the reviewer. If the instruction file is unreadable, report that exact failure and stop. Return your findings as text in your final message; do not route them through any findings-reporting tool the host may offer.

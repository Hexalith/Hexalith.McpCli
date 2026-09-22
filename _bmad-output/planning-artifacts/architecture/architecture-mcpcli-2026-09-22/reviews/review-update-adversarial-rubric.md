# Architecture update: independent rubric and adversarial review

**Verdict:** The spine is mechanically sound and covers the principal architecture dimensions, but two high-severity conflicts keep it from being a stable implementation contract. One is an explicit proposed change to the inherited PRD acceptance gate; the other makes the stated out-of-process test Catalog impossible under the spine's own dependency and manifest rules.

Review target: `../ARCHITECTURE-SPINE.md` (draft, 2026-09-22). Deterministic check: `uv run .agents/skills/bmad-architecture/scripts/lint_spine.py --workspace _bmad-output/planning-artifacts/architecture/architecture-mcpcli-2026-09-22` returned `ok: true`, zero findings. This is a semantic review; no spine edits were made.

## High findings

### H1. AD-16 changes the inherited live acceptance contract without approval

**Evidence.** The PRD's FR-20 requires **both Heads to submit every Operation** to a running EventStore and requires the result documents to be equal (`prd.md:395-397`). SM-4 repeats the same-topology parity requirement for every Operation (`prd.md:506`). The spine's AD-16 instead sends every Operation through both Heads against a reset loopback HTTP Gateway, then makes **one** live submission per vector without comparing two live results (`ARCHITECTURE-SPINE.md:146-150`). The spine itself acknowledges this as `[ASSUMPTION]` and requests PRD owner confirmation (`:318-319`, `:325-327`). The loopback refinement makes the parity test executable, but does not resolve this source-contract conflict.

**Adversarial construction.** Team A implements AD-16 and passes a fake parity suite plus one live call per Operation. Team B builds the PRD gate and requires two live Head calls, masking only generated IDs. Both can plausibly say their work is complete, but the release gate disagrees and Team A's v1 is unaccepted by the PRD.

**Disposition: discuss before the integration-harness story closes.** The proposed AD-16 design may be technically better for state-changing Commands, but this is a source-contract amendment, not an architecture-only refinement. Obtain the PRD owner's decision; amend FR-20 and SM-4 if accepted, or revise AD-16 to satisfy them. Keep the open question visible until then.

### H2. The out-of-process test Catalog cannot include `Sample.Contracts` as specified

**Evidence.** AD-16 requires a production-like Catalog containing Tenants, Parties, and the synthetic sample, and its loopback parity lane drives the built `hexalith` CLI process and MCP stdio client against that Catalog (`:146-150`). AD-4 limits the executable's manifest to flagged production Contracts `PackageReference` entries in the tool project (`:73-77`). AD-2 says only the executable references Contracts packages (`:47-51`); AD-15 says the sample is never referenced by `src/` (`:140-144`). AD-3 allows unit tests to pass `Sample.Contracts` directly, but it gives the out-of-process executable no test Catalog injection seam (`:67-71`). The new loopback server supplies Gateway responses, not assemblies, so it does not close this gap.

**Adversarial construction.** A test developer follows the manifest and production dependency rules: the launched tool sees Tenants and Parties only, so sample parity calls return `unknown_operation`. Another developer makes the launched tool see the sample by adding a conditional source/project reference or runtime loading; that weakens the manifest-only or `src/` boundary. Both cannot satisfy all current rules at once.

**Disposition: autofix in the spine.** State that the out-of-process parity lane covers the production manifest's Operations and keep the synthetic sample in isolated in-process Catalog tests; alternatively define a precise test-only executable build/injection seam that is excluded from the shipped tool and still generated from flagged references. Update AD-16's "same Catalog" wording accordingly.

## Medium findings

### M1. Windows profile-file protection is less determinate than the cross-platform promise

**Evidence.** AD-14 requires restrictive permissions at file creation and gives exact `0700`/`0600` rules only for non-Windows; the target and lock must be regular files, not symlinks (`:133-137`). AD-17 publishes a portable framework-dependent tool (`:151-155`), and the spine binds NFR-5 secret handling and NFR-6 portability (`:297-299`). Two Windows implementations could inherit different directory ACLs yet each claim that it created a "restrictive" file.

**Adversarial construction.** One implementation explicitly restricts the profile, temporary file, and lock to the current user; another creates files under an inherited, broader directory ACL. Both pass Unix permission tests and the current prose, but one exposes a stored token to other local principals.

**Disposition: autofix or defer with a named Windows release gate.** Specify the Windows access rule for profile, temporary, and lock files and test it on Windows, or state that Windows support is deferred and narrow the portability claim. This is a boundary invariant because separately built profile-store and packaging work must agree.

### M2. The semantics of an unknown Module in `list_operations` remain open

**Evidence.** AD-5 binds exact result/error records to PRD addendum §G (`:79-83`), but the only lookup error is `unknown_operation`; AD-9 defines that error for descriptor lookup (`:103-107`). Neither AD-3 nor the conventions (`:67-71`, `:183-186`) state what `list_operations` returns for an unknown Module. The PRD/addendum list the operation result shape and error variants but do not resolve that case (`addendum.md:280-282`, `:370-376`).

**Adversarial construction.** The Core Catalog implementer returns `{module: "missing", operations: []}`. Another implementer returns `unknown_operation` with `operation: "missing"`, which violates the documented canonical Operation Name constraint. The heads can each be built compliantly but expose incompatible behavior to callers.

**Disposition: autofix.** Define a single Catalog-level behavior for an unknown Module, ideally the valid empty `list_operations` document or a specifically designed error variant; add one cross-head fixture. Do not overload `unknown_operation` with a noncanonical Module Name.

## Rubric walk

| Check | Assessment |
| --- | --- |
| Real divergence points | Strong boundary rules for package dependencies, manifest discovery, one Core call model, serializer, envelope resolution, settings, and outputs. H2 and M2 remain. |
| `AD` rules enforce their `Prevents` claims | Most are explicit and testable. AD-16 cannot satisfy its own out-of-process sample assertion under AD-4/AD-15 (H2). AD-14's Windows token protection is not fully testable (M1). |
| Deferred items | HTTP identity, later CLI/MCP surfaces, query extras, and trimming have seams or revisit triggers. None independently requires a v1 boundary choice beyond the listed findings. |
| Technology and brownfield fit | Stack is pinned; the architecture memlog records API checks. This review did not independently verify registry currency; the separate technology lens should own that check. Existing EventStore gateway, sibling CLI/MCP patterns, Builds imports, and Aspire test helpers are accounted for. |
| PRD coverage and inheritance | The capability map covers FR-1–FR-22 and NFR-1–NFR-8. AD-16 is an **unapproved conflict with the PRD**, not an inherited parent-spine violation (H1). The other accepted PRD amendments are named. |
| Structural dimensions | Paradigm, dependency direction, discovery, execution, data/serialization, settings and mutable state, test strategy, deployment environments, CI, release, and operational channel behavior are each decided or explicitly deferred/open. No wholly silent dimension found. |

## Suggested gate result

Hold final status until H1 has an owner decision and H2 is reconciled in AD-16. M1 and M2 are narrow spine edits that can be applied without reopening the paradigm or stack.

## Closure check after targeted revision

Checked the revised spine after the findings above. This section supersedes the original disposition for H2 and M1; the earlier text remains as review history.

| Finding | Current result | Evidence |
| --- | --- | --- |
| H2, synthetic sample in the out-of-process Catalog | **Closed.** AD-16 now says the shipped out-of-process tool Catalog contains only flagged production Contracts assemblies. A separate test-only benchmark builds the production-like Catalog plus `Sample.Contracts` through `CatalogBuilder.Build`. This satisfies AD-3, AD-4, and AD-15 without a production loading hook. | `ARCHITECTURE-SPINE.md:72`, `:78`, `:144`, `:150` |
| M1, Windows profile permissions | **Closed.** AD-14 now disables inheritance and requires explicit access for only the current user and LOCAL SYSTEM on the directory, profile, temporary file, and lock before token bytes are written. It requires Windows permission tests. | `ARCHITECTURE-SPINE.md:138` |
| M2, unknown Module result | **Tracked as an open question.** The new question correctly rejects both an invalid `unknown_operation` payload and a success document naming an undeclared Module. It requires a PRD owner choice before the public Catalog surface is frozen. | `ARCHITECTURE-SPINE.md:327` |
| H1, live conformance contract | **Still open.** AD-16 retains the single live submission and loopback parity split. The spine explicitly asks the PRD owner to decide whether it replaces FR-20 and SM-4. | `ARCHITECTURE-SPINE.md:150`, `:326` |

No new concrete incompatibility was found in these revisions. The current gate concern is the inherited PRD acceptance conflict (H1); M2 remains a bounded public-contract decision before implementation.

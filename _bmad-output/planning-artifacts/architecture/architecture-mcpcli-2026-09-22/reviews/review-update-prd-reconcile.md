# PRD reconciliation — architecture spine update

Reviewed the current draft `ARCHITECTURE-SPINE.md` against the final `prd.md` and its normative addendum §§E and G on 2026-09-22. This is a read-only review of those source artifacts; no spine or PRD text was changed.

## Verdict

**Needs source reconciliation before finalization.** The revised AD-5 and AD-9 resolve validation findings VAL-001 and VAL-002. AD-16 deliberately proposes a different integration contract from the final PRD and correctly tags it as an assumption, but the two documents cannot both be the release gate. The remaining findings below identify requirements that the spine does not yet bind or source text that should be updated with the new design.

## Findings

### 1. Critical — AD-16 changes the final live coverage and parity gate

- **Evidence:** PRD `prd.md:395-403` requires **both Heads** to submit **every** listed Operation against a running EventStore, with Gateway acceptance and equal result documents. `prd.md:502-507` requires both Heads against **one EventStore with identical inputs** for every Operation and equality after masking generated message and correlation identifiers. The spine `ARCHITECTURE-SPINE.md:145-150` instead runs each vector **once** live, does not compare two live results, and moves cross-head equality to a scripted fake/capture-replay lane. `ARCHITECTURE-SPINE.md:317-318` explicitly calls this a proposed replacement.
- **Impact:** The proposed test split may be technically sound for state-changing Commands, but satisfying AD-16 would still leave FR-20 and SM-4 unfulfilled as written. A release story could claim a green gate while the final PRD says it is incomplete.
- **Disposition:** Obtain a product-owner amendment to FR-20 and SM-4, with the exact parity and live semantics, **or** design an isolated-state live method that meets the existing text. Keep `[ASSUMPTION]` and the open question until that choice is recorded. The prior VAL-003 and VAL-004 concerns explain why the current literal gate is difficult; they do not silently amend the PRD.

### 2. High — The FR-21 inventory-to-Catalog gate is missing from the architecture's coverage mechanism

- **Evidence:** `prd.md:399-411` requires a maintainer-approved, versioned Parties inventory, a canonical-name comparison to `list_operations parties`, a separate decorated-contract-type match against the internal descriptor or manifest, and approved exclusion rows; any missing, extra, mismatched, or unapproved row fails Gateway readiness. `prd.md:453-464,479-480` makes that check a Module prerequisite. The spine's AD-16 (`ARCHITECTURE-SPINE.md:145-150`) matches conformance vectors to decorated Operations, which is a different set and does not check legacy exclusions or decorated type identity. The capability map (`ARCHITECTURE-SPINE.md:293-295`) places FR-21 under “documents outside `src/`” without a coverage-check owner or gate.
- **Impact:** Every decorated Operation could have a vector while legacy agent operations are omitted, a wrong CLR contract type is exposed, or exclusions lack maintainer approval. The v1 Parties coverage gate could pass despite failing FR-20/FR-21.
- **Disposition:** Bind the approved inventory format and test boundary to the Catalog coverage check, including canonical name, type identity, and exclusion approval. The versioned inventory can remain outside `src/`; the gate must consume it.

### 3. High — AD-17 cannot perform the required first Decoration Package release as stated

- **Evidence:** `prd.md:432-436,443-450` says the Decoration Package is published **before any upstream decoration begins**, and the tool follows after upstream decorated Contracts versions exist; the packages share one version when both form the public surface. AD-17 (`ARCHITECTURE-SPINE.md:151-155`) defines one prepare/publish transaction that always packs exactly `Hexalith.McpCli.Abstractions` and `Hexalith.McpCli`, validates both, and smokes offline discovery. AD-15 and the open questions (`ARCHITECTURE-SPINE.md:139-143,317-322`) also say the first decorated Tenants/Parties pins are unavailable until upstream releases.
- **Impact:** Module maintainers need a published Abstractions package to decorate and publish their Contracts Libraries; the release rule requires the decorated Libraries and releasable tool to exist first. The initial publication has no defined path.
- **Disposition:** Define a bounded Abstractions-only bootstrap release, then the paired tool/Abstractions release after the decorated pins exist, or document another concrete ordering that respects §7. State how shared versioning and package validation apply to the bootstrap.

### 4. Medium — A synthetic sample cannot enter the out-of-process Catalog through the stated production manifest

- **Evidence:** PRD `prd.md:99-100,421-424` permits exactly one test-only synthetic Module for the production-like benchmark Catalog. AD-15 (`ARCHITECTURE-SPINE.md:139-143`) says `Sample.Contracts` is never referenced by `src/`. AD-4 (`ARCHITECTURE-SPINE.md:73-77`) loads exactly the assembly manifest generated from the tool project's flagged production package references, with no runtime scan or hand-maintained list. AD-16 (`ARCHITECTURE-SPINE.md:145-150`) then says the same production-like Catalog contains Tenants, Parties, and the sample while the parity lane drives the built `hexalith` process.
- **Impact:** The built process cannot discover the test-only sample through its production manifest. Different test units may use incompatible Catalogs, and the intended NFR-1 benchmark may accidentally cover a different set from the parity lane.
- **Disposition:** Separate the in-process benchmark/test Catalog (which can pass the synthetic assembly to `CatalogBuilder`) from the out-of-process tool Catalog, or specify a test-only composition that admits the sample without shipping it or weakening AD-4/AD-15.

### 5. Medium — Routing equality loses the required `redundant_value` warning

- **Evidence:** PRD `prd.md:165-173,206-225` requires a `redundant_value` warning when an attribute value equals an interface or convention value. The spine's routing convention (`ARCHITECTURE-SPINE.md:181-183`) says “equal values ignored”; it lists `redundant_value` as a possible category but gives no rule that emits it.
- **Impact:** One Catalog implementation can silently ignore redundant declarations while another emits a warning. Under `--strict`, that changes the exit result.
- **Disposition:** State that equality with interface or convention emits `redundant_value` and keeps the Operation; only a differing interface value emits `conflicting_value`, while a differing convention value overrides it.

### 6. Medium — Recursive lint inspection is not bound

- **Evidence:** PRD `prd.md:184-191` requires recursive detection of undescribed and identifier-like properties and RFC 6901 pointers using Module-serialized names. Addendum `addendum.md:335-341` defines property-level finding shapes. The spine `ARCHITECTURE-SPINE.md:91-96,183-184` names schema derivation and the lint categories but never says lint traverses nested object and collection properties or how it forms nested property pointers. AD-5's general §G reference covers output shapes but not the PRD's recursive traversal.
- **Impact:** A flat `describe --lint` implementation can pass the category tests while missing description gaps in nested Payloads, contrary to FR-4 and NFR-8.
- **Disposition:** Add a short lint invariant: recursively inspect serialized Payload members, emit one property-level finding with its escaped JSON Pointer for each applicable gap, and keep these out of Catalog diagnostics.

### 7. Medium — The initial MCP registration decision conflicts with contextual addendum §B

- **Evidence:** Addendum `addendum.md:77-90` says runtime tools use `McpServerTool.Create` **and a custom list-tools handler**, explicitly citing spine AD-12. The revised AD-12 (`ARCHITECTURE-SPINE.md:121-125`) forbids a custom list handler and uses a filtered `ToolCollection` with built-in dispatch. Addendum §§A–D are context rather than the normative §§E/G (`addendum.md:8-12`), so this is source drift rather than a public-contract failure.
- **Impact:** A builder reading the addendum as implementation guidance can choose the obsolete registration path and disagree with the spine.
- **Disposition:** Update addendum §B to the verified AD-12 SDK model, or mark that sentence superseded. Keep the spine's decision if its SDK verification remains valid.

### 8. Low — Tool-budget measurement should name the PRD's exact counted surface

- **Evidence:** PRD `prd.md:421-425` counts the five Generic Tool **names, descriptions, and input schemas** under 8,000 characters, with output schemas measured separately. AD-12 (`ARCHITECTURE-SPINE.md:121-125`) says “the five definitions total under 8,000 characters”; its `OutputSchema` is part of each constructed definition.
- **Impact:** A test can apply the threshold to a different byte set, either over-rejecting the required output schemas or undercounting the input surface.
- **Disposition:** Name the exact counted fields and measure output schemas separately.

## Confirmed reconciliations

- **VAL-001 fixed:** AD-9 (`ARCHITECTURE-SPINE.md:103-107`) generates one message identifier, uses it as the omitted command correlation identifier, and accepts an idempotency key only from the caller. AD-5 (`:79-83`) echoes the key only when supplied. These match `prd.md:103-105,338-355` and `addendum.md:192-196,277-304`.
- **VAL-002 fixed at the spine contract level:** AD-5 (`ARCHITECTURE-SPINE.md:79-83`) binds the typed documents to the exhaustive normative addendum §G, including required/optional members, omission, Gateway status and metadata; AD-12 (`:121-125`) binds output schemas and error carriage. The convention list (`:183-185`) uses the PRD lint and error codes. Contract fixtures remain necessary to verify the future implementation.
- **Late AD-9 correction present:** a missing required idempotency key reports `/idempotencyKey` (`ARCHITECTURE-SPINE.md:107`), matching `prd.md:354`.
- **Other previously identified source rules retained:** missing Gateway URL affects execution and `submittable`, not discovery (`ARCHITECTURE-SPINE.md:67-71,127-131`; `prd.md:301-307`); `IdentifierKind` and unmarked `*Id` handling match `prd.md:231-240` (`ARCHITECTURE-SPINE.md:97-101`); the sample cardinality is one (`ARCHITECTURE-SPINE.md:193`, `prd.md:423`).

## Targeted closure check — later spine revision

Checked the revised spine after AD-21 and the associated edits. The original findings remain above as the review history; the current disposition is:

| Finding | Current disposition | Evidence |
| --- | --- | --- |
| 1. AD-16 versus FR-20/SM-4 | **Open by design** | AD-16 `:146-150` still separates loopback parity from once-only live execution; Open Questions `:325-326` requests the PRD owner's choice. |
| 2. FR-21 inventory gate | **Closed** | AD-21 `:176-180` now covers every Legacy Server and Frozen CLI inventory and binds canonical-name, contract-type, duplicate, and approved-exclusion checks to Module readiness and release; AD-3 `:72` includes `OperationDescriptor.ContractType`; map `:300-301` assigns the generic check to `tests/`. |
| 3. Abstractions bootstrap | **Closed** | AD-17 `:152-156` provides a one-time Abstractions-only pack/publish and CI gate before upstream decoration, then paired releases with shared versions. |
| 4. Synthetic sample in manifest | **Closed** | AD-16 `:146-150` explicitly keeps the out-of-process tool on its production manifest and builds the benchmark Catalog in process through `CatalogBuilder.Build` with the single sample. |
| 5. `redundant_value` warning | **Closed** | Routing convention `:189` now emits it for equality with an interface or convention; `:190` retains it in the diagnostic set. |
| 6. Recursive lint | **Closed** | AD-7 `:91-96` now requires recursive inspection of nested objects and collections and escaped RFC 6901 pointers in Module-serialized casing. |
| 7. Addendum §B registration drift | **Open, explicitly tracked** | AD-12 `:121-126` uses built-in filtered dispatch; Open Questions `:328` names the stale contextual addendum sentence. |
| 8. Tool-budget fields | **Closed** | AD-12 `:126` now counts exactly names, descriptions, and input schemas under 8,000 characters and measures output schemas separately. |

The closure check leaves only findings 1 and 7 open, both expressly listed under the spine's Open Questions. Finding 1 requires the PRD owner's decision before the integration-harness story closes; finding 7 requires the contextual addendum §B sentence to be updated after the AD-12 choice is confirmed.

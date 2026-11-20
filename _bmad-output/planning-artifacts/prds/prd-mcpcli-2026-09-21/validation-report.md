# Hexalith.McpCli PRD validation

**Grade Fair.** 0 critical · 2 high · 9 medium · 5 low.

Reviewed 2026-11-20T16:00+01:00 against the working tree at `6993abfe`. [PRD](prd.md) · [Normative addendum](addendum.md) · [Quality rubric](../../../../.agents/skills/bmad-prd/assets/prd-validation-checklist.md)

## Overall verdict

The PRD supports enrollment and migration planning, and all 13 findings from the previous validation remain closed. This full review found two high-priority issues. The release authorities disagree about who may publish the next stable tool, and the profile contract omits a supported operation that can erase saved settings.

The public 3.0.0 tool contains Parties and Tenants. The additional Projects Operations belong to the source checkout. The hosted HTTP decision, Projects live qualification, Folders enrollment and legacy retirement remain open delivery work.

[Prior validation](validation-report-2026-11-20-before-update.md) · [Review of all 13 corrections](review-validation-followup-2026-11-20.md)

## Dimension verdicts

| Dimension | Verdict | Assessment |
|---|---|---|
| Decision-readiness | Adequate | McpCli identifies candidate evidence and owners. The cross-project review found that Platform AD-11 and McpCli AD-17 assign different stable publishers, leaving the next promotion without an agreed decision. |
| Substance over theater | Strong | The startup benchmark names its cohort and limit. Parity and live semantic checks specify separate observable outcomes. |
| Strategic coherence | Adequate | The shared catalog supports the two-module journey. The README-only timing measure still depends on a write whose public-agent eligibility is disputed. |
| Done-ness clarity | Adequate | Both Heads have explicit failure and result requirements. Profile replacement and a catalog-admissible Query example still allow materially different implementations or results. |
| Scope honesty | Adequate | The PRD distinguishes enrolled modules from live qualification and retirement. Publication state and the Platform deployment boundary need more precise scope. |
| Downstream usability | Adequate | The stable requirement IDs and two contract tables support implementation. Several input boundaries and the modern MCP wire example still require an additional source. |
| Shape fit | Strong | The main document explains product and release decisions. The addendum provides field-level contracts for the shared CLI and MCP surfaces. |

## Findings by severity

### Critical (0)

None.

### High (2)

#### Two projects assign stable tool publication to different workflows

*PRD §7 and Story 5.15 · Decision-readiness*

McpCli AD-17 and §7 specify a shared-version package pair. Platform AD-11 reserves stable tool publication for the Platform staging workflow and assigns McpCli the stable Abstractions package and prerelease tool. Story 5.15 names McpCli and CiCd owners, but a rehearsal on their workflow alone cannot settle who may publish the next stable tool.

**Correction.** Have Platform, McpCli and CiCd release owners record the applicable release track, publisher, version rule and source of final archive digests before accepting the rehearsal. Preserve the recorded release history. [McpCli AD-17, line 163](../../architecture/architecture-mcpcli-2026-09-22/ARCHITECTURE-SPINE.md#L163) · [Platform AD-11, line 190](../../../../references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md#L190)

#### Profile replacement can clear saved connection and operator settings

*PRD FR-18 and addendum §E · Done-ness clarity*

`config profile add` with an existing name replaces the whole record. It requires an explicit URL, stores only the supplied connection fields, and clears omitted credentials and saved operator settings. “Behave as in the admin CLI” gives an implementer no acceptance rule for that state change.

**Correction.** Specify create versus replace, fields retained and cleared, and the operator flags rejected before writing. Distinguish whole-record replacement from single-field `config set` and from the proposed private rotation flow. [Profile add implementation, line 615](../../../../src/Hexalith.McpCli/Cli/CliRunner.cs#L615) · [Whole-record test, line 1814](../../../../tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs#L1814)

### Medium (9)

#### The README-only timing metric still uses a disputed write

*PRD SM-6, FR-21 and README operator checklist · Strategic coherence*

UJ-1 now uses two authorized reads. SM-6 separately times the first successful `send_command` using the README, whose procedure directs the operator to `parties.create-party` (T04). Per-run operator approval does not resolve the separate K12 owner decision on agent eligibility.

**Correction.** Choose a preauthorized, agent-eligible Command for the timed exercise, or defer that measurement until the Parties and McpCli owners resolve T04. [Operator procedure, line 453](../../../../README.md#L453) · [Parties restriction, line 178](../../architecture/architecture-mcpcli-2026-09-22/AD-23-non-gateway-capability-classes.md#L178)

#### A valid Query example can invalidate the describe result

*PRD §5.1, FR-1 and FR-7, addendum §G · Done-ness clarity*

A synthetic collection Query with `example` set to `[]` passed Catalog admission. Its `describe_operation` result then failed the advertised output schema, which requires an object for a present `example`. The production examples passed.

**Correction.** Specify the object-root rule for a declared example and require the `invalid_example` diagnostic on violation. Keep support for permitted Query payload roots and add the collection Query as a contract test. [Catalog example validation, line 225](../../../../src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs#L225) · [Discovery result schema, line 158](../../../../src/Hexalith.McpCli.Core/Serialization/ResultDocumentSchema.cs#L158)

#### The query paging arguments omit accepted limits and error behavior

*Addendum §E call arguments and PRD FR-15/16 · Downstream usability*

The generic arguments table names `pageSize`, `offset` and `cursor` but omits their bounds and combinations. In both MCP revisions a `pageSize` token of `25.0` failed integer binding with `-32602`, while `201` reached the tool and returned `validation_failed` at `/pageSize`.

**Correction.** Specify page size 1–200, offset 0–2,147,483,647, cursor length up to 4,096 UTF-16 units and the nonblank-cursor/offset exclusion. Distinguish CLI parsing, MCP binding and executor validation. [Published paging rules, line 591](../../../../README.md#L591) · [Paging arguments, line 234](addendum.md#L234)

#### Profile management has different selection rules from inspection

*PRD FR-13/18 and addendum §E · Downstream usability*

FR-13 applies flag, environment and saved-profile selection to every verb. `config current` honors that order. The named management verbs ignore `--profile` and `EVENTSTORE_PROFILE`, even if they name a missing profile. A conforming implementation could incorrectly block a repair or select the wrong profile.

**Correction.** Limit session precedence to the applicable commands. Identify the management verbs and test `config current` and a named management command with the same missing selector. [Selection rules, line 370](../../../../README.md#L370) · [Management tests, line 1268](../../../../tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs#L1268)

#### The onboarding checklist makes an enrollment inventory look optional

*PRD §8.1, checklist item 8 · Downstream usability*

The checklist requires an approved inventory only for Modules replacing a legacy surface. The release gate also requires an approved and hash-bound inventory for a newly enrolled Module with no predecessor.

**Correction.** Require the approved release inventory for every enrollment. Apply the legacy-operation mapping only to Modules replacing a legacy surface. [Conformance gate, line 137](../../../../tools/conformance-vectors/v1/README.md#L137) · [Onboarding checklist, line 505](prd.md#L505)

#### Platform admission rules are missing from the migration and HTTP handoffs

*PRD FR-22, §8.2 and OQ-1 · Scope honesty*

Platform AD-11 restricts legacy compatibility to named migrations outside every Platform composition. A new hosted transport also requires a Platform architecture decision covering its surface class, Keycloak client, exposure and realm entries. The PRD specifies owner review for K10 but omits those deployment rules.

**Correction.** Add the legacy composition limit to FR-22 and the Platform admission decision to the hosted HTTP acceptance criteria. Keep K10 token exchange, denial evidence and independent retirement gates. [Platform legacy-surface rule, line 194](../../../../references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md#L194) · [Compatibility rule, line 459](prd.md#L459)

#### The raw MCP example needs a protocol-version label

*Addendum §E, complete tools/call example · Downstream usability*

The documented tool arguments bind under both supported revisions. After 2026-07-28 discovery, sending the literal frame without per-request `_meta` produced a legacy-shaped reply. The modern envelope produced the typed response with `resultType`.

**Correction.** Label the displayed frame for the 2025-06-18 initialized session. Show the required per-request protocol-version and client-capabilities metadata for 2026-07-28, or point to a complete modern frame. [Request example, line 249](addendum.md#L249) · [Two supported flows, line 630](../../../../README.md#L630) · [Version-specific client fixture, line 81](../../../../tests/Hexalith.McpCli.Mcp.Tests/McpTestSession.cs#L81)

#### An invalid module fixed tenant excludes the entire assembly

*PRD FR-6, diagnostic table · Done-ness clarity*

The `invalid_routing_value` row gives a type-level exclusion for an invalid Module `FixedTenant`. The Catalog emits one assembly-level diagnostic and skips the Module before scanning its types. An invalid Operation routing field has a narrower effect.

**Correction.** Give `FixedTenant` its own trigger and assembly-wide consequence under the same diagnostic code. Retain type exclusion for invalid Operation routing. [Catalog marker check, line 45](../../../../src/Hexalith.McpCli.Core/Catalog/CatalogBuilder.cs#L45) · [Diagnostic table, line 232](prd.md#L232)

#### The status section skips the latest public tool package

*PRD §0 and §8.1 · Scope honesty*

The PRD reports the first release, 2.0.1, and the current source manifest. The latest public pair is 3.0.0, released on 15 November. Its tool contains Parties and Tenants. Projects is present on the reviewed main checkout. A default package installation and a build from that checkout therefore offer different catalogs.

**Correction.** Date the latest public pair, identify its shipped Modules, and retain the separate counts and qualification status for the working tree. [Public 3.0.0 release](https://github.com/Hexalith/Hexalith.McpCli/releases/tag/v3.0.0) · [Published tool archive](https://api.nuget.org/v3-flatcontainer/hexalith.mcpcli/3.0.0/hexalith.mcpcli.3.0.0.nupkg) · [Projects on main, line 531](../../../../README.md#L531)

### Low (5)

#### Post-start request errors and host faults need distinct outcomes

*PRD FR-6/10 and addendum §G · Done-ness clarity*

FR-6 and FR-10 send all post-start failures through the protocol. Section G and the CLI tests also cover a host fault with no request to answer. It emits a stderr diagnostic and exits 2.

**Correction.** Limit the protocol-only rule to request-scoped failures. Reference §G for normal shutdown and host termination. [Host fault test, line 758](../../../../tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs#L758) · [Error documents, line 521](addendum.md#L521)

#### Whitespace-only operation and module names fail before lookup

*PRD FR-11 and addendum §E · Downstream usability*

The lookup rule treats a nonempty name as eligible for catalog lookup. A string containing only spaces fails earlier. MCP returns invalid parameters, and the CLI returns `invalid_arguments`.

**Correction.** Use “nonblank” for required operation and module names. Preserve the input spelling for genuine lookup misses. [MCP name checks, line 67](../../../../src/Hexalith.McpCli.Mcp/McpCliMcpServiceCollectionExtensions.cs#L67) · [CLI name checks, line 344](../../../../src/Hexalith.McpCli/Cli/CliRunner.cs#L344)

#### Rendered lists change the open-question numbers

*PRD §10.2–10.3 · Downstream usability*

Markdown renumbers the lists consecutively. The deletion-order item labeled 6 in the source appears as 2 in the rendered Open list, making an OQ reference point to a different item.

**Correction.** Write the identifiers as literal labels such as `OQ-6` in bullets or a table so they survive rendering. [Open and resolved lists, line 580](prd.md#L580)

#### The declaration table makes a Query aggregate constant compulsory

*PRD §5.1 and FR-2 · Downstream usability*

The table requires an `aggregateId` constant for a list-style Query without an aggregate property. FR-2 and the Catalog allow both declarations to be absent and then require the caller’s explicit aggregate ID.

**Correction.** Mark the constant optional and retain its mutual exclusion with the property. Refer to the per-call requirement when both are absent. [Declaration table, line 146](prd.md#L146) · [Catalog regression, line 139](../../../../tests/Hexalith.McpCli.Core.Tests/CatalogTests.cs#L139)

#### The generic-runner constraint is written as a repository-wide rule

*PRD §4 and FR-20 · Scope honesty*

FR-20 says the whole repository contains no Module-specific setup code. The adopted decision restricts the generic runner, while §4 permits named test fixtures and the test AppHost contains approved Module-specific setup.

**Correction.** Apply the setup restriction to the generic runner. Keep the production dependency rule and permitted integration-test composition distinct. [Approved runner wording, line 249](../../sprint-change-proposal-2026-11-10-shape-coverage.md#L249) · [Test AppHost, line 59](../../../../tests/Hexalith.McpCli.AppHost/Program.cs#L59)

## Checks and scope

- The seven-dimension review, public-contract review and migration review reported 17 items. The duplicate paging finding was counted once. The earlier 13 corrections were checked against the final PRD and addendum.
- All 22 FRs, eight NFRs, three journeys, seven success metrics and four counter-metrics have unique identifiers within their groups. Eight inline assumptions have eight index entries. Fourteen local document links and anchors resolved, and all 13 JSON examples parsed.
- The 36 focused local Linux Release tests passed with zero failures or skips (13 Core, 7 CLI, 16 MCP). On both supported MCP revisions, all five documented successes and five errors passed their advertised output schemas. A separate synthetic Query exposed the non-object example issue. The raw modern MCP frame was tested separately from its tool arguments.
- The public release and NuGet archives identify 3.0.0 at commit `63df6d2b`. The source manifest at `6993abfe` exposes 26 Operations across three Modules. The checks used local Release executables and loopback responses. Live Gateway, cross-platform and release acceptance require their own evidence.

## Reviewer files

- [Quality rubric](review-revalidation-rubric-2026-11-20.md)
- [Public contract](review-revalidation-contract-2026-11-20.md)
- [Migration and release](review-revalidation-migration-2026-11-20.md)

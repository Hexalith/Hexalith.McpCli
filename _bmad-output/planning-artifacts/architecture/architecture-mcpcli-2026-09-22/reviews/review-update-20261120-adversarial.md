# Architecture update review: incompatible implementations

Reviewed the November 20 working spine against McpCli source `790d2cdb`, its public contract and the root-pinned Platform spine at `b8048739`. The draft leaves two Platform boundaries and two existing input-validation rules open to incompatible implementations.

## High · Connected operation availability

AD-3 derives `submittable` from read-only mode and the configured Gateway URL. An implementer of a Platform-connected tool could apply that rule to a bundled Operation and enable it whenever the URL is present. The Platform Gateway applies the active environment's catalog, which can have a different schema or surface eligibility. Both implementers would be following their respective decision documents.

Keep the existing offline field and result shape. For the proposed Platform-connected path, add the prerequisite that the selected Gateway serves the Operation as executable with a matching contract-schema digest, McpCli-eligible surface and current authorization. The Gateway reauthorizes the call. Record this as an integration obligation pending delivery. [Platform AD-11, Availability](../../../../../references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md#ad-11--one-generic-tool-with-environment-aware-discovery-adopted-amended) · [Public discovery contract](../../../prds/prd-mcpcli-2026-09-21/addendum.md)

## High · Integration environment ownership

AD-16 describes the private McpCli AppHost lane, and AD-17 consumes its qualification evidence. A McpCli fixture could launch and clean that topology and report success while a Platform release operator expects the same test to have run against the Platform runner's managed environment. The two reports could refer to different compositions and catalog generations.

Identify the private AppHost run as module product CI. For Platform integration, the Platform runner provisions, supplies the versioned environment descriptor and owns cleanup. The participating McpCli tests consume that descriptor. Require evidence from the selected Platform environment before making a Platform qualification or staging claim. [Platform AD-10, Owner](../../../../../references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md#ad-10--test-environments-have-explicit-run-ownership-adopted-amended) · [McpCli live lane](../../../../../tools/live-topology/README.md)

## Medium · Duplicate JSON members

AD-5 and AD-9 require a root error for malformed JSON. Parsers differ on whether to accept duplicate object members, including inside a nested object. One implementation could submit the surviving value while another returns a validation error. State the existing Core contract for both execution tools: reject duplicate property names at any depth during raw JSON parsing, return one `validation_failed` violation at `/` and make zero Gateway calls. [Core query regression](../../../../../tests/Hexalith.McpCli.Core.Tests/QueryValidationTests.cs) · [CLI execution contract](../../../../../tests/Hexalith.McpCli.Cli.Tests/CliOutputContractTests.cs)

## Medium · Extension validation across storage and execution

An ordinarily allowed key can occur twice with different casing in a call. AD-9 describes case-insensitive allowlist membership without requiring case-insensitive uniqueness among the submitted keys. AD-13 describes stored allowlist validation without naming its reserved namespace. A profile writer and executor could therefore disagree about which settings can be used.

Identify the shared key validator in AD-9/13. Reject `actor:globalAdmin` and the `identity:` prefix case-insensitively in both profile allowlists and submitted maps. Reject case-insensitive duplicate call keys and preserve the spelling and values of accepted keys on the wire. [Shared validator](../../../../../src/Hexalith.McpCli.Core/Execution/ExtensionValidator.cs) · [Profile compatibility tests](../../../../../tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs) · [Operator guidance](../../../../../README.md)

The stable-publisher choice, hosted HTTP admission, Parties eligibility, Projects paging and the future acknowledgment client already have explicit authority and revisit conditions. They require the recorded owner decisions or evidence.

## Final disposition · 2026-11-20

| Finding | Verification in the revised spine | Disposition |
| --- | --- | --- |
| Connected operation availability | AD-3 requires the selected Gateway's executable entry, matching digest, served surface eligibility and current authorization. AD-9 applies these checks before submission. The Gateway reauthorizes each call. | Resolved for architecture. Platform integration still requires the named qualification evidence. |
| Integration environment ownership | AD-16 assigns the private AppHost run to McpCli product CI. For Platform integration, the Platform runner owns provisioning through cleanup, supplies the versioned descriptor and provides separate staging evidence. | Resolved for architecture. |
| Duplicate JSON members | AD-5 requires a single root validation error and zero Gateway calls when either execution tool receives a duplicate object member at any depth. | Resolved. |
| Stored and submitted extension keys | AD-9 specifies case-insensitive uniqueness and reserved keys, and retains accepted spelling. AD-13 uses the shared validator for profile writes and resolution. | Resolved. |

The adversarial gate passes for the revised spine. These dispositions cover all four findings. Runtime and release qualification retain their separate owners and evidence requirements. [Revised architecture](../ARCHITECTURE-SPINE.md)

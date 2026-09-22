---
title: "Update reconciliation: PRD 2026-09-22 handoff"
reviewed: ARCHITECTURE-SPINE.md
against: prd.md §10.1, §§4 and 5.1, FR-7, FR-13, FR-15, FR-16, FR-18, FR-20; addendum §§A, B, E
date: '2026-09-22'
status: findings
---

# PRD update reconciliation

## Verdict

**Hold before the executor epic.** The five §10.1 decisions now appear correctly in their named records: AD-7 includes `actorProperty`; AD-9 implements the operator-gated per-call tenant, Actor filling, and Command-only correlation/extensions; AD-11/AD-14 own `~/.eventstore/mcpcli.json` and the new Profile fields; AD-15 carries the exact production allowlist; and AD-19 carries the Query constant plus the nonempty-identifier rule. The dependent text is not fully reconciled, however: two omissions would make a literal executor violate FR-7/FR-15, and two shared-model/discovery rules still contradict the PRD package.

## Critical

### C1. The frozen Catalog model drops Module data that AD-7, AD-9, and AD-19 require

PRD §5.1 makes `fixedTenant` and `serializerOptionsProvider` Module-marker members. The provider's converters take precedence over canonical Payload options in Schema derivation and Payload handling; FR-7 specifically relies on this for converter-backed identifiers. The spine instead freezes `ModuleDescriptor(Name, Description, IdentifierKind, Operations)` (AD-3), prohibits every `JsonSerializerOptions` except the two canonical instances (AD-6), always derives the Schema with `McpCliJson.Payload` (AD-7), and deserializes an `ICommandContract` accessor with that same canonical instance (AD-19). AD-9 nevertheless expects the descriptor to supply `fixedTenant`.

Built literally, Core must either re-reflect over the marker outside the Catalog, violating AD-3, or ignore `fixedTenant`; and a Module converter can disagree with the advertised Schema, validation, and aggregate accessor. Amend AD-3 to retain `FixedTenant` and the resolved per-Module Payload serialization policy; amend AD-6/AD-7/AD-19 so the Module provider's converters precede the canonical Payload converters while Envelope and result serialization remain tool-owned.

### C2. FR-15's Gateway-pattern validation is still absent from the executor contract

FR-15 requires pre-validation of Tenant, aggregate identifier, entity identifier, extension keys, and Routing Values against the Gateway patterns. AD-8 validates a `String` aggregate only as nonempty and Tenant only as nonempty; AD-9 checks extension membership but states no Tenant, aggregate, entity, or extension-key pattern validation; AD-19 pattern-validates only the Query's constant. Thus an explicit/accessor aggregate, Tenant, or `entityId` can pass Core and be rejected first by the Gateway, directly contradicting FR-15.

Add one explicit validation step to AD-9 for the per-call fields and one Catalog-build rule for Routing Values/constants, with the exact FR-15 patterns and violation pointers (`/tenant`, `/aggregateId`, `/entityId`, `/extensions/<key>`).

## High

### H1. AD-5 still lets the CLI turn its session Tenant into a per-call Tenant

Addendum §E and FR-13 say only MCP has a per-call `tenant`; CLI `--tenant` is a global session setting. AD-10 correctly separates per-call argument records from session `EnvelopeContext`, but AD-5 says both heads bind the same argument records, those records contain `Tenant?`, and every argument-record property must have a CLI option. A literal CLI story can therefore bind global `--tenant` into `SendCommandArguments.Tenant` / `RunQueryArguments.Tenant`, collapsing the distinction on which AD-9's operator gate depends.

State in AD-5 that the MCP adapter alone binds the argument-record `Tenant`; the CLI always leaves that member null and supplies global `--tenant` only through `ResolvedSettings`/`EnvelopeContext`. Replace the blanket CLI-option assertion with a surface mapping assertion against addendum §E.

### H2. AD-4 contradicts the normative discovery mechanism recorded in the PRD package

PRD FR-5 and addendum §B say an MSBuild target collects `PackageReference` items marked `HexalithContracts="true"` into the build-time scan list, and FR-5 requires a test that the generated list equals that flagged set. AD-4 instead uses a Roslyn generator that scans referenced assembly symbols and keeps marker-bearing assemblies. These mechanisms differ for an unmarked flagged package and make the FR-5 equality test impossible as specified.

Change AD-4 to the flagged-PackageReference/MSBuild manifest, or explicitly amend FR-5 and addendum §B. Leaving both instructions makes the generator epic non-convergent.

## Medium

### M1. AD-15's policy is reconciled, but its v1 Module versions are not pinned

FR-20 requires pinned package references. AD-15 says “first decorated release,” while the Stack records `Hexalith.Tenants.Contracts` as `>= 5.7.0` and `Hexalith.Parties.Contracts` as `>= 1.1.1`. Those are lower bounds, not pins, even though AD-15 says the closure test enforces versions.

Until the decorated releases exist, record the exact versions as an open prerequisite; before implementation, replace the inequalities with exact central package pins and make the closure test compare against them.

## Reconciled without a finding

- AD-7: `actorProperty` is now an envelope-filled, `readOnly`, non-required Payload property.
- AD-9: fixed Tenant precedence, the operator override gate, required Actor, Command-only correlation/extensions, disagreement handling, and no Query correlation/extensions match FR-16 and addendum §§B/E.
- AD-11/AD-14: the tool-only Profile store and `actor`, `allowTenantOverride`, and `allowedExtensions` fields match FR-18 and addendum §§A/E.
- AD-15: the production allowlist and test-only exception now match PRD §4 and FR-20, subject to M1.
- AD-19: explicit/accessor/Query-constant precedence, mutual exclusion, `aggregateIdRequired`, and refusal of an empty identifier match §5.1 and FR-16, subject to C1/C2.

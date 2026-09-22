---
title: "Update reviewer gate: good-spine rubric"
reviewed: ARCHITECTURE-SPINE.md
date: '2026-09-22'
status: findings
fallback: sequential review because subagents hit the usage limit
---

# Good-spine rubric

## Verdict

**Pass after three tightenings.** The updated spine covers the five PRD handoff decisions and their downstream model, settings, discovery, and dependency effects. Three rules still permit compliant stories to diverge.

## High

### H1. A declared `correlationProperty` has no value when the caller omits `correlationId`

AD-9 says a Command correlation identifier is optional but also says `correlationProperty` is overwritten. It does not say whether omission removes the Payload property, writes null, generates a separate value, or uses the generated message identifier. Independently built executor and fixture stories can choose differently.

**Autofix:** resolve Command correlation once as `argument ?? MessageId`, pass it explicitly to `SubmitCommandRequest`, and use the same value for `correlationProperty` and the result expectation.

### H2. AD-15 can be read as banning the external packages the Stack requires

AD-15 calls its list the production allowlist, while the Stack necessarily includes ModelContextProtocol, System.CommandLine, JsonSchema.Net, and Microsoft.Extensions. The repository baseline frames the allowlist as the permitted Hexalith dependency boundary.

**Autofix:** name it the **Hexalith production-dependency allowlist** and state that non-Hexalith dependencies are limited separately by the pinned Stack.

## Medium

### M1. Equality semantics are unstated at three security-sensitive seams

AD-9 does not fix comparison semantics for per-call versus session Tenant, Payload versus resolved Actor, aggregate argument versus accessor, or extension-key membership. Case-sensitive and case-insensitive implementations can both claim compliance.

**Autofix:** use ordinal equality for Tenant, Actor, and aggregate identifiers after validation; use ordinal-ignore-case membership for extension keys to match the Gateway dictionary behavior; reject case-insensitive duplicates in `allowedExtensions` at configuration load.

## Checklist result

- Real divergence points for the five handoff decisions: covered, subject to H1/M1.
- Enforceable `Binds`/`Prevents`/`Rule`: present for every AD; linter clean.
- Deferred items: no executor-critical item is deferred; exact decorated package pins have an explicit OQ-8 revisit condition.
- Named technology: no new technology was introduced; versions remain pinned where releases exist.
- Brownfield and PRD fit: local Gateway/client behavior and PRD rules are reflected.
- Operational envelope: developer, CI, release, and deferred HTTP environments remain explicit.

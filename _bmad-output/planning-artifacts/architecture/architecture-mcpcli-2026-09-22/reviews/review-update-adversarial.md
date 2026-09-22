---
title: "Update reviewer gate: adversarial seam review"
reviewed: ARCHITECTURE-SPINE.md
date: '2026-09-22'
status: findings
fallback: sequential review because subagents hit the usage limit
---

# Adversarial seam review

## Verdict

**Pass after closing one execution hole and one contract hole.** The updated ADs now converge on the requested behavior, but two independently built units can still obey the text and fail at their seam.

## Critical

### C1. The executor validates before inserting values that can violate the Schema

AD-9 validates the caller Payload, then inserts Tenant, Actor, correlation, and idempotency values into properties that AD-7 made optional. If a Module author points an envelope property at a non-string or converter-constrained member, the caller Payload passes because the property is absent; the rebuilt Payload can then violate the advertised Schema and still reach the Gateway. An executor story can revalidate while another can trust the Catalog, and both satisfy the current sequence.

**Autofix:** validate the rebuilt Payload against the same stored Schema and Module options before constructing the Gateway request; merge those violations into `validation_failed` and make a zero-call assertion part of the executor contract.

## High

### H1. `serializerOptionsProvider` has no callable ABI

AD-3/AD-6 say the Catalog invokes a static provider once, but neither fixes what the attribute stores nor the member signature. Abstractions can expose a provider `Type`, a member name, or a delegate; Core can look for a property, field, or method. Independently implemented Decoration Package and Catalog stories can therefore be incompatible while each follows the spine.

**Autofix:** fix the public marker member and provider interface in the spine, for example `Type? SerializerOptionsProvider` whose type implements a dependency-free `IHexalithJsonOptionsProvider` with one `static abstract JsonSerializerOptions CreateOptions()` member, or record the exact alternative chosen.

## Medium

### M1. Manifest and Catalog tests do not explicitly cover the flagged-but-unmarked seam

AD-4 defines both halves but only requires equality between flagged references and generated pairs. A build can generate the correct pair while the Catalog accidentally reports an unmarked package as an empty Module.

**Autofix:** include one flagged unmarked assembly in the manifest test and assert it is invisible with no diagnostic, distinct from a flagged marked empty assembly producing `empty_module`.

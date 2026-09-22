# Accepted PRD alignment for the architecture update

The product owner accepted both decisions. The PRD, addendum, and spine were updated on 2026-09-22; the alternatives below remain as decision context.

## Decision 1 — live coverage and cross-head parity

Recommended amendment to FR-20 and SM-4: every decorated Tenants and Parties Operation has a versioned, maintainer-approved conformance vector. Both out-of-process heads execute every vector against the same reset loopback Gateway script; compare the canonical result and error documents after masking only generated message and correlation identifiers. A separate Aspire lane executes each vector once against a running EventStore and asserts Gateway acceptance or a returned Query document plus the vector's semantic checks. No live Command is submitted twice merely to compare documents. The live lane is blocking in release CI. This replaces the current requirement that both heads submit each Operation to one live topology and return equal documents.

Alternative: retain two live submissions per Operation, but require isolated equivalent state and versioned setup for each head, with a precisely defined normalization of generated and domain-assigned values. The architecture would need a different AD-16 and a source amendment describing that normalization.

## Decision 2 — unknown Module

Recommended addendum §G variant: `unknown_module` has required `code`, `module`, and `suggestions`. `module` echoes the non-empty requested value; `suggestions` is an array of at most three declared canonical Module Names. `list_operations` uses this variant when the requested Module is absent. This keeps the success document's `module` field reserved for a declared canonical Module Name.

Alternative: define a success result `{ "module": "<requested-name>", "operations": [] }` for unknown names and relax §G's declared-Module constraint for that case.

## Context correction after AD-12 is accepted

Replace addendum §B's custom list-tools-handler wording with one settings-filtered `ToolCollection` using the pinned SDK's built-in list and call dispatch. No public argument or result shape changes.

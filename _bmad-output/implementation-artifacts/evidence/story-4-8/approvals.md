# Story 4.8 approvals

Both maintainer decisions below are human-owned. The requesting user, acting as
Tenants maintainer under the spec's 2026-10-19 decision, gave both on 2026-10-20.

## 1. Constant list aggregate `index` (confirmed)

`tenants.list-tenants` and `tenants.get-user-tenants` route to the constant
aggregate `index` (`HexalithQuery.AggregateId = "index"`). Facts for the decision:

- `GetUserTenantsQuery` already binds REST reads to the constant aggregate
  `index` (`[RestQueryBinding(RestQueryBindingSource.Constant, "index", ...)]`).
  `ListTenantsQuery` has no REST binding.
- Both handlers ignore the aggregate identifier for data selection.
  `ListTenantsQueryHandler` reads the singleton `projection:tenant-index:singleton`.
  `GetUserTenantsQueryHandler` lists the payload `UserId`, else the routed entity,
  else the caller.
- `index` matches the Gateway and McpCli aggregate-identifier rule (ASCII letters,
  digits, `.`, `_`, `-`).
- When a caller omits the entity identifier, the Gateway routes it to the aggregate
  identifier (`QueriesController`: `entityId = request.EntityId` or
  `request.AggregateId`). The handler therefore treats an entity identifier equal
  to the aggregate identifier as "not chosen by the caller".

Record: approver is the requesting user, as Tenants maintainer; date 2026-10-20;
decision `index` confirmed (answer "Confirm `index`").

## 2. Tenants conformance vectors (approved for this story's scope)

Record these items, following `tools/conformance-vectors/v1/README.md`
("Module author approval"):

| Item | Value |
| --- | --- |
| Format | `formatVersion: 1` |
| Vector set | `Hexalith.Tenants/tests/conformance-vectors/mcpcli-v1/*.json`: 14 files, one per operation |
| Vector repository revision | Tenants `9e08a75eef4bd16994c9b7835be19849fa34fd99` (on `origin/main`), which lands these 14 files exactly as validated and approved. |
| Validator revision | McpCli `tools/conformance-vectors/v1` at `447085c42ec606f642240c4cae0415e7c2f97467`. It is unchanged at McpCli HEAD `742f5b6ead66937f62025b73d77452e0f8126658`. |
| Package | `Hexalith.Tenants.Contracts` `0.0.0-story48`: a local scratch pack, not a release |
| Artifact hash | `sha512-Od2hpUmNTlE9Zd6DV4LEQ+IdFIkDhp1X9Oo0M5EZ25ALSMMC0Udb3URXXV3bDLA/8KnQT658QjAQ9MdU+lcnnA==` |
| Validation | `vector-validation.txt`: exit 0, 14 vectors, no missing, duplicate or extra vector. The vector files are unchanged; they were revalidated against each regenerated scratch artifact, most recently this one. |
| Loopback | `loopback.txt`: 14 PASS, exit 0 |
| Approving maintainer | The requesting user, as Tenants maintainer, 2026-10-20 (answer "Approve") |

The vectors name the scratch version `0.0.0-story48`. Release and enrollment are
deferred (`deferred-work.md`, Story 4.8 split). They must be revalidated against
the immutable release artifact, with its final version, before approval for
enrollment. Their scripted continuation cursors are valid only for loopback.
Live paging and filter proof belongs to Story 4.13, so Gateway-ready acceptance
stays blocked.

## 3. NFR-8 description review (done)

A fresh-context reviewer saw only `catalog-dump.json`, with no source,
specification or tests. The review is in `nfr8-review.md`. The epic still
requires the review to be recorded in the Tenants pull request (PRD §8.1 item
6), and that pull request does not exist yet.

## 4. Open points for the Tenants maintainer (no change made)

- **`Stream` on `tenants.get-tenant-audit`.** The spec boundary names only `From`,
  `To` and `Category`, so a CLR `Stream` is not honored. The schema describes it
  as having no effect. Decide whether gateway callers should be able to select the
  audit owner stream. The `global-administrators` stream is valid only for tenant
  `system`, and the read is restricted to global administrators.
- **First-member bootstrap.** `AddUserToTenant` lets any caller add the first
  member, with any role, to a tenant that never had one. The description states
  this existing aggregate rule (round-2 reviewer observation 16), and it is now
  reachable through McpCli. Confirm it is intended.
- **`get-user-tenants` without `UserId`.** The Gateway routes an omitted entity
  identifier to the aggregate `index`, so the legacy fallback lists a user named
  `index`. The description says to always set `UserId`. Making it schema-required
  would need `[JsonRequired]` or `required` on the contract.

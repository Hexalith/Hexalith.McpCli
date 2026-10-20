# Story 4.8 NFR-8 description review

Each round used a fresh-context reviewer with no access to the module source,
specification or tests. The reviewer received only `catalog-dump.json` (the
scratch-host discovery output) and the generic description of the tool's
discovery surface. Each round's text is recorded verbatim.

## Round 1 (artifact `sha512-A3Zfw+gbsrwUYu5esTkE0Qsjl21jIGdF8b7X0a9gvYmeP+50QQbIKIJ2P7JjwpW6r9Ig0ELC4EUHgziAgr+lPQ==`)

**Overall verdict: PASS WITH NOTES** (no blocking findings; two schema/description contradictions and several underspecified failure/permission behaviours).

| Item | Verdict | Reason |
|---|---|---|
| module `tenants` | note | Clear scope; never defines "global administrator" nor explains that calls run under the `system` tenant while acting on the tenant named in `TenantId`. |
| add-user-to-tenant | note | First-member exception is ambiguous about who may invoke it and which role may be granted; `UserId` says "token subject" but example is an email. |
| change-user-role | pass | Permissions, non-member rejection, and same-role no-op are all stated. |
| create-tenant | note | `Description` text says "omitted means none" but the schema lists it as `required`; no stated limits on `Name`. |
| disable-tenant | pass | Effect, permission, and rejection cases are clear. |
| enable-tenant | pass | Effect, permission, and rejection cases are clear. |
| get-tenant | pass | Fields, permission, and not-found vs forbidden behaviour are clear (minor nits F10, F14). |
| get-tenant-audit | note | `Stream` description uses unexplained jargon; `pageSize` behaviour above 200 unspecified; "profile" changes undefined. |
| get-tenant-users | pass | Ordering, permission, paging are clear (missing-tenant behaviour unstated, nit). |
| get-user-tenants | note | Unclear whether a caller lacking visibility gets a rejection or a filtered/empty list; no guidance on how a caller finds its own subject. |
| list-tenants | pass | Visibility, item fields, paging clearly described. |
| remove-tenant-configuration | pass | Permission and missing-key rejection clear. |
| remove-user-from-tenant | pass | Permission and non-member rejection clear. |
| set-tenant-configuration | pass | Limits given (nits: rejection on 100-key limit, value visibility to members). |
| update-tenant | note | Same `Description` required-vs-omitted contradiction as create-tenant; full-replace semantics can silently clear the description. |

Findings: F1 (minor) create-tenant `Description` required by the schema but described as omittable; F2 (minor) the same for update-tenant, with a rename silently clearing the description; F3 (minor) add-user-to-tenant first-member rule ambiguous and security-relevant; F4 (minor) `UserId` described as the token subject while the example is an email, and whether users are checked is unstated; F5 (minor) get-user-tenants does not say whether invisible memberships are rejected or filtered; F6 (nit) `Stream` jargon, ignored-or-rejected unstated; F7 (nit) payload `Cursor`/`PageSize` ignored-or-rejected unstated; F8 (nit) audit `pageSize` above 200 unstated; F9 (nit) "profile" undefined in audit `Category`; F10 (nit) per-tenant read `TenantId` not stated as required, unknown-tenant result unstated for get-tenant-users and get-tenant-audit; F11 (nit) no `Name`/`Description` length limits; F12 (nit) module description does not define global administrator or the `system` tenant; F13 (nit) set-tenant-configuration 101st-key rejection and member-visible values unstated; F14 (nit) get-tenant vs get-tenant-users guidance.

Could not determine from the dump alone: what "global administrator" means or how to tell; whether `aggregateId`/`entityId` call arguments should be set; whether the tool enforces the schema `required` list; last-owner rules, case sensitivity of `TenantId`/`Key`, whether `UserId` is validated against the IdP; result and error shapes; runtime truth of any described behaviour (`submittable: false`).

### Round 1 disposition

Applied to the Contracts before round 2:

- F1, F2: `Description` now says "send null for none" and "null clears it". To keep the description while renaming, send it again.
- F3: the exact rule is now stated: any caller may add the first member of a never-populated tenant, with any role. This is current aggregate behavior and is unchanged.
- F4: `UserId` is the subject (sub) claim and is not checked against the identity provider. Examples now use a subject-like value.
- F5: invisible memberships are left out, so the list can be empty.
- F6, F7: `Stream`, `Cursor` and `PageSize` now say "Ignored by this tool".
- F9: the Administrative category now lists its events.
- F10: per-tenant `TenantId` is marked Required. The missing-tenant result is stated for get-tenant-users (not found or forbidden) and get-tenant-audit (empty trail).
- F12: the module description now explains the `system` tenant and the global administrator.
- F13: the key limit's effect and member visibility are stated.
- F14: get-tenant points to get-tenant-users for long member lists.

Not applied:

- F8: the tool itself rejects `pageSize` above 200 before the Gateway.
- F11: the Tenants contracts declare no `Name` limit, and inventing one would be inaccurate.

## Round 2 (artifact `sha512-d+jqLErQXKa8R2h44oj/8KxEH89MTxdJplr+3d+HWjLBa0KO4B+Iqm+VnDbdT1Tl749PvGS6yNQlTTvmrfLTxQ==`)

**Overall verdict: PASS WITH NOTES.** No description blocks correct use; the notes are minor gaps and inconsistencies.

| Item | Verdict | Reason |
|---|---|---|
| module `tenants` | note | "acts on the tenant named by TenantId" is false for list-tenants and get-user-tenants; "platform tenant system" parses awkwardly. |
| add-user-to-tenant | pass | Purpose, permissions, first-member rule, duplicate rejection and role meanings are clear. |
| change-user-role | note | Self-demotion and demoting the last TenantOwner are not covered. |
| create-tenant | note | Calls the description "optional", but the schema requires the key (null allowed); no Name limits. |
| disable-tenant | pass | Clear; the blocked-changes list omits the description (nit). |
| enable-tenant | pass | Clear. |
| get-tenant | note | "Required." on TenantId vs a schema with no required list; paging arguments not addressed. |
| get-tenant-audit | note | Same "Required." mismatch; `Stream` unexplained, "Ignored by this tool" ambiguous. |
| get-tenant-users | note | Same "Required." mismatch. |
| get-user-tenants | note | Same mismatch; "use your own subject" assumes the caller knows it. |
| list-tenants | pass | Visibility, fields and paging clear. |
| remove-tenant-configuration | pass | Clear. |
| remove-user-from-tenant | note | Removing oneself or the last TenantOwner not covered. |
| set-tenant-configuration | pass | Limits, key cap, no-op and secrets warning given. |
| update-tenant | note | Replace semantics explained; no Name limits. |

Findings: 1 (minor) module wording; 2 (minor) create-tenant optional vs required `Description` key; 3 (minor) no `Name`/`Description` limits; 4 (minor) "Required." identifiers vs schema without `required`; 5 (minor) last-TenantOwner removal/demotion unstated; 6 (minor) caller may not know its own subject; 7 (nit) `Stream`; 8 (nit) payload `Cursor`/`PageSize` "ignored" ambiguous; 9 (nit) get-tenant is not paged; 10 (nit) `offset` support unstated; 11 (nit) `Unknown` in the role enum; 12 (nit) `TenantId` case sensitivity; 13 (nit) `Key` case sensitivity; 14 (nit) disable/enable omit the description; 15 (nit) same-role change "changes nothing" — accepted?; 16 (observation, owners to confirm) any caller may make themselves TenantOwner of a never-populated tenant.

Could not determine: error shapes and asynchronous rejection, result shapes beyond prose, how one becomes a global administrator, whether ignored members are stripped, retry/idempotency safety, "never had a member" vs "has no members".

### Round 2 disposition

Applied before round 3 (each claim checked against the aggregate and handlers):

- 1: the module wording now names list-tenants and get-user-tenants.
- 2: create-tenant says "a description (null for none)", and `Description` says
  the key is required.
- 4: per-tenant `TenantId` now reads "Required; a call without it is rejected"
  (the tool cannot derive the aggregate identifier without it). `UserId` now says
  to always set it: an omitted value does not default to the caller and usually
  returns an empty list.
- 5: change-user-role and remove-user-from-tenant state that the last TenantOwner
  may be demoted or removed, after which only a global administrator can manage
  members, roles and configuration. The aggregate has no last-owner guard.
- 6: get-user-tenants points to list-tenants for one's own tenants.
- 7, 8: `Stream`, `Cursor` and `PageSize` now read "Has no effect".
- 9: get-tenant states it is not paged.
- 10: the paged reads state that offset is not supported (it is rejected as
  `invalid-page`).
- 12, 13: `TenantId` and configuration keys are stated as case-sensitive
  (ordinal dictionaries and state keys).
- 14: disable and enable now include the description.
- 15: a same-role change is accepted and changes nothing.

Left for the Tenants maintainer:

- 3: no `Name` limit exists in the contracts.
- 4 (schema): marking the identifiers schema-required would need `required` or
  `[JsonRequired]` on the query classes, which changes the contract surface the
  spec freezes.
- 11: removing `Unknown` from `TenantRole` would change a wire type.
- 16: an existing aggregate rule, `HasMembershipHistory` bypass. Changing it would
  alter authorization; the spec forbids widening it, and narrowing it needs a
  decision.

## Round 3 (artifact `sha512-9wev5QoW4HAWFWh2PcLQ7AFzwGOSzN/Ig83DJolHt2XVjEvjP53v1auro9eV6svRycqhJamhisi2/o/xPsCcqQ==`)

**Overall verdict: PASS WITH NOTES.** No blocking findings; every description lets a caller decide when to use the operation and how to fill the payload. Four minor issues and several nits remain.

| Item | Verdict | Reason |
|---|---|---|
| Module `tenants` | pass | States the scope, the fixed `system` tenant versus the target `TenantId`, and what a global administrator is (nit F7). |
| add-user-to-tenant | pass | Permissions, first-member rule, duplicate rejection, role semantics and `Unknown` rejection are clear (nits F7, F8). |
| change-user-role | pass | Non-member rejection, same-role no-op and last-owner demotion are covered (nit F8). |
| create-tenant | note | `TenantId` rules are precise and the `Description` null handling matches the schema; no `Name` limits (F4). |
| disable-tenant | pass | What is blocked, who may call it, and the unknown or already-disabled rejection. |
| enable-tenant | pass | Clear, and symmetric with disable. |
| get-tenant | note | Not-found versus forbidden and "not paged" are clear; `TenantId` is called required but is not in the schema's required list (F1). |
| get-tenant-audit | note | The permission, filter semantics and From-after-To rejection are clear (F1, F3, nit F6). |
| get-tenant-users | note | Clear (F1, F3, nit F5). |
| get-user-tenants | note | The visibility rules are explained well (F2, F3, nit F5). |
| list-tenants | note | Clear, and the `{}` example helps (F3, nit F5). |
| remove-tenant-configuration | pass | Clear, with an exact case-sensitive key and missing-key rejection (nit F8). |
| remove-user-from-tenant | pass | Clear, including last-owner removal (nit F8). |
| set-tenant-configuration | pass | Upsert, limits, 100-key cap and the secrets warning (nits F8, F9). |
| update-tenant | note | Permissions and the replace-both behavior are clear, with the keep-description hint (F4, nit F10). |

Findings:

- F1 (minor): `TenantId` "Required" is not in the schema's required list, so the tool does not catch a missing value before submission.
- F2 (minor): "usually returns an empty list" for an omitted `UserId` is vague.
- F3 (minor): "offset is not supported" does not say whether it is ignored or rejected.
- F4 (minor): `Name` and `Description` have no stated limits.
- F5 (nit): the wording of the `pageSize` clamp.
- F6 (nit): `Category` also accepts null.
- F7 (nit): cross-references should use the full `tenants.` names.
- F8 (nit): member and configuration writes should state that an unknown or disabled tenant is rejected.
- F9 (nit): the characters allowed in `Key`.
- F10 (nit): re-sending unchanged update values.
- Design observation: any caller can make themselves TenantOwner of a never-populated tenant; the owners should confirm it is intended.

Could not determine: caller identity and how global administrators are made, whether the prose matches runtime behavior, real limits, result field shapes, cursor validity across changed filters, reserved identifiers, effects of disabling outside this module, read-after-write visibility, error documents.

### Round 3 disposition

There are no blocking findings, so no further review round was run. A later follow-up
review changed wording only: the four paged reads now say the next-page cursor
is the result document's `cursor` (also `paging.nextCursor` when a paging
argument was sent), and get-tenant says its paging arguments are "not used"
rather than "have no effect". The final artifact is therefore
`sha512-Od2hpUmNTlE9Zd6DV4LEQ+IdFIkDhp1X9Oo0M5EZ25ALSMMC0Udb3URXXV3bDLA/8KnQT658QjAQ9MdU+lcnnA==`, not the round-3 artifact.
These notes are left for the Tenants maintainer's review in the Tenants pull
request:

- F1: needs `required` or `[JsonRequired]` on the contract, which the spec freezes.
- F3: precise wording; offset is rejected as `invalid-page`.
- F4: no limits exist in the contracts.
- F2 and F5 to F10: wording.
- The design observation is listed in `approvals.md` §4.

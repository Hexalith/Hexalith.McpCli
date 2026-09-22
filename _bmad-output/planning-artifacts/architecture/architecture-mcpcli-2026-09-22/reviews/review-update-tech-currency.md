---
title: "Update reviewer gate: technology and reality check"
reviewed: ARCHITECTURE-SPINE.md
date: '2026-09-22'
status: findings
fallback: sequential review because subagents hit the usage limit
---

# Technology and reality check

## Verdict

**Pass after two reality fixes.** The five update decisions match the PRD and current EventStore source. The package versions already recorded in the memlog remain the current verified set; unreleased decorated Contracts versions are correctly left as an explicit prerequisite rather than guessed.

## High

### H1. Command extension pre-validation stops short of the pinned Gateway validator

`SubmitCommandRequestValidator` limits extensions to 50 entries, keys to 100 characters, values to 1,000 characters, total UTF-8 size to 64 KiB, and rejects dangerous characters and injection patterns. AD-9 validates only allowlist membership. That lets a request reach the Gateway with a failure FR-15 says Core must catch first.

**Autofix:** bind AD-9 to those pinned-version limits and report each violation under `/extensions` or `/extensions/<escaped-key>` before the client call.

## Medium

### M1. The manifest target is attached before its input item is guaranteed to exist

AD-4 says a target “after `ResolvePackageAssets`” reads `ReferenceCopyLocalPaths`. In SDK projects, `ReferenceCopyLocalPaths` is the resolved-reference output consumed after `ResolveReferences`; merely running after package asset resolution does not guarantee it has been populated.

**Autofix:** run the generation target after or depend on `ResolveReferences`, while still using `NuGetPackageId` to match the flagged direct references.

## Verified claims

- The pinned `SubmitQueryRequest` has no correlation or extensions member, and its validator rejects nonempty `AdditionalProperties`; AD-5/AD-9 correctly remove them from Queries.
- Both command and query validators require a nonempty aggregate identifier; AD-19 correctly forbids the old empty-string fallback.
- Tenant/domain and aggregate/entity patterns and length limits in AD-9 match the pinned validators.
- Command correlation is optional at the client contract; the Gateway defaults it to the message identifier when absent.
- The profile-store change is a PRD product decision and no longer claims compatibility with the admin CLI file.
- No technology version changed in this update. The existing version evidence remains applicable.

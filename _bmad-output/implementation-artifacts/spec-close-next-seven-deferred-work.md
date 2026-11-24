---
title: 'Close the next seven actionable deferred-work items'
type: 'bugfix'
created: '2026-11-24'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Implement the next seven deferred-work items, in priority order. Each one needs tests where they apply, a done mark in the ledger, and its own commit that references the item. Skip blocked or obsolete items, record why, and take the next item so that seven are completed in total. Afterwards, run the full Release build and test suite, fix any failures, and push directly to main.

</frozen-after-approval>

## Implementation Notes

- Priority follows the earlier batches: explicit severity, then original ledger order within a severity. Every High, Medium and Low entry still open is blocked, already resolved, or owned upstream, so selection continued with unranked entries in ledger order.
- Completed: Story 2.1 host configuration, Story 2.3 HTML-safe JSON escaping, Story 2.5 live Query proof criteria, Story 2.8 canonical ULID planning text, Story 2.8 executor order, Story 5.4 R54-D5 linked evidence roots and Story 5.6 local gitlink globs.
- Skipped with recorded reasons: Story 2.3 tenant and actor clearing and secret token input, Story 2.7 uncertain-failure identifiers, Story 2.8 Identifier Kind discovery and R54-D9 need decisions. The Story 2.11 ARM legs belong to Hexalith.CiCd, the Tenants Low items belong upstream, and the Story 5.4 owner items need approvals. The ledger's "Next seven follow-up dispositions" table lists them.
- The empty host builder moves the unused content root to the host's base directory. The boundary harness lifecycle expectation was updated in a separate commit.
- A concurrent `/pushall` session pushed the first Story 2.1 commit before an amend. Local work was rebuilt on `origin/main` without rewriting it, and later commits were published by that session as they landed.
- CLI text is ASCII after the encoder change, so non-ASCII output stays safe for Windows console code pages. Structured MCP content keeps the `Result` options.
- A fresh proprietary-surface scan reports the same 17 pre-existing errors and 494 surfaces before and after the census change.
- Story 1.7's blank executor operation was already refused by both heads; an MCP regression now protects that guard. Verified resolutions were added to original entries, including those closed by earlier follow-up tables.

## Review Triage Log

- **Medium, patched.** The host configuration test did not cover the variables the README names. A process test now sets `DOTNET_ENVIRONMENT` and `Logging__*` beside a malformed Development file.
- **Low, patched.** The host test dropped mutating verbs and checked documents loosely. Each verb now compares exit code, stdout and stderr with a clean run.
- **Low, patched.** The WSL `--cd` advice blamed a directory scan the empty builder removed. The README now attributes the stall to earlier releases.
- **Low, patched.** The README claimed all result text is ASCII, including module and operation tables, and called `'` a quote. The rule now covers JSON text and double quotes.
- **Low, patched.** The architecture and epic context still named only the `Result` options for emitted text. They now name the shared text writer.
- **Low, patched.** CLI tests built expected stdout with `McpCliJson.Result`. They now use the emitted text writer.
- **Medium, patched.** No head-level test covered configuration table values or result files. One now does, and it fails when either writer reverts.
- **Low, patched.** The MCP text test duplicated the shared session helper, and the text options depended on member order. Both are fixed.
- **Low, patched.** The Story 2.5 criteria named only Tenants and omitted the source-equivalence proof. They now cover the Gateway and require that proof.
- **Low, patched.** FR16 and AD-8 still said ULID without the canonical rule. Both now require canonical uppercase ULIDs.
- **Medium, patched.** The documented executor order had no test. Core tests pair an aggregate mismatch with each envelope or paging fault.
- **Low, patched.** The ancestor-link refusal reused the missing-root rule. It is now `root-path-not-canonical` and documented.
- **Low, patched.** The census test lacked a Compile positive case and a `?` wildcard case. Both are covered.
- **Medium, deferred, unverified.** The scanner still checks its root once and opens by path, so a concurrent link swap can redirect it. Ledger entry added.
- **Low, deferred.** The census refuses globs whose single-segment wildcards cannot reach a gitlink below their directory. No current root is affected. Ledger entry added.
- **False.** `HostBaseDirectory` hard-codes Release, but `BoundaryHeads` always launches the Release host, so the two agree in Debug runs too.
- **Low, rejected.** `Resolver.matches` keeps its own wildcard split. Sharing `glob_directory` would only touch reviewed substituted-branch code.

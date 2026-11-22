---
title: 'Resolve five conformance vector deferrals'
type: 'bugfix'
created: '2026-11-22'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem.** The offline v1 conformance validator can approve cursors and extensions that Core will reject. Three other ledger items still track routing identifier syntax, input Payload depth, and extension replay after their respective checks landed.

**Approach.** Resolve the five entries as one conformance maintenance task. Align offline cursor and extension checks with Core, verify the existing routing and depth boundaries, and exercise the isolated extension allowlist through both real Heads with a mixed-case key in the synthetic Command vector. Keep the v1 format and approved production vector bytes intact.

</frozen-after-approval>

## Implementation Notes

- Starting revision on `main` is `a8f2b5fa35227ee22ee925ce88640db745c9af8e`. Selected five actionable entries from the deferred-work ledger. The two extension-limit entries describe one defect. The change has a small test-tooling footprint and no unsettled product decision or new external effect. The user authorized the eventual push.
- Use `OperationExecutor.ValidateQueryArguments` for the UTF-16 cursor limit and `ExtensionValidator` for fixed extension restrictions. Implement the checks at `validate.py`'s shared step boundary, with located errors and boundary regressions in `test_validate.py`. The environment allowlist remains a replay concern.
- Verify the existing `aggregateId` schema references and `_payload_depth` with their all-position regressions. Add the mixed-case extension to `sample-command.json` so `run_loopback.py` checks the captured CLI and MCP requests. Document and close the five selected ledger entries with executed evidence.
- The check uses the Python standard library. To verify the Unicode compatibility ranges, enumerate U+0000–U+FFFF with `Regex(@"^\w\z", RegexOptions.CultureInvariant)` on .NET 11.0.0. Compare that set with `_is_dotnet_word` using each version's Unicode general categories. All 65,536 classifications matched with Unicode 13.0, 14.0, 15.0, 15.1, 16.0 and 17.0.
- The Release solution build passed with the workspace's .NET 11 SDK and installed Aspire bundle. All 46 approved historical and current vector files passed the offline validator and matched their approval hashes. Release sample validation passed 194 Python tests. Synthetic Release loopback passed the create, query and rename vectors through CLI and MCP, including the case-distinct extension keys across the two Command vectors. The live runner continuation test passed against the built Core validator.
- The exact commit message passed the released Builds guard's pinned commitlint policy with zero warnings and zero errors.

## Review Triage Log

- **Medium, patched.** Python's Unicode word categories varied by interpreter. Supplemented the categories to match .NET 11 and tested the Unicode 16 additions and older and newer exclusions.
- **Medium, patched.** A shared replay profile rejected separate calls with case variants of the same extension key. The profile now contains one case-insensitive key, with original keys and values verified in the captured requests.
- **Medium, patched.** Lone surrogate escapes could fail JSON decoding in Core preflight, and NUL could fail CLI process creation. The offline validator rejects both with a located cursor diagnostic.
- **Medium, patched.** Opaque cursors such as `--help` reached the CLI as option tokens. Replay binds them with `--cursor=<value>`. The loopback check covers both heads, and the live runner check verifies the CLI argument for a captured continuation cursor.
- **Low, patched.** JSON quoting of printable invalid keys changed their displayed pointer. Extension diagnostics now escape nonprintable characters for display and preserve the pointer spelling of printable characters.
- **Low, patched.** Added Query array depth coverage at 64 and 65 across all three call positions to corroborate the original report.

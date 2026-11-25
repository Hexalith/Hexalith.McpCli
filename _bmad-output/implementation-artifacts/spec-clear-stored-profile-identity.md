---
title: 'Clear a stored profile tenant or actor'
type: 'feature'
created: '2026-12-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close the Story 2.3 profile field-clearing deferral. Extend `config set` with an explicit `--clear` option for `tenant` and `actor`. Given a stored profile, clearing one field removes that setting and preserves the other fields and active selection. Invalid combinations fail before writing.

</frozen-after-approval>

## Implementation Notes

Reuse the existing field mutation and output preflight. Preserve validation of explicitly supplied values, including blank strings.

Review caught Boolean parsing of a value after `--clear`. The flag now takes no argument. Regression tests also inspect the stored JSON, clear an inactive profile, and cover output preflight with a populated actor. Existing profile mutation validation still applies to legacy records.

The Release build, all 245 config tests, and the output contract tests passed on Linux. The output suite includes ten Windows-only skips.

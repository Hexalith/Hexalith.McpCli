---
title: 'Close the next seven actionable deferred-work items'
type: 'bugfix'
created: '2026-11-24'
status: 'in-progress'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Implement the next seven deferred-work items, in priority order. Each one needs tests where they apply, a done mark in the ledger, and its own commit that references the item. Skip blocked or obsolete items, record why, and take the next item so that seven are completed in total. Afterwards, run the full Release build and test suite, fix any failures, and push directly to main.

</frozen-after-approval>

## Implementation Notes

- Priority follows the earlier batches: explicit severity, then original ledger order within a severity. Every High, Medium and Low entry still open is blocked, already resolved, or owned upstream. Selection therefore continued with unranked entries in ledger order.
- Selected: Story 2.1 host configuration (ledger line 207), Story 2.3 HTML-safe JSON escaping (283), Story 2.5 live Query proof criteria (308), Story 2.8 canonical ULID planning text (352), Story 2.8 executor order (386), and Story 5.4 R54-D5 and R54-D9 (1000, 1024).

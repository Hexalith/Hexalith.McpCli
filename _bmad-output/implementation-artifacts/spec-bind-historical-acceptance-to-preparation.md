---
title: 'Bind historical staged acceptance to preparation-time source evidence'
type: 'bugfix'
created: '2026-12-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close the Story 4.16 source-evidence comparison deferral in the retained paired verifier. Given authenticated preparation and acceptance artifacts, reject acceptance if its re-verified source evidence differs from the final preparation snapshot. Keep independent validation of each snapshot and of fresh publication-time source evidence.

</frozen-after-approval>

## Implementation Notes

Compare parsed receipt documents after package and preparation validation. The two retained Story 4.16 acceptance packets already have identical final preparation and acceptance receipts.

The comparator requires `--acceptance-source` when run directly. The retained publication verifier passes the receipt from the authenticated acceptance archive. Review added duplicate-member rejection for the three source receipts. The focused test accepts reformatting and refuses a CI rerun, a moved FR-22 upstream revision, an earlier preparation snapshot and a conflicting duplicate member while preserving the independent package checks.

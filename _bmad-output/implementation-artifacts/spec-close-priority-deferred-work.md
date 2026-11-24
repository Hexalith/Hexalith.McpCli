---
title: 'Close the next ten actionable deferred-work items'
type: 'bugfix'
created: '2026-11-24'
status: 'in-progress'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Complete ten still-relevant deferred items in severity order, using ledger order for ties. Track completed items separately from blocked and superseded findings. Each implementation carries its regression coverage and ledger closure in a separate validated commit. Run the full Release build and test suite before directly pushing main.

</frozen-after-approval>

## Implementation Notes

- The initial local and remote main revision was `fab626ebc6c433ee8195ca7013b7aec5f16f0f53`. Release restore and build passed.
- The baseline live preparation stopped at the Dapr runtime version check. The isolated host reported 1.19.1 and the qualified profile requires 1.19.2.

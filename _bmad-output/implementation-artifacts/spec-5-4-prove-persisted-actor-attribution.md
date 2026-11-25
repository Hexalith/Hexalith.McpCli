---
title: 'Prove persisted actor attribution through both heads'
type: 'bugfix'
created: '2026-11-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close the Story 5.4 persisted-actor deferral with execution evidence from the qualified synthetic cohort. Submit an independent create Command through each head and prove that its durable creation envelope records the configured credential's signed subject. Retain the earlier retirement verdict and its approval packet as historical evidence.

</frozen-after-approval>

## Implementation Notes

- The shared-head boundary supplies a configured session Actor that differs from the credential’s signed subject. It binds the accepted correlation ID to the captured Gateway request and reads the signed principal and correlation ID from the corresponding durable creation event.
- The boundary receipt records an assertion for each head. Synthetic identity and credential values stay outside the receipt.
- Review confirmed that the qualified EventStore envelope carries the subject and correlation ID, and that the prior boundary receipt consumers accept additional cases.

## Verification

Qualified isolated run `11b8663ec0114d87ac869ac44c5d0255` on candidate `826fc016a1daaef3cf296a76c1b2e9a64a5aa044` passed `SharedHeadsPreserveAuthorizationAndDeactivationSafety`. The CLI and MCP records both match the persisted actor to the signed subject and the event correlation to the accepted Command. The boundary receipt SHA-256 is `6a6beeaa1f9826f985637adf82c0e1757948bd26a5b77bc6edddbda4db4ce0af`. The native selection SHA-256 is `9d90f7d0a73c70e98693d4c45b6750bf4c55868b0499b53e8b88bdf411de36be`.

The final change keeps attribution metadata checks specific to creation. The persisted-state unit tests cover missing and mismatched subject or correlation and preserve the earlier event-type and sequence checks.

---
title: 'Protect profile credential entry and transport'
type: 'feature'
created: '2026-11-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close the Story 2.3 credential-entry deferral through approved Story 5.16. Give profile creation and rotation explicit non-echoing terminal and redirected stdin modes. Keep rotation in the locked store transaction and preserve unrelated settings. Refuse bearer credentials on non-loopback HTTP for both heads and on profile mutation. Update operator procedures and verify the successful and rejected paths with synthetic credentials.

</frozen-after-approval>

## Implementation Notes

- Creation and rotation use `--token-input prompt|stdin`. Rotation checks the Gateway URL again under the profile lock and observes cancellation before atomic replacement.
- The two heads require HTTPS or a loopback IP address for a bearer credential. Credentialed HTTP bypasses proxies.
- The Release solution build, focused CLI process tests, and Core profile tests passed. A Linux pseudoterminal verified successful non-echoing entry and Ctrl+C preservation.

## Review Triage Log

- High, patched. Credentialed HTTP bypasses proxies and the HTTP exception accepts only loopback IP addresses.
- High, patched. The locked replacement refuses a changed Gateway URL during rotation.
- Medium, patched. Lock acquisition and file replacement observe cancellation.
- Medium, patched. Private add validates the URL before requesting input and checks UTF-8 and line endings without echoing credential content.
- Medium, verified. Tests exercise real process input, a proxy decoy, both startup channels, and preservation of profile state. The Linux PTY check covers interactive success and cancellation.

---
title: 'Verify signatures on historical public package downloads'
type: 'bugfix'
created: '2026-12-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close the Story 4.18 public package signature deferral in the retained bootstrap and paired helpers. Given a downloaded public package, both callers require successful cryptographic verification before comparing consumer contents. Missing, invalid, or uncheckable signatures fail the verification without a second push.

</frozen-after-approval>

## Implementation Notes

Put the check in the helpers' shared public download path. Use the installed .NET SDK’s NuGet verifier and a bounded process deadline. Keep the digest and consumer-content comparison as independent checks.

The shared download helper verified both published 2.0.1 packages from NuGet.org. Tests exercise unsigned and malformed archives through the real verifier and a timeout through a mock. Once a download returns HTTP 200, verification runs once, independently of the publisher’s existing bounded wait for HTTP 404 during indexing.

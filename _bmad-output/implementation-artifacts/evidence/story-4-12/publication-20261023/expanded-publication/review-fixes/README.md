# Focused review corrections

These checks cover the edited topology files only. Parent full verification is
separate. No McpCli commit or index change was made; the frozen source packet was
not modified. Actual user AppHosts and Redis were preserved.

- Port conversion is inside Program's existing diagnostic boundary. Launch tests
  assert exit 2, empty stdout and exact stderr for malformed/overflowing values.
  Guard and launch tests align the helper's 1024–65535 range; 1023 is rejected,
  1024 passes, and an occupied-port listener remains bound during invocation.
- Nonzero Dapr-list failure includes a 512-character stderr excerpt; executable
  stub cases cover both normal detail and truncation.
- The fixture supplements the standard basic Dapr probe with a three-second CLI
  version deadline, mandatory mTLS credentials/settings and a three-second Sentry
  transport probe. Missing requirements use the standard skip prefix. Child
  smoke tests protect actual fixture invocation; immutable environment and
  ephemeral-port tests cover missing/available Sentry without binding host 50001.
- Actual AppHost composition evaluates both app and sidecar environments without
  starting resources or emitting token values. All three pairs share distinct
  generated nonempty tokens. This revealed that the pinned Gateway helper also
  needed explicit generated-token wiring; it is now included. The same test
  checks every sidecar ACL attachment and actual Gateway content root.
- Seven source-removal/substitution controls each built and failed the covering
  composition test. Removing the actual fixture's prerequisite call also failed
  the child-process covering tests. All sources and binaries were restored and
  positive checks passed afterward. Token hashes/lengths are used; no raw token
  is written to evidence.
- The single discovered live smoke now requires real 401 responses to missing
  and malformed JWTs before its one successful authenticated query. All requests
  have cancellation deadlines. A real local 403 additionally covers the pinned
  client exception, status and exact contextual failure diagnostic.
- README requires disposable isolated Dapr/private Redis and an outer deadline.
  The bounded bootstrap recreated all four native binaries from official pinned
  image digests, verified each recorded SHA-256 and removed only its never-started
  extraction containers. It never connected to host Redis or stopped processes.

Focused positive results: configuration 28, launch 18, prerequisites 10 and HTTP
boundaries 2, all passed with zero skips/failures. Discovery is still exactly one
smoke. The final private smoke passed: one executed, zero failed/skipped, 22.789
seconds (outer command 23.051 seconds). All four owned infrastructure processes
exited 0. Raw asynchronous resource logs record both 401 completions; the final
success completion line was not flushed, so success is established by the passed
pinned-client successful-document assertions, not an invented 200 log. See
`live-auth-enforcement/` for result, sanitized extract and original raw-log hashes.

Earlier failed focused attempts are retained separately. `focused-results.json`
contains the initial exact-wording/token finding; `focused-second-results.json`
contains the earlier basic-skip wording failure. They are superseded by the
successful restored/final test receipts. `composition-removal-controls.json` and
`prerequisite-invocation-control.json` retain the executed negative controls.

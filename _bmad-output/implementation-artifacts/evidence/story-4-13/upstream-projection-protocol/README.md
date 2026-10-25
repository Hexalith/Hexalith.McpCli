# Parties projection protocol serialization candidate

The real Parties host applied its broad string-enum converter to SDK protocol
responses. The published DomainService 3.127.0 endpoint returns
`Results.Ok(ProjectionDispatchResponse)`, while the Gateway deserializes the
outcome using plain `JsonSerializerDefaults.Web`. String status values fail that
reader, so the Gateway defers delivery without completing the reservation.
This matches the retained full-lane mutation failures: initial read models are
persisted but later heads repeatedly report `delivery_in_progress`.

The bounded candidate uses the existing .NET 10
`JsonNumberEnumConverter<ProjectionDispatchStatus>` ahead of the broad converter
in `PartiesServiceCollectionExtensions.AddParties`. It leaves
`PartiesJsonOptions.Default`, Contracts, domain payload enum strings and SDK
packages unchanged. No platform publication is required.

`candidate.json` identifies the isolated owner worktree, base commit, exact
source hashes and patch hash. `candidate.patch` contains only the host JSON
configuration repair and new `PartyProjectionProtocolSerializationTests.cs`.
The worktree also retains the earlier query-discovery qualification source,
which is explicitly excluded from this patch. The active owner has unrelated
changes in the same production configuration file; it was never edited.
`owner-preservation.json` confirms its staged diff and the relevant working
files remain byte-identical.

The new two-case test starts the actual host, resolves its real HTTP JSON
options and executes the SDK's `Results.Ok` response path. Both cases fail on
the unchanged host because `outcomes[0].status` is a string, rather than a
number. After the narrow override, both pass: Completed and AlreadyCompleted
serialize as 0 and 1, plain-Web Gateway decoding succeeds, and a real
CreateParty payload retains its camel-case fields, omitted nulls and string
PartyType. The canonical PartiesJsonOptions.Default string convention remains
unchanged. No test-specific JSON configuration or projection handlers are
registered.

Exact verification commands, working directories, exits and output are kept
beside this note:

- `red-build.json` preserves the initial test-helper CA2007 build rejection.
  ConfigureAwait was added to the helper; this is separate from the wire defect.
- `red-build-2.json`: package-mode Release warnings-as-errors build passes,
  with zero warnings/errors.
- `red-wire.json`: two cases fail exactly at Number versus String.
- `green-build.json`: same Release build passes, zero warnings/errors.
- `green-wire.json`: both serialization cases pass, zero failures/skips.
- `green-query.json`: all four existing actual-host query compatibility cases
  pass, zero failures/skips.
- `diff-check.json` preserves Git's default rejection of CRLF as whitespace;
  the repository's .editorconfig requires CRLF. `diff-check-crlf.json` allows
  CRLF explicitly and passes without changing repository configuration.

The qualified repair is committed and pushed at
`d83fec24167aafd4edfc4d2f7310d6a87a218a1c`, in
[Parties PR #58](https://github.com/Hexalith/Hexalith.Parties/pull/58). The root
reference is clean at that exact commit, and its Release server build succeeds
(`integrated-server-build.json`). `commitlint.json`, `commit.json`, `push.json`
and `pull-request.json` retain the exact validated message and integration steps.
No owner main merge or package publication has occurred.

PR CI remains red on the same five tests as main before this repair: the public
Contracts snapshot and four existing platform/source-receipt checks.
`ci-baseline-comparison.json` lists the identical failing names and hashes the
exact main/candidate raw logs retained as gzip archives. Automated code/security
reviews, CodeQL and the successful commitlint run pass; the PR is left open.
The owner snapshot and human source evidence have not been rewritten to hide
these unrelated failures.

Full live acceptance is determined separately by the fresh complete lane under
`../live-complete/`. The previous 18-pass/three-failure full-lane receipt remains
historical evidence and cannot grant completion.

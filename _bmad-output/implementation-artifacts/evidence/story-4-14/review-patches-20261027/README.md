# Story 4.14 review patch qualification — 2026-10-27

All 15 patches D1, D2 and P1–P13 are implemented. Preparation records each source
server's resolved EventStore package version, verifies the pinned Aspire 13.6.1
release archive before extraction, checks exact OpenSSL 3 sonames, and retains
cancellation time within the hook/step budgets. Vector failures now retain their
Operation/result/error and name failed Operations in the CI log. Regression
fixtures independently protect receipt containment, smoke cleanup, runtime count,
generation log/XML redaction, evidence symlinks, preparation identity, built tests,
tool/binary admission, outer deadlines and refusal of stale diagnostics.

The owning Builds change is the documentation-only commit
`857ef02dbb4bde1bd4e678546aa41e73fb7d68b1`, directly based on the former pin
`35587cfd104c5750d8ec3c0716933f386d6a0232`. The caller pin and gitlink select the
new revision. [Exact owner patch](builds-docs.patch), [local Git bundle](builds.bundle),
[323 passing workflow assertions](builds-workflow-tests.txt),
[commitlint qualification](builds-commitlint.txt), and both actionlint outputs
are retained. The owner worktree is `/tmp/mcpcli-414-builds-review-20261027`;
the existing owner main checkout was preserved.

| Check | Result |
| --- | --- |
| Fresh solution restore and Release `-warnaserror` build | Passed; zero warnings/errors |
| Six focused test projects | 1,531 passed, zero failed, five existing non-live skips |
| Complete Python suite | 137 passed |
| Guard-removal mutations | All 18 caught by assertions |
| Caller deadline/evidence input removals | All three caught by assertions |
| Exact preparation/runner hooks | Passed in 22.135 / 820.096 seconds |
| Live semantics | 21 passing vectors and independent passing authenticated smoke |
| Live ownership and XML | 22 owned cleanup receipts and 22 passing, unskipped cases |
| Business effects | 144 phases, 53 single Command submissions, 53 distinct message IDs, 91 Query attempts |
| Retained live archive | All 1,455 files compared byte-for-byte with original evidence |

[Verification index](verification.json), [source fingerprints](source-hashes.json),
[complete Python output](python-tests.txt), [mutation proof](mutations.json),
[caller mutation proof](caller-mutations.json), and [exact live commands](live-commands.json)
record the checks. Per-project .NET output, syntax checks and preparation/runner
stdout/stderr are adjacent. [Live archive](live-ci.tar.gz) contains the complete
support-safe evidence directory; [audit](live-audit.txt) verifies coverage, XML,
cleanup, Command submissions and every archived file. Credentials, private
runtime state and native binaries are excluded; the archive has no JWT or PEM
credential candidates. Original runtime/evidence paths remain in the index for
independent inspection before task-owned cleanup.

The real preparation hid existing Aspire launchers from PATH, exercising the
first-install archive path. [Release qualification](aspire-release.json) binds
the published GitHub asset digest, downloaded archive, selected executable and
all 490 expected bundle payload files. Preparation records EventStore/Tenants
servers at EventStore 3.128.0 and Parties at 3.127.0; McpCli's own restore retains
3.127.0. Approved Contracts/vector bytes and dependency-policy versions are
unchanged.

The new Builds revision is qualified locally and has not been published. This
implementation stage permits no pushes or Git remote operations; hosted
resolution and acceptance of the updated caller remain the existing integration
follow-up. The previous pin's recorded hosted acceptance remains historical
proof. Existing Dapr port-bind intermittence and agent-context package-version
wording stay deferred. Paired package publication remains disabled.

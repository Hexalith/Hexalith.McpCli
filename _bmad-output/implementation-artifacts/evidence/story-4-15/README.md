# Story 4.15 local implementation evidence

The owning AI.Tools candidate adds migration plan **1.0.0**, links it from the
published ownership rule and README, and retains the existing rule verbatim.
The [plan snapshot](upstream/hexalith-mcpcli-migration-instructions.md) lists the
legacy servers, Projects plug-in, five frozen module CLIs and EventStore Admin's
successor inventory gap. Six immutable inventory links bind exact McpCli commit
`c694bff5a29073bee6848b88c142f7da23efcf85`. Session scope approval is distinct
from unasserted external owner approval; deferrals, compatibility behavior,
coordinated FrontComposer/Projects retirement and Memories' later HTTP per-user
identity prerequisite are preserved. No operation disposition is changed and no
retirement or runtime behavior is authorized.

## Published baseline and local candidate

The core rule was directly integrated into published AI.Tools main as
`3f194e17174994d308ec84af9ee2b5aa68674d0d`, whose parent is
`5f93d2ec8239494852c97032c819cb1689939e36`. No merge commit or PR is invented.
The root baseline at `c694bff5a29073bee6848b88c142f7da23efcf85` already pins
that revision. The root reference's local `HEAD`, `main` and `origin/main`
agree; these are previously available local observations, not a fresh remote
main check. That revision does not contain the new migration plan.

The clean owning checkout at `/home/administrator/projects/hexalith/aitools`
was safely fast-forwarded from `5bf12bbcec3d8a2016396c27439de9b5107f9e5d` to
that published baseline using local pack/unpack, followed by `git merge
--ff-only`. [Preparation commands](offline-baseline-preparation.json) preserve
full identities and exact results. The owner's remote-tracking ref remains at
the older revision because no fetch occurred. Three candidate documents are
uncommitted in the owner; no reference contents or root gitlink were changed.

`upstream-candidate.patch.gz` retains the raw patch, including existing CRLF
policy bytes; decompress it before `git apply`. `upstream-candidate-files.tar.gz`
retains the three exact candidate files. Applying the patch to an archive of
published baseline `3f194e17174994d308ec84af9ee2b5aa68674d0d` reproduces every
candidate byte. The browseable plan is an exact copy. [File hashes](files.sha256.json)
bind the packet and candidate contents; [verification](verification.json)
records exact commands, exits, checks and inventory hashes.

## Verification and limits

The local synchronization script and both explicit `cmp` commands pass without
editing any entry point. In temporary copies, separate drift in AGENTS, CLAUDE
and Copilot causes the script to exit 1 and name the changed comparisons;
restoring the temporary bytes returns success. Immutable inventory targets,
version pins, topical links, policy preservation, patch/archive reproduction,
root containment and unchanged release guards are checked offline. Both paired
release entry points still refuse before any remote request.

Root `git diff --check` passes. Plain owning `git diff --check` exits 2 because
its existing CRLF policy file has no whitespace attributes: the six added CRLF
lines are reported as trailing whitespace. Preserving the established bytes,
`git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff
--check` passes. This qualified result is not an unqualified plain-command pass.
No .NET, live, hosted or remote check is claimed for this documentation change.

The [owning commitlint probe](owning-commitlint-availability.json) finds no
tracked package, lock or commitlint configuration. An offline cached CLI 21.2.4
is callable, but its resolved rules are empty. The empty-input probe exits 1
because no message was supplied; that is not a rejected message or successful
validation. No commit-message candidate was created, presented or used. Owning
pinned validation must be resolved before any later candidate commit.

## Outstanding completion and release requirements

Story 4.15 remains **in-progress**, and the instruction prerequisite remains
**incomplete**. The implementation-stage instruction prohibits pushes and remote
operations. The finished rule and plan still require review and authoritative
upstream main integration, then a qualified published revision in the root
baseline with fresh ancestry/containment, file hashes and synchronization
results. A local patch or open PR cannot satisfy those requirements.

Paired-release readiness remains blocked. Story 4.16 owns paired-publication
implementation; dependency, inventory, authorization, loopback, live, package
and retirement gates remain independent. The Abstractions-only bootstrap stays
exempt. No publication, external owner approval or retirement is asserted.

# Story 5.3 verification

This evidence belongs to
[spec 5.3](../../spec-5-3-enroll-replacement-contracts-and-profiles.md). It
records approved Parties inventory amendments 1.1.0 and 1.2.0, including the
C05 pre-read correction, the C06 and C07 resolutions, the G6 profile rules and their
verification. It grants no execution, parity,
publication or retirement authority.

## Approval state

**1.1.0 approved (2026-11-09).** The owner selected "Approve Parties 1.1.0
as Parties owner" after seeing its exact word diff and hash. The original
[receipt](approval/approval.json) and the preserved
[1.1.0 inventory and receipt](approval/1.1.0/) retain those exact approved bytes.

**1.2.0 approved (2026-11-09).** The user replied "approve" directly to the
request to approve the displayed 1.2.0 diff and SHA-256 as Parties owner. The
[approval receipt](approval/amendment-1.2.0.json) records the accepted action
label "Approve Parties 1.2.0 as Parties owner", the separate verbatim response
"approve", the existing approver identity, the Parties owning-maintainer
role, both inventory hashes and the prior receipt hash. The approved inventory
bytes are unchanged from the presented candidate. Inventory 1.2.0 is now the
latest approved version; the C05 ledger item and all three review findings are
closed. A subsequent byte change requires another exact-byte approval.

## Pins

| Input | Revision |
| --- | --- |
| Original implementation baseline | `4bc4be5deca889d1594b0d367e313592c9421fe8` |
| Review pass 2 baseline | `1ff2052653247a5fcca6e322c6da6ea1723a2eb1` (uncommitted documentation patches on top) |
| `references/Hexalith.EventStore` gitlink | `3d4ba67db99f2f0bcd64b7d353609b555870cc9b` |
| `references/Hexalith.Parties` gitlink | `1308ad000c79ebc394fc395588f9af91092e8c4c` |
| Parties inventory source revision | `493730941329d1bca3b4f6b2f6a67ffe305c2443` (unchanged) |
| Enrolled Parties Contracts | `Hexalith.Parties.Contracts` 1.5.1 (unchanged) |
| Platform rule for decision 1 | `references/Hexalith.Platform/_bmad-output/planning-artifacts/architecture/architecture-platform-2026-09-27/ARCHITECTURE-SPINE.md:182` at `01e5b6530af96ad6eaa69cc1867d43def56c43ca` |

No Parties Contracts upgrade is made. No release after 1.5.1 closes C06 or C07:
upstream `50904cc4ba53c9b0b2c082d5872a0d276be8f5c3` (`v3.0.0-109-g50904cc4`,
the 3.1.0 line) still lists both as open gates in its `README.md:197` and
`:230`, and its Query declarations no longer carry the `ProjectionActorType`
that 1.5.1 declares (`src/Hexalith.Parties.Contracts/Queries/GetParty.cs:10` at
`v1.5.1`). Vectors, live plans, artifact approvals and the dependency policy
are unchanged.

## Amendment hash chain

| Version | Path | SHA-256 |
| --- | --- | --- |
| 1.0.0 (approved, A1) | `approval/1.0.0/parties-migration-inventory-v1.md` | `c4db93be3422adff86568225d3dfed129b5c546bd4306c9ff3d0bbf0d0441a8f` |
| 1.1.0 (approved, Story 5.3) | `approval/1.1.0/parties-migration-inventory-v1.md` | `8fc4078842d141151c521f0288f1eb7f9b984505c7b4a1458fa40de8dba4c51e` |
| 1.2.0 (approved, review pass 2) | `../../parties-migration-inventory-v1.md` | `2f359904fe87fab8325b6fc759676c1fc792a27e0857d47631d8eeec8b420a28` |

The preserved 1.0.0 bytes equal the inventory at the pinned baseline
`4bc4be5deca889d1594b0d367e313592c9421fe8`, where it was last changed in
`3dd4976812d48c6ba6bb578dce34f3041569f5fb`. For a word-level review:

    git diff --no-index --word-diff=plain \
      _bmad-output/implementation-artifacts/evidence/story-5-3/approval/1.0.0/parties-migration-inventory-v1.md \
      _bmad-output/implementation-artifacts/evidence/story-5-3/approval/1.1.0/parties-migration-inventory-v1.md

For the 1.2.0 correction, compare the preserved 1.1.0 file to the main
inventory. Only C05's acceptance cell and the version/amendment narrative
change; C06, C07, every other row, all targets and all dispositions are unchanged.

Changed rows in the historical 1.0.0 to 1.1.0 amendment: C05, C06 and C07. Narrative changes: the version and amendment
frontmatter, the introduction pointer, the coverage-rule eligibility wording,
the new **A1 amendment 1.1.0** subsection, and the scope of the Story 4.1
checker with the pointer to this file. The source revision, the 24 row
identities (L01–L05, T01–T07, C01–C08, N01–N04), the targets, every
disposition and coverage value, the routing decision and the A1 limits are
unchanged. `tools/conformance-vectors/v1/modules/Hexalith.Parties.Contracts/approval.json`
binds `tools/inventory-coverage/v1/parties-approved.json`, which is unchanged;
no CI gate hashes this markdown.

The Story 4.1 checker (`../story-4-1/verification.md`) asserts
`inventory_version: '1.0.0'` and reads the live inventory path, so it covers
the approved 1.0.0 bytes at its pinned Parties revision and fails on 1.1.0.

## Reproducible static check

The block below checks both amendments without network access, restores,
builds or reference changes. It verifies the preserved 1.0.0 bytes against
`4bc4be5` and the preserved 1.1.0 bytes against `1ff2052`, retains the 24 row
IDs, and checks that 1.0.0 to 1.1.0 appends only C05/C06/C07 acceptance text.
It then checks that 1.1.0 to 1.2.0 changes only C05's acceptance cell, verifies
all three inventory hashes and the prior receipt hash, and checks the new
receipt in pending or approved mode. Approved mode requires the exact owner
label, agreement across the instruction/decision/authority-confirmation fields,
the same signatory and the Parties owning-maintainer authority. Pending mode
asserts that no approval has been recorded.

Extract and run it from the repository root. It writes to a fresh task-owned
`mktemp` file, so concurrent sessions cannot run each other's extracted script:

    script=$(mktemp "${TMPDIR:-/tmp}/mcpcli-story-5-3-static-check.XXXXXX")
    python3 - "$script" <<'PY'
    import sys
    from pathlib import Path
    text = Path('_bmad-output/implementation-artifacts/evidence/story-5-3/verification.md').read_text()
    Path(sys.argv[1]).write_text(text.split('```bash\n', 1)[1].split('\n```', 1)[0] + '\n')
    PY
    bash -e "$script"

```bash
set -e
python3 - <<'PY'
import hashlib
import json
import re
import subprocess
from pathlib import Path

BASE = '4bc4be5deca889d1594b0d367e313592c9421fe8'
INVENTORY = '_bmad-output/implementation-artifacts/parties-migration-inventory-v1.md'
EVIDENCE = Path('_bmad-output/implementation-artifacts/evidence/story-5-3/approval')
A1_CELL = ' | [A1](#a1-session-approval-2026-10-16) |'
ROW_IDS = ([f'L{i:02d}' for i in range(1, 6)] + [f'T{i:02d}' for i in range(1, 8)]
           + [f'C{i:02d}' for i in range(1, 9)] + [f'N{i:02d}' for i in range(1, 5)])

def check_approval_labels(receipt, amendment, expected_label):
    assert (receipt['exact_approval_instruction'] == amendment['exact_approval_instruction']
            == amendment['approval_decision'] == receipt['exact_authority_confirmation'] == expected_label), 'approval labels must match the exact owner instruction'
    assert receipt['approver'] and receipt['approver'] == amendment['approver'], 'approval signatories differ'
    assert receipt['approval_authority'] == 'requesting-user-owning-maintainer'
    assert receipt['authority_scope'] == ['Parties owning maintainer']


committed = subprocess.run(['git', 'show', f'{BASE}:{INVENTORY}'], check=True, capture_output=True).stdout
preserved = (EVIDENCE / '1.0.0/parties-migration-inventory-v1.md').read_bytes()
current = (EVIDENCE / '1.1.0/parties-migration-inventory-v1.md').read_bytes()
assert current == subprocess.run(['git', 'show', f'1ff2052653247a5fcca6e322c6da6ea1723a2eb1:{INVENTORY}'], check=True, capture_output=True).stdout
assert (EVIDENCE / '1.1.0/approval.json').read_bytes() == (EVIDENCE / 'approval.json').read_bytes()
assert (EVIDENCE / '1.1.0/approval.json').read_bytes() == subprocess.run(['git', 'show', f'1ff2052653247a5fcca6e322c6da6ea1723a2eb1:{EVIDENCE}/approval.json'], check=True, capture_output=True).stdout
assert preserved == committed, 'the preserved 1.0.0 bytes differ from the pinned baseline inventory'
old_sha = hashlib.sha256(preserved).hexdigest()
new_sha = hashlib.sha256(current).hexdigest()
print(f'1.0.0 sha256 {old_sha}')
print(f'1.1.0 sha256 {new_sha}')


def version(text):
    front = text.split('---\n', 2)[1]
    return re.search(r"^inventory_version: '([^']+)'$", front, re.M).group(1)


def rows(text):
    found = {}
    for line in text.splitlines():
        match = re.match(r'^\| ([LTCN][0-9]{2})(?: / [A-Za-z0-9]+)? \|', line)
        if match:
            assert match.group(1) not in found, f'duplicate row {match.group(1)}'
            found[match.group(1)] = line
    return found


old_text, new_text = preserved.decode(), current.decode()
assert version(old_text) == '1.0.0', version(old_text)
assert version(new_text) == '1.1.0', version(new_text)
old_rows, new_rows = rows(old_text), rows(new_text)
assert sorted(old_rows) == sorted(ROW_IDS) == sorted(new_rows), (sorted(old_rows), sorted(new_rows))
changed = [row for row in ROW_IDS if old_rows[row] != new_rows[row]]
assert changed == ['C05', 'C06', 'C07'], changed
for row in changed:
    assert old_rows[row].endswith(A1_CELL) and new_rows[row].endswith(A1_CELL), row
    assert new_rows[row].startswith(old_rows[row][:-len(A1_CELL)] + ' '), f'{row} changes more than its appended text'

receipt = json.loads((EVIDENCE / 'approval.json').read_text())
amendment = receipt['amendments'][0]
inventory = receipt['inventories'][0]
assert receipt['schema_version'] == 1 and receipt['decision'] in ('pending', 'approved'), receipt['decision']
assert (amendment['from_version'], amendment['to_version']) == ('1.0.0', '1.1.0')
assert amendment['from_sha256'] == inventory['preserved_sha256'] == old_sha
assert amendment['to_sha256'] == new_sha, 'the receipt does not bind the current 1.1.0 bytes'
assert inventory['row_ids'] == ROW_IDS and amendment['changed_rows'] == changed and amendment['added_rows'] == []
if receipt['decision'] == 'approved':
    assert inventory['approved_sha256'] == new_sha
    check_approval_labels(receipt, amendment, 'Approve Parties 1.1.0 as Parties owner')
else:
    assert inventory['approved_sha256'] is None and receipt['exact_approval_instruction'] is None
print(f"Static check passed: 24 rows, changed {', '.join(changed)}; receipt decision {receipt['decision']}.")

candidate = Path(INVENTORY).read_bytes()
candidate_sha = hashlib.sha256(candidate).hexdigest()
assert version(candidate.decode()) == '1.2.0'
candidate_rows = rows(candidate.decode())
assert sorted(candidate_rows) == sorted(ROW_IDS)
assert [row for row in ROW_IDS if new_rows[row] != candidate_rows[row]] == ['C05']
before_cells, after_cells = new_rows['C05'].split('|'), candidate_rows['C05'].split('|')
assert len(before_cells) == len(after_cells)
assert before_cells[:3] == after_cells[:3] and before_cells[4:] == after_cells[4:], 'C05 changes outside its acceptance cell'
for field in ('source_repository', 'source_revision', 'source_spec', 'maintainer_approval_ref', 'amendment_source_spec'):
    pattern = rf'^{field}: (.+)$'
    assert re.search(pattern, new_text, re.M).group(1) == re.search(pattern, candidate.decode(), re.M).group(1), field
candidate_receipt = json.loads((EVIDENCE / 'amendment-1.2.0.json').read_text())
candidate_amendment = candidate_receipt['amendments'][0]
candidate_inventory = candidate_receipt['inventories'][0]
assert candidate_receipt['decision'] in ('pending', 'approved')
assert (candidate_amendment['from_version'], candidate_amendment['to_version']) == ('1.1.0', '1.2.0')
assert candidate_amendment['from_sha256'] == candidate_inventory['preserved_sha256'] == new_sha
assert candidate_amendment['to_sha256'] == candidate_inventory['proposed_sha256'] == candidate_sha
assert candidate_inventory['row_ids'] == ROW_IDS and candidate_amendment['changed_rows'] == ['C05'] and candidate_amendment['added_rows'] == []
assert candidate_receipt['prior_approval']['sha256'] == hashlib.sha256((EVIDENCE / '1.1.0/approval.json').read_bytes()).hexdigest()
if candidate_receipt['decision'] == 'approved':
    assert candidate_inventory['approved_sha256'] == candidate_sha
    check_approval_labels(candidate_receipt, candidate_amendment, 'Approve Parties 1.2.0 as Parties owner')
else:
    assert candidate_inventory['approved_sha256'] is None
    assert candidate_receipt['exact_approval_instruction'] is None and candidate_receipt['exact_authority_confirmation'] is None
    assert candidate_receipt['approver'] is None and candidate_receipt['approved_on'] is None
    assert candidate_receipt['approval_authority'] is None and candidate_receipt['authority_scope'] == []
    assert candidate_amendment['exact_approval_instruction'] is None and candidate_amendment['approval_decision'] is None
    assert candidate_amendment['approver'] is None and candidate_amendment['approved_on'] is None
print(f'1.2.0 sha256 {candidate_sha}')
print(f"1.1.0 -> 1.2.0 static check passed: 24 rows, changed C05; receipt decision {candidate_receipt['decision']}.")

PY
```

## C05 delete oracles

The aggregate's deactivate guards and legacy tool body are unchanged since
`4937309`; the SDK detail read must be evaluated separately. Approved 1.1.0
omitted a pre-read failure and overstated the legacy missing/erased oracles.
The owner-approved 1.2.0 C05 correction records the following branches and
supersedes the incomplete 1.1.0 oracle.

| State / selected path | McpCli `parties.deactivate-party` | Legacy `delete_party` |
| --- | --- | --- |
| Missing aggregate | Direct Command rejection: `gateway_error` 404, reason `party-not-found` | Absent SDK detail causes pre-read HTTP 500 / `downstream_failed`, with no Command submission. `not_found` applies if the selected query path returns 404/410, or an active stale read permits submission and the Command then rejects with 404. |
| Erased or erasure in progress | Direct Command rejection: 422, reason `party-erasure-in-progress` | The cited current SDK suppresses erased detail, giving pre-read 500 / `downstream_failed`. A successful inactive read gives idempotent success without submission; a successful active read permits a Command whose 422 maps to `validation_failed`. The pinned `4937309` SDK lacks the current `IsErased: false` guard. |
| Processing restricted | Direct Command rejection: 422, reason `party-processing-restricted` | Successful inactive read: idempotent success without submission. Successful active read: submit, then Command 422 / `validation_failed`. Failed SDK pre-read: `downstream_failed`, no submission. |
| Inactive, after aggregate guards | `accepted` (aggregate NoOp) | Successful inactive read: idempotent success without submission. A missing/unavailable read model can still fail first with `downstream_failed`. |

The complete pre-read trace at the recorded gitlinks is:

- `references/Hexalith.Parties/src/Hexalith.Parties.Mcp/Tools/PartiesMcpTools.cs:406`
  calls `GetPartyAsync` before checking `IsActive` or submitting a Command.
- At pinned Parties `4937309`, `PartySdkQueryService.cs:341-343` returns
  `ActorNotFoundInfrastructure` when detail is absent. At the cited
  `1308ad000c79ebc394fc395588f9af91092e8c4c` checkout,
  `references/Hexalith.Parties/src/Hexalith.Parties/Queries/PartySdkQueryService.cs:324-326`
  returns `ReadModelUnavailable` for absent or erased detail. Both names carry
  the legacy wire sentinel `actor-not-found-infrastructure`.
- `references/Hexalith.EventStore/src/Hexalith.EventStore.Server/Queries/QueryRouter.cs:168-170`
  forwards a failed SDK result with `NotFound: false`.
  `references/Hexalith.EventStore/src/Hexalith.EventStore.Server/Pipeline/SubmitQueryHandler.cs:159-162`
  matches spaced not-found messages, so that hyphenated sentinel falls through
  to HTTP 500 at `:133-141`.
- `references/Hexalith.Parties/src/Hexalith.Parties.Client/HttpPartiesQueryClient.cs:157-159`
  throws on the failed pre-read; `PartiesMcpTools.cs:591-597` maps 5xx to
  `downstream_failed`, 404/410 to `not_found` and 422 to `validation_failed`.

The aggregate handler at `4937309:src/Hexalith.Parties/Domain/PartyAggregate.cs:851-874`
equals the current `PartyAggregate.cs:867-890`. `RejectIfErasureInProgress`
(`:1560`) checks `ErasurePending` through `Erased`; `RejectIfRestricted`
(`:1547`) runs before the inactive NoOp. These source oracles require the
selected deployed SDK/Gateway dispatch and pre-read state to be recorded in
execution evidence. No live comparison or upstream behavior change is claimed.

## C06 error privacy

Generic behavior, unchanged by this story:
`src/Hexalith.McpCli.Core/Execution/OperationError.cs:41-53` copies only
status, detail or title, reason, retryable, clientAction, retryAfter and a
canonical correlation ID, and `src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:35-42`
maps every other exception to a fixed `internal_error`.

Finding and fix: the inner-exception case failed at first. The default
`IHttpClientFactory` logger wrote the transport exception to stderr, including
downstream response text quoted by `HttpRequestException` (for example
`Received an invalid header line: '…'`). `src/Hexalith.McpCli/Hosting/HostFactory.cs:51-57`
now replaces the Gateway client loggers with `GatewayPipelineHttpLogger` and
`GatewayHandlerHttpLogger`. These keep the same four informational entries, with
the same categories, event IDs and messages, but log a failure without its
exception, and they log the request URL without its query. The change is
generic, so no module name appears in `src/`.

Guard tests:

- `tests/Hexalith.McpCli.Cli.Tests/PartiesMigrationCompatibilityTests.cs:56`: eight cases, covering Command and
  Query for Problem Details markers in `type`, `instance`, `tenantId`, `errors`,
  `extensions`, `rejectionType`, `category`, `correctiveAction`,
  `degradation` and `traceId`, a non-JSON body, an invalid-header transport
  failure whose marker is proven present in the client's exception chain, and a
  malformed 2xx body. Parties CLI, Parties MCP, Sample CLI and Sample MCP must
  each produce the same pinned complete document; no marker or personal value
  may appear on stdout, stderr, MCP text content or MCP structured content; and
  stderr must hold only the pinned Gateway entries (and MCP server entries for
  the MCP head).
- Removing the logger replacement fails both inner-transport cases, and only
  those; that mutation was run and reverted.

Reliance on upstream Query handling: detail (or title), reason, clientAction
and retryAfter are copied as the Gateway sends them, and for a non-JSON
response detail is the HTTP reason phrase. The Gateway sanitizes Command
rejections
(`references/Hexalith.EventStore/src/Hexalith.EventStore/ErrorHandling/DomainCommandRejectedExceptionHandler.cs:43-58`)
but passes a module's Query error message through as detail for every status
except the invalid-page 400 and 403
(`references/Hexalith.EventStore/src/Hexalith.EventStore/ErrorHandling/QueryExecutionFailedExceptionHandler.cs:88-94`),
including the 400 malformed-request response built from the module's
`sentinel: detail` message
(`references/Hexalith.EventStore/src/Hexalith.EventStore.Server/Pipeline/SubmitQueryHandler.cs:104-113`).
Parties returns only sentinel codes there
(`references/Hexalith.Parties/src/Hexalith.Parties/Queries/PartySdkQueryService.cs:242`,
`:248`). The upstream handoff is tracked in `deferred-work.md` under the Story
5.3 heading.

## C07 legacy Party IDs

- `PartiesMigrationCompatibilityTests.cs:124`: braced, parenthesized and
  X-format GUID root `PartyId` values fail with the same pinned
  `validation_failed` document at `/PartyId` through both heads, for
  `parties.deactivate-party` and `parties.get-party`, with zero Gateway
  requests and no HTTP diagnostics.
- `PartiesMigrationCompatibilityTests.cs:169`: `Legacy.party_01-A` as root,
  braced and parenthesized GUID `ContactChannelId` values and an X-format GUID
  `IdentifierId` reach the Gateway byte-for-byte through both heads.
- No validator changed and no ID is converted. The aggregate rule is
  `src/Hexalith.McpCli.Core/Catalog/RoutingResolver.cs:140-143`; EventStore
  enforces the same rule in
  `references/Hexalith.EventStore/src/Hexalith.EventStore.Contracts/Identity/AggregateIdentity.cs:11`
  and `:136`; `references/Hexalith.Parties/src/Hexalith.Parties.Contracts/ValueObjects/PartyIdentifier.cs:24-50`
  admits the legacy forms.
- `PartiesMigrationCompatibilityTests.cs:257` checks that the restored Parties
  Contracts package is exactly 1.5.1.

## G6 profiles and identity

Decision 1 (single source):
`src/Hexalith.McpCli.Core/Settings/SettingsResolver.cs:86` fails a resolved
URL and token whose source classes differ (an `EVENTSTORE_*` label is the
environment; `flag` and `profile` stay themselves), before any host or Gateway
exists. The message names both sources and never the token. A blank token is
validated first, so it still reports the blank-token error.
A URL without a token resolves. A token without any URL also resolves, because
no Gateway can be called; `ResolvesAGatewayUrlOrTokenAlone` pins this.

- `tests/Hexalith.McpCli.Core.Tests/SettingsAndRegistrationTests.cs:21`
  (`ResolvesPrecedenceAndRecordsSources`, updated to the rule), `:76`, `:128`
  and `:172` (the complete blank-token document before the source comparison).
- `tests/Hexalith.McpCli.Cli.Tests/ConfigCommandTests.cs:2163`: sixteen
  mixed cases on `send`, `query`, `mcp`, `modules` and `config current`, with
  the complete document on stdout (CLI) or stderr (MCP), exit 2, no host start,
  zero requests to either Gateway and no token or masked token on any channel.
- `ConfigCommandTests.cs:2263`: twelve one-source cases send exactly the
  source's bearer credential, or none, to exactly that Gateway; a lower-precedence
  profile's URL and token are never used.
- The existing `ConfigCommandTests.AddIgnoresEnvironmentOperatorSettingsAsync`
  now expects `config profile add --url` beside an inherited `EVENTSTORE_TOKEN`
  to fail with the same message and write nothing. With `--url` and `--token`
  it still stores only flag values.
- `tools/live-topology/run_live.py` passes the private Gateway URL through
  `EVENTSTORE_URL` with `EVENTSTORE_TOKEN`, instead of as `--url`.
  `tools/live-topology/test_live_runner.py` asserts that neither value appears
  in the CLI arguments.

Admin isolation and the environment allowlist:

- `ConfigCommandTests.cs:2363`: `modules`, `operations`, `describe`, `send`,
  `query` and `mcp` give identical channels with and without a hostile admin
  `profiles.json` beside `mcpcli.json` and hostile `EVENTSTORE_ADMIN_*` values.
  They never contact the admin URL and ask the environment only for the nine
  supported names.
- `ConfigCommandTests.cs:2457` repeats this through the built executable's
  real process environment for `modules`, `describe`, `send` and `query`.
- `tests/Hexalith.McpCli.Cli.Tests/McpStdioProcessTests.cs:416` repeats it
  over stdio through the `tests/fixtures/StdioHost` child process, which runs
  the real `CliRunner` `mcp` verb with the Sample manifest and an injected
  profile path; it is a test fixture process, not the shipped executable. The
  hostile environment sets `EVENTSTORE_ADMIN_URL`, `_TOKEN`, `_PROFILE` and
  `_FORMAT`.

Identity mismatch (existing checks at
`src/Hexalith.McpCli.Core/Execution/OperationExecutor.cs:137-153`, unchanged):
`tests/Hexalith.McpCli.Cli.Tests/CliMcpCommandParityTests.cs:186` and
`tests/Hexalith.McpCli.Cli.Tests/CliMcpQueryParityTests.cs:37` pin equal complete
`validation_failed` documents from both heads with zero Gateway requests. They
cover a disagreeing payload tenant or actor, and undeclared `TenantId`,
`Tenant` or `ActorId` members on Parties payloads.

Profile names (`epic-2-retro-item-2-anchor-profile-names`, closed):
`src/Hexalith.McpCli.Core/Settings/ProfileStore.cs:397` now ends in `\z`.
`tests/Hexalith.McpCli.Core.Tests/ProfileStoreTests.cs:529` and `:566` and
`ConfigCommandTests.cs:2530` reject `dev\n` through the Core store and the CLI
documents, with unchanged profile bytes. Restoring `$`, or removing the
single-source rule, fails every corresponding case; both mutations were run and
reverted.

Decision 2 (output files): `epic-2-retro-item-1-protect-profile-output` stays
open (`_bmad-output/implementation-artifacts/sprint-status.yaml:180`,
`_bmad-output/implementation-artifacts/deferred-work.md:400`, formerly `:398`).
For G6's output-file treatment, no admin `--output` semantics migrate, and
McpCli's own output contract stands. The README migration table records this.

## Implementation gates run for 1.1.0 (2026-11-09)

The original implementation parent reran the full verification after review
pass 1, from one fresh restore and one Release build. These are historical
1.1.0 results; review pass 2 documentation validation is recorded below:

| Command | Result |
| --- | --- |
| `dotnet restore Hexalith.McpCli.slnx` | exit 0 |
| `dotnet build Hexalith.McpCli.slnx --no-restore --configuration Release -warnaserror` | 0 warnings, 0 errors |
| `dotnet test tests/Hexalith.McpCli.Abstractions.Tests --no-build --configuration Release` | 20 passed |
| `dotnet test tests/Hexalith.McpCli.Analyzers.Tests --no-build --configuration Release` | 19 passed |
| `dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release` | 881 total, 877 passed, 4 skipped (Windows-only) |
| `dotnet test tests/Hexalith.McpCli.Cli.Tests --no-build --configuration Release` | 558 total, 556 passed, 2 skipped |
| `dotnet test tests/Hexalith.McpCli.Mcp.Tests --no-build --configuration Release` | 94 passed |
| `dotnet test tests/Hexalith.McpCli.Manifest.Tests --no-build --configuration Release` | 362 passed, including `DependencyPolicyTests` |
| `dotnet tests/Hexalith.McpCli.Core.Tests/bin/Release/net10.0/Hexalith.McpCli.Core.Tests.dll -class Hexalith.McpCli.Core.Tests.EnrolledModuleCoverageTests` | 5 passed |
| `python3 tools/conformance-vectors/v1/check_enrolled.py --output <task-owned directory>` | exit 0: Parties 1.5.1 (7 operations) and Tenants 7.0.5 (14 operations) complete vector replay passed; full-v1 acceptance true |
| `python3 -m unittest discover -s tools/live-topology -p 'test_*.py'` | 198 tests, OK |
| `python3 tools/live-topology/run-vectors.py --output <task-owned directory> --preflight-only` | exit 0, `PREFLIGHT-ONLY: full live acceptance=False` (expected; no live lane was run) |
| Story 5.3 static check above | exit 0: 24 rows, changed C05, C06, C07; receipt decision pending, then approved after the owner's approval |
| `git diff --check 4bc4be5deca889d1594b0d367e313592c9421fe8` | clean |

`GatewayHttpLogTextTests` (`tests/Hexalith.McpCli.Cli.Tests/GatewayHttpLogTextTests.cs`)
pins that the logged request text drops user information, query and fragment.
No live topology, Aspire lane or Windows suite was run; live acceptance,
authorization and domain effects remain Story 5.4 and later gates.


## Review pass 2 patch validation (2026-11-09)

The [validation receipt](review-pass-2-validation.json) records these checks:

- Both amendments pass the extracted static check in their actual states:
  historical 1.1.0 approved, and 1.2.0 first pending then approved after the
  owner response. All 24 row identities remain;
  only C05's acceptance cell changes in 1.2.0.
- Seven contradictory-label probes are rejected, including inconsistent
  instruction/decision fields and matching but negative labels. A synthetic
  approved 1.2.0 receipt passed in memory during pre-approval validation;
  the actual approved receipt passes after the owner response, and two further
  negative probes reject altered instruction/decision labels on that receipt.
  Removing the exact-label check admits the bad receipt, proving the negative
  probe protects this correction.
- Built Release CLI probes confirm the README recovery for both an active
  invalid profile rename and removal. Each starts with the complete expected
  `configuration_invalid` document and exit 2, then `config profile list`
  succeeds with exit 0 and empty stderr. The private file stays 0600 and the
  read leaves its corrected bytes unchanged.
- The 1.1.0 inventory and receipt are preserved byte-for-byte from `1ff2052`.
  Their hashes are bound by `approval/amendment-1.2.0.json`. The original
  `approval/approval.json` and the 1.0.0 archive remain unchanged.
- `git diff --check` passes. No production source or dependency changed, so
  the review's passing Release build and focused tests were not repeated.

[Exact approved 1.1.0 to 1.2.0 diff](approval/amendment-1.2.0.diff). The owner
approved the unchanged inventory hash in the amendment table above. C05 and
Story 5.3 are complete; live parity and retirement gates remain separate.

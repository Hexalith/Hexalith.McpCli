# Census amendment 1.0.3 — owner draft (not approved)

This folder is a **draft**. It grants no allowance, exclusion or authority. The
active policy (`baseline.json` plus amendments 1.0.1 and 1.0.2) is unchanged,
and no approval receipt exists in the repository.

## What is approved, and how it is applied

The owner approves the exact operation lists in
[authorization.draft.json](authorization.draft.json). The binding is its
canonical JSON (sorted keys, no whitespace).

- File SHA-256: `bd087b3942724ec4832c311f17eee065cfc73b68d4aa867a5591eb5e53305632`
- Canonical SHA-256: `df0eda1a9c9d6289c3c02f51c5b5345ea8eb32669eea9f80af70c17ff1382474`

After approval, [assemble-amendment.py](assemble-amendment.py) `--write "<label>"`
writes these files from those lists unchanged:

- `tools/proprietary-surfaces/v1/amendments/1.0.3.json`: the five lists plus the
  header `fromVersion` 1.0.2, `toVersion` 1.0.3, `previousSha256` of
  `amendments/1.0.2.json`, and an `approval` block. That block binds the
  receipt's path and SHA-256.
- `amendments/1.0.3-approval.json`: a v2 receipt. Its `authorization` equals the
  lists exactly. Its `authority` binds only the existing lineage: the Story 5.1
  inventory `approval.json` and the 1.0.1 and 1.0.2 receipts. It records the
  selected label verbatim (`approvalLabel`), the source report and the root pins.
- `amendments.json`: the 1.0.3 entry is appended, and prior entries keep their bytes.

## Owner decisions (2026-11-12, quoted)

- "Review first, then approve": three independent review layers ran on this draft
  and the checker change. Their findings and verdicts are in the story spec's
  Review Triage Log, and the fixes are applied here.
- "Add as PE03 tooling": `Hexalith.Platform.Composition`. Platform `3ad2f29a` made
  it a non-packable `PlatformSourceStateWorker` executable that reads a JSON path
  list on stdin and prints a source-state hash. It has no `System.CommandLine`, no
  MCP package and no tool packing.
- "Checker fix + new version": `check.py` accepts a file when any exact-file
  exclusion for that path lists its hash, and a file-bound path never falls back
  to a directory-scope exclusion. `test_later_exact_file_exclusion_approves_another_byte_version`
  covers it; four executed guard-removal controls each fail it. The draft adds
  the refreshed Builds `Tools/package-version-audit.json` bytes (`173efbb30709e624ee0ec041ea5c0a62188499b5b5b1cf1a4d516dd045af71e2`).

## What the draft covers (all 30 rejected identities and the audit drift)

| Class | Entries | Why |
|---|---:|---|
| G4 `compatibility-publication-or-route` | 5 | Package identities of the approved PS01 `Hexalith.EventStore.Admin.Cli` and PS10 `Hexalith.Folders.Cli` projects, on files that already have approved PS and G4 allowances. Also three Memories identities (`registry.hexalith.com/memories-mcp`, `mcp`, and the CLI pack-verification project reference) on files whose approved G4 allowances route the Memories PS surfaces. |
| PE01 `exempt-build-publication` | 4 | The Builds `publish-container-to-registry` action, which publishes a consumer's HexalithApp API/Web server containers, and package identities of the two `hexalith-module` pack templates that row PE01 names. |
| PE03 `platform-qualification-tooling` | 1 | `Hexalith.Platform.Composition`, by owner decision. |
| PE05 test and performance fixtures | 4 | The disposable Builds release-create fixture (project and container): its hosted test runs build draft releases that are then deleted. Also the full-path Tenants performance seed driver. The approved ChatBot `Mcp.Tests` allowance is replaced, because `ChatBotMcpServiceTests.cs` adds `mcp-registration` (1 removal + 1 addition). |
| PE06 `external-developer-configuration` | 4 | `servers`-section stdio entries in ChatBot, Folders, Projects and Timesheets `.mcp.json` that launch the local `fluentui-mcp` command: Microsoft's Fluent UI Blazor MCP server, the .NET tool `microsoft.fluentui.aspnetcore.mcpserver`. The builder recomputes each identity hash from that exact entry. The HTTP `mcpServers` entry was already approved. |
| PE09 `qualification-evidence-tooling` | 1 | Package identity of the approved Memories `GenerateBenchmarkVectors` tool. |
| PN09 `domain-service-publication` | 7 | The EventStore image pinned by digest in seven retained 2026-10-31 Platform operator-setup packets; same class as the approved Platform Timesheets image. |
| PE07 exclusions `captured-evidence` | 2 files | Conversations' preparation-only story 9.2 repair proposal JSON. It is excluded by exact blob hash because its package list names `Hexalith.EventStore.Client`, `.Contracts`, `.DomainService` and `.ServiceDefaults` as evidence, not as a Conversations publication. Also the refreshed Builds package-audit snapshot. |

[build-draft.py](build-draft.py) refuses to build unless:
- the report's parent is `HEAD`, and no root gitlink has moved;
- every pick matches its expected identity, kind and signal set;
- every "already approved" claim is an active allowance;
- every exclusion hash is read from the committed blob.

[not-included.json](not-included.json) is `[]`.

## Verification

Source report: `guard-excuse-review-20261111/runs/final-2/census.json`, SHA-256
`6385946560009db6f4fbbf70157e2ab1ff49e8d8de57f647caf504a271899548`, at parent `f223aaa5acd70c04a413f3251f83d96472a6b0d9`.

- **Chain rehearsal** ([rehearsal-load.json](rehearsal-load.json)):
  `assemble-amendment.py --rehearse <empty dir outside the repository>` builds
  1.0.3 and a rehearsal receipt there. `check.py`'s own `load_policy` then loads
  the chain at version 1.0.3, with 522 allowances and 64 exclusions. Nothing is
  written inside the repository.
- **Coverage dry run:** `dry-run-gate.py <empty dir>` applies the indexed
  amendments as `load_policy` does: index hashes are checked, and each removal
  must match exactly one entry. The merged scratch baseline has SHA-256 `d77e37d23ee55d308f9d3982e56a9d2b38557cf30be5e189504a4c1969f3da3b`
  ([dry-run-merge.json](dry-run-merge.json)). The scan command was
  `check.py --baseline <dir>/baseline.json --amendments <dir>/amendments.json --output <dir>/census.json`
  (`check.py` SHA-256 `88516f2c23799dbe3ae19284d0a6324804227e23df65a5828203c6d06a711385`); it exits 1
  ([dry-run-census.json](dry-run-census.json), SHA-256 `a24d90241cc36bab327f82f7755e9ed69088b43db2c3b5ee9e3c2bd740edf37d`).
  - Rejected observations: 30 → **0**.
  - Coverage errors: 47 → **46**; only the Builds audit drift resolves.
  - Passing roots: 3 → **6** of 17. Fully inspected roots: 6 → 6.
- **Evidence:** [secret-scan.json](secret-scan.json) covers this folder.

## What this draft does not do

- **CI stays red:** an allowance cannot settle a file the census could not
  inspect. The 46 coverage errors, including the Tenants AppHost Compile
  fallback, are grouped in the
  [decision packet](../guard-excuse-review-20261111/decision-packet.md).
- **Ten stale allowances remain:** seven `node:` GitLab-template entries in
  agent-skill copies (ChatBot 3, Platform 2, Timesheets 2), the ChatBot
  StoryEvidenceGate release-workflow entry, the Platform test-extension
  qualification workflow, and the `repository:` entry in Platform's Timesheets
  chart. Staleness is reported and never fails; removing them is a separate
  exact-removal decision.
- **Approvals accumulate:** exclusion entries have no removal operation, so
  earlier approved byte versions of a file stay approved.
- **Inventory not updated:** `Hexalith.Platform.Composition` under PE03 and the
  Builds release fixture under PE05 go beyond the rows' enumerated lists in
  technical inventory 1.0.2. This census amendment is the binding census record;
  reconciling the inventory is tracked in `deferred-work.md`.

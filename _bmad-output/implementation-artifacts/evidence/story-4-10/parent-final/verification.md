# Independent final verification — Story 4.10

The final local candidate is reviewed and verified to the limits below. Story
4.10 remains in progress: the exact candidate needs fresh owner approval, three
existing upstream fitness failures block complete Parties CI, and publication,
published-byte verification, the central pin and production enrollment are open.

[Exact commands, working directories, exit codes and logs](checks.json) were
recorded by the parent independently after all review patches. Projects ran
sequentially. Both complete Release builds used `--no-restore --configuration
Release -warnaserror -m:1` and passed with zero warnings/errors.

| Final test project | Passed | Failed | Skipped | Exit |
| --- | ---: | ---: | ---: | ---: |
| McpCli.Abstractions.Tests | 20 | 0 | 0 | 0 |
| McpCli.Analyzers.Tests | 19 | 0 | 0 | 0 |
| McpCli.Core.Tests | 659 | 0 | 2 | 0 |
| McpCli.Cli.Tests | 479 | 0 | 2 | 0 |
| McpCli.Mcp.Tests | 58 | 0 | 0 | 0 |
| McpCli.Manifest.Tests | 103 | 0 | 0 | 0 |
| Parties.Contracts.Tests | 201 | 0 | 0 | 0 |
| Parties.Server.Tests | 315 | 0 | 0 | 0 |
| Parties.Client.Tests | 330 | 0 | 0 | 0 |
| Parties.Tests | 2,064 | 3 | 0 | 2 |

All test commands were `dotnet test tests/<project> --no-build --configuration
Release`. The four skips are existing Core/CLI skips. Manifest.Tests ran after
a fresh solution restore following loopback, as required by repository guidance.

`bash tools/conformance-vectors/v1/run-sample-validation.sh Release` and
`bash tools/conformance-vectors/v1/run-sample-loopback.sh` both returned 0, with
all 87 Python regressions passing in each invocation. The process fixture proved
nonempty enrollment through the actual checker/verifier and complete CLI/MCP
replay, retained 53 resolved package identities/hashes and approval input hashes,
then rejected a structurally valid false semantic assertion at replay with useful
diagnostics and no stale success receipt. The final production enrollment command
returned 0 with **zero enrolled packages**; this does not prove Parties enrollment.

The [final exact-artifact receipt](../verification.json) separately records seven
strict Catalog operations, seven clean descriptions and complete seven-vector
CLI/MCP replay. The [final description reviewer](../description-review-final.json)
read only those seven built documents and found no remaining wording gaps.
Three independent code review lenses completed, with all patch routes resolved
and the two low schema findings explicitly retained in the source spec's triage.

## Upstream blocker

From `/home/administrator/projects/hexalith/parties`,
`dotnet test tests/Hexalith.Parties.Tests --no-build --configuration Release`
returned **2**, with **2,064 passed, three failed, zero skipped**. The failures in
[the final log](parties-tests.txt) are:

- `PlatformApiPrerequisitesTests.FinalDependencyReceiptsMatchTheSelectedPackageAndSourceGraph`.
- `PlatformApiPrerequisitesTests.McpCliSiblingLayoutsSelectAbstractionsProjectWithoutNestedCheckout("Hexalith.McpCli")`.
- `PlatformApiPrerequisitesTests.McpCliSiblingLayoutsSelectAbstractionsProjectWithoutNestedCheckout("references/Hexalith.McpCli")`.

These match the failures recorded before review. The final proof command
`git diff --exit-code HEAD -- Directory.Build.props src/Hexalith.Parties.Contracts/Hexalith.Parties.Contracts.csproj tests/Hexalith.Parties.Tests/FitnessTests/PlatformApiPrerequisitesTests.cs`
returned **0**. The relevant source-selection/configuration expectations remain
unchanged. No tests or release gates were weakened. The final verification
[summary](summary.json) deliberately reports `blocked` rather than a clean pass.

## Integrity and release boundary

[Integrity checks](integrity.json) matched all 196 Parties source, seven vector
and 30 McpCli verifier input hashes to the final pending receipt. Exact artifact
bytes and vector hashes match the passing artifact receipt. Seven current
description hashes bind the independent review. The original candidate,
manifests and first-review document hashes still match the archived receipts;
all 68 archived files remain retained. [Final log hashes](log-files.sha256.json)
identify the parent verification logs.

The [pending receipt](../pending-approval.json) identifies version
`0.0.0-story410`, the raw archive SHA512, all seven vector SHA256 values,
the authoritative A1 migration inventory (including N01–N04 exclusions), the
pending release inventory candidate and the final description review.
It grants no release approval. Historical Story 4.9 approvals remain unchanged.

The approved spec requires: “Obtain fresh maintainer approval for the complete
artifact/vectors and release inventory.” Publication must use the protected
owning workflow after that approval and green owning CI. Published bytes and
rebound vectors must pass verification again before a Builds pin and enrollment.
The workflow's completion/commit step is not applied while these acceptance
criteria remain unmet. This work did not stage, commit, push or move gitlinks.

Scripted replay proves transport routing and public result/error parity. It does
not prove live authorization, cross-tenant denial or persisted command effects;
C06–C08 and Stories 4.11/4.13 retain their assigned proof requirements.

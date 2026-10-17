# Inventory coverage v1

This test-only format checks declared migration scope against the built Catalog.
The artifact and checker stay outside production source and configuration. They
are never read at runtime and do not enroll modules. The existing Core.Tests CI
lane executes the sample gate without a Parties package or Gateway.

Run from the repository root after the normal solution restore and Release build:

```sh
dotnet test tests/Hexalith.McpCli.Core.Tests --no-build --configuration Release
```

The project copies `sample-approved.json` to the test output. The test resolves it
from `AppContext.BaseDirectory`, so discovery does not depend on the process CWD.

## JSON v1 fields

Files use strict UTF-8, with an optional UTF-8 byte order mark. Invalid byte
sequences fail before JSON validation. Every field below is required. Objects
reject unknown fields and duplicate JSON keys at every depth. Strings must be
nonempty without surrounding whitespace; arrays must be nonempty. JSON comments and trailing commas are not accepted.

| Location | Fields and meaning |
| --- | --- |
| Root | `formatVersion`: integer `1`; `module`: canonical lowercase kebab-case module; `purpose`: `fixture` or `release`; `targets`: normalized target array; `legacyRows`: source decision array. |
| Target | `id`: stable unique target ID; `name`: unique canonical `module.operation` name; `contractType`: unique exact CLR `Type.FullName`. Names and CLR identities are compared ordinally, with no casing or whitespace normalization. |
| Legacy row | `id`: stable unique row ID; `legacyOperation`: source tool, resource, CLI operation or inventoried variant; `targetIds`: references to normalized targets; `disposition`: `replace`, `withdraw`, or `defer`; `coverage`: `include` or `exclude`; `rationale`: explicit decision reason; `approval`: decision evidence. |
| Approval | `status`: must be `approved`; `authority`: `owning-maintainer` or `synthetic-fixture`; `reference`: an evidence reference, independently verified by the owner/reviewer. |

`include` requires approved `replace`. `exclude` requires approved `withdraw` or
`defer`. An excluded target records the exact intended name and CLR identity that
must remain absent, even if that contract has never been implemented. Every
target needs at least one row reference. Multiple legacy rows may share a target;
a row cannot repeat a reference and shared rows cannot disagree about coverage.
A legacy workflow can reference multiple targets without duplicating target rows.
An exclusion does not confer permission to delete a legacy surface.

`scope-only` authority is rejected: a requesting user's scope decision cannot
establish owning-maintainer release readiness. `synthetic-fixture` authority is
accepted only for `purpose: "fixture"`; it cannot certify a release inventory.
`owning-maintainer` records the claimed owner decision, not proof of authenticity.
A passing gate proves names/types and explicit recorded decisions only. It cannot
prove source-surface completeness, approval authenticity, behavior parity,
authorization, publication readiness or retirement permission. Independent owner
evidence must establish completeness and authentic approvals; conformance vectors
cannot substitute for this coverage gate.

## Synthetic fixture certification

The approvals in `sample-approved.json` are deliberately synthetic test fixture
certifications, recorded here for this fixture alone. They certify the expected
three sample declarations, a shared read reference, and two absent synthetic
exclusions. They do not represent approvals by any domain maintainer. The two
excluded CLR names are synthetic absent types. No Parties intent, source, package,
approval or release claim is delivered or altered by this fixture.

## Comparison and diagnostics

`InventoryCoverageGate.CheckFile(path, catalog, provider)` loads strict JSON,
validates scope, calls unfiltered public `ICatalog.ListOperations(module)`, and
independently reads `provider.Get(false)` for internal descriptors. Every included
name must appear once publicly and once internally with exactly the recorded
`OperationDescriptor.ContractType.FullName`. Excluded names/types must be absent;
extra public or internal operations fail. Any Catalog declaration error fails,
even if the surviving operations match. Catalog warnings alone are not errors.
The test also checks that public module, list and describe JSON expose neither
contract-type fields nor mapped full CLR names.

Findings are ordinally sorted strings, prefixed by the supplied file path/label
and a JSON path, stable `row ID`, `target ID`, Catalog diagnostic type, or unexpected
operation name. Messages identify the field, conflicting identity, or expected and
actual value. Invalid documents fail before comparison; malformed JSON reports
zero-based line and byte positions. Empty findings mean the recorded scope matches.
For example:

```text
inventory.json:target T01: public name expected 'sample.create-item' once; actual missing.
inventory.json:row L01: dangling target reference 'T99'.
```

## Future owner handoff

Keep existing Markdown inventories and session decisions as their authoritative
human evidence. Independently enumerate every source surface and variant, obtain
owning-maintainer decisions, and transcribe them into a new versioned JSON artifact
outside `src/` without inventing approvals. Pending intended Parties targets are
still undelivered; do not turn their names into a coverage or release claim.

For a later owner-approved module, supply its decorated Contracts assembly to the
existing `CatalogProvider`/`CatalogService`, copy the new inventory into test output,
and call the same checker with that module's artifact. No module-specific checker
branch is needed. Use `purpose: "release"` and genuine `owning-maintainer` evidence
for release coverage; synthetic fixture authority is rejected there. Verify
approval references and source completeness separately. Enrollment, published
Contracts pins, Gateway behavior and retirement gates remain separate work.

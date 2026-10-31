---
title: Align the existing dependency closure with its shared catalog
status: done
created: 2026-10-31
baseline_commit: e8914c09f154d7b2d039f31f0620b0f103f838fa
---

## Intent

The operator requests synchronized repositories and current dependencies without bypassing automated checks. Concurrent e8914c0 advanced the shared catalog while preserving the old exact baseline map. CI41193401022 rejects the actual restored closure before live vectors: Commons.UniqueIds2.30.7, JsonPointer.Net7.0.4 and JsonSchema.Net9.6.0 differ from2.30.3/7.0.3/9.5.0. The retained live-preflight artifact13039578255 is `/tmp/mcp-e891-live-preflight.zip`.

Update only those three exact existing package versions after checking the real restored production graph. Preserve direct package roots, approved module artifacts/versions, decoration package, vectors, approvals, dependency count, package allow-list and all actual endpoint/auth/persistence checks. There is no added production root or wider module import. Preserve all concurrent operational evidence and root-declared pointer updates; do not initialize nested submodules.

## File Scope

- `tools/dependency-policy.json` - exact existing closure versions
- `tests/Hexalith.McpCli.Manifest.Tests/DependencyPolicyTests.cs` - retain exact integration fixture closure with the same updated Commons version
- `_bmad-output/implementation-artifacts/spec-sync-qualified-dependency-closure.md` - actual diagnosis and verification

## Verification

Build/run the existing Manifest dependency-policy tests with the current top-level shared catalog, and check the actual NuGet production closure through the unchanged live preflight checker. Pinned commitlint must validate the exact full candidate before owning commit/push. Require the new exact-main hosted CI and all21 unskipped live vectors; this metadata fix does not itself claim their completion.

Initial targeted run107casesfoundoneexpectedfixturemismatch: itsseparateexactHexalithintegrationclosurestilllistedCommons2.30.3. Updateonlythatexistingentrytoactual2.30.7; allpackageIDs/otherexpectedversionsstayfixed. Productiongraphand106otherpolicycasesalready pass.

Finalfocusedproof: Manifest.Tests Releasebuild0warnings/errors; directDependencyPolicyTests107/107passed,zerofailed/skipped16.122s. Unchangedlive_plans.check_dependenciesacceptstheactualrestoredproductionassetswithupdatedfinitebaseline. Logs `/tmp/mcp-e891-closure-{build,tests}.log`. Allapprovedmoduleversions/archives/vectorbytesanddirectpackageIDsareunchanged. Parentstillrequiresexact-mainfullCI/all21livevectors.

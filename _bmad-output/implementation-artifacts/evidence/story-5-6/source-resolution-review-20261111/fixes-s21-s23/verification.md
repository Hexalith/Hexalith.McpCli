# Review fixes S21–S23

Unsupported printf variable writes invalidate their destination, including
attached `-vname` forms. An unknown destination invalidates potentially affected
state. Multiple assignments invalidate every identified destination, preventing
reuse of a prior approved target.

ContainerRegistry is retained as classification metadata. Image association
uses the complete declared registry, namespace and repository, removing only
tag/digest suffixes for comparison. Registry ports remain part of the name.
Other registries/namespaces and projects with any MCP/CLI signal remain visible.
No allowance data or module-specific branch changed.

Three new regression methods and the directly affected S06 regression pass,
including full CLI streams, exact identities, tagged/digested images, registry
ports and proprietary registration signals. Ten targeted mutation controls pass;
`git diff --check` passes. The combined [runner](../mutation-guards.py) retains
101 controls, adapts the S06 container anchor, and adds nine controls (110 total).
`--round-three-only` selects the ten targeted controls. Full verification remains
with the parent workflow.

The [receipt](verification.json) binds current sources and the exact
[previous runner bytes](mutation-guards-prior.py). The [prior-evidence manifest](prior-review-evidence.json)
was checked after implementation: attempts/parent-final-1/ and all earlier review
evidence are unchanged, apart from the explicitly versioned active runner.
Every original source-resolution packet file remains byte-identical. The initial
printf test capture is retained; its accidental statement-counter shadowing was
corrected before the final passing capture.

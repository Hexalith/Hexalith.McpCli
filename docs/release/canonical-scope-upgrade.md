# Canonical scope upgrade (2.0.0)

The public CLI now normalizes valid tenant identifiers to lowercase and reserves `system` from variable tenant input. Operations that run in a platform namespace declare their `platform:<scope>` value in Contracts metadata. Discovery reports `platformScope` for those operations and omits the per-call tenant argument.

`Hexalith.McpCli.Abstractions` 2.0.0 was published as a bootstrap package for the coordinated dependency upgrade. The `Hexalith.McpCli` tool was not published at 2.0.0. The paired release must use a later shared version selected by semantic-release and publish both package IDs at that version; do not reuse the occupied Abstractions 2.0.0 identity. Review callers that supplied `system` or a tenant for an operation with a declared platform scope. Published legacy modules with an explicit fixed `system` tenant remain readable during the coordinated package transition.

The paired release verifies exact-source CI, immutable staged package bytes, cross-platform smoke, and public NuGet publication. A user-authorized automated acceptance records its bypass of manual client sessions without claiming those sessions occurred.

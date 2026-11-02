# Canonical scope upgrade (2.0.0)

The public CLI now normalizes valid tenant identifiers to lowercase and reserves `system` from variable tenant input. Operations that run in a platform namespace declare their `platform:<scope>` value in Contracts metadata. Discovery reports `platformScope` for those operations and omits the per-call tenant argument.

Update `Hexalith.McpCli` and `Hexalith.McpCli.Abstractions` together to 2.0.0. Review callers that supplied `system` or a tenant for an operation with a declared platform scope. Published legacy modules with an explicit fixed `system` tenant remain readable during the coordinated package transition.

The paired release verifies exact-source CI, immutable staged package bytes, cross-platform smoke, and public NuGet publication. A user-authorized automated acceptance records its bypass of manual client sessions without claiming those sessions occurred.

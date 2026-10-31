# Live operator environment — 2026-10-31

The approved environment is **ready for human checks**. Story 4.17 remains in progress. All owner phases passed, including real DNS/backup/metadata, administrator/writer bootstrap, Gateway /ready, all four Pods Ready, persisted tenant/member, and a read-only non-administrator query from the exact staged 1.2.0 CLI. This does not establish an actual MCP client session or independent timing. No Party command has been submitted by the owner.

- Gateway: `http://127.0.0.1:18170`; the verified owned forward is running in WSL Ubuntu-26.04 and stops no later than token expiry.
- Namespace and selected tenant: `mcpcli-417-20261031-155f9b6d`.
- Operator actor/subject: `mcpcli-417-operator-20261031-155f9b6d`; persisted `TenantContributor`, `global_admin=false`.
- Operator token expires **2026-10-31 09:54:53 UTC / 10:54:53 Europe/Paris**. Its value is only in the protected profile; never paste it into chat, client JSON or evidence.
- Private `MCPCLI_HOME`: `/tmp/mcpcli-417-v1-private-20261031-attempt8/operator-home`; profile name `operator`.
- Exact accepted 1.2.0 executable: `/tmp/mcpcli-417-offline-20261030/private/tools/hexalith`.
- Accepted local package directory for a new installation: `/tmp/mcpcli-416-hosted-svjuv79c/attempt4/paired-preparation/packages`. Verify README package/receipt hashes before installation.

For ordinary sessions, merge the appropriate protected fragment into the client's configuration, preserving other servers. These files contain paths only, no credential values. They have not been registered automatically:

- Linux/WSL-native client: `/tmp/mcpcli-417-v1-private-20261031-attempt8/mcp-linux.json` (`mcpServers`).
- Native Windows Claude Desktop or Copilot Global launching WSL: `/tmp/mcpcli-417-v1-private-20261031-attempt8/mcp-windows-wsl.json` (`mcpServers`); it explicitly selects Ubuntu-26.04, user administrator and the installed .NET root.
- Native Windows VS Code Local harness: `/tmp/mcpcli-417-v1-private-20261031-attempt8/mcp-vscode-local-windows-wsl.json` (`servers`).

Remove inherited `EVENTSTORE_*` settings, then follow the [README client/task procedure](../../../../../README.md#operator-setup-with-the-staged-120-tool) and the observer's [acceptance checklist](../../../../../docs/release/operator-setup-checklist.md). Confirm one server exposes all five generic tools and both modules. Read this tenant through fixed system routing, send one fresh synthetic Party using the README payload, then query its persisted details. Use new Party/contact/identifier IDs for each client/attempt and preserve uncertain outcomes without repeating a Command.

**Independent timing:** use a first-time operator before practising the setup, or a separate first-time person. Supply endpoint, tenant, actor, token and expiry privately as prerequisites. That operator uses only the README, a fresh installation and fresh MCPCLI_HOME, creates the profile/registration after the timer starts, and stops timing on the first successful MCP send_command. Do not reuse the prepared profile, installation or these fragments to claim a full timed setup. Retain every assistance/failure/overrun; target 900 seconds. The timed client can also supply a named-client session if its full initialization/discovery/persisted-result evidence is retained.

Record the three actual client sessions and timer using the checklist. The namespace stays available for these checks; cleanup is still required afterward. The approved packet review expires 2026-11-01 07:37:50 UTC. Retire through its UID-bound cleanup before that deadline; do not reuse an expired review. [Live readiness evidence](metadata-execution-20261031/live-readiness.json) retains exact ownership and completed phases, and [approval](metadata-execution-20261031/approval.json) binds the packet hash. The three earlier failed environments are removed; their journals/backups/activation evidence remain retained.

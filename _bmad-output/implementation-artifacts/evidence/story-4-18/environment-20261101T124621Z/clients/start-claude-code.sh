#!/usr/bin/env bash
set -euo pipefail
cd /tmp/mcpcli-4-18-41307182275/client-workspace
for eventstore_name in ${!EVENTSTORE_@}; do unset "$eventstore_name"; done
exec /home/administrator/.local/bin/claude --mcp-config /home/administrator/projects/hexalith/mcpcli/_bmad-output/implementation-artifacts/evidence/story-4-18/environment-20261101T124621Z/clients/mcp-linux.json --strict-mcp-config --session-id 7ceb60f0-3ebf-490b-ba96-7ccb271ff745 --debug-file /tmp/mcpcli-4-18-41307182275/environment-private-20261101T124621Z/clients/claude-code-debug.log 'Read /home/administrator/projects/hexalith/mcpcli/_bmad-output/implementation-artifacts/evidence/story-4-18/environment-20261101T124621Z/clients/claude-code-task.md fully and perform this approved actual-client acceptance task using the hexalith MCP tools.'

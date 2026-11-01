# Fresh Claude Desktop acceptance task — Story 4.18, attempt 1

Use the actual hexalith MCP server in this Claude Desktop session. Read this file fully, then perform the calls below through its MCP tools. This is an operator-assisted actual-client acceptance session; synthetic results, CLI/HTTP substitutes or narrative claims are insufficient.

The operator approves exactly one synthetic Party creation with ID `party-418-desktop-20261101-1`, in selected tenant `mcpcli-417-20261101-00c6a713`, through the accepted staged tool 1.2.0 from source `17eb4fbbc151ca4b99dfa452e9f65655db2b402f`, staging run 41307182275. The environment owner approved packet `f2e88eb4dc9536709a0b1daf9193423cbb9011ddf5a8b59c7775fce1a97d598e` and its real readiness/persisted membership passed. Profile operator has the private credentials already; never read, print or copy its token. Ordinary client tool-approval prompts still apply. Token expiry is **2026-11-01T16:07:34+00:00**. Use the server's configured session tenant and actor; do not supply per-call tenant, actor, correlation or idempotency overrides.

Confirm the actual MCP connection/initialization identifies server hexalith version 1.2.0. Require exactly these five generic tools: list_modules, list_operations, describe_operation, run_query, send_command. Use only this server for all calls. First perform the six discovery/description calls, then read the tenant. Its result must use tenant system and document.tenantId `mcpcli-417-20261101-00c6a713`, status Active and membership for `mcpcli-417-operator-20261101-00c6a713` with role TenantContributor. Require the selected operations to be submittable before creating anything.

Perform the following MCP argument objects in order. Payload values are JSON strings, not nested objects. The one send_command is authorized only after those checks pass.

1. Call `list_modules` with:

```json
{}
```

2. Call `list_operations` with:

```json
{"module": "tenants"}
```

3. Call `list_operations` with:

```json
{"module": "parties"}
```

4. Call `describe_operation` with:

```json
{"operation": "tenants.get-tenant"}
```

5. Call `describe_operation` with:

```json
{"operation": "parties.create-party"}
```

6. Call `describe_operation` with:

```json
{"operation": "parties.get-party"}
```

7. Call `run_query` with:

```json
{"operation": "tenants.get-tenant", "payload": "{\"TenantId\":\"mcpcli-417-20261101-00c6a713\"}"}
```

8. Call `send_command` with:

```json
{"operation": "parties.create-party", "payload": "{\"PartyId\":\"party-418-desktop-20261101-1\",\"Type\":\"Person\",\"PersonDetails\":{\"FirstName\":\"Operator\",\"LastName\":\"Setup\"},\"ContactChannels\":[{\"PartyId\":\"party-418-desktop-20261101-1\",\"ContactChannelId\":\"email-party-418-desktop-20261101-1\",\"Type\":\"Email\",\"Value\":\"operator@example.test\",\"IsPreferred\":true}],\"Identifiers\":[{\"PartyId\":\"party-418-desktop-20261101-1\",\"IdentifierId\":\"external-party-418-desktop-20261101-1\",\"Type\":\"Other\",\"Value\":\"operator-setup\"}]}"}
```

9. Call `run_query` with:

```json
{"operation": "parties.get-party", "payload": "{\"PartyId\":\"party-418-desktop-20261101-1\"}", "entityId": "party-418-desktop-20261101-1"}
```

Stop immediately on any failure or uncertain command result. Never repeat send_command, add an idempotency key, change its payload/identity, fall back to CLI/curl or repair server configuration during this attempt. Only if the persisted projection is pending, bounded repeat parties.get-party reads for at most 45 seconds are permitted; retain every read.

The accepted command must have isError false, status accepted, selected tenant `mcpcli-417-20261101-00c6a713` and aggregateId `party-418-desktop-20261101-1`; keep its canonical message/correlation IDs and actual tool result. The final persisted document must have id `party-418-desktop-20261101-1`, isActive true, isErased false, PersonDetails Operator/Setup, preferred Email operator@example.test with contact ID `email-party-418-desktop-20261101-1`, and Other identifier operator-setup with ID `external-party-418-desktop-20261101-1`. Preserve actual result property casing. Matching text/structuredContent and actual persisted contents are required.

Report the actual tool calls/results and any assistance, trust/permission prompts or failures. Do not claim a full pass from discovery or command acceptance alone. Stop when the persisted read is verified; leave environment cleanup to the owner. This session does not replace the retained assisted 685-second timing exception.

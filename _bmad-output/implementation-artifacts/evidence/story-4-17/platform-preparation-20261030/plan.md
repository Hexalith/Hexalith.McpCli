# Story 4.17 temporary Platform environment preparation

The user selected environment preparation on 2026-10-30. This document specifies
the preparation work; it is neither an executable deployment packet nor approval
to deploy. Actual client and timing acceptance remain outstanding.

## Ownership and target

Work belongs in `/home/administrator/projects/hexalith/platform`, outside McpCli's
read-only `references/`. That checkout is on `main` at
`92f8f05187afc873806f48af75a736ee5ae997c0` and has unrelated modifications.
Prepare from isolated source inputs, recording full revisions and content hashes;
preserve the existing checkout's changes. Initialize no nested submodules and
change no recorded dependency versions.

Use the existing Kubernetes target at `192.168.1.30`, previously observed through
context `jpiquot@local`, API `https://192.168.1.30:6443`. Before a later deployment,
recheck the exact target and availability. Give the task a fresh namespace and
release identity. Keep Gateway access private, reached through an operator-local
port-forward. Do not reuse `ext-secrets-1-isolated`, another application's data,
its credentials, or a shared fixture endpoint.

## Existing composition

`PlatformHostedPublishing.Describe` derives workload metadata from
`PlatformApplicationGraph` and `PlatformDaprBindings`. The maintained chart in
`eng/helm-qualification/chart/` consumes that metadata, preserving declared Dapr
components, subscriptions and receiver ACLs.

Current Parties composition selects eight servers: `eventstore`, `tenants`,
`tenants-api`, `parties`, `memories`, `memories-domain-service`,
`memories-access-telemetry-clock` and `memories-access-telemetry`.
`PartiesAdoptionTests.ActualPartiesDeclarationValidatesAndSelectsEightMappedServers`
pins this closure. Retain the declared dependencies.

The chart's saved graph currently contains seven workloads and omits
`memories/domain`. Regenerate it through the canonical graph producer and reconcile
the stale count assertions in `PlatformHostedPublishingTests.cs` before rendering.
The generic chart and its current source declarations must agree. The native
Aspire probe uses `qualification.invalid` images; its output is not deployable.
The existing Helm fallback records why native Dapr export was insufficient.

## Preparation footprint

Add `eng/mcpcli-operator-setup/` in the owning Platform repository:

- `prepare.py` and `test_prepare.py`: validate source identities and the complete
  graph; resolve immutable image references, environment bindings and private
  credential references; render a new review packet. The preparer must perform
  no cluster, registry or application mutation.
- `profile.template.json`: define the exact input fields, with a strict
  distinction between public metadata and private credential locations. An
  unfilled template must fail preparation.
- A task-owned seed helper using the existing owner APIs, and `README.md`:
  describe the bounded bootstrap, access, verification and cleanup sequence.

Reuse existing generic composition and chart code. Any correction belongs to
Platform; do not add module-specific production behavior to McpCli or modify
module checkouts under `references/`.

## Authentication and initial state

Existing isolated-test configuration supports a private finite-lived JWT issuer
without a new identity server. `PlatformLocalProfile.cs` and the local profile
identify the real configuration keys; hosted resources must receive private
Secret references rather than literal keys in tracked values.

Keep bootstrap authority and signing material separate from client credentials.
Scope the operator identity to `system`, one task tenant, the required domains
and command/query permissions; verify the Parties write authorization rather
than inheriting a reader-only role. Keep client credentials outside transcripts,
command arguments, tracked files and review artifacts.

`PlatformNativeTestPreparation.cs` demonstrates the real bootstrap sequence:
bound-workload `BootstrapGlobalAdmin`, Gateway `CreateTenant` and `AddUserToTenant`
with the `system` envelope, persisted tenant confirmation, then the Memories
preparation required by the selected closure. Its routing catalog and bound
workload inputs come from `PlatformRoutingCatalogBootstrap.cs`. That method is a
runner-scoped reference, not a reusable installed endpoint. The task helper must
use the actual owner APIs and authentication seams. It must not forge successful
state or silently retry an uncertain submission.

## Review packet and verification

Preparation must produce:

- Exact source, graph, chart and image identities; actual pullable image digests;
  environment namespace/release and a complete resource inventory.
- Explicit CPU, memory and storage bounds; task-owned data services and mounts;
  existing control-plane prerequisites and private credential references. Do not
  change shared cluster identity, Dapr control-plane or unrelated infrastructure.
- Rendered application and environment manifests, seed operations and their
  principal scopes, access/port-forward commands, expiration and cleanup plan.
- Offline validation results and exact remaining blockers. Missing image digests,
  provider endpoints, required credentials or graph parity block an apply-ready
  result; synthetic fixture values never satisfy them.

Run focused Platform graph/parity and chart tests, plus preparation tests proving
missing or conflicting inputs are refused and no external write occurs. A local
render is not installed readiness. After the complete packet is reviewed and
deployment is authorized, recheck its bindings, deploy only its owned resources,
confirm declared readiness and persisted seed state, then supply the private
operator profile to the human client sessions. Record every uncertain result
without automatic command retry.

The final client task reads the selected tenant through Tenants, creates a fresh
Party in that tenant and reads its persisted details through the accepted 1.2.0
generic MCP server. The independent operator's timer starts before installation
and ends at the first successful `send_command`; all attempts and assistance stay
visible. Preparation, installation and offline protocol checks cannot replace
those executed acceptance records.

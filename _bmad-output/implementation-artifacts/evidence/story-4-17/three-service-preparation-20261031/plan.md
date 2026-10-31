# Approved three-service operator environment

On 2026-10-31 the human selected the three-service v1 topology. This supersedes
the full Platform reference-closure requirement for this temporary operator
environment. Continue implementation under the existing spec approval; the
completed deployment packet still needs review before it is applied.

## Ownership and behavior

Implement preparation in the owning Platform checkout at
`/home/administrator/projects/hexalith/platform/eng/mcpcli-operator-setup/v1/`.
Preserve the existing eight-workload preparer and all earlier attempts/evidence.
Preserve concurrent changes and commits in both repositories. Do not edit
`references/`, change dependency pins or rebuild/substitute the accepted tool.

The behavioral source is McpCli's existing qualified test topology:

- `tests/Hexalith.McpCli.AppHost/Program.cs`, `appsettings.json`,
  `TopologyConfiguration.cs` and its Dapr component files.
- `tests/Hexalith.McpCli.Integration.Tests/AspireTopologyFixture.cs`,
  `AdministratorAuthorityBootstrap.cs`, `ProjectionWriterBootstrap.cs` and the
  live runner's empty-store backup/bootstrap procedure.
- The accepted staged 1.2.0 tool and approved Tenants/Parties vectors. This work
  does not change its Contracts enrollment, output or routing behavior.

The application set is exactly Gateway, Tenants domain service and Parties
domain service. It has one task-owned state/pubsub/configuration provider where
the actual fixture requires it, private application/Dapr credentials and one
fresh tenant. It introduces no MCP server per module or identity server and
claims no qualification of Platform's full reference closure.

## Images and configuration

Inspect the actual released image configuration and packaged capabilities before
selecting each immutable digest. Existing registry reads resolve Gateway
3.128.3/3.128.4, Tenants 5.10.0 and Parties 1.5.1; see the previous
`remote-inspection-20261030/registry.json`. Current source has adopted EventStore
3.128.4 for a Tenants floor: validate the effective image/package compatibility
instead of assuming that the older Gateway is sufficient. The accepted 1.2.0
tool remains unchanged. Artifact/metadata downloads needed for this preparation
are reads; no registry publication is authorized.

Do not infer capability equivalence from tags or manifest existence. Inspect
the image's runtime/configuration, entrypoint and relevant assembly metadata
without starting applications. If a released artifact cannot supply the fixture
behavior, use a compatible owner-provided source/artifact path and retain its
exact identities and evidence. Refuse an unresolved mismatch.

Reproduce the fixture's `system` Tenants/global-administrator routes, wildcard
`party` route, topic settings and authenticated application channels. Scope the
human client JWT to the task tenant and required domains/permissions, including
Tenants reads through `system`; keep administrator/writer activation authority
separate. Preserve genuine membership/bootstrap and persisted-state checks.
Generate fresh task-owned credentials outside the checkout, with private modes.
Handle configured registry authentication privately; any image-pull Secret
creation/delegation must be explicit in the review packet. Never expose credentials
or retrieve Kubernetes Secret resources.

Use a fresh `mcpcli-417-*` namespace on `jpiquot@local`, API
`https://192.168.1.30:6443`. Keep all services private and expose Gateway only
through an operator-local loopback port-forward. Use the existing Dapr control
plane; do not mutate shared Dapr, cluster identity, CRDs or other applications.
Bound workload/storage resources, preserve channel/receiver protections and use
task-owned data. Read-only target metadata checks remain authorized.

## Concrete packet

Produce a filled packet, not only a profile template or generic validator:

1. Source/fixture/image/configuration bindings and hashes, exact target,
   namespace/release, resource inventory and resource limits.
2. Rendered namespace, data service, application and Dapr manifests; private
   input-file references, Secret names/keys and creation steps without values.
3. A phased initial-state procedure. Establish the actual task store as empty
   and capture its provider-native pre-application backup before starting
   applications. Do not substitute a fabricated receipt or a different store's
   backup. Observe persisted administrator bootstrap, activate the real writer
   protocol using the actual runtime source identity, seed the task tenant/member
   and confirm the resulting state through owner APIs.
4. Exact apply, readiness, seed, local access and cleanup commands. Bind seed
   operations to the reviewed packet/hash/scope/expiry. Mutations execute once;
   only observation calls may poll within deadlines. An uncertain outcome stops
   further writes and remains retained.
5. Local validation and a clear boundary between prepared artifacts and executed
   acceptance. Any backup/UID/state that can exist only after authorized
   installation must be produced by the reviewed phase, never invented during
   preparation. Recheck target and freshness before application.

Validate manifests, fixture parity, image/package capabilities and sensitive
boundaries with the narrow relevant checks. Every new guard needs a meaningful
refusal regression. Reuse the earlier preparer's tested mechanisms where useful;
do not weaken its historical full-closure checks to accept this different fixture.

Resolve preparable inputs from available source, artifacts and configured local
authentication. Report any genuine remaining blocker with exact commands and
results. Deployment, publication, Kubernetes Secret retrieval and domain writes
remain outside the current authorization. Actual three-client sessions,
persisted Party evidence and the independent README-only timer remain required
after the environment is installed and handed over.

## Recovery after the first approved deployment (2026-10-31)

The exact packet `79b9b6febc3c6ba8ca9753c1d8a4776f4eef07470fe25dcec3a01b3c84e5cedd` was approved by the human and executed once. Infrastructure and a real empty Redis backup succeeded. Gateway phase exited 1 with `Phase stopped: RemoteDisconnected. Preserve the journal; do not retry uncertain writes.` The Pod existed but had no `daprd` container or init sidecar. The injector logged `service account 'jpiquot' not on the list of allowed controller accounts`. Its webhook selectors are empty and failurePolicy is Ignore. Exact sanitized evidence, approval, original phase receipts and cleanup are in sibling `execution-20261031/`. The namespace and its backing volume were removed using approved UID-bound cleanup; preserve the private attempt4 backup and journal. No later application/bootstrap/seed/handoff phase ran.

Complete recovery preparation in the same owning `v1/` directory, without executing another deployment. Preserve historical packet bytes, receipts and failures. Use controller-owned application Jobs with `restartPolicy: Never`, `backoffLimit: 0`, one completion/parallelism, and a replacement/failure policy that prevents automatic bootstrap re-execution; validate actual target support from bounded metadata/official Kubernetes/Dapr sources. The Dapr 1.18.1 default allowlist includes kube-system:job-controller (primary source: https://raw.githubusercontent.com/dapr/dapr/v1.18.1/pkg/injector/service/injector.go); verify the target controller identity without impersonating it or changing the shared injector. Keep the exact three applications, immutable images, resource limits and Secret boundaries. Redis may remain its original plain task Pod because it does not need Dapr.

Resolve the single owned application Pod from its Job UID and task labels, bind its identity before observation/forwarding, and explicitly require actual sidecar injection before relying on Running/liveness. Support ordinary and native-init sidecar layouts only when observed/appropriate. GET observations must tolerate transient connection refusal/disconnect only within the existing bounded poll and preserve failure diagnostics; never retry an activation or domain-command POST. Read-only query polling can be bounded, but uncertain POSTs remain terminal. Keep application readiness/backup/admin/writer/member gates unchanged.

Produce fresh external private inputs and a new filled namespace packet with explicit Job controls, dynamic Pod ownership, forward/access commands, source/evidence bindings and approved cleanup procedure. Add meaningful refusal and startup-transport regressions; retain the original error and successful tests. Explain the controller-only adaptation, exact target/image/resources, credentials delegation and expiry in the concrete guide. Update the McpCli public snapshot/status/checklist/spec notes while retaining original source and packet identities. Recheck accepted 1.2.0 provenance and protect the independent fresh-install timing requirement. Stop at the concrete review boundary; the original approval does not authorize applying a different packet.

### Startup-order finding for recovery

The failed Gateway's sanitized log also shows `eventstore-domain-metadata:parties` calling `/admin/operational-index-metadata` during startup, before `/alive` is available. Current ordinary owner source `references/Hexalith.EventStore/src/Hexalith.EventStore/Indexes/AdminOperationalIndexHostedService.cs:46` awaits per-domain metadata in `StartAsync`, tolerates partial metadata failures and starts its refresh loop afterward. This checkout can differ from the image; use the actual observed image logs and inspect required runtime members before relying on details. The qualified fixture creates all three application resources before awaiting topology readiness (`tests/Hexalith.McpCli.AppHost/Program.cs:73`). Avoid a startup dependency cycle in which Gateway liveness must pass while its registered Tenants/Parties services are still deliberately absent. Arrange the fresh packet's app-create versus app-liveness/readiness phases to match fixture semantics after the verified backup, without submitting domain commands/named deliveries before administrator/writer gates. Retain explicit startup ordering and test it.

## Recovery after the second approved deployment: node-local DNS

The human approved exact recovery SHA `1f632480a23e000ade4abbb9a89ec6632fd29c6f75268eac2b977cc181fd69fc`; infrastructure/real empty backup and all three injected controller Jobs completed, followed by Gateway liveness. Administrator observation exited 1 with `Phase stopped: observation-deadline-exceeded. Preserve the journal; do not retry uncertain writes.` Its retained read observations repeatedly returned HTTP 500. Writer, seed and handoff never ran. Dapr logs stop at `Fetching initial identity`; app logs report 127.0.0.1:3500 refused. The existing Pod resolver is nameserver `169.254.25.10`, and bounded `timeout 5 getent ahostsv4` for Dapr Sentry/Redis exited 143 without an answer. The namespace NetworkPolicy only allowed kube-system namespace DNS, omitting node-local hostNetwork traffic. Selected kube-system `daemonset/nodelocaldns` metadata confirms hostNetwork and its actual local resolver args; no shared setting was changed. Redis DBSIZE remained zero. Approved UID cleanup removed namespace and volume; preserve original private attempt6 backup/journal and all `recovery-execution-20261031/` observations and receipts.

Prepare a fresh concrete packet, without applying it, retaining the same three immutable application images, controller Job/no-retry/UID rules, fixed tenant routing, private credential bounds, actual backup/writer/admin/member gates and independent client/timing acceptance. Bind the exact observed node-local resolver in target evidence and allow only its /32 (or actual explicit observed resolver address) TCP/UDP 53 egress, alongside legitimate cluster DNS rules; do not broadly open egress. Retain source/target/policy hashes. Inspect the owning Platform's existing network-policy/DNS configuration to avoid another target-specific omission. Read-only target DNS metadata and actual resolver observations are authorized; no Secret retrieval or shared changes.

Add an early read-only DNS/policy check using the newly established provider Pod before any application Jobs: verify the actual Pod resolver matches the reviewed allowed addresses and bounded resolution of Redis and Dapr control-plane endpoints succeeds. No synthetic resolver proof, policy bypass or undeclared temporary workload. Use tools genuinely present in the pinned provider image; resolve any preparable tool/config requirements before review. Preserve meaningful timeout/diagnostic output without credentials. After all apps are created and liveness observed, require actual sidecar runtime readiness (without prematurely requiring writer-gated app /ready) before persisted administrator queries. Refuse missing, terminated, unready or identity-changed sidecars under bounded observation; keep POST non-retry and writer/app readiness gates. Test each new refusal plus delayed DNS/sidecar success, safe channels and absence of mutation submission after failure.

Produce new private inputs/namespace and a filled packet/guide with exact DNS adaptation and phase sequence, local checks and protected handoff. Update separate public snapshots/status/checklist/spec notes, preserving both approved failed executions and all earlier packets. Stop for concrete review before applying a changed packet. No operator client or timer has run; no live acceptance may be inferred.

Existing owner reference: `eng/ext-secrets-1/install_isolated_registry.py:148` already contains the node-local `169.254.25.10/32` UDP/TCP 53 NetworkPolicy rule. Inspect that rule as ordinary source only; its unrelated IDP/Secret retrieval workflow is outside this task and must not be invoked. Preserve all other existing isolation rules.

## Recovery after third approved execution: Gateway metadata probe authentication

The human approved DNS packet SHA `23f8ac08ed0051024c4e1c0264fafd7037f96040ec911b58cca72124dac9094f`. This time infrastructure, actual installed-policy/resolver/DNS checks, native empty backup, all three injected Jobs, Gateway liveness, all sidecar runtime identities/readiness, and persisted administrator membership succeeded. Writer activation was submitted once and persisted protocol v2 for `717a06e16c3afd81b904eaf4de646b74b13262d2`. Its readiness poll then expired on HTTP503. The stopped writer journal remains uncertain; do not rewrite it or activate again. Exact selected maintenance-marker HGET (not event-stream reads) proved schemaVersion1/writerProtocolVersion2/source commit/activation time. Seed and handoff never ran. Approved UID cleanup removed namespace and volume. Receipts and sanitized logs are in `dns-execution-20261031/`; private attempt7 backup/journal remain untouched.

Gateway health logs name `dapr-actor-placement`: its raw local metadata HTTP probe receives401. A temporary private metadata forward (already stopped) observed unauthenticated GET401 and configured-token GET200 with actorRuntime.hostReady=true, runtimeStatus RUNNING and placement connected. This is a probe/API-auth mismatch, not absent actor placement. Current ordinary owner source `references/Hexalith.EventStore/src/Hexalith.EventStore/HealthChecks/DaprActorPlacementProbe.cs` uses HttpClient.GetAsync on local /v1.0/metadata without adding the API token; `HealthCheckBuilderExtensions.cs` registers it without a header handler. Verify the relevant effective image member/behavior rather than assuming newer checkout equivalence. No upstream production or references edits are authorized.

Prepare a compatible fresh configuration packet, preserving all successful DNS, Job, identity, sidecar, real-backup/admin/writer/member and POST non-retry controls. Assess the qualified fixture's API/app-channel distinction. Preferred minimal adaptation is Gateway-only local Dapr HTTP/gRPC API without the optional API token, strictly bound to127.0.0.1 inside its Pod, so the unchanged real probe can work. Retain the required Gateway app-channel token, public Gateway JWT authentication, Dapr mTLS, network isolation and Tenants/Parties local API token protections. Remove only the unused Gateway API-token Secret/env/annotation if this mode is verified compatible; make the resulting eight-Secret inventory and local trust boundary explicit for human review. Never expose the tokenless API publicly or across Pods, disable health checks, force readiness, substitute a synthetic probe, or change accepted tool/contracts/images without a proven owner-compatible need.

Add a pre-writer real metadata/actor-placement check matching the unchanged health-probe behavior, after sidecar runtime readiness and before irreversible writer activation. It must prove auth compatibility and actual hostReady through the real Gateway sidecar metadata endpoint using an explicitly reviewed temporary loopback-only forward/port (for example18171); do not invent placement state. Keep genuine Gateway /ready and all app readiness after writer activation. Add meaningful guards/tests for token-mode/private-loopback/application-token/JWT/mTLS constraints, missing or unauthenticated/forbidden/unready metadata, delayed success and no mutation submission on refusal. Preserve the original accepted activation marker and never replay it in the retired store.

Prepare fresh private inputs, namespace, exact packet/guide and separate public snapshots/status/checklist/spec notes. Resolve preparable inputs without new deployment; stop for concrete review, explicitly explaining the Gateway local API mode change and unchanged remote authentication. Neither an operator client nor the independent timer has run.

Additional retained observation to assess, without assuming a new failure: `dns-execution-20261031/tenants-writer-diagnostic-sanitized.log` contains `WireAdminAssertionRemoved` for the initial BootstrapGlobalAdmin. Persisted administrator lookup subsequently succeeded, so this does not prove a seed-authority defect. Before finalizing, check that the approved raw CreateTenant/AddUser seeding uses the now-persisted administrator authority through the effective Gateway/domain configuration; preserve real authority checks and do not execute sample commands or weaken signed/verified admin boundaries during preparation. Resolve any concrete configuration mismatch supported by effective artifacts/fixture, while retaining the exact two reviewed seed payloads.

## Current continuation: assisted Desktop admission failure (2026-10-31)

The fourth approved packet `063bac572c44e85441169aa4410b4001886f5ae7ed6e212f3c5138c607e86be4` completed every owner phase through handoff, including persisted tenant/member and non-administrator CLI reads. Its environment remains live: namespace/tenant `mcpcli-417-20261031-155f9b6d`, Gateway Job UID `28e35ef6-189a-443a-8faf-5e576768293f`, Gateway Pod `eventstore-l6rpl` UID `1daa2ee7-b949-41f2-b41c-4ce33e902e25`. All containers were Ready with zero restarts at the bounded diagnostic observation. The review expires 2026-11-01T07:37:50Z; the current operator token expires 2026-10-31T09:54:53Z. Do not retire this environment while preparing a repair.

The user needed direct assistance configuring Windows Claude Desktop. The existing `%APPDATA%/Claude/claude_desktop_config.json` was backed up and only its `mcpServers.hexalith` entry added; `ado`, `playwright` and other preferences were preserved. The installed MSIX application reports version 4.4212.0.0. A separate owner Windows-to-WSL stdio check initialized successfully and exposed the five generic tools/both modules; this is supplementary, not the actual GUI task or independent timing. The user then reported both modules, a successful exact tenant/member read through `system`, local idempotency ULID validation failure (no submission), and one subsequent failed Party command plus read. Preserve the assisted failed attempt; no timer measurement or complete three-client acceptance exists.

Submitted Party: `party-417-desktop-20261031-1`, selected tenant above, idempotency key `01M68JJB7QJS46XXDT4AQCDRT3`. Command correlation `01M68JJNZN338R4KCQNC8T9EFX` returned503 `idempotency_admission_unavailable`; read correlation `01M68JJW11DZ07BHQTBB2KQP21` returned500 `actor-not-found-infrastructure`. Actual Gateway logs at 2026-10-31T08:52:48Z show `InvalidOperationException` at admission and no routing at that request; at08:52:54Z Gateway invoked Parties `/query`, received HTTP200 containing the failure, then mapped it to500. Never replay this command automatically, with either the same or a different key.

Private bounded logs and decompiled effective DLL members are under `/tmp/mcpcli-417-v1-private-20261031-attempt8/client-diagnostics-0854/`. These logs may contain private information; retain only verified sanitized relevant observations publicly. The Gateway's `/etc/gateway/appsettings.json` and environment omit `EventStore:IdempotencyAdmission`, and the image appsettings contain no such section. Effective `Hexalith.EventStore.Server.Commands.ConfigurationIdempotencyDigestKeyProvider.GetKeyRingAsync` refuses disabled/non-Configuration options; effective options default `Enabled=false`. Actual DLLs are in `/tmp/mcpcli-417-v1-images-20261031/{eventstore,parties}/`; do not substitute newer source. The effective Parties `PartySdkQueryService.ReadDetailAsync` returns the legacy `actor-not-found-infrastructure` reason for missing/erased detail; this 500 alone is not evidence of failed actor placement.

Prepare the smallest configuration-only repair in owning Platform `eng/mcpcli-operator-setup/v1/`. Verify actual Gateway admission configuration and trusted-intent support needed by the exact accepted CreateParty contract before finalizing. Keep the accepted CLI, three images, public authentication, channel protections, tenant routing, current persisted state and original execution journals unchanged. Generate any new digest-key material privately, with strong length/version checks; no material in public manifests, environment literals, command arguments or evidence. Configuration-backed keys are permitted only by the effective Development/test policy; any Secret references and new permissions must be explicit and narrowly scoped in the repair packet.

Prefer a reviewed Gateway-only repair retaining the existing Redis, Tenants, Parties, tenant/member and writer state. Establish whether the effective singleton options/key-provider can reload; never assume ConfigMap propagation updates cached admission settings. If a Gateway Job replacement/restart is required, prepare its exact old-UID preconditions, one-shot deletion/create, replacement identity binding, real metadata/health/read-only verification and owned forward recovery. No mutation may run during preparation. Existing no-restart approval does not cover this replacement: stop at a concrete repair review. Do not replay bootstrap, writer activation, seed or any Party write, or delete/replace the Redis/domain workloads. If these requirements cannot be met, report the concrete blocker instead of silently choosing another topology or bypassing admission.

Protect the preparation with meaningful refusal/success tests and exact configuration/artifact bindings. Retain sanitized user/server attempt evidence, correct the earlier live-ready status to explain the blocked Party task, and update guide/checklist/spec as needed. Keep the frozen intent and baseline untouched. No actual client or timer success may be claimed; changed remote configuration remains pending concrete review.

The parent retained the actual user-reported outcomes and sanitized corroborating server messages in `claude-desktop-20261031-attempt1/{user-report,server-observations}.json` beside this plan. The exact staged 1.2.0 `describe parties.create-party --profile operator` reports `envelope.idempotencyKeyRequired=false`: the key is optional for this operation. Do not claim that the contract requires it. The reported caller supplied a key, which selected the currently unconfigured trusted-admission path; removing/changing it is not an authorized recovery for this uncertain submission. Preserve the README argument contract and verify the actual trusted-intent adapter support before treating a key-provider change alone as sufficient.

Scope of any adapter blocker: it applies to keyed admission. The existing approved README example omits the optional key and must not be described as requiring this adapter. An owner artifact/composition decision is necessary to enable trusted keyed admission; a key-only restart would not fix it. Preserve the original keyed attempt and do not change/replay its arguments automatically. A separate fresh human-approved test using the existing README argument contract is a distinct possible next action, with fresh identifiers and explicit human control, not proof that the failed keyed attempt succeeded. Do not submit that action during diagnostic/preparation work or silently erase the recorded failure.

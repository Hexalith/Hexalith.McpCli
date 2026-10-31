# Temporary operator topology decision

The approved plan selects Platform's complete eight-workload reference closure.
The operator acceptance goal itself requires the accepted generic MCP server,
Tenants and Parties. This proposal records a scope choice; it authorizes no
deployment and changes no approved module enrollment.

## Current evidence

Bounded inspection of `jpiquot@local` confirmed API
`https://192.168.1.30:6443`, Dapr 1.18.1 and two OpenEBS hostpath storage classes.
It found no Parties workload. Existing application namespaces and credentials are
not the new task environment.

The reference closure requires `tenants/api` and `memories/domain`. Registry
manifest inspection returned not-found for `tenants-api:5.11.1`,
`tenants-api:5.10.0` and `memories-domain-service:3.0.10` at their declared
repository names. Other module manifests resolve. See `registry.json` and
`registry-followup.json`. No image publication occurred.

A mapped-source Builds-owned Gateway now compiles with the catalog/channel calls
and has a validated local image archive. This resolves the host compilation/base
input limitation; it does not establish hosted catalog, private provider,
bootstrap or runtime readiness for the eight-workload composition. The earlier
package-mode and Platform.Custody failures remain historical attempts.

## Proposed operator-only alternative

Prepare a new private namespace on the same selected cluster using the existing
three-service McpCli v1 test topology: EventStore Gateway, Tenants domain service
and Parties domain service, with isolated Dapr state/pubsub and task credentials.
Use `tests/Hexalith.McpCli.AppHost/Program.cs`, its configuration and the live
topology runner's source-bound bootstrap/writer procedures as the behavioral
reference. Those tests underlie the accepted source's successful CI; this is not
a claim that the topology or any GUI client has executed on the selected cluster.

The corresponding released image manifests resolve:

| Workload | Image | Manifest digest |
| --- | --- | --- |
| Gateway | `registry.hexalith.com/eventstore:3.128.3` | `sha256:0ab1771c85e22784dd0f2becdd1824b46879a035a226a61b7551c951297800a5` |
| Tenants | `registry.hexalith.com/tenants:5.10.0` | `sha256:2bc415a61466693bfa7e6c0df1c9aab319b0ef2e82c620897aa9faa1b58f75a5` |
| Parties | `registry.hexalith.com/parties:1.5.1` | `sha256:85afc9e954146883da56edce78e2ddaf401a47b35241bdceed87dfc20217aceb` |

Manifest availability alone proves neither fixture-equivalent configuration nor
node pullability or readiness. Preparation must validate the image configuration
and actual packaged capabilities against the fixture, retain source/contract
bindings, and refuse a mismatch. Do not bypass the real writer activation,
administrator bootstrap, caller authentication or tenant authorization. The human
client identity remains separate from bootstrap authority.

Keep the exact accepted 1.2.0 tool, both enrolled Contracts versions, one generic
stdio server, fixed Tenants `system` routing, selected Parties tenant and the same
three-client/persisted-state/timing requirements. Retain every failed attempt.
Deployment still requires review of the concrete packet. This alternative is
operator-test evidence, not qualification of Platform's full reference closure.

## Choices

- **Use the three-service v1 topology:** explicitly replace the approved
  full-reference-closure constraint for this temporary operator environment.
  Prepare the fixture-equivalent packet and validate all bindings before review.
- **Keep the full Platform closure:** retain the eight-service constraint and
  finish the missing image/provider/catalog/bootstrap preparation. No incomplete
  profile or native-runner assumption can be presented as apply-ready.

The recommended choice is the three-service topology because its scope matches
the v1 task and its tested composition. The human must approve that change to the
frozen constraint before implementation follows this alternative.

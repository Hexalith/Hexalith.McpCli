# Query spike for Story 2.5

Status: **live page received** (2026-10-01). Synthetic acceptance coverage passes. After the user authorized reuse of the running local topology, EventStore.Client 3.110.0 returned a Tenants page containing one item. `index` remains a candidate for Tenants maintainer confirmation in Story 4.8.

## Revisions and pinned boundary

| Component | Full revision / version |
| --- | --- |
| McpCli baseline | `ff7f5e18ee9eeeee7dae30ca52b2c6ee2e841896` |
| Root-declared EventStore checkout | `ed11fd62eb736af6cf28a80654cf421f0764e03e` |
| Root-declared Tenants checkout | `3ce15d103227fb7767820fc89c51b75b86401ff3` |
| Root-declared Builds checkout | `21ce044ab465ccb2adab58b3d66e394ffbecf3c2` |
| Root-declared Commons checkout | `c13dc6679aa91144b6d541078f3f20019d79c2eb` |
| Authorized runtime Tenants checkout (`/home/administrator/projects/hexalith/tenants`) | `78e09184247c38641242c676eed40502a477eb7e` |
| Authorized runtime EventStore checkout (`/home/administrator/projects/hexalith/tenants/references/Hexalith.EventStore`) | `19dc1f82122564453163ac010dc7e5ae81db7ed3` |
| EventStore.Client and its Contracts dependency | `3.110.0` |
| Client / Contracts package source revision (both `.nuspec` files) | `27279fe6431925a6ea046c3f89af61487185c7de` |
| SDK / Aspire CLI | `.NET 10.0.401` / `13.5.3+b5f143315ffb6968ea939a9978797a5b20e4c688` |

The spike directly references the pinned Client package; it has no McpCli or Tenants package/project reference. The runtime checkout revisions above were observed with clean working trees. Aspire resource `project.path` values identified those runtime repositories; they differ from McpCli's root-declared checkouts under the user's approved topology substitution. Runtime source is not evidence of the pinned package's validation pattern. Obtain the pinned pattern with:

```sh
git -C references/Hexalith.EventStore show 27279fe6431925a6ea046c3f89af61487185c7de:src/Hexalith.EventStore/Validation/SubmitQueryRequestValidator.cs
```

That source limits `AggregateId` to 256 characters and uses `^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$`. `index` satisfies both checks. The [pinned validator source](https://github.com/Hexalith/Hexalith.EventStore/blob/27279fe6431925a6ea046c3f89af61487185c7de/src/Hexalith.EventStore/Validation/SubmitQueryRequestValidator.cs) supports only syntactic validity; the [authorized live run](#authorized-live-run) supplies the live acceptance evidence, and maintainer confirmation remains for Story 4.8.

The cited sources are unchanged at the runtime revisions. Each of these comparisons printed no differences (code review, 2026-10-01):

```sh
git -C /home/administrator/projects/hexalith/tenants diff --stat 3ce15d103227fb7767820fc89c51b75b86401ff3 78e09184247c38641242c676eed40502a477eb7e -- src/Hexalith.Tenants.Contracts/Queries/ListTenantsQuery.cs src/Hexalith.Tenants.Contracts/Queries/PaginatedResult.cs
git -C references/Hexalith.EventStore diff --stat 27279fe6431925a6ea046c3f89af61487185c7de 19dc1f82122564453163ac010dc7e5ae81db7ed3 -- src/Hexalith.EventStore/Validation/SubmitQueryRequestValidator.cs
```

## Request and identity

The direct-client request was one POST to the authorized running EventStore resource's `/api/v1/queries` endpoint:

```json
{"tenant":"system","domain":"tenants","aggregateId":"index","queryType":"list-tenants","projectionType":"tenant-index","payload":{"PageSize":25}}
```

`ListTenantsQuery` declares `tenants`, `list-tenants`, and `tenant-index` in `references/Hexalith.Tenants/src/Hexalith.Tenants.Contracts/Queries/ListTenantsQuery.cs`. Current Tenants uses the platform domain-query handler; no obsolete custom projection actor is synthesized. `PageSize` is the query's own payload member, and public envelope paging is absent. No correlation identifier or extensions are generated.

The user authorized reuse of the running topology and its generated local administrator identity. The token endpoint was `https://localhost:8180/realms/hexalith/protocol/openid-connect/token`, with client/audience `hexalith-eventstore` and the password grant. The local realm grants the generated identity access to `system` and the query permission; the AppHost bootstraps its stable subject as a Tenants global administrator. Static example credentials and authentication bypasses were not used.

Aspire `describe` redacts generated username/password values. The launcher used the `eventstore-admin-ui` PID reported by Aspire to read its actual environment in memory and passed the generated username/password and discovered endpoints to the harness through stdin. It forwarded that resource's `SSL_CERT_DIR` for the local development certificate trust. No credentials, token, or raw resource description were printed or saved. The successful authenticated Gateway response supplies the live authorization evidence.

No separate endpoint or administrator identity was allocated. The query used the user-owned endpoint `http://localhost:8080/api/v1/queries`. No user resources were started, stopped, restarted, or changed.

## Initial isolation checks and approved resolution

Read-only commands run from the McpCli repository:

```sh
aspire --version
aspire ps --non-interactive --format Json
aspire describe --apphost /home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants.AppHost/Hexalith.Tenants.AppHost.csproj --non-interactive --format Json
aspire describe --apphost references/Hexalith.EventStore/src/Hexalith.EventStore.AppHost/Hexalith.EventStore.AppHost.csproj --non-interactive --format Json
aspire start --help
aspire docs search 'aspire start isolated' --non-interactive
aspire docs get aspire-start-command --non-interactive
aspire docs search 'isolated Dapr' --non-interactive
aspire docs get set-up-dapr-resources-in-the-apphost --non-interactive
dotnet msbuild references/Hexalith.EventStore/src/Hexalith.EventStore.AppHost/Hexalith.EventStore.AppHost.csproj -p:UseHexalithProjectReferences=true -p:HexalithTenantsBasePath=/home/administrator/projects/hexalith/mcpcli/references/Hexalith.Tenants/src -getProperty:HexalithTenantsBasePath,HexalithTenantsFromSource,UseHexalithProjectReferences
unshare --net true
```

Do not save raw `aspire ps` / `describe` output: it can contain dashboard tokens and resource credentials. Only the following sanitized findings are retained:

- `aspire ps` found the user-owned Tenants AppHost running outside this workspace. EventStore, Tenants, and their sidecars are running; the root-declared EventStore AppHost is not running (`No AppHost is currently running ...`).
- User EventStore endpoint: `http://localhost:8080`; EventStore Dapr HTTP endpoint: `http://localhost:3501`. User sidecars use app IDs `eventstore`, `tenants`, and `tenants-api`, with placement `localhost:50005` and scheduler `localhost:50006`.
- CLI help/docs describe `--isolated` as randomizing ports and isolating user secrets. That does not establish separation of Dapr app identities or arbitrary shared filesystem paths.
- `references/Hexalith.EventStore/src/Hexalith.EventStore.Aspire/HexalithEventStoreExtensions.cs` hardcodes `AppId = "eventstore"` and defaults `eventStoreDaprHttpPort` to `3501`. Current AppHost does not expose that argument or the app IDs as configuration. Domain module app IDs also remain `tenants` / `tenants-api`.
- `AspireDaprLocalServiceEndpoints` supports `Dapr:PlacementHostAddress` / `Dapr:SchedulerHostAddress`; overriding those two services alone would not separate the fixed sidecar endpoint, service-discovery identities, or filesystem state.
- AppHost `ResolveIsolatedDaprComponentPath` deletes every YAML file under the shared `/tmp/hexalith-eventstore-dapr-components/statestore/` directory before copying its component. This existing directory was present. `--isolated` does not rewrite this explicit `Path.GetTempPath()` location. Keycloak render cleanup and empty-resource paths also need ownership verification before a second host starts.
- MSBuild evaluated the root path successfully: `HexalithTenantsBasePath=/home/administrator/projects/hexalith/mcpcli/references/Hexalith.Tenants/src`, `HexalithTenantsFromSource=true`, `UseHexalithProjectReferences=true`. No nested checkout was needed or initialized.
- The network namespace capability probe exited 1: `unshare: unshare failed: Operation not permitted`.

**Initial blocker:** the existing AppHost had no verified way to start beside the user's topology with separate Dapr identities, fixed endpoints, and shared temporary files under the original permitted footprint. Startup was not attempted. The user then explicitly authorized a read-only pinned-client query against the running topology, relaxing the separate isolated-run requirement; the spec records that approval. No upstream AppHost change was required for this proof.

No spike runtime resources were created. The user-owned host was neither stopped nor restarted. The temporary source/build directory below contains no credentials and remains available for reproduction.

## Reproduce the prepared harness

Recreate the credential-free harness files if `/tmp` has been cleared:

```sh
mkdir -p /tmp/mcpcli-story-25-spike
cat > /tmp/mcpcli-story-25-spike/Spike.csproj <<'CSPROJ'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Hexalith.EventStore.Client" Version="[3.110.0]" />
  </ItemGroup>
</Project>
CSPROJ
cat > /tmp/mcpcli-story-25-spike/Program.cs <<'CS'
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Queries;
using Microsoft.Extensions.Options;

const string aggregatePattern = "^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$";
bool candidateMatches = "index".Length <= 256 && Regex.IsMatch("index", aggregatePattern, RegexOptions.CultureInvariant);
if (!candidateMatches)
{
    throw new InvalidOperationException("Candidate does not satisfy the pinned Gateway pattern.");
}

var request = new SubmitQueryRequest("system", "tenants", "index", "list-tenants", "tenant-index",
    JsonSerializer.SerializeToElement(new { PageSize = 25 }));
var json = new JsonSerializerOptions(JsonSerializerDefaults.Web)
{
    DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull,
};
if (args.SequenceEqual(new[] { "--validate-only" }))
{
    Console.WriteLine(JsonSerializer.Serialize(new
    {
        client = typeof(EventStoreGatewayClient).Assembly.GetName().Version?.ToString(),
        pin = "3.110.0",
        candidateMatches,
        aggregatePattern,
        request,
        submitted = false,
    }, json));
    return 0;
}

// The launcher sends this JSON through stdin; credentials are never command arguments or files.
string stage = "input";
using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(30));
try
{
    using JsonDocument settings = JsonDocument.Parse(await Console.In.ReadToEndAsync(timeout.Token));
    JsonElement root = settings.RootElement;
    Uri gatewayUrl = new(root.GetProperty("gatewayUrl").GetString()!);
    Uri tokenEndpoint = new(root.GetProperty("tokenEndpoint").GetString()!);
    using var identityClient = new HttpClient();
    using var form = new FormUrlEncodedContent(new Dictionary<string, string>
    {
        ["grant_type"] = "password",
        ["client_id"] = "hexalith-eventstore",
        ["username"] = root.GetProperty("adminUsername").GetString()!,
        ["password"] = root.GetProperty("adminPassword").GetString()!,
    });
    stage = "authentication";
    using HttpResponseMessage authentication = await identityClient.PostAsync(tokenEndpoint, form, timeout.Token);
    if (!authentication.IsSuccessStatusCode)
    {
        Console.WriteLine(JsonSerializer.Serialize(new { blocker = "administrator_token_request_failed", stage, status = (int)authentication.StatusCode }, json));
        return 2;
    }

    using JsonDocument tokenDocument = JsonDocument.Parse(await authentication.Content.ReadAsStringAsync(timeout.Token));
    if (tokenDocument.RootElement.ValueKind != JsonValueKind.Object
        || !tokenDocument.RootElement.TryGetProperty("access_token", out JsonElement accessToken)
        || accessToken.ValueKind != JsonValueKind.String
        || string.IsNullOrWhiteSpace(accessToken.GetString()))
    {
        Console.WriteLine(JsonSerializer.Serialize(new { blocker = "authentication_missing_token", stage }, json));
        return 2;
    }

    string token = accessToken.GetString()!;
    using var http = new HttpClient { BaseAddress = gatewayUrl, Timeout = TimeSpan.FromSeconds(30) };
    http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var client = new EventStoreGatewayClient(http, Options.Create(new EventStoreGatewayClientOptions { BaseAddress = gatewayUrl }));
    stage = "gateway";
    EventStoreQueryResult result = await client.SubmitQueryAsync(request, cancellationToken: timeout.Token);
    if (result.Payload is not { ValueKind: JsonValueKind.Object } page
        || !page.TryGetProperty("items", out JsonElement items) || items.ValueKind != JsonValueKind.Array)
    {
        Console.WriteLine(JsonSerializer.Serialize(new { blocker = "response_was_not_a_page", stage }, json));
        return 2;
    }

    // Retain page shape and counts; remove tenant details and opaque cursor values from evidence.
    JsonObject sanitizedPage = JsonNode.Parse(page.GetRawText())!.AsObject();
    sanitizedPage["items"] = new JsonArray(items.EnumerateArray().Select(_ => (JsonNode?)JsonValue.Create("[redacted tenant]")).ToArray());
    if (sanitizedPage["cursor"] is not null)
    {
        sanitizedPage["cursor"] = "[redacted cursor]";
    }

    Console.WriteLine(JsonSerializer.Serialize(new
    {
        pin = "3.110.0",
        endpoint = new Uri(gatewayUrl, "api/v1/queries"),
        request,
        candidateMatches,
        page = sanitizedPage,
        paging = result.Metadata?.Paging is { } paging ? new
        {
            paging.PageSize,
            paging.Offset,
            paging.TotalCount,
            paging.HasMore,
            hasNextCursor = paging.NextCursor is not null,
        } : null,
    }, json));
    return 0;
}
catch (EventStoreGatewayException exception)
{
    Console.WriteLine(JsonSerializer.Serialize(new
    {
        blocker = "gateway_error",
        stage,
        exception.StatusCode,
        exception.ReasonCode,
    }, json));
    return 2;
}
catch (HttpRequestException)
{
    Console.WriteLine(JsonSerializer.Serialize(new { blocker = stage + "_transport_failure", stage }, json));
    return 2;
}
catch (OperationCanceledException)
{
    Console.WriteLine(JsonSerializer.Serialize(new { blocker = stage + "_timeout", stage }, json));
    return 2;
}
catch (JsonException)
{
    Console.WriteLine(JsonSerializer.Serialize(new { blocker = stage + "_malformed_json", stage }, json));
    return 2;
}
catch (Exception exception) when (stage == "input"
    && exception is ArgumentException or InvalidOperationException or KeyNotFoundException or UriFormatException)
{
    Console.WriteLine(JsonSerializer.Serialize(new { blocker = "input_invalid", stage }, json));
    return 2;
}
catch (Exception)
{
    Console.WriteLine(JsonSerializer.Serialize(new { blocker = "spike_internal_error", stage }, json));
    return 2;
}
CS
dotnet build /tmp/mcpcli-story-25-spike/Spike.csproj --configuration Debug -m:1
dotnet /tmp/mcpcli-story-25-spike/bin/Debug/net10.0/Spike.dll --validate-only
```

Actual sanitized result: build succeeded with 0 warnings and 0 errors; validate-only exited 0 and reported:

```json
{"client":"3.110.0.0","pin":"3.110.0","candidateMatches":true,"aggregatePattern":"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$","request":{"tenant":"system","domain":"tenants","aggregateId":"index","queryType":"list-tenants","projectionType":"tenant-index","payload":{"PageSize":25}},"submitted":false}
```

## Authorized live run

Both readiness checks exited 0 and reported healthy before submission:

```sh
aspire wait eventstore --apphost /home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants.AppHost/Hexalith.Tenants.AppHost.csproj --timeout 30 --non-interactive
aspire wait tenants --apphost /home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants.AppHost/Hexalith.Tenants.AppHost.csproj --timeout 30 --non-interactive
```

The following Linux launcher reproduces the approved invocation without writing credentials or printing raw Aspire output:

```python
import json
import os
from pathlib import Path
import subprocess

apphost = "/home/administrator/projects/hexalith/tenants/src/Hexalith.Tenants.AppHost/Hexalith.Tenants.AppHost.csproj"
describe = subprocess.run(
    ["aspire", "describe", "--apphost", apphost, "--non-interactive", "--format", "Json"],
    check=True, capture_output=True, text=True, timeout=30,
)
resources = json.loads(describe.stdout)["resources"]
ui = next(resource for resource in resources if resource["displayName"] == "eventstore-admin-ui")
pid = int(ui["properties"]["executable.pid"])
environment = dict(
    entry.decode().split("=", 1)
    for entry in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    if entry and b"=" in entry
)
prefix = "EventStore__Authentication__"
required = ["Username", "Password", "TokenEndpoint"]
if not all(environment.get(prefix + name) for name in required):
    raise SystemExit("Generated credential fields unavailable; no query submitted.")
gateway = next(resource for resource in resources if resource["displayName"] == "eventstore")
gateway_url = next(item["url"] for item in gateway["urls"] if item["url"].startswith("http://"))
settings = {
    "gatewayUrl": gateway_url.rstrip("/") + "/",
    "tokenEndpoint": environment[prefix + "TokenEndpoint"],
    "adminUsername": environment[prefix + "Username"],
    "adminPassword": environment[prefix + "Password"],
}
spike_environment = os.environ.copy()
if environment.get("SSL_CERT_DIR"):
    spike_environment["SSL_CERT_DIR"] = environment["SSL_CERT_DIR"]
spike = subprocess.run(
    ["dotnet", "/tmp/mcpcli-story-25-spike/bin/Debug/net10.0/Spike.dll"],
    input=json.dumps(settings), capture_output=True, text=True,
    env=spike_environment, timeout=45,
)
print("Spike exit:", spike.returncode)
if spike.stdout.strip():
    evidence = json.loads(spike.stdout)
    print(json.dumps(evidence))
    if spike.returncode == 0:
        Path("/tmp/mcpcli-story-25-spike/live-result.json").write_text(json.dumps(evidence, indent=2) + "\n")
if spike.returncode and not spike.stdout.strip():
    print("No sanitized response; inspect the failure without logging credentials.")
raise SystemExit(spike.returncode)
```

The actual harness exited 0 and returned this sanitized page:

```json
{"pin":"3.110.0","endpoint":"http://localhost:8080/api/v1/queries","request":{"tenant":"system","domain":"tenants","aggregateId":"index","queryType":"list-tenants","projectionType":"tenant-index","payload":{"PageSize":25}},"candidateMatches":true,"page":{"items":["[redacted tenant]"],"cursor":null,"hasMore":false}}
```

The harness makes one `SubmitQueryAsync` call, requires an object page with an `items` array, redacts item details and opaque cursor values, and reports numeric/boolean paging metadata when supplied. The Gateway supplied no envelope paging metadata in this run. The returned page proves that `index` is accepted by the running Gateway and Tenants handler in addition to matching the pinned validator pattern; it does not establish an upstream contract declaration.

## Acceptance verification and handoff

```sh
dotnet build tests/Hexalith.McpCli.Core.Tests/Hexalith.McpCli.Core.Tests.csproj --configuration Debug --no-restore -m:1
dotnet build tests/Hexalith.McpCli.Cli.Tests/Hexalith.McpCli.Cli.Tests.csproj --configuration Debug --no-restore -m:1
dotnet tests/Hexalith.McpCli.Core.Tests/bin/Debug/net10.0/Hexalith.McpCli.Core.Tests.dll -class '*QueryExecutionTests'
dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll -class '*QueryCommandTests'
dotnet tests/Hexalith.McpCli.Core.Tests/bin/Debug/net10.0/Hexalith.McpCli.Core.Tests.dll
dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll
git diff --check
```

After review fixes, both builds succeeded with 0 warnings/errors. Focused suites passed 27 Core and 19 CLI cases with 0 failures/skips. Full CLI passed 231/231 with 0 failures/skips. Full Core had 271 cases, 269 passing, 0 failing, and 2 existing Windows-only ACL skips on Linux (`WindowsTemporaryFileHasPrivateAclBeforeTokenBytesAreWritten`, `WindowsProfileFilesHavePrivateAcls`). Windows ACL execution remains an environment-specific limitation; the query acceptance cases all ran. Eleven synthetic failure probes verified sanitized harness errors, including its real authentication timeout; no live query was repeated. `git diff --check` passed.

For Story 4.8, the Tenants maintainer must confirm the list-query aggregate constant `index`, the authoritative transport/projection behavior, and the generated global-administrator requirements. The candidate is syntactically valid at the pinned Gateway version, appears in current Tenants query tests, and succeeded in this live query. Maintainer confirmation and upstream decoration remain work for Story 4.8; no message was sent to the maintainer in this run.

## Sanitized failure verification

Authentication, token parsing, and Gateway submission now share one protected scope. Failures report only a stage, stable blocker code, and HTTP status/reason codes when applicable; credentials, exception messages, response bodies, and stack traces are omitted. Missing, null, numeric, blank, or non-object token responses all produce `authentication_missing_token`. Transport failures, the bounded 30-second timeout, and malformed JSON produce stage-specific blockers. Invalid launcher input is also sanitized.

Executed only synthetic loopback failure probes after this correction; the live query above was not repeated:

```sh
cat > /tmp/mcpcli-story-25-spike/failure-probes.py <<'PY'
import contextlib
import http.server
import json
from pathlib import Path
import socket
import subprocess
import threading
import time

assembly = '/tmp/mcpcli-story-25-spike/bin/Debug/net10.0/Spike.dll'
sentinels = ['synthetic-username-sentinel', 'synthetic-password-sentinel']
results = []

def probe(name, stdin, expected):
    run = subprocess.run(['dotnet', assembly], input=stdin, text=True, capture_output=True, timeout=36)
    assert run.returncode == 2, (name, run.returncode)
    assert run.stderr == '', (name, 'unexpected stderr')
    assert all(value not in run.stdout + run.stderr for value in sentinels), (name, 'credential leak')
    result = json.loads(run.stdout)
    assert result['blocker'] == expected, (name, result)
    results.append({'probe': name, 'exit': run.returncode, 'result': result, 'stderrEmpty': True, 'credentialFree': True})

def input_for(endpoint):
    return json.dumps({'gatewayUrl': 'http://127.0.0.1:1/', 'tokenEndpoint': endpoint,
        'adminUsername': sentinels[0], 'adminPassword': sentinels[1]})

@contextlib.contextmanager
def identity_server(body, status=200, delay=0):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length', '0')))
            time.sleep(delay)
            try:
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port) + '/token'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

probe('malformed-input', '{', 'input_malformed_json')
probe('missing-input-properties', '{}', 'input_invalid')
with socket.socket() as reservation:
    reservation.bind(('127.0.0.1', 0))
    closed_port = reservation.getsockname()[1]
probe('refused-authentication-connection', input_for('http://127.0.0.1:' + str(closed_port) + '/token'), 'authentication_transport_failure')
with identity_server(b'{}', status=401) as endpoint:
    probe('authentication-http-failure', input_for(endpoint), 'administrator_token_request_failed')
with identity_server(b'{') as endpoint:
    probe('malformed-authentication-json', input_for(endpoint), 'authentication_malformed_json')
for name, body in [('absent', b'{}'), ('null', b'{"access_token":null}'), ('numeric', b'{"access_token":7}'),
                   ('blank', b'{"access_token":" "}'), ('array-root', b'[]')]:
    with identity_server(body) as endpoint:
        probe('missing-token-' + name, input_for(endpoint), 'authentication_missing_token')
with identity_server(b'{}', delay=35) as endpoint:
    probe('authentication-timeout', input_for(endpoint), 'authentication_timeout')
Path('/tmp/mcpcli-story-25-spike/failure-probes.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({'passed': len(results), 'failed': 0, 'results': '/tmp/mcpcli-story-25-spike/failure-probes.json'}))
PY
dotnet build /tmp/mcpcli-story-25-spike/Spike.csproj --configuration Debug --no-restore -m:1
python3 /tmp/mcpcli-story-25-spike/failure-probes.py
dotnet tests/Hexalith.McpCli.Cli.Tests/bin/Debug/net10.0/Hexalith.McpCli.Cli.Tests.dll -class '*QueryCommandTests'
```

The harness build succeeded with 0 warnings/errors. All 11 probes passed: malformed input, missing input properties, refused authentication connection, HTTP 401, malformed authentication JSON, five missing/invalid token representations, and authentication timeout. Every probe exited 2 with a single valid JSON blocker, empty stderr, and no synthetic credential sentinels in output. Sanitized results are saved at `/tmp/mcpcli-story-25-spike/failure-probes.json`.

The corrected focused CLI class passed **19/19**, with 0 failures/skips; output is saved at `/tmp/mcpcli-story-25-spike/query-command-tests.log`. It now includes a profile-only tenant invocation and verifies the exact synthetic Bearer header on every request. Listener setup and task failures cannot skip directory cleanup, and task draining preserves an existing test failure. `git diff --check` passed.

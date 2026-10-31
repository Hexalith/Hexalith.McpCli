using System.Diagnostics;
using System.Net;
using System.Net.Http.Json;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Exercises actual package gateway sockets and cryptographic rejection boundaries.</summary>
public sealed class PackageGatewayBoundaryTests : IAsyncLifetime
{
    private readonly RSA _proofKey = RSA.Create(2048);
    private readonly string _signingKey = Convert.ToBase64String(RandomNumberGenerator.GetBytes(32));
    private readonly string _channelToken = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
    private bool _disposed;
    private Process? _process;
    private HttpClient? _http;
    private Task<string>? _stdout;
    private Task<string>? _stderr;
    private HttpListener? _unavailableDapr;
    private readonly CancellationTokenSource _unavailableDaprStop = new();
    private Task? _unavailableDaprPump;

    /// <inheritdoc/>
    public async ValueTask InitializeAsync()
    {
        try { await StartGatewayAsync(); }
        catch
        {
            await DisposeAsync();
            throw;
        }
    }

    private async Task StartGatewayAsync()
    {
        string root = DependencyPolicyTests.FindRepositoryRoot();
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string directory = Path.Combine(root, "tests", "Hexalith.McpCli.EventStoreGateway.TestHost", "bin", configuration, "net10.0");
        string assembly = Path.Combine(directory, "Hexalith.McpCli.EventStoreGateway.TestHost.dll");
        Assert.True(File.Exists(assembly), "Build the owned package gateway host before its boundary tests.");
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        var start = new ProcessStartInfo("dotnet", assembly)
        {
            WorkingDirectory = directory, RedirectStandardOutput = true, RedirectStandardError = true,
        };
        start.Environment["ASPNETCORE_URLS"] = $"http://127.0.0.1:{port}";
        start.Environment["ASPNETCORE_ENVIRONMENT"] = "Development";
        start.Environment["DOTNET_ENVIRONMENT"] = "Development";
        start.Environment["ASPNETCORE_CONTENTROOT"] = directory;
        // Negative HTTP boundaries need no successful Dapr state. An owned
        // rejecting endpoint prevents access to a user's runtime; actual gateway
        // metadata failure handling remains active and no index is fabricated.
        using var reservation = new TcpListener(IPAddress.Loopback, 0);
        reservation.Start();
        int daprPort = ((IPEndPoint)reservation.LocalEndpoint).Port;
        reservation.Stop();
        string inertDapr = $"http://127.0.0.1:{daprPort}";
        _unavailableDapr = new HttpListener();
        _unavailableDapr.Prefixes.Add(inertDapr + "/");
        _unavailableDapr.Start();
        _unavailableDaprPump = RejectUnavailableMetadataAsync();
        start.Environment["DAPR_HTTP_ENDPOINT"] = inertDapr;
        start.Environment["DAPR_GRPC_ENDPOINT"] = inertDapr;
        start.Environment["APP_API_TOKEN"] = _channelToken;
        start.Environment["Authentication__JwtBearer__Authority"] = "";
        start.Environment["Authentication__JwtBearer__SigningKey"] = _signingKey;
        start.Environment["Authentication__JwtBearer__Issuer"] = "mcpcli-boundary-tests";
        start.Environment["Authentication__JwtBearer__Audience"] = "hexalith-eventstore";
        start.Environment["Authentication__JwtBearer__AllowedAlgorithms__0"] = "HS256";
        start.Environment["Authentication__JwtBearer__RequireHttpsMetadata"] = "false";
        start.Environment["Authentication__DaprInternal__Audience"] = "eventstore";
        start.Environment["Authentication__DaprInternal__AllowedCallers__0"] = "tenants";
        start.Environment["Authentication__BoundStreamRead__PublicKeys__tenants"] = Convert.ToBase64String(_proofKey.ExportSubjectPublicKeyInfo());
        start.Environment["Authentication__BoundStreamRead__AllowedDomains__tenants"] = "tenants,global-administrators";
        start.Environment["Testing__BodyLimitProbe"] = "true";
        _process = Process.Start(start)!;
        _stdout = _process.StandardOutput.ReadToEndAsync();
        _stderr = _process.StandardError.ReadToEndAsync();
        _http = new HttpClient { BaseAddress = new Uri($"http://127.0.0.1:{port}"), Timeout = TimeSpan.FromSeconds(5) };
        using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(20));
        while (!deadline.IsCancellationRequested)
        {
            if (_process.HasExited)
            {
                string diagnostic = ((await _stdout) + (await _stderr))
                    .Replace(_signingKey, "[REDACTED]", StringComparison.Ordinal)
                    .Replace(_channelToken, "[REDACTED]", StringComparison.Ordinal)
                    .Replace(Convert.ToBase64String(_proofKey.ExportPkcs8PrivateKey()), "[REDACTED]", StringComparison.Ordinal);
                throw new InvalidOperationException("The actual package gateway process exited before readiness: " + diagnostic[^Math.Min(5000, diagnostic.Length)..]);
            }
            try
            {
                using HttpResponseMessage response = await _http.GetAsync("alive", deadline.Token);
                if (response.StatusCode == HttpStatusCode.OK) return;
            }
            catch (HttpRequestException) { }
            await Task.Delay(100, deadline.Token);
        }
        throw new TimeoutException("The package gateway did not start within the bounded deadline.");
    }

    /// <summary>The required package defaults retain their reviewed native source and match the launched bytes.</summary>
    [Fact]
    public void PackageConfigurationRetainsReviewedSourceAndDeployedHashes()
    {
        string host = Path.Combine(DependencyPolicyTests.FindRepositoryRoot(), "tests", "Hexalith.McpCli.EventStoreGateway.TestHost");
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(Path.Combine(host, "Configuration", "provenance.json")));
        JsonElement profile = document.RootElement;
        Assert.Equal("published", profile.GetProperty("profile").GetString());
        Assert.Equal("3.128.4", profile.GetProperty("eventStoreVersion").GetString());
        Assert.Equal("https://github.com/Hexalith/Hexalith.EventStore.git", profile.GetProperty("sourceRepository").GetString());
        Assert.Equal("ab39879c06eea69668916941ce46a2b6d7e8efd9", profile.GetProperty("sourceCommit").GetString());
        foreach (JsonProperty file in profile.GetProperty("files").EnumerateObject())
        {
            string path = Path.Combine(host, file.Name);
            string hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
            Assert.Equal(file.Value.GetProperty("sha256").GetString(), hash);
        }
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        Assert.Equal(File.ReadAllBytes(Path.Combine(host, "Configuration", "appsettings.gateway.json")),
            File.ReadAllBytes(Path.Combine(host, "bin", configuration, "net10.0", "appsettings.gateway.json")));
    }

    /// <summary>Requests at the configured limit succeed; Kestrel rejects a larger body without an endpoint size attribute.</summary>
    [Theory]
    [InlineData(1_048_576, HttpStatusCode.OK)]
    [InlineData(1_048_577, HttpStatusCode.RequestEntityTooLarge)]
    public async Task ActualKestrelEnforcesOneMiB(int bytes, HttpStatusCode expected)
    {
        using var content = new ByteArrayContent(new byte[bytes]);
        using HttpResponseMessage response = await _http!.PostAsync("testing/body-limit", content, TestContext.Current.CancellationToken);
        Assert.Equal(expected, response.StatusCode);
    }

    /// <summary>Cryptographically admitted workload requests still require the exact independent signing proof and domain grant.</summary>
    [Theory]
    [InlineData("absent-proof")]
    [InlineData("wrong-key")]
    [InlineData("mismatched-caller")]
    [InlineData("outside-domain")]
    public async Task ActualStreamBoundaryRejectsInvalidAuthority(string defect)
    {
        using HttpRequestMessage request = CreateStreamRequest(defect);
        using HttpResponseMessage response = await _http!.SendAsync(request, TestContext.Current.CancellationToken);
        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
    }

    /// <summary>A valid proof reaches unavailable private infrastructure, proving the denied probes passed authentication.</summary>
    [Fact]
    public async Task ActualStreamBoundaryAdmitsValidAuthorityBeforeStateAccess()
    {
        using HttpRequestMessage request = CreateStreamRequest("valid");
        using HttpResponseMessage response = await _http!.SendAsync(request, TestContext.Current.CancellationToken);
        Assert.Equal(HttpStatusCode.InternalServerError, response.StatusCode);
        string body = await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken);
        Assert.Contains("Stream replay failed.", body, StringComparison.Ordinal);
    }

    private HttpRequestMessage CreateStreamRequest(string defect)
    {
        long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        string domain = defect == "outside-domain" ? "party" : "tenants";
        string header = Encode(JsonSerializer.SerializeToUtf8Bytes(new { alg = "HS256", typ = "JWT" }));
        string payload = Encode(JsonSerializer.SerializeToUtf8Bytes(new Dictionary<string, object>
        {
            ["iss"] = "mcpcli-boundary-tests", ["aud"] = "eventstore", ["azp"] = "tenants",
            ["eventstore:operation"] = "eventstore:stream-read", ["iat"] = now, ["nbf"] = now - 5,
            ["exp"] = now + 60, ["jti"] = Guid.NewGuid().ToString("N"),
        }));
        string unsigned = header + "." + payload;
        string assertion = unsigned + "." + Encode(HMACSHA256.HashData(Encoding.UTF8.GetBytes(_signingKey), Encoding.ASCII.GetBytes(unsigned)));
        var request = new HttpRequestMessage(HttpMethod.Post, "api/v1/streams/read/workload")
        {
            Content = JsonContent.Create(new { tenant = "system", domain, aggregateId = "tenant-a" }),
        };
        request.Headers.Add("dapr-api-token", _channelToken);
        request.Headers.Add("X-Hexalith-Workload-Assertion", assertion);
        if (defect != "absent-proof")
        {
            string proofPayload = Encode(JsonSerializer.SerializeToUtf8Bytes(new
            {
                version = 1, caller = defect == "mismatched-caller" ? "other-owner" : "tenants",
                tenant = "system", domain, aggregateId = "tenant-a", issuedAt = now, expiresAt = now + 30,
                nonce = Convert.ToHexString(RandomNumberGenerator.GetBytes(16)),
            }));
            using RSA wrongKey = RSA.Create(2048);
            RSA signer = defect == "wrong-key" ? wrongKey : _proofKey;
            string proof = proofPayload + "." + Encode(signer.SignData(Encoding.ASCII.GetBytes(proofPayload), HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1));
            request.Headers.Add("X-Hexalith-Bound-Stream-Read-Proof", proof);
        }
        return request;
    }

    /// <inheritdoc/>
    public async ValueTask DisposeAsync()
    {
        if (_disposed) return;
        _disposed = true;
        _http?.Dispose();
        _proofKey.Dispose();
        _unavailableDaprStop.Cancel();
        _unavailableDapr?.Close();
        if (_unavailableDaprPump is not null) await _unavailableDaprPump;
        _unavailableDaprStop.Dispose();
        if (_process is not null)
        {
            if (!_process.HasExited) _process.Kill(entireProcessTree: true);
            await _process.WaitForExitAsync();
            if (_stdout is not null) _ = await _stdout;
            if (_stderr is not null) _ = await _stderr;
            _process.Dispose();
        }
    }

    private static string Encode(byte[] value) => Convert.ToBase64String(value).TrimEnd('=').Replace('+', '-').Replace('/', '_');

    private async Task RejectUnavailableMetadataAsync()
    {
        try
        {
            while (!_unavailableDaprStop.IsCancellationRequested)
            {
                HttpListenerContext context = await _unavailableDapr!.GetContextAsync().WaitAsync(_unavailableDaprStop.Token);
                // Reject every infrastructure request. No metadata, catalog, actor state or successful
                // authority response is fabricated for these pre-state rejection checks.
                context.Response.StatusCode = 403;
                context.Response.ContentLength64 = 0;
                context.Response.Close();
            }
        }
        catch (OperationCanceledException) when (_unavailableDaprStop.IsCancellationRequested) { }
        catch (HttpListenerException) when (_unavailableDaprStop.IsCancellationRequested) { }
        catch (ObjectDisposedException) when (_unavailableDaprStop.IsCancellationRequested) { }
    }
}

using System.Diagnostics;
using System.Net;
using System.Security.Cryptography;
using System.Text.Json;

using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects the fresh-store maintenance boundary and single activation submission.</summary>
public sealed class ProjectionWriterBootstrapTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "mcpcli-writer-" + Guid.NewGuid().ToString("N"));
    private readonly string? _previousIsolation = Environment.GetEnvironmentVariable("MCPCLI_ISOLATED_TOPOLOGY");
    private readonly string? _previousOutput = Environment.GetEnvironmentVariable("MCPCLI_LIVE_OUTPUT");

    /// <summary>Creates only test-owned backup and output paths.</summary>
    public ProjectionWriterBootstrapTests()
    {
        Directory.CreateDirectory(_root);
        Environment.SetEnvironmentVariable("MCPCLI_ISOLATED_TOPOLOGY", "1");
        Environment.SetEnvironmentVariable("MCPCLI_LIVE_OUTPUT", _root);
    }

    /// <summary>A provider-native empty backup binds the marker activation to exact retained bytes.</summary>
    [Fact]
    public async Task ActivationIsSubmittedOnceAndReadinessOnlyPolls()
    {
        string receipt = Backup();
        int posts = 0, reads = 0;
        using var handler = new ProjectionWriterBootstrapHandler(async request =>
        {
            if (request.Method == HttpMethod.Post)
            {
                posts++;
                Assert.Equal("/api/v1/admin/projections/delivery-writer-protocol/activate", request.RequestUri!.AbsolutePath);
                using JsonDocument body = JsonDocument.Parse(await request.Content!.ReadAsStringAsync().ConfigureAwait(false));
                Assert.Equal(new string('a', 40), body.RootElement.GetProperty("cutoverCommit").GetString());
                Assert.Equal(ProjectionWriterBootstrap.VerifyBackup(receipt), body.RootElement.GetProperty("backupReference").GetString());
                foreach (string flag in new[] { "writersQuiesced", "retryWorkersQuiesced", "downgradeProhibitedAcknowledged" })
                    Assert.True(body.RootElement.GetProperty(flag).GetBoolean());
                return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{\"status\":\"Activated\"}") };
            }
            Assert.Equal(HttpMethod.Get, request.Method);
            Assert.Equal("/ready", request.RequestUri!.AbsolutePath);
            return new HttpResponseMessage(++reads == 1 ? HttpStatusCode.ServiceUnavailable : HttpStatusCode.OK);
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/") };
        await ProjectionWriterBootstrap.ActivateAsync(http, receipt, new string('a', 40), TestContext.Current.CancellationToken);
        Assert.Equal(1, posts);
        Assert.Equal(2, reads);
        using JsonDocument result = JsonDocument.Parse(File.ReadAllText(Path.Combine(_root, "writer-bootstrap.json")));
        Assert.Equal("passed", result.RootElement.GetProperty("result").GetString());
        Assert.Equal(1, result.RootElement.GetProperty("activationCount").GetInt32());
        Assert.True(result.RootElement.GetProperty("readinessObserved").GetBoolean());
    }

    /// <summary>Invalid provenance never reaches the privileged endpoint.</summary>
    [Theory]
    [InlineData("isolation")]
    [InlineData("source")]
    [InlineData("uppercase-source")]
    [InlineData("missing-output")]
    [InlineData("header")]
    [InlineData("location")]
    [InlineData("nonempty")]
    [InlineData("after-applications")]
    [InlineData("hash")]
    public async Task UnsafeInputsFailBeforeMaintenance(string defect)
    {
        string receipt = Backup(defect == "nonempty" ? 1 : 0, defect != "after-applications");
        if (defect == "hash") File.AppendAllText(Path.Combine(_root, "initial-empty.rdb"), "changed");
        if (defect == "isolation") Environment.SetEnvironmentVariable("MCPCLI_ISOLATED_TOPOLOGY", "0");
        if (defect == "missing-output") Environment.SetEnvironmentVariable("MCPCLI_LIVE_OUTPUT", null);
        if (defect is "header" or "location")
        {
            string backup = Path.Combine(_root, "initial-empty.rdb");
            if (defect == "header") File.WriteAllText(backup, "INVALID0012empty-test-state");
            if (defect == "location")
            {
                string other = Path.Combine(_root, "other");
                Directory.CreateDirectory(other);
                string moved = Path.Combine(other, "initial-empty.rdb");
                File.Move(backup, moved);
                backup = moved;
            }
            File.WriteAllText(receipt, JsonSerializer.Serialize(new { databaseSize = 0, createdBeforeApplications = true,
                backupFile = backup, sha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(backup))) }));
        }
        int calls = 0;
        using var handler = new ProjectionWriterBootstrapHandler(_ =>
        {
            calls++;
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK));
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/") };
        await Assert.ThrowsAsync<InvalidOperationException>(() => ProjectionWriterBootstrap.ActivateAsync(http, receipt,
            defect == "source" ? new string('a', 39) : defect == "uppercase-source" ? new string('A', 40) : new string('a', 40), TestContext.Current.CancellationToken));
        Assert.Equal(0, calls);
        Assert.False(File.Exists(Path.Combine(_root, "writer-bootstrap.json")));
    }

    /// <summary>A rejected maintenance call is a failure and is never resubmitted for convergence.</summary>
    [Fact]
    public async Task RejectedActivationFailsWithoutRetryOrSuccessReceipt()
    {
        int calls = 0;
        using var handler = new ProjectionWriterBootstrapHandler(_ =>
        {
            calls++;
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.Conflict));
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/") };
        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ProjectionWriterBootstrap.ActivateAsync(http, Backup(), new string('a', 40), TestContext.Current.CancellationToken));
        Assert.Equal("Private projection writer activation failed with HTTP 409.", failure.Message);
        Assert.Equal(1, calls);
        Assert.False(File.Exists(Path.Combine(_root, "writer-bootstrap.json")));
    }

    /// <summary>A successful HTTP response still requires the actual activation receipt before readiness can grant success.</summary>
    [Fact]
    public async Task MissingActivatedReceiptFailsWithoutReadinessOrRetry()
    {
        int calls = 0;
        using var handler = new ProjectionWriterBootstrapHandler(request =>
        {
            calls++;
            Assert.Equal(HttpMethod.Post, request.Method);
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{\"status\":\"Pending\"}") });
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/") };
        InvalidOperationException failure = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            ProjectionWriterBootstrap.ActivateAsync(http, Backup(), new string('a', 40), TestContext.Current.CancellationToken));
        Assert.Equal("Private projection writer activation returned no Activated receipt.", failure.Message);
        Assert.Equal(1, calls);
        Assert.False(File.Exists(Path.Combine(_root, "writer-bootstrap.json")));
    }

    /// <summary>Persistent unreadiness fails at the real 30-second deadline without reactivating or recording success.</summary>
    [Fact]
    public async Task PersistentUnreadinessFailsAtBootstrapDeadlineWithoutSuccessReceipt()
    {
        int posts = 0, reads = 0;
        using var handler = new ProjectionWriterBootstrapHandler(request =>
        {
            if (request.Method == HttpMethod.Post)
            {
                posts++;
                return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{\"status\":\"Activated\"}") });
            }
            Assert.Equal(HttpMethod.Get, request.Method);
            Assert.Equal("/ready", request.RequestUri!.AbsolutePath);
            reads++;
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.ServiceUnavailable));
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/"), Timeout = TimeSpan.FromSeconds(40) };
        var elapsed = Stopwatch.StartNew();
        OperationCanceledException failure = await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>
            ProjectionWriterBootstrap.ActivateAsync(http, Backup(), new string('a', 40), TestContext.Current.CancellationToken)
                .WaitAsync(TimeSpan.FromSeconds(35), TestContext.Current.CancellationToken));
        Assert.True(failure.CancellationToken.IsCancellationRequested);
        Assert.InRange(elapsed.Elapsed, TimeSpan.FromSeconds(29), TimeSpan.FromSeconds(35));
        Assert.Equal(1, posts);
        Assert.True(reads > 1);
        Assert.False(File.Exists(Path.Combine(_root, "writer-bootstrap.json")));
    }

    /// <summary>Caller cancellation stops readiness polling promptly and cannot publish a success receipt.</summary>
    [Fact]
    public async Task CallerCancellationStopsReadinessWithoutReactivationOrSuccessReceipt()
    {
        int posts = 0, reads = 0;
        var observed = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        using var handler = new ProjectionWriterBootstrapHandler(request =>
        {
            if (request.Method == HttpMethod.Post)
            {
                posts++;
                return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{\"status\":\"Activated\"}") });
            }
            Assert.Equal(HttpMethod.Get, request.Method);
            Assert.Equal("/ready", request.RequestUri!.AbsolutePath);
            reads++;
            observed.TrySetResult();
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.ServiceUnavailable));
        });
        using var http = new HttpClient(handler) { BaseAddress = new Uri("http://127.0.0.1:1234/") };
        using var caller = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        Task pending = ProjectionWriterBootstrap.ActivateAsync(http, Backup(), new string('a', 40), caller.Token);
        await observed.Task.WaitAsync(TimeSpan.FromSeconds(5), TestContext.Current.CancellationToken);
        var elapsed = Stopwatch.StartNew();
        caller.Cancel();
        OperationCanceledException failure = await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>
            pending.WaitAsync(TimeSpan.FromSeconds(5), TestContext.Current.CancellationToken));
        Assert.True(failure.CancellationToken.IsCancellationRequested);
        Assert.True(elapsed.Elapsed < TimeSpan.FromSeconds(5));
        Assert.Equal(1, posts);
        Assert.True(reads >= 1);
        Assert.False(File.Exists(Path.Combine(_root, "writer-bootstrap.json")));
    }

    private string Backup(int databaseSize = 0, bool beforeApplications = true)
    {
        string backup = Path.Combine(_root, "initial-empty.rdb");
        byte[] bytes = "REDIS0012empty-test-state"u8.ToArray();
        File.WriteAllBytes(backup, bytes);
        string receipt = Path.Combine(_root, "initial-redis-backup.json");
        File.WriteAllText(receipt, JsonSerializer.Serialize(new { databaseSize, createdBeforeApplications = beforeApplications,
            backupFile = backup, sha256 = Convert.ToHexStringLower(SHA256.HashData(bytes)) }));
        return receipt;
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        Environment.SetEnvironmentVariable("MCPCLI_ISOLATED_TOPOLOGY", _previousIsolation);
        Environment.SetEnvironmentVariable("MCPCLI_LIVE_OUTPUT", _previousOutput);
        Directory.Delete(_root, recursive: true);
    }
}

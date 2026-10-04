using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Settings;
using Shouldly;
using StringContracts = global::Catalog.String.Contracts;
using SampleContracts = Hexalith.McpCli.Sample.Contracts;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Exercises CLI failures through the pinned HTTP client and result-file writer.</summary>
public sealed class ExecutionFailureCommandTests
{
    private const string Id = "01J9MZHXT3RKM0VWXRXGSJDATK";

    /// <summary>Problem Details status and supplied metadata survive one command submission.</summary>
    [Fact]
    public async Task CompleteProblemDetailsKeepsExceptionStatusAsync()
    {
        const string body = """
            {"status":422,"title":"Conflict","detail":"The item already exists.","reasonCode":"duplicate-item",
             "code":"fallback","reason":"legacy","retryable":false,"clientAction":"inspect",
             "retryAfter":"25","correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK"}
            """;
        (int exit, string output, int calls) = await InvokeGatewayAsync(true, 409, body);
        exit.ShouldBe(2, output);
        AssertJson(output,
            $$$"""{"error":{"code":"gateway_error","status":422,"detail":"The item already exists.","reason":"duplicate-item","retryable":false,"clientAction":"inspect","retryAfter":"25","correlationId":"{{{Id}}}"}}""");
        calls.ShouldBe(1);
    }

    /// <summary>Blank or absent Problem Details retain only status and the client title fallback.</summary>
    [Theory]
    [InlineData("{}")]
    [InlineData("{\"title\":\" \",\"detail\":\" \",\"reasonCode\":\" \",\"code\":\" \",\"reason\":\" \",\"clientAction\":\" \",\"correlationId\":\"bad-id\"}")]
    public async Task BlankProblemDetailsOmitsMetadataAsync(string body)
    {
        (int exit, string output, int calls) = await InvokeGatewayAsync(false, 409, body);
        exit.ShouldBe(2, output);
        string detail = body == "{}" ? "Conflict" : "Gateway request failed.";
        AssertJson(output, "{\"error\":{\"code\":\"gateway_error\",\"status\":409,\"detail\":\"" + detail + "\"}}");
        calls.ShouldBe(1);
    }

    /// <summary>Malformed successful responses and semantic query failure retain 2xx client statuses.</summary>
    [Theory]
    [InlineData(true, 202, "{", 202, "Command response body could not be parsed.", false)]
    [InlineData(false, 200, "{", 200, "Query response body could not be parsed.", false)]
    [InlineData(false, 200, "{\"correlationId\":\"01J9MZHXT3RKM0VWXRXGSJDATK\",\"success\":false,\"errorMessage\":\"Access denied.\"}", 200, "Access denied.", true)]
    public async Task SuccessfulHttpFailureHasNoResultAsync(bool command, int httpStatus, string body,
        int expectedStatus, string detail, bool correlation)
    {
        (int exit, string output, int calls) = await InvokeGatewayAsync(command, httpStatus, body);
        exit.ShouldBe(2, output);
        string expected = "{\"error\":{\"code\":\"gateway_error\",\"status\":" + expectedStatus
            + ",\"detail\":" + JsonSerializer.Serialize(detail)
            + (correlation ? ",\"correlationId\":\"" + Id + "\"" : "") + "}}";
        AssertJson(output, expected);
        calls.ShouldBe(1);
    }

    /// <summary>A missing @file is an action failure with a safe message, stdout error, and unchanged result file.</summary>
    [Fact]
    public async Task MissingPayloadFileHidesPathAndKeepsResultAsync()
    {
        string directory = NewDirectory();
        try
        {
            string result = Path.Combine(directory, "result.json");
            await File.WriteAllTextAsync(result, "old result", TestContext.Current.CancellationToken);
            string missing = Path.Combine(directory, "secret-token-file.json");
            (int exit, string output, _) = await InvokeCliAsync(
                ["query", "string-fixture.list-items", "--payload", "@" + missing, "--output", result], directory);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"internal_error","message":"The CLI action failed."}}""");
            output.ShouldNotContain(missing);
            (await File.ReadAllTextAsync(result, TestContext.Current.CancellationToken)).ShouldBe("old result");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Table plus output still routes a real failure as one stdout error without changing the file.</summary>
    [Fact]
    public async Task TableAndOutputFailureLeavesExistingFileAsync()
    {
        string directory = NewDirectory();
        try
        {
            string result = Path.Combine(directory, "result.json");
            await File.WriteAllTextAsync(result, "old result", TestContext.Current.CancellationToken);
            (int exit, string output, _) = await InvokeCliAsync(
                ["query", "string-fixture.list-items", "--payload", "{", "--format", "table", "--output", result,
                    "--url", "http://127.0.0.1:1/"], directory);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"validation_failed","operation":"string-fixture.list-items","violations":[{"path":"/","message":"The payload must be valid JSON without duplicate properties."}]}}""");
            (await File.ReadAllTextAsync(result, TestContext.Current.CancellationToken)).ShouldBe("old result");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A real table output write failure emits only a safe stdout error.</summary>
    [Fact]
    public async Task TableOutputWriteFailureUsesInternalErrorAsync()
    {
        string directory = NewDirectory();
        string targetDirectory = Path.Combine(directory, "result-directory");
        Directory.CreateDirectory(targetDirectory);
        try
        {
            (int exit, string output, _) = await InvokeCliAsync(
                ["modules", "--format", "table", "--output", targetDirectory], directory);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"internal_error","message":"The CLI action failed."}}""");
            Directory.Exists(targetDirectory).ShouldBeTrue();
            Directory.GetFiles(directory, ".mcpcli-*").ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A profile management read failure omits the profile path.</summary>
    [Fact]
    public async Task ProfileActionIoUsesSafeMessageAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }

        string directory = NewDirectory();
        string profile = Path.Combine(directory, "mcpcli.json");
        try
        {
            await File.WriteAllTextAsync(profile, "secret-token-path", TestContext.Current.CancellationToken);
            File.SetUnixFileMode(profile, UnixFileMode.None);
            (int exit, string output, _) = await InvokeCliAsync(["config", "profile", "list"], directory);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"internal_error","message":"The CLI action failed."}}""");
            output.ShouldNotContain(profile);
        }
        finally
        {
            File.SetUnixFileMode(profile, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>All public error variants remain JSON on stdout in table mode with an output path.</summary>
    [Theory]
    [InlineData("validation_failed")]
    [InlineData("gateway_error")]
    [InlineData("unknown_operation")]
    [InlineData("unknown_module")]
    [InlineData("invalid_arguments")]
    [InlineData("read_only")]
    [InlineData("catalog_empty")]
    [InlineData("catalog_invalid")]
    [InlineData("unsupported_transport")]
    [InlineData("configuration_invalid")]
    [InlineData("internal_error")]
    public async Task CliOutputErrorsNeverReplaceResultAsync(string code)
    {
        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(path, "old result", TestContext.Current.CancellationToken);
            OperationError error = code switch
            {
                "validation_failed" => new(code, Operation: "sample.get", Violations: [new("/", "Invalid payload.")]),
                "gateway_error" => new(code, Status: 200, Detail: "Malformed success."),
                "unknown_operation" => new(code, Operation: "sample.gte", Suggestions: ["sample.get"]),
                "unknown_module" => new(code, Module: "sampl", Suggestions: []),
                "invalid_arguments" => new(code, Argument: "payload", Message: "Payload is required."),
                _ => new(code, Message: "Stable failure."),
            };
            TextWriter original = Console.Out;
            using var output = new StringWriter();
            try
            {
                Console.SetOut(output);
                int exit = await CliOutput.WriteAsync(null, error, Settings(path, "table"), TestContext.Current.CancellationToken);
                exit.ShouldBe(2);
            }
            finally
            {
                Console.SetOut(original);
            }

            using JsonDocument json = JsonDocument.Parse(output.ToString());
            json.RootElement.EnumerateObject().Select(item => item.Name).ShouldBe(["error"]);
            json.RootElement.GetProperty("error").GetProperty("code").GetString().ShouldBe(code);
            (await File.ReadAllTextAsync(path, TestContext.Current.CancellationToken)).ShouldBe("old result");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A post-truncation fault restores bytes, mode, link identity, and removes temporary files.</summary>
    [Fact]
    public async Task PostTruncationFailureRestoresExistingTargetAsync()
    {
        string directory = NewDirectory();
        string target = Path.Combine(directory, "target.json");
        string link = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(target, "old result", TestContext.Current.CancellationToken);
            if (!OperatingSystem.IsWindows())
            {
                File.SetUnixFileMode(target, UnixFileMode.UserRead | UnixFileMode.UserWrite);
                File.CreateSymbolicLink(link, target);
            }
            else
            {
                link = target;
            }

            byte[]? acl = TrySetAcl(target);
            UnixFileMode? beforeMode = OperatingSystem.IsWindows() ? null : File.GetUnixFileMode(target);
            byte[] before = await File.ReadAllBytesAsync(target, TestContext.Current.CancellationToken);
            string[] tempBefore = Directory.GetFiles(Path.GetTempPath(), ".mcpcli-*");
            Func<CancellationToken, Task> fault = _ => throw new IOException("secret after truncation");

            await Should.ThrowAsync<IOException>(() => CliOutput.WriteAsync(new { updated = true }, null,
                Settings(link), TestContext.Current.CancellationToken, afterDestinationTruncated: fault));

            (await File.ReadAllBytesAsync(target, TestContext.Current.CancellationToken)).ShouldBe(before);
            if (!OperatingSystem.IsWindows())
            {
                File.GetUnixFileMode(target).ShouldBe(beforeMode!.Value);
                File.ResolveLinkTarget(link, returnFinalTarget: false).ShouldNotBeNull().FullName.ShouldBe(target);
            }

            if (acl is not null)
            {
                ReadAcl(target).ShouldBe(acl);
            }

            Directory.GetFiles(Path.GetTempPath(), ".mcpcli-*").Except(tempBefore).ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Readable writable existing files keep mode and symbolic-link target on successful output.</summary>
    [Fact]
    public async Task ExistingResultPreservesModeAclAndLinkAsync()
    {
        string directory = NewDirectory();
        string target = Path.Combine(directory, "target.json");
        string link = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(target, "old result", TestContext.Current.CancellationToken);
            if (!OperatingSystem.IsWindows())
            {
                File.SetUnixFileMode(target, UnixFileMode.UserRead | UnixFileMode.UserWrite);
                File.CreateSymbolicLink(link, target);
            }
            else
            {
                link = target;
            }

            byte[]? acl = TrySetAcl(target);
            UnixFileMode? beforeMode = OperatingSystem.IsWindows() ? null : File.GetUnixFileMode(target);
            int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(link), TestContext.Current.CancellationToken);
            exit.ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(target, TestContext.Current.CancellationToken), """{"updated":true}""");
            if (!OperatingSystem.IsWindows())
            {
                File.GetUnixFileMode(target).ShouldBe(beforeMode!.Value);
                File.ResolveLinkTarget(link, returnFinalTarget: false).ShouldNotBeNull().FullName.ShouldBe(target);
            }

            if (acl is not null)
            {
                ReadAcl(target).ShouldBe(acl);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A dangling output link creates its target while retaining the link itself.</summary>
    [Fact]
    public async Task DanglingResultLinkCreatesTargetAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }

        string directory = NewDirectory();
        string target = Path.Combine(directory, "new-target.json");
        string link = Path.Combine(directory, "result.json");
        try
        {
            File.CreateSymbolicLink(link, target);
            File.Exists(target).ShouldBeFalse();

            int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(link), TestContext.Current.CancellationToken);

            exit.ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(target, TestContext.Current.CancellationToken), """{"updated":true}""");
            File.ResolveLinkTarget(link, returnFinalTarget: false).ShouldNotBeNull().FullName.ShouldBe(target);
            File.GetUnixFileMode(target).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A new result is privately staged and keeps mode 0600 after publication on Unix.</summary>
    [Fact]
    public async Task NewResultHasPrivateModeAsync()
    {
        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.json");
        try
        {
            int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(path), TestContext.Current.CancellationToken);

            exit.ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(path, TestContext.Current.CancellationToken), """{"updated":true}""");
            if (!OperatingSystem.IsWindows())
            {
                File.GetUnixFileMode(path).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>An existing file remains writable while a cooperating reader holds it open.</summary>
    [Fact]
    public async Task ExistingResultAllowsCooperatingReaderAsync()
    {
        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(path, "old result", TestContext.Current.CancellationToken);
            using (FileStream reader = new(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            {
                int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(path), TestContext.Current.CancellationToken);
                exit.ShouldBe(0);
            }

            AssertJson(await File.ReadAllTextAsync(path, TestContext.Current.CancellationToken), """{"updated":true}""");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A FIFO is refused before backup and cannot hold the result writer open.</summary>
    [Fact]
    public async Task NonSeekableResultTargetIsRefusedAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            return;
        }

        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.fifo");
        try
        {
            Mkfifo(path, 0x180).ShouldBe(0);
            await Should.ThrowAsync<IOException>(() => CliOutput.WriteAsync(new { updated = true }, null,
                Settings(path), TestContext.Current.CancellationToken).WaitAsync(TimeSpan.FromSeconds(3),
                    TestContext.Current.CancellationToken));
            File.GetUnixFileMode(path).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>ACL setup errors other than unsupported-filesystem errors fail the test.</summary>
    [Fact]
    public void UnexpectedAclSetupErrorIsNotIgnored()
    {
        if (!OperatingSystem.IsLinux())
        {
            return;
        }

        string missing = Path.Combine(Path.GetTempPath(), "missing-acl-" + Guid.NewGuid().ToString("N"));
        Should.Throw<IOException>(() => TrySetAcl(missing));
    }

    /// <summary>A write-only destination is refused before mutation because its bytes cannot be backed up.</summary>
    [Fact]
    public async Task WriteOnlyExistingResultIsSafelyRefusedAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }
        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(path, "old result", TestContext.Current.CancellationToken);
            File.SetUnixFileMode(path, UnixFileMode.UserWrite);
            await Should.ThrowAsync<UnauthorizedAccessException>(() => CliOutput.WriteAsync(new { updated = true }, null,
                Settings(path), TestContext.Current.CancellationToken));
            File.SetUnixFileMode(path, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            (await File.ReadAllTextAsync(path, TestContext.Current.CancellationToken)).ShouldBe("old result");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A real CLI call cannot overwrite a read-only result even in a writable directory.</summary>
    [Fact]
    public async Task ReadOnlyExistingResultStaysUnchangedAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }

        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(path, "old result", TestContext.Current.CancellationToken);
            File.SetUnixFileMode(path, UnixFileMode.UserRead);
            (int exit, string output, _) = await InvokeCliAsync(["modules", "--output", path], directory);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"internal_error","message":"The CLI action failed."}}""");
            File.GetUnixFileMode(path).ShouldBe(UnixFileMode.UserRead);
            (await File.ReadAllTextAsync(path, TestContext.Current.CancellationToken)).ShouldBe("old result");
        }
        finally
        {
            File.SetUnixFileMode(path, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>An existing writable file can be updated when its directory is not writable.</summary>
    [Fact]
    public async Task ExistingFileWorksInUnwritableDirectoryAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }
        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(path, "old result", TestContext.Current.CancellationToken);
            File.SetUnixFileMode(directory, UnixFileMode.UserRead | UnixFileMode.UserExecute);
            int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(path), TestContext.Current.CancellationToken);
            exit.ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(path, TestContext.Current.CancellationToken), """{"updated":true}""");
        }
        finally
        {
            File.SetUnixFileMode(directory, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
            Directory.Delete(directory, recursive: true);
        }
    }

    private static async Task<(int Exit, string Output, int Calls)> InvokeGatewayAsync(bool command, int status, string body)
    {
        string directory = NewDirectory();
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(15));
        using var probe = new TcpListener(IPAddress.Loopback, 0);
        probe.Start();
        int port = ((IPEndPoint)probe.LocalEndpoint).Port;
        probe.Stop();
        string url = $"http://127.0.0.1:{port}/";
        using var gateway = new HttpListener();
        gateway.Prefixes.Add(url);
        gateway.Start();
        int calls = 0;
        Task response = Task.Run(async () =>
        {
            HttpListenerContext context = await gateway.GetContextAsync().WaitAsync(timeout.Token);
            Interlocked.Increment(ref calls);
            context.Request.HttpMethod.ShouldBe("POST");
            context.Request.Url!.AbsolutePath.ShouldBe(command ? "/api/v1/commands" : "/api/v1/queries");
            using var reader = new StreamReader(context.Request.InputStream);
            _ = await reader.ReadToEndAsync(timeout.Token);
            context.Response.StatusCode = status;
            context.Response.StatusDescription = status == 409 ? "Conflict" : status == 202 ? "Accepted" : "OK";
            context.Response.ContentType = "application/problem+json";
            byte[] bytes = Encoding.UTF8.GetBytes(body);
            context.Response.ContentLength64 = bytes.Length;
            await context.Response.OutputStream.WriteAsync(bytes, timeout.Token);
            context.Response.Close();
        }, timeout.Token);
        try
        {
            string[] invocation = command
                ? ["send", "sample.create-item", "--payload", $"{{\"ItemId\":\"{Id}\",\"Title\":\"Hello\"}}", "--url", url]
                : ["query", "string-fixture.list-items", "--payload", "{}", "--url", url];
            (int exit, string output, _) = await InvokeCliAsync(invocation, directory);
            await response.WaitAsync(timeout.Token);
            return (exit, output, calls);
        }
        finally
        {
            await timeout.CancelAsync();
            gateway.Stop();
            Directory.Delete(directory, recursive: true);
        }
    }

    private static async Task<(int Exit, string Output, string Error)> InvokeCliAsync(string[] arguments, string directory)
    {
        TextWriter originalOut = Console.Out;
        TextWriter originalError = Console.Error;
        using var output = new StringWriter();
        using var error = new StringWriter();
        try
        {
            Console.SetOut(output);
            Console.SetError(error);
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            Func<IReadOnlyList<Assembly>> manifest = () => [typeof(SampleContracts.CreateItemCommand).Assembly,
                typeof(StringContracts.Module).Assembly];
            int exit = await new CliRunner(store, manifest, _ => null).Parse(arguments)
                .InvokeAsync(cancellationToken: TestContext.Current.CancellationToken);
            return (exit, output.ToString(), error.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    private static ResolvedSettings Settings(string output, string format = "json")
        => new(null, null, null, null, false, new HashSet<string>(), format, output, false, false, null,
            new Dictionary<string, string>());

    private static string NewDirectory()
    {
        string path = Path.Combine(Path.GetTempPath(), "mcpcli-failures-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }

    private static void AssertJson(string actual, string expected)
    {
        using JsonDocument actualDocument = JsonDocument.Parse(actual);
        using JsonDocument expectedDocument = JsonDocument.Parse(expected);
        JsonElement.DeepEquals(actualDocument.RootElement, expectedDocument.RootElement).ShouldBeTrue(actual);
    }

    private static byte[]? TrySetAcl(string path)
    {
        if (!OperatingSystem.IsLinux())
        {
            return null;
        }

        // POSIX ACL version 2: owner rw, named user r, group r, mask r, other none.
        byte[] acl = [2, 0, 0, 0,
            1, 0, 6, 0, 255, 255, 255, 255,
            2, 0, 4, 0, 232, 3, 0, 0,
            4, 0, 4, 0, 255, 255, 255, 255,
            16, 0, 4, 0, 255, 255, 255, 255,
            32, 0, 0, 0, 255, 255, 255, 255];
        if (SetXattr(path, "system.posix_acl_access", acl, (nuint)acl.Length, 0) == 0)
        {
            return ReadAcl(path) ?? throw new IOException("POSIX ACL setup succeeded but the ACL could not be read.");
        }

        int error = Marshal.GetLastPInvokeError();
        return error is 95 or 38 ? null : throw new IOException($"POSIX ACL setup failed with errno {error}.");
    }

    private static byte[]? ReadAcl(string path)
    {
        byte[] acl = new byte[256];
        long length = GetXattr(path, "system.posix_acl_access", acl, (nuint)acl.Length);
        return length > 0 ? acl[..(int)length] : null;
    }

    [DllImport("libc", EntryPoint = "setxattr", SetLastError = true)]
    private static extern int SetXattr(string path, string name, byte[] value, nuint size, int flags);

    [DllImport("libc", EntryPoint = "getxattr", SetLastError = true)]
    private static extern long GetXattr(string path, string name, byte[] value, nuint size);

    [DllImport("libc", EntryPoint = "mkfifo", SetLastError = true)]
    private static extern int Mkfifo(string path, uint mode);
}

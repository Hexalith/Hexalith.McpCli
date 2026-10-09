using System.IO.Pipes;
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

    /// <summary>A missing, empty, or unreadable @file is an invalid argument with a safe message and unchanged result file.</summary>
    [Fact]
    public async Task MissingPayloadFileHidesPathAndKeepsResultAsync()
    {
        string directory = NewDirectory();
        try
        {
            string result = Path.Combine(directory, "result.json");
            await File.WriteAllTextAsync(result, "old result", TestContext.Current.CancellationToken);
            string missing = Path.Combine(directory, "secret-token-file.json");
            (int exit, string output, string stderr) = await InvokeCliAsync(
                ["query", "string-fixture.list-items", "--payload", "@" + missing, "--output", result], directory, TestContext.Current.CancellationToken);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"invalid_arguments","message":"Unable to read the payload file.","argument":"payload"}}""");
            output.ShouldNotContain(missing);
            stderr.ShouldNotContain(missing);
            (int emptyExit, string emptyOutput, _) = await InvokeCliAsync(
                ["query", "string-fixture.list-items", "--payload", "@", "--output", result], directory,
                TestContext.Current.CancellationToken);
            emptyExit.ShouldBe(2, emptyOutput);
            AssertJson(emptyOutput, """{"error":{"code":"invalid_arguments","message":"Unable to read the payload file.","argument":"payload"}}""");
            string unreadable = Directory.CreateDirectory(Path.Combine(directory, "secret-payload-directory")).FullName;
            (int unreadableExit, string unreadableOutput, string unreadableStderr) = await InvokeCliAsync(
                ["query", "string-fixture.list-items", "--payload", "@" + unreadable, "--output", result], directory,
                TestContext.Current.CancellationToken);
            unreadableExit.ShouldBe(2, unreadableOutput);
            AssertJson(unreadableOutput, """{"error":{"code":"invalid_arguments","message":"Unable to read the payload file.","argument":"payload"}}""");
            unreadableOutput.ShouldNotContain(unreadable);
            unreadableStderr.ShouldNotContain(unreadable);
            (await File.ReadAllTextAsync(result, TestContext.Current.CancellationToken)).ShouldBe("old result");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A missing command payload file is an invalid argument and leaves the requested result untouched.</summary>
    [Fact]
    public async Task MissingCommandPayloadFileLeavesResultUnchangedAsync()
    {
        string directory = NewDirectory();
        try
        {
            string result = Path.Combine(directory, "result.json");
            string missing = Path.Combine(directory, "secret-command-payload.json");
            await File.WriteAllTextAsync(result, "old result", TestContext.Current.CancellationToken);

            (int exit, string output, string stderr) = await InvokeCliAsync(
                ["send", "sample.create-item", "--payload", "@" + missing, "--output", result,
                    "--url", "http://127.0.0.1:1/"], directory, TestContext.Current.CancellationToken);

            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"invalid_arguments","message":"Unable to read the payload file.","argument":"payload"}}""");
            output.ShouldNotContain(missing);
            stderr.ShouldNotContain(missing);
            (await File.ReadAllTextAsync(result, TestContext.Current.CancellationToken)).ShouldBe("old result");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A predictable result-path failure prevents command submission.</summary>
    [Fact]
    public async Task BadCommandOutputPathPreventsRequestAsync()
    {
        string directory = NewDirectory();
        string outputDirectory = Path.Combine(directory, "result-directory");
        Directory.CreateDirectory(outputDirectory);
        try
        {
            (int exit, string output, int calls) = await InvokeGatewayAsync(
                true, 202, "", outputDirectory, acceptedCommand: true);

            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"internal_error","message":"The result destination cannot be written; no request was sent."}}""");
            calls.ShouldBe(0);
            Directory.Exists(outputDirectory).ShouldBeTrue();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A device write can fail after one accepted command, without suggesting a retry.</summary>
    [Fact]
    public async Task AcceptedCommandDeviceWriteFailureReportsAfterOneRequestAsync()
    {
        Assert.SkipWhen(!OperatingSystem.IsLinux(), "The full-device fixture requires Linux.");
        (int exit, string output, int calls) = await InvokeGatewayAsync(
            true, 202, "", "/dev/full", acceptedCommand: true);
        exit.ShouldBe(2, output);
        AssertJson(output, """{"error":{"code":"internal_error","message":"The CLI action failed."}}""");
        calls.ShouldBe(1);
    }

    /// <summary>A successful command writes its canonical result to an existing file after one submission.</summary>
    [Fact]
    public async Task AcceptedCommandWritesExistingResultFileAsync()
    {
        string directory = NewDirectory();
        try
        {
            string target = Path.Combine(directory, "result.json");
            File.WriteAllText(target, "old result");
            (int exit, string output, int calls) = await InvokeGatewayAsync(
                true, 202, "", target, acceptedCommand: true);
            exit.ShouldBe(0, output);
            output.ShouldBeEmpty();
            calls.ShouldBe(1);
            using JsonDocument document = JsonDocument.Parse(File.ReadAllText(target));
            document.RootElement.GetProperty("operation").GetString().ShouldBe("sample.create-item");
            document.RootElement.GetProperty("status").GetString().ShouldBe("accepted");
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
                    "--url", "http://127.0.0.1:1/"], directory, TestContext.Current.CancellationToken);
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
            (int exit, string output, string stderr) = await InvokeCliAsync(
                ["modules", "--format", "table", "--output", targetDirectory], directory, TestContext.Current.CancellationToken);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"internal_error","message":"The CLI action failed."}}""");
            stderr.ShouldNotContain(targetDirectory);
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
            Assert.Skip("This filesystem behavior requires Unix.");
            return;
        }

        string directory = NewDirectory();
        string profile = Path.Combine(directory, "mcpcli.json");
        try
        {
            await File.WriteAllTextAsync(profile, "secret-token-path", TestContext.Current.CancellationToken);
            File.SetUnixFileMode(profile, UnixFileMode.None);
            (int exit, string output, string stderr) = await InvokeCliAsync(["config", "profile", "list"], directory, TestContext.Current.CancellationToken);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"internal_error","message":"The CLI action failed."}}""");
            output.ShouldNotContain(profile);
            stderr.ShouldNotContain(profile);
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
            await File.WriteAllTextAsync(target, new string('x', 4096), TestContext.Current.CancellationToken);
            if (!OperatingSystem.IsWindows())
            {
                File.SetUnixFileMode(target, UnixFileMode.UserRead | UnixFileMode.UserWrite);
                File.CreateSymbolicLink(link, "target.json");
            }
            else
            {
                link = target;
            }

            byte[]? acl = TrySetAcl(target);
            UnixFileMode? beforeMode = OperatingSystem.IsWindows() ? null : File.GetUnixFileMode(target);
            byte[] before = await File.ReadAllBytesAsync(target, TestContext.Current.CancellationToken);
            string[] tempBefore = Directory.GetFiles(Path.GetTempPath(), ".mcpcli-*");
            Func<FileStream, CancellationToken, Task> fault = async (stream, token) =>
            {
                await stream.WriteAsync(new byte[8192], token);
                throw new IOException("secret after partial write");
            };

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
            await File.WriteAllTextAsync(target, new string('x', 4096), TestContext.Current.CancellationToken);
            if (!OperatingSystem.IsWindows())
            {
                File.SetUnixFileMode(target, UnixFileMode.UserRead | UnixFileMode.UserWrite);
                File.CreateSymbolicLink(link, "target.json");
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
            Assert.Skip("This filesystem behavior requires Unix.");
            return;
        }

        string directory = NewDirectory();
        string target = Path.Combine(directory, "new-target.json");
        string link = Path.Combine(directory, "result.json");
        try
        {
            File.CreateSymbolicLink(link, "new-target.json");
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

    /// <summary>Relative links resolve from physical parent directories before the destination is selected.</summary>
    [Fact]
    public async Task NestedRelativeLinksUpdatePhysicalTargetAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            Assert.Skip("This filesystem behavior requires Unix.");
            return;
        }

        string directory = NewDirectory();
        try
        {
            string a = Path.Combine(directory, "a");
            string x = Path.Combine(directory, "x");
            string y = Path.Combine(x, "y");
            Directory.CreateDirectory(a);
            Directory.CreateDirectory(y);
            string correct = Path.Combine(x, "t.json");
            string wrong = Path.Combine(a, "t.json");
            await File.WriteAllTextAsync(correct, "old target", TestContext.Current.CancellationToken);
            await File.WriteAllTextAsync(wrong, "unrelated", TestContext.Current.CancellationToken);
            Directory.CreateSymbolicLink(Path.Combine(a, "linkdir"), "../x/y");
            File.CreateSymbolicLink(Path.Combine(y, "result.json"), "../t.json");

            int exit = await CliOutput.WriteAsync(new { updated = true }, null,
                Settings(Path.Combine(a, "linkdir", "result.json")), TestContext.Current.CancellationToken);

            exit.ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(correct, TestContext.Current.CancellationToken), """{"updated":true}""");
            (await File.ReadAllTextAsync(wrong, TestContext.Current.CancellationToken)).ShouldBe("unrelated");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A parent traversal after a directory link follows the physical link target.</summary>
    [Fact]
    public async Task ParentTraversalAfterDirectoryLinkUpdatesPhysicalTargetAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            Assert.Skip("This filesystem behavior requires Unix.");
            return;
        }

        string directory = NewDirectory();
        try
        {
            string a = Path.Combine(directory, "a");
            string x = Path.Combine(directory, "x");
            Directory.CreateDirectory(a);
            Directory.CreateDirectory(Path.Combine(x, "y"));
            string correct = Path.Combine(x, "result.json");
            string wrong = Path.Combine(a, "result.json");
            await File.WriteAllTextAsync(correct, "old target", TestContext.Current.CancellationToken);
            await File.WriteAllTextAsync(wrong, "unrelated", TestContext.Current.CancellationToken);
            Directory.CreateSymbolicLink(Path.Combine(a, "linkdir"), "../x/y");

            int exit = await CliOutput.WriteAsync(new { updated = true }, null,
                Settings(Path.Combine(a, "linkdir", "..", "result.json")), TestContext.Current.CancellationToken);

            exit.ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(correct, TestContext.Current.CancellationToken), """{"updated":true}""");
            (await File.ReadAllTextAsync(wrong, TestContext.Current.CancellationToken)).ShouldBe("unrelated");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A file or absent parent cannot be bypassed with a subsequent parent traversal.</summary>
    [Theory]
    [InlineData("file")]
    [InlineData("missing")]
    public async Task ParentTraversalCannotBypassInvalidIntermediateAsync(string intermediate)
    {
        string directory = NewDirectory();
        string result = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(result, "unrelated", TestContext.Current.CancellationToken);
            await File.WriteAllTextAsync(Path.Combine(directory, "file"), "plain file", TestContext.Current.CancellationToken);
            await Should.ThrowAsync<IOException>(() => CliOutput.WriteAsync(new { updated = true }, null,
                Settings(Path.Combine(directory, intermediate, "..", "result.json")),
                TestContext.Current.CancellationToken));
            (await File.ReadAllTextAsync(result, TestContext.Current.CancellationToken)).ShouldBe("unrelated");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Restrictive umask cannot make staged or backup files unreadable during rollback.</summary>
    [Fact]
    public async Task RestrictiveUmaskPreservesNewAndExistingOutputAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("This filesystem behavior requires Linux.");
            return;
        }

        string directory = NewDirectory();
        string existing = Path.Combine(directory, "existing.json");
        string created = Path.Combine(directory, "created.json");
        try
        {
            await File.WriteAllTextAsync(existing, "old result", TestContext.Current.CancellationToken);
            uint previous = Umask(0x1FF);
            try
            {
                (await CliOutput.WriteAsync(new { updated = true }, null, Settings(created),
                    TestContext.Current.CancellationToken)).ShouldBe(0);
                File.GetUnixFileMode(created).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
                AssertJson(await File.ReadAllTextAsync(created, TestContext.Current.CancellationToken), """{"updated":true}""");

                Func<FileStream, CancellationToken, Task> fault = (_, _) => throw new IOException("injected write failure");
                await Should.ThrowAsync<IOException>(() => CliOutput.WriteAsync(new { updated = true }, null,
                    Settings(existing), TestContext.Current.CancellationToken, afterDestinationTruncated: fault));
                (await File.ReadAllTextAsync(existing, TestContext.Current.CancellationToken)).ShouldBe("old result");
            }
            finally
            {
                _ = Umask(previous);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>An unlinked regular file remains writable through its proc fd without a ghost pathname.</summary>
    [Fact]
    public async Task UnlinkedProcFdRegularFileUpdatesOpenHandleAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("This filesystem behavior requires Linux.");
            return;
        }

        string directory = NewDirectory();
        string original = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(original, "old result", TestContext.Current.CancellationToken);
            await using FileStream handle = new(original, FileMode.Open, FileAccess.ReadWrite,
                FileShare.ReadWrite | FileShare.Delete, bufferSize: 0, useAsync: true);
            string fdPath = "/proc/self/fd/" + handle.SafeFileHandle.DangerousGetHandle().ToInt64();
            File.Delete(original);
            string ghost = original + " (deleted)";
            File.Exists(ghost).ShouldBeFalse();

            int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(fdPath),
                TestContext.Current.CancellationToken);

            exit.ShouldBe(0);
            handle.Position = 0;
            using var reader = new StreamReader(handle, leaveOpen: true);
            AssertJson(await reader.ReadToEndAsync(TestContext.Current.CancellationToken), """{"updated":true}""");
            File.Exists(original).ShouldBeFalse();
            File.Exists(ghost).ShouldBeFalse();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A literal pipe-shaped symlink target is an ordinary filename.</summary>
    [Fact]
    public async Task LiteralPipeNamedSymlinkTargetIsCreatedAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            Assert.Skip("This filename and symbolic link require Unix.");
            return;
        }

        string directory = NewDirectory();
        string target = Path.Combine(directory, "pipe:[123]");
        string link = Path.Combine(directory, "result.json");
        try
        {
            File.CreateSymbolicLink(link, "pipe:[123]");
            (await CliOutput.WriteAsync(new { updated = true }, null, Settings(link),
                TestContext.Current.CancellationToken)).ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(target, TestContext.Current.CancellationToken), """{"updated":true}""");
            File.ResolveLinkTarget(link, returnFinalTarget: false).ShouldNotBeNull().FullName.ShouldBe(target);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A symlink target with a trailing slash cannot be treated as a regular result file.</summary>
    [Fact]
    public async Task TrailingSlashSymlinkTargetCannotOverwriteFileAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            Assert.Skip("This symbolic link behavior requires Unix.");
            return;
        }

        string directory = NewDirectory();
        string target = Path.Combine(directory, "target.json");
        string link = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(target, "old result", TestContext.Current.CancellationToken);
            File.CreateSymbolicLink(link, "target.json/");
            await Should.ThrowAsync<IOException>(() => CliOutput.WriteAsync(new { updated = true }, null,
                Settings(link), TestContext.Current.CancellationToken));
            (await File.ReadAllTextAsync(target, TestContext.Current.CancellationToken)).ShouldBe("old result");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A symlink chain within the Linux limit remains a usable output path.</summary>
    [Fact]
    public async Task ThirtyThreeLinkOutputChainWorksAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("This symbolic link limit requires Linux.");
            return;
        }

        string directory = NewDirectory();
        string target = Path.Combine(directory, "target.json");
        try
        {
            await File.WriteAllTextAsync(target, "old result", TestContext.Current.CancellationToken);
            for (int index = 32; index >= 0; index--)
            {
                File.CreateSymbolicLink(Path.Combine(directory, "link-" + index),
                    index == 32 ? "target.json" : "link-" + (index + 1));
            }

            (await CliOutput.WriteAsync(new { updated = true }, null, Settings(Path.Combine(directory, "link-0")),
                TestContext.Current.CancellationToken)).ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(target, TestContext.Current.CancellationToken), """{"updated":true}""");
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
            await File.WriteAllTextAsync(path, new string('x', 4096), TestContext.Current.CancellationToken);
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

    /// <summary>A FIFO receives the result directly without staging or backup.</summary>
    [Fact]
    public async Task NonSeekableResultTargetWritesDirectlyAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("This filesystem behavior requires Linux.");
            return;
        }

        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.fifo");
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(3));
        try
        {
            Mkfifo(path, 0x180).ShouldBe(0);
            Task<string> reader = Task.Run(async () =>
            {
                await using FileStream stream = new(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite,
                    bufferSize: 0, useAsync: true);
                using var textReader = new StreamReader(stream);
                return await textReader.ReadToEndAsync(timeout.Token);
            }, timeout.Token);
            int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(path), timeout.Token)
                .WaitAsync(timeout.Token);
            exit.ShouldBe(0);
            AssertJson(await reader.WaitAsync(timeout.Token), """{"updated":true}""");
            File.GetUnixFileMode(path).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A proc fd pipe receives the result directly without resolving its pseudo target as a file path.</summary>
    [Fact]
    public async Task ProcFdPipeReceivesResultDirectlyAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("This filesystem behavior requires Linux.");
            return;
        }

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(3));
        using var pipe = new AnonymousPipeServerStream(PipeDirection.In, HandleInheritability.None);
        string path = "/proc/self/fd/" + pipe.GetClientHandleAsString();
        Task<string> reader = Task.Run(async () =>
        {
            using var textReader = new StreamReader(pipe);
            return await textReader.ReadToEndAsync(timeout.Token);
        }, timeout.Token);

        int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(path), timeout.Token)
            .WaitAsync(timeout.Token);
        pipe.DisposeLocalCopyOfClientHandle();

        exit.ShouldBe(0);
        AssertJson(await reader.WaitAsync(timeout.Token), """{"updated":true}""");
    }

    /// <summary>A character device accepts direct output without a seek or truncate operation.</summary>
    [Fact]
    public async Task DeviceResultTargetWritesDirectlyAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("This filesystem behavior requires Linux.");
            return;
        }

        int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings("/dev/null"),
            TestContext.Current.CancellationToken);
        exit.ShouldBe(0);
    }

    /// <summary>A proc fd naming a character device, as /dev/stdout does under a null redirect, is written directly.</summary>
    [Fact]
    public async Task ProcFdDeviceResultTargetWritesDirectlyAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("This filesystem behavior requires Linux.");
            return;
        }

        using FileStream device = new("/dev/null", FileMode.Open, FileAccess.Write);
        string path = "/proc/self/fd/" + device.SafeFileHandle.DangerousGetHandle().ToInt64();

        int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(path),
            TestContext.Current.CancellationToken);
        exit.ShouldBe(0);
    }

    /// <summary>A regular tmpfs file under /dev/shm is truncated like any other existing result.</summary>
    [Fact]
    public async Task ExistingDevShmResultIsTruncatedAsync()
    {
        if (!OperatingSystem.IsLinux() || !Directory.Exists("/dev/shm"))
        {
            Assert.Skip("This filesystem behavior requires Linux /dev/shm.");
            return;
        }

        string path = Path.Combine("/dev/shm", "mcpcli-result-" + Guid.NewGuid().ToString("N") + ".json");
        try
        {
            await File.WriteAllTextAsync(path, new string('x', 4096), TestContext.Current.CancellationToken);

            int exit = await CliOutput.WriteAsync(new { updated = true }, null, Settings(path),
                TestContext.Current.CancellationToken);

            exit.ShouldBe(0);
            AssertJson(await File.ReadAllTextAsync(path, TestContext.Current.CancellationToken), """{"updated":true}""");
        }
        finally
        {
            File.Delete(path);
        }
    }

    /// <summary>ACL setup errors other than unsupported-filesystem errors fail the test.</summary>
    [Fact]
    public void UnexpectedAclSetupErrorIsNotIgnored()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("This filesystem behavior requires Linux.");
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
            Assert.Skip("This filesystem behavior requires Unix.");
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
            Assert.Skip("This filesystem behavior requires Unix.");
            return;
        }

        string directory = NewDirectory();
        string path = Path.Combine(directory, "result.json");
        try
        {
            await File.WriteAllTextAsync(path, "old result", TestContext.Current.CancellationToken);
            File.SetUnixFileMode(path, UnixFileMode.UserRead);
            (int exit, string output, string stderr) = await InvokeCliAsync(["modules", "--output", path], directory, TestContext.Current.CancellationToken);
            exit.ShouldBe(2, output);
            AssertJson(output, """{"error":{"code":"internal_error","message":"The CLI action failed."}}""");
            stderr.ShouldNotContain(path);
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
            Assert.Skip("This filesystem behavior requires Unix.");
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

    private static async Task<(int Exit, string Output, int Calls)> InvokeGatewayAsync(bool command, int status, string body,
        string? outputPath = null, bool acceptedCommand = false)
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
            try
            {
                while (!timeout.IsCancellationRequested)
                {
                    HttpListenerContext context = await gateway.GetContextAsync().WaitAsync(timeout.Token);
                    Interlocked.Increment(ref calls);
                    context.Request.HttpMethod.ShouldBe("POST");
                    context.Request.Url!.AbsolutePath.ShouldBe(command ? "/api/v1/commands" : "/api/v1/queries");
                    using var reader = new StreamReader(context.Request.InputStream);
                    string requestBody = await reader.ReadToEndAsync(timeout.Token);
                    string responseBody = body;
                    if (acceptedCommand)
                    {
                        using JsonDocument request = JsonDocument.Parse(requestBody);
                        responseBody = JsonSerializer.Serialize(new
                        {
                            correlationId = request.RootElement.GetProperty("correlationId").GetString(),
                            messageId = request.RootElement.GetProperty("messageId").GetString(),
                        });
                    }

                    context.Response.StatusCode = status;
                    context.Response.StatusDescription = status == 409 ? "Conflict" : status == 202 ? "Accepted" : "OK";
                    context.Response.ContentType = acceptedCommand ? "application/json" : "application/problem+json";
                    byte[] bytes = Encoding.UTF8.GetBytes(responseBody);
                    context.Response.ContentLength64 = bytes.Length;
                    await context.Response.OutputStream.WriteAsync(bytes, timeout.Token);
                    context.Response.Close();
                }
            }
            catch (OperationCanceledException) when (timeout.IsCancellationRequested)
            {
            }
        }, timeout.Token);
        try
        {
            string[] invocation = command
                ? ["send", "sample.create-item", "--payload", $"{{\"ItemId\":\"{Id}\",\"Title\":\"Hello\"}}", "--url", url]
                : ["query", "string-fixture.list-items", "--payload", "{}", "--url", url];
            if (outputPath is not null)
            {
                invocation = [.. invocation, "--output", outputPath];
            }

            (int exit, string output, _) = await InvokeCliAsync(invocation, directory, timeout.Token);
            await timeout.CancelAsync();
            await response.WaitAsync(TimeSpan.FromSeconds(3), TestContext.Current.CancellationToken);
            return (exit, output, calls);
        }
        finally
        {
            await timeout.CancelAsync();
            gateway.Stop();
            Directory.Delete(directory, recursive: true);
        }
    }

    private static async Task<(int Exit, string Output, string Error)> InvokeCliAsync(string[] arguments, string directory,
        CancellationToken cancellationToken)
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
            int exit = await new CliRunner(store, manifest, _ => null).InvokeAsync(arguments, cancellationToken);
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
        nint length = GetXattr(path, "system.posix_acl_access", acl, (nuint)acl.Length);
        return length > 0 ? acl[..(int)length] : null;
    }

    [DllImport("libc", EntryPoint = "setxattr", SetLastError = true)]
    private static extern int SetXattr(string path, string name, byte[] value, nuint size, int flags);

    [DllImport("libc", EntryPoint = "getxattr", SetLastError = true)]
    private static extern nint GetXattr(string path, string name, byte[] value, nuint size);

    [DllImport("libc", EntryPoint = "umask")]
    private static extern uint Umask(uint mask);

    [DllImport("libc", EntryPoint = "mkfifo", SetLastError = true)]
    private static extern int Mkfifo(string path, uint mode);
}

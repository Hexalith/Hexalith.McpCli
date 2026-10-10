using System.Diagnostics;
using System.IO.Pipes;
using System.Net.Sockets;
using System.Reflection;
using System.Runtime.Versioning;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Checks the public CLI output and status contract through the checked entry path.</summary>
public sealed class CliOutputContractTests
{
    private static readonly Assembly[] SampleManifest = [typeof(CreateItemCommand).Assembly];

    /// <summary>Malformed input is one safe error with no usage or supplied value.</summary>
    [Fact]
    public async Task ParserFailuresUseSafeDocumentsAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            (string[] Arguments, string Argument)[] cases =
            [
                (["unknown-verb"], "arguments"),
                (["operations", "-x"], "arguments"),
                (["operations", "--clear"], "arguments"),
                (["operations", "--bogus-secret"], "arguments"),
                (["query", "--page-size", "99999999999999999999"], "pageSize"),
                (["query", "--page-size"], "pageSize"),
                (["config", "set", "dev", "tenant", "value", "extra"], "arguments"),
                (["--help=secret"], "arguments"),
                (["/?=secret"], "arguments"),
                (["/h=secret"], "arguments"),
                (["--version=secret"], "arguments"),
                (["modules", "--strict=secret", "--help"], "arguments"),
                (["modules", "--read-only=secret"], "readOnly"),
                (["modules", "--strict=true", "--read-only=bad"], "readOnly"),
                (["modules", "--read-only", "maybe"], "readOnly"),
                (["modules", "--token", "/?=secret"], "arguments"),
                (["operations", "sample", "--kind", "-?=secret"], "arguments"),
                (["query", "--page-size:abc"], "pageSize"),
                (["modules", "--strict:secret"], "strict"),
                (["operations", "--strict=bad"], "strict"),
                (["describe", "--lint=bad"], "lint"),
                (["--version", "--bogus-secret"], "arguments"),
                (["[suggest]", "unknown-verb-secret"], "arguments"),
                (["[suggest:3]", "con"], "arguments"),
                (["operations", "--read-only", "sample", "extra"], "arguments"),
                (["describe", "--strict", "sample.create-item", "extra"], "arguments"),
            ];
            foreach ((string[] arguments, string expectedArgument) in cases)
            {
                (int exit, string output, string error) = await InvokeAsync(store, arguments);
                exit.ShouldBe(2, string.Join(' ', arguments) + output + error);
                error.ShouldBeEmpty();
                output.ShouldNotContain("secret");
                output.ShouldNotContain("Usage:");
                AssertError(output, "invalid_arguments").GetProperty("argument").GetString().ShouldBe(expectedArgument);
            }

            (int mcpExit, string mcpOutput, string mcpError) = await InvokeAsync(store,
                ["mcp", "--transport", "-x"]);
            mcpExit.ShouldBe(2);
            mcpOutput.ShouldBeEmpty();
            AssertError(mcpError, "invalid_arguments");

            (int directiveExit, string directiveOutput, string directiveError) = await InvokeAsync(store,
                ["[suggest]", "mcp", "--transport", "http"]);
            directiveExit.ShouldBe(2);
            directiveOutput.ShouldBeEmpty();
            AssertError(directiveError, "invalid_arguments");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Colon-attached option values accepted by the parser remain valid.</summary>
    [Fact]
    public async Task ColonAttachedOptionsRemainValidAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            (int exit, string output, string error) = await InvokeAsync(store,
                ["--tenant:foo", "config", "current", "--read-only:true"]);
            exit.ShouldBe(0, output + error);
            using JsonDocument document = JsonDocument.Parse(output);
            document.RootElement.GetProperty("tenant").GetString().ShouldBe("foo");
            document.RootElement.GetProperty("readOnly").GetBoolean().ShouldBeTrue();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Bare help stays successful while supplied invalid operands and settings do not bypass validation.</summary>
    [Fact]
    public async Task HelpAliasesValidateSuppliedInputAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            foreach (string[] arguments in new[]
                {
                    new[] { "--help" }, new[] { "config", "--help" }, new[] { "config", "profile", "add", "-h" },
                    new[] { "operations", "-?" }, new[] { "operations", "/?" }, new[] { "operations", "/h" },
                })
            {
                (int exit, string output, string error) = await InvokeAsync(store, arguments);
                exit.ShouldBe(0, string.Join(' ', arguments) + output + error);
                output.ShouldContain("Usage:");
                error.ShouldBeEmpty();
            }

            (string[] Arguments, string Code)[] invalid =
            [
                (["operations", "", "--help"], "invalid_arguments"),
                (["describe", "", "-h"], "invalid_arguments"),
                (["send", "--payload", "{}", "--help"], "invalid_arguments"),
                (["query", "--payload", "{}", "-?"], "invalid_arguments"),
                (["operations", "sample", "--kind", "bad", "/?"], "invalid_arguments"),
                (["config", "set", "dev", "tenant", "--help"], "invalid_arguments"),
                (["config", "use", "--clear=false", "--help"], "invalid_arguments"),
                (["modules", "--url", "ftp://bad.example/", "--help"], "invalid_arguments"),
                (["modules", "--format", "xml", "--help"], "invalid_arguments"),
                (["config", "profile", "remove", "missing", "--help"], "invalid_arguments"),
                (["config", "use", "missing", "-h"], "invalid_arguments"),
                (["config", "set", "dev", "badfield", "x", "--help"], "invalid_arguments"),
                (["config", "profile", "add", "dev", "--help"], "invalid_arguments"),
            ];
            foreach ((string[] arguments, string code) in invalid)
            {
                (int exit, string output, string error) = await InvokeAsync(store, arguments);
                exit.ShouldBe(2, string.Join(' ', arguments) + output + error);
                error.ShouldBeEmpty();
                output.ShouldNotContain("Usage:");
                AssertError(output, code);
            }

            (int httpExit, string httpOut, string httpError) = await InvokeAsync(store,
                ["mcp", "--transport", "http", "--help"]);
            httpExit.ShouldBe(2);
            httpOut.ShouldBeEmpty();
            AssertError(httpError, "invalid_arguments");

            (int slashHttpExit, string slashHttpOut, string slashHttpError) = await InvokeAsync(store,
                ["mcp", "--transport", "http", "/h"]);
            slashHttpExit.ShouldBe(2);
            slashHttpOut.ShouldBeEmpty();
            AssertError(slashHttpError, "invalid_arguments");

            (int mcpSettingsExit, string mcpSettingsOut, string mcpSettingsError) = await InvokeAsync(store,
                ["mcp", "--url", "ftp://bad.example/", "--help"]);
            mcpSettingsExit.ShouldBe(2);
            mcpSettingsOut.ShouldBeEmpty();
            AssertError(mcpSettingsError, "invalid_arguments");

            (int mcpFormatExit, string mcpFormatOut, string mcpFormatError) = await InvokeAsync(store,
                ["mcp", "--format", "table", "--help"]);
            mcpFormatExit.ShouldBe(2);
            mcpFormatOut.ShouldBeEmpty();
            AssertError(mcpFormatError, "invalid_arguments");

            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            (int literalExit, string literalOutput, string literalError) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "--", "--help"]);
            literalExit.ShouldBe(0, literalOutput + literalError);
            literalOutput.ShouldNotContain("Usage:");
            store.Read().Profiles["dev"].Actor.ShouldBe("--help");

            foreach (string value in new[] { "[suggest]", "[suggest:3]" })
            {
                (int settingExit, string settingOutput, string settingError) = await InvokeAsync(store,
                    ["config", "set", "dev", "actor", value]);
                settingExit.ShouldBe(0, settingOutput + settingError);
                settingError.ShouldBeEmpty();
                store.Read().Profiles["dev"].Actor.ShouldBe(value);
            }

            foreach (string value in new[] { "/h", "/?" })
            {
                (int settingExit, string settingOutput, string settingError) = await InvokeAsync(store,
                    ["config", "set", "dev", "actor", "--", value]);
                settingExit.ShouldBe(0, settingOutput + settingError);
                settingError.ShouldBeEmpty();
                store.Read().Profiles["dev"].Actor.ShouldBe(value);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>HTTP transport is refused before the Catalog manifest is read.</summary>
    [Fact]
    public async Task PlainHttpTransportUsesStderrWithoutCatalogAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            int manifestReads = 0;
            Func<IReadOnlyList<Assembly>> manifest = () =>
            {
                manifestReads++;
                return SampleManifest;
            };

            (int exit, string output, string error) = await InvokeAsync(store,
                ["mcp", "--transport", "http"], manifest);
            exit.ShouldBe(2);
            output.ShouldBeEmpty();
            AssertError(error, "unsupported_transport").GetProperty("message").GetString()!.ShouldContain("next release");
            manifestReads.ShouldBe(0);

            foreach (string[] malformed in new[]
                {
                    new[] { "mcp", "--transport=--bogus-secret" },
                    new[] { "mcp", "--transport=-x" },
                })
            {
                (int malformedExit, string malformedOutput, string malformedError) = await InvokeAsync(store,
                    malformed, manifest);
                malformedExit.ShouldBe(2);
                malformedOutput.ShouldBeEmpty();
                malformedError.ShouldNotContain("bogus-secret");
                AssertError(malformedError, "invalid_arguments");
                manifestReads.ShouldBe(0);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A version token after the option separator is a literal config value.</summary>
    [Fact]
    public async Task VersionAfterSeparatorIsLiteralProfileValueAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));

            (int exit, string output, string error) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "--", "--version"]);
            exit.ShouldBe(0, output + error);
            error.ShouldBeEmpty();
            using (JsonDocument document = JsonDocument.Parse(output))
            {
                document.RootElement.GetProperty("field").GetString().ShouldBe("actor");
            }

            store.Read().Profiles["dev"].Actor.ShouldBe("--version");

            (int malformedExit, string malformedOutput, string malformedError) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "--version"]);
            malformedExit.ShouldBe(2);
            malformedError.ShouldBeEmpty();
            AssertError(malformedOutput, "invalid_arguments");
            store.Read().Profiles["dev"].Actor.ShouldBe("--version");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Known no-result errors win over an unusable destination, while valid mutations are blocked.</summary>
    [Fact]
    public async Task ResultPreflightPreservesErrorPrecedenceAndProfilesAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            byte[] before = File.ReadAllBytes(store.ProfilePath);
            string bad = Path.Combine(directory, "occupied-directory");
            Directory.CreateDirectory(bad);

            (int discoveryExit, string discovery, _) = await InvokeAsync(store,
                ["operations", "missing", "--output", bad]);
            discoveryExit.ShouldBe(2);
            AssertError(discovery, "unknown_module");

            foreach (string[] arguments in new[]
                {
                    new[] { "config", "profile", "add", "new", "--url", "https://gateway.example/" },
                    new[] { "config", "profile", "remove", "dev" },
                    new[] { "config", "use", "dev" },
                    new[] { "config", "set", "dev", "actor", "operator" },
                })
            {
                (int exit, string output, _) = await InvokeAsync(store, [.. arguments, "--output", bad]);
                exit.ShouldBe(2, string.Join(' ', arguments) + output);
                AssertError(output, "internal_error").GetProperty("message").GetString().ShouldBe(
                    "The result destination cannot be written; no request was sent.");
                File.ReadAllBytes(store.ProfilePath).ShouldBe(before);
            }

            foreach (string[] arguments in new[]
                {
                    new[] { "config", "profile", "remove", "missing" },
                    new[] { "config", "use", "missing" },
                    new[] { "config", "profile", "add", "bad name", "--url", "https://gateway.example/" },
                    new[] { "config", "set", "dev", "allowTenantOverride", "bad" },
                    new[] { "config", "set", "dev", "allowedExtensions", "bad key" },
                })
            {
                (int exit, string output, _) = await InvokeAsync(store, [.. arguments, "--output", bad]);
                exit.ShouldBe(2);
                AssertError(output, "configuration_invalid");
                File.ReadAllBytes(store.ProfilePath).ShouldBe(before);
            }

            File.WriteAllText(store.ProfilePath, "{");
            foreach (string[] arguments in new[]
                {
                    new[] { "config", "profile", "add", "new", "--url", "https://gateway.example/" },
                    new[] { "config", "use", "--clear" },
                })
            {
                (int exit, string output, _) = await InvokeAsync(store, [.. arguments, "--output", bad]);
                exit.ShouldBe(2);
                AssertError(output, "configuration_invalid");
                File.ReadAllText(store.ProfilePath).ShouldBe("{");
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Existing files and links remain valid result destinations.</summary>
    [Fact]
    public async Task ExistingFileAndLinkReceiveConfigResultsAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string target = Path.Combine(directory, "result.json");
            File.WriteAllText(target, "old result");
            (int exit, string output, _) = await InvokeAsync(store, ["config", "current", "--output", target]);
            exit.ShouldBe(0, output);
            output.ShouldBeEmpty();
            using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(target)))
            {
                document.RootElement.GetProperty("format").GetString().ShouldBe("json");
            }

            if (!OperatingSystem.IsWindows())
            {
                string link = Path.Combine(directory, "result-link");
                File.CreateSymbolicLink(link, target);
                (exit, output, _) = await InvokeAsync(store, ["config", "profile", "list", "--output", link]);
                exit.ShouldBe(0, output);
                output.ShouldBeEmpty();
                new FileInfo(link).LinkTarget.ShouldBe(target);
                using JsonDocument document = JsonDocument.Parse(File.ReadAllText(target));
                document.RootElement.GetProperty("profiles").GetArrayLength().ShouldBe(0);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Successful profile writes leave no preflight probes in either staging location.</summary>
    [Fact]
    public async Task MutationPreflightRemovesProbeFilesAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            string[] beforeTemp = Directory.GetFiles(Path.GetTempPath(), ".mcpcli-probe-*");
            string created = Path.Combine(directory, "new-result.json");
            (int newExit, string newOutput, _) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "first", "--output", created]);
            newExit.ShouldBe(0, newOutput);
            newOutput.ShouldBeEmpty();
            File.Exists(created).ShouldBeTrue();
            Directory.GetFiles(directory, ".mcpcli-probe-*").ShouldBeEmpty();
            Directory.GetFiles(Path.GetTempPath(), ".mcpcli-probe-*").ShouldBe(beforeTemp);

            (int existingExit, string existingOutput, _) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "second", "--output", created]);
            existingExit.ShouldBe(0, existingOutput);
            existingOutput.ShouldBeEmpty();
            Directory.GetFiles(directory, ".mcpcli-probe-*").ShouldBeEmpty();
            Directory.GetFiles(Path.GetTempPath(), ".mcpcli-probe-*").ShouldBe(beforeTemp);

            if (!OperatingSystem.IsWindows())
            {
                string link = Path.Combine(directory, "result-link");
                File.CreateSymbolicLink(link, created);
                (int linkExit, string linkOutput, _) = await InvokeAsync(store,
                    ["config", "set", "dev", "actor", "third", "--output", link]);
                linkExit.ShouldBe(0, linkOutput);
                linkOutput.ShouldBeEmpty();
                new FileInfo(link).LinkTarget.ShouldBe(created);
                Directory.GetFiles(Path.GetTempPath(), ".mcpcli-probe-*").ShouldBe(beforeTemp);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Core failures keep their documents despite a bad path, and a valid query probes before submission.</summary>
    [Fact]
    public async Task QueryPreflightRunsAfterNoResultChecksAsync()
    {
        string directory = NewDirectory();
        try
        {
            await using var harness = new QueryCliHarness();
            string bad = Path.Combine(directory, "occupied-directory");
            Directory.CreateDirectory(bad);

            (int unknownExit, string unknown, _) = await harness.InvokeAsync(
                ["query", "missing.operation", "--payload", "{}", "--output", bad]);
            unknownExit.ShouldBe(2);
            AssertError(unknown, "unknown_operation");

            (int invalidExit, string invalid, _) = await harness.InvokeAsync(
                ["query", "string-fixture.list-items", "--payload", "{", "--output", bad]);
            invalidExit.ShouldBe(2);
            AssertError(invalid, "validation_failed");

            (int badExit, string failed, _) = await harness.InvokeAsync(
                ["query", "string-fixture.list-items", "--payload", "{}", "--output", bad]);
            badExit.ShouldBe(2);
            AssertError(failed, "internal_error").GetProperty("message").GetString().ShouldBe(
                "The result destination cannot be written; no request was sent.");
            harness.Calls.ShouldBe(0);

            string target = Path.Combine(directory, "query-result.json");
            File.WriteAllText(target, "old result");
            (int successExit, string successOutput, _) = await harness.InvokeAsync(
                ["query", "string-fixture.list-items", "--payload", "{}", "--output", target]);
            successExit.ShouldBe(0, successOutput);
            successOutput.ShouldBeEmpty();
            harness.Calls.ShouldBe(1);
            using JsonDocument document = JsonDocument.Parse(File.ReadAllText(target));
            document.RootElement.GetProperty("operation").GetString().ShouldBe("string-fixture.list-items");
            document.RootElement.GetProperty("document").GetProperty("items").GetArrayLength().ShouldBe(0);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Late Core paging and aggregate validation wins over destination preflight.</summary>
    [Fact]
    public async Task LaterCoreValidationWinsOverBadOutputPathAsync()
    {
        string directory = NewDirectory();
        try
        {
            await using var harness = new QueryCliHarness();
            string bad = Path.Combine(directory, "occupied-directory");
            Directory.CreateDirectory(bad);
            (string[] Arguments, string Path)[] cases =
            [
                (["query", "string-fixture.list-items", "--payload", "{}", "--page-size", "0"], "/pageSize"),
                (["query", "string-fixture.list-items", "--payload", "{}", "--aggregate-id", "a/b"], "/aggregateId"),
                (["send", "routing-fixture.renamed-aggregate", "--payload",
                    $$"""{"aggregate/~id":"{{QueryCliHarness.ItemId}}"}""", "--aggregate-id",
                    "01ARZ3NDEKTSV4RRFFQ69G5FAW", "--tenant", "session-tenant"], "/aggregateId"),
            ];

            foreach ((string[] arguments, string path) in cases)
            {
                (int exit, string output, _) = await harness.InvokeAsync([.. arguments, "--output", bad]);
                exit.ShouldBe(2, output);
                JsonElement failure = AssertError(output, "validation_failed");
                failure.GetProperty("violations").EnumerateArray()
                    .Select(violation => violation.GetProperty("path").GetString()).ShouldContain(path);
                harness.Calls.ShouldBe(0);
                Directory.EnumerateFileSystemEntries(bad).ShouldBeEmpty();
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Command lookup and payload failures keep their Core errors ahead of output-path checks.</summary>
    [Fact]
    public async Task SendNoResultErrorsWinOverBadOutputPathAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string bad = Path.Combine(directory, "occupied-directory");
            Directory.CreateDirectory(bad);
            string[] before = Directory.GetFileSystemEntries(directory);

            (int unknownExit, string unknownOutput, string unknownError) = await InvokeAsync(store,
                ["send", "missing.operation", "--payload", "{}", "--output", bad]);
            unknownExit.ShouldBe(2);
            unknownError.ShouldBeEmpty();
            AssertError(unknownOutput, "unknown_operation");

            (int invalidExit, string invalidOutput, string invalidError) = await InvokeAsync(store,
                ["send", "sample.create-item", "--payload", "{", "--url", "http://127.0.0.1:1/", "--output", bad]);
            invalidExit.ShouldBe(2);
            invalidError.ShouldBeEmpty();
            AssertError(invalidOutput, "validation_failed");

            Directory.GetFileSystemEntries(directory).ShouldBe(before);
            Directory.EnumerateFileSystemEntries(bad).ShouldBeEmpty();
            File.Exists(store.ProfilePath).ShouldBeFalse();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A missing system staging directory is rejected before a profile change.</summary>
    [Fact]
    public async Task MissingExistingFileStagingDirectoryPreventsMutationAsync()
    {
        Assert.SkipWhen(OperatingSystem.IsWindows(),
            "A child process cannot reliably redirect ProfileStore's Windows user-profile path.");
        string directory = NewDirectory();
        try
        {
            string target = Path.Combine(directory, "result.json");
            File.WriteAllText(target, "old result");
            var start = new ProcessStartInfo
            {
                FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
            };
            foreach (string name in start.Environment.Keys
                .Where(name => name.StartsWith("EVENTSTORE_", StringComparison.OrdinalIgnoreCase)).ToArray())
            {
                start.Environment.Remove(name);
            }

            start.Environment["HOME"] = directory;
            start.Environment["TMPDIR"] = Path.Combine(directory, "missing-temp");
            start.ArgumentList.Add(typeof(CliRunner).Assembly.Location);
            foreach (string argument in new[]
                { "config", "profile", "add", "dev", "--url", "https://gateway.example/", "--output", target })
            {
                start.ArgumentList.Add(argument);
            }

            using Process process = Process.Start(start).ShouldNotBeNull();
            Task<string> stdout = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
            Task<string> stderr = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
            string output = await stdout;
            string error = await stderr;
            await process.WaitForExitAsync(TestContext.Current.CancellationToken);
            process.ExitCode.ShouldBe(2, output + error);
            AssertError(output, "internal_error");
            File.ReadAllText(target).ShouldBe("old result");
            File.Exists(Path.Combine(directory, ".eventstore", "mcpcli.json")).ShouldBeFalse();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Empty lists have no phantom row, and raw descriptions cannot add columns or rows.</summary>
    [Fact]
    public async Task TableCellsKeepOnePhysicalRowAndConfigJsonEscapesAsync()
    {
        string directory = NewDirectory();
        TextWriter original = Console.Out;
        using var output = new StringWriter();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            ResolvedSettings settings = new SettingsResolver(store, new Dictionary<string, string?>())
                .Resolve(new SettingsInput(Format: "table")).Settings.ShouldNotBeNull();
            Console.SetOut(output);
            await CliOutput.WriteAsync(new ModulesDocument([]), null, settings,
                TestContext.Current.CancellationToken, "NAME\tOPERATIONS\tDESCRIPTION");
            output.ToString().ShouldBe("NAME\tOPERATIONS\tDESCRIPTION" + Environment.NewLine);

            output.GetStringBuilder().Clear();
            await CliOutput.WriteAsync(new ModulesDocument([new ModuleSummary("sample", "tab\tand\nline\r\\path", 1)]),
                null, settings, TestContext.Current.CancellationToken, "NAME\tOPERATIONS\tDESCRIPTION");
            output.ToString().ShouldBe("NAME\tOPERATIONS\tDESCRIPTION" + Environment.NewLine
                + "sample\t1\ttab\\tand\\nline\\r\\\\path" + Environment.NewLine);

            output.GetStringBuilder().Clear();
            await CliOutput.WriteAsync(new OperationsDocument("sample", []), null, settings,
                TestContext.Current.CancellationToken, "NAME\tKIND\tDESCRIPTION");
            output.ToString().ShouldBe("NAME\tKIND\tDESCRIPTION" + Environment.NewLine);

            output.GetStringBuilder().Clear();
            await CliOutput.WriteAsync(new OperationsDocument("sample",
                [new OperationSummary("sample.operation", "read", "tab\tand\nline\r\\path")]), null, settings,
                TestContext.Current.CancellationToken, "NAME\tKIND\tDESCRIPTION");
            output.ToString().ShouldBe("NAME\tKIND\tDESCRIPTION" + Environment.NewLine
                + "sample.operation\tread\ttab\\tand\\nline\\r\\\\path" + Environment.NewLine);

            output.GetStringBuilder().Clear();
            await CliOutput.WriteAsync(new { value = "a\\b" }, null, settings,
                TestContext.Current.CancellationToken, "FIELD\tVALUE");
            string row = output.ToString().Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries)[1];
            JsonDocument.Parse(row["value\t".Length..]).RootElement.GetString().ShouldBe("a\\b");
        }
        finally
        {
            Console.SetOut(original);
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Unusable links, sockets, and proc descriptors fail before creating a profile.</summary>
    [Fact]
    public async Task SpecialTargetsAreClassifiedBeforeMutationAsync()
    {
        Assert.SkipWhen(OperatingSystem.IsWindows(), "Unix file-type fixtures are required.");
        string directory = NewDirectory();
        string socketPath = Path.Combine("/tmp", "mc-" + Guid.NewGuid().ToString("N")[..8]);
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string link = Path.Combine(directory, "unusable-link");
            File.CreateSymbolicLink(link, Path.Combine(directory, "missing-parent", "result.json"));
            using var socket = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
            socket.Bind(new UnixDomainSocketEndPoint(socketPath));

            string[] targets = OperatingSystem.IsLinux()
                ? [link, socketPath, "/proc/self/fd/999999"]
                : [link, socketPath];
            foreach (string target in targets)
            {
                (int exit, string output, _) = await InvokeAsync(store,
                    ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--output", target]);
                exit.ShouldBe(2, target + output);
                AssertError(output, "internal_error");
                File.Exists(store.ProfilePath).ShouldBeFalse();
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
            if (File.Exists(socketPath))
            {
                File.Delete(socketPath);
            }
        }
    }

    /// <summary>CLI file output accepts a character device and a live anonymous pipe.</summary>
    [Fact]
    public async Task CliAcceptsDeviceAndProcFdPipeAsync()
    {
        Assert.SkipWhen(!OperatingSystem.IsLinux(), "The device and proc-fd fixtures require Linux.");
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            (int deviceExit, string deviceOutput, string deviceError) = await InvokeAsync(store,
                ["config", "current", "--output", "/dev/null"]);
            deviceExit.ShouldBe(0, deviceOutput + deviceError);
            deviceOutput.ShouldBeEmpty();

            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            (int mutationExit, string mutationOutput, string mutationError) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "device", "--output", "/dev/null"]);
            mutationExit.ShouldBe(0, mutationOutput + mutationError);
            mutationOutput.ShouldBeEmpty();
            store.Read().Profiles["dev"].Actor.ShouldBe("device");

            for (int index = 0; index < 2; index++)
            {
                using var server = new AnonymousPipeServerStream(PipeDirection.Out, HandleInheritability.None);
                using var client = new AnonymousPipeClientStream(PipeDirection.In, server.ClientSafePipeHandle);
                string path = "/proc/self/fd/" + server.SafePipeHandle.DangerousGetHandle().ToInt64();
                string[] arguments = index == 0
                    ? ["config", "current", "--output", path]
                    : ["config", "set", "dev", "actor", "pipe", "--output", path];
                (int pipeExit, string pipeOutput, string pipeError) = await InvokeAsync(store, arguments);
                pipeExit.ShouldBe(0, pipeOutput + pipeError);
                pipeOutput.ShouldBeEmpty();
                server.Dispose();
                using var reader = new StreamReader(client);
                using JsonDocument result = JsonDocument.Parse(
                    await reader.ReadToEndAsync(TestContext.Current.CancellationToken));
                if (index == 0)
                {
                    result.RootElement.GetProperty("format").GetString().ShouldBe("json");
                }
                else
                {
                    result.RootElement.GetProperty("field").GetString().ShouldBe("actor");
                    store.Read().Profiles["dev"].Actor.ShouldBe("pipe");
                }
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A FIFO with owner-denied write access fails, while one with write access needs no reader at preflight.</summary>
    [Fact]
    public async Task FifoPreflightChecksAccessWithoutWaitingForReaderAsync()
    {
        if (!OperatingSystem.IsLinux())
        {
            Assert.Skip("The FIFO fixture uses the Linux mkfifo utility.");
            return;
        }
        Assert.SkipWhen(Environment.IsPrivilegedProcess,
            "Root can bypass the owner-denied FIFO fixture and block opening it without a reader.");
        string directory = NewDirectory();
        try
        {
            string fifo = Path.Combine(directory, "result-fifo");
            using (Process created = Process.Start(new ProcessStartInfo("mkfifo")
            {
                ArgumentList = { fifo },
                UseShellExecute = false,
            }).ShouldNotBeNull())
            {
                await created.WaitForExitAsync(TestContext.Current.CancellationToken);
                created.ExitCode.ShouldBe(0);
            }

            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            File.SetUnixFileMode(fifo, UnixFileMode.OtherWrite);
            (int exit, string output, _) = await InvokeAsync(store,
                ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--output", fifo]);
            exit.ShouldBe(2, output);
            AssertError(output, "internal_error");
            File.Exists(store.ProfilePath).ShouldBeFalse();

            File.SetUnixFileMode(fifo, UnixFileMode.UserWrite);
            CliOutput.Preflight(fifo);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Existing-file and new-file permission failures are caught before profile mutation.</summary>
    [Fact]
    public async Task DeniedRegularAndNewFileParentPreventMutationAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            Assert.Skip("Unix file modes are required for this fixture.");
            return;
        }

        Assert.SkipWhen(Environment.IsPrivilegedProcess,
            "Root can create the staging probe in a read-only parent.");
        string directory = NewDirectory();
        string parent = Path.Combine(directory, "no-write-parent");
        Directory.CreateDirectory(parent);
        string existing = Path.Combine(directory, "read-only-result.json");
        File.WriteAllText(existing, "old result");
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            File.SetUnixFileMode(existing, UnixFileMode.UserRead);
            File.SetUnixFileMode(parent, UnixFileMode.UserRead | UnixFileMode.UserExecute);
            foreach (string target in new[] { existing, Path.Combine(parent, "new-result.json") })
            {
                (int exit, string output, _) = await InvokeAsync(store,
                    ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--output", target]);
                exit.ShouldBe(2, target + output);
                AssertError(output, "internal_error");
                File.Exists(store.ProfilePath).ShouldBeFalse();
            }

            File.ReadAllText(existing).ShouldBe("old result");
        }
        finally
        {
            File.SetUnixFileMode(existing, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            File.SetUnixFileMode(parent, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A Windows read-only result file prevents profile mutation and is reset before fixture cleanup.</summary>
    [Fact]
    public async Task WindowsReadOnlyExistingOutputPreventsProfileMutationAsync()
    {
        if (!OperatingSystem.IsWindows())
        {
            Assert.Skip("Windows file attributes are required for this fixture.");
            return;
        }

        string directory = NewDirectory();
        string target = Path.Combine(directory, "read-only-result.json");
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            byte[] before = File.ReadAllBytes(store.ProfilePath);
            File.WriteAllText(target, "old result");
            File.SetAttributes(target, FileAttributes.ReadOnly);

            (int exit, string output, string error) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "operator", "--output", target]);
            exit.ShouldBe(2, output + error);
            error.ShouldBeEmpty();
            AssertError(output, "internal_error");
            File.ReadAllBytes(store.ProfilePath).ShouldBe(before);
            File.ReadAllText(target).ShouldBe("old result");
        }
        finally
        {
            if (File.Exists(target))
            {
                File.SetAttributes(target, FileAttributes.Normal);
            }

            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>An ACL-denied Windows target is never mistaken for a missing result file.</summary>
    [Fact]
    [SupportedOSPlatform("windows")]
    public async Task WindowsInaccessibleExistingOutputPreventsProfileMutationAsync()
    {
        Assert.SkipUnless(OperatingSystem.IsWindows(), "Windows ACLs are required for this fixture.");
        string directory = NewDirectory();
        string target = Path.Combine(directory, "inaccessible-result.json");
        var file = new FileInfo(target);
        FileSecurity? originalAcl = null;
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            byte[] before = File.ReadAllBytes(store.ProfilePath);
            File.WriteAllText(target, "old result");

            originalAcl = file.GetAccessControl();
            FileSecurity denied = file.GetAccessControl();
            SecurityIdentifier user = WindowsIdentity.GetCurrent().User.ShouldNotBeNull();
            denied.AddAccessRule(new FileSystemAccessRule(user, FileSystemRights.ReadAttributes, AccessControlType.Deny));
            file.SetAccessControl(denied);
            Should.Throw<UnauthorizedAccessException>(() => File.GetAttributes(target));

            (int exit, string output, string error) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "operator", "--output", target]);
            exit.ShouldBe(2, output + error);
            error.ShouldBeEmpty();
            AssertError(output, "internal_error");
            File.ReadAllBytes(store.ProfilePath).ShouldBe(before);

            file.SetAccessControl(originalAcl);
            originalAcl = null;
            File.ReadAllText(target).ShouldBe("old result");
        }
        finally
        {
            if (originalAcl is not null)
            {
                file.SetAccessControl(originalAcl);
            }

            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The current build's executable uses the checked parser rather than invoking a raw parse.</summary>
    [Fact]
    public async Task CurrentExecutableRejectsMalformedInputAsync()
    {
        var start = new ProcessStartInfo
        {
            FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        start.ArgumentList.Add(typeof(CliRunner).Assembly.Location);
        start.ArgumentList.Add("--version");
        start.ArgumentList.Add("--bogus-secret");
        using Process process = Process.Start(start).ShouldNotBeNull();
        Task<string> stdout = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
        Task<string> stderr = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
        string output = await stdout;
        string error = await stderr;
        await process.WaitForExitAsync(TestContext.Current.CancellationToken);
        process.ExitCode.ShouldBe(2, output + error);
        error.ShouldBeEmpty();
        output.ShouldNotContain("bogus-secret");
        AssertError(output, "invalid_arguments");
    }

    private static async Task<(int Exit, string Output, string Error)> InvokeAsync(ProfileStore store, string[] arguments,
        Func<IReadOnlyList<Assembly>>? manifest = null)
    {
        TextWriter originalOut = Console.Out;
        TextWriter originalError = Console.Error;
        using var output = new StringWriter();
        using var error = new StringWriter();
        try
        {
            Console.SetOut(output);
            Console.SetError(error);
            int exit = await new CliRunner(store, manifest ?? (() => SampleManifest), _ => null)
                .InvokeAsync(arguments, TestContext.Current.CancellationToken);
            return (exit, output.ToString(), error.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    private static JsonElement AssertError(string output, string code)
    {
        using JsonDocument document = JsonDocument.Parse(output);
        JsonElement root = document.RootElement;
        root.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
        JsonElement error = root.GetProperty("error");
        error.GetProperty("code").GetString().ShouldBe(code);
        return error.Clone();
    }

    private static string NewDirectory()
    {
        string path = Path.Combine(Path.GetTempPath(), "mcpcli-output-contract-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }
}

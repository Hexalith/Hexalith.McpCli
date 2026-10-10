using System.CommandLine;
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
    private const string ScanMessage = "The command contains an unknown or malformed option. Run with --help for usage.";
    private const string ParseMessage = "The command arguments are missing or invalid. Run with --help for usage.";
    private const string HelpMessage = "Help must be requested without arguments or options.";

    /// <summary>Malformed input is one safe error with no usage or supplied value.</summary>
    [Fact]
    public async Task ParserFailuresUseSafeDocumentsAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            (string[] Arguments, string Argument, string Message)[] cases =
            [
                (["unknown-verb"], "arguments", ParseMessage),
                (["operations", "-x"], "arguments", ScanMessage),
                (["operations", "--clear"], "arguments", ScanMessage),
                (["operations", "--bogus-secret"], "arguments", ScanMessage),
                (["query", "--page-size", "99999999999999999999"], "pageSize", ParseMessage),
                (["query", "--page-size"], "pageSize", ParseMessage),
                (["config", "set", "dev", "tenant", "value", "extra"], "arguments", ParseMessage),
                (["--help=secret"], "arguments", ScanMessage),
                (["/?=secret"], "arguments", ScanMessage),
                (["/h=secret"], "arguments", ScanMessage),
                (["--version=secret"], "arguments", ScanMessage),
                (["modules", "--strict=secret", "--help"], "arguments", ScanMessage),
                (["modules", "--read-only=secret"], "readOnly", ScanMessage),
                (["modules", "--strict=true", "--read-only=bad"], "readOnly", ScanMessage),
                (["modules", "--read-only", "maybe"], "readOnly", ParseMessage),
                (["modules", "--token", "/?=secret"], "arguments", ScanMessage),
                (["operations", "sample", "--kind", "-?=secret"], "arguments", ScanMessage),
                (["query", "--page-size:abc"], "pageSize", ParseMessage),
                (["modules", "--strict:secret"], "strict", ScanMessage),
                (["operations", "--strict=bad"], "strict", ScanMessage),
                (["describe", "--lint=bad"], "lint", ScanMessage),
                (["--version", "--bogus-secret"], "arguments", ScanMessage),
                (["[suggest]", "unknown-verb-secret"], "arguments", ScanMessage),
                (["[suggest:3]", "con"], "arguments", ScanMessage),
                (["[bogus]", "modules"], "arguments", ScanMessage),
                (["[x:secret]", "modules"], "arguments", ScanMessage),
                (["[bogus]", "[suggest]", "config", "current"], "arguments", ScanMessage),
                (["operations", "--read-only", "sample", "extra"], "arguments", ParseMessage),
                (["describe", "--strict", "sample.create-item", "extra"], "arguments", ParseMessage),
            ];
            foreach ((string[] arguments, string expectedArgument, string expectedMessage) in cases)
            {
                (int exit, string output, string error) = await InvokeAsync(store, arguments);
                exit.ShouldBe(2, string.Join(' ', arguments) + output + error);
                error.ShouldBeEmpty();
                output.ShouldNotContain("secret");
                output.ShouldNotContain("Usage:");
                AssertInvalidArguments(output, expectedMessage, expectedArgument);
            }

            foreach (string[] arguments in new[]
                {
                    Array.Empty<string>(), new[] { "config" }, new[] { "config", "profile" },
                    new[] { "unknown-verb" },
                })
            {
                (int exit, string output, string error) = await InvokeAsync(store, arguments);
                exit.ShouldBe(2, output + error);
                error.ShouldBeEmpty();
                AssertInvalidArguments(output, ParseMessage, "arguments");
            }

            (int mcpExit, string mcpOutput, string mcpError) = await InvokeAsync(store,
                ["mcp", "--transport", "-x"]);
            mcpExit.ShouldBe(2);
            mcpOutput.ShouldBeEmpty();
            AssertInvalidArguments(mcpError, ScanMessage, "arguments");

            (int directiveExit, string directiveOutput, string directiveError) = await InvokeAsync(store,
                ["[suggest]", "mcp", "--transport", "http"]);
            directiveExit.ShouldBe(2);
            directiveOutput.ShouldBeEmpty();
            AssertInvalidArguments(directiveError, ScanMessage, "arguments");

            store.Add("dev", new ConnectionProfile("https://gateway.example/", Actor: "original"));
            string rootName = RootCommand.ExecutableName;
            string profilePath = Path.Combine(directory, "mcpcli.json");
            byte[] originalProfile = File.ReadAllBytes(profilePath);
            foreach (string[] arguments in new[]
                {
                    new[] { "[x]", "config", "set", "dev", "actor", "bracket" },
                    new[] { "[bogus]", "config", "profile", "remove", "dev" },
                    new[] { rootName, "[bogus]", "config", "profile", "remove", "dev" },
                })
            {
                (int exit, string output, string error) = await InvokeAsync(store, arguments);
                exit.ShouldBe(2, string.Join(' ', arguments) + output + error);
                error.ShouldBeEmpty();
                AssertInvalidArguments(output, ScanMessage, "arguments");
                File.ReadAllBytes(profilePath).ShouldBe(originalProfile);
            }
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
            error.ShouldBeEmpty();

            foreach ((string attached, string masked) in new[]
                {
                    ("--token=--abc", "--ab***"),
                    ("--token:--abc", "--ab***"),
                    ("--token=-h", "***"),
                    ("--token:-h", "***"),
                })
            {
                (int tokenExit, string tokenOutput, string tokenError) = await InvokeAsync(store,
                    [attached, "config", "current"]);
                tokenExit.ShouldBe(0, tokenOutput + tokenError);
                tokenError.ShouldBeEmpty();
                using JsonDocument tokenDocument = JsonDocument.Parse(tokenOutput);
                tokenDocument.RootElement.GetProperty("token").GetString().ShouldBe(masked);
            }
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
                    new[] { "--help", "-h" }, new[] { "config", "profile", "add", "-h", "--help", "/?" },
                })
            {
                (int exit, string output, string error) = await InvokeAsync(store, arguments);
                exit.ShouldBe(0, string.Join(' ', arguments) + output + error);
                output.ShouldContain("Usage:");
                error.ShouldBeEmpty();
            }

            string[][] invalid =
            [
                ["operations", "", "--help"],
                ["describe", "", "-h"],
                ["send", "--payload", "{}", "--help"],
                ["query", "--payload", "{}", "-?"],
                ["operations", "sample", "--kind", "bad", "/?"],
                ["config", "set", "dev", "tenant", "--help"],
                ["config", "use", "--clear=false", "--help"],
                ["modules", "--url", "ftp://bad.example/", "--help"],
                ["modules", "--format", "xml", "--help"],
                ["config", "profile", "remove", "missing", "--help"],
                ["config", "use", "missing", "-h"],
                ["config", "set", "dev", "badfield", "x", "--help"],
                ["config", "profile", "add", "dev", "--help"],
                ["--help", "modules"],
                ["config", "--help", "set"],
            ];
            foreach (string[] arguments in invalid)
            {
                (int exit, string output, string error) = await InvokeAsync(store, arguments);
                exit.ShouldBe(2, string.Join(' ', arguments) + output + error);
                error.ShouldBeEmpty();
                output.ShouldNotContain("Usage:");
                AssertInvalidArguments(output, HelpMessage, "arguments");
            }

            (int httpExit, string httpOut, string httpError) = await InvokeAsync(store,
                ["mcp", "--transport", "http", "--help"]);
            httpExit.ShouldBe(2);
            httpOut.ShouldBeEmpty();
            AssertInvalidArguments(httpError, HelpMessage, "arguments");

            (int slashHttpExit, string slashHttpOut, string slashHttpError) = await InvokeAsync(store,
                ["mcp", "--transport", "http", "/h"]);
            slashHttpExit.ShouldBe(2);
            slashHttpOut.ShouldBeEmpty();
            AssertInvalidArguments(slashHttpError, HelpMessage, "arguments");

            (int mcpSettingsExit, string mcpSettingsOut, string mcpSettingsError) = await InvokeAsync(store,
                ["mcp", "--url", "ftp://bad.example/", "--help"]);
            mcpSettingsExit.ShouldBe(2);
            mcpSettingsOut.ShouldBeEmpty();
            AssertInvalidArguments(mcpSettingsError, HelpMessage, "arguments");

            (int mcpFormatExit, string mcpFormatOut, string mcpFormatError) = await InvokeAsync(store,
                ["mcp", "--format", "table", "--help"]);
            mcpFormatExit.ShouldBe(2);
            mcpFormatOut.ShouldBeEmpty();
            AssertInvalidArguments(mcpFormatError, HelpMessage, "arguments");

            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            (int literalExit, string literalOutput, string literalError) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "--", "--help"]);
            literalExit.ShouldBe(0, literalOutput + literalError);
            QueryCliHarness.AssertJson(literalOutput, """{"profile":"dev","field":"actor"}""");
            literalError.ShouldBeEmpty();
            store.Read().Profiles["dev"].Actor.ShouldBe("--help");

            (int dashExit, string dashOutput, string dashError) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "-"]);
            dashExit.ShouldBe(0, dashOutput + dashError);
            QueryCliHarness.AssertJson(dashOutput, """{"profile":"dev","field":"actor"}""");
            dashError.ShouldBeEmpty();
            store.Read().Profiles["dev"].Actor.ShouldBe("-");

            foreach (string value in new[] { "[suggest]", "[suggest:3]" })
            {
                (int settingExit, string settingOutput, string settingError) = await InvokeAsync(store,
                    ["config", "set", "dev", "actor", value]);
                settingExit.ShouldBe(0, settingOutput + settingError);
                settingError.ShouldBeEmpty();
                store.Read().Profiles["dev"].Actor.ShouldBe(value);
            }

            foreach (string value in new[] { "/h", "/?", "/h:x", "/?=x" })
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
            AssertErrorJson(error,
                """{"error":{"code":"unsupported_transport","message":"Only stdio transport is available; HTTP transport is planned for the next release."}}""");
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
                AssertInvalidArguments(malformedError, ScanMessage, "arguments");
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
            AssertInvalidArguments(malformedOutput, "Version must be requested alone.", "arguments");
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

            (int discoveryExit, string discovery, string discoveryError) = await InvokeAsync(store,
                ["operations", "missing", "--output", bad]);
            discoveryExit.ShouldBe(2);
            discoveryError.ShouldBeEmpty();
            AssertErrorJson(discovery,
                """{"error":{"code":"unknown_module","module":"missing","suggestions":["sample"]}}""");

            foreach (string[] arguments in new[]
                {
                    new[] { "config", "profile", "add", "new", "--url", "https://gateway.example/" },
                    new[] { "config", "profile", "remove", "dev" },
                    new[] { "config", "use", "dev" },
                    new[] { "config", "set", "dev", "actor", "operator" },
                })
            {
                (int exit, string output, string error) = await InvokeAsync(store, [.. arguments, "--output", bad]);
                exit.ShouldBe(2, string.Join(' ', arguments) + output);
                error.ShouldBeEmpty();
                using JsonDocument actual = JsonDocument.Parse(output);
                using JsonDocument expected = JsonDocument.Parse("""
                    {"error":{"code":"internal_error","message":"The result destination cannot be written; no request was sent."}}
                    """);
                JsonElement.DeepEquals(actual.RootElement, expected.RootElement).ShouldBeTrue(output);
                File.ReadAllBytes(store.ProfilePath).ShouldBe(before);
            }

            foreach ((string[] arguments, string message) in new[]
                {
                    (new[] { "config", "profile", "remove", "missing" }, "The named mcpcli profile does not exist."),
                    (new[] { "config", "use", "missing" }, "The named mcpcli profile does not exist."),
                    (new[] { "config", "profile", "add", "bad name", "--url", "https://gateway.example/" },
                        "Profile names must contain 1 to 64 ASCII letters, digits, underscores, or hyphens."),
                    (new[] { "config", "set", "dev", "allowTenantOverride", "bad" },
                        "allowTenantOverride must be true, false, 1, or 0."),
                    (new[] { "config", "set", "dev", "allowedExtensions", "bad key" },
                        "A profile has invalid allowed extension keys."),
                })
            {
                (int exit, string output, string error) = await InvokeAsync(store, [.. arguments, "--output", bad]);
                exit.ShouldBe(2);
                error.ShouldBeEmpty();
                AssertErrorJson(output, $$$"""{"error":{"code":"configuration_invalid","message":"{{{message}}}"}}""");
                File.ReadAllBytes(store.ProfilePath).ShouldBe(before);
            }

            File.WriteAllText(store.ProfilePath, "{");
            foreach (string[] arguments in new[]
                {
                    new[] { "config", "profile", "add", "new", "--url", "https://gateway.example/" },
                    new[] { "config", "use", "--clear" },
                })
            {
                (int exit, string output, string error) = await InvokeAsync(store, [.. arguments, "--output", bad]);
                exit.ShouldBe(2);
                error.ShouldBeEmpty();
                AssertErrorJson(output,
                    """{"error":{"code":"configuration_invalid","message":"The mcpcli profile document is malformed or has unknown or duplicate fields."}}""");
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
            (int exit, string output, string error) = await InvokeAsync(store, ["config", "current", "--output", target]);
            exit.ShouldBe(0, output + error);
            output.ShouldBeEmpty();
            error.ShouldBeEmpty();
            using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(target)))
            {
                document.RootElement.GetProperty("format").GetString().ShouldBe("json");
            }

            if (!OperatingSystem.IsWindows())
            {
                string link = Path.Combine(directory, "result-link");
                File.CreateSymbolicLink(link, target);
                (exit, output, error) = await InvokeAsync(store, ["config", "profile", "list", "--output", link]);
                exit.ShouldBe(0, output + error);
                output.ShouldBeEmpty();
                error.ShouldBeEmpty();
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

    /// <summary>An existing result file can be replaced when its directory cannot create new files.</summary>
    [Fact]
    public async Task ExistingFileWorksInUnwritableDirectoryThroughCliAsync()
    {
        if (OperatingSystem.IsWindows())
        {
            Assert.Skip("Unix file modes are required for this fixture.");
            return;
        }
        string directory = NewDirectory();
        string parent = Path.Combine(directory, "read-only-directory");
        Directory.CreateDirectory(parent);
        string target = Path.Combine(parent, "result.json");
        File.WriteAllText(target, "old result");
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            File.SetUnixFileMode(target, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            File.SetUnixFileMode(parent, UnixFileMode.UserRead | UnixFileMode.UserExecute);

            (int exit, string output, string error) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "x", "--output", target]);
            exit.ShouldBe(0, output + error);
            output.ShouldBeEmpty();
            error.ShouldBeEmpty();
            store.Read().Profiles["dev"].Actor.ShouldBe("x");
            using JsonDocument document = JsonDocument.Parse(File.ReadAllText(target));
            document.RootElement.GetProperty("profile").GetString().ShouldBe("dev");
            document.RootElement.GetProperty("field").GetString().ShouldBe("actor");
        }
        finally
        {
            File.SetUnixFileMode(parent, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Discovery results, including lint findings, use the selected file and retain their exit code.</summary>
    [Fact]
    public async Task DiscoveryResultsUseOutputFileAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            (string[] Arguments, Assembly[] Manifest, int Exit)[] cases =
            [
                (["modules"], SampleManifest, 0),
                (["operations", "sample"], SampleManifest, 0),
                (["describe", "sample.get-item"], SampleManifest, 0),
                (["describe", "lint-fixture.inspect-hollow", "--lint"], [typeof(global::Catalog.Lint.Contracts.Module).Assembly], 1),
            ];

            for (int index = 0; index < cases.Length; index++)
            {
                (string[] arguments, Assembly[] manifest, int expectedExit) = cases[index];
                (int baselineExit, string baselineOutput, string baselineError) = await InvokeAsync(store, arguments, () => manifest);
                baselineExit.ShouldBe(expectedExit);
                baselineError.ShouldBeEmpty();
                string target = Path.Combine(directory, $"result-{index}.json");
                (int exit, string output, string error) = await InvokeAsync(store,
                    [.. arguments, "--output", target], () => manifest);
                exit.ShouldBe(expectedExit, output + error);
                output.ShouldBeEmpty();
                error.ShouldBeEmpty();
                File.ReadAllText(target).ShouldBe(baselineOutput);
                using JsonDocument document = JsonDocument.Parse(File.ReadAllText(target));
                if (expectedExit == 1)
                {
                    document.RootElement.GetProperty("lintFindings").GetArrayLength().ShouldBeGreaterThan(0);
                }
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
            (int newExit, string newOutput, string newError) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "first", "--output", created]);
            newExit.ShouldBe(0, newOutput + newError);
            newOutput.ShouldBeEmpty();
            newError.ShouldBeEmpty();
            File.Exists(created).ShouldBeTrue();
            Directory.GetFiles(directory, ".mcpcli-probe-*").ShouldBeEmpty();
            Directory.GetFiles(Path.GetTempPath(), ".mcpcli-probe-*").ShouldBe(beforeTemp);

            (int existingExit, string existingOutput, string existingError) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "second", "--output", created]);
            existingExit.ShouldBe(0, existingOutput + existingError);
            existingOutput.ShouldBeEmpty();
            existingError.ShouldBeEmpty();
            Directory.GetFiles(directory, ".mcpcli-probe-*").ShouldBeEmpty();
            Directory.GetFiles(Path.GetTempPath(), ".mcpcli-probe-*").ShouldBe(beforeTemp);

            if (!OperatingSystem.IsWindows())
            {
                string link = Path.Combine(directory, "result-link");
                File.CreateSymbolicLink(link, created);
                (int linkExit, string linkOutput, string linkError) = await InvokeAsync(store,
                    ["config", "set", "dev", "actor", "third", "--output", link]);
                linkExit.ShouldBe(0, linkOutput + linkError);
                linkOutput.ShouldBeEmpty();
                linkError.ShouldBeEmpty();
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

            (int unknownExit, string unknown, string unknownError) = await harness.InvokeAsync(
                ["query", "missing.operation", "--payload", "{}", "--output", bad]);
            unknownExit.ShouldBe(2);
            QueryCliHarness.AssertDiagnostics(unknownError);
            AssertErrorJson(unknown,
                """{"error":{"code":"unknown_operation","operation":"missing.operation","suggestions":["lint-fixture.move-item","string-fixture.lookup","lint-fixture.inspect-item"]}}""");

            (int invalidExit, string invalid, string invalidError) = await harness.InvokeAsync(
                ["query", "string-fixture.list-items", "--payload", "{", "--output", bad]);
            invalidExit.ShouldBe(2);
            QueryCliHarness.AssertDiagnostics(invalidError);
            AssertErrorJson(invalid,
                """{"error":{"code":"validation_failed","operation":"string-fixture.list-items","violations":[{"path":"/","message":"The payload must be valid JSON without duplicate properties."}]}}""");

            (int badExit, string failed, string badError) = await harness.InvokeAsync(
                ["query", "string-fixture.list-items", "--payload", "{}", "--output", bad]);
            badExit.ShouldBe(2);
            QueryCliHarness.AssertDiagnostics(badError);
            AssertPreflightError(failed);
            harness.Calls.ShouldBe(0);

            string target = Path.Combine(directory, "query-result.json");
            File.WriteAllText(target, "old result");
            (int successExit, string successOutput, string successError) = await harness.InvokeAsync(
                ["query", "string-fixture.list-items", "--payload", "{}", "--format", "table", "--output", target]);
            successExit.ShouldBe(0, successOutput + successError);
            successOutput.ShouldBeEmpty();
            const string formatNote = "This result is emitted as JSON; no table view is defined.";
            string noteLine = formatNote + Environment.NewLine;
            successError.EndsWith(noteLine, StringComparison.Ordinal).ShouldBeTrue(successError);
            successError.Split(formatNote, StringSplitOptions.None).Length.ShouldBe(2);
            QueryCliHarness.AssertDiagnostics(successError[..^noteLine.Length]);
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
            (string[] Arguments, string Expected)[] cases =
            [
                (["query", "string-fixture.list-items", "--payload", "{}", "--page-size", "0"],
                    """{"error":{"code":"validation_failed","operation":"string-fixture.list-items","violations":[{"path":"/pageSize","message":"Page size must be between 1 and 200."}]}}"""),
                (["query", "string-fixture.list-items", "--payload", "{}", "--aggregate-id", "a/b"],
                    """{"error":{"code":"validation_failed","operation":"string-fixture.list-items","violations":[{"path":"/aggregateId","message":"The aggregate identifier does not match the module and Gateway rules."}]}}"""),
                (["send", "routing-fixture.renamed-aggregate", "--payload",
                    $$"""{"aggregate/~id":"{{QueryCliHarness.ItemId}}"}""", "--aggregate-id",
                    "01ARZ3NDEKTSV4RRFFQ69G5FAW", "--tenant", "session-tenant"],
                    """{"error":{"code":"validation_failed","operation":"routing-fixture.renamed-aggregate","violations":[{"path":"/aggregateId","message":"The explicit aggregate identifier disagrees with the payload."}]}}"""),
            ];

            foreach ((string[] arguments, string expected) in cases)
            {
                (int exit, string output, string error) = await harness.InvokeAsync([.. arguments, "--output", bad]);
                exit.ShouldBe(2, output + error);
                QueryCliHarness.AssertDiagnostics(error);
                AssertErrorJson(output, expected);
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
            AssertErrorJson(unknownOutput,
                """{"error":{"code":"unknown_operation","operation":"missing.operation","suggestions":["sample.create-item","sample.get-item","sample.rename-item"]}}""");

            (int invalidExit, string invalidOutput, string invalidError) = await InvokeAsync(store,
                ["send", "sample.create-item", "--payload", "{", "--url", "http://127.0.0.1:1/", "--output", bad]);
            invalidExit.ShouldBe(2);
            invalidError.ShouldBeEmpty();
            AssertErrorJson(invalidOutput,
                """{"error":{"code":"validation_failed","operation":"sample.create-item","violations":[{"path":"/","message":"The payload must be valid JSON without duplicate properties."}]}}""");

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
            error.ShouldBeEmpty();
            AssertPreflightError(output);
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
                (int exit, string output, string error) = await InvokeAsync(store,
                    ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--output", target]);
                exit.ShouldBe(2, target + output + error);
                error.ShouldBeEmpty();
                AssertPreflightError(output);
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
            deviceError.ShouldBeEmpty();

            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            (int mutationExit, string mutationOutput, string mutationError) = await InvokeAsync(store,
                ["config", "set", "dev", "actor", "device", "--output", "/dev/null"]);
            mutationExit.ShouldBe(0, mutationOutput + mutationError);
            mutationOutput.ShouldBeEmpty();
            mutationError.ShouldBeEmpty();
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
                pipeError.ShouldBeEmpty();
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
            (int exit, string output, string error) = await InvokeAsync(store,
                ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--output", fifo]);
            exit.ShouldBe(2, output + error);
            error.ShouldBeEmpty();
            AssertPreflightError(output);
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
                (int exit, string output, string error) = await InvokeAsync(store,
                    ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--output", target]);
                exit.ShouldBe(2, target + output + error);
                error.ShouldBeEmpty();
                AssertPreflightError(output);
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
            AssertPreflightError(output);
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
            AssertPreflightError(output);
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
        AssertInvalidArguments(output, ScanMessage, "arguments");
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

    /// <summary>A sharing conflict is refused before the profile or result file changes.</summary>
    [Fact]
    public async Task ExistingOutputSharingConflictPreventsProfileMutationAsync()
    {
        string directory = NewDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            byte[] profileBefore = File.ReadAllBytes(store.ProfilePath);
            string target = Path.Combine(directory, "locked-result.json");
            File.WriteAllText(target, "old result");

            using (new FileStream(target, FileMode.Open, FileAccess.ReadWrite, FileShare.None))
            {
                (int exit, string output, string error) = await InvokeAsync(store,
                    ["config", "set", "dev", "actor", "locked", "--output", target]);
                exit.ShouldBe(2, output + error);
                AssertPreflightError(output);
                error.ShouldBeEmpty();
                File.ReadAllBytes(store.ProfilePath).ShouldBe(profileBefore);
            }

            File.ReadAllText(target).ShouldBe("old result");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static void AssertInvalidArguments(string output, string message, string argument)
        => AssertErrorJson(output, JsonSerializer.Serialize(new
        {
            error = new { code = "invalid_arguments", message, argument },
        }));

    private static void AssertPreflightError(string output)
        => AssertErrorJson(output,
            """{"error":{"code":"internal_error","message":"The result destination cannot be written; no request was sent."}}""");

    private static void AssertErrorJson(string output, string expected)
    {
        using JsonDocument actualDocument = JsonDocument.Parse(output);
        using JsonDocument expectedDocument = JsonDocument.Parse(expected);
        JsonElement.DeepEquals(actualDocument.RootElement, expectedDocument.RootElement).ShouldBeTrue(output);
    }

    private static string NewDirectory()
    {
        string path = Path.Combine(Path.GetTempPath(), "mcpcli-output-contract-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }
}

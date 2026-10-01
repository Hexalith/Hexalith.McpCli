using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;
using ModelContextProtocol.Server;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Checks the CLI's profile verbs through the actual command parser.</summary>
public sealed class ConfigCommandTests
{
    private const string SuppliedToken = "supplied-secret-value";

    private const string StoredToken = "stored-secret-value";

    /// <summary>A profile can be added, selected, edited, listed, and removed without printing its secret.</summary>
    [Fact]
    public async Task ProfileCommandsRoundTripWithoutExposingTokenAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            (int addExit, string added, _) = await InvokeAsync(store, "config", "profile", "add", "dev",
                "--url", "https://gateway.example/", "--token", "secret-value");
            addExit.ShouldBe(0);
            added.ShouldNotContain("secret-value");

            (int useExit, string selected, _) = await InvokeAsync(store, "config", "use", "dev");
            useExit.ShouldBe(0);
            JsonDocument.Parse(selected).RootElement.GetProperty("activeProfile").GetString().ShouldBe("dev");

            (int setExit, _, _) = await InvokeAsync(store, "config", "set", "dev", "tenant", "acme");
            setExit.ShouldBe(0);
            (int currentExit, string current, _) = await InvokeAsync(store, "config", "current");
            currentExit.ShouldBe(0);
            current.ShouldContain("secr***");
            current.ShouldNotContain("secret-value");
            JsonDocument.Parse(current).RootElement.GetProperty("tenant").GetString().ShouldBe("acme");

            (int listExit, string listing, _) = await InvokeAsync(store, "config", "profile", "list");
            listExit.ShouldBe(0);
            listing.ShouldContain("secr***");
            listing.ShouldNotContain("secret-value");

            (int removeExit, _, _) = await InvokeAsync(store, "config", "profile", "remove", "dev");
            removeExit.ShouldBe(0);
            store.Read().Profiles.ShouldBeEmpty();
            store.Read().ActiveProfile.ShouldBeNull();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Profile selection uses the flag, environment, and active profile in that order.</summary>
    [Fact]
    public async Task CurrentUsesProfileSelectionPrecedenceAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("active", new ConnectionProfile(Tenant: "active-tenant"));
            store.Add("environment", new ConnectionProfile(Tenant: "environment-tenant"));
            store.Add("flag", new ConnectionProfile(Tenant: "flag-tenant"));
            store.Use("active");
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_PROFILE"] = "environment" };

            (int flagExit, string flagOutput, _) = await InvokeAsync(store, environment, null,
                "config", "current", "--profile", "flag");
            (int environmentExit, string environmentOutput, _) = await InvokeAsync(store, environment, null,
                "config", "current");
            (int activeExit, string activeOutput, _) = await InvokeAsync(store, new Dictionary<string, string?>(), null,
                "config", "current");

            flagExit.ShouldBe(0);
            environmentExit.ShouldBe(0);
            activeExit.ShouldBe(0);
            AssertCurrent(flagOutput, "flag", "flag-tenant", "flag");
            AssertCurrent(environmentOutput, "environment", "environment-tenant", "EVENTSTORE_PROFILE");
            AssertCurrent(activeOutput, "active", "active-tenant", "activeProfile");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Every supported environment setting flows through bootstrap with its exact source.</summary>
    [Fact]
    public async Task CurrentResolvesEverySupportedEnvironmentSettingAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("environment", new ConnectionProfile(
                "https://profile.example/", "profile-token", "table", "profile-tenant", "profile-actor", false));
            var environment = new Dictionary<string, string?>
            {
                ["EVENTSTORE_PROFILE"] = "environment",
                ["EVENTSTORE_URL"] = "https://environment.example/",
                ["EVENTSTORE_TOKEN"] = "environment-token",
                ["EVENTSTORE_TENANT"] = "environment-tenant",
                ["EVENTSTORE_ACTOR"] = "environment-actor",
                ["EVENTSTORE_ALLOW_TENANT_OVERRIDE"] = "true",
                ["EVENTSTORE_FORMAT"] = "json",
                ["EVENTSTORE_READ_ONLY"] = "true",
                ["EVENTSTORE_STRICT"] = "true",
            };

            (int exit, string output, string error) = await InvokeAsync(store, environment, null,
                "config", "current");

            exit.ShouldBe(0);
            error.ShouldBeEmpty();
            output.ShouldNotContain("environment-token");
            JsonElement current = JsonDocument.Parse(output).RootElement;
            current.GetProperty("profile").GetString().ShouldBe("environment");
            current.GetProperty("url").GetString().ShouldBe("https://environment.example/");
            current.GetProperty("token").GetString().ShouldBe("envi***");
            current.GetProperty("tenant").GetString().ShouldBe("environment-tenant");
            current.GetProperty("actor").GetString().ShouldBe("environment-actor");
            current.GetProperty("allowTenantOverride").GetBoolean().ShouldBeTrue();
            current.GetProperty("format").GetString().ShouldBe("json");
            current.GetProperty("readOnly").GetBoolean().ShouldBeTrue();
            current.GetProperty("strict").GetBoolean().ShouldBeTrue();
            current.GetProperty("allowedExtensions").GetArrayLength().ShouldBe(0);
            JsonElement sources = current.GetProperty("sources");
            foreach (string name in environment.Keys)
            {
                string field = name switch
                {
                    "EVENTSTORE_PROFILE" => "profile",
                    "EVENTSTORE_URL" => "url",
                    "EVENTSTORE_TOKEN" => "token",
                    "EVENTSTORE_TENANT" => "tenant",
                    "EVENTSTORE_ACTOR" => "actor",
                    "EVENTSTORE_ALLOW_TENANT_OVERRIDE" => "allowTenantOverride",
                    "EVENTSTORE_FORMAT" => "format",
                    "EVENTSTORE_READ_ONLY" => "readOnly",
                    _ => "strict",
                };
                sources.GetProperty(field).GetString().ShouldBe(name);
            }

            sources.GetProperty("allowedExtensions").GetString().ShouldBe("default");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The executable uses the production environment reader when resolving current settings.</summary>
    [Fact]
    public async Task CurrentExecutableReadsProcessEnvironmentAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
                RedirectStandardError = true,
                RedirectStandardOutput = true,
                UseShellExecute = false,
            };
            foreach (string name in startInfo.Environment.Keys
                .Where(name => name.StartsWith("EVENTSTORE_", StringComparison.Ordinal)).ToArray())
            {
                startInfo.Environment.Remove(name);
            }

            startInfo.Environment["HOME"] = directory;
            startInfo.Environment["USERPROFILE"] = directory;
            startInfo.Environment["EVENTSTORE_TENANT"] = "process-tenant";
            startInfo.Environment["EVENTSTORE_READ_ONLY"] = "true";
            startInfo.ArgumentList.Add(typeof(CliRunner).Assembly.Location);
            startInfo.ArgumentList.Add("config");
            startInfo.ArgumentList.Add("current");

            using Process process = Process.Start(startInfo).ShouldNotBeNull();
            Task<string> output = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
            Task<string> error = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
            await process.WaitForExitAsync(TestContext.Current.CancellationToken);

            process.ExitCode.ShouldBe(0);
            (await error).ShouldBeEmpty();
            JsonElement current = JsonDocument.Parse(await output).RootElement;
            current.GetProperty("tenant").GetString().ShouldBe("process-tenant");
            current.GetProperty("readOnly").GetBoolean().ShouldBeTrue();
            JsonElement sources = current.GetProperty("sources");
            sources.GetProperty("tenant").GetString().ShouldBe("EVENTSTORE_TENANT");
            sources.GetProperty("readOnly").GetString().ShouldBe("EVENTSTORE_READ_ONLY");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The executable never expands an <c>@</c>-prefixed token as a response file or echoes it.</summary>
    [Fact]
    public async Task ExecutableStoresAtPrefixedTokenVerbatimAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            const string token = "@s3cretTokValue";
            var startInfo = new ProcessStartInfo
            {
                FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
                RedirectStandardError = true,
                RedirectStandardOutput = true,
                UseShellExecute = false,
            };
            foreach (string name in startInfo.Environment.Keys
                .Where(name => name.StartsWith("EVENTSTORE_", StringComparison.Ordinal)).ToArray())
            {
                startInfo.Environment.Remove(name);
            }

            startInfo.Environment["HOME"] = directory;
            startInfo.Environment["USERPROFILE"] = directory;
            startInfo.ArgumentList.Add(typeof(CliRunner).Assembly.Location);
            foreach (string argument in new[]
                { "config", "profile", "add", "dev", "--url", "https://gateway.example/", "--token", token })
            {
                startInfo.ArgumentList.Add(argument);
            }

            using Process process = Process.Start(startInfo).ShouldNotBeNull();
            Task<string> output = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
            Task<string> error = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
            await process.WaitForExitAsync(TestContext.Current.CancellationToken);

            string standardOutput = await output;
            string standardError = await error;
            process.ExitCode.ShouldBe(0, standardOutput + standardError);
            AssertNoSecret(standardOutput, standardError, token, token[1..], "Response file");
            new ProfileStore(Path.Combine(directory, ".eventstore", "mcpcli.json")).Read()
                .Profiles["dev"].Token.ShouldBe(token);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Bare boolean flags are explicit true values and the current document is complete.</summary>
    [Fact]
    public async Task CurrentBindsBareFlagsAndEmitsAllValuesAndSourcesAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "current", "--allow-tenant-override", "--read-only", "--strict");

            exit.ShouldBe(0);
            error.ShouldBeEmpty();
            JsonElement current = JsonDocument.Parse(output).RootElement;
            current.GetProperty("profile").ValueKind.ShouldBe(JsonValueKind.Null);
            current.GetProperty("url").ValueKind.ShouldBe(JsonValueKind.Null);
            current.GetProperty("token").ValueKind.ShouldBe(JsonValueKind.Null);
            current.GetProperty("tenant").ValueKind.ShouldBe(JsonValueKind.Null);
            current.GetProperty("actor").ValueKind.ShouldBe(JsonValueKind.Null);
            current.GetProperty("allowTenantOverride").GetBoolean().ShouldBeTrue();
            current.GetProperty("allowedExtensions").GetArrayLength().ShouldBe(0);
            current.GetProperty("format").GetString().ShouldBe("json");
            current.GetProperty("output").ValueKind.ShouldBe(JsonValueKind.Null);
            current.GetProperty("readOnly").GetBoolean().ShouldBeTrue();
            current.GetProperty("strict").GetBoolean().ShouldBeTrue();
            JsonElement sources = current.GetProperty("sources");
            sources.GetProperty("allowTenantOverride").GetString().ShouldBe("flag");
            sources.GetProperty("readOnly").GetString().ShouldBe("flag");
            sources.GetProperty("strict").GetString().ShouldBe("flag");
            sources.GetProperty("output").GetString().ShouldBe("default");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Explicit false boolean flags override inherited true values.</summary>
    [Fact]
    public async Task CurrentFalseFlagsOverrideInheritedTrueValuesAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile(AllowTenantOverride: true));
            store.Use("dev");
            var environment = new Dictionary<string, string?>
            {
                ["EVENTSTORE_READ_ONLY"] = "true",
                ["EVENTSTORE_STRICT"] = "true",
            };

            (int exit, string output, string error) = await InvokeAsync(store, environment, null,
                "config", "current", "--allow-tenant-override", "false", "--read-only", "false", "--strict", "false");

            exit.ShouldBe(0);
            error.ShouldBeEmpty();
            JsonElement current = JsonDocument.Parse(output).RootElement;
            current.GetProperty("allowTenantOverride").GetBoolean().ShouldBeFalse();
            current.GetProperty("readOnly").GetBoolean().ShouldBeFalse();
            current.GetProperty("strict").GetBoolean().ShouldBeFalse();
            JsonElement sources = current.GetProperty("sources");
            sources.GetProperty("allowTenantOverride").GetString().ShouldBe("flag");
            sources.GetProperty("readOnly").GetString().ShouldBe("flag");
            sources.GetProperty("strict").GetString().ShouldBe("flag");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Allowed extension output is deterministic regardless of stored order.</summary>
    [Fact]
    public async Task CurrentOrdersAllowedExtensionsAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile(AllowedExtensions: ["zeta", "Alpha", "beta"]));
            store.Use("dev");

            (int exit, string output, string error) = await InvokeAsync(store, "config", "current");

            exit.ShouldBe(0);
            error.ShouldBeEmpty();
            JsonElement extensions = JsonDocument.Parse(output).RootElement.GetProperty("allowedExtensions");
            extensions.EnumerateArray().Select(item => item.GetString()).ShouldBe(["Alpha", "beta", "zeta"]);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Current can report and use its explicit output path.</summary>
    [Fact]
    public async Task CurrentIncludesOutputSettingAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string resultPath = Path.Combine(directory, "current.json");

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "current", "--output", resultPath);

            exit.ShouldBe(0);
            output.ShouldBeEmpty();
            error.ShouldBeEmpty();
            JsonElement current = JsonDocument.Parse(File.ReadAllText(resultPath)).RootElement;
            current.GetProperty("output").GetString().ShouldBe(resultPath);
            current.GetProperty("sources").GetProperty("output").GetString().ShouldBe("flag");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Table output includes every resolved field, all sources, and only the masked token.</summary>
    [Fact]
    public async Task CurrentTableIncludesEveryValueAndSourceWithoutRawTokenAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            const string token = "secret-value";
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile(
                "https://gateway.example/", token, "json", "acme", "operator", true, ["trace-id"]));
            store.Use("dev");
            var environment = new Dictionary<string, string?>
            {
                ["EVENTSTORE_READ_ONLY"] = "true",
                ["EVENTSTORE_STRICT"] = "true",
            };

            (int exit, string output, string error) = await InvokeAsync(store, environment, null,
                "config", "current", "--format", "table");

            exit.ShouldBe(0);
            error.ShouldBeEmpty();
            output.ShouldContain("secr***");
            output.ShouldNotContain(token);
            string[] rows = output.Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries);
            rows[0].ShouldBe("FIELD\tVALUE");
            rows.Length.ShouldBe(13);
            rows.Skip(1).ShouldAllBe(row => row.Count(character => character == '\t') == 1);
            rows.Skip(1).Select(row => row[..row.IndexOf('\t')]).ShouldBe([
                "profile", "url", "token", "tenant", "actor", "allowTenantOverride", "allowedExtensions",
                "format", "output", "readOnly", "strict", "sources",
            ]);
            rows.ShouldContain("profile\t\"dev\"");
            rows.ShouldContain("url\t\"https://gateway.example/\"");
            rows.ShouldContain("token\t\"secr***\"");
            rows.ShouldContain("tenant\t\"acme\"");
            rows.ShouldContain("actor\t\"operator\"");
            rows.ShouldContain("allowTenantOverride\ttrue");
            rows.ShouldContain("allowedExtensions\t[\"trace-id\"]");
            rows.ShouldContain("format\t\"table\"");
            rows.ShouldContain("output\tnull");
            rows.ShouldContain("readOnly\ttrue");
            rows.ShouldContain("strict\ttrue");
            string sourceRow = rows.Single(row => row.StartsWith("sources\t", StringComparison.Ordinal));
            JsonElement sources = JsonDocument.Parse(sourceRow["sources\t".Length..]).RootElement;
            sources.EnumerateObject().Select(property => property.Name).ShouldBe([
                "profile", "url", "token", "tenant", "actor", "format", "allowTenantOverride", "readOnly",
                "strict", "output", "allowedExtensions",
            ], ignoreOrder: true);
            sources.GetProperty("profile").GetString().ShouldBe("activeProfile");
            sources.GetProperty("format").GetString().ShouldBe("flag");
            sources.GetProperty("output").GetString().ShouldBe("default");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Whitespace-only output is rejected before any file can be created.</summary>
    [Fact]
    public async Task CurrentRejectsWhitespaceOutputWithoutWritingAsync()
    {
        string directory = TemporaryDirectory();
        string originalDirectory = Environment.CurrentDirectory;
        try
        {
            Environment.CurrentDirectory = directory;
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "current", "--output", " ");

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            JsonElement document = JsonDocument.Parse(output).RootElement;
            document.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
            JsonElement configurationError = document.GetProperty("error");
            configurationError.GetProperty("code").GetString().ShouldBe("configuration_invalid");
            configurationError.GetProperty("message").GetString().ShouldNotBeNull().ShouldContain("flag");
            Directory.EnumerateFileSystemEntries(directory).ShouldBeEmpty();
        }
        finally
        {
            Environment.CurrentDirectory = originalDirectory;
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Known malformed sources produce only the canonical configuration error.</summary>
    [Theory]
    [InlineData("EVENTSTORE_URL", "not-a-url")]
    [InlineData("EVENTSTORE_FORMAT", "yaml")]
    [InlineData("EVENTSTORE_TOKEN", " ")]
    [InlineData("EVENTSTORE_TENANT", " ")]
    [InlineData("EVENTSTORE_ACTOR", " ")]
    [InlineData("EVENTSTORE_READ_ONLY", "yes")]
    public async Task CurrentNamesInvalidEnvironmentSourceAsync(string name, string value)
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var environment = new Dictionary<string, string?> { [name] = value };

            (int exit, string output, string error) = await InvokeAsync(store, environment, null,
                "config", "current");

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            JsonElement document = JsonDocument.Parse(output).RootElement;
            document.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
            JsonElement configurationError = document.GetProperty("error");
            configurationError.GetProperty("code").GetString().ShouldBe("configuration_invalid");
            configurationError.GetProperty("message").GetString().ShouldNotBeNull().ShouldContain(name);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A missing environment-selected profile returns the canonical source-specific error.</summary>
    [Fact]
    public async Task CurrentNamesMissingEnvironmentProfileSourceAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_PROFILE"] = "missing" };

            (int exit, string output, string error) = await InvokeAsync(store, environment, null,
                "config", "current");

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            JsonElement document = JsonDocument.Parse(output).RootElement;
            document.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
            JsonElement configurationError = document.GetProperty("error");
            configurationError.GetProperty("code").GetString().ShouldBe("configuration_invalid");
            configurationError.GetProperty("message").GetString()
                .ShouldBe("The selected profile 'missing' from EVENTSTORE_PROFILE does not exist.");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A missing flag-selected profile returns the canonical flag-source error.</summary>
    [Fact]
    public async Task CurrentNamesMissingFlagProfileSourceAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "current", "--profile", "missing");

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            JsonElement document = JsonDocument.Parse(output).RootElement;
            document.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
            JsonElement configurationError = document.GetProperty("error");
            configurationError.GetProperty("code").GetString().ShouldBe("configuration_invalid");
            configurationError.GetProperty("message").GetString()
                .ShouldBe("The selected profile 'missing' from flag does not exist.");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>An invalid stored allowlist returns the canonical profile-source error.</summary>
    [Fact]
    public async Task CurrentNamesInvalidProfileAllowlistSourceAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            File.WriteAllText(store.ProfilePath, """
                {"version":1,"activeProfile":"dev","profiles":{"dev":{"allowedExtensions":["../unsafe"]}}}
                """);

            (int exit, string output, string error) = await InvokeAsync(store, "config", "current");

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            JsonElement document = JsonDocument.Parse(output).RootElement;
            document.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
            JsonElement configurationError = document.GetProperty("error");
            configurationError.GetProperty("code").GetString().ShouldBe("configuration_invalid");
            configurationError.GetProperty("message").GetString().ShouldNotBeNull()
                .ShouldStartWith("Invalid mcpcli profile file:");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Inspection ignores the admin profile path and environment namespace.</summary>
    [Fact]
    public async Task CurrentDoesNotReadAdminConfigurationAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            Directory.CreateDirectory(directory);
            const string adminSecret = "admin-secret-value";
            File.WriteAllText(Path.Combine(directory, "profiles.json"), JsonSerializer.Serialize(new
            {
                activeProfile = "admin",
                profiles = new { admin = new { url = "https://admin.example/", token = adminSecret } },
            }));
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var environment = new Dictionary<string, string?>
            {
                ["EVENTSTORE_ADMIN_URL"] = "https://admin-environment.example/",
                ["EVENTSTORE_ADMIN_TOKEN"] = adminSecret,
            };

            (int exit, string output, string error) = await InvokeAsync(store, environment, null,
                "config", "current");

            exit.ShouldBe(0);
            output.ShouldNotContain(adminSecret);
            error.ShouldNotContain(adminSecret);
            JsonElement current = JsonDocument.Parse(output).RootElement;
            current.GetProperty("profile").ValueKind.ShouldBe(JsonValueKind.Null);
            current.GetProperty("url").ValueKind.ShouldBe(JsonValueKind.Null);
            current.GetProperty("token").ValueKind.ShouldBe(JsonValueKind.Null);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Inspection is offline and never evaluates the Contracts manifest.</summary>
    [Fact]
    public async Task CurrentWithoutUrlDoesNotBuildCatalogAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            int manifestReads = 0;
            IReadOnlyList<Assembly> ThrowingManifest()
            {
                manifestReads++;
                throw new InvalidOperationException("The manifest must remain lazy.");
            }

            (int exit, string output, string error) = await InvokeAsync(store,
                new Dictionary<string, string?>(), ThrowingManifest, "config", "current");

            exit.ShouldBe(0);
            error.ShouldBeEmpty();
            JsonDocument.Parse(output).RootElement.GetProperty("url").ValueKind.ShouldBe(JsonValueKind.Null);
            manifestReads.ShouldBe(0);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Read-only settings resolved by the MCP verb remove the command tool from advertisement.</summary>
    [Fact]
    public async Task McpReadOnlyOmitsSendCommandAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            int hostRuns = 0;
            Task<int> InspectMcpAsync(IHost host, CancellationToken cancellationToken)
            {
                cancellationToken.ThrowIfCancellationRequested();
                hostRuns++;
                host.Services.GetRequiredService<ResolvedSettings>().ReadOnly.ShouldBeTrue();
                McpServerPrimitiveCollection<McpServerTool> tools = host.Services
                    .GetRequiredService<IOptions<McpServerOptions>>().Value.ToolCollection.ShouldNotBeNull();
                tools.Select(tool => tool.ProtocolTool.Name).ShouldNotContain("send_command");
                tools.Select(tool => tool.ProtocolTool.Name).ShouldContain("run_query");
                return Task.FromResult(0);
            }

            int exit = await new CliRunner(
                store,
                () => [typeof(CreateItemCommand).Assembly],
                _ => null,
                InspectMcpAsync)
                .Parse(["mcp", "--read-only"])
                .InvokeAsync(cancellationToken: TestContext.Current.CancellationToken);

            exit.ShouldBe(0);
            hostRuns.ShouldBe(1);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>MCP configuration failures emit only a canonical stderr document and never start the host.</summary>
    [Fact]
    public async Task McpNamesInvalidEnvironmentSourceOnStandardErrorAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_URL"] = "not-a-url" };
            int hostRuns = 0;
            Task<int> FailIfRunAsync(IHost _, CancellationToken __)
            {
                hostRuns++;
                return Task.FromException<int>(new InvalidOperationException("MCP must not start."));
            }

            (int exit, string output, string error) = await InvokeAsync(
                store, environment, () => [typeof(CreateItemCommand).Assembly], FailIfRunAsync, "mcp");

            exit.ShouldBe(2);
            output.ShouldBeEmpty();
            hostRuns.ShouldBe(0);
            JsonElement document = JsonDocument.Parse(error).RootElement;
            document.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
            JsonElement configurationError = document.GetProperty("error");
            configurationError.GetProperty("code").GetString().ShouldBe("configuration_invalid");
            configurationError.GetProperty("message").GetString().ShouldNotBeNull()
                .ShouldContain("EVENTSTORE_URL");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Explicit MCP format and output errors are deterministic before settings resolution.</summary>
    [Fact]
    public async Task McpValidatesExplicitOptionsBeforeSettingsResolutionAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var invalidEnvironment = new Dictionary<string, string?> { ["EVENTSTORE_URL"] = "not-a-url" };

            (int formatExit, string formatOutput, string formatError) = await InvokeAsync(
                store, invalidEnvironment, null, "mcp", "--format", "table", "--output", " ");
            formatExit.ShouldBe(2);
            formatOutput.ShouldBeEmpty();
            JsonElement formatDocument = JsonDocument.Parse(formatError).RootElement.GetProperty("error");
            formatDocument.GetProperty("code").GetString().ShouldBe("invalid_arguments");
            formatDocument.GetProperty("argument").GetString().ShouldBe("format");
            formatDocument.GetProperty("message").GetString().ShouldNotBeNull().ShouldNotContain("EVENTSTORE_URL");

            (int outputExit, string output, string outputError) = await InvokeAsync(
                store, invalidEnvironment, null, "mcp", "--output", " ");
            outputExit.ShouldBe(2);
            output.ShouldBeEmpty();
            JsonElement outputDocument = JsonDocument.Parse(outputError).RootElement.GetProperty("error");
            outputDocument.GetProperty("code").GetString().ShouldBe("invalid_arguments");
            outputDocument.GetProperty("argument").GetString().ShouldBe("output");
            outputDocument.GetProperty("message").GetString().ShouldNotBeNull().ShouldNotContain("EVENTSTORE_URL");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The executable version path succeeds before settings, host, or Catalog construction.</summary>
    [Fact]
    public async Task VersionUsesEarlyOfflineEntryPointAsync()
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
        };
        startInfo.ArgumentList.Add(typeof(CliRunner).Assembly.Location);
        startInfo.ArgumentList.Add("--version");
        startInfo.Environment["EVENTSTORE_READ_ONLY"] = "yes";
        startInfo.Environment["EVENTSTORE_URL"] = "not-a-url";

        using Process process = Process.Start(startInfo).ShouldNotBeNull();
        Task<string> output = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
        Task<string> error = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
        await process.WaitForExitAsync(TestContext.Current.CancellationToken);

        process.ExitCode.ShouldBe(0);
        (await output).Trim().ShouldNotBeEmpty();
        (await error).ShouldBeEmpty();
    }

    /// <summary>Long and short tokens never appear raw on either CLI channel.</summary>
    [Theory]
    [InlineData("secret-value", "secr***")]
    [InlineData("tiny", "***")]
    public async Task CurrentNeverExposesRawTokenAsync(string token, string masked)
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_TOKEN"] = token };

            (int exit, string output, string error) = await InvokeAsync(store, environment, null,
                "config", "current");

            exit.ShouldBe(0);
            output.ShouldContain(masked);
            output.ShouldNotContain(token);
            error.ShouldNotContain(token);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Invalid profile input returns the shared error document and leaves no target.</summary>
    [Fact]
    public async Task InvalidProfileAddDoesNotWriteAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            (int exit, string output, _) = await InvokeAsync(store, "config", "profile", "add", "bad name",
                "--url", "https://gateway.example/");
            exit.ShouldBe(2);
            JsonDocument.Parse(output).RootElement.GetProperty("error").GetProperty("code").GetString()
                .ShouldBe("configuration_invalid");
            File.Exists(store.ProfilePath).ShouldBeFalse();
        }
        finally
        {
            if (Directory.Exists(directory))
            {
                Directory.Delete(directory, recursive: true);
            }
        }
    }

    /// <summary>The first add creates a private version-1 file with only the supplied fields and leaves the admin file alone.</summary>
    [Fact]
    public async Task FirstAddStoresOnlySuppliedFieldsAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            const string token = "first-secret-value";
            string adminPath = Path.Combine(directory, "profiles.json");
            File.WriteAllText(adminPath, "{\"activeProfile\":\"dev\",\"profiles\":{}}");
            byte[] adminBytes = File.ReadAllBytes(adminPath);
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "profile", "add", "dev", "--url", "https://gateway.example/", "--token", token);

            exit.ShouldBe(0);
            AssertNoSecret(output, error, token);
            JsonDocument.Parse(output).RootElement.GetProperty("name").GetString().ShouldBe("dev");
            using JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath));
            written.RootElement.GetProperty("version").GetInt32().ShouldBe(1);
            written.RootElement.TryGetProperty("activeProfile", out _).ShouldBeFalse();
            JsonElement profile = written.RootElement.GetProperty("profiles").GetProperty("dev");
            profile.EnumerateObject().Select(property => property.Name).ShouldBe(["url", "token"]);
            profile.GetProperty("url").GetString().ShouldBe("https://gateway.example/");
            profile.GetProperty("token").GetString().ShouldBe(token);
            File.ReadAllBytes(adminPath).ShouldBe(adminBytes);
            if (!OperatingSystem.IsWindows())
            {
                File.GetUnixFileMode(store.ProfilePath).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>An explicit format is stored, while the presentation format never leaks from the environment.</summary>
    [Fact]
    public async Task AddStoresOnlyExplicitFormatAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_FORMAT"] = "table" };

            (int implicitExit, _, _) = await InvokeAsync(store, environment, null,
                "config", "profile", "add", "implicit", "--url", "https://gateway.example/");
            (int explicitExit, _, _) = await InvokeAsync(store,
                "config", "profile", "add", "explicit", "--url", "https://gateway.example/", "--format", "table");

            implicitExit.ShouldBe(0);
            explicitExit.ShouldBe(0);
            ProfileSnapshot snapshot = store.Read();
            snapshot.Profiles["implicit"].Format.ShouldBeNull();
            snapshot.Profiles["implicit"].Token.ShouldBeNull();
            snapshot.Profiles["explicit"].Format.ShouldBe("table");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Adding the profile that a missing environment selection names creates it.</summary>
    [Fact]
    public async Task AddCreatesMissingSelectedProfileAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            (int exit, string output, _) = await InvokeAsync(store,
                new Dictionary<string, string?> { ["EVENTSTORE_PROFILE"] = "staging" }, null,
                "config", "profile", "add", "staging", "--url", "https://staging.example/");

            exit.ShouldBe(0, output);
            store.Read().Profiles["staging"].Url.ShouldBe("https://staging.example/");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A selected profile that never exists blocks none of the management verbs.</summary>
    /// <param name="useEnvironment">Whether the missing profile is selected by environment rather than flag.</param>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ManagementVerbsIgnoreMissingSelectionAsync(bool useEnvironment)
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            Dictionary<string, string?> environment = useEnvironment
                ? new() { ["EVENTSTORE_PROFILE"] = "ghost" }
                : [];
            string[] selection = useEnvironment ? [] : ["--profile", "ghost"];
            string[][] verbs =
            [
                ["config", "profile", "add", "staging", "--url", "https://staging.example/"],
                ["config", "profile", "list"],
                ["config", "use", "staging"],
                ["config", "set", "staging", "tenant", "acme"],
                ["config", "use", "--clear"],
                ["config", "profile", "remove", "staging"],
            ];

            foreach (string[] verb in verbs)
            {
                (int exit, string output, _) = await InvokeAsync(store, environment, null, [.. verb, .. selection]);
                exit.ShouldBe(0, string.Join(' ', verb) + ": " + output);
            }

            ProfileSnapshot snapshot = store.Read();
            snapshot.Profiles.ContainsKey("staging").ShouldBeFalse();
            snapshot.Profiles.ContainsKey("ghost").ShouldBeFalse();
            snapshot.ActiveProfile.ShouldBeNull();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A token beginning with <c>@</c> is never expanded as a response file or echoed on either channel.</summary>
    [Fact]
    public async Task AtPrefixedTokenIsNeverExpandedOrEchoedAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            const string token = "@s3cretTokValue";
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "profile", "add", "dev", "--url", "https://gateway.example/", "--token", token);

            exit.ShouldBe(0, output + error);
            AssertNoSecret(output, error, token, token[1..]);
            store.Read().Profiles["dev"].Token.ShouldBe(token);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>List is sorted and masked; use selects and clears the active profile.</summary>
    [Fact]
    public async Task ListUseAndClearMaskEveryTokenAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            const string devToken = "dev-secret-value";
            const string prodToken = "prod-secret-value";
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            (int prodExit, string prodOutput, string prodError) = await InvokeAsync(store,
                "config", "profile", "add", "prod", "--url", "https://prod.example/", "--token", prodToken);
            (int devExit, string devOutput, string devError) = await InvokeAsync(store,
                "config", "profile", "add", "dev", "--url", "https://dev.example/", "--token", devToken);
            prodExit.ShouldBe(0);
            devExit.ShouldBe(0);
            AssertNoSecret(prodOutput + devOutput, prodError + devError, devToken, prodToken);

            (int listExit, string listing, string listError) = await InvokeAsync(store, "config", "profile", "list");
            listExit.ShouldBe(0);
            AssertNoSecret(listing, listError, devToken, prodToken);
            JsonElement document = JsonDocument.Parse(listing).RootElement;
            document.GetProperty("activeProfile").ValueKind.ShouldBe(JsonValueKind.Null);
            JsonElement[] profiles = [.. document.GetProperty("profiles").EnumerateArray()];
            profiles.Select(profile => profile.GetProperty("name").GetString()).ShouldBe(["dev", "prod"]);
            profiles[0].GetProperty("token").GetString().ShouldBe(ProfileStore.MaskToken(devToken));
            profiles[1].GetProperty("token").GetString().ShouldBe(ProfileStore.MaskToken(prodToken));

            (int useExit, string selected, string useError) = await InvokeAsync(store, "config", "use", "dev");
            useExit.ShouldBe(0);
            AssertNoSecret(selected, useError, devToken, prodToken);
            JsonDocument.Parse(selected).RootElement.GetProperty("activeProfile").GetString().ShouldBe("dev");
            store.Read().ActiveProfile.ShouldBe("dev");

            (int tableExit, string table, string tableError) = await InvokeAsync(store,
                "config", "profile", "list", "--format", "table");
            tableExit.ShouldBe(0);
            AssertNoSecret(table, tableError, devToken, prodToken);
            table.ShouldStartWith("FIELD\tVALUE");

            (int clearExit, string cleared, string clearError) = await InvokeAsync(store, "config", "use", "--clear");
            clearExit.ShouldBe(0);
            AssertNoSecret(cleared, clearError, devToken, prodToken);
            JsonDocument.Parse(cleared).RootElement.GetProperty("activeProfile").ValueKind.ShouldBe(JsonValueKind.Null);
            store.Read().ActiveProfile.ShouldBeNull();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Management output uses the flag, environment, or JSON default, never the active profile's format.</summary>
    [Fact]
    public async Task ManagementOutputIgnoresActiveProfileFormatAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", Format: "table"));
            store.Use("dev");

            (int listExit, string listing, _) = await InvokeAsync(store, "config", "profile", "list");
            (int useExit, string selected, _) = await InvokeAsync(store, "config", "use", "dev");
            (int environmentExit, string environmentListing, _) = await InvokeAsync(store,
                new Dictionary<string, string?> { ["EVENTSTORE_FORMAT"] = "table" }, null, "config", "profile", "list");

            listExit.ShouldBe(0);
            useExit.ShouldBe(0);
            environmentExit.ShouldBe(0);
            JsonDocument.Parse(listing).RootElement.GetProperty("activeProfile").GetString().ShouldBe("dev");
            JsonDocument.Parse(selected).RootElement.GetProperty("activeProfile").GetString().ShouldBe("dev");
            environmentListing.ShouldStartWith("FIELD\tVALUE");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Gets invalid profile-management inputs that must fail as configuration errors.</summary>
    public static TheoryData<string[], bool> InvalidManagementInputs
    {
        get
        {
            string[][] inputs =
            [
                ["config", "profile", "add", "bad name", "--url", "https://gateway.example/", "--token", SuppliedToken],
                ["config", "profile", "add", "", "--url", "https://gateway.example/", "--token", SuppliedToken],
                ["config", "profile", "add", new string('a', 65), "--url", "https://gateway.example/", "--token", SuppliedToken],
                ["config", "profile", "add", "dev", "--url", "ftp://x", "--token", SuppliedToken],
                ["config", "profile", "add", "dev", "--url", "not-a-url", "--token", SuppliedToken],
                ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--format", "xml", "--token", SuppliedToken],
                ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--token", " "],
                ["config", "use", "missing", "--token", SuppliedToken],
                ["config", "use", "bad name"],
                ["config", "set", "dev", "colour", "red", "--token", SuppliedToken],
                ["config", "set", "dev", "Tenant", "acme"],
                ["config", "set", "dev", "format", "json"],
                ["config", "set", "dev", "token", SuppliedToken],
                ["config", "set", "dev", "allowTenantOverride", "yes"],
                ["config", "set", "dev", "tenant", " "],
                ["config", "set", "dev", "tenant", ""],
                ["config", "set", "dev", "actor", ""],
                ["config", "set", "dev", "actor", " "],
                ["config", "set", "dev", "allowedExtensions", "a,A"],
                ["config", "set", "dev", "allowedExtensions", "a,"],
                ["config", "set", "dev", "allowedExtensions", "a, b"],
                ["config", "set", "dev", "allowedExtensions", "a ,b"],
                ["config", "set", "missing", "tenant", "x", "--token", SuppliedToken],
                ["config", "set", "", "tenant", "x"],
                ["config", "set", " ", "tenant", "x"],
                ["config", "set", "dev", "", "x"],
                ["config", "set", "dev", " ", "x"],
                ["config", "profile", "remove", "missing", "--token", SuppliedToken],
                ["config", "profile", "remove", ""],
                ["config", "profile", "remove", " "],
            ];
            var data = new TheoryData<string[], bool>();
            foreach (string[] input in inputs)
            {
                data.Add(input, true);
                data.Add(input, false);
            }

            return data;
        }
    }

    /// <summary>Invalid names, URLs, formats, tokens, fields, values, and targets fail as configuration errors without a write.</summary>
    /// <param name="args">The command-line arguments.</param>
    /// <param name="existing">Whether a profile file exists before the command.</param>
    [Theory]
    [MemberData(nameof(InvalidManagementInputs))]
    public async Task InvalidManagementInputFailsWithoutMutationAsync(string[] args, bool existing)
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            byte[]? previous = null;
            if (existing)
            {
                store.Add("dev", new ConnectionProfile("https://gateway.example/", StoredToken));
                previous = File.ReadAllBytes(store.ProfilePath);
            }

            (int exit, string output, string error) = await InvokeAsync(store, args);

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            AssertError(output, "configuration_invalid");
            AssertNoSecret(output, error, SuppliedToken, StoredToken);
            if (previous is null)
            {
                File.Exists(store.ProfilePath).ShouldBeFalse();
            }
            else
            {
                File.ReadAllBytes(store.ProfilePath).ShouldBe(previous);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Absent required arguments remain usage errors and never touch the store.</summary>
    /// <param name="args">The command-line arguments.</param>
    /// <param name="argument">The reported argument name.</param>
    [Theory]
    [InlineData(new[] { "config", "profile", "add", "--url", "https://gateway.example/" }, "name")]
    [InlineData(new[] { "config", "profile", "add", "dev" }, "url")]
    [InlineData(new[] { "config", "use" }, "name")]
    [InlineData(new[] { "config", "profile", "remove" }, "name")]
    [InlineData(new[] { "config", "set" }, "set")]
    [InlineData(new[] { "config", "set", "dev" }, "set")]
    [InlineData(new[] { "config", "set", "dev", "tenant" }, "set")]
    public async Task MissingRequiredArgumentIsInvalidArgumentsAsync(string[] args, string argument)
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            (int exit, string output, string error) = await InvokeAsync(store, args);

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            AssertError(output, "invalid_arguments").GetProperty("argument").GetString().ShouldBe(argument);
            File.Exists(store.ProfilePath).ShouldBeFalse();
            Directory.EnumerateFileSystemEntries(directory).ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Gets hostile target states crossed with the profile-management verbs they must block.</summary>
    public static TheoryData<string, string[]> HostileTargets
    {
        get
        {
            string[][] mutations =
            [
                ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--token", SuppliedToken],
                ["config", "use", "dev"],
                ["config", "use", "--clear"],
            ];
            string[] list = ["config", "profile", "list"];
            var data = new TheoryData<string, string[]>();
            foreach (string kind in new[] { "symlink-target", "malformed", "version-2", "unknown-field", "duplicate-key" })
            {
                foreach (string[] mutation in mutations)
                {
                    data.Add(kind, mutation);
                }

                data.Add(kind, list);
            }

            foreach (string[] mutation in mutations)
            {
                data.Add("symlink-lock", mutation);
            }

            return data;
        }
    }

    /// <summary>Symlinked, malformed, unsupported, and unknown-field targets fail without following links or rewriting.</summary>
    /// <param name="kind">The hostile target kind.</param>
    /// <param name="args">The command-line arguments.</param>
    [Theory]
    [MemberData(nameof(HostileTargets))]
    public async Task HostileTargetFailsWithoutMutationAsync(string kind, string[] args)
    {
        Assert.SkipWhen(OperatingSystem.IsWindows() && kind.StartsWith("symlink", StringComparison.Ordinal),
            "Symbolic-link targets are exercised only on Unix-like systems.");

        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string external = Path.Combine(directory, "external.json");
            string stored = "{\"version\":1,\"activeProfile\":\"dev\",\"profiles\":{\"dev\":{\"token\":\"" + StoredToken + "\"}}}";
            string content = kind switch
            {
                "malformed" => "{\"version\":1,\"profiles\":{\"dev\":{\"token\":\"" + StoredToken + "\"",
                "version-2" => stored.Replace("\"version\":1", "\"version\":2", StringComparison.Ordinal),
                "unknown-field" => stored.Replace("\"token\"", "\"colour\":\"red\",\"token\"", StringComparison.Ordinal),
                "duplicate-key" => stored.Replace("\"profiles\"", "\"version\":1,\"profiles\"", StringComparison.Ordinal),
                _ => stored,
            };
            string linkPath = kind == "symlink-lock" ? store.ProfilePath + ".lock" : store.ProfilePath;
            if (kind.StartsWith("symlink", StringComparison.Ordinal))
            {
                File.WriteAllText(external, content);
                File.CreateSymbolicLink(linkPath, external);
            }
            else
            {
                File.WriteAllText(store.ProfilePath, content);
            }

            byte[] previous = File.ReadAllBytes(kind.StartsWith("symlink", StringComparison.Ordinal) ? external : store.ProfilePath);

            (int exit, string output, string error) = await InvokeAsync(store, args);

            exit.ShouldBe(2);
            AssertError(output, "configuration_invalid");
            AssertNoSecret(output, error, SuppliedToken, StoredToken);
            if (kind.StartsWith("symlink", StringComparison.Ordinal))
            {
                File.ReadAllBytes(external).ShouldBe(previous);
                new FileInfo(linkPath).LinkTarget.ShouldBe(external);
                if (kind == "symlink-lock")
                {
                    File.Exists(store.ProfilePath).ShouldBeFalse();
                }
            }
            else
            {
                File.ReadAllBytes(store.ProfilePath).ShouldBe(previous);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A stale temporary file from an interrupted write is ignored.</summary>
    [Fact]
    public async Task AddIgnoresStaleTemporaryFileAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            string stale = store.ProfilePath + ".tmp-0123456789abcdef";
            File.WriteAllText(stale, "{broken");

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "profile", "add", "test", "--url", "https://test.example/", "--token", SuppliedToken);

            exit.ShouldBe(0);
            AssertNoSecret(output, error, SuppliedToken);
            store.Read().Profiles.Keys.ShouldBe(["dev", "test"], ignoreOrder: true);
            File.ReadAllText(stale).ShouldBe("{broken");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Setting one field through the parser changes only that field.</summary>
    [Fact]
    public async Task SetChangesOnlyTheNamedFieldAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var original = new ConnectionProfile("https://gateway.example/", StoredToken, Tenant: "acme");
            var other = new ConnectionProfile("https://test.example/", Actor: "tester");
            store.Add("dev", original);
            store.Add("test", other);
            store.Use("test");

            (int exit, string output, string error) = await InvokeAsync(store, "config", "set", "dev", "actor", "ops");

            exit.ShouldBe(0, output);
            error.ShouldBeEmpty();
            AssertNoSecret(output, error, StoredToken);
            JsonElement document = JsonDocument.Parse(output).RootElement;
            document.GetProperty("profile").GetString().ShouldBe("dev");
            document.GetProperty("field").GetString().ShouldBe("actor");
            ProfileSnapshot snapshot = store.Read();
            snapshot.Profiles["dev"].ShouldBe(original with { Actor = "ops" });
            snapshot.Profiles["test"].ShouldBe(other);
            snapshot.ActiveProfile.ShouldBe("test");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Allowed extensions are stored as a list, and an empty argument stores an empty list.</summary>
    [Fact]
    public async Task SetStoresAllowedExtensionsListAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", StoredToken));

            (int listExit, string listOutput, string listError) = await InvokeAsync(store,
                "config", "set", "dev", "allowedExtensions", "task-id,trace-id");
            listExit.ShouldBe(0, listOutput);
            listError.ShouldBeEmpty();
            AssertNoSecret(listOutput, listError, StoredToken);
            JsonElement listDocument = JsonDocument.Parse(listOutput).RootElement;
            listDocument.GetProperty("profile").GetString().ShouldBe("dev");
            listDocument.GetProperty("field").GetString().ShouldBe("allowedExtensions");
            store.Read().Profiles["dev"].AllowedExtensions.ShouldBe(["task-id", "trace-id"]);

            (int emptyExit, string emptyOutput, string emptyError) = await InvokeAsync(store,
                "config", "set", "dev", "allowedExtensions", string.Empty);
            emptyExit.ShouldBe(0, emptyOutput);
            emptyError.ShouldBeEmpty();
            AssertNoSecret(emptyOutput, emptyError, StoredToken);
            JsonElement emptyDocument = JsonDocument.Parse(emptyOutput).RootElement;
            emptyDocument.GetProperty("profile").GetString().ShouldBe("dev");
            emptyDocument.GetProperty("field").GetString().ShouldBe("allowedExtensions");
            using JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath));
            JsonElement extensions = written.RootElement.GetProperty("profiles").GetProperty("dev").GetProperty("allowedExtensions");
            extensions.ValueKind.ShouldBe(JsonValueKind.Array);
            extensions.GetArrayLength().ShouldBe(0);
            store.Read().Profiles["dev"].Token.ShouldBe(StoredToken);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Remove clears the active selection only when it names the removed profile.</summary>
    [Fact]
    public async Task RemoveClearsOnlyItsOwnSelectionAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://dev.example/", StoredToken));
            store.Add("test", new ConnectionProfile("https://test.example/"));
            store.Add("prod", new ConnectionProfile("https://prod.example/"));
            store.Use("dev");

            (int devExit, string devOutput, string devError) = await InvokeAsync(store, "config", "profile", "remove", "dev");
            devExit.ShouldBe(0, devOutput);
            devError.ShouldBeEmpty();
            AssertNoSecret(devOutput, devError, StoredToken);
            JsonElement removedDev = JsonDocument.Parse(devOutput).RootElement;
            removedDev.GetProperty("name").GetString().ShouldBe("dev");
            removedDev.GetProperty("activeProfile").ValueKind.ShouldBe(JsonValueKind.Null);
            store.Read().Profiles.Keys.ShouldBe(["test", "prod"], ignoreOrder: true);
            using (JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath)))
            {
                written.RootElement.TryGetProperty("activeProfile", out _).ShouldBeFalse();
            }

            (int useExit, _, string useError) = await InvokeAsync(store, "config", "use", "test");
            useExit.ShouldBe(0);
            useError.ShouldBeEmpty();
            (int prodExit, string prodOutput, string prodError) = await InvokeAsync(store, "config", "profile", "remove", "prod");
            prodExit.ShouldBe(0, prodOutput);
            prodError.ShouldBeEmpty();
            JsonDocument.Parse(prodOutput).RootElement.GetProperty("activeProfile").GetString().ShouldBe("test");
            store.Read().ActiveProfile.ShouldBe("test");

            (int testExit, string testOutput, string testError) = await InvokeAsync(store, "config", "profile", "remove", "test");
            testExit.ShouldBe(0, testOutput);
            testError.ShouldBeEmpty();
            JsonDocument.Parse(testOutput).RootElement.GetProperty("activeProfile").ValueKind.ShouldBe(JsonValueKind.Null);
            store.Read().Profiles.ShouldBeEmpty();
            store.Read().ActiveProfile.ShouldBeNull();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Adding an existing name replaces the whole record while keeping other profiles and the selection.</summary>
    [Fact]
    public async Task AddReplacesTheWholeRecordAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var other = new ConnectionProfile("https://test.example/", "test-secret-value", Tenant: "other");
            store.Add("dev", new ConnectionProfile("https://gateway.example/", StoredToken, "table", "acme", "ops", true));
            store.Set("dev", "allowedExtensions", "task-id");
            store.Add("test", other);
            store.Use("dev");

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "profile", "add", "dev", "--url", "https://u2.example/");

            exit.ShouldBe(0, output);
            error.ShouldBeEmpty();
            AssertNoSecret(output, error, StoredToken, "test-secret-value");
            JsonDocument.Parse(output).RootElement.GetProperty("activeProfile").GetString().ShouldBe("dev");
            ProfileSnapshot snapshot = store.Read();
            snapshot.Profiles["dev"].ShouldBe(new ConnectionProfile("https://u2.example/"));
            snapshot.Profiles["test"].ShouldBe(other);
            snapshot.ActiveProfile.ShouldBe("dev");
            using JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath));
            written.RootElement.GetProperty("profiles").GetProperty("dev").EnumerateObject()
                .Select(property => property.Name).ShouldBe(["url"]);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Gets explicit operator flags for profile add with the first offending argument they must report.</summary>
    public static TheoryData<string[], string, bool> AddOperatorFlags
    {
        get
        {
            (string[] Flags, string Argument)[] inputs =
            [
                (["--tenant", "acme"], "tenant"),
                (["--actor", "x"], "actor"),
                (["--actor", ""], "actor"),
                (["--actor", " "], "actor"),
                (["--allow-tenant-override"], "allowTenantOverride"),
                (["--allow-tenant-override", "false"], "allowTenantOverride"),
                (["--allow-tenant-override", "--actor", "x", "--tenant", "acme"], "tenant"),
                (["--allow-tenant-override", "--actor", "x"], "actor"),
                (["--tenant", " "], "tenant"),
                (["--tenant", ""], "tenant"),
            ];
            var data = new TheoryData<string[], string, bool>();
            foreach ((string[] flags, string argument) in inputs)
            {
                data.Add(flags, argument, true);
                data.Add(flags, argument, false);
            }

            return data;
        }
    }

    /// <summary>Explicit tenant, actor, or tenant-override flags on add fail as usage errors and write nothing.</summary>
    /// <param name="flags">The operator flags supplied to add.</param>
    /// <param name="argument">The first offending argument.</param>
    /// <param name="existing">Whether a profile file exists before the command.</param>
    [Theory]
    [MemberData(nameof(AddOperatorFlags))]
    public async Task AddRejectsOperatorFlagsWithoutWritingAsync(string[] flags, string argument, bool existing)
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            byte[]? previous = null;
            if (existing)
            {
                store.Add("dev", new ConnectionProfile("https://gateway.example/", StoredToken));
                previous = File.ReadAllBytes(store.ProfilePath);
            }

            (int exit, string output, string error) = await InvokeAsync(store,
                ["config", "profile", "add", "dev", "--url", "https://u2.example/", "--token", SuppliedToken, .. flags]);

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            AssertNoSecret(output, error, SuppliedToken, StoredToken);
            output.ShouldNotContain("\\u00");
            JsonElement failure = AssertError(output, "invalid_arguments");
            failure.GetProperty("argument").GetString().ShouldBe(argument);
            string message = failure.GetProperty("message").GetString().ShouldNotBeNull();
            string flag = argument == "allowTenantOverride" ? "--allow-tenant-override" : "--" + argument;
            message.ShouldContain(flag);
            message.ShouldStartWith("config profile add does not accept ");
            message.ShouldContain("wrote nothing");
            message.ShouldContain($"config set PROFILE {argument} VALUE", Case.Sensitive);
            if (previous is null)
            {
                Directory.EnumerateFileSystemEntries(directory).ShouldBeEmpty();
            }
            else
            {
                File.ReadAllBytes(store.ProfilePath).ShouldBe(previous);
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Add help states that only connection flags are stored and that operator fields belong to config set.</summary>
    [Fact]
    public async Task AddHelpLimitsStoredFlagsAndPointsOperatorFieldsToSetAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            (int exit, string output, string error) = await InvokeAsync(
                store, "config", "profile", "add", "--help");

            exit.ShouldBe(0, output + error);
            error.ShouldBeEmpty();
            string normalizedOutput = string.Join(' ', output.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries));
            normalizedOutput.ShouldContain(
                "Add or replace a connection profile from --url, --token, and --format; set operator fields with config set");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Add stores only explicit connection fields and ignores operator settings from the environment.</summary>
    [Fact]
    public async Task AddIgnoresEnvironmentOperatorSettingsAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            const string environmentToken = "environment-secret-value";
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var environment = new Dictionary<string, string?>
            {
                ["EVENTSTORE_URL"] = "https://environment.example/",
                ["EVENTSTORE_TOKEN"] = environmentToken,
                ["EVENTSTORE_TENANT"] = "environment-tenant",
                ["EVENTSTORE_ACTOR"] = "environment-actor",
                ["EVENTSTORE_ALLOW_TENANT_OVERRIDE"] = "true",
            };

            (int exit, string output, string error) = await InvokeAsync(store, environment, null,
                "config", "profile", "add", "dev");

            exit.ShouldBe(2);
            error.ShouldBeEmpty();
            AssertNoSecret(output, error, environmentToken);
            AssertError(output, "invalid_arguments").GetProperty("argument").GetString().ShouldBe("url");
            Directory.EnumerateFileSystemEntries(directory).ShouldBeEmpty();

            (exit, output, error) = await InvokeAsync(store, environment, null,
                "config", "profile", "add", "dev", "--url", "https://gateway.example/");

            exit.ShouldBe(0, output);
            error.ShouldBeEmpty();
            AssertNoSecret(output, error, environmentToken);
            JsonDocument.Parse(output).RootElement.TryGetProperty("error", out _).ShouldBeFalse();
            ConnectionProfile profile = store.Read().Profiles["dev"];
            profile.Url.ShouldBe("https://gateway.example/");
            profile.Token.ShouldBeNull();
            profile.Tenant.ShouldBeNull();
            profile.Actor.ShouldBeNull();
            profile.AllowTenantOverride.ShouldBeNull();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Add accepts the other global options and writes its result to the requested output file.</summary>
    [Fact]
    public async Task AddAcceptsOtherGlobalOptionsAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            string resultPath = Path.Combine(directory, "result.json");

            (int exit, string output, string error) = await InvokeAsync(store,
                "config", "profile", "add", "dev", "--url", "https://gateway.example/",
                "--read-only", "--strict", "--output", resultPath);

            exit.ShouldBe(0, output);
            output.ShouldBeEmpty();
            error.ShouldBeEmpty();
            store.Read().Profiles["dev"].ShouldBe(new ConnectionProfile("https://gateway.example/"));
            using JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath));
            written.RootElement.GetProperty("profiles").GetProperty("dev").EnumerateObject()
                .Select(property => property.Name).ShouldBe(["url"]);
            using JsonDocument result = JsonDocument.Parse(File.ReadAllText(resultPath));
            result.RootElement.EnumerateObject().Select(property => property.Name)
                .ShouldBe(["name", "activeProfile"], ignoreOrder: true);
            result.RootElement.GetProperty("name").GetString().ShouldBe("dev");
            result.RootElement.GetProperty("activeProfile").ValueKind.ShouldBe(JsonValueKind.Null);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Two concurrent processes setting different fields both persist their values.</summary>
    [Fact]
    public async Task ConcurrentSetProcessesPreserveBothValuesAsync()
    {
        Assert.SkipWhen(OperatingSystem.IsWindows(),
            "The child process home redirect is not honored on Windows, so it would touch the real profile file.");
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, ".eventstore", "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", StoredToken));

            // Holding the transaction lock forces both processes to queue on it, so they contend when it is released.
            Task<(int Exit, string Output, string Error)> tenant;
            Task<(int Exit, string Output, string Error)> actor;
            using (new FileStream(store.ProfilePath + ".lock", FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
            {
                tenant = RunExecutableAsync(directory, "config", "set", "dev", "tenant", "a");
                actor = RunExecutableAsync(directory, "config", "set", "dev", "actor", "b");
                await Task.Delay(TimeSpan.FromSeconds(2), TestContext.Current.CancellationToken);

                // A set that skipped the lock would already have finished; both must still be waiting on it.
                tenant.IsCompleted.ShouldBeFalse("`set dev tenant a` finished while the transaction lock was held.");
                actor.IsCompleted.ShouldBeFalse("`set dev actor b` finished while the transaction lock was held.");
            }

            (int Exit, string Output, string Error)[] results = await Task.WhenAll(tenant, actor);

            foreach ((int exit, string output, string error) in results)
            {
                exit.ShouldBe(0, output + error);
                error.ShouldBeEmpty();
                AssertNoSecret(output, error, StoredToken);
            }

            ConnectionProfile profile = store.Read().Profiles["dev"];
            profile.Tenant.ShouldBe("a");
            profile.Actor.ShouldBe("b");
            profile.Token.ShouldBe(StoredToken);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Every verb succeeds when the admin CLI's profile path cannot be opened and its environment is hostile.</summary>
    [Fact]
    public async Task VerbsNeverOpenAdminProfilesAsync()
    {
        Assert.SkipWhen(OperatingSystem.IsWindows(),
            "The child process home redirect is not honored on Windows, so it would touch the real profile file.");
        string directory = TemporaryDirectory();
        try
        {
            const string adminSecret = "admin-secret-value";
            string adminPath = Path.Combine(directory, ".eventstore", "profiles.json");
            Directory.CreateDirectory(adminPath);
            var adminEnvironment = new Dictionary<string, string>
            {
                ["EVENTSTORE_ADMIN_URL"] = "not-a-url",
                ["EVENTSTORE_ADMIN_TOKEN"] = adminSecret,
                ["EVENTSTORE_ADMIN_PROFILE"] = "admin",
                ["EVENTSTORE_ADMIN_FORMAT"] = "yaml",
            };
            string[][] verbs =
            [
                ["config", "profile", "add", "dev", "--url", "https://gateway.example/", "--token", SuppliedToken],
                ["config", "profile", "list"],
                ["config", "use", "dev"],
                ["config", "set", "dev", "tenant", "acme"],
                ["config", "set", "dev", "allowedExtensions", "task-id"],
                ["config", "current"],
                ["config", "use", "--clear"],
                ["config", "current"],
                ["config", "profile", "add", "dev", "--url", "https://u2.example/"],
                ["config", "profile", "remove", "dev"],
            ];

            foreach (string[] verb in verbs)
            {
                (int exit, string output, string error) = await RunExecutableAsync(directory, adminEnvironment, verb);
                exit.ShouldBe(0, string.Join(' ', verb) + ": " + output + error);
                error.ShouldBeEmpty();
                AssertNoSecret(output, error, SuppliedToken, adminSecret, ProfileStore.MaskToken(adminSecret)!);
            }

            Directory.Exists(adminPath).ShouldBeTrue();
            Directory.EnumerateFileSystemEntries(adminPath).ShouldBeEmpty();
            new ProfileStore(Path.Combine(directory, ".eventstore", "mcpcli.json")).Read().Profiles.ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static JsonElement AssertError(string output, string code)
    {
        JsonElement document = JsonDocument.Parse(output).RootElement;
        document.EnumerateObject().Select(property => property.Name).ShouldBe(["error"]);
        JsonElement error = document.GetProperty("error");
        error.GetProperty("code").GetString().ShouldBe(code);
        return error;
    }

    private static void AssertNoSecret(string output, string error, params string[] tokens)
    {
        foreach (string token in tokens)
        {
            output.ShouldNotContain(token);
            error.ShouldNotContain(token);
        }
    }

    private static Task<(int Exit, string Output, string Error)> InvokeAsync(ProfileStore store, params string[] args)
        => InvokeAsync(store, new Dictionary<string, string?>(), null, args);

    private static async Task<(int Exit, string Output, string Error)> InvokeAsync(
        ProfileStore store,
        IReadOnlyDictionary<string, string?> environment,
        Func<IReadOnlyList<Assembly>>? manifest,
        params string[] args)
        => await InvokeAsync(store, environment, manifest, null, args);

    private static async Task<(int Exit, string Output, string Error)> InvokeAsync(
        ProfileStore store,
        IReadOnlyDictionary<string, string?> environment,
        Func<IReadOnlyList<Assembly>>? manifest,
        Func<IHost, CancellationToken, Task<int>>? runMcp,
        params string[] args)
    {
        TextWriter originalOut = Console.Out;
        TextWriter originalError = Console.Error;
        using var output = new StringWriter();
        using var error = new StringWriter();
        try
        {
            Console.SetOut(output);
            Console.SetError(error);
            int exit = await new CliRunner(store, manifest,
                name => environment.TryGetValue(name, out string? value) ? value : null, runMcp)
                .Parse(args).InvokeAsync();
            return (exit, output.ToString(), error.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    private static Task<(int Exit, string Output, string Error)> RunExecutableAsync(string home, params string[] args)
        => RunExecutableAsync(home, new Dictionary<string, string>(), args);

    private static async Task<(int Exit, string Output, string Error)> RunExecutableAsync(
        string home,
        IReadOnlyDictionary<string, string> environment,
        params string[] args)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
        };
        foreach (string name in startInfo.Environment.Keys
            .Where(name => name.StartsWith("EVENTSTORE_", StringComparison.Ordinal)).ToArray())
        {
            startInfo.Environment.Remove(name);
        }

        startInfo.Environment["HOME"] = home;
        startInfo.Environment["USERPROFILE"] = home;
        foreach ((string name, string value) in environment)
        {
            startInfo.Environment[name] = value;
        }

        startInfo.ArgumentList.Add(typeof(CliRunner).Assembly.Location);
        foreach (string argument in args)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using Process process = Process.Start(startInfo).ShouldNotBeNull();
        Task<string> output = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
        Task<string> error = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
        await process.WaitForExitAsync(TestContext.Current.CancellationToken);
        return (process.ExitCode, await output, await error);
    }

    private static string TemporaryDirectory()
    {
        string path = Path.Combine(Path.GetTempPath(), "mcpcli-cli-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }

    private static void AssertCurrent(string json, string profile, string tenant, string source)
    {
        JsonElement current = JsonDocument.Parse(json).RootElement;
        current.GetProperty("profile").GetString().ShouldBe(profile);
        current.GetProperty("tenant").GetString().ShouldBe(tenant);
        current.GetProperty("sources").GetProperty("profile").GetString().ShouldBe(source);
    }
}

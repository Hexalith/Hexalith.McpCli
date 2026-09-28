using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;
using ModelContextProtocol.Client;
using ModelContextProtocol.Server;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Checks the CLI's profile verbs through the actual command parser.</summary>
public sealed class ConfigCommandTests
{
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
            configurationError.GetProperty("message").GetString().ShouldNotBeNull()
                .ShouldContain("EVENTSTORE_PROFILE");
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
            configurationError.GetProperty("message").GetString().ShouldNotBeNull().ShouldContain("flag");
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
                .CreateRoot().Parse(["mcp", "--read-only"])
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

    /// <summary>The executable MCP path initializes, lists tools, and shuts down over stdio.</summary>
    [Fact]
    public async Task McpExecutableInitializesAndListsToolsOverStdioAsync()
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        string directory = TemporaryDirectory();
        try
        {
            Dictionary<string, string?> environment = StdioClientTransportOptions.GetDefaultEnvironmentVariables();
            environment["HOME"] = directory;
            environment["USERPROFILE"] = directory;
            string? dotnetRoot = Environment.GetEnvironmentVariable("DOTNET_ROOT");
            if (dotnetRoot is not null)
            {
                environment["DOTNET_ROOT"] = dotnetRoot;
            }

            var transport = new StdioClientTransport(new StdioClientTransportOptions
            {
                Command = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
                Arguments = [ConformanceHostPath(), "mcp"],
                Name = "mcpcli-production-stdio",
                WorkingDirectory = directory,
                InheritEnvironmentVariables = false,
                EnvironmentVariables = environment,
                ShutdownTimeout = TimeSpan.FromSeconds(5),
            });
            await using McpClient client = await McpClient.CreateAsync(
                transport,
                new McpClientOptions { ProtocolVersion = "2025-06-18" },
                cancellationToken: timeout.Token);

            IList<McpClientTool> tools = await client.ListToolsAsync(cancellationToken: timeout.Token);

            tools.Select(tool => tool.Name).ShouldBe([
                "list_modules", "list_operations", "describe_operation", "send_command", "run_query",
            ]);
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
                .CreateRoot().Parse(args).InvokeAsync();
            return (exit, output.ToString(), error.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    private static string TemporaryDirectory()
    {
        string path = Path.Combine(Path.GetTempPath(), "mcpcli-cli-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }

    private static string ConformanceHostPath()
    {
        DirectoryInfo? root = new(AppContext.BaseDirectory);
        while (root is not null && !File.Exists(Path.Combine(root.FullName, "Hexalith.McpCli.slnx")))
        {
            root = root.Parent;
        }

        root.ShouldNotBeNull();
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent.ShouldNotBeNull().Name;
        return Path.Combine(root.FullName, "tests", "Hexalith.McpCli.ConformanceHost", "bin", configuration,
            "net10.0", "Hexalith.McpCli.ConformanceHost.dll");
    }

    private static void AssertCurrent(string json, string profile, string tenant, string source)
    {
        JsonElement current = JsonDocument.Parse(json).RootElement;
        current.GetProperty("profile").GetString().ShouldBe(profile);
        current.GetProperty("tenant").GetString().ShouldBe(tenant);
        current.GetProperty("sources").GetProperty("profile").GetString().ShouldBe(source);
    }
}

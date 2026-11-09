using Hexalith.EventStore.Client.Gateway;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Settings;
using Microsoft.Extensions.DependencyInjection;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks shared settings precedence and the one-gateway DI boundary.</summary>
public sealed class SettingsAndRegistrationTests
{
    /// <summary>
    /// Explicit options take precedence over environment and the selected profile, field by field, while the Gateway URL
    /// and token always come together from one source.
    /// </summary>
    /// <param name="source">The single source supplying both the Gateway URL and the token.</param>
    [Theory]
    [InlineData("flag")]
    [InlineData("environment")]
    [InlineData("profile")]
    public void ResolvesPrecedenceAndRecordsSources(string source)
    {
        string path = TemporaryPath();
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, """
                {"version":1,"activeProfile":"dev","profiles":{"dev":{"url":"https://profile.example/","token":"profile-token","tenant":"profile-tenant","allowedExtensions":["task-id"]}}}
                """);
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_TENANT"] = "environment-tenant" };
            if (source != "profile")
            {
                environment["EVENTSTORE_URL"] = "https://environment.example/";
                environment["EVENTSTORE_TOKEN"] = "environment-token";
            }

            SettingsInput input = source == "flag"
                ? new SettingsInput(Url: "https://flag.example/", Token: "flag-token", Actor: "operator")
                : new SettingsInput(Actor: "operator");
            SettingsResolution resolution = new SettingsResolver(new ProfileStore(path), environment).Resolve(input);

            resolution.Error.ShouldBeNull();
            ResolvedSettings settings = resolution.Settings.ShouldNotBeNull();
            settings.Url.ShouldBe(new Uri($"https://{source}.example/"));
            settings.Token.ShouldBe(source + "-token");
            settings.Tenant.ShouldBe("environment-tenant");
            settings.Actor.ShouldBe("operator");
            settings.AllowedExtensions.Contains("TASK-ID").ShouldBeTrue();
            settings.Sources["url"].ShouldBe(source == "environment" ? "EVENTSTORE_URL" : source);
            settings.Sources["token"].ShouldBe(source == "environment" ? "EVENTSTORE_TOKEN" : source);
            settings.Sources["tenant"].ShouldBe("EVENTSTORE_TENANT");
            settings.Sources["actor"].ShouldBe("flag");
            settings.Sources["format"].ShouldBe("default");
            settings.Sources["output"].ShouldBe("default");
            settings.Sources["allowedExtensions"].ShouldBe("profile");
        }
        finally
        {
            Directory.Delete(Path.GetDirectoryName(path)!, recursive: true);
        }
    }

    /// <summary>
    /// A Gateway URL and token from different sources fail before any host or Gateway exists, naming both sources and
    /// never the token.
    /// </summary>
    /// <param name="urlSource">The source supplying the URL.</param>
    /// <param name="tokenSource">The source supplying the token.</param>
    [Theory]
    [InlineData("flag", "profile")]
    [InlineData("environment", "profile")]
    [InlineData("flag", "environment")]
    [InlineData("profile", "flag")]
    [InlineData("profile", "environment")]
    [InlineData("environment", "flag")]
    public void RejectsGatewayUrlAndTokenFromDifferentSources(string urlSource, string tokenSource)
    {
        const string profileToken = "profile-secret-token";
        const string environmentToken = "environment-secret-token";
        const string flagToken = "flag-secret-token";
        var profiles = new Dictionary<string, ConnectionProfile>(StringComparer.Ordinal)
        {
            // A profile that supplies the token also keeps its own URL, which a flag or environment URL overrides.
            ["dev"] = new(Url: "https://profile.example/", Token: tokenSource == "profile" ? profileToken : null),
        };
        var environment = new Dictionary<string, string?>();
        if (urlSource == "environment")
        {
            environment["EVENTSTORE_URL"] = "https://environment.example/";
        }

        if (tokenSource == "environment")
        {
            environment["EVENTSTORE_TOKEN"] = environmentToken;
        }

        var input = new SettingsInput(Url: urlSource == "flag" ? "https://flag.example/" : null,
            Token: tokenSource == "flag" ? flagToken : null);

        SettingsResolution resolution = new SettingsResolver(() => new ProfileSnapshot(1, "dev", profiles), environment)
            .Resolve(input);

        resolution.Settings.ShouldBeNull();
        OperationError error = resolution.Error.ShouldNotBeNull();
        error.ShouldBe(new OperationError("configuration_invalid", Message:
            $"The gateway URL from {Name(urlSource, "EVENTSTORE_URL")} and the token from {Name(tokenSource, "EVENTSTORE_TOKEN")} "
            + "must come from the same source: flags, environment, or the selected profile."));
        string document = System.Text.Json.JsonSerializer.Serialize(error);
        foreach (string token in new[] { profileToken, environmentToken, flagToken })
        {
            document.ShouldNotContain(token);
            document.ShouldNotContain(ProfileStore.MaskToken(token)!);
        }

        static string Name(string source, string environmentName) => source == "environment" ? environmentName : source;
    }

    /// <summary>A Gateway URL without any token resolves from each source, as does a token without any URL.</summary>
    /// <param name="source">The source supplying the only connection value.</param>
    /// <param name="urlOnly">Whether the value is a URL rather than a token.</param>
    [Theory]
    [InlineData("flag", true)]
    [InlineData("environment", true)]
    [InlineData("profile", true)]
    [InlineData("flag", false)]
    [InlineData("environment", false)]
    [InlineData("profile", false)]
    public void ResolvesAGatewayUrlOrTokenAlone(string source, bool urlOnly)
    {
        var profiles = new Dictionary<string, ConnectionProfile>(StringComparer.Ordinal)
        {
            ["dev"] = source == "profile"
                ? new(Url: urlOnly ? "https://profile.example/" : null, Token: urlOnly ? null : "profile-token")
                : new(Tenant: "acme"),
        };
        var environment = new Dictionary<string, string?>();
        if (source == "environment")
        {
            environment[urlOnly ? "EVENTSTORE_URL" : "EVENTSTORE_TOKEN"] = urlOnly ? "https://environment.example/" : "environment-token";
        }

        SettingsInput input = source != "flag" ? new SettingsInput()
            : urlOnly ? new SettingsInput(Url: "https://flag.example/") : new SettingsInput(Token: "flag-token");

        SettingsResolution resolution = new SettingsResolver(() => new ProfileSnapshot(1, "dev", profiles), environment)
            .Resolve(input);

        resolution.Error.ShouldBeNull();
        ResolvedSettings settings = resolution.Settings.ShouldNotBeNull();
        string named = source == "environment" ? (urlOnly ? "EVENTSTORE_URL" : "EVENTSTORE_TOKEN") : source;
        if (urlOnly)
        {
            settings.Url.ShouldBe(new Uri($"https://{source}.example/"));
            settings.Token.ShouldBeNull();
            settings.Sources["url"].ShouldBe(named);
            settings.Sources["token"].ShouldBe("default");
        }
        else
        {
            settings.Url.ShouldBeNull();
            settings.Token.ShouldBe(source + "-token");
            settings.Sources["url"].ShouldBe("default");
            settings.Sources["token"].ShouldBe(named);
        }
    }

    /// <summary>
    /// A blank token is reported as the blank-token error before the URL and token sources are compared, so a flag URL
    /// beside a blank <c>EVENTSTORE_TOKEN</c> names the blank value rather than a source mix.
    /// </summary>
    [Fact]
    public void BlankTokenFailsBeforeTheSourceComparison()
    {
        var environment = new Dictionary<string, string?> { ["EVENTSTORE_TOKEN"] = " " };

        SettingsResolution resolution = new SettingsResolver(
            () => new ProfileSnapshot(1, null, new Dictionary<string, ConnectionProfile>()), environment)
            .Resolve(new SettingsInput(Url: "https://flag.example/"));

        resolution.Settings.ShouldBeNull();
        OperationError error = resolution.Error.ShouldNotBeNull();
        System.Text.Json.JsonSerializer.Serialize(new { error }, Hexalith.McpCli.Core.Serialization.McpCliJson.Result)
            .ShouldBe(System.Text.Json.JsonSerializer.Serialize(new
            {
                error = new { code = "configuration_invalid", message = "Invalid token from EVENTSTORE_TOKEN; the value cannot be blank." },
            }, Hexalith.McpCli.Core.Serialization.McpCliJson.Result));
    }

    /// <summary>Profile selection uses flag, environment, then active profile.</summary>
    [Fact]
    public void ResolvesProfileSelectionPrecedence()
    {
        string path = TemporaryPath();
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, """
                {"version":1,"activeProfile":"active","profiles":{
                  "active":{"tenant":"active-tenant"},
                  "environment":{"tenant":"environment-tenant"},
                  "flag":{"tenant":"flag-tenant"}
                }}
                """);
            var environment = new Dictionary<string, string?> { ["EVENTSTORE_PROFILE"] = "environment" };

            ResolvedSettings flagged = new SettingsResolver(new ProfileStore(path), environment)
                .Resolve(new SettingsInput(Profile: "flag")).Settings.ShouldNotBeNull();
            ResolvedSettings fromEnvironment = new SettingsResolver(new ProfileStore(path), environment)
                .Resolve(new SettingsInput()).Settings.ShouldNotBeNull();
            ResolvedSettings active = new SettingsResolver(new ProfileStore(path), new Dictionary<string, string?>())
                .Resolve(new SettingsInput()).Settings.ShouldNotBeNull();

            flagged.Profile.ShouldBe("flag");
            flagged.Tenant.ShouldBe("flag-tenant");
            flagged.Sources["profile"].ShouldBe("flag");
            fromEnvironment.Profile.ShouldBe("environment");
            fromEnvironment.Tenant.ShouldBe("environment-tenant");
            fromEnvironment.Sources["profile"].ShouldBe("EVENTSTORE_PROFILE");
            active.Profile.ShouldBe("active");
            active.Tenant.ShouldBe("active-tenant");
            active.Sources["profile"].ShouldBe("activeProfile");
        }
        finally
        {
            Directory.Delete(Path.GetDirectoryName(path)!, recursive: true);
        }
    }

    /// <summary>Documented defaults are explicit values with default source attribution.</summary>
    [Fact]
    public void ResolvesDefaultsAndRecordsEverySource()
    {
        SettingsResolution resolution = new SettingsResolver(
            () => new ProfileSnapshot(1, null, new Dictionary<string, ConnectionProfile>()),
            new Dictionary<string, string?>()).Resolve(new SettingsInput());

        resolution.Error.ShouldBeNull();
        ResolvedSettings settings = resolution.Settings.ShouldNotBeNull();
        settings.Url.ShouldBeNull();
        settings.Token.ShouldBeNull();
        settings.Tenant.ShouldBeNull();
        settings.Actor.ShouldBeNull();
        settings.AllowTenantOverride.ShouldBeFalse();
        settings.AllowedExtensions.ShouldBeEmpty();
        settings.Format.ShouldBe("json");
        settings.Output.ShouldBeNull();
        settings.ReadOnly.ShouldBeFalse();
        settings.Strict.ShouldBeFalse();
        settings.Profile.ShouldBeNull();
        settings.Sources.Keys.ShouldBe([
            "profile", "url", "token", "tenant", "actor", "format", "allowTenantOverride", "readOnly",
            "strict", "output", "allowedExtensions",
        ], ignoreOrder: true);
        settings.Sources.Values.ShouldAllBe(source => source == "default");
    }

    /// <summary>Malformed profile entries and settings fail before a host is built.</summary>
    [Theory]
    [InlineData("{\"version\":2,\"profiles\":{}}", "configuration_invalid")]
    [InlineData("{\"version\":1,\"profiles\":{},\"unexpected\":1}", "configuration_invalid")]
    [InlineData("{\"version\":1,\"profiles\":{},\"version\":1}", "configuration_invalid")]
    public void RejectsMalformedProfile(string json, string expectedCode)
    {
        string path = TemporaryPath();
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, json);

            SettingsResolution resolution = new SettingsResolver(new ProfileStore(path),
                new Dictionary<string, string?>()).Resolve(new SettingsInput());

            resolution.Settings.ShouldBeNull();
            resolution.Error.ShouldNotBeNull().Code.ShouldBe(expectedCode);
        }
        finally
        {
            Directory.Delete(Path.GetDirectoryName(path)!, recursive: true);
        }
    }

    /// <summary>The shared registration adds one EventStore client and no authentication handler.</summary>
    [Fact]
    public void RegistersOneGatewayClientWithoutHeadAuthentication()
    {
        ResolvedSettings settings = new SettingsResolver(new ProfileStore(TemporaryPath()),
            new Dictionary<string, string?>()).Resolve(new SettingsInput()).Settings.ShouldNotBeNull();
        var services = new ServiceCollection();
        services.AddLogging();

        services.AddMcpCliCore(settings, () => [], _ => { });

        services.Count(descriptor => descriptor.ServiceType == typeof(IEventStoreGatewayClient)).ShouldBe(1);
        services.Count(descriptor => typeof(DelegatingHandler).IsAssignableFrom(descriptor.ServiceType)).ShouldBe(0);
        using ServiceProvider provider = services.BuildServiceProvider();
        provider.GetRequiredService<ResolvedSettings>().ShouldBeSameAs(settings);
        provider.GetRequiredService<IOperationExecutor>().ShouldNotBeNull();
    }

    /// <summary>Each environment boolean accepts both word and numeric spellings.</summary>
    [Theory]
    [InlineData("EVENTSTORE_ALLOW_TENANT_OVERRIDE", "true", true)]
    [InlineData("EVENTSTORE_ALLOW_TENANT_OVERRIDE", "false", false)]
    [InlineData("EVENTSTORE_ALLOW_TENANT_OVERRIDE", "1", true)]
    [InlineData("EVENTSTORE_ALLOW_TENANT_OVERRIDE", "0", false)]
    [InlineData("EVENTSTORE_READ_ONLY", "true", true)]
    [InlineData("EVENTSTORE_READ_ONLY", "false", false)]
    [InlineData("EVENTSTORE_READ_ONLY", "1", true)]
    [InlineData("EVENTSTORE_READ_ONLY", "0", false)]
    [InlineData("EVENTSTORE_STRICT", "true", true)]
    [InlineData("EVENTSTORE_STRICT", "false", false)]
    [InlineData("EVENTSTORE_STRICT", "1", true)]
    [InlineData("EVENTSTORE_STRICT", "0", false)]
    public void ResolvesEnvironmentBoolean(string name, string raw, bool expected)
    {
        var environment = new Dictionary<string, string?> { [name] = raw };
        SettingsResolution resolution = new SettingsResolver(new ProfileStore(TemporaryPath()), environment)
            .Resolve(new SettingsInput());

        resolution.Error.ShouldBeNull();
        ResolvedSettings settings = resolution.Settings.ShouldNotBeNull();
        bool actual = name switch
        {
            "EVENTSTORE_ALLOW_TENANT_OVERRIDE" => settings.AllowTenantOverride,
            "EVENTSTORE_READ_ONLY" => settings.ReadOnly,
            _ => settings.Strict,
        };
        actual.ShouldBe(expected);
    }

    /// <summary>Invalid environment booleans identify their exact source.</summary>
    [Theory]
    [InlineData("EVENTSTORE_ALLOW_TENANT_OVERRIDE", "yes")]
    [InlineData("EVENTSTORE_READ_ONLY", "TRUE")]
    [InlineData("EVENTSTORE_STRICT", "False")]
    public void RejectsInvalidEnvironmentBooleanWithSource(string name, string raw)
    {
        var environment = new Dictionary<string, string?> { [name] = raw };

        SettingsResolution resolution = new SettingsResolver(new ProfileStore(TemporaryPath()), environment)
            .Resolve(new SettingsInput());

        resolution.Settings.ShouldBeNull();
        OperationError error = resolution.Error.ShouldNotBeNull();
        error.Code.ShouldBe("configuration_invalid");
        error.Message.ShouldNotBeNull().ShouldContain(name);
    }

    /// <summary>Stored allowlists apply key rules without inheriting one-call count limits.</summary>
    [Fact]
    public void AllowsProfileAllowlistLargerThanSubmissionLimit()
    {
        string path = TemporaryPath();
        try
        {
            IReadOnlyList<string> keys = Enumerable.Range(0, 40).Select(index => "key-" + index).ToArray();
            var store = new ProfileStore(path);
            store.Add("dev", new ConnectionProfile(AllowedExtensions: keys));
            store.Use("dev");

            SettingsResolution resolution = new SettingsResolver(store, new Dictionary<string, string?>())
                .Resolve(new SettingsInput());

            resolution.Error.ShouldBeNull();
            resolution.Settings.ShouldNotBeNull().AllowedExtensions.Count.ShouldBe(40);
        }
        finally
        {
            Directory.Delete(Path.GetDirectoryName(path)!, recursive: true);
        }
    }

    /// <summary>Invalid stored allowlist keys identify the profile source.</summary>
    [Fact]
    public void RejectsInvalidProfileAllowlistKeyWithSource()
    {
        string path = TemporaryPath();
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, """
                {"version":1,"activeProfile":"dev","profiles":{"dev":{"allowedExtensions":["../unsafe"]}}}
                """);

            SettingsResolution resolution = new SettingsResolver(new ProfileStore(path),
                new Dictionary<string, string?>()).Resolve(new SettingsInput());

            resolution.Settings.ShouldBeNull();
            OperationError error = resolution.Error.ShouldNotBeNull();
            error.Code.ShouldBe("configuration_invalid");
            error.Message.ShouldNotBeNull().ShouldStartWith("Invalid mcpcli profile file:");
        }
        finally
        {
            Directory.Delete(Path.GetDirectoryName(path)!, recursive: true);
        }
    }

    /// <summary>Profile mutation rejects an invalid allowlist key without changing the stored profile.</summary>
    [Fact]
    public void SetRejectsInvalidAllowlistKeyWithoutMutation()
    {
        string path = TemporaryPath();
        try
        {
            var store = new ProfileStore(path);
            store.Add("dev", new ConnectionProfile(AllowedExtensions: ["safe-key"]));

            Should.Throw<InvalidDataException>(() => store.Set("dev", "allowedExtensions", "../unsafe"));

            ConnectionProfile profile = store.Read().Profiles["dev"];
            profile.AllowedExtensions.ShouldBe(["safe-key"]);
        }
        finally
        {
            Directory.Delete(Path.GetDirectoryName(path)!, recursive: true);
        }
    }

    /// <summary>Resolver validation identifies the profile source even when the store seam supplies invalid data.</summary>
    [Fact]
    public void ResolverRejectsInvalidAllowlistKeyWithExactSourceMessage()
    {
        var profiles = new Dictionary<string, ConnectionProfile>(StringComparer.Ordinal)
        {
            ["dev"] = new(AllowedExtensions: ["../unsafe"]),
        };
        var resolver = new SettingsResolver(
            () => new ProfileSnapshot(1, "dev", profiles),
            new Dictionary<string, string?>());

        SettingsResolution resolution = resolver.Resolve(new SettingsInput());

        resolution.Settings.ShouldBeNull();
        OperationError error = resolution.Error.ShouldNotBeNull();
        error.Code.ShouldBe("configuration_invalid");
        error.Message.ShouldBe("The selected profile contains an invalid allowed extension key from profile.");
    }

    /// <summary>Profile read I/O omits exception paths while expected profile validation stays specific.</summary>
    [Fact]
    public void ProfileReadIoHidesPaths()
    {
        var resolver = new SettingsResolver(
            () => throw new IOException("secret-token /private/profile.json"), new Dictionary<string, string?>());

        OperationError error = resolver.Resolve(new SettingsInput()).Error.ShouldNotBeNull();

        error.Code.ShouldBe("configuration_invalid");
        error.Message.ShouldBe("Unable to read the mcpcli profile file.");
        var denied = new SettingsResolver(
            () => throw new UnauthorizedAccessException("secret-token /private/profile.json"),
            new Dictionary<string, string?>());
        OperationError deniedError = denied.Resolve(new SettingsInput()).Error.ShouldNotBeNull();
        deniedError.Code.ShouldBe("configuration_invalid");
        deniedError.Message.ShouldBe("Unable to read the mcpcli profile file.");
        var invalid = new SettingsResolver(
            () => throw new InvalidDataException("The mcpcli profile document has an unsupported version."),
            new Dictionary<string, string?>());
        invalid.Resolve(new SettingsInput()).Error.ShouldNotBeNull().Message
            .ShouldBe("Invalid mcpcli profile file: The mcpcli profile document has an unsupported version.");
    }

    /// <summary>Resolution performs exactly one profile read.</summary>
    [Fact]
    public void ReadsProfileSnapshotOnce()
    {
        int reads = 0;
        var snapshot = new ProfileSnapshot(1, null, new Dictionary<string, ConnectionProfile>());
        var resolver = new SettingsResolver(() =>
        {
            reads++;
            return snapshot;
        }, new Dictionary<string, string?>());

        resolver.Resolve(new SettingsInput()).Error.ShouldBeNull();

        reads.ShouldBe(1);
    }

    /// <summary>Every diagnostic token display hides short secrets and redacts long ones.</summary>
    [Theory]
    [InlineData("abcd", "***")]
    [InlineData("abc", "***")]
    [InlineData("abcdefgh", "abcd***")]
    public void RedactsTokensInDisplayAndSettingsText(string token, string expected)
    {
        var input = new SettingsInput(Token: token);
        var profile = new ConnectionProfile(Token: token);
        ResolvedSettings settings = new SettingsResolver(new ProfileStore(TemporaryPath()),
            new Dictionary<string, string?>()).Resolve(input).Settings.ShouldNotBeNull();

        ProfileStore.MaskToken(token).ShouldBe(expected);
        foreach (string text in new[] { input.ToString(), profile.ToString(), settings.ToString() })
        {
            text.ShouldContain(expected);
            text.ShouldNotContain(token);
        }

        System.Text.Json.JsonSerializer.Serialize(input).ShouldNotContain(token);
        System.Text.Json.JsonSerializer.Serialize(settings).ShouldNotContain(token);
    }

    private static string TemporaryPath()
        => Path.Combine(Path.GetTempPath(), "mcpcli-settings-" + Guid.NewGuid().ToString("N"), "mcpcli.json");
}

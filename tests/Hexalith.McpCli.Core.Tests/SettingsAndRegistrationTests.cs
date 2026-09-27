using Hexalith.EventStore.Client.Gateway;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Core.Execution;
using Microsoft.Extensions.DependencyInjection;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks shared settings precedence and the one-gateway DI boundary.</summary>
public sealed class SettingsAndRegistrationTests
{
    /// <summary>Explicit options take precedence over environment and the selected profile.</summary>
    [Fact]
    public void ResolvesPrecedenceAndRecordsSources()
    {
        string path = TemporaryPath();
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, """
                {"version":1,"activeProfile":"dev","profiles":{"dev":{"url":"https://profile.example/","token":"profile-token","tenant":"profile-tenant","allowedExtensions":["task-id"]}}}
                """);
            var environment = new Dictionary<string, string?>
            {
                ["EVENTSTORE_URL"] = "https://environment.example/",
                ["EVENTSTORE_TOKEN"] = "environment-token",
            };

            SettingsResolution resolution = new SettingsResolver(new ProfileStore(path), environment)
                .Resolve(new SettingsInput(Url: "https://flag.example/", Actor: "operator"));

            resolution.Error.ShouldBeNull();
            ResolvedSettings settings = resolution.Settings.ShouldNotBeNull();
            settings.Url.ShouldBe(new Uri("https://flag.example/"));
            settings.Token.ShouldBe("environment-token");
            settings.Tenant.ShouldBe("profile-tenant");
            settings.Actor.ShouldBe("operator");
            settings.AllowedExtensions.Contains("TASK-ID").ShouldBeTrue();
            settings.Sources["url"].ShouldBe("flag");
            settings.Sources["token"].ShouldBe("EVENTSTORE_TOKEN");
            settings.Sources["tenant"].ShouldBe("profile");
        }
        finally
        {
            Directory.Delete(Path.GetDirectoryName(path)!, recursive: true);
        }
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

    /// <summary>Environment booleans accept both word and numeric spellings.</summary>
    [Theory]
    [InlineData("true", true)]
    [InlineData("false", false)]
    [InlineData("1", true)]
    [InlineData("0", false)]
    public void ResolvesEnvironmentBoolean(string raw, bool expected)
    {
        var environment = new Dictionary<string, string?> { ["EVENTSTORE_READ_ONLY"] = raw };
        SettingsResolution resolution = new SettingsResolver(new ProfileStore(TemporaryPath()), environment)
            .Resolve(new SettingsInput());

        resolution.Error.ShouldBeNull();
        resolution.Settings.ShouldNotBeNull().ReadOnly.ShouldBe(expected);
    }

    private static string TemporaryPath()
        => Path.Combine(Path.GetTempPath(), "mcpcli-settings-" + Guid.NewGuid().ToString("N"), "mcpcli.json");
}

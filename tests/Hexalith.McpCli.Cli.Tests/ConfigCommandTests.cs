using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Settings;
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

    private static async Task<(int Exit, string Output, string Error)> InvokeAsync(ProfileStore store, params string[] args)
    {
        TextWriter originalOut = Console.Out;
        TextWriter originalError = Console.Error;
        using var output = new StringWriter();
        using var error = new StringWriter();
        try
        {
            Console.SetOut(output);
            Console.SetError(error);
            int exit = await new CliRunner(store).CreateRoot().Parse(args).InvokeAsync();
            return (exit, output.ToString(), error.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    private static string TemporaryDirectory()
        => Path.Combine(Path.GetTempPath(), "mcpcli-cli-" + Guid.NewGuid().ToString("N"));
}

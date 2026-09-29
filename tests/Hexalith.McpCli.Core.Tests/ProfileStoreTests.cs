using System.Text.Json;
using Hexalith.McpCli.Core.Settings;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks profile transactions, validation, and private storage.</summary>
public sealed class ProfileStoreTests
{
    /// <summary>Token masking uses safe Unicode text-element prefixes and never returns the complete token.</summary>
    [Theory]
    [InlineData("abcd", "***")]
    [InlineData("***", "###")]
    [InlineData("****", "***")]
    [InlineData("abcd*", "***")]
    [InlineData("abcd***", "***")]
    [InlineData("\u001babcdef", "***")]
    [InlineData("\u2028abcdef", "***")]
    [InlineData("\u2029abcdef", "***")]
    [InlineData("\u202eabcdef", "***")]
    [InlineData("😀😁😂🤣", "***")]
    [InlineData("😀a\u0301bcdef", "😀a\u0301bc***")]
    public void MasksTokenSafely(string token, string expected)
    {
        string masked = ProfileStore.MaskToken(token).ShouldNotBeNull();

        masked.ShouldBe(expected);
        masked.ShouldNotContain(token);
    }

    /// <summary>All profile commands round-trip without exposing the admin CLI file.</summary>
    [Fact]
    public void MutationsRoundTripAndKeepPrivatePermissions()
    {
        string directory = TemporaryDirectory();
        try
        {
            Directory.CreateDirectory(directory);
            string adminPath = Path.Combine(directory, "profiles.json");
            File.WriteAllText(adminPath, "admin-sentinel");
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token", "json"));
            store.Use("dev");
            store.Set("dev", "tenant", "acme");
            store.Set("dev", "actor", "operator");
            store.Set("dev", "allowTenantOverride", "1");
            store.Set("dev", "allowedExtensions", "task-id,trace-id");

            ProfileSnapshot snapshot = store.Read();
            snapshot.ActiveProfile.ShouldBe("dev");
            snapshot.Profiles["dev"].Tenant.ShouldBe("acme");
            snapshot.Profiles["dev"].Actor.ShouldBe("operator");
            snapshot.Profiles["dev"].AllowTenantOverride.ShouldBe(true);
            snapshot.Profiles["dev"].AllowedExtensions.ShouldBe(new[] { "task-id", "trace-id" });
            ProfileStore.MaskToken(snapshot.Profiles["dev"].Token).ShouldBe("secr***");
            File.ReadAllText(adminPath).ShouldBe("admin-sentinel");

            if (!OperatingSystem.IsWindows())
            {
                File.GetUnixFileMode(directory).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
                File.GetUnixFileMode(store.ProfilePath).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
                File.GetUnixFileMode(store.ProfilePath + ".lock").ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
            }

            store.Remove("dev");
            store.Read().ActiveProfile.ShouldBeNull();
            store.Read().Profiles.ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Concurrent writers reload under the lock, preserving every update.</summary>
    [Fact]
    public async Task ConcurrentWritersDoNotLoseProfilesAsync()
    {
        string directory = TemporaryDirectory();
        try
        {
            string path = Path.Combine(directory, "mcpcli.json");
            Task[] writes = Enumerable.Range(0, 12).Select(index => Task.Run(() =>
                new ProfileStore(path).Add("profile_" + index, new ConnectionProfile("https://gateway.example/")))).ToArray();
            await Task.WhenAll(writes);

            new ProfileStore(path).Read().Profiles.Count.ShouldBe(12);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Invalid updates leave the complete prior target untouched.</summary>
    [Fact]
    public void InvalidMutationsDoNotReplaceTheTarget()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            string previous = File.ReadAllText(store.ProfilePath);

            Should.Throw<InvalidDataException>(() => store.Set("dev", "allowedExtensions", "task-id,TASK-ID"));
            Should.Throw<InvalidDataException>(() => store.Set("missing", "tenant", "acme"));
            Should.Throw<InvalidDataException>(() => store.Add("invalid name", new ConnectionProfile("https://gateway.example/")));
            File.ReadAllText(store.ProfilePath).ShouldBe(previous);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A stale temporary file is ignored and the target remains readable.</summary>
    [Fact]
    public void IgnoresInterruptedTemporaryFile()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));
            File.WriteAllText(store.ProfilePath + ".tmp-stale", "{broken");

            store.Add("test", new ConnectionProfile("https://test.example/"));

            store.Read().Profiles.Count.ShouldBe(2);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Symlink targets and lock files are never opened for mutation.</summary>
    [Fact]
    public void RejectsSymlinkTargetAndLock()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }

        string directory = TemporaryDirectory();
        try
        {
            Directory.CreateDirectory(directory);
            string external = Path.Combine(directory, "external.json");
            File.WriteAllText(external, "sentinel");
            string target = Path.Combine(directory, "mcpcli.json");
            File.CreateSymbolicLink(target, external);
            var store = new ProfileStore(target);
            Should.Throw<InvalidDataException>(() => store.Add("dev", new ConnectionProfile("https://gateway.example/")));
            File.Delete(target);
            File.CreateSymbolicLink(target + ".lock", external);
            Should.Throw<InvalidDataException>(() => store.Add("dev", new ConnectionProfile("https://gateway.example/")));
            File.ReadAllText(external).ShouldBe("sentinel");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A linked profile directory is rejected before chmod or any write.</summary>
    [Fact]
    public void RejectsSymlinkProfileDirectory()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }

        string root = TemporaryDirectory();
        try
        {
            Directory.CreateDirectory(root);
            string external = Path.Combine(root, "external");
            Directory.CreateDirectory(external);
            UnixFileMode originalMode = File.GetUnixFileMode(external);
            string linked = Path.Combine(root, ".eventstore");
            Directory.CreateSymbolicLink(linked, external);

            var store = new ProfileStore(Path.Combine(linked, "mcpcli.json"));
            Should.Throw<InvalidDataException>(() => store.Read());
            Should.Throw<InvalidDataException>(() => store.Add("dev", new ConnectionProfile("https://gateway.example/")));
            File.Exists(Path.Combine(external, "mcpcli.json")).ShouldBeFalse();
            File.GetUnixFileMode(external).ShouldBe(originalMode);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    /// <summary>Malformed, unknown-field, duplicate-key, and unsupported-version targets fail without being overwritten.</summary>
    /// <param name="content">The hostile target document.</param>
    [Theory]
    [InlineData("{\"version\":1,\"profiles\":{\"dev\":{\"token\":\"hostile-secret\"")]
    [InlineData("{\"version\":1,\"profiles\":{\"dev\":{\"token\":\"hostile-secret\",\"colour\":\"red\"}}}")]
    [InlineData("{\"version\":1,\"profiles\":{},\"extra\":true}")]
    [InlineData("{\"version\":1,\"profiles\":{\"dev\":{\"token\":\"hostile-secret\"},\"dev\":{}}}")]
    [InlineData("{\"version\":2,\"profiles\":{\"dev\":{\"token\":\"hostile-secret\"}}}")]
    public void HostileTargetsFailWithoutMutation(string content)
    {
        string directory = TemporaryDirectory();
        try
        {
            Directory.CreateDirectory(directory);
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            File.WriteAllText(store.ProfilePath, content);
            byte[] previous = File.ReadAllBytes(store.ProfilePath);

            InvalidDataException read = Should.Throw<InvalidDataException>(() => store.Read());
            InvalidDataException add = Should.Throw<InvalidDataException>(
                () => store.Add("dev", new ConnectionProfile("https://gateway.example/", "new-secret")));
            InvalidDataException use = Should.Throw<InvalidDataException>(() => store.Use("dev"));
            InvalidDataException clear = Should.Throw<InvalidDataException>(() => store.Use(null));

            File.ReadAllBytes(store.ProfilePath).ShouldBe(previous);
            foreach (InvalidDataException exception in new[] { read, add, use, clear })
            {
                exception.Message.ShouldNotContain("hostile-secret");
                exception.Message.ShouldNotContain("new-secret");
                exception.InnerException.ShouldBeNull();
            }
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The written document stores only supplied fields and never writes explicit nulls.</summary>
    [Fact]
    public void WritesOnlySuppliedFields()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));

            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token"));

            using JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath));
            JsonElement root = written.RootElement;
            root.EnumerateObject().Select(property => property.Name).ShouldBe(["version", "profiles"]);
            root.GetProperty("version").GetInt32().ShouldBe(1);
            JsonElement profile = root.GetProperty("profiles").GetProperty("dev");
            profile.EnumerateObject().Select(property => property.Name).ShouldBe(["url", "token"]);
            profile.GetProperty("url").GetString().ShouldBe("https://gateway.example/");

            store.Use("dev");
            store.Use(null);
            using JsonDocument cleared = JsonDocument.Parse(File.ReadAllText(store.ProfilePath));
            cleared.RootElement.TryGetProperty("activeProfile", out _).ShouldBeFalse();
            store.Read().ActiveProfile.ShouldBeNull();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static string TemporaryDirectory()
        => Path.Combine(Path.GetTempPath(), "mcpcli-profile-" + Guid.NewGuid().ToString("N"));
}

using Hexalith.McpCli.Core.Settings;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks profile transactions, validation, and private storage.</summary>
public sealed class ProfileStoreTests
{
    /// <summary>Token masking uses safe Unicode text-element prefixes and never returns the complete token.</summary>
    [Theory]
    [InlineData("abcd", "***")]
    [InlineData("***", "****")]
    [InlineData("abcd***", "abcd****")]
    [InlineData("\u001babcdef", "***")]
    [InlineData("\u202eabcdef", "***")]
    [InlineData("😀a\u0301bcdef", "😀a\u0301bc***")]
    public void MasksTokenSafely(string token, string expected)
    {
        string masked = ProfileStore.MaskToken(token).ShouldNotBeNull();

        masked.ShouldBe(expected);
        masked.ShouldNotBe(token);
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

    private static string TemporaryDirectory()
        => Path.Combine(Path.GetTempPath(), "mcpcli-profile-" + Guid.NewGuid().ToString("N"));
}

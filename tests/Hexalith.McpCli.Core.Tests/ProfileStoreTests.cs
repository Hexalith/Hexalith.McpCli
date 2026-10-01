using System.Runtime.Versioning;
using System.Security.AccessControl;
using System.Security.Principal;
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

    /// <summary>Setting one field changes only that field and keeps every other profile and the selection.</summary>
    [Fact]
    public void SetChangesOnlyTheNamedField()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var original = new ConnectionProfile("https://gateway.example/", "secret-token", Tenant: "acme");
            var other = new ConnectionProfile("https://test.example/", Actor: "tester");
            store.Add("dev", original);
            store.Add("test", other);
            store.Use("test");

            store.Set("dev", "actor", "ops");

            ProfileSnapshot snapshot = store.Read();
            snapshot.Profiles["dev"].ShouldBe(original with { Actor = "ops" });
            snapshot.Profiles["test"].ShouldBe(other);
            snapshot.ActiveProfile.ShouldBe("test");
            using JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath));
            written.RootElement.GetProperty("profiles").GetProperty("dev").EnumerateObject()
                .Select(property => property.Name).ShouldBe(["url", "token", "tenant", "actor"], ignoreOrder: true);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Allowed extensions are split on commas without trimming, and an empty value stores an empty list.</summary>
    [Fact]
    public void SetStoresAllowedExtensionsAsValidatedList()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/"));

            store.Set("dev", "allowedExtensions", "task-id,trace-id");
            store.Read().Profiles["dev"].AllowedExtensions.ShouldBe(["task-id", "trace-id"]);

            store.Set("dev", "allowedExtensions", string.Empty);
            store.Read().Profiles["dev"].AllowedExtensions.ShouldNotBeNull().ShouldBeEmpty();
            using JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath));
            JsonElement extensions = written.RootElement.GetProperty("profiles").GetProperty("dev").GetProperty("allowedExtensions");
            extensions.ValueKind.ShouldBe(JsonValueKind.Array);
            extensions.GetArrayLength().ShouldBe(0);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Unknown or case-mismatched fields, invalid values, bad keys, and bad names fail without changing bytes.</summary>
    /// <param name="name">The profile name.</param>
    /// <param name="field">The field name.</param>
    /// <param name="value">The field value.</param>
    [Theory]
    [InlineData("dev", "colour", "red")]
    [InlineData("dev", "Tenant", "acme")]
    [InlineData("dev", "url", "https://other.example/")]
    [InlineData("dev", "token", "other-token")]
    [InlineData("dev", "format", "json")]
    [InlineData("dev", "", "x")]
    [InlineData("dev", " ", "x")]
    [InlineData("dev", "allowTenantOverride", "yes")]
    [InlineData("dev", "tenant", " ")]
    [InlineData("dev", "actor", "")]
    [InlineData("dev", "allowedExtensions", "a,A")]
    [InlineData("dev", "allowedExtensions", "a,")]
    [InlineData("dev", "allowedExtensions", "a, b")]
    [InlineData("dev", "allowedExtensions", "a ,b")]
    [InlineData("dev", "allowedExtensions", " a")]
    [InlineData("dev", "allowedExtensions", "../unsafe")]
    [InlineData("dev", "allowedExtensions", "javascript:x")]
    [InlineData("missing", "tenant", "x")]
    [InlineData("", "tenant", "x")]
    [InlineData(" ", "tenant", "x")]
    public void InvalidSetFailsWithoutChangingBytes(string name, string field, string value)
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token", Tenant: "acme"));
            byte[] previous = File.ReadAllBytes(store.ProfilePath);

            InvalidDataException failure = Should.Throw<InvalidDataException>(() => store.Set(name, field, value));

            failure.Message.ShouldNotContain("secret-token");
            File.ReadAllBytes(store.ProfilePath).ShouldBe(previous);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Add replaces the whole record while keeping other profiles and the active selection.</summary>
    [Fact]
    public void AddReplacesTheWholeRecord()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            var other = new ConnectionProfile("https://test.example/", "test-token", Tenant: "other");
            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token", "table", "acme", "ops", true));
            store.Set("dev", "allowedExtensions", "task-id");
            store.Add("test", other);
            store.Use("dev");

            store.Add("dev", new ConnectionProfile("https://u2.example/"));

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

    /// <summary>Remove clears the active selection only when it names the removed profile.</summary>
    [Fact]
    public void RemoveClearsOnlyItsOwnSelection()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://dev.example/"));
            store.Add("test", new ConnectionProfile("https://test.example/"));
            store.Add("prod", new ConnectionProfile("https://prod.example/"));
            store.Use("dev");

            ProfileSnapshot removedActive = store.Remove("dev");
            removedActive.ActiveProfile.ShouldBeNull();
            removedActive.Profiles.Keys.ShouldBe(["test", "prod"], ignoreOrder: true);
            using (JsonDocument written = JsonDocument.Parse(File.ReadAllText(store.ProfilePath)))
            {
                written.RootElement.TryGetProperty("activeProfile", out _).ShouldBeFalse();
            }

            store.Use("test");
            store.Remove("prod").ActiveProfile.ShouldBe("test");
            store.Read().ActiveProfile.ShouldBe("test");

            ProfileSnapshot removedLast = store.Remove("test");
            removedLast.ActiveProfile.ShouldBeNull();
            removedLast.Profiles.ShouldBeEmpty();
            store.Read().ActiveProfile.ShouldBeNull();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>Removing a missing or invalid name fails without changing bytes.</summary>
    /// <param name="name">The profile name.</param>
    [Theory]
    [InlineData("missing")]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("bad name")]
    public void InvalidRemoveFailsWithoutChangingBytes(string name)
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token"));
            store.Use("dev");
            byte[] previous = File.ReadAllBytes(store.ProfilePath);

            Should.Throw<InvalidDataException>(() => store.Remove(name));

            File.ReadAllBytes(store.ProfilePath).ShouldBe(previous);
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A serialization failure after bytes reach the temporary file leaves the target intact and no temporary file.</summary>
    [Fact]
    public void InterruptedWriteKeepsPreviousTargetAndRemovesTemporaryFile()
    {
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token"));
            byte[] previous = File.ReadAllBytes(store.ProfilePath);
            long partialLength = 0;
            JsonSerializerOptions options = ConnectionProfileProbeConverter.Options(index =>
            {
                if (index == 2)
                {
                    partialLength = new FileInfo(TemporaryFiles(store).Single()).Length;
                    throw new InvalidOperationException("Simulated serialization failure.");
                }
            });

            // The large middle profile forces the serializer to flush a partial document before the failing write.
            Should.Throw<InvalidOperationException>(() => new ProfileFileTransaction(store.ProfilePath).Apply(
                store.Read,
                snapshot => snapshot with
                {
                    Profiles = new Dictionary<string, ConnectionProfile>(snapshot.Profiles, StringComparer.Ordinal)
                    {
                        ["large"] = new ConnectionProfile(Tenant: new string('t', 256 * 1024)),
                        ["tail"] = new ConnectionProfile(Tenant: "tail"),
                    },
                },
                options));

            partialLength.ShouldBeGreaterThan(0);
            File.ReadAllBytes(store.ProfilePath).ShouldBe(previous);
            TemporaryFiles(store).ShouldBeEmpty();
            store.Read().Profiles.Keys.ShouldBe(["dev"]);

            // The failed write released the lock and temporary stream, so the next mutation commits.
            store.Set("dev", "tenant", "acme");
            store.Read().Profiles["dev"].Tenant.ShouldBe("acme");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The temporary file is private before any profile bytes are serialized into it.</summary>
    [Fact]
    [UnsupportedOSPlatform("windows")]
    public void TemporaryFileIsPrivateBeforeTokenBytesAreWritten()
    {
        Assert.SkipWhen(OperatingSystem.IsWindows(), "Unix file modes are exercised only on Unix-like systems.");
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token"));
            var observed = new List<UnixFileMode>();
            JsonSerializerOptions options = ConnectionProfileProbeConverter.Options(
                _ => observed.Add(File.GetUnixFileMode(TemporaryFiles(store).Single())));

            new ProfileFileTransaction(store.ProfilePath).Apply(store.Read, snapshot => snapshot, options);

            observed.ShouldNotBeEmpty();
            observed.ShouldAllBe(mode => mode == (UnixFileMode.UserRead | UnixFileMode.UserWrite));
            TemporaryFiles(store).ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>A mutation tightens a pre-existing permissive directory, target, and lock to owner-only modes.</summary>
    [Fact]
    [UnsupportedOSPlatform("windows")]
    public void MutationRestrictsPermissivePreexistingModes()
    {
        Assert.SkipWhen(OperatingSystem.IsWindows(), "Unix file modes are exercised only on Unix-like systems.");
        string directory = TemporaryDirectory();
        try
        {
            const UnixFileMode Permissive = UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.GroupRead | UnixFileMode.OtherRead;
            Directory.CreateDirectory(directory);
            File.SetUnixFileMode(directory, Permissive | UnixFileMode.UserExecute | UnixFileMode.GroupExecute | UnixFileMode.OtherExecute);
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            File.WriteAllText(store.ProfilePath, "{\"version\":1,\"profiles\":{\"dev\":{\"token\":\"secret-token\"}}}");
            File.WriteAllText(store.ProfilePath + ".lock", string.Empty);
            File.SetUnixFileMode(store.ProfilePath, Permissive);
            File.SetUnixFileMode(store.ProfilePath + ".lock", Permissive);

            store.Set("dev", "tenant", "acme");

            File.GetUnixFileMode(directory).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
            File.GetUnixFileMode(store.ProfilePath).ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
            File.GetUnixFileMode(store.ProfilePath + ".lock").ShouldBe(UnixFileMode.UserRead | UnixFileMode.UserWrite);
            store.Read().Profiles["dev"].ShouldBe(new ConnectionProfile(Token: "secret-token", Tenant: "acme"));
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The directory, target, and lock carry protected ACLs for only the current user and LocalSystem.</summary>
    [Fact]
    [SupportedOSPlatform("windows")]
    public void WindowsProfileFilesHavePrivateAcls()
    {
        Assert.SkipUnless(OperatingSystem.IsWindows(), "Windows ACLs are exercised only on Windows.");
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token"));
            store.Set("dev", "tenant", "acme");

            AssertPrivateAcl(new DirectoryInfo(directory).GetAccessControl());
            AssertPrivateAcl(new FileInfo(store.ProfilePath).GetAccessControl());
            AssertPrivateAcl(new FileInfo(store.ProfilePath + ".lock").GetAccessControl());
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    /// <summary>The temporary file carries protected ACLs for only the current user and LocalSystem before profile bytes are serialized into it.</summary>
    [Fact]
    [SupportedOSPlatform("windows")]
    public void WindowsTemporaryFileHasPrivateAclBeforeTokenBytesAreWritten()
    {
        Assert.SkipUnless(OperatingSystem.IsWindows(), "Windows ACLs are exercised only on Windows.");
        string directory = TemporaryDirectory();
        try
        {
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            store.Add("dev", new ConnectionProfile("https://gateway.example/", "secret-token"));
            var observed = new List<FileSecurity>();
            JsonSerializerOptions options = ConnectionProfileProbeConverter.Options(_ =>
            {
                // ReadPermissions requests ACL metadata only; it does not conflict with the writer's FileShare.None.
                using FileStream permissions = new FileInfo(TemporaryFiles(store).Single()).Create(
                    FileMode.Open, FileSystemRights.ReadPermissions, FileShare.ReadWrite,
                    bufferSize: 1, options: FileOptions.None, fileSecurity: null);
                observed.Add(permissions.GetAccessControl());
            });

            new ProfileFileTransaction(store.ProfilePath).Apply(store.Read, snapshot => snapshot, options);

            observed.ShouldNotBeEmpty();
            foreach (FileSecurity security in observed)
            {
                AssertPrivateAcl(security);
            }

            TemporaryFiles(store).ShouldBeEmpty();
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    [SupportedOSPlatform("windows")]
    private static void AssertPrivateAcl(FileSystemSecurity security)
    {
        security.AreAccessRulesProtected.ShouldBeTrue();
        SecurityIdentifier user = WindowsIdentity.GetCurrent().User.ShouldNotBeNull();
        var system = new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null);
        FileSystemAccessRule[] rules = [.. security.GetAccessRules(true, true, typeof(SecurityIdentifier))
            .Cast<FileSystemAccessRule>()];
        rules.ShouldNotBeEmpty();
        foreach (FileSystemAccessRule rule in rules)
        {
            rule.AccessControlType.ShouldBe(AccessControlType.Allow);
            rule.FileSystemRights.ShouldBe(FileSystemRights.FullControl);
            rule.IsInherited.ShouldBeFalse();
        }

        // A process running as LocalSystem has one identity, so its ACL legitimately holds only that SID.
        SecurityIdentifier[] expected = user == system ? [system] : [user, system];
        rules.Select(rule => (SecurityIdentifier)rule.IdentityReference).Distinct().ShouldBe(expected, ignoreOrder: true);
    }

    private static string[] TemporaryFiles(ProfileStore store)
        => Directory.GetFiles(Path.GetDirectoryName(store.ProfilePath)!, Path.GetFileName(store.ProfilePath) + ".tmp-*");

    private static string TemporaryDirectory()
        => Path.Combine(Path.GetTempPath(), "mcpcli-profile-" + Guid.NewGuid().ToString("N"));
}

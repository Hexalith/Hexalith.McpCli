using System.Diagnostics;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.Xml.Linq;
using System.Runtime.ExceptionServices;
using System.Text;

namespace Hexalith.McpCli.AppHost;

/// <summary>Invokes the existing Platform catalog executable over immutable copies of prepared owner assemblies.</summary>
internal static class NativeCatalogTool
{
    /// <summary>Builds the existing tool in a private directory and returns its actual catalog receipt.</summary>
    /// <param name="repositoryRoot">The owning McpCli checkout.</param>
    /// <param name="directory">The private directory owned by this activation attempt.</param>
    /// <param name="instanceId">The bounded catalog instance identity.</param>
    /// <param name="gatewayAppId">The actual gateway application identity.</param>
    /// <param name="sdkVersion">The exact published SDK cohort prepared for every host.</param>
    /// <param name="owners">The prepared declaration and adapter assemblies with actual receiver identities.</param>
    /// <param name="token">The bounded startup lifetime.</param>
    /// <param name="dotnetExecutable">Optional controlled-process executable for offline preparation tests.</param>
    internal static async Task<JsonDocument> GenerateAsync(DirectoryInfo repositoryRoot, string directory,
        string instanceId, string gatewayAppId, string sdkVersion,
        IReadOnlyList<(string OwnerPath, string AdapterPath, string AppId)> owners, CancellationToken token, string dotnetExecutable = "dotnet")
    {
        ArgumentNullException.ThrowIfNull(repositoryRoot);
        if (owners.Count == 0 || owners.Any(owner => !Path.IsPathFullyQualified(owner.OwnerPath)
            || !Path.IsPathFullyQualified(owner.AdapterPath) || string.IsNullOrWhiteSpace(owner.AppId)))
        {
            throw new InvalidDataException("Exact prepared owner/adapter assemblies and application identities are required.");
        }
        string template = Path.Combine(repositoryRoot.FullName, "references", "Hexalith.Platform", "src", "Hexalith.Platform.CatalogBuilder", "Hexalith.Platform.CatalogBuilder.csproj");
        string build = Path.Combine(directory, "reader");
        PrepareBuildDirectory(repositoryRoot.FullName, build);
        string project = Path.Combine(build, "Hexalith.Platform.CatalogBuilder.csproj");
        XDocument xml = XDocument.Load(template);
        xml.Root!.AddFirst(new XElement("Import", new XAttribute("Project", Path.Combine(repositoryRoot.FullName, "Directory.Packages.props"))));
        xml.Root.AddFirst(new XElement("Import", new XAttribute("Project", Path.Combine(repositoryRoot.FullName, "Directory.Build.props"))));
        XElement references = new("ItemGroup");
        Dictionary<string, string> copied = new(StringComparer.OrdinalIgnoreCase);
        Dictionary<string, string> inputHashes = new(StringComparer.Ordinal);
        foreach (string source in owners.SelectMany(owner => new[] { owner.OwnerPath, owner.AdapterPath }).Distinct(StringComparer.Ordinal))
        {
            string name = AssemblyName.GetAssemblyName(source).Name!;
            string destination = Path.Combine(build, "owners", name);
            CreatePrivateDirectory(destination);
            foreach (string dependency in Directory.EnumerateFiles(Path.GetDirectoryName(source)!, "*.dll"))
            {
                string filename = Path.GetFileName(dependency);
                byte[] bytes = await File.ReadAllBytesAsync(dependency, token).ConfigureAwait(false);
                string hash = Convert.ToHexStringLower(SHA256.HashData(bytes));
                inputHashes[dependency] = hash;
                string target = Path.Combine(destination, filename);
                await File.WriteAllBytesAsync(target, bytes, token).ConfigureAwait(false);
                if (!copied.TryAdd(filename, target)
                    && !File.ReadAllBytes(copied[filename]).AsSpan().SequenceEqual(File.ReadAllBytes(target)))
                {
                    throw new InvalidDataException("Prepared catalog owners contain different copies of " + filename + ".");
                }
            }
            references.Add(new XElement("Reference", new XAttribute("Include", name),
                new XElement("HintPath", Path.Combine(destination, Path.GetFileName(source)))));
        }
        string bindings = Path.Combine(build, "bindings.props");
        new XDocument(new XElement("Project", references)).Save(bindings);
        xml.Save(project);
        File.Copy(Path.Combine(Path.GetDirectoryName(template)!, "Program.cs"), Path.Combine(build, "Program.cs"));
        string output = Path.Combine(build, "output");
        string auditPath = Environment.GetEnvironmentVariable("MCPCLI_NATIVE_READER_AUDIT_PATH")
            ?? throw new InvalidOperationException("The isolated reader requires its retained online graph audit.");
        string auditHash = Environment.GetEnvironmentVariable("MCPCLI_NATIVE_READER_AUDIT_SHA256")
            ?? throw new InvalidOperationException("The isolated reader requires its prepared online audit hash.");
        using JsonDocument audit = NativeCatalogAudit.Load(repositoryRoot.FullName, auditPath, auditHash, sdkVersion);
        // Restore only metadata before checking the retained audit and the actual package bytes compilation will consume.
        string[] properties = ["-p:GeneratePackageOnBuild=false", "-p:NuGetAudit=false", "-p:CentralPackageVersionsFileImported=true",
            "-p:UseHexalithProjectReferences=false", "-p:HexalithEventStoreVersion=" + sdkVersion,
            "-p:PlatformCatalogBindings=" + bindings, "--nologo", "-warnaserror"];
        await RunAsync(build, "restore.log", ["restore", project, "-p:Configuration=Release", .. properties], token, dotnetExecutable).ConfigureAwait(false);
        Dictionary<string, string> auditedPackageGraph;
        using (JsonDocument assets = JsonDocument.Parse(await File.ReadAllBytesAsync(Path.Combine(build, "obj", "project.assets.json"), token).ConfigureAwait(false)))
        {
            auditedPackageGraph = NativeCatalogAudit.RequireCoverage(assets.RootElement, audit.RootElement);
            JsonProperty[] sdk = assets.RootElement.GetProperty("libraries").EnumerateObject()
                .Where(library => library.Name.StartsWith("Hexalith.EventStore.", StringComparison.Ordinal)).ToArray();
            if (sdk.Length == 0 || sdk.Any(library => library.Name[(library.Name.LastIndexOf('/') + 1)..] != sdkVersion
                || library.Value.GetProperty("type").GetString() != "package"))
            {
                throw new InvalidDataException("The actual private catalog reader did not restore the exact published SDK cohort.");
            }
        }
        await RunAsync(build, "build.log", ["build", project, "--no-restore", "-c", "Release", "-m:1", "--output", output,
            .. properties], token, dotnetExecutable).ConfigureAwait(false);
        foreach ((string filename, string source) in copied)
        {
            string target = Path.Combine(output, filename);
            if (File.Exists(target))
            {
                if (!File.ReadAllBytes(source).AsSpan().SequenceEqual(File.ReadAllBytes(target)))
                {
                    throw new InvalidDataException("The catalog reader restored a different prepared runtime binary: " + filename + ".");
                }
            }
            else
            {
                File.Copy(source, target);
            }
        }
        string request = Path.Combine(build, "request.json");
        await File.WriteAllBytesAsync(request, JsonSerializer.SerializeToUtf8Bytes(new
        {
            generation = 1, instanceId, outputDirectory = directory, gatewayAppId,
            owners = owners.Select(owner => new
            {
                assembly = AssemblyName.GetAssemblyName(owner.OwnerPath).Name!,
                adapterAssembly = AssemblyName.GetAssemblyName(owner.AdapterPath).Name!,
                appId = owner.AppId,
            }),
        }), token).ConfigureAwait(false);
        await RunAsync(build, "generation.log", [Path.Combine(output, "Hexalith.Platform.CatalogBuilder.dll"), request], token, dotnetExecutable).ConfigureAwait(false);
        foreach ((string path, string digest) in inputHashes)
        {
            if (Convert.ToHexStringLower(SHA256.HashData(await File.ReadAllBytesAsync(path, token).ConfigureAwait(false))) != digest)
                throw new InvalidDataException("A separately prepared owner dependency changed during catalog generation.");
        }
        await File.WriteAllBytesAsync(Path.Combine(build, "preparation.json"), JsonSerializer.SerializeToUtf8Bytes(new
        {
            instanceId, gatewayAppId, sdkVersion,
            auditReceiptSha256 = auditHash, auditedPackageGraph,
            templateSource = template,
            templateProjectSha256 = Digest(File.ReadAllBytes(template)),
            readerProjectSha256 = Digest(File.ReadAllBytes(project)),
            globalJsonSha256 = Digest(File.ReadAllBytes(Path.Combine(build, "global.json"))),
            bindingsSha256 = Digest(File.ReadAllBytes(bindings)),
            templateHash = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(Path.Combine(build, "Program.cs")))),
            inputHashes,
        }), token).ConfigureAwait(false);
        return JsonDocument.Parse(await File.ReadAllBytesAsync(Path.Combine(directory, "receipt.json"), token).ConfigureAwait(false));
    }

    /// <summary>Places the exact root SDK policy in the private reader ancestry before invoking dotnet.</summary>
    internal static void PrepareBuildDirectory(string repositoryRoot, string build)
    {
        CreatePrivateDirectory(build);
        File.Copy(Path.Combine(repositoryRoot, "global.json"), Path.Combine(build, "global.json"));
    }

    /// <summary>Creates a private run-owned directory without broadening existing permissions.</summary>
    internal static void CreatePrivateDirectory(string path)
    {
        if (Path.Exists(path) || new DirectoryInfo(path).LinkTarget is not null)
        {
            throw new InvalidDataException("A catalog preparation directory is already occupied.");
        }
        Directory.CreateDirectory(path);
        if (!OperatingSystem.IsWindows())
        {
            File.SetUnixFileMode(path, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
        }
    }

    /// <summary>Runs preparation in a new owned directory and removes it after a fully stopped preparation failure.</summary>
    internal static async Task RunOwnedPreparationAsync(string path, string owner, Func<Task> prepare)
    {
        CreatePrivateDirectory(path);
        try { File.WriteAllText(Path.Combine(path, ".owner"), owner); }
        catch (Exception failure)
        {
            await NativeCatalogCleanup.RunAsync(failure, () => { Directory.Delete(path, recursive: false); return ValueTask.CompletedTask; }).ConfigureAwait(false);
            throw;
        }
        try { await prepare().ConfigureAwait(false); }
        catch (Exception failure)
        {
            string diagnostics = NativeCatalogDiagnostics.Read(path);
            if (diagnostics.Length > 0)
            {
                failure.Data["NativeCatalogDiagnostics"] = diagnostics;
                try { Console.Error.WriteLine(diagnostics); }
                catch (Exception diagnosticFailure) when (diagnosticFailure is IOException or ObjectDisposedException)
                {
                    failure.Data["CatalogDiagnosticOutputFailure"] = diagnosticFailure.GetType().Name;
                }
            }
            await NativeCatalogCleanup.RunAsync(failure, () =>
            {
                if (!failure.Data.Contains("CatalogOwnedProcessStillRunning")) DeleteOwnedDirectory(path, owner);
                return ValueTask.CompletedTask;
            }).ConfigureAwait(false);
            throw;
        }
    }

    /// <summary>Deletes only a preparation directory whose private ownership marker still matches this run.</summary>
    internal static void DeleteOwnedDirectory(string path, string owner)
    {
        if (!Directory.Exists(path)) { return; }
        string marker = Path.Combine(path, ".owner");
        if (new DirectoryInfo(path).LinkTarget is not null || new FileInfo(marker).LinkTarget is not null
            || !File.Exists(marker) || File.ReadAllText(marker) != owner)
        {
            throw new InvalidDataException("A foreign preparation directory must not be deleted.");
        }
        Directory.Delete(path, recursive: true);
    }

    /// <summary>Marks ownership before termination attempts and clears it only after confirmed exit.</summary>
    internal static async Task ConfirmTerminationAsync(Action kill, Func<CancellationToken, Task> wait, Exception failure)
    {
        failure.Data["CatalogOwnedProcessStillRunning"] = true;
        try { kill(); }
        catch (Exception cleanupFailure) { failure.Data["CatalogKillFailure"] = cleanupFailure.GetType().Name; }
        using var cleanup = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        try
        {
            await wait(cleanup.Token).ConfigureAwait(false);
            failure.Data.Remove("CatalogOwnedProcessStillRunning");
        }
        catch (Exception cleanupFailure) { failure.Data["CatalogExitConfirmationFailure"] = cleanupFailure.GetType().Name; }
    }

    private static async Task<string> ReadDiagnosticsAsync(StreamReader reader, CancellationToken token)
    {
        var retained = new StringBuilder();
        char[] buffer = new char[2048];
        try
        {
            int count;
            while ((count = await reader.ReadAsync(buffer, token).ConfigureAwait(false)) > 0)
                if (retained.Length < 8192) retained.Append(buffer, 0, Math.Min(count, 8192 - retained.Length));
        }
        catch (Exception failure) when (failure is OperationCanceledException or IOException or ObjectDisposedException) { }
        return NativeCatalogDiagnostics.Sanitize(retained.ToString());
    }

    private static async Task RunAsync(string directory, string log, IReadOnlyList<string> arguments, CancellationToken token, string dotnetExecutable)
    {
        ProcessStartInfo start = new(dotnetExecutable)
        {
            WorkingDirectory = directory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false,
        };
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        token.ThrowIfCancellationRequested();
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("The actual catalog executable did not start.");
        using var capture = CancellationTokenSource.CreateLinkedTokenSource(token);
        Task<string> output = ReadDiagnosticsAsync(process.StandardOutput, capture.Token);
        Task<string> error = ReadDiagnosticsAsync(process.StandardError, capture.Token);
        Exception? failure = null;
        try { await process.WaitForExitAsync(token).ConfigureAwait(false); }
        catch (Exception original)
        {
            failure = original;
            await ConfirmTerminationAsync(() => process.Kill(entireProcessTree: true),
                cancellation => process.WaitForExitAsync(cancellation), original).ConfigureAwait(false);
            await capture.CancelAsync().ConfigureAwait(false);
        }
        string diagnostics = string.Empty;
        try { diagnostics = string.Join(Environment.NewLine, await Task.WhenAll(output, error).WaitAsync(TimeSpan.FromSeconds(2)).ConfigureAwait(false)); }
        catch (Exception diagnosticFailure)
        {
            failure ??= diagnosticFailure;
            if (diagnosticFailure is TimeoutException) failure.Data["CatalogOwnedProcessStillRunning"] = true;
        }
        diagnostics = NativeCatalogDiagnostics.Sanitize(diagnostics);
        try { File.WriteAllText(Path.Combine(directory, log), diagnostics); }
        catch (Exception logFailure)
        {
            if (failure is null) failure = logFailure;
            else failure.Data["CatalogDiagnosticWriteFailure"] = logFailure.GetType().Name;
        }
        if (failure is not null) ExceptionDispatchInfo.Capture(failure).Throw();
        if (process.ExitCode != 0)
            throw new InvalidDataException("The actual Platform catalog tool refused preparation. " + diagnostics);
    }

    private static string Digest(byte[] bytes) => Convert.ToHexStringLower(SHA256.HashData(bytes));
}

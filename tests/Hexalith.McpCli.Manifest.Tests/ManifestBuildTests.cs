using System.Diagnostics;
using System.IO.Compression;
using System.Security;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>
/// Verifies that package enrollment is resolved from copy-local package assets.
/// </summary>
public sealed class ManifestBuildTests
{
    private static readonly string SampleAssembly = typeof(SampleSerializerOptions).Assembly.Location;
    private static readonly string MarkedEmptyAssembly = typeof(global::Manifest.MarkedEmpty.Contracts.Module).Assembly.Location;
    private static readonly string UnmarkedAssembly = typeof(global::Manifest.Unmarked.Contracts.Placeholder).Assembly.Location;

    /// <summary>Checks ordering, marker independence, excluded references, and repeatability.</summary>
    [Fact]
    public void FlaggedPackagesProduceStableSortedManifest()
    {
        string root = CreateFixtureRoot();
        try
        {
            string feed = Path.Combine(root, "feed");
            CreatePackage(feed, "Hexalith.McpCli.Sample.Contracts", (SampleAssembly, "lib/net10.0/Hexalith.McpCli.Sample.Contracts.dll"));
            CreatePackage(feed, "Manifest.MarkedEmpty.Contracts", (MarkedEmptyAssembly, "lib/net10.0/Manifest.MarkedEmpty.Contracts.dll"));
            CreatePackage(feed, "Manifest.Unmarked.Contracts", (UnmarkedAssembly, "lib/net10.0/manifest.AUnmarked.Contracts.dll"));
            string project = WriteProject(root,
                ("Manifest.Unmarked.Contracts", true),
                ("Manifest.MarkedEmpty.Contracts", true),
                ("Hexalith.McpCli.Sample.Contracts", true));
            RunDotnet(root, true, "restore", project, "--source", feed);
            RunDotnet(root, true, "build", project, "--no-restore", "--configuration", "Release");

            string manifest = ManifestPath(root);
            byte[] first = File.ReadAllBytes(manifest);
            string generated = Encoding.UTF8.GetString(first);
            generated.ShouldContain("\r\n");
            generated.Replace("\r\n", string.Empty, StringComparison.Ordinal).ShouldNotContain("\n");
            ReadEntries(manifest).ShouldBe(new[]
            {
                ("Hexalith.McpCli.Sample.Contracts", "Hexalith.McpCli.Sample.Contracts"),
                ("Manifest.MarkedEmpty.Contracts", "Manifest.MarkedEmpty.Contracts"),
                ("Manifest.Unmarked.Contracts", "manifest.AUnmarked.Contracts"),
            });

            RunDotnet(root, true, "build", project, "--no-restore", "--configuration", "Release");
            File.ReadAllBytes(manifest).ShouldBe(first);
            RunDotnet(root, true, "clean", project, "--configuration", "Release");
            File.Exists(manifest).ShouldBeFalse();
            RunDotnet(root, true, "build", project, "--no-restore", "--configuration", "Release", "-p:DesignTimeBuild=true");
            File.Exists(manifest).ShouldBeTrue();
            string compileItems = RunDotnet(root, true, "msbuild", project, "-getItem:Compile", "-p:Configuration=Release", "-p:DesignTimeBuild=true");
            using (JsonDocument document = JsonDocument.Parse(compileItems))
            {
                document.RootElement.GetProperty("Items").GetProperty("Compile").EnumerateArray()
                    .Any(item => string.Equals(item.GetProperty("FullPath").GetString(), manifest, StringComparison.OrdinalIgnoreCase))
                    .ShouldBeTrue();
            }

            // Changing only the direct flag must remove the unmarked package's entry.
            WriteProject(root,
                ("Manifest.Unmarked.Contracts", false),
                ("Manifest.MarkedEmpty.Contracts", true),
                ("Hexalith.McpCli.Sample.Contracts", true));
            RunDotnet(root, true, "restore", project, "--source", feed);
            RunDotnet(root, true, "build", project, "--no-restore", "--configuration", "Release");
            ReadEntries(manifest).ShouldBe(new[]
            {
                ("Hexalith.McpCli.Sample.Contracts", "Hexalith.McpCli.Sample.Contracts"),
                ("Manifest.MarkedEmpty.Contracts", "Manifest.MarkedEmpty.Contracts"),
            });
            byte[] withUnflaggedReference = File.ReadAllBytes(manifest);
            RunDotnet(root, true, "build", project, "--no-restore", "--configuration", "Release");
            File.ReadAllBytes(manifest).ShouldBe(withUnflaggedReference);
            string missingFlag = RunDotnet(root, false, "build", project, "--no-restore", "--configuration", "Release", "-p:RequireContractsFlag=true");
            missingFlag.ShouldContain("Manifest.Unmarked.Contracts");
            missingFlag.ShouldContain("must declare HexalithContracts");
            File.Exists(manifest).ShouldBeFalse();
        }
        finally
        {
            Directory.Delete(root, true);
        }
    }

    /// <summary>Checks a flagged package with no copy-local Contracts DLL fails.</summary>
    [Fact]
    public void MissingContractsAssetFailsWithPackageAndCount()
    {
        string root = CreateFixtureRoot();
        try
        {
            string feed = Path.Combine(root, "feed");
            CreatePackage(feed, "Manifest.MarkedEmpty.Contracts", (MarkedEmptyAssembly, "lib/net10.0/Manifest.MarkedEmpty.Contracts.dll"));
            CreatePackage(feed, "Manifest.Zero.Contracts", (UnmarkedAssembly, "lib/net10.0/Unrelated.dll"));
            string project = WriteProject(root, ("Manifest.MarkedEmpty.Contracts", true));
            RunDotnet(root, true, "restore", project, "--source", feed);
            RunDotnet(root, true, "build", project, "--no-restore", "--configuration", "Release");
            File.Exists(ManifestPath(root)).ShouldBeTrue();
            WriteProject(root, ("Manifest.Zero.Contracts", true));
            RunDotnet(root, true, "restore", project, "--source", feed);
            string output = RunDotnet(root, false, "build", project, "--no-restore", "--configuration", "Release");
            output.ShouldContain("Manifest.Zero.Contracts");
            output.ShouldContain("0 matching *.Contracts.dll");
            File.Exists(ManifestPath(root)).ShouldBeFalse();
        }
        finally
        {
            Directory.Delete(root, true);
        }
    }

    /// <summary>Checks a flagged package with two copy-local Contracts DLLs fails.</summary>
    [Fact]
    public void AmbiguousContractsAssetsFailWithPackageAndCount()
    {
        string root = CreateFixtureRoot();
        try
        {
            string feed = Path.Combine(root, "feed");
            CreatePackage(feed, "Manifest.MarkedEmpty.Contracts", (MarkedEmptyAssembly, "lib/net10.0/Manifest.MarkedEmpty.Contracts.dll"));
            CreatePackage(feed, "Manifest.Ambiguous.Contracts",
                (SampleAssembly, "lib/net10.0/Hexalith.McpCli.Sample.Contracts.dll"),
                (MarkedEmptyAssembly, "lib/net10.0/Manifest.MarkedEmpty.Contracts.dll"));
            string project = WriteProject(root, ("Manifest.MarkedEmpty.Contracts", true));
            RunDotnet(root, true, "restore", project, "--source", feed);
            RunDotnet(root, true, "build", project, "--no-restore", "--configuration", "Release");
            File.Exists(ManifestPath(root)).ShouldBeTrue();
            WriteProject(root, ("Manifest.Ambiguous.Contracts", true));
            RunDotnet(root, true, "restore", project, "--source", feed);
            string output = RunDotnet(root, false, "build", project, "--no-restore", "--configuration", "Release");
            output.ShouldContain("Manifest.Ambiguous.Contracts");
            output.ShouldContain("2 matching *.Contracts.dll");
            File.Exists(ManifestPath(root)).ShouldBeFalse();
        }
        finally
        {
            Directory.Delete(root, true);
        }
    }

    /// <summary>Rejects a package asset renamed away from its assembly identity.</summary>
    [Fact]
    public void RenamedContractsAssetFailsWithPackageIdentity()
    {
        string root = CreateFixtureRoot();
        try
        {
            string feed = Path.Combine(root, "feed");
            CreatePackage(feed, "Manifest.Renamed.Contracts", (UnmarkedAssembly, "lib/net10.0/Manifest.Renamed.Contracts.dll"));
            string project = WriteProject(root, ("Manifest.Renamed.Contracts", true));
            RunDotnet(root, true, "restore", project, "--source", feed);
            string output = RunDotnet(root, false, "build", project, "--no-restore", "--configuration", "Release");
            output.ShouldContain("Manifest.Renamed.Contracts");
            output.ShouldContain("assembly identity 'manifest.AUnmarked.Contracts'");
            File.Exists(ManifestPath(root)).ShouldBeFalse();
        }
        finally
        {
            Directory.Delete(root, true);
        }
    }

    /// <summary>Matches a differently cased direct package reference to its resolved package identity.</summary>
    [Fact]
    public void PackageIdMatchingUsesResolvedIdentity()
    {
        string root = CreateFixtureRoot();
        try
        {
            string feed = Path.Combine(root, "feed");
            CreatePackage(feed, "Manifest.Unmarked.Contracts", (UnmarkedAssembly, "lib/net10.0/manifest.AUnmarked.Contracts.dll"));
            string project = WriteProject(root, ("manifest.unmarked.contracts", true));
            RunDotnet(root, true, "restore", project, "--source", feed);
            RunDotnet(root, true, "build", project, "--no-restore", "--configuration", "Release");
            ReadEntries(ManifestPath(root)).ShouldBe(new[]
            {
                ("Manifest.Unmarked.Contracts", "manifest.AUnmarked.Contracts"),
            });
        }
        finally
        {
            Directory.Delete(root, true);
        }
    }

    /// <summary>Checks the real shipping project requires explicit Contracts enrollment.</summary>
    [Fact]
    public void ShippingProjectRequiresContractsFlag()
    {
        string repositoryRoot = FindRepositoryRoot();
        string project = Path.Combine(repositoryRoot, "src", "Hexalith.McpCli", "Hexalith.McpCli.csproj");
        RunDotnet(repositoryRoot, true, "msbuild", project, "-getProperty:RequireContractsFlag").Trim().ShouldBe("true");
    }

    private static string CreateFixtureRoot()
    {
        string path = Path.Combine(Path.GetTempPath(), "mcpcli-manifest-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        string repositoryRoot = FindRepositoryRoot();
        File.Copy(Path.Combine(repositoryRoot, "global.json"), Path.Combine(path, "global.json"));
        File.WriteAllText(Path.Combine(path, "Directory.Build.props"), "<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup></Project>");
        File.WriteAllText(Path.Combine(path, "Directory.Build.targets"), "<Project />");
        File.WriteAllText(Path.Combine(path, "Directory.Packages.props"), "<Project><PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup><ItemGroup><PackageVersion Include=\"Hexalith.McpCli.Sample.Contracts\" Version=\"1.0.0\" /><PackageVersion Include=\"Manifest.MarkedEmpty.Contracts\" Version=\"1.0.0\" /><PackageVersion Include=\"Manifest.Unmarked.Contracts\" Version=\"1.0.0\" /><PackageVersion Include=\"Manifest.Zero.Contracts\" Version=\"1.0.0\" /><PackageVersion Include=\"Manifest.Ambiguous.Contracts\" Version=\"1.0.0\" /><PackageVersion Include=\"Manifest.Renamed.Contracts\" Version=\"1.0.0\" /></ItemGroup></Project>");
        return path;
    }

    private static void CreatePackage(string feed, string packageId, params (string Source, string Entry)[] assets)
    {
        Directory.CreateDirectory(feed);
        using ZipArchive archive = ZipFile.Open(Path.Combine(feed, packageId + ".1.0.0.nupkg"), ZipArchiveMode.Create);
        ZipArchiveEntry nuspec = archive.CreateEntry(packageId + ".nuspec");
        using (StreamWriter writer = new(nuspec.Open(), new UTF8Encoding(false)))
        {
            writer.Write($"<?xml version=\"1.0\"?><package xmlns=\"http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd\"><metadata><id>{packageId}</id><version>1.0.0</version><authors>Tests</authors><description>Manifest fixture</description></metadata></package>");
        }

        foreach ((string source, string entry) in assets)
        {
            archive.CreateEntryFromFile(source, entry);
        }
    }

    private static string WriteProject(string root, params (string PackageId, bool Flagged)[] packages)
    {
        string targets = FindTargetsPath();
        StringBuilder project = new();
        project.Append("<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup><ItemGroup>");
        foreach ((string id, bool flagged) in packages)
        {
            project.Append("<PackageReference Include=\"").Append(id).Append("\" HexalithContracts=\"").Append(flagged ? "true" : "false").Append("\" />");
        }

        project.Append("</ItemGroup><Import Project=\"").Append(SecurityElement.Escape(targets)).Append("\" /></Project>");
        string path = Path.Combine(root, "ManifestFixture.csproj");
        File.WriteAllText(path, project.ToString());
        File.WriteAllText(Path.Combine(root, "Program.cs"), "using Hexalith.McpCli.Hosting;\ninternal static class Program { private static void Main() { System.Console.WriteLine(ModuleAssemblyManifest.Entries.Length); } }\n");
        return path;
    }

    private static string FindTargetsPath()
        => Path.Combine(FindRepositoryRoot(), "src", "Hexalith.McpCli", "Build", "ModuleAssemblyManifest.targets");

    private static string FindRepositoryRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null && !File.Exists(Path.Combine(current.FullName, "Hexalith.McpCli.slnx")))
        {
            current = current.Parent;
        }

        current.ShouldNotBeNull();
        return current.FullName;
    }

    private static string ManifestPath(string root)
        => Path.Combine(root, "obj", "Release", "net10.0", "ModuleAssemblyManifest.g.cs");

    private static (string PackageId, string AssemblyName)[] ReadEntries(string path)
        => Regex.Matches(File.ReadAllText(path), "\\(\"(?<id>[^\"]+)\", \"(?<name>[^\"]+)\"\\)")
            .Select(match => (match.Groups["id"].Value, match.Groups["name"].Value))
            .ToArray();

    private static string RunDotnet(string workingDirectory, bool expectSuccess, params string[] arguments)
    {
        using Process process = new()
        {
            StartInfo = new ProcessStartInfo("dotnet")
            {
                WorkingDirectory = workingDirectory,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
            },
        };
        foreach (string argument in arguments)
        {
            process.StartInfo.ArgumentList.Add(argument);
        }

        process.StartInfo.Environment["NUGET_PACKAGES"] = Path.Combine(workingDirectory, "packages");
        process.Start();
        Task<string> stdout = process.StandardOutput.ReadToEndAsync();
        Task<string> stderr = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(180_000))
        {
            process.Kill(entireProcessTree: true);
            process.WaitForExit();
            throw new TimeoutException($"dotnet {string.Join(' ', arguments)} timed out after three minutes.");
        }

        string output = stdout.GetAwaiter().GetResult() + stderr.GetAwaiter().GetResult();
        if (expectSuccess)
        {
            process.ExitCode.ShouldBe(0, output);
        }
        else
        {
            process.ExitCode.ShouldNotBe(0, output);
        }

        return output;
    }
}

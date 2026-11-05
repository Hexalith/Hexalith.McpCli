using System.Security.Cryptography;
using System.Text.Json;
using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;
using Hexalith.EventStore.Aspire;

string project = args[0];
string output = args[1];
string reportPath = args[2];
Dictionary<string, string> Hashes() => Directory.EnumerateFiles(output).Where(p => p.EndsWith(".dll") || p.EndsWith(".json"))
    .ToDictionary(p => Path.GetFileName(p)!, p => Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(p))))!;
var before = Hashes();
var builder = DistributedApplication.CreateBuilder(new DistributedApplicationOptions { Args = [], ProjectDirectory = Path.GetDirectoryName(project) });
var owner = builder.AddProject("tenants-owner-probe", project)
    .WithEnvironment("UseHexalithProjectReferences", "false")
    .WithEnvironment("UseNuGetDeps", "true")
    .WithEnvironment("HexalithEventStoreFromSource", "false")
    .WithEnvironment("HexalithEventStoreVersion", "4.1.0");
using var deadline = new CancellationTokenSource(TimeSpan.FromMinutes(3));
await using var prepared = await owner.PrepareEventStoreDevelopmentOwnerAsync("Hexalith.Tenants.Contracts.dll", "Hexalith.Tenants.Server.dll", TimeSpan.FromMinutes(3), deadline.Token);
var after = Hashes();
var differences = before.Keys.Union(after.Keys).Where(k => before.GetValueOrDefault(k) != after.GetValueOrDefault(k)).ToArray();
string receipt = File.ReadAllText(Path.Combine(prepared.Directory, "preparation.json"));
File.WriteAllText(reportPath, JsonSerializer.Serialize(new { before, after, differences, preparation = JsonDocument.Parse(receipt).RootElement }, new JsonSerializerOptions { WriteIndented = true }));
if (differences.Length > 0) throw new InvalidOperationException("SDK preparation changed deployed bytes: " + string.Join(", ", differences));
Console.WriteLine($"SDK4.1 owner preparation preserved all {before.Count} deployed DLL/configuration files.");

using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Security.Cryptography;

namespace Hexalith.McpCli.AppHost;

/// <summary>Validates the source and local runtime boundary before starting the test topology.</summary>
internal static class TopologyConfiguration
{
    /// <summary>Requires current fixture JSON to come from the trusted .NET 11 shared runtime.</summary>
    internal static void RequireCurrentManagedRuntime()
    {
        if (!string.Equals(Environment.GetEnvironmentVariable("McpCliCurrentNativeProfile"), "true", StringComparison.OrdinalIgnoreCase)) return;
        Version jsonVersion = typeof(JsonElement).Assembly.GetName().Version!;
        string corePath = typeof(object).Assembly.Location;
        string jsonPath = typeof(JsonElement).Assembly.Location;
        ValidateCurrentManagedRuntime(Environment.Version, jsonVersion, corePath, jsonPath);
        Console.WriteLine($"Current native managed runtime: {Environment.Version}; Core: {corePath}; JsonElement: {jsonPath}");
    }

    /// <summary>Rejects a NuGet or alternate runtime JSON image before the strict child loader runs.</summary>
    internal static void ValidateCurrentManagedRuntime(Version runtime, Version json, string corePath, string jsonPath)
    {
        if (runtime != new Version(11, 0, 0) || json != new Version(11, 0, 0, 0))
            throw new InvalidOperationException("The current native fixture requires the exact .NET 11.0.0 runtime and System.Text.Json 11 identity.");
        if (!string.Equals(Path.GetDirectoryName(Path.GetFullPath(corePath)), Path.GetDirectoryName(Path.GetFullPath(jsonPath)), StringComparison.Ordinal))
            throw new InvalidOperationException("The current native fixture requires JsonElement from the actual trusted shared runtime directory.");
    }

    /// <summary>Requires the immutable wrapper-owned empty backup before catalog or writer mutation.</summary>
    internal static string VerifyFreshBackup(string receiptPath)
    {
        using JsonDocument proof = JsonDocument.Parse(File.ReadAllText(receiptPath), new JsonDocumentOptions { AllowDuplicateProperties = false });
        JsonElement root = proof.RootElement;
        if (root.GetProperty("databaseSize").GetInt32() != 0 || !root.GetProperty("createdBeforeApplications").GetBoolean())
            throw new InvalidOperationException("Writer bootstrap requires the wrapper's empty pre-application Redis backup.");
        string backup = root.GetProperty("backupFile").GetString()!;
        byte[] bytes = File.ReadAllBytes(backup);
        string hash = Convert.ToHexStringLower(SHA256.HashData(bytes));
        if (!bytes.AsSpan().StartsWith("REDIS"u8) || root.GetProperty("sha256").GetString() != hash
            || Path.GetDirectoryName(Path.GetFullPath(backup)) != Path.GetDirectoryName(Path.GetFullPath(receiptPath)))
            throw new InvalidOperationException("Writer bootstrap backup bytes or location do not match the private receipt.");
        return $"sha256:{hash};file:{Path.GetFullPath(backup)}";
    }

    /// <summary>The private test administrator configured for the server-owned bootstrap.</summary>
    internal const string BootstrapAdministratorId = "mcpcli-live-admin";

    /// <summary>Requires authentic bootstrap for exactly the identity used by the private fixture.</summary>
    internal static void ValidateBootstrap(bool enabled, string? userId)
    {
        if (!enabled || userId != BootstrapAdministratorId)
            throw new InvalidOperationException($"Tenants bootstrap must be enabled for the test-owned administrator '{BootstrapAdministratorId}'.");
    }

    /// <summary>The Dapr applications owned by this topology.</summary>
    internal static readonly string[] ApplicationIds = ["eventstore", "tenants", "parties"];

    /// <summary>The root source checkouts required by the published helpers.</summary>
    internal static readonly string[] Modules = ["Hexalith.EventStore", "Hexalith.Tenants", "Hexalith.Parties"];

    /// <summary>Resolves the explicit package compatibility host before registration; publish keeps the native host.</summary>
    internal static string ResolveGatewayProject(string root, bool usePackagedGateway, bool isPublishMode)
    {
        string project = usePackagedGateway && !isPublishMode
            ? Path.Combine(root, "tests", "Hexalith.McpCli.EventStoreGateway.TestHost", "Hexalith.McpCli.EventStoreGateway.TestHost.csproj")
            : Path.Combine(root, "references", "Hexalith.EventStore", "src", "Hexalith.EventStore", "Hexalith.EventStore.csproj");
        return File.Exists(project) ? project
            : throw new InvalidOperationException($"Required selected Gateway project '{project}' is missing; no alternate host was selected.");
    }

    /// <summary>Requires each server to come from its declared direct root checkout.</summary>
    internal static void ValidateWorkspace(string root)
    {
        string modulesPath = Path.Combine(root, ".gitmodules");
        var declared = new HashSet<string>(StringComparer.Ordinal);
        bool inSubmodule = false;
        foreach (string line in File.Exists(modulesPath) ? File.ReadLines(modulesPath) : [])
        {
            string text = line.Trim();
            if (text.StartsWith('['))
            {
                inSubmodule = text.StartsWith("[submodule ", StringComparison.Ordinal) && text.EndsWith(']');
            }
            else if (inSubmodule)
            {
                int separator = text.IndexOf('=');
                if (separator >= 0 && text[..separator].Trim() == "path")
                {
                    declared.Add(text[(separator + 1)..].Trim().Trim('"'));
                }
            }
        }

        foreach (string module in Modules)
        {
            string relative = "references/" + module;
            string checkout = Path.Combine(root, "references", module);
            string project = Path.Combine(checkout, "src", module, module + ".csproj");
            if (!declared.Contains(relative))
            {
                throw new InvalidOperationException($"Required root checkout '{relative}' is not declared in '{modulesPath}'. Required project: '{project}'.");
            }

            if (!File.Exists(project))
            {
                throw new InvalidOperationException($"Required root source project '{project}' is missing. Initialize only the declared root checkout '{relative}'.");
            }

            if (new DirectoryInfo(checkout).LinkTarget is not null
                || !File.Exists(Path.Combine(checkout, ".git")) && !Directory.Exists(Path.Combine(checkout, ".git")))
            {
                throw new InvalidOperationException($"Required root checkout '{checkout}' must be a direct Git checkout, not a sibling link or copied source directory.");
            }

            var start = new ProcessStartInfo("git") { RedirectStandardOutput = true, RedirectStandardError = true };
            foreach (string argument in new[] { "-C", checkout, "rev-parse", "--show-toplevel" }) start.ArgumentList.Add(argument);
            using Process git = Process.Start(start) ?? throw new InvalidOperationException($"Cannot verify root checkout '{checkout}'.");
            Task<string> output = git.StandardOutput.ReadToEndAsync();
            Task<string> error = git.StandardError.ReadToEndAsync();
            if (!git.WaitForExit(10000))
            {
                git.Kill(entireProcessTree: true);
                throw new TimeoutException($"Root checkout verification exceeded 10 seconds for '{checkout}'.");
            }

            string actual = output.GetAwaiter().GetResult().Trim();
            _ = error.GetAwaiter().GetResult();
            if (git.ExitCode != 0 || string.IsNullOrWhiteSpace(actual)
                || !Path.GetFullPath(actual).Equals(Path.GetFullPath(checkout),
                    OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal))
            {
                throw new InvalidOperationException($"Required root checkout '{checkout}' is not its own Git working tree.");
            }
        }
    }

    /// <summary>Requires an explicit signing key suitable for the platform's Development JWT validation.</summary>
    internal static void ValidateSigningKey(string? key)
    {
        if (string.IsNullOrWhiteSpace(key) || Encoding.UTF8.GetByteCount(key) < 32)
        {
            throw new InvalidOperationException("Authentication:JwtBearer:SigningKey must contain at least 32 UTF-8 bytes for the Development test topology.");
        }
    }

    /// <summary>Rejects a requested topology whose Dapr identities are already in use.</summary>
    internal static void ValidateRunningApplications(string snapshot)
    {
        using JsonDocument document = JsonDocument.Parse(snapshot);
        if (document.RootElement.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidOperationException("Cannot validate topology conflicts: 'dapr list --output json' must return an array.");
        }

        var applications = new HashSet<string>(StringComparer.Ordinal);
        int index = 0;
        foreach (JsonElement item in document.RootElement.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Object || !item.TryGetProperty("appId", out JsonElement identity)
                || identity.ValueKind != JsonValueKind.String || string.IsNullOrWhiteSpace(identity.GetString()))
            {
                throw new InvalidOperationException($"Cannot validate topology conflicts: Dapr entry {index} must be an object with a non-empty string 'appId'.");
            }

            applications.Add(identity.GetString()!);
            index++;
        }

        string[] conflicts = applications.Where(id => ApplicationIds.Contains(id, StringComparer.Ordinal))
            .Order(StringComparer.Ordinal).ToArray();
        if (conflicts.Length > 0)
        {
            throw new InvalidOperationException($"Conflicting Dapr application IDs: {string.Join(", ", conflicts)}. The requested test topology cannot start alongside these applications.");
        }
    }

    /// <summary>Checks live Dapr registrations and the Gateway sidecar port without altering existing processes.</summary>
    internal static void EnsureNoConflictingTopology(int gatewayPort)
    {
        var start = new ProcessStartInfo("dapr") { RedirectStandardOutput = true, RedirectStandardError = true };
        start.ArgumentList.Add("list");
        start.ArgumentList.Add("--output");
        start.ArgumentList.Add("json");
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Could not run 'dapr list --output json' to check topology conflicts.");
        Task<string> output = process.StandardOutput.ReadToEndAsync();
        Task<string> error = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(10000))
        {
            process.Kill(entireProcessTree: true);
            throw new TimeoutException("Topology conflict check 'dapr list --output json' exceeded 10 seconds.");
        }

        if (process.ExitCode != 0)
        {
            string detail = error.GetAwaiter().GetResult().Trim();
            if (detail.Length > 512) detail = detail[..512] + "...";
            throw new InvalidOperationException($"Topology conflict check 'dapr list --output json' exited {process.ExitCode}. stderr: {detail}");
        }

        ValidateRunningApplications(output.GetAwaiter().GetResult());
        _ = error.GetAwaiter().GetResult();
        ValidateGatewayPort(gatewayPort);
    }

    /// <summary>Rejects an occupied or invalid Gateway sidecar port before launch.</summary>
    internal static void ValidateGatewayPort(int port)
    {
        if (port is < 1024 or > 65535)
        {
            throw new InvalidOperationException("Dapr:GatewayHttpPort must be between 1024 and 65535.");
        }

        using var listener = new TcpListener(IPAddress.Loopback, port);
        try
        {
            listener.Start();
        }
        catch (SocketException exception)
        {
            throw new InvalidOperationException($"Gateway Dapr HTTP port {port} is already in use; the test topology cannot start.", exception);
        }
    }
}

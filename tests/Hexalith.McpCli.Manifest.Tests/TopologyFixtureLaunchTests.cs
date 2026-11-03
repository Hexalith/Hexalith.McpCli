using System.Diagnostics;
using System.IdentityModel.Tokens.Jwt;
using Microsoft.IdentityModel.Tokens;
using System.Reflection;
using System.Runtime.Loader;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Protects actual fixture environment selection and refusals without starting infrastructure.</summary>
[Collection("TopologyFixtureEnvironment")]
public sealed class TopologyFixtureLaunchTests
{
    /// <summary>Both real fixture consumers select Development before preparation despite inherited production settings.</summary>
    [Theory]
    [InlineData("LiveVectorTests", "Production", "Staging")]
    [InlineData("LiveVectorTests", "Staging", "Production")]
    [InlineData("GatewaySmokeTests", "Production", "Staging")]
    [InlineData("GatewaySmokeTests", "Staging", "Production")]
    public async Task SharedFixtureArgumentsSelectExplicitDevelopment(string consumerName, string dotnetEnvironment, string aspnetEnvironment)
    {
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string assemblyPath = Path.Combine(DependencyPolicyTests.FindRepositoryRoot(), "tests", "Hexalith.McpCli.Integration.Tests",
            "bin", configuration, "net10.0", "Hexalith.McpCli.Integration.Tests.dll");
        var context = new AssemblyLoadContext("fixture-environment-" + Guid.NewGuid().ToString("N"), isCollectible: true);
        var resolver = new AssemblyDependencyResolver(assemblyPath);
        context.Resolving += (_, name) => resolver.ResolveAssemblyToPath(name) is { } path ? context.LoadFromAssemblyPath(path) : null;
        string? priorDotnet = Environment.GetEnvironmentVariable("DOTNET_ENVIRONMENT");
        string? priorAspnet = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT");
        try
        {
            Environment.SetEnvironmentVariable("DOTNET_ENVIRONMENT", dotnetEnvironment);
            Environment.SetEnvironmentVariable("ASPNETCORE_ENVIRONMENT", aspnetEnvironment);
            Assembly integration = context.LoadFromAssemblyPath(assemblyPath);
            Type fixtureType = integration.GetType("Hexalith.McpCli.Integration.Tests.AspireTopologyFixture", throwOnError: true)!;
            Type consumer = integration.GetType("Hexalith.McpCli.Integration.Tests." + consumerName, throwOnError: true)!;
            Assert.Equal(fixtureType, Assert.Single(Assert.Single(consumer.GetConstructors()).GetParameters()).ParameterType);
            Assert.Equal("AspireTopology", Assert.Single(consumer.CustomAttributes,
                attribute => attribute.AttributeType.FullName == "Xunit.CollectionAttribute").ConstructorArguments[0].Value);
            Type collection = integration.GetType("Hexalith.McpCli.Integration.Tests.AspireTopologyCollection", throwOnError: true)!;
            Assert.Contains(collection.GetInterfaces(), item => item.IsGenericType
                && item.GetGenericTypeDefinition().FullName == "Xunit.ICollectionFixture`1" && item.GenericTypeArguments[0] == fixtureType);
            object fixture = Activator.CreateInstance(fixtureType)!;
            string[] arguments = ((IEnumerable<string>)fixtureType.GetProperty("ExtraAppArgs", BindingFlags.Instance | BindingFlags.NonPublic)!
                .GetValue(fixture)!).ToArray();
            Type testingBuilder = context.LoadFromAssemblyName(new AssemblyName("Aspire.Hosting.Testing"))
                .GetType("Aspire.Hosting.Testing.DistributedApplicationTestingBuilder", throwOnError: true)!;
            // Use the pinned factory's builder-only seam with actual AppHost metadata, without invoking its entry point.
            MethodInfo create = Assert.Single(testingBuilder.GetMethods(BindingFlags.NonPublic | BindingFlags.Static),
                method => method.Name == "Create" && method.GetParameters().Length == 3
                    && method.GetParameters()[2].ParameterType == typeof(Assembly));
            Delegate configure = Delegate.CreateDelegate(create.GetParameters()[1].ParameterType,
                typeof(TopologyFixtureLaunchTests).GetMethod(nameof(PreserveBuilderOptions), BindingFlags.NonPublic | BindingFlags.Static)!);
            Assembly appHost = context.LoadFromAssemblyPath(Path.Combine(DependencyPolicyTests.FindRepositoryRoot(), "tests",
                "Hexalith.McpCli.AppHost", "bin", configuration, "net10.0", "Hexalith.McpCli.AppHost.dll"));
            using var reflection = context.EnterContextualReflection();
            foreach (bool explicitDevelopment in new[] { false, true })
            {
                string[] selected = explicitDevelopment ? arguments : arguments.Where(argument => !argument.StartsWith("--environment=", StringComparison.Ordinal)).ToArray();
                await using IAsyncDisposable builder = (IAsyncDisposable)create.Invoke(null, [selected, configure, appHost])!;
                Type builderType = builder.GetType();
                object environment = builderType.GetProperty("Environment")!.GetValue(builder)!;
                Assert.Equal(explicitDevelopment ? "Development" : dotnetEnvironment,
                    environment.GetType().GetProperty("EnvironmentName")!.GetValue(environment));
                object execution = builderType.GetProperty("ExecutionContext")!.GetValue(builder)!;
                Assert.Equal(true, execution.GetType().GetProperty("IsRunMode")!.GetValue(execution));
            }
        }
        finally
        {
            Environment.SetEnvironmentVariable("DOTNET_ENVIRONMENT", priorDotnet);
            Environment.SetEnvironmentVariable("ASPNETCORE_ENVIRONMENT", priorAspnet);
            context.Unload();
        }
    }

    /// <summary>The actual live fixture signs its bounded administrator hint and a forged signature never authenticates.</summary>
    [Theory]
    [InlineData(false, false)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(true, true)]
    public void LiveAdministratorHintRequiresTheActualFixtureSignature(bool forged, bool nonmember)
    {
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string path = Path.Combine(DependencyPolicyTests.FindRepositoryRoot(), "tests", "Hexalith.McpCli.Integration.Tests",
            "bin", configuration, "net10.0", "Hexalith.McpCli.Integration.Tests.dll");
        var context = new AssemblyLoadContext("signed-fixture-" + Guid.NewGuid().ToString("N"), isCollectible: true);
        var resolver = new AssemblyDependencyResolver(path);
        context.Resolving += (_, name) => resolver.ResolveAssemblyToPath(name) is { } resolved ? context.LoadFromAssemblyPath(resolved) : null;
        try
        {
            Type type = context.LoadFromAssemblyPath(path).GetType("Hexalith.McpCli.Integration.Tests.AspireTopologyFixture", throwOnError: true)!;
            object fixture = Activator.CreateInstance(type)!;
            string token = (string)type.GetMethod(nonmember ? "CreateNonmemberIdentity" : "CreateLiveIdentity", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(fixture, null)!;
            string key = (string)type.GetField("_signingKey", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(fixture)!;
            if (forged)
            {
                int start = token.LastIndexOf('.') + 1;
                token = token[..start] + (token[start] == 'A' ? 'B' : 'A') + token[(start + 1)..];
            }
            var handler = new JwtSecurityTokenHandler { MapInboundClaims = false };
            var validation = new TokenValidationParameters
            {
                ValidIssuer = "mcpcli-live-tests", ValidAudience = "hexalith-eventstore", ValidateLifetime = true,
                RequireSignedTokens = true, ValidateIssuerSigningKey = true,
                IssuerSigningKey = new SymmetricSecurityKey(System.Text.Encoding.UTF8.GetBytes(key)),
                ValidAlgorithms = [SecurityAlgorithms.HmacSha256],
            };
            if (forged) Assert.Throws<SecurityTokenSignatureKeyNotFoundException>(() => handler.ValidateToken(token, validation, out _));
            else
            {
                var principal = handler.ValidateToken(token, validation, out _);
                Assert.Equal(nonmember ? "mcpcli-live-nonmember" : "mcpcli-live-admin", principal.FindFirst("sub")!.Value);
                Assert.Equal("GlobalAdministrator", principal.FindFirst("role")!.Value);
                Assert.Equal("agent", principal.FindFirst("eventstore:surface")!.Value);
                Assert.False(principal.HasClaim(claim => claim.Type is "global_admin" or "is_global_admin"));
            }
        }
        finally { context.Unload(); }
    }

    private static void PreserveBuilderOptions(object applicationOptions, object hostOptions) { }

    /// <summary>Direct execution fails closed, and a missing root source retains its required path.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UnsafeOrIncompleteFixtureFailsBeforeInfrastructure(bool isolated)
    {
        string root = Path.Combine(Path.GetTempPath(), "mcpcli-fixture-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(root, "src"));
        string repository = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent!.Name;
        string source = Path.Combine(repository, "tests", "Hexalith.McpCli.Integration.Tests", "bin", configuration, "net10.0");
        string target = Path.Combine(root, "tests", "Hexalith.McpCli.Integration.Tests", "bin", configuration, "net10.0");
        try
        {
            foreach (string file in Directory.EnumerateFiles(source, "*", SearchOption.AllDirectories))
            {
                string destination = Path.Combine(target, Path.GetRelativePath(source, file));
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                File.Copy(file, destination);
            }
            File.WriteAllText(Path.Combine(root, ".gitmodules"), "[submodule \"Hexalith.EventStore\"]\n path = references/Hexalith.EventStore\n");
            string dotnet = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH")
                ?? Path.GetFullPath(Path.Combine(System.Runtime.InteropServices.RuntimeEnvironment.GetRuntimeDirectory(), "..", "..", "..", OperatingSystem.IsWindows() ? "dotnet.exe" : "dotnet"));
            var start = new ProcessStartInfo(dotnet)
            {
                WorkingDirectory = root, RedirectStandardOutput = true, RedirectStandardError = true,
            };
            start.ArgumentList.Add(Path.Combine(target, "Hexalith.McpCli.Integration.Tests.dll"));
            start.ArgumentList.Add("-method");
            start.ArgumentList.Add("*AuthenticatedQueryReturnsSuccessfulDocument");
            start.Environment["MCPCLI_ISOLATED_TOPOLOGY"] = isolated ? "1" : null;
            start.Environment["PATH"] = Path.Combine(root, "no-infrastructure");
            using Process process = Process.Start(start)!;
            Task<string> stdout = process.StandardOutput.ReadToEndAsync(TestContext.Current.CancellationToken);
            Task<string> stderr = process.StandardError.ReadToEndAsync(TestContext.Current.CancellationToken);
            using var deadline = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
            deadline.CancelAfter(TimeSpan.FromSeconds(20));
            try { await process.WaitForExitAsync(deadline.Token); }
            finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
            string output = await stdout;
            Assert.Equal(1, process.ExitCode);
            string error = await stderr;
            string expected = isolated
                ? $"Required root source project '{Path.Combine(root, "references", "Hexalith.EventStore", "src", "Hexalith.EventStore", "Hexalith.EventStore.csproj")}' is missing. Initialize only the declared root checkout 'references/Hexalith.EventStore'."
                : "Live topology tests require tools/live-topology/run-isolated.py; refusing to use host Dapr or Redis.";
            Assert.Equal(string.Empty, error);
            Assert.Contains(expected, output);
            Assert.Contains("Failed: 1, Skipped: 0", output);
            Assert.DoesNotContain("DAPR integration prerequisites are unavailable", output + error);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }
}

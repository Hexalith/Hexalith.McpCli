using System.Reflection;
using System.Reflection.Emit;
using System.Text.Json;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using NSubstitute;
using Shouldly;
using Routing = global::Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Checks declared platform scopes without changing ordinary tenant selection.</summary>
public sealed class PlatformScopeTests
{
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

    /// <summary>Discovery identifies platform operations and keeps ordinary tenant inputs visible.</summary>
    [Fact]
    public void DiscoveryShowsOnlyDeclaredPlatformScopes()
    {
        var provider = Provider();
        ICatalog catalog = new CatalogService(provider, new ExecutionAvailability(false, true), strict: false);

        foreach (string name in new[] { "routing-fixture.colon-wire", "routing-fixture.items-list" })
        {
            OperationDescriptionDocument description = catalog.Describe(name).Document.ShouldNotBeNull();
            OperationEnvelopeDocument envelope = description.Envelope;
            envelope.PlatformScope.ShouldBe("platform:routing");
            envelope.FixedTenant.ShouldBeNull();
            envelope.Arguments.ShouldNotContain("tenant");
            JsonElement json = JsonSerializer.SerializeToElement(description, McpCliJson.Result);
            json.GetProperty("envelope").GetProperty("platformScope").GetString().ShouldBe("platform:routing");
            json.GetProperty("envelope").TryGetProperty("fixedTenant", out _).ShouldBeFalse();
        }

        OperationEnvelopeDocument ordinary = catalog.Describe("routing-fixture.get-http2-status")
            .Document.ShouldNotBeNull().Envelope;
        ordinary.PlatformScope.ShouldBeNull();
        ordinary.Arguments.ShouldContain("tenant");
    }

    /// <summary>A declared query scope wins over a session tenant and reaches the gateway unchanged.</summary>
    [Theory]
    [InlineData(null)]
    [InlineData("platform:routing")]
    public async Task QueryForwardsDeclaredPlatformScopeAsync(string? callScope)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("routing-fixture.items-list", "{}", Tenant: callScope, AggregateId: ItemId), Context("session-tenant"),
            TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        outcome.Document.ShouldBeOfType<Hexalith.McpCli.Core.Execution.QueryResult>()
            .Tenant.ShouldBe("platform:routing");
        gateway.ReceivedCalls().ShouldHaveSingleItem().GetArguments()[0]
            .ShouldBeOfType<SubmitQueryRequest>().Tenant.ShouldBe("platform:routing");
    }

    /// <summary>A declared command scope wins over a session tenant and reaches the gateway unchanged.</summary>
    [Fact]
    public async Task CommandForwardsDeclaredPlatformScopeAsync()
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new SendCommandArguments("routing-fixture.colon-wire", $$"""{"ItemId":"{{ItemId}}"}"""),
            Context("session-tenant"), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        outcome.Document.ShouldBeOfType<CommandResult>().Tenant.ShouldBe("platform:routing");
        gateway.ReceivedCalls().ShouldHaveSingleItem().GetArguments()[0]
            .ShouldBeOfType<SubmitCommandRequest>().Tenant.ShouldBe("platform:routing");
    }

    /// <summary>Case variants of one explicit public tenant resolve to the same canonical scope.</summary>
    [Fact]
    public async Task PublicTenantIsCanonicalizedBeforeOverrideCheckAsync()
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("routing-fixture.get-http2-status", "{}", Tenant: "acme", AggregateId: ItemId),
            Context("AcMe"), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        gateway.ReceivedCalls().ShouldHaveSingleItem().GetArguments()[0]
            .ShouldBeOfType<SubmitQueryRequest>().Tenant.ShouldBe("acme");
    }

    /// <summary>Conflicting per-call scopes are refused before any gateway call.</summary>
    [Theory]
    [InlineData("routing-fixture.items-list", "other-tenant")]
    [InlineData("routing-fixture.items-list", "platform:other")]
    [InlineData("routing-fixture.colon-wire", "system")]
    public async Task PlatformScopeConflictIsRefusedAsync(string operation, string suppliedScope)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationCall call = operation.EndsWith("items-list", StringComparison.Ordinal)
            ? new RunQueryArguments(operation, "{}", Tenant: suppliedScope)
            : new SendCommandArguments(operation, $$"""{"ItemId":"{{ItemId}}"}""", Tenant: suppliedScope);

        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(call, Context(null),
            TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Code.ShouldBe("validation_failed");
        outcome.Error.Violations.ShouldNotBeNull().ShouldHaveSingleItem().Path.ShouldBe("/tenant");
        gateway.ReceivedCalls().ShouldBeEmpty();
    }

    /// <summary>Public system is refused for variable-scope operations before gateway submission.</summary>
    [Theory]
    [InlineData(null, "system")]
    [InlineData("system", null)]
    [InlineData(null, "System")]
    public async Task PublicSystemIsRefusedAsync(string? sessionTenant, string? callTenant)
    {
        IEventStoreGatewayClient gateway = Gateway();
        OperationOutcome outcome = await Executor(gateway).ExecuteAsync(
            new RunQueryArguments("routing-fixture.get-http2-status", "{}", Tenant: callTenant, AggregateId: ItemId),
            Context(sessionTenant), TestContext.Current.CancellationToken);

        outcome.Error.ShouldNotBeNull().Violations.ShouldNotBeNull().ShouldHaveSingleItem().Path.ShouldBe("/tenant");
        gateway.ReceivedCalls().ShouldBeEmpty();
    }

    /// <summary>Malformed and module-conflicting declarations are excluded from the catalog.</summary>
    [Theory]
    [InlineData("platform:Upper", null)]
    [InlineData("platform:", null)]
    [InlineData("platform:double--dash", null)]
    [InlineData("platform:-routing", null)]
    [InlineData("platform:routing-", null)]
    [InlineData("platform:rou_ting", null)]
    [InlineData("platform:a:b", null)]
    [InlineData("other-tenant", null)]
    [InlineData("platform:routing", "fixed-tenant")]
    public void InvalidPlatformDeclarationIsExcluded(string scope, string? moduleFixedTenant)
    {
        AssemblyBuilder assembly = AssemblyBuilder.DefineDynamicAssembly(
            new AssemblyName("PlatformScopeProbe" + Guid.NewGuid().ToString("N")), AssemblyBuilderAccess.Run);
        ConstructorInfo moduleConstructor = typeof(HexalithModuleAttribute).GetConstructor(
            [typeof(string), typeof(string), typeof(IdentifierKind)])!;
        assembly.SetCustomAttribute(new CustomAttributeBuilder(moduleConstructor,
            ["scope-probe", "Platform scope validation probe.", IdentifierKind.String],
            [typeof(HexalithModuleAttribute).GetProperty(nameof(HexalithModuleAttribute.FixedTenant))!],
            [moduleFixedTenant]));
        TypeBuilder type = assembly.DefineDynamicModule("probe").DefineType("ProbeQuery", TypeAttributes.Public);
        ConstructorInfo queryConstructor = typeof(HexalithQueryAttribute).GetConstructor([typeof(string)])!;
        type.SetCustomAttribute(new CustomAttributeBuilder(queryConstructor, ["Probe invalid platform scope."],
            [typeof(HexalithQueryAttribute).GetProperty(nameof(HexalithQueryAttribute.PlatformScope))!],
            [scope]));
        _ = type.CreateType();

        CatalogSnapshot catalog = CatalogBuilder.Build([assembly]);

        catalog.Modules.Single().Operations.ShouldBeEmpty();
        catalog.Diagnostics.ShouldContain(diagnostic => diagnostic.Category == "invalid_routing_value"
            && diagnostic.TypeName == "ProbeQuery" && diagnostic.Message.Contains("PlatformScope", StringComparison.Ordinal));
    }

    /// <summary>A platform scope fills an omitted tenant property and rejects a conflicting payload.</summary>
    [Theory]
    [InlineData(null, false)]
    [InlineData("platform:routing", false)]
    [InlineData("platform:other", true)]
    public async Task PlatformScopeControlsMappedPayloadTenantAsync(string? suppliedTenant, bool refused)
    {
        Assembly fixture = TenantPropertyFixture();
        var provider = new CatalogProvider(() => [fixture], new RecordingLogger<CatalogProvider>());
        IEventStoreGatewayClient gateway = Gateway();
        var executor = new OperationExecutor(provider, new ExecutionAvailability(false, true), gateway, strict: false);
        string payload = suppliedTenant is null ? "{}" : JsonSerializer.Serialize(new { Tenant = suppliedTenant });

        OperationOutcome outcome = await executor.ExecuteAsync(new RunQueryArguments("scope-probe.inspect", payload),
            Context("unrelated-session"), TestContext.Current.CancellationToken);

        if (refused)
        {
            outcome.Error.ShouldNotBeNull().Violations.ShouldNotBeNull().ShouldHaveSingleItem().Path.ShouldBe("/Tenant");
            gateway.ReceivedCalls().ShouldBeEmpty();
            return;
        }

        outcome.Error.ShouldBeNull();
        SubmitQueryRequest request = gateway.ReceivedCalls().ShouldHaveSingleItem().GetArguments()[0]
            .ShouldBeOfType<SubmitQueryRequest>();
        request.Tenant.ShouldBe("platform:routing");
        request.Payload.ShouldNotBeNull().GetProperty("Tenant").GetString().ShouldBe("platform:routing");
    }

    /// <summary>Legacy fixed-system declarations still forward their exact historical scope.</summary>
    [Fact]
    public async Task LegacyFixedSystemRemainsUnchangedAsync()
    {
        Assembly fixture = TenantPropertyFixture(platformScope: null, fixedTenant: "system");
        var provider = new CatalogProvider(() => [fixture], new RecordingLogger<CatalogProvider>());
        IEventStoreGatewayClient gateway = Gateway();
        var executor = new OperationExecutor(provider, new ExecutionAvailability(false, true), gateway, strict: false);

        OperationOutcome outcome = await executor.ExecuteAsync(new RunQueryArguments("scope-probe.inspect", "{}"),
            Context("unrelated-session"), TestContext.Current.CancellationToken);

        outcome.Error.ShouldBeNull();
        gateway.ReceivedCalls().ShouldHaveSingleItem().GetArguments()[0]
            .ShouldBeOfType<SubmitQueryRequest>().Tenant.ShouldBe("system");
    }

    private static Assembly TenantPropertyFixture(string? platformScope = "platform:routing", string? fixedTenant = null)
    {
        AssemblyBuilder assembly = AssemblyBuilder.DefineDynamicAssembly(
            new AssemblyName("TenantPropertyProbe" + Guid.NewGuid().ToString("N")), AssemblyBuilderAccess.Run);
        assembly.SetCustomAttribute(new CustomAttributeBuilder(typeof(HexalithModuleAttribute).GetConstructor(
            [typeof(string), typeof(string), typeof(IdentifierKind)])!,
            ["scope-probe", "Isolated tenant property fixture.", IdentifierKind.String],
            [typeof(HexalithModuleAttribute).GetProperty(nameof(HexalithModuleAttribute.FixedTenant))!], [fixedTenant]));
        TypeBuilder type = assembly.DefineDynamicModule("probe").DefineType("ProbeQuery", TypeAttributes.Public);
        _ = type.DefineDefaultConstructor(MethodAttributes.Public);
        FieldBuilder field = type.DefineField("_tenant", typeof(string), FieldAttributes.Private);
        PropertyBuilder property = type.DefineProperty("Tenant", PropertyAttributes.None, typeof(string), null);
        MethodBuilder getter = type.DefineMethod("get_Tenant", MethodAttributes.Public | MethodAttributes.SpecialName,
            typeof(string), Type.EmptyTypes);
        ILGenerator get = getter.GetILGenerator();
        get.Emit(OpCodes.Ldarg_0);
        get.Emit(OpCodes.Ldfld, field);
        get.Emit(OpCodes.Ret);
        MethodBuilder setter = type.DefineMethod("set_Tenant", MethodAttributes.Public | MethodAttributes.SpecialName,
            typeof(void), [typeof(string)]);
        ILGenerator set = setter.GetILGenerator();
        set.Emit(OpCodes.Ldarg_0);
        set.Emit(OpCodes.Ldarg_1);
        set.Emit(OpCodes.Stfld, field);
        set.Emit(OpCodes.Ret);
        property.SetGetMethod(getter);
        property.SetSetMethod(setter);
        string[] names = ["Name", "Domain", "WireType", "ProjectionType", "AggregateId", "TenantProperty", "PlatformScope"];
        type.SetCustomAttribute(new CustomAttributeBuilder(typeof(HexalithQueryAttribute).GetConstructor([typeof(string)])!,
            ["Inspect the isolated tenant scope."], names.Select(name => typeof(HexalithQueryAttribute).GetProperty(name)!).ToArray(),
            ["inspect", "scope", "inspect", "scope-items", ItemId, "Tenant", platformScope]));
        _ = type.CreateType();
        return assembly;
    }

    private static CatalogProvider Provider() => new(() => [typeof(Routing.Module).Assembly],
        new RecordingLogger<CatalogProvider>());

    private static IOperationExecutor Executor(IEventStoreGatewayClient gateway)
        => new OperationExecutor(Provider(), new ExecutionAvailability(false, true), gateway, strict: false);

    private static EnvelopeContext Context(string? tenant) => new(tenant, null, false, new HashSet<string>());

    private static IEventStoreGatewayClient Gateway()
    {
        IEventStoreGatewayClient gateway = Substitute.For<IEventStoreGatewayClient>();
        gateway.SubmitQueryAsync(Arg.Any<SubmitQueryRequest>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new EventStoreQueryResult(ItemId,
                JsonSerializer.SerializeToElement(new { items = Array.Empty<string>() }), false, null)));
        gateway.SubmitCommandAsync(Arg.Any<SubmitCommandRequest>(), Arg.Any<CancellationToken>())
            .Returns(Task.FromResult(new SubmitCommandResponse(ItemId)));
        return gateway;
    }
}

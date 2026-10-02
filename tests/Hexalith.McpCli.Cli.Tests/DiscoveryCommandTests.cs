using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Sample.Contracts;
using Shouldly;
using Explicit = global::Catalog.Explicit.Contracts;
using Lint = global::Catalog.Lint.Contracts;
using MarkedEmpty = global::Manifest.MarkedEmpty.Contracts;
using Routing = global::Catalog.Routing.Contracts;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Checks offline discovery contracts through CLI parsing and invocation.</summary>
public sealed class DiscoveryCommandTests
{
    private const string FormatNote = "This result is emitted as JSON; no table view is defined.";

    private static readonly Assembly[] SampleManifest = [typeof(CreateItemCommand).Assembly];

    private static readonly Assembly[] MixedManifest =
    [
        typeof(CreateItemCommand).Assembly,
        typeof(Routing.Module).Assembly,
        typeof(MarkedEmpty.Module).Assembly,
        typeof(Lint.Module).Assembly,
        typeof(Explicit.Module).Assembly,
    ];

    /// <summary>All discovery verbs produce their complete documents without a Gateway URL.</summary>
    [Fact]
    public async Task DiscoveryWorksOfflineWithExactDocumentsAsync()
    {
        (int modulesExit, string modules, string modulesError) = await InvokeAsync(SampleManifest, "modules");
        modulesExit.ShouldBe(0);
        modulesError.ShouldBeEmpty();
        AssertJson(modules, """
            {"modules":[{"name":"sample","description":"Synthetic operations for testing module declarations.","operationCount":3}]}
            """);

        (int operationsExit, string operations, string operationsError) = await InvokeAsync(SampleManifest,
            "operations", "sample");
        operationsExit.ShouldBe(0);
        operationsError.ShouldBeEmpty();
        AssertJson(operations, """
            {"module":"sample","operations":[
                {"name":"sample.create-item","kind":"write","description":"Create a synthetic item in the sample module."},
                {"name":"sample.get-item","kind":"read","description":"Read one synthetic item from the sample projection."},
                {"name":"sample.rename-item","kind":"write","description":"Rename a synthetic item in the sample module."}
            ]}
            """);

        (int describeExit, string describe, string describeError) = await InvokeAsync(SampleManifest,
            "describe", "sample.get-item");
        describeExit.ShouldBe(0);
        describeError.ShouldBeEmpty();
        AssertSampleDescription(describe, write: false, "configuration_invalid");
    }

    /// <summary>Read-only availability takes precedence for writes, and URL availability affects descriptions only.</summary>
    [Theory]
    [InlineData(false, false)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(true, true)]
    public async Task AvailabilityUsesReadOnlyAndUrlWithoutFilteringListsAsync(bool hasUrl, bool readOnly)
    {
        string[] flags = [.. hasUrl ? new[] { "--url", "http://127.0.0.1:1/" } : [],
            .. readOnly ? new[] { "--read-only" } : []];
        foreach (bool write in new[] { false, true })
        {
            string operation = write ? "sample.create-item" : "sample.get-item";
            (int exit, string output, string error) = await InvokeAsync(SampleManifest, ["describe", operation, .. flags]);
            exit.ShouldBe(0);
            error.ShouldBeEmpty();
            AssertSampleDescription(output, write, write && readOnly ? "read_only" : hasUrl ? null : "configuration_invalid");
        }

        (int listExit, string listing, string listError) = await InvokeAsync(SampleManifest,
            ["operations", "sample", .. flags]);
        listExit.ShouldBe(0);
        listError.ShouldBeEmpty();
        AssertJson(listing, """
            {"module":"sample","operations":[
                {"name":"sample.create-item","kind":"write","description":"Create a synthetic item in the sample module."},
                {"name":"sample.get-item","kind":"read","description":"Read one synthetic item from the sample projection."},
                {"name":"sample.rename-item","kind":"write","description":"Rename a synthetic item in the sample module."}
            ]}
            """);

        (int writesExit, string writes, string writesError) = await InvokeAsync(SampleManifest,
            ["operations", "sample", "--kind", "write", .. flags]);
        writesExit.ShouldBe(0);
        writesError.ShouldBeEmpty();
        AssertJson(writes, """
            {"module":"sample","operations":[
                {"name":"sample.create-item","kind":"write","description":"Create a synthetic item in the sample module."},
                {"name":"sample.rename-item","kind":"write","description":"Rename a synthetic item in the sample module."}
            ]}
            """);

        (int modulesExit, string modules, string modulesError) = await InvokeAsync(SampleManifest, ["modules", .. flags]);
        modulesExit.ShouldBe(0);
        modulesError.ShouldBeEmpty();
        AssertJson(modules, """
            {"modules":[{"name":"sample","description":"Synthetic operations for testing module declarations.","operationCount":3}]}
            """);
    }

    /// <summary>Manifest order does not change ordinal module lists, valid-operation counts, or operation lists.</summary>
    [Fact]
    public async Task ListsAreOrdinalAndKeepMarkedEmptyModulesAsync()
    {
        const string expected = """
            {"modules":[
                {"name":"explicit-fixture","description":"Explicit wire type fixture.","operationCount":1},
                {"name":"lint-fixture","description":"Description quality fixtures.","operationCount":4},
                {"name":"marked-empty","description":"Module with no operations.","operationCount":0},
                {"name":"routing-fixture","description":"Valid routing, aggregate source, and envelope variants.","operationCount":12},
                {"name":"sample","description":"Synthetic operations for testing module declarations.","operationCount":3}
            ]}
            """;
        foreach (Assembly[] manifest in new[] { MixedManifest, MixedManifest.Reverse().ToArray() })
        {
            (int exit, string output, string error) = await InvokeAsync(manifest, "modules");
            exit.ShouldBe(0);
            AssertJson(output, expected);
            AssertDiagnostics(error);

            (int operationsExit, string operations, string operationsError) = await InvokeAsync(manifest,
                "operations", "routing-fixture");
            operationsExit.ShouldBe(0);
            AssertDiagnostics(operationsError);
            JsonElement list = Parse(operations);
            AssertMembers(list, "module", "operations");
            list.GetProperty("module").GetString().ShouldBe("routing-fixture");
            list.GetProperty("operations").EnumerateArray().Select(item => item.GetProperty("name").GetString()).ShouldBe(
            [
                "routing-fixture.colon-wire", "routing-fixture.competing-route", "routing-fixture.computed-envelope", "routing-fixture.envelope-item",
                "routing-fixture.get-http2-status", "routing-fixture.interface-item", "routing-fixture.items-list",
                "routing-fixture.nullable-idempotency", "routing-fixture.redundant-convention",
                "routing-fixture.redundant-interface", "routing-fixture.renamed-aggregate",
                "routing-fixture.required-nullable-idempotency",
            ]);
            foreach (JsonElement item in list.GetProperty("operations").EnumerateArray())
            {
                AssertMembers(item, "name", "kind", "description");
                item.GetProperty("description").GetString().ShouldNotBeNullOrWhiteSpace();
            }
        }
    }

    /// <summary>Read/write filters and empty module lists preserve exact documents with array values.</summary>
    [Theory]
    [InlineData("sample", null)]
    [InlineData("sample", "read")]
    [InlineData("sample", "write")]
    [InlineData("marked-empty", null)]
    [InlineData("marked-empty", "read")]
    [InlineData("marked-empty", "write")]
    public async Task FiltersReturnExactOperationDocumentsAsync(string module, string? kind)
    {
        Assembly[] manifest = [typeof(MarkedEmpty.Module).Assembly, .. SampleManifest];
        (int exit, string output, string error) = await InvokeAsync(manifest, ["operations", module,
            .. kind is null ? [] : new[] { "--kind", kind }]);
        exit.ShouldBe(0);
        error.ShouldContain("empty_module");
        string[] operations = module == "marked-empty" ? [] : kind switch
        {
            "read" => ["""{"name":"sample.get-item","kind":"read","description":"Read one synthetic item from the sample projection."}"""],
            "write" =>
            [
                """{"name":"sample.create-item","kind":"write","description":"Create a synthetic item in the sample module."}""",
                """{"name":"sample.rename-item","kind":"write","description":"Rename a synthetic item in the sample module."}""",
            ],
            _ =>
            [
                """{"name":"sample.create-item","kind":"write","description":"Create a synthetic item in the sample module."}""",
                """{"name":"sample.get-item","kind":"read","description":"Read one synthetic item from the sample projection."}""",
                """{"name":"sample.rename-item","kind":"write","description":"Rename a synthetic item in the sample module."}""",
            ],
        };
        AssertJson(output, $$"""{"module":"{{module}}","operations":[{{string.Join(',', operations)}}]}""");
    }

    /// <summary>Missing/blank names and invalid filters fail binding before the manifest is evaluated.</summary>
    [Theory]
    [InlineData("operations", null, null, "module", "module is required and must be non-empty")]
    [InlineData("operations", "", null, "module", "module is required and must be non-empty")]
    [InlineData("operations", " \t", null, "module", "module is required and must be non-empty")]
    [InlineData("describe", null, null, "operation", "operation is required and must be non-empty")]
    [InlineData("describe", "", null, "operation", "operation is required and must be non-empty")]
    [InlineData("describe", " \t", null, "operation", "operation is required and must be non-empty")]
    [InlineData("operations", "sample", "", "kind", "kind must be read or write")]
    [InlineData("operations", "sample", "READ", "kind", "kind must be read or write")]
    [InlineData("operations", "sample", "other", "kind", "kind must be read or write")]
    public async Task BindingErrorsDoNotBuildCatalogAsync(string verb, string? name, string? kind,
        string argument, string message)
    {
        int manifestReads = 0;
        IReadOnlyList<Assembly> Manifest()
        {
            manifestReads++;
            throw new InvalidOperationException("Binding must finish before catalog access.");
        }

        (int exit, string output, string error) = await InvokeAsync(Manifest,
            [verb, .. name is null ? [] : new[] { name }, .. kind is null ? [] : new[] { "--kind", kind }]);
        exit.ShouldBe(2);
        error.ShouldBeEmpty();
        manifestReads.ShouldBe(0);
        AssertJson(output, JsonSerializer.Serialize(new { error = new { code = "invalid_arguments", argument, message } }));
    }

    /// <summary>Unknown names preserve requested casing and cap suggestions ordered by distance then ordinal name.</summary>
    [Theory]
    [InlineData("operations", "fixture", "module", "unknown_module", "lint-fixture", "sample", "routing-fixture")]
    [InlineData("operations", "SAMPLE", "module", "unknown_module", "sample", "marked-empty", "lint-fixture")]
    [InlineData("operations", "sAmPlE", "module", "unknown_module", "sample", "marked-empty", "lint-fixture")]
    [InlineData("operations", "xxxxxxxxxxxxxxxx", "module", "unknown_module", "explicit-fixture", "lint-fixture", "routing-fixture")]
    [InlineData("describe", "sample.item", "operation", "unknown_operation", "sample.get-item", "sample.create-item", "sample.rename-item")]
    [InlineData("describe", "SAMPLE.GET-ITEM", "operation", "unknown_operation", "sample.get-item", "sample.create-item", "sample.rename-item")]
    public async Task UnknownNamesReturnExactErrorsAndSuggestionsAsync(string verb, string requested, string member,
        string code, string first, string second, string third)
    {
        (int exit, string output, string error) = await InvokeAsync(MixedManifest, verb, requested);
        exit.ShouldBe(2);
        AssertDiagnostics(error);
        var details = new Dictionary<string, object>
        {
            ["code"] = code,
            [member] = requested,
            ["suggestions"] = new[] { first, second, third },
        };
        AssertJson(output, JsonSerializer.Serialize(new { error = details }));
    }

    /// <summary>A small catalog returns only existing suggestions rather than padding the array.</summary>
    [Fact]
    public async Task UnknownModuleWithOneCandidateHasOneSuggestionAsync()
    {
        (int exit, string output, string error) = await InvokeAsync(SampleManifest, "operations", "Smple");
        exit.ShouldBe(2);
        error.ShouldBeEmpty();
        AssertJson(output, """{"error":{"code":"unknown_module","module":"Smple","suggestions":["sample"]}}""");
    }

    /// <summary>Nonfixed tenants, examples, and declared idempotency requirements flow into envelope documents.</summary>
    [Fact]
    public async Task DescribeKeepsModuleCasingAndApplicableEnvelopeArgumentsAsync()
    {
        Assembly[] manifest = [typeof(Routing.Module).Assembly];
        (int exit, string output, string error) = await InvokeAsync(manifest, "describe", "routing-fixture.envelope-item");
        exit.ShouldBe(0);
        error.ShouldContain("Catalog warning ");
        JsonElement description = Parse(output);
        AssertMembers(description, "name", "kind", "description", "schema", "example", "envelope", "lintFindings", "submittable", "reason");
        description.GetProperty("name").GetString().ShouldBe("routing-fixture.envelope-item");
        description.GetProperty("kind").GetString().ShouldBe("write");
        description.GetProperty("description").GetString().ShouldBe("Change an item using mapped envelope values.");
        AssertJson(description.GetProperty("example").GetRawText(), """{"ItemId":"01ARZ3NDEKTSV4RRFFQ69G5FAV"}""");
        AssertJson(description.GetProperty("envelope").GetRawText(), """
            {"aggregateIdRequired":false,"idempotencyKeyRequired":true,
             "arguments":["tenant","aggregateId","correlationId","idempotencyKey","extensions"]}
            """);
        description.GetProperty("submittable").GetBoolean().ShouldBeFalse();
        description.GetProperty("reason").GetString().ShouldBe("configuration_invalid");
        AssertJson(description.GetProperty("lintFindings").GetRawText(), """
            [
                {"code":"missing_property_description","severity":"warning",
                 "message":"Describe payload member Actor so callers understand its meaning.","property":"/properties/Actor"},
                {"code":"missing_property_description","severity":"warning",
                 "message":"Describe payload member Correlation so callers understand its meaning.","property":"/properties/Correlation"},
                {"code":"missing_property_description","severity":"warning",
                 "message":"Describe payload member Idempotency so callers understand its meaning.","property":"/properties/Idempotency"},
                {"code":"missing_property_description","severity":"warning",
                 "message":"Describe payload member ItemId so callers understand its meaning.","property":"/properties/ItemId"},
                {"code":"missing_property_description","severity":"warning",
                 "message":"Describe payload member Tenant so callers understand its meaning.","property":"/properties/tenant~1~0"}
            ]
            """);
        AssertJson(description.GetProperty("schema").GetRawText(), """
            {"type":"object","properties":{
                "ItemId":{"type":"string","pattern":"^[0-7][0-9A-HJKMNP-TV-Z]{25}$","minLength":26,"maxLength":26},
                "tenant/~":{"type":"string","readOnly":true},
                "Correlation":{"type":"string","readOnly":true},
                "Idempotency":{"type":"string","readOnly":true},
                "Actor":{"type":"string","readOnly":true}
            },"required":["ItemId"],"additionalProperties":false}
            """);

        (int queryExit, string queryOutput, _) = await InvokeAsync(manifest, "describe", "routing-fixture.get-http2-status");
        queryExit.ShouldBe(0);
        AssertJson(queryOutput, """
            {"name":"routing-fixture.get-http2-status","kind":"read","description":"Read HTTP2 status.",
             "schema":{"type":["object","null"],"additionalProperties":false},
             "envelope":{"aggregateIdRequired":true,"idempotencyKeyRequired":false,
                "arguments":["tenant","aggregateId","entityId","pageSize","offset","cursor"]},
             "lintFindings":[],"submittable":false,"reason":"configuration_invalid"}
            """);

        (int optionalExit, string optionalOutput, _) = await InvokeAsync(manifest, "describe", "routing-fixture.nullable-idempotency");
        optionalExit.ShouldBe(0);
        AssertJson(optionalOutput, """
            {"name":"routing-fixture.nullable-idempotency","kind":"write","description":"Command with an optional idempotency key.",
             "schema":{"type":"object","properties":{
                "ItemId":{"type":"string","pattern":"^[0-7][0-9A-HJKMNP-TV-Z]{25}$","minLength":26,"maxLength":26},
                "Idempotency":{"type":["string","null"],"default":null,"readOnly":true}
             },"required":["ItemId"],"additionalProperties":false},
             "envelope":{"aggregateIdRequired":false,"idempotencyKeyRequired":false,
                "arguments":["tenant","aggregateId","correlationId","idempotencyKey","extensions"]},
             "lintFindings":[
                {"code":"missing_property_description","severity":"warning",
                 "message":"Describe payload member Idempotency so callers understand its meaning.","property":"/properties/Idempotency"},
                {"code":"missing_property_description","severity":"warning",
                 "message":"Describe payload member ItemId so callers understand its meaning.","property":"/properties/ItemId"}
             ],"submittable":false,"reason":"configuration_invalid"}
            """);
    }

    /// <summary>Lint is always present, never invalidates strict catalogs, and affects exit only when requested.</summary>
    [Theory]
    [InlineData(false, false)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(true, true)]
    public async Task LintFlagChangesOnlyExitAndTableFallbackKeepsJsonAsync(bool findings, bool table)
    {
        Assembly[] manifest = findings ? [typeof(Lint.Module).Assembly] : SampleManifest;
        string operation = findings ? "lint-fixture.inspect-hollow" : "sample.get-item";
        string[] flags = ["--strict", .. table ? new[] { "--format", "table" } : []];
        (int normalExit, string normal, string normalError) = await InvokeAsync(manifest, ["describe", operation, .. flags]);
        (int lintExit, string lint, string lintError) = await InvokeAsync(manifest, ["describe", operation, "--lint", .. flags]);
        normalExit.ShouldBe(0);
        lintExit.ShouldBe(findings ? 1 : 0);
        lint.ShouldBe(normal);
        normalError.ShouldBe(table ? FormatNote + Environment.NewLine : string.Empty);
        lintError.ShouldBe(normalError);
        if (findings)
        {
            AssertJson(normal, """
                {"name":"lint-fixture.inspect-hollow","kind":"read","description":" inspect hollow ",
                 "schema":{"type":["object","null"],"additionalProperties":false},
                 "envelope":{"aggregateIdRequired":false,"idempotencyKeyRequired":false,
                    "arguments":["tenant","aggregateId","entityId","pageSize","offset","cursor"]},
                 "lintFindings":[{"code":"hollow_description","severity":"warning",
                    "message":"Operation description only repeats the name of InspectHollowQuery; explain what it does."}],
                 "submittable":false,"reason":"configuration_invalid"}
                """);
        }
        else
        {
            AssertSampleDescription(normal, write: false, "configuration_invalid");
        }
    }

    /// <summary>Property lint retains escaped schema pointers and complete finding members on stdout only.</summary>
    [Fact]
    public async Task PropertyLintUsesSerializedPointersAndAllRequiredMembersAsync()
    {
        (int exit, string output, string error) = await InvokeAsync([typeof(Lint.Module).Assembly],
            "describe", "lint-fixture.inspect-item", "--lint", "--strict");
        exit.ShouldBe(1);
        error.ShouldBeEmpty();
        JsonElement description = Parse(output);
        AssertMembers(description, "name", "kind", "description", "schema", "envelope", "lintFindings", "submittable", "reason");
        JsonElement[] findings = description.GetProperty("lintFindings").EnumerateArray().ToArray();
        findings.Select(finding => (Code: finding.GetProperty("code").GetString(), Property: finding.GetProperty("property").GetString()))
            .ShouldBe(new (string? Code, string? Property)[]
            {
                ("payload_paging_member", "/properties/Cursor"),
                ("missing_property_description", "/properties/Entries/items/properties/Count"),
                ("missing_property_description", "/properties/EntriesByKey/additionalProperties/properties/Quantity"),
                ("unmarked_identifier_like_property", "/properties/ExternalId"),
                ("missing_property_description", "/properties/Maybe/properties/Count"),
                ("unmarked_identifier_like_property", "/properties/Maybe/properties/ExternalId"),
                ("unmarked_identifier_like_property", "/properties/Nested/properties/external~1~0id"),
                ("missing_property_description", "/properties/Nested/properties/nested~1~0"),
                ("missing_property_description", "/properties/Nested/properties/page~1~0size"),
                ("payload_paging_member", "/properties/Nested/properties/page~1~0size"),
                ("payload_paging_member", "/properties/Offset"),
                ("payload_paging_member", "/properties/PageSize"),
                ("missing_property_description", "/properties/Tenant"),
                ("missing_property_description", "/properties/lowerCamel"),
            });
        foreach (JsonElement finding in findings)
        {
            AssertMembers(finding, "code", "severity", "message", "property");
            finding.GetProperty("severity").GetString().ShouldBe("warning");
            finding.GetProperty("message").GetString().ShouldNotBeNullOrWhiteSpace();
        }

        JsonElement renamed = findings.Single(item => item.GetProperty("property").GetString() == "/properties/Nested/properties/nested~1~0");
        AssertJson(renamed.GetRawText(), """
            {"code":"missing_property_description","severity":"warning",
             "message":"Describe payload member Escaped so callers understand its meaning.",
             "property":"/properties/Nested/properties/nested~1~0"}
            """);
        JsonElement paging = findings.Single(item => item.GetProperty("code").GetString() == "payload_paging_member"
            && item.GetProperty("property").GetString() == "/properties/Nested/properties/page~1~0size");
        AssertJson(paging.GetRawText(), """
            {"code":"payload_paging_member","severity":"warning",
             "message":"Move paging member PageSize to the query envelope argument.",
             "property":"/properties/Nested/properties/page~1~0size"}
            """);
    }

    /// <summary>Tab-separated list headers and rows keep their existing spelling and format.</summary>
    [Fact]
    public async Task TablesPreserveModuleOperationAndEmptyRowsAsync()
    {
        Assembly[] manifest = [typeof(MarkedEmpty.Module).Assembly, .. SampleManifest];
        (int modulesExit, string modules, string modulesError) = await InvokeAsync(manifest, "modules", "--format", "table");
        modulesExit.ShouldBe(0);
        modulesError.ShouldContain("empty_module");
        modules.ShouldBe(string.Join(Environment.NewLine,
            "NAME\tOPERATIONS\tDESCRIPTION",
            "marked-empty\t0\tModule with no operations.",
            "sample\t3\tSynthetic operations for testing module declarations.", string.Empty));

        (int operationsExit, string operations, string operationsError) = await InvokeAsync(manifest,
            "operations", "sample", "--kind", "write", "--format", "table");
        operationsExit.ShouldBe(0);
        operationsError.ShouldContain("empty_module");
        operations.ShouldBe(string.Join(Environment.NewLine,
            "NAME\tKIND\tDESCRIPTION",
            "sample.create-item\twrite\tCreate a synthetic item in the sample module.",
            "sample.rename-item\twrite\tRename a synthetic item in the sample module.", string.Empty));

        (int emptyExit, string empty, string emptyError) = await InvokeAsync(manifest,
            "operations", "marked-empty", "--format", "table");
        emptyExit.ShouldBe(0);
        emptyError.ShouldContain("empty_module");
        empty.ShouldBe("NAME\tKIND\tDESCRIPTION" + Environment.NewLine + Environment.NewLine);

        (int unknownExit, string unknown, string unknownError) = await InvokeAsync(SampleManifest,
            "operations", "Missing", "--format", "table");
        unknownExit.ShouldBe(2);
        unknownError.ShouldBeEmpty();
        AssertJson(unknown, """{"error":{"code":"unknown_module","module":"Missing","suggestions":["sample"]}}""");
    }

    /// <summary>Warnings and errors remain on stderr, ordinary mode keeps valid operations, and strict rejects diagnostics.</summary>
    [Theory]
    [InlineData(false, false)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(true, true)]
    public async Task DiagnosticsAffectOnlyStrictAccessAsync(bool warning, bool strict)
    {
        Assembly[] manifest = warning ? [typeof(Routing.Module).Assembly] : [typeof(Explicit.Module).Assembly];
        foreach (string[] verb in new[]
        {
            new[] { "modules" },
            new[] { "operations", warning ? "routing-fixture" : "explicit-fixture" },
            new[] { "describe", warning ? "routing-fixture.items-list" : "explicit-fixture.valid" },
        })
        {
            (int exit, string output, string error) = await InvokeAsync(manifest,
                [.. verb, .. strict ? new[] { "--strict" } : []]);
            exit.ShouldBe(strict ? 2 : 0);
            error.ShouldContain(warning ? "Catalog warning " : "Catalog error ");
            error.ShouldNotContain(warning ? "Catalog error " : "Catalog warning ");
            error.ShouldContain(warning ? "CompetingRouteCommand" : "MissingWireQuery");
            if (strict)
            {
                AssertJson(output, JsonSerializer.Serialize(new
                {
                    error = new
                    {
                        code = "catalog_invalid",
                        message = $"Strict mode rejects the Catalog because it has {(warning ? 7 : 1)} diagnostic(s).",
                    },
                }));
            }
            else
            {
                AssertJson(output, ExpectedRetainedDocument(warning, verb[0]));
            }
        }
    }

    /// <summary>Strict diagnostics precede emptiness; an empty manifest returns catalog_empty in both modes.</summary>
    [Theory]
    [InlineData(false, false)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(true, true)]
    public async Task EmptyCatalogReturnsExactErrorsAsync(bool marked, bool strict)
    {
        Assembly[] manifest = marked ? [typeof(MarkedEmpty.Module).Assembly] : [];
        foreach (string[] verb in new[] { new[] { "modules" }, new[] { "operations", "marked-empty" }, new[] { "describe", "missing.read" } })
        {
            (int exit, string output, string error) = await InvokeAsync(manifest,
                [.. verb, .. strict ? new[] { "--strict" } : []]);
            exit.ShouldBe(2);
            if (marked)
            {
                error.ShouldContain("empty_module");
            }
            else
            {
                error.ShouldBeEmpty();
            }

            AssertJson(output, marked && strict
                ? """{"error":{"code":"catalog_invalid","message":"Strict mode rejects the Catalog because it has 1 diagnostic(s)."}}"""
                : """{"error":{"code":"catalog_empty","message":"The Catalog exposes no valid Operations."}}""");
        }
    }

    /// <summary>Configured URL discovery opens zero connections to a bounded local listener.</summary>
    [Fact]
    public async Task ConfiguredUrlDiscoveryDoesNotContactGatewayAsync()
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int connections = 0;
        async Task CountConnectionsAsync()
        {
            try
            {
                while (!timeout.IsCancellationRequested)
                {
                    // Count the connection itself, so contact that never sends a request line is still caught.
                    using TcpClient client = await listener.AcceptTcpClientAsync(timeout.Token);
                    Interlocked.Increment(ref connections);

                    // Close the connection so an accidental call fails promptly instead of hanging the test.
                }
            }
            catch (OperationCanceledException) when (timeout.IsCancellationRequested)
            {
            }
        }

        Task accepting = CountConnectionsAsync();
        try
        {
            string url = $"http://127.0.0.1:{((IPEndPoint)listener.LocalEndpoint).Port}/";
            foreach (string[] verb in new[]
            {
                new[] { "modules" }, new[] { "operations", "sample" },
                new[] { "describe", "sample.create-item" }, new[] { "describe", "sample.get-item" },
            })
            {
                (int exit, string output, string error) = await InvokeAsync(SampleManifest, [.. verb, "--url", url]);
                exit.ShouldBe(0);
                error.ShouldBeEmpty();
                if (verb[0] == "describe")
                {
                    Parse(output).GetProperty("submittable").GetBoolean().ShouldBeTrue();
                }
            }

            await Task.Delay(TimeSpan.FromMilliseconds(100), timeout.Token);
        }
        finally
        {
            try
            {
                timeout.Cancel();
                await accepting;
            }
            finally
            {
                listener.Stop();
            }
        }

        Volatile.Read(ref connections).ShouldBe(0);
    }

    private static string ExpectedRetainedDocument(bool warning, string verb)
        => (warning, verb) switch
        {
            (true, "modules") => """
                {"modules":[{"name":"routing-fixture","description":"Valid routing, aggregate source, and envelope variants.","operationCount":12}]}
                """,
            (false, "modules") => """
                {"modules":[{"name":"explicit-fixture","description":"Explicit wire type fixture.","operationCount":1}]}
                """,
            (true, "operations") => """
                {"module":"routing-fixture","operations":[
                    {"name":"routing-fixture.colon-wire","kind":"write","description":"Command with a colon in its wire type."},
                    {"name":"routing-fixture.competing-route","kind":"write","description":"Command with competing route values."},
                    {"name":"routing-fixture.computed-envelope","kind":"write","description":"Command with a computed aggregate identifier and envelope members."},
                    {"name":"routing-fixture.envelope-item","kind":"write","description":"Change an item using mapped envelope values."},
                    {"name":"routing-fixture.get-http2-status","kind":"read","description":"Read HTTP2 status."},
                    {"name":"routing-fixture.interface-item","kind":"read","description":"Read an item through the query interface."},
                    {"name":"routing-fixture.items-list","kind":"read","description":"List all synthetic items."},
                    {"name":"routing-fixture.nullable-idempotency","kind":"write","description":"Command with an optional idempotency key."},
                    {"name":"routing-fixture.redundant-convention","kind":"read","description":"Query whose attribute repeats its convention wire type."},
                    {"name":"routing-fixture.redundant-interface","kind":"write","description":"Command whose attribute repeats its interface domain."},
                    {"name":"routing-fixture.renamed-aggregate","kind":"write","description":"Read a renamed aggregate property."},
                    {"name":"routing-fixture.required-nullable-idempotency","kind":"write","description":"Command with a required nullable idempotency member."}
                ]}
                """,
            (false, "operations") => """
                {"module":"explicit-fixture","operations":[
                    {"name":"explicit-fixture.valid","kind":"read","description":"Valid explicit-route query."}
                ]}
                """,
            (true, "describe") => """
                {"name":"routing-fixture.items-list","kind":"read","description":"List all synthetic items.",
                 "schema":{"type":["object","null"],"additionalProperties":false},
                 "envelope":{"aggregateIdRequired":false,"idempotencyKeyRequired":false,
                    "arguments":["tenant","aggregateId","entityId","pageSize","offset","cursor"]},
                 "lintFindings":[],"submittable":false,"reason":"configuration_invalid"}
                """,
            (false, "describe") => """
                {"name":"explicit-fixture.valid","kind":"read","description":"Valid explicit-route query.",
                 "schema":{"type":["object","null"],"additionalProperties":false},
                 "envelope":{"aggregateIdRequired":true,"idempotencyKeyRequired":false,
                    "arguments":["tenant","aggregateId","entityId","pageSize","offset","cursor"]},
                 "lintFindings":[],"submittable":false,"reason":"configuration_invalid"}
                """,
            _ => throw new ArgumentOutOfRangeException(nameof(verb)),
        };

    private static void AssertSampleDescription(string output, bool write, string? reason)
    {
        string schema = write ? """
            {"type":"object","properties":{
                "ItemId":{"type":"string","pattern":"^[0-7][0-9A-HJKMNP-TV-Z]{25}$","minLength":26,"maxLength":26,"description":"The ULID of the new item."},
                "Title":{"type":"string","description":"The title shown for the item."}
            },"required":["ItemId","Title"],"additionalProperties":false}
            """ : """
            {"type":["object","null"],"properties":{
                "ItemId":{"type":"string","pattern":"^[0-7][0-9A-HJKMNP-TV-Z]{25}$","minLength":26,"maxLength":26,"description":"The ULID of the item to read."}
            },"required":["ItemId"],"additionalProperties":false}
            """;
        string arguments = write ? """["aggregateId","correlationId","idempotencyKey","extensions"]"""
            : """["aggregateId","entityId","pageSize","offset","cursor"]""";
        string name = write ? "sample.create-item" : "sample.get-item";
        string description = write ? "Create a synthetic item in the sample module." : "Read one synthetic item from the sample projection.";
        string optionalReason = reason is null ? string.Empty : ",\"reason\":" + JsonSerializer.Serialize(reason);
        AssertJson(output, $$"""
            {"name":"{{name}}","kind":"{{(write ? "write" : "read")}}","description":"{{description}}",
             "schema":{{schema}},"envelope":{"fixedTenant":"sample-tenant","aggregateIdRequired":false,
                "idempotencyKeyRequired":false,"arguments":{{arguments}}},
             "lintFindings":[],"submittable":{{(reason is null ? "true" : "false")}}{{optionalReason}}}
            """);
    }

    private static void AssertDiagnostics(string error)
    {
        error.ShouldContain("CompetingRouteCommand");
        error.ShouldContain("MissingWireQuery");
        error.ShouldContain("Catalog warning ");
        error.ShouldContain("Catalog error ");
    }

    private static void AssertMembers(JsonElement json, params string[] names)
        => json.EnumerateObject().Select(item => item.Name).Order(StringComparer.Ordinal)
            .ShouldBe(names.Order(StringComparer.Ordinal));

    private static void AssertJson(string actual, string expected)
        => JsonElement.DeepEquals(Parse(actual), Parse(expected)).ShouldBeTrue(actual);

    private static JsonElement Parse(string json)
    {
        using JsonDocument document = JsonDocument.Parse(json);
        return document.RootElement.Clone();
    }

    private static Task<(int Exit, string Output, string Error)> InvokeAsync(Assembly[] manifest, params string[] args)
        => InvokeAsync(() => manifest, args);

    private static async Task<(int Exit, string Output, string Error)> InvokeAsync(
        Func<IReadOnlyList<Assembly>> manifest, params string[] args)
    {
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-discovery-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        TextWriter originalOut = Console.Out;
        TextWriter originalError = Console.Error;
        TextReader originalIn = Console.In;
        using var output = new StringWriter();
        using var error = new StringWriter();
        using var input = new StringReader(string.Empty);
        using CancellationTokenSource timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(10));
        try
        {
            Console.SetOut(output);
            Console.SetError(error);
            Console.SetIn(input);
            var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
            int exit = await new CliRunner(store, manifest, _ => null).Parse(args).InvokeAsync(cancellationToken: timeout.Token);
            return (exit, output.ToString(), error.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
            Console.SetIn(originalIn);
            Directory.Delete(directory, recursive: true);
        }
    }
}

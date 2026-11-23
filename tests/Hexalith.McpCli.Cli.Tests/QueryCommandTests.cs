using System.Reflection;
using System.Text.Json;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Settings;
using Shouldly;
using Routing = global::Catalog.Routing.Contracts;
using StringContracts = global::Catalog.String.Contracts;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Exercises query payload sources and exact gateway documents through CLI parsing.</summary>
public sealed class QueryCommandTests
{
    private const string ProfileToken = "query-test-token";
    private const string ItemId = "01ARZ3NDEKTSV4RRFFQ69G5FAV";

    /// <summary>Inline, file, and stdin payloads submit once and return canonical object or null documents.</summary>
    [Theory]
    [InlineData("inline", "accessor", false, true)]
    [InlineData("file", "accessor", false, true)]
    [InlineData("stdin", "accessor", false, true)]
    [InlineData("inline", "accessor", true, true)]
    [InlineData("file", "accessor", true, true)]
    [InlineData("stdin", "accessor", true, true)]
    [InlineData("inline", "constant", false, true)]
    [InlineData("file", "constant", false, true)]
    [InlineData("stdin", "constant", false, true)]
    [InlineData("inline", "constant", true, true)]
    [InlineData("file", "constant", true, true)]
    [InlineData("stdin", "constant", true, true)]
    [InlineData("inline", "explicit", false, true)]
    [InlineData("file", "explicit", false, true)]
    [InlineData("stdin", "explicit", false, true)]
    [InlineData("inline", "explicit", true, true)]
    [InlineData("file", "explicit", true, true)]
    [InlineData("stdin", "explicit", true, true)]
    [InlineData("inline", "accessor", false, false)]
    public async Task PayloadSourcesUseOneDescriptorRoutedPostAsync(
        string source, string aggregateSource, bool nullPayload, bool tenantFlag)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(TestContext.Current.CancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(15));
        string directory = Path.Combine(Path.GetTempPath(), "mcpcli-query-" + Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(directory);
            string document = nullPayload ? "null" : """{"items":[{"key":"item-42"}]}""";
            await using var gateway = new ScriptedGateway(_ => ScriptedGateway.Response(200, "OK", "application/json",
                $$"""{"correlationId":"01J9MZHXT3RKM0VWXRXGSJDATK","payload":{{document}},"success":true}"""));

            TextReader originalIn = Console.In;
            TextWriter originalOut = Console.Out;
            TextWriter originalError = Console.Error;
            using var output = new StringWriter();
            using var error = new StringWriter();
            string payload = aggregateSource == "accessor" ? $$"""{"ItemId":"{{ItemId}}"}""" : "{}";
            using var input = new StringReader(source == "stdin" ? payload : "stdin must not be read");
            try
            {
                string payloadArgument = payload;
                if (source == "file")
                {
                    string payloadFile = Path.Combine(directory, "query.json");
                    await File.WriteAllTextAsync(payloadFile, payload, timeout.Token);
                    payloadArgument = "@" + payloadFile;
                }
                else if (source == "stdin")
                {
                    payloadArgument = "-";
                }

                string operation = aggregateSource switch
                {
                    "constant" => "string-fixture.list-items",
                    "explicit" => "routing-fixture.get-http2-status",
                    _ => "routing-fixture.interface-item",
                };
                var store = new ProfileStore(Path.Combine(directory, "mcpcli.json"));
                store.Add("query-profile", new ConnectionProfile(gateway.Url, Token: ProfileToken, Tenant: "profile-tenant"));
                store.Use("query-profile");
                Func<IReadOnlyList<Assembly>> manifest = () => [typeof(Routing.Module).Assembly, typeof(StringContracts.Module).Assembly];
                List<string> arguments = ["query", operation, "--payload", payloadArgument];
                if (tenantFlag)
                {
                    arguments.AddRange(["--tenant", "session-tenant"]);
                }
                if (aggregateSource == "explicit")
                {
                    arguments.AddRange(["--aggregate-id", ItemId]);
                }

                Console.SetIn(input);
                Console.SetOut(output);
                Console.SetError(error);
                int exit = await new CliRunner(store, manifest, _ => null).InvokeAsync(arguments, timeout.Token);

                exit.ShouldBe(0, output.ToString() + error.ToString());
                GatewayRequest request = gateway.Requests.ShouldHaveSingleItem();
                request.Method.ShouldBe("POST");
                request.Path.ShouldBe("/api/v1/queries");
                request.Headers["Authorization"].ShouldBe("Bearer " + ProfileToken);
                string tenant = aggregateSource == "constant" ? "fixed-tenant"
                    : tenantFlag ? "session-tenant" : "profile-tenant";
                string expectedRequest = aggregateSource switch
                {
                    "constant" => """
                        {"tenant":"fixed-tenant","domain":"string-fixture","aggregateId":"items-index",
                         "queryType":"list-items-wire","projectionType":"string-items","payload":{}}
                        """,
                    "explicit" => $$$"""
                        {"tenant":"{{{tenant}}}","domain":"routing","aggregateId":"{{{ItemId}}}",
                         "queryType":"get-http2-status","projectionType":"routing-items","payload":{}}
                        """,
                    _ => $$"""
                        {"tenant":"{{tenant}}","domain":"routing","aggregateId":"{{ItemId}}",
                         "queryType":"interface-item-wire","projectionType":"routing-items",
                         "payload":{"ItemId":"{{ItemId}}"},"projectionActorType":"RoutingProjectionActor"}
                        """,
                };
                using JsonDocument expected = JsonDocument.Parse(expectedRequest);
                using JsonDocument actualRequest = JsonDocument.Parse(request.Body);
                JsonElement.DeepEquals(actualRequest.RootElement, expected.RootElement).ShouldBeTrue();
                using JsonDocument actualResult = JsonDocument.Parse(output.ToString());
                using JsonDocument expectedResult = JsonDocument.Parse(
                    $$"""{"operation":"{{operation}}","tenant":"{{tenant}}","document":{{document}}}""");
                JsonElement.DeepEquals(actualResult.RootElement, expectedResult.RootElement).ShouldBeTrue();
            }
            finally
            {
                Console.SetIn(originalIn);
                Console.SetOut(originalOut);
                Console.SetError(originalError);
            }
        }
        finally
        {
            if (Directory.Exists(directory))
            {
                Directory.Delete(directory, recursive: true);
            }
        }
    }
}

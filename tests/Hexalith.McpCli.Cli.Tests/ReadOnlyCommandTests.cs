using System.Text.Json;
using Shouldly;
using static Hexalith.McpCli.Cli.Tests.QueryCliHarness;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Proves read-only sessions refuse writes while preserving discovery and query execution.</summary>
public sealed class ReadOnlyCommandTests
{
    /// <summary>Combines both activation sources, URL states, and command input forms.</summary>
    public static TheoryData<bool, bool, string> RefusedInputs()
    {
        var data = new TheoryData<bool, bool, string>();
        foreach (bool environment in new[] { false, true })
        {
            foreach (bool withUrl in new[] { false, true })
            {
                foreach (string input in new[] { "absent", "invalid", "valid", "file", "stdin", "extension" })
                {
                    data.Add(environment, withUrl, input);
                }
            }
        }

        return data;
    }

    /// <summary>Refusal precedes input acquisition and leaves the Gateway and existing result file untouched.</summary>
    [Theory]
    [MemberData(nameof(RefusedInputs))]
    public async Task SendRefusesBeforeReadingInputAsync(bool environment, bool withUrl, string source)
    {
        await using var harness = new QueryCliHarness();
        string outputPath = Path.GetTempFileName();
        try
        {
            await File.WriteAllTextAsync(outputPath, "previous result", TestContext.Current.CancellationToken);
            List<string> args = ["send", "routing-fixture.computed-envelope", "--output", outputPath, "--format", "table"];
            if (!environment)
            {
                args.Add("--read-only");
            }

            switch (source)
            {
                case "invalid": args.AddRange(["--payload", "{"]); break;
                case "valid": args.AddRange(["--payload", $$"""{"ItemId":"{{ItemId}}"}""", "--tenant", "acme", "--actor", "operator-1"]); break;
                case "file": args.AddRange(["--payload", "@" + Path.Combine(outputPath, "missing.json")]); break;
                case "stdin": args.AddRange(["--payload", "-"]); break;
                case "extension": args.AddRange(["--payload", "{}", "--extension", "missing-equals"]); break;
            }

            // A disposed reader throws if the CLI attempts to acquire stdin, including an omitted payload.
            using var input = new StringReader("must not be read");
            input.Dispose();
            (int exit, string output, string error) = await harness.InvokeAsync(
                [.. args], withUrl, environment ? "true" : null, input);
            exit.ShouldBe(2);
            AssertJson(output, """{"error":{"code":"read_only","message":"Command submission is disabled in read-only mode."}}""");
            AssertDiagnostics(error);
            harness.Calls.ShouldBe(0);
            (await File.ReadAllTextAsync(outputPath, TestContext.Current.CancellationToken)).ShouldBe("previous result");
        }
        finally
        {
            File.Delete(outputPath);
        }
    }

    /// <summary>The shared executor still owns lookup and kind failures before read-only refusal.</summary>
    [Theory]
    [InlineData("unknown.operation", "unknown_operation")]
    [InlineData("string-fixture.list-items", "validation_failed")]
    public async Task SendPreservesLookupAndKindErrorsAsync(string operation, string code)
    {
        await using var harness = new QueryCliHarness();
        using var input = new StringReader("");
        input.Dispose();
        (int exit, string output, _) = await harness.InvokeAsync(
            ["send", operation, "--read-only", "--payload", "-"], withUrl: false, standardInput: input);
        exit.ShouldBe(2);
        using JsonDocument result = JsonDocument.Parse(output);
        JsonElement error = result.RootElement.GetProperty("error");
        error.GetProperty("code").GetString().ShouldBe(code);
        error.GetProperty("operation").GetString().ShouldBe(operation);
        if (code == "validation_failed")
        {
            error.GetProperty("violations")[0].GetProperty("path").GetString().ShouldBe("/operation");
        }
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Flag and environment activation permit a normally routed query without changing its documents.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task QueryRemainsAvailableAsync(bool environment)
    {
        await using var harness = new QueryCliHarness();
        string[] flags = environment ? [] : ["--read-only"];
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["query", "string-fixture.list-items", "--payload", "{}", .. flags],
            readOnlyEnvironment: environment ? "true" : null);
        exit.ShouldBe(0);
        AssertJson(output, """{"operation":"string-fixture.list-items","tenant":"fixed-tenant","document":{"items":[]}}""");
        AssertDiagnostics(error);
        harness.AssertRequest("""
            {"tenant":"fixed-tenant","domain":"string-fixture","aggregateId":"items-index",
             "queryType":"list-items-wire","projectionType":"string-items","payload":{}}
            """);
    }

    /// <summary>Environment-activated read-only discovery retains writes and describes their availability offline.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task EnvironmentPreservesDiscoveryAsync(bool withUrl)
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, _) = await harness.InvokeAsync(
            ["operations", "routing-fixture"], withUrl, "true");
        exit.ShouldBe(0);
        using JsonDocument list = JsonDocument.Parse(output);
        list.RootElement.GetProperty("operations").EnumerateArray().ShouldContain(operation =>
            operation.GetProperty("name").GetString() == "routing-fixture.computed-envelope"
            && operation.GetProperty("kind").GetString() == "write");

        foreach (bool write in new[] { false, true })
        {
            string operation = write ? "routing-fixture.computed-envelope" : "string-fixture.list-items";
            (int describeExit, string description, _) = await harness.InvokeAsync(["describe", operation], withUrl, "true");
            describeExit.ShouldBe(0);
            using JsonDocument document = JsonDocument.Parse(description);
            document.RootElement.GetProperty("kind").GetString().ShouldBe(write ? "write" : "read");
            document.RootElement.GetProperty("submittable").GetBoolean().ShouldBe(!write && withUrl);
            if (write || !withUrl)
            {
                document.RootElement.GetProperty("reason").GetString().ShouldBe(write ? "read_only" : "configuration_invalid");
            }
            else
            {
                document.RootElement.TryGetProperty("reason", out _).ShouldBeFalse();
            }
        }
        harness.Calls.ShouldBe(0);
    }

    /// <summary>Explicit false restores one successful write when the environment enables read-only mode.</summary>
    [Fact]
    public async Task ExplicitFalseAllowsCommandSubmissionAsync()
    {
        await using var harness = new QueryCliHarness(commandResponse: true);
        (int exit, string output, string error) = await harness.InvokeAsync(
            ["send", "routing-fixture.computed-envelope", "--read-only", "false",
                "--payload", $$"""{"ItemId":"{{ItemId}}"}""", "--tenant", "acme", "--actor", "operator-1"],
            readOnlyEnvironment: "true");
        exit.ShouldBe(0, output + error);
        using JsonDocument document = JsonDocument.Parse(output);
        document.RootElement.GetProperty("operation").GetString().ShouldBe("routing-fixture.computed-envelope");
        document.RootElement.GetProperty("status").GetString().ShouldBe("accepted");
        document.RootElement.GetProperty("aggregateId").GetString().ShouldBe(ItemId);
        document.RootElement.GetProperty("tenant").GetString().ShouldBe("acme");
        harness.Calls.ShouldBe(1);
    }

    /// <summary>An explicit false flag overrides the environment and restores ordinary payload validation.</summary>
    [Fact]
    public async Task ExplicitFalseOverridesEnvironmentAsync()
    {
        await using var harness = new QueryCliHarness();
        (int exit, string output, _) = await harness.InvokeAsync(
            ["send", "routing-fixture.computed-envelope", "--read-only", "false", "--payload", "{"],
            readOnlyEnvironment: "true");
        exit.ShouldBe(2);
        using JsonDocument document = JsonDocument.Parse(output);
        document.RootElement.GetProperty("error").GetProperty("code").GetString().ShouldBe("validation_failed");
        harness.Calls.ShouldBe(0);
    }
}

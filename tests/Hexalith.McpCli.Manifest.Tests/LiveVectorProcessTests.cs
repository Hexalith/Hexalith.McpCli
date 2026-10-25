using System.Text.Json;

using Hexalith.McpCli.Integration.Tests;

namespace Hexalith.McpCli.Manifest.Tests;

/// <summary>Exercises the actual private Python handoff without launching a topology.</summary>
public sealed class LiveVectorProcessTests
{
    /// <summary>The executing child receives the selected host, binding and private credentials.</summary>
    [Fact]
    public async Task ActualChildReceivesResolvedHostAndParentBinding()
    {
        string root = Path.Combine(Path.GetTempPath(), "mcpcli-handoff-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(root, "tools", "live-topology"));
        try
        {
            string script = """
                import json, os, pathlib, sys
                root = pathlib.Path.cwd()
                (root / 'handoff.json').write_text(json.dumps({'args':sys.argv[1:], 'binding':os.environ['MCPCLI_LIVE_BINDING'], 'url':os.environ['MCPCLI_LIVE_URL'], 'token':os.environ['MCPCLI_LIVE_TOKEN']}))
                (root / 'live-result.json').write_text(json.dumps({'operation':'fixture.operation', 'result':'passed'}))
                """;
            await File.WriteAllTextAsync(Path.Combine(root, "tools", "live-topology", "run_live.py"), script, TestContext.Current.CancellationToken);
            string host = Path.Combine(root, "selected adapter.dll");
            const string binding = "{\"planSha256\":\"parent-plan\"}";
            await LiveVectorProcess.RunAsync(root, "fixture.operation", root, host, binding,
                new Uri("http://127.0.0.1:12345/"), "private-child-token", TestContext.Current.CancellationToken);

            using JsonDocument handoff = JsonDocument.Parse(await File.ReadAllTextAsync(Path.Combine(root, "handoff.json"), TestContext.Current.CancellationToken));
            Assert.Equal(["--operation", "fixture.operation", "--output", root, "--host", host],
                handoff.RootElement.GetProperty("args").EnumerateArray().Select(value => value.GetString()).ToArray());
            Assert.Equal(binding, handoff.RootElement.GetProperty("binding").GetString());
            Assert.Equal("http://127.0.0.1:12345/", handoff.RootElement.GetProperty("url").GetString());
            Assert.Equal("private-child-token", handoff.RootElement.GetProperty("token").GetString());
        }
        finally { Directory.Delete(root, recursive: true); }
    }

    /// <summary>A failed child cannot reuse an earlier success or expose its private identity in diagnostics.</summary>
    /// <param name="defect">The independently rejected child outcome.</param>
    [Theory]
    [InlineData("nonzero")]
    [InlineData("missing-receipt")]
    [InlineData("operation")]
    [InlineData("result")]
    public async Task FailedChildInvalidatesStaleReceiptAndKeepsDiagnosticsTokenSafe(string defect)
    {
        string root = Path.Combine(Path.GetTempPath(), "mcpcli-handoff-failure-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(root, "tools", "live-topology"));
        try
        {
            const string token = "private-failing-child-token";
            await File.WriteAllTextAsync(Path.Combine(root, "live-result.json"),
                "{\"operation\":\"fixture.operation\",\"result\":\"passed\"}", TestContext.Current.CancellationToken);
            string script = "defect = " + JsonSerializer.Serialize(defect) + "\n" + """
                import json, os, pathlib, sys
                root = pathlib.Path.cwd()
                receipt = root / 'live-result.json'
                (root / 'receipt-state.json').write_text(json.dumps({'staleReceiptPresent': receipt.exists()}))
                token = os.environ['MCPCLI_LIVE_TOKEN']
                print('child stdout ' + token)
                print('child stderr ' + token, file=sys.stderr)
                if defect != 'missing-receipt':
                    receipt.write_text(json.dumps({'operation': 'wrong-' + token if defect == 'operation' else 'fixture.operation',
                                                   'result': 'failed-' + token if defect == 'result' else 'passed'}))
                sys.exit(7 if defect == 'nonzero' else 0)
                """;
            await File.WriteAllTextAsync(Path.Combine(root, "tools", "live-topology", "run_live.py"), script, TestContext.Current.CancellationToken);
            Exception? failure = await Record.ExceptionAsync(() => LiveVectorProcess.RunAsync(root, "fixture.operation", root,
                Path.Combine(root, "selected adapter.dll"), "{}", new Uri("http://127.0.0.1:12345/"), token,
                TestContext.Current.CancellationToken));
            Assert.NotNull(failure);
            Assert.Contains("Live vector fixture.operation", failure.Message, StringComparison.Ordinal);
            Assert.DoesNotContain(token, failure.ToString(), StringComparison.Ordinal);
            string reason = defect switch
            {
                "nonzero" => "failed:",
                "missing-receipt" => "omitted its receipt",
                "operation" => "returned a different Operation",
                _ => "returned an unsuccessful result",
            };
            Assert.Contains(reason, failure.Message, StringComparison.Ordinal);
            if (defect == "nonzero")
            {
                Assert.Contains("child stdout <redacted>", failure.Message, StringComparison.Ordinal);
                Assert.Contains("child stderr <redacted>", failure.Message, StringComparison.Ordinal);
            }
            if (defect is "operation" or "result")
                Assert.Contains("<redacted>", failure.Message, StringComparison.Ordinal);
            using JsonDocument state = JsonDocument.Parse(await File.ReadAllTextAsync(Path.Combine(root, "receipt-state.json"), TestContext.Current.CancellationToken));
            Assert.False(state.RootElement.GetProperty("staleReceiptPresent").GetBoolean());
            if (defect == "missing-receipt") Assert.False(File.Exists(Path.Combine(root, "live-result.json")));
        }
        finally { Directory.Delete(root, recursive: true); }
    }
}

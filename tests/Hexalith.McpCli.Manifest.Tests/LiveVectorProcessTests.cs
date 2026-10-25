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
}

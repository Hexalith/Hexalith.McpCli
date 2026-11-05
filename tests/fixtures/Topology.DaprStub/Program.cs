if (args is ["catalog-pipe-holder", string pidFile])
{
    File.WriteAllText(pidFile, Environment.ProcessId.ToString(System.Globalization.CultureInfo.InvariantCulture));
    await Task.Delay(TimeSpan.FromSeconds(30));
    return 0;
}

if (args is ["catalog-pipe-parent", string marker])
{
    var start = new System.Diagnostics.ProcessStartInfo(Environment.ProcessPath!) { UseShellExecute = false };
    start.ArgumentList.Add("catalog-pipe-holder");
    start.ArgumentList.Add(marker);
    using System.Diagnostics.Process child = System.Diagnostics.Process.Start(start)
        ?? throw new InvalidOperationException("The controlled pipe holder did not start.");
    return 0;
}

if (Environment.GetEnvironmentVariable("MCPCLI_TEST_READER_ASSETS") is { Length: > 0 } readerAssets)
{
    File.AppendAllText(Environment.GetEnvironmentVariable("MCPCLI_TEST_READER_CALLS")!, System.Text.Json.JsonSerializer.Serialize(args) + Environment.NewLine);
    if (args is ["restore", string project, ..])
    {
        string directory = Path.Combine(Path.GetDirectoryName(project)!, "obj");
        Directory.CreateDirectory(directory);
        File.Copy(readerAssets, Path.Combine(directory, "project.assets.json"));
        return 0;
    }
    Console.Error.WriteLine("controlled-reader-build-stop");
    return 9;
}

if (args.Contains("rev-parse") && int.TryParse(Environment.GetEnvironmentVariable("MCPCLI_TEST_GIT_DELAY_MS"), out int gitDelay))
{
    Thread.Sleep(gitDelay);
    return 0;
}

if (int.TryParse(Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_DELAY_MS"), out int delay)) Thread.Sleep(delay);
if (args.SequenceEqual(new[] { "--version" }))
{
    if (int.TryParse(Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_VERSION_EXIT"), out int versionExit) && versionExit != 0)
        return versionExit;
    Console.WriteLine(Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_VERSION_OUTPUT") ?? "CLI version: test-fixture");
    return 0;
}

if (!args.SequenceEqual(new[] { "list", "--output", "json" }))
{
    Console.Error.WriteLine("The preflight fixture supports only 'dapr list --output json'.");
    return 64;
}

if (int.TryParse(Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_EXIT"), out int exitCode) && exitCode != 0)
{
    Console.Error.WriteLine(Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_ERROR"));
    return exitCode;
}

Console.WriteLine(Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_SNAPSHOT") ?? "[]");
return 0;

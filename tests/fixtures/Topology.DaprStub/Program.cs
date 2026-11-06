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
    string? behavior = Environment.GetEnvironmentVariable("MCPCLI_TEST_READER_BEHAVIOR");
    if (args is ["restore", string project, ..])
    {
        string directory = Path.Combine(Path.GetDirectoryName(project)!, "obj");
        Directory.CreateDirectory(directory);
        File.Copy(readerAssets, Path.Combine(directory, "project.assets.json"));
        if (behavior == "copy-cohort-before-build")
            File.AppendAllText(Path.Combine(Path.GetDirectoryName(project)!, "PublishedCatalogArtifactCohort.cs"), "// changed copy");
        if (behavior == "catalog-source-after-restore")
            File.AppendAllText(Environment.GetEnvironmentVariable("MCPCLI_TEST_READER_CATALOG_SOURCE")!, "// changed catalog");
        return 0;
    }
    if (behavior is not null && args is ["build", ..])
    {
        Directory.CreateDirectory(args[Array.IndexOf(args, "--output") + 1]);
        string build = Path.GetDirectoryName(args[1])!;
        if (behavior == "copy-cohort-after-build")
            File.AppendAllText(Path.Combine(build, "PublishedCatalogArtifactCohort.cs"), "// changed build copy");
        if (behavior == "uppercase-source-after-build")
            File.WriteAllText(Path.Combine(build, "Extra.CS"), "// unsealed uppercase source");
        return 0;
    }
    if (behavior is not null && args is [_, string request])
    {
        using var document = System.Text.Json.JsonDocument.Parse(File.ReadAllBytes(request));
        string output = document.RootElement.GetProperty("outputDirectory").GetString()!;
        if (behavior == "source-cohort-after-generation")
            File.AppendAllText(Environment.GetEnvironmentVariable("MCPCLI_TEST_READER_COHORT_SOURCE")!, "// changed source");
        if (behavior == "copy-cohort-after-generation")
            File.AppendAllText(Path.Combine(Path.GetDirectoryName(request)!, "PublishedCatalogArtifactCohort.cs"), "// changed copy");
        if (behavior == "extra-source-after-generation")
        {
            string extra = Path.Combine(Path.GetDirectoryName(request)!, "extra");
            Directory.CreateDirectory(extra);
            File.WriteAllText(Path.Combine(extra, "Unsealed.cs"), "// unsealed source");
        }
        File.WriteAllText(Path.Combine(output, "receipt.json"), "{\"result\":\"controlled-fixture\"}");
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

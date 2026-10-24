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

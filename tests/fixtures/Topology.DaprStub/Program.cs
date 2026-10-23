if (args.SequenceEqual(new[] { "--version" }))
{
    if (int.TryParse(Environment.GetEnvironmentVariable("MCPCLI_TEST_DAPR_DELAY_MS"), out int delay)) Thread.Sleep(delay);
    Console.WriteLine("CLI version: test-fixture");
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

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>One HTTP request captured by <see cref="ScriptedGateway" />.</summary>
/// <param name="Method">The request method.</param>
/// <param name="Path">The request target path.</param>
/// <param name="Headers">The request headers by case-insensitive name.</param>
/// <param name="Body">The decoded UTF-8 request body.</param>
internal sealed record GatewayRequest(string Method, string Path, IReadOnlyDictionary<string, string> Headers, string Body);

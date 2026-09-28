using System.Text.Json;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Core.Settings;

namespace Hexalith.McpCli.Cli;

/// <summary>Writes one public Core document to the CLI output channel.</summary>
internal static class CliOutput
{
    internal static async Task<int> WriteAsync(object? document, OperationError? error,
        ResolvedSettings settings, CancellationToken cancellationToken, bool tabular = false)
    {
        if (error is null && settings.Format == "table" && !tabular)
        {
            await Console.Error.WriteLineAsync("This result is emitted as JSON; no table view is defined.").ConfigureAwait(false);
        }

        string output = error is not null
            ? JsonSerializer.Serialize(new { error }, McpCliJson.Result)
            : settings.Format == "table" && tabular ? FormatTable(document!) : JsonSerializer.Serialize(document, McpCliJson.Result);
        if (error is null && settings.Output is not null)
        {
            await File.WriteAllTextAsync(settings.Output, output + Environment.NewLine, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            await Console.Out.WriteLineAsync(output).ConfigureAwait(false);
        }

        return error is null ? 0 : 2;
    }

    internal static Task<int> WriteErrorAsync(OperationError error, CancellationToken cancellationToken)
    {
        _ = cancellationToken;
        return WriteDirectErrorAsync(error);
    }

    private static async Task<int> WriteDirectErrorAsync(OperationError error)
    {
        await Console.Out.WriteLineAsync(JsonSerializer.Serialize(new { error }, McpCliJson.Result)).ConfigureAwait(false);
        return 2;
    }

    private static string FormatTable(object document)
    {
        if (document is ModulesDocument modules)
        {
            return "NAME\tOPERATIONS\tDESCRIPTION" + Environment.NewLine
                + string.Join(Environment.NewLine, modules.Modules.Select(module
                    => $"{module.Name}\t{module.OperationCount}\t{module.Description}"));
        }

        if (document is OperationsDocument operations)
        {
            return "NAME\tKIND\tDESCRIPTION" + Environment.NewLine
                + string.Join(Environment.NewLine, operations.Operations.Select(operation
                    => $"{operation.Name}\t{operation.Kind}\t{operation.Description}"));
        }

        JsonElement json = JsonSerializer.SerializeToElement(document, McpCliJson.Result);
        return "FIELD\tVALUE" + Environment.NewLine + string.Join(Environment.NewLine,
            json.EnumerateObject().Select(property => property.Name + "\t" + JsonSerializer.Serialize(property.Value)));
    }
}

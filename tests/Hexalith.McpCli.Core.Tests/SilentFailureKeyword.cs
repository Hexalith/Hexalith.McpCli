using System.Text.Json;
using Json.Schema;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Provides a schema keyword that rejects an instance without supplying an error message.</summary>
internal sealed class SilentFailureKeyword : IKeywordHandler
{
    /// <inheritdoc />
    public string Name => "silentFailure";

    /// <inheritdoc />
    public object ValidateKeywordValue(JsonElement value) => value.GetBoolean();

    /// <inheritdoc />
    public void BuildSubschemas(KeywordData keyword, BuildContext context)
    {
    }

    /// <inheritdoc />
    public KeywordEvaluation Evaluate(KeywordData keyword, EvaluationContext context)
        => new() { Keyword = Name, IsValid = false };
}

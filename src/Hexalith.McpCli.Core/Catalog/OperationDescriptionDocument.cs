using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>The public description of one operation.</summary>
/// <param name="Name">The canonical operation name.</param>
/// <param name="Kind">The public read or write kind.</param>
/// <param name="Description">The operation description.</param>
/// <param name="Schema">The module payload schema.</param>
/// <param name="Example">The optional example payload.</param>
/// <param name="Envelope">The applicable envelope fields.</param>
/// <param name="LintFindings">Description quality findings.</param>
/// <param name="Submittable">Whether this session can submit the operation.</param>
/// <param name="Reason">The reason submission is unavailable.</param>
public sealed record OperationDescriptionDocument(
    string Name,
    string Kind,
    string Description,
    JsonNode Schema,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] JsonNode? Example,
    OperationEnvelopeDocument Envelope,
    IReadOnlyList<LintFinding> LintFindings,
    bool Submittable,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Reason);

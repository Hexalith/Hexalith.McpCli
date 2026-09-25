namespace Hexalith.McpCli.Core.Schema;

/// <summary>Contains all reported payload violations.</summary>
/// <param name="Violations">The violations in evaluator order.</param>
public sealed record PayloadValidationResult(IReadOnlyList<PayloadViolation> Violations)
{
    /// <summary>Gets whether the payload passed validation.</summary>
    public bool IsValid => Violations.Count == 0;
}

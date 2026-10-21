using Hexalith.McpCli.Core.Catalog;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Protects exact approved lint without allowing new findings or broad code suppression.</summary>
public sealed class DescriptionLintGateTests
{
    private const string Accepted = """[{"operation":"tenants.list-tenants","code":"payload_paging_member","property":"/properties/PageSize","approvalReference":"test-only recorded approval"}]""";

    /// <summary>Only the recorded operation/property exception passes.</summary>
    [Fact]
    public void ExactApprovalPassesButOtherOperationsPropertiesAndCodesFail()
    {
        DescriptionLintGate.Check([("tenants.list-tenants", new LintFinding("payload_paging_member", "warning", "message", "/properties/PageSize"))], Accepted).ShouldBeEmpty();
        DescriptionLintGate.Check([("tenants.other", new LintFinding("payload_paging_member", "warning", "message", "/properties/PageSize"))], Accepted)
            .ShouldBe(new[] { "stale accepted lint [\"tenants.list-tenants\",\"payload_paging_member\",\"/properties/PageSize\"].",
                "unapproved lint [\"tenants.other\",\"payload_paging_member\",\"/properties/PageSize\"]." });
        DescriptionLintGate.Check([("tenants.list-tenants", new LintFinding("payload_paging_member", "warning", "message", "/properties/Cursor"))], Accepted)
            .ShouldBe(new[] { "stale accepted lint [\"tenants.list-tenants\",\"payload_paging_member\",\"/properties/PageSize\"].",
                "unapproved lint [\"tenants.list-tenants\",\"payload_paging_member\",\"/properties/Cursor\"]." });
        DescriptionLintGate.Check([("tenants.list-tenants", new LintFinding("missing_description", "warning", "message", "/properties/PageSize"))], Accepted)
            .ShouldBe(new[] { "stale accepted lint [\"tenants.list-tenants\",\"payload_paging_member\",\"/properties/PageSize\"].",
                "unapproved lint [\"tenants.list-tenants\",\"missing_description\",\"/properties/PageSize\"]." });
    }

    /// <summary>Unrecorded findings, stale exceptions and absent approval references fail.</summary>
    [Fact]
    public void MissingApprovalAndStaleExceptionsFail()
    {
        DescriptionLintGate.Check([], Accepted).ShouldBe(new[] { "stale accepted lint [\"tenants.list-tenants\",\"payload_paging_member\",\"/properties/PageSize\"]." });
        DescriptionLintGate.Check([("parties.list-parties", new LintFinding("payload_paging_member", "warning", "message", "/properties/PageSize"))], null)
            .ShouldBe(new[] { "unapproved lint [\"parties.list-parties\",\"payload_paging_member\",\"/properties/PageSize\"]." });
        DescriptionLintGate.Check([], Accepted.Replace("test-only recorded approval", ""))
            .ShouldBe(new[] { "accepted lint: expected operation, code, property and nonempty approvalReference." });
    }

    /// <summary>Malformed approval documents fail with complete deterministic diagnostics.</summary>
    /// <param name="json">The malformed acceptance document.</param>
    /// <param name="expected">The full expected diagnostic.</param>
    [Theory]
    [InlineData("{}", "accepted lint: expected array.")]
    [InlineData("null", "accepted lint: expected array.")]
    [InlineData("{", "accepted lint: invalid JSON.")]
    [InlineData("[null]", "accepted lint: expected operation, code, property and nonempty approvalReference.")]
    [InlineData("[{\"operation\":\"tenants.list-tenants\",\"code\":\"payload_paging_member\",\"property\":\"/properties/PageSize\"}]", "accepted lint: expected operation, code, property and nonempty approvalReference.")]
    [InlineData("[{\"operation\":\"tenants.list-tenants\",\"code\":\"payload_paging_member\",\"property\":\"/properties/PageSize\",\"approvalReference\":\"test-only\",\"extra\":\"unapproved\"}]", "accepted lint: expected operation, code, property and nonempty approvalReference.")]
    [InlineData("[{\"operation\":\"tenants.list-tenants\",\"code\":\"payload_paging_member\",\"property\":\"/properties/PageSize\",\"reference\":\"test-only\"}]", "accepted lint: expected operation, code, property and nonempty approvalReference.")]
    public void MalformedApprovalDocumentsFail(string json, string expected)
        => DescriptionLintGate.Check([], json).ShouldBe(new[] { expected });

    /// <summary>Repeated exact acceptances cannot hide duplicate approval rows.</summary>
    [Fact]
    public void DuplicateApprovalRowsFail()
        => DescriptionLintGate.Check([], "[" + Accepted[1..^1] + "," + Accepted[1..^1] + "]")
            .ShouldBe(new[] { "accepted lint: duplicate exception [\"tenants.list-tenants\",\"payload_paging_member\",\"/properties/PageSize\"]." });
}

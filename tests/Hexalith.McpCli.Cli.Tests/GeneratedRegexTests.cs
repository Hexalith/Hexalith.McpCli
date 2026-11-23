using System.Reflection;
using System.Text.RegularExpressions;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Cli;
using Hexalith.McpCli.Core.Settings;
using Hexalith.McpCli.Mcp;
using Shouldly;

namespace Hexalith.McpCli.Cli.Tests;

/// <summary>Checks .NET validation anchors in the production runtime assemblies.</summary>
public sealed class GeneratedRegexTests
{
    /// <summary>Rejects whole-string patterns whose dollar anchor also accepts a trailing newline.</summary>
    [Fact]
    public void WholeStringPatternsUseAbsoluteEndAnchor()
    {
        Assembly[] assemblies =
        [
            typeof(HexalithModuleAttribute).Assembly,
            typeof(ProfileStore).Assembly,
            typeof(McpCliMcpServiceCollectionExtensions).Assembly,
            typeof(CliRunner).Assembly,
        ];
        const BindingFlags flags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static
            | BindingFlags.Instance | BindingFlags.DeclaredOnly;
        var violations = new List<string>();
        foreach (Type type in assemblies.SelectMany(assembly => assembly.GetTypes()))
        {
            foreach (MemberInfo member in type.GetMembers(flags))
            {
                string? pattern = member.GetCustomAttribute<GeneratedRegexAttribute>()?.Pattern;
                if (pattern is not null && pattern.StartsWith('^') && Regex.IsMatch(pattern, @"(?<!\\)(?:\\\\)*\$\z"))
                {
                    violations.Add($"{type.FullName}.{member.Name}");
                }
            }
        }

        violations.ShouldBeEmpty(@"Whole-string .NET regexes must use \z in place of $.");
    }
}

using System.Collections.Immutable;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Analyzers;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Diagnostics;
using Shouldly;

namespace Hexalith.McpCli.Analyzers.Tests;

/// <summary>
/// Verifies warnings on semantically identified operation declarations.
/// </summary>
public sealed class MissingOperationDescriptionAnalyzerTests
{
    /// <summary>Reports a warning for literal or constant blank descriptions on classes and records.</summary>
    /// <param name="declaration">The decorated operation declaration.</param>
    [Theory]
    [InlineData("[HexalithCommand(\"\")] public class MissingCommand { }")]
    [InlineData("[HexalithCommand(\" \\t \")] public record MissingCommand;")]
    [InlineData("[HexalithQuery(\"\")] public class MissingQuery { }")]
    [InlineData("[HexalithQuery(\"  \")] public record MissingQuery;")]
    [InlineData("[HexalithCommand(Text.Blank)] public record MissingCommand;")]
    [InlineData("[HexalithQuery(Text.Blank)] public class MissingQuery { }")]
    [InlineData("[HexalithCommand(Text.Empty)] public class MissingCommand { }")]
    [InlineData("[HexalithQuery(Text.Empty)] public record MissingQuery;")]
    [InlineData("[HexalithCommandAttribute(\"\")] public class MissingCommand { }")]
    [InlineData("[HexalithQueryAttribute(\"\")] public record MissingQuery;")]
    [InlineData("[HexalithCommand(null)] public class MissingCommand { }")]
    [InlineData("[HexalithQuery(null)] public record MissingQuery;")]
    public async Task BlankDescriptionsWarnAtTypeName(string declaration)
    {
        string source = "using Hexalith.McpCli.Abstractions; internal static class Text { internal const string Blank = \"   \"; internal const string Empty = \"\"; } " + declaration;
        ImmutableArray<Diagnostic> diagnostics = await AnalyzeAsync(source);

        Diagnostic diagnostic = diagnostics.ShouldHaveSingleItem();
        diagnostic.Id.ShouldBe(MissingOperationDescriptionAnalyzer.DiagnosticId);
        diagnostic.Severity.ShouldBe(DiagnosticSeverity.Warning);
        string typeName = declaration.Contains("MissingCommand", StringComparison.Ordinal) ? "MissingCommand" : "MissingQuery";
        diagnostic.Location.SourceSpan.Start.ShouldBe(source.LastIndexOf(typeName, StringComparison.Ordinal));
        diagnostic.GetMessage().ShouldBe($"Operation '{typeName}' needs a nonblank description");
    }

    /// <summary>Accepts nonblank descriptions, including compile-time constants.</summary>
    [Fact]
    public async Task NonblankDescriptionsDoNotWarn()
    {
        const string source = """
            using Hexalith.McpCli.Abstractions;
            namespace Contracts;
            internal static class Text { internal const string Valid = "  Finds items  "; }
            [HexalithCommand("Creates an item")] public sealed class CreateItem { }
            [HexalithQuery(Text.Valid)] public sealed record FindItems;
            """;

        (await AnalyzeAsync(source)).ShouldBeEmpty();
    }

    /// <summary>Ignores undecorated types and unrelated attributes with the same short name.</summary>
    [Fact]
    public async Task UnrelatedDeclarationsDoNotWarn()
    {
        const string source = """
            using System;
            namespace Other;
            [AttributeUsage(AttributeTargets.Class)]
            public sealed class HexalithCommandAttribute(string description) : Attribute { }
            [AttributeUsage(AttributeTargets.Class)]
            public sealed class HexalithQueryAttribute(string description) : Attribute { }
            [HexalithCommand("")] public sealed class UnrelatedCommand { }
            [HexalithQueryAttribute("")] public sealed record UnrelatedQuery;
            public sealed record PlainQuery;
            """;

        (await AnalyzeAsync(source)).ShouldBeEmpty();
    }

    /// <summary>Reports only one warning when both operation decorations are blank.</summary>
    [Fact]
    public async Task MultipleBlankDecorationsProduceOneWarning()
    {
        const string source = """
            using Hexalith.McpCli.Abstractions;
            [HexalithCommand("")]
            [HexalithQuery(" ")]
            public sealed record AmbiguousOperation;
            """;

        (await AnalyzeAsync(source)).ShouldHaveSingleItem();
    }

    /// <summary>Locates a partial type warning at the declaration carrying the decoration.</summary>
    [Fact]
    public async Task PartialTypeWarningPointsToDecoratedDeclaration()
    {
        const string source = """
            using Hexalith.McpCli.Abstractions;
            public partial class PartialOperation { }
            [HexalithQuery("")]
            public partial class PartialOperation { }
            """;

        Diagnostic diagnostic = (await AnalyzeAsync(source)).ShouldHaveSingleItem();
        diagnostic.Location.SourceSpan.Start.ShouldBe(source.LastIndexOf("PartialOperation", StringComparison.Ordinal));
    }

    /// <summary>Ignores a counterfeit type with the same fully qualified name in another assembly.</summary>
    [Fact]
    public async Task CounterfeitAttributeDoesNotWarn()
    {
        const string source = """
            namespace Hexalith.McpCli.Abstractions
            {
                [System.AttributeUsage(System.AttributeTargets.Class)]
                public sealed class HexalithQueryAttribute(string description) : System.Attribute { }
            }
            namespace Contracts
            {
                [Hexalith.McpCli.Abstractions.HexalithQuery("")]
                public sealed record UnrelatedQuery;
            }
            """;

        (await AnalyzeAsync(source)).ShouldBeEmpty();
    }

    /// <summary>Finds the real attribute when a same-named source attribute is also present.</summary>
    [Fact]
    public async Task SameMetadataNameStillWarnsForGenuineAttribute()
    {
        const string source = """
            extern alias genuine;
            namespace Hexalith.McpCli.Abstractions
            {
                [System.AttributeUsage(System.AttributeTargets.Class)]
                public sealed class HexalithQueryAttribute(string description) : System.Attribute { }
            }
            namespace Contracts
            {
                [genuine::Hexalith.McpCli.Abstractions.HexalithQuery("")]
                public sealed record GenuineQuery;
                [Hexalith.McpCli.Abstractions.HexalithQuery("")]
                public sealed record CounterfeitQuery;
            }
            """;

        Diagnostic diagnostic = (await AnalyzeAsync(source, aliasAbstractions: true)).ShouldHaveSingleItem();
        diagnostic.Location.SourceSpan.Start.ShouldBe(source.IndexOf("GenuineQuery", StringComparison.Ordinal));
        diagnostic.GetMessage().ShouldBe("Operation 'GenuineQuery' needs a nonblank description");
    }

    /// <summary>Warns on decorated types in generated Contracts source.</summary>
    [Fact]
    public async Task GeneratedContractsSourceWarns()
    {
        const string source = """
            using Hexalith.McpCli.Abstractions;
            [HexalithQuery(" ")]
            public sealed record GeneratedQuery;
            """;

        Diagnostic diagnostic = (await AnalyzeAsync(source, "GeneratedContracts.g.cs")).ShouldHaveSingleItem();
        diagnostic.Id.ShouldBe(MissingOperationDescriptionAnalyzer.DiagnosticId);
        diagnostic.Location.SourceSpan.Start.ShouldBe(source.IndexOf("GeneratedQuery", StringComparison.Ordinal));
    }

    private static async Task<ImmutableArray<Diagnostic>> AnalyzeAsync(
        string source,
        string path = "Contracts.cs",
        bool aliasAbstractions = false)
    {
        var tree = CSharpSyntaxTree.ParseText(source, new CSharpParseOptions(LanguageVersion.CSharp14), path);
        string? trustedAssemblies = AppContext.GetData("TRUSTED_PLATFORM_ASSEMBLIES") as string;
        trustedAssemblies.ShouldNotBeNull();
        IEnumerable<MetadataReference> references = trustedAssemblies.Split(Path.PathSeparator)
            .Select(path => MetadataReference.CreateFromFile(path));
        MetadataReferenceProperties abstractionsProperties = aliasAbstractions
            ? new MetadataReferenceProperties(aliases: ImmutableArray.Create("genuine"))
            : MetadataReferenceProperties.Assembly;
        references = references.Append(MetadataReference.CreateFromFile(
            typeof(HexalithCommandAttribute).Assembly.Location,
            abstractionsProperties));
        CSharpCompilation compilation = CSharpCompilation.Create(
            "AnalyzerFixture",
            [tree],
            references,
            new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));
        compilation.GetDiagnostics().Where(diagnostic => diagnostic.Severity == DiagnosticSeverity.Error).ShouldBeEmpty();
        return await compilation.WithAnalyzers(
            ImmutableArray.Create<DiagnosticAnalyzer>(new MissingOperationDescriptionAnalyzer())).GetAnalyzerDiagnosticsAsync();
    }
}

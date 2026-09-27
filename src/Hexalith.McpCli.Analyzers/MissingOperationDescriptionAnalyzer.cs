using System.Collections.Immutable;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Diagnostics;

namespace Hexalith.McpCli.Analyzers;

/// <summary>
/// Warns when a decorated operation has no useful description.
/// </summary>
[DiagnosticAnalyzer(LanguageNames.CSharp)]
public sealed class MissingOperationDescriptionAnalyzer : DiagnosticAnalyzer
{
    /// <summary>The stable diagnostic identifier for a missing operation description.</summary>
    public const string DiagnosticId = "MCPCLI001";

    private static readonly DiagnosticDescriptor Rule = new(
        DiagnosticId,
        "Operation description is missing",
        "Operation '{0}' needs a nonblank description",
        "Usage",
        DiagnosticSeverity.Warning,
        isEnabledByDefault: true,
        description: "Hexalith commands and queries need a nonblank description for agent discovery.");

    /// <inheritdoc />
    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics => ImmutableArray.Create(Rule);

    /// <inheritdoc />
    public override void Initialize(AnalysisContext context)
    {
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.Analyze | GeneratedCodeAnalysisFlags.ReportDiagnostics);
        context.EnableConcurrentExecution();
        context.RegisterCompilationStartAction(startContext =>
        {
            INamedTypeSymbol? commandAttribute = startContext.Compilation.GetTypeByMetadataName(
                "Hexalith.McpCli.Abstractions.HexalithCommandAttribute");
            INamedTypeSymbol? queryAttribute = startContext.Compilation.GetTypeByMetadataName(
                "Hexalith.McpCli.Abstractions.HexalithQueryAttribute");
            if (commandAttribute?.ContainingAssembly.Identity.Name != "Hexalith.McpCli.Abstractions")
            {
                commandAttribute = null;
            }

            if (queryAttribute?.ContainingAssembly.Identity.Name != "Hexalith.McpCli.Abstractions")
            {
                queryAttribute = null;
            }

            if (commandAttribute is null && queryAttribute is null)
            {
                return;
            }

            startContext.RegisterSymbolAction(symbolContext =>
            {
                var type = (INamedTypeSymbol)symbolContext.Symbol;
                if (type.TypeKind != TypeKind.Class)
                {
                    return;
                }

                foreach (AttributeData attribute in type.GetAttributes())
                {
                    if (attribute.AttributeClass is null
                        || (!SymbolEqualityComparer.Default.Equals(attribute.AttributeClass, commandAttribute)
                            && !SymbolEqualityComparer.Default.Equals(attribute.AttributeClass, queryAttribute)))
                    {
                        continue;
                    }

                    if (attribute.ConstructorArguments.Length == 0)
                    {
                        continue;
                    }

                    TypedConstant description = attribute.ConstructorArguments[0];
                    if (description.Kind == TypedConstantKind.Primitive
                        && string.IsNullOrWhiteSpace(description.Value as string))
                    {
                        SyntaxReference? attributeSyntax = attribute.ApplicationSyntaxReference;
                        SyntaxReference? declaration = attributeSyntax is null
                            ? null
                            : type.DeclaringSyntaxReferences.FirstOrDefault(reference =>
                                reference.SyntaxTree == attributeSyntax.SyntaxTree
                                && reference.Span.Contains(attributeSyntax.Span));
                        Location? location = declaration is null
                            ? type.Locations.FirstOrDefault()
                            : type.Locations.FirstOrDefault(candidate =>
                                candidate.SourceTree == declaration.SyntaxTree
                                && declaration.Span.Contains(candidate.SourceSpan));
                        if (location is not null && location.IsInSource)
                        {
                            symbolContext.ReportDiagnostic(Diagnostic.Create(Rule, location, type.Name));
                        }

                        break;
                    }
                }
            }, SymbolKind.NamedType);
        });
    }
}

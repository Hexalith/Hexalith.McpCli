namespace Hexalith.McpCli.Core.Tests;

/// <summary>One module-scoped Operation Shape and the hash-approved vectors that cover it.</summary>
/// <param name="Module">The canonical module that declares the shape.</param>
/// <param name="Key">The opaque Operation Shape key.</param>
/// <param name="Operations">The cataloged operations with this shape, in ordinal order.</param>
/// <param name="VectorFiles">The full paths of hash-approved vector files whose operation has this shape, in ordinal order.</param>
/// <param name="VectorOperations">The distinct operations those vectors exercise, in ordinal order.</param>
internal sealed record ShapeCoverage(string Module, string Key, IReadOnlyList<string> Operations,
    IReadOnlyList<string> VectorFiles, IReadOnlyList<string> VectorOperations);

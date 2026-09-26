namespace Hexalith.McpCli.Core.Catalog;

/// <summary>
/// Reports a Contracts declaration that the Catalog cannot expose; the only exception type the Catalog turns into a diagnostic.
/// </summary>
public sealed class ContractDeclarationException : Exception
{
    /// <summary>Initializes a new instance of the <see cref="ContractDeclarationException"/> class.</summary>
    /// <param name="category">The stable Catalog diagnostic category.</param>
    /// <param name="message">The author-facing detail naming the failing member or value.</param>
    public ContractDeclarationException(string category, string message)
        : this(category, message, null)
    {
    }

    /// <summary>Initializes a new instance of the <see cref="ContractDeclarationException"/> class.</summary>
    /// <param name="category">The stable Catalog diagnostic category.</param>
    /// <param name="message">The author-facing detail naming the failing member or value.</param>
    /// <param name="innerException">The underlying contract failure, if any.</param>
    public ContractDeclarationException(string category, string message, Exception? innerException)
        : base(message, innerException)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(category);
        ArgumentException.ThrowIfNullOrWhiteSpace(message);
        Category = category;
    }

    /// <summary>Gets the stable Catalog diagnostic category.</summary>
    public string Category { get; }
}

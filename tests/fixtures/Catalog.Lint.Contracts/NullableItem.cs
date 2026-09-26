using System.ComponentModel;

namespace Catalog.Lint.Contracts;

/// <summary>Provides nullable nested value-type members for description linting.</summary>
/// <param name="Count">An undescribed nested count.</param>
/// <param name="ExternalId">A described identifier-like nested member.</param>
public readonly record struct NullableItem(
    int Count,
    [property: Description("An external reference identifier in the nullable item.")] string ExternalId);

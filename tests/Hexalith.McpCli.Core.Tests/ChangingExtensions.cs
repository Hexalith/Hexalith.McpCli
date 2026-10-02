using System.Collections;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Changes its enumerated value after the first read to expose repeated caller enumeration.</summary>
internal sealed class ChangingExtensions : IReadOnlyDictionary<string, string>
{
    private int _enumerationCount;

    /// <summary>Gets the number of times the caller enumerated the dictionary.</summary>
    public int EnumerationCount => Volatile.Read(ref _enumerationCount);

    /// <inheritdoc />
    public int Count => 1;

    /// <inheritdoc />
    public IEnumerable<string> Keys => ["task-id"];

    /// <inheritdoc />
    public IEnumerable<string> Values => ["safe"];

    /// <inheritdoc />
    public string this[string key] => ContainsKey(key) ? "safe" : throw new KeyNotFoundException();

    /// <inheritdoc />
    public bool ContainsKey(string key) => string.Equals(key, "task-id", StringComparison.Ordinal);

    /// <inheritdoc />
    public bool TryGetValue(string key, out string value)
    {
        bool found = ContainsKey(key);
        value = found ? "safe" : string.Empty;
        return found;
    }

    /// <inheritdoc />
    public IEnumerator<KeyValuePair<string, string>> GetEnumerator()
    {
        string value = Interlocked.Increment(ref _enumerationCount) == 1 ? "safe" : "<script>";
        return ((IEnumerable<KeyValuePair<string, string>>)
            [new KeyValuePair<string, string>("task-id", value)]).GetEnumerator();
    }

    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}

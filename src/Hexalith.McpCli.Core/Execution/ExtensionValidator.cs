using System.Text;
using System.Text.RegularExpressions;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Execution;

/// <summary>Applies the gateway's default extension limits before submission.</summary>
internal static partial class ExtensionValidator
{
    private const string ReservedActorAdminKey = "actor:globalAdmin";

    internal static IReadOnlyList<PayloadViolation> Validate(
        IReadOnlyDictionary<string, string>? extensions,
        IReadOnlySet<string> allowedExtensions)
    {
        if (extensions is null || extensions.Count == 0)
        {
            return [];
        }

        var violations = new List<PayloadViolation>();
        if (extensions.Count > 32)
        {
            violations.Add(new PayloadViolation("/extensions", "At most 32 extensions are allowed."));
        }

        int totalSize = 0;
        var seenKeys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach ((string key, string value) in extensions.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            string pointer = "/extensions/" + key.Replace("~", "~0", StringComparison.Ordinal).Replace("/", "~1", StringComparison.Ordinal);
            if (!seenKeys.Add(key))
            {
                violations.Add(new PayloadViolation(pointer, "Extension keys must be unique regardless of case."));
            }

            if (!allowedExtensions.Any(allowed => string.Equals(allowed, key, StringComparison.OrdinalIgnoreCase)))
            {
                violations.Add(new PayloadViolation(pointer, "The extension key is not allowlisted."));
            }

            if (IsReservedKey(key))
            {
                violations.Add(new PayloadViolation(pointer, "The extension key is reserved."));
            }
            else if (!IsValidKey(key))
            {
                violations.Add(new PayloadViolation(pointer, "The extension key is invalid."));
            }

            if (value is null || value.Length > 1_000 || HasForbiddenControl(value)
                || HasDangerousCharacters(value) || HasInjection(value))
            {
                violations.Add(new PayloadViolation(pointer, "The extension value is invalid."));
                continue;
            }

            totalSize += Encoding.UTF8.GetByteCount(key) + Encoding.UTF8.GetByteCount(value);
        }

        if (totalSize > 4_096)
        {
            violations.Add(new PayloadViolation("/extensions", "The combined extension size exceeds 4096 UTF-8 bytes."));
        }

        return violations;
    }

    /// <summary>Checks the grammar and sanitizer rules shared by stored allowlists and submitted extensions.</summary>
    /// <param name="key">The extension key to validate.</param>
    /// <returns><see langword="true" /> when the key is safe and well-formed; otherwise, <see langword="false" />.</returns>
    internal static bool IsValidKey(string key)
        => key.Length is >= 1 and <= 100 && KeyPattern().IsMatch(key) && !HasInjection(key)
            && !IsReservedKey(key);

    private static bool IsReservedKey(string key)
        => string.Equals(key, ReservedActorAdminKey, StringComparison.OrdinalIgnoreCase)
            || key.StartsWith("identity:", StringComparison.OrdinalIgnoreCase);

    private static bool HasForbiddenControl(string value)
        => value.Any(character => character is < (char)0x20 and not '\t' and not '\n' and not '\r');

    private static bool HasDangerousCharacters(string value)
        => value.AsSpan().IndexOfAny(['<', '>', '&', '\'', '"']) >= 0;

    private static bool HasInjection(string value)
        => XssPattern().IsMatch(value) || SqlPattern().IsMatch(value) || LdapPattern().IsMatch(value) || PathPattern().IsMatch(value);

    [GeneratedRegex(@"^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?(?::[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?)*\z")]
    private static partial Regex KeyPattern();

    [GeneratedRegex(@"(?i)(<\s*script|javascript\s*:|on\w+\s*=|<\s*iframe|<\s*object|<\s*embed)")]
    private static partial Regex XssPattern();

    [GeneratedRegex(@"(?i)(';\s*(DROP|ALTER|DELETE|INSERT|UPDATE|EXEC)|UNION\s+SELECT|--\s*$)")]
    private static partial Regex SqlPattern();

    [GeneratedRegex(@"(\)\(|\*\)\(|\|\(|&\()")]
    private static partial Regex LdapPattern();

    [GeneratedRegex(@"(\.\./|\.\.\\)")]
    private static partial Regex PathPattern();
}

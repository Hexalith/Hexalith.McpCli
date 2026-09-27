using System.Text;
using System.Text.RegularExpressions;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Execution;

/// <summary>Applies the gateway's default extension limits before submission.</summary>
internal static partial class ExtensionValidator
{
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
        foreach ((string key, string value) in extensions.OrderBy(item => item.Key, StringComparer.Ordinal))
        {
            string pointer = "/extensions/" + key.Replace("~", "~0", StringComparison.Ordinal).Replace("/", "~1", StringComparison.Ordinal);
            if (!allowedExtensions.Any(allowed => string.Equals(allowed, key, StringComparison.OrdinalIgnoreCase)))
            {
                violations.Add(new PayloadViolation(pointer, "The extension key is not allowlisted."));
            }

            if (key.Length is < 1 or > 100 || !KeyPattern().IsMatch(key) || HasInjection(key))
            {
                violations.Add(new PayloadViolation(pointer, "The extension key is invalid."));
            }

            if (value is null || value.Length > 1_000 || HasForbiddenControl(value) || HasInjection(value))
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

    private static bool HasForbiddenControl(string value)
        => value.Any(character => character is < (char)0x20 and not '\t' and not '\n' and not '\r');

    private static bool HasInjection(string value)
        => XssPattern().IsMatch(value) || SqlPattern().IsMatch(value) || LdapPattern().IsMatch(value) || PathPattern().IsMatch(value);

    [GeneratedRegex(@"^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?(?::[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?)*$")]
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

using System.Collections;
using System.Text.RegularExpressions;
using System.Text.Json;

namespace Hexalith.McpCli.AppHost;

/// <summary>Retains bounded source-tool diagnostics using the CI lane's credential redaction conventions.</summary>
internal static class NativeCatalogDiagnostics
{
    /// <summary>Removes PEM, bearer, named key and known environment-secret values before retention.</summary>
    internal static string Sanitize(string text)
    {
        text = Regex.Replace(text, "-----BEGIN [^-]+-----.*?(?:-----END [^-]+-----|\\z)", "[REDACTED PEM]", RegexOptions.Singleline);
        text = Regex.Replace(text, @"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED JWT]");
        text = Regex.Replace(text, @"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]");
        text = Regex.Replace(text, @"(?i)((?<quote>\\+)""[^""\r\n]*(?:SigningKey|PrivateKey)\k<quote>""\s*:\s*)\k<quote>""[^""\r\n]*(?:\k<quote>""|\z)",
            match => match.Groups[1].Value + match.Groups["quote"].Value + "\"[REDACTED]" + match.Groups["quote"].Value + "\"");
        text = Regex.Replace(text, "\"(?:[^\"\\\\]|\\\\.)*\"", match =>
        {
            if (!match.Value.Contains('\\')) return match.Value;
            try
            {
                string decoded = JsonSerializer.Deserialize<string>(match.Value)!;
                string redacted = Sanitize(decoded);
                return redacted == decoded ? match.Value : JsonSerializer.Serialize(redacted);
            }
            catch (JsonException) { return match.Value; }
        });
        text = Regex.Replace(text, @"(?i)(""[^""]*(?:SigningKey|PrivateKey)""\s*:\s*)""[^""]*(?:""|\z)", "$1\"[REDACTED]\"");
        text = Regex.Replace(text, @"(?i)((?:SigningKey|PrivateKey)(?:=|:|\s)+)[^\s,\]""}]+", "$1[REDACTED]");
        foreach (DictionaryEntry entry in Environment.GetEnvironmentVariables())
        {
            if (entry.Key is string key && entry.Value is string value && value.Length >= 8
                && Regex.IsMatch(key, "TOKEN|PASSWORD|SECRET|CERT_KEY|SIGNINGKEY|PRIVATE_?KEY|API_KEY", RegexOptions.IgnoreCase))
                text = text.Replace(value, "[REDACTED]", StringComparison.Ordinal);
        }
        return text.Length <= 16_384 ? text : text[..16_384] + " [TRUNCATED]";
    }

    /// <summary>Copies only allowlisted already-sanitized tool diagnostics before owned cleanup removes files.</summary>
    internal static string Read(string directory)
    {
        var parts = new List<string>();
        foreach (string name in new[] { "restore.log", "build.log", "generation.log" })
        {
            string path = Path.Combine(directory, "reader", name);
            if (!File.Exists(path)) continue;
            try
            {
                using var reader = new StreamReader(path);
                char[] buffer = new char[16_384];
                int count = reader.ReadBlock(buffer, 0, buffer.Length);
                parts.Add(name + ": " + Sanitize(new string(buffer, 0, count)));
            }
            catch (Exception failure) when (failure is IOException or UnauthorizedAccessException)
            {
                parts.Add(name + ": diagnostic file unavailable (" + failure.GetType().Name + ")");
            }
        }
        return Sanitize(string.Join(Environment.NewLine, parts));
    }
}

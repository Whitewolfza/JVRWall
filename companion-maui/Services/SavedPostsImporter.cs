using System.Text.Json;
using System.Text.RegularExpressions;

namespace JVRWall.Companion.Services;

public record SavedItem(string Url, string Label, bool LooksLikeRecipe);

/// <summary>
/// Facebook has no API for saved posts. This reads the "Saved items and collections"
/// JSON from Facebook's "Download your information" export (or plain pasted links).
/// </summary>
public static class SavedPostsImporter
{
    static readonly Regex UrlRx = new(@"https?://[^\s""<>]+", RegexOptions.IgnoreCase);
    static readonly Regex RecipeRx = new(
        @"recipe|ingredient|cook|bake|baking|dinner|lunch|breakfast|dessert|casserole|soup|stew|salad|pasta|chicken|beef|cake|cookies?|bread|sauce|marinade|air ?fryer|slow ?cooker|oven|tbsp|tsp|cups?\b|resep|braai|potjie",
        RegexOptions.IgnoreCase);

    public static List<SavedItem> Scan(IEnumerable<string> fileContents)
    {
        var raw = new List<(string url, string label, string text)>();
        foreach (var content in fileContents)
        {
            try
            {
                using var doc = JsonDocument.Parse(content);
                Walk(doc.RootElement, "", raw);
            }
            catch (JsonException)
            {
                foreach (Match m in UrlRx.Matches(content)) raw.Add((m.Value, "", ""));
            }
        }
        var seen = new HashSet<string>();
        return raw.Where(r => seen.Add(r.url))
            .Select(r =>
            {
                var label = FixMojibake(r.label);
                return new SavedItem(r.url, label, RecipeRx.IsMatch(FixMojibake(r.text) + " " + r.url));
            }).ToList();
    }

    static void Walk(JsonElement el, string ctx, List<(string, string, string)> acc)
    {
        switch (el.ValueKind)
        {
            case JsonValueKind.Array:
                foreach (var e in el.EnumerateArray()) Walk(e, ctx, acc);
                break;
            case JsonValueKind.Object:
                string? name = Str(el, "name") ?? Str(el, "title");
                var c = Str(el, "title") ?? Str(el, "text") ?? Str(el, "description") ?? ctx;
                var url = Str(el, "url") ?? Str(el, "href") ?? Str(el, "uri");
                if (url != null && UrlRx.IsMatch(url) && url.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                    acc.Add((url, name ?? c, string.Join(' ', new[] { name, Str(el, "text"), Str(el, "description"), c }.Where(s => s != null))));
                foreach (var p in el.EnumerateObject()) Walk(p.Value, c, acc);
                break;
        }
    }

    static string? Str(JsonElement el, string prop) =>
        el.TryGetProperty(prop, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;

    // Facebook exports UTF-8 bytes escaped as latin-1 code points.
    static string FixMojibake(string s)
    {
        if (s.Any(ch => ch > 255)) return s;
        try { return System.Text.Encoding.UTF8.GetString(System.Text.Encoding.Latin1.GetBytes(s)); }
        catch { return s; }
    }
}

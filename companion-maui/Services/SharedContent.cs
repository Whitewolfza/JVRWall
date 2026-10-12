using System.Text.RegularExpressions;

namespace JVRWall.Companion.Services;

public record SharedRecipe(string Name, string? Url, string? Notes);

/// <summary>Turns shared text (e.g. from Facebook's Share sheet) into a recipe draft.</summary>
public static class SharedContent
{
    static readonly Regex UrlRx = new(@"https?://[^\s""<>]+", RegexOptions.IgnoreCase);

    public static SharedRecipe Parse(string? subject, string? text)
    {
        text ??= "";
        var m = UrlRx.Match(text);
        var url = m.Success ? m.Value : null;
        var body = UrlRx.Replace(text, "").Trim();
        var firstLine = body.Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                            .FirstOrDefault();
        var name = !string.IsNullOrWhiteSpace(subject) && !UrlRx.IsMatch(subject) ? subject!.Trim() : firstLine ?? url ?? "";
        if (name.Length > 120) name = name[..120];
        return new SharedRecipe(name, url, body.Length == 0 ? null : body[..Math.Min(body.Length, 2000)]);
    }
}

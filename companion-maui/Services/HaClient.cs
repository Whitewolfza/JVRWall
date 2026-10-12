using System.Net.Http.Headers;
using System.Net.Http.Json;

namespace JVRWall.Companion.Services;

public class HaClient
{
    static readonly HttpClient Http = new();

    public static string? BaseUrl { get => Preferences.Get("ha_url", null); set => Preferences.Set("ha_url", value?.Trim().TrimEnd('/') ?? ""); }
    public static Task<string?> GetToken() => SecureStorage.GetAsync("ha_token");
    public static Task SetToken(string t) => SecureStorage.SetAsync("ha_token", t.Trim());

    public static async Task<(bool ok, string message)> AddRecipe(string name, string? url, string? notes, string source)
    {
        var token = await GetToken();
        if (string.IsNullOrEmpty(BaseUrl) || string.IsNullOrEmpty(token))
            return (false, "Set the Home Assistant URL and token in Settings first.");
        if (!BaseUrl!.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            return (false, "Home Assistant URL must use https://");
        try
        {
            using var req = new HttpRequestMessage(HttpMethod.Post, $"{BaseUrl}/api/services/jvrwall/add_recipe");
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            req.Content = JsonContent.Create(new { name, url, notes, source });
            using var res = await Http.SendAsync(req);
            return res.IsSuccessStatusCode ? (true, "Saved") : (false, $"Failed: {(int)res.StatusCode}");
        }
        catch (Exception ex) { return (false, "Failed: " + ex.Message); }
    }
}

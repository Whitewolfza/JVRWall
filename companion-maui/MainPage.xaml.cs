using JVRWall.Companion.Services;

namespace JVRWall.Companion;

public partial class MainPage : ContentPage
{
    List<SavedItem> _items = new();

    public MainPage()
    {
        InitializeComponent();
        HaUrlEntry.Text = HaClient.BaseUrl;
    }

    protected override async void OnAppearing()
    {
        base.OnAppearing();
        TokenEntry.Text = await HaClient.GetToken();
    }

    /// <summary>Called by the platform share receiver.</summary>
    public void ReceiveShare(string? subject, string? text)
    {
        var r = SharedContent.Parse(subject, text);
        MainThread.BeginInvokeOnMainThread(() =>
        {
            NameEntry.Text = r.Name; UrlEntry.Text = r.Url; NotesEditor.Text = r.Notes;
            StatusLabel.Text = "Review and tap Save.";
        });
    }

    async void OnPaste(object? s, EventArgs e) =>
        ReceiveShare(null, await Clipboard.Default.GetTextAsync());

    async void OnSave(object? s, EventArgs e)
    {
        var (ok, msg) = await HaClient.AddRecipe(NameEntry.Text ?? "", UrlEntry.Text, NotesEditor.Text, "facebook-share");
        StatusLabel.Text = ok ? "✔ Recipe saved!" : msg;
    }

    async void OnSaveSettings(object? s, EventArgs e)
    {
        HaClient.BaseUrl = HaUrlEntry.Text;
        await HaClient.SetToken(TokenEntry.Text ?? "");
        StatusLabel.Text = "Settings saved.";
    }

    async void OnPickFile(object? s, EventArgs e)
    {
        var files = await FilePicker.Default.PickMultipleAsync();
        if (files == null) return;
        var contents = new List<string>();
        foreach (var f in files)
        {
            using var r = new StreamReader(await f.OpenReadAsync());
            contents.Add(await r.ReadToEndAsync());
        }
        _items = SavedPostsImporter.Scan(contents);
        Found.ItemsSource = _items.Select(i => new { i.Url, Label = string.IsNullOrEmpty(i.Label) ? i.Url : i.Label, i.LooksLikeRecipe }).ToList();
        Found.SelectedItems.Clear();
        foreach (var o in (IEnumerable<dynamic>)Found.ItemsSource)
            if (o.LooksLikeRecipe) Found.SelectedItems.Add(o);
        AddSelected.IsVisible = _items.Count > 0;
        StatusLabel.Text = $"{_items.Count} item(s) found, {_items.Count(i => i.LooksLikeRecipe)} look like recipes.";
    }

    void OnSelectionChanged(object? s, SelectionChangedEventArgs e) { }

    async void OnAddSelected(object? s, EventArgs e)
    {
        int ok = 0, bad = 0;
        foreach (dynamic o in Found.SelectedItems.ToList())
        {
            var (good, _) = await HaClient.AddRecipe((string)o.Label, (string)o.Url, null, "facebook-saved");
            if (good) ok++; else bad++;
        }
        StatusLabel.Text = $"Added {ok} recipe(s)" + (bad > 0 ? $", {bad} failed" : "") + ".";
    }
}

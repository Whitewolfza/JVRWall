using Android.App;
using Android.Content;
using Android.Content.PM;

namespace JVRWall.Companion;

[Activity(Theme = "@style/Maui.SplashTheme", MainLauncher = true, LaunchMode = LaunchMode.SingleTop,
    ConfigurationChanges = ConfigChanges.ScreenSize | ConfigChanges.Orientation | ConfigChanges.UiMode |
                           ConfigChanges.ScreenLayout | ConfigChanges.SmallestScreenSize | ConfigChanges.Density)]
[IntentFilter(new[] { Intent.ActionSend }, Categories = new[] { Intent.CategoryDefault }, DataMimeType = "text/plain")]
public class MainActivity : MauiAppCompatActivity
{
    protected override void OnCreate(Android.OS.Bundle? savedInstanceState)
    {
        base.OnCreate(savedInstanceState);
        HandleShare(Intent);
    }

    protected override void OnNewIntent(Intent? intent)
    {
        base.OnNewIntent(intent);
        HandleShare(intent);
    }

    static void HandleShare(Intent? intent)
    {
        if (intent?.Action != Intent.ActionSend) return;
        var text = intent.GetStringExtra(Intent.ExtraText);
        var subject = intent.GetStringExtra(Intent.ExtraSubject);
        // App.Main may not exist yet on cold start; retry shortly.
        Task.Run(async () =>
        {
            for (int i = 0; i < 50 && App.Main == null; i++) await Task.Delay(100);
            App.Main?.ReceiveShare(subject, text);
        });
    }
}

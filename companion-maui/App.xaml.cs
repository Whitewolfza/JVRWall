namespace JVRWall.Companion;

public partial class App : Application
{
    public static MainPage? Main { get; private set; }

    public App()
    {
        InitializeComponent();
        Main = new MainPage();
        MainPage = new NavigationPage(Main);
    }
}

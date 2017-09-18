import warnings
import my_scripts.my_app

if __name__ == "__main__":
    warnings.filterwarnings('ignore')
    my_scripts.my_app.MyApp(redirect=False).MainLoop()

import wx
import my_frame

class MyApp(wx.App):
    def OnInit(self):
        frame = my_frame.MyFrame(None, "YouTube Music - David Georiev - v3.30")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True

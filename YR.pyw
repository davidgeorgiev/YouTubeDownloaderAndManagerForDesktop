import wx
import wx.html2
import urllib2
import json
import urllib
import os
from playsound import playsound
import threading
import re
import time
import webbrowser
GlobalSmartThreadRuning = 0


api_key = #ENTER YOUR API KEY HERE

class MyYouTubeSearcher():
    def __init__(self,parent):
        self.parent = parent
        self.data_info = ""
        self.full_data_info = ""
        self.content_details = ""
        self.t1 = 0
        self.DeleteAllMp3()
    def SearchPlease(self,query):
        query = query.encode(encoding='UTF-8',errors='strict')
        self.DeleteAllMp3()
        self.parent.statusbar.SetStatusText('Searching for '+query.decode(encoding='UTF-8',errors='strict'))
        query = query.replace(' ', '+')
        self.data_info = ""
        self.found_ids = list()
        splitted_content = list()
        my_url = "https://www.googleapis.com/youtube/v3/search?part=id&q="+query+"&type=video&key="+api_key
        content = urllib2.urlopen(my_url).read()
        self.data_info = json.loads(content)
        self.SaveThumbByIndex(0)
    def LoadStatisticsAndInformationByIndex(self,index):
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.data_info["items"][index]["id"]["videoId"]+"&key="+api_key+"&fields=items(id,snippet(channelId,title,categoryId),statistics)&part=snippet,statistics"
        content = urllib2.urlopen(my_url).read()
        self.full_data_info = json.loads(content)
    def LoadContentDetailsByIndex(self,index):
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.data_info["items"][index]["id"]["videoId"]+"&part=contentDetails&key="+api_key
        content = urllib2.urlopen(my_url).read()
        self.content_details = json.loads(content)
    def GetDuration(self):
        duration_str = self.content_details["items"][0]["contentDetails"]["duration"]
        duration_sec = re.findall('\d+', duration_str)
        i = 0
        mul = 1
        sum_seconds = 0
        while(i<len(duration_sec)):
            sum_seconds += int(duration_sec[len(duration_sec)-1-i])*mul
            i+=1
            mul*=60
        return str(sum_seconds)
    def GetTitle(self):
        return self.full_data_info["items"][0]["snippet"]["title"]
    def SaveThumbByIndex(self,index):
        self.parent.statusbar.SetStatusText('Fetching image...')
        thumb_url = "https://img.youtube.com/vi/"+self.data_info["items"][index]["id"]["videoId"]+"/0.jpg"
        testfile = urllib.URLopener()
        testfile.retrieve(thumb_url, "file.jpg")

    def DownloadMp3ByIndex(self,index):
        self.parent.statusbar.SetStatusText('Downloading mp3...')
        #json_url = "http://www.youtubeinmp3.com/fetch/?format=JSON&video=https://www.youtube.com/watch?v="+self.data_info["items"][index]["id"]["videoId"]
        #content = urllib2.urlopen(json_url).read()
        #mp3_info = json.loads(content)
        #print mp3_info["link"]
        command = 'youtubedl\\youtubedl.exe "https://www.youtube.com/watch?v='+self.data_info["items"][index]["id"]["videoId"]+'" --extract-audio --audio-format mp3'
        os.system(command)
    def PlayMp3InDir(self,event):
        self.parent.statusbar.SetStatusText('Playing music...')
        self.SearchMp3FileAndPlay()
    def DeleteAllMp3(self):
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                if file.endswith('.mp3'):
                    os.system('del "'+os.path.join(root,file)+'"')
    def SearchMp3FileAndPlay(self):
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                if file.endswith('.mp3'):
                    #print 'rename '+os.path.join(root,file)+' '+os.path.join(root,'mp3.mp3')
                    os.system('rename "'+os.path.join(root,file)+'" "'+'mp3.mp3'+'"')
                    playsound("mp3.mp3")
    def StopNow(self):
        self.t1.stop()
class MyFrame(wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, title):
        self.MyYouTubeSearcherObj = MyYouTubeSearcher(self)

        wx.Frame.__init__(self, parent, -1, title,
                          pos=(150, 150), size=(380, 545))

        # Create the menubar
        self.menuBar = wx.MenuBar()

        # and a menu
        self.menu = wx.Menu()

        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        self.menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit this simple sample")

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.OnTimeToClose, id=wx.ID_EXIT)

        # and put the menu on the menubar
        self.menuBar.Append(self.menu, "&File")
        self.SetMenuBar(self.menuBar)

        self.statusbar = self.CreateStatusBar()


        # Now create the Panel to put the other controls on.
        self.panel = wx.Panel(self)

        # and a few controls
        self.text = wx.StaticText(self.panel, -1, "")
        self.text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.text.SetSize(self.text.GetBestSize())

        self.search_text = wx.TextCtrl(self.panel, size=(140, -1))
        self.smartbtn = wx.Button(self.panel, -1, "Smart Button")

        self.browser = wx.html2.WebView.New(self.panel)

        self.remaining_time_seconds = wx.StaticText(self.panel, -1, "")
        self.remaining_time_seconds.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.remaining_time_seconds.SetSize(self.remaining_time_seconds.GetBestSize())

        self.open_in_browser_btn = wx.Button(self.panel, -1, "Open in browser")
        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnSmartButton, self.smartbtn)
        self.Bind(wx.EVT_BUTTON, self.OnOpenInBrowser, self.open_in_browser_btn)

        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.search_text)
        self.sizer.Add(self.smartbtn, 0, wx.ALL, 10)
        self.sizer.Add(self.text, 0, wx.ALL, 10)

        self.sizer.Add(self.browser, 1, wx.EXPAND, 10)
        self.sizer.Add(self.remaining_time_seconds, 0, wx.ALL, 10)
        self.sizer.Add(self.open_in_browser_btn, 0, wx.ALL, 10)
        self.panel.SetSizer(self.sizer)
        self.panel.Layout()

        self.browser.SetPage('<img src="'+os.getcwd()+'\\no.png" alt="no image" height="240" width="320">',"")
        self.open_in_browser_btn.Disable()
    def OnRestart(self, evt):
        self.Destroy()
    def OnTimeToClose(self, evt):
        """Event handler for the button click."""
        self.Destroy()

    def OnFunButton(self, evt):
        """Event handler for the button click."""
        self.MyYouTubeSearcherObj.SearchPlease(self.search_text.GetValue())
    def OnSmartButton(self, evt):
        self.smartbtn.Disable()
        """Event handler for the button click."""
        self.MyYouTubeSearcherObj.SearchPlease(self.search_text.GetValue())
        self.MyYouTubeSearcherObj.LoadStatisticsAndInformationByIndex(0)
        self.MyYouTubeSearcherObj.LoadContentDetailsByIndex(0)
        self.browser.SetPage('<img src="'+os.getcwd()+'\\file.jpg" alt="'+self.MyYouTubeSearcherObj.GetTitle().encode(encoding='UTF-8',errors='strict')+'" height="240" width="320">',"")

        self.text.SetLabel(self.MyYouTubeSearcherObj.GetTitle())
        self.open_in_browser_btn.Enable()
        self.panel.Layout()
        self.t1 = threading.Thread(target=self.SmartBtnThread)
        self.t1.daemon = True
        self.t1.start()
    def RunTimer(self):
        remaining_time = int(self.MyYouTubeSearcherObj.GetDuration())
        while(remaining_time>0):
            time.sleep(1)
            remaining_time-=1
            self.remaining_time_seconds.SetLabel(str(remaining_time)+" seconds remaining")
    def SmartBtnThread(self):
        self.OnReadButton("")
        self.t_timer = threading.Thread(target=self.RunTimer)
        self.t_timer.daemon = True
        self.t_timer.start()
        self.MyYouTubeSearcherObj.PlayMp3InDir("")
        self.smartbtn.Disable()
    def OnReadButton(self, evt):
        """Event handler for the button click."""
        self.MyYouTubeSearcherObj.DownloadMp3ByIndex(0)
    def OnOpenInBrowser(self,event):
        url = 'https://www.youtube.com/watch?v='+self.MyYouTubeSearcherObj.data_info["items"][0]["id"]["videoId"]
        webbrowser.open_new(url)
        self.Destroy()

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "YouTube Radio")
        self.SetTopWindow(frame)

        frame.Show(True)
        return True

if __name__ == "__main__":
    MyApp(redirect=False).MainLoop()

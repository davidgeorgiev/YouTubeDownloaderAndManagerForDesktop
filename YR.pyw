import wx
import wx.html2
import urllib2
import json
import urllib
import os
import threading
import re
import time
import webbrowser
from msvcrt import getch
GlobalSmartThreadRuning = 0


api_key = #ENTER YOUR API KEY HERE

class MyYouTubeSearcher():
    def __init__(self,parent):
        self.index = 0
        self.parent = parent
        self.data_info = ""
        self.full_data_info = ""
        self.content_details = ""
        self.t1 = 0
        self.DeleteAllMp3()
    def GetNumberOfFoundVideos(self):
        return len(self.data_info)-2
    def SearchPlease(self,query):
        query = query.encode(encoding='UTF-8',errors='strict')
        self.parent.statusbar.SetStatusText('Searching for '+query.decode(encoding='UTF-8',errors='strict'))
        query = query.replace(' ', '+')
        self.data_info = list()
        self.found_ids = list()
        splitted_content = list()
        my_url = "https://www.googleapis.com/youtube/v3/search?part=id&q="+query+"&type=video&key="+api_key
        content = urllib2.urlopen(my_url).read()
        self.data_info = json.loads(content)
        self.parent.statusbar.SetStatusText('Done')
    def LoadStatisticsAndInformationByIndex(self,index):
        self.full_data_info = list()
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.data_info["items"][index]["id"]["videoId"]+"&key="+api_key+"&fields=items(id,snippet(channelId,title,categoryId),statistics)&part=snippet,statistics"
        content = urllib2.urlopen(my_url).read()
        self.full_data_info = json.loads(content)
    def LoadContentDetailsByIndex(self,index):
        self.content_details = list()
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
        return re.sub('[^A-Za-z0-9]+', ' ', self.full_data_info["items"][0]["snippet"]["title"])
    def SaveThumbByIndex(self,index):
        print(self.GetNumberOfFoundVideos())
        if self.GetNumberOfFoundVideos()==3:
            self.parent.text.SetLabel("")
            self.parent.duration_info.SetLabel("")
            self.parent.browser.SetPage('<img src="'+os.getcwd()+'\\no.png" alt="no image" height="240" width="320">',"")
            self.parent.statusbar.SetStatusText('Nothing Found...')
            return None
        self.parent.statusbar.SetStatusText('Fetching image...')
        thumb_url = "https://img.youtube.com/vi/"+self.data_info["items"][index]["id"]["videoId"]+"/0.jpg"
        testfile = urllib.URLopener()
        testfile.retrieve(thumb_url, "file.jpg")
        self.parent.statusbar.SetStatusText('Done')
    def DownloadMp3ByIndex(self,index):
        self.parent.statusbar.SetStatusText('Downloading mp3...')
        #json_url = "http://www.youtubeinmp3.com/fetch/?format=JSON&video=https://www.youtube.com/watch?v="+self.data_info["items"][index]["id"]["videoId"]
        #content = urllib2.urlopen(json_url).read()
        #mp3_info = json.loads(content)
        #print mp3_info["link"]
        command = 'youtubedl\\youtubedl.exe "https://www.youtube.com/watch?v='+self.data_info["items"][index]["id"]["videoId"]+'" --extract-audio --audio-format mp3'
        self.AppendToLogFile('https://www.youtube.com/watch?v='+self.data_info["items"][index]["id"]["videoId"])
        os.system(command)
        self.parent.statusbar.SetStatusText('Done')
    def AppendToLogFile(self,log):
        with open("all_played_videos.txt", "a") as myfile:
            myfile.write(log+'\n')
    def LetsHearTheSong(self):
        self.t_timer = threading.Thread(target=self.parent.RunTimer)
        self.t_timer.daemon = True
        self.t_timer.start()
        os.startfile("mp3.mp3", 'open')
    def PlayMp3InDir(self,event):
        self.parent.statusbar.SetStatusText('Playing music...')
        self.RenameMp3File()
        self.LetsHearTheSong()
        self.parent.statusbar.SetStatusText('Done')
    def DeleteAllMp3(self):
        self.StopMusic()
        time.sleep(2)
        os.system('del "'+os.path.join(os.getcwd(),"*.mp3")+'"')
    def RenameMp3File(self):
        self.StopMusic()
        time.sleep(2)
        os.system('rename "'+os.path.join(os.getcwd(),"*.mp3")+'" "'+'mp3.mp3'+'"')

    def StopMusic(self):
        os.startfile("no sound\\no.mp3", 'open')
    def GetRandomWord(self):
        url = "http://setgetgo.com/randomword/get.php"
        content = urllib2.urlopen(url).read()
        print content
        self.parent.search_text.SetValue(content+" music")
class MyFrame(wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, title):
        self.remaining_time_in_seconds_for_timer_data = 0
        self.MyYouTubeSearcherObj = MyYouTubeSearcher(self)

        wx.Frame.__init__(self, parent, -1, title, pos=(150, 150), size=(370, 630),style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        self.Center()


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
        self.check_random_search = wx.CheckBox(self.panel, label = 'random search',pos = (10,10))
        self.text = wx.StaticText(self.panel, -1, "")
        self.duration_info = wx.StaticText(self.panel, -1, "")
        self.text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.text.SetSize(self.text.GetBestSize())

        self.search_text = wx.TextCtrl(self.panel)
        self.smartbtn = wx.Button(self.panel, -1, "Smart Button")
        self.playbtn = wx.Button(self.panel, -1, "Play Button")
        self.prevbtn = wx.Button(self.panel, -1, "Prev")
        self.nextbtn = wx.Button(self.panel, -1, "Next")

        self.browser = wx.html2.WebView.New(self.panel)

        self.remaining_time_seconds = wx.StaticText(self.panel, -1, "")
        self.remaining_time_seconds.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.remaining_time_seconds.SetSize(self.remaining_time_seconds.GetBestSize())

        self.open_in_browser_btn = wx.Button(self.panel, -1, "Open in browser")
        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnSmartButton, self.smartbtn)
        self.Bind(wx.EVT_BUTTON, self.OnOpenInBrowser, self.open_in_browser_btn)
        self.Bind(wx.EVT_BUTTON, self.OnLetSPlayMusic, self.playbtn)
        self.Bind(wx.EVT_BUTTON, self.PrevSong, self.prevbtn)
        self.Bind(wx.EVT_BUTTON, self.NextSong, self.nextbtn)


        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer.Add(self.check_random_search,0,wx.ALL,10)
        self.sizer2.Add(self.smartbtn, 0, wx.ALL, 10)
        self.sizer2.Add(self.playbtn, 0, wx.ALL, 10)
        self.sizer2.Add(self.search_text,flag=wx.ALIGN_CENTER)
        self.sizer3.Add(self.prevbtn, 0, wx.ALL, 10)
        self.sizer3.Add(self.nextbtn, 0, wx.ALL, 10)
        self.sizer.Add(self.sizer2)
        self.sizer.Add(self.text, 0, wx.ALL, 10)
        self.sizer.Add(self.duration_info, 0, wx.ALL, 10)

        self.sizer.Add(self.browser, 1, wx.EXPAND, 10)
        self.sizer.Add(self.remaining_time_seconds, 0, wx.ALL, 10)
        self.sizer.Add(self.sizer3)
        self.sizer.Add(self.open_in_browser_btn, 0, wx.ALL, 10)



        self.panel.SetSizer(self.sizer)
        self.panel.Layout()

        self.browser.SetPage('<img src="'+os.getcwd()+'\\no.png" alt="no image" height="240" width="320">',"")
        self.playbtn.Disable()
        self.open_in_browser_btn.Disable()
        self.prevbtn.Disable()
        self.nextbtn.Disable()

    def OnRestart(self, evt):
        self.Destroy()
    def OnTimeToClose(self, evt):
        """Event handler for the button click."""
        self.Destroy()


    def OnSmartButton(self, evt):
        """Event handler for the button click."""
        if(self.check_random_search.GetValue()==1):
            self.MyYouTubeSearcherObj.GetRandomWord()
        self.MyYouTubeSearcherObj.index = 0
        self.RefreshPrevAndNextButtons()
        self.MyYouTubeSearcherObj.SearchPlease(self.search_text.GetValue())
        self.RefreshSongInfo()

        self.playbtn.Enable()
        self.open_in_browser_btn.Enable()
        self.panel.Layout()
    def StopTimer(self):
        self.remaining_time_in_seconds_for_timer_data = -1000
        for i in range(5):
            time.sleep(0.4)

    def OnLetSPlayMusic(self, evt):
        self.StopTimer()
        self.MyYouTubeSearcherObj.DeleteAllMp3()
        self.remaining_time_in_seconds_for_timer_data = int(self.MyYouTubeSearcherObj.GetDuration())
        self.t1 = threading.Thread(target=self.SmartBtnThread)
        self.t1.daemon = True
        self.t1.start()
    def RefreshPrevAndNextButtons(self):
        #print(str(self.MyYouTubeSearcherObj.index)+" "+str(self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()))
        if(self.MyYouTubeSearcherObj.index==0):
            self.prevbtn.Disable()
        else:
            self.prevbtn.Enable()
        if(self.MyYouTubeSearcherObj.index==self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()):
            self.nextbtn.Disable()
        else:
            self.nextbtn.Enable()
    def PrevSong(self, evt):
        self.MyYouTubeSearcherObj.index-=1
        self.RefreshSongInfo()
        self.RefreshPrevAndNextButtons()
    def NextSong(self, evt):
        self.MyYouTubeSearcherObj.index+=1
        self.RefreshSongInfo()
        self.RefreshPrevAndNextButtons()
    def RefreshSongInfo(self):
        #print(self.MyYouTubeSearcherObj.data_info["items"][self.MyYouTubeSearcherObj.index]["id"]["videoId"])
        self.MyYouTubeSearcherObj.SaveThumbByIndex(self.MyYouTubeSearcherObj.index)
        self.MyYouTubeSearcherObj.LoadStatisticsAndInformationByIndex(self.MyYouTubeSearcherObj.index)
        self.MyYouTubeSearcherObj.LoadContentDetailsByIndex(self.MyYouTubeSearcherObj.index)
        self.browser.SetPage('<img src="'+os.getcwd()+'\\file.jpg" alt="'+self.MyYouTubeSearcherObj.GetTitle().encode(encoding='UTF-8',errors='strict')+'" height="240" width="320">',"")
        self.text.SetLabel(self.MyYouTubeSearcherObj.GetTitle())
        self.duration_info.SetLabel("duration in seconds = "+self.MyYouTubeSearcherObj.GetDuration())
        self.panel.Layout()
    def RunTimer(self):
        while(self.remaining_time_in_seconds_for_timer_data>0):
            time.sleep(1)
            self.remaining_time_in_seconds_for_timer_data-=1
            self.remaining_time_seconds.SetLabel(str(self.remaining_time_in_seconds_for_timer_data)+" seconds remaining")
        self.playbtn.Enable()

        self.remaining_time_seconds.SetLabel("")
    def SmartBtnThread(self):
        self.OnReadButton("")

        self.MyYouTubeSearcherObj.PlayMp3InDir("")
        self.smartbtn.Enable()
    def OnReadButton(self, evt):
        """Event handler for the button click."""
        self.smartbtn.Disable()
        self.playbtn.Disable()
        self.MyYouTubeSearcherObj.DownloadMp3ByIndex(self.MyYouTubeSearcherObj.index)
        self.smartbtn.Enable()
        self.playbtn.Enable()
    def OnOpenInBrowser(self,event):
        #self.StopTimer()
        #self.MyYouTubeSearcherObj.StopMusic()
        url = 'https://www.youtube.com/watch?v='+self.MyYouTubeSearcherObj.data_info["items"][self.MyYouTubeSearcherObj.index]["id"]["videoId"]
        webbrowser.open_new(url)
        self.MyYouTubeSearcherObj.AppendToLogFile('https://www.youtube.com/watch?v='+self.MyYouTubeSearcherObj.data_info["items"][self.MyYouTubeSearcherObj.index]["id"]["videoId"])
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "YouTube Music - David Georiev - v1.10")
        self.SetTopWindow(frame)

        frame.Show(True)
        return True

if __name__ == "__main__":
    MyApp(redirect=False).MainLoop()

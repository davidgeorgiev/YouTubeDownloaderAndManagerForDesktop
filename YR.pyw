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
import os.path
GlobalSmartThreadRuning = 0


api_key = #ENTER YOUR API KEY HERE

class MyYouTubeSearcher():
    def __init__(self,parent):
        self.index = 0
        self.parent = parent
        self.data_info = ""
        self.full_data_info = ""
        self.content_details = ""
        self.ext = 'mp3'
    def GetWatchUrl(self):
        return 'https://www.youtube.com/watch?v='+self.data_info["items"][self.index]["id"]["videoId"]
    def GetSavingFileName(self):
        return self.GetTitle()[:30].replace(" ","_")+'_'+str(self.data_info["items"][self.index]["id"]["videoId"])+'.'+self.ext
    def SetExt(self,param):
        self.ext = param
    def GetNumberOfFoundVideos(self):
        return len(self.data_info)-2
    def SearchPlease(self,query):
        query = query.encode(encoding='UTF-8',errors='strict')
        self.parent.statusbar.SetStatusText('Searching for "'+query.decode(encoding='UTF-8',errors='strict')+'"')
        query = query.replace(' ', '+')
        self.data_info = list()
        self.found_ids = list()
        splitted_content = list()
        my_url = "https://www.googleapis.com/youtube/v3/search?part=id&q="+query+"&type=video&key="+api_key
        content = urllib2.urlopen(my_url).read()
        self.data_info = json.loads(content)
        self.parent.statusbar.SetStatusText('Done')
    def LoadStatisticsAndInformation(self):
        self.full_data_info = list()
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.data_info["items"][self.index]["id"]["videoId"]+"&key="+api_key+"&fields=items(id,snippet(channelId,title,categoryId),statistics)&part=snippet,statistics"
        content = urllib2.urlopen(my_url).read()
        self.full_data_info = json.loads(content)
    def LoadContentDetails(self):
        self.content_details = list()
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.data_info["items"][self.index]["id"]["videoId"]+"&part=contentDetails&key="+api_key
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
        return str(re.sub('[^A-Za-z0-9]+', ' ', self.full_data_info["items"][0]["snippet"]["title"]))
    def SaveThumb(self):
        self.parent.statusbar.SetStatusText('Fetching image...')
        thumb_url = "https://img.youtube.com/vi/"+self.data_info["items"][self.index]["id"]["videoId"]+"/0.jpg"
        testfile = urllib.URLopener()
        testfile.retrieve(thumb_url, "file.jpg")
        self.parent.statusbar.SetStatusText('Done')
    def DownloadFile(self):
        self.parent.statusbar.SetStatusText('Downloading: '+self.GetSavingFileName()[:15]+'...'+self.GetSavingFileName()[20:])
        hight_quality_parameters = ''
        format_parameters = ''

        if self.parent.IfVideo('just check') == 0:
            if self.parent.IfHightQuality() == 1:
                hight_quality_parameters+='-f webm --audio-quality 0'
            format_parameters = '--extract-audio --audio-format mp3'
        else:
            if self.parent.IfHightQuality() == 1:
                hight_quality_parameters = '-f best'
            else:
                hight_quality_parameters = '-f "best[height<500]"'
            format_parameters = "--merge-output-format mp4"
        os.system('del '+'"downloads\\'+self.GetSavingFileName()+'"')
        command = 'youtubedl\\youtubedl.exe "'+self.GetWatchUrl()+'" '+hight_quality_parameters+' '+format_parameters+' -o "./downloads/temp.'+'%'+'(ext)s"'
        self.AppendToLogFile(self.GetWatchUrl())
        os.system(command)
        self.parent.statusbar.SetStatusText('Done')
    def AppendToLogFile(self,log):
        with open("all_played_videos.txt", "a") as myfile:
            myfile.write(log+'\n')
    def LetsHearTheSong(self):
        self.t_timer = threading.Thread(target=self.parent.RunTimer)
        self.t_timer.daemon = True
        self.t_timer.start()

        os.startfile('downloads\\'+self.GetSavingFileName(), 'open')
    def PlayMp3InDir(self,event):
        self.parent.statusbar.SetStatusText('Playing music...')
        if(self.RenameMp3File()==1):
            self.LetsHearTheSong()
        self.parent.statusbar.SetStatusText('Done')
    def CleanDirectoryFromDumpFiles(self):
        self.parent.statusbar.SetStatusText('Cleaning download dir dump files...')
        test=os.listdir(os.getcwd()+"\\downloads")
        print test
        for item in test:
            if item.endswith(".webm") or item.endswith(".part") or item.endswith("temp.mp3") or item.endswith("temp.mp4"):
                os.remove(os.getcwd()+"\\downloads\\"+item)
        self.parent.statusbar.SetStatusText('Done')
    def DeleteAllMp3(self):
        self.parent.statusbar.SetStatusText('Deleting all downloads...')
        self.StopMusic()
        time.sleep(2)
        os.system('del /Q "'+os.getcwd()+'\\downloads\\*"')
        self.parent.statusbar.SetStatusText('Done')
    def ShowMessageCantBeDownload(self):
        dlg = wx.MessageDialog(self.parent.panel,"The format you want is unavailable! \nPlease change the quality or format and try again.", "Download warning!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()
    def RenameMp3File(self):
        self.StopMusic()
        time.sleep(2)
        file_to_check_and_rename = os.path.join(os.getcwd(), "downloads\\temp."+self.ext)
        if(os.path.isfile(file_to_check_and_rename)):
            os.system('rename "'+file_to_check_and_rename+'" "'+self.GetSavingFileName()+'"')
            return 1
        else:
            self.ShowMessageCantBeDownload()
            return 0
    def StopMusic(self):
        os.startfile("no sound\\no.mp3", 'open')
        os.startfile("no sound\\no.mp4", 'open')
        time.sleep(1)
    def GetRandomWord(self):
        url = "http://setgetgo.com/randomword/get.php"
        content = urllib2.urlopen(url).read()
        self.parent.search_text.SetValue(content+" music")
class MyFrame(wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, title):
        self.IfVideoTrigger = 0
        self.remaining_time_in_seconds_for_timer_data = 0
        self.MyYouTubeSearcherObj = MyYouTubeSearcher(self)
        self.now_timer_is_running = 0

        wx.Frame.__init__(self, parent, -1, title, pos=(150, 150), size=(725, 522),style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
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

        # statusbar initialization
        self.statusbar = self.CreateStatusBar(2)

        # Now create the Panel to put the other controls on.
        self.panel = wx.Panel(self)

        # and a few controls
        self.check_random_search = wx.CheckBox(self.panel, label = 'random search',pos = (10,10))
        self.check_hight_quality = wx.CheckBox(self.panel, label = 'hight quality',pos = (10,10))
        self.check_mp4_or_mp3 = wx.Button(self.panel, -1, self.MyYouTubeSearcherObj.ext)
        self.text = wx.StaticText(self.panel, -1, "")
        self.duration_info = wx.StaticText(self.panel, -1, "")
        self.text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.text.SetSize(self.text.GetBestSize())
        self.search_text = wx.TextCtrl(self.panel)
        self.smartbtn = wx.Button(self.panel, -1, "Smart Button")
        self.playbtn = wx.Button(self.panel, -1, "Play Button")
        self.prevbtn = wx.Button(self.panel, -1, "Prev")
        self.nextbtn = wx.Button(self.panel, -1, "Next")
        self.browser = wx.html2.WebView.New(self.panel,size=(390, 275))
        self.open_in_browser_btn = wx.Button(self.panel, -1, "Open in browser")
        self.delete_downloads_btn = wx.Button(self.panel, -1, "Delete downloads")

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.IfVideo, self.check_mp4_or_mp3)
        self.Bind(wx.EVT_BUTTON, self.OnSmartButton, self.smartbtn)
        self.Bind(wx.EVT_BUTTON, self.OnOpenInBrowser, self.open_in_browser_btn)
        self.Bind(wx.EVT_BUTTON, self.OnDeleteDownloads, self.delete_downloads_btn)
        self.Bind(wx.EVT_BUTTON, self.OnLetSPlayMusic, self.playbtn)
        self.Bind(wx.EVT_BUTTON, self.PrevSong, self.prevbtn)
        self.Bind(wx.EVT_BUTTON, self.NextSong, self.nextbtn)

        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer4 = wx.BoxSizer(wx.HORIZONTAL)

        # Adding things to sizers
        self.sizer1.Add(self.check_random_search,0,wx.ALL,10)
        self.sizer1.Add(self.check_hight_quality,0,wx.ALL,10)
        self.sizer1.Add(self.check_mp4_or_mp3,0,wx.ALL,10)
        self.sizer2.Add(self.smartbtn, 0, wx.ALL, 10)
        self.sizer2.Add(self.playbtn, 0, wx.ALL, 10)
        self.sizer2.Add(self.search_text,flag=wx.ALIGN_CENTER)
        self.sizer3.Add(self.prevbtn, 0, wx.ALL, 10)
        self.sizer3.Add(self.nextbtn, 0, wx.ALL, 10)
        self.left_sizer.Add(self.sizer1)
        self.left_sizer.Add(self.sizer2)
        self.right_sizer.Add(self.text, 0, wx.ALL, 10)
        self.right_sizer.Add(self.duration_info, 0, wx.ALL, 10)
        self.right_sizer.Add(self.browser, proportion=0, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.right_sizer.Add(self.sizer3)
        self.sizer4.Add(self.open_in_browser_btn, 0, wx.ALL, 10)
        self.sizer4.Add(self.delete_downloads_btn, 0, wx.ALL, 10)
        self.right_sizer.Add(self.sizer4)
        self.main_sizer.Add(self.left_sizer)
        self.main_sizer.Add(self.right_sizer)

        # set main sizer to panel
        self.panel.SetSizer(self.main_sizer)
        self.panel.Layout()

        # some start GUI configurations
        self.browser.SetPage('<img src="'+os.getcwd()+'\\no.png" alt="no image" height="240" width="320">',"")
        self.playbtn.Disable()
        self.open_in_browser_btn.Disable()
        self.prevbtn.Disable()
        self.nextbtn.Disable()
        self.check_hight_quality.SetValue(1)
    def OnDeleteDownloads(self,evt):
        dlg = wx.MessageDialog(None, 'All download files will be deleted?', 'Delete?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION )
        result = dlg.ShowModal()
        if result == wx.ID_NO:
            return
        self.MyYouTubeSearcherObj.DeleteAllMp3()
    def IfVideo(self,evt):
        if(evt!='just check'):
            self.IfVideoTrigger = not self.IfVideoTrigger
        if(self.IfVideoTrigger==1):
            self.MyYouTubeSearcherObj.SetExt("mp4")
            self.check_mp4_or_mp3.SetLabel(self.MyYouTubeSearcherObj.ext)
            return 1
        else:
            self.MyYouTubeSearcherObj.SetExt("mp3")
            self.check_mp4_or_mp3.SetLabel(self.MyYouTubeSearcherObj.ext)
            return 0
    def IfHightQuality(self):
        return self.check_hight_quality.GetValue()
    def OnTimeToClose(self, evt):
        self.Destroy()

    def OnSmartButton(self, evt):
        self.text.SetLabel("Searching...")
        self.duration_info.SetLabel("duration in seconds = unavailable")
        self.browser.SetPage('<img src="'+os.getcwd()+'\\no.png" alt="no image" height="240" width="320">',"")
        if(self.check_random_search.GetValue()==1):
            self.MyYouTubeSearcherObj.GetRandomWord()
        self.MyYouTubeSearcherObj.index = 0
        self.RefreshPrevAndNextButtons()
        self.MyYouTubeSearcherObj.SearchPlease(self.search_text.GetValue())
        if self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()==3:
            self.text.SetLabel("No Results!")
            self.duration_info.SetLabel("duration in seconds = unavailable")
            self.browser.SetPage('<img src="'+os.getcwd()+'\\no.png" alt="no image" height="240" width="320">',"")
            self.statusbar.SetStatusText('Nothing Found...')
            return None
        self.RefreshSongInfo()

        self.playbtn.Enable()
        self.open_in_browser_btn.Enable()
    def StopTimer(self):
        self.now_timer_is_running = 0
    def OnLetSPlayMusic(self, evt):
        self.MyYouTubeSearcherObj.CleanDirectoryFromDumpFiles()
        self.StopTimer()
        self.MyYouTubeSearcherObj.StopMusic()
        self.remaining_time_in_seconds_for_timer_data = int(self.MyYouTubeSearcherObj.GetDuration())
        t1 = threading.Thread(target=self.SmartBtnThread)
        t1.daemon = True
        t1.start()
    def RefreshPrevAndNextButtons(self):
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
        self.MyYouTubeSearcherObj.SaveThumb()
        self.MyYouTubeSearcherObj.LoadStatisticsAndInformation()
        self.MyYouTubeSearcherObj.LoadContentDetails()
        self.browser.SetPage('<img src="'+os.getcwd()+'\\file.jpg" alt="'+self.MyYouTubeSearcherObj.GetTitle()+'" height="240" width="320">',"")
        self.text.SetLabel(self.MyYouTubeSearcherObj.GetTitle())
        self.duration_info.SetLabel("duration in seconds = "+self.MyYouTubeSearcherObj.GetDuration())
    def RunTimer(self):
        title = self.MyYouTubeSearcherObj.GetTitle()
        dots = ""
        if(len(title)>30):
            dots = "..."
        self.now_timer_is_running = 1
        remaining_time_in_seconds_for_timer_data = self.remaining_time_in_seconds_for_timer_data
        while(remaining_time_in_seconds_for_timer_data>0 and self.now_timer_is_running):
            time.sleep(1)
            remaining_time_in_seconds_for_timer_data-=1
            self.statusbar.SetStatusText("Playing: "+title[:30]+dots+" ["+str(remaining_time_in_seconds_for_timer_data)+" seconds remaining]", 1)
        self.statusbar.SetStatusText("", 1)
    def SmartBtnThread(self):
        self.OnReadButton("")
        self.MyYouTubeSearcherObj.PlayMp3InDir("")
    def OnReadButton(self, evt):
        self.playbtn.Disable()
        self.check_mp4_or_mp3.Disable()
        self.check_hight_quality.Disable()
        self.delete_downloads_btn.Disable()
        self.MyYouTubeSearcherObj.DownloadFile()
        self.playbtn.Enable()
        self.check_mp4_or_mp3.Enable()
        self.check_hight_quality.Enable()
        self.delete_downloads_btn.Enable()
    def OnOpenInBrowser(self,event):
        url = self.MyYouTubeSearcherObj.GetWatchUrl()
        webbrowser.open_new(url)
        self.MyYouTubeSearcherObj.AppendToLogFile(url)
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "YouTube Music - David Georiev - v1.50")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True

if __name__ == "__main__":
    MyApp(redirect=False).MainLoop()

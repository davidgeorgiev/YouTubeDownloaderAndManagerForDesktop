import yr_constants
import time
import wx
import threading

class HistoryStuff():
    def __init__(self,parent):
        self.parent = parent
        self.history_list = list()
        self.in_history_mode = 0
        self.index = 0
        self.if_all_prepearings_done = 0
        self.syncing_now = 0
    def CleanAllHistory(self):
        self.history_list = list()
        self.SetIndex(1)
        dlg = wx.MessageDialog(None, 'All history will be cleaned.', 'Delete?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION )
        result = dlg.ShowModal()
        if result == wx.ID_NO:
            return 0
        my_file = open(yr_constants.FILENAME_HISTORY,"w")
        my_file.close()
        return 1
    def AllPrepearingsDone(self):
        return self.if_all_prepearings_done
    def SetAllPrepearingsDone(self):
        self.if_all_prepearings_done = 1
    def UnsetAllPrepearingsDone(self):
        self.if_all_prepearings_done = 0
    def RemoveDuplicates(self):
        reversed_list = self.history_list
        reversed_list.reverse()
        unique_list = list()
        for i in reversed_list:
            if i not in unique_list:
                unique_list.append(i)
        unique_list.reverse()
        self.history_list = unique_list
        self.SaveListToFile(self.history_list)
    def SaveListToFile(self, arg_list):
        myfile = open(yr_constants.FILENAME_HISTORY, "w")
        for videoId in arg_list:
            myfile.write("https://www.youtube.com/watch?v="+videoId+"\n")
        myfile.close()
    def DeleteCurrentItem(self):
        history_list = self.ReadHistoryFromFile()
        history_list.remove(self.history_list[self.index])
        del self.history_list[self.index]
        self.DecrementIndex()
        self.SaveListToFile(history_list)
    def GetCurrentVideoId(self):
        return self.history_list[self.GetIndex()]
    def EnableDisableHistoryMode(self,val):
        self.in_history_mode = val
        if(val == 0):
            self.history_list = list()
            self.UnsetAllPrepearingsDone()
            self.SetIndex(0)
            self.parent.toolbar.EnableTool(self.parent.APP_SYNC_HISTORY_PLAYLIST, False)
        else:
            self.parent.MyYouTubeSearcherObj.CleanDataInfo()
            self.parent.MyYouTubeSearcherObj.RefreshNumberOfFoundVideos()
            self.parent.prev_page_btn.Disable()
            self.parent.next_page_btn.Disable()
            self.RemoveDuplicates()
            self.index = self.GetSizeOfHistory()-1
            if(self.parent.CheckIfSomeFilterSet()):
                self.parent.RefreshSongInfo()
                self.parent.RefreshPrevAndNextButtons()
                self.history_list = self.parent.MyYouTubeSearcherObj.FilterResults(self.history_list)
            self.parent.current_main_title = "Your History"
            self.index = self.GetSizeOfHistory()-1
            self.parent.RefreshSongInfo()
            self.parent.toolbar.EnableTool(self.parent.APP_SYNC_HISTORY_PLAYLIST, True)
    def WaitSyncToCompleteAndEnableButtons(self):
        while(1):
            time.sleep(0.5)
            if(not self.syncing_now):
                break
        self.parent.smartbtn.Enable()
        self.parent.toolbar.EnableTool(self.parent.APP_CLARIFAI_SEARCH,True)
        self.parent.toolbar.EnableTool(self.parent.APP_HISTORY,True)
        self.parent.toolbar.EnableTool(self.parent.APP_SYNC_HISTORY_PLAYLIST,True)
        self.parent.ShowMessageHistorySynced()
    def SyncHistoryPlaylist(self,evt):
        self.parent.smartbtn.Disable()
        self.parent.toolbar.EnableTool(self.parent.APP_CLARIFAI_SEARCH,False)
        self.parent.toolbar.EnableTool(self.parent.APP_HISTORY,False)
        self.parent.toolbar.EnableTool(self.parent.APP_SYNC_HISTORY_PLAYLIST,False)
        try:
            os.unlink(self.parent.MyOAuthManagerObj.history_playlist_id_filename)
        except:
            pass
        self.parent.MyOAuthManagerObj.CreateHistoryPlaylistIfNotCreated()
        self.syncing_now = 1
        sync_thread = threading.Thread(target=self.AddAllHistoryToHistoryPlaylist)
        sync_thread.start()
        wait_to_enable_buttons_thread = threading.Thread(target=self.WaitSyncToCompleteAndEnableButtons)
        wait_to_enable_buttons_thread.start()
    def AddAllHistoryToHistoryPlaylist(self):
        size = float(self.GetSizeOfHistory())
        index = float(0)
        percent = float(0)
        for videoId in self.history_list:
            index += 1
            if(size/100)>0:
                percent = index/(size/100)
            self.parent.statusbar.SetStatusText("["+str(int(percent))+"%"+"] Syncing video with id: "+videoId)
            self.parent.MyOAuthManagerObj.add_video_to_playlist(videoId,self.parent.MyOAuthManagerObj.GetMyHistoryPlaylistId())
        self.parent.statusbar.SetStatusText("")
        self.syncing_now = 0
    def GetIndex(self):
        return self.index
    def IncrementIndex(self):
        if(self.index+1<self.GetSizeOfHistory()):
            self.index+=1
            return 0
        else:
            return 1
    def DecrementIndex(self):
        if(self.index-1>=0):
            self.index-=1
    def SetIndex(self,new):
        if(new-1>=0)and(new-1<self.GetSizeOfHistory()):
            self.index = new-1
    def CheckIfInHistoryMode(self):
        return self.in_history_mode
    def AppendToHistoryFile(self,log):
        with open(yr_constants.FILENAME_HISTORY, "a") as myfile:
            myfile.write(log+'\n')
    def ReadHistoryFromFile(self):
        self.parent.statusbar.SetStatusText("Reading history from file...",1)
        content = list()
        with open(yr_constants.FILENAME_HISTORY) as f:
            content = f.readlines()
        i = 0
        for item in content:
            content[i] = item.replace("https://www.youtube.com/watch?v=","").replace("\n","")
            i+=1
        #content.reverse()
        self.parent.statusbar.SetStatusText("",1)
        return content
    def GetSizeOfHistory(self):
        return len(self.history_list)

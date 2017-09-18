import wx
import wx.lib.scrolledpanel
import yr_constants
import image_tools

class ScrollingWindowVideos(wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, size, title):
        self.size = size
        self.number_in_grid = 4
        self.ImageToolsObj = image_tools.ImageTools(self)
        self.parent = parent
        self.parent.smartbtn.Disable()
        self.parent.toolbar.EnableTool(self.parent.APP_HISTORY,False)
        self.parent.toolbar.EnableTool(self.parent.APP_SCROLLING_WINDOW,False)
        self.index_of_last_loaded_video = 0
        wx.Frame.__init__(self, parent, -1, title, pos=(150, 150), size=self.size,style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)
        self.Center()
        self.statusbar = self.CreateStatusBar(2)
        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=self.size, pos=(0,0), style=wx.SIMPLE_BORDER)
        #self.panel.SetBackgroundColour('#FFFFFF')

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.videos_sizer = wx.BoxSizer(wx.VERTICAL)
        self.load_more_bnt_sizer = wx.BoxSizer(wx.VERTICAL)

        self.load_more_btn = wx.Button(self.panel, -1, "show more", size=(100, 25))
        self.Bind(wx.EVT_BUTTON, lambda event: self.LoadMoreNVideos(9), self.load_more_btn)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.__destroy)

        self.main_sizer.Add(self.videos_sizer)
        self.load_more_bnt_sizer.Add(self.load_more_btn, 0, wx.LEFT, (self.size[0]/2)-60)
        self.main_sizer.Add(self.load_more_bnt_sizer)

        self.panel.SetSizer(self.main_sizer)
        self.panel.Layout()
        self.LoadMoreNVideos(9)
    def LoadMoreNVideos(self,n):
        video_ids = list()
        if self.parent.HistoryStuffObj.CheckIfInHistoryMode():
            video_ids = self.parent.HistoryStuffObj.history_list
        else:
            video_ids_unformated = self.parent.MyYouTubeSearcherObj.data_info
            for the_id in video_ids_unformated["items"]:
                video_ids.append(the_id["id"]["videoId"])
        i = self.index_of_last_loaded_video
        while(i!=self.index_of_last_loaded_video+n):
            if(i==len(video_ids)):
                self.load_more_btn.Disable()
                break
            thumb_name = yr_constants.DIRNAME_SCROLLING_WINDOW_THUMBS_FOLDER+"\\"+str(i)
            self.parent.MyYouTubeSearcherObj.SaveThumbParam(video_ids[i],thumb_name+".jpg")
            self.ImageToolsObj.ResizeImage(thumb_name+".jpg",(self.size[0]/self.number_in_grid,self.size[1]/self.number_in_grid))
            video_sizer = wx.BoxSizer(wx.VERTICAL)
            if(i%3==0) or i == self.index_of_last_loaded_video:
                side_videos_sizer = wx.BoxSizer(wx.HORIZONTAL)
            BitMap = wx.StaticBitmap(self.panel, -1, wx.Bitmap(thumb_name+".png", wx.BITMAP_TYPE_ANY), size=(self.size[0]/self.number_in_grid, self.size[1]/self.number_in_grid))
            BitMap.Bind(wx.EVT_LEFT_DOWN, lambda event,index=i: self.SetAndClose(event,index))
            video_title = wx.StaticText(self.panel, -1, self.parent.MyYouTubeSearcherObj.GetTitleFromId(video_ids[i]), size=(170, 60))
            video_title.Bind(wx.EVT_LEFT_DOWN, lambda event,index=i: self.SetAndClose(event,index))
            video_sizer.Add(video_title, 0, wx.LEFT, 27)
            video_sizer.Add(BitMap, 0, wx.LEFT, 27)
            side_videos_sizer.Add(video_sizer)
            if(i%3==0):
                self.videos_sizer.Add(side_videos_sizer, 0, wx.TOP, 30)
            i+=1
            self.panel.Layout()
            self.panel.SetupScrolling(scrollToTop=False)
        self.index_of_last_loaded_video = i
        return
    def SetAndClose(self,event,index):
        self.parent.ChangeIndex(index+1)
        self.Destroy()
    def __destroy(self,evt):
        self.parent.smartbtn.Enable()
        self.parent.toolbar.EnableTool(self.parent.APP_HISTORY,True)
        self.parent.toolbar.EnableTool(self.parent.APP_SCROLLING_WINDOW,True)
        self.Destroy()

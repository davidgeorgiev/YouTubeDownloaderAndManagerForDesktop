import my_oauth_manager
import my_youtube_searcher
import history_stuff
import image_tools
import my_globals
import yr_constants
import win32clipboard
import os.path
import wx
import wx.html2
import webbrowser
import threading
import global_functions
import time
import scrolling_window_videos

class MyFrame(wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, title):
        self.MyOAuthManagerObj = my_oauth_manager.MyOAuthManager(self)
        self.MyYouTubeSearcherObj = my_youtube_searcher.MyYouTubeSearcher(self)
        self.HistoryStuffObj = history_stuff.HistoryStuff(self)
        self.MyImageToolsObj = image_tools.ImageTools(self)

        self.IfVideoTrigger = 0
        self.remaining_time_in_seconds_for_timer_data = 0

        self.now_timer_is_running = 0
        self.user_input_backup = ""
        self.related_thumbnail_updater_thread_is_running = 0
        self.related_thumbnail_updater_thread_is_stopped = 1
        self.related_thumbnail_id_updater_thread = 0
        self.related_thumbnails_current_indexes = [0]*6
        self.current_main_title = ""
        self.info_shown = 0
        self.size_without_info = (645,620)
        self.size_with_info = (930,620)
        self.url_link_is_in_clipboard = 0
        self.copy_checker_btn_thread_is_running = 0
        self.copy_checker_btn_thread_stopped = 1

        wx.Frame.__init__(self, parent, -1, title, pos=(150, 150), size=self.size_without_info,style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)

        self.Center()

        #CONSTANTS
        self.APP_EXIT = 1
        self.APP_HISTORY = 2
        self.APP_RECOMMEND = 3
        self.APP_OPEN_IN_BROWSER = 4
        self.APP_DELETE_DOWNLOADS = 5
        self.APP_SHOW_AND_HIDE_INFO = 6
        self.APP_PLAY_EMBED = 7
        self.APP_CLARIFAI_SEARCH = 8
        self.APP_OPEN_DOWNLOADS = 9
        self.APP_ADD_TO_HISTORY = 10
        self.APP_SYNC_HISTORY_PLAYLIST = 11
        self.APP_LOG_OUT_ACCOUNT = 12
        self.APP_CLEAN_ALL_HISTORY = 13
        self.APP_SCROLLING_WINDOW = 14
        # Create the menubar
        self.menuBar = wx.MenuBar()
        # and a menu
        self.fileMenu = wx.Menu()
        self.searchMenu = wx.Menu()
        self.optionsMenu = wx.Menu()
        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        switch_youtube_account_item = wx.MenuItem(self.fileMenu, self.APP_LOG_OUT_ACCOUNT, '&Log out')
        switch_youtube_account_item.SetBitmap(wx.Bitmap(yr_constants.FILENAME_SWITCH_ACCOUNT_ICON))
        self.fileMenu.AppendItem(switch_youtube_account_item)

        clean_all_history_item = wx.MenuItem(self.optionsMenu, self.APP_CLEAN_ALL_HISTORY, '&Clean all history')
        clean_all_history_item.SetBitmap(wx.Bitmap(yr_constants.FILENAME_CLEAN_ALL_HISTORY_ICON))
        self.optionsMenu.AppendItem(clean_all_history_item)

        self.random_search_menu_checkbox = self.searchMenu.Append(wx.ID_ANY, 'Random search', 'Random search', kind=wx.ITEM_CHECK)
        self.search_for_list_menu_checkbox = self.searchMenu.Append(wx.ID_ANY, 'Search for list', 'Search for list', kind=wx.ITEM_CHECK)
        self.searchMenu.Check(self.random_search_menu_checkbox.GetId(), False)
        self.searchMenu.Check(self.search_for_list_menu_checkbox.GetId(), False)

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.OnLogOutAccount, id=self.APP_LOG_OUT_ACCOUNT)
        self.Bind(wx.EVT_MENU, self.OnStartHistoryMode, id=self.APP_HISTORY)
        self.Bind(wx.EVT_MENU, self.OnRecommendButtonPressed, id=self.APP_RECOMMEND)
        self.Bind(wx.EVT_MENU, self.OnCleanHistory, id=self.APP_CLEAN_ALL_HISTORY)

        # and put the menu on the menubar
        self.menuBar.Append(self.fileMenu, "&File")
        self.menuBar.Append(self.searchMenu, "&Search options")
        self.menuBar.Append(self.optionsMenu, "&Options")
        self.SetMenuBar(self.menuBar)



        # TOOLBAR
        self.toolbar = self.CreateToolBar()
        delete_downloads_tool = self.toolbar.AddLabelTool(self.APP_DELETE_DOWNLOADS, 'Delete Downloads', wx.Bitmap(yr_constants.FILENAME_DELETE_DOWNLOADS_ICON))
        self.Bind(wx.EVT_TOOL, self.OnDeleteDownloads, delete_downloads_tool)
        open_in_browser_tool = self.toolbar.AddLabelTool(self.APP_OPEN_IN_BROWSER, 'Open In Browser', wx.Bitmap(yr_constants.FILENAME_OPEN_IN_BROWSER_ICON))
        self.Bind(wx.EVT_TOOL, self.OnOpenInBrowser, open_in_browser_tool)
        recommend_tool = self.toolbar.AddLabelTool(self.APP_RECOMMEND, "Recommend for you", wx.Bitmap(yr_constants.FILENAME_RECOMMEND_ICON))
        self.Bind(wx.EVT_TOOL, self.OnRecommendButtonPressed, recommend_tool)
        history_tool = self.toolbar.AddLabelTool(self.APP_HISTORY, 'History', wx.Bitmap(yr_constants.FILENAME_HISTORY_ICON))
        self.Bind(wx.EVT_TOOL, self.OnStartHistoryMode, history_tool)
        show_and_hide_info_tool = self.toolbar.AddLabelTool(self.APP_SHOW_AND_HIDE_INFO, 'Show And Hide Info Tool', wx.Bitmap(yr_constants.FILENAME_INFO_ICON))
        self.Bind(wx.EVT_TOOL, self.OnShowAndHideInfoTool, show_and_hide_info_tool)
        play_embed_tool = self.toolbar.AddLabelTool(self.APP_PLAY_EMBED, 'Play in IFrame', wx.Bitmap(yr_constants.FILENAME_PLAY_EMBED_ICON))
        self.Bind(wx.EVT_TOOL, self.OnPlayEmbed, play_embed_tool)
        clarifai_search_tool = self.toolbar.AddLabelTool(self.APP_CLARIFAI_SEARCH, 'Clarifai search', wx.Bitmap(yr_constants.FILENAME_CLARIFAI_SEARCH_ICON))
        self.Bind(wx.EVT_TOOL, self.OnSearchByThumbnailButton, clarifai_search_tool)
        open_downloads_tool = self.toolbar.AddLabelTool(self.APP_OPEN_DOWNLOADS, 'Open downloads', wx.Bitmap(yr_constants.FILENAME_DOWNLOADS_ICON))
        self.Bind(wx.EVT_TOOL, self.OnOpenDownloads, open_downloads_tool)
        add_to_history_tool = self.toolbar.AddLabelTool(self.APP_ADD_TO_HISTORY, 'Add to history', wx.Bitmap(yr_constants.FILENAME_ADD_TO_HISTORY_ICON))
        self.Bind(wx.EVT_TOOL, self.AddCurrentVideoToHistory, add_to_history_tool)
        sync_history_tool = self.toolbar.AddLabelTool(self.APP_SYNC_HISTORY_PLAYLIST, 'Sync history', wx.Bitmap(yr_constants.FILENAME_SYNC_HISTORY_ICON))
        self.Bind(wx.EVT_TOOL, self.HistoryStuffObj.SyncHistoryPlaylist, sync_history_tool)
        show_scrolling_window_videos = self.toolbar.AddLabelTool(self.APP_SCROLLING_WINDOW, 'Scrolling Window', wx.Bitmap(yr_constants.FILENAME_SCROLLING_WINDOW_ICON))
        self.Bind(wx.EVT_TOOL, self.OnShowScrollingVideoWindow, show_scrolling_window_videos)




        self.toolbar.Realize()
        self.toolbar.SetBackgroundColour("RGB(220,220,220)")
        self.toolbar.EnableTool(self.APP_SYNC_HISTORY_PLAYLIST, False)
        # statusbar initialization
        self.statusbar = self.CreateStatusBar(2)

        # Now create the Panel to put the other controls on.
        self.panel = wx.Panel(self)

        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        self.thumblails_sizer_l = wx.BoxSizer(wx.VERTICAL)
        self.thumblails_sizer_r = wx.BoxSizer(wx.VERTICAL)
        self.hq_mp3_or_mp4_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.search_box_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.full_info_sizer = wx.BoxSizer(wx.VERTICAL)
        self.full_info_sizer_subsizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        self.full_info_sizer_subsizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        self.full_info_sizer_subsizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        self.add_to_favorites_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # and a few controls
        self.check_show_only_HD = wx.CheckBox(self.panel, label = 'Only HD',pos = (10,10))
        self.filter_label_from = wx.StaticText(self.panel, -1, "from")
        self.filter_label_to = wx.StaticText(self.panel, -1, "to")
        self.filter_label_minutes = wx.StaticText(self.panel, -1, "mins    ")
        self.min_min_edit = wx.TextCtrl(self.panel,size=(20, -1))
        self.max_min_edit = wx.TextCtrl(self.panel,size=(20, -1))
        self.check_hight_quality = wx.CheckBox(self.panel, label = 'HQ',pos = (10,10))
        self.check_auto_play = wx.CheckBox(self.panel, label = 'auto play',pos = (10,10))
        self.check_mp4_or_mp3 = wx.Button(self.panel, -1, self.MyYouTubeSearcherObj.ext, size=(40, 25))
        self.main_title_static_text = wx.StaticText(self.panel, -1, "", size=(200, 20))
        self.main_title_static_text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.text = wx.StaticText(self.panel, -1, "", size=(200, 50))
        self.duration_info = wx.StaticText(self.panel, -1, "")
        self.text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.search_text = wx.TextCtrl(self.panel,size=(200, -1), style =  wx.TE_PROCESS_ENTER)
        self.smartbtn = wx.Button(self.panel, -1, "Search", size=(60, 25))
        self.playbtn = wx.Button(self.panel, -1, "Download selected video",size=(270, 25))
        self.prevbtn = wx.Button(self.panel, -1, "Prev video")
        self.nextbtn = wx.Button(self.panel, -1, "Next video")
        self.prev_page_btn = wx.Button(self.panel, -1, "Prev page")
        self.next_page_btn = wx.Button(self.panel, -1, "Next page")
        self.index_info_edit = wx.TextCtrl(self.panel,size=(30, -1),style =  wx.TE_PROCESS_ENTER)
        self.index_info = wx.StaticText(self.panel, -1, "")
        self.main_image_thumb = wx.StaticBitmap(self.panel, -1, wx.Bitmap(yr_constants.FILENAME_BIG_NO_THUMBNAIL, wx.BITMAP_TYPE_ANY), size=(320, 240))
        self.check_continuous_play = wx.CheckBox(self.panel, label = 'continuous',pos = (10,10))
        self.title_description_static_text = wx.StaticText(self.panel, -1, "  Description", size=(200, 20))
        self.title_description_static_text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.description_static_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE,size=(287, 342),pos=(5,5))
        self.channel_btn = wx.Button(self.panel, -1, "Open channel")
        self.likes_gauge = wx.Gauge(self.panel, range=100, size=(200, 30))
        self.like_static_image = wx.StaticBitmap(self.panel, -1, wx.Bitmap(yr_constants.FILENAME_LIKE_ICON, wx.BITMAP_TYPE_ANY), size=(30, 27))
        self.dislike_static_image = wx.StaticBitmap(self.panel, -1, wx.Bitmap(yr_constants.FILENAME_DISLIKE_ICON, wx.BITMAP_TYPE_ANY), size=(30, 27))
        self.copy_link_btn = wx.Button(self.panel, -1, "Copy link")
        self.subscribe_btn = wx.Button(self.panel, -1, "Subscribe")
        self.add_to_favorites_static_image = wx.StaticBitmap(self.panel, -1, wx.Bitmap(yr_constants.FILENAME_ADD_TO_FAVORITES_EMPTY_ICON, wx.BITMAP_TYPE_ANY), size=(50, 50))

        # GRID OF THUMBNAILS
        self.sBitMaps = list()
        i = 0
        while(i<=5):
            self.sBitMaps.append(wx.StaticBitmap(self.panel, -1, wx.Bitmap(yr_constants.FILENAME_SMALL_NO_THUMBNAIL, wx.BITMAP_TYPE_ANY), size=(120, 90)))
            self.sBitMaps[i].Bind(wx.EVT_LEFT_DOWN, lambda event,index=i: self.OnClickThumbnail(index))
            self.sBitMaps[i].Bind(wx.EVT_ENTER_WINDOW, lambda event,index=i: self.OnHoverThumbnail(index))
            self.sBitMaps[i].Bind(wx.EVT_LEAVE_WINDOW, self.OnExitThumbnail)
            i+=1


        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.IfVideo, self.check_mp4_or_mp3)
        self.Bind(wx.EVT_BUTTON, lambda event: self.OnSmartButton(""), self.smartbtn)
        self.Bind(wx.EVT_BUTTON, self.OnDownloadFile, self.playbtn)
        self.Bind(wx.EVT_BUTTON, self.PrevSong, self.prevbtn)
        self.Bind(wx.EVT_BUTTON, self.NextSong, self.nextbtn)
        self.Bind(wx.EVT_BUTTON, self.PrevPage, self.prev_page_btn)
        self.Bind(wx.EVT_BUTTON, self.NextPage, self.next_page_btn)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnChangeIndex, self.index_info_edit)
        self.Bind(wx.EVT_TEXT_ENTER, lambda event: self.OnSmartButton(""), self.search_text)
        self.main_image_thumb.Bind(wx.EVT_ENTER_WINDOW, self.OnHoverMainThumbnail)
        self.main_image_thumb.Bind(wx.EVT_LEAVE_WINDOW, self.OnExitMainThumbnail)
        self.main_image_thumb.Bind(wx.EVT_LEFT_DOWN, self.OnClickMainThumbnail)
        self.channel_btn.Bind(wx.EVT_BUTTON, self.OnOpenChannel)
        self.copy_link_btn.Bind(wx.EVT_BUTTON, self.OnCopyLink)
        self.likes_gauge.Bind(wx.EVT_ENTER_WINDOW, self.OnHoverGauge)
        self.likes_gauge.Bind(wx.EVT_LEAVE_WINDOW, self.OnExitLikeDislike)
        self.like_static_image.Bind(wx.EVT_LEFT_DOWN, self.LikeCurrentVideo)
        self.dislike_static_image.Bind(wx.EVT_LEFT_DOWN, self.DislikeCurrentVideo)
        self.like_static_image.Bind(wx.EVT_ENTER_WINDOW, self.OnHoverLikeCurrentVideoStaticImage)
        self.dislike_static_image.Bind(wx.EVT_ENTER_WINDOW, self.OnHoverDislikeCurrentVideoStaticImage)
        self.like_static_image.Bind(wx.EVT_LEAVE_WINDOW, self.OnExitLikeCurrentVideoStaticImage)
        self.dislike_static_image.Bind(wx.EVT_LEAVE_WINDOW, self.OnExitDislikeCurrentVideoStaticImage)
        self.subscribe_btn.Bind(wx.EVT_LEFT_DOWN, self.SubscribeCurrentChannel)
        self.add_to_favorites_static_image.Bind(wx.EVT_LEFT_DOWN, self.OnClickHeart)
        self.add_to_favorites_static_image.Bind(wx.EVT_ENTER_WINDOW, self.OnHoverHeart)
        self.add_to_favorites_static_image.Bind(wx.EVT_LEAVE_WINDOW, self.OnExitHeart)


        # GRID OF THUMBNAILS
        for i in range(3):
            self.thumblails_sizer_l.Add(self.sBitMaps[i], flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        for i in range(3):
            self.thumblails_sizer_r.Add(self.sBitMaps[3+i], flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)

        # Adding things to sizers
        self.full_info_sizer.Add(self.title_description_static_text, 0, wx.ALL, 10)
        self.full_info_sizer.Add(self.description_static_text, 0, wx.LEFT , 19)
        self.full_info_sizer_subsizer_1.Add(self.channel_btn, 0, wx.LEFT, 52)
        self.full_info_sizer_subsizer_1.Add(self.copy_link_btn, 0, wx.LEFT, 18)
        self.full_info_sizer.Add(self.full_info_sizer_subsizer_1, 0, wx.ALL, 10)
        self.full_info_sizer_subsizer_2.Add(self.like_static_image, 0, wx.LEFT, 32)
        self.full_info_sizer_subsizer_2.Add(self.likes_gauge, 0, wx.LEFT, 0)
        self.full_info_sizer_subsizer_2.Add(self.dislike_static_image, 0, wx.LEFT, 0)
        self.full_info_sizer_subsizer_3.Add(self.subscribe_btn, 0, wx.LEFT, 62)
        self.filter_sizer.Add(self.check_show_only_HD,flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.full_info_sizer.Add(self.full_info_sizer_subsizer_2, 0, wx.TOP, 0)
        self.full_info_sizer.Add(self.full_info_sizer_subsizer_3, 0, wx.TOP, 10)
        self.filter_sizer.Add(self.filter_label_from, 0, wx.ALL, 10)
        self.filter_sizer.Add(self.min_min_edit, 0, wx.ALL, 10)
        self.filter_sizer.Add(self.filter_label_to, 0, wx.ALL, 10)
        self.filter_sizer.Add(self.max_min_edit, 0, wx.ALL, 10)
        self.filter_sizer.Add(self.filter_label_minutes, 0, wx.ALL, 10)
        self.sizer2.Add(self.playbtn, 0, wx.ALL, 10)
        self.sizer3.Add(self.prevbtn, 0, wx.ALL, 10)
        self.sizer3.Add(self.nextbtn, 0, wx.ALL, 10)
        self.sizer3.Add(self.index_info_edit, 0, wx.ALL, 10)
        self.sizer3.Add(self.index_info, 0, wx.ALL, 10)
        self.sizer4.Add(self.prev_page_btn, 0, wx.LEFT, 10)
        self.add_to_favorites_sizer.Add(self.add_to_favorites_static_image, 0, wx.TOP, -30)
        self.sizer4.Add(self.add_to_favorites_sizer, 0, wx.LEFT, 42)
        self.sizer4.Add(self.next_page_btn, 0, wx.LEFT, 42)
        self.left_sizer.Add(self.sizer1, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.left_sizer.Add(self.filter_sizer, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.search_box_btn_sizer.Add(self.search_text,flag=wx.ALIGN_CENTER)
        self.search_box_btn_sizer.Add(self.smartbtn, 0, wx.ALL, 10)
        self.left_sizer.Add(self.search_box_btn_sizer, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.hq_mp3_or_mp4_sizer.Add(self.check_mp4_or_mp3,0,wx.ALL,10)
        self.hq_mp3_or_mp4_sizer.Add(self.check_hight_quality,flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.hq_mp3_or_mp4_sizer.Add(self.check_auto_play, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.hq_mp3_or_mp4_sizer.Add(self.check_continuous_play, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.left_sizer.Add(self.hq_mp3_or_mp4_sizer)
        self.left_sizer.Add(self.sizer2)
        self.left_sizer.Add(self.left_sizer1)
        self.left_sizer1.Add(self.thumblails_sizer_l, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.left_sizer1.Add(self.thumblails_sizer_r, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.right_sizer.Add(self.main_title_static_text, 0, wx.ALL, 10)
        self.right_sizer.Add(self.text, 0, wx.ALL, 10)
        self.right_sizer.Add(self.duration_info, 0, wx.ALL, 10)
        self.right_sizer.Add(self.main_image_thumb, flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.right_sizer.Add(self.sizer3)
        self.right_sizer.Add(self.sizer4, 0, wx.TOP, 28)
        self.right_sizer.Add(self.sizer5)
        self.main_sizer.Add(self.left_sizer)
        self.main_sizer.Add(self.right_sizer)
        self.main_sizer.Add(self.full_info_sizer)
        # set main sizer to panel
        self.panel.SetSizer(self.main_sizer)
        self.panel.Layout()
        # some start GUI configurations

        self.playbtn.Disable()
        self.toolbar.EnableTool(self.APP_PLAY_EMBED,False)
        self.toolbar.EnableTool(self.APP_OPEN_IN_BROWSER,False)
        self.toolbar.EnableTool(self.APP_CLARIFAI_SEARCH,False)
        self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,False)
        self.prevbtn.Disable()
        self.nextbtn.Disable()
        self.check_hight_quality.SetValue(1)
        self.index_info_edit.Disable()
        self.prev_page_btn.Disable()
        self.next_page_btn.Disable()
        self.DrawInterfaceLines()
    def OnShowScrollingVideoWindow(self,evt):
        MyScrollingWindow = scrolling_window_videos.ScrollingWindowVideos(self,self.size_without_info,"Videos")
        MyScrollingWindow.Show(True)
    def OnCleanHistory(self,evt):
        if self.HistoryStuffObj.CleanAllHistory():
            self.NothingFoundRefresh()
            self.main_title_static_text.SetLabel("Nothing in History")
            self.ShowMessageHistoryCleaned()
        return
    def ShowMessageHistoryCleaned(self):
        dlg = wx.MessageDialog(self.panel,'History cleaned!', "Cleaned", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()
    def OnHoverLikeCurrentVideoStaticImage(self,evt):
        if(self.VideoInformationExists()):
            self.like_static_image.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        return
    def OnHoverDislikeCurrentVideoStaticImage(self,evt):
        if(self.VideoInformationExists()):
            self.dislike_static_image.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        return
    def OnExitLikeCurrentVideoStaticImage(self,evt):
        self.like_static_image.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        return
    def OnExitDislikeCurrentVideoStaticImage(self,evt):
        self.dislike_static_image.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        return
    def VideoInformationExists(self):
        if self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()!=0 or my_globals.GlobalVideoIdForRelated!="" or self.HistoryStuffObj.GetSizeOfHistory()!=0:
            if(len(self.MyYouTubeSearcherObj.full_data_info["items"])>0):
                return 1
        return 0
    def OnHoverHeart(self,evt):
        if(self.VideoInformationExists()):
            self.add_to_favorites_static_image.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
            self.add_to_favorites_static_image.SetBitmap(wx.Bitmap(yr_constants.FILENAME_ADD_TO_FAVORITES_ICON,wx.BITMAP_TYPE_ANY))
        return
    def OnExitHeart(self,evt):
        self.add_to_favorites_static_image.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        self.add_to_favorites_static_image.SetBitmap(wx.Bitmap(yr_constants.FILENAME_ADD_TO_FAVORITES_EMPTY_ICON,wx.BITMAP_TYPE_ANY))
        return
    def OnClickHeart(self,evt):
        if(self.VideoInformationExists()):
            added = self.MyOAuthManagerObj.add_video_to_playlist(self.MyYouTubeSearcherObj.GetCurrentVideoId(),self.MyOAuthManagerObj.get_favorites_playlist_id())
            if(added):
                self.ShowMessageAddedToFavorites()
        return
    def ShowMessageAddedToFavorites(self):
        dlg = wx.MessageDialog(self.panel,'Video added to your "favorites playlist".', "Added to Favorites", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()
    def SubscribeCurrentChannel(self,evt):
        if(self.VideoInformationExists()):
                channel_name = self.MyOAuthManagerObj.add_subscription(self.MyYouTubeSearcherObj.full_data_info["items"][0]["snippet"]["channelId"])
                self.statusbar.SetStatusText("Subscribed to "+channel_name)
                return
        self.statusbar.SetStatusText("Couldn't make a subscription.")
    def OnLogOutAccount(self,evt):
        try:
            os.unlink(yr_constants.FILENAME_AUTHENTICATE_INFO_JSON)
            self.Destroy()
        except:
            pass
    def LikeCurrentVideo(self,evt):
        self.MyOAuthManagerObj.LikeAVideo(self.MyYouTubeSearcherObj.GetCurrentVideoId(),"like")
        self.statusbar.SetStatusText("You like this video")
        return
    def DislikeCurrentVideo(self,evt):
        self.MyOAuthManagerObj.LikeAVideo(self.MyYouTubeSearcherObj.GetCurrentVideoId(),"dislike")
        self.statusbar.SetStatusText("You dislike this video")
        return
    def RefreshPrevAndNextPageButtons(self):
        if(self.MyYouTubeSearcherObj.pages_tokens[0]==""):
            self.prev_page_btn.Disable()
        else:
            self.prev_page_btn.Enable()
        if(self.MyYouTubeSearcherObj.pages_tokens[1]==""):
            self.next_page_btn.Disable()
        else:
            self.next_page_btn.Enable()
    def PrevPage(self,evt):
        self.OnSmartButton(self.MyYouTubeSearcherObj.pages_tokens[0])
        self.RefreshPrevAndNextPageButtons()
        return
    def NextPage(self,evt):
        self.OnSmartButton(self.MyYouTubeSearcherObj.pages_tokens[1])
        self.RefreshPrevAndNextPageButtons()
        return
    def OnPlayEmbed(self,evt):
        webbrowser.open(yr_constants.FILENAME_IFRAME_HTML)
    def OnHoverGauge(self,evt):
        info_for_showing = ""
        if(self.VideoInformationExists()):
            likes = int(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["likeCount"])
            likes = global_functions.intWithCommas(likes)
            info_for_showing+="likes: "+likes+" "
            dislikes = int(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["dislikeCount"])
            dislikes = global_functions.intWithCommas(dislikes)
            info_for_showing+="dislikes: "+dislikes+" "
            self.statusbar.SetStatusText(info_for_showing)
    def OnExitLikeDislike(self,evt):
        self.statusbar.SetStatusText("")
    def DrawInterfaceLines(self):
        self.ln = wx.StaticLine(self.panel, -1,pos=(0,0), style=wx.LI_VERTICAL)
        self.ln.SetSize((1000,3))
        self.ln = wx.StaticLine(self.panel, -1,pos=(290,0), style=wx.LI_HORIZONTAL)
        self.ln.SetSize((2,1000))
        self.ln = wx.StaticLine(self.panel, -1,pos=(0,195), style=wx.LI_HORIZONTAL)
        self.ln.SetSize((290,400))
        self.ln = wx.StaticLine(self.panel, -1,pos=(650,39), style=wx.LI_HORIZONTAL)
        self.ln.SetSize((290,500))
        i = 0
        while(i<900):
            i+=10
            self.ln = wx.StaticLine(self.panel, -1,pos=(280+i,37), style=wx.LI_VERTICAL)
            self.ln.SetSize((5,2))
        i = 0
    def GetRealVideoIdAuto(self):
        if(my_globals.GlobalVideoIdForRelated==""):
            return self.MyYouTubeSearcherObj.GetCurrentVideoId()
        else:
            return my_globals.GlobalVideoIdForRelated
    def OnCopyLink(self,evt):
        videoId = self.GetRealVideoIdAuto()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText("https://www.youtube.com/watch?v="+videoId)
        win32clipboard.CloseClipboard()
        return
    def CopyButtonThread(self):
        videoId = self.GetRealVideoIdAuto()
        self.SetOffCopyCheckThread()
        while(not self.copy_checker_btn_thread_stopped):
            time.sleep(0.1)
        self.SetOnCopyCheckThread()
        self.copy_checker_btn_thread_stopped = 0
        while(self.CheckCopyThreadIsRunning()):
            time.sleep(1)
            try:
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                if(data == "https://www.youtube.com/watch?v="+videoId):
                    self.url_link_is_in_clipboard = 1
                    self.copy_link_btn.Disable()
                    self.copy_link_btn.SetLabel("In Clipboard")
                else:
                    self.url_link_is_in_clipboard = 0
                    self.copy_link_btn.Enable()
                    self.copy_link_btn.SetLabel("Copy Link")
            except:
                pass
        self.copy_checker_btn_thread_stopped = 1
    def SetOnCopyCheckThread(self):
        self.copy_checker_btn_thread_is_running = 1
    def SetOffCopyCheckThread(self):
        self.copy_checker_btn_thread_is_running = 0
    def CheckCopyThreadIsRunning(self):
        return self.copy_checker_btn_thread_is_running
    def OnEraseBackground(self, evt):
        return
    def RefreshAdditionalInformation(self):
        if(self.VideoInformationExists()):
            self.description_static_text.SetValue(self.MyYouTubeSearcherObj.full_data_info["items"][0]["snippet"]["description"])
            likes = float(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["likeCount"])
            dislikes = float(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["dislikeCount"])
            if(((likes+dislikes)/100)!=0):
                self.likes_gauge.SetValue(likes/((likes+dislikes)/100))
            else:
                self.likes_gauge.SetValue(0)
            self.subscribe_btn.Enable()
            self.channel_btn.Enable()
            copy_button_thread = threading.Thread(target=self.CopyButtonThread)
            copy_button_thread.start()
        else:
            self.subscribe_btn.Disable()
            self.channel_btn.Disable()
            self.copy_link_btn.Disable()
    def OnOpenChannel(self,evt):
        if(self.VideoInformationExists()):
            webbrowser.open_new("https://www.youtube.com/channel/"+self.MyYouTubeSearcherObj.full_data_info["items"][0]["snippet"]["channelId"])
    def OnShowAndHideInfoTool(self,evt):
        animation_speed = 30
        #self.panel.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        if(self.info_shown):
            i = self.size_with_info
            k = 0
            while(i[0]-k > self.size_without_info[0]):
                k+=animation_speed
                self.SetSize((i[0]-k,i[1]))
                self.Center()
            self.info_shown = 0
            if(animation_speed>30):
                self.SetSize(self.size_without_info)
        else:
            i = self.size_without_info
            k = 0
            while(i[0]+k <= self.size_with_info[0]):
                k+=animation_speed
                self.SetSize((i[0]+k,i[1]))
                self.Center()
            if(animation_speed>30):
                self.SetSize(self.size_with_info)
            self.info_shown = 1
            self.RefreshAdditionalInformation()
        #self.panel.SetBackgroundStyle(wx.BG_STYLE_ERASE)
        self.OnEraseBackground(wx.wx.EVT_ERASE_BACKGROUND)
    def CheckIfSomeFilterSet(self):
        if(self.check_show_only_HD.GetValue() or self.min_min_edit.GetValue() or self.max_min_edit.GetValue()):
            return 1
        else:
            return 0
    def OnClickMainThumbnail(self,evt):
        if self.HistoryStuffObj.CheckIfInHistoryMode() and my_globals.GlobalVideoIdForRelated == "" and self.HistoryStuffObj.AllPrepearingsDone() and self.HistoryStuffObj.GetSizeOfHistory()!=0:
            dlg = wx.MessageDialog(None, 'Item will be deleted from history.', 'Delete?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION )
            result = dlg.ShowModal()
            if result == wx.ID_NO:
                return
            self.HistoryStuffObj.DeleteCurrentItem()
            if(self.HistoryStuffObj.GetSizeOfHistory() == 0):
                self.NothingFoundRefresh()
                self.main_title_static_text.SetLabel("Nothing in History")
                return
            self.RefreshSongInfo()
    def OnHoverMainThumbnail(self,evt):
        if self.HistoryStuffObj.CheckIfInHistoryMode() and my_globals.GlobalVideoIdForRelated == "" and self.HistoryStuffObj.AllPrepearingsDone() and self.HistoryStuffObj.GetSizeOfHistory()!=0:
            self.main_image_thumb.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
            self.MyImageToolsObj.MergeTwoImagesToMerged(yr_constants.FILENAME_MAIN_THUMBNAIL_IMAGE,yr_constants.FILENAME_TRASH_OVERLAY_IMAGE)
            self.main_image_thumb.SetBitmap(wx.Bitmap(yr_constants.FILENAME_MERGED_IMAGE,wx.BITMAP_TYPE_ANY))
        else:
            self.main_image_thumb.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        if(self.VideoInformationExists()):
            self.statusbar.SetStatusText(self.MyYouTubeSearcherObj.GetTitleFromId(""))
    def OnExitMainThumbnail(self,evt):
        if self.HistoryStuffObj.CheckIfInHistoryMode() and (self.HistoryStuffObj.GetSizeOfHistory() != 0):
            self.main_image_thumb.SetBitmap(wx.Bitmap(yr_constants.FILENAME_MAIN_THUMBNAIL_IMAGE,wx.BITMAP_TYPE_ANY))
        self.statusbar.SetStatusText("")
    def OnRecommendButtonPressed(self,evt):
        if os.stat(yr_constants.FILENAME_HISTORY).st_size != 0:
            my_globals.GlobalVideoIdForRelated = self.MyYouTubeSearcherObj.RelateFromHistoryRecommenderObj.GetRecommendedVideoId()
            if(my_globals.GlobalVideoIdForRelated!=""):
                self.RefreshSongInfo()
            self.playbtn.Enable()
            self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,True)
            self.toolbar.EnableTool(self.APP_PLAY_EMBED,True)
        else:
            self.ShowMessageNoHistory()
    def OnChangeCheckboxRandomSearch(self,evt):
        if self.random_search_menu_checkbox.IsChecked():
            self.user_input_backup = self.search_text.GetValue()
            self.search_text.Disable()
            self.search_text.SetValue("")
        else:
            self.search_text.Enable()
            self.search_text.SetValue(self.user_input_backup)
    def OnSearchByThumbnailButton(self,evt):
        self.search_text.Disable()
        self.search_text.SetValue(self.MyYouTubeSearcherObj.UpdateTagsAndGetTagsForThumbnailAsStringForSearch(3))
        self.OnSmartButton("")
        self.search_text.Enable()
    def OnChangeIndex(self,evt):
        self.ChangeIndex(self.index_info_edit.GetValue())
    def OnStartHistoryModeThread(self):
        if os.stat(yr_constants.FILENAME_HISTORY).st_size > 0:
            self.HistoryStuffObj.UnsetAllPrepearingsDone()
            self.toolbar.EnableTool(self.APP_HISTORY,False)
            self.smartbtn.Disable()
            self.toolbar.EnableTool(self.APP_CLARIFAI_SEARCH,False)
            my_globals.GlobalVideoIdForRelated = ""
            if(my_globals.GlobalIfNowDownloading==0):
                self.playbtn.Enable()
                self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,True)
                self.toolbar.EnableTool(self.APP_PLAY_EMBED,True)
            self.HistoryStuffObj.history_list = self.HistoryStuffObj.ReadHistoryFromFile()
            self.HistoryStuffObj.EnableDisableHistoryMode(1)
            self.RefreshPrevAndNextButtons()
            self.smartbtn.Enable()
            self.toolbar.EnableTool(self.APP_CLARIFAI_SEARCH,True)
            self.toolbar.EnableTool(self.APP_HISTORY,True)
            self.HistoryStuffObj.SetAllPrepearingsDone()
        else:
            self.ShowMessageNoHistory()
    def ShowMessageNoHistory(self):
        dlg = wx.MessageDialog(self.panel,"There is not history yet. Download something or \nadd a video to history with the [+] button", "No history found!!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()
    def OnStartHistoryMode(self,evt):
        t = threading.Thread(target = self.OnStartHistoryModeThread)
        t.start()
    def OnOpenDownloads(self,evt):
        os.startfile(os.getcwd()+"./"+yr_constants.DIRNAME_DOWNLOADS_FOLDER)
    def UnloadRelatedThumbs(self):
        for bitmap in self.sBitMaps:
            bitmap.SetBitmap(wx.Bitmap(yr_constants.FILENAME_SMALL_NO_THUMBNAIL,wx.BITMAP_TYPE_ANY))
    def RefreshRelatedThumbs(self):
        ids = self.MyYouTubeSearcherObj.GetRelatedIds(None)
        i = 0
        self.UnloadRelatedThumbs()
        for my_id in ids:
            if i > 5:
                break
            img_address_local = "./"+yr_constants.DIRNAME_RELATED_IMAGES_FOLDER+"/"+my_id+"-"+str(self.related_thumbnails_current_indexes[i])+".jpg"
            if os.path.isfile(img_address_local):
                self.sBitMaps[i].SetBitmap(wx.Bitmap(img_address_local,wx.BITMAP_TYPE_ANY))
            i+=1
    def RunRelatedThumbnailsLoopUpdaterThread(self):
        t1 = threading.Thread(target=self.ThumbnailLoopUpdater)
        t1.daemon = True
        t1.start()
    def ThumbnailLoopUpdater(self):
        self.related_thumbnail_updater_thread_is_running = 0
        while(not self.related_thumbnail_updater_thread_is_stopped):
            time.sleep(0.1)
        self.related_thumbnail_updater_thread_is_running = 1
        self.related_thumbnail_updater_thread_is_stopped = 0
        bitmapId = self.related_thumbnail_id_updater_thread
        ids = self.MyYouTubeSearcherObj.GetRelatedIds(None)
        k = self.related_thumbnails_current_indexes[bitmapId]
        while(1):
            k+=1
            if k > 2:
                k=0
            img_address_local = "./"+yr_constants.DIRNAME_RELATED_IMAGES_FOLDER+"/"+ids[bitmapId]+"-"+str(k)+".jpg"
            self.related_thumbnails_current_indexes[bitmapId] = k
            if os.path.isfile(img_address_local):
                self.sBitMaps[bitmapId].SetBitmap(wx.Bitmap(img_address_local,wx.BITMAP_TYPE_ANY))
            for i in range(100):
                time.sleep(0.01)
                if(not self.related_thumbnail_updater_thread_is_running):
                    self.related_thumbnail_updater_thread_is_stopped = 1
                    return

    def OnHoverThumbnail(self, id):
        if(self.VideoInformationExists()):
            ids = self.MyYouTubeSearcherObj.GetRelatedIds(None)
            if(len(ids)>id):
                self.statusbar.SetStatusText(self.MyYouTubeSearcherObj.GetTitleFromId(ids[id]))
                self.related_thumbnail_id_updater_thread = id
                self.RunRelatedThumbnailsLoopUpdaterThread()
    def OnExitThumbnail(self,evt):
        self.related_thumbnail_updater_thread_is_running = 0
        self.statusbar.SetStatusText("")
    def OnClickThumbnail(self, id):
        ids = self.MyYouTubeSearcherObj.GetRelatedIds(None)
        if(len(ids)>id):
            my_globals.GlobalVideoIdForRelated = ids[id]
            self.RefreshSongInfo()
        return
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
    def IfAutoPlay(self):
        return self.check_auto_play.GetValue()
    def OnTimeToClose(self, evt):
        self.Destroy()

    def OnSmartButton(self, pageToken):
        my_globals.GlobalVideoIdForRelated = ""
        self.HistoryStuffObj.EnableDisableHistoryMode(0)
        self.text.SetLabel("Searching...")
        self.duration_info.SetLabel("unavailable")
        if(self.random_search_menu_checkbox.IsChecked()):
            self.MyYouTubeSearcherObj.GetRandomWord()
        self.RefreshPrevAndNextButtons()
        if(self.search_for_list_menu_checkbox.IsChecked()):
            self.MyYouTubeSearcherObj.SearchListPlease(self.search_text.GetValue(),pageToken)
        else:

            self.MyYouTubeSearcherObj.SearchPlease(self.search_text.GetValue(),pageToken)
        self.RefreshPrevAndNextPageButtons()
        if(self.CheckIfSomeFilterSet()):
            self.MyYouTubeSearcherObj.data_info = self.MyYouTubeSearcherObj.FilterResults(self.MyYouTubeSearcherObj.data_info)
            self.MyYouTubeSearcherObj.RefreshNumberOfFoundVideos()
        if self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()==0:
            self.NothingFoundRefresh()
            return None
        self.MyYouTubeSearcherObj.SetIndex(1)
        self.RefreshSongInfo()
        if(my_globals.GlobalIfNowDownloading==0):
            self.playbtn.Enable()
            self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,True)
            self.toolbar.EnableTool(self.APP_PLAY_EMBED,True)
    def ResetAndDisableIndexFieldAndMaxIndex(self):
        self.prevbtn.Disable()
        self.nextbtn.Disable()
        self.index_info_edit.Disable()
        self.index_info_edit.SetValue("")
        self.index_info.SetLabel("")
    def NothingFoundRefresh(self):
        self.UnloadRelatedThumbs()
        self.text.SetLabel("No Results!")
        self.statusbar.SetStatusText('Nothing Found...',1)
        self.duration_info.SetLabel("unavailable")
        self.main_image_thumb.SetBitmap(wx.Bitmap(yr_constants.FILENAME_BIG_NO_THUMBNAIL,wx.BITMAP_TYPE_ANY))
        self.toolbar.EnableTool(self.APP_OPEN_IN_BROWSER,False)
        self.toolbar.EnableTool(self.APP_CLARIFAI_SEARCH,False)
        self.playbtn.Disable()
        self.ResetAndDisableIndexFieldAndMaxIndex()
        self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,False)
        self.toolbar.EnableTool(self.APP_PLAY_EMBED,False)
    def StopTimer(self):
        self.now_timer_is_running = 0
    def OnDownloadFile(self, evt):
        self.MyYouTubeSearcherObj.CleanDirectoryFromDumpFiles()
        self.StopTimer()
        if(self.check_continuous_play.GetValue):
            self.MyYouTubeSearcherObj.StopMusic()
        self.remaining_time_in_seconds_for_timer_data = int(self.MyYouTubeSearcherObj.GetDuration())
        t1 = threading.Thread(target=self.DownloadBtnThread)
        t1.daemon = True
        t1.start()
    def RefreshPrevAndNextButtons(self):
        if self.HistoryStuffObj.CheckIfInHistoryMode():
            number_of_elements = self.HistoryStuffObj.GetSizeOfHistory()
            current_index = self.HistoryStuffObj.GetIndex()
        else:
            current_index = self.MyYouTubeSearcherObj.GetIndex()
            number_of_elements = self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()
        if(current_index==0):
            self.prevbtn.Disable()
        else:
            self.prevbtn.Enable()
        if(current_index==number_of_elements-1):
            self.nextbtn.Disable()
        else:
            self.nextbtn.Enable()
    def PrevSong(self, evt):
        if self.HistoryStuffObj.CheckIfInHistoryMode():
            self.HistoryStuffObj.DecrementIndex()
        else:
            self.MyYouTubeSearcherObj.DecrementIndex()
        my_globals.GlobalVideoIdForRelated = ""
        self.RefreshSongInfo()
        self.RefreshPrevAndNextButtons()
    def ChangeIndex(self,new_index):
        if self.HistoryStuffObj.CheckIfInHistoryMode():
            self.HistoryStuffObj.SetIndex(int(new_index))
        else:
            self.MyYouTubeSearcherObj.SetIndex(int(new_index))
        my_globals.GlobalVideoIdForRelated = ""
        self.RefreshSongInfo()
        self.RefreshPrevAndNextButtons()
    def NextSong(self, evt):
        if self.HistoryStuffObj.CheckIfInHistoryMode():
            if_last = self.HistoryStuffObj.IncrementIndex()
        else:
            if_last = self.MyYouTubeSearcherObj.IncrementIndex()
        my_globals.GlobalVideoIdForRelated = ""
        self.RefreshSongInfo()
        self.RefreshPrevAndNextButtons()
        return if_last
    def RefreshSongInfo(self):
        self.UnloadRelatedThumbs()
        self.main_image_thumb.SetBitmap(wx.Bitmap(yr_constants.FILENAME_BIG_NO_THUMBNAIL,wx.BITMAP_TYPE_ANY))
        if self.HistoryStuffObj.CheckIfInHistoryMode():
            number_of_elements = self.HistoryStuffObj.GetSizeOfHistory()
            current_index = self.HistoryStuffObj.GetIndex()
        else:
            current_index = self.MyYouTubeSearcherObj.GetIndex()
            number_of_elements = self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()
        thread_loading_related_videos = threading.Thread(target=self.MyYouTubeSearcherObj.LoadRelatedVideos)
        thread_loading_related_videos.daemon = True
        thread_loading_related_videos.start()
        #self.MyYouTubeSearcherObj.LoadRelatedVideos()
        self.MyYouTubeSearcherObj.SaveThumb()
        self.MyYouTubeSearcherObj.LoadStatisticsAndInformation()
        self.MyYouTubeSearcherObj.LoadContentDetails()
        img_downloaded = self.MyImageToolsObj.ResizeImage(yr_constants.FILENAME_MAIN_THUMBNAIL_BEFORE_CONVERTION,(320,240))
        self.MyYouTubeSearcherObj.CreateHtmlWithIFrameForCurrentVideo()
        if(my_globals.GlobalVideoIdForRelated != ""):
            self.main_title_static_text.SetLabel("Related Video")
        else:
            self.main_title_static_text.SetLabel(self.current_main_title)
        if(self.MyYouTubeSearcherObj.GetTitleFromId("")=="Deleted Video"):
            self.NextSong("")
            return
        self.text.SetLabel(self.MyYouTubeSearcherObj.GetTitleFromId(""))
        self.text.Wrap(300)
        views_count = global_functions.intWithCommas(int(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["viewCount"]))
        spaces_between = 34
        spaces_between = (spaces_between-len(views_count))/2
        label_future_text = "Views: "+views_count
        for i in range(spaces_between):
            label_future_text += " "
        label_future_text += self.MyYouTubeSearcherObj.GetPublishedAt()
        for i in range(spaces_between):
            label_future_text += " "
        label_future_text += "["+self.MyYouTubeSearcherObj.NormalizeSeconds(self.MyYouTubeSearcherObj.GetDuration())+"]"
        self.duration_info.SetLabel(label_future_text)
        self.index_info_edit.Enable()
        self.index_info_edit.SetValue(str(current_index+1))
        self.index_info.SetLabel("/"+str(number_of_elements))
        if(img_downloaded):
            #self.panel.SetBackgroundColour(self.MyImageToolsObj.GetAvgColorOfAnImage(yr_constants.FILENAME_MAIN_THUMBNAIL_IMAGE,150))
            #self.panel.Refresh()
            self.main_image_thumb.SetBitmap(wx.Bitmap(yr_constants.FILENAME_MAIN_THUMBNAIL_IMAGE,wx.BITMAP_TYPE_ANY))
        else:
            #self.panel.SetBackgroundColour(self.MyImageToolsObj.GetAvgColorOfAnImage(yr_constants.FILENAME_BIG_NO_THUMBNAIL,150))
            #self.panel.Refresh()
            self.main_image_thumb.SetBitmap(wx.Bitmap(yr_constants.FILENAME_BIG_NO_THUMBNAIL,wx.BITMAP_TYPE_ANY))
        self.toolbar.EnableTool(self.APP_OPEN_IN_BROWSER,True)
        self.toolbar.EnableTool(self.APP_CLARIFAI_SEARCH,True)
        if(self.info_shown):
            self.RefreshAdditionalInformation()
    def RunTimer(self):
        title = self.MyYouTubeSearcherObj.temp_future_filename
        dots = ""
        if(len(title)>30):
            dots = "..."
        if(my_globals.GlobalLastRenameFileResult):
            self.now_timer_is_running = 1
        else:
            self.now_timer_is_running = 0
        remaining_time_in_seconds_for_timer_data = self.remaining_time_in_seconds_for_timer_data
        while(remaining_time_in_seconds_for_timer_data>0 and self.now_timer_is_running):
            time.sleep(1)
            remaining_time_in_seconds_for_timer_data-=1
            self.statusbar.SetStatusText("Playing: "+title[:30]+dots+" ["+self.MyYouTubeSearcherObj.NormalizeSeconds(remaining_time_in_seconds_for_timer_data)+"]", 1)
        self.statusbar.SetStatusText("", 1)
        if(self.now_timer_is_running):
            self.CheckAndContinueIfIsEnabledContinuousMode("start_from_beginning_after_end")
    def CheckAndContinueIfIsEnabledContinuousMode(self,argument):
        if(self.check_continuous_play.GetValue()):
            if self.NextSong(""):
                if(argument == "start_from_beginning_after_end"):
                    self.ChangeIndex("1")
                elif(argument == "stop_after_end"):
                    self.ShowAllDownloadMessage()
                    return
            self.OnDownloadFile("")
    def ShowAllDownloadMessage(self):
        dlg = wx.MessageDialog(self.panel,"The list ended. All Downloaded.", "Download complete!", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    def DownloadBtnThread(self):
        self.OnDownloadButton("")
        if(self.IfAutoPlay()==1):
            self.MyYouTubeSearcherObj.PlayMp3InDir("")
            return
        self.CheckAndContinueIfIsEnabledContinuousMode("stop_after_end")

    def OnDownloadButton(self, evt):
        my_globals.GlobalIfNowDownloading = 1
        self.check_auto_play.Disable()
        self.playbtn.Disable()
        self.toolbar.EnableTool(self.APP_PLAY_EMBED,False)
        self.check_mp4_or_mp3.Disable()
        self.check_hight_quality.Disable()
        self.toolbar.EnableTool(self.APP_DELETE_DOWNLOADS,False)
        self.MyYouTubeSearcherObj.DownloadFile()
        self.check_auto_play.Enable()
        self.playbtn.Enable()
        self.toolbar.EnableTool(self.APP_PLAY_EMBED,True)
        self.check_mp4_or_mp3.Enable()
        self.check_hight_quality.Enable()
        self.toolbar.EnableTool(self.APP_DELETE_DOWNLOADS,True)
        my_globals.GlobalIfNowDownloading = 0
    def AddCurrentVideoToHistory(self,event):
        url = self.MyYouTubeSearcherObj.GetWatchUrl()
        self.HistoryStuffObj.AppendToHistoryFile(url)
        self.ShowMessageSavedToHistory()
    def ShowMessageSavedToHistory(self):
        dlg = wx.MessageDialog(self.panel,"Video has been saved to your history!", "Video added", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    def ShowMessageHistorySynced(self):
        dlg = wx.MessageDialog(self.panel,"All videos has been synchronised on you youtube history playlist!", "History synchronised successfully!", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    def OnOpenInBrowser(self,event):
        webbrowser.open_new(self.MyYouTubeSearcherObj.GetWatchUrl())

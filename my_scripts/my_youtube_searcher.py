import yr_constants
import clarifai_tagger
import relate_from_history_recommender
import urllib2
import json
import my_globals
import os
import urllib
from win32api import GetSystemMetrics
import isodate
import time
import re
import webbrowser
from time import gmtime, strftime
import os.path
import wx
import webbrowser
import threading

class MyYouTubeSearcher():
    def __init__(self,parent):
        self.index = 0
        self.parent = parent
        self.data_info = dict()
        self.full_data_info = dict()
        self.content_details = dict()
        self.related_videos = dict()
        self.ext = 'mp3'
        self.number_of_found_videos = 0
        self.temp_future_filename = ""
        self.MyClarifaiTaggerObj = clarifai_tagger.ClarifayTagger(self)
        self.RelateFromHistoryRecommenderObj = relate_from_history_recommender.RelateFromHistoryRecommender(self)
        self.pages_tokens = ["",""]
    def CleanDataInfo(self):
        self.data_info = dict()
    def CreateHtmlWithIFrameForCurrentVideo(self):
        html_file = open(yr_constants.FILENAME_IFRAME_HTML,"w")
        html_file.write('<iframe width="'+str(GetSystemMetrics(0)/2)+'" height="'+str(GetSystemMetrics(1)/2)+'" src="https://www.youtube.com/embed/'+self.GetCurrentVideoId()+'?rel=0&autoplay=1" frameborder="0" allowfullscreen></iframe>')
        html_file.close()
    def GetIndex(self):
        return self.index
    def IncrementIndex(self):
        if(self.index+1<self.GetNumberOfFoundVideos()):
            self.index+=1
            return 0
        else:
            return 1 #is last song
    def DecrementIndex(self):
        if(self.index-1>=0):
            self.index-=1
    def SetIndex(self,new):
        if(new-1>=0)and(new-1<self.GetNumberOfFoundVideos()):
            self.index = new-1

    def GetCurrentVideoId(self):
        if(my_globals.GlobalVideoIdForRelated!=""):
            return my_globals.GlobalVideoIdForRelated
        if(self.parent.HistoryStuffObj.CheckIfInHistoryMode()):
            return self.parent.HistoryStuffObj.GetCurrentVideoId()
        else:
            if(self.parent.search_for_list_menu_checkbox.IsChecked()):
                return self.data_info["items"][self.GetIndex()]["snippet"]["resourceId"]["videoId"]
            else:
                return self.data_info["items"][self.GetIndex()]["id"]["videoId"]
    def GetWatchUrl(self):
        return 'https://www.youtube.com/watch?v='+self.GetCurrentVideoId()
    def GetSavingFileName(self):
        return self.GetTitle()[:30].replace(" ","_")+'_'+str(self.GetCurrentVideoId())+'.'+self.ext
    def SetExt(self,param):
        self.ext = param
    def RefreshNumberOfFoundVideos(self):
        if "items" in self.data_info:
            self.number_of_found_videos = len(self.data_info["items"])
        else:
            self.number_of_found_videos = 0
    def FilterResults(self,arg_dict):
        only_HD = self.parent.check_show_only_HD.GetValue()
        min_min = self.parent.min_min_edit.GetValue()
        max_min = self.parent.max_min_edit.GetValue()
        the_dict = arg_dict
        indexes_for_delete = list()
        i = 0
        videoIds = list()
        for key in arg_dict:
            if(key == "items"):
                arg_check = "dict"
            else:
                arg_check = "list"
        if(arg_check == "dict"):
            for videoIdDict in the_dict["items"]:
                for key in videoIdDict:
                    if key == "snippet":
                        videoIds.append(videoIdDict["snippet"]["resourceId"]["videoId"])
                    else:
                        videoIds.append(videoIdDict["id"]["videoId"])
        else:
            videoIds = arg_dict
        counter = float(0)
        percent = int(0)
        size = float(len(videoIds))
        for videoId in videoIds:
            counter+=1
            if(size!=0):
                percent = counter/(size/100)
            self.parent.statusbar.SetStatusText("Filtering: "+str(int(percent))+"%",1)
            url = "https://www.googleapis.com/youtube/v3/videos?id="+videoId+"&part=contentDetails&fields=items(contentDetails(duration,definition))&key="+yr_constants.api_key
            content = urllib2.urlopen(url).read()
            contents = json.loads(content)
            if(len(contents["items"])>0):
                if(only_HD):
                    if(contents["items"][0]["contentDetails"]["definition"]!="hd"):
                        indexes_for_delete.append(i)
                if(min_min and max_min):
                    duration = isodate.parse_duration(contents["items"][0]["contentDetails"]["duration"])
                    duration_in_minutes = duration.total_seconds()/60
                    if(duration_in_minutes <= int(min_min) or duration_in_minutes >= int(max_min)):
                        if i not in indexes_for_delete:
                            indexes_for_delete.append(i)
            else:
                indexes_for_delete.append(i)
            i += 1
        indexes_for_delete.reverse()
        if(arg_check == "dict"):
            for index_for_delete in indexes_for_delete:
                del the_dict["items"][index_for_delete]
            return the_dict
        elif(arg_check == "list"):
            for index_for_delete in indexes_for_delete:
                del videoIds[index_for_delete]
            return videoIds
        self.parent.statusbar.SetStatusText("",1)
    def SearchPlease(self,query,pageToken):
        if(pageToken!=""):
            pageToken = "pageToken="+pageToken+"&"
        self.parent.current_main_title = "Search videos: "+query
        self.parent.statusbar.SetStatusText('Searching for "'+query+'"')
        query = query.encode(encoding='UTF-8',errors='strict')
        query = query.replace(' ', '+')
        self.data_info = dict()
        self.found_ids = dict()
        my_url = "https://www.googleapis.com/youtube/v3/search?"+pageToken+"part=id&q="+query+"&maxResults=30&type=video&fields=prevPageToken,nextPageToken,items(id(videoId))&key="+yr_constants.api_key
        #webbrowser.open_new(my_url)
        content = urllib2.urlopen(my_url).read()
        self.data_info = json.loads(content)
        self.pages_tokens = ["",""]
        if "nextPageToken" in self.data_info:
            self.pages_tokens[1] = self.data_info["nextPageToken"]
            del self.data_info["nextPageToken"]
        if "prevPageToken" in self.data_info:
            self.pages_tokens[0] = self.data_info["prevPageToken"]
            del self.data_info["prevPageToken"]
        self.RefreshNumberOfFoundVideos()
        self.parent.statusbar.SetStatusText("",1)
    def SearchListPlease(self,query,pageToken):
        if(pageToken!=""):
            pageToken = "pageToken="+pageToken+"&"
        self.parent.statusbar.SetStatusText('Searching for "'+query+'"')
        query = query.encode(encoding='UTF-8',errors='strict')
        query = query.replace(' ', '+')
        self.data_info = dict()
        self.found_ids = dict()
        found_lists_info = dict()
        my_url = "https://www.googleapis.com/youtube/v3/search?part=snippet,id&kind=playlist&q="+query+"&maxResults=1&type=playlist&fields=items(id(playlistId),snippet(title))&key="+yr_constants.api_key
        #webbrowser.open_new(my_url)
        content = urllib2.urlopen(my_url).read()
        found_lists_info = json.loads(content)
        playlistId = found_lists_info["items"][0]["id"]["playlistId"]
        self.parent.current_main_title = "List: "+found_lists_info["items"][0]["snippet"]["title"]
        my_url = "https://www.googleapis.com/youtube/v3/playlistItems?"+pageToken+"part=snippet&maxResults=30&playlistId="+playlistId+"&fields=prevPageToken,nextPageToken,items(snippet(resourceId(videoId)))&key="+yr_constants.api_key
        #webbrowser.open_new(my_url)
        content = urllib2.urlopen(my_url).read()
        self.data_info = json.loads(content)
        self.pages_tokens = ["",""]
        if "nextPageToken" in self.data_info:
            self.pages_tokens[1] = self.data_info["nextPageToken"]
            del self.data_info["nextPageToken"]
        if "prevPageToken" in self.data_info:
            self.pages_tokens[0] = self.data_info["prevPageToken"]
            del self.data_info["prevPageToken"]
        self.RefreshNumberOfFoundVideos()
        self.parent.statusbar.SetStatusText("",1)
    def LoadStatisticsAndInformation(self):
        self.parent.statusbar.SetStatusText("Requesting for statistics and information...",1)
        self.full_data_info = dict()
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.GetCurrentVideoId()+"&key="+yr_constants.api_key+"&fields=items(id,snippet(publishedAt,channelId,title,description,categoryId),statistics)&part=snippet,statistics"
        #webbrowser.open_new(my_url)
        content = urllib2.urlopen(my_url).read()
        self.full_data_info = json.loads(content)
        self.parent.statusbar.SetStatusText("",1)
    def LoadContentDetails(self):
        self.parent.statusbar.SetStatusText("Loading content details...",1)
        self.content_details = dict()
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.GetCurrentVideoId()+"&part=contentDetails&fields=items(contentDetails(duration,definition))&key="+yr_constants.api_key
        #webbrowser.open_new(my_url)
        content = urllib2.urlopen(my_url).read()
        self.content_details = json.loads(content)
        self.parent.statusbar.SetStatusText("",1)
    def RequestRelatedVideosDictByVideoWithId(self,videoId):
        if(self.parent.check_hight_quality.GetValue()):
            max_results = "12"
        else:
            max_results = "6"
        self.parent.statusbar.SetStatusText("Requesting related videos dictionary...",1)
        my_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId="+videoId+"&maxResults="+max_results+"&type=video&fields=items(id(videoId))&key="+yr_constants.api_key
        #webbrowser.open_new(my_url)
        content = urllib2.urlopen(my_url).read()
        return json.loads(content)
        self.parent.statusbar.SetStatusText("",1)
    def LoadRelatedVideos(self):
        self.related_videos = dict()
        self.related_videos = self.RequestRelatedVideosDictByVideoWithId(self.GetCurrentVideoId())
        if(self.parent.CheckIfSomeFilterSet()):
            self.related_videos = self.FilterResults(self.related_videos)
        self.SaveRelatedThumbs()
        self.parent.RefreshRelatedThumbs()
    def GetRelatedIds(self,related_videos_dict):
        if related_videos_dict == None:
            related_videos_dict = self.related_videos
        if(len(related_videos_dict)==0):
            return list()
        list_to_return = list()
        i = 0
        while(i<len(related_videos_dict["items"])):
            list_to_return.append(related_videos_dict["items"][i]["id"]["videoId"])
            i+=1
        return list_to_return
    def GetDuration(self):
        if(len(self.content_details["items"])>0):
            duration_str = self.content_details["items"][0]["contentDetails"]["duration"]
            dur=isodate.parse_duration(duration_str)
            return str(int(dur.total_seconds()))
        else:
            return "unavailable"

    def GetPublishedAt(self):
        if(len(self.full_data_info["items"])>0):
            return str(isodate.parse_datetime(self.full_data_info["items"][0]["snippet"]["publishedAt"])).split("+")[0]
        else:
            return ""
    def GetTitleFromId(self,id):
        self.parent.statusbar.SetStatusText("Getting title from id",1)
        if id=="":
            id = self.GetCurrentVideoId()
        info = dict()
        url = 'https://www.googleapis.com/youtube/v3/videos?id='+id+'&key='+yr_constants.api_key+'&fields=items(snippet(title))&part=snippet'
        content = urllib2.urlopen(url).read()
        info = json.loads(content)
        self.parent.statusbar.SetStatusText("",1)
        if(len(info["items"])>0):
            return info["items"][0]["snippet"]["title"]
        else:
            return "Deleted Video"
    def GetTitle(self):
        return str(re.sub('[^A-Za-z0-9]+', ' ', self.full_data_info["items"][0]["snippet"]["title"]))
    def GetNumberOfFoundVideos(self):
        return self.number_of_found_videos
    def GetThumbUrlById(self,videoId):
        if videoId == "":
            videoId = self.GetCurrentVideoId()
        return "https://img.youtube.com/vi/"+videoId+"/0.jpg"
    def UpdateTagsAndGetTagsForThumbnailAsStringForSearch(self,amount):
        self.MyClarifaiTaggerObj.UpdateTags(self.GetThumbUrlById(""))
        return self.MyClarifaiTaggerObj.GetStringOfTagsWithAmount(amount)
    def SaveThumb(self):
        self.parent.statusbar.SetStatusText('Fetching main thumbnail...',1)
        thumb_url = self.GetThumbUrlById(self.GetCurrentVideoId())
        testfile = urllib.URLopener()
        try:
            testfile.retrieve(thumb_url, yr_constants.FILENAME_MAIN_THUMBNAIL_BEFORE_CONVERTION)
        except IOError:
            pass
        self.parent.statusbar.SetStatusText("",1)
    def SaveThumbParam(self,videoId,filename):
        self.parent.statusbar.SetStatusText('Fetching some thumbnail...',1)
        thumb_url = self.GetThumbUrlById(videoId)
        testfile = urllib.URLopener()
        try:
            testfile.retrieve(thumb_url, filename)
        except IOError:
            pass
        self.parent.statusbar.SetStatusText("",1)
    def ClearRelatedThubms(self):
        os.system('del /Q "'+os.getcwd()+'\\'+yr_constants.DIRNAME_RELATED_IMAGES_FOLDER+'\\*"')
    def SaveRelatedThumbs(self):
        self.ClearRelatedThubms()
        self.parent.statusbar.SetStatusText('Fetching related thumbs...',1)
        related_ids = self.GetRelatedIds(None)
        for related_id in related_ids:
            for i in range(3):
                local_address = "./"+yr_constants.DIRNAME_RELATED_IMAGES_FOLDER+"/"+related_id+"-"+str(i)+".jpg"
                thumb_url = "https://img.youtube.com/vi/"+related_id+"/"+str(i+1)+".jpg"
                testfile = urllib.URLopener()
                try:
                    r = testfile.retrieve(thumb_url, local_address)
                except IOError:
                    pass

        self.parent.statusbar.SetStatusText("",1)
    def DownloadingStatusLoopUpdater(self):
        while(my_globals.GlobalIfNowDownloading):
            time.sleep(0.1)
            self.parent.statusbar.SetStatusText('Downloading: '+self.temp_future_filename[:15]+'...'+self.temp_future_filename[20:],1)
        self.parent.statusbar.SetStatusText("",1)
    def DownloadFile(self):
        self.temp_future_filename = self.GetSavingFileName()
        thread_download_status_loop_updater = threading.Thread(target=self.DownloadingStatusLoopUpdater)
        thread_download_status_loop_updater.daemon = True
        thread_download_status_loop_updater.start()
        hight_quality_parameters = ""
        format_parameters = ""

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
        os.system('del '+'"'+yr_constants.DIRNAME_DOWNLOADS_FOLDER+'\\'+self.temp_future_filename+'"')
        command = 'youtubedl\\youtubedl.exe "'+self.GetWatchUrl()+'" '+hight_quality_parameters+' '+format_parameters+' -o "./'+yr_constants.DIRNAME_DOWNLOADS_FOLDER+'/temp.'+'%'+'(ext)s"'
        self.parent.HistoryStuffObj.AppendToHistoryFile(self.GetWatchUrl())
        os.system(command)
        self.RenameMp3File()
        self.parent.statusbar.SetStatusText("",1)
    def LetsHearTheSong(self):
        if(self.parent.IfAutoPlay()==1):
            if(my_globals.GlobalLastRenameFileResult):
                self.t_timer = threading.Thread(target=self.parent.RunTimer)
                self.t_timer.daemon = True
                self.t_timer.start()
                os.startfile(yr_constants.DIRNAME_DOWNLOADS_FOLDER+'\\'+self.temp_future_filename, 'open')
            else:
                self.parent.CheckAndContinueIfIsEnabledContinuousMode("start_from_beginning_after_end")
    def PlayMp3InDir(self,event):
        self.parent.statusbar.SetStatusText('Prepare file...',1)
        self.LetsHearTheSong()
        self.parent.statusbar.SetStatusText("",1)
    def CleanDirectoryFromDumpFiles(self):
        self.parent.statusbar.SetStatusText('Cleaning download dir dump files...',1)
        test=os.listdir(os.getcwd()+"\\"+yr_constants.DIRNAME_DOWNLOADS_FOLDER)
        for item in test:
            if item.endswith(".webm") or item.endswith(".part") or item.endswith("temp.mp3") or item.endswith("temp.mp4"):
                os.remove(os.getcwd()+"\\"+yr_constants.DIRNAME_DOWNLOADS_FOLDER+"\\"+item)
        self.parent.statusbar.SetStatusText("",1)
    def DeleteAllMp3(self):
        self.parent.statusbar.SetStatusText('Deleting all downloads...',1)
        self.StopMusic()
        time.sleep(2)
        os.system('del /Q "'+os.getcwd()+'\\'+yr_constants.DIRNAME_DOWNLOADS_FOLDER+'\\*"')
        self.parent.statusbar.SetStatusText("",1)
    def ShowMessageCantBeDownload(self):
        dlg = wx.MessageDialog(self.parent.panel,"The format you want is unavailable! \nPlease change the quality or format and try again.", "Download warning!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()
    def RenameMp3File(self):
        self.StopMusic()
        time.sleep(2)
        file_to_check_and_rename = os.path.join(os.getcwd(), yr_constants.DIRNAME_DOWNLOADS_FOLDER+"\\temp."+self.ext)
        if(os.path.isfile(file_to_check_and_rename)):
            os.system('rename "'+file_to_check_and_rename+'" "'+self.temp_future_filename+'"')
            my_globals.GlobalLastRenameFileResult = 1
            return 1
        else:
            if(not self.parent.check_continuous_play.GetValue()):
                self.ShowMessageCantBeDownload()
            my_globals.GlobalLastRenameFileResult = 0
            return 0
    def StopMusic(self):
        if(self.parent.IfAutoPlay()==1):
            os.startfile(yr_constants.FILENAME_NO_SOUND_MP3, 'open')
            os.startfile(yr_constants.FILENAME_NO_SOUND_MP4, 'open')
            time.sleep(1)
    def GetRandomWord(self):
        url = "http://setgetgo.com/randomword/get.php"
        content = urllib2.urlopen(url).read()
        self.parent.search_text.SetValue(content)
    def NormalizeSeconds(self,sec):
        if(sec!="unavailable"):
            return time.strftime('%H:%M:%S', time.gmtime(float(sec)))
        else:
            return ""

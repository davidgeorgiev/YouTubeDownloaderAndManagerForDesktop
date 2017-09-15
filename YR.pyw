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
import isodate
from clarifai.rest import ClarifaiApp
from random import shuffle
from random import randint
import unicodedata
import warnings
import Image
import wx.lib.scrolledpanel
import win32clipboard
from win32api import GetSystemMetrics

warnings.filterwarnings('ignore')

GlobalSmartThreadRuning = 0
GlobalVideoIdForRelated = ""
GlobalIfNowDownloading = 0
GlobalLastRenameFileResult = 0
api_key = #ENTER YOUR API KEY HERE

def intWithCommas(x):
    if type(x) not in [type(0), type(0L)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithCommas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)
class ImageTools():
    def __init__ (self,parent):
        self.parent = parent
    def ResizeImage(self,infile,size):
        temp_name = "temp-converting.png"
        try:
            self.parent.statusbar.SetStatusText("Converting main thumbnail...",1)
            im = Image.open(infile)
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(temp_name, "PNG")
            os.unlink(infile)
            infile = infile.split(infile.split(".")[-1])[0]+"png"
            if(os.path.isfile(infile)):
                os.unlink(infile)
            os.rename(temp_name,infile)
            self.parent.statusbar.SetStatusText("",1)
            return 1
        except IOError:
            #"cannot create thumbnail"
            return 0

    def MergeTwoImagesToMerged(self,bg,fg):
        background = Image.open(bg)
        foreground = Image.open(fg)
        background.paste(foreground, (0, 0), foreground)
        background.save("merged.png", "PNG")

    def GetAvgColorOfAnImage(self,img_url,sum_val):
        im = Image.open("file.png")
        i = 0
        red_counter = 0
        red_sum = 0
        green_counter = 0
        green_sum = 0
        blue_counter = 0
        blue_sum = 0
        for value in im.histogram():
            if value>0 and value<256:
                red_counter+=1
                red_sum+=value
            if value>255 and value<511:
                green_counter+=1
                green_sum+=value-255
            if value>510 and value<766:
                blue_counter+=1
                blue_sum+=value-510
            i+=1
        avg_red = red_sum/red_counter
        avg_green = green_sum/green_counter
        avg_blue = blue_sum/blue_counter
        avg_red += sum_val
        avg_green += sum_val
        avg_blue += sum_val
        if(avg_red>255):
            avg_red=255
        if(avg_red<0):
            avg_red=0
        if(avg_green>255):
            avg_green=255
        if(avg_green<0):
            avg_red=0
        if(avg_blue>255):
            avg_blue=255
        if(avg_blue<0):
            avg_blue=0
        return "RGB("+str(avg_red)+","+str(avg_green)+","+str(avg_blue)+")"
class RelateFromHistoryRecommender():
    def __init__(self,parent):
        self.base_random_video_id = ""
        self.currentRecommendVideoId = ""
        self.parent = parent
    def AnalyzeHistoryFileAndGetRandomVideo(self):
        content = list()
        with open("./all_played_videos.txt") as f:
            content = f.readlines()
        shuffle(content)
        self.base_random_video_id = content[0].replace("https://www.youtube.com/watch?v=","").replace("\n","")
    def GetRecommendedVideoId(self):
        self.parent.parent.statusbar.SetStatusText("Analyzing history and get video",1)
        self.AnalyzeHistoryFileAndGetRandomVideo()
        result_dict = self.parent.RequestRelatedVideosDictByVideoWithId(self.base_random_video_id)
        if(self.parent.parent.CheckIfSomeFilterSet()):
            result_dict = self.parent.FilterResults(result_dict)
        videoIds = self.parent.GetRelatedIds(result_dict)
        shuffle(videoIds)
        if(len(videoIds) == 0):
            self.parent.parent.statusbar.SetStatusText("Nothing found! Try again!",1)
            return ""
        else:
            return videoIds[0]
class ClarifayTagger():
    def __init__(self,parent):
        self.parent = parent
        self.last_tags = list()
    def UpdateTags(self,arg_url):
        self.parent.parent.statusbar.SetStatusText("Getting tags for thumbnail with clarifai",1)
        tags = list()
        app = ClarifaiApp()
        model = app.models.get('general-v1.3')
        response = model.predict_by_url(url=arg_url)
        concepts = response['outputs'][0]['data']['concepts']
        for concept in concepts:
            tags.append(concept['name'])
            self.last_tags = tags
        self.parent.parent.statusbar.SetStatusText("",1)
    def GetLastTags(self):
        return self.last_tags
    def GetRandomTagsWithAmount(self,amount):
        tags = self.last_tags
        shuffle(tags)
        return tags[:amount]
    def GetTagsWithAmount(self,amount):
        tags = self.last_tags
        return tags[:amount]
    def GetStringOfTags(self):
        return " ".join(self.last_tags)
    def GetStringOfRandomTagsWithAmount(self,amount):
        return " ".join(self.GetRandomTagsWithAmount(amount))
    def GetStringOfTagsWithAmount(self,amount):
        return " ".join(self.GetTagsWithAmount(amount))
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
        self.MyClarifaiTaggerObj = ClarifayTagger(self)
        self.RelateFromHistoryRecommenderObj = RelateFromHistoryRecommender(self)
        self.pages_tokens = ["",""]
    def CreateHtmlWithIFrameForCurrentVideo(self):
        html_file = open("index.html","w")
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
        global GlobalVideoIdForRelated
        if(GlobalVideoIdForRelated!=""):
            return GlobalVideoIdForRelated
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
        self.number_of_found_videos = len(self.data_info["items"])
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
            url = "https://www.googleapis.com/youtube/v3/videos?id="+videoId+"&part=contentDetails&fields=items(contentDetails(duration,definition))&key="+api_key
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
        my_url = "https://www.googleapis.com/youtube/v3/search?"+pageToken+"part=id&q="+query+"&maxResults=30&type=video&fields=prevPageToken,nextPageToken,items(id(videoId))&key="+api_key
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
        my_url = "https://www.googleapis.com/youtube/v3/search?part=snippet,id&kind=playlist&q="+query+"&maxResults=1&type=playlist&fields=items(id(playlistId),snippet(title))&key="+api_key
        #webbrowser.open_new(my_url)
        content = urllib2.urlopen(my_url).read()
        found_lists_info = json.loads(content)
        playlistId = found_lists_info["items"][0]["id"]["playlistId"]
        self.parent.current_main_title = "List: "+found_lists_info["items"][0]["snippet"]["title"]
        my_url = "https://www.googleapis.com/youtube/v3/playlistItems?"+pageToken+"part=snippet&maxResults=30&playlistId="+playlistId+"&fields=prevPageToken,nextPageToken,items(snippet(resourceId(videoId)))&key="+api_key
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
        self.number_of_found_videos = len(self.data_info[u"items"])
        self.parent.statusbar.SetStatusText("",1)
    def LoadStatisticsAndInformation(self):
        self.parent.statusbar.SetStatusText("Requesting for statistics and information...",1)
        self.full_data_info = dict()
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.GetCurrentVideoId()+"&key="+api_key+"&fields=items(id,snippet(publishedAt,channelId,title,description,categoryId),statistics)&part=snippet,statistics"
        #webbrowser.open_new(my_url)
        content = urllib2.urlopen(my_url).read()
        self.full_data_info = json.loads(content)
        self.parent.statusbar.SetStatusText("",1)
    def LoadContentDetails(self):
        self.parent.statusbar.SetStatusText("Loading content details...",1)
        self.content_details = dict()
        my_url = "https://www.googleapis.com/youtube/v3/videos?id="+self.GetCurrentVideoId()+"&part=contentDetails&fields=items(contentDetails(duration,definition))&key="+api_key
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
        my_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId="+videoId+"&maxResults="+max_results+"&type=video&fields=items(id(videoId))&key="+api_key
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
        url = 'https://www.googleapis.com/youtube/v3/videos?id='+id+'&key='+api_key+'&fields=items(snippet(title))&part=snippet'
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
            testfile.retrieve(thumb_url, "file.jpg")
        except IOError:
            a=1
        self.parent.statusbar.SetStatusText("",1)
    def ClearRelatedThubms(self):
        os.system('del /Q "'+os.getcwd()+'\\related_images\\*"')
    def SaveRelatedThumbs(self):
        self.ClearRelatedThubms()
        self.parent.statusbar.SetStatusText('Fetching related thumbs...',1)
        related_ids = self.GetRelatedIds(None)
        for related_id in related_ids:
            for i in range(3):
                local_address = "./related_images/"+related_id+"-"+str(i)+".jpg"
                thumb_url = "https://img.youtube.com/vi/"+related_id+"/"+str(i+1)+".jpg"
                testfile = urllib.URLopener()
                try:
                    r = testfile.retrieve(thumb_url, local_address)
                except IOError:
                    a=1

        self.parent.statusbar.SetStatusText("",1)
    def DownloadingStatusLoopUpdater(self):
        global GlobalIfNowDownloading
        while(GlobalIfNowDownloading):
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
        os.system('del '+'"downloads\\'+self.temp_future_filename+'"')
        command = 'youtubedl\\youtubedl.exe "'+self.GetWatchUrl()+'" '+hight_quality_parameters+' '+format_parameters+' -o "./downloads/temp.'+'%'+'(ext)s"'
        self.parent.HistoryStuffObj.AppendToHistoryFile(self.GetWatchUrl())
        os.system(command)
        self.RenameMp3File()
        self.parent.statusbar.SetStatusText("",1)
    def LetsHearTheSong(self):
        global GlobalLastRenameFileResult
        if(self.parent.IfAutoPlay()==1):
            if(GlobalLastRenameFileResult):
                self.t_timer = threading.Thread(target=self.parent.RunTimer)
                self.t_timer.daemon = True
                self.t_timer.start()
                os.startfile('downloads\\'+self.temp_future_filename, 'open')
            else:
                self.parent.CheckAndContinueIfIsEnabledContinuousMode("start_from_beginning_after_end")
    def PlayMp3InDir(self,event):
        self.parent.statusbar.SetStatusText('Prepare file...',1)
        self.LetsHearTheSong()
        self.parent.statusbar.SetStatusText("",1)
    def CleanDirectoryFromDumpFiles(self):
        self.parent.statusbar.SetStatusText('Cleaning download dir dump files...',1)
        test=os.listdir(os.getcwd()+"\\downloads")
        for item in test:
            if item.endswith(".webm") or item.endswith(".part") or item.endswith("temp.mp3") or item.endswith("temp.mp4"):
                os.remove(os.getcwd()+"\\downloads\\"+item)
        self.parent.statusbar.SetStatusText("",1)
    def DeleteAllMp3(self):
        self.parent.statusbar.SetStatusText('Deleting all downloads...',1)
        self.StopMusic()
        time.sleep(2)
        os.system('del /Q "'+os.getcwd()+'\\downloads\\*"')
        self.parent.statusbar.SetStatusText("",1)
    def ShowMessageCantBeDownload(self):
        dlg = wx.MessageDialog(self.parent.panel,"The format you want is unavailable! \nPlease change the quality or format and try again.", "Download warning!", wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()
    def RenameMp3File(self):
        global GlobalLastRenameFileResult
        self.StopMusic()
        time.sleep(2)
        file_to_check_and_rename = os.path.join(os.getcwd(), "downloads\\temp."+self.ext)
        if(os.path.isfile(file_to_check_and_rename)):
            os.system('rename "'+file_to_check_and_rename+'" "'+self.temp_future_filename+'"')
            GlobalLastRenameFileResult = 1
            return 1
        else:
            if(not self.parent.check_continuous_play.GetValue()):
                self.ShowMessageCantBeDownload()
            GlobalLastRenameFileResult = 0
            return 0
    def StopMusic(self):
        if(self.parent.IfAutoPlay()==1):
            os.startfile("no sound\\no.mp3", 'open')
            os.startfile("no sound\\no.mp4", 'open')
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
class HistoryStuff():
    def __init__(self,parent):
        self.parent = parent
        self.history_list = list()
        self.in_history_mode = 0
        self.index = 0
        self.if_all_prepearings_done = 0
    def AllPrepearingsDone(self):
        return self.if_all_prepearings_done
    def SetAllPrepearingsDone(self):
        self. if_all_prepearings_done = 1
    def UnsetAllPrepearingsDone(self):
        self. if_all_prepearings_done = 0
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
        myfile = open("all_played_videos.txt", "w")
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
            self.index = self.GetSizeOfHistory()-1
        else:
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
        with open("all_played_videos.txt", "a") as myfile:
            myfile.write(log+'\n')
    def ReadHistoryFromFile(self):
        self.parent.statusbar.SetStatusText("Reading history from file...",1)
        content = list()
        with open("./all_played_videos.txt") as f:
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
class MyFrame(wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, title):
        self.IfVideoTrigger = 0
        self.remaining_time_in_seconds_for_timer_data = 0
        self.MyYouTubeSearcherObj = MyYouTubeSearcher(self)
        self.HistoryStuffObj = HistoryStuff(self)
        self.MyImageToolsObj = ImageTools(self)
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
        # Create the menubar
        self.menuBar = wx.MenuBar()
        # and a menu
        self.fileMenu = wx.Menu()
        self.searchMenu = wx.Menu()
        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        quit_menu_item = wx.MenuItem(self.fileMenu, self.APP_EXIT, '&Quit')
        quit_menu_item.SetBitmap(wx.Bitmap('exit.png'))
        self.fileMenu.AppendItem(quit_menu_item)

        self.random_search_menu_checkbox = self.searchMenu.Append(wx.ID_ANY, 'Random search', 'Random search', kind=wx.ITEM_CHECK)
        self.search_for_list_menu_checkbox = self.searchMenu.Append(wx.ID_ANY, 'Search for list', 'Search for list', kind=wx.ITEM_CHECK)
        self.searchMenu.Check(self.random_search_menu_checkbox.GetId(), False)
        self.searchMenu.Check(self.search_for_list_menu_checkbox.GetId(), False)

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.OnTimeToClose, id=self.APP_EXIT)
        self.Bind(wx.EVT_MENU, self.OnStartHistoryMode, id=self.APP_HISTORY)
        self.Bind(wx.EVT_MENU, self.OnRecommendButtonPressed, id=self.APP_RECOMMEND)


        # and put the menu on the menubar
        self.menuBar.Append(self.fileMenu, "&File")
        self.menuBar.Append(self.searchMenu, "&Search options")

        self.SetMenuBar(self.menuBar)

        # TOOLBAR
        self.toolbar = self.CreateToolBar()
        delete_downloads_tool = self.toolbar.AddLabelTool(self.APP_DELETE_DOWNLOADS, 'Delete Downloads', wx.Bitmap('delete_downloads.png'))
        self.Bind(wx.EVT_TOOL, self.OnDeleteDownloads, delete_downloads_tool)
        open_in_browser_tool = self.toolbar.AddLabelTool(self.APP_OPEN_IN_BROWSER, 'Open In Browser', wx.Bitmap('open_in_browser.png'))
        self.Bind(wx.EVT_TOOL, self.OnOpenInBrowser, open_in_browser_tool)
        recommend_tool = self.toolbar.AddLabelTool(self.APP_RECOMMEND, "Recommend for you", wx.Bitmap('recommend.png'))
        self.Bind(wx.EVT_TOOL, self.OnRecommendButtonPressed, recommend_tool)
        history_tool = self.toolbar.AddLabelTool(self.APP_HISTORY, 'History', wx.Bitmap('history.png'))
        self.Bind(wx.EVT_TOOL, self.OnStartHistoryMode, history_tool)
        show_and_hide_info_tool = self.toolbar.AddLabelTool(self.APP_SHOW_AND_HIDE_INFO, 'Show And Hide Info Tool', wx.Bitmap('info.png'))
        self.Bind(wx.EVT_TOOL, self.OnShowAndHideInfoTool, show_and_hide_info_tool)
        play_embed_tool = self.toolbar.AddLabelTool(self.APP_PLAY_EMBED, 'Play in IFrame', wx.Bitmap('play_embed.png'))
        self.Bind(wx.EVT_TOOL, self.OnPlayEmbed, play_embed_tool)
        clarifai_search_tool = self.toolbar.AddLabelTool(self.APP_CLARIFAI_SEARCH, 'Clarifai search', wx.Bitmap('clarifai_search.png'))
        self.Bind(wx.EVT_TOOL, self.OnSearchByThumbnailButton, clarifai_search_tool)
        open_downloads_tool = self.toolbar.AddLabelTool(self.APP_OPEN_DOWNLOADS, 'Open downloads', wx.Bitmap('downloads_icon.png'))
        self.Bind(wx.EVT_TOOL, self.OnOpenDownloads, open_downloads_tool)
        add_to_history_tool = self.toolbar.AddLabelTool(self.APP_ADD_TO_HISTORY, 'Add to history', wx.Bitmap('add_to_history.png'))
        self.Bind(wx.EVT_TOOL, self.AddCurrentVideoToHistory, add_to_history_tool)




        self.toolbar.Realize()
        self.toolbar.SetBackgroundColour("RGB(220,220,220)")
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
        self.main_image_thumb = wx.StaticBitmap(self.panel, -1, wx.Bitmap("no.png", wx.BITMAP_TYPE_ANY), size=(320, 240))
        self.check_continuous_play = wx.CheckBox(self.panel, label = 'continuous',pos = (10,10))
        self.title_description_static_text = wx.StaticText(self.panel, -1, "  Description", size=(200, 20))
        self.title_description_static_text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.description_static_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE,size=(287, 342),pos=(5,5))
        self.channel_btn = wx.Button(self.panel, -1, "Open channel")
        self.likes_gauge = wx.Gauge(self.panel, range=100, size=(200, 30))
        self.like_static_image = wx.StaticBitmap(self.panel, -1, wx.Bitmap("like.png", wx.BITMAP_TYPE_ANY), size=(30, 27))
        self.dislike_static_image = wx.StaticBitmap(self.panel, -1, wx.Bitmap("dislike.png", wx.BITMAP_TYPE_ANY), size=(30, 27))
        self.copy_link_btn = wx.Button(self.panel, -1, "Copy link")

        # GRID OF THUMBNAILS
        self.sBitMaps = list()
        self.sBitMaps.append(wx.StaticBitmap(self.panel, -1, wx.Bitmap("no_small.png", wx.BITMAP_TYPE_ANY), size=(120, 90)))
        self.sBitMaps[0].Bind(wx.EVT_LEFT_DOWN, lambda event: self.OnClickThumbnail(0))
        self.sBitMaps[0].Bind(wx.EVT_ENTER_WINDOW, lambda event: self.OnHoverThumbnail(0))
        self.sBitMaps[0].Bind(wx.EVT_LEAVE_WINDOW, self.OnExitThumbnail)
        self.sBitMaps.append(wx.StaticBitmap(self.panel, -1, wx.Bitmap("no_small.png", wx.BITMAP_TYPE_ANY), size=(120, 90)))
        self.sBitMaps[1].Bind(wx.EVT_LEFT_DOWN, lambda event: self.OnClickThumbnail(1))
        self.sBitMaps[1].Bind(wx.EVT_ENTER_WINDOW, lambda event: self.OnHoverThumbnail(1))
        self.sBitMaps[1].Bind(wx.EVT_LEAVE_WINDOW, self.OnExitThumbnail)
        self.sBitMaps.append(wx.StaticBitmap(self.panel, -1, wx.Bitmap("no_small.png", wx.BITMAP_TYPE_ANY), size=(120, 90)))
        self.sBitMaps[2].Bind(wx.EVT_LEFT_DOWN, lambda event: self.OnClickThumbnail(2))
        self.sBitMaps[2].Bind(wx.EVT_ENTER_WINDOW, lambda event: self.OnHoverThumbnail(2))
        self.sBitMaps[2].Bind(wx.EVT_LEAVE_WINDOW, self.OnExitThumbnail)
        self.sBitMaps.append(wx.StaticBitmap(self.panel, -1, wx.Bitmap("no_small.png", wx.BITMAP_TYPE_ANY), size=(120, 90)))
        self.sBitMaps[3].Bind(wx.EVT_LEFT_DOWN, lambda event: self.OnClickThumbnail(3))
        self.sBitMaps[3].Bind(wx.EVT_ENTER_WINDOW, lambda event: self.OnHoverThumbnail(3))
        self.sBitMaps[3].Bind(wx.EVT_LEAVE_WINDOW, self.OnExitThumbnail)
        self.sBitMaps.append(wx.StaticBitmap(self.panel, -1, wx.Bitmap("no_small.png", wx.BITMAP_TYPE_ANY), size=(120, 90)))
        self.sBitMaps[4].Bind(wx.EVT_LEFT_DOWN, lambda event: self.OnClickThumbnail(4))
        self.sBitMaps[4].Bind(wx.EVT_ENTER_WINDOW, lambda event: self.OnHoverThumbnail(4))
        self.sBitMaps[4].Bind(wx.EVT_LEAVE_WINDOW, self.OnExitThumbnail)
        self.sBitMaps.append(wx.StaticBitmap(self.panel, -1, wx.Bitmap("no_small.png", wx.BITMAP_TYPE_ANY), size=(120, 90)))
        self.sBitMaps[5].Bind(wx.EVT_LEFT_DOWN, lambda event: self.OnClickThumbnail(5))
        self.sBitMaps[5].Bind(wx.EVT_ENTER_WINDOW, lambda event: self.OnHoverThumbnail(5))
        self.sBitMaps[5].Bind(wx.EVT_LEAVE_WINDOW, self.OnExitThumbnail)

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
        self.filter_sizer.Add(self.check_show_only_HD,flag=wx.ALIGN_CENTER | wx.ALL | wx.EXPAND,border=5)
        self.full_info_sizer.Add(self.full_info_sizer_subsizer_2, 0, wx.TOP, 0)
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
        self.sizer4.Add(self.next_page_btn, 0, wx.LEFT, 135)
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

        self.DrawInterfaceLines()
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
        webbrowser.open("index.html")
    def OnHoverGauge(self,evt):
        global GlobalVideoIdForRelated
        if self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()!=0 or GlobalVideoIdForRelated!="" or self.HistoryStuffObj.GetSizeOfHistory()!=0:
            info_for_showing = ""
            if(len(self.MyYouTubeSearcherObj.full_data_info["items"])>0):
                    likes = int(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["likeCount"])
                    likes = intWithCommas(likes)
                    info_for_showing+="likes: "+likes+" "
                    dislikes = int(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["dislikeCount"])
                    dislikes = intWithCommas(dislikes)
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
        global GlobalVideoIdForRelated
        if(GlobalVideoIdForRelated==""):
            return self.MyYouTubeSearcherObj.GetCurrentVideoId()
        else:
            return GlobalVideoIdForRelated
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
                a=0
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
        global GlobalVideoIdForRelated
        if self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()!=0 or GlobalVideoIdForRelated!="" or self.HistoryStuffObj.GetSizeOfHistory()!=0:
            if(len(self.MyYouTubeSearcherObj.full_data_info["items"])>0):
                self.description_static_text.SetValue(self.MyYouTubeSearcherObj.full_data_info["items"][0]["snippet"]["description"])
                likes = float(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["likeCount"])
                dislikes = float(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["dislikeCount"])
                if(((likes+dislikes)/100)!=0):
                    self.likes_gauge.SetValue(likes/((likes+dislikes)/100))
                else:
                    self.likes_gauge.SetValue(0)
            self.channel_btn.Enable()
            copy_button_thread = threading.Thread(target=self.CopyButtonThread)
            copy_button_thread.start()
        else:
            self.channel_btn.Disable()
            self.copy_link_btn.Disable()
    def OnOpenChannel(self,evt):
        global GlobalVideoIdForRelated
        if self.MyYouTubeSearcherObj.GetNumberOfFoundVideos()!=0 or GlobalVideoIdForRelated!="" or self.HistoryStuffObj.GetSizeOfHistory()!=0:
            if(len(self.MyYouTubeSearcherObj.full_data_info["items"])>0):
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
        if self.HistoryStuffObj.CheckIfInHistoryMode() and GlobalVideoIdForRelated == "" and self.HistoryStuffObj.AllPrepearingsDone():
            dlg = wx.MessageDialog(None, 'Item will be deleted from history.', 'Delete?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION )
            result = dlg.ShowModal()
            if result == wx.ID_NO:
                return
            self.HistoryStuffObj.DeleteCurrentItem()
            self.RefreshSongInfo()
    def OnHoverMainThumbnail(self,evt):
        global GlobalVideoIdForRelated
        if self.HistoryStuffObj.CheckIfInHistoryMode() and GlobalVideoIdForRelated == "" and self.HistoryStuffObj.AllPrepearingsDone():
            self.main_image_thumb.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
            self.MyImageToolsObj.MergeTwoImagesToMerged("file.png","trash.png")
            self.main_image_thumb.SetBitmap(wx.Bitmap("merged.png",wx.BITMAP_TYPE_ANY))
        else:
            self.main_image_thumb.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        if not ((self.MyYouTubeSearcherObj.number_of_found_videos == 0) and (GlobalVideoIdForRelated=="") and (self.HistoryStuffObj.GetSizeOfHistory() == 0)):
            self.statusbar.SetStatusText(self.MyYouTubeSearcherObj.GetTitleFromId(""))
    def OnExitMainThumbnail(self,evt):
        if self.HistoryStuffObj.CheckIfInHistoryMode():
            self.main_image_thumb.SetBitmap(wx.Bitmap("file.png",wx.BITMAP_TYPE_ANY))
        self.statusbar.SetStatusText("")
    def OnRecommendButtonPressed(self,evt):
        global GlobalVideoIdForRelated
        GlobalVideoIdForRelated = self.MyYouTubeSearcherObj.RelateFromHistoryRecommenderObj.GetRecommendedVideoId()
        if(GlobalVideoIdForRelated!=""):
            self.RefreshSongInfo()
        self.playbtn.Enable()
        self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,True)
        self.toolbar.EnableTool(self.APP_PLAY_EMBED,True)
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
        self.HistoryStuffObj.UnsetAllPrepearingsDone()
        self.toolbar.EnableTool(self.APP_HISTORY,False)
        self.smartbtn.Disable()
        global GlobalVideoIdForRelated
        GlobalVideoIdForRelated = ""
        global GlobalIfNowDownloading
        if(GlobalIfNowDownloading==0):
            self.playbtn.Enable()
            self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,True)
            self.toolbar.EnableTool(self.APP_PLAY_EMBED,True)
        self.HistoryStuffObj.history_list = self.HistoryStuffObj.ReadHistoryFromFile()
        self.HistoryStuffObj.EnableDisableHistoryMode(1)
        self.RefreshPrevAndNextButtons()
        self.smartbtn.Enable()
        self.toolbar.EnableTool(self.APP_HISTORY,True)
        self.HistoryStuffObj.SetAllPrepearingsDone()
    def OnStartHistoryMode(self,evt):
        t = threading.Thread(target = self.OnStartHistoryModeThread)
        t.start()
    def OnOpenDownloads(self,evt):
        os.startfile(os.getcwd()+"./downloads")
    def UnloadRelatedThumbs(self):
        for bitmap in self.sBitMaps:
            bitmap.SetBitmap(wx.Bitmap("no_small.png",wx.BITMAP_TYPE_ANY))
    def RefreshRelatedThumbs(self):
        ids = self.MyYouTubeSearcherObj.GetRelatedIds(None)
        i = 0
        self.UnloadRelatedThumbs()
        for my_id in ids:
            if i > 5:
                break
            img_address_local = "./related_images/"+my_id+"-"+str(self.related_thumbnails_current_indexes[i])+".jpg"
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
            img_address_local = "./related_images/"+ids[bitmapId]+"-"+str(k)+".jpg"
            self.related_thumbnails_current_indexes[bitmapId] = k
            if os.path.isfile(img_address_local):
                self.sBitMaps[bitmapId].SetBitmap(wx.Bitmap(img_address_local,wx.BITMAP_TYPE_ANY))
            for i in range(100):
                time.sleep(0.01)
                if(not self.related_thumbnail_updater_thread_is_running):
                    self.related_thumbnail_updater_thread_is_stopped = 1
                    return

    def OnHoverThumbnail(self, id):
        ids = self.MyYouTubeSearcherObj.GetRelatedIds(None)
        if(len(ids)>id):
            self.statusbar.SetStatusText(self.MyYouTubeSearcherObj.GetTitleFromId(ids[id]))
            self.related_thumbnail_id_updater_thread = id
            self.RunRelatedThumbnailsLoopUpdaterThread()
    def OnExitThumbnail(self,evt):
        self.related_thumbnail_updater_thread_is_running = 0
        self.statusbar.SetStatusText("")
    def OnClickThumbnail(self, id):
        global GlobalVideoIdForRelated
        ids = self.MyYouTubeSearcherObj.GetRelatedIds(None)
        if(len(ids)>id):
            GlobalVideoIdForRelated = ids[id]
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
        global GlobalVideoIdForRelated
        GlobalVideoIdForRelated = ""
        self.HistoryStuffObj.EnableDisableHistoryMode(0)
        self.text.SetLabel("Searching...")
        self.duration_info.SetLabel("unavailable")
        if(self.random_search_menu_checkbox.IsChecked()) and evt!="related_is_called":
            self.MyYouTubeSearcherObj.GetRandomWord()
        self.MyYouTubeSearcherObj.SetIndex(1)
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
            self.UnloadRelatedThumbs()
            self.text.SetLabel("No Results!")
            self.statusbar.SetStatusText('Nothing Found...',1)
            self.toolbar.EnableTool(self.APP_OPEN_IN_BROWSER,False)
            self.toolbar.EnableTool(self.APP_CLARIFAI_SEARCH,False)
            self.playbtn.Disable()
            self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,False)
            self.toolbar.EnableTool(self.APP_PLAY_EMBED,False)
            return None
        self.RefreshSongInfo()
        global GlobalIfNowDownloading
        if(GlobalIfNowDownloading==0):
            self.playbtn.Enable()
            self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,True)
            self.toolbar.EnableTool(self.APP_PLAY_EMBED,True)

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
        global GlobalVideoIdForRelated
        GlobalVideoIdForRelated = ""
        self.RefreshSongInfo()
        self.RefreshPrevAndNextButtons()
    def ChangeIndex(self,new_index):
        if self.HistoryStuffObj.CheckIfInHistoryMode():
            self.HistoryStuffObj.SetIndex(int(new_index))
        else:
            self.MyYouTubeSearcherObj.SetIndex(int(new_index))
        global GlobalVideoIdForRelated
        GlobalVideoIdForRelated = ""
        self.RefreshSongInfo()
        self.RefreshPrevAndNextButtons()
    def NextSong(self, evt):
        if self.HistoryStuffObj.CheckIfInHistoryMode():
            if_last = self.HistoryStuffObj.IncrementIndex()
        else:
            if_last = self.MyYouTubeSearcherObj.IncrementIndex()
        global GlobalVideoIdForRelated
        GlobalVideoIdForRelated = ""
        self.RefreshSongInfo()
        self.RefreshPrevAndNextButtons()
        return if_last
    def RefreshSongInfo(self):
        global GlobalVideoIdForRelated
        self.UnloadRelatedThumbs()
        self.main_image_thumb.SetBitmap(wx.Bitmap("no.png",wx.BITMAP_TYPE_ANY))
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
        img_downloaded = self.MyImageToolsObj.ResizeImage("file.jpg",(320,240))
        self.MyYouTubeSearcherObj.CreateHtmlWithIFrameForCurrentVideo()
        if(GlobalVideoIdForRelated != ""):
            self.main_title_static_text.SetLabel("Related Video")
        else:
            self.main_title_static_text.SetLabel(self.current_main_title)
        if(self.MyYouTubeSearcherObj.GetTitleFromId("")=="Deleted Video"):
            self.NextSong("")
            return
        self.text.SetLabel(self.MyYouTubeSearcherObj.GetTitleFromId(""))
        self.text.Wrap(300)
        views_count = intWithCommas(int(self.MyYouTubeSearcherObj.full_data_info["items"][0]["statistics"]["viewCount"]))
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
            #self.panel.SetBackgroundColour(self.MyImageToolsObj.GetAvgColorOfAnImage("file.png",150))
            #self.panel.Refresh()
            self.main_image_thumb.SetBitmap(wx.Bitmap("file.png",wx.BITMAP_TYPE_ANY))
        else:
            #self.panel.SetBackgroundColour(self.MyImageToolsObj.GetAvgColorOfAnImage("no.png",150))
            #self.panel.Refresh()
            self.main_image_thumb.SetBitmap(wx.Bitmap("no.png",wx.BITMAP_TYPE_ANY))
        self.toolbar.EnableTool(self.APP_OPEN_IN_BROWSER,True)
        self.toolbar.EnableTool(self.APP_CLARIFAI_SEARCH,True)
        if(self.info_shown):
            self.RefreshAdditionalInformation()
    def RunTimer(self):
        global GlobalLastRenameFileResult
        title = self.MyYouTubeSearcherObj.temp_future_filename
        dots = ""
        if(len(title)>30):
            dots = "..."
        if(GlobalLastRenameFileResult):
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
        global GlobalIfNowDownloading
        GlobalIfNowDownloading = 1
        self.check_auto_play.Disable()
        self.playbtn.Disable()
        self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,False)
        self.toolbar.EnableTool(self.APP_PLAY_EMBED,False)
        self.check_mp4_or_mp3.Disable()
        self.check_hight_quality.Disable()
        self.toolbar.EnableTool(self.APP_DELETE_DOWNLOADS,False)
        self.MyYouTubeSearcherObj.DownloadFile()
        self.check_auto_play.Enable()
        self.playbtn.Enable()
        self.toolbar.EnableTool(self.APP_ADD_TO_HISTORY,True)
        self.toolbar.EnableTool(self.APP_PLAY_EMBED,True)
        self.check_mp4_or_mp3.Enable()
        self.check_hight_quality.Enable()
        self.toolbar.EnableTool(self.APP_DELETE_DOWNLOADS,True)
        GlobalIfNowDownloading = 0
    def AddCurrentVideoToHistory(self,event):
        url = self.MyYouTubeSearcherObj.GetWatchUrl()
        self.HistoryStuffObj.AppendToHistoryFile(url)
        self.ShowMessageSavedToHistory()
    def ShowMessageSavedToHistory(self):
        dlg = wx.MessageDialog(self.panel,"Video has been saved to your history!", "Video added", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    def OnOpenInBrowser(self,event):
        webbrowser.open_new(url)
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "YouTube Music - David Georiev - v2.70")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True

if __name__ == "__main__":
    MyApp(redirect=False).MainLoop()

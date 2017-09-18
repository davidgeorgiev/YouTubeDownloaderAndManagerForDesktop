import yr_constants
from random import shuffle

class RelateFromHistoryRecommender():
    def __init__(self,parent):
        self.base_random_video_id = ""
        self.currentRecommendVideoId = ""
        self.parent = parent
    def AnalyzeHistoryFileAndGetRandomVideo(self):
        content = list()
        with open(yr_constants.FILENAME_HISTORY) as f:
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

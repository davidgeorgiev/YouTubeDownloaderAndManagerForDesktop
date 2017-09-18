import httplib2
import sys
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
import yr_constants
import os.path

class MyOAuthManager():
    def __init__(self,parent):
        self.parent = parent
        self.ReAuthenticate()
        self.history_playlist_id_filename = yr_constants.FILENAME_HISTORY_PLAYLIST
        self.user_playlists = self.get_user_playlists()
    def ReAuthenticate(self):
        self.youtube = self.get_authenticated_service()
    def get_authenticated_service(self):
        argparser.add_argument("--videoid", default="L-oNKK1CrnU", help="ID of video to like.")
        args = argparser.parse_args()
        flow = flow_from_clientsecrets(yr_constants.CLIENT_SECRETS_FILE,scope=yr_constants.YOUTUBE_READ_WRITE_SCOPE,message=yr_constants.MISSING_CLIENT_SECRETS_MESSAGE)

        storage = Storage(yr_constants.FILENAME_AUTHENTICATE_INFO_JSON)
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage, args)

        return build(yr_constants.YOUTUBE_API_SERVICE_NAME, yr_constants.YOUTUBE_API_VERSION,http=credentials.authorize(httplib2.Http()))
    def CreateHistoryPlaylistIfNotCreated(self):
        if(not os.path.isfile(self.history_playlist_id_filename)):
            playlists_insert_response = self.youtube.playlists().insert(
              part="snippet,status",
              body=dict(
                snippet=dict(
                  title="History playlist - "+strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                  description="Youtube manager and downloader playlist"
                ),
                status=dict(
                  privacyStatus="private"
                )
              )
            ).execute()

            history_playlist_id_file = open(self.history_playlist_id_filename,"w")
            history_playlist_id_file.write(playlists_insert_response["id"])
            history_playlist_id_file.close()
    def GetMyHistoryPlaylistId(self):
        with open(self.history_playlist_id_filename) as f:
            content = f.readlines()
        return content[0]
    def add_video_to_playlist(self,videoID,playlistID):
        try:
            add_video_request= self.youtube.playlistItems().insert(part="snippet",body={'snippet': {'playlistId': playlistID,'resourceId': {'kind': 'youtube#video','videoId': videoID}}, 'position': '0'}).execute()
            return 1
        except:
            self.parent.statusbar.SetStatusText("can't add video to playlist!")
            return 0
    def LikeAVideo(self,videoId,like_or_dislike):
        self.youtube.videos().rate(id=videoId,rating=like_or_dislike).execute()
    def add_subscription(self, channel_id):
        add_subscription_response = self.youtube.subscriptions().insert(part='snippet',body=dict(snippet=dict(resourceId=dict(channelId=channel_id)))).execute()

        return add_subscription_response["snippet"]["title"]
    def get_user_playlists(self):
        playlists = list()
        get_lists_response = self.youtube.channels().list(part='contentDetails',mine='true').execute()
        for playlist in get_lists_response["items"][0]["contentDetails"]["relatedPlaylists"]:
            playlists.append([playlist,get_lists_response["items"][0]["contentDetails"]["relatedPlaylists"][playlist]])
        return playlists
    def get_favorites_playlist_id(self):
        for playlist in self.user_playlists:
            if(playlist[0] == "favorites"):
                return playlist[1]

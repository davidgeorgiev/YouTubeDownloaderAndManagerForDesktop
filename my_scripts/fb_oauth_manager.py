# Facebook SDK
import facebook
import os
class FacebookOAuthManager():
    def __init__(self,parent,app_id,app_secret,tooken,extended_tooken_filename):
        self.parent = parent
        self.facebook_graph = None
        self.app_id = app_id
        self.app_secret = app_secret
        self.tooken = tooken
        self.extended_tooken_filename = extended_tooken_filename
    def ExtendUserTooken(self):
        if not os.path.isfile(self.extended_tooken_filename):
            facebook_graph = facebook.GraphAPI(self.tooken)
            long_token = facebook_graph.extend_access_token(self.app_id,self.app_secret)
            out_file = open(self.extended_tooken_filename,"w")
            out_file.write(long_token["access_token"])
            out_file.close()
    def InitFacebookGraphWithExtendedTooken(self):
        with open(self.extended_tooken_filename) as f:
            lines = f.readlines()
        self.facebook_graph = facebook.GraphAPI(lines[0])
    def MakeAPost(self,content,url):
        result = 0
        try:
            result = self.facebook_graph.put_object(parent_object="me",connection_name="feed",message=content,link=url)
        except:
            pass
        if(result):
            return 1
        else:
            return 0

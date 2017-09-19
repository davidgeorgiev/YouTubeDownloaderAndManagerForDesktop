'''import requests
import facebook
import json
facebook_secret = "237804aea683910e67b993d1b8c18dad"
fb_app_id = "117361628954371"

class FacebookOAuthManager():
    def __init__(self,parent):
        self.parent = parent
    def Example(self):
        content = requests.get('https://graph.facebook.com/oauth/access_token?grant_type=client_credentials&client_id='+fb_app_id+'&client_secret='+facebook_secret)
        my_dict = json.loads(str(content.text))
        print my_dict["access_token"].split("|")[1]

        token = my_dict["access_token"]
        print token

        graph = facebook.GraphAPI(access_token="EAACEdEose0cBAK6uIHDZBE2i8xXZCqTGGlB5lkepeiZB6NXIQaAdwHyHbHVvHIyZCTx5rJjYZAEYlm1oaUmqh3F3wH9FAtZAvM0u2mFWz3ZB6D0fW6aR75LgAbyxPsOA7zc7I0r7AaV1eJZCCkZBJW6MLa2QV0Yqu0a64AqIa2yEwcJemd63CeDZAdDaQjEt1tZA9dK2B5tVVOmUQZDZD",version="2.1")

        profile = graph.get_object("me")
        print profile
        friends = graph.get_connections("me", "friends")
        friend_list = [friend['name'] for friend in friends['data']]

        print friend_list

        graph.put_object(
   parent_object="me",
   connection_name="feed",
   message="This is a great website. Everyone should visit it.",
   link="https://www.facebook.com")

if __name__ == "__main__":
    FB = FacebookOAuthManager(None)
    FB.Example()
'''
'''
import web
from facebook import GraphAPI
from urlparse import parse_qs


def TryMe():
    url = ('/', 'index')

    app_id = "117361628954371"
    app_secret = "237804aea683910e67b993d1b8c18dad"
    post_login_url = "http://0.0.0.0:8080/"

    user_data = web.input(code=None)

    if not user_data.code:
        dialog_url = ( "http://www.facebook.com/dialog/oauth?" +
                                   "client_id=" + app_id +
                                   "&redirect_uri=" + post_login_url +
                                   "&scope=publish_stream" )

        return "<script>top.location.href='" + dialog_url + "'</script>"
    else:
        graph = GraphAPI()
        response = graph.get(
            path='oauth/access_token',
            client_id=app_id,
            client_secret=app_secret,
            redirect_uri=post_login_url,
            code=code
        )
        data = parse_qs(response)
        graph = GraphAPI(data['access_token'][0])
        graph.post(path = 'me/feed', message = 'Your message here')

TryMe()
'''
'''
import facebook
app_id = 117361628954371
app_secret = "237804aea683910e67b993d1b8c18dad"
oath_access_token = facebook.utils.get_application_access_token(app_id, app_secret)
print oath_access_token
'''
'''
import urllib
import urlparse
import time
import web

FACEBOOK_APP_ID = "117361628954371"
FACEBOOK_APP_SECRET = "237804aea683910e67b993d1b8c18dad"

def path_url():
    return "http://localhost:8080" + web.ctx.fullpath

class FBManager:
    def login(self):
        data = web.input()
        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri=path_url())
        if data.code is None:
            return web.seeother('http://www.facebook.com/dialog/oauth?' + urllib.urlencode(args) + '&scope=' + urllib.quote('user_likes,friends_likes,user_birthday,friends_birthday'))
        args['code'] = data.code
        args['client_secret'] = FACEBOOK_APP_SECRET

        response = urlparse.parse_qs(urllib.urlopen("https://graph.facebook.com/oauth/access_token?" + urllib.urlencode(args)).read())
        access_token = response["access_token"][-1]
        profile = json.load(urllib.urlopen("https://graph.facebook.com/me?fields=id,name,birthday,location,gender&" + urllib.urlencode(dict(access_token=access_token))))
        web.setcookie('fb_userid', str(profile['id']), expires=time.time() + 7 * 86400)
        web.setcookie('fb_username', str(profile['name']), expires=time.time() + 7 * 86400)

    def logout(self):
        web.setcookie('fb_userid', '', expires=time.time() - 86400)
        web.setcookie('fb_username', '', expires=time.time() - 86400)

if __name__ == "__main__":
    FB = FBManager()
    FB.login()
'''
'''
import urllib
import json
FACEBOOK_APP_ID = "117361628954371"
FACEBOOK_APP_SECRET = "237804aea683910e67b993d1b8c18dad"
def fetch_app_access_token(fb_app_id, fb_app_secret):
    resp = urllib.urlopen('https://graph.facebook.com/oauth/access_token?client_id=' +fb_app_id + '&client_secret=' + fb_app_secret +'&grant_type=client_credentials')
    my_dict = json.loads(str(resp.read()))
    token = my_dict["access_token"]
    print token
if __name__ == "__main__":
    fetch_app_access_token(FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
'''

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

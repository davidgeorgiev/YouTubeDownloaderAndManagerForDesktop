from clarifai.rest import ClarifaiApp


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

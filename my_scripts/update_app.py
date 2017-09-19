import urllib
import zipfile
import os
import shutil

class AppUpdater():
    def __init__(self,parent):
        self.parent = parent
        self.path_to_zip_file = "master.zip"
        self.from_path = "master\\YouTubeDownloaderAndManagerForDesktop-master"
    def DownloadZip(self):
        urllib.urlretrieve ("https://github.com/davidgeorgiev/YouTubeDownloaderAndManagerForDesktop/archive/master.zip", self.path_to_zip_file)
    def ExtractZip(self):
        zip_ref = zipfile.ZipFile(self.path_to_zip_file, 'r')
        zip_ref.extractall(os.getcwd()+"\\master")
        zip_ref.close()
    def MoveAndReplace(self):
        for filename in os.listdir(os.getcwd()+"\\my_scripts"):
            if(filename!="api_keys.py"):
                os.unlink(os.getcwd()+"\\my_scripts\\"+filename)
        for filename in os.listdir(os.getcwd()+"\\GUI_Images"):
            os.unlink(os.getcwd()+"\\GUI_Images\\"+filename)
        #if(os.path.isdir(os.getcwd()+"\\my_scripts")):
            #os.rmdir(os.getcwd()+"\\my_scripts")
        if(os.path.isfile("YR.pyw")):
            os.unlink("YR.pyw")
        if(os.path.isfile("README.md")):
            os.unlink("README.md")
        for filename in os.listdir(os.getcwd()+"\\master\\YouTubeDownloaderAndManagerForDesktop-master\\my_scripts\\"):
            os.rename(os.getcwd()+"\\master\\YouTubeDownloaderAndManagerForDesktop-master\\my_scripts\\"+filename,os.getcwd()+"\\my_scripts\\"+filename)
        for filename in os.listdir(os.getcwd()+"\\master\\YouTubeDownloaderAndManagerForDesktop-master\\GUI_Images\\"):
            os.rename(os.getcwd()+"\\master\\YouTubeDownloaderAndManagerForDesktop-master\\GUI_Images\\"+filename,os.getcwd()+"\\GUI_Images\\"+filename)
        os.rename(os.getcwd()+"\\master\\YouTubeDownloaderAndManagerForDesktop-master\\YR.pyw",os.getcwd()+"\\YR.pyw")

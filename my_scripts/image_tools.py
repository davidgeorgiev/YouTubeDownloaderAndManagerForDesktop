import yr_constants
import Image
import os
import os.path

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
        background.save(yr_constants.FILENAME_MERGED_IMAGE, "PNG")

    def GetAvgColorOfAnImage(self,img_url,sum_val):
        im = Image.open(yr_constants.FILENAME_MAIN_THUMBNAIL_IMAGE)
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

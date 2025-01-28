from logging import raiseExceptions
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib.pyplot as plt
#import ImageUtils
import os
import subprocess

import base64
from io import BytesIO


BLANK = "blank"

class ImageUtils(object):

    img = None
    BLANK = "blank"

    def __init__(self, img, size=None) -> None:
        self.setImage(img, size)

    def setImage(self, img, size=None):
        if type(img) == str and img == BLANK:
            if type(size) is not tuple:
                raise ValueError("size for a blank image must be defined")

            self.img = Image.new("RGB", size, (255, 255, 255))

            return

        if type(img) == np.ndarray:
            self.img = Image.fromarray(img)
        elif type(img) == Image.Image:
            self.img = img
        elif type(img) == ImageUtils:
            self.img = img.getImage()
        else:
            self.img = Image.open(img)

    def getWidth(self):
        return self.img.size[0]

    def getHeight(self):
        return self.img.size[1]

    def getSize(self):
        return self.img.size

    def getDraw(self):
        return ImageDraw.Draw(self.img)        
        
    
    def convertToGrayScale(self):
        self.img = Image.fromarray(cv2.cvtColor(np.asarray(self.img.convert('L')), cv2.COLOR_GRAY2RGB))
        
        return self

    def bgr_to_rgb(self):
        self.img = Image.fromarray(cv2.cvtColor(np.asarray(self.img), cv2.COLOR_BGR2RGB))

    def convertToRGB(self):
        if self.img.mode == 'L':
            self.img = Image.fromarray(cv2.cvtColor(np.asarray(self.img), cv2.COLOR_GRAY2RGB))
        elif self.img.mode == 'RGBA':
            self.img = Image.fromarray(cv2.cvtColor(np.asarray(self.img), cv2.COLOR_RGBA2RGB))

        return self

    def applyGaussianBlur(self):
        self.img = self.img.filter(ImageFilter.GaussianBlur(10))

    def applyBackground(self, color):     
        if len(self.img.split()) == 4:
            background = Image.new("RGB", self.img.size, color=color)
            background.paste(self.img, mask=self.img.split()[3]) # 3 is the alpha channel

            self.img = background

    def drawText(self, text: str, font:ImageFont, text_color):
        W, H = (self.getWidth(), self.getHeight())

        self.draw = ImageDraw.Draw(self.img)  

        _, _, w, h = self.draw.textbbox((0, 0), text, font=font)

        self.draw.text(((W-w)/2, (H-h)/2), text, font=font, fill=text_color)

        return self.img

    def sharpenImage(self):
        sharpen_filter = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharped_img = cv2.filter2D(np.array(self.img), -1, sharpen_filter)

        self.setImage(sharped_img)

    def convertToBrightnessScale(self, file_name: str):
        img = np.array(self.img)

        for row in range(self.getHeight()):
            for col in range(self.getWidth()):
                bg = self.img.getpixel((col, row))

                luminosity = self.calculateLuminosity(bg)
                
                img[row][col] = (luminosity, luminosity, luminosity)

        
        self.save(file_name, img)

    def removeBackground(self):
        self.save("tmp/_____temp_____.png", override=True)
        
        subprocess.call('backgroundremover -i "tmp/_____temp_____.png" -a -ae 15 -o "tmp/_____temp_____.png.bgremoved.png"')

        self.setImage('tmp/_____temp_____.png.bgremoved.png')

        #os.remove("_____temp_____.png")
        #os.remove("_____temp_____.png.bgremoved.png")

    def fill(self, color):
        img = np.array(self.img)

        for row in range(self.getHeight()):
            for col in range(self.getWidth()):
                img[row][col] = color

        self.setImage(img)

    def getCannyEdges(self):
        return ImageUtils(cv2.Canny(np.asarray(self.img),100,200))


    def copyColoredPixelsFrom(self, mask, destinationColoredPixel=(255,255,255), follow_luminosity=False):
        if mask.getWidth() != self.getWidth() and mask.getHeight() != self.getHeight():
            raise ValueError("input and current image dimensions should be same")
        
        mask_width = mask.getWidth()
        mask_height = mask.getHeight()

        # input = np.asarray(input)
        img = np.array(self.img)

        
        # restriction for only painting upto 3 points
        painted = False
        paint_limit = 2
        paint_num = 0

        
        scale = 256 / 8


        #for row in tqdm(range(mask_height)):
        for row in range(mask_height):
            for col in range(mask_width):
                mask_color = mask.getImage().getpixel((col, row))
                if self.img.getpixel((col, row)) != destinationColoredPixel:
                    # if it is destination pixel then copy
                    img[row][col] = mask_color
                    #print(mask.getImage().getpixel((col, row)), img[row][col], mask.getImage().mode)


                    if painted == True:
                        paint_num += 1
                    
                    if paint_num >= paint_limit:
                        painted = False
                        paint_num = 0

                elif follow_luminosity:
                    # if it's not a destination pixel,
                    # then it means it's a white pixel and we need to shrink
                    # black pixels depending on the mask's pixel

                    #mask_bg = mask.getImage().getpixel((col, row))

                    if self.calculateLuminosity(mask_color) >  scale * 7:
                        continue

                    if painted == False:
                        increasing_paths = self.findLuminosityIncreasingPath((col, row), mask)

                        for path in increasing_paths:
                            if path == "left":
                                try:
                                    for i in range(col, col + paint_limit):
                                        bg = mask.getImage().getpixel((i, row))
                            
                                        optimalFilling = self.calculateOptimalFilling(bg)
                                        img = self.fillSurroundingPoints(
                                            row, 
                                            i, 
                                            _range=optimalFilling[0], 
                                            color=optimalFilling[1], 
                                            axis="x", 
                                            img=img,
                                            mask=mask)
                                except IndexError:
                                    pass
                            elif path == "right":
                                try:
                                    for i in range(col - paint_limit, col):
                                        bg = mask.getImage().getpixel((i, row))
                            
                                        optimalFilling = self.calculateOptimalFilling(bg)
                                        img = self.fillSurroundingPoints(
                                            row, 
                                            i, 
                                            _range=optimalFilling[0], 
                                            color=optimalFilling[1], 
                                            axis="x", 
                                            img=img,
                                            mask=mask)
                                except IndexError:
                                    pass
                            elif path == "up":
                                try:
                                    for i in range(row - paint_limit, row):
                                        bg = mask.getImage().getpixel((col, i))
                            
                                        optimalFilling = self.calculateOptimalFilling(bg)
                                        img = self.fillSurroundingPoints(
                                            i, 
                                            col, 
                                            _range=optimalFilling[0], 
                                            color=optimalFilling[1], 
                                            axis="y", 
                                            img=img,
                                            mask=mask)
                                except IndexError:
                                    pass
                            elif path == "down":
                                try:
                                    for i in range(row, row + paint_limit):
                                        bg = mask.getImage().getpixel((col, i))
                            
                                        optimalFilling = self.calculateOptimalFilling(bg)
                                        img = self.fillSurroundingPoints(
                                            i, 
                                            col, 
                                            _range=optimalFilling[0], 
                                            color=optimalFilling[1], 
                                            axis="y", 
                                            img=img,
                                            mask=mask)
                                except IndexError:
                                    pass

                        paint_num += 1
                    
                    if paint_num >= paint_limit:
                        painted = True
                        paint_num = 0

        self.setImage(img)

    def calculateLuminosity(self, bg):
        return 0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2] # per ITU-R BT.709

    def calculateOptimalFilling(self, bg):
        luma = self.calculateLuminosity(bg)
        brightness_scale = 256 / 8
        
        
        range, color, axis = (0, 0), (0, 0, 0), "x"
        follow_limit = 0 
        

        if luma <= brightness_scale * 1:
            range = 1, 1
            color = (0, 0, 0)
            axis = "x"
            follow_limit = 1
        elif luma <= brightness_scale * 2:
            range = 1, 1
            color = (0, 0, 0)
            axis ="xy"
            follow_limit = 2
        elif luma <= brightness_scale * 3:
            range = 1, 1
            color = (0, 0, 0)
            axis="x"
            follow_limit = 2
        elif luma <= brightness_scale * 4:
            range = 1, 1
            color = (0, 0, 0)
            axis="x"
            follow_limit = 2
        elif luma <= brightness_scale * 5:
            range = 1, 1
            color = (0, 0, 0)
            axis="x"   
            follow_limit = 2
        elif luma <= brightness_scale * 6:
            range = 1, 1
            color = (0, 0, 0)
            axis="x"


        return range, bg, axis, follow_limit

    def areAllElemSame(self, arr):
        if arr == []:
            return False

        return arr.count(arr[0])==len(arr)

    def isLuminosityIncreasing(self, luminos):
        if luminos == []:
            return False

        last_lumas = [256]
        for luma in luminos:
            if luma <= last_lumas[-1]:
                last_lumas.append(luma)
            else:
                return False

        return self.areAllElemSame(last_lumas[1:]) == False

    def isLuminosityDecreasing(self, luminos):
        if luminos == []:
            return False

        last_lumas = [0]
        for luma in luminos:
            if luma >= last_lumas[-1]:
                last_lumas.append(luma)
            else:
                return False

        return self.areAllElemSame(last_lumas[1:]) == False

    def findLuminosityIncreasingPath(self, coordinates, img=None):
        if img == None:
            print("using image")
            img = self

        x = coordinates[0]
        y = coordinates[1]
        
        try:
            left = [self.calculateLuminosity(img.getImage().getpixel((_x, y))) for _x in range(x, x + 4)]
        except IndexError:
            left = []
        try:
            right = [self.calculateLuminosity(img.getImage().getpixel((_x, y))) for _x in range(x - 4, x)]
        except IndexError:
            right = []

        try:
            up = [self.calculateLuminosity(img.getImage().getpixel((x, _y))) for _y in range(y - 4, y)]
        except IndexError:
            up = []
        
        try:
            down = [self.calculateLuminosity(img.getImage().getpixel((x, _y))) for _y in range(y, y + 4)]
        except IndexError:
            down = []

        result = []
        
        if self.isLuminosityIncreasing(left): result.append("left")
        if self.isLuminosityDecreasing(right): result.append("right")
        if self.isLuminosityDecreasing(up): result.append("up")
        if self.isLuminosityIncreasing(down): result.append("down")

        return result


    def fillSurroundingPoints(self, y, x, _range, color=(255, 255, 255), axis="xy", img=None, mask=None, follow=True, follow_limit=2, follow_num=0):
        if img is None:
            img = self.img

        # print(followMask)

        if mask == None:
            return img
        
        if follow_num >= follow_limit:
            return img

        col = x
        row = y

        for i in range(y - _range[0], y + _range[0]):
            for j in range(x - _range[0], x + _range[1]):
                try:
                    img[i][j] = color
                except IndexError:
                    pass    

        paths = self.findLuminosityIncreasingPath((col, row), mask)

        limit = 1

        for path in paths:
            if path == "left":
                try:
                    for i in range(col, col + limit):
                        bg = mask.getImage().getpixel((i, row))
            
                        optimalFilling = self.calculateOptimalFilling(bg)
                        img = self.fillSurroundingPoints(
                            row, 
                            i, 
                            _range=optimalFilling[0], 
                            color=optimalFilling[1], 
                            axis="x", 
                            img=img,
                            mask=mask,
                            follow_limit=follow_limit-1,
                            follow_num=follow_num+1)
                except IndexError:
                    pass
            elif path == "right":
                try:
                    for i in range(col - limit, col):
                        bg = mask.getImage().getpixel((i, row))
            
                        optimalFilling = self.calculateOptimalFilling(bg)
                        img = self.fillSurroundingPoints(
                            row, 
                            i, 
                            _range=optimalFilling[0], 
                            color=optimalFilling[1], 
                            axis="x", 
                            img=img,
                            mask=mask,
                            follow_limit=follow_limit-1,
                            follow_num=follow_num+1)
                except IndexError:
                    pass
            elif path == "up":
                try:
                    for i in range(row - limit, row):
                        bg = mask.getImage().getpixel((col, i))
            
                        optimalFilling = self.calculateOptimalFilling(bg)
                        img = self.fillSurroundingPoints(
                            i, 
                            col, 
                            _range=optimalFilling[0], 
                            color=optimalFilling[1], 
                            axis="y", 
                            img=img,
                            mask=mask,
                            follow_limit=follow_limit-1,
                            follow_num=follow_num+1)
                except IndexError:
                    pass
            elif path == "down":
                try:
                    for i in range(row, row + limit):
                        bg = mask.getImage().getpixel((col, i))
            
                        optimalFilling = self.calculateOptimalFilling(bg)
                        img = self.fillSurroundingPoints(
                            i, 
                            col, 
                            _range=optimalFilling[0], 
                            color=optimalFilling[1], 
                            axis="y", 
                            img=img,
                            mask=mask,
                            follow_limit=follow_limit-1,
                            follow_num=follow_num+1)
                except IndexError:
                    pass

        return img
                
    def getImage(self) -> Image:
        return self.img

    def getImageArray(self) -> np.ndarray: 
        return np.array(self.img)

    def show(self):
        # plt.imshow(self.img, interpolation="bilinear")
        # plt.axis("off")
        # plt.gcf().tight_layout(pad=0, rect=(0, 0, 0, 0))
        # plt.show()

        cv2.imshow('image', self.getImageArray())
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        

    def save(self, name="outputs/output.png", img=None, override=False, addTopBorder=True):
        if img is None:
            img = self.img

        if not override:
            count = 0
            while os.path.exists(name):
                name = name.split(".")[0].split("_")[0] + "_" + str(count + 1) +  ".png"
                count += 1

        if addTopBorder:
            new_size = (self.getWidth(), self.getHeight() + 8)

            new_im = Image.new("RGB", new_size, (255,255,255))
            box = tuple((n - o) for n, o in zip(new_size, self.getSize()))
            new_im.paste(img, box)

            img = new_im

        plt.imshow(img, interpolation="bilinear")
        plt.axis("off")
        plt.savefig(name, bbox_inches='tight', pad_inches=0, dpi=600)


    def returnBase64(self):
        buffered = BytesIO()
        self.img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue())
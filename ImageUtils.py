from logging import raiseExceptions
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib.pyplot as plt
import ImageUtils
import os
import subprocess
from tqdm import tqdm

BLANK = "blank"

class ImageUtils(object):

    img = None

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
        else:
            self.img = Image.open(img)

    def getWidth(self):
        return self.img.size[0]

    def getHeight(self):
        return self.img.size[1]

    def getSize(self):
        return self.img.size
    
    def convertToGrayScale(self):
        self.img = Image.fromarray(cv2.cvtColor(np.asarray(self.img.convert('L')), cv2.COLOR_GRAY2RGB))
        
        return self.img

    def applyGaussianBlur(self):
        self.img = self.img.filter(ImageFilter.GaussianBlur(10))

    def applyBackground(self, color):     
        if len(self.img.split()) == 4:
            background = Image.new("RGB", self.img.size, color=color)
            background.paste(self.img, mask=self.img.split()[3]) # 3 is the alpha channel

            self.img = background

    def drawText(self, text: str, font:ImageFont, text_color):
        self.draw = ImageDraw.Draw(self.img)        
        self.draw.text((0, 0), text, font=font, fill=text_color)

        return self.img

    def convertToBrightnessScale(self, file_name: str):
        img = np.array(self.img)

        for row in range(self.getHeight()):
            for col in range(self.getWidth()):
                bg = self.img.getpixel((col, row))

                luminosity = self.calculateLuminosity(bg)
                
                img[row][col] = (luminosity, luminosity, luminosity)

        
        self.save(file_name, img)

    def removeBackground(self):
        self.save("_____temp_____.png")
        
        subprocess.call('backgroundremover -i _____temp_____.png -a -ae 15 -o _____temp_____.png.bgremoved.png')

        self.setImage('_____temp_____.png.bgremoved.png')

        #os.remove("_____temp_____.png")
        #os.remove("_____temp_____.png.bgremoved.png")


    def copyColoredPixelsFrom(self, input: ImageUtils, destinationColoredPixels=(0,0,0)):
        if input.getWidth() != self.getWidth() and input.getHeight() != self.getHeight():
            raise ValueError("input and current image dimensions should be same")
        
        input_width = input.getWidth()
        input_height = input.getHeight()

        # input = np.asarray(input)
        img = np.array(self.img)


        # plt.imshow(img)
        # plt.show()

        x = 0
        painted_x = False
        
        max_range = 4

        for row in tqdm(range(self.getHeight())):
            for col in range(self.getWidth()):
                if self.img.getpixel((col, row)) == destinationColoredPixels:
                    if input.getImage().getpixel((col, row)) != (255, 255, 255):
                        bg = input.getImage().getpixel((col, row))
                        luma = 0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2] # per ITU-R BT.709
                    
                    
                        #img[row][col] = input.getImage().getpixel((col, row))
                        
                        img[row][col] = (0, 0, 0)
                        


                    if painted_x == True:
                        x += 1
                    
                    if x >= max_range:
                        painted_x = False
                        x = 0
                else:
                    if painted_x == False:
                        bg = input.getImage().getpixel((col, row))
                        
                        optimalFilling = self.calculateOptimalFilling(bg)
                        img = self.fillSurroundingPoints(
                            row, 
                            col, 
                            _range=optimalFilling[0], 
                            color=optimalFilling[1], 
                            axis=optimalFilling[2], 
                            img=img,
                            mask=input,
                            follow_limit=4 if optimalFilling[3] == None else optimalFilling[3])


                        x += 1

                    if x >= max_range:
                        painted_x = True
                        x = 0
 

        self.setImage(img)

    def calculateLuminosity(self, bg):
        return 0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2] # per ITU-R BT.709

    def calculateOptimalFilling(self, bg):
        luma = self.calculateLuminosity(bg)
        brightness_scale = 256 / 11
        
        
        range, color, axis = None, None, None
        follow_limit = None 
        

        if luma <= brightness_scale * 1:
            range = 1, 1
            color = (0, 0, 0)
            axis = "x"
            follow_limit = 1
        elif luma <= brightness_scale * 2:
            range = 2, 2
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
            follow_limit = 4
        elif luma <= brightness_scale * 5:
            range = 1, 1
            color = (0, 0, 0)
            axis="x"   
            follow_limit = 6
        elif luma <= brightness_scale * 6:
            range = 1, 1
            color = (255, 255, 255)
            axis="x"
            range = 0, 0
        elif luma <= brightness_scale * 7:
            range = 1, 1
            color = (255, 255, 255) 
            axis="x"
            range = 0, 0
        elif luma <= brightness_scale * 8:
            range = 2, 2
            color = (255, 255, 255) 
            axis="x"
            range = 1, 1
        elif luma <= brightness_scale * 9:
            range = 1, 1
            color = (255, 255, 255) 
            axis="xy"
        elif luma <= brightness_scale * 10:
            range = 1, 1
            color = (255, 255, 255) 
            axis="xy"
            follow_limit = 2
        elif luma <= brightness_scale * 11:
            range = 2, 2
            color = (255, 255, 255) 
            axis="xy"
            follow_limit = 1

        return range, color, axis, follow_limit

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
            img = self.img

        x = coordinates[0]
        y = coordinates[1]
        
        try:
            left = [self.calculateLuminosity(img.getImage().getpixel((_x, y))) for _x in range(x, x + 3)]
        except IndexError:
            left = []
        try:
            right = [self.calculateLuminosity(img.getImage().getpixel((_x, y))) for _x in range(x - 3, x)]
        except IndexError:
            right = []

        try:
            up = [self.calculateLuminosity(img.getImage().getpixel((x, _y))) for _y in range(y - 3, y)]
        except IndexError:
            up = []
        
        try:
            down = [self.calculateLuminosity(img.getImage().getpixel((x, _y))) for _y in range(y, y + 3)]
        except IndexError:
            down = []

        result = []
        
        if self.isLuminosityIncreasing(left): result.append("left")
        if self.isLuminosityDecreasing(right): result.append("right")
        if self.isLuminosityDecreasing(up): result.append("up")
        if self.isLuminosityIncreasing(down): result.append("down")

        return result


    def fillSurroundingPoints(self, y, x, _range, color=(255, 255, 255), axis="xy", img=None, mask=None, follow=True, follow_limit=4, follow_num=0):
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

        for path in paths:
            if path == "left":
                try:
                    for i in range(col, col + 3):
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
                    for i in range(col - 3, col):
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
                    for i in range(row - 3, row):
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
                    for i in range(row, row + 3):
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

    def show(self):
        plt.imshow(self.img, interpolation="bilinear")
        plt.show()

    def save(self, name="output.png", img=None):
        if img is None:
            img = self.img

        plt.imshow(img, interpolation="bilinear")
        plt.axis("off")
        plt.savefig(name, bbox_inches='tight', pad_inches=0)
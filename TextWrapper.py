from argparse import ArgumentError
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from tqdm import tqdm

import cv2

from ImageUtils2 import ImageUtils

class TextWrapper(object):
    """ Helper class to wrap text in lines, based on given text, font
        and max allowed line width.
    """

    def __init__(self, text, font: ImageFont, outline_font : ImageFont, image: ImageUtils, line_height, letter_spacing=5, fill="black", space_width="auto"):
        self.text = text
        self.text_lines = [
            ' '.join([w.strip() for w in l.split(' ') if w])
            for l in text.split('\n')
            if l
        ]
        self.font : ImageFont = font
        self.outline_font : ImageFont = outline_font
        self.max_width = image.getWidth()
        self.max_height = image.getHeight()
        self.image = image
        # if self.image.getImageArray().ndim == 2:
        #     self.image.convertToRGB()

        self.image_array = np.array(self.image.getImage())
        self.imageDraw = image.getDraw()
        self.fill = fill
        self.line_height = line_height
        self.letter_spacing = letter_spacing

        self.draw = ImageDraw.Draw(
            Image.new(
                mode='RGB',
                size=(100, 100)
            )
        )

        if space_width == "auto":
            self.space_width = self.draw.textsize(
                text=' ',
                font=self.fontl
            )[0] - 3
        else:
            self.space_width = space_width

    def get_text_width(self, text):
        return self.draw.textsize(
            text=text,
            font=self.font
        )[0]

    def calculate_max_chars_for_image(self, progressFunc):
        pos = (0, 0)

        length = 0
        progress = 0
        for line in self.text_lines:
            for word in line:
                if pos[1] >= self.max_height:
                    break
                
                if progressFunc is not None:
                    progressFunc(int((progress*100) / len(line)))


                word_width = self.get_text_width(word)
    
                if word == " ":
                    word_width = self.space_width

                expected_width = pos[0] + self.space_width + word_width

                if expected_width <= self.max_width:
                    # word fits in line
                    length += 1

                    pos = np.add(pos, (word_width + (self.letter_spacing if word != " " else 0), 0))
                else:
                    # word doesn't fit in line
                    length += 1

                    # if first character is space, then skip it
                    if word == ' ':
                        continue

                    pos = (0, pos[1] + self.line_height)
                    pos = (word_width + self.letter_spacing, pos[1])    

                progress += 1     

        return length

    def drawText(self, based_on_luminosity=False, mask: Image = None, progressFunc = None):
        if based_on_luminosity and not mask:
            raise ArgumentError(mask, "mask should be provided for tracing")

        pos = (0, 0)

        progress = 0
        total = self.calculate_max_chars_for_image(progressFunc)
        for line in self.text_lines:
            for word in tqdm(line, total=total):
                if pos[1] >= self.max_height:
                    break

                if progressFunc is not None:
                    progressFunc(int((progress*100) / total))


                word_width = self.get_text_width(word)
    
                if word == " ":
                    word_width = self.space_width

                expected_width = pos[0] + self.space_width + word_width

                if expected_width <= self.max_width:
                    # word fits in line

                    patch = self.drawFollowingDarkness(word, pos, word_width, self.line_height, mask, based_on_luminosity)
                    self.image_array[pos[1]:pos[1] + self.line_height, pos[0]:pos[0] + word_width] = patch

                    pos = np.add(pos, (word_width + (self.letter_spacing if word != " " else 0), 0))
                else:
                    # word doesn't fit in line

                    # if first character is space, then skip it
                    if word == ' ':
                        continue

                
                    pos = (0, pos[1] + self.line_height)

                    patch = self.drawFollowingDarkness(word, pos, word_width, self.line_height, mask, based_on_luminosity)
                    self.image_array[pos[1]:pos[1] + self.line_height, pos[0]:pos[0] + word_width] = patch

                    pos = (word_width + self.letter_spacing, pos[1])         

                progress += 1

        if based_on_luminosity:
            self.image.setImage(self.image_array)
    
        return self.image           
                    

    def drawFollowingDarkness(self, letter, pos, text_width, text_height, mask, follow_luminosity=True):
        x = pos[0]
        y = pos[1]

        mask = np.array(mask)

        #cv2.imshow("ImageWindow", mask)

        # cut out patch under word box
        _patch = mask[y:y + text_height, x:x + text_width]

        blank_patch = ImageUtils(ImageUtils.BLANK, (_patch.shape[1], _patch.shape[0]))
        
        
        grid_rows = 2
        grid_cols = 3

        inner_grid_box_height = int(text_height / grid_rows)
        inner_grid_box_width = int(text_width / grid_cols)

        for row in range(1, grid_rows + 1):
            for col in range(1, grid_cols + 1):
                inner_patch = _patch[(inner_grid_box_height * (row - 1)):(inner_grid_box_height * row), (inner_grid_box_width * (col - 1)):(inner_grid_box_width * col)]

                # check if the text is within the bounds of the image
                reshape = inner_patch.reshape(-1, 3)
                if not np.all(reshape.shape):
                    return tuple((255, 255, 255)) # default color for text that is out of bounds

                _inner_patch = cv2.cvtColor(inner_patch, cv2.COLOR_RGB2GRAY)
                _inner_patch = cv2.cvtColor(_inner_patch, cv2.COLOR_GRAY2RGB)
                _reshape = _inner_patch.reshape(-1, 3)

                common_color_in_patch = tuple(np.mean(_reshape, axis=0))
                luminosity = self.calculateLuminosity(common_color_in_patch)

                inner_patch = cv2.cvtColor(inner_patch, cv2.COLOR_RGB2BGR)
                reshape = inner_patch.reshape(-1, 3)

                scale = 256 / 8

                blank_patch = ImageUtils(blank_patch)
                _blank_patch = blank_patch

                og_font = self.font
                fake_font_used = False

                if luminosity < scale:
                    self.font = self.font.font_variant(size=self.font.size)
                    self.font.set_variation_by_name('Black')
                    fake_font_used = True
                elif luminosity < scale * 2:
                    self.font = self.font.font_variant(size=self.font.size + 1)
                    self.font.set_variation_by_name('ExtraBold')
                    fake_font_used = True
                elif luminosity < scale * 3:
                    self.font = self.font.font_variant(size=self.font.size + 1)
                    self.font.set_variation_by_name('Bold')
                    fake_font_used = True
                elif luminosity < scale * 4:
                    self.font = self.font.font_variant(size=self.font.size)
                    self.font.set_variation_by_name('SemiBold')
                    fake_font_used = True
                elif luminosity < scale * 5:
                    self.font.set_variation_by_name('Medium')
                elif luminosity < scale * 6:
                    self.font = self.font.font_variant(size=self.font.size - 1)
                    self.font.set_variation_by_name('Regular')
                    fake_font_used = True
                elif luminosity < scale * 7:
                    self.font = self.font.font_variant(size=self.font.size - 1)
                    self.font.set_variation_by_name('Regular')
                    fake_font_used = True
                elif luminosity < scale * 8:
                    self.font = self.font.font_variant(size=self.font.size)
                    self.font.set_variation_by_name('ExtraLight')
                    fake_font_used = True




                _blank_patch.drawText(letter, self.font, (0, 0, 0))



                if fake_font_used:
                   self.font = og_font
                   fake_font_used = False

                #_blank_patch.sharpenImage()

                blank_patch = blank_patch.getImageArray()
                _blank_patch = _blank_patch.getImageArray()


                blank_patch[(inner_grid_box_height * (row - 1)):(inner_grid_box_height * row), (inner_grid_box_width * (col - 1)):(inner_grid_box_width * col)] = _blank_patch[(inner_grid_box_height * (row - 1)):(inner_grid_box_height * row), (inner_grid_box_width * (col - 1)):(inner_grid_box_width * col)]

        # if self.calculateLuminosity(np.mean(_patch.reshape(-1, 3), axis=0)) <= (256 / 11) * 10:
        #     test_patch = ImageUtils(blank_patch)
        #     test_patch.copyColoredPixelsFrom(ImageUtils(_patch), follow_luminosity=True)

        #     return test_patch.getImageArray()
        # else:
        #     return blank_patch

        reshape = _patch.reshape(-1, 3)
        common_color_in_patch = tuple(np.mean(reshape, axis=0))
        luminosity = self.calculateLuminosity(common_color_in_patch)


        # if luminosity <= 225:
        test_patch = ImageUtils(blank_patch)
        
        #test_patch.fill((0, 0, 0))
        test_patch.bgr_to_rgb()
        # cv2.imshow("ImageWindow", test_patch.getImageArray())
        # cv2.waitKey()
        test_patch.copyColoredPixelsFrom(ImageUtils(_patch), follow_luminosity=False)
        # cv2.imshow("ImageWindow", test_patch.getImageArray())
            # cv2.waitKey()
        # else:
            # test_patch = ImageUtils(blank_patch)
            # test_patch.fill((255, 255, 255))
            # test_patch.drawText(letter, self.outline_font, (0, 0, 0))
            # test_patch.copyColoredPixelsFrom(ImageUtils(_patch), follow_luminosity=False)

        


        return test_patch.getImageArray()        

    def drawTextBasedOnLuminosity(self):
        self.drawText(based_on_luminosity=True)


    def calculateLuminosity(self, color):
        return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2] # per ITU-R BT.709
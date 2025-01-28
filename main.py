import base64
import io
import os, sys, re, time, math
from TextWrapper import TextWrapper
from ImageUtils2 import ImageUtils, BLANK
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtWebChannel

from PyQt5.QtCore import QUrl, QObject, pyqtSignal, QThread

from PIL import ImageFont


# if getattr(sys, 'frozen', None):
#      basedir = sys._MEIPASS
# else:
#      basedir = os.path.dirname(__file__)


# get data directory (using getcwd() is needed to support running example in generated IPython notebook)
cwd = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()


WINDOW_WIDTH = 650
WINDOW_HEIGHT = 500

debug = False


class DrawWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def setup(self, text, font, outline_font, font_size, output_image, input_image):
        self.text = text
        self.font = font
        self.outline_font = outline_font
        self.font_size = font_size
        self.output_image = output_image
        self.input_image = input_image

    def run(self):
        # Here we pass the update_progress (uncalled!)
        # function to the long_running_function:
        #long_running_function(self.update_progress)
        tw = TextWrapper(self.text, self.font, self.outline_font, self.output_image, line_height=self.font_size, letter_spacing=1, fill="black", space_width=1)
        tw.drawText(based_on_luminosity=True, mask=self.input_image.getImage(), progressFunc=self.update_progress)

        print("finished")    
        self.finished.emit()

    def update_progress(self, percent):
        self.progress.emit(percent)


class App(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, name, width, height):
        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setApplicationDisplayName(name)

        
        QtWebEngineWidgets.QWebEngineView.__init__(self)        

        #self.web = QtWebEngineWidgets.QWebEngineView()
        self.web_channel = QtWebChannel.QWebChannel(self)
        self.page().setWebChannel(self.web_channel)
        self.web_channel.registerObject('WebChannel', self)
        self.loadFinished.connect(self.setupFonts)

    def load_url(self, url):
        self.load(QUrl(url))
        self.show()    

    def run_main_loop(self):
        sys.exit(self.app.exec_())

    def setupFonts(self):
        _fonts = [x.split(".")[0] for x in os.listdir(cwd + "/fonts/")]
        _fonts.sort()
        fonts = []
        for font in _fonts:
            if "outline" in font.lower():
                continue
            
            fonts.append(font)
        
        fonts = ["<option>"+x+"</option>" for x in fonts]

        fonts = "".join(fonts)

        self.page().runJavaScript('setupFonts("' + fonts + '")')

    @QtCore.pyqtSlot(str)
    def print(self, string):
        print(string)

    @QtCore.pyqtSlot(str, str, str, bool, str)
    def make_image(self, text, font_family, font_size, remove_background, image):
        print (text, font_family, font_size, math.floor(float(font_size)), remove_background)
        text = text * 50
        font_size = math.floor(float(font_size))

        input_image = ImageUtils(self.stringToImage(image))

        if remove_background:
            input_image.removeBackground() 
        
        input_image.convertToRGB()

        #input_image.show()


        print(input_image.getSize())

        self.output_image = ImageUtils(BLANK, (input_image.getWidth(), input_image.getHeight()))
        self.output_image.convertToRGB()

        font_path = os.path.join(cwd, "fonts", font_family + ".ttf")

        print(font_path)

        font = ImageFont.truetype(font_path, font_size)
        font.set_variation_by_name('Black')


        outline_font = cwd + "/fonts/LondrinaOutline.ttf"
        outline_font = ImageFont.truetype(outline_font, font_size)

        if debug:
            tw = TextWrapper(text, font, outline_font, self.output_image, line_height=font_size, letter_spacing=1, fill="black", space_width=1)
            tw.drawText(based_on_luminosity=True, mask=input_image.getImage())

            self.show_output_image()      

        if not debug:    
            self.thread = QThread()
            self.worker = DrawWorker()
            self.worker.setup(text, font, outline_font, font_size, self.output_image, input_image)

            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.show_output_image)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.update_progress)

            self.thread.start()



    def show_output_image(self):
        self.output_image.sharpenImage()

        self.page().runJavaScript("submit_btn.removeAttribute('disabled')")
        #self.output_image.show()
        self.page().runJavaScript("showImage(\"" + str(self.output_image.returnBase64().decode("utf-8")) + "\")") 
         
    @QtCore.pyqtSlot()
    def save_output_image(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')
        self.output_image.save(name, override=True)

    def update_progress(self, progress):
        self.page().runJavaScript("progressBar.value = %d;" % progress)



    # Take in base64 string and return cv image
    def stringToImage(self, base64_string):
        imgdata = re.sub('^data:image/.+;base64,', '', base64_string)
        imgdata = base64.b64decode(str(imgdata))
        img = io.BytesIO(imgdata)
        return img 

app = App("Text-to-Image", WINDOW_WIDTH, WINDOW_HEIGHT)
app.load_url(cwd.replace("\\", "/") + "/UI/ui.html")
app.run_main_loop()





# text = "There's no time for us. There's no place for us. What is this thing that builds our dreams, yet slips away from us. Who wants to live forever. Who wants to live forever. Oh ooo oh. There's no chance for us. It's all decided for us. This world has only one sweet moment set aside for us. Who wants to live forever, Who wants to live forever, Ooh. Who dares to love forever. Oh oo woh, when love must die. But touch my tears with your lips. Touch my world with your fingertips. And we can have forever, And we can love forever, Forever is our today. Who wants to live forever. Who wants to live forever. Forever is our today. Who waits forever anyway?"*150

# input = ImageUtils(cwd + '/inputs/people.jpg')
# #input.removeBackground()
# #input.applyBackground("white")
# input.convertToGrayScale()

# #input.show()

# image = ImageUtils(BLANK, (input.getWidth(), input.getHeight()))
# image.convertToGrayScale()


# font_path = cwd + "/fonts/grandstander/Grandstander-VariableFont_wght.ttf"
# font_size = 13

# font = ImageFont.truetype(font_path, font_size)
# font.set_variation_by_name('Black')

# tw = TextWrapper(text, font, image.getWidth(), image.getHeight(), image, line_height=font_size -2, letter_spacing=1, fill="black", space_width=1)
# tw.drawText(based_on_luminosity=True, mask=input.getImage())


# #image.copyColoredPixelsFrom(input)

# image.show()
# image.save()
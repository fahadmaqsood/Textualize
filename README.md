# Textualize
A tool that transforms images into text-based art by adjusting text density and font thickness to replicate the image visually. Users input both text and an image, and the app generates a readable text representation of the image. Built using image processing, text manipulation, and custom algorithms to create unique text art.

# Example output
![Click to see example image](https://i.imgur.com/P904SEc.jpeg)

# How to run?
After installing dependencies, simply execute `python main.py`.

This will launch the window like below:  
![Click to see the image](https://i.imgur.com/6nlcTTV.png)
  
You can add your own text and select your own image. Default font size might not look good, you will have to experiment to find the ideal size.

# How to compile into executable file?
`pyinstaller --onedir main.py --add-data="./UI/*;./UI/" --add-data="./fonts/*;./fonts/" --noconfirm --noconsole`

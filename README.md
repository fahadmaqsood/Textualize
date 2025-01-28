# Textualize
A tool that transforms images into text-based art by adjusting text density and font thickness to replicate the image visually. Users input both text and an image, and the app generates a readable text representation of the image. Built using image processing, text manipulation, and custom algorithms to create unique text art.

# Example output
![Click to see example image](https://i.imgur.com/P904SEc.jpeg)

# How to run?
After installing dependencies, simply execute `python main.py`.

# How to compile into executable file?
`pyinstaller --onedir main.py --add-data="./UI/*;./UI/" --add-data="./fonts/*;./fonts/" --noconfirm --noconsole`

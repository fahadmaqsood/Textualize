from ImageUtils2 import ImageUtils
import matplotlib.pyplot as plt

from skimage.transform import PiecewiseAffineTransform

transform = PiecewiseAffineTransform()



image = ImageUtils("C:\\Users\\ADMIN\\Downloads\\WhatsApp Image 2022-10-30 at 18.05.52.jpg")



edges = image.getCannyEdges().convertToGrayScale().convertToRGB().convertToGrayScale().getImageArray()

image = image.convertToGrayScale().convertToRGB().convertToGrayScale().getImageArray()


edges = edges[100:200, 100:200]
image = image[100:200, 100:200]



# estimation = transform.estimate(edges.getImageArray(), )

# print(estimation)
#image = image.getImageArray()

plt.subplot(121),plt.imshow(image,cmap = 'gray')
plt.title('Original Image'), plt.xticks([]), plt.yticks([])
plt.subplot(122),plt.imshow(edges,cmap = 'gray')
plt.title('Edge Image'), plt.xticks([]), plt.yticks([])
plt.show()


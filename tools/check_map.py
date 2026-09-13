import yaml
import cv2

with open('maps/building.yaml') as f:
    info = yaml.safe_load(f)

res = info['resolution']
origin = info['origin']

img = cv2.imread('maps/building.pgm', cv2.IMREAD_GRAYSCALE)
h, w = img.shape

# Convert 1.8, 1.8 to pixel coords
x_m = 1.8
y_m = 1.8

px = int((x_m - origin[0]) / res)
py = h - int((y_m - origin[1]) / res) # y is inverted in image coords usually

print(f"Pixel at {px}, {py} is {img[py, px]}")
# Check neighborhood
for i in range(-5, 6):
    for j in range(-5, 6):
        if img[py+i, px+j] < 200:
            print(f"Obstacle at {px+j}, {py+i}: {img[py+i, px+j]}")


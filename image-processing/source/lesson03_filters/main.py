from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import Image, display
from PIL import Image as PILImage


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


output = Path("output")
output.mkdir(exist_ok=True)
print("环境就绪")

import cv2

shapes = PILImage.open(data_path("images/shapes.png")).convert("RGB")
gray = shapes.convert("L")
hsv = shapes.convert("HSV")
gray_array = np.array(gray)
hsv_array = np.array(hsv)
print("灰度图模式：", gray.mode, "尺寸：", gray.size)
print("HSV 数组形状：", hsv_array.shape)
print("灰度均值：", round(float(gray_array.mean()), 1))
display(gray)


from PIL import ImageFilter

blurred = shapes.filter(ImageFilter.GaussianBlur(radius=4))
sharpened = shapes.filter(ImageFilter.UnsharpMask(radius=2, percent=180, threshold=3))
print("模糊半径：4")
print("锐化强度：180%")
print("模糊后均值：", round(float(np.array(blurred.convert("L")).mean()), 1))
print("锐化后均值：", round(float(np.array(sharpened.convert("L")).mean()), 1))


blue_mask = (hsv_array[:, :, 0] >= 140) & (hsv_array[:, :, 1] >= 80)
print("蓝色系像素占比：", round(float(blue_mask.mean() * 100), 1), "%")


kernel_blur = np.ones((5, 5), np.float32) / 25
kernel_edge = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], np.float32)

smoothed = cv2.filter2D(gray_array, -1, kernel_blur)
edges = cv2.filter2D(gray_array, -1, kernel_edge)
edges = np.clip(edges, 0, 255).astype(np.uint8)

fig, axes = plt.subplots(2, 2, figsize=(10, 7))
panels = [
    (gray_array, "灰度原图"),
    (blurred, "高斯模糊"),
    (sharpened, "锐化"),
    (edges, "边缘卷积核"),
]
for ax, (picture, title) in zip(axes.flat, panels):
    ax.imshow(picture, cmap="gray" if title != "锐化" else None)
    ax.set_title(title)
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "filters.png", dpi=110)
display(Image(filename=str(output / "filters.png")))
plt.close(fig)

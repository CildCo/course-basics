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

shapes = np.array(PILImage.open(data_path("images/shapes.png")).convert("RGB"))
gray = cv2.cvtColor(shapes, cv2.COLOR_RGB2GRAY)
edges = cv2.Canny(gray, 80, 160)
print("图像尺寸：", gray.shape)
print("边缘像素数：", int(np.count_nonzero(edges)))


contours, hierarchy = cv2.findContours(
    edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)
valid = [contour for contour in contours if cv2.contourArea(contour) > 500]
print("外轮廓数量：", len(contours))
print("面积大于 500 的轮廓：", len(valid))
for index, contour in enumerate(valid, 1):
    x, y, width, height = cv2.boundingRect(contour)
    print(
        f"轮廓{index}：面积={cv2.contourArea(contour):.0f} "
        f"边界=({x}, {y}, {width}, {height})"
    )


canvas = shapes.copy()
cv2.drawContours(canvas, valid, -1, (220, 40, 40), 3)
for contour in valid:
    x, y, width, height = cv2.boundingRect(contour)
    cv2.rectangle(canvas, (x, y), (x + width, y + height), (40, 140, 80), 2)

fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
axes[0].imshow(edges, cmap="gray")
axes[0].set_title("Canny 边缘")
axes[0].axis("off")
axes[1].imshow(canvas)
axes[1].set_title(f"外轮廓与边界框（{len(valid)} 个）")
axes[1].axis("off")
fig.tight_layout()
fig.savefig(output / "contours.png", dpi=110)
display(Image(filename=str(output / "contours.png")))
plt.close(fig)

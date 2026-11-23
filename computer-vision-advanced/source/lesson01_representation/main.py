import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import Image, display


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


output = Path("output")
output.mkdir(exist_ok=True)
print("输出目录已就绪")

from PIL import Image as PILImage

image = PILImage.open(data_path("images/scene.png"))
print("格式：", image.format)
print("尺寸（宽, 高）：", image.size)
print("颜色模式：", image.mode)
display(image)


pixels = np.array(image)
print("数组形状：", pixels.shape)
print("数据类型：", pixels.dtype)
print("最小值 / 最大值：", int(pixels.min()), int(pixels.max()))
print("左上角像素：", pixels[0, 0].tolist())
print("太阳中心像素：", pixels[85, 375].tolist())
print("草地像素：", pixels[330, 240].tolist())
print("内存占用：", pixels.nbytes, "字节")

for index, name in enumerate(["红", "绿", "蓝"]):
    print(f"{name}通道均值：{pixels[:, :, index].mean():.1f}")


fig, axes = plt.subplots(1, 4, figsize=(11, 3.2))
axes[0].imshow(pixels)
axes[0].set_title("原图")
for index, name in enumerate(["红", "绿", "蓝"]):
    axes[index + 1].imshow(pixels[:, :, index], cmap="gray")
    axes[index + 1].set_title(f"{name}通道")
for ax in axes:
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "channels.png", dpi=110)
display(Image(filename=str(output / "channels.png")))
plt.close(fig)


import cv2

rgb = np.array(image)
bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

print("RGB 左上角：", rgb[0, 0].tolist())
print("BGR 左上角：", bgr[0, 0].tolist())
print("HSV 左上角：", hsv[0, 0].tolist())
print("H 范围：", int(hsv[:, :, 0].min()), "到", int(hsv[:, :, 0].max()))
print("S 均值：", round(float(hsv[:, :, 1].mean()), 1))
print("V 均值：", round(float(hsv[:, :, 2].mean()), 1))

fig, axes = plt.subplots(1, 4, figsize=(11, 3.2))
axes[0].imshow(rgb)
axes[0].set_title("原图")
axes[1].imshow(hsv[:, :, 0], cmap="hsv")
axes[1].set_title("H 色调")
axes[2].imshow(hsv[:, :, 1], cmap="gray")
axes[2].set_title("S 饱和度")
axes[3].imshow(hsv[:, :, 2], cmap="gray")
axes[3].set_title("V 明度")
for ax in axes:
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "hsv.png", dpi=110)
display(Image(filename=str(output / "hsv.png")))
plt.close(fig)


lower = np.array([20, 120, 120])
upper = np.array([35, 255, 255])
mask = cv2.inRange(hsv, lower, upper)

print("命中像素：", int((mask > 0).sum()))
print("命中比例：", f"{(mask > 0).mean():.2%}")
rows, cols = np.where(mask > 0)
print("外接框（x1, y1, x2, y2）：", int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max()))

fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
axes[0].imshow(rgb)
axes[0].set_title("原图")
axes[1].imshow(mask, cmap="gray")
axes[1].set_title("HSV 颜色 mask")
highlight = rgb.copy()
highlight[mask == 0] = (highlight[mask == 0] * 0.25).astype(np.uint8)
axes[2].imshow(highlight)
axes[2].set_title("保留命中区域")
for ax in axes:
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "threshold.png", dpi=110)
display(Image(filename=str(output / "threshold.png")))
plt.close(fig)

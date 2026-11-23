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

gray = np.array(PILImage.open(data_path("images/gradient.png")).convert("L"))
hist, bin_edges = np.histogram(gray, bins=32, range=(0, 255))
print("像素总数：", gray.size)
print("最暗像素：", int(gray.min()))
print("最亮像素：", int(gray.max()))
print("前 5 个区间计数：", hist[:5].tolist())


fig, ax = plt.subplots(figsize=(8, 3.6))
ax.bar(bin_edges[:-1], hist, width=np.diff(bin_edges), align="edge", color="#4C78A8")
ax.set_title("灰度直方图：每个亮度区间有多少像素")
ax.set_xlabel("亮度")
ax.set_ylabel("像素数")
fig.tight_layout()
fig.savefig(output / "histogram.png", dpi=110)
display(Image(filename=str(output / "histogram.png")))
plt.close(fig)


binary = np.where(gray >= 128, 255, 0).astype(np.uint8)
otsu_value, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
print("固定阈值 128 的白色占比：", round(float((binary == 255).mean() * 100), 1), "%")
print("Otsu 自动阈值：", round(float(otsu_value), 1))
print("Otsu 白色占比：", round(float((otsu == 255).mean() * 100), 1), "%")


fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
for ax, picture, title, cmap in zip(
    axes,
    [gray, binary, otsu],
    ["灰度原图", "固定阈值 128", f"Otsu 阈值 {otsu_value:.0f}"],
    ["gray", "gray", "gray"],
):
    ax.imshow(picture, cmap=cmap, vmin=0, vmax=255)
    ax.set_title(title)
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "threshold.png", dpi=110)
display(Image(filename=str(output / "threshold.png")))
plt.close(fig)

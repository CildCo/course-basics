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

clean = np.array(PILImage.open(data_path("images/shapes.png")).convert("L"))
print("灰度图形状：", clean.shape)
print("像素范围：", int(clean.min()), "到", int(clean.max()))
print("平均灰度：", round(float(clean.mean()), 1))

rng = np.random.RandomState(7)
noisy = clean.copy()
count = int(noisy.size * 0.05)
rows = rng.randint(0, noisy.shape[0], count)
cols = rng.randint(0, noisy.shape[1], count)
noisy[rows, cols] = rng.choice([0, 255], count)
print("椒盐噪声比例：", f"{np.mean(noisy != clean):.2%}")


def psnr(reference, result):
    mse = np.mean((reference.astype(np.float32) - result.astype(np.float32)) ** 2)
    if mse == 0:
        return float("inf")
    return 10 * np.log10(255 ** 2 / mse)


mean_filtered = cv2.blur(noisy, (5, 5))
gauss_filtered = cv2.GaussianBlur(noisy, (5, 5), 0)
median_filtered = cv2.medianBlur(noisy, 5)

results = [
    ("均值滤波", mean_filtered),
    ("高斯滤波", gauss_filtered),
    ("中值滤波", median_filtered),
]
for name, result in results:
    print(f"{name} PSNR：{psnr(clean, result):.2f} dB")

fig, axes = plt.subplots(1, 5, figsize=(13, 3))
panels = [("干净图", clean), ("加噪图", noisy)] + results
for ax, (name, picture) in zip(axes, panels):
    ax.imshow(picture, cmap="gray", vmin=0, vmax=255)
    ax.set_title(name)
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "filters.png", dpi=110)
display(Image(filename=str(output / "filters.png")))
plt.close(fig)


gx = cv2.Sobel(clean, cv2.CV_32F, 1, 0, ksize=3)
gy = cv2.Sobel(clean, cv2.CV_32F, 0, 1, ksize=3)
magnitude = cv2.magnitude(gx, gy)
magnitude = np.clip(magnitude / magnitude.max() * 255, 0, 255).astype(np.uint8)
edges = cv2.Canny(clean, 60, 160)

print("Sobel 平均梯度：", round(float(magnitude.mean()), 1))
print("Canny 边缘像素：", int((edges > 0).sum()), f"({(edges > 0).mean():.2%})")

fig, axes = plt.subplots(1, 3, figsize=(10, 3.4))
axes[0].imshow(clean, cmap="gray", vmin=0, vmax=255)
axes[0].set_title("灰度图")
axes[1].imshow(magnitude, cmap="gray")
axes[1].set_title("Sobel 梯度幅值")
axes[2].imshow(edges, cmap="gray")
axes[2].set_title("Canny 边缘")
for ax in axes:
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "edges.png", dpi=110)
display(Image(filename=str(output / "edges.png")))
plt.close(fig)


blurred = cv2.GaussianBlur(clean, (5, 5), 0)
_, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
kernel = np.ones((5, 5), np.uint8)
opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
areas = sorted([cv2.contourArea(contour) for contour in contours], reverse=True)

print("Otsu 阈值后的前景占比：", f"{(binary > 0).mean():.2%}")
print("连通区域数量：", len(contours))
print("各区域面积：", [round(area, 1) for area in areas])

canvas = cv2.cvtColor(closed, cv2.COLOR_GRAY2RGB)
cv2.drawContours(canvas, contours, -1, (220, 70, 60), 2)

fig, axes = plt.subplots(1, 4, figsize=(12, 3.2))
axes[0].imshow(binary, cmap="gray")
axes[0].set_title("二值化")
axes[1].imshow(opened, cmap="gray")
axes[1].set_title("开运算")
axes[2].imshow(closed, cmap="gray")
axes[2].set_title("闭运算")
axes[3].imshow(canvas)
axes[3].set_title("轮廓")
for ax in axes:
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "morphology.png", dpi=110)
display(Image(filename=str(output / "morphology.png")))
plt.close(fig)

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

product = np.array(PILImage.open(data_path("images/product.png")).convert("RGB"))
height, width = product.shape[:2]
center = (width // 2, height // 2)
rotation = cv2.getRotationMatrix2D(center, 12, 0.9)
rotated = cv2.warpAffine(
    product, rotation, (width, height), borderValue=(255, 255, 255)
)
PILImage.fromarray(rotated).save(output / "rotated.png")
print("原图尺寸：", (width, height))
print("旋转后尺寸：", (rotated.shape[1], rotated.shape[0]))
print("旋转矩阵：")
print(np.round(rotation, 2))


source = np.float32([[300, 140], [520, 140], [520, 500], [300, 500]])
target = np.float32([[0, 0], [300, 0], [300, 500], [0, 500]])
perspective = cv2.getPerspectiveTransform(source, target)
warped = cv2.warpPerspective(
    product, perspective, (300, 500), borderValue=(255, 255, 255)
)
PILImage.fromarray(warped).save(output / "perspective.png")
print("透视变换后尺寸：", (warped.shape[1], warped.shape[0]))
print("目标四角：", target.astype(int).tolist())


small = cv2.resize(product, (400, 300), interpolation=cv2.INTER_AREA)
flipped = cv2.flip(small, 1)

fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
for ax, picture, title in zip(
    axes,
    [product, rotated, flipped],
    ["原图", "旋转并缩小", "缩放后水平翻转"],
):
    ax.imshow(picture)
    ax.set_title(title)
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "transform_compare.png", dpi=110)
display(Image(filename=str(output / "transform_compare.png")))
plt.close(fig)

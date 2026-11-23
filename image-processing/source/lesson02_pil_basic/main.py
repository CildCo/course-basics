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

original = PILImage.open(data_path("images/product.png")).convert("RGB")
print("原图尺寸：", original.size)
print("原图模式：", original.mode)
display(original)


box = (150, 100, 650, 500)
cropped = original.crop(box)
resized = cropped.resize((400, 300), PILImage.LANCZOS)
rotated = resized.rotate(15, expand=True)
print("裁剪后：", cropped.size)
print("缩放后：", resized.size)
print("旋转后：", rotated.size)
cropped.save(output / "product_cropped.png")
resized.save(output / "product_resized.png")
rotated.save(output / "product_rotated.png")


fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
for ax, picture, title in zip(
    axes,
    [original, cropped, rotated],
    ["原图", "裁剪", "缩放并旋转"],
):
    ax.imshow(picture)
    ax.set_title(f"{title} {picture.size}")
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "pil_steps.png", dpi=110)
display(Image(filename=str(output / "pil_steps.png")))
plt.close(fig)


original.save(output / "product_copy.jpg", quality=85)
original.save(output / "product_copy.png")
for name in ["product_copy.jpg", "product_copy.png"]:
    path = output / name
    print(f"{name}：{path.stat().st_size} 字节")

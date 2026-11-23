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

image = PILImage.open(data_path("images/gradient.png"))
print("格式：", image.format)
print("尺寸（宽, 高）：", image.size)
print("颜色模式：", image.mode)
display(image)


pixels = np.array(image)
print("数组形状：", pixels.shape)
print("数据类型：", pixels.dtype)
print("左上角像素 RGB：", pixels[0, 0].tolist())
print("中心像素 RGB：", pixels[300, 400].tolist())
print("右上角像素 RGB：", pixels[0, 799].tolist())
print("红色通道均值：", round(float(pixels[:, :, 0].mean()), 1))


fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
for ax, index, title in zip(axes, range(3), ["红色通道", "绿色通道", "蓝色通道"]):
    ax.imshow(pixels[:, :, index], cmap="gray", vmin=0, vmax=255)
    ax.set_title(f"{title}（灰度显示）")
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "channels.png", dpi=110)
display(Image(filename=str(output / "channels.png")))
plt.close(fig)

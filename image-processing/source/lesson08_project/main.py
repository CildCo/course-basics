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

from PIL import ImageDraw, ImageFont


def load_font(size):
    for name in ["msyh.ttc", "simhei.ttf", "arial.ttf"]:
        candidate = Path("C:/Windows/Fonts") / name
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def add_watermark(picture, text):
    layer = PILImage.new("RGBA", picture.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = load_font(26)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    width = right - left
    height = bottom - top
    x = picture.width - width - 20
    y = picture.height - height - 18
    draw.rounded_rectangle(
        (x - 10, y - 8, x + width + 10, y + height + 8),
        radius=6,
        fill=(0, 0, 0, 90),
    )
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 210))
    return PILImage.alpha_composite(picture.convert("RGBA"), layer).convert("RGB")


def clean_background(picture, threshold=235):
    array = np.array(picture.convert("RGB"))
    background = np.all(array >= threshold, axis=2)
    array[background] = (255, 255, 255)
    return PILImage.fromarray(array)


def fit_canvas(picture, size=600):
    picture = picture.copy()
    picture.thumbnail((size - 80, size - 80), PILImage.LANCZOS)
    canvas = PILImage.new("RGB", (size, size), (255, 255, 255))
    canvas.paste(
        picture,
        ((size - picture.width) // 2, (size - picture.height) // 2),
    )
    return canvas


print("处理函数已就绪")


import json

image_dir = data_path("images")
ready_dir = output / "products"
ready_dir.mkdir(parents=True, exist_ok=True)
records = []
for path in sorted(image_dir.glob("*.png")):
    with PILImage.open(path) as handle:
        original = handle.convert("RGB")
    cleaned = clean_background(original)
    ready = fit_canvas(cleaned, 600)
    ready = add_watermark(ready, "示例商品图")
    target = ready_dir / f"{path.stem}_ready.png"
    ready.save(target)
    records.append(
        {
            "source": path.name,
            "originalSize": list(original.size),
            "outputSize": list(ready.size),
            "bytes": target.stat().st_size,
        }
    )

report = {"targetSize": "600x600", "count": len(records), "items": records}
report_path = output / "report.json"
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))


with PILImage.open(data_path("images/product.png")) as handle:
    before = handle.convert("RGB")
after = PILImage.open(ready_dir / "product_ready.png").convert("RGB")

fig, axes = plt.subplots(1, 2, figsize=(10, 5))
axes[0].imshow(before)
axes[0].set_title(f"处理前 {before.size}")
axes[0].axis("off")
axes[1].imshow(after)
axes[1].set_title(f"处理后 {after.size}")
axes[1].axis("off")
fig.tight_layout()
fig.savefig(output / "comparison.png", dpi=110)
display(Image(filename=str(output / "comparison.png")))
plt.close(fig)
print("成品数量：", len(list(ready_dir.glob("*.png"))))
print("对比图字节：", (output / "comparison.png").stat().st_size)


print("报告文件：", report_path.name)
print("成品目录：", ready_dir.name)
print("报告条目：")
for row in report["items"]:
    print(
        f"{row['source']} {row['originalSize']} -> {row['outputSize']} "
        f"{row['bytes']} 字节"
    )

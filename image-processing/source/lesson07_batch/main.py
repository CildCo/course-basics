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

image_dir = data_path("images")
files = sorted(image_dir.glob("*.png"))
batch_dir = output / "batch"
batch_dir.mkdir(parents=True, exist_ok=True)
print("待处理图片：", len(files))
for path in files:
    with PILImage.open(path) as handle:
        picture = handle.convert("RGB")
    width, height = picture.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    square = picture.crop((left, top, left + side, top + side))
    square = square.resize((400, 400), PILImage.LANCZOS)
    target = batch_dir / f"{path.stem}_400.png"
    square.save(target)
    print(f"{path.name} -> {target.name} {square.size}")


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
    font = load_font(28)
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


watermark_dir = output / "watermark"
watermark_dir.mkdir(parents=True, exist_ok=True)
for path in sorted(batch_dir.glob("*.png")):
    with PILImage.open(path) as handle:
        picture = handle.convert("RGB")
    marked = add_watermark(picture, "码袋子 · 示例")
    marked.save(watermark_dir / path.name)
    print(path.name, "已加水印")


thumbs = sorted(watermark_dir.glob("*.png"))
sheet = PILImage.new("RGB", (len(thumbs) * 210 + 10, 210), (245, 245, 245))
for index, path in enumerate(thumbs):
    with PILImage.open(path) as handle:
        thumb = handle.convert("RGB").resize((200, 200), PILImage.LANCZOS)
    sheet.paste(thumb, (index * 210 + 10, 5))
sheet.save(output / "contact_sheet.png")
print(f"拼版尺寸：{sheet.size}")
print("拼版文件字节：", (output / "contact_sheet.png").stat().st_size)
display(Image(filename=str(output / "contact_sheet.png")))

from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)

from PyPDF2 import PdfReader, PdfWriter

SOURCE = data_path("sample.pdf")
reader = PdfReader(str(SOURCE))
print("源文件页数:", len(reader.pages))
print("第一页尺寸:", round(float(reader.pages[0].mediabox.width)), "x", round(float(reader.pages[0].mediabox.height)))


merged_path = out_dir / "merged.pdf"
writer = PdfWriter()
for _ in range(2):
    for page in reader.pages:
        writer.add_page(page)
with merged_path.open("wb") as file:
    writer.write(file)

print("合并后页数:", len(PdfReader(str(merged_path)).pages))


split_path = out_dir / "first-two-pages.pdf"
writer = PdfWriter()
for page in PdfReader(str(merged_path)).pages[:2]:
    writer.add_page(page)
with split_path.open("wb") as file:
    writer.write(file)

print("拆分文件页数:", len(PdfReader(str(split_path)).pages))
print("拆分文件第一页开头:", PdfReader(str(split_path)).pages[0].extract_text().splitlines()[0])


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

watermark_path = out_dir / "watermark.pdf"
canvas_obj = canvas.Canvas(str(watermark_path), pagesize=A4)
canvas_obj.setFont("Helvetica-Bold", 36)
canvas_obj.setFillGray(0.75)
canvas_obj.saveState()
canvas_obj.translate(A4[0] / 2, A4[1] / 2)
canvas_obj.rotate(45)
canvas_obj.drawCentredString(0, 0, "CONFIDENTIAL")
canvas_obj.restoreState()
canvas_obj.save()

print("水印页数:", len(PdfReader(str(watermark_path)).pages))


watermarked_path = out_dir / "watermarked.pdf"
watermark_page = PdfReader(str(watermark_path)).pages[0]

writer = PdfWriter()
for page in PdfReader(str(merged_path)).pages:
    page.merge_page(watermark_page)
    writer.add_page(page)
with watermarked_path.open("wb") as file:
    writer.write(file)

print("加水印后页数:", len(PdfReader(str(watermarked_path)).pages))
print("第一页开头:", PdfReader(str(watermarked_path)).pages[0].extract_text().splitlines()[0])

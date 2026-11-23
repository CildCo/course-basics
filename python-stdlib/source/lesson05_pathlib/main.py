import tempfile
from pathlib import Path

tmp = tempfile.TemporaryDirectory()
root = Path(tmp.name) / "project"
(root / "notes").mkdir(parents=True)

(root / "notes" / "day1.txt").write_text("第一天：路径与文件\n", encoding="utf-8")
(root / "notes" / "day2.txt").write_text("第二天：遍历与统计\n", encoding="utf-8")
(root / "readme.md").write_text("# 示例课程\n", encoding="utf-8")

for path in sorted(root.rglob("*")):
    print(path.relative_to(root))


for path in sorted(root.rglob("*.txt")):
    text = path.read_text(encoding="utf-8").strip()
    print(path.name, "|", text, "|", path.stat().st_size, "字节")


import os

note = root / "notes" / "day1.txt"
print("文件名：", note.name)
print("后缀：", note.suffix)
print("父目录：", note.parent.name)
print("是否存在：", note.exists())
print("换成 md：", note.with_suffix(".md").name)
print("拼接：", (note.parent / "day3.txt").relative_to(root))

print("os.listdir：", sorted(os.listdir(root)))
print("os.path.join：", os.path.join("notes", "day1.txt"))


with tempfile.TemporaryDirectory() as work:
    work_dir = Path(work)
    draft = work_dir / "draft.txt"
    draft.write_text("临时内容", encoding="utf-8")
    print("临时文件：", draft.name, "存在：", draft.exists())
print("退出 with 后目录还在吗：", work_dir.exists())

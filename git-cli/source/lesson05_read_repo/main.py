from pathlib import Path

here = Path.cwd()
if (here / "source").is_dir():
    source_root = here / "source"
elif (here.parent / "source").is_dir():
    source_root = here.parent / "source"
else:
    source_root = here

print("源码目录：", source_root.name)
for path in sorted(source_root.iterdir()):
    if path.name.startswith("."):
        continue
    print("目录" if path.is_dir() else "文件", path.name)


readme = source_root / "README.md"
print(readme.read_text(encoding="utf-8").splitlines()[0])
requirements = source_root / "requirements.txt"
print(requirements.read_text(encoding="utf-8").strip() or "无第三方依赖")


run_all = source_root / "run_all.py"
print("有 run_all.py：", run_all.exists())
if run_all.exists():
    for line in run_all.read_text(encoding="utf-8").splitlines()[:12]:
        print(line)

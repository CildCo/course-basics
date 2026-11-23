import matplotlib
matplotlib.use("Agg")

from pathlib import Path


out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)

import hashlib
from importlib import metadata

packages = ["requests", "pandas", "matplotlib", "python-docx", "pdfplumber"]
for name in packages:
    try:
        print(f"{name}=={metadata.version(name)}")
    except metadata.PackageNotFoundError:
        print(f"{name} (未安装)")

print("已安装包总数:", len(list(metadata.distributions())))


requirements = "\n".join(
    [
        "requests==2.34.2",
        "pandas==2.3.3",
        "matplotlib==3.11.2",
        "python-docx==1.2.0",
        "pdfplumber==0.11.10",
    ]
) + "\n"
requirements_path = out_dir / "requirements.txt"
requirements_path.write_text(requirements, encoding="utf-8")

digest = hashlib.sha256(requirements_path.read_bytes()).hexdigest()
print(requirements)
print("文件 SHA256:", digest)


import difflib

popular = [
    "requests",
    "numpy",
    "pandas",
    "matplotlib",
    "flask",
    "fastapi",
    "pdfplumber",
]
candidates = ["requests", "reqeusts", "numppy", "pandas", "pdfpluber", "flaskk"]

for name in candidates:
    if name in popular:
        print(f"{name}: 已知包")
        continue
    matches = difflib.get_close_matches(name, popular, n=1, cutoff=0.8)
    if matches:
        print(f"{name}: 可疑，接近 {matches[0]}")
    else:
        print(f"{name}: 未匹配")


for name in ["pandas", "python-docx"]:
    info = metadata.metadata(name)
    requires = info.get_all("Requires-Dist") or []
    print(f"{name} 的依赖数量:", len(requires))
    for item in requires[:3]:
        print("  ", item)

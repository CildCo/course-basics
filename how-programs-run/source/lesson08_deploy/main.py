import atexit
import shutil
import tempfile
from pathlib import Path

ROOT = Path(tempfile.mkdtemp(prefix="deploy-demo-"))
atexit.register(shutil.rmtree, ROOT, ignore_errors=True)

project = ROOT / "demo-app"
(project / "app").mkdir(parents=True)
(project / "app" / "__init__.py").write_text("", encoding="utf-8", newline="\n")
(project / "app" / "main.py").write_text(
    "def main():\n    print('hello from demo-app')\n\n"
    "if __name__ == '__main__':\n    main()\n",
    encoding="utf-8",
    newline="\n",
)
(project / "requirements.txt").write_text(
    "# 示例项目只用标准库\n", encoding="utf-8", newline="\n"
)
(project / "README.md").write_text("# demo-app\n", encoding="utf-8", newline="\n")

print("项目文件：")
for path in sorted(project.rglob("*")):
    if path.is_file():
        print(" ", path.relative_to(project).as_posix())


import importlib.util
import py_compile

cache_dir = ROOT / "cache"
cache_dir.mkdir()
pyc_path = cache_dir / "main.pyc"
py_compile.compile(
    str(project / "app" / "main.py"), cfile=str(pyc_path), doraise=True
)

header = pyc_path.read_bytes()[:4]
print("pyc 文件大小：", pyc_path.stat().st_size, "字节")
print("pyc 魔数：", header.hex())
print("与当前解释器一致：", header == importlib.util.MAGIC_NUMBER)


import zipfile

archive_path = ROOT / "demo-app.zip"
with zipfile.ZipFile(archive_path, "w") as archive:
    for path in sorted(project.rglob("*")):
        if path.is_file():
            name = "demo-app/" + path.relative_to(project).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())

with zipfile.ZipFile(archive_path) as archive:
    print("压缩包内容：")
    for info in archive.infolist():
        print(f"  {info.filename} ({info.file_size} 字节)")
    print("完整性检查通过：", archive.testzip() is None)


steps = [
    "构建：把源码和依赖打成可分发产物",
    "配置：准备解释器版本、环境变量和外部服务",
    "启动：用进程管理器拉起服务并设置重启策略",
    "验证：健康检查、看日志、保留上一个版本用于回滚",
]
for number, step in enumerate(steps, 1):
    print(number, step)

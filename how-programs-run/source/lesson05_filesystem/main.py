import atexit
import shutil
import tempfile
from pathlib import Path

ROOT = Path(tempfile.mkdtemp(prefix="files-demo-"))
atexit.register(shutil.rmtree, ROOT, ignore_errors=True)

logs = ROOT / "logs"
logs.mkdir()
log_file = logs / "app.log"
log_file.write_text("启动服务\n处理请求\n服务停止\n", encoding="utf-8", newline="\n")

print("目录存在：", logs.is_dir())
print("文件存在：", log_file.is_file())
print("文件名：", log_file.name)
print("后缀：", log_file.suffix)
print("相对路径：", log_file.relative_to(ROOT).as_posix())
print("文件大小：", log_file.stat().st_size, "字节")


config = ROOT / "config" / "settings.json"
config.parent.mkdir(parents=True)
config.write_text('{"debug": false}\n', encoding="utf-8")

print("父目录名：", config.parent.name)
print("是绝对路径：", config.is_absolute())
print("拼接结果相同：", (ROOT / "config" / "settings.json") == config)
print("读取内容：", config.read_text(encoding="utf-8").strip())


import os
import stat

mode = config.stat().st_mode
print("可读：", os.access(config, os.R_OK))
print("可写：", os.access(config, os.W_OK))
print("是普通文件：", stat.S_ISREG(mode))
print("临时目录下的文件：")
for path in sorted(ROOT.rglob("*")):
    if path.is_file():
        print(" ", path.relative_to(ROOT).as_posix())

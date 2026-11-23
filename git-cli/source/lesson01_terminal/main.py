import os
import sys
from pathlib import Path

print("系统：", os.name)
print("平台：", sys.platform)
print("当前目录名：", Path.cwd().name)
print("Python：", sys.version.split()[0])


relative = Path("output") / "demo.txt"
relative.parent.mkdir(exist_ok=True)
relative.write_text("hello", encoding="utf-8")
print("相对路径：", relative)
print("后缀：", relative.suffix)
print("存在：", relative.exists())


path_value = os.environ.get("PATH", "")
print("PATH 条目数：", len(path_value.split(os.pathsep)))
print("Python 可执行文件：", Path(sys.executable).name)

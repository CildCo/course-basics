import sys

print("版本：", ".".join(str(part) for part in sys.version_info[:3]))
print("可执行文件：", sys.executable.split("\\")[-1])


import subprocess
import sys

result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print(result.stdout.split(" from ")[0])


print("创建：python -m venv .venv")
print("激活 Windows：.venv\\Scripts\\activate")
print("激活 macOS/Linux：source .venv/bin/activate")
print("安装：pip install pandas")
print("记录：pip freeze > requirements.txt")

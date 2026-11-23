import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-c", "print('hello from child')"],
    capture_output=True,
    text=True,
)
print("返回码：", result.returncode)
print("标准输出：", result.stdout.strip())
print("标准错误：", repr(result.stderr))


failed = subprocess.run(
    [sys.executable, "-c", "import sys; sys.exit(3)"],
    capture_output=True,
    text=True,
)
print("主动退出的返回码：", failed.returncode)

error = subprocess.run(
    [sys.executable, "-c", "raise ValueError('bad input')"],
    capture_output=True,
    text=True,
)
print("异常退出的返回码：", error.returncode)
print("最后一行：", error.stderr.strip().splitlines()[-1])


if sys.platform == "win32":
    command = ["cmd", "/c", "echo hello-from-system"]
else:
    command = ["sh", "-c", "echo hello-from-system"]

shell_result = subprocess.run(command, capture_output=True, text=True)
print("系统：", sys.platform)
print("返回码：", shell_result.returncode)
print("输出：", shell_result.stdout.strip())


print("Python 版本：", sys.version.split()[0])
print("解释器：", sys.executable)
print("平台：", sys.platform)
print("命令行参数个数：", len(sys.argv))

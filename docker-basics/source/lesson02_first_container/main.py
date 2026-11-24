import os
import subprocess
import time
import uuid
from pathlib import Path

def run(cmd, timeout=60, check=False):
    """执行一条 docker 命令，打印命令和输出。"""
    print("$", subprocess.list2cmdline(cmd))
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("找不到 docker 命令，请先安装并启动 Docker Desktop。") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"命令超过 {timeout} 秒未完成：{' '.join(cmd)}") from exc

    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    print(output or "(无输出)")
    print("退出码:", proc.returncode)
    if check and proc.returncode != 0:
        raise RuntimeError(f"命令失败：{' '.join(cmd)}")
    return proc

def ensure_docker():
    """先确认 Docker 可用，失败时给出可读错误。"""
    try:
        print("$", subprocess.list2cmdline(["docker", "info", "--format", "{{.ServerVersion}}"]))
        proc = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("找不到 docker 命令，请先安装并启动 Docker Desktop。") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("docker info 超过 60 秒未返回，Docker 可能没有启动。") from exc

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(
            "Docker 未运行或当前用户没有访问权限。请启动 Docker Desktop 后重试。"
            "原始错误：" + detail
        )
    version = proc.stdout.strip()
    print("Docker 服务版本:", version)
    return version

SUFFIX = f"{os.getpid()}-{uuid.uuid4().hex[:6]}"
ensure_docker()


run(["docker", "run", "--rm", "busybox:latest", "echo", "hello from container"])


run([
    "docker", "run", "--rm", "--name", "demo-busybox-" + SUFFIX,
    "busybox:latest", "sh", "-c",
    'echo "container=$(hostname)"; echo "pid=$$"; ls /',
])


run([
    "docker", "run", "--rm", "busybox:latest", "sh", "-c",
    'for i in 1 2 3; do echo "line $i"; done',
])

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


name = "demo-logs-" + SUFFIX
try:
    started = run([
        "docker", "run", "-d", "--name", name, "busybox:latest", "sh", "-c",
        'for i in 1 2 3; do echo "log line $i"; sleep 1; done; sleep 5',
    ])
    if started.returncode != 0:
        raise RuntimeError("演示容器启动失败。")
    time.sleep(1.5)
    run(["docker", "logs", name])
    run([
        "docker", "inspect", "--format",
        "状态={{.State.Status}} PID={{.State.Pid}} 镜像={{.Config.Image}}",
        name,
    ])
finally:
    run(["docker", "rm", "-f", name])


run(["docker", "system", "df"])


run(["docker", "image", "inspect", "demo-not-exist:0.0.1"])
print("退出码非 0 说明本机没有这个镜像；先检查名字和标签，再决定是否拉取。")


import socket

sock = socket.socket()
sock.bind(("127.0.0.1", 0))
sock.listen(5)
port = sock.getsockname()[1]
print("先用 Python 占住本机端口:", port)

name = "demo-port-" + SUFFIX
try:
    conflict = run([
        "docker", "run", "-d", "--name", name,
        "-p", f"127.0.0.1:{port}:80", "nginx:latest",
    ])
    print("绑定已占用端口的退出码:", conflict.returncode)
finally:
    sock.close()
    run(["docker", "rm", "-f", name])

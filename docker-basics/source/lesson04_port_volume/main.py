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


import urllib.request

name = "demo-nginx-" + SUFFIX
try:
    started = run([
        "docker", "run", "-d", "--rm", "--name", name,
        "-p", "127.0.0.1::80", "nginx:latest",
    ])
    if started.returncode != 0:
        raise RuntimeError("nginx 容器启动失败。")

    time.sleep(1)
    port_line = run(["docker", "port", name, "80/tcp"], check=True).stdout.strip()
    port = int(port_line.rsplit(":", 1)[1])
    print("映射后的本机端口:", port)

    last_error = None
    for _ in range(20):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                print("HTTP 状态:", resp.status)
                print("首页前 120 个字符:", html[:120].replace("\n", " "))
            break
        except Exception as exc:
            last_error = exc
            time.sleep(0.3)
    else:
        raise RuntimeError(f"nginx 没有在端口 {port} 上响应：{last_error}")
finally:
    run(["docker", "stop", name])


volume_dir = Path.cwd() / "output" / "volume-demo"
volume_dir.mkdir(parents=True, exist_ok=True)
try:
    run([
        "docker", "run", "--rm",
        "-v", f"{volume_dir.as_posix()}:/data",
        "busybox:latest", "sh", "-c",
        "echo '来自容器的内容' > /data/from-container.txt",
    ])
    print("宿主机读到:", (volume_dir / "from-container.txt").read_text(encoding="utf-8").strip())
finally:
    import shutil
    shutil.rmtree(volume_dir, ignore_errors=True)


run([
    "docker", "run", "--rm", "-e", "GREETING=hello from env",
    "busybox:latest", "sh", "-c", "echo $GREETING",
])

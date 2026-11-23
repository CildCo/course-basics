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


demo_dir = Path.cwd() / "output" / "docker-demo"
demo_dir.mkdir(parents=True, exist_ok=True)
(demo_dir / "message.txt").write_text("这是打包进镜像的文本文件\n", encoding="utf-8")

dockerfile = """FROM busybox:latest
LABEL course="docker-basics"
COPY message.txt /message.txt
ENV APP_MODE=demo
CMD ["sh", "-c", "cat /message.txt && echo mode=$APP_MODE"]
"""
(demo_dir / "Dockerfile").write_text(dockerfile, encoding="utf-8")

print(dockerfile)
print("构建上下文:", sorted(path.name for path in demo_dir.iterdir()))


image = "maidai-demo:1.0"
try:
    build = run([
        "docker", "build", "-t", image, "output/docker-demo",
    ])
    if build.returncode != 0:
        raise RuntimeError("镜像构建失败，请检查 Dockerfile 和构建上下文。")
    run(["docker", "run", "--rm", image])
finally:
    run(["docker", "rmi", "-f", image])


run(["docker", "images", "--filter", "reference=maidai-demo"])

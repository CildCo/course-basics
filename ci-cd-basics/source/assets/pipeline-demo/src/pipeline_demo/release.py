"""发布相关的小函数：版本解析、递增、制品命名和校验和。"""

from __future__ import annotations

import hashlib
import re

VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_version(text: str) -> tuple[int, int, int]:
    """把 "1.2.3" 解析成 (1, 2, 3)，格式不对直接报错。"""
    match = VERSION_PATTERN.match(text.strip())
    if not match:
        raise ValueError(f"版本号格式应为 X.Y.Z：{text!r}")
    return tuple(int(part) for part in match.groups())


def bump(version: str, part: str = "patch") -> str:
    """按 patch / minor / major 递增版本号。"""
    major, minor, patch = parse_version(version)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"不支持的版本部位：{part!r}")


def release_tag(version: str, commit: str) -> str:
    """生成发布标签，例如 v0.3.1-abc1234。"""
    parse_version(version)
    short = commit.strip()[:7]
    if not short:
        raise ValueError("提交号不能为空")
    return f"v{version}-{short}"


def artifact_name(package: str, version: str, python_tag: str = "py3") -> str:
    """生成 wheel 文件名，标签规则与打包工具保持一致。"""
    parse_version(version)
    normalized = package.strip().lower().replace("_", "-")
    if not normalized:
        raise ValueError("包名不能为空")
    return f"{normalized}-{version}-{python_tag}-none-any.whl"


def checksum(data: bytes, algorithm: str = "sha256") -> str:
    """计算制品的十六进制摘要，用于发布后核对文件。"""
    digest = hashlib.new(algorithm)
    digest.update(data)
    return digest.hexdigest()

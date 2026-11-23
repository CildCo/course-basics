import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import re

SECRET_PATTERN = re.compile(r"(?i)(token|password|secret|api_key)=([^\s]+)")


def redact(line, known_secrets=()):
    """先按字段名遮值，再替换已知密钥，形成两层保护。"""
    masked = SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=***", line)
    for value in known_secrets:
        if value:
            masked = masked.replace(value, "***")
    return masked


logs = [
    "login ok user=alice",
    "deploy token=abc123 target=staging",
    "password=hunter2 retry=1",
    "credential sk-demo-999 loaded",
]
known = ["sk-demo-999"]

for line in logs:
    print(redact(line, known))

leftover = [line for line in logs if known[0] in redact(line, known)]
print("泄露检查:", "通过" if not leftover else leftover)


class Release:
    def __init__(self, version, digest):
        self.version = version
        self.digest = digest


class Registry:
    """内存里的制品库，按发布顺序保存不可变制品。"""

    def __init__(self):
        self.releases = []
        self.current = None

    def publish(self, release):
        if any(item.version == release.version for item in self.releases):
            raise ValueError(f"版本已存在，不能覆盖: {release.version}")
        self.releases.append(release)

    def deploy(self, version):
        release = next((item for item in self.releases if item.version == version), None)
        if release is None:
            raise ValueError(f"没有制品: {version}")
        self.current = release

    def rollback(self):
        if self.current is None or len(self.releases) < 2:
            raise RuntimeError("没有可回滚的版本")
        index = self.releases.index(self.current)
        if index == 0:
            raise RuntimeError("已经是最早的版本")
        self.current = self.releases[index - 1]


registry = Registry()
for version, digest in [
    ("1.4.2", "sha256:aaa"),
    ("1.5.0", "sha256:bbb"),
    ("1.5.1", "sha256:ccc"),
]:
    registry.publish(Release(version, digest))

registry.deploy("1.5.1")
print("上线:", registry.current.version, registry.current.digest)
registry.rollback()
print("回滚:", registry.current.version, registry.current.digest)
registry.rollback()
print("再回滚:", registry.current.version, registry.current.digest)
print("可用版本:", [release.version for release in registry.releases])


def preflight(config):
    problems = []
    if config.get("environment") not in {"staging", "production"}:
        problems.append("环境名不合法")
    if config.get("environment") == "production" and not config.get("requires_approval"):
        problems.append("生产环境必须审批")
    if config.get("secrets_in_repo"):
        problems.append("密钥不能写进仓库")
    return problems


configs = [
    {"environment": "staging", "requires_approval": False, "secrets_in_repo": False},
    {"environment": "production", "requires_approval": False, "secrets_in_repo": False},
    {"environment": "production", "requires_approval": True, "secrets_in_repo": True},
]

for config in configs:
    problems = preflight(config)
    print(config["environment"], "->", problems or "通过")

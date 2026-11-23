import json
from copy import deepcopy
from pathlib import Path

OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)
CONFIG_PATH = OUTPUT / "config.json"
CONFIG_PATH.write_text(
    json.dumps(
        {
            "api": {
                "base_url": "http://127.0.0.1:8010",
                "token": "local-dev-token",
            },
            "log_level": "INFO",
            "page_size": 20,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

DEFAULTS = {
    "api": {"base_url": "https://api.example.com", "token": ""},
    "log_level": "WARNING",
    "page_size": 10,
}

print(CONFIG_PATH.read_text(encoding="utf-8"))


def deep_merge(base, override):
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_settings(config_path=None, env=None):
    env = env or {}
    settings = deepcopy(DEFAULTS)
    if config_path and Path(config_path).exists():
        file_data = json.loads(Path(config_path).read_text(encoding="utf-8"))
        settings = deep_merge(settings, file_data)
    if "TASKKIT_API_TOKEN" in env:
        settings["api"]["token"] = env["TASKKIT_API_TOKEN"]
    if "TASKKIT_LOG_LEVEL" in env:
        settings["log_level"] = env["TASKKIT_LOG_LEVEL"]
    if "TASKKIT_PAGE_SIZE" in env:
        settings["page_size"] = int(env["TASKKIT_PAGE_SIZE"])
    return settings


if __name__ == "__main__":
    file_only = load_settings(CONFIG_PATH)
    with_env = load_settings(
        CONFIG_PATH,
        env={
            "TASKKIT_API_TOKEN": "env-secret-456",
            "TASKKIT_LOG_LEVEL": "DEBUG",
        },
    )
    print(
        "只用配置文件：",
        file_only["api"]["base_url"],
        file_only["log_level"],
        file_only["page_size"],
    )
    print(
        "环境变量覆盖：",
        with_env["api"]["base_url"],
        with_env["log_level"],
        with_env["page_size"],
    )
    print("令牌已被环境变量替换：", with_env["api"]["token"] != file_only["api"]["token"])


SENSITIVE_WORDS = ("token", "password", "secret", "api_key")


def mask_secret(value):
    text = str(value)
    if not text:
        return ""
    if len(text) <= 6:
        return "***"
    return f"{text[:2]}***{text[-2:]}"


def mask_mapping(data):
    masked = {}
    for key, value in data.items():
        if isinstance(value, dict):
            masked[key] = mask_mapping(value)
        elif any(word in key.lower() for word in SENSITIVE_WORDS):
            masked[key] = mask_secret(value)
        else:
            masked[key] = value
    return masked


if __name__ == "__main__":
    print(json.dumps(mask_mapping(with_env), ensure_ascii=False, indent=2))


import io
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "time": self.formatTime(record, "%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        payload.update(getattr(record, "context", {}))
        return json.dumps(payload, ensure_ascii=False)


def build_logger(level):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("taskkit")
    logger.handlers.clear()
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger, stream


if __name__ == "__main__":
    logger, stream = build_logger(with_env["log_level"])
    logger.debug("调试信息只在 DEBUG 级别出现")
    logger.info(
        "加载任务",
        extra={"context": {"task_count": 4, "source": "assets/tasks.json"}},
    )
    logger.warning(
        "接口配置已加载",
        extra={"context": {"api": mask_mapping(with_env["api"])}},
    )
    print(stream.getvalue(), end="")


import shutil

if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("临时配置已清理：", not CONFIG_PATH.exists())

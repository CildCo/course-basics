from pathlib import Path


def course_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for base in (here, *here.parents):
        if (base / "assets").is_dir() and (
            (base / "collection.json").exists() or (base / "README.md").exists()
        ):
            return base
    try:
        return Path(__file__).resolve().parent.parent
    except NameError:
        return here.parent


def data_path(name: str) -> Path:
    return course_root() / "assets" / name


def output_dir() -> Path:
    target = course_root() / "output"
    target.mkdir(parents=True, exist_ok=True)
    return target

import os
from dataclasses import dataclass


def read_env_file(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError(f"配置行缺少等号：{line}")
        values[key.strip()] = value.strip()
    return values


@dataclass(frozen=True)
class Settings:
    name: str = "FastAPI 进阶"
    env: str = "dev"
    secret: str = ""
    access_token_minutes: int = 30
    database_url: str = "sqlite://"

    @classmethod
    def load(cls) -> "Settings":
        raw = read_env_file(data_path("app.env.example"))

        def pick(key: str, default: str) -> str:
            return os.environ.get(f"APP_{key}") or raw.get(key) or default

        settings = cls(
            name=pick("NAME", "FastAPI 进阶"),
            env=pick("ENV", "dev"),
            secret=pick("SECRET", ""),
            access_token_minutes=int(pick("ACCESS_TOKEN_MINUTES", "30")),
            database_url=pick("DATABASE_URL", "sqlite://"),
        )
        return settings.validate()

    def validate(self) -> "Settings":
        if self.env not in {"dev", "test", "prod"}:
            raise ValueError(f"未知环境：{self.env}")
        if len(self.secret) < 12:
            raise ValueError("APP_SECRET 至少 12 位")
        if not 1 <= self.access_token_minutes <= 1440:
            raise ValueError("Token 有效期必须在 1 到 1440 分钟之间")
        return self

    def describe(self) -> dict:
        return {
            "name": self.name,
            "env": self.env,
            "secret": self.secret[:4] + "****",
            "access_token_minutes": self.access_token_minutes,
            "database_url": self.database_url,
        }


print("配置文件字段:", sorted(read_env_file(data_path("app.env.example"))))
settings = Settings.load()
print("当前配置:", settings.describe())


from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title=settings.name)
    app.state.settings = settings

    def get_settings() -> Settings:
        return app.state.settings

    @app.get("/health")
    def health(config: Settings = Depends(get_settings)):
        return {
            "app": config.name,
            "env": config.env,
            "token_minutes": config.access_token_minutes,
        }

    @app.get("/config/check")
    def config_check(config: Settings = Depends(get_settings)):
        return {
            "database_url": config.database_url,
            "secret_masked": config.secret[:4] + "****",
        }

    return app


client = TestClient(create_app(settings))
print("健康检查:", client.get("/health").json())
print("配置检查:", client.get("/config/check").json())


os.environ["APP_ENV"] = "test"
os.environ["APP_ACCESS_TOKEN_MINUTES"] = "5"
overridden = Settings.load()
print("环境变量覆盖:", overridden.describe())

del os.environ["APP_ENV"]
del os.environ["APP_ACCESS_TOKEN_MINUTES"]
restored = Settings.load()
print("恢复文件配置:", restored.describe()["env"], restored.access_token_minutes)

os.environ["APP_SECRET"] = "short"
try:
    Settings.load()
except ValueError as exc:
    print("密钥校验失败:", exc)
finally:
    del os.environ["APP_SECRET"]

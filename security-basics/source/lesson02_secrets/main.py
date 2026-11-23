from pathlib import Path


out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)

import os
import secrets


def mask(value, keep=4):
    if not value:
        return "(未设置)"
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep)


api_key = secrets.token_urlsafe(24)
print("生成的密钥长度:", len(api_key), "字符")
print("打码显示:", mask(api_key))


db_password = secrets.token_urlsafe(18)
print("数据库密码:", mask(db_password))
print("API 密钥:", mask(api_key))
print("只保留前 4 位用于识别:", api_key[:4])


os.environ["MAIDAI_API_KEY"] = api_key
loaded = os.environ.get("MAIDAI_API_KEY", "")
print("环境变量是否存在:", bool(loaded))
print("读到的值:", mask(loaded))

missing = os.environ.get("MAIDAI_NOT_SET")
print("缺失时:", mask(missing))


example = out_dir / ".env.example"
example.write_text(
    "MAIDAI_API_KEY=\n"
    "MAIDAI_DB_PASSWORD=\n",
    encoding="utf-8",
)
print(example.read_text(encoding="utf-8"))

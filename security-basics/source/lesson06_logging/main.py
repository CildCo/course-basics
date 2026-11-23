from pathlib import Path


out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)

import json
import logging
import re


def mask_phone(text):
    return re.sub(r"(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)", r"\1****\2", text)


def mask_email(text):
    return re.sub(r"([\w.+-]{1,2})[\w.+-]*(@[\w.-]+)", r"\1***\2", text)


def mask_id_card(text):
    return re.sub(r"(?<!\d)(\d{6})\d{8}(\d{3}[\dXx])(?!\d)", r"\1********\2", text)


def redact(text):
    text = mask_phone(text)
    text = mask_email(text)
    text = mask_id_card(text)
    return text


sample = "联系 13812345678，邮箱 zhang.san@example.com，身份证 110101199003071234"
print("原文:", sample)
print("脱敏:", redact(sample))


import io


class RedactFilter(logging.Filter):
    def filter(self, record):
        record.msg = redact(str(record.msg))
        record.args = ()
        return True


logger = logging.getLogger("maidai.demo")
logger.setLevel(logging.INFO)
logger.handlers.clear()

stream = io.StringIO()
handler = logging.StreamHandler(stream)
handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
handler.addFilter(RedactFilter())
logger.addHandler(handler)

logger.info("用户 13812345678 登录失败，邮箱 zhang.san@example.com")
print(stream.getvalue().strip())


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"level": record.levelname, "message": record.getMessage()}
        return json.dumps(payload, ensure_ascii=False)


logger.handlers.clear()
stream = io.StringIO()
handler = logging.StreamHandler(stream)
handler.setFormatter(JsonFormatter())
handler.addFilter(RedactFilter())
logger.addHandler(handler)

logger.warning("身份证 110101199003071234 校验失败，订单 2026-001")
print(stream.getvalue().strip())


raw = "订单 2026-001 联系人 13900001111 邮箱 li.si@example.com"
print("脱敏前:", raw)
print("脱敏后:", redact(raw))
print("长度变化:", len(raw), "->", len(redact(raw)))

import json
import re
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

specs = {
    item["name"]: item
    for item in json.loads(data_path("tool_specs.json").read_text(encoding="utf-8"))["tools"]
}
query_schema = specs["query_orders"]["parameters"]
print(json.dumps(query_schema, ensure_ascii=False, indent=2))


TYPE_CHECKS = {
    "object": lambda item: isinstance(item, dict),
    "array": lambda item: isinstance(item, list),
    "string": lambda item: isinstance(item, str),
    "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
    "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
    "boolean": lambda item: isinstance(item, bool),
}


def validate(value, schema, path="$"):
    errors = []
    expected = schema.get("type")
    if expected and not TYPE_CHECKS[expected](value):
        errors.append(f"{path}: 期望 {expected}，实际是 {type(value).__name__}")
        return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: 必须是 {schema['enum']} 之一，实际是 {value!r}")

    if expected in {"integer", "number"}:
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: 不能小于 {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: 不能大于 {schema['maximum']}")

    if expected == "string":
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: 不符合格式 {schema['pattern']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: 长度不能超过 {schema['maxLength']}")

    if expected == "array" and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(validate(item, schema["items"], f"{path}[{index}]"))

    if expected == "object":
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: 缺少必填参数")
        for key, item in value.items():
            if key not in properties:
                if schema.get("additionalProperties") is False:
                    errors.append(f"{path}.{key}: 不允许的参数")
                continue
            errors.extend(validate(item, properties[key], f"{path}.{key}"))

    return errors


cases = [
    ("合法调用", {"region": "华东", "status": "paid", "limit": 3}),
    ("缺少必填", {"status": "paid"}),
    ("枚举之外", {"region": "西北", "status": "paid"}),
    ("类型错误", {"region": "华东", "limit": "三"}),
    ("多余参数", {"region": "华东", "debug": True}),
    ("范围越界", {"region": "华东", "limit": 0}),
]

for label, args in cases:
    errors = validate(args, query_schema)
    verdict = "通过" if not errors else "拒绝"
    print(f"{label}: {verdict}")
    for message in errors:
        print("  -", message)


def apply_defaults(args, schema):
    if schema.get("type") != "object":
        return args
    result = dict(args)
    for key, prop in schema.get("properties", {}).items():
        if key not in result and "default" in prop:
            result[key] = prop["default"]
    return result


valid = {"region": "华东"}
errors = validate(valid, query_schema)
print("校验:", "通过" if not errors else errors)
print("补默认值后:", apply_defaults(valid, query_schema))

try:
    from pydantic import BaseModel, Field, ValidationError

    class QueryOrders(BaseModel):
        region: str
        status: str = "paid"
        limit: int = Field(default=5, ge=1, le=100)

    print("pydantic 合法:", QueryOrders(**{"region": "华东"}).model_dump())
    try:
        QueryOrders(**{"region": "华东", "limit": "三"})
    except ValidationError as exc:
        for item in exc.errors():
            location = ".".join(str(part) for part in item["loc"])
            print("pydantic 错误:", location, item["msg"])
except ImportError:
    print("当前环境没有安装 pydantic，跳过对照")


messages = validate({"region": "华东", "limit": "三"}, query_schema)
feedback = "参数校验未通过，请修正后重试：" + "；".join(messages)
print(feedback)

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from html import escape

from IPython.display import HTML, display

rows = [
    ("GET", "读取资源或集合", "是", "是", "200", "404"),
    ("POST", "创建资源或提交一次性动作", "否", "否", "201 / 202", "400 / 409 / 422"),
    ("PUT", "用完整表示替换资源", "否", "是", "200 / 204", "400 / 404 / 409"),
    ("PATCH", "只修改提交的字段", "否", "看写法", "200 / 204", "400 / 404 / 415 / 422"),
    ("DELETE", "删除资源", "否", "是", "204", "404 / 409"),
]
head = (
    "<tr><th>方法</th><th>用途</th><th>安全</th><th>幂等</th>"
    "<th>成功码</th><th>常见失败码</th></tr>"
)
body = "".join(
    "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
    for row in rows
)
display(HTML(f"<table><thead>{head}</thead><tbody>{body}</tbody></table>"))
print("方法语义表:", len(rows), "行，5 种方法")


book = {
    "id": 7,
    "title": "网络基础",
    "author": "周航",
    "year": 2018,
    "tags": ["network"],
}


def put(current: dict, payload: dict) -> dict:
    return {"id": current["id"], **payload}


def patch(current: dict, changes: dict) -> dict:
    return {**current, **changes}


full = {"title": "网络基础（第2版）", "author": "周航", "year": 2021}
after_put = put(book, full)
print("PUT 后:", after_put)
print("PUT 重复执行结果相同:", put(book, full) == after_put)

after_patch = patch(book, {"year": 2021})
print("PATCH 后:", after_patch)
print("PATCH 保留未提交字段:", after_patch["title"], after_patch["tags"])


def status_for(action: str, outcome: str) -> int:
    mapping = {
        ("list", "ok"): 200,
        ("read", "ok"): 200,
        ("read", "missing"): 404,
        ("create", "ok"): 201,
        ("create", "duplicate"): 409,
        ("replace", "ok"): 200,
        ("patch", "ok"): 200,
        ("delete", "ok"): 204,
        ("delete", "missing"): 404,
        ("list", "bad_filter"): 400,
        ("create", "invalid"): 422,
        ("read", "rate_limited"): 429,
        ("read", "server_error"): 500,
    }
    return mapping.get((action, outcome), 500)


cases = [
    ("list", "ok"),
    ("read", "missing"),
    ("create", "ok"),
    ("create", "duplicate"),
    ("create", "invalid"),
    ("delete", "ok"),
    ("delete", "missing"),
    ("list", "bad_filter"),
    ("read", "rate_limited"),
]
for action, outcome in cases:
    print(f"{action:<8}{outcome:<14}-> {status_for(action, outcome)}")

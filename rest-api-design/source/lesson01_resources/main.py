import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path


def course_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for base in (here, *here.parents):
        if (base / "assets").is_dir():
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


print("课程目录:", course_root().name)
print("数据目录:", (course_root() / "assets").relative_to(course_root()).as_posix())
print("输出目录:", output_dir().relative_to(course_root()).as_posix())

lines = data_path("url_candidates.txt").read_text(encoding="utf-8").splitlines()
candidates = [
    line.strip()
    for line in lines
    if line.strip() and not line.lstrip().startswith("#")
]
print("待检查路径:", len(candidates), "条")
print("前三条:", candidates[:3])


import re

VERBS = {
    "get", "create", "update", "delete", "add",
    "remove", "list", "search", "export",
}


def audit(path: str) -> list[str]:
    issues = []
    path_only = path.split("?", 1)[0]
    if path_only != path_only.lower():
        issues.append("包含大写字母")
    if path_only.endswith("/"):
        issues.append("结尾多了斜杠")
    if re.search(r"\.(json|xml|php|aspx?)$", path_only):
        issues.append("带文件后缀")
    if "_" in path_only:
        issues.append("用下划线分隔")
    for segment in (part for part in path_only.split("/") if part):
        lowered = segment.lower()
        if lowered in VERBS:
            issues.append(f"路径段是动词 {segment}")
        elif any(lowered.startswith(verb) and len(segment) > len(verb) for verb in VERBS):
            issues.append(f"路径段以动词开头 {segment}")
    if "action=" in path:
        issues.append("用查询参数传动作")
    return issues or ["通过"]


for path in candidates:
    print(f"{path:<38} {'；'.join(audit(path))}")


from html import escape

from IPython.display import HTML, display

rewrites = [
    ("/api/getUserList", "/api/v1/users", "集合名词本身就表示列表"),
    ("/api/user/list", "/api/v1/users", "集合不需要再加 list"),
    ("/api/users/", "/api/v1/users", "去掉结尾斜杠"),
    ("/api/users/123/getOrders", "/api/v1/users/123/orders", "子资源用层级表达"),
    ("/api/order_detail?id=123", "/api/v1/orders/123", "标识放进路径"),
    ("/api/Orders", "/api/v1/orders", "路径统一小写"),
    ("/api/orders.json", "/api/v1/orders", "格式由请求头协商"),
    ("/api/user_profile", "/api/v1/users/{id}/profile", "复合名词拆成层级"),
    ("/api/orders?action=cancel&id=123", "/api/v1/orders/123", "取消改成 PATCH 状态"),
    ("/api/reports/exportExcel", "/api/v1/reports/{id}/exports", "导出是新建任务资源"),
]

rows = []
for old, new, reason in rewrites:
    rows.append(
        "<tr>"
        f"<td><code>{escape(old)}</code></td>"
        f"<td><code>{escape(new)}</code></td>"
        f"<td>{escape(reason)}</td>"
        "</tr>"
    )
table = (
    "<table><thead><tr><th>原路径</th><th>改写后</th><th>原因</th></tr></thead>"
    "<tbody>" + "".join(rows) + "</tbody></table>"
)
display(HTML(table))

report = ["原路径\t改写后\t原因"] + ["\t".join(row) for row in rewrites]
target = output_dir() / "url-rewrite.txt"
target.write_text("\n".join(report) + "\n", encoding="utf-8")
print("改写建议已写入:", target.name, "共", len(rewrites), "条")

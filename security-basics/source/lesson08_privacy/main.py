import hashlib
import hmac
import json
from datetime import date

SALT = b"demo-only-salt"

users = [
    {
        "id": 1,
        "name": "张三",
        "phone": "13812345678",
        "email": "zhang@example.com",
        "city": "上海",
        "birth_date": "1990-03-07",
        "created_at": date(2026, 1, 5),
    },
    {
        "id": 2,
        "name": "李四",
        "phone": "13900001111",
        "email": "li@example.com",
        "city": "深圳",
        "birth_date": "1988-11-22",
        "created_at": date(2026, 2, 10),
    },
    {
        "id": 3,
        "name": "王五",
        "phone": "13700002222",
        "email": "wang@example.com",
        "city": "北京",
        "birth_date": "1995-06-18",
        "created_at": date(2026, 3, 15),
    },
    {
        "id": 4,
        "name": "赵六",
        "phone": "13600003333",
        "email": "zhao@example.com",
        "city": "上海",
        "birth_date": "1992-09-30",
        "created_at": date(2026, 4, 20),
    },
]

print("原始记录数:", len(users))
print(json.dumps(users[0], ensure_ascii=False, default=str))


def pseudonym(value):
    digest = hmac.new(SALT, value.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:12]


def analytics_rows(users):
    return [
        {"user_token": pseudonym(str(user["id"])), "city": user["city"]}
        for user in users
    ]


rows = analytics_rows(users)
print("分析数据字段:", list(rows[0].keys()))
for row in rows:
    print(row)


CUTOFF = date(2026, 3, 1)
kept = [user for user in users if user["created_at"] >= CUTOFF]
expired = [user for user in users if user["created_at"] < CUTOFF]

print("保留:", len(kept), "条")
print("到期删除:", len(expired), "条")
print("删除编号:", [user["id"] for user in expired])
print("保留编号:", [user["id"] for user in kept])


consents = {1: True, 2: True, 3: False, 4: True}


def can_export(user):
    return consents.get(user["id"], False)


export = [user for user in kept if can_export(user)]
print("可导出的用户:", [user["id"] for user in export])

delete_id = 2
remaining = [user for user in users if user["id"] != delete_id]
export_after = [user for user in remaining if can_export(user)]

print("删除请求: 用户", delete_id)
print("删除前:", len(users), "条，删除后:", len(remaining), "条")
print("删除后仍能查到:", any(user["id"] == delete_id for user in remaining))
print("导出列表已移除:", delete_id not in [user["id"] for user in export_after])

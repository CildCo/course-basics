import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STAGES = ["检查", "测试", "构建", "制品", "部署"]


def run_pipeline(commit, fail_at=None):
    """按顺序执行阶段，任一阶段失败后，后面的阶段标记为跳过。"""
    results = []
    blocked = False
    for stage in STAGES:
        if blocked:
            results.append((stage, "跳过"))
        elif stage == fail_at:
            results.append((stage, "失败"))
            blocked = True
        else:
            results.append((stage, "通过"))
    return results


def print_run(commit, results):
    print(f"提交 {commit}")
    for index, (stage, status) in enumerate(results, 1):
        print(f"  {index}. {stage:<4} {status}")
    passed = sum(1 for _, status in results if status == "通过")
    print(f"结果：通过 {passed} 关，共 {len(results)} 关\n")


print_run("a1b2c3d", run_pipeline("a1b2c3d"))
print_run("e4f5a6b", run_pipeline("e4f5a6b", fail_at="测试"))


from collections import Counter

runs = [
    ("a1b2c3d", None),
    ("b2c3d4e", "检查"),
    ("c3d4e5f", None),
    ("d4e5f6a", "测试"),
    ("e5f6a7b", None),
    ("f6a7b8c", "构建"),
]

failed = Counter()
for commit, fail_at in runs:
    for stage, status in run_pipeline(commit, fail_at):
        if status == "失败":
            failed[stage] += 1

print("六次提交中，各阶段失败的次数：")
for stage in STAGES:
    print(f"  {stage:<4} {failed[stage]}")
print("全部通过的提交：", sum(1 for _, fail_at in runs if fail_at is None), "次")

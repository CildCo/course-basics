import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml

workflow_text = """
name: ci
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m pytest
"""

data = yaml.safe_load(workflow_text)
print("顶层键:", [repr(key) for key in data])

fixed_text = workflow_text.replace("\non:\n", '\n"on":\n')
fixed = yaml.safe_load(fixed_text)
print("加引号后的键:", list(fixed))
print("触发事件:", list(fixed["on"]))
print("任务:", list(fixed["jobs"]))


def validate_workflow(text):
    """检查 workflow 的必要结构和依赖，返回问题列表。"""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [f"YAML 语法错误: {exc.__class__.__name__}"]

    problems = []
    if not isinstance(data, dict):
        return ["顶层必须是映射"]
    if not data.get("name"):
        problems.append("缺少 name")
    if data.get("on") is None:
        problems.append("缺少 on 触发条件")

    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        problems.append("缺少 jobs")
        return problems

    known = set(jobs)
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            problems.append(f"jobs.{job_name} 必须是映射")
            continue
        if not job.get("runs-on"):
            problems.append(f"jobs.{job_name} 缺少 runs-on")

        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            problems.append(f"jobs.{job_name} 缺少 steps")
        else:
            for index, step in enumerate(steps, 1):
                if not isinstance(step, dict) or not (step.get("uses") or step.get("run")):
                    problems.append(f"jobs.{job_name}.steps[{index}] 必须包含 uses 或 run")

        needs = job.get("needs") or []
        if isinstance(needs, str):
            needs = [needs]
        for need in needs:
            if need not in known:
                problems.append(f"jobs.{job_name} 依赖了不存在的 {need}")
    return problems


print("合格流水线的问题:", validate_workflow(fixed_text))

bad_text = """
name: ci
"on": push
jobs:
  test:
    steps:
      - run: python -m pytest
  deploy:
    runs-on: ubuntu-latest
    needs: [build]
    steps: []
"""

for problem in validate_workflow(bad_text):
    print("问题:", problem)


job = fixed["jobs"]["test"]
print("运行环境:", job["runs-on"])
print("步骤数:", len(job["steps"]))
for index, step in enumerate(job["steps"], 1):
    action = step.get("uses") or step.get("run")
    print(f"  {index}. {action}")

import json
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

RETRY_POLICY = json.loads(data_path("policy.json").read_text(encoding="utf-8"))["retry"]
print("重试配置:", RETRY_POLICY)


class TemporaryError(RuntimeError):
    """可以重试的临时故障。"""


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def sleep(self, seconds):
        self.sleeps.append(round(seconds, 2))
        self.now = round(self.now + seconds, 2)


def call_with_retry(func, clock, max_attempts=3, base_delay=0.5, factor=2.0, deadline=2.0):
    attempts = []
    for number in range(1, max_attempts + 1):
        started = clock.now
        try:
            value = func(number)
        except TemporaryError as exc:
            attempts.append({"number": number, "started": started, "ok": False, "error": str(exc)})
            delay = base_delay * factor ** (number - 1)
            if number == max_attempts:
                break
            if clock.now + delay > deadline:
                attempts.append(
                    {"number": 0, "started": clock.now, "ok": False, "error": "总时限内无法再等一个退避间隔"}
                )
                break
            clock.sleep(delay)
        else:
            attempts.append({"number": number, "started": started, "ok": True, "error": ""})
            return value, attempts
    return None, attempts


class FlakyCounter:
    def __init__(self, fail_times):
        self.fail_times = fail_times
        self.calls = 0

    def __call__(self, number):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise TemporaryError(f"第 {self.calls} 次调用超时")
        return {"rows": 3, "calls": self.calls}


clock = FakeClock()
tool = FlakyCounter(fail_times=2)
value, attempts = call_with_retry(tool, clock, **RETRY_POLICY)
print("结果:", value)
print("实际等待:", clock.sleeps, "累计:", clock.now)
for item in attempts:
    mark = "成功" if item["ok"] else "失败"
    label = f"第{item['number']}次" if item["number"] else "停止"
    print(f"  {label} 开始={item['started']:.2f}s {mark} {item['error']}")


clock2 = FakeClock()
always = FlakyCounter(fail_times=99)
value2, attempts2 = call_with_retry(always, clock2, **{**RETRY_POLICY, "max_attempts": 10})
print("一直失败的结果:", value2)
print("实际等待:", clock2.sleeps, "累计:", clock2.now)
for item in attempts2:
    mark = "成功" if item["ok"] else "失败"
    label = f"第{item['number']}次" if item["number"] else "停止"
    print(f"  {label} 开始={item['started']:.2f}s {mark} {item['error']}")


class IdempotentAppender:
    def __init__(self, path):
        self.path = path
        self.completed = {}
        self.writes = 0

    def append(self, key, line):
        if key in self.completed:
            return {"status": "duplicate", "writes": self.writes}
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
        self.completed[key] = line
        self.writes += 1
        return {"status": "written", "writes": self.writes}


log_path = out / "idempotent.log"
log_path.write_text("", encoding="utf-8", newline="\n")
appender = IdempotentAppender(log_path)
key = "write-summary-001"
print(appender.append(key, "华东 9730.50"))
print(appender.append(key, "华东 9730.50"))
print(appender.append("write-summary-002", "华北 5230.00"))
print("文件内容:")
print(log_path.read_text(encoding="utf-8"))


print("重试策略:")
for key, value in RETRY_POLICY.items():
    print(f"- {key}: {value}")
print("适用错误: 临时故障（超时、连接中断、临时限流）")
print("不适用: 参数错误、权限拒绝、业务规则失败")

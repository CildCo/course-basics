import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

import sys
from pathlib import Path


def course_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for base in (here, *here.parents):
        if (base / "assets").is_dir() and (base / "collection.json").exists():
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

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

app = FastAPI(title="短链接服务")


@app.exception_handler(HTTPException)
async def handle_http_error(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", "http_error")
        message = detail.get("message", "")
    else:
        code = "http_error"
        message = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
        headers=exc.headers,
    )


@app.get("/links/{code}")
def redirect(code: str):
    if code == "missing":
        raise HTTPException(
            status_code=404,
            detail={"code": "link_not_found", "message": "短链接不存在"},
        )
    if code == "gone":
        raise HTTPException(
            status_code=410,
            detail={"code": "link_expired", "message": "短链接已过期"},
        )
    return {"code": code}


client = TestClient(app)
for path in ("/links/missing", "/links/gone", "/links/ok"):
    response = client.get(path)
    print(path, response.status_code, response.json())


from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = now if now is not None else 0.0
        events = self._events[key]
        while events and now - events[0] >= self.window_seconds:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True


limiter = RateLimiter(limit=3, window_seconds=60)
timeline = []
for moment in (0, 10, 20, 30, 70):
    allowed = limiter.allow("demo", now=moment)
    timeline.append((moment, allowed))
    print(f"t={moment:>2}s", "放行" if allowed else "限流")


import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7, 2.8))
for moment, allowed in timeline:
    color = "#2f6f68" if allowed else "#b4553f"
    ax.scatter(moment, 1 if allowed else 0, s=90, color=color, zorder=3)
    ax.vlines(moment, 0, 1 if allowed else 0, color="#b0b0b0", linestyle=":", zorder=1)
ax.set_yticks([0, 1], ["Blocked", "Allowed"])
ax.set_xlabel("Seconds")
ax.set_title("Requests under a 3-per-60s limit")
ax.set_xlim(-5, 80)
ax.grid(axis="x", linestyle=":", alpha=0.4)
plt.tight_layout()

chart = output_dir() / "rate-limit.png"
fig.savefig(chart, dpi=140, bbox_inches="tight")
print("图表文件:", chart.name, chart.stat().st_size, "字节")


from time import monotonic

limiter = RateLimiter(limit=2, window_seconds=60)


def check_rate_limit(
    request: Request,
    x_client_id: str = Header(default="anonymous"),
) -> None:
    key = f"{x_client_id}:{request.url.path}"
    if not limiter.allow(key, now=monotonic()):
        raise HTTPException(
            status_code=429,
            detail={"code": "rate_limited", "message": "请求过于频繁，请稍后再试"},
            headers={"Retry-After": "60"},
        )


@app.post("/links", status_code=201, dependencies=[Depends(check_rate_limit)])
def create_link(payload: dict):
    return {"code": "created", "payload": payload}


client = TestClient(app)
statuses = []
for index in range(3):
    response = client.post(
        "/links",
        json={"target_url": f"https://example.com/{index}"},
        headers={"X-Client-Id": "demo"},
    )
    statuses.append(response.status_code)
    if response.status_code == 429:
        print("第", index + 1, "次:", response.status_code, response.headers.get("retry-after"), response.json())
    else:
        print("第", index + 1, "次:", response.status_code)
print("状态序列:", statuses)

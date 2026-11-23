from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    done: bool = False


class Task(TaskCreate):
    id: int


class TaskRecord(Task):
    internal_note: str = "仅内部可见"


app = FastAPI()
TASKS = {
    1: Task(id=1, title="写周报"),
    2: Task(id=2, title="修 bug", done=True),
}


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    new_id = max(TASKS) + 1
    task = Task(id=new_id, **payload.model_dump())
    TASKS[new_id] = task
    return task


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    return TASKS[task_id]


@app.get("/tasks/{task_id}/internal", response_model=Task)
def get_internal_record(task_id: int):
    task = TASKS[task_id]
    return TaskRecord(**task.model_dump(), internal_note="负责人：小居")


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    del TASKS[task_id]


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/codes/{code}")
def check_code(code: str):
    if not code.startswith("T-"):
        raise ValueError("编号必须以 T- 开头")
    return {"code": code}


client = TestClient(app)
print("应用已就绪，现有任务:", sorted(TASKS))


created = client.post("/tasks", json={"title": "整理需求"})
print("创建:", created.status_code, created.json())

found = client.get("/tasks/1")
print("查询:", found.status_code, found.json())

missing = client.get("/tasks/99")
print("不存在:", missing.status_code, missing.json())

deleted = client.delete("/tasks/2")
print("删除:", deleted.status_code, "响应体长度:", len(deleted.content))

print("删除后再查:", client.get("/tasks/2").status_code)


internal = client.get("/tasks/1/internal")
print("内部记录接口:", internal.status_code, internal.json())
print("是否包含 internal_note:", "internal_note" in internal.json())

print("业务错误:", client.get("/codes/X-1").status_code, client.get("/codes/X-1").json())
print("合法编号:", client.get("/codes/T-100").json())

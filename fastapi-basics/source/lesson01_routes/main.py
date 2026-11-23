from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI(title="任务服务", version="0.1.0")


@app.get("/")
def read_root():
    return {"message": "服务已启动"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


print("应用已创建，路由数:", len(app.routes))


client = TestClient(app)

root = client.get("/")
print("GET / ->", root.status_code, root.json())
print("Content-Type:", root.headers["content-type"])

health = client.get("/health")
print("GET /health ->", health.status_code, health.json())


print("错误路径:", client.get("/missing").status_code)
print("错误方法:", client.post("/").status_code)

schema = client.get("/openapi.json").json()
print("已注册路径:", list(schema["paths"]))
print("/docs 页面:", client.get("/docs").status_code)

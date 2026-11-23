from pathlib import Path

test_dir = Path.cwd() / "output" / "tests"
test_dir.mkdir(parents=True, exist_ok=True)
test_file = test_dir / "test_api.py"

test_file.write_text(
    """
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"item_id": item_id, "name": f"商品{item_id}"}


client = TestClient(app)


def test_read_item():
    response = client.get("/items/3")
    assert response.status_code == 200
    assert response.json()["item_id"] == 3


def test_missing_item():
    response = client.get("/items/0")
    assert response.status_code == 404
    assert response.json()["detail"] == "商品不存在"


def test_invalid_id():
    response = client.get("/items/abc")
    assert response.status_code == 422
""",
    encoding="utf-8",
)

print("测试文件:", test_file)
print("行数:", len(test_file.read_text(encoding="utf-8").splitlines()))


import os
import subprocess
import sys

env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
result = subprocess.run(
    [sys.executable, "-m", "pytest", str(test_file), "-q", "--color=no", "-p", "no:cacheprovider"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    env=env,
)

print("退出码:", result.returncode)
print(result.stdout.strip())
assert result.returncode == 0, result.stderr

from pydantic import BaseModel, Field, ValidationError

class Item(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    price: float = Field(gt=0)
    tags: list[str] = Field(default_factory=list)

item = Item(name="键盘", price=199.0, tags=["数码"])
print(item)
print(item.model_dump())


try:
    Item(name="", price=-1)
except ValidationError as exc:
    for error in exc.errors():
        print("字段:", error["loc"], "原因:", error["msg"])


import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


@app.post("/items", response_model=Item)
def create_item(item: Item):
    return item


client = TestClient(app)

ok = client.post("/items", json={"name": "键盘", "price": 199, "tags": ["数码"]})
print("合法请求:", ok.status_code)
print(json.dumps(ok.json(), ensure_ascii=False, indent=2))

bad = client.post("/items", json={"name": "", "price": -1})
print("非法请求:", bad.status_code)
print(json.dumps(bad.json(), ensure_ascii=False, indent=2))

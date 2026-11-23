{
  try {
    const data = JSON.parse("{bad json}");
    console.log(data);
  } catch (error) {
    console.log("解析失败：", error.name);
  } finally {
    console.log("清理完成");
  }
}


{
  class ValidationError extends Error {
    constructor(message, field) {
      super(message);
      this.name = "ValidationError";
      this.field = field;
    }
  }

  function checkAge(age) {
    if (age < 0) {
      throw new ValidationError("年龄不能为负数", "age");
    }
    return age;
  }

  try {
    checkAge(-1);
  } catch (error) {
    console.log(error.name, error.field, error.message);
  }
}


{
  const assert = require("assert");

  function add(a, b) {
    return a + b;
  }

  assert.strictEqual(add(2, 3), 5);
  assert.throws(() => JSON.parse("{bad}"), SyntaxError);
  console.log("全部断言通过");
}


{
  const assert = require("assert");

  const tests = [];

  function test(name, fn) {
    tests.push({ name, fn });
  }

  function run() {
    let passed = 0;
    for (const item of tests) {
      try {
        item.fn();
        passed += 1;
        console.log("通过：", item.name);
      } catch (error) {
        console.log("失败：", item.name, error.message);
      }
    }
    console.log(`共 ${tests.length} 项，通过 ${passed} 项`);
  }

  test("1 + 1 等于 2", () => assert.strictEqual(1 + 1, 2));
  test("字符串包含 node", () => assert.ok("node".includes("nod")));
  run();
}


{
  function loadConfig(value) {
    console.error("[debug] 收到值：", value);
    return value ?? "默认配置";
  }

  console.log(loadConfig(null));
}

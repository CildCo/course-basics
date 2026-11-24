{
  const raw = "  JavaScript,Node,小程序  ";
  const parts = raw.trim().split(",");
  console.log(parts.length);
  console.log(parts.join(" / "));
  console.log(raw.includes("Node"), raw.startsWith("  Java"));
}


{
  const course = { id: "javascript-basics", title: "JavaScript 入门", tags: ["js", "node"] };
  const text = JSON.stringify(course);
  console.log(text);
  const parsed = JSON.parse(text);
  console.log(parsed.title, parsed.tags[1]);
}


{
  const fs = require("fs");
  const path = require("path");

  const dir = path.join(process.cwd(), "output", "module-demo");
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, "math-tools.js");
  fs.writeFileSync(
    file,
    "module.exports = { add: (a, b) => a + b, square: (n) => n * n };\n"
  );
  try {
    const tools = require(file);
    console.log("3 + 4 =", tools.add(3, 4));
    console.log("5 的平方 =", tools.square(5));
  } finally {
    fs.rmSync(path.join(process.cwd(), "output"), { recursive: true, force: true });
  }
}


{
  const data = { name: "小李", run: () => {}, score: NaN, note: undefined };
  console.log(JSON.stringify(data));
}

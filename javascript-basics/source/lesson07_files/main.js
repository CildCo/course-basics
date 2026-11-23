{
  const fs = require("fs/promises");
  const path = require("path");

  async function main() {
    const dir = path.join(process.cwd(), "output", "files-text");
    await fs.mkdir(dir, { recursive: true });
    try {
      const file = path.join(dir, "note.txt");
      await fs.writeFile(file, "第一行\n第二行\n", "utf8");
      const text = await fs.readFile(file, "utf8");
      console.log(text.trim());
    } finally {
      await fs.rm(path.join(process.cwd(), "output"), { recursive: true, force: true });
    }
  }

  main();
}


{
  const fs = require("fs/promises");
  const path = require("path");

  async function main() {
    const dir = path.join(process.cwd(), "output", "files-json");
    await fs.mkdir(dir, { recursive: true });
    try {
      const file = path.join(dir, "course.json");
      const data = { id: "javascript-basics", lessons: 10 };
      await fs.writeFile(file, JSON.stringify(data, null, 2), "utf8");
      const loaded = JSON.parse(await fs.readFile(file, "utf8"));
      console.log(loaded.id, loaded.lessons);
    } finally {
      await fs.rm(path.join(process.cwd(), "output"), { recursive: true, force: true });
    }
  }

  main();
}


{
  const fs = require("fs/promises");
  const path = require("path");

  async function main() {
    const dir = path.join(process.cwd(), "output", "files-list");
    await fs.mkdir(dir, { recursive: true });
    try {
      await fs.writeFile(path.join(dir, "a.txt"), "A\n", "utf8");
      await fs.appendFile(path.join(dir, "a.txt"), "B\n", "utf8");
      const files = await fs.readdir(dir);
      const text = await fs.readFile(path.join(dir, "a.txt"), "utf8");
      console.log("文件：", files.join(", "));
      console.log("内容：", text.trim().replace("\n", " / "));
    } finally {
      await fs.rm(path.join(process.cwd(), "output"), { recursive: true, force: true });
    }
  }

  main();
}

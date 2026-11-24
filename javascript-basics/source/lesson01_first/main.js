{
  console.log("你好，JavaScript");
  console.log("1 + 2 =", 1 + 2);
  console.log("今天", 3, "节课");
}


{
  console.log("Node 版本：", process.version);
  console.log("操作系统：", process.platform);
  console.log("启动参数：", process.argv.slice(0, 2).join(" "));
}


{
  const lessons = ["JavaScript 入门", "Node 基础", "小程序脚本"];
  console.log("学习计划：", lessons.length, "节");
  console.log("第一节：", lessons[0]);
}


{
  const name = "小李";
  const goal = "学会写小程序脚本";
  console.log(name + "的目标：" + goal);
}

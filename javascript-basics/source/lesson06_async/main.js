{
  console.log("开始");
  setTimeout(() => console.log("100ms 后"), 100);
  setTimeout(() => console.log("50ms 后"), 50);
  console.log("结束");
}


{
  function loadCourse() {
    return new Promise((resolve) => {
      setTimeout(() => resolve({ title: "JavaScript 入门", lessons: 10 }), 80);
    });
  }

  loadCourse().then((course) => console.log(course.title, course.lessons));
}


{
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  async function main() {
    console.log("请求开始");
    await sleep(70);
    console.log("拿到数据");
    await sleep(40);
    console.log("渲染完成");
  }

  main();
}


{
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  async function fetchScore(name, ms) {
    await sleep(ms);
    return `${name}:${ms}`;
  }

  async function main() {
    const results = await Promise.all([
      fetchScore("A", 60),
      fetchScore("B", 90),
      fetchScore("C", 120)
    ]);
    console.log(results.join(" "));
  }

  main();
}

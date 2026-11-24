{
  const score = 78;
  if (score >= 90) {
    console.log("优秀");
  } else if (score >= 60) {
    console.log("及格");
  } else {
    console.log("需要复习");
  }
}


{
  const action = "download";
  switch (action) {
    case "download":
      console.log("开始下载");
      break;
    case "preview":
      console.log("打开预览");
      break;
    default:
      console.log("未知操作");
  }
}


{
  for (let i = 1; i <= 3; i++) {
    console.log("第", i, "次");
  }

  let total = 0;
  let n = 1;
  while (n <= 5) {
    total += n;
    n++;
  }
  console.log("1 到 5 求和：", total);
}


{
  function greet(name, prefix = "同学") {
    return `你好，${prefix}${name}`;
  }
  console.log(greet("小李"));
  console.log(greet("小李", "老师"));
}


{
  const double = (n) => n * 2;
  console.log(double(21));

  function makeCounter() {
    let count = 0;
    return () => {
      count += 1;
      return count;
    };
  }
  const next = makeCounter();
  console.log(next(), next(), next());
}

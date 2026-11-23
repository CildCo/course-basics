{
  let count = 1;
  count = count + 1;
  const course = "JavaScript 入门";
  console.log(course, count);
}


{
  const title = "码袋子";
  const lessons = 10;
  const passed = true;
  const nothing = null;
  let notReady;
  console.log(typeof title, typeof lessons, typeof passed);
  console.log(typeof nothing, typeof notReady);
}


{
  const price = 19.9;
  const amount = 3;
  const total = price * amount;
  console.log(`单价 ${price} 元，共 ${amount} 份，总价 ${total.toFixed(2)} 元`);
  console.log("取整：", Math.floor(total), "四舍五入：", Math.round(total));
  console.log(10 % 3, 2 ** 3);
}


{
  console.log(0 == "");
  console.log(0 === "");
  console.log(Number("42") + 1);
  console.log(String(42) + 1);
}

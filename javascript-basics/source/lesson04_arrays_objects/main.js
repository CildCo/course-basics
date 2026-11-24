{
  const prices = [19.9, 39, 5.5, 88];
  const cheap = prices.filter((p) => p < 50);
  const doubled = cheap.map((p) => p * 2);
  console.log(cheap);
  console.log(doubled);
}


{
  const scores = [72, 95, 60, 88];
  const total = scores.reduce((sum, n) => sum + n, 0);
  const sorted = [...scores].sort((a, b) => b - a);
  console.log("总分：", total, "平均：", total / scores.length);
  console.log("从高到低：", sorted);
  console.log("原数组：", scores);
}


{
  const course = { id: "javascript-basics", title: "JavaScript 入门", lessons: 10 };
  const { title, lessons } = course;
  const updated = { ...course, lessons: lessons + 1 };
  console.log(title, lessons);
  console.log(updated);
}


{
  const user = { name: "小李", profile: { city: "杭州" } };
  const guest = { name: "访客" };
  console.log(user.profile?.city);
  console.log(guest.profile?.city ?? "未填写");
}

from collections import Counter

text = "the quick brown fox jumps over the lazy dog the fox"
words = text.lower().split()
counter = Counter(words)
print(counter)
print("出现最多的两个词：", counter.most_common(2))
print("fox 出现次数：", counter["fox"])
print("cat 出现次数：", counter["cat"])


from collections import defaultdict

records = [
    ("水果", "苹果"),
    ("水果", "香蕉"),
    ("饮料", "咖啡"),
    ("水果", "樱桃"),
    ("饮料", "茶"),
]

groups = defaultdict(list)
for category, name in records:
    groups[category].append(name)

print(dict(groups))
print("第一次访问 snack：", groups["snack"])
print("访问后：", dict(groups))


from collections import deque

queue = deque(["job-1", "job-2"])
queue.append("job-3")
print("处理：", queue.popleft())
queue.appendleft("job-0")
print("剩余：", list(queue))

recent = deque(maxlen=3)
for page in ["/", "/courses", "/courses/python-stdlib", "/about"]:
    recent.append(page)
print("最近 3 条：", list(recent))


from collections import namedtuple

Lesson = namedtuple("Lesson", ["id", "title", "minutes"])
lesson = Lesson("01", "容器增强", 14)
print(lesson)
print("标题：", lesson.title)
print("字段：", lesson._fields)
print("转字典：", lesson._asdict())

import re

email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
valid = ["xiaoju@example.com", "dev+test@mail.example.cn", "a_b@sub.domain.io"]
invalid = ["xiaoju@", "@example.com", "xiaoju@example", "xiaoju example.com"]

print("通过：", [item for item in valid if email_pattern.fullmatch(item)])
print("拒绝：", [item for item in invalid if not email_pattern.fullmatch(item)])


date_pattern = re.compile(
    r"(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12]\d|3[01])"
)
for text in ["2026-03-01", "2026-13-01", "2026-02-30", "2026-3-1"]:
    match = date_pattern.fullmatch(text)
    print(text, "→", match.groupdict() if match else "格式不匹配")


phone_pattern = re.compile(r"1[3-9]\d{9}")
samples = ["13812345678", "19900001111", "12812345678", "138-1234-5678", "1381234567"]
for text in samples:
    print(f"{text:<15}", bool(phone_pattern.fullmatch(text)))

cleaned = re.sub(r"[\s-]", "", "138-1234-5678")
print("先清洗再匹配：", cleaned, bool(phone_pattern.fullmatch(cleaned)))


url_pattern = re.compile(r"https?://[A-Za-z0-9.-]+(?::\d+)?(?:/[^\s]*)?")
text = "文档 https://example.com/docs?id=3 和 http://localhost:8010/admin 都可以"
print("提取：", url_pattern.findall(text))

for url in ["https://example.com", "ftp://example.com", "https://"]:
    print(f"{url:<25}", bool(url_pattern.fullmatch(url)))

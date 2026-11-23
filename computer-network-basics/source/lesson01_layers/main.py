from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
print("环境就绪")

message = "GET /course HTTP/1.1\r\nHost: example.local\r\n\r\n"
frame = message.encode("utf-8")
print("应用层：HTTP 报文", len(frame), "字节")
for layer, proto, overhead in [
    ("传输层", "TCP 头", 20),
    ("网络层", "IP 头", 20),
    ("网络接口层", "以太网帧头", 18),
]:
    frame = b"\x00" * overhead + frame
    print(f"{layer}：加上 {proto} {overhead} 字节，累计 {len(frame)} 字节")
print("最终在网线上传输的字节数：", len(frame))


def unwrap(frame):
    steps = [
        ("网络接口层", "去掉以太网头尾", 18),
        ("网络层", "去掉 IP 头", 20),
        ("传输层", "去掉 TCP 头", 20),
    ]
    size = len(frame)
    for layer, action, cut in steps:
        size -= cut
        print(f"{layer}：{action}，剩余 {size} 字节")
    payload = frame[18 + 20 + 20:]
    print("应用层看到的第一行：", payload.decode("utf-8").splitlines()[0])
    return payload


payload = unwrap(frame)
print("还原后的报文长度：", len(payload))


steps = [
    ("1. 解析域名", "DNS 把 example.local 变成 192.0.2.20（文档示例地址）"),
    ("2. 建立连接", "TCP 向 443 端口发起三次握手"),
    ("3. 协商加密", "TLS 握手，校验服务器证书"),
    ("4. 发送请求", "HTTP GET /course，带上 Host 和头部"),
    ("5. 接收响应", "状态码 200，正文分块返回"),
    ("6. 渲染页面", "浏览器解析 HTML、加载静态资源"),
]
for step, detail in steps:
    print(f"{step:<10}{detail}")

def add(a, b):
    return a + b

print("调用结果：", add(2, 3))


import dis

dis.dis(add)


print("源代码：def add(a, b): return a + b")
print("字节码长度：", len(add.__code__.co_code), "字节")
print("字节码十六进制：", add.__code__.co_code.hex())
print("指令序列：", [instruction.opname for instruction in dis.get_instructions(add)])


source = "result = 6 * 7"
code_object = compile(source, "<demo>", "exec")
namespace = {}
exec(code_object, namespace)

print("编译产物类型：", type(code_object).__name__)
print("执行结果：", namespace["result"])
print("字节码前 8 个字节：", code_object.co_code[:8].hex())


import platform
import sys

print("解释器实现：", platform.python_implementation())
print("语言版本：", ".".join(str(part) for part in sys.version_info[:2]))
print("实现名称：", sys.implementation.name)

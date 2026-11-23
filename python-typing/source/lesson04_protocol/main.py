class ConsoleNotifier:
    def send(self, message: str) -> None:
        print("控制台：", message)


class ListNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


def notify(notifier, messages: list[str]) -> None:
    for message in messages:
        notifier.send(message)


notify(ConsoleNotifier(), ["课程已更新", "记得交作业"])
box = ListNotifier()
notify(box, ["第一条"])
print(box.messages)


from typing import Protocol


class Notifier(Protocol):
    def send(self, message: str) -> None:
        ...


def notify_all(notifier: Notifier, messages: list[str]) -> None:
    for message in messages:
        notifier.send(message)


notify_all(ConsoleNotifier(), ["Protocol 只描述形状"])


from typing import runtime_checkable


@runtime_checkable
class Sized(Protocol):
    def __len__(self) -> int:
        ...


print(isinstance([1, 2, 3], Sized))
print(isinstance("python", Sized))
print(isinstance(42, Sized))


class BrokenNotifier:
    def send_message(self, message: str) -> None:
        print(message)


print("BrokenNotifier 有 send 方法吗：", hasattr(BrokenNotifier(), "send"))
try:
    notify_all(BrokenNotifier(), ["这条会失败"])
except AttributeError as exc:
    print(type(exc).__name__, exc)

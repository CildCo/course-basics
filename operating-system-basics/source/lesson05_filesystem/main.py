from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)


class Inode:
    def __init__(self, number, kind, mode, content=""):
        self.number = number
        self.kind = kind
        self.mode = mode
        self.content = content
        self.links = 1

    def __repr__(self):
        return f"Inode({self.number}, {self.kind})"


class MiniFS:
    def __init__(self):
        self.inodes = {1: Inode(1, "dir", 0o755, {})}
        self.next_number = 2

    def _new_inode(self, kind, mode, content):
        inode = Inode(self.next_number, kind, mode, content)
        self.inodes[inode.number] = inode
        self.next_number += 1
        return inode

    def _walk(self, path, create_dir=False):
        parts = [part for part in path.strip("/").split("/") if part]
        current = self.inodes[1]
        trail = [1]
        for part in parts:
            if current.kind != "dir":
                raise NotADirectoryError(path)
            if part not in current.content:
                if create_dir:
                    current.content[part] = self._new_inode("dir", 0o755, {}).number
                else:
                    raise FileNotFoundError(part)
            current = self.inodes[current.content[part]]
            trail.append(current.number)
        return current, trail

    def mkdir(self, path):
        return self._walk(path, create_dir=True)[0]

    def create(self, path, content):
        parent_path, name = path.rsplit("/", 1)
        parent = self.mkdir(parent_path)
        if name in parent.content:
            raise FileExistsError(path)
        inode = self._new_inode("file", 0o644, content)
        parent.content[name] = inode.number
        return inode

    def read(self, path):
        return self._walk(path)[0].content


fs = MiniFS()
notes = fs.create("/home/student/notes.txt", "第一行\n第二行\n")

print("文件内容：", fs.read("/home/student/notes.txt").strip())
print("文件 inode：", notes.number, "，链接数：", notes.links)

_, trail = fs._walk("/home/student/notes.txt")
print("路径解析经过的 inode：", " -> ".join(str(number) for number in trail))
print("根目录条目：", fs.inodes[1].content)
home = fs.inodes[fs.inodes[1].content["home"]]
print("home 的条目：", home.content)


def add_link(fs, old_path, new_path):
    inode = fs._walk(old_path)[0]
    parent_path, name = new_path.rsplit("/", 1)
    parent = fs.mkdir(parent_path)
    parent.content[name] = inode.number
    inode.links += 1
    return inode


def remove_entry(fs, path):
    parent_path, name = path.rsplit("/", 1)
    parent = fs._walk(parent_path)[0]
    inode = fs.inodes[parent.content.pop(name)]
    inode.links -= 1
    if inode.links == 0:
        del fs.inodes[inode.number]
    return inode


def add_symlink(fs, target, link_path):
    parent_path, name = link_path.rsplit("/", 1)
    parent = fs.mkdir(parent_path)
    inode = fs._new_inode("link", 0o777, target)
    parent.content[name] = inode.number
    return inode


def follow(fs, path):
    inode = fs._walk(path)[0]
    if inode.kind == "link":
        return fs._walk(inode.content)[0]
    return inode


copy = add_link(fs, "/home/student/notes.txt", "/home/student/copy.txt")
print("硬链接后 inode：", notes.number, copy.number, "，链接数：", copy.links)

remove_entry(fs, "/home/student/notes.txt")
print("删除原文件后 copy.txt 的内容：", fs.read("/home/student/copy.txt").strip())
print("剩余链接数：", copy.links)

shortcut = add_symlink(fs, "/home/student/copy.txt", "/home/student/shortcut")
print("符号链接自己的 inode：", shortcut.number, "，内容是目标路径：", shortcut.content)
print("跟随符号链接读到：", follow(fs, "/home/student/shortcut").content.strip())

remove_entry(fs, "/home/student/copy.txt")
try:
    follow(fs, "/home/student/shortcut")
except FileNotFoundError:
    print("目标删除后，符号链接变成悬空链接")


def mode_text(mode):
    letters = "rwxrwxrwx"
    return "".join(
        letter if mode & (1 << (8 - index)) else "-"
        for index, letter in enumerate(letters)
    )


ROLE_SHIFT = {"所有者": 6, "同组": 3, "其他人": 0}
ACTION_SHIFT = {"读": 2, "写": 1, "执行": 0}


def can_access(mode, role, action):
    return bool(mode & (1 << (ROLE_SHIFT[role] + ACTION_SHIFT[action])))


script = fs.create("/home/student/run.sh", "print('hello')\n")
script.mode = 0o755

for path in ["/home", "/home/student", "/home/student/run.sh"]:
    inode = fs._walk(path)[0]
    print(f"{path:<24} {mode_text(inode.mode)} ({oct(inode.mode)})")

for role in ["所有者", "同组", "其他人"]:
    allowed = [
        action for action in ["读", "写", "执行"]
        if can_access(script.mode, role, action)
    ]
    print(f"{role:<4} 对 run.sh 可以：{'、'.join(allowed) if allowed else '无'}")

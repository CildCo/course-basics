import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import json


def data_path(name):
    here = Path.cwd().resolve()
    for base in (here, *here.parents):
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"assets/{name}")


OUT = Path.cwd() / "output"
OUT.mkdir(exist_ok=True)
config = json.loads(data_path("plugins.json").read_text(encoding="utf-8"))
text = data_path("sample.txt").read_text(encoding="utf-8").strip()
print("插件配置:", data_path("plugins.json").relative_to(Path.cwd().parent).as_posix())
print("样本文本:", data_path("sample.txt").relative_to(Path.cwd().parent).as_posix())
print("样本长度:", len(text), "字符")


class Plugin:
    name = ""
    registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.name:
            return
        if cls.name in Plugin.registry:
            raise ValueError(f"插件名重复: {cls.name}")
        Plugin.registry[cls.name] = cls

    def run(self, text, config):
        raise NotImplementedError


class TextStats(Plugin):
    name = "text_stats"

    def run(self, text, config):
        chinese_chars = sum(1 for char in text if "一" <= char <= "鿿")
        return {
            "chars": len(text),
            "chinese_chars": chinese_chars,
            "lines": len(text.splitlines()),
        }


class KeywordScan(Plugin):
    name = "keyword_scan"

    def run(self, text, config):
        counts = {word: text.count(word) for word in config.get("keywords", [])}
        return {"hits": counts, "total": sum(counts.values())}


class LineStats(Plugin):
    name = "line_stats"

    def run(self, text, config):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        longest = max(lines, key=len) if lines else ""
        return {
            "non_empty_lines": len(lines),
            "longest_preview": longest[: config.get("limit", 40)],
        }


print("已注册插件:", sorted(Plugin.registry))


def build_plugins(config):
    ready = []
    skipped = []
    for item in config["plugins"]:
        name = item["name"]
        if not item.get("enabled", True):
            skipped.append({"name": name, "reason": "disabled"})
            continue
        cls = Plugin.registry.get(name)
        if cls is None:
            skipped.append({"name": name, "reason": "not registered"})
            continue
        ready.append((cls(), item.get("config", {})))
    return ready, skipped


ready, skipped = build_plugins(config)
print("就绪:", [plugin.name for plugin, _ in ready])
print("跳过:", skipped)


results = []
for plugin, settings in ready:
    try:
        value = plugin.run(text, settings)
        results.append({"name": plugin.name, "result": value})
    except Exception as exc:
        results.append({"name": plugin.name, "error": f"{type(exc).__name__}: {exc}"})

for row in results:
    print(row["name"], json.dumps(row["result"], ensure_ascii=False))


report = {
    "source": "assets/sample.txt",
    "enabled": [plugin.name for plugin, _ in ready],
    "skipped": skipped,
    "results": results,
}
(OUT / "plugin-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

summary_lines = [
    "插件系统报告",
    f"执行: {len(results)}",
    f"跳过: {len(skipped)}",
]
for row in results:
    summary_lines.append(f"- {row['name']}: {json.dumps(row['result'], ensure_ascii=False)}")
(OUT / "plugin-summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
print((OUT / "plugin-summary.txt").read_text(encoding="utf-8"))

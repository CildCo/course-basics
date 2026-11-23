"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_graph/main.py",
    "lesson02_bfs/main.py",
    "lesson03_dfs/main.py",
    "lesson04_dijkstra/main.py",
    "lesson05_dp_intro/main.py",
    "lesson06_knapsack/main.py",
    "lesson07_greedy_backtracking/main.py",
    "lesson08_route/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

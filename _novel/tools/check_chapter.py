#!/usr/bin/env python3
"""检查一章《断纱》正文是否符合硬性规则。

用法: python3 _novel/tools/check_chapter.py _novel/chapters/001.md
退出码 0 = 通过，1 = 有必须修改的问题。
"""
import re
import sys

BANNED = [
    "这一刻", "那一刻", "终于明白", "仿佛整个世界", "眼眶微微", "眼眶泛红",
    "嘴角勾起", "一抹微笑", "五味杂陈", "百感交集", "时间仿佛静止",
    "岁月的痕迹", "命运的齿轮", "这一切才刚刚开始", "她不知道的是",
    "他不知道的是", "你不知道的是",
]
SOFT_WORDS = ["仿佛", "似乎", "宛如"]
MIN_CHARS, MAX_CHARS = 2800, 3400


def main(path: str) -> int:
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    body = "\n".join(l for l in lines if not l.startswith("#"))
    problems, notes = [], []

    cjk = len(re.findall(r"[一-鿿]", body))
    notes.append(f"汉字数: {cjk}（目标 {MIN_CHARS}–{MAX_CHARS}）")
    if not MIN_CHARS <= cjk <= MAX_CHARS:
        problems.append(f"字数 {cjk} 超出 {MIN_CHARS}–{MAX_CHARS}")

    for q in ["“", "”", "「", "」", '"']:
        if q in body:
            problems.append(f"正文出现引号 {q}（对话不用引号）")

    for w in BANNED:
        if w in body:
            problems.append(f"禁用套话: {w}")

    soft = sum(body.count(w) for w in SOFT_WORDS)
    notes.append(f"仿佛/似乎/宛如 共 {soft} 次（上限 3）")
    if soft > 3:
        problems.append(f"仿佛/似乎/宛如 出现 {soft} 次，超过 3 次")

    if not lines or not re.match(r"^# 第.+章　.+", lines[0]):
        problems.append("第一行必须是 '# 第X章　章名'（全角空格）")

    for n in notes:
        print("·", n)
    if problems:
        print("✗ 需要修改：")
        for p in problems:
            print("  -", p)
        return 1
    print("✓ 通过硬性检查")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

#!/usr/bin/env python3
"""列出下一章要写的信息：章号、标题行、文件路径、大纲条目、需要参考的前文。

用法（仓库根目录）: python3 _novel/tools/next_chapter.py
"""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

NOVEL = Path(__file__).resolve().parents[1]
state = json.loads((NOVEL / "state.json").read_text(encoding="utf-8"))
outline = (NOVEL / "outline.md").read_text(encoding="utf-8")

DIGITS = "零一二三四五六七八九"


def cn(n: int) -> str:
    if n < 10:
        return DIGITS[n]
    tens, ones = divmod(n, 10)
    s = ("" if tens == 1 else DIGITS[tens]) + "十"
    return s + (DIGITS[ones] if ones else "")


entries = {}
for m in re.finditer(r"^### 第(\d+)章　(.+?)\n(.*?)(?=^### |^---|\Z)", outline, re.S | re.M):
    n = int(m.group(1))
    pov = re.search(r"- \*\*(\S+?) /", m.group(3))
    entries[n] = dict(title=m.group(2).strip(), body=m.group(0).strip(), pov=pov.group(1) if pov else "?")

N = state["last_published"] + 1
total = state["total_chapters"]
tz8 = timezone(timedelta(hours=8))
today = datetime.now(tz8).date().isoformat()

if N > total:
    print(f"全书 {total} 章已全部发布。无需写作。")
    raise SystemExit(0)

published_today = [e for e in state["log"] if e["published_at"][:10] == today]
if published_today:
    print(f"⚠ 今天（{today}）已经发布过：{published_today[-1]['title']}。默认不再更新。")

e = entries[N]
same_pov = [n for n in range(N - 1, 0, -1) if entries.get(n, {}).get("pov") == e["pov"]]
print(f"下一章：N = {N}")
print(f"标题行：# 第{cn(N)}章　{e['title']}")
print(f"文件：_novel/chapters/{N:03d}.md")
print(f"视角：{e['pov']}")
print(f"衔接参考：上一章 _novel/chapters/{N-1:03d}.md" if N > 1 else "衔接参考：（第一章，无）")
print(f"同视角参考：_novel/chapters/{same_pov[0]:03d}.md" if same_pov else "同视角参考：（本视角首次出场，按 style.md 示例定调）")
print("当前北京时间：", datetime.now(tz8).replace(microsecond=0).isoformat())
print("\n===== 大纲：本章 =====\n" + e["body"])
for k in (N + 1, N + 2):
    if k in entries:
        print(f"\n===== 大纲：第{k}章（仅作方向，不得提前写）=====\n" + entries[k]["body"])

#!/usr/bin/env python3
"""把 _novel/ 里已发布的章节生成静态网站（输出到仓库根目录）。

用法（在仓库根目录运行）: python3 _novel/tools/build_site.py
只依赖 Python 标准库。生成：index.html、c/NNN.html、feed.xml、assets/style.css、404.html
"""
import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOVEL = ROOT / "_novel"
SITE = json.loads((NOVEL / "site.json").read_text(encoding="utf-8"))
STATE = json.loads((NOVEL / "state.json").read_text(encoding="utf-8"))
TOTAL = STATE["total_chapters"]
TITLE = SITE["title"]

ROOFLINE = (
    '<svg class="roof" viewBox="0 0 600 28" preserveAspectRatio="none" aria-hidden="true">'
    '<path d="' + "".join(f"M{x},26 L{x},6 L{x + 30},26 " for x in range(0, 600, 30)) + '"/>'
    '<line x1="0" y1="26.5" x2="600" y2="26.5"/></svg>'
)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def parse_chapter(n: int):
    path = NOVEL / "chapters" / f"{n:03d}.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0].lstrip("#").strip()
    paras, buf = [], []
    for line in lines[1:]:
        if line.strip():
            buf.append(line.strip())
        elif buf:
            paras.append("".join(buf))
            buf = []
    if buf:
        paras.append("".join(buf))
    chars = sum(len(re.findall(r"[一-鿿]", p)) for p in paras)
    return title, paras, chars


def para_html(p: str) -> str:
    # 一苇的笔记条目（1. 2. / 待查： / 线索 / 物证）不缩进
    if re.match(r"^(\d+[\.、]|待查|线索|物证|备注|录音)", p):
        return f'<p class="note">{esc(p)}</p>'
    if p.startswith(">"):
        return f'<blockquote>{esc(p.lstrip("> ").strip())}</blockquote>'
    if p in ("* * *", "***", "——"):
        return '<hr class="knot">'
    return f"<p>{esc(p)}</p>"


def volume_of(n: int) -> str:
    for v in SITE["volumes"]:
        if v["from"] <= n <= v["to"]:
            return v["name"]
    return ""


def fmt_date(iso: str) -> str:
    d = datetime.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日"


def page(title: str, body: str, depth: int, desc: str = "", extra_head: str = "") -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or SITE['blurb'][:120])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc or SITE['blurb'][:120])}">
<link rel="stylesheet" href="{up}assets/style.css">
<link rel="alternate" type="application/atom+xml" title="{esc(TITLE)}" href="{up}feed.xml">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%23f6f1e7'/%3E%3Cpath d='M4 22 L4 10 L16 22 L16 10 L28 22' fill='none' stroke='%232a2622' stroke-width='2'/%3E%3Cline x1='4' y1='26' x2='28' y2='26' stroke='%23b8322a' stroke-width='2'/%3E%3C/svg%3E">
{extra_head}
</head>
<body>
{body}
<footer class="site-foot">
  <p><a href="{esc(SITE['blog_url'])}">回到博客 · {esc(SITE['blog_name'])}</a>　·　<a href="{up}feed.xml">订阅更新（RSS）</a></p>
  <p class="ai">{esc(SITE['ai_note'])}</p>
</footer>
</body>
</html>
"""


FONT_SCRIPT = """<script>
(function(){
  var root=document.documentElement, k='duansha-fs', v=null;
  try{v=localStorage.getItem(k);}catch(e){}
  if(v){root.style.setProperty('--fs',v+'px');}
  document.querySelectorAll('[data-fs]').forEach(function(b){
    b.addEventListener('click',function(){
      var cur=parseFloat(getComputedStyle(root).getPropertyValue('--fs'))||19;
      var next=Math.min(26,Math.max(15,cur+parseFloat(b.dataset.fs)));
      root.style.setProperty('--fs',next+'px');
      try{localStorage.setItem(k,String(next));}catch(e){}
    });
  });
})();
</script>"""


def build():
    published = sorted(STATE["log"], key=lambda e: e["chapter"])
    published = [e for e in published if e["chapter"] <= STATE["last_published"]]
    chapters = {}
    for e in published:
        n = e["chapter"]
        title, paras, chars = parse_chapter(n)
        chapters[n] = dict(title=title, paras=paras, chars=chars, date=e["published_at"])

    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "c").mkdir(exist_ok=True)
    (ROOT / "assets" / "style.css").write_text(CSS, encoding="utf-8")

    nums = sorted(chapters)
    last = nums[-1] if nums else None

    # ---- 章节页 ----
    for i, n in enumerate(nums):
        ch = chapters[n]
        prev_link = (
            f'<a href="{nums[i-1]:03d}.html">← 上一章</a>' if i > 0 else '<span class="dim">已是第一章</span>'
        )
        if i < len(nums) - 1:
            next_link = f'<a href="{nums[i+1]:03d}.html">下一章 →</a>'
        elif n < TOTAL:
            next_link = f'<span class="dim">下一章　{esc(SITE["update_note"].split("，")[-1])}</span>'
        else:
            next_link = '<span class="dim">全书完</span>'
        body = f"""<header class="bar">
  <a class="brand" href="../index.html">{esc(TITLE)}</a>
  <span class="tools"><button data-fs="-1" aria-label="缩小字号">A−</button><button data-fs="1" aria-label="放大字号">A+</button><a href="../index.html#toc">目录</a></span>
</header>
<main class="chapter">
  {ROOFLINE}
  <p class="vol">{esc(volume_of(n))}</p>
  <h1>{esc(ch['title'])}</h1>
  <p class="meta">{fmt_date(ch['date'])}　·　{ch['chars']} 字</p>
  <article>
{chr(10).join('    ' + para_html(p) for p in ch['paras'])}
  </article>
  <div class="end" aria-hidden="true"></div>
  <nav class="pager">{prev_link}<a href="../index.html#toc">目录</a>{next_link}</nav>
</main>
{FONT_SCRIPT}"""
        (ROOT / "c" / f"{n:03d}.html").write_text(
            page(f"{ch['title']} · {TITLE}", body, 1, desc=ch["paras"][0][:100] if ch["paras"] else ""),
            encoding="utf-8",
        )

    # ---- 目录页 ----
    status = "全书完" if last == TOTAL else "连载中"
    count = len(nums)
    words = sum(c["chars"] for c in chapters.values())
    toc_parts = []
    for v in SITE["volumes"]:
        items = [n for n in nums if v["from"] <= n <= v["to"]]
        if not items:
            continue
        lis = "\n".join(
            f'      <li><a href="c/{n:03d}.html"><span class="t">{esc(chapters[n]["title"])}</span>'
            f'<span class="d">{fmt_date(chapters[n]["date"])[5:]}</span></a></li>'
            for n in items
        )
        toc_parts.append(f'    <h2>{esc(v["name"])}</h2>\n    <ol>\n{lis}\n    </ol>')
    if nums:
        cta = (
            f'<a class="btn primary" href="c/{nums[0]:03d}.html">从第一章读起</a>'
            + (f'<a class="btn" href="c/{last:03d}.html">最新：{esc(chapters[last]["title"])}</a>' if last != nums[0] else "")
        )
    else:
        cta = '<span class="dim">第一章即将发布</span>'
    body = f"""<main class="home">
  {ROOFLINE}
  <h1 class="book">{esc(TITLE)}</h1>
  <p class="meta">长篇小说　·　{status}　·　已更新 {count} / {TOTAL} 章　·　{words} 字</p>
  <p class="blurb">{esc(SITE['blurb'])}</p>
  <p class="cta">{cta}</p>
  <p class="meta small">{esc(SITE['update_note'])}</p>
  <section id="toc" class="toc">
{chr(10).join(toc_parts)}
  </section>
</main>"""
    (ROOT / "index.html").write_text(page(f"{TITLE} · 长篇小说", body, 0), encoding="utf-8")

    # ---- 404 ----
    (ROOT / "404.html").write_text(
        page(f"找不到页面 · {TITLE}", f'<main class="home">{ROOFLINE}<h1 class="book">断头了</h1>'
             f'<p class="blurb">这一页不存在。<a href="/duansha/">回到目录</a></p></main>', 0),
        encoding="utf-8",
    )

    # ---- Atom feed ----
    base = SITE["site_url"]
    updated = chapters[last]["date"] if nums else datetime.now().astimezone().isoformat()
    entries = []
    for n in reversed(nums[-20:]):
        ch = chapters[n]
        content = "".join(para_html(p) for p in ch["paras"])
        entries.append(f"""  <entry>
    <title>{esc(ch['title'])}</title>
    <link href="{base}c/{n:03d}.html"/>
    <id>{base}c/{n:03d}.html</id>
    <updated>{ch['date']}</updated>
    <content type="html">{esc(content)}</content>
  </entry>""")
    feed = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{esc(TITLE)}</title>
  <subtitle>{esc(SITE['blurb'])}</subtitle>
  <link href="{base}"/>
  <link rel="self" href="{base}feed.xml"/>
  <id>{base}</id>
  <updated>{updated}</updated>
  <author><name>{esc(SITE['blog_name'])}</name></author>
{chr(10).join(entries)}
</feed>
"""
    (ROOT / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"built: {count} chapters, {words} chars → index.html, c/, feed.xml")


CSS = """:root{
  --paper:#f6f1e7; --ink:#2a2622; --muted:#857c71; --line:#ddd3c1; --thread:#b8322a; --card:#efe8da;
  --fs:19px;
  --serif:"Songti SC","STSong","Noto Serif CJK SC","Noto Serif SC","Source Han Serif SC","Source Han Serif CN","SimSun",serif;
  --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){--paper:#1c1b19;--ink:#ddd5c8;--muted:#8e867a;--line:#35322c;--thread:#d25a4f;--card:#24221f;color-scheme:dark;}
}
:root[data-theme="dark"]{--paper:#1c1b19;--ink:#ddd5c8;--muted:#8e867a;--line:#35322c;--thread:#d25a4f;--card:#24221f;color-scheme:dark;}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);line-height:1.9}
a{color:inherit;text-decoration-color:var(--line);text-underline-offset:.25em}
a:hover{color:var(--thread);text-decoration-color:var(--thread)}
.dim{color:var(--muted)}
.roof{display:block;width:100%;height:28px;margin:0 0 2.2rem}
.roof path{fill:none;stroke:var(--muted);stroke-width:1.2;vector-effect:non-scaling-stroke}
.roof line{stroke:var(--thread);stroke-width:1.5;vector-effect:non-scaling-stroke}

/* 顶栏 */
.bar{position:sticky;top:0;z-index:2;display:flex;justify-content:space-between;align-items:center;gap:1rem;
  padding:.6rem 16px;background:var(--paper);background:color-mix(in srgb,var(--paper) 92%,transparent);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line);font-family:var(--sans);font-size:14px}
.brand{font-family:var(--serif);font-size:17px;letter-spacing:.3em;text-decoration:none}
.tools{display:flex;align-items:center;gap:.4rem}
.tools button{font:inherit;color:var(--muted);background:none;border:1px solid var(--line);border-radius:4px;padding:.15rem .5rem;cursor:pointer}
.tools button:hover{color:var(--thread);border-color:var(--thread)}
.tools a{color:var(--muted);text-decoration:none;margin-left:.4rem}

/* 目录页 */
.home{max-width:40rem;margin:0 auto;padding:3rem 16px 2rem}
.book{font-size:clamp(2.6rem,9vw,3.6rem);font-weight:600;letter-spacing:.5em;margin:0 0 .6rem;line-height:1.3}
.meta{font-family:var(--sans);font-size:13px;color:var(--muted);margin:.2rem 0}
.meta.small{font-size:12px}
.blurb{font-size:17px;line-height:2;margin:1.8rem 0;text-align:justify}
.cta{display:flex;flex-wrap:wrap;gap:.6rem;margin:1.6rem 0 .6rem}
.btn{display:inline-block;font-family:var(--sans);font-size:14px;padding:.55rem 1.1rem;border:1px solid var(--ink);border-radius:999px;text-decoration:none}
.btn.primary{background:var(--ink);color:var(--paper)}
.btn.primary:hover{background:var(--thread);border-color:var(--thread);color:#fff}
.toc{margin-top:3rem;border-top:1px solid var(--line)}
.toc h2{font-size:15px;font-weight:600;letter-spacing:.2em;color:var(--muted);margin:2rem 0 .6rem}
.toc ol{list-style:none;margin:0;padding:0}
.toc li a{display:flex;justify-content:space-between;gap:1rem;padding:.7rem 0;border-bottom:1px dashed var(--line);text-decoration:none}
.toc .d{font-family:var(--sans);font-size:12px;color:var(--muted);white-space:nowrap;align-self:center}

/* 章节页 */
.chapter{max-width:36rem;margin:0 auto;padding:2.4rem 16px 2rem}
.vol{font-family:var(--sans);font-size:12px;letter-spacing:.3em;color:var(--muted);margin:0}
.chapter h1{font-size:clamp(1.6rem,6vw,2rem);font-weight:600;letter-spacing:.12em;margin:.4rem 0 .4rem;line-height:1.4}
.chapter .meta{margin-bottom:2.4rem}
article{font-size:var(--fs);line-height:2.05;text-align:justify;hyphens:auto}
article p{margin:0 0 1.05em;text-indent:2em}
article p.note{text-indent:0;padding-left:.2em}
article blockquote{margin:1.2em 0;padding:.2em 0 .2em 1em;border-left:2px solid var(--thread);color:var(--muted)}
hr.knot{border:0;height:1px;width:3rem;margin:2em auto;background:var(--thread)}
.end{width:3rem;height:2px;background:var(--thread);margin:2.6rem auto 2.2rem}
.pager{display:flex;justify-content:space-between;align-items:center;gap:.8rem;font-family:var(--sans);font-size:14px;
  border-top:1px solid var(--line);padding-top:1.2rem}
.pager a{text-decoration:none}

.site-foot{max-width:40rem;margin:2rem auto 0;padding:1.6rem 16px 3rem;border-top:1px solid var(--line);
  font-family:var(--sans);font-size:12px;color:var(--muted);text-align:center}
.site-foot p{margin:.3rem 0}
.site-foot a{text-decoration:none}
@media (max-width:420px){ :root{--fs:18px} .book{letter-spacing:.35em} }
"""

if __name__ == "__main__":
    build()

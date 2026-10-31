# 《断纱》写一章、发一章的流程

> 按需更新：用户说"写下一章""更新""发表"之类的话时，严格按本文件执行。仓库：`qinghuidaqzp/duansha`；网站：https://qinghuidaqzp.github.io/duansha/
> 用户说几章就写几章，每一章都完整走一遍第 0–6 步，最后统一做第 7 步。所有路径相对仓库根目录。
> 新会话里先调用 add_repo（owner: qinghuidaqzp, repo: duansha, access: push）并按返回说明克隆仓库。

## 0. 确定要写哪一章
运行 `python3 _novel/tools/next_chapter.py`。它会给出：章号 N、标题行、文件名、视角、要参考的前文、本章和后两章的大纲条目、当前北京时间。

- 输出"全书已全部发布" → 不写作，告诉用户全书已完结，结束。
- 输出"⚠ 今天已经发布过"只是提示，用户要求更新就照常写。
- 用户如果只说"写"没说"发"，写完自检后先把正文发给用户看，等确认再做第 4–6 步。

## 1. 读材料（全部读完再动笔）
1. `_novel/bible.md` 全文
2. `_novel/style.md` 全文
3. 第 0 步输出的大纲条目（后两章只作方向参考，**不得提前写**）
4. `_novel/summaries.md` 全文
5. `_novel/continuity.md` 全文
6. 上一章正文全文（衔接时间、情绪）
7. 第 0 步给出的"同视角参考"章节正文全文（保持人物的声音）

## 2. 写作
动笔前先想清楚（不必写出来）：
- 当下锚点：具体时间、地点、持续多久
- 3–5 次记忆跳转，各自的触发物（声音、气味、物件、词）
- 本章用到的母题
- 本章**允许**揭示什么、**不得**揭示什么（对照 bible 第四节的章节进度）
- 结尾落点（画面或动作）

然后写入第 0 步给出的文件 `_novel/chapters/NNN.md`：
- 第一行用第 0 步给出的标题行（`# 第X章　章名`，全角空格）
- 段落之间空一行；对话不用引号
- 一苇的章节：笔记条目每条单独成段，以 `1.` `2.` 或 `待查：` `线索：` `物证：` 开头

## 3. 自检与修改（至少一轮，认真做）
1. 运行 `python3 _novel/tools/check_chapter.py _novel/chapters/NNN.md`，必须通过。
2. 从头通读一遍，逐条核对并修改：
   - 人称与文体是否符合本章视角（bible 第五节）
   - 与 bible、continuity、前文有无事实矛盾：人名、年龄、日期、地点、物件、秀英的病程阶段
   - 有没有提前泄露后文才揭示的秘密
   - 有没有禁止的套话、说教、点题、比喻泛滥（style.md）
   - 有没有至少一个扎实的现实细节场景
   - 结尾是否落在画面或动作上
3. 改完再跑一次检查脚本。

## 4. 更新记录
- `_novel/summaries.md` 末尾追加：`## 第X章　章名（视角｜故事时间）` + 150–250 字摘要（发生了什么、人物状态变化、埋下的线索）。
- `_novel/continuity.md` 末尾追加 `## 第X章`，列出本章新确立、后文必须保持一致的具体事实；没有就写"无新增"。
- `_novel/state.json`：`last_published` 改为 N；`log` 末尾追加
  `{"chapter": N, "title": "第X章　章名", "published_at": "<第 0 步输出的北京时间>"}`。

## 5. 生成网站并推送
```
python3 _novel/tools/build_site.py
git config user.name "qinghuidaqzp"
git config user.email "qinghuidaqzp@users.noreply.github.com"
git add -A
git commit -m "连载：第X章　章名"     # 不要加任何 Co-Authored-By 或 Claude 署名行（仓库主人要求贡献者里不出现 Claude）
git push origin main
```
- 推送被拒（非快进）：`git pull --rebase origin main` 后再推一次。
- 推送仍失败（如授权失效、403）：不要再试，第 7 步把原因告诉用户（多半需要在 GitHub 上重新授权 Claude 应用访问 duansha 仓库），结束。

## 6. 确认上线
推送后等约 1–2 分钟（用 Monitor 等待，不要用前台 sleep），查询 GitHub Pages 的部署任务：
```
gh api "repos/qinghuidaqzp/duansha/actions/runs?per_page=1&head_sha=$(git rev-parse HEAD)" \
  --jq '.workflow_runs[0] | "\(.name) \(.status) \(.conclusion)"'
```
期望 `pages build and deployment completed success`。若还是 `queued`/`in_progress`，再等一分钟查一次（最多 3 次）。若 `failure`，在第 7 步告诉用户。若查不到任何记录，说明 Pages 可能被关闭了，提醒用户到仓库 Settings → Pages 检查。
（沙箱网络打不开 github.io 网页本身；Pages 的 API 路径也被代理拦截，所以以部署任务状态为准。）

## 7. 告诉用户
用 SendUserMessage 发一条简短消息，格式：

> 《断纱》第X章《章名》已发布（N/60）
> 链接：https://qinghuidaqzp.github.io/duansha/c/NNN.html
> 一句话介绍本章（不剧透），字数。

有异常（构建失败、推送失败、大纲冲突）就在消息里说清楚。

## 规则
- 只改 `_novel/chapters/`、`summaries.md`、`continuity.md`、`state.json` 和生成的网站文件（`index.html`、`c/`、`feed.xml`、`assets/`、`404.html`）。
- **不改** `bible.md`、`outline.md`、`style.md`、`site.json`、`tools/`、本文件——它们由人工维护。
- 发现大纲与已发布正文冲突时，以已发布正文为准继续写，在 continuity.md 记一笔，并在给用户的消息里提一句。

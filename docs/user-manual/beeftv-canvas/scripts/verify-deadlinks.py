#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第一道闸：站内死链核对（发布产物里的每个 href 是否真的可达）。

**为什么要有这道闸**：VitePress 的 `ignoreDeadLinks` 会放过指向 `srcExclude` 文件的链接
（如被排除的 `PUBLISH.md` / `task-inventory.yml`），**发布后就是 404**。
所以逐个解析 href 兜底，而不是相信构建器的检查。

## Batch 168：从 `build-site.sh` 的 heredoc 抽出来

原先它是内联在 `build-site.sh` 里的一段 `python3 - <<'PYEOF' … || true`。抽出有两个理由，
**第二个比第一个更要紧**：

1. **它因此无法被反向验证**——十道闸里唯独它一道没有反验（Batch 167 普查）。
   批次的整个主题是「每道闸都要有反验」，把它留在 shell 里就等于留一个没人验过的洞。
2. **它把「工具失败」当成「没有问题」**：`python3 … 2>/dev/null || true` 一旦失败，
   `DEAD_REPORT` 为空 → `DEAD_COUNT` 取到 0 → 输出「站内链接全部可达」。
   **这与 Batch 157 的「工具失败被当成零命中」是同一个病，藏在唯一没人反验的那道闸里。**

顺带修掉第三处 cwd 依赖：`DIST` 原本是相对路径，现在由 `__file__` 推导
（闸 9 的方向十照不到 heredoc，但危害完全一样）。

退出码：0 无死链；1 有死链；2 未能核对（dist 不存在 / 一个 html 都没扫到）。
"""

import os
import re
import sys
from urllib.parse import urldefrag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, ".vitepress", "dist")

HREF_RE = re.compile(r'href="([^"]+)"')
SKIP_PREFIX = ("http", "mailto:", "data:", "#")


def collect():
    exists = set()
    pages = []
    for root, _, files in os.walk(DIST):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), DIST).replace("\\", "/")
            exists.add(rel)
            if f.endswith(".html"):
                pages.append(os.path.join(root, f))
    dead = set()
    for path in pages:
        page = os.path.relpath(path, DIST).replace("\\", "/")
        base = os.path.dirname(page)
        with open(path, encoding="utf-8", errors="ignore") as fh:
            html = fh.read()
        for href in HREF_RE.findall(html):
            if href.startswith(SKIP_PREFIX):
                continue
            target = urldefrag(href)[0]
            if not target:
                continue
            # ⚠️ Batch 168：**结尾斜杠必须在归一化之前记下来**。
            # 原写法先 normpath 再判 `target.endswith("/")`，而 normpath 会把结尾斜杠**吃掉**，
            # 于是**相对**目录链接（`guide/`）被当成「名叫 guide 的文件」去找 → **误报死链**。
            #
            # **这里纠正过一个过头结论**：我一度写「那条分支是货真价实的死代码」，
            # 拿数据一对就站不住——**绝对** href（`/guide/`）走的是 `lstrip("/")` 分支、
            # 不经 normpath，结尾斜杠还在，**旧逻辑本来就判对**。
            # 实测对照（旧 / 新）：`guide/` 旧=guide(误报) 新=guide/index.html(对)，
            # `/guide/` 旧=新=guide/index.html(都对)。**真缺陷是两种 href 形态行为不一致**，
            # 不是分支没被写到。
            #
            # 为什么一直没被发现：手册正文里**一条内部链接都不带结尾斜杠**，
            # 所以这条分支**从未被触发过**——**「全绿」不代表规则被验证过，
            # 只代表它没被触发过。** 手册约定用 `.md` 相对链接（闸 9 方向六强制），
            # 于是这个缺陷在当前手册里**没有实际影响**，但它是一颗哑弹：
            # 谁在产物页里写一个目录链接就会被误报。
            #
            # ⚠️ 第一版修法又引入了新错：对 `href="/"` 而言，
            # 归一化成 "" 之后已被改成 `index.html`，**再追加一次就变成 index.html.html**，
            # 于是真实产物里 35 个页面全部误报。**顺序必须写成互斥的分支，不能叠加。**
            trailing_slash = target.endswith("/")
            if target.startswith("/"):
                target = target.lstrip("/")
            else:
                target = os.path.normpath(os.path.join(base, target))
            target = target.replace("\\", "/")
            # "/" 与 "./" 都解析到站点根 index.html
            if target in ("", ".", ".."):
                target = "index.html"
            elif trailing_slash and not target.endswith("index.html"):
                target = target.rstrip("/") + "/index.html"
            if target not in exists:
                dead.add(f"{page} -> {href}")
    return dead, len(pages)


def main():
    if not os.path.isdir(DIST):
        print(f"[skip] 未找到 {DIST}（尚未构建），站内死链核对本轮未能进行")
        return 2
    dead, n_pages = collect()
    # 一个 html 都没扫到 = 产物是空的或读不动，**不是「没有死链」**
    if n_pages == 0:
        print("[skip] 产物里一个 html 都没有，站内死链核对本轮未能进行")
        return 2
    if dead:
        print(f"站内死链核对：{n_pages} 个页面中发现 {len(dead)} 处不可达链接")
        for d in sorted(dead):
            print("  " + d)
        return 1
    print(f"站内死链核对通过：{n_pages} 个页面的 href 逐个解析后全部可达"
          f"（VitePress 的 ignoreDeadLinks 放过的那类也已兜住）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

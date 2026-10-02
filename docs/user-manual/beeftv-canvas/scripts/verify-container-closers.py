#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十八道闸：`:::` 闭合符**不得多于**开容器（嵌套深度不得为负）。

背景（Batch 231）：手册用 VitePress 自定义容器（`::: warning` / `::: tip` / `::: danger`）
做提示块。本批去查一个**悬了五个批次的旧问题**：`storage-quota.md` 的容器在文本层面
「7 开 6 闭」不配对，而 dist 渲染看起来正常——**原因不明，当时记下「不动」**。

**查清楚了，而且结论与直觉相反。** 用手册自带的 vitepress 1.6.4 管线做最小实验
（`createMarkdownRenderer`，四种形态）：

  ① 外层欠一个 `:::`（现状）  → 渲染**完全正常**，0 个字面量。
     **markdown-it-container 会自动闭合没关掉的容器。**
  ② 补一个 `:::`（「修好配对」）→ 多出来那个没有容器可关，
     **被当作正文渲染成 `<p>:::</p>`，读者在页面上看得见。**
  ③ 补两个 → 同样漏出 2 个字面量。
  ④ 单层欠一个（无嵌套）→ 同样自动闭合，干净。

**所以「配对」不是缺陷，恰恰是「不配对」里少的那一个方向才是安全的那个方向。**
本批自己踩了这个坑：先按「结构上应该配平」的直觉给 3 处补了 `:::`，
**重建后一 diff 才发现每一页都多出了读者可见的字面 `:::`**，
随即 `git checkout --` 回退。**是渲染结果的 diff 救了它，不是结构推理。**

**本闸因此只抓一个方向：深度不得为负。**
  · 少一个闭合符 → **放行**（渲染器自动闭合，读者看不到任何东西）；
  · 多一个闭合符 → **报**（它会变成正文，读者看得见）。

**为什么必须是「嵌套深度」而不是「开闭计数」**：
计数只看得见差值，看不见顺序。`开1闭1开1闭0` 与 `开1闭0闭1开1闭0` 的计数一样，
可前者没问题、后者多了一个孤立的 `:::`。本闸逐行维护一个深度计数，
**只在深度要变负的那一刻报，并指出那一行的行号**。

**为什么不算「欠闭合」**（这是本闸最重要的一条取舍）：
它无害、有渲染器兜底，而**为了让判据变绿去补闭合符，反而会制造读者可见的缺陷**
——本批亲身验证过。**一个会把正确的东西报成缺陷的判据，比没有判据更糟。**

容器可以嵌在列表项里（`- ::: warning …` / 缩进的 `  :::`），
第一版探针要求行首就是 `:::`，**把 6 个正常页面报成不配对**——
**探针的错误长得极像被测对象的错误**（Batch 225 记过一次，这里又撞上）。
本闸的两种形态都认。

退出码：0 通过；1 有闭合符没有对应容器；2 未能核对（正文页读不到足够多）。
"""

import os
import re
import sys

# 开容器：行首可有缩进、可有列表标记，后面必须跟内容（标题或类型名）
OPEN_RE = re.compile(r"^\s*(?:[-*+]\s+)?(:{3,})\s*(\S.*)$")
# 闭合符：整行只有若干个冒号
CLOSE_RE = re.compile(r"^\s*(:{3,})\s*$")

CONTENT_PAGES = ("00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md")

# 扫到的开容器数量下限。**低于它就报「未能核对」，不许报「通过」**（纪律 156）。
# 真实值 97，取 30 留足余量，又足以抓住「页面集合写错 / 扫空」这类整片失效。
MIN_BLOCKS = 30


def strip_fenced(text):
    """挖空围栏代码块但**保留行数**——报错要带 `:行号`，行号必须对得上原文。"""
    out, in_fence, fence = [], False, None
    for line in text.split("\n"):
        m = re.match(r"^[ \t]*(```|~~~)", line)
        if m:
            if not in_fence:
                in_fence, fence = True, m.group(1)
            elif m.group(1) == fence:
                in_fence, fence = False, None
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def content_pages(root):
    """手册的正文页（与闸 26 / 27 同一套范围口径）。"""
    out = []
    for base in CONTENT_PAGES:
        p = os.path.join(root, base)
        if os.path.isfile(p):
            out.append(p)
    task_dir = os.path.join(root, "10-tasks")
    if os.path.isdir(task_dir):
        for name in sorted(os.listdir(task_dir)):
            if name.endswith(".md"):
                out.append(os.path.join(task_dir, name))
    return out


def scan(path, rel):
    """返回 (多余闭合符列表, 开容器数, 结束时未闭合的层数)。"""
    body = strip_fenced(open(path, encoding="utf-8", errors="ignore").read())
    depth = 0
    opens = 0
    extra = []
    for lineno, line in enumerate(body.split("\n"), 1):
        mo, mc = OPEN_RE.match(line), CLOSE_RE.match(line)
        if mo:
            # `::::`（4 个冒号）开一层，`:::`（3 个）也开一层——VitePress 用冒号个数分层
            depth += 1
            opens += 1
        elif mc:
            if depth == 0:
                extra.append((lineno, len(mc.group(1))))
            else:
                depth -= 1
    return extra, opens, depth


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pages = content_pages(root)
    if len(pages) < 10:
        print(f"[未能核对] 只找到 {len(pages)} 个正文页（下限 10），输入范围明显不对")
        return 2

    problems, unclosed = [], []
    total_opens = 0
    for page in pages:
        rel = os.path.relpath(page, root)
        extra, opens, depth = scan(page, rel)
        total_opens += opens
        for lineno, n in extra:
            problems.append(
                f"{rel}:{lineno} 这一行有 {n} 个冒号，**但此刻没有容器可关**"
                f"（前面的容器都已闭合）——markdown-it-container 会把它当正文渲染成 "
                f"`<p>:::</p>`，**读者在页面上看得见**"
            )
        if depth:
            unclosed.append((rel, depth))

    if total_opens < MIN_BLOCKS:
        print(f"[未能核对] 只扫到 {total_opens} 个开容器（下限 {MIN_BLOCKS}）"
              f"——本闸本轮什么也没检查，**不能按「没有多余闭合符」通过**")
        return 2

    if problems:
        print(f"自定义容器闭合核对：{total_opens} 个开容器，{len(problems)} 处闭合符没有对应容器")
        for x in problems:
            print("  ✗ " + x)
        print("  → 删掉多余的 `:::`，**不要为了「配平」去补**（Batch 231 实测：补上去的"
              "闭合符会变成正文显示给读者）")
        return 1

    print(f"自定义容器闭合核对：{total_opens} 个容器，没有多余的闭合符"
          f"（{len(pages)} 个正文页）")
    if unclosed:
        # **少闭合是安全的**（渲染器自动闭合，读者看不到）——如实说出来，
        # **但绝不把它报成问题**，更不能建议「补一个」：实测补了就出事。
        detail = "、".join(f"{r} 欠 {d} 层" for r, d in unclosed)
        print(f"  另有 {len(unclosed)} 处**少**了闭合符（{detail}）——"
              f"**这一侧渲染器会自动闭合、读者看不到，本闸有意不管**；"
              f"补上去反而会让 `:::` 作为正文出现在页面上（Batch 231 实测）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

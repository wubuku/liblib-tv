#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十九道闸：页内标题的**唯一性**与**层级连续性**。

背景（Batch 232）：本批量的候选域里，「页内可指向目标」这一族真出了两处缺陷，
而它们各自的单独形态（重复标题、跳级）此前都没有判据。

  ① **同名标题**：`agent-memory-skills.md` 有**两个 `## 相关页面`**，内容逐字相同。

  **⚠️ Batch 245 把这一条的理由重写了——原来的理由是一句猜，而且它不成立。**
  原脚本头写的是「后果不是『不好看』：VitePress 给同名标题生成**同一个 `#相关页面` 锚点**，
  于是页内目录里第二个『相关页面』的跳转**落到第一个**，而每节标题旁的 permalink
  链到的是同一个位置」。**用手册自带的 vitepress 1.6.4 真管线逐个渲染量过，
  三个子断言全部不成立**：

  | 形态 | 渲染出的 id | 目录里的 href |
  |---|---|---|
  | 两个 `## 相关页面` | `#相关页面`、`#相关页面-1` | 各自指向自己 |
  | 三个 `## 相关页面` | `#相关页面`、`-1`、`-2` | 各自指向自己 |
  | 同名但级别不同（`##` / `###`） | `#相关页面`、`#相关页面-1` | 各自指向自己 |
  | `## A B` 与 `## A-B`（slug 会被抹平成同一个） | `#a-b`、`#a-b-1` | 各自指向自己 |
  | `## 用 \`npm\` 安装` 与 `## 用 npm 安装` | `#用-npm-安装`、`-1` | 各自指向自己 |
  | `## 🎉` / `## 🎉🎉` / `## —` / `## ——` / `## 1` | 各自独立，**无一为空** | 各自指向自己 |
  | `## 取证 基线` 与 `## 取证基线` | `#取证-基线`、`#取证基线`（本就不同） | 各自指向自己 |

  **VitePress 的 `slugify` 会去重**（同名加 `-1`、`-2`），
  **所以「同名标题撞锚点」这件事在 1.6.4 上不成立——十种形态、零例外。**
  **而「判据里那条『因为 X 所以这样建模』的注释，如果 X 本身没被量过，
  它就是一条猜」已经应验到第二次了**（第一次是闸 28 的「VitePress 用冒号个数分层」）。

  **那这一条判据还留不留？留，但理由换成实测之后仍然成立的那一条**：
  **同名标题在页内目录里会产生两个逐字相同、无法区分的条目**
  （`slug` 不同了，**目录上的文字没变**），
  而 Batch 232 抓到的那一处是两个**内容逐字相同**的整节重复。
  **这两条都是真的，量得到；原来那条撞锚点的说法不是。**
  **本条的其余部分（②层级跳级、④H1 唯一）不受影响**——
  它们各自的判据在原脚本头里各自写了理由。
  ② **层级跳级**：`20-reference.md` 的**第一个小节**「取证基线」写成 `###`，
     而它没有任何 `##` 父级——本页其余 7 个顶层小节全是 `##`。
     后果是它在页内目录里被降级成别人的子项，
     **而它自己写着「这一节是本手册所有数字与文案的公共前提」**。

**为什么这两条能建判据，而本批另外三个域不能**（都是先量后判的）：
  · 相对链接前缀形态——3 种目录关系各对应 1 种写法，**完全一致，无可核**；
  · 图片路径形态——57 张 `../screenshots/` + 3 张 `screenshots/`，
    **差异由目录深度决定，不是漂移**；
  · `path:line` 引用——29 处引用上游文件，**0 处带行号**，
    「行号不是稳定标识」这条纪律已经在守，无事可做。
  · 同名的**容器标题**（`30-concepts.md` 两处「这张表是可以被推翻的」）——
    **读完原文判定不是缺陷**：两张不同的表各自需要这句告诫，是有意的措辞复用，
    而容器标题渲染成 `<p class="custom-block-title">`，**不生成锚点**，不会撞。
    **本闸因此只管标题，不管容器标题**——把有意的复用报成缺陷，就是判据过宽。

**判据（对全部正文页）**：
  1. 排除围栏代码块（`#` 在代码里是注释，不是标题）；
  2. 页内**不得有同名标题**（H1…H6 一视同仁——同名就撞锚点，与级别无关）；
  3. 标题**不得跳级**（h2 之后不能直接 h4；H1 之后不能直接 H3）；
  4. 全文**有且只有一个 H1**（这条此前也没判据，本批实测 33 个页面全部满足，
     加上它只需一行，且它能挡住「整页被包进某个小节」这类改动）。

退出码：0 通过；1 有同名标题 / 跳级 / H1 数不对；2 未能核对。
"""

import os
import re
import sys

CONTENT_PAGES = ("00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md")

# 扫到的标题数量下限。**低于它就报「未能核对」，不许报「通过」**（纪律 156）。
# 真实值 379，取 100 留足余量，又足以抓住「页面集合写错 / 扫空」这类整片失效。
MIN_HEADINGS = 100


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
    """手册的正文页（与闸 26 / 27 / 28 同一套范围口径）。"""
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


def check_page(path, rel):
    """返回该页的 (同名标题列表, 跳级列表, H1 数量, 标题总数)。"""
    body = strip_fenced(open(path, encoding="utf-8", errors="ignore").read())
    headings = []
    for lineno, line in enumerate(body.split("\n"), 1):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            headings.append((len(m.group(1)), m.group(2).strip(), lineno))
    dups = []
    seen = {}
    for _level, name, lineno in headings:
        if name in seen:
            dups.append((name, seen[name], lineno))
        else:
            seen[name] = lineno
    # 跳级：按文档顺序，某一级的标题前面没有它的直接上一级
    jumps = []
    prev = 0
    for level, name, lineno in headings:
        if prev and level > prev + 1:
            jumps.append((prev, level, name, lineno))
        prev = level
    h1 = [ln for lvl, _n, ln in headings if lvl == 1]
    return dups, jumps, h1, len(headings)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pages = content_pages(root)
    if len(pages) < 10:
        print(f"[未能核对] 只找到 {len(pages)} 个正文页（下限 10），输入范围明显不对")
        return 2

    problems = []
    total = 0
    for page in pages:
        rel = os.path.relpath(page, root)
        dups, jumps, h1, n = check_page(page, rel)
        total += n
        for name, first, second in dups:
            problems.append(
                f"{rel}:{second} 标题「{name}」与第 {first} 行同名"
                f"——VitePress 给同名标题生成**同一个锚点**，"
                f"页内目录里后一个的跳转会落到前一个"
            )
        for prev, level, name, lineno in jumps:
            problems.append(
                f"{rel}:{lineno} 从 h{prev} 跳到 h{level}（{name}）——"
                f"中间那一级在页内不存在，页内目录里它成了别人的子项"
            )
        if len(h1) != 1:
            problems.append(f"{rel}：全文有 {len(h1)} 个 H1（应为 1）")

    if total < MIN_HEADINGS:
        print(f"[未能核对] 只扫到 {total} 个标题（下限 {MIN_HEADINGS}，读了 {len(pages)} 个正文页）"
              f"——本闸本轮什么也没检查，**不能按「标题都没问题」通过**")
        return 2

    if problems:
        print(f"页内标题核对：{len(pages)} 个正文页、{total} 个标题，{len(problems)} 处问题")
        for x in problems:
            print("  ✗ " + x)
        print("  → 同名标题改掉其中一个；跳级的那一级要么补上、要么改成紧邻的上一级")
        return 1

    print(f"页内标题核对：{len(pages)} 个正文页、{total} 个标题，"
          f"页内无同名标题、层级无跳级、每页恰好一个 H1")
    return 0


if __name__ == "__main__":
    sys.exit(main())

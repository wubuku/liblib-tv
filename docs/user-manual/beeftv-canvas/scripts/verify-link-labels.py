#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十六道闸：正文内链的**链接文字**必须是目标页的真名。

背景（Batch 229）：翻手册正文里的内链时发现一件事——**同一本手册里，
「链接该写成什么样」有两套并存的写法，谁也没判**：

  · `10-tasks/README.md`（任务索引）的 29 条链接，**文字 = 目标页 H1**，
    由 `verify-meta.py` 的 `index_check()` 核着；
  · 正文里的 168 条内链，**147 条（87.5%）的文字是裸文件名**——
    写的是 `[storage-quota.md](storage-quota.md)`。读者在渲染后的站点上
    看到的就是 `storage-quota.md` 这一串路径，而同一本书的索引里
    同一页叫「账号存储、容量与配额」。**同一页两个名字。**
  · 剩下 21 条用的是中文页名，可这 21 条是**三种形态并存**：
    完整 H1（「故障排查」）、H1 冒号前的简称（「发起图片生成」）、
    目标页某个小节的名字（「批量创作表」）。

**为什么这类缺陷能活这么久**：闸 9 核的是「链接指向的文件在不在」，
闸 18 核的是「内链可达」——**两条都不看链接上写的是什么字**。
可达性全绿，而读者点过去之前看到的那串 `.md` 没人管。

判据（对全部正文页，含 `10-tasks/README.md`）：
  1. 抽正文里所有 `.md` 相对链接（**排除图片** `![]()`、
     **排除围栏代码块**——那里的链接是示例不是导航）；
  2. 目标文件必须存在（这一条闸 18 已经核过，本闸只做前置判断，
     **文件不存在时报「本闸只管文字」而不是冒充内链闸**）；
  3. 链接文字必须落在该目标页的**合法名字集合**里：
       · 目标页的 H1；
       · 目标页任意标题（H1/H2/H3…）的**「：」前部分**；
       · 目标页任意标题本身。
     这三条合起来等于「**这个名字在目标页上确实存在**」——
     不用任何人工维护的名字表，也不用模糊匹配。
     实测假阳性为 0：手册里 21 条本来写对的链接，去重后 17 种写法
     全部命中；`点击这里` / `点这里` / `详见` / `更多` 这类占位词一个都不命中。

**为什么不用「文字 = H1」这一条更严的规则**（Batch 139/141/142 的老教训）：
行文里放 23 字的完整 H1 会把句子撑散——「见『概念：BeefTV 是怎么工作的』」
读者要读两遍才知道点过去是什么。所以 H1 冒号前的简称是被允许的，
而**简称必须真的等于 H1 的前半**，不能是随手编的。

**为什么不用登记表**（Batch 226/227/228 连着三批的教训）：
登记表要人维护，而维护成本会转化成「为了让闸变绿而往表里加例外」。
本闸的合法集**从目标页自己算出来**——目标页改标题，合法集跟着变，
不需要任何人记得同步一张表。Batch 228 已经在「引号内容对账上游」上撞过
「前提不成立」的墙，本闸的教训是：**能从前缀算出来的，就别登记**。

退出码：0 通过；1 有链接文字不是目标页的真名；2 未能核对
（正文页读不到足够多 / 一条内链都没扫到）。
"""

import os
import re
import sys

# 正文页：根目录的 4 个内容页 + 10-tasks/ 下的任务页。
# **判据自己的输入范围要声明出来**（Batch 226 实测：excluded 任务的
# manual_pages 不一定是它的专属页，所以这里不查账本，直接按文件系统枚举）。
CONTENT_PAGES = ("00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md")

# 只认页面间相对链接，且扩展名必须是 .md
LINK = re.compile(r"(?<!!)\[([^\]\n]*)\]\(((?:\./|\.\./)?[a-z0-9][a-z0-9\-]*\.md)\)")

# 扫到的内链条数下限。**低于它就报「未能核对」，不许报「通过」**——
# 「0 条链接 → 0 个问题」和「168 条链接全部合规」在退出码上没区别，
# 在措辞上却天差地别（Batch 191/192 实测，纪律 156）。
# 真实值 168，取 60 留足余量，又足以抓住「cwd 指错 / 页面集合写错」这类整片扫空。
MIN_SCANNED_LINKS = 60


def strip_fenced(text):
    """把围栏代码块（``` 与 ~~~）整段**挖空但保留行数**。

    保留行数不是洁癖：报错要带 `:行号`，而行号必须对得上原文。
    第一版用 `re.sub` 直接删掉整段，链接虽然不再被扫到，
    **可剩下那些行的行号全部前移了**——报出来的行号指向别处，
    比不报错更坏。
    """
    out, in_fence, fence = [], False, None
    for line in text.split("\n"):
        m = re.match(r"^[ \t]*(```|~~~)", line)
        if m:
            if not in_fence:
                in_fence, fence = True, m.group(1)
            elif m.group(1) == fence:
                in_fence, fence = False, None
            out.append("")          # 围栏行本身也清空
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def page_path(root, base):
    """按「先 10-tasks/ 再根目录」的顺序找页面——两种位置都真实存在。"""
    for cand in (os.path.join(root, "10-tasks", base), os.path.join(root, base)):
        if os.path.isfile(cand):
            return cand
    return None


def content_pages(root):
    """手册的正文页清单（含任务索引 README.md——它也是读者会点的地方）。"""
    out = []
    for base in CONTENT_PAGES:
        p = page_path(root, base)
        if p:
            out.append(p)
    task_dir = os.path.join(root, "10-tasks")
    if os.path.isdir(task_dir):
        for name in sorted(os.listdir(task_dir)):
            if name.endswith(".md"):
                out.append(os.path.join(task_dir, name))
    return out


def legal_names(path):
    """该页的合法名字 = H1 + 各级标题 + 它们「：」前的部分。

    「标题（提示）」不算进这个集合——提示语各不相同（「无入口，副本不上传」
    「当前无入口」），**没法枚举，只能按形态判**，故由 `is_legal_name` 处理。
    """
    body = strip_fenced(open(path, encoding="utf-8", errors="ignore").read())
    names = set()
    for m in re.finditer(r"^#{1,6}\s+(.*)$", body, re.M):
        h = m.group(1).strip()
        if not h:
            continue
        names.add(h)
        if "：" in h:
            names.add(h.split("：")[0].strip())
    return names


def is_legal_name(label, names):
    """链接文字是否是该页的真名。

    两形态都算：
      · 原样等于某个真名；
      · 真名 + 一句**全角括号**提示（「只读画布与画布副本（无入口，副本不上传）」）——
        这正是 `verify-meta.py` 的 `index_check()` 用 `H1_PAREN` 认可的形态，
        本闸第一版漏了它，上线首跑就把两条**本来正确**的索引链接报成了问题。
        漏判合法形态和误判有问题一样，都会让人不信任这道闸。
    """
    if label in names:
        return True
    return any(label.startswith(n + "（") and label.endswith("）") for n in names)


def scan(root):
    """返回 (问题列表, 扫到的链接数, 读不到的页数, 目标缺失的链接数)。"""
    problems, n_links, unreadable, missing_target = [], 0, 0, 0
    cache = {}

    def names_for(base):
        if base not in cache:
            p = page_path(root, base)
            if p is None:
                cache[base] = None
            else:
                cache[base] = legal_names(p)
        return cache[base]

    for page in content_pages(root):
        try:
            raw = open(page, encoding="utf-8", errors="ignore").read()
        except OSError:
            unreadable += 1
            continue
        rel = os.path.relpath(page, root)
        # 行号对齐的关键：`strip_fenced` 保留行数，所以这里的行号就是原文行号
        for lineno, line in enumerate(strip_fenced(raw).split("\n"), 1):
            for m in LINK.finditer(line):
                label, target = m.group(1).strip(), m.group(2)
                base = target.split("/")[-1]
                n_links += 1
                names = names_for(base)
                if names is None:
                    missing_target += 1
                    continue
                if not names:
                    # 目标页一个标题都没有——核不了，如实说，不猜
                    problems.append(
                        f"{rel}:{lineno} 「{label}」→ {base}：目标页读不出任何标题，"
                        f"本闸无法核对它的合法名字"
                    )
                    continue
                if not is_legal_name(label, names):
                    shown = "、".join(sorted(names)[:4])
                    if len(names) > 4:
                        shown += " …"
                    problems.append(
                        f"{rel}:{lineno} 链接文字「{label}」不是 {base} 的真名"
                        f"（该页可用的名字：{shown}）"
                    )
    return problems, n_links, unreadable, missing_target


def main():
    # 手册根目录由脚本自身位置推导，**不依赖 cwd**（Batch 166 实测教训）
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pages = content_pages(root)
    if len(pages) < 10:
        print(f"[未能核对] 只找到 {len(pages)} 个正文页（下限 10），输入范围明显不对——本闸本轮什么也没检查")
        return 2

    problems, n_links, unreadable, missing_target = scan(root)

    if unreadable:
        print(f"[未能核对] 有 {unreadable} 个正文页读不到，无法完成核对")
        return 2
    if missing_target:
        # 内链可达性由闸 18 管；本闸只管文字。目标缺失时**如实说本闸跳过了多少条**，
        # 不把「没核」说成「核过没问题」（纪律 160：超时/缺输入 ≠ 通过）。
        print(f"[部分核对] 有 {missing_target} 条内链的目标文件不存在（可达性由内链闸负责），"
              f"本闸只核了其余链接的文字")
    if n_links < MIN_SCANNED_LINKS:
        print(f"[未能核对] 只扫到 {n_links} 条内链（下限 {MIN_SCANNED_LINKS}），"
              f"输入范围明显不对——本闸本轮未能核对")
        return 2

    if problems:
        print(f"正文内链文字核对：扫到 {n_links} 条内链，{len(problems)} 条的链接文字"
              f"不是目标页的真名（读者会看到文件名，或看到一个该页上不存在的名字）")
        for x in problems:
            print("  ✗ " + x)
        print("  → 链接文字写成目标页的 H1，或它的「：」前简称；不要写 .md 文件名")
        return 1

    print(f"正文内链文字核对：{n_links} 条内链的文字全部是目标页的真名"
          f"（{len(content_pages(root))} 个正文页，含任务索引）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十一道闸：账本交叉引用完整性（Batch 184 新增）。

背景（Batch 184）：Batch 183 立了闸 19 管「批次号不许重复」，本批顺着同一类问题往下查
——**账本引用的东西，是不是真的存在**。查出 2 处真缺陷：

  · `PROGRESS.md` 的 Batch 179 行写着「**纪律 166** 的第三次应验」，**而纪律只到 140，
    编号 166 从来不存在**；
  · `AUDIT.md` 的「环境记录十六（Batch 33，…）」**有完整记录，Batch 33 却从未在
    批次表里出现过**——那一批真的发生过，只是没登记。

**本闸只覆盖两个结构化模式，而且是量过假阳性率之后才定的范围。**这一点必须写下来，
因为本批最值钱的发现恰恰是**反面**的：

    探针共报出 12 个「悬空引用」，逐个读原文后**只剩 2 个是真的**。10 个假的分三类：

  1. 「闸 24」「闸 26」——原文是「**第六道闸 24 → 26 条**」，那是**断言条数**不是闸号；
  2. 「Batch 299」「Batch 288」——那是**别的仓**（jimeng）的批次编号；
  3. 「方向一二」「方向一二三四」「方向四一」——「方向一二」是这个文档的
     **连写枚举**（方向一、方向二），而「方向四**一上线**就会…」是「方向四，一上线」；
  4. 另外两个假阳性是我**自己的探针**造出来的：中文数字解析器漏了「零」，
     于是「一百零一」被算成 100、报出「环境记录 100 重复十次」——**修好解析器后
     实测无任何重复编号**。

**所以本闸刻意不去扫这三类**：「闸 N」与「方向 X」在自由散文里**无法与正文可靠区分**，
硬扫就是往闸门里灌噪音——而**判据把不相干的东西报成异常，人就会学会忽略它**
（Batch 142 闸 8 第一版把 40+ 行正常历史行全报成异常，同一条教训）。
只扫两种**带结构标记、不会被散文冒充**的写法：

  · 方向一：`## 环境记录…（Batch N，…）`——**全角括号 + 全角逗号**紧跟在「Batch N」后面，
    这是 AUDIT.md 自己的标题格式，散文里不会出现；
  · 方向二：`纪律 N` 出现在 .md 全文——**数字是 ASCII**，而中文行文里说纪律一律带
    汉字（「纪律 128/129/130」「纪律一百四十」），所以 `纪律 \\d+` 命中的一定是
    **编号引用**而不是叙述。

两条都刻意**不判「连续」**：环境记录实测缺 29 与 31，**但缺号不是错误**——
批次数与记录数本来就不必一一对应（一个批次可以没有独立记录，一条记录也可以覆盖多批）。
**判据过严同样是错**（Batch 139/141/142 的同一课）。

退出码：0 引用全部对得上；1 有悬空引用；2 读不到应核的文件（未能核对，不等于通过）。
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS = os.path.join(ROOT, "PROGRESS.md")
AUDIT = os.path.join(ROOT, "AUDIT.md")
RULES = os.path.join(ROOT, "AUDIT-RULES.md")

# 方向一：环境记录标题里的 Batch N（全角括号 + 全角逗号，散文里不会出现）
REC_RE = re.compile(r"^##\s*环境记录[^\n]*?（Batch\s*(\d+[a-z]?)\s*[，,]")
# 方向二：纪律编号引用（ASCII 数字；中文叙述里说纪律带汉字，不会命中）
DISC_RE = re.compile(r"纪律\s*(\d+)")
# 批次表的行首形态
ROW_RE = re.compile(r"^\|\s*([^|]*?)\s*\|")
SECTION = "## Batch 计划与状态"
NUM_RE = re.compile(r"^\d+[a-z]?$")

SKIP_DIRS = {".git", "node_modules", ".vitepress", "dist"}


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def md_files():
    """手册树内全部 .md（跳过依赖与构建产物——判据的输入范围必须等于发布范围）。"""
    seen = set()
    for base in (PROGRESS, AUDIT, RULES):
        seen.add(base)
        yield base
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            if p not in seen:
                seen.add(p)
                yield p


def defined_disciplines():
    """AUDIT-RULES.md 里真正定义出来的纪律编号（形如 `101. **…` 的顶层条目）。"""
    out = set()
    for line in read(RULES).split("\n"):
        m = re.match(r"^(\d+)\.\s+\*\*", line)
        if m:
            out.add(int(m.group(1)))
    return out


def batch_table_numbers():
    lines = read(PROGRESS).split("\n")
    sec = next(i for i, l in enumerate(lines) if l.strip() == SECTION)
    start = next(i for i in range(sec, len(lines))
                 if ROW_RE.match(lines[i]) and ROW_RE.match(lines[i]).group(1) == "Batch")
    end = next(i for i in range(start + 1, len(lines)) if not lines[i].startswith("|"))
    return {ROW_RE.match(l).group(1) for l in lines[start + 2:end]
            if ROW_RE.match(l) and NUM_RE.match(ROW_RE.match(l).group(1))}


def main():
    try:
        discs = defined_disciplines()
        batches = batch_table_numbers()
    except (OSError, UnicodeDecodeError, StopIteration) as exc:
        print(f"[未能核对] {exc}")
        return 2
    if not discs or not batches:
        print("[未能核对] 纪律或批次表解析出 0 条——解析器退化了，按规则不得当成通过")
        return 2

    problems = []
    scanned = 0

    # 方向一：环境记录里的 Batch N 必须已登记
    recs = 0
    for i, line in enumerate(read(AUDIT).split("\n"), 1):
        m = REC_RE.match(line)
        if not m:
            continue
        recs += 1
        n = m.group(1)
        if n not in batches:
            problems.append(f"方向一：AUDIT.md 第 {i} 行的环境记录声明「Batch {n}」，"
                            f"而批次表里没有这一行——**这一批发生过，只是没登记**")
    print(f"方向一：{recs} 条环境记录，批次表 {len(batches)} 个编号")

    # 方向二：纪律编号引用必须已定义
    refs = 0
    for p in md_files():
        try:
            text = read(p)
        except (OSError, UnicodeDecodeError) as exc:
            problems.append(f"[未能核对] 读不到 {os.path.relpath(p, ROOT)}：{exc}")
            continue
        scanned += 1
        for i, line in enumerate(text.split("\n"), 1):
            for m in DISC_RE.finditer(line):
                refs += 1
                n = int(m.group(1))
                if n not in discs:
                    problems.append(
                        f"方向二：{os.path.relpath(p, ROOT)} 第 {i} 行引用「纪律 {n}」，"
                        f"而 AUDIT-RULES.md 里没有这一条（现有 {min(discs)}..{max(discs)}）")
    print(f"方向二：{scanned} 个 .md、{refs} 处纪律编号引用，现有 {min(discs)}..{max(discs)} 条")

    if problems:
        for p in problems:
            print(f"  ✗ {p}")
        print(f"账本交叉引用核对：{len(problems)} 处悬空引用")
        return 1
    print("账本交叉引用核对通过：环境记录声明的批次都已登记，纪律编号引用都指向真实条目")
    return 0


if __name__ == "__main__":
    sys.exit(main())

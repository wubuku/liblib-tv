#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十九道闸：批次账本的行完整性（Batch 183 新增）。

背景（Batch 183）：为了给 Batch 182 补一行 `| 182 |`，去定位批次表末尾，
**发现表里有两条 `| 178 |`**，而且**两条出自同一个提交 `da21d0c3`**——
也就是同一批里把同一件事写了两遍，两遍各记了一个不同的头条：

  · 长那条（2262 字符）记的是「升版 + 顺带逮到 34 例反验静悄悄坏了三个批次」，
    带 ①–⑧ 全部八点、纪律 124–127、验收写「17 道闸全绿」；
  · 短那条（1523 字符）记的是「升版 + 闸 7 因上游真的修复而红」，
    只有 ①②③⑦⑧，纪律写 124/125、验收写「16 道闸全绿」。

**长那条是超集**，短那条是同一批的早期草稿、写完没删。已按「保留超集、
把短条独有的两条事实并进去」处理。但真正值得注意的是**它为什么能躺着**：

  · 闸 8 `verify-tables.py` 核的是**列数**（有没有被裸竖线多切一列），
    而这两行列数完全正常——**结构没坏，所以闸 8 看不见它**；
  · 闸 9 `verify-meta.py` 核的是**计数与索引的双向一致**，
    「某个批次号出现两次」不在它的任何一个方向里；
  · 于是 18 道闸全绿，而**账本在自相矛盾**：想查「Batch 178 做了什么」的人
    会找到两个不同的答案，且**没有任何机制提示他该怀疑**。

本批把「行重复」立成常驻守卫。判据只有一条方向，但有三个容易写错的地方，
每一个都写成独立的检查而不是靠自觉：

  1. **只核批次表那一张，不跨表**。`PROGRESS.md` 里还有别的表（发布对照表等），
     它们的行也以数字开头（出现过 `| 18 |`）。**跨表比对会把它们报成重复**——
     而那正是本闸第一版的写法，靠反验用例 2 才没让它活下来。
     所以判据**先按表头定位**（`## Batch 计划与状态` 之后、表头单元格恰为 `Batch`
     的那一张），再在**这张表内部**比重复。
  2. **批次号形态单独核**。形态非法（空格、全角数字、`#17c`）会让重复检查
     把两行当成两个不同的东西，于是**重复检查被形态问题静悄悄架空**——
     和 Batch 180「阈值从没被读过」同源：判据读的是一个恒真的量。
  3. **报重复时必须给出行号和两边的内容长度**。只说「有重复」的话，
     读者还得自己找；而两份重复行往往一长一短，**长度差正是判断谁是草稿的线索**。

为什么单列一道闸而不是塞进 build-site 的内联检查：
闸 8 管的是**表格结构**（渲染会不会错位），本闸管的是**账本内容**（同一个编号
被登记了几次、每一行登记全了没有）。两者看同一张表、判完全不同的东西，
混在一起会让闸 8 的「只判结构不判内容」这条边界失守。

Batch 216 补上第二个方向（这个名字从此才名副其实）：
写这个脚本时它的名字里就带着「行完整性」，而**它只做了两件事——查重复、查形态**。
拿四种候选损坏去打它，**四种全部报绿**：内容列留空 / 状态列整个删掉 /
状态写「进行中」 / 内容格写成空格。其中两种根本不该报（状态列留空是 GFM 认可的
形态、内容格写成空格等价于留空），**而「状态列整个删掉」是真缺陷**。

现场比预想的难看：**190 行数据里有 78 行只有两格**（批次号 + 内容），**占 41%**，
集中在 Batch 92–173——那一段的内容列是完整的长文，**状态列从来没被登记过**。
闸 8 看不见它们，因为它的判据是「未转义竖线数**不得超过**表头列数」，
理由就写在它的脚本头里：「GFM 规定少于一列的行会被补空单元格，**渲染正常**」。

**那个理由对渲染成立，对账本不成立**——渲染上「状态列留空」和「状态列不存在」
确实一模一样，**但账本上它们是两件事**：前者是「登记了这一批、内容待补」，
后者是「这一批的完成情况根本没人记」。而这 78 批**全都完成、已合入 master**
（逐个 `git log` 查到 78 个提交；Batch 92 那行还只能靠行 blame 定位到
`13ce0ace`，因为它的提交消息写成小写的 "bee tv manual batch 92"）。
**账本写着「不知道」，而事实是「已完成」——这正是最不容易被发现的那类损坏。**

所以新方向只判一件事：**数据行的列数不得少于表头列数**，并与闸 8 划清两半：
  · **少列 → 本闸报**（账本缺登记；GFM 认可，但语义缺失）；
  · **多列 → 仍归闸 8**（结构真的坏了，会把整行渲染错位）。
这条分工是量出来的、不是分配的：闸 8 报多列不报少列，本闸反过来，
**两道闸合起来才覆盖「列数不对」的全部方向**。
**刻意不判「某格留空」**——当前树上内容列 0 处留空，而 GFM 认为它正常，
加进去只会逼出一张豁免表（Batch 142 闸 8 第一版的教训）。

退出码：0 批次表行完整；1 有重复、形态非法或缺列；2 读不到批次表（未能核对，不等于通过）。
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS = os.path.join(ROOT, "PROGRESS.md")

SECTION = "## Batch 计划与状态"
# 批次号形态：整数 + 可选小写字母后缀。表内既有形态就是 1 / 6a / 8b / 17c / 17d，
# **刻意不含别的**——加形态等于加豁免，而豁免表一旦靠「我记得它其实也行」维持，
# 就等于给判据开后门（Batch 135 的教训）。
NUM_RE = re.compile(r"^\d+[a-z]?$")
ROW_RE = re.compile(r"^\|\s*([^|]*?)\s*\|")
# 未转义竖线——**必须与闸 8 同一套判定**（前一位不是反斜杠），否则同一个单元格
# 在两道闸里会被数出不同的列数，而「两道闸对同一行给出不同列数」这件事
# 没有任何人会去追。Batch 143 那行的内容里有大量 `\|\|` 与带竖线的代码片段。
CELL_SPLIT = re.compile(r"(?<!\\)\|")


def locate_batch_table(lines):
    """返回批次表的行区间 [start, end)。定位不到就抛错。"""
    try:
        sec = next(i for i, l in enumerate(lines) if l.strip() == SECTION)
    except StopIteration:
        raise LookupError(f"{PROGRESS} 里找不到小节标题「{SECTION}」")
    start = None
    for i in range(sec, len(lines)):
        m = ROW_RE.match(lines[i])
        if m and m.group(1) == "Batch":
            start = i
            break
    if start is None:
        raise LookupError(f"小节「{SECTION}」之后找不到表头单元格恰为 Batch 的表格")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if not lines[i].startswith("|"):
            end = i
            break
    return start, end


def cells(raw):
    """按 markdown 规则切一行的单元格：**未转义**的竖线才是分隔符。

    刻意不去掉首尾竖线之外的东西，也不做半吊子的转义还原——只需要数出列数，
    而转义竖线留在格内不影响列数。首尾竖线的判定排除 `\\` 结尾（转义竖线）。
    """
    s = raw.strip()
    if s.startswith("|"):
        s = s[1:]
    if len(s) > 1 and s.endswith("|") and s[-2] != "\\":
        s = s[:-1]
    return [c.strip() for c in CELL_SPLIT.split(s)]


def main():
    try:
        with io.open(PROGRESS, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        start, end = locate_batch_table(lines)
    except (LookupError, OSError, UnicodeDecodeError) as exc:
        print(f"[未能核对] {exc}")
        return 2

    problems = []
    seen = {}
    total = 0
    short = 0

    # 表头列数是**算出来的**而不是写死的 3：这张表哪天加一列（比如单列 commit），
    # 写死的判据会立刻误报一整片。写死的是**下限**——三列是这张表的语义契约
    # （批次号 / 内容 / 状态），少一列说明表头自己就缺了，而那样会让下面所有
    # 「少列」判断失去参照（Batch 215 的同款：判据读一个恒真的量等于没有判据）。
    head = cells(lines[start])
    head_cols = len(head)
    if head_cols < 3:
        problems.append(
            f"第{start + 1}行：批次表表头只有 {head_cols} 列（应为 3：批次号 / 内容 / 状态）"
            f"——表头缺列会让「数据行少列」这项判断失去参照")
        head_cols = 3
    for i in range(start + 2, end):          # 跳过表头与其下的分隔行
        raw = lines[i]
        if not raw.startswith("|"):
            continue
        m = ROW_RE.match(raw)
        if not m:
            continue
        num = m.group(1)
        if not num:                          # 整行留空，不是批次行
            continue
        total += 1
        got = len(cells(raw))
        if got < head_cols:
            short += 1
            problems.append(
                f"行{i + 1}：批次 {num} 只有 {got} 列，表头 {head_cols} 列"
                f"（缺 {head_cols - got} 格——GFM 会补空格子所以渲染正常，"
                f"但账本上「状态列不存在」与「状态留空」是两件事）")
        if not NUM_RE.match(num):
            problems.append(
                f"行{i + 1}：批次号形态非法 {num!r}（只接受整数 + 可选小写字母后缀，如 6a / 17d）")
            continue
        if num in seen:
            problems.append(
                f"批次号 {num} 登记了不止一次：行{seen[num][0]}（{seen[num][1]} 字符）"
                f" 与 行{i + 1}（{len(raw)} 字符）")
        else:
            seen[num] = (i + 1, len(raw))

    uniq = len(seen)
    print(f"批次表：{total} 行、{uniq} 个唯一批次号、表头 {head_cols} 列"
          f"（小节在第 {start + 1} 行，表体到第 {end} 行；少列 {short} 行）")
    if problems:
        for p in problems:
            print(f"  ✗ {p}")
        print(f"批次账本行核对：{len(problems)} 处不一致")
        return 1
    print("批次账本行核对通过：每个批次号只登记一次，形态全部合法，列数与表头一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())

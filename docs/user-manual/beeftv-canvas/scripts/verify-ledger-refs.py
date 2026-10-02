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
#: 纪律条目的两个组成部分（Batch 194 拆开，见 defined_disciplines 的 docstring）
_DISC_DEF_RE = re.compile(r"^(\d+)\.\s+\*\*")
_BATCH_TAG_RE = re.compile(r"（Batch\s*\d+")
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
    """AUDIT-RULES.md 里真正定义出来的纪律编号。

    **锚为什么不是 `^(\\d+)\\.\\s+\\*\\*`**（Batch 194 实测，这是个真缺陷）：
    旧锚把 `AUDIT-RULES.md` 里**至少 17 行普通编号列表**当成了纪律——
    「注册表里有吗 / 当前上下文会渲染它吗 / 点下去 handler…」（第 41–43 行）、
    「结论对不对 / 理由对不对」（59–60）、「事实查清 / 缺陷分类 / 修内容…」（300–308）、
    「必须校验反向验证自己的前提 / 别用 `grep -q` 配 `pipefail`…」（407–415）……
    **它们大多编号 1–9，与早期真纪律 1–9 重号，所以 `max` 看起来正常，
    而闸 21 输出的「现有 1..163 条」这个数字一直是错的**——
    **错的不是计数，是集合里混着 17 个不是纪律的东西**，
    而且它让「引用纪律 2」这类悬空引用查不出来（2 被当成纪律了）。

    **新锚额外要求该行（或它的紧邻续行）带「（Batch N」**。
    实测：真纪律 **157 条**全部带，普通列表**一条都不带**；
    **续行兜底是为纪律 163 加的**——它的标题行恰好断在 `」`，
    `（Batch 193）。` 落在下一行，**第一版新锚因此漏掉了它**
    （而它正是本批刚写的那一条，**漏掉最新那条纪律是最坏的失败方式**）。
    **实测误纳风险 0 行**：没有任何一个普通列表的下一行以 `（Batch` 开头。
    """
    out = set()
    lines = read(RULES).split("\n")
    for i, line in enumerate(lines):
        m = _DISC_DEF_RE.match(line)
        if not m:
            continue
        if _BATCH_TAG_RE.search(line):
            out.add(int(m.group(1)))
            continue
        nxt = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
        if nxt.startswith("（Batch"):
            out.add(int(m.group(1)))
    return out


def discipline_shaped_without_batch_tag():
    """形如 `N. **…`、编号 **≥ 10**、却没有任何批次标注的行。

    **为什么卡在「≥ 10」——第一版不卡，结果误报 17 行**（Batch 194 首跑）：
    第一版的判据是「没有标注」，而**能区分普通列表与真纪律的恰恰就是标注本身**，
    所以它对着普通列表报警——**这是循环**：
    「注册表里有吗 / 结论对不对 / 事实查清 / 显式路径 commit…」这些工作流步骤
    本来就没有批次标注。

    卡在 ≥ 10 之后实测干净：**所有无标注的行编号都在 1–9**
    （真纪律 1–9 全部带标注，所以它们不会落进这条），**17 处误报全部消失**。

    **这条方向能防什么、防不了什么，必须写清楚**：
      · 能防：**新写的纪律（10 号起）漏了批次标注** ——
        而 Batch 193 的纪律 163 恰好踩过（标题行断在 `」`，标注落到下一行，
        没有续行兜底的第一版判据直接漏掉了它，**而它恰好是最新、最该被引用的一条**）；
      · 防不了：**1、4、8 三条早期纪律漏标注**。
        **这里实测到一件必须说清的事**：`1..9` 里**只有 1、4、8 是真纪律**
        （分别写着「新增闸门时必须同时新增它那一行的反验」「要有一条用例证明扫描不是复读现有名单」
        「『A 不触发 X』≠『结果不成立』」），**2/3/5/6/7/9 从来就不是纪律**——
        它们是「注册表里有吗」与五步法那几组普通列表，只是**编号恰好落在 1–9 里**。
        **所以这条方向的 10 号阈值不是在切「大小」，它切开的正好是「不是纪律的那几个」。**
        本批没有更好的办法让 1/4/8 也被覆盖，
        **判据的边界就该写在判据里，而不是让人以为它全覆盖了**。
    """
    lines = read(RULES).split("\n")
    out = []
    for i, line in enumerate(lines):
        m = _DISC_DEF_RE.match(line)
        if not m or int(m.group(1)) < 10 or _BATCH_TAG_RE.search(line):
            continue
        nxt = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
        if not nxt.startswith("（Batch"):
            out.append((i + 1, line))
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
    print(f"方向二：{scanned} 个 .md、{refs} 处纪律编号引用，"
          f"现有 **{len(discs)} 条**纪律（编号 {min(discs)}..{max(discs)}）"
          f"——**报条数而不只报范围**，范围看不出混进来的东西（纪律 156，Batch 194）")

    # 方向三：形如 `N. **…` 却既不带「（Batch N」也没有紧邻续行标注的行。
    # **Batch 193 的纪律 163 踩过这个坑**（标题行断在 `」`，标注落在下一行），
    # 而没有续行兜底的第一版判据**直接漏掉了它**——
    # **漏掉最新那一条纪律是最坏的失败方式**：它恰好是最需要被引用的那条。
    for lineno, line in discipline_shaped_without_batch_tag():
        problems.append(
            "方向三：AUDIT-RULES.md 第 %d 行形如「%s …」却没有任何批次标注，"
            "**闸 21 不会把它认成纪律**——而这类行正是普通编号列表与真纪律的区别所在，"
            "**判据认不出来它就不可能被引用检查覆盖**。"
            "　→ 写纪律时把「（Batch N）」放在标题行，或紧接标题行的续行开头"
            % (lineno, line[:24].strip()))

    if problems:
        for p in problems:
            print(f"  ✗ {p}")
        print(f"账本交叉引用核对：{len(problems)} 处悬空引用")
        return 1
    # **两个数必须来自同一处**（Batch 194 首跑教训）：
    # 第一版在成功行里另算了一遍 `split("## 环境记录")`，于是它报 145、成功行报 149
    # ——**一份输出里两个数自相矛盾，而人只会记住其中一个**（纪律 156）。
    # 现在两个数都直接用方向一/方向二算出来的那两个变量。
    print("账本交叉引用核对通过：%d 条环境记录、%d 条纪律（编号 %d..%d）"
          "——纪律数**不再含普通编号列表**（Batch 194）"
          % (recs, len(discs), min(discs), max(discs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

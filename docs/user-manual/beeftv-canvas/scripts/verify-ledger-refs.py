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
    return {n for n, _line in discipline_items()}


def discipline_items():
    """纪律列表的 `(编号, 原文)` 序列——**Batch 199 换了判据的依据**。

    **旧判据是「这一行（或紧邻续行）带 `（Batch N` 标点」**，
    而它被实测证伪了两次：
      · Batch 194 收窄它，是为了把 17 行普通编号列表排除掉；
      · **但它按标点筛，于是把纪律列表自己的 6 条筛掉了**——
        纪律 2/3/5/6/7/9 写的是「。Batch 135」而不是「（Batch 135）」。
        实测闸 21 报「172 条（编号 1..178）」：**6 条真纪律不存在，
        1 条普通列表（第 160 行「新增闸门时必须同时新增它那一行的反验」）
        却被当成纪律 1**——**这个数多算与少算同时发生。**
        Batch 194 的 docstring 甚至把「2/3/5/6/7/9 从来就不是纪律」写成了事实，
        **而那句话是被这个坏判据算出来的**，不是观察出来的。

    **新判据：纪律就是那条「从 1 开始、逐 +1、不间断」的编号列表。**
    实测：它从第 411 行到 1813 行，**178 条、编号 1..178、零断点**；
    文档里其余 `N. **…` 形态的行共 11 行（10 行普通列表 + 刚改掉的第 160 行），
    **最长的一段只有 10 条**——**178 与 10 差一个数量级，取最长段不会选错。**

    **为什么「编号连续」比「带不带标点」更接近事实**：
    纪律是**按顺序累加**的账，新纪律永远接在末尾；
    而普通编号列表总是从 1 或某个小号重新开始。**「它接在上一条后面吗」是事实，
    「作者当时用了哪种括号」是写法**（纪律 171：判据认事实，不认写法）。
    """
    items = []
    for i, line in enumerate(read(RULES).split("\n")):
        m = _DISC_DEF_RE.match(line)
        if m:
            items.append((int(m.group(1)), line))
    best, cur = [], []
    for n, line in items:
        if cur and n == cur[-1][0] + 1:
            cur.append((n, line))
        else:
            if len(cur) > len(best):
                best = cur
            cur = [(n, line)]
    if len(cur) > len(best):
        best = cur
    return best


def discipline_tail_after_list():
    """纪律列表**末尾之后**还有 `N. **…` 形态的行——说明列表中间缺了一段。

    **为什么必须单独判**（Batch 199 实测的弱点）：新判据取「最长的连续段」，
    所以**删掉中间一条纪律，列表只是变短，门会安静地把 178 改口成 99**——
    **报出来的新数字仍然是自洽的，仍然看不出问题**。
    这条守卫问的是另一个问题：**文件里有没有比列表末尾更大的编号**。
    实测现状为 0（普通列表的编号都在 1–10，远小于 178）。
    """
    best = discipline_items()
    if not best:
        return []
    top = best[-1][0]
    out = []
    for i, line in enumerate(read(RULES).split("\n")):
        m = _DISC_DEF_RE.match(line)
        if m and int(m.group(1)) > top:
            out.append((i + 1, line))
    return out


def discipline_shaped_without_batch_tag():
    """形如 `N. **…`、**带批次标注、却落在纪律列表之外**的行。

    ── Batch 199 把这一整段重写了，因为上面那段描述的是**一个已被证伪的判据** ──

    **旧判据是「编号 ≥ 10 且没有 `（Batch N` 标注」**，它来自 Batch 194，
    当时的目的是把 17 行普通编号列表排除掉。**它确实做到了**（首跑零误报），
    **但它同时把纪律列表自己的 6 条排除掉了**，而且旧 docstring 把这件事
    **当成事实写了下来**：

        「`1..9` 里只有 1、4、8 是真纪律，**2/3/5/6/7/9 从来就不是纪律**」

    **那句话是错的。** Batch 199 实测：`2/3/5/6/7/9` 是纪律列表里**实打实的六条**
    （「必须校验反向验证自己的前提」「别用 `grep -q` 配 `pipefail` 做前提校验」
    「判据要覆盖上游最可能怎么修」「发现一个洞要顺着查同类」
    「从函数实现推出的『用户该怎么做』必须实测」「判据不能假设上游两处写法一致」
    「断言的措辞精度就是手册的措辞上限」中的对应条目），
    **它们只是把批次写成「。Batch 135」而不是「（Batch 135）」**——
    于是按标点筛的判据看不见它们。
    **更糟的是那句「从来就不是纪律」被写进了代码注释**，
    **下一个人读到它会以为已经查过了**。

    **新判据只问一件事：它在不在纪律列表里。** 在 → 是纪律（不管有没有标注）；
    不在却带标注 → **它想当纪律却站错了位置**（实测抓到第 160 行那个
    「三条规矩」列表项，**已按纪律 161 当年用过的手法改成 `·`**）。

    **为什么不用「带不带标注」当依据**：标注是**写法**，位置是**事实**。
    Batch 194 自己已经察觉到这一点（「10 号阈值不是在切『大小』」），
    **而本批直接换掉了那个阈值**。
    """
    lines = read(RULES).split("\n")
    known = {line for _n, line in discipline_items()}
    out = []
    for i, line in enumerate(lines):
        m = _DISC_DEF_RE.match(line)
        if not m or line in known:
            continue
        nxt = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
        # **带批次标注**才是「本该是纪律」的信号：普通列表从不写批次。
        # 实测文档改完之后这里应为 0——而旧的「编号 ≥ 10 且无标注」
        # 是在切「大小」，Batch 194 自己就说过「10 号阈值不是在切大小」。
        if _BATCH_TAG_RE.search(line) or nxt.startswith("（Batch"):
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

    # 方向三（Batch 199 重写）：**形如 `N. **…` 且带批次标注，却落在纪律列表之外**。
    #
    # **旧版是「编号 ≥ 10 且不带（Batch 标注」**，Batch 194 自己就写明了
    # 「**10 号阈值不是在切『大小』，它切开的正好是『不是纪律的那几个』**」——
    # 而那正是被坏判据算出来的假结论。新判据不再看编号大小，
    # 只问「**它是不是在纪律列表里**」：
    #   · 在列表里 → 是纪律（哪怕它没写批次，2/3/5/6/7/9 就是这种情况）；
    #   · 不在列表里却带批次标注 → **它想当纪律却站错了位置**
    #     （实测抓到第 160 行那个「三条规矩」列表项，**已改成 `·`**）。
    for lineno, line in discipline_shaped_without_batch_tag():
        problems.append(
            "方向三：AUDIT-RULES.md 第 %d 行形如「%s …」且带批次标注，"
            "**却落在纪律列表之外**——纪律是那条从 1 起逐 +1 的连续列表，"
            "站错位置的纪律**不会被引用检查覆盖**。"
            "　→ 要么把它挪进纪律列表并重新编号，要么确认它是普通列表、"
            "**把编号列表项改成 `·`**（同段的其它条目多半已经是 `·`）"
            % (lineno, line[:24].strip()))

    # 方向三之二：纪律列表**末尾之后**还有纪律形态的行 → 中间缺了一段。
    # **不加这条，新判据会把「删掉一条纪律」报成一个自洽的新数字**（实测弱点）。
    for lineno, line in discipline_tail_after_list():
        problems.append(
            "方向三之二：AUDIT-RULES.md 第 %d 行的编号 %s **大于纪律列表的末尾编号**——"
            "纪律列表中间缺了一段（Batch 199：删掉中间一条纪律，"
            "「取最长连续段」只会让门安静地把 178 改口成一个更小的自洽数字）"
            "　→ 补回缺失的纪律，或确认末尾编号之后那些行属于什么"
            % (lineno, line[:3].strip()))

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

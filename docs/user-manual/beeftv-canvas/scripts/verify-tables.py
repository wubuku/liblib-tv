#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第七道闸：markdown 表格结构核对。

背景（Batch 142）：修一批否定式断言时，撞见 `PROGRESS.md` 里 **5 行表格被代码里的
`||` 截断**（Batch 122 / 124 / 135 / 136 / 102）。markdown 表格里，**单元格内部的裸竖线
会多切出一列**，那几行渲染出来是错位的——而它们**已经错了好几个批次没人发现**，
因为前六道闸都不看表格结构。

**这类损坏和 Batch 135「不可达声明悄悄过期」是同一类风险**：它不会让构建失败，
只会让读账本的人看到错位的内容，而且**越是内容里带代码的行越容易中招**
（`a || b`、`x ? y : z` 这类写法天然含竖线）。

判据（对**全部** .md，含内部资料——损坏恰恰出在内部资料里，发布页当时是干净的）：
  1. 跳过围栏代码块（``` / ~~~）内的内容：那里的竖线不是表格；
  2. 连续成块的 `|` 开头行算一张表，用**表头行的未转义竖线数**定列数；
  3. 块内每一行的未转义竖线数**不得超过**表头列数；
  4. 为什么是「超过」而不是「等于」：GFM 规定**少于一列的行会被补空单元格**，
     渲染正常。而**多于表头**会真的多切出一列、把内容错位——
     Batch 142 撞见的 `||` 截断与 `20-reference.md` 里被裸竖线切断的 URL 都是这一类。
     （本闸第一版写成「必须等于」，立刻把 40+ 行正常的历史行全报成异常——
     **判据过严同样是错**，和 Batch 139/141/142 的判据 bug 同一个教训。）
  4之二. **Batch 216 订正本条里一句从没被核对过的断言**。原文写的是
     「`PROGRESS.md` 里大量历史行就是『状态』列留空（3 个竖线对 4 列表头），
     **那是刻意的，不是损坏**」。实测两处都不成立：

       · 那 78 行不是「状态列留空」，是**整列不存在**（整行只有批次号 + 内容两格）；
       · 「刻意」这个词**没有依据**——逐个 `git log` 查过，78 批**全部完成、
         已合入 master**。也就是说账本当时记的是「不知道」，而事实是「已完成」。

     **本条继续不管少列，这个结论不变，但理由必须换成真的那句**：
     判据按哪一层语义判，就只对那一层负责。少列在 **GFM 渲染层**是正常的
     （本闸承诺的就是「渲染会不会错位」），而在**账本语义层**它是缺登记——
     已由**闸 19** 在同批接管。两道闸合起来才覆盖「列数不对」的全部方向，
     **分工是量出来的，不是分配的**。
  5. 未转义竖线的判定是**前面不是反斜杠**。因此代码段里的 `||` 必须写成 `\\|\\|`，
     单元格里的 URL 含 `|` 也要转义。

为什么单列一道闸而不是塞进 build-site 的内联检查：
  前六道闸查的是**内容对不对**（引用、端点、标签、断言），这一道查的是**结构坏没坏**——
  坏掉的表格会让前六道闸读到的内容本身就是错位的，属于它们的前置条件。

退出码：0 全部表格结构一致；1 有行与所在表的列数不符。
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
MANUAL = os.path.dirname(ROOT)


def unescaped_pipes(line):
    """未转义的竖线数量：前面不是反斜杠的 `|`。"""
    return len(re.findall(r"(?<!\\)\|", line))


def ends_with_pipe(line):
    """这一行是不是以**未转义**的竖线结尾（GFM 表格行的规范形态）。

    **Batch 206 新增的判据，配一条实测出来的假阴性**：
    本闸原先只比「未转义竖线总数」与表头个数，**而少一个与多一个会互相抵消**——
    实测 `AUDIT-RULES.md` 里「闸 17」那一行**行尾根本没有竖线**（它被切在倒数第二格），
    却在 350 列处有一个裸竖线恰好把总数凑够，于是本闸报绿。
    **「少一个结构竖线 + 多一个字面竖线」在计数上等价，在危害上完全不同**：
    前者让 GFM 少切一列，后者让一行凭空多出一列。

    **为什么单独立一条而不是把「少于表头」也算坏**：
    「少于表头」是**有意允许**的（GFM 补空），本项目有大量「状态」列留空的历史行。
    **行尾有没有竖线与列数够不够是两件事**，混在一起判就会把有意留空的行一起冤枉。
    """
    t = line.rstrip()
    return bool(t) and t[-1] == "|" and (len(t) < 2 or t[-2] != "\\")


def is_separator(line):
    s = line.strip()
    return bool(s) and set(s) <= set("|-: ") and "-" in s


#: GFM 分隔行的**每一格**必须长这样（Batch 213）。
#: **与上面那个宽松版 `is_separator` 的区别要说清楚**：
#: 宽松版问的是「这一行看起来像不像分隔行」（字符集 + 至少一个 `-`），
#: 它是 Batch 174 判「单行块」用的；**本条问的是「GFM 会不会真的把它当分隔行」**——
#: 而 GFM 要求**每格都匹配 `^:?-+:?$`，且格的个数与表头相同**。
#: **两种问法都留着，因为它们回答的不是同一个问题。**
_DELIM_CELL = re.compile(r"^:?-{1,}:?$")


def is_real_delimiter(line, header_n):
    """这一行是不是 GFM 意义上的分隔行（且列数与表头相同）。"""
    t = line.strip()
    if not t or unescaped_pipes(t) != header_n:
        return False
    return all(_DELIM_CELL.match(c.strip())
               for c in t.strip("|").split("|"))


def scan(path):
    """返回 [(行号, 该行未转义竖线数, 表头列数, 行首摘录)]。"""
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")
    except (IOError, UnicodeDecodeError):
        return []

    problems = []
    tail_problems = []          # **行尾缺竖线**（Batch 206，与列数分开记）
    sep_problems = []           # **第二行不是合法分隔行**（Batch 213，再单列一处）
    fence = None
    block = []  # [(行号, 原始行)]

    def flush():
        if not block:
            return
        header_n = unescaped_pipes(block[0][1])
        # ⚠️ Batch 174 新增：**块只有一行、且那一行不是分隔行** = 畸形表。
        # GFM 要求「表头 + 分隔行」相邻才算表格；一旦中间被空行或引用块隔开，
        # **整块会被当成普通段落原样显示**——不报错、不截断，只是**表格消失了**。
        # 本闸原先只比「同一块内各行的列数」，而畸形表在它眼里是「一个 1 行的块」，
        # 列数自然一致，**于是完全看不见**。
        # 真实案例两处：`20-reference.md` 的 `/dev/folders` 那一行被空行隔在路由表之外
        # （**读者看到的是一行悬空的表格文字**），以及小节标题里手写的「策略项」表头
        # 与 `|---|` 之间夹进了引用块——后者是本批自己写坏的，当场被这条判据抓住。
        if len(block) == 1 and not is_separator(block[0][1]):
            problems.append((block[0][0], header_n, header_n,
                             block[0][1].strip()[:70] + "  ← 单行且不是分隔行"))
            block.clear()
            return
        # **Batch 213：块有两行以上时，第二行必须是 GFM 意义上的分隔行。**
        # **实测漏报面**（量出来的，不是推的）：在 PROGRESS.md 那张批次表上注入五种损坏，
        # **五种里有五种闸 8 报绿**——删掉整条分隔行 / 分隔行少一列 / 分隔行写成 `| |` /
        # 分隔行缺首尾竖线 / 分隔行被空行隔开。
        # **五种是同一个根因**：本闸把「连续的 `|` 行」当成表，
        # **却从不问第二行是不是分隔行**——
        # 而 **GFM 里没有分隔行的 `|` 行块根本不是表格，它会被原样当普通文本显示**。
        # **这正是本闸存在的意义那一类**（Batch 142 的原话）：
        # 不让构建失败，只让人看到错位的内容。
        # **假阳性实测**：全树 253 段非围栏的 `|` 行块里 **252 段是真表格**，
        # **被这条判据报出来的只有 1 段——而那一段是真缺陷**（见下）。
        if len(block) >= 2 and not is_real_delimiter(block[1][1], header_n):
            sep_problems.append(
                (block[1][0], unescaped_pipes(block[1][1]), header_n,
                 block[1][1].strip()[:70]
                 + "  ← 它的上一行是表头，而**它不是分隔行**："
                   "GFM 不会把这块当表格，整块会被原样显示成普通文本"))
        for lineno, raw in block:
            n = unescaped_pipes(raw)
            # 多于表头 = 真的多切出一列 = 损坏；少于表头会被 GFM 补空，不算
            if n > header_n:
                problems.append((lineno, n, header_n, raw.strip()[:70]))
            # **行尾必须是一个未转义竖线**（Batch 206）：列数相等不等于这一行是表格行。
            # **刻意与上一条分开判**——「列数够不够」和「这一行闭没闭合」是两件事。
            if not ends_with_pipe(raw):
                tail_problems.append(
                    (lineno, n, header_n,
                     raw.strip()[:70] + "  ← 行尾没有竖线，这一行不是一条闭合的表格行"))
        block.clear()

    for idx, line in enumerate(lines, 1):
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            mark = m.group(1)[0]
            if fence is None:
                fence = mark
            elif fence == mark:
                fence = None
            flush()
            continue
        if fence is not None:
            continue
        if line.lstrip().startswith("|"):
            block.append((idx, line))
        else:
            flush()
    flush()
    return tail_problems + sep_problems + problems


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else MANUAL
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in (".vitepress", "node_modules", ".git", "dist")]
        for name in filenames:
            if name.endswith(".md"):
                files.append(os.path.join(dirpath, name))
    files.sort()

    total_bad = 0
    checked = 0
    for path in files:
        problems = scan(path)
        checked += 1
        if not problems:
            continue
        rel = os.path.relpath(path, root)
        print(f"  ✗ {rel}：{len(problems)} 处表格结构问题")
        for lineno, n, header_n, excerpt in problems:
            if excerpt.endswith("← 单行且不是分隔行"):
                # 这类不是「列数不符」，是**整张表不会被渲染成表格**（Batch 174）
                print(f"      第 {lineno} 行：这一行没有和分隔行相邻，"
                      f"**整块不会被渲染成表格**（GFM 要求表头与分隔行紧挨着）| "
                      f"{excerpt.rsplit('  ←', 1)[0]}")
            else:
                print(f"      第 {lineno} 行：未转义竖线 {n} 个，表头是 {header_n} 个 | {excerpt}")
        total_bad += len(problems)

    if total_bad:
        print(f"表格结构核对：{total_bad} 行异常（{checked} 个文件）")
        print("  → 单元格内的竖线必须转义成 \\| （代码段里的 `||` 写成 `\\|\\|`）")
        return 1
    # **零输入不许报绿**（Batch 191 纪律 156 + Batch 192 实测）。
    # 实测本闸在一棵**空手册树**上原样输出「表格结构核对：**0 个文件**、全部表格行列数一致」
    # 并 rc=0——**「一个文件都没检查」和「全部文件都合格」在退出码与措辞上都一样**，
    # 而前者读起来像好消息。它躲过 25 道闸的原因很朴素：**它核的东西是 .md 文件，
    # 而空树里没有 .md**，于是任何「先读文件再核」的判据都会空转。
    if checked == 0:
        print("[未能核对] 一个 .md 文件都没找到——本闸本轮什么也没检查，"
              "**不能按「全部表格都没问题」通过**")
        return 2
    print(f"表格结构核对：{checked} 个文件、全部表格行列数一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())

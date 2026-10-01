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
     渲染正常；`PROGRESS.md` 里大量历史行就是「状态」列留空（3 个竖线对 4 列表头），
     **那是刻意的，不是损坏**。而**多于表头**会真的多切出一列、把内容错位——
     Batch 142 撞见的 `||` 截断与 `20-reference.md` 里被裸竖线切断的 URL 都是这一类。
     （本闸第一版写成「必须等于」，立刻把 40+ 行正常的历史行全报成异常——
     **判据过严同样是错**，和 Batch 139/141/142 的判据 bug 同一个教训。）
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


def is_separator(line):
    s = line.strip()
    return bool(s) and set(s) <= set("|-: ") and "-" in s


def scan(path):
    """返回 [(行号, 该行未转义竖线数, 表头列数, 行首摘录)]。"""
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")
    except (IOError, UnicodeDecodeError):
        return []

    problems = []
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
        for lineno, raw in block:
            n = unescaped_pipes(raw)
            # 多于表头 = 真的多切出一列 = 损坏；少于表头会被 GFM 补空，不算
            if n > header_n:
                problems.append((lineno, n, header_n, raw.strip()[:70]))
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
    return problems


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
    print(f"表格结构核对：{checked} 个文件、全部表格行列数一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())

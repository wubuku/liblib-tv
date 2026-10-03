#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**「一行 Markdown 表格行」的三件事，各只有一份实现**（Batch 256 新增）。

**这个模块存在的理由是一次普查的结果**（不是一次事故）：
全树逐文件抽出正则字面量、归一化之后统计跨文件重复，**6 条**，
而排在最前面的两条各是 **3 份**：

| 概念 | 收敛前 | 位置 |
|---|---|---|
| 读表格行的**首格** | **3 份**（**md5 逐字节相同**） | `selftest-batch-rows.py` / `verify-batch-rows.py` / `verify-ledger-refs.py` |
| 按**未转义**竖线切单元格 | **3 份** | 同上 + `verify-tables.py` |
| 是不是一个**批次号** | 2 份（**写法不同但语义相同**） | `verify-batch-rows.py` 的 `NUM_RE` / `selftest-batch-rows.py` 的 `re.fullmatch(r"\\d+[a-z]?")` |

**纪律 274：共享概念只能有一份实现。** 而**「同一件事被手写几遍，就会有几套判真条件」**——
**这三条在本项目里已经出现过一次真实后果**：Batch 252 改闸 5 的表格行判据时，
**如果 `verify-exclusions.py` 那一份没被一起看过，就会出现「三份里两份改了、一份没改」**，
而**没有任何判据会报「这三份应该一致」**。

**刻意不在这里的东西**：`verify-exclusions.py` 里的 `^[ \\t]{0,3}\\|`
（Batch 252 改的，md5 与本模块的 `ROW_RE` 不同）。
**它问的是另一个问题**——**「这一行是不是表格行」与「这一行是不是一整块表格的表头」
是两个问题**（纪律 279 推论的同一族：别因为沾边就合并）。
**合并它们会让闸 5 把 4 空格的代码块当成表格行**——那正是 Batch 252 修掉的形态。

**为什么本模块只放这三件、而不是「所有表格相关的工具」**：
**共享概念的边界要窄**。三件事的共同点是**它们都被至少三处用到、
且逐字相同或语义相同**；再加一件进去就成了「顺手」，而**顺手会慢慢长成垃圾桶**。
零外部依赖，与 `baseline` / `batchread` / `scope` / `pngstat` / `headingkey` / `stagedeps` 一致。
"""

import re

#: **一行表格行的首格**。**收敛前有 3 份逐字节相同的拷贝**（md5 `d96214d3`）。
#:
#: **它是干什么的**：`^\|\\s*([^|]*?)\\s*\\|` —— 行首一个竖线，
#: 然后**尽量少**地取到下一个竖线之前的非竖线内容（`[^|]*?` 的懒惰 + 两侧 `\\s*` 吃掉空白），
#: 最后必须紧跟一个竖线。
#:
#: **注意它认的是「首格」，不是「整行的各格」**——
#: 分割各格是 `UNESCAPED_SPLIT` 的事，**两件事不要混**。
ROW_RE = re.compile(r"^\|\s*([^|]*?)\s*\|")

#: **按未转义竖线切**。`(?<!\\)` 的意思是「前面不是反斜杠」——
#: **转义竖线（`\\|`）是单元格内容的一部分，不切**。
#:
#: **收敛前有 3 份**：`selftest-batch-rows.py` 的 `SPLIT`、
#: `verify-batch-rows.py` 的 `CELL_SPLIT`、`verify-tables.py` 的 `_UNESCAPED_SPLIT`。
UNESCAPED_SPLIT = re.compile(r"(?<!\\)\|")

#: **批次号**：`1` / `6a` / `17c`。
#:
#: **字母后缀不是缺陷**——本树的批次表里**有意**存在 `17a`/`17b`/`17c`、
#: `6a`/`6b`/`6c`、`8a`/`8b` 这类子批次（Batch 199 起）。
#:
#: **收敛前有两种写法**：`verify-batch-rows.py` 用带锚点的 `NUM_RE.match(...)`，
#: `selftest-batch-rows.py` 用 `re.fullmatch(r"\\d+[a-z]?", ...)`——
#: **两者语义相同**（`^…$` 加 `match` 等价于 `fullmatch`），
#: **而「语义相同但写法不同」是收敛的理由，不是保留两份的理由**：
#: **下一次有人只想改其中一份的时候，两份就会真的不一样了。**
BATCH_NUM_RE = re.compile(r"^\d+[a-z]?$")


def first_cell(line):
    """表格行首格；**不是表格行就返回 `None`**（而不是抛异常或返回空串——
    **「这一行没有首格」与「首格是空」是两件事**）。"""
    m = ROW_RE.match(line)
    return m.group(1) if m else None


def cells(line):
    """按**未转义**竖线切一行的各格。**首尾两个空元素是竖线本身带来的，不是格子。**"""
    return UNESCAPED_SPLIT.split(line)


def is_batch_number(s):
    return bool(BATCH_NUM_RE.match(s))

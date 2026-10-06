#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方向十二反验用例 49（不误伤）：**只改闸清单表某一行末尾的说明文字**。

**它与用例 48 是成对的，而它钉的是方向十二自己的风险**：
方向十二读的是「第 N 行是哪道闸」，**不读那一行的说明文字**——
**而闸清单表第三格恰好是自由散文**，每道闸上线时都要在里头补一段来历。
如果判据越界去比第三格的内容，那么**任何人给任何一道闸补一句来历都会被报红**
（误伤比漏报更坏，纪律 248）。

**与前 47 条用例的关系**：它们没有一条能伤到方向十二——
前 47 条改的是 README / 索引 / 侧栏 / 页面 H1 / 登记表**例数**，
**方向十二的输入只有两列（行位置 ↔ 脚本），而它们一行都没碰过**。
**「本批之前没有用例能覆盖它」与「它一定不会误伤」是两件事**，所以要补这一条。

**锚点**：闸清单表里 `scripts/verify-tables.py` 那一行，
**改前改后都存在**，且只往它的**最后一格**末尾追加一句话，**不碰前两格**。
"""
import sys

s = sys.stdin.read()
lines = s.split("\n")

MARK = "`scripts/verify-tables.py`"
idx = [i for i, ln in enumerate(lines) if ln.startswith("|") and MARK in ln]
assert len(idx) == 1, "锚点未命中：`%s` 应当恰好出现在一行闸清单表里，实得 %d 行" % (MARK, len(idx))
i = idx[0]

row = lines[i]
assert row.rstrip().endswith("|"), "锚点未命中：那一行不是收尾带竖线的表格行"

ADD = " **（Batch 319 用例 49 追加的一句来历说明，只动这一格）**"
# 插到**最后一格**的末尾（收尾竖线之前），**不新增竖线**——
# 表格单元格内出现裸竖线会让整张表多切一格，那是闸 8 的职责，不是这一条要验的。
new_row = row.rstrip()[:-1].rstrip() + ADD + " |"
assert new_row.count("|") == row.count("|"), "空转：追加说明改变了竖线数"
lines[i] = new_row
out = "\n".join(lines)
assert out != s, "空转：文件没变"
sys.stdout.write(out)

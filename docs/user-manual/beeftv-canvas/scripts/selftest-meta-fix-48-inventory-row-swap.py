#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方向十二反验用例 48（能抓）：把闸清单表的第 9、10 两行**对调**。

**注入的正是本批实测到的那 10 行错位里的两行**——
闸清单表第 9 行说「截图取证文案」、第 10 行说「手册元数据」，
而覆盖度表与对应关系表都说「闸 9 = 元数据 / 闸 10 = 截图取证文案」。
Batch 319 的对照实验 D 臂实测：**对调之后 44 道闸新增报红 0 道**，
而 A 臂（改对应关系表的闸号）新增报红 1 道——
**说明这一族错位至今无人守**，本方向就是为它立的。

**为什么必须是「对调」而不是「改一个数字」**：改数字会被方向十一之③抓到
（编号集合会缺一个多一个），**而对调后编号集合一个不少**——
**这正是它能活到今天的原因，也是唯一能验出方向十二与方向十一之③不是同一件事的注入。**

**锚点必须改前改后都存在**（本批纪律）：本脚本用两个**闸脚本路径**定位，
它们在两行里各出现一次，不随它们彼此的先后顺序改变——
**所以这个注入在任何一种行序下都打得中**。
"""
import re
import sys

s = sys.stdin.read()
lines = s.split("\n")

META = "`scripts/verify-meta.py`"
LIT = "`scripts/verify-screenshots-literals.py`"

i_meta = [i for i, ln in enumerate(lines)
          if ln.startswith("|") and META in ln and "|" in ln[ln.index(META):]]
i_lit = [i for i, ln in enumerate(lines)
         if ln.startswith("|") and LIT in ln and "|" in ln[ln.index(LIT):]]
assert len(i_meta) == 1, "锚点未命中：`%s` 应当恰好出现在一行闸清单表里，实得 %d 行" % (META, len(i_meta))
assert len(i_lit) == 1, "锚点未命中：`%s` 应当恰好出现在一行闸清单表里，实得 %d 行" % (LIT, len(i_lit))
a, b = i_meta[0], i_lit[0]

# **前提：现在是对的**（Batch 319 已把行序修成闸号序）。
# 若哪天顺序又变了而脚本还照跑，这条用例会去「修复」而不是「注入」——
# **那它就成了一个把真缺陷抹掉的用例**，所以必须先断言顺序。
assert a < b, ("前提不成立：闸清单表里 `%s` 不在 `%s` 之前（行 %d vs %d）——"
               "行序已经不等于闸号序，本用例会把真缺陷抹平而不是注入它"
               % (META, LIT, a + 1, b + 1))

lines[a], lines[b] = lines[b], lines[a]
out = "\n".join(lines)
assert out != s, "空转：两行内容相同，对调后文件没变"
sys.stdout.write(out)

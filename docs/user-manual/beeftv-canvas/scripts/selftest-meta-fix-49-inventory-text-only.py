#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方向十二反验用例 49（不误伤）：**只改闸清单表某一行末尾的说明文字**。

**⚠️ Batch 320 修过这个夹具的锚点，而修的原因正是它自己的纪律**：**
第一版用「行以 `|` 开头且含有 `` `scripts/verify-tables.py` ``」定位，**
**而同一个批次我在「闸 → 反验对应关系」表 9 元数据那一行的说明里写了
`` `verify-tables.py` ``**——于是它一次匹配到 **2 行**，断言失败，
**该用例被判作废**（而**作废正是这套反验的正确行为**：Batch 229 那 3 例空跑
之后补的 `VOID++` 就是为了这个）。**它同时说明一件事：锚点会随着我自己写的
正文一起漂移**——**所以锚点必须落在结构上，而不是落在「某个字符串恰好在这一行」上。**

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

#: **直接引用 `verify-meta.py` 里的那一条，不抄第二份**——
#: **第一版把它抄了一份，而闸 37 `verify-duplication.py` 当场报「同一段正则字面量
#: 出现在 2 个文件里、登记表里没有它」**（它由 `selftest-duplication.py` 真跑时抓到）。
#: **修法是收敛、不是登记**（纪律 274：共享概念只能有一份实现）。
#: **顺带得到一个更好的性质**：夹具此后测的就是**判据自己正在用的那一条**，
#: **方向十二的形态一变，夹具自动跟着变**——而抄一份的话它会静悄悄地留在旧形态上。
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("vm", "scripts/verify-meta.py")
_vm = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_vm)
_INV_ROW_RE = _vm._INV_ROW_RE

s = sys.stdin.read()
lines = s.split("\n")

# **注意 `group(1)` 是带 `verify-` 前缀的裸名**（`verify-tables`），不是 `tables`——
# **而本批当天已经因为「忘剥 `verify-` 前缀」栽了五次**（纪律 355），
# **所以这一行旁边就把它写出来，而不是指望下次记得**。
WANT = "verify-tables"
idx = [i for i, ln in enumerate(lines)
       if _INV_ROW_RE.match(ln) and _INV_ROW_RE.match(ln).group(1) == WANT]
assert len(idx) == 1, ("锚点未命中：闸清单表里 `scripts/verify-%s.py` 应当恰好一行，"
                       "实得 %d 行" % (WANT, len(idx)))
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

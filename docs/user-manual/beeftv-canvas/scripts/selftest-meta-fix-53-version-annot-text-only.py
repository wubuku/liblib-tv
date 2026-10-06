#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方向十四反验用例 53（不误伤）：**同一行、只改冒号之后的说明、版本号一个字不动**。

**它比「改别的行」更强一档**：改的就是方向十四读的那一行
（**Batch 320 的用例 51 已经用过这个更强形状**，方向十三那边有效，
**而方向十四是新的判据，它自己的误伤风险此前无人验过**）。
**前 51 例一条都不碰版本标注**，所以方向十四引入的误伤风险是新的。

**为什么必须有不误伤这一支**：方向十四的正向形态是
「引用块行 + 以 `>` 开头 + 含 `vX.Y.Z 起`」——
**而这个形态很宽**，正文里、注释里、别的页里都可能撞上同一种字面。
**没有这一支，就不知道它是「只认版本号」还是「碰见 `v1.6.22 起` 就报」。**
"""
import re
import sys

s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, l in enumerate(lines)
       if l.lstrip().startswith(">") and "v1.6.22 起不再弹" in l]
assert len(idx) == 1, ("锚点未命中：引用块里含「v1.6.22 起不再弹」的行应当恰好 1 行，"
                       "实得 %d" % len(idx))
i = idx[0]
before = lines[i]
#: **只动版本号之后的那半句**——把「直接建出空场景节点」改成「直接建出一个空场景节点」
assert "直接建出空场景节点" in before, "锚点未命中：那一行没有要改的说明文字：%r" % before[:70]
lines[i] = before.replace("直接建出空场景节点", "直接建出一个空场景节点", 1)
out = "\n".join(lines)
assert out != s, "空转：文件没变"
#: **版本号必须一个字都没动**——这一支的全部意义就在这里
m = re.search(r"v(\d+)\.(\d+)\.(\d+)\s*起", lines[i])
assert m and m.group(0) == "v1.6.22 起", \
    "版本号被动过了：%r —— **不误伤这一支的前提就是版本号不许动**" % (m and m.group(0))
sys.stdout.write(out)

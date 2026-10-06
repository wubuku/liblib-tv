#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方向十三反验用例 50（能抓）：把 `verify-tables.py` docstring 自称的闸号改错。

**注入的就是 Batch 319 对照实验的 C 臂**——那一臂实测「44 道闸新增报红 0 道」，
**而它之所以没有判据守，是因为这个家族至今没有**。

**锚点必须改前改后都存在**：用「三引号 + 第」开头的**那一行**定位，
**而不是全局替换「第 N 道闸」**——`verify-tables.py` 的 docstring 里
还写着「本文原先自称『第七道闸』」（Batch 246 的订正说明），
**全局替换会把那句订正也一起改掉，于是注入做的是另一件事**
（而输出看起来一样，这是 Batch 304 记过的形态）。
"""
import re
import sys

s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, l in enumerate(lines)
       if l.lstrip().startswith('"""第') and "道闸" in l]
assert len(idx) == 1, ("锚点未命中：以 `\"\"\"第` 开头且含「道闸」的行应当恰好 1 行，实得 %d"
                       % len(idx))
i = idx[0]
m = re.match(r'^(\s*"""第)([一二三四五六七八九十]+)(道闸.*)$', lines[i])
assert m, "锚点未命中：那一行不是「\"\"\"第 N 道闸…」的形态：%r" % lines[i][:60]
assert m.group(2) == "八", ("锚点未命中：真实自称是「第%s道闸」，而本用例钉的是「第八道闸」"
                            % m.group(2))
lines[i] = m.group(1) + "七" + m.group(3)
out = "\n".join(lines)
assert out != s, "空转：文件没变"
assert "第七道闸" in out, "空转：改后没有出现「第七道闸」"
sys.stdout.write(out)

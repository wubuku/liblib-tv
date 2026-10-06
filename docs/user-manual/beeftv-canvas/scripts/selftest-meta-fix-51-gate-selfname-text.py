#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方向十三反验用例 51（不误伤）：docstring 首行**只改说明、闸号不动**。

**它与用例 50 是成对的，而它比「改 docstring 的别的行」更强一档**：
它改的就是**方向十三读的那一行**，只是改的不是闸号。
**方向十三必须只认那个 N，不能认整行、也不能认首行的长度**——
**而前 49 例一条都碰不到 docstring**（它们改 README / 索引 / 侧栏 / H1 / 例数 /
表格行序），**所以方向十三自己引入的误伤风险此前无人验过**。

**锚点**：与用例 50 同一个锚点行（`\"\"\"第 N 道闸…`），
**改前改后都存在**；只往冒号之后追加一句，**N 一个字不动**。
"""
import re
import sys

s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, l in enumerate(lines)
       if l.lstrip().startswith('"""第') and "道闸" in l]
assert len(idx) == 1, ("锚点未命中：应当恰好 1 行，实得 %d" % len(idx))
i = idx[0]
m = re.match(r'^(\s*"""第)([一二三四五六七八九十]+)(道闸.*)$', lines[i])
assert m, "锚点未命中：那一行不是「\"\"\"第 N 道闸…」的形态：%r" % lines[i][:60]

# **只动 N 之后的说明部分**
tail = m.group(3)
assert "：" in tail, "锚点未命中：说明部分里没有冒号可挂：%r" % tail[:60]
lines[i] = m.group(1) + m.group(2) + tail + "（用例 51：同一行只改说明，闸号不动）"

out = "\n".join(lines)
assert out != s, "空转：文件没变"
# **闸号必须原样保留**——这一条是本用例与 50 的全部区别
new_m = re.match(r'^(\s*"""第)([一二三四五六七八九十]+)(道闸.*)$', out.split("\n")[i])
assert new_m.group(2) == m.group(2), "空转：闸号被改动了，本用例就不是「不误伤」那一支"
sys.stdout.write(out)

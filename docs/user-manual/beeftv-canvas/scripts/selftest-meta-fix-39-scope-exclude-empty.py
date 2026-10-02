#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""注入：把 `config.mjs` 的 `srcExclude` 改成空数组 `[]`。

**这一例专治「零输入不许报绿」**（Batch 191）。空集合在这里**不是**「没有排除项」
这种正常情况，而是**判据悄悄从「排除」翻成「全放行」**：
所有 md 都会算成发布页，于是「内容页数」凭空多出 6 个、
方向一的方向会因为数字对不上而报出一片假异常——
**而闸门自己完全看不出哪里不对**。

**判据把「读到了 0 个排除项」当成合法输入，就等于把一把没有刻度的尺子当成了尺子用。**
所以它必须 rc=2「未能核对」。
"""
import re
import sys

s = sys.stdin.read()
m = re.search(r"srcExclude:\s*\[.*?\]", s, re.S)
assert m, "锚点：config.mjs 里找不到 srcExclude——空转，作废本用例"
out = s[:m.start()] + "srcExclude: []" + s[m.end():]
assert out != s, "替换后内容没变——空转，作废本用例"
assert "srcExclude: []" in out, "注入不干净"
sys.stdout.write(out)

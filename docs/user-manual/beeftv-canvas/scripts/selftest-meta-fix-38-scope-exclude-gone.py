#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""注入：把 `config.mjs` 的 `srcExclude` 整条删掉。

**「读得到文件，但里面没有 srcExclude」**——发布范围的定义改了（比如换了
配置写法、或把这行挪到了别处），而闸 9 的正向数字全靠它划定「哪些算发布页」。
这时**必须 rc=2「未能核对」，不得退回任何内置列表**：
退回列表等于把刚拆掉的副本又装回去，而且这次是在没人知道的情况下。
"""
import re
import sys

s = sys.stdin.read()
m = re.search(r"^\s*srcExclude:\s*\[.*?\],?\s*$", s, re.S | re.M)
assert m, "锚点：config.mjs 里找不到 srcExclude 那一行——空转，作废本用例"
out = s[:m.start()] + s[m.end():]
assert out != s, "替换后内容没变——空转，作废本用例"
assert "srcExclude" not in out, "srcExclude 仍残留在注入结果里，注入不干净"
sys.stdout.write(out)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：找出 `libtv.director.timeline-guide.dismissed.v1` 这个键的**全部**使用点。

★ 目的：读它的地方 ⟹ 引导的**启动条件**（什么时候弹）；写它的地方 ⟹ 什么时候被标记看过。
"""
import pathlib
import re

CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
OUT = pathlib.Path("/tmp/liblib_srcjs2/guide834-flag.txt")

s = CHUNK.read_text(encoding="utf-8", errors="replace")
key = "timeline-guide.dismissed"
idxs = [m.start() for m in re.finditer(re.escape(key), s)]
lines = ["命中 %d 处" % len(idxs)]
for i in idxs:
    lines.append("=== at %d ===" % i)
    lines.append(s[max(0, i - 1500):i + 900])
    lines.append("")
OUT.write_text("\n".join(lines), encoding="utf-8")
print("已落盘：", OUT)
print("命中", len(idxs), "处")
for i in idxs:
    print("--- at", i, "---")
    print(s[max(0, i - 900):i + 400])

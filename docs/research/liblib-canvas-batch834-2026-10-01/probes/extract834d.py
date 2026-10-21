#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：找出引导的**启动条件**（localStorage 标记的读取处 ＋ step 的初值/置 0 处）。"""
import pathlib
import re

CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
OUT = pathlib.Path("/tmp/liblib_srcjs2/guide834-start.txt")

s = CHUNK.read_text(encoding="utf-8", errors="replace")
lines = []
for pat in (r"getItem\(l6\)", r"ex\(0\)", r"useState\(null\)", r"ex\("):
    ms = list(re.finditer(pat, s))
    lines.append("=== %s (%d 处) ===" % (pat, len(ms)))
    for m in ms[:8]:
        i = m.start()
        seg = s[max(0, i - 500):i + 400]
        if pat == r"ex\(" and not re.search(r"timeline|guide|localStorage", seg):
            continue
        lines.append(seg)
        lines.append("  ---")
OUT.write_text("\n".join(lines), encoding="utf-8")
print("已落盘：", OUT)
print("\n".join(lines)[:7000])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：抽出「帮助 → 使用教程」菜单项调用的那个函数（`_`）的原文。

★ 目的：确认「使用教程」是不是**复位**引导（把 step 归 0 ＋ 清掉 localStorage 标记），
  还是只是「打开时间轴」。
"""
import pathlib
import re

CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
OUT = pathlib.Path("/tmp/liblib_srcjs2/guide834-tutorial.txt")

s = CHUNK.read_text(encoding="utf-8", errors="replace")

# 找到帮助菜单的调用点：onClick:()=>{N(!1),_()}
i = s.find("canvas:directorTutorial\")})")
if i < 0:
    raise SystemExit("找不到使用教程菜单项")
seg = s[max(0, i - 120000):i]

lines = []
for name in (r"_\s*=\s*\(0,o\.useCallback\)", r"_=\(\)=>", r"let _"):
    ms = list(re.finditer(name, seg))
    lines.append("=== %s (%d 处) ===" % (name, len(ms)))
    for m in ms[-4:]:
        j = m.start()
        lines.append(seg[max(0, j - 400):j + 500])
        lines.append("  ---")
OUT.write_text("\n".join(lines), encoding="utf-8")
print("已落盘：", OUT)
print("\n".join(lines)[:5000])

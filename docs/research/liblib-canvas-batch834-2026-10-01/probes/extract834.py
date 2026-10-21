#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：从源站 chunk 里抽出引导状态机（step / onNext / onSkip / 隐藏条件）。

★ 为什么读 chunk 而不是从行为反推：引导的「什么时候开始／第 5 步之后怎么办／
  收起状态存哪」这些**状态机**在行为上很难反推（尤其「是否持久化」）⟹ 直接读原文。
"""
import pathlib
import re
import sys

CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
OUT = pathlib.Path("/tmp/liblib_srcjs2/guide834-state.txt")


def main():
    s = CHUNK.read_text(encoding="utf-8", errors="replace")
    i = s.find("(0,i.jsx)(cC,")
    if i < 0:
        raise SystemExit("找不到 cC 的调用点")
    seg = s[max(0, i - 90000):i]
    lines = []
    for name in ("eG=", "eK=", "eg=", "l6="):
        ms = list(re.finditer(re.escape(name), seg))
        lines.append("=== %s (%d 处) ===" % (name, len(ms)))
        for m in ms[-3:]:
            j = m.start()
            lines.append(seg[max(0, j - 300):j + 460])
            lines.append("  ---")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("已落盘：", OUT)
    print("\n".join(lines)[:6000])


if __name__ == "__main__":
    main()

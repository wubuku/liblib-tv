#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833：源站 raw 与 clone raw 的 15 枚预设语义**逐字段比对**。

★ 这只是「核对」，不是门禁（门禁在 scripts/verify-liblib-batch833.py）。
  它存在的意义：把「两边相等」这件事**当场跑出来**，而不是靠眼看。
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIELDS = ("位置", "旋转", "注视", "FOV")


def main():
    src = json.loads((ROOT / "raw" / "source-833-camera-preset-semantics.json")
                     .read_text(encoding="utf-8"))
    cl = json.loads((ROOT / "raw" / "clone-833-camera-preset-semantics.json")
                    .read_text(encoding="utf-8"))
    sp = src["预设"]
    cp = cl["②逐枚"]
    assert len(sp) == len(cp) == 15, (len(sp), len(cp))
    bad = []
    for s, c in zip(sp, cp):
        if s["label"] != c["label"]:
            bad.append(("标签", s["label"], c["label"]))
            continue
        sem = c["语义"]
        for k in FIELDS:
            a = s[k] if isinstance(s[k], list) else [s[k]]
            b = sem[k] if isinstance(sem[k], list) else [sem[k]]
            a = [float(x) for x in a]
            b = [float(x) for x in b]
            if a != b:
                bad.append((s["label"], k, a, b))
        if c["后机位数"] != c["前机位数"] + 1:
            bad.append((s["label"], "机位数", c["前机位数"], c["后机位数"]))
    print("字段不一致：", bad if bad else "无（15 枚 × 4 字段 = 60 组全等）")
    print("删除日志：")
    for line in cl["③删除日志"]:
        print("  ", line)
    print("末次机位：", cl["④末次机位"])
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

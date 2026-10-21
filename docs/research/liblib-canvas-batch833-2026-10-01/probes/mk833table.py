#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833：从 raw **程序化**生成 README 里的 15 枚语义表（不手抄）。

★ 为什么：15 枚 × 4 组 = 60 个数 ⟹ 手抄必然出错 ⟹ 而 README 里的表
  是**给人看**的，它必须与 raw（门禁的期望值）**逐字一致** ⟹ 所以由脚本生成。

用法：python3 mk833table.py  ⟹ 打印 Markdown 表行（不含表头）
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "raw" / "source-833-camera-preset-semantics.json"


def fmt(values):
    if isinstance(values, list):
        return "(" + ", ".join(("%g" % float(v)) for v in values) + ")"
    return "%g" % float(values)


def main():
    doc = json.loads(RAW.read_text(encoding="utf-8"))
    for p in doc["预设"]:
        print("| 序 %d | %s | %s | %s | %s | %s |" % (
            p["idx"], p["label"], fmt(p["位置"]), fmt(p["旋转"]),
            fmt(p["注视"]), fmt(p["FOV"])))


if __name__ == "__main__":
    main()

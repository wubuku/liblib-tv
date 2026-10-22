#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846：源站 ↔ clone 的**逐字段几何对拍**（只读，不改任何东西）。

## 为什么需要这个脚本

846 的源站 raw 里，`读数.chip` 是一个**混合数组**（35 条）：
  · 真正的 chip（50×26 的圆角胶囊）共 **14** 枚（发型 7 ＋ 妆容 7）
  · **色块**（35×35 的圆）共 **21** 枚（发色 11 ＋ 口红 10）⟹ ⟹ 它们也被
    探针的 chip 选择器捞进来了（⟹ ⟹ **不是探针的错**，是源站这两个控件
    共用了同一套「胶囊」类名）
⟹ ⟹ **分不开就没法对拍** ⟹ ⟹ 本脚本按**盒高**（26 ⟹ chip；35 ⟹ 色块）
把混合数组**机械地**分成两类 ⟹ ⟹ 再逐项比。

★ 判定只用**绝对几何**（⟹ ⟹ 源站与 clone 的模态同在视口 (361,161)，
  ⟹ ⟹ clone 的 rel 坐标 ＋ 361/161 就是同一片的绝对坐标）。

★ 输出：`/tmp/b846-parity.json`
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch846-2026-10-01"
RAW = BATCH / "raw/source-846-outfit.json"
CLONE = pathlib.Path("/tmp/b846-clone-outfit.json")

# ★ clone 的 rel → abs 的偏移（★ clone 与源站的模态**同在视口 (361,161)**）
MODAL = (361, 161)


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def to_abs(box):
    if not box:
        return None
    return {"x": box["x"] + MODAL[0], "y": box["y"] + MODAL[1],
            "w": box["w"], "h": box["h"]}


def main():
    src = load(RAW)["★读数"]
    cl = load(CLONE)["A_第四段"]
    out = {}

    # ── 拆分源站的混合 chip 数组 ─────────────────────────────────────
    chips = [c for c in src["chip"] if c["box"]["h"] == 26]
    swatches = [c for c in src["chip"] if c["box"]["h"] == 35]
    out["★源站_chip数"] = len(chips)
    out["★源站_色块数"] = len(swatches)
    out["★源站_混合数组总数"] = len(src["chip"])

    # ── H3 ────────────────────────────────────────────────────────────
    src_h3 = [(h["text"], h["box"]) for h in src["H3"]]
    cl_h3 = [(h["text"], to_abs(h["box"])) for h in cl["H3"]]
    out["★H3_源站"] = src_h3
    out["★H3_clone"] = cl_h3
    out["★H3_逐项相等"] = (src_h3 == cl_h3)

    # ── chip（按**出现顺序**一一对应） ────────────────────────────────
    src_chips = [(c["text"], c["box"]) for c in chips]
    cl_chips = [(c["text"], to_abs(c["box"])) for c in cl["chip"]]
    out["★chip_源站"] = src_chips
    out["★chip_clone"] = cl_chips
    out["★chip_逐项相等"] = (src_chips == cl_chips)

    # ── 色块（源站混合数组里**没有**文案 ⟹ ⟹ 只比盒） ────────────────
    src_sw = [c["box"] for c in swatches]
    cl_sw = [to_abs(c["box"]) for c in cl["色块"]]
    out["★色块_源站"] = src_sw
    out["★色块_clone"] = cl_sw
    out["★色块_逐项相等"] = (src_sw == cl_sw)

    # ── 卡片 ──────────────────────────────────────────────────────────
    src_cards = [(c["aria"], c["卡盒"]) for c in src["卡片"]]
    cl_cards = [(c.get("aria"), to_abs(c["卡盒"])) for c in cl["卡片"]]
    out["★卡片_源站"] = src_cards
    out["★卡片_clone"] = cl_cards
    out["★卡片_逐项相等"] = (src_cards == cl_cards)

    # ── 卡片**名字**盒（源站名字 11px/16px 在图下方） ─────────────────
    src_names = [(c["aria"], c["名字盒"]) for c in src["卡片"]]
    cl_names = [(c.get("aria"), to_abs(c.get("名字盒"))) for c in cl["卡片"]]
    out["★卡片名_源站"] = src_names
    out["★卡片名_clone"] = cl_names
    out["★卡片名_逐项相等"] = (src_names == cl_names)

    # ── 卡片**媒体盒**（76×76 的图区） ────────────────────────────────
    src_media = [(c["aria"], c["媒体盒"]) for c in src["卡片"]]
    cl_media = [(c.get("aria"), to_abs(c.get("媒体盒"))) for c in cl["卡片"]]
    out["★媒体盒_源站"] = src_media
    out["★媒体盒_clone"] = cl_media
    out["★媒体盒_逐项相等"] = (src_media == cl_media)

    # ── 子页签行：三枚的盒 ────────────────────────────────────────────
    src_tabs = [(b["aria"], b["box"]) for b in src["子页签行"]["按钮"]]
    cl_tabs = [(b.get("aria") or b.get("text"), to_abs(b["box"]))
               for b in cl["子页签行"]["按钮"]]
    out["★子页签_源站"] = src_tabs
    out["★子页签_clone"] = cl_tabs
    out["★子页签_逐项相等"] = (src_tabs == cl_tabs)

    # ── 滚动高 ────────────────────────────────────────────────────────
    out["★滚动高_源站"] = src["滚动区"]["滚动高"]
    out["★滚动高_clone"] = (cl.get("面板") or {}).get("滚动高")
    out["★滚动高_相等"] = (out["★滚动高_源站"] == out["★滚动高_clone"])

    # ── 汇总 ──────────────────────────────────────────────────────────
    keys = [k for k in out if k.endswith("_逐项相等") or k.endswith("_相等")]
    out["★汇总"] = {k: out[k] for k in keys}
    out["★全绿"] = all(out[k] for k in keys)
    return out


if __name__ == "__main__":
    out = main()
    pathlib.Path("/tmp/b846-parity.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：/tmp/b846-parity.json")
    for k, v in out["★汇总"].items():
        print("  %-24s %s" % (k, v))
    print("★全绿 =", out["★全绿"])
    if not out["★全绿"]:
        for k in out["★汇总"]:
            if out["★汇总"][k] is False:
                print("\n── %s 不等 ──" % k)
                a = out.get(k.replace("_逐项相等", "_源站")) or out.get(k.replace("_相等", "_源站"))
                b = out.get(k.replace("_逐项相等", "_clone")) or out.get(k.replace("_相等", "_clone"))
                if isinstance(a, list) and isinstance(b, list):
                    for i in range(max(len(a), len(b))):
                        x = a[i] if i < len(a) else None
                        y = b[i] if i < len(b) else None
                        flag = "  " if x == y else "✗ "
                        print("  %s[%2d] 源=%s" % (flag, i, x))
                        if x != y:
                            print("        clone=%s" % (y,))
                else:
                    print("  源=%s clone=%s" % (a, b))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 831：把 clone 的 ⌘ 徽标**像素**与源站截图里的 ⌘ 徽标逐像素比对。

★ 为什么必须做像素比对：⌘ 是 **16×16 的 SVG path**（batch 830 的教训）⟹
  「path 字符串逐字相等」只证明**数据**一致，不证明**渲染**一致；
  而 path 抄错（把下半部两条臂的先后顺序抄反了）在 16px 上**肉眼看不出来**。

★ 本批的实测结论：把 path 改回源站真原文之前，clone 与源站的同一枚 ⌘
  **最大绝对差 54/255、有 10 个像素差 > 8** ⟹ 明显不同形；
  改对之后 **最大绝对差 5/255、零个像素差 > 8** ⟹ 完全同形。
  ⟹ ★ 这条比对**有能力**区分「path 抄对」与「path 抄错」⟹ 可以当门禁用。

## 用法

    python3 glyphcmp831.py            # 用仓库里的两张截图比对

## 判据

- 允许对齐位移 ±3px（截图渲染的亚像素差异）
- **最大绝对差 ≤ 24** 且 **差 > 8 的像素数 ≤ 2** ⟹ 判「同形」
"""
import json
import pathlib
import sys

from PIL import Image

BATCH = pathlib.Path(__file__).resolve().parent.parent
SRC = BATCH / "images" / "source-831_shortcuts.png"
CLONE = BATCH / "images" / "clone-831_shortcuts.png"
OUT = BATCH / "raw" / "glyph-831-pixel-compare.json"

# 源站「打组」行的 ⌘ 徽标（读数 allSvgs[0] = 695,209,16,16）
# ⟹ clone 同一坐标（几何已逐字相等 ⟹ 同一位置）
GLYPHS = {"command": (695, 209, 16, 16)}

# 判定阈值（★ 必须小于「path 抄错」那版的实测差异：最大差 54 / 10 个像素差>8）
MAX_ABS_DIFF = 24
MAX_OVER8 = 2


def crop(img, x, y, w, h):
    return img.crop((x, y, x + w, y + h)).convert("L")


def matrix(im):
    return [[im.getpixel((a, b)) for a in range(im.width)] for b in range(im.height)]


def best_shift(a, b, rng=3):
    ma, mb = matrix(a), matrix(b)
    best = None
    for dy in range(-rng, rng + 1):
        for dx in range(-rng, rng + 1):
            diffs = []
            for y in range(len(ma)):
                for x in range(len(ma[0])):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < len(mb) and 0 <= xx < len(mb[0]):
                        diffs.append(abs(ma[y][x] - mb[yy][xx]))
            if not diffs:
                continue
            score = sum(diffs) / len(diffs)
            if best is None or score < best[0]:
                best = (round(score, 3), dx, dy)
    return best


def compare(src_img, clone_img, x, y, w, h):
    a = crop(src_img, x, y, w, h)
    b = crop(clone_img, x, y, w, h)
    score, dx, dy = best_shift(a, b)
    ma, mb = matrix(a), matrix(b)
    diffs = []
    for yy in range(h):
        for xx in range(w):
            y2, x2 = yy + dy, xx + dx
            if 0 <= y2 < h and 0 <= x2 < w:
                diffs.append(abs(ma[yy][xx] - mb[y2][x2]))
    maxd = max(diffs)
    over8 = sum(1 for d in diffs if d > 8)
    return {
        "裁剪": [x, y, w, h],
        "对齐位移": [dx, dy],
        "平均绝对差": score,
        "最大绝对差": maxd,
        "差 > 8 的像素数": over8,
        "总像素数": len(diffs),
        "判定": "同形" if maxd <= MAX_ABS_DIFF and over8 <= MAX_OVER8 else "★不同形",
        "源站像素矩阵": ma,
        "clone像素矩阵": mb,
    }


def main():
    if not SRC.exists() or not CLONE.exists():
        print("缺截图：%s / %s" % (SRC, CLONE))
        return 1
    src = Image.open(SRC)
    clone = Image.open(CLONE)
    out = {}
    bad = 0
    for name, (x, y, w, h) in GLYPHS.items():
        r = compare(src, clone, x, y, w, h)
        out[name] = r
        print("%-8s 对齐位移=(%d,%d) 平均差=%.2f 最大差=%d 差>8 的像素=%d/%d → %s"
              % (name, r["对齐位移"][0], r["对齐位移"][1], r["平均绝对差"],
                 r["最大绝对差"], r["差 > 8 的像素数"], r["总像素数"], r["判定"]))
        if r["判定"] != "同形":
            bad += 1
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

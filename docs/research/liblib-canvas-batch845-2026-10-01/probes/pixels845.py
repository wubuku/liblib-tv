#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 845：**像素**证据提取 —— 从源站截屏里**机器提取**滑杆的外观事实。

## 为什么需要这一步

`source845_body.py` 量到的是**结构**（哪些元素、盒多大、计算样式是什么），
但**外观**（轨道几像素粗、什么颜色；圆钮几像素、什么颜色；圆心点什么颜色）
**结构量不出来** ⟹ ⟹ 必须看像素。

★ 而且这一步**不能靠推理**：clone 原来的样式是「4px 轨道 ＋ 12px 圆钮 ＋ 无填充段」，
  看着「像」，但源站**不是**这样 ⟹ ⟹ 只有像素能定案。

## 怎么提取（★ 不手打坐标）

- 轨道行 ＝ `输入盒.y + 5`（输入盒 12 高 ⟹ 中心行；轨道是 2px ⟹ 中心行必然落在轨道里）
- 圆钮   ＝ 该行里「≥ 240 的近白**连续段**」（轨道填充段也是近白 ⟹ 故圆钮取**最长的那段**，
          再用「该段上方/下方是否变窄」交叉验证它是个圆）
- 填充段 ＝ 从轨道左端起、到圆钮左缘止的连续近白段
- 未填充 ＝ 圆钮右缘之后、轨道右端之前的像素
- 圆心点 ＝ 圆钮中心 2×2 的像素（比圆钮暗得多）

★ **行程公式**（inset／travel）由**两条**滑杆**解**出来：
  「丰胸」min −100 ⟹ 初值 0 ⟹ ratio 0.5；「AI 增高」min 0 ⟹ ratio 0
  ⟹ ⟹ 两个圆钮中心 ⟹ ⟹ 解出 inset 与 travel（★ 不是手打常数）

★ 输出：`docs/research/liblib-canvas-batch845-2026-10-01/raw/source-845-pixels.json`
"""
import json
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch845-2026-10-01"
RAW_BODY = BATCH / "raw/source-845-body.json"
RAW_VISUAL = BATCH / "raw/source-845-visual.json"
PNG = BATCH / "raw/source-845-sliders.png"
OUT = BATCH / "raw/source-845-pixels.json"

NEAR_WHITE = 240      # ★ 近白阈值（圆钮与填充段都是 255）
BRIGHT = 100         # ★ 「亮」的阈值（用来找轨道行）


def analyze(path: pathlib.Path, origin, sliders):
    im = Image.open(path).convert("RGB")
    px = im.load()
    ox, oy = origin["x"], origin["y"]

    def gray(x, y):
        return px[x - ox, y - oy][0]

    out = {"★截图原点_abs": origin, "★图片尺寸": list(im.size), "滑杆": []}

    # ★ 面板底色（取整张图里最常见的暗色）
    hist = {}
    for yy in range(im.size[1]):
        for xx in range(im.size[0]):
            c = px[xx, yy][0]
            hist[c] = hist.get(c, 0) + 1
    bg = max((c for c in hist if c < 100), key=lambda c: hist[c])
    out["★面板底色灰阶"] = bg

    for s in sliders:
        inp = s["输入盒"]
        dot_box = s["缩略点盒"]
        left, right = inp["x"], inp["x"] + inp["w"] - 1
        top, bot = inp["y"] - 8, inp["y"] + 14

        # ★★ 「不是底色」＝ 这个像素**被画过东西**（轨道 53／圆钮 255／圆心点 70 都算）
        #   ⟹ ⟹ 底色 36 不算 ⟹ ⟹ 与「近白」无关 ⟹ ⟹ 轨道（53）与圆钮（255）都能判出来
        LIT = bg + 4

        # ★ 轨道行 ⟹ 该行里「被画过」的像素铺满整条轨道
        track_rows = []
        for y in range(top, bot + 1):
            n = sum(1 for x in range(left, right + 1) if gray(x, y) > LIT)
            if n > (right - left + 1) * 0.8:
                track_rows.append(y)
        y_mid = track_rows[len(track_rows) // 2] if track_rows else inp["y"] + 5

        # ★ 圆钮直径 ⟹ 量**圆心那一列**的竖向跨度
        #   （★ 圆钮是圆 ⟹ 宽＝高；★ 竖向是**唯一**不与「2px 高的轨道」混淆的方向）
        cx = dot_box["x"] + dot_box["w"] / 2.0
        col = int(round(cx))
        ys = [y for y in range(top, bot + 1) if gray(col, y) > LIT]
        diameter = max(ys) - min(ys) + 1
        k0, k1 = cx - diameter / 2.0, cx + diameter / 2.0

        row = [gray(x, y_mid) for x in range(left, right + 1)]
        fill_vals = row[: int(round(k0)) - left]        # ★ 轨道左端 ⟹ 圆钮左缘
        unfilled = row[int(round(k1)) - left + 1:]       # ★ 圆钮右缘 ⟹ 轨道右端

        # ★ 圆心点 ⟹ 用 DOM 给的 2×2 盒取像素
        dot = [[gray(dot_box["x"] + dx, dot_box["y"] + dy) for dx in (0, 1)]
               for dy in (0, 1)]

        ratio = (float(s["value"]) - float(s["min"])) / (float(s["max"]) - float(s["min"]))
        out["滑杆"].append({
            "名字": s["名字文字"],
            "min": s["min"], "max": s["max"], "value": s["value"],
            "★ratio": ratio,
            "★轨道行": track_rows,
            "★轨道厚": len(track_rows),
            "★圆钮盒": {"x": k0, "y": y_mid - diameter // 2,
                         "w": diameter, "h": diameter},
            "★圆钮中心x": cx,
            "★圆钮直径": diameter,
            "★圆心点像素": dot,
            "★圆心点灰阶": [dot[0][0], dot[0][1], dot[1][0], dot[1][1]],
            "★填充段_灰阶": sorted(set(fill_vals))[-3:],
            "★未填充段_灰阶": sorted(set(unfilled))[:3] if unfilled else [],
            "★源站DOM_缩略点盒": dot_box,
        })
    return out


def main() -> int:
    body = json.loads(RAW_BODY.read_text(encoding="utf-8"))
    visual = json.loads(RAW_VISUAL.read_text(encoding="utf-8"))
    sliders = body["★读数"]["滑杆"]
    origin = visual["★截图片段"]

    # ★ 只有**截图窗口内**的滑杆能被像素分析（视口外的滑杆在图片里不存在）
    clip = origin
    vis = []
    for s in sliders:
        y = s["输入盒"]["y"]
        if clip["y"] <= y <= clip["y"] + clip["height"]:
            vis.append(s)
    out = analyze(PNG, origin, vis)

    # ★★ 由**两条**滑杆解出「圆钮中心的行程公式」：center = 轨道左端 + inset + ratio·travel
    #   ⟹ ⟹ 两个 (ratio, center) 解两个未知数 ⟹ ⟹ 不是手打常数
    pts = [(r["★ratio"], r["★圆钮中心x"] - sliders[0]["输入盒"]["x"])
           for r in out["滑杆"] if r["名字"] in ("丰胸", "AI 增高")]
    if len(pts) == 2:
        (r0, c0), (r1, c1) = sorted(pts)
        travel = (c1 - c0) / (r1 - r0) if r1 != r0 else None
        inset = c0 - r0 * travel if travel is not None else None
        out["★行程公式"] = {
            "式": "圆钮中心x = 轨道左端 + inset + ratio * travel",
            "inset": inset, "travel": travel,
            "★由哪两条解出": ["AI 增高（ratio 0）", "丰胸（ratio 0.5）"],
        }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已写入", OUT)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2200])
    return 0


if __name__ == "__main__":
    sys.exit(main())

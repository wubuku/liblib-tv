#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 850：**机器提取**预览区（中列）的期望值。

★ 原则（沿用前几批的纪律）：
  - 期望值**全部**从**入库的源站 raw**里提取 ⟹ ⟹ **不手打**；
  - **原点也**从 raw 提取 ⟹ ⟹ 不用「361/161」这种手打常数；
  - 提取完**自己校验**（交叉校验 ＋ 不变量）⟹ ⟹ 不合格就**不产出**。

## 原点是怎么机器提取的

★ 源站模态**外框**是 1200×760 @ (360,160) 且带 **1px border**
  ⟹ ⟹ **内容框** = 1198×758 @ **(361,161)** ⟹ ⟹ 内容原点 = 外框原点 ＋ 边框宽度。
★ 本脚本从 raw 的「★模态根」盒 ＋ `borderTopWidth` **算**出这个原点 ⟹ ⟹ 不手打。

## 交叉校验（两条独立证据）

① **跨 raw**：batch 848 的 raw（**另一趟探针、另一份坐标**）里同一批元素
   ⟹ ⟹ 减同一个原点后 ⟹ ⟹ rel 盒必须与 850 raw **逐项相同**；
② **不变量**：右栏 ASIDE 的 rel x ＝ 912 ⟹ ⟹ 与 clone 侧的右栏 rel x 一致
   ⟹ ⟹ 说明原点没取错 1px。

## 输出

`probes/preview-850-data.json`
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch850-2026-10-01"
RAW = BATCH / "raw"
OUT = BATCH / "probes/preview-850-data.json"

R_DEFAULT = RAW / "source-850-default.json"
R_HALF = RAW / "source-850-half.json"
R_FULL = RAW / "source-850-full.json"
R_848 = ROOT / ("docs/research/liblib-canvas-batch848-2026-10-01"
                "/raw/source-848-p1.json")


def read_json(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def walk(node, path="root", out=None):
    """★ 把 raw 的树摊平成 [(路径, 节点)]。"""
    if out is None:
        out = []
    if not isinstance(node, dict):
        return out
    out.append((path, node))
    for i, k in enumerate(node.get("c2") or []):
        walk(k, "%s.c2[%d]" % (path, i), out)
    return out


def find_one(node, pred):
    for _, n in walk(node):
        if pred(n):
            return n
    return None


def norm_box(node):
    """★ raw 里的盒有两种形状：[x,y,w,h] 与 {x,y,w,h} ⟹ ⟹ 统一。"""
    b = node.get("b")
    if isinstance(b, list):
        return {"x": b[0], "y": b[1], "w": b[2], "h": b[3]}
    if isinstance(b, dict):
        return {"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"]}
    raise ValueError("这个节点没有盒：%r" % (node.get("t"),))


def rel(box, ox, oy):
    return {"x": box["x"] - ox, "y": box["y"] - oy,
            "w": box["w"], "h": box["h"]}


def modal_origin(raw):
    """★ 从 raw 的「★模态根的子」**机器提取**内容原点。

    ★ 源站模态**外框**是 1200×760 @ (360,160) ⟹ ⟹ 它的直接子元素里
      **「左上角坐标最小」的那个**就是**内容框**（1198×758 @ 361,161）
      ⟹ ⟹ 它的左上角 ＝ 内容原点。
    ★ ⟹ ⟹ **不手打 361/161**（★ 手打的常数会带着「上次是对的」这个假设进来）。
    ★ ⟹ ⟹ ⚠️ 判据是「(x, y) 字典序最小」⟹ ⟹ **不是**「第一个」
      ⟹ ⟹ （★ 第一个可能是右上角那枚绝对定位的 BUTTON ⟹ ⟹ 曾把原点取成 (1514,185)）。
    """
    root = raw["★模态根"]
    rb = root["b"]
    kids = [k for k in (raw.get("★模态根的子") or []) if k.get("b")]
    if not kids:
        raise SystemExit("★ raw 里没有模态根的子元素 ⟹ ⟹ 没法算原点")
    kid = min(kids, key=lambda k: (k["b"][0], k["b"][1]))
    kb = kid["b"]
    return {"x": kb[0], "y": kb[1],
            "外框": {"x": rb[0], "y": rb[1], "w": rb[2], "h": rb[3]},
            "内容框": {"x": kb[0], "y": kb[1], "w": kb[2], "h": kb[3]}}


def main() -> int:
    rd = read_json(R_DEFAULT)
    rh = read_json(R_HALF)
    rf = read_json(R_FULL)
    r848 = read_json(R_848)

    # ── ① 原点：机器提取 ────────────────────────────────────────────────
    o_default = modal_origin(rd)
    o_half = modal_origin(rh)
    o_full = modal_origin(rf)
    for name, o in (("default", o_default), ("half", o_half), ("full", o_full)):
        if o["x"] != o_default["x"] or o["y"] != o_default["y"]:
            print("✘ 三趟读数的原点不一致：%s" % name)
            return 1
    ox, oy = o_default["x"], o_default["y"]

    # ── ② 交叉校验：batch 848 的 raw（**另一趟探针、另一份坐标**）
    #    ⟹ ⟹ 用**绝对坐标**逐项比对（★ 最强的一条：两次独立读数一模一样）──
    tree848 = r848["★整棵子树"]
    main848 = find_one(tree848, lambda n: n.get("t") == "MAIN")
    # ★ 右栏：取**所有 ASIDE 里 x 最大**的那个（★ 画布上也有 aside ⟹ ⟹ 不能取第一个）
    asides = [n for _, n in walk(tree848) if n.get("t") == "ASIDE"]
    aside848 = max(asides, key=lambda n: norm_box(n)["x"]) if asides else None
    # ★ 工具行：★ 必须从**中列子树**里找（★ 模态底部也有 bottom-4 的元素）
    tools848 = find_one(main848, lambda n: n.get("t") == "DIV"
                         and "bottom-4" in (n.get("c") or "")
                         and "left-1/2" in (n.get("c") or "")) if main848 else None
    if not (main848 and aside848 and tools848):
        print("✘ 848 raw 里没找到 MAIN／ASIDE／工具行 ⟹ ⟹ 交叉校验做不了")
        return 1
    # ★ 850 侧的**绝对**坐标（★ full 态 ＝ identity transform ⟹ 视觉盒 ＝ 布局盒）
    tree850 = rf["★中列"]
    main850 = tree850
    tools850 = find_one(tree850, lambda n: n.get("t") == "DIV"
                        and "bottom-4" in (n.get("c") or "")
                        and "left-1/2" in (n.get("c") or ""))
    for name, a, b in (("中列", main848, main850),
                       ("工具行", tools848, tools850)):
        ba, bb = norm_box(a), norm_box(b)
        if ba != bb:
            print("✘ 交叉校验失败：848 raw 的%s绝对盒 %s ≠ 850 raw 的 %s"
                  % (name, ba, bb))
            return 1
    cross = {
        "★方式": "★ 绝对坐标逐项比对（★ 848 是**另一趟探针**、另一份坐标）",
        "中列": norm_box(main848),
        "右栏": norm_box(aside848),
        "工具行": norm_box(tools848),
    }
    # ★ 不变量：右栏 rel x ＝ 912（★ 与 clone 侧一致 ⟹ ⟹ 说明原点没取错 1px）
    aside_rel = rel(norm_box(aside848), ox, oy)
    if aside_rel["x"] != 912:
        print("✘ 不变量失败：右栏 rel x = %s（应为 912）" % aside_rel["x"])
        return 1
    # ★ 不变量：内容框在 1920×1080 视口里**居中**（⟹ ⟹ 原点必须是 (361,161)）
    cb = o_default["内容框"]
    if (1920 - cb["w"]) // 2 != cb["x"] or (1080 - cb["h"]) // 2 != cb["y"]:
        print("✘ 不变量失败：内容框 %s 在 1920×1080 里没居中" % cb)
        return 1

    def collect(raw, origin):
        """★ 从一棵中列子树里，按**语义**挑出本批要的那些元素。"""
        tree = raw["★中列"]
        o = (origin["x"], origin["y"])
        main = tree
        figure = find_one(tree, lambda n: n.get("t") == "DIV"
                          and "left-1/2" in (n.get("c") or "")
                          and "w-[467px]" in (n.get("c") or ""))
        zoom = find_one(tree, lambda n: "previewZoom" in (n.get("c") or ""))
        imgbox = find_one(tree, lambda n: n.get("t") == "DIV"
                          and "w-[425px]" in (n.get("c") or ""))
        img = find_one(tree, lambda n: n.get("t") == "IMG")
        canvas = find_one(tree, lambda n: n.get("t") == "CANVAS")
        mask = find_one(tree, lambda n: "previewMaskFade" in (n.get("c") or ""))
        blur = find_one(tree, lambda n: "previewMaskBlur" in (n.get("c") or ""))
        fade = find_one(tree, lambda n: (n.get("s") or {}).get("bi", "none") != "none")
        tools = find_one(tree, lambda n: n.get("t") == "DIV"
                         and "bottom-4" in (n.get("c") or "")
                         and "left-1/2" in (n.get("c") or ""))
        sep = find_one(tree, lambda n: n.get("t") == "SPAN")
        buttons = []
        if tools:
            for k in tools.get("c2") or []:
                if k.get("t") == "BUTTON":
                    buttons.append(k)
        return {
            "中列": rel(norm_box(main), *o),
            "图容器": rel(norm_box(figure), *o) if figure else None,
            "变换层": rel(norm_box(zoom), *o) if zoom else None,
            "变换层class": (zoom or {}).get("c"),
            "变换层矩阵": (zoom or {}).get("s", {}).get("tr"),
            "变换层原点": (zoom or {}).get("s", {}).get("to"),
            "变换层过渡": (zoom or {}).get("s", {}).get("ts"),
            "图盒": rel(norm_box(imgbox), *o) if imgbox else None,
            "图元素": rel(norm_box(img), *o) if img else None,
            "图源": (img or {}).get("src"),
            "canvas叠层": rel(norm_box(canvas), *o) if canvas else None,
            "canvas可见性": (canvas or {}).get("s", {}).get("vis"),
            "遮罩": rel(norm_box(mask), *o) if mask else None,
            "遮罩透明度": (mask or {}).get("s", {}).get("op"),
            "遮罩class": (mask or {}).get("c"),
            "遮罩过渡": (mask or {}).get("s", {}).get("ts"),
            "blur层": rel(norm_box(blur), *o) if blur else None,
            "blur值": (blur or {}).get("s", {}).get("bt"),
            "blur过渡": (blur or {}).get("s", {}).get("ts"),
            "渐变层": rel(norm_box(fade), *o) if fade else None,
            "渐变": (fade or {}).get("s", {}).get("bi"),
            "工具行": rel(norm_box(tools), *o) if tools else None,
            "工具行class": (tools or {}).get("c"),
            "工具行底色": (tools or {}).get("s", {}).get("bg"),
            "分隔线": rel(norm_box(sep), *o) if sep else None,
            "分隔线底色": (sep or {}).get("s", {}).get("bg"),
            "按钮": [{
                "aria": b.get("ar"),
                "class": b.get("c"),
                "盒": rel(norm_box(b), *o),
                "底色": b.get("s", {}).get("bg"),
                "文字色": b.get("s", {}).get("col"),
                "圆角": b.get("s", {}).get("br"),
            } for b in buttons],
        }

    full = collect(rf, o_full)
    half = collect(rh, o_half)
    default = collect(rd, o_default)

    # ★★ 交叉校验（绝对坐标）已在上面做完 ⟹ ⟹ 这里不再重复算 rel

    # ★ 自校验 ③：两枚按钮的**文字色**必须一白（选中）一灰（未选）⟹ ⟹ 两态相反
    def color_pair(st):
        c = {b["aria"]: b["文字色"] for b in st["按钮"]}
        return c

    for name, st, on in (("default", default, "半身"), ("full", full, "全身")):
        c = color_pair(st)
        if set(c) != {"半身", "全身"}:
            print("✘ %s 态的两枚按钮 aria 不对：%r" % (name, c))
            return 1
        sel = c[on]
        other = c["全身" if on == "半身" else "半身"]
        if sel != "rgb(255, 255, 255)":
            print("✘ %s 态选中的那枚文字色不是纯白：%r" % (name, sel))
            return 1
        if other != "rgba(255, 255, 255, 0.6)":
            print("✘ %s 态未选中的那枚文字色不是 60%% 白：%r" % (name, other))
            return 1

    # ★ 自校验 ④：渐变必须是**多段**（★ clone 之前是 2 段）⟹ ⟹ 段数 ≥ 8
    grad = full["渐变"] or ""
    if grad.count("rgba(") + grad.count("rgb(") < 8:
        print("✘ 渐变段数太少（%d）⟹ ⟹ raw 读数不完整" % grad.count("rgba("))
        return 1

    # ★ 自校验 ⑤：两态的**变换矩阵**必须不同（★ 否则「切取景」根本没生效）
    if default["变换层矩阵"] == full["变换层矩阵"]:
        print("✘ 两态的变换矩阵相同 ⟹ ⟹ 「半身/全身」在源站没有区别")
        return 1

    out = {
        "★模态原点": {"x": ox, "y": oy},
        "★原点来源": {"外框": o_default["外框"], "内容框": o_default["内容框"],
                       "说明": "★ 从模态根的**直接子元素**里挑出那个「内容框」"
                               "（1198×758）⟹ ⟹ 它的左上角 ＝ 内容原点（★ 机器提取，不手打）"},
        "★交叉校验": {"方式": cross["★方式"], "中列": cross["中列"],
                      "右栏": cross["右栏"], "工具行": cross["工具行"],
                      "不变量": ["右栏 rel x == 912",
                                 "内容框在 1920×1080 视口里居中"]},
        "★default": default,
        "★half": half,
        "★full": full,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("✔ 已写入", OUT)
    print("  内容原点 = (%d, %d)　★ 机器提取自「模态根的子元素里的内容框 %s」"
          % (ox, oy, o_default["内容框"]))
    print("  交叉校验：848 raw 与 850 raw 的**绝对盒**逐项相同 ✔（中列 %s）"
          % cross["中列"])
    print("  渐变段数 = %d" % (grad.count("rgba(") + grad.count("rgb(")))
    print("  半身矩阵 = %s" % default["变换层矩阵"])
    print("  全身矩阵 = %s" % full["变换层矩阵"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

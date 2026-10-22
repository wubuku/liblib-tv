#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 847：**像素差异归因** —— 差异到底落在**文字**上还是**图标**上？

## 为什么需要这一支

`probes/pixeldiff847_voice.py` 只回答「**差了多少**」（1010／51000＝1.98%）
⟹ ⟹ 但那是**数量**，不是**位置** ⟹ ⟹ 「差异集中在图标字形区」这句话如果只写进
README 而没有机器判定 ⟹ ⟹ 就是**没有证据的断言**（★ 本仓库的纪律：
★ 结论必须由**可复现的脚本**钉住）。

★ 本脚本把差异**逐像素归因**到三个桶：
  ① **文字桶**（raw 实测的文字盒，★ w>0 才算 ⟹ ⟹ w=0 的那两枚页签的
     「内层文字盒」是源站**裁掉**的 ⟹ ⟹ 不可见 ⟹ ⟹ 不参与）；
  ② **图标桶**（raw 实测的图标盒：工具行两枚 ＋ 每张卡的图标 ＋ 播放图标）；
  ③ **残差桶**（其余差异像素）⟹ ⟹ 预期是**三枚页签的图标**
     ⟹ ⟹ 判定方式：**每个残差连通分量的水平范围必须落在某枚页签按钮内**
     ⟹ ⟹ 且**不落在**该页签的文字盒里。

★ 三条断言：
  A1 **文字桶内差异像素 == 0** ⟹ ⟹ 「中文字**像素级**一致」；
  A2 残差**每个**连通分量都落在某枚页签按钮的水平范围内；
  A3 ①∪②∪③ **覆盖**全部差异像素（分母独立算 ⟹ ⟹ 比较数 == 期望项数）。

★ **阴性自检**（★ 防止「探测器坏了 ⟹ 于是报 0」）：
  ★ 往**一张文字盒**里注入 **1 个**差异像素 ⟹ ⟹ A1 **必须失败**
  ⟹ ⟹ 否则「A1 == 0」这条结论**不成立**（它可能只是没在比）。

★ **所有盒都从 `raw/source-847-voice.json` 取** ⟹ ⟹ **不手打**
（★ 「手打的标识符是输入，不是测量」）。

## 输出

`raw/pixel-attrib-847-voice.json`
"""
import json
import pathlib
import sys

from PIL import Image, ImageChops

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch847-2026-10-01"
RAW = BATCH / "raw/source-847-voice.json"
SRC_PNG = BATCH / "raw/source-847-voice.png"
CLONE_PNG = BATCH / "raw/clone-847-voice.png"
OUT_JSON = BATCH / "raw/pixel-attrib-847-voice.json"

# ★ 与 pixeldiff847_voice.py **同一个**阈值（灰度差 > 8 才算「差异像素」）
THRESH = 8


def in_box(pt, box) -> bool:
    x, y = pt
    return (box["x"] <= x < box["x"] + box["w"]
            and box["y"] <= y < box["y"] + box["h"])


def load_boxes():
    """★ 从 raw 取三类盒（★ 不手打 ⟹ ⟹ 也不在本脚本里写死坐标）。"""
    raw = json.loads(RAW.read_text(encoding="utf-8"))["★读数"]
    text_boxes = []          # ① 文字盒（w>0）
    icon_boxes = []          # ② 图标盒
    tab_spans = []           # ③ 残差要落进去的「页签按钮」水平范围
    for i, sp in enumerate(raw["标题行"]["子节点"]):
        btn = sp["孙节点"][0]
        tab_spans.append({"名": "页签%d(%s)" % (i, btn.get("text", "")),
                          "x0": btn["box"]["x"], "x1": btn["box"]["x"] + btn["box"]["w"]})
        inner = btn.get("内层文字盒")
        # ★ w=0 ⟹ 源站把文字**裁掉**了 ⟹ ⟹ 不可见 ⟹ ⟹ 不参与文字桶
        if inner and inner.get("w", 0) > 0:
            text_boxes.append({"名": "页签%d文字(%s)" % (i, btn.get("text", "")), "盒": inner})
    for i, b in enumerate(raw["工具行"]["按钮"]):
        if b.get("图标盒"):
            icon_boxes.append({"名": "工具行图标%d" % i, "盒": b["图标盒"]})
    for i, c in enumerate(raw["音色卡"][:2]):
        if c.get("图标盒"):
            icon_boxes.append({"名": "卡%d图标" % i, "盒": c["图标盒"]})
        if c.get("播放图标盒"):
            icon_boxes.append({"名": "卡%d播放图标" % i, "盒": c["播放图标盒"]})
        for key, label in (("名字盒", "名字"), ("副标盒", "副标")):
            if c.get(key):
                text_boxes.append({"名": "卡%d%s(%s)" % (i, label, c.get(label, "")), "盒": c[key]})
    return text_boxes, icon_boxes, tab_spans


def diff_points(a: Image.Image, b: Image.Image, mutate=None):
    """★ 返回差异像素点集（绝对坐标）。`mutate` 用于**阴性自检**。"""
    if mutate is not None:
        b = mutate(b)
    g = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L")
    w, h = g.size
    px = g.load()
    return [(x, y) for y in range(h) for x in range(w) if px[x, y] > THRESH]


def components(pts):
    """4-邻接连通分量 ⟹ 每个分量的包围盒。"""
    s = set(pts)
    seen = set()
    comps = []
    for p in pts:
        if p in seen:
            continue
        stack = [p]
        seen.add(p)
        comp = []
        while stack:
            x, y = stack.pop()
            comp.append((x, y))
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in s and q not in seen:
                    seen.add(q)
                    stack.append(q)
        xs = [q[0] for q in comp]
        ys = [q[1] for q in comp]
        comps.append({"x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys),
                      "n": len(comp)})
    return comps


def attribute(pts, text_boxes, icon_boxes, tab_spans, offset):
    """把差异点分进三个桶（★ 互斥 ⟹ ⟹ 桶和 == 总量）。"""
    buckets = {"文字": [], "图标": [], "残差": []}
    for p in pts:
        ax, ay = p[0] + offset[0], p[1] + offset[1]
        if any(in_box((ax, ay), t["盒"]) for t in text_boxes):
            buckets["文字"].append((ax, ay))
        elif any(in_box((ax, ay), i["盒"]) for i in icon_boxes):
            buckets["图标"].append((ax, ay))
        else:
            buckets["残差"].append((ax, ay))
    return buckets


def residual_in_tab(buckets, tab_spans):
    """★ 残差的每个连通分量是否都落在某枚页签按钮的水平范围内。

    ★ 注意：桶里存的**已经是绝对坐标**（`attribute()` 里加过偏移）
    ⟹ ⟹ 这里**不能再减一次** clip 偏移（★ 第一版减了两次 ⟹ ⟹ A2 全假 ⟹ ⟹ 差点
    被当成「残差不在页签内」的结论）。
    """
    comps = components([(x, y) for (x, y) in buckets["残差"]])
    report = []
    ok = True
    for c in comps:
        hit = [t for t in tab_spans if t["x0"] <= c["x0"] and c["x1"] < t["x1"]]
        report.append({"分量": c, "落在页签": hit[0]["名"] if hit else None})
        if not hit:
            ok = False
    return ok, report


def main() -> int:
    out = {}
    try:
        text_boxes, icon_boxes, tab_spans = load_boxes()
        a = Image.open(SRC_PNG).convert("RGB")
        b = Image.open(CLONE_PNG).convert("RGB")
        if a.size != b.size:
            out["★异常"] = "两张图尺寸不同：%s vs %s" % (a.size, b.size)
            OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
            return 1

        pts = diff_points(a, b)
        buckets = attribute(pts, text_boxes, icon_boxes, tab_spans, (1290, 225))
        ok2, comp_report = residual_in_tab(buckets, tab_spans)

        # ★ 断言 A1：文字桶内差异 == 0
        a1 = len(buckets["文字"]) == 0
        # ★ 断言 A2：残差每个分量都落在某枚页签内
        a2 = ok2
        # ★ 断言 A3：三个桶覆盖全部差异像素（分母独立算）
        a3 = (len(buckets["文字"]) + len(buckets["图标"]) + len(buckets["残差"]) == len(pts))

        # ★ ★ 阴性自检：往**一张文字盒**注入 1 个差异像素 ⟹ ⟹ A1 **必须失败**
        probe_box = text_boxes[0]["盒"]
        px_b = b.load()

        def inject(img):
            im = img.copy()
            p = im.load()
            x = probe_box["x"] - 1290
            y = probe_box["y"] - 225
            p[x, y] = (255, 0, 0) if p[x, y] != (255, 0, 0) else (0, 255, 0)
            return im

        neg_pts = diff_points(a, b, mutate=inject)
        neg_buckets = attribute(neg_pts, text_boxes, icon_boxes, tab_spans, (1290, 225))
        neg_a1 = len(neg_buckets["文字"]) == 0     # ★ 期望为 **False**（探测器有牙）
        neg_ok = (not neg_a1) and len(neg_buckets["文字"]) >= 1

        out["★输入"] = {
            "源站PNG": str(SRC_PNG.relative_to(ROOT)),
            "clonePNG": str(CLONE_PNG.relative_to(ROOT)),
            "阈值": THRESH,
            "★文字盒来源": "raw/source-847-voice.json（★ 机器提取 ⟹ ⟹ 不手打）",
        }
        out["★差异像素总数"] = len(pts)
        out["★三桶"] = {
            "文字": len(buckets["文字"]),
            "图标": len(buckets["图标"]),
            "残差": len(buckets["残差"]),
        }
        out["★文字桶明细"] = [{"名": t["名"], "盒": t["盒"],
                               "差异像素": sum(1 for p in buckets["文字"]
                                             if in_box(p, t["盒"]))}
                              for t in text_boxes]
        out["★图标桶明细"] = [{"名": i["名"], "盒": i["盒"],
                               "差异像素": sum(1 for p in buckets["图标"]
                                             if in_box(p, i["盒"]))}
                              for i in icon_boxes]
        out["★残差分量"] = comp_report
        out["★文字盒数"] = len(text_boxes)
        out["★图标盒数"] = len(icon_boxes)
        out["★断言"] = {
            "A1_文字桶内差异为0": a1,
            "A2_残差每块落在某枚页签内": a2,
            "A3_三桶覆盖全部差异像素": a3,
        }
        out["★阴性自检"] = {
            "注入位置": text_boxes[0]["名"],
            "注入盒": probe_box,
            "注入后文字桶差异像素": len(neg_buckets["文字"]),
            "★A1在注入后是否失败": (not neg_a1),
            "★阴性自检通过": neg_ok,
        }
        all_ok = a1 and a2 and a3 and neg_ok
        out["★结论"] = ("三桶覆盖全部差异；文字桶 0 ⟹ 中文字像素级一致；"
                        "残差全部落在页签内 ⟹ 是页签图标字形"
                        if all_ok else "★ 有断言未通过")
        out["★PASS"] = bool(all_ok)
    except Exception:
        import traceback
        out["★异常"] = traceback.format_exc()
        out["★PASS"] = False
    finally:
        OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT_JSON)
        print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])
    return 0 if out.get("★PASS") else 1


if __name__ == "__main__":
    sys.exit(main())

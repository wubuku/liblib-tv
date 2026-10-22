#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846：源站 ↔ clone 的**外观（计算样式）**对拍。

## 与几何对拍分开的原因

★ batch 842 的教训：「**几何对齐 ≠ 外观对齐**」⟹ ⟹ 只比盒子的对拍脚本
  **看不到**颜色/字号/圆角/边框这类差异 ⟹ ⟹ 必须**另有一层**比计算样式。

★ 本脚本比的是**颜色与排版**这几类（⟹ ⟹ **故意不碰**几何 ⟹ ⟹ 与
  `parity846.py` 的字段**互不重叠** ⟹ ⟹ 两条判据不会因同一个缺陷一起翻）：
    · chip：底色 / 文字色 / 字号 / 行高 / 圆角 / 边框 / 内边距
    · 色块：边框色 / 圆角 / 选中态 box-shadow
    · 卡片：名字色 / 字号 / 行高；媒体区底色
    · H3：字号 / 行高 / 字重 / 颜色
    · 子页签：选中态文字色 / 选中态下边框色 / 未选中文字色

★ 「源站那一侧」的期望值**全部**来自 `raw/source-846-outfit.json`
  （机器提取 ⟹ ⟹ 不是手打常数）。

★ 输出：`/tmp/b846-style.json`
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch846-2026-10-01"
RAW = BATCH / "raw/source-846-outfit.json"
CLONE = pathlib.Path("/tmp/b846-clone-outfit.json")


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def main():
    src = load(RAW)["★读数"]
    cl = load(CLONE)["A_第四段"]
    out = {}

    def sty(e):
        """★ 取「计算样式」字典。

        ★ raw 里**两种**形状都有：
          · chip / H3 / 子页签 ⟹ 挂在对象的 `style` 键下
          · 卡片 ⟹ `名字样式` / `媒体样式` / `卡样式` **直接就是**样式字典
        ⟹ ⟹ 这里统一成「直接就是样式字典」的形状（⟹ ⟹ 调用方自己挑键名）。
        """
        return (e or {}).get("style") or (e or {})

    # ── chip ──────────────────────────────────────────────────────────
    chips = [c for c in src["chip"] if c["box"]["h"] == 26]
    out["★chip_源站_样式"] = [
        {"text": c["text"],
         "backgroundColor": sty(c)["backgroundColor"],
         "color": sty(c)["color"],
         "fontSize": sty(c)["fontSize"],
         "lineHeight": sty(c)["lineHeight"],
         "fontWeight": sty(c)["fontWeight"],
         "borderRadius": sty(c)["borderRadius"],
         "borderTopWidth": sty(c)["borderTopWidth"],
         "borderTopColor": sty(c)["borderTopColor"],
         "paddingLeft": sty(c)["paddingLeft"],
         "paddingTop": sty(c)["paddingTop"],
         "paddingRight": sty(c)["paddingRight"],
         "paddingBottom": sty(c)["paddingBottom"],
         "display": sty(c)["display"]}
        for c in chips]
    out["★chip_clone_样式"] = [
        {"text": c["text"],
         "backgroundColor": sty(c)["backgroundColor"],
         "color": sty(c)["color"],
         "fontSize": sty(c)["fontSize"],
         "lineHeight": sty(c)["lineHeight"],
         "fontWeight": sty(c)["fontWeight"],
         "borderRadius": sty(c)["borderRadius"],
         "borderTopWidth": sty(c)["borderTopWidth"],
         "borderTopColor": sty(c)["borderTopColor"],
         "paddingLeft": sty(c)["paddingLeft"],
         "paddingTop": sty(c)["paddingTop"],
         "paddingRight": sty(c)["paddingRight"],
         "paddingBottom": sty(c)["paddingBottom"],
         "display": sty(c)["display"]}
        for c in cl["chip"]]

    # ── 色块（★ 源站混合数组里没记 boxShadow ⟹ ⟹ 选中态另行读） ───────
    sw = [c for c in src["chip"] if c["box"]["h"] == 35]
    out["★色块_源站_样式"] = [
        {"backgroundColor": sty(c)["backgroundColor"],
         "borderRadius": sty(c)["borderRadius"],
         "borderTopWidth": sty(c)["borderTopWidth"],
         "borderTopColor": sty(c)["borderTopColor"],
         "选中": c.get("选中")}
        for c in sw]
    out["★色块_clone_样式"] = [
        {"backgroundColor": sty(c)["backgroundColor"],
         "borderRadius": sty(c)["borderRadius"],
         "borderTopWidth": sty(c)["borderTopWidth"],
         "borderTopColor": sty(c)["borderTopColor"],
         "选中": c.get("选中")}
        for c in cl["色块"]]

    # ── 卡片名字 + 媒体区 ─────────────────────────────────────────────
    # ★ 注意：源站 raw 的「名字样式」**没有** color 这一项
    #   （★ 846 源站探针的 `st()` 没取 color 在那一层 ⟹ ⟹ raw 里就是没有）
    #   ⟹ ⟹ **不比**这一项（⟹ ⟹ 只比 raw 里**两边都有**的键）
    #   ⟹ ⟹ ★ 不是「放过差异」，是「该项在源站**没有读数**⟹ ⟹ 无从比起」
    out["★卡片名_源站_样式"] = [
        {"aria": c["aria"], "fontSize": sty(c["名字样式"])["fontSize"],
         "lineHeight": sty(c["名字样式"])["lineHeight"],
         "fontWeight": sty(c["名字样式"])["fontWeight"]}
        for c in src["卡片"]]
    out["★卡片名_clone_样式"] = [
        {"aria": c.get("aria"), "fontSize": sty(c["名字样式"])["fontSize"],
         "lineHeight": sty(c["名字样式"])["lineHeight"],
         "fontWeight": sty(c["名字样式"])["fontWeight"]}
        for c in cl["卡片"]]
    out["★媒体区_源站_样式"] = [
        {"aria": c["aria"], "backgroundColor": sty(c["媒体样式"])["backgroundColor"],
         "borderRadius": sty(c["媒体样式"])["borderRadius"]}
        for c in src["卡片"]]
    out["★媒体区_clone_样式"] = [
        {"aria": c.get("aria"), "backgroundColor": sty(c["媒体样式"])["backgroundColor"],
         "borderRadius": sty(c["媒体样式"])["borderRadius"]}
        for c in cl["卡片"]]

    # ── H3 ────────────────────────────────────────────────────────────
    out["★H3_源站_样式"] = [
        {"text": h["text"], "fontSize": sty(h)["fontSize"],
         "lineHeight": sty(h)["lineHeight"], "fontWeight": sty(h)["fontWeight"],
         "color": sty(h)["color"]}
        for h in src["H3"]]
    out["★H3_clone_样式"] = [
        {"text": h["text"], "fontSize": sty(h)["fontSize"],
         "lineHeight": sty(h)["lineHeight"], "fontWeight": sty(h)["fontWeight"],
         "color": sty(h)["color"]}
        for h in cl["H3"]]

    # ── 子页签：★ 只比**颜色**（⟹ ⟹ 盒已由几何对拍覆盖） ──────────────
    # ★★ 源站的 borderBottom **不在** 846 主 raw 里（★ 主 raw 的 `st()` 没取那两项）
    #   ⟹ ⟹ 改从**补测 raw** `source-846-tabfont.json` 取（★ 同一次源站会话测的）
    #   ⟹ ⟹ 两侧**同口径**
    # ★★★ 关于**字号**：源站**按钮本身**是 16px/24.8px ⟹ ⟹ 那是**继承值**；
    #   真正画字的那层（最内层文字 span）是 **14px/22px** ⟹ ⟹ 必须取那一层。
    #   ⟹ ⟹ 若拿按钮的 16px 去比 clone 按钮的 14px ⟹ ⟹ 就是**口径差**，
    #   不是真差异（★ 像素对照实测「造型」二字**完全一致** ⟹ ⟹ 证明这是口径差）。
    # ★★★ 关于**未选中那两枚**：源站**每一枚**都渲染 label span，未选中时
    #   那个 span 的盒宽是 **0**（`grid-template-columns:0px` ＋ `overflow:hidden`
    #   ⟹ ⟹ 文字被**裁掉** ⟹ ⟹ **不可见**）；clone **不渲染**那个 label。
    #   ⟹ ⟹ ★ **DOM 结构不等，但可见结果相同** ⟹ ⟹ 故这里比的是
    #   「**可见文字**」（盒宽 > 0 的那层）⟹ ⟹ 而非「label 元素是否存在」。
    #   ⟹ ⟹ 这处**结构偏差**在 README 里如实标注（且像素对照已证明它**不可见**）。
    tabfont = load(BATCH / "raw/source-846-tabfont.json")["★子页签行"]["按钮"]
    out["★子页签_源站_样式"] = [
        {"aria": b["aria"], "color": b["style"]["color"],
         "borderBottomColor": b["style"]["borderBottomColor"],
         "borderBottomWidth": b["style"]["borderBottomWidth"],
         # ★ **可见**文字的盒宽（0 ⟹ ⟹ 那一枚没有可见文字）
         "可见文字宽": (b.get("内层文字盒") or {}).get("w", 0),
         # ★ 可见文字的排版（⟹ ⟹ 未选中时是 null ⟹ ⟹ 两侧都是 null）
         "文字fontSize": ((b.get("内层文字样式") or {}).get("fontSize")
                          if (b.get("内层文字盒") or {}).get("w", 0) > 0 else None),
         "文字lineHeight": ((b.get("内层文字样式") or {}).get("lineHeight")
                            if (b.get("内层文字盒") or {}).get("w", 0) > 0 else None),
         "文字color": ((b.get("内层文字样式") or {}).get("color")
                       if (b.get("内层文字盒") or {}).get("w", 0) > 0 else None)}
        for b in tabfont]
    out["★子页签_clone_样式"] = [
        {"aria": b.get("aria") or b.get("text"), "color": sty(b)["color"],
         "borderBottomColor": sty(b)["borderBottomColor"],
         "borderBottomWidth": sty(b)["borderBottomWidth"],
         "可见文字宽": (b.get("文字盒") or {}).get("w", 0),
         "文字fontSize": ((sty(b.get("文字样式")) or {}).get("fontSize")
                          if (b.get("文字盒") or {}).get("w", 0) > 0 else None),
         "文字lineHeight": ((sty(b.get("文字样式")) or {}).get("lineHeight")
                            if (b.get("文字盒") or {}).get("w", 0) > 0 else None),
         "文字color": ((sty(b.get("文字样式")) or {}).get("color")
                       if (b.get("文字盒") or {}).get("w", 0) > 0 else None)}
        for b in cl["子页签行"]["按钮"]]

    # ── 子页签行**容器**的底边框（★ 源站 nav 的那条 240px 白 8% 的线） ──
    #   ⟹ ⟹ 主 raw 里的 nav `style` 也没取 borderBottom ⟹ ⟹ 同样从补测 raw 取
    tf_style = load(BATCH / "raw/source-846-tabfont.json")["★子页签行"]["style"]
    out["★nav边框_源站"] = {
        "borderBottomWidth": tf_style.get("borderBottomWidth"),
        "borderBottomColor": tf_style.get("borderBottomColor"),
    }
    nav_cl = cl["子页签行"].get("边框") or {}
    out["★nav边框_clone"] = {
        "borderBottomWidth": nav_cl.get("borderBottomWidth"),
        "borderBottomColor": nav_cl.get("borderBottomColor"),
    }

    # ── 逐类比对 ──────────────────────────────────────────────────────
    diffs = {}
    for tag in ("chip", "色块", "卡片名", "媒体区", "H3", "子页签"):
        a = out["★%s_源站_样式" % tag]
        b = out["★%s_clone_样式" % tag]
        d = []
        for i in range(max(len(a), len(b))):
            x = a[i] if i < len(a) else None
            y = b[i] if i < len(b) else None
            if x != y:
                d.append({"序": i, "源站": x, "clone": y})
        diffs[tag] = d
    # ── nav 边框线（★ 单条 ⟹ ⟹ 单独比 ⟹ ⟹ 不混进上面的逐项比对） ────
    nav_src = out["★nav边框_源站"]
    nav_cl = out["★nav边框_clone"]
    diffs["nav边框"] = [] if nav_src == nav_cl else [
        {"序": 0, "源站": nav_src, "clone": nav_cl}]
    out["★差异"] = diffs
    out["★各类差异数"] = {k: len(v) for k, v in diffs.items()}
    out["★全绿"] = all(not v for v in diffs.values())
    return out


if __name__ == "__main__":
    out = main()
    pathlib.Path("/tmp/b846-style.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：/tmp/b846-style.json")
    print("各类差异数：", json.dumps(out["★各类差异数"], ensure_ascii=False))
    print("★全绿 =", out["★全绿"])
    for tag, ds in out["★差异"].items():
        for d in ds[:6]:
            print("\n── %s[%d]" % (tag, d["序"]))
            print("   源站 =", json.dumps(d["源站"], ensure_ascii=False))
            print("   clone=", json.dumps(d["clone"], ensure_ascii=False))

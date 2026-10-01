#!/usr/bin/env python3
"""batch 629 验收：又矮又窄的那个交叉网格，并**修正 628 豁免的划线位置**。

## 这一批要补的洞

- 627 扫的是 **86 个宽度 × 高度固定 900**
- 628 扫的是 **75 个高度 × 宽度固定 1440**

两批各自留白的正是「又窄又矮」这一角。它最可能藏东西，理由有两条：

1. **窄屏是另一套布局** —— 场景树与属性列变成抽屉、工具条改两行、左列从 320 收到
   220（`max-[899px]:w-[220px]`）。在 900 高的网格上量到的窄屏布局，每一列的
   **纵向**空间都是宽裕的。
2. **矮视口已被证明会触发真实碰撞** —— 628 在 ≤440 挖出 gizmo 被压住。窄屏把这
   几者叠在一起：更窄的列、更矮的视口、同一个 182px 贴底时间轴。

所以「窄屏在 900 高看起来干净」完全可能只是「高视口替它把纵向空间补上了」。

## 本批最重要的产出：**我上一批把线画错了**

探针一跑，176 格里有 **26 格出现无法解释的 `covered`**，受害者还是 gizmo 的
`X 正向` / `X 反向` / `Y 反向` / `重置视角` —— 但盖住它们的**不是底部 prompt 条**
（那条已被 628 的豁免接住），而是：

    16:9 · 9:16 · 1:1 · 画幅比例 · 开启九宫格辅助线 · 动画时间轴   ← 视口自己的顶部工具条
    角色01 · 陈默可拖动三轴控件16:9                                  ← gizmo 自己的信息面板

780×400 那格最能说明问题：视口才 136 高，`Y 反向` 被**同一个 gizmo 的信息面板**盖住。

所以 628 的豁免按「盖住者是底部条」划线**划窄了** —— 它只匹配到了 628 恰好看见的
那一次碰撞。真相是关于**受害者与退化视口**的：3D 视口里的控件，在一个矮到装不下
自己那些顶部锚定控件的视口里，本来就不该指望它可点。改按 `victimInViewport` 划
线，盖住者只记录给读者看。

**教训**：一条豁免如果按「盖住者是谁」划线，它就只覆盖作者当时看见的那一次碰撞；
按「受害者处于什么退化条件」划线才划得对。627 的「先问阈值本来在数什么」是同一条
教训的另一个侧面。

## 三条本批特有的合同

1. **几何边界轴在交叉网格上仍然干净**（176 格「视口外且够不着」= 0，非空转）。
2. **挤压集合能被一个闭式公式逐格预测**。见下面「我自己那条断言是错的」。
3. **宽视口（≥899）不因此获得豁免**：窄屏 rail 隐藏那条路走不通 —— 360/520/780 下
   `data-director-icon-rail` 是 `display:none`、盒子 0×0，命中者根本不在 rail 内。
   （这一条是探针先猜「窄屏水平 rail 条」再被实测推翻的，见 README。）

## 我自己那条断言是错的，迁移成更强的

629 第一版的第 7 条断言写的是：**「这条碰撞只取决于视口高度、与窗口宽高无关，所以
628（1440 宽扫高度）与 629（11 个窄侧宽度扫高度）独立得出的视口高度上界必须一致」**。

它红了：360..898 宽的���界恒为视口高 **148**，唯独 899 宽是 **130**。

定点取证（`/tmp/dbg629c.py`，量了边界两侧共 8 格）给出的机制是：

- **gizmo 整簇在窗口坐标里恒定不动。** 盒恒 `t=108 b=188`，六个轴按钮与「重置视角」
  的底边在 898 / 899 / 1440 三个宽度、360 / 400 / 480 三个高度上**逐像素相同**
  （`Y 反向 b=183`、`重置视角 b=222.5`）。它既不随视口高度动，也不随宽度动。
- **盖住者全都锚在视口底。** `[data-director-bottom-bar]` 是 `absolute bottom-0
  z-[200]`，高恒 48，里面装着三个兄弟：视口工具条（就是那个「角色01 · 陈默可拖动
  三轴控件…」信息面板）、prompt 条、以及工具条那一行。628 认的
  `[data-director-scene-prompt-bar]` 只是**三个孩子之一**，而 628 那些格子里恰好只
  出现了这一个 —— 这就是 628 那条线划窄的精确原因。
- **时间轴高度按断点分族**：≤898 是 176/124（展开/收起），≥899 是 182/88。

于是碰撞条件恒等于

    受害者在视口内的底边 + 视口底部带宽(48)  ≥  视口高

而**视口高 = 窗口高 − 88 − 时间轴高**，两族的时间轴高差 6px（展开态），所以同一条
物理边界在窄族落在视口高 136、在桌面族落在 130 —— **差得正好是那 6px**。

我原来那句断言错在**跨布局族比较原始视口高**：两族的「窗口高 → 视口高」换算本来就不
同，拿原始视口高去跨族对齐是在比苹果和橘子。合同不删，迁移成两条更严的：

- `every-squeeze-row-satisfies-the-closed-form`（必要条件，85 行逐行验）
- `the-squeeze-set-is-exactly-what-the-geometry-predicts`（充分条件，**逐格**比对
  实测集合与公式预测集合，176 格全等 —— 公式若错一格即红）
- `the-raw-viewport-bound-is-reconciled-by-the-timeline-height`（把 148 vs 130 这个
  差异**钉死**为两族时间轴高度之差，而不是当噪声放过）

「豁免的边界从扫描自身推导」这条原则在这里升级成：**豁免的边界要能被几何算出来**。

## 不声称

- **源站任何事**。gizmo、视口工具条、prompt 条的几何都是 1920×1150 的源站实测值，
  而碰撞只出现在从未采样过的矮/窄视口，源站会不会撞**未取证**。
- **这个角是「最危险」的**，只主张它是 627 与 628 都没量到的那一块。
- **闭式公式对源站成立**。它描述的是 clone 在这两个布局族里的读数；源站的时间轴高度、
  视口内 gizmo 簇的定位都未在矮/窄视口下取证过。
- **视口挤压该怎么做**。视口被压到 90px 高时 3D 场景本身已不可用，但该怎么处置是
  产品决定，不是能从几何推出来的。本批只把解释结构化并量出边界。
- **底部带宽 48 是常量**。每格都实测，只在公式里当该格的读数用。
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

_s = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(b617)

# The narrow-side widths from batch 623's breakpoint set, plus the 899 edge.
WIDTHS = [360, 390, 430, 480, 520, 620, 680, 780, 850, 898, 899]
HEIGHTS = [360, 400, 480, 560, 640, 720, 800, 900]
STATES = [("expanded", "false"), ("collapsed", "true")]
CROSSCHECK = [(360, 360), (390, 400), (520, 480), (780, 400), (899, 360), (899, 900)]

# Batch 623's breakpoint convention: `min-[899px]` switches the desk to the
# three-column desktop layout, so 898 and 899 are different layout FAMILIES and
# must never be compared in the same unit (see the docstring).
NARROW_MAX = 898

# The chrome the closed form needs.  Every number is measured per cell — the
# 48px bottom band is a reading, never a magic constant.
CHROME_JS = """() => {
  const rect = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {top: r.top, left: r.left, width: r.width,
            height: r.height, bottom: r.bottom, right: r.right};
  };
  return {
    viewport: rect('[data-director-viewport]'),
    bottomBar: rect('[data-director-bottom-bar]'),
    timeline: rect('[data-director-timeline]'),
  };
}"""


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(160)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def set_collapsed(page, want: str) -> None:
    got = page.locator("[data-director-timeline]").first.get_attribute(
        "data-director-timeline-collapsed")
    if got != want:
        page.locator("[data-director-timeline-collapse]").first.click(timeout=15_000)
        page.wait_for_timeout(500)
    now = page.locator("[data-director-timeline]").first.get_attribute(
        "data-director-timeline-collapsed")
    if now != want:
        raise RuntimeError(f"could not reach collapsed={want} (got {now})")


def measure(page) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    chrome = page.evaluate(CHROME_JS)
    vp = chrome["viewport"]
    # The closed form: the gizmo cluster is pinned in WINDOW coordinates, so a
    # victim is squeezed exactly when its own bottom edge, measured down from
    # the viewport's top edge, reaches the viewport's bottom-anchored band.
    # `band` is the measured height of that band, not a literal.
    band = chrome["bottomBar"]["height"] if chrome["bottomBar"] else None
    return {
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"], b["data"])
                        for b in r["offViewportUnreachable"]],
        "scrollable": len(r["offViewportScrollable"]),
        "covered": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "byTimeline": len(r["coveredByTimelineOverlay"]),
        # (label, victimInViewport, viewportH) — the coverer is recorded on the
        # raw item for the reader, but the gate is the victim's viewport.
        "viewportSqueeze": [(b["label"], b["victimInViewport"], b.get("viewportH"))
                            for b in r["coveredByViewportSqueeze"]],
        "squeezeRows": [(b["label"], b["box"], b["hitLabel"], b.get("viewportH"))
                        for b in r["coveredByViewportSqueeze"]],
        "squeezeCoverers": [(b["label"], b.get("hitLabel"),
                             bool(b.get("hitInBottomBand")))
                            for b in r["coveredByViewportSqueeze"]],
        # Every control the audit considered blocked, with the fields the
        # prediction needs.  The prediction is built from these candidates
        # rather than from the observed set, which is what keeps the equality
        # check from being circular.
        "blocked": [(b["label"], b["box"], b["panel"], b["timelineOverlay"],
                     b["clipped"], b["victimInViewport"])
                    for b in r["blocked"]],
        "chrome": chrome,
        "band": band,
        "viewportH": round(vp["height"], 3) if vp else None,
        "viewportTop": round(vp["top"], 3) if vp else None,
        "timelineH": round(chrome["timeline"]["height"], 3)
        if chrome["timeline"] else None,
    }


def predict(r: dict[str, Any]) -> set[str]:
    """Which controls the geometry alone says must be squeezed in this cell.

    Three conditions, and dropping any one of them is a bug this batch made:
    the control must be INSIDE the viewport in the DOM (`victimInViewport`) —
    a scene-tree row can share the viewport's y band and still be in another
    column; it must not be clipped by its own scroller — the viewport toolbar
    is 711px wide inside a 360px viewport, so most of its buttons overflow
    sideways and are clipped, not covered; and it must be unexplained by the
    other buckets.  Then the closed form decides the rest.
    """
    vp_top, vh, band = r["viewportTop"], r["viewportH"], r["band"]
    if vp_top is None or vh is None or band is None:
        return set()
    out = set()
    for label, box, panel, timeline_overlay, clipped, in_viewport in r["blocked"]:
        if panel or timeline_overlay or clipped or not in_viewport:
            continue
        if (box[1] + box[3] - vp_top) + band >= vh:
            out.add(label)
    return out


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    cross: dict[str, Any] = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        for state, want in STATES:
            page = br.new_page(viewport={"width": 899, "height": 900},
                               device_scale_factor=1)
            b617.open_desk(page)
            for w in WIDTHS:
                page.set_viewport_size({"width": w, "height": 900})
                page.wait_for_timeout(180)
                for h in HEIGHTS:
                    page.set_viewport_size({"width": w, "height": h})
                    page.wait_for_timeout(180)
                    set_collapsed(page, want)
                    prep(page)
                    cells[f"{state}@{w}x{h}"] = measure(page)
            page.close()

        for w, h in CROSSCHECK:
            fresh = br.new_page(viewport={"width": w, "height": h},
                                device_scale_factor=1)
            b617.open_desk(fresh)
            prep(fresh)
            cross[f"expanded@{w}x{h}"] = measure(fresh)
            fresh.close()
        br.close()

    out = {
        "batch": 629,
        "title": "the short-and-narrow corner neither 627 nor 628 covered, and a "
                 "correction: batch 628's viewport-squeeze exemption was keyed on "
                 "the coverer instead of the victim's degeneracy",
        "date": "2026-10-01",
        "widths": WIDTHS,
        "heights": HEIGHTS,
        "states": [s for s, _ in STATES],
        "cells": cells,
        "freshLoadCrosscheck": cross,
    }

    v.check(f"the-grid-covers-{len(WIDTHS)}w-x-{len(HEIGHTS)}h-x-{len(STATES)}state",
            len(cells) == len(WIDTHS) * len(HEIGHTS) * len(STATES),
            detail=len(cells))

    bad = {k: r["unreachable"] for k, r in cells.items() if r["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail={k: r[:3] for k, r in list(bad.items())[:6]})

    vac = [k for k, r in cells.items() if r["offViewport"] == 0]
    v.check("every-cell-actually-exercised-the-off-viewport-branch", not vac,
            detail=vac[:8])

    uncov = {k: r["covered"] for k, r in cells.items() if r["covered"]}
    v.check("no-cell-has-an-unexplained-covered-control", not uncov,
            detail={k: r[:3] for k, r in list(uncov.items())[:6]})

    loose = {k: [e for e in r["viewportSqueeze"] if not e[1]]
             for k, r in cells.items()
             if [e for e in r["viewportSqueeze"] if not e[1]]}
    v.check("every-viewport-exemption-is-inside-the-viewport", not loose,
            detail={k: r[:3] for k, r in list(loose.items())[:6]})

    squeezed = [k for k, r in cells.items() if r["viewportSqueeze"]]
    v.check("the-viewport-squeeze-is-actually-exercised", bool(squeezed),
            detail={"cells": squeezed[:10], "count": len(squeezed)})

    # --- the closed form, necessary condition ----------------------------
    # Every squeezed row must satisfy  (victimBottom - viewportTop) + band
    # >= viewportHeight.  If the exemption ever fires where geometry says it
    # should not, this is what catches it.
    viol = []
    for k, r in cells.items():
        for label, box, _hit, _vh in r["squeezeRows"]:
            vp_top, vh, band = r["viewportTop"], r["viewportH"], r["band"]
            if None in (vp_top, vh, band):
                viol.append((k, label, "chrome-missing"))
                continue
            if (box[1] + box[3] - vp_top) + band < vh:
                viol.append((k, label, box, round(vh, 1), band))
    v.check("every-squeeze-row-satisfies-the-closed-form", not viol,
            detail=viol[:6])

    # --- the coverer is always the viewport's bottom BAND ----------------
    # Batch 628 keyed on `[data-director-scene-prompt-bar]`, which is one of
    # the band's three children.  Pin the band instead, so the lesson cannot
    # regress into naming a sibling.
    not_band = [row for r in cells.values() for row in r["squeezeCoverers"]
                if not row[2]]
    v.check("every-squeeze-coverer-is-in-the-viewports-bottom-band",
            not not_band, detail=not_band[:6])

    # --- the closed form, sufficient condition ----------------------------
    # Per cell, the observed set of squeezed controls must EQUAL the set the
    # geometry predicts — built from the blocked candidates, not from the
    # observed set, so this is not circular.  176 cells, all three directions:
    # a missing victim, an extra victim, and a wrong viewport height all fail.
    diff = {}
    for k, r in cells.items():
        got = {row[0] for row in r["squeezeRows"]}
        want = predict(r)
        if got != want:
            diff[k] = {"observed": sorted(got), "predicted": sorted(want)}
    v.check("the-squeeze-set-is-exactly-what-the-geometry-predicts", not diff,
            detail=dict(list(diff.items())[:4]))

    # --- reconcile the discrepancy that killed the first version ----------
    # The raw viewport-height bound is 148 across 360..898 and 130 at 899.
    # That is not noise: the two layout families run different timeline
    # heights, so viewportH = windowH - topbar - timelineH differs by exactly
    # that much.  Pin the difference instead of deleting the observation.
    #
    # Unified statement, covering all four (state, family) pairs — including
    # collapsed@desktop, which squeezes in NO grid cell.  That one is not a
    # gap in the data: with an 88px timeline the viewport is already 184 tall
    # at the shortest window in the grid, and the closed form's highest
    # threshold is 182.5, so "no cell" is the predicted answer.  A family with
    # no squeeze is therefore only acceptable if the formula says so.
    cells_by: dict[tuple[str, str], list[tuple[float, float, set[str], set[str]]]] = {}
    tl_h: dict[tuple[str, str], float] = {}
    for k, r in cells.items():
        state, wh = k.split("@")
        w = int(wh.split("x")[0])
        side = "narrow" if w <= NARROW_MAX else "desktop"
        cells_by.setdefault((state, side), []).append(
            (r["viewportH"], r["timelineH"], predict(r),
             {row[0] for row in r["squeezeRows"]}))
        tl_h.setdefault((state, side), r["timelineH"])

    recon: dict[str, dict[str, Any]] = {}
    for (state, side), rows in sorted(cells_by.items()):
        observed = [vh for vh, _tl, _pred, actual in rows if actual]
        predicted = [vh for vh, _tl, pred, _actual in rows if pred]
        recon[f"{state}/{side}"] = {
            "timelineHeight": tl_h[(state, side)],
            "predictedBound": max(predicted) if predicted else None,
            "observedBound": max(observed) if observed else None,
            "cells": len(rows),
        }
    mism = {k: d for k, d in recon.items()
            if d["predictedBound"] != d["observedBound"]}
    v.check("the-observed-bound-equals-the-predicted-bound-per-family",
            not mism, detail={"perCellFamily": recon, "mismatches": mism})

    gaps = {}
    for state in sorted({k.split("/")[0] for k in recon}):
        n = recon.get(f"{state}/narrow")
        d = recon.get(f"{state}/desktop")
        if not n or not d or n["observedBound"] is None \
                or d["observedBound"] is None:
            continue
        d_bound = n["observedBound"] - d["observedBound"]
        d_tl = d["timelineHeight"] - n["timelineHeight"]
        gaps[state] = {"bounds": {NARROW_MAX: n["observedBound"],
                                  NARROW_MAX + 1: d["observedBound"]},
                       "boundGap": d_bound, "timelineGap": round(d_tl, 1),
                       "explained": abs(d_bound - d_tl) < 0.5}
    bad_gap = {s: d for s, d in gaps.items() if not d["explained"]}
    v.check("the-raw-viewport-bound-is-reconciled-by-the-timeline-height",
            not bad_gap and bool(gaps), detail=gaps)

    v.check("the-raw-bound-really-did-differ-across-families",
            any(recon.get(f"{s}/narrow", {}).get("observedBound")
                != recon.get(f"{s}/desktop", {}).get("observedBound")
                for s in ("expanded", "collapsed")),
            detail={k: v["observedBound"] for k, v in recon.items()})

    # Fresh loads must agree with the resized page — including the squeeze set,
    # so the closed form is confirmed on a page that never got resized too.
    mism = [k for k, r in cross.items()
            if (r["total"], r["offViewport"], len(r["covered"]),
                tuple(sorted(x[0] for x in r["squeezeRows"])))
            != (cells[k]["total"], cells[k]["offViewport"],
                len(cells[k]["covered"]),
                tuple(sorted(x[0] for x in cells[k]["squeezeRows"])))]
    v.check(f"the-{len(CROSSCHECK)}-fresh-loads-agree-with-the-resized-page",
            not mism, detail=mism)

    cross_pred = {k: {"observed": sorted({x[0] for x in r["squeezeRows"]}),
                      "predicted": sorted(predict(r))}
                  for k, r in cross.items()}
    cross_bad = {k: d for k, d in cross_pred.items()
                 if d["observed"] != d["predicted"]}
    v.check("the-closed-form-also-holds-on-every-fresh-load", not cross_bad,
            detail=cross_bad)

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "offViewport": sum(r["offViewport"] for r in cells.values()),
        "viewportSqueezeCells": len(squeezed),
        "squeezeRows": sum(len(r["squeezeRows"]) for r in cells.values()),
        "perCellFamilyBound": recon,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch629-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

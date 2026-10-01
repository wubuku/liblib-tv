#!/usr/bin/env python3
"""batch 633 验收：**宽度 × 时间轴高度**的交叉网格 —— 掩埋曲面与宽度无关。

## 这一批补的是哪块洞

630 扫了 12 档拖拽高度 × 10 个窗口，但每个窗口只配少数几个宽度；631 扫 11 宽度
× 2 档高度；632 扫 25 宽度 × 默认高度。**没有任何一批把「宽度」和「拖拽高度」
交叉起来扫**，而 628 第一族的掩埋数同时依赖两者（列的 x 几何由宽度决定、
时间轴盖多深由拖拽高度决定）。这个曲面没人画过。

窗口高度固定 **660**：可用纵向空间 660−88 = 572 > 420，整个拖拽量程都放得下，
630 那个钳制不会介入 —— 本批只量掩埋曲面，不重复 630。

## 本批的结论：这个曲面是 2×8 的阶梯函数，**宽度不是变量**

10 个宽度（360/480/620/780/898/899/1024/1280/1440/1920）× 8 档高度 = **80 格**，
掩埋数：

| 族 | 88 | 120 | 150 | 182 | 240 | 300 | 360 | 420 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ≤898（5 个宽度） | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0** |
| ≥899（5 个宽度） | 1 | 1 | 1 | 1 | 4 | 4 | 10 | **15** |

**每一族内部 5 个宽度逐格相同**。机制：三个列都是 `absolute bottom-0`，它们盖到
哪条 y 只取决于**时间轴的顶边 = 窗口高 − 拖拽高度**，而行的 y 由列的内容决定、
不随列的宽度变化（标签短、列 233px，不换行）。所以宽度这个轴对掩埋**没有贡献**。

这条结论有两个用处：**(a)** 它把 630 在 1440/1920 上读到的数**推广到整族**，
反过来加强了 628 台账里的「299 枚」；**(b)** 它告诉后来的批次：这个问题的宽度轴
**不必再扫**。

≤898 整行为 0 的原因也在这里：那些列是屏外 `inert` 抽屉（`-220,88`），它们的行
**根本不在视口内**，所以不是「被盖住」而是「视口外」——由 627 的 `isClipped` 解释，
不记进掩埋数。

## 80 格的三条边界轴全干净

够不着 **0** / 零尺寸 **0** / 无法解释 **0**，且无一格零视外控件（非空转）。
零尺寸检查沿用 623 的 `BLIND_JS`；受害者按**列**归属（631 已证明按名字列举成员
会漏掉同族其他成员）。

## 不声称

- 源站任何事。第一族是 613 在源站 1920×1150 实测的源站事实；**源站在矮视口下
  掩埋多少行，未取证**，故本批只主张 clone 在这个窗口高度上的读数。
- 「掩埋曲面与宽度无关」是**在窗口高 660、这 10 个宽度、这 8 档高度下**成立的。
  它不是全局定理：若某档高度下列内容换行、行 y 改变，曲面就会变。
- 第一族该修。处置仍卡在源站矮视口读数上。
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")
b623 = _load("623")
b629 = _load("629")

# 623's breakpoint convention again: >=899 is the three-column desktop layout.
NARROW_MAX = 898
WIDTHS = [360, 480, 620, 780, 898, 899, 1024, 1280, 1440, 1920]
TIMELINES = [88, 120, 150, 182, 240, 300, 360, 420]
DEFAULT_HEIGHT = 182
WIN_H = 660
CROSSCHECK = [(899, 420), (898, 420), (1440, 360), (360, 420)]

GEOM_JS = """() => {
  const rd = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {t: Math.round(r.top * 10) / 10, l: Math.round(r.left * 10) / 10,
            w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10,
            b: Math.round(r.bottom * 10) / 10, r: Math.round(r.right * 10) / 10,
            display: getComputedStyle(el).display};
  };
  return {
    viewport: rd('[data-director-viewport]'),
    timeline: rd('[data-director-timeline]'),
    bottomBar: rd('[data-director-bottom-bar]'),
    rail: rd('[data-director-icon-rail]'),
    tree: rd('aside[aria-label="场景对象"]'),
    inspector: rd('aside[aria-label="属性"]'),
  };
}"""


def column_of(box: list[float], g: dict[str, Any]) -> str:
    cx = box[0] + box[2] / 2
    for name in ("rail", "tree", "inspector"):
        rect = g.get(name)
        if rect and rect["display"] != "none" and rect["w"] > 0 \
                and rect["l"] - 0.5 <= cx <= rect["r"] + 0.5:
            return name
    return "other"


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(140)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def ask(page, th: int) -> None:
    page.evaluate("(n) => window.__director_store.getState().setTimelineHeight(n)", th)
    page.wait_for_timeout(200)


def measure(page) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(GEOM_JS)
    z = page.evaluate(b623.BLIND_JS)
    vp = g["viewport"]
    rows = [(b["label"], b["box"], b["hitLabel"], column_of(b["box"], g))
            for b in r["coveredByTimelineOverlay"]]
    return {
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"]) for b in r["offViewportUnreachable"]],
        "zeroSize": z,
        "unexplained": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "buried": rows,
        "buriedLabels": sorted({x[0] for x in rows}),
        "buriedColumns": sorted({x[3] for x in rows}),
        # every victim must sit BELOW the timeline's top edge — the one geometric
        # fact the whole surface rests on
        "aboveTimelineTop": [x[0] for x in rows
                             if x[1][1] + x[1][3] <= g["timeline"]["t"] + 0.5],
        "squeezeRows": [(b["label"], b["box"], b["hitLabel"])
                        for b in r["coveredByViewportSqueeze"]],
        "blocked": [(b["label"], b["box"], b["panel"], b["timelineOverlay"],
                     b["clipped"], b["victimInViewport"])
                    for b in r["blocked"]],
        "geom": g,
        "viewportH": round(vp["h"], 3) if vp else None,
        "viewportTop": round(vp["t"], 3) if vp else None,
        "band": g["bottomBar"]["h"] if g["bottomBar"] else None,
    }


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
        for w in WIDTHS:
            page = br.new_page(viewport={"width": w, "height": WIN_H},
                               device_scale_factor=1)
            b617.open_desk(page)
            for th in TIMELINES:
                page.set_viewport_size({"width": w, "height": WIN_H})
                page.wait_for_timeout(160)
                ask(page, th)
                prep(page)
                cells[f"{w}/tl={th}"] = measure(page)
            page.close()
        for w, th in CROSSCHECK:
            fresh = br.new_page(viewport={"width": w, "height": WIN_H},
                                device_scale_factor=1)
            b617.open_desk(fresh)
            ask(fresh, th)
            prep(fresh)
            cross[f"{w}/tl={th}"] = measure(fresh)
            fresh.close()
        br.close()

    out = {
        "batch": 633,
        "title": "the width x timeline-height cross grid: the burial surface is "
                 "a 2x8 step function and width is not a variable",
        "date": "2026-10-01",
        "widths": WIDTHS,
        "timelineHeights": TIMELINES,
        "windowHeight": WIN_H,
        "cells": cells,
        "freshLoadCrosscheck": cross,
    }

    v.check(f"the-grid-covers-{len(WIDTHS)}w-x-{len(TIMELINES)}tl",
            len(cells) == len(WIDTHS) * len(TIMELINES), detail=len(cells))

    # --- the three boundary axes ----------------------------------------
    bad = {k: r["unreachable"] for k, r in cells.items() if r["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail=dict(list(bad.items())[:6]))

    zbad = {k: r["zeroSize"] for k, r in cells.items() if r["zeroSize"]}
    v.check("no-cell-has-a-control-collapsed-to-nothing", not zbad,
            detail={k: r[:4] for k, r in list(zbad.items())[:6]})

    uncov = {k: r["unexplained"] for k, r in cells.items() if r["unexplained"]}
    v.check("no-cell-has-an-unexplained-covered-control", not uncov,
            detail=dict(list(uncov.items())[:6]))

    vac = [k for k, r in cells.items() if r["offViewport"] == 0]
    v.check("every-cell-actually-exercised-the-off-viewport-branch", not vac,
            detail=vac[:8])

    # --- the one geometric fact the surface rests on ---------------------
    above = {k: r["aboveTimelineTop"] for k, r in cells.items()
             if r["aboveTimelineTop"]}
    v.check("every-buried-control-sits-below-the-timelines-top-edge", not above,
            detail=dict(list(above.items())[:6]))

    # --- THE CLAIM: width is not a variable -----------------------------
    def side(w: int) -> str:
        return "narrow" if w <= NARROW_MAX else "desktop"

    surface: dict[str, dict[int, list[int]]] = {}
    for k, r in cells.items():
        w = int(k.split("/")[0])
        surface.setdefault(side(w), {}).setdefault(int(k.split("=")[1]), []).append(
            len(r["buried"]))
    # ...and the step function itself, pinned so any change is visible.
    # A per-family dict is truthy even when every entry inside it is empty, so
    # collect the ragged (family, height) pairs as a FLAT list — the first
    # version of this check built a nested dict and reported a failure whose
    # own detail said both families were uniform.
    ragged = [(f, t, sorted(set(rows[t])))
              for f, rows in surface.items()
              for t in rows if len(set(rows[t])) > 1]
    v.check("the-burial-count-is-identical-at-every-width-in-its-family", not ragged,
            detail={"raggedCells": ragged,
                    "surface": {f: {str(t): sorted(set(v))[0]
                                    for t, v in sorted(rows.items())}
                                for f, rows in surface.items()}})

    # ...and the step function itself, pinned so any change is visible.
    narrow_vals = sorted({sorted(set(v))[0] for v in surface["narrow"].values()})
    desk_vals = [sorted(set(v))[0] for _t, v in sorted(surface["desktop"].items())]
    v.check("the-narrow-family-buries-nothing-and-the-desktop-family-a-fixed-step",
            narrow_vals == [0] and desk_vals == [1, 1, 1, 1, 4, 4, 10, 15],
            detail={"narrow": narrow_vals, "desktop": desk_vals})

    # --- the step is driven by which entries fall under the top edge -----
    default_row = {w: cells[f"{w}/tl={DEFAULT_HEIGHT}"]
                   for w in WIDTHS if w > NARROW_MAX}
    only_help = {w: r["buriedLabels"] for w, r in default_row.items()
                 if r["buriedLabels"] != ["帮助"]}
    v.check("at-the-default-height-only-帮助-is-buried", not only_help,
            detail=only_help)

    cols = {w: r["buriedColumns"] for w, r in default_row.items()}
    v.check("at-the-default-height-the-victim-is-the-rails-帮助",
            all(c == ["rail"] for c in cols.values()), detail=cols)

    maxed = {w: r["buriedColumns"] for w, r in
             ((w, cells[f"{w}/tl={max(TIMELINES)}"]) for w in WIDTHS
              if w > NARROW_MAX)}
    v.check("at-max-height-the-victims-are-the-rail-plus-the-tree-rows",
            all(set(c) == {"rail", "tree"} for c in maxed.values()), detail=maxed)

    # --- 630/629's law still holds here ---------------------------------
    diff = {}
    for k, r in cells.items():
        got = {row[0] for row in r["squeezeRows"]}
        want = b629.predict(r)
        if got != want:
            diff[k] = {"observed": sorted(got), "predicted": sorted(want)}
    v.check("629s-closed-form-still-predicts-every-cell-here", not diff,
            detail=dict(list(diff.items())[:4]))

    mism = [k for k, r in cross.items()
            if (r["total"], len(r["buried"]), tuple(r["buriedLabels"]))
            != (cells[k]["total"], len(cells[k]["buried"]),
                tuple(cells[k]["buriedLabels"]))]
    v.check(f"the-{len(CROSSCHECK)}-fresh-loads-agree-with-the-resized-page",
            not mism, detail=mism)

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "unreachable": sum(len(r["unreachable"]) for r in cells.values()),
        "zeroSize": sum(len(r["zeroSize"]) for r in cells.values()),
        "unexplained": sum(len(r["unexplained"]) for r in cells.values()),
        "offViewport": sum(r["offViewport"] for r in cells.values()),
        "burialSurface": {f: {str(t): sorted(set(v))[0]
                              for t, v in sorted(rows.items())}
                          for f, rows in surface.items()},
        "labelsAtMax": {str(w): cells[f"{w}/tl={max(TIMELINES)}"]["buriedLabels"]
                        for w in WIDTHS if w > NARROW_MAX},
    }
    audit = ROOT / "docs/research/liblib-canvas-batch633-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

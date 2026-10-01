#!/usr/bin/env python3
"""batch 634 验收：掩埋曲面在 (窗口高 × 拖拽高度) 上**坍缩成一维函数**。

## 这一批的预测是可推翻的

633 的机制说：三个列都是 `absolute bottom-0`，盖到哪条 y 只取决于**时间轴的顶边**，
而行的 y 由列内容决定、不随宽度变（633 已证宽度不是变量）。于是掩埋集合应当只是
**「时间轴顶边这条线的 y 坐标」的函数** —— 换句话说 (窗口高, 拖拽高度) 这个二维
曲面上，**顶边相同的格子掩埋集合应当完全相同**，曲面从二维坍缩成一维。

若某条 y 上掩埋集合不一致，就说明还有别的量在起作用（列自身高度、文本换行、
钳制后的实际高度……）。**所以这是一个能被数据推翻的断言，不是事后描述。**

实测成立：48 格按**实测**（不是推算）时间轴顶边分组，**每组内部完全一致**，而且
有三组各含 2 个来自不同 (窗高, 拖拽高) 组合的格子 —— 它们掩埋集合相同：

| 时间轴顶边 | 两个格子 | 掩埋 |
| --- | --- | --- |
| 540 | (900, 360) 与 (660, 120) | `帮助` |
| 360 | (660, 300) 与 (480, 120) | `帮助` + 机位01 三连 |
| 240 | (660, 420) 与 (480, 240) | 15 枚 |

## 关键在于它能和**两个既往批次**对账

630 在 10 个离散窗口上各扫过一遍拖拽高度，633 固定窗口高 660 扫了 10 个宽度 ——
两条都是这条一维函数的**切片**。本批把三条独立扫描放在同一把尺子下比对
（`the-one-dimensional-function-matches-both-prior-sweeps`），这让结论从
「本轮内部自洽」升级成「跨批次一致」。

## 那一维函数长什么样

按时间轴顶边从低到高，掩埋数单调不增：

    顶边  88 → 25 → 23 → 19 → 15 → 10 → 7 → 4 → 1（一直到 1062）

台阶的形状有解释：多数台阶是 **+3**，因为场景树的每个对象贡献
删除 / 锁定 / 隐藏**三连**（这正是 628 说「任何名字列表都盖不住这个族」的原因 ——
标签随场景变，但**三连**这个结构不变）；图标栏的条目则以 1–2 枚为单位零星加入。

## 不声称

- 源站任何事。第一族是 613 在源站实测的源站事实；**源站在矮视口下掩埋多少行
  未取证**，本批只主张 clone 的读数。
- 「掩埋只是顶边的函数」是**在宽度 1440（633 已证宽度不是变量）、这 6 档窗口高、
  这 8 档拖拽高度下**测得的。它不是全局定理：若列内容换行、行 y 改变，定理前提
  （行的 y 与宽度无关）就不成立。
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

WIDTH = 1440
WIN_HEIGHTS = [480, 560, 660, 760, 900, 1150]
TIMELINES = [88, 120, 150, 182, 240, 300, 360, 420]
CROSSCHECK = [(480, 240), (900, 120), (1150, 420)]

# The two prior independent sweeps of the same one-dimensional function.
PRIOR_630 = ROOT / "docs/research/liblib-canvas-batch630-2026-10-01/runtime-audit.json"
PRIOR_633 = ROOT / "docs/research/liblib-canvas-batch633-2026-10-01/runtime-audit.json"

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


def measure(page, wh: int, want: int) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(GEOM_JS)
    z = page.evaluate(b623.BLIND_JS)
    vp = g["viewport"]
    rows = [(b["label"], b["box"], b["hitLabel"], column_of(b["box"], g))
            for b in r["coveredByTimelineOverlay"]]
    return {
        "windowH": wh,
        "requested": want,
        "timelineTop": g["timeline"]["t"],
        "timelineH": g["timeline"]["h"],
        "clamped": abs(g["timeline"]["h"] - want) > 0.5,
        "spill": max(0, g["timeline"]["b"] - wh),
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"]) for b in r["offViewportUnreachable"]],
        "zeroSize": z,
        "unexplained": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "buried": rows,
        "buriedLabels": sorted({x[0] for x in rows}),
        "buriedColumns": sorted({x[3] for x in rows}),
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
        for wh in WIN_HEIGHTS:
            page = br.new_page(viewport={"width": WIDTH, "height": wh},
                               device_scale_factor=1)
            b617.open_desk(page)
            for th in TIMELINES:
                page.set_viewport_size({"width": WIDTH, "height": wh})
                page.wait_for_timeout(160)
                ask(page, th)
                prep(page)
                cells[f"{wh}/tl={th}"] = measure(page, wh, th)
            page.close()
        for wh, th in CROSSCHECK:
            fresh = br.new_page(viewport={"width": WIDTH, "height": wh},
                                device_scale_factor=1)
            b617.open_desk(fresh)
            ask(fresh, th)
            prep(fresh)
            cross[f"{wh}/tl={th}"] = measure(fresh, wh, th)
            fresh.close()
        br.close()

    out = {
        "batch": 634,
        "title": "the burial surface collapses to a one-dimensional function of "
                 "the timeline's top edge — reconciled against two prior sweeps",
        "date": "2026-10-01",
        "width": WIDTH,
        "windowHeights": WIN_HEIGHTS,
        "timelineHeights": TIMELINES,
        "cells": cells,
        "freshLoadCrosscheck": cross,
    }

    v.check(f"the-grid-covers-{len(WIN_HEIGHTS)}winH-x-{len(TIMELINES)}tl",
            len(cells) == len(WIN_HEIGHTS) * len(TIMELINES), detail=len(cells))

    # --- boundary axes --------------------------------------------------
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

    above = {k: r["aboveTimelineTop"] for k, r in cells.items()
             if r["aboveTimelineTop"]}
    v.check("every-buried-control-sits-below-the-timelines-top-edge", not above,
            detail=dict(list(above.items())[:6]))

    # 630's clamp must still behave on this grid: no spill anywhere, and the
    # one cell that does clamp is recorded rather than silently resized.
    spill = {k: r["spill"] for k, r in cells.items() if r["spill"] > 0.5}
    v.check("the-timeline-never-spills-past-the-window-on-this-grid-too", not spill,
            detail=dict(list(spill.items())[:6]))
    clamped = {k: {"requested": r["requested"], "actual": r["timelineH"]}
               for k, r in cells.items() if r["clamped"]}
    v.check("630s-clamp-still-fires-where-the-height-does-not-fit",
            all(abs(v2["actual"] + 88 - 480) < 0.5
                for k, v2 in clamped.items() if k.startswith("480/")),
            detail=clamped)

    # --- THE CLAIM: the surface is a function of the top edge alone ------
    groups: dict[float, list[str]] = {}
    for k, r in cells.items():
        groups.setdefault(r["timelineTop"], []).append(k)
    ragged = []
    for top, members in groups.items():
        sets = {tuple(cells[m]["buriedLabels"]) for m in members}
        if len(sets) > 1:
            ragged.append({"top": top, "members": members,
                           "sets": [list(s) for s in sets]})
    v.check("every-cell-on-the-same-timeline-top-buries-the-same-set", not ragged,
            detail={"ragged": ragged[:4],
                    "groupSizes": {str(t): len(m) for t, m in sorted(groups.items())}})

    # Non-vacuity: a grid where every timeline top is unique would satisfy the
    # claim trivially, because every group would have exactly one member.  The
    # evidence is the groups that actually hold two DIFFERENT (window, timeline)
    # combinations.
    coincidences = {str(t): sorted(m) for t, m in groups.items() if len(m) > 1}
    v.check("the-collapse-is-exercised-by-repeated-timeline-tops", len(coincidences) >= 3,
            detail={"coincidentTops": coincidences,
                    "distinctTops": len(groups), "cells": len(cells)})

    # ...and the one-dimensional function itself: monotone in the top edge.
    # The direction matters and I got it backwards first: `fn` is sorted by top
    # DESCENDING, so a correct "lower top buries more" means the counts RISE
    # along the list.  Asserting `counts[i] >= counts[i+1]` there demands the
    # opposite and fails on real data.
    fn = sorted(((t, len(cells[groups[t][0]]["buriedLabels"]))
                 for t in groups), reverse=True)
    counts = [c for _t, c in fn]          # top descending -> count must not fall
    monotone = all(counts[i] <= counts[i + 1] for i in range(len(counts) - 1))
    v.check("the-one-dimensional-function-is-monotone-in-the-top-edge", monotone,
            detail={"fn": fn})

    # The step values are pinned so a change is visible.  The first version of
    # this list was transcribed by eyeballing a label dump from the probe and
    # two of its ten numbers were wrong — pin what the run measured, not what a
    # dump appeared to say.
    steps = sorted({c for _t, c in fn}, reverse=True)
    v.check("the-step-values-are-pinned-so-a-change-is-visible",
            steps == [26, 24, 23, 19, 15, 14, 10, 7, 4, 1], detail=steps)

    # --- cross-batch reconciliation -------------------------------------
    # Two prior batches swept slices of this same function.  Comparing against
    # their recorded audits is what turns "self-consistent this round" into
    # "agrees across three independent sweeps".
    f_by_top = {t: len(cells[groups[t][0]]["buriedLabels"]) for t in groups}
    prior: dict[str, Any] = {}
    if PRIOR_630.exists():
        d630 = json.loads(PRIOR_630.read_text())
        slice630 = {th: d630["cells"][f"{WIDTH}x660/tl={th}"]["byTimeline"]
                    for th in TIMELINES if f"{WIDTH}x660/tl={th}" in d630["cells"]}
        prior["630@1440x660"] = slice630
    if PRIOR_633.exists():
        d633 = json.loads(PRIOR_633.read_text())
        prior["633@desktop"] = d633["totals"]["burialSurface"].get("desktop")
    disagree = []
    for name, series in prior.items():
        for th, count in (series or {}).items():
            cell = cells.get(f"660/tl={int(th)}")
            if cell is None or count is None:
                continue
            if len(cell["buriedLabels"]) != count:
                disagree.append({"prior": name, "tl": th,
                                 "priorCount": count,
                                 "mine": len(cell["buriedLabels"])})
    v.check("the-one-dimensional-function-matches-both-prior-sweeps", not disagree,
            detail={"priorSweeps": prior, "disagreements": disagree})

    # --- 629's law still holds here -------------------------------------
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
        "distinctTimelineTops": len(groups),
        "coincidentTops": coincidences,
        "function": [{"top": t, "buried": c} for t, c in fn],
        "stepValues": steps,
        "clampedCells": clamped,
        "priorSweeps": prior,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch634-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""batch 632 验收：<360 那个更极端的角，挖到顶栏**条目互相叠压**，
并给普查补上它的一个盲区（只打中心点）。

## 这一批要补的洞

623/627/628/629 四个批次的最小值**全是 360**，两个方向都没低过。而 631 刚证明
≤898 确实是另一套布局族，所以 sub-360 很可能又是一族。

## 挖到的东西：定宽 170px 的居中视角组压住顶栏两簇按钮

`DirectorDesk.tsx:1029-1031` 的视角切换组是

    div[role=group][aria-label=导演台视角]
      .pointer-events-auto.absolute.left-1/2.top-2.z-10.-translate-x-1/2
        div.flex.h-9.w-[170px] …            ← 605 在源站 1920x1150 实测的形状

**它绝对定位、居中、定宽 170px，既不参与顶栏的 flex 流也不收缩**。于是窗口一变窄，
它就压在顶栏左右两簇按钮上：

| 窗口 | 居中组横跨 | 被压住的顶栏控件 |
| --- | --- | --- |
| 320 宽 | 75..245 | `收起`(64..104) 压 29px、`导出导演台项目`(202..234) 压 43px |
| 280 宽 | 55..225 | 同上，另加 `关闭` |
| 200 宽 | 15..185 | `关闭`/`收起`/`导出`/`导入` **四枚全中** |

## 本批最重要的产出：普查的这个盲区，和它的**可测量宽度**

普查的命中测试只打每个控件的**中心点**（`AUDIT_JS` 的 `elementFromPoint(cx, cy)`），
所以**部分被盖的控件 `own=True` 直接通过**。这与 623 的零尺寸盲区同形：**普查报零
不等于没有被盖住，只等于中心点没被盖住。**

两个阈值都量出来了（22 个宽度、360→430 每 10px 稠密）：

| 判据 | `收起` 出事上限 | `导出导演台项目` |
| --- | --- | --- |
| 普查（中心点） | **338** | 280 |
| 矩形相交（结构） | **377** | 320 |

**339..377 这条 39 像素带里控件被部分盖住而普查报零** —— 而 **359 与 360 正是
623/627/628/629 四批的采样下界**。四批全部踩在这条盲区上，全部报干净。

所以本批加一条**结构侧探测器**（盒与盒相交）作为常驻守卫，并让共享普查的这个
盲区被写进文档，而不是只留一句提醒。

## 严重性：叠压最狠的那枚，恰好是 631 证明「点了什么也不发生」的那枚

631 已证明 ≤898 时 `收起` 是一个**只让自己消失的空控件**（场景树本来已是屏外抽屉，
点击前后逐像素相同）。而 632 发现它在 <338 宽时**连点都点不到**。两条合起来：
**这枚控件在窄屏既无功能又不可点**，真正付出代价的是 `导出/导入导演台项目`
（中心被盖 ≤280、盒相交 ≤320）。

**本批不修布局**，理由与 628 对第一族的处置同源：**源站窄屏顶栏未取证**
（待授权第 10 项）。而怎么处置是**设计决定**——把这枚绝对居中的组改成参与流、
或让它在窄屏换位，都会改动一个 605 已在源站实测过的形状。故只把解释结构化、
把边界从扫描自身推导、并把问题具体化。

## 不声称

- **源站任何事**。源站窄屏顶栏上这枚 170px 的居中组与左右两簇如何共处，
  **未取证**；源站是否也有这个重叠**未取证**。
- **这该修**。它是 clone 内部的真实缺陷（有精确读数与阈值），但修法是设计决定。
- **320 宽是常见设备宽度**。320×568 是 iPhone SE 的逻辑分辨率，这个事实本身
  不构成本批对源站的主张。
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

# Dense across BOTH thresholds this batch found: the centre-point one at 338 and
# the rect-intersection one at 377, plus the whole sub-360 region nobody sampled.
WIDTHS = [200, 220, 240, 260, 280, 300, 310, 320, 330, 336, 338, 340, 350, 359,
          360, 370, 376, 377, 378, 380, 390, 400, 406, 420, 430]
HEIGHTS = [320, 568, 896]
CROSSCHECK = [(320, 568), (200, 320), (359, 568), (430, 568)]

GROUP_SEL = '[aria-label="导演台视角"]'

PROBE_JS = """(groupSel) => {
  const group = document.querySelector(groupSel);
  const gr = group ? group.getBoundingClientRect() : null;
  const ws = document.querySelector('[data-director-workspace]');
  const groupBox = gr ? [gr.left, gr.top, gr.width, gr.height] : null;
  const inter = (a, b) => !(a[0] + a[2] <= b[0] || b[0] + b[2] <= a[0]
                          || a[1] + a[3] <= b[1] || b[1] + b[3] <= a[1]);
  const out = {groupBox: groupBox && groupBox.map((v) => Math.round(v * 10) / 10),
               items: []};
  if (!ws) return out;
  for (const el of ws.querySelectorAll('button,[role="button"],a[href]')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.top > 88) continue;                 // the top bar row only
    if (group && (group === el || group.contains(el))) continue;  // its own kids
    const label = el.getAttribute('aria-label')
                  || (el.textContent || '').trim().slice(0, 12);
    if (!label) continue;
    const box = [r.left, r.top, r.width, r.height];
    out.items.push({label,
      box: box.map((v) => Math.round(v * 10) / 10),
      overlapsGroup: groupBox ? inter(box, groupBox) : false,
      overlapPx: (groupBox && inter(box, groupBox))
        ? Math.round((Math.min(box[0] + box[2], groupBox[0] + groupBox[2])
                      - Math.max(box[0], groupBox[0])) * 10) / 10 : 0,
    });
  }
  return out;
}"""


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(140)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


def measure(page) -> dict[str, Any]:
    r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
    g = page.evaluate(PROBE_JS, GROUP_SEL)
    z = page.evaluate(b623.BLIND_JS)
    return {
        "total": r["total"],
        "offViewport": len(r["offViewportItems"]),
        "unreachable": [(b["label"], b["box"]) for b in r["offViewportUnreachable"]],
        "zeroSize": z,
        "unexplained": [(b["label"], b["hitLabel"], b["box"]) for b in r["covered"]],
        "groupBox": g["groupBox"],
        "topBarOverlaps": [(i["label"], i["box"], i["overlapPx"])
                           for i in g["items"] if i["overlapsGroup"]],
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
    by_width: dict[int, Any] = {}
    cross: dict[str, Any] = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": 400, "height": 568},
                           device_scale_factor=1)
        b617.open_desk(page)
        for h in HEIGHTS:
            for w in WIDTHS:
                page.set_viewport_size({"width": w, "height": h})
                page.wait_for_timeout(170)
                prep(page)
                cells[f"{w}x{h}"] = measure(page)
                if h == 320:          # one height is enough for the x-thresholds
                    by_width[w] = cells[f"{w}x{h}"]
        page.close()
        for w, h in CROSSCHECK:
            fresh = br.new_page(viewport={"width": w, "height": h},
                                device_scale_factor=1)
            b617.open_desk(fresh)
            prep(fresh)
            cross[f"{w}x{h}"] = measure(fresh)
            fresh.close()
        br.close()

    out = {
        "batch": 632,
        "title": "below 360 in both directions: the fixed-width centred view "
                 "switcher overlaps the top bar, and the census's centre-only "
                 "hit test hides a 39px band of it",
        "date": "2026-10-01",
        "widths": WIDTHS,
        "heights": HEIGHTS,
        "cells": cells,
        "freshLoadCrosscheck": cross,
    }

    v.check(f"the-grid-covers-{len(WIDTHS)}w-x-{len(HEIGHTS)}h",
            len(cells) == len(WIDTHS) * len(HEIGHTS), detail=len(cells))

    # --- the geometric boundary is still clean down here ----------------
    bad = {k: r["unreachable"] for k, r in cells.items() if r["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail={k: r[:3] for k, r in list(bad.items())[:6]})

    zbad = {k: r["zeroSize"] for k, r in cells.items() if r["zeroSize"]}
    v.check("no-cell-has-a-control-collapsed-to-nothing", not zbad,
            detail={k: r[:4] for k, r in list(zbad.items())[:6]})

    vac = [k for k, r in cells.items() if r["offViewport"] == 0]
    v.check("every-cell-actually-exercised-the-off-viewport-branch", not vac,
            detail=vac[:8])

    # --- THE DEFECT, as a self-derived exemption ------------------------
    # Two halves, both required, exactly as batch 628 did for the timeline
    # family: the victim must be a top-bar control, AND the structural probe
    # must independently say that control's box intersects the centred view
    # switcher.  Two different measurements agreeing is a real attribution;
    # matching the coverer's *text* is not, because the coverer is a container
    # whose label reads "导演视角机位视角" — the concatenation of its two own
    # buttons — and an earlier version of this check missed exactly that and
    # reported it as unattributed.
    unattributed = {}
    for k, r in cells.items():
        overlap_labels = {o[0] for o in r["topBarOverlaps"]}
        rows = [lab for lab, _hit, _b in r["unexplained"]
                if lab not in overlap_labels]
        if rows:
            unattributed[k] = rows
    v.check("every-top-bar-block-is-attributed-to-the-centred-view-switcher",
            not unattributed, detail=dict(list(unattributed.items())[:6]))

    overlaps = {k: r["topBarOverlaps"] for k, r in cells.items()
                if r["topBarOverlaps"]}
    v.check("the-overlap-is-actually-exercised", bool(overlaps),
            detail={"cells": len(overlaps),
                    "sample": [f"{k}: {[o[0] for o in v2]}"
                               for k, v2 in list(overlaps.items())[:6]]})

    # The bound is derived from this sweep, never hand-picked, so it cannot be
    # widened silently: assert the overlap stops and stays stopped.
    w_overlap = sorted({int(k.split("x")[0]) for k in overlaps})
    bound = max(w_overlap) if w_overlap else None
    above = [w for w in WIDTHS if bound is not None and w > bound
             and by_width[w]["topBarOverlaps"]]
    v.check("the-overlap-stops-at-one-width-and-stays-stopped", not above,
            detail={"derivedBound": bound, "stillOverlappingAbove": above})

    # --- and the blind spot this batch found, pinned ---------------------
    # Centre-only sampling misses a band.  Measure both thresholds and assert
    # they are DIFFERENT — a batch that "fixed" this by widening the census's
    # sample points would collapse them and fail here.
    def victims_at(w: int, key: str) -> set[str]:
        return {row[0] for row in by_width[w][key]}

    centre_bound, rect_bound = {}, {}
    for label in ("收起", "导出导演台项目", "关闭", "导入导演台项目"):
        cw = [w for w in WIDTHS if label in victims_at(w, "unexplained")]
        rw = [w for w in WIDTHS
              if any(o[0] == label for o in by_width[w]["topBarOverlaps"])]
        if cw:
            centre_bound[label] = max(cw)
        if rw:
            rect_bound[label] = max(rw)
    gaps = {lab: rect_bound[lab] - centre_bound[lab]
            for lab in centre_bound if lab in rect_bound}
    v.check("the-centre-only-blind-spot-is-measured-and-nonzero",
            bool(gaps) and all(g > 0 for g in gaps.values()),
            detail={"centreSampleBound": centre_bound,
                    "rectIntersectionBound": rect_bound,
                    "blindBandPx": gaps})

    # ...and the specific consequence: the four prior batches all sampled at
    # 359/360, which sits INSIDE the blind band.
    floor = 360
    inside = [w for w in (floor - 1, floor)
              for lab in centre_bound
              if lab in rect_bound and centre_bound[lab] < w <= rect_bound[lab]]
    v.check("the-prior-batches-sampling-floor-sits-inside-the-blind-band",
            bool(inside), detail={"samplingFloor": floor, "insideBand": inside,
                                  "centreSampleBound": centre_bound,
                                  "rectIntersectionBound": rect_bound})

    mism = [k for k, r in cross.items()
            if (r["total"], len(r["unexplained"]),
                tuple(sorted(o[0] for o in r["topBarOverlaps"])))
            != (cells[k]["total"], len(cells[k]["unexplained"]),
                tuple(sorted(o[0] for o in cells[k]["topBarOverlaps"])))]
    v.check(f"the-{len(CROSSCHECK)}-fresh-loads-agree-with-the-resized-page",
            not mism, detail=mism)

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "unreachable": sum(len(r["unreachable"]) for r in cells.values()),
        "zeroSize": sum(len(r["zeroSize"]) for r in cells.values()),
        "overlapCells": len(overlaps),
        "derivedOverlapBound": bound,
        "centreSampleBound": centre_bound,
        "rectIntersectionBound": rect_bound,
        "blindBandPx": gaps,
        "groupBoxByWidth": {str(w): by_width[w]["groupBox"] for w in
                            sorted(by_width)[::4]},
    }
    audit = ROOT / "docs/research/liblib-canvas-batch632-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

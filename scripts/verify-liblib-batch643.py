#!/usr/bin/env python3
"""batch 643 验收：让「被裁」与「被盖」不再互斥，并证明**两种直觉修法都是错的**

## 问题

`AUDIT_JS` 里有两件互相独立的事实：

    clipped —— 它落在**自己**某个滚动/裁剪祖先的 client rect 之外
    covered —— 在它的中心点上，有**别的东西**被画在了上面

而判据把第一件当成了第二件的**否决权**：

    clipped = !own && !panel && isClipped(el)
    timelineOverlay = !own && !clipped && !panel && ...
    viewportSqueeze = !own && !clipped && !panel && ...
    unexplained     = failed.filter(!i.clipped && !i.panel && ...)

于是「既被自己的行裁掉、又被另一个面压住」的控件被归进 `clipped`，
**四个记账桶一个都不进**。batch 640 看不见它（它的搜索条件要求中心点是通的），
batch 642 只是因为新加的 `roundControls` 顺手带出了它才报出来 —— 两者都不在找这个状态。

## 本批做了什么、没做什么

**做了**：在共享判据里**只增不改**地加入联合谓词与三个此前从未被测量的事实
（最内层裁剪祖先是谁、它到底能不能滚、盖住它在不在这个祖先里），
并给出独立的新桶 `bothCoveredAndClipped`。

**没做**：**没有**改 `covered` / `timelineOverlay` / `viewportSqueeze` 的任何一个判定。
本批**不主张**这 14 枚是缺陷，也**不主张**它们无害 —— 它只主张
判据过去**连放它们的地方都没有**。

## 为什么不能顺手把 `!clipped` 删掉

这是本批最贵的一条，也是我原本要写错的那条。

第一版想法：既然两件事独立，那就去掉否决权，让 14 枚自然落进
`coveredByViewportSqueeze`。实测下来**这个修法错在它看起来很干净**：

  * 14 枚里有 **12** 枚 `victimInViewport` 为真 —— 删掉 `!clipped` 后它们会被 squeeze 族
    吸收；另外 **2** 枚（时间轴自己的 `添加关键帧` / `删除关键帧`）不在视口里，会
    **反向**冒成新的 `covered` 缺陷。一个修法同时朝两个方向出错，就不是修法；
  * 而 629 的闭式 `(bottom - vp_top) + band >= vh` 对 **14/14 全部成立**。

也就是说这个改动**会被自己的闭式判为自洽**，任何「公式同不同意」的检查都会放行。
但闭式在这里根本没有分辨力：盖住它们的表面实测有 **5 个**（提示条 / WebGL 画布 /
属性列 / 时间轴缩放输入 / 时间轴最小化按钮），闭式对这 5 个家族的答案是同一个。

**闭式同意，不构成证据。** 这正是要有独立一桶的理由。

## 我的第一版联合桶虚胖了 26 倍

第一版写的是 `!own && !panel && isClipped(el)`，跑出来 **363 枚**。
错在 `!own` 对**出屏**控件同样为真 —— 出屏时中心探针被跳过、`hit` 是 `null`，
根本没有东西压着它。于是「只是滚出窗口」被当成了「被盖住」。

覆盖那一半必须显式要求 `hit !== null`。收紧后是 **14 枚**，与独立探针
（`/tmp/dbg643a.py`，先筛 `hitTag` 非空）逐格一致。

这是本批第二次「测试自身写错要当信号读」。第一次是「每个宽度都必须非空」那条
断言 —— 它在 898 与 1920 上变红，而**红是对的、断言是错的**：那两个宽度的联合桶
本来就该是空的，验收器里改为由几何推出的两条检查（溢出是必要条件；空宽度
的溢出尾部整段落在窗口之外）来陈述这件事。

## 零回归是机械证明的

1. 本批对 `scripts/verify-liblib-batch617.py` 的改动是**纯增量**；
2. `verify-liblib-batch639.py` / `verify-liblib-batch640.py` 重跑后，
   两份**已落盘**的 audit JSON 与 HEAD 逐字节相同（`git diff --quiet`）；
3. 更强的一条直接写进检查：当前 `covered` 集合与 **batch 642 已落盘**的
   `unexplained` 集合逐格相同 —— 判决本身跨批次没动。

## 零源站断言

本批只主张 clone 的读数与判据的性质，不主张源站任何事。
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

WIDTHS = [339, 480, 620, 898, 899, 1440, 1920]
WIN_H = 900

# Batch 642's measurement, restated so this batch can assert it still holds
# without re-deriving it.  The census is the shared instrument; these are the
# labels 642 named, kept as a cross-batch anchor.
GIZMO_LABELS = {"X 正向", "X 反向", "Y 正向", "Y 反向", "Z 正向", "Z 反向"}

# Batch 639 established these as family- and state-independent constants over 64
# cells.  This batch MEASURES them again at every width rather than importing
# them, so check 11 is a reconciliation and not a tautology.
VIEWTOP_FROM_639 = 88
BAND_FROM_639 = 48

# Batch 629's closed form, quoted verbatim.  The ONLY change is dropping its
# `clipped` term, which is precisely the veto batch 643 is about.
def squeeze_predicted(box, vp_top, band, vh):
    return (box[1] + box[3] - vp_top) + band >= vh


CHROME_JS = """() => {
  const rect = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {top: Math.round(r.top * 10) / 10,
            left: Math.round(r.left),
            height: Math.round(r.height * 10) / 10};
  };
  const surfaces = new Set();
  for (const el of document.querySelectorAll('*')) {
    for (const k of Object.keys(el.dataset || {})) {
      if (k.indexOf('director') === 0) surfaces.add(k);
    }
  }
  // The three horizontally-scrolling rows a joint case can come from, each
  // with its live overflow extent.  Measured, never assumed: the point of the
  // two checks built on this is to explain why 898 and 1920 are EMPTY, and
  // that explanation has to come from geometry rather than from a list.
  const rows = {};
  const sub = document.querySelector('[data-director-scene-prompt-submit]');
  const rowSpecs = [
    ['directorViewportToolbar', '[data-director-viewport-toolbar]'],
    ['bottomBarScroller', '[data-director-bottom-bar] > div'],
    ['directorTimelineControlsScroll',
     '[data-director-timeline-controls-scroll]'],
  ];
  if (sub) {
    let a = sub.parentElement;
    while (a && a !== document.body) {
      const s = getComputedStyle(a);
      if (s.overflowX === 'auto' || s.overflowX === 'scroll') {
        rowSpecs.push(['promptBarRow', null]);
        if (!rows.promptBarRow) {
          const r = a.getBoundingClientRect();
          rows.promptBarRow = {
            clientWidth: a.clientWidth, scrollWidth: a.scrollWidth,
            left: Math.round(r.left), width: Math.round(r.width),
            overflowsX: a.scrollWidth > a.clientWidth + 0.5,
            tailRight: Math.round(r.left + a.scrollWidth),
          };
        }
        break;
      }
      a = a.parentElement;
    }
  }
  for (const [name, sel] of rowSpecs) {
    if (rows[name] || !sel) continue;
    const el = document.querySelector(sel);
    if (!el) { rows[name] = null; continue; }
    const r = el.getBoundingClientRect();
    rows[name] = {
      clientWidth: el.clientWidth, scrollWidth: el.scrollWidth,
      left: Math.round(r.left), width: Math.round(r.width),
      overflowsX: el.scrollWidth > el.clientWidth + 0.5,
      tailRight: Math.round(r.left + el.scrollWidth),
    };
  }
  const ins = document.querySelector('aside[aria-label="属性"]');
  return {viewport: rect('[data-director-viewport]'),
          bottomBar: rect('[data-director-bottom-bar]'),
          inspectorLeft: ins ? Math.round(ins.getBoundingClientRect().left) : null,
          windowWidth: innerWidth,
          rows: rows,
          surfaces: Array.from(surfaces).sort()};
}"""

# For every joint control: what is ACTUALLY painted at its centre, and is the
# control itself among them.  `elementFromPoint` alone cannot tell "something is
# painted on top of me" apart from "I am not painted here at all" — which is
# exactly the distinction this batch is about, so it has to be measured.
HITSTACK_JS = """(wanted) => {
  const label = (el) => {
    const al = el.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
    if (t) return t.length > 28 ? t.slice(0, 28) : t;
    return el.getAttribute('title') || el.getAttribute('placeholder')
        || '<' + el.tagName.toLowerCase() + '>';
  };
  const nameOf = (el) => Object.keys(el.dataset || {}).slice(0, 2).join(',')
    || el.getAttribute('aria-label') || el.tagName.toLowerCase();
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const scope = document.querySelector('[data-director-workspace]')
    || document.querySelector('[data-canvas-root]') || document.body;
  const byBox = {};
  for (const el of document.querySelectorAll(SEL)) {
    if (!scope.contains(el)) continue;
    const r = el.getBoundingClientRect();
    const key = label(el) + '|' + [r.x, r.y, r.width, r.height]
      .map((n) => Math.round(n * 10) / 10).join(',');
    byBox[key] = el;
  }
  const out = [];
  for (const w of wanted) {
    const el = byBox[w.key];
    if (!el) { out.push({key: w.key, missing: true}); continue; }
    const r = el.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const stack = document.elementsFromPoint(cx, cy) || [];
    const names = stack.slice(0, 6).map(nameOf);
    out.push({key: w.key, cx: Math.round(cx), cy: Math.round(cy),
              stackSize: stack.length, stack: names,
              victimPresent: stack.indexOf(el) !== -1});
  }
  return out;
}"""


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": str(detail)[:4000]}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:220]}" if detail else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

    prior = json.loads((ROOT / "docs/research/"
                        "liblib-canvas-batch642-2026-10-01/"
                        "runtime-audit.json").read_text())

    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS:
            page = br.new_page(viewport={"width": w, "height": WIN_H},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.set_viewport_size({"width": w, "height": WIN_H})
            page.wait_for_timeout(260)
            page.mouse.move(5, 5)
            page.wait_for_timeout(130)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            chrome = page.evaluate(CHROME_JS)
            r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))

            joint = r.get("bothCoveredAndClipped") or []
            vp_top = chrome["viewport"]["top"]
            vh = chrome["viewport"]["height"]
            band = chrome["bottomBar"]["height"]
            rows = []
            for j in joint:
                rows.append({
                    "label": j["label"], "box": j["box"], "round": j["round"],
                    "hitLabel": j["hitLabel"], "hitTag": j["hitTag"],
                    "clipperKey": j["clipperKey"],
                    "clipperCanScroll": j["clipperCanScroll"],
                    "covererInClipper": j["covererInClipper"],
                    "covererSurface": j["covererSurface"],
                    "covererSurfaceBox": j["covererSurfaceBox"],
                    "victimSurface": j["victimSurface"],
                    "victimInViewport": j["victimInViewport"],
                    "victimInColumn": j["victimInColumn"],
                    "hitInTimeline": j["hitInTimeline"],
                    "timelineOverlay": j["timelineOverlay"],
                    "viewportSqueeze": j["viewportSqueeze"],
                    "viewportH": j["viewportH"],
                    "squeezeWouldPredict": squeeze_predicted(
                        j["box"], vp_top, band, vh),
                })

            legacy = [b for b in r["blocked"]
                      if b.get("clipped") and not b.get("panel")
                      and b.get("hitTag")]
            hs = {h["key"]: h for h in page.evaluate(
                HITSTACK_JS,
                [{"key": f"{j['label']}|" + ",".join(str(x) for x in j["box"])}
                 for j in joint])}
            cells[str(w)] = {
                "total": r["total"], "blocked": len(r["blocked"]),
                "viewportTop": vp_top, "viewportH": vh, "band": band,
                "jointCount": len(joint),
                "jointSurfaces": r.get("jointCovererSurfaces"),
                "joint": rows,
                # the legacy route, recomputed in Python from the UNTOUCHED
                # `clipped` field — an independent witness for the new flag
                "legacyClippedCount": len(legacy),
                "legacyLabels": sorted({b["label"] for b in legacy}),
                "covered": [[b["label"], b["hitLabel"], b["box"]]
                            for b in r["covered"]],
                "timelineOverlay": len(r["coveredByTimelineOverlay"]),
                "viewportSqueeze": len(r["coveredByViewportSqueeze"]),
                "unreachable": [[b["label"], b["box"]]
                                for b in r["offViewportUnreachable"]],
                "roundCount": len(r.get("roundControls") or []),
                "rows": chrome["rows"],
                "inspectorLeft": chrome["inspectorLeft"],
                "hitStack": hs,
                "surfacesInDom": chrome["surfaces"],
            }
            page.close()
        br.close()

    # ------------------------------------------------------------------ 1
    v.check(f"the-grid-runs-{len(WIDTHS)}-widths", len(cells) == len(WIDTHS),
            detail=len(cells))

    # ------------------------------------------------------------------ 2
    # My first version asserted "populated at every width" and it went red at
    # 898 and 1920.  The red was RIGHT and the assertion was wrong: at those
    # two widths no row actually overflows into anything.  So state the
    # geometry instead of demanding a number — in both directions.
    per_width = {w: c["jointCount"] for w, c in cells.items()}
    overflowing = {w: sorted(k for k, r in c["rows"].items()
                             if r and r["overflowsX"])
                   for w, c in cells.items()}
    v.check("every-width-with-a-joint-case-has-a-row-that-overflows",
            all(overflowing[w] for w, c in cells.items()
                if c["jointCount"] > 0),
            detail={"perWidth": per_width, "rowsOverflowing": overflowing,
                    "direction": "necessary condition — a joint case needs "
                                 "something to stick out of a scroll box, and "
                                 "at 898/1920 there is nothing to stick out"})

    # The converse, so the empty widths are empty for a READABLE reason rather
    # than by omission.  At 898 the only overflowing row is the prompt-bar row
    # (944 > 874) and its overflow tail ends at x 1237 — past the 898px window,
    # where nothing is painted.  At 1920 no row overflows at all.
    unjustified = {}
    for w, c in cells.items():
        if c["jointCount"] != 0:
            continue
        tail = {k: r["tailRight"] for k, r in c["rows"].items()
                if r and r["overflowsX"]}
        inside = {k: t for k, t in tail.items() if t <= int(w)}
        if inside:
            unjustified[w] = {"overflowTailStillInsideTheWindow": inside}
    v.check("the-empty-widths-are-empty-because-the-overflow-tail-leaves-the-window",
            not unjustified,
            detail={"emptyWidths": [w for w, c in cells.items()
                                    if c["jointCount"] == 0],
                    "theirOverflowingTails": {
                        w: {k: r["tailRight"] for k, r in c["rows"].items()
                            if r and r["overflowsX"]}
                        for w, c in cells.items() if c["jointCount"] == 0},
                    "widthsWithNoGeometricReasonToBeEmpty": unjustified,
                    "reading": "898's only overflowing row ends its tail past "
                               "the 898px window (see theirOverflowingTails), "
                               "so nothing is painted over the overflow; 1920 "
                               "has no overflowing row at all. Both are empty "
                               "BECAUSE of geometry, not because the probe "
                               "missed them."})

    total_joint = sum(c["jointCount"] for c in cells.values())

    # ------------------------------------------------------------------ 3
    # The new flag must be a faithful re-derivation of what the untouched
    # `clipped` field already said, or the comparison in check 4 is circular.
    mism = {w: {"new": c["jointCount"], "legacy": c["legacyClippedCount"]}
            for w, c in cells.items()
            if c["jointCount"] != c["legacyClippedCount"]}
    v.check("the-joint-bucket-agrees-with-the-untouched-clipped-field",
            not mism, detail={"mismatchedWidths": mism,
                              "totalJoint": total_joint})

    # ------------------------------------------------------------------ 4
    # THE VETO, measured: not one joint control is accounted anywhere.
    veto_bad = {w: {"timelineOverlay": c["timelineOverlay"],
                    "viewportSqueeze": c["viewportSqueeze"],
                    "covered": len(c["covered"]),
                    "joint": c["jointCount"]}
               for w, c in cells.items()
               if any(j["label"] in {x[0] for x in c["covered"]}
                      or j["timelineOverlay"] or j["viewportSqueeze"]
                      for j in c["joint"])}
    v.check("no-joint-control-is-accounted-in-any-coverage-bucket", not veto_bad,
            detail={"widthsWhereAJointControlWasSomehowAccounted": veto_bad,
                    "jointTotal": total_joint,
                    "reading": "covered / timelineOverlay / viewportSqueeze all "
                               "carry `!clipped`, so the joint state had no home"})

    # ------------------------------------------------------------------ 5
    inside = [{"width": w, "label": j["label"], "clipperKey": j["clipperKey"],
               "covererSurface": j["covererSurface"]}
              for w, c in cells.items() for j in c["joint"]
              if j["covererInClipper"]]
    v.check("every-joint-controls-coverer-is-outside-its-own-scroller",
            not inside,
            detail={"casesWhereTheCovererSharesTheScroller": inside,
                    "measured": f"{total_joint - len(inside)}/{total_joint}",
                    "whyItIsTheLoadBearingFact":
                        "`clipped` is read as 'scroll the row and it comes back'. "
                        "That remedy needs the coverer to move WITH the scroller. "
                        "It never does, in any measured case."})

    # ------------------------------------------------------------------ 6
    # The counterweight.  Batch 643 does NOT claim these are defects, and this
    # is why: the `clipped` remedy is real.  Stating it explicitly is what stops
    # a later batch from manufacturing a defect out of the joint state.
    noscroll = [{"width": w, "label": j["label"], "clipperKey": j["clipperKey"]}
                for w, c in cells.items() for j in c["joint"]
                if not j["clipperCanScroll"]]
    v.check("every-joint-controls-scroller-can-actually-scroll", not noscroll,
            detail={"casesWithAnUnscrollableClipper": noscroll,
                    "measured": f"{total_joint - len(noscroll)}/{total_joint}",
                    "honesty": "this batch therefore claims NO defect here; it "
                               "claims only that the two facts were conflated"})

    # ------------------------------------------------------------------ 7
    typed = sorted({j["covererSurface"] for c in cells.values()
                    for j in c["joint"]})
    not_in_dom = [s for w, c in cells.items()
                   for s in {j["covererSurface"] for j in c["joint"]}
                   if s not in c["surfacesInDom"]]
    v.check("the-coverer-surfaces-are-read-from-the-dom-not-typed",
            not not_in_dom,
            detail={"surfacesSeen": typed,
                    "surfacesNotPresentInTheLiveDom": sorted(set(not_in_dom)),
                    "howVerified": "each surface name was checked against a "
                                   "fresh scan of every data-director* key on "
                                   "the live page at that width"})

    # ------------------------------------------------------------------ 8
    scrollers = sorted({j["clipperKey"] for c in cells.values()
                        for j in c["joint"]})
    v.check("the-joint-state-is-not-one-phenomenon",
            len(typed) >= 3 and len(scrollers) >= 3,
            detail={"distinctCovererSurfaces": typed,
                    "distinctScrollers": scrollers,
                    "reading": "one bucket would still hide four different "
                               "layout collisions; naming them is the point"})

    surface_hist: dict[str, int] = {}
    for c in cells.values():
        for j in c["joint"]:
            surface_hist[j["covererSurface"]] = surface_hist.get(
                j["covererSurface"], 0) + 1

    # ------------------------------------------------------------------ 9
    # THE DECISIVE CHECK.  Fold the joint state into `viewportSqueeze` by
    # dropping `!clipped`, and 629's own closed form AGREES with the result —
    # while the coverer that actually did the covering takes five different
    # values.  A formula that answers identically for five different causes has
    # no discriminating power here, so "the formula agrees" is not evidence.
    absorb = [j for c in cells.values() for j in c["joint"]
              if j["squeezeWouldPredict"]]
    v.check("629s-closed-form-agrees-with-the-whole-joint-set-yet-cannot-tell-the-families-apart",
            len(absorb) == total_joint and len(typed) >= 3,
            detail={"jointTotal": total_joint,
                    "closedFormWouldAbsorb": len(absorb),
                    "distinctActualCoverers": len(typed),
                    "covererHistogram": dict(sorted(surface_hist.items())),
                    "trap": "deleting `!clipped` looks self-consistent because "
                            "629's formula blesses it; the formula fires on "
                            "every one of them regardless of which surface "
                            "actually covered them, so it confirms nothing"})

    # ------------------------------------------------------------------ 10
    absorbed = [j for c in cells.values() for j in c["joint"]
                if j["victimInViewport"]]
    surfaced = [j for c in cells.values() for j in c["joint"]
                if not j["victimInViewport"]]
    v.check("deleting-the-veto-would-move-verdicts-in-two-different-directions",
            bool(absorbed) and bool(surfaced),
            detail={"wouldBeAbsorbedByTheSqueezeFamily": len(absorbed),
                    "wouldSurfaceAsCovered": len(surfaced),
                    "absorbedLabels": sorted({j["label"] for j in absorbed}),
                    "surfacedLabels": sorted({j["label"] for j in surfaced}),
                    "reading": "the timeline's own two rows fall outside the "
                               "viewport, so deleting the veto would report "
                               "them as NEW defects while silently excusing the "
                               "other eleven. A fix that errs in both "
                               "directions at once is not a fix."})

    # ------------------------------------------------------------------ 11
    # The ground-truth half of the question the structure half cannot answer:
    # `elementFromPoint` returns ONE element and gives no way to tell
    # "something is painted on top of me" apart from "I am not painted here at
    # all".  `elementsFromPoint` returns the whole stack, so it can.
    painted = []
    for w, c in cells.items():
        for j in c["joint"]:
            key = f"{j['label']}|" + ",".join(str(x) for x in j["box"])
            h = (c.get("hitStack") or {}).get(key) or {}
            painted.append({"width": w, "label": j["label"], "key": key,
                            "found": "key" in h,
                            "stack": h.get("stack"),
                            "victimPresent": h.get("victimPresent")})
    unmeasured = [p for p in painted if not p["found"]]
    still_painted = [p for p in painted if p["victimPresent"] is True]
    v.check("no-joint-control-is-painted-at-its-own-sample-point",
            bool(painted) and not unmeasured and not still_painted,
            detail={"measured": f"{len(painted) - len(still_painted)}"
                               f"/{len(painted)} absent from their own "
                               f"elementsFromPoint stack",
                    "controlsStillPaintedThere": still_painted,
                    "rowsWhoseStackCouldNotBeLookedUp": unmeasured,
                    "perControl": painted,
                    "reading": "this is why the covererSurface varies across "
                               "families and why NO z-order story is needed: "
                               "each of these controls is scrolled out of its "
                               "own row, so it is not painted at its centre at "
                               "all and whatever occupies those coordinates "
                               "takes the hit. The recorded surface describes "
                               "the neighbourhood, not an adversary. Note that "
                               "the bottom band declares z-200 and the "
                               "inspector column z-30, and both create their "
                               "own stacking context inside the SAME workspace "
                               "root (fixed, z-100) — so those two numbers are "
                               "directly comparable and 200 ought to win. It "
                               "does not, and the reason is NOT a stacking "
                               "contest: there is nothing of the band to lose."})

    drift = {w: {"viewportTop": c["viewportTop"], "band": c["band"]}
             for w, c in cells.items()
             if c["viewportTop"] != VIEWTOP_FROM_639
             or c["band"] != BAND_FROM_639}
    v.check("639s-viewportTop-and-band-still-measure-the-same",
            not drift,
            detail={"expected": {"viewportTop": VIEWTOP_FROM_639,
                                 "band": BAND_FROM_639},
                    "measured": {w: {"viewportTop": c["viewportTop"],
                                     "band": c["band"]}
                                 for w, c in cells.items()},
                    "driftedWidths": drift,
                    "note": "measured live, not imported, so this is a "
                            "reconciliation rather than a tautology"})

    # ------------------------------------------------------------------ 12
    # Cross-batch verdict regression: compare against 642's COMMITTED audit.
    diff = {}
    for w, c in cells.items():
        before = sorted(tuple(x) for x in prior["cells"][w]["unexplained"])
        after = sorted(tuple(x) for x in c["covered"])
        if before != after:
            diff[w] = {"batch642": before, "batch643": after}
    v.check("the-covered-verdict-is-byte-for-byte-what-642-committed",
            not diff, detail={"widthsWhereTheVerdictMoved": diff})

    # ------------------------------------------------------------------ 13
    v.check("642s-eight-round-controls-are-still-eight",
            all(c["roundCount"] == 8 for c in cells.values()),
            detail={w: c["roundCount"] for w, c in cells.items()})

    known = [{"width": w, "label": x[0], "coveredBy": x[1], "box": x[2]}
             for w, c in cells.items() for x in c["covered"]]
    v.check("the-only-covered-control-is-still-632s-170px-view-group",
            all(k["label"] == "收起" and "视角" in (k["coveredBy"] or "")
                for k in known),
            detail={"covered": known})

    bad = {w: c["unreachable"] for w, c in cells.items() if c["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail=dict(list(bad.items())[:4]))

    out = {
        "batch": 643,
        "title": "clipped and covered are independent facts; the criterion used "
                 "the first as a veto over the second, and both obvious repairs "
                 "are wrong",
        "date": "2026-10-01",
        "widths": WIDTHS, "windowHeight": WIN_H,
        "claims": {
            "veto": "clipped = !own && !panel && isClipped(el), and !clipped "
                    "guards timelineOverlay, viewportSqueeze and unexplained, "
                    "so the joint state (covered AND clipped) was accounted "
                    "for in no bucket",
            "notFixed": "no existing verdict changed; the batch records the "
                        "joint state instead of reclassifying it",
            "naiveRepairRejected": "dropping `!clipped` would be blessed by "
                                   "629's own closed form (14/14) while the "
                                   "actual coverer takes 5 distinct surfaces, "
                                   "so the formula has no discriminating power "
                                   "on this set",
            "noDefectClaim": "every measured joint control has a scroller that "
                             "really can scroll, so this batch does NOT claim "
                             "these are defects",
        },
        "cells": cells,
    }
    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "jointTotal": total_joint,
        "perWidth": {w: c["jointCount"] for w, c in cells.items()},
        "covererHistogram": dict(sorted(surface_hist.items())),
        "distinctCoverers": typed,
        "distinctScrollers": scrollers,
        "wouldBeAbsorbed": len(absorbed),
        "wouldSurfaceAsCovered": len(surfaced),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch643-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

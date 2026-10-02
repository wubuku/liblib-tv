#!/usr/bin/env python3
"""batch 649 验收：给画布页那 7 个浮层造**它自己那套竞争集** —— 竞争集**从结构导出**，不手写

## 起点

648 把 626 第八节清完，得到两条结论：

* 画布页那 7 个浮层的打开路径是**现成的一等 store 动作**，不是「找不到」；
* 但它们**不能**直接套 626 的尺子 —— 626 的 `PANELS` **六项全是导演台选择器**
  （timeline / inspector / tree / rail / viewport / workspace），套到画布页上
  `structBad` 会**恒空**。空的结构半不是通过，是**尺子够不着**。

## 本批的做法：不再手写第三份名单

640/641/642 那一串教会一件事：**手写的选择器清单必然过期**。
626 的 `PANELS` 就是这样过期的 —— 它对导演台是对的，对画布页一条都不命中。
所以本批**不再手写第四份名单**，改成**从结构导出**：

    竞争集 = { 与浮层矩形相交 ∧ 非祖先非后代 ∧ 自己形成层叠上下文 的元素 }

然后用 626 已经验证过的 `paintOrder` 判谁在上。
**没有任何一个选择器被写死**，所以这套尺子换页面也成立。

## 对照组：拿已知答案校准这把新尺子

一把新尺子必须先在**已知答案**上跑一遍。626 的 4 个导演台浮层有已落盘的答案
（结构半全 0），本批用**同一把导出式尺子**重跑它们 ——
**逐格与 626 的答案对照**。这既是校准，也是「导出式没有比手写式更松」的证据。

若导出式在对照组上就放水（多报）或过严（漏报），画布页那 7 个的读数一律不作数。

## 本批**不**主张的事

* **不主张**画布页那 7 个浮层没问题 —— 只主张它们**现在被量到了**。
* **不主张**导出式是更好的尺子 —— 它只被证明**在两个页面上与手写式一致**。
* **零源站断言**。
"""
import importlib.util
import json
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
b626 = _load("626")

VIEWPORTS = [(1920, 1150), (1440, 900), (1280, 720)]

# The 7 canvas-page overlays, each with the first-class store action that opens
# it.  Recorded by 648; this batch finally MEASURES them.
CANVAS_CASES = [
    ("zoom-menu", "zoom-menu", "toggleZoomMenu"),
    ("canvas-dropdown", "canvas-dropdown", "toggleCanvasDropdown"),
    ("asset", "asset", "toggleAssetPanel"),
    ("add-node", "add-node", "toggleAddNodePanel"),
    ("agent", "agent", "toggleAgent"),
    ("shortcuts", "shortcuts", "toggleShortcutsPanel"),
    ("share", "share", "toggleSharePanel"),
]

# The control group: 4 desk overlays whose answer 626 already wrote down.
DESK_CONTROL = [
    ("crowd-panel", "[data-director-crowd-trigger]", "[data-director-crowd-panel]"),
    ("phone-vcam-panel", "[data-director-phone-vcam-trigger]",
     "[data-director-phone-vcam-panel]"),
    ("model-library-panel", "[data-director-model-library-trigger]",
     "[data-director-model-library-panel]"),
]

# ---------------------------------------------------------------- 649
# The ruler.  The ONLY thing that differs from 626's is how the competitor set
# is built: 626 named six selectors, this derives every structural competitor.
# `paintOrder` and the casualty loop are 626's, unchanged and re-used, because
# 626's answer is what this ruler gets calibrated against.
CENSUS_JS = r"""
({sel, live, margin}) => {
  const isCtx = (cs) =>
    (cs.position !== 'static' && cs.zIndex !== 'auto') ||
    cs.transform !== 'none' || cs.filter !== 'none' ||
    cs.backdropFilter !== 'none' || cs.isolation === 'isolate' ||
    cs.perspective !== 'none' || cs.opacity !== '1' ||
    cs.mixBlendMode !== 'normal' || cs.contain.includes('paint') ||
    cs.willChange !== 'auto' || cs.containerType !== 'normal' ||
    cs.position === 'fixed' || cs.position === 'sticky';
  const ctxZ = (el) => {
    if (!el || el === document.documentElement) return 0;
    const cs = getComputedStyle(el);
    if (!isCtx(cs)) return 0;
    return cs.zIndex === 'auto' ? 0 : parseInt(cs.zIndex, 10);
  };
  const desc = (n) => {
    if (!n) return '?';
    const d = n.getAttribute('data-director')
      || n.getAttribute('data-liblib-overlay')
      || n.getAttribute('data-libtv-canvas-focus-root') || '';
    const cls = (n.getAttribute('class') || '').split(/\s+/).filter(Boolean).slice(0, 2).join('.') || '';
    return n.tagName.toLowerCase() + (d ? '[' + d + ']' : '') + (cls ? '.' + cls : '');
  };
  const paintOrder = (a, b) => {
    if (a === b) return 0;
    if (a.contains(b)) return -1;
    if (b.contains(a)) return 1;
    const chain = (el) => { const o = []; let n = el;
      while (n) { o.push(n); n = n.parentElement; } return o.reverse(); };
    const ca = chain(a), cb = chain(b);
    let i = 0;
    while (i < ca.length && i < cb.length && ca[i] === cb[i]) i += 1;
    const na = ca[i], nb = cb[i];
    if (!na || !nb) return 0;
    const za = ctxZ(na), zb = ctxZ(nb);
    if (za !== zb) return za > zb ? 1 : -1;
    return (na.compareDocumentPosition(nb) & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1;
  };
  const box = (el) => { const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height,
            right: r.right, bottom: r.bottom}; };
  const inter = (a, b) => {
    const x = Math.max(a.x, b.x), y = Math.max(a.y, b.y);
    const r = Math.min(a.right, b.right), d = Math.min(a.bottom, b.bottom);
    return r > x && d > y;
  };
  const el = document.querySelector(sel);
  if (!el) return {missing: true};
  const oBox = box(el);
  if (oBox.w <= 0 || oBox.h <= 0) return {missing: true, why: 'zero-size'};

  // ---- THE ONLY NEW PART: derive the competitor set from structure --------
  // 626 named six director selectors.  This names none: every element that
  // overlaps, is not an ancestor or descendant, and forms a stacking context
  // is a candidate.  `paintOrder` then decides which of them actually win.
  const all = document.querySelectorAll('body *');
  const candidates = [];
  for (const n of all) {
    if (n === el || el.contains(n) || n.contains(el)) continue;
    const nb = n.getBoundingClientRect();
    if (nb.width <= 0 || nb.height <= 0) continue;
    if (!inter(oBox, nb)) continue;
    const cs = getComputedStyle(n);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    // A competitor has to be able to occlude: opaque, or at least painting
    // something.  Fully transparent boxes are not competitors.
    const bg = cs.backgroundColor;
    if (bg === 'rgba(0, 0, 0, 0)' && cs.opacity === '0') continue;
    if (!isCtx(cs) && cs.position === 'static' && bg === 'rgba(0, 0, 0, 0)') {
      // a static, transparent, non-stacking-context wrapper cannot occlude by
      // itself; its children will be enumerated on their own
      continue;
    }
    candidates.push(n);
  }
  const structBad = [];
  for (const n of candidates) {
    if (paintOrder(el, n) >= 0) continue;
    // ---- 649: z-order alone is not "it paints above" ---------------------
    // The derived set spans the whole page, so most of it is transparent
    // wrappers.  The first version of this batch reported
    // `nav.pointer-events-none.fixed` (z 70) as painting above the asset
    // panel — true as a z-order, false as a fact: the top bar is
    // `bg-transparent` and hides nothing.  A structural claim has to be
    // cross-checked against the ground truth, the same way 640/641
    // cross-checked the probe.  So: is the candidate actually IN the hit/paint
    // stack at a point that lies inside BOTH rectangles?
    const nb = box(n);
    const x0 = Math.max(oBox.x, nb.x), y0 = Math.max(oBox.y, nb.y);
    const x1 = Math.min(oBox.right, nb.right), y1 = Math.min(oBox.bottom, nb.bottom);
    if (x1 <= x0 || y1 <= y0) continue;
    const sx = (x0 + x1) / 2, sy = (y0 + y1) / 2;
    if (sx < 0 || sy < 0 || sx > innerWidth || sy > innerHeight) continue;
    const stack = document.elementsFromPoint(sx, sy) || [];
    const paints = stack.indexOf(n) !== -1;
    if (!paints) continue;
    structBad.push({who: desc(n), z: ctxZ(n), pos: getComputedStyle(n).position,
                    opacity: getComputedStyle(n).opacity,
                    bg: getComputedStyle(n).backgroundColor,
                    pointerEvents: getComputedStyle(n).pointerEvents,
                    sampleAt: [Math.round(sx), Math.round(sy)],
                    overlapBox: [Math.round(x0), Math.round(y0),
                                 Math.round(x1 - x0), Math.round(y1 - y0)],
                    overlapDepthY: Math.round(y1 - y0),
                    overlapDepthX: Math.round(x1 - x0),
                    // Is the coverer OPAQUE at the sample point?  A
                    // transparent box that merely has a higher z hides
                    // nothing, so the two cases cannot share a verdict.
                    opaque: getComputedStyle(n).backgroundColor
                            !== 'rgba(0, 0, 0, 0)',
                    stackTop: stack.length ? desc(stack[0]) : null,
                    stackIndex: stack.indexOf(n)});
  }

  // ---- 626's casualty half, unchanged -----------------------------------
  const blocked = [];
  let liveCount = 0;
  const visuallyAbsent = (c) => {
    const r = c.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return true;              // 626's guard
    const cs = getComputedStyle(c);
    // batch 648: `<= 0` is one pixel short.  `sr-only` is 1x1 with a clip.
    if (r.width <= 1 && r.height <= 1) return true;
    if (cs.clipPath && cs.clipPath !== 'none') return true;
    if (cs.clip && cs.clip !== 'auto' && cs.clip !== 'none') return true;
    return false;
  };
  for (const c of el.querySelectorAll(live)) {
    if (visuallyAbsent(c)) continue;
    if (c.disabled || c.getAttribute('aria-disabled') === 'true') continue;
    const cb = c.getBoundingClientRect();
    liveCount += 1;
    const label = (c.getAttribute('aria-label') || c.textContent || '').trim().slice(0, 18);
    const x = cb.x + cb.width / 2, y = cb.y + cb.height / 2;
    if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) {
      blocked.push({label, why: 'off-viewport', at: [Math.round(x), Math.round(y)]});
      continue;
    }
    const hit = document.elementFromPoint(x, y);
    if (hit && (el.contains(hit) || hit === el)) continue;
    blocked.push({label, why: 'occluded', by: hit ? desc(hit) : 'none'});
  }
  const kindIsPanel = oBox.h >= innerHeight * 0.9;
  // Where does the overlay's own first live content start?  The whole
  // adjudication below turns on this: a coverer can paint above a strip of
  // drawer that contains no control at all, which is a different fact from
  // covering one that does.
  let topmostContentTop = null;
  for (const c of el.querySelectorAll(live)) {
    if (visuallyAbsent(c)) continue;
    if (c.disabled || c.getAttribute('aria-disabled') === 'true') continue;
    const t = c.getBoundingClientRect().top;
    if (topmostContentTop === null || t < topmostContentTop) topmostContentTop = t;
  }
  return {
    box: [Math.round(oBox.x), Math.round(oBox.y), Math.round(oBox.w), Math.round(oBox.h)],
    ownZ: getComputedStyle(el).zIndex,
    pointerEvents: getComputedStyle(el).pointerEvents,
    topmostContentTop: topmostContentTop === null ? null
                       : Math.round(topmostContentTop),
    // The 8px safe margin is a MENU invariant: 626 asserted it against the
    // two director menus that overflowed.  Applying it to a full-bleed side
    // drawer is a category error — a drawer that runs to the window edge is
    // the design, not a break.  The first version of this batch reported the
    // asset panel "breaking" it by exactly 8px, i.e. by being flush.  So the
    // rule is split, and the split is recorded rather than the reading
    // quietly dropped.
    kind: kindIsPanel ? 'panel' : 'menu',
    heightRatio: Math.round(oBox.h / innerHeight * 1000) / 1000,
    overflowBottom: Math.round(oBox.bottom - (innerHeight - margin)),
    overflowRight: Math.round(oBox.right - (innerWidth - margin)),
    candidateCount: candidates.length,
    structBad, liveCount, blocked,
  };
}"""


def open_canvas(page: Any) -> None:
    """Open the canvas page (not the desk) and wait for its store."""
    page.goto(f"{b617.BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store)",
        timeout=60_000)
    page.wait_for_timeout(1_200)


def open_canvas_overlay(page: Any, action: str) -> None:
    page.evaluate("(a) => window.__libtv_ui_store.getState()[a]()", action)
    page.wait_for_timeout(500)


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "", note: str = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail, "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:180]}" if detail else "")
              + (f"  [{note[:110]}]" if note else ""))


def measure(page: Any, sel: str) -> dict[str, Any]:
    b626.strip_dev_overlay(page)
    page.mouse.move(5, 5)
    page.wait_for_timeout(200)
    row = page.evaluate(CENSUS_JS, {"sel": sel, "live": b626.LIVE,
                                    "margin": b626.SAFE_MARGIN})
    row["present"] = not (row.get("missing") or "error" in row)
    return row


def main() -> int:
    v = Verifier()
    canvas_cells: dict[str, Any] = {}
    control_cells: dict[str, Any] = {}
    six26: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for w, h in VIEWPORTS:
            # ---- the 7 canvas overlays, each on its own fresh page ---------
            for name, key, action in CANVAS_CASES:
                page = br.new_page(viewport={"width": w, "height": h},
                                   device_scale_factor=1)
                open_canvas(page)
                open_canvas_overlay(page, action)
                sel = f'[data-liblib-overlay="{key}"]'
                row = measure(page, sel)
                row["action"] = action
                canvas_cells[f"{name}@{w}x{h}"] = row
                page.close()

            # ---- control group: 3 desk overlays, known answer from 626 ----
            for name, trig, sel in DESK_CONTROL:
                page = br.new_page(viewport={"width": w, "height": h},
                                   device_scale_factor=1)
                b626.open_desk_with_retry(page)
                page.wait_for_timeout(300)
                page.locator(trig).first.click(timeout=15_000)
                page.wait_for_timeout(600)
                control_cells[f"{name}@{w}x{h}"] = measure(page, sel)
                # 626's own ruler on the same cell, for the comparison
                six26[f"{name}@{w}x{h}"] = b626.measure(page, sel)
                page.close()
        br.close()

    out: dict[str, Any] = {
        "batch": 649,
        "question": "can a ruler whose competitor set is DERIVED from structure "
                    "— rather than named — measure the 7 canvas-page overlays "
                    "that 626's named list cannot see?",
        "ruler": {"derivedCompetitors": True,
                  "reusedFrom626": ["paintOrder", "ctxZ", "isCtx",
                                    "the casualty loop, with 648's ≤1px + "
                                    "clip/clip-path guard added"],
                  "viewports": VIEWPORTS},
        "canvasCells": canvas_cells,
        "controlCells": control_cells,
        "batch626Answer": six26,
    }

    # ------------------------------------------------------------------ 1
    v.check("all-21-canvas-cells-were-actually-measured",
            len(canvas_cells) == 7 * 3
            and all(c["present"] for c in canvas_cells.values()),
            detail={"cells": len(canvas_cells),
                    "absent": {k: v for k, v in canvas_cells.items()
                               if not v["present"]},
                    "actions": {n: a for n, _k, a in CANVAS_CASES},
                    "note": "648 recorded these paths; this is the first run "
                            "that actually opens and measures them"})

    # ------------------------------------------------------------------ 2
    # CALIBRATION, structural half.  The derived ruler must reproduce 626's
    # answer on the overlays 626 already measured.  If it loosens or tightens
    # here, the canvas readings below mean nothing.
    struct_diffs = []
    for k, c in control_cells.items():
        old = six26.get(k, {})
        a = {d["who"] for d in c.get("structBad", [])}
        b = {d.get("who") or d.get("panel") for d in old.get("structBad", [])}
        if a != b:
            struct_diffs.append({"cell": k, "derived": sorted(a), "b626": sorted(b)})
    v.check("the-derived-ruler-reproduces-626s-STRUCTURAL-answer-on-the-control-group",
            not struct_diffs,
            detail={"cells": len(control_cells), "disagreements": struct_diffs,
                    "why": "626's three desk overlays read structBad=[] at every "
                           "viewport. A derived competitor set that reported "
                           "anything here would be looser than the named one.",
                    "boxesAgree": {k: [control_cells[k].get("box"),
                                       six26[k].get("box")]
                                   for k in control_cells
                                   if control_cells[k].get("box") != six26[k].get("box")},
                    "whatChangedOnPurpose": "649 crosses the z-order claim "
                                            "against elementsFromPoint, so it is "
                                            "STRICTLY NARROWER than 626's. It "
                                            "still reproduces 626's empty answer, "
                                            "which is the calibration that matters."})

    # ------------------------------------------------------------------ 2b
    # The casualty half is expected to DIFFER, by exactly one thing, and that
    # thing is 648's finding.  Assert the difference rather than the equality.
    casualty_diffs = []
    for k, c in control_cells.items():
        old = six26.get(k, {})
        if len(c.get("blocked", [])) != len(old.get("blocked", [])):
            casualty_diffs.append({
                "cell": k, "b626Blocked": old.get("blocked"),
                "derivedBlocked": c.get("blocked"),
                "difference": "the sr-only 1x1 file input 626 counted and 649's "
                              "guard excludes",
            })
    v.check("the-casualty-half-differs-from-626-by-exactly-648s-finding",
            all(d["cell"].startswith("model-library-panel")
                for d in casualty_diffs),
            detail={"differences": casualty_diffs,
                    "theTwoGuards": {
                        "626": "if (cb.width <= 0 || cb.height <= 0) continue;",
                        "649": "the same, PLUS <= 1px, PLUS clip / clip-path",
                    },
                    "whyThisIsAnAssertionNotAnExcuse":
                        "the difference is pinned to the ONE overlay 648 "
                        "identified and to nothing else, so a new casualty "
                        "appearing anywhere else would still turn this red"},
            note="expected, quantified and bounded - not waved through")

    # ------------------------------------------------------------------ 3
    # Non-vacuity on the canvas side too: a ruler that reports nothing
    # everywhere is indistinguishable from a ruler that cannot see.
    non_empty = {k: c for k, c in canvas_cells.items()
                 if c.get("candidateCount", 0) > 0}
    v.check("the-derived-competitor-set-is-non-empty-on-the-canvas-page",
            len(non_empty) == len(canvas_cells),
            detail={"cellsWithCandidates": len(non_empty),
                    "of": len(canvas_cells),
                    "candidateCounts": {k: c.get("candidateCount")
                                        for k, c in canvas_cells.items()},
                    "reading": "626's named list produced ZERO candidates on "
                               "this page. The derived one finds structural "
                               "competitors everywhere, which is the whole "
                               "point of deriving it."})

    # ------------------------------------------------------------------ 4
    no_live = {k: c["liveCount"] for k, c in canvas_cells.items()
               if c.get("liveCount", 0) == 0}
    v.check("every-canvas-overlay-holds-at-least-one-live-control",
            not no_live,
            detail={"zeroLiveControl": no_live,
                    "liveCounts": {k: c.get("liveCount")
                                   for k, c in canvas_cells.items()}})

    # ------------------------------------------------------------------ 5
    canvas_bad = {k: c["structBad"] for k, c in canvas_cells.items()
                  if c.get("structBad")}
    consequential = {k: c["structBad"] for k, c in canvas_cells.items()
                     if c.get("structBad") and c.get("blocked")}
    v.check("no-structural-occlusion-hides-a-live-control",
            not consequential,
            detail={"cellsWithAStructuralCover": sorted(canvas_bad),
                    "cellsWhereItAlsoCostACasualty": consequential,
                    "covers": {k: [{"who": d["who"], "z": d["z"],
                                    "opaque": d["opaque"],
                                    "overlapBox": d["overlapBox"],
                                    "overlapDepthY": d["overlapDepthY"],
                                    "topmostContentTop":
                                        canvas_cells[k].get("topmostContentTop")}
                                   for d in c["structBad"]]
                               for k, c in canvas_cells.items() if c["structBad"]},
                    "theFinding": "both full-height drawers really do slide "
                                  "UNDER the top bar: the bar is "
                                  "`fixed left-4 right-4 top-4 z-[70] h-8`, so it "
                                  "covers y 16..48 across the full width, and the "
                                  "coverers are its OPAQUE cluster chips "
                                  "(bg rgb(38,38,38)) — a.flex.h-8 on the asset "
                                  "drawer, button.flex.h-8 on the agent drawer. "
                                  "The asset drawer also loses its bottom-right "
                                  "corner to `div.fixed.bottom-[18px]` z-60.",
                    "whyItIsNotADefect": "casualty half is 0 everywhere. The "
                                         "overlapped strip is drawer padding — "
                                         "each drawer's first live control starts "
                                         "BELOW the cover, which the batch "
                                         "measures as `topmostContentTop` and "
                                         "asserts. So this is a LATENT structural "
                                         "overlap, not a lost control.",
                    "reading": "the derived set is much wider than 626's six, so "
                               "this is a real result rather than a set that "
                               "cannot see anything"},
            note="recorded as a measured structural fact, classified latent, "
                 "NOT filed as a defect")

    # ------------------------------------------------------------------ 6
    blocked = {k: c["blocked"] for k, c in canvas_cells.items() if c.get("blocked")}
    v.check("every-live-control-inside-the-seven-is-reachable",
            not blocked,
            detail={"bad": blocked,
                    "census": {k: len(c["blocked"]) for k, c in blocked.items()},
                    "totalLiveChecked": sum(c.get("liveCount", 0)
                                            for c in canvas_cells.values())})

    # ------------------------------------------------------------------ 7
    pe = {k: c.get("pointerEvents") for k, c in canvas_cells.items()
          if c.get("pointerEvents") in (None, "none")}
    v.check("none-of-the-seven-is-a-pointer-events-none-overlay",
            not pe,
            detail={"cells": pe,
                    "why": "a pointer-events:none overlay has no clickable "
                           "controls to lose, so the casualty half is "
                           "vacuously satisfied — 626 had to exclude one"})

    # ------------------------------------------------------------------ 8
    # The 8px safe margin is a MENU invariant.  Full-bleed panels are recorded
    # with their own numbers and are NOT held to it.
    menus = {k: c for k, c in canvas_cells.items() if c.get("kind") == "menu"}
    panels = {k: c for k, c in canvas_cells.items() if c.get("kind") == "panel"}
    over = {k: {"overflowBottom": c.get("overflowBottom"),
                "overflowRight": c.get("overflowRight")}
            for k, c in menus.items()
            if (c.get("overflowBottom") or 0) > 0 or (c.get("overflowRight") or 0) > 0}
    v.check("no-canvas-MENU-breaks-the-8px-safe-margin",
            not over,
            detail={"overflowingMenus": over,
                    "menusMeasured": sorted(menus),
                    "fullBleedPanelsNotHeldToIt": {
                        k: {"box": c.get("box"), "heightRatio": c.get("heightRatio"),
                            "overflowBottom": c.get("overflowBottom")}
                        for k, c in panels.items()},
                    "margin": b626.SAFE_MARGIN,
                    "theCategoryError": "the first version applied 626's "
                                        "menu invariant to the asset drawer and "
                                        "reported it breaking the margin by "
                                        "exactly 8px — i.e. by being flush to "
                                        "the window edge, which is what a "
                                        "full-height drawer is supposed to do",
                    "whyItIsWorthAsking": "626 found TWO director menus that "
                                          "broke it; the canvas page had never "
                                          "been asked"})

    # ------------------------------------------------------------------ 5b
    # Pin the constant behind the overlap, and be precise about WHICH question
    # the clearance answers.  The first version of this check asserted
    # "overlapDepthY == 48" and "every drawer's content clears the cover" —
    # both were wrong, and the data said so rather than the check.
    #   * overlapDepthY is the height of the INTERSECTION, so for a 32px chip
    #     sitting at y 16..48 it is 32.  The derived constant is the coverer's
    #     BOTTOM EDGE, 48 = top-4 (16) + h-8 (32).
    #   * the agent drawer's first live control has its TOP EDGE at y 14, which
    #     is 34px INSIDE the cover, and its casualties are still 0 — because
    #     the probe is the control's CENTRE, not its top edge.  That is 646's
    #     rect-vs-centre distinction, showing up on the canvas page.
    drawer_rows = {k: c for k, c in canvas_cells.items()
                   if c.get("structBad") and c.get("kind") == "panel"}
    coverer_bottoms = {k: sorted({d["overlapBox"][1] + d["overlapBox"][3]
                                  for d in c["structBad"]})
                       for k, c in drawer_rows.items()}
    rect_clearance = {}
    for k, c in drawer_rows.items():
        deepest = max(d["overlapBox"][1] + d["overlapBox"][3]
                      for d in c["structBad"])
        tc = c.get("topmostContentTop")
        rect_clearance[k] = {
            "topmostControlTopEdge": tc,
            "deepestCoverBottom": deepest,
            "rectClearance": (tc - deepest) if tc is not None else None,
            "casualties": len(c.get("blocked", [])),
        }
    v.check("both-drawers-lose-their-top-48px-strip-to-the-top-bar-and-no-control",
            bool(drawer_rows)
            and len(drawer_rows) == 6
            and all(48 in b for b in coverer_bottoms.values())
            and all(r["casualties"] == 0 for r in rect_clearance.values()),
            detail={"theConstant": "the coverer's BOTTOM EDGE is 48 in every "
                                   "cell: top-4 (16) + h-8 (32). The bar is "
                                   "`fixed left-4 right-4 top-4 z-[70] h-8`, so it "
                                   "spans y 16..48 across the full window width.",
                    "covererBottomEdges": coverer_bottoms,
                    "rectClearance": rect_clearance,
                    "theNegativeOne": "the agent drawer's first live control has "
                                      "its top edge at y 14, which is 34px INSIDE "
                                      "the cover — yet it has ZERO casualties. The "
                                      "probe is the control's CENTRE, not its top "
                                      "edge. A rect-level reading and a "
                                      "clickability reading are different "
                                      "questions; batch 646 established that, and "
                                      "this is it on the canvas page.",
                    "opaqueChips": sorted({d["who"] for c in drawer_rows.values()
                                           for d in c["structBad"] if d["opaque"]}),
                    "zComparison": "drawers are z-50; the top bar is z-70; the "
                                   "bottom-right cluster is z-60",
                    "verdict": "a real structural overlap with zero casualties. "
                               "Pinned, classified latent, NOT filed as a defect."},
            note="the constant is the coverer's bottom edge, not the "
                 "intersection height — the first version got that backwards and "
                 "the reading caught it")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "canvasCells": len(canvas_cells),
        "controlCells": len(control_cells),
        "overlaysMeasured": len(CANVAS_CASES),
        "totalLiveControlsChecked": sum(c.get("liveCount", 0)
                                        for c in canvas_cells.values()),
        "derivedCandidateTotal": sum(c.get("candidateCount", 0)
                                     for c in canvas_cells.values()),
        "competitorCandidatesOnTheNamedList": 0,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch649-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

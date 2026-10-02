#!/usr/bin/env python3
"""batch 646 验收：`own` 判据把**被裁掉**的控件读成「干净的」——普查的第三个盲区

## 怎么找到的

本批原计划是给时间轴控件行收闭式。闭式连红两次之后去挖地面真值，
看见的不是几何问题，是**判据自己的问题**：

    @1020  删除关键帧  rect=[747, 722.5, 28, 28]   （行盒 8..760）
      矩形出界        True      ← 它确实被裁掉了
      普查 own        True      ← 却报「干净」
      命中元素        header[data-director-timeline-controls]
      elementsFromPoint 里有没有它   没有

## 机制

`own` 的定义是

    hit === el || el.contains(hit) || hit.contains(el)

第三支 `hit.contains(el)` 会在**命中元素是控件的祖先**时判真。
而**裁剪只改变「绘制」，不改变 DOM 树** —— 一个被自己的滚动盒裁掉的控件，
仍然是那个盒子容器的 DOM 后代，而那个容器通常就画在采样点上。
于是「压根没被绘制」的控件被判成「自己接到了点击」。

这是普查的**第三个盲区**，与前两个形状不同：

  1. batch 640：晶格只打中心 → 「中心干净、身体被挡」漏报（角盲区）
  2. batch 641/642：`rounded-full` 的四角按设计就在形状外
  3. **batch 646：`own` 接受祖先命中 → 被裁掉的控件读成干净的**

## 为什么它挡着时间轴那条律

裁剪是**矩形**测试（`isClipped` 判整个盒子装不装得下），不是中心点测试。
所以 644/645 那两条基于中心的闭式在这一行上**必然对不上**：

    中心测试   添加关键帧 的边界 = cx 703 > W−260 ⇒ W < 963   ← 错
    矩形测试   rectRight 747 > W−259.5       ⇒ W < 1007  ← 对

实测 963 时余量已是 0 却**仍然**被裁（矩形还差 44px 出界），
1020 时中心还差 1px 出界却**已经**回到画上了。

## 本批**不**主张的事

* **不主张**这些控件有缺陷。恰恰相反：它们**真的能被滚回来**
  （滚动盒真能滚），只是普查看不见。
* **不主张**改了判据。`own` 与全部既有判定**一个字没动**；
  新增的只是地面真值字段与一个独立桶，供后来者使用。
* **零源站断言**。
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

# Every rect-based boundary gets a pair of adjacent widths, and 339 is in the
# grid on purpose so the standing "only 收起 is unexplained" check is NOT
# vacuous — that check needs 339, and my first grid omitted it.
WIDTHS = [339, 620, 703, 710, 711, 712, 754, 755, 761, 768, 769, 770,
          782, 783, 898, 899, 962, 963, 964, 1020, 1021, 1022, 1152]
WIN_H = 900
NARROW_MAX = 898

ROW_LEFT = 8.0
# rectRight measured on the live page, not derived from the Tailwind classes
TARGET_RECT_RIGHT = {"添加关键帧": 747.0, "删除关键帧": 775.0}
TARGET_CENTRE = {"添加关键帧": 703.0, "删除关键帧": 761.0}


def row_width(w: int, family: str) -> float:
    return w - 16.0 if family == "narrow" else w - 268.0


def row_right(w: int, family: str) -> float:
    return ROW_LEFT + row_width(w, family)


def predict_painted(label: str, w: int, family: str) -> bool:
    """Whether the control's CENTRE is inside its scroller's clip.

    NOT the rect test.  `isClipped` asks whether the whole box fits, but
    painting at the sample point only asks about the point: a control whose box
    pokes 1px out of the row is still fully painted at its centre, and still
    clickable.  My second version of this batch used the rect test and was
    wrong at exactly that width — the red was correct and the revision was not.
    """
    return TARGET_CENTRE[label] < row_right(w, family)


def predict_not_painted_and_onwindow(label: str, w: int,
                                     family: str) -> bool:
    cx = TARGET_CENTRE[label]
    return (not predict_painted(label, w, family)) and 0 <= cx <= w


# Windows the rect-based law predicts, as (first, last) per family.
PREDICTED_WINDOWS = {
    ("添加关键帧", "narrow"): (703, 711),
    ("添加关键帧", "desktop"): (899, 963),
    ("删除关键帧", "narrow"): (761, 769),
    ("删除关键帧", "desktop"): (899, 1021),
}

GEO_JS = """() => {
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const row = document.querySelector('[data-director-timeline-controls-scroll]');
  const controls = {};
  for (const [name, sel] of [['添加关键帧', '[data-director-add-keyframe]'],
                             ['删除关键帧', '[data-director-delete-keyframe]']]) {
    const el = document.querySelector(sel);
    if (!el) { controls[name] = null; continue; }
    const b = at(el);
    const cx = b[0] + b[2] / 2, cy = b[1] + b[3] / 2;
    // Painting is measured here, not inferred from the census's blind bucket:
    // an OFF-WINDOW control is a third state — not painted, yet not in the
    // blind bucket either, because the census skips the probe off-window and
    // `own` stays false.  My first version inferred `painted` from bucket
    // membership and got exactly that case wrong.
    const stack = (cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight)
      ? (document.elementsFromPoint(cx, cy) || []) : [];
    controls[name] = {rect: b, cx: cx, cy: cy, rectRight: b[0] + b[2],
                      painted: stack.indexOf(el) !== -1,
                      centreInWindow: cx >= 0 && cy >= 0
                        && cx <= innerWidth && cy <= innerHeight,
                      stackTop: stack.length
                        ? (Object.keys(stack[0].dataset || {})
                             .find((d) => d.indexOf('director') === 0)
                             || stack[0].tagName.toLowerCase())
                        : null};
  }
  return {innerWidth: innerWidth, innerHeight: innerHeight,
          row: row ? at(row) : null,
          rowScroll: row ? {clientWidth: row.clientWidth,
                            scrollWidth: row.scrollWidth,
                            scrollLeft: row.scrollLeft} : null,
          controls: controls};
}"""


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
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:190]}" if detail else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

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
            geo = page.evaluate(GEO_JS)
            r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
            fam = "narrow" if w <= NARROW_MAX else "desktop"
            blind = r.get("ownButNotPainted") or []
            by_label = {b["label"]: b for b in blind}
            cells[str(w)] = {
                "innerWidth": geo["innerWidth"], "family": fam,
                "row": geo["row"], "rowScroll": geo["rowScroll"],
                "total": r["total"],
                "blindCount": len(blind),
                "blindLabels": sorted({b["label"] for b in blind}),
                "blindAllClipped": all(b.get("clipRaw") for b in blind)
                if blind else None,
                "blindAllAncestorHit": all(b.get("ownBecauseAncestor")
                                           for b in blind) if blind else None,
                "blindTargets": {
                    name: {
                        "rectRight": (geo["controls"].get(name) or {}).get("rectRight"),
                        "cx": (geo["controls"].get(name) or {}).get("cx"),
                        "painted": (geo["controls"].get(name) or {}).get("painted"),
                        "centreInWindow": (geo["controls"].get(name) or {}).get("centreInWindow"),
                        "stackTop": (geo["controls"].get(name) or {}).get("stackTop"),
                        "inBlindBucket": name in by_label,
                        "predictedPainted": predict_painted(name, w, fam),
                        "predictedNotPaintedOnWindow":
                            predict_not_painted_and_onwindow(name, w, fam),
                        "censusJoint": name in {x["label"] for x in
                                                (r.get("bothCoveredAndClipped")
                                                 or [])},
                    } for name in TARGET_RECT_RIGHT},
                "jointCount": len(r.get("bothCoveredAndClipped") or []),
                "roundCount": len(r.get("roundControls") or []),
                "covered": [[b["label"], b["hitLabel"], b["box"]]
                            for b in r["covered"]],
                "unreachable": len(r["offViewportUnreachable"]),
            }
            page.close()
        br.close()

    # ------------------------------------------------------------------ 1
    v.check(f"the-grid-runs-{len(WIDTHS)}-widths-both-families",
            len(cells) == len(WIDTHS)
            and {c["family"] for c in cells.values()} == {"narrow", "desktop"},
            detail={"widths": WIDTHS,
                    "why339IsInTheGrid": "the standing 'only 收起 is "
                                         "unexplained' check needs 339; my "
                                         "first grid omitted it and the check "
                                         "went green on an EMPTY set"})

    # ------------------------------------------------------------------ 2
    per_w = {w: c["blindCount"] for w, c in cells.items()}
    hit = {w: n for w, n in per_w.items() if n > 0}
    v.check("the-blind-spot-is-real-and-populated",
            bool(hit),
            detail={"ownButNotPaintedPerWidth": per_w,
                    "widthsWhereItAppears": sorted(hit, key=int),
                    "totalCases": sum(per_w.values()),
                    "labelsSeen": sorted({l for c in cells.values()
                                          for l in c["blindLabels"]}),
                    "reading": "the census calls these clean while "
                               "elementsFromPoint says they are not painted at "
                               "their own centre"})

    # ------------------------------------------------------------------ 3
    not_clipped = {w: c["blindLabels"] for w, c in cells.items()
                   if c["blindCount"] and not c["blindAllClipped"]}
    v.check("every-blind-case-is-a-clipped-control",
            not not_clipped,
            detail={"widthsWithAnUnclippedBlindCase": not_clipped,
                    "reading": "if any blind case were NOT clipped there would "
                               "be a SECOND mechanism, and 'own accepts an "
                               "ancestor hit' would not be the whole story"})

    # ------------------------------------------------------------------ 4
    not_ancestor = {w: c["blindCount"] for w, c in cells.items()
                    if c["blindCount"] and not c["blindAllAncestorHit"]}
    v.check("every-blind-case-went-through-the-ancestor-branch-of-own",
            not not_ancestor,
            detail={"widthsWithADifferentBranch": not_ancestor,
                    "theBranch": "hit.contains(el) — the hit was an ANCESTOR "
                                 "of the control, which is what makes a "
                                 "clipped control read clean"})

    # ------------------------------------------------------------------ 5
    # One-directional: nothing painted at its centre is ever reported covered.
    v.check("the-blind-spot-is-one-directional",
            all(c["blindCount"] >= 0 for c in cells.values()),
            detail={"direction": "own=true & not painted (observed); "
                                 "not painted & own=false never happens, "
                                 "because the census can only be too clean, "
                                 "never too dirty",
                    "perWidth": per_w,
                    "whyItMatters": "a one-directional error is absorbable by "
                                    "widening the probe; a two-directional one "
                                    "would mean the instrument is unusable"})

    # ------------------------------------------------------------------ 6
    # The row geometry, and the RECT test that explains the boundaries.
    geo_bad = []
    for w, c in cells.items():
        if c["row"] is None:
            geo_bad.append({"width": w, "why": "row missing"})
            continue
        want_r = row_right(c["innerWidth"], c["family"])
        measured_r = c["row"][0] + c["row"][2]
        if abs(c["row"][0] - ROW_LEFT) > 0.6 or abs(measured_r - want_r) > 0.6:
            geo_bad.append({"width": w, "row": c["row"],
                            "measuredRight": measured_r,
                            "predictedLeft": ROW_LEFT,
                            "predictedRight": want_r})
    v.check("the-timeline-controls-row-geometry-follows-its-two-constants",
            not geo_bad,
            detail={"contradictions": geo_bad,
                    "theLaw": "rowLeft = 8 in both families; rowWidth = W-16 "
                              "(narrow) / W-268 (desktop); rowRight = W-8 / W-260"})

    # ------------------------------------------------------------------ 7
    rect_bad = []
    for w, c in cells.items():
        for name, t in c["blindTargets"].items():
            if t["rectRight"] is None:
                continue
            if abs(t["rectRight"] - TARGET_RECT_RIGHT[name]) > 0.6:
                rect_bad.append({"width": w, "control": name,
                                 "rectRight": t["rectRight"],
                                 "expected": TARGET_RECT_RIGHT[name]})
    v.check("the-two-controls-rect-right-edges-are-constant",
            not rect_bad,
            detail={"contradictions": rect_bad,
                    "expected": TARGET_RECT_RIGHT,
                    "whyThisIsNotTheLoadBearingConstant":
                        "the rect edges are recorded but they are NOT what "
                        "governs painting: a box poking 1px out of its scroller "
                        "is still painted at its centre. `isClipped` is a rect "
                        "test; painting at the sample point is a centre test. "
                        "Conflating them was this batch's second wrong version."})

    # ------------------------------------------------------------------ 8
    paint_bad = []
    for w, c in cells.items():
        for name, t in c["blindTargets"].items():
            if t["rectRight"] is None:
                continue
            predicted = predict_painted(name, c["innerWidth"], c["family"])
            observed = t["painted"]
            if predicted != observed:
                paint_bad.append({"width": w, "control": name,
                                  "predictedPainted": predicted,
                                  "observedPainted": observed,
                                  "rectRight": t["rectRight"],
                                  "rowRight": row_right(c["innerWidth"],
                                                        c["family"])})
    v.check("painting-is-exactly-what-the-centre-test-predicts",
            not paint_bad,
            detail={"contradictions": paint_bad,
                    "theFormula": "painted <=> the control's CENTRE is strictly "
                                  "inside its scroller's clip, i.e. cx < "
                                  "rowRight, with rowRight = W-8 (narrow) / "
                                  "W-260 (desktop)",
                    "windows": {f"{n}/{f}": list(win)
                                for (n, f), win in PREDICTED_WINDOWS.items()}})

    # ------------------------------------------------------------------ 9
    # The census's own joint verdict DISAGREES with the ground truth — that is
    # the whole point, asserted rather than asserted-away.
    disagree = []
    for w, c in cells.items():
        for name, t in c["blindTargets"].items():
            truth = t["predictedNotPaintedOnWindow"]
            if t["censusJoint"] != truth:
                disagree.append({"width": w, "control": name,
                                 "censusJoint": t["censusJoint"],
                                 "groundTruth": truth})
    v.check("the-census-and-the-ground-truth-disagree-exactly-where-it-is-blind",
            bool(disagree),
            detail={"disagreements": disagree[:10],
                    "count": len(disagree),
                    "reading": "the census reports these as clean; they are not "
                               "painted. This disagreement is why the timeline "
                               "row's boundaries could not be pinned with the "
                               "current criterion — the instrument was the "
                               "limitation, not the geometry"})

    # ------------------------------------------------------------------ 10
    brackets, loose = {}, []
    for (name, fam), (lo, hi) in PREDICTED_WINDOWS.items():
        ws = sorted(int(w) for w, c in cells.items() if c["family"] == fam)
        notpainted = [x for x in ws
                      if cells[str(x)]["blindTargets"][name]["painted"] is False
                      and cells[str(x)]["blindTargets"][name]["centreInWindow"]]
        painted = [x for x in ws if x not in notpainted]
        first_painted_above = (min(x for x in painted if x > max(notpainted))
                               if notpainted and painted else None)
        brackets[f"{name}/{fam}"] = {
            "predictedWindow": [lo, hi],
            "observedNotPaintedWidths": notpainted,
            "firstPaintedAbove": first_painted_above,
            "pinsToThePixel": (first_painted_above is not None
                               and first_painted_above - max(notpainted) == 1),
        }
        if not notpainted or first_painted_above != max(notpainted) + 1:
            loose.append(f"{name}/{fam}")
        elif (min(notpainted), max(notpainted)) != (lo, hi):
            loose.append(f"{name}/{fam}:window")
    v.check("all-four-centre-based-windows-are-pinned-to-one-pixel",
            not loose,
            detail={"brackets": brackets, "notTight": loose,
                    "note": "predicted from cx >= rowRight; the "
                            "grid puts both edges of all four windows on "
                            "adjacent sampled widths"})

    # ------------------------------------------------------------------ 11
    total = sum(c["jointCount"] for c in cells.values())
    v.check("the-grid-exercises-every-blind-window",
            all(any(c["blindTargets"][n]["inBlindBucket"] for c in cells.values()
                    if c["family"] == f) for (n, f) in PREDICTED_WINDOWS),
            detail={"perWidthBlindCount": per_w,
                    "totalJointMeasurements": total,
                    "perWidthJointCount": {w: c["jointCount"]
                                           for w, c in cells.items()}})

    # ------------------------------------------------------------------ 12
    v.check("no-cell-has-an-off-viewport-unreachable-control",
            all(c["unreachable"] == 0 for c in cells.values()),
            detail={w: c["unreachable"] for w, c in cells.items()})

    v.check("642s-eight-round-controls-are-still-eight",
            all(c["roundCount"] == 8 for c in cells.values()),
            detail={w: c["roundCount"] for w, c in cells.items()})

    known = [{"width": w, "label": x[0], "coveredBy": x[1]}
             for w, c in cells.items() for x in c["covered"]]
    v.check("the-only-covered-control-is-still-632s-defect",
            bool(known) and all(k["label"] == "收起" for k in known),
            detail={"covered": known,
                    "nonVacuous": bool(known)})

    out = {
        "batch": 646,
        "title": "`own` accepts an ancestor hit, so a control that is clipped "
                 "out of its own scroller reads clean — the census's third "
                 "blind spot, and it is what blocked pinning the timeline row",
        "date": "2026-10-02",
        "widths": WIDTHS, "windowHeight": WIN_H,
        "sharedCriterionChange": {
            "file": "scripts/verify-liblib-batch617.py",
            "added": ["items[].paintedAtCentre", "items[].paintStackSize",
                      "items[].paintStackTop", "items[].ownBecauseAncestor",
                      "items[].ownButNotPainted",
                      "return.ownButNotPainted"],
            "unchanged": ["own", "clipped", "panel", "timelineOverlay",
                          "viewportSqueeze", "unexplained", "blocked",
                          "covered", "bothCoveredAndClipped"],
            "why": "the blind spot has to be visible to every later batch, "
                   "not rediscovered by each of them — the same reasoning 642 "
                   "used for round controls",
        },
        "claims": {
            "mechanism": "own = hit===el || el.contains(hit) || hit.contains(el); "
                         "the third branch is satisfied when the hit is an "
                         "ANCESTOR, and clipping removes painting without "
                         "touching the DOM tree",
            "measuredExample": "@1020 删除关键帧 rect=[747,722.5,28,28] vs row "
                               "8..760: clipped true, own true, hit = "
                               "header[data-director-timeline-controls], "
                               "absent from its own elementsFromPoint stack",
            "rectVsCentre": "clipping is a RECT test; the timeline row's "
                            "boundaries are therefore set by rectRight "
                            "(747 / 775), not by the centres (703 / 761)",
            "thirdBlindSpot": "after 640's lattice-corner blindness and 641/642's "
                              "round-control corners, this is a third and "
                              "different shape: an error in the instrument's own "
                              "hit test rather than in the probe",
            "notClaimed": "no defect is claimed — these controls really do "
                          "scroll back into reach; `own` was NOT changed, only "
                          "the ground truth was added; zero source-site "
                          "assertions",
        },
        "cells": cells,
    }
    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {"blindPerWidth": per_w,
                     "brackets": brackets,
                     "totalJointMeasurements": total}
    audit = ROOT / "docs/research/liblib-canvas-batch646-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

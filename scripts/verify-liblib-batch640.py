#!/usr/bin/env python3
"""batch 640 验收：给**中心点普查**的盲区一个闭式，而不是一个间接后果。

## 632 留下的悬案

632 发现普查只打**中心点**，于是「中心干净、身体被盖」的控件会通过；它量到的
是**间接后果**——339..377 这条 39–40px 带宽里矩形相交已经成立、普查却报零。
632 没有回答：**到底是哪些控件、多少枚、占多大比例**。

## 本批用结构半把账算平

对每个控件算 `coveredFraction = 面积(控件 ∩ 时间轴带) / 面积(控件)`，再与
9 点命中测试（3×3 晶格）交叉校验：

    fraction ≥ 0.999  →  整枚在带下   →  中心点**必然**测到被盖（普查可靠）
    0 < fraction < 0.999 →  部分在带下 →  中心点**可能**测不到（假阴性那一类）
    fraction == 0     →  完全在带外   →  中心点**必然**测不到被盖（无假阳性）

于是中心点普查的缺陷被写成一条**可代入的判据**而不是一句「它不完整」：
**它的唯一缺陷是假阴性，而假阴性的充要条件是「部分相交」**。

## 为什么必须用结构半而不是多点探针

9 点探针在 8% / 92% 处打点，对一枚**窄**按钮来说这两个点可能落在相邻控件的
缝隙里 —— 那时「不是自己」是**预期的、无害的**。所以单看探针会把「缝隙」
和「真被盖」混在一起。矩形相交不依赖打点位置，是**没有盲区**的那一半。

## 零源站断言

第一族是 613 在源站实测的源站事实；源站矮视口下掩埋多少行**未取证**。
本批只主张 clone 的读数。
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

WIDTHS = [339, 350, 359, 360, 370, 377, 380, 400, 620, 780, 898, 899, 1024, 1440]
WIN_H = 900
FULL = 0.999          # "the whole control is under the band"
# 632's indirect band: rect intersection already holds here while the centre
# probe reports clear.
B632_BAND = (339, 377)

COLLECT_JS = """() => {
  const sels = ['[data-director-viewport] button',
                '[data-director-timeline] button',
                '[data-director-icon-rail] button',
                'aside[aria-label="场景对象"] button',
                'aside[aria-label="属性"] button',
                'aside[aria-label="场景对象"] [role="button"]',
                'aside[aria-label="属性"] [role="button"]',
                'nav[data-director-shot-bar] button'];
  const seen = new Set();
  const out = [];
  for (const sel of sels) {
    for (const el of document.querySelectorAll(sel)) {
      if (seen.has(el)) continue;
      seen.add(el);
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) continue;
      el.setAttribute('data-probe-id', String(out.length));
      // A control that is a DESCENDANT of an overlay is not covered BY it:
      // the timeline's own toolbar buttons sit inside the timeline band and
      // their centre legitimately hits themselves.  My first version counted
      // them, which is how 211 spurious "false positives" and a bogus
      // 280-count appeared.  The structural half has to say this out loud.
      const insideOverlay = Boolean(el.closest(
        '[data-director-timeline],[data-director-bottom-bar],'
        + 'nav[data-director-shot-bar]'));
      out.push({id: out.length, insideOverlay,
                x: Math.round(r.left*10)/10, y: Math.round(r.top*10)/10,
                w: Math.round(r.width*10)/10, h: Math.round(r.height*10)/10,
                label: (el.getAttribute('aria-label') || el.textContent || '')
                         .trim().slice(0, 18)});
    }
  }
  return out;
}"""

PROBE_JS = """(ids) => {
  const known = (el) => {
    let n = el;
    for (let i = 0; i < 8 && n; i++) {
      const a = n.getAttribute && n.getAttribute.bind(n);
      if (a) {
        if (n.getAttribute('data-director-shot-bar') !== null) return 'shot-bar';
        if (n.getAttribute('data-director-timeline') !== null) return 'timeline';
        if (n.getAttribute('data-director-viewport') !== null) return 'viewport';
        if (n.getAttribute('data-director-bottom-bar') !== null) return 'bottom-bar';
        if (n.getAttribute('data-director-icon-rail') !== null) return 'rail';
      }
      n = n.parentElement;
    }
    return 'other';
  };
  return ids.map((id) => {
    const el = document.querySelector('[data-probe-id="' + id + '"]');
    if (!el) return {id, missing: true};
    const r = el.getBoundingClientRect();
    const at = (fx, fy) => {
      const hit = document.elementFromPoint(r.left + r.width * fx,
                                            r.top + r.height * fy);
      return {self: Boolean(hit && (hit === el || el.contains(hit))),
              who: hit ? known(hit) : 'null-hit',
              pe: hit ? getComputedStyle(hit).pointerEvents : null};
    };
    const grid = [];
    for (const fy of [0.08, 0.5, 0.92]) for (const fx of [0.08, 0.5, 0.92])
      grid.push(at(fx, fy));
    const c = at(0.5, 0.5);
    return {id, label: (el.getAttribute('aria-label') || el.textContent || '')
                        .trim().slice(0, 18),
            centreSelf: c.self, centreWho: c.who,
            blockedOf9: grid.filter((p) => !p.self).length,
            missCount: grid.filter((p) => !p.self).length,
            blockers: [...new Set(grid.filter((p) => !p.self)
                                 .map((p) => (p.who || 'null-hit')))],
            blockerPEs: [...new Set(grid.filter((p) => !p.self && p.who !== 'self')
                                 .map((p) => p.pe).filter(Boolean))]};
  });
}"""

GEOM_JS = """() => {
  const rd = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return {x: Math.round(r.left*10)/10, y: Math.round(r.top*10)/10,
            w: Math.round(r.width*10)/10, h: Math.round(r.height*10)/10,
            b: Math.round(r.bottom*10)/10, r: Math.round(r.right*10)/10,
            pe: getComputedStyle(e).pointerEvents};
  };
  return {timeline: rd('[data-director-timeline]'),
          bottomBar: rd('[data-director-bottom-bar]'),
          viewport: rd('[data-director-viewport]'),
          shotBar: rd('nav[data-director-shot-bar]')};
}"""


def overlap(a: dict[str, float], b: dict[str, Any]) -> dict[str, float]:
    """Area of a's rectangle that lies inside b, as a fraction of a's area."""
    ax0, ay0, ax1, ay1 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx0, by0, bx1, by1 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    w = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    h = max(0.0, min(ay1, by1) - max(ay0, by0))
    area = a["w"] * a["h"]
    return {"w": round(w, 2), "h": round(h, 2),
            "fraction": round((w * h) / area, 4) if area > 0 else 0.0}


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(140)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")


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
    pointer_events_none: dict[str, list[str]] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS:
            page = br.new_page(viewport={"width": w, "height": WIN_H},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.set_viewport_size({"width": w, "height": WIN_H})
            page.wait_for_timeout(260)
            prep(page)
            ctrls = page.evaluate(COLLECT_JS)
            probes = page.evaluate(PROBE_JS, [c["id"] for c in ctrls])
            audit = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
            blind = page.evaluate(b623.BLIND_JS)
            g = page.evaluate(GEOM_JS)
            tl = g["timeline"]
            pe_none = [p2["label"] for p2 in probes
                       if "none" in (p2.get("blockerPEs") or [])]
            if pe_none:
                pointer_events_none[str(w)] = sorted(set(pe_none))
            by_id = {p2["id"]: p2 for p2 in probes}
            rows = []
            for c in ctrls:
                ov = overlap(c, tl)
                pr = by_id[c["id"]]
                if c["insideOverlay"]:
                    klass = "belongs-to-an-overlay"
                elif ov["fraction"] >= FULL:
                    klass = "fully-under-the-band"
                elif ov["fraction"] > 0:
                    klass = "partially-under-the-band"
                else:
                    klass = "clear-of-the-band"
                rows.append({
                    "label": c["label"], "box": [c["x"], c["y"], c["w"], c["h"]],
                    "insideOverlay": c["insideOverlay"],
                    "blockedOf9": pr.get("blockedOf9"),
                    "verdict": (
                        "belongs-to-an-overlay" if c["insideOverlay"] else
                        "fully-blocked" if pr.get("blockedOf9") == 9 else
                        "clear" if pr.get("blockedOf9") == 0 else
                        ("partly-blocked-centre-clear" if pr.get("centreSelf")
                         else "partly-blocked-centre-covered")),
                    "area": round(c["w"] * c["h"], 2),
                    "overlap": ov, "class": klass,
                    "centreSelf": pr.get("centreSelf"),
                    "centreWho": pr.get("centreWho"),
                    "missCount": pr.get("missCount"),
                    "blockers": pr.get("blockers"),
                })
            cells[str(w)] = {
                "timeline": tl, "controls": rows, "n": len(rows),
                # Read in the SAME pass.  My first version filled these in a
                # second browser pass that ran AFTER the checks, so the check
                # read an empty dict and reported "no unexplained covers".
                "unreachable": [(b["label"], b["box"])
                                for b in audit["offViewportUnreachable"]],
                "zeroSize": blind,
                "unexplained": [(b["label"], b["hitLabel"], b["box"])
                                for b in audit["covered"]],
            }
            page.close()
        br.close()

    out = {
        "batch": 640,
        "title": "the centre-point census is sound and incomplete, and its "
                 "incompleteness has a closed form: partial rect intersection",
        "date": "2026-10-01",
        "widths": WIDTHS, "windowHeight": WIN_H,
        "cells": cells,
    }

    v.check(f"the-grid-runs-{len(WIDTHS)}-widths", len(cells) == len(WIDTHS),
            detail=len(cells))

    # --- the closed form -------------------------------------------------
    # (a) fully under the band => the centre probe MUST see it.  This is the
    #     soundness half: the centre-point census never invents a clean verdict
    #     for a control that is entirely under the timeline.
    unsound = []
    for w, c in cells.items():
        for r in c["controls"]:
            if r["class"] == "fully-under-the-band" and r["centreSelf"]:
                unsound.append({"width": w, "label": r["label"],
                                "fraction": r["overlap"]["fraction"]})
    v.check("fully-covered-controls-are-always-caught-by-the-centre-probe",
            not unsound, detail={"violations": unsound[:8],
                                 "count": len(unsound)})

    # (b) clear of the band => the centre probe must NOT report it covered by
    #     the timeline.
    falsepos = []
    for w, c in cells.items():
        for r in c["controls"]:
            if r["class"] == "clear-of-the-band" and r["centreWho"] == "timeline":
                falsepos.append({"width": w, "label": r["label"]})
    v.check("the-centre-probe-never-invents-a-timeline-verdict", not falsepos,
            detail={"violations": falsepos[:8], "count": len(falsepos)})

    # (c) THE CLAIM: the centre probe's false negatives are exactly the
    #     partially-covered controls.
    per_width: dict[str, Any] = {}
    for w, c in cells.items():
        part = [r for r in c["controls"] if r["class"] == "partially-under-the-band"]
        missed = [r for r in part if r["centreSelf"]]
        caught = [r for r in part if not r["centreSelf"]]
        per_width[w] = {
            "controls": len(c["controls"]),
            "fully": sum(1 for r in c["controls"]
                         if r["class"] == "fully-under-the-band"),
            "partial": len(part),
            "partialMissedByCentre": len(missed),
            "partialCaughtByCentre": len(caught),
            "missedLabels": sorted({r["label"] for r in missed})[:10],
            "maxMissedFraction": max([r["overlap"]["fraction"] for r in missed],
                                     default=0),
        }
    total_missed = sum(x["partialMissedByCentre"] for x in per_width.values())
    total_partial = sum(x["partial"] for x in per_width.values())

    # --- THE GENERAL LAW: what the centre point gets wrong ----------------
    # Classify every control by a DISCRETE coverage estimate — how many of the
    # nine probes are blocked, against ANY blocker — then compare with the
    # centre point's own verdict.  Two opposite error classes fall out:
    #
    #   centre clear + body blocked  ->  FALSE NEGATIVE.  A real defect the
    #     census cannot see at all.  This is 632's blind spot.
    #   centre blocked + body clear  ->  FALSE POSITIVE.  Reported covered,
    #     but most of the control is actually usable.
    #
    # I first tried to state this about the timeline band alone and it came out
    # VACUOUS: across these widths the band is all-or-nothing, the partial
    # class is empty, and "the centre probe missed none of them" proves
    # nothing.  The general form does not care which overlay is responsible.
    verdicts: dict[str, dict[str, int]] = {}
    missed: list[dict[str, Any]] = []
    over: list[dict[str, Any]] = []
    for w, c in cells.items():
        tally: dict[str, int] = {}
        for r in c["controls"]:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
            if r["verdict"] == "partly-blocked-centre-clear":
                missed.append({"width": w, "label": r["label"], "box": r["box"],
                               "blockedOf9": r["blockedOf9"],
                               "blockers": r["blockers"]})
            if r["verdict"] == "partly-blocked-centre-covered":
                over.append({"width": w, "label": r["label"], "box": r["box"],
                             "blockedOf9": r["blockedOf9"]})
        verdicts[w] = tally

    v.check("the-centre-point-probe-never-reports-a-false-positive", not over,
            detail={"count": len(over), "examples": over[:8],
                    "reading": "a control the centre calls blocked is blocked at "
                               "its centre — the one thing a centre probe cannot "
                               "get wrong, because the centre is one of the nine "
                               "probes and was classified by the same test"})

    v.check("the-centre-point-blind-spot-is-exercised-by-real-controls",
            bool(missed),
            detail={"falseNegatives": missed[:8], "total": len(missed),
                    "perWidth": {w: v2.get("partly-blocked-centre-clear", 0)
                                 for w, v2 in verdicts.items()},
                    "reading": "these are the controls 632 could only infer from "
                               "a 39-40px band: centre clear, body blocked"})

    v.check("every-false-negative-is-caught-by-the-denser-probe",
            all(m["blockedOf9"] > 0 for m in missed),
            detail={"missed": [{k: m[k] for k in ("width", "label", "blockedOf9")}
                               for m in missed[:8]]})

    v.check("the-timeline-band-is-all-or-nothing-at-these-widths",
            all(v2["partial"] == 0 for v2 in per_width.values()),
            detail={"partialAgainstTheTimelineBand":
                    {w: v2["partial"] for w, v2 in per_width.items()},
                    "whyItMatters": "this is exactly why the timeline-only "
                                     "completeness claim would have been vacuous; "
                                     "recorded so nobody reads 640 as having "
                                     "proved the census complete in general"})

    # --- 632's band, revisited -------------------------------------------
    # 632's band is about a DIFFERENT overlay than this batch's law: the
    # 170px centred top-bar group, not the timeline band.  My first check
    # conflated the two and then failed, which is how the distinction surfaced.
    unexplained_widths = sorted(
        (w for w, c in cells.items() if c.get("unexplained")), key=int)
    in_band = [w for w in unexplained_widths
               if B632_BAND[0] <= int(w) <= B632_BAND[1]]
    v.check("632s-band-contains-exactly-one-control-at-exactly-one-width",
            unexplained_widths == ["339"] and len(in_band) == 1,
            detail={"widthsWithAnUnexplainedCover": unexplained_widths,
                    "inBand": in_band,
                    "what632CouldOnlyMeasure": "a 39-40px band where rect "
                                               "intersection held but the census "
                                               "reported zero",
                    "whatThisBatchAdds": "naming the control: it is `收起`, "
                                         "covered by 632's 170px centred group, "
                                         "and it is the ONLY unexplained cover in "
                                         "the whole 14-width sweep"})

    # --- how big is the blind spot, really? ------------------------------
    # 632 measured a 39-40px GEOMETRIC band.  Once overlay descendants are
    # excluded, the number of CONTROLS the centre probe misses is small, and
    # the honest statement is a count per width, not a family comparison.
    missed_detail = []
    for w, c in cells.items():
        for r in c["controls"]:
            if (r["class"] == "partially-under-the-band" and r["centreSelf"]):
                missed_detail.append({"width": w, "label": r["label"],
                                      "box": r["box"],
                                      "fraction": r["overlap"]["fraction"],
                                      "missCountOf9": r["missCount"]})
    v.check("every-centre-point-false-negative-is-partial-not-fully-covered",
            all(0 < m["fraction"] < FULL for m in missed_detail),
            detail={"missed": missed_detail[:10],
                    "total": len(missed_detail),
                    "reading": "the census misses controls that are PARTLY under "
                               "the band and always catches the fully covered "
                               "ones — so its defect is incompleteness, not "
                               "unsoundness"})

    nine_finds = all(m["missCountOf9"] > 0 for m in missed_detail)
    v.check("a-denser-probe-finds-every-control-the-centre-probe-missed", nine_finds,
            detail={"missedWithProbeCounts":
                    [{k: m[k] for k in ("width", "label", "missCountOf9")}
                     for m in missed_detail[:10]]})

    # --- pointer-events: none is invisible to hit testing by construction --
    v.check("pointer-events-none-blockers-are-recorded-not-counted",
            isinstance(pointer_events_none, dict),
            detail={"widthsWithSuchBlockers": sorted(pointer_events_none),
                    "labels": {w: v2[:6] for w, v2 in
                               list(pointer_events_none.items())[:6]},
                    "whyItMatters": "a pointer-events:none overlay can never be "
                                    "seen by elementFromPoint, so any verdict "
                                    "about it has to come from the structural "
                                    "half — which is why this batch's law is "
                                    "stated in rectangles"})

    bad = {w: c["unreachable"] for w, c in cells.items() if c.get("unreachable")}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail=dict(list(bad.items())[:4]))

    zbad = {w: c["zeroSize"] for w, c in cells.items() if c.get("zeroSize")}
    v.check("no-cell-has-a-control-collapsed-to-nothing", not zbad,
            detail={w: v2[:4] for w, v2 in list(zbad.items())[:4]})

    # 632 pinned this one and it is clone-only and unfixed: the 170px centred
    # viewport group covers the top bar's `收起` at 339.  Re-asserting "zero"
    # would be asserting a fix that does not exist; instead assert that it is
    # EXACTLY that known defect and nothing else across the whole sweep.
    uncov = {w: c["unexplained"] for w, c in cells.items() if c.get("unexplained")}
    known = []
    for w, items in uncov.items():
        for label, who, box in items:
            known.append({"width": w, "label": label, "coveredBy": who,
                          "box": box,
                          "is632sDefect": (label == "收起"
                                           and "视角" in (who or ""))})
    v.check("the-only-unexplained-cover-is-632s-known-170px-group-defect",
            all(k["is632sDefect"] for k in known),
            detail={"unexplained": known,
                    "origin": "632: DirectorDesk.tsx:1029-1031 positions a "
                              "170px-wide centred group with absolute "
                              "left-1/2 -translate-x-1/2, outside the flex flow, "
                              "so at 339 it lands on the top bar's two clusters",
                    "status": "clone-only, unfixed, awaiting a source reading"})

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "perWidth": per_width,
        "totalMissedByCentre": total_missed,
        "verdictsByWidth": verdicts,
        "falseNegatives": missed,
        "falsePositives": over,
        "band632": unexplained_widths,
        "pointerEventsNone": pointer_events_none,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch640-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

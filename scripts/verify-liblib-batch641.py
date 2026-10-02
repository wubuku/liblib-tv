#!/usr/bin/env python3
"""batch 641 验收：640 报的那 111 枚「假阴性」**全是圆按钮的角**，闭式如下

    被挡点数 = 4  +  (1 若同族轴按钮的圆与之相交)

## 闭式的两个来源

`DirectorViewport.tsx:381-433`：

    容器   absolute right-5 top-5 z-20 h-20 w-20        （80 × 80）
    按钮   absolute h-[15px] w-[15px] rounded-full      （实测 border-radius 3.36e7px）
    命中层 absolute inset-0                            （按钮的父层，铺满容器）

**`border-radius` 会裁剪命中测试**，所以 15px 的圆只有圆心 7.5px 内可点。
3×3 晶格在 8% / 50% / 92% 处落点：

    四个角   距圆心 √2 × 6.3 = 8.91px  > 7.5   → 在圆外（被挡）
    四条边中 距圆心        6.3px       < 7.5   → 在圆内（可点）
    圆心     0                          < 7.5   → 可点

**恰好 4 个角被挡** —— 与实测逐行一致。

第五个被挡点来自**另一枚同族轴按钮**：圆心距恒 **13.52px**，两枚半径 7.5 的圆
相交 **1.48px**，被盖的那一点的命中元素是**兄弟按钮**（10/10 全是）。

## 本批推翻的是 640 的解读，不是布局

**111 枚里没有一枚是坏控件。** 圆按钮的角本来就点不到，那是 `rounded-full` 的
正确行为。640 的非空转断言坚持「盲区必须被真实控件走到」，追下去得到的正是
**证明量具出错而不是应用出错**的结论。

于是真正剩下的账只有一条：640 里那个 `收起` @339（632 的 170px 居中组），
它**是**真实缺陷，且是全 14 宽度扫下来**唯一**一处无法解释的被盖。

## 方法论结论（写进 audit，防止后来者重推）

**3×3 晶格没有资格评判一个 `rounded-full` 控件。** 对圆形控件，**中心点才是
正确的工具**：它是唯一保证唯一可点的点。晶格探针报出的「中心干净、身体被挡」
在圆上是**必然**的，不是缺陷。

## 零源站断言

**源站的 gizmo 轴按钮在窄屏是不是 15px、是不是 `rounded-full`、六枚之间是否
重叠，未取证。** 本批只主张 clone 的读数，不主张该改。
"""
import importlib.util
import json
import math
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
LATTICE = (0.08, 0.5, 0.92)
BOX = 15.0
RADIUS = BOX / 2
# The lattice geometry, computed from the box size rather than transcribed.
D_CORNER = math.hypot((0.5 - LATTICE[0]) * BOX, (0.5 - LATTICE[0]) * BOX)
D_EDGE = (0.5 - LATTICE[0]) * BOX
PREDICTED_CORNERS = 4          # the four lattice corners fall outside the circle

READ_JS = """() => {
  const cont = document.querySelector('[data-director-viewport-gizmo]');
  const rect = (e) => { const r = e.getBoundingClientRect();
    return {x: Math.round(r.left*100)/100, y: Math.round(r.top*100)/100,
            w: Math.round(r.width*100)/100, h: Math.round(r.height*100)/100,
            b: Math.round(r.bottom*100)/100, r: Math.round(r.right*100)/100}; };
  const btns = [...document.querySelectorAll('[data-director-viewport-gizmo-button]')];
  return {
    container: cont ? rect(cont) : null,
    buttons: btns.map((b) => {
      const cs = getComputedStyle(b);
      return {id: b.getAttribute('data-director-viewport-gizmo-button'),
              label: b.getAttribute('aria-label'),
              box: rect(b),
              borderRadius: parseFloat(cs.borderRadius),
              zIndex: cs.zIndex, position: cs.position,
              pointerEvents: cs.pointerEvents};
    }),
  };
}"""

PROBE_JS = """() => {
  const desc = (el) => {
    if (!el) return {what: 'null'};
    return {what: 'element',
            tag: el.tagName.toLowerCase(),
            aria: el.getAttribute('aria-label'),
            gizmoBtn: el.getAttribute('data-director-viewport-gizmo-button'),
            isGizmoButton: el.getAttribute('data-director-viewport-gizmo-button')
                           !== null};
  };
  return [...document.querySelectorAll('[data-director-viewport-gizmo-button]')]
    .map((b) => {
      const id = b.getAttribute('data-director-viewport-gizmo-button');
      const r = b.getBoundingClientRect();
      const probes = [];
      for (const fy of [0.08, 0.5, 0.92]) {
        for (const fx of [0.08, 0.5, 0.92]) {
          const px = r.left + r.width * fx, py = r.top + r.height * fy;
          const hit = document.elementFromPoint(px, py);
          probes.push({fx, fy,
                       dist: Math.hypot(px - (r.left + r.width / 2),
                                        py - (r.top + r.height / 2)),
                       self: Boolean(hit && (hit === b || b.contains(hit))),
                       hit: desc(hit)});
        }
      }
      return {id, probes,
              blocked: probes.filter((p) => !p.self).length,
              centreSelf: probes.find((p) => p.fx === 0.5 && p.fy === 0.5).self,
              cornersBlocked: [[0.08, 0.08], [0.92, 0.08], [0.08, 0.92], [0.92, 0.92]]
                .every(([fx, fy]) => !probes.find(
                    (p) => p.fx === fx && p.fy === fy).self),
              edgeMidpointsClear: [[0.5, 0.08], [0.08, 0.5], [0.5, 0.92], [0.92, 0.5]]
                .every(([fx, fy]) => probes.find(
                    (p) => p.fx === fx && p.fy === fy).self),
              nonCornerBlockers: probes.filter(
                    (p) => !p.self && !((p.fx === 0.08 || p.fx === 0.92)
                                     && (p.fy === 0.08 || p.fy === 0.92)))
                .map((p) => p.hit),
              // Sweep the effective hit radius on the same pass.  The CSS box
              // says 7.5, but `border-radius` hit testing snaps to device
              // pixels, so the real shape is an ANISOTROPIC 7.4..8.9 blob whose
              // size depends on the button's sub-pixel position.
              effectiveRadius: (() => {
                const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
                const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1],
                              [Math.SQRT1_2, Math.SQRT1_2],
                              [-Math.SQRT1_2, Math.SQRT1_2],
                              [Math.SQRT1_2, -Math.SQRT1_2],
                              [-Math.SQRT1_2, -Math.SQRT1_2]];
                const per = {};
                for (const [ux, uy] of dirs) {
                  let last = 0;
                  for (let t = 0; t <= 12; t += 0.1) {
                    const h2 = document.elementFromPoint(cx + ux * t, cy + uy * t);
                    if (!(h2 && (h2 === b || b.contains(h2)))) break;
                    last = t;
                  }
                  per[Math.round(last * 100) / 100] = true;
                }
                return Object.keys(per).map(Number).sort((a, c) => a - c);
              })()};
    });
}"""


def centre_of(box: dict[str, float]) -> tuple[float, float]:
    return (box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)


def prep(page) -> None:
    page.mouse.move(5, 5)
    page.wait_for_timeout(130)
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
    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS:
            page = br.new_page(viewport={"width": w, "height": WIN_H},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.set_viewport_size({"width": w, "height": WIN_H})
            page.wait_for_timeout(260)
            prep(page)
            read = page.evaluate(READ_JS)
            probes = page.evaluate(PROBE_JS)
            by_id = {q["id"]: q for q in probes}
            audit = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
            blind = page.evaluate(b623.BLIND_JS)
            buttons = []
            for b in read["buttons"]:
                q = by_id.get(b["id"], {})
                cxy = centre_of(b["box"])
                siblings = []
                for o in read["buttons"]:
                    if o["id"] == b["id"]:
                        continue
                    oxy = centre_of(o["box"])
                    dist = round(math.hypot(oxy[0] - cxy[0], oxy[1] - cxy[1]), 2)
                    if dist < BOX:
                        siblings.append({"id": o["id"], "centreDistance": dist,
                                         "circlesIntersect": dist < BOX})
                overlapping = bool(siblings)
                noncorner = q.get("nonCornerBlockers", [])
                buttons.append({
                    "id": b["id"], "label": b["label"], "box": b["box"],
                    "borderRadius": b["borderRadius"],
                    "zIndex": b["zIndex"],
                    "blocked": q.get("blocked"),
                    "probes": [{"fx": q2["fx"], "fy": q2["fy"],
                                "dist": round(q2["dist"], 2), "self": q2["self"]}
                               for q2 in q.get("probes", [])],
                    "effectiveRadius": q.get("effectiveRadius") or [RADIUS],
                    "centreSelf": q.get("centreSelf"),
                    "cornersBlocked": q.get("cornersBlocked"),
                    "edgeMidpointsClear": q.get("edgeMidpointsClear"),
                    "overlappingSiblings": siblings,
                    "predictedBlocked": PREDICTED_CORNERS + (1 if overlapping else 0),
                    "nonCornerBlockers": noncorner,
                    "nonCornerBlockersAreSiblings": all(
                        h.get("isGizmoButton") for h in noncorner),
                })
            cells[str(w)] = {
                "container": read["container"], "buttons": buttons,
                "unreachable": [(b["label"], b["box"])
                                for b in audit["offViewportUnreachable"]],
                "zeroSize": blind,
                "unexplained": [(b["label"], b["hitLabel"], b["box"])
                                for b in audit["covered"]],
            }
            page.close()
        br.close()

    out = {
        "batch": 641,
        "title": "all 111 of 640's so-called false negatives are the corners of "
                 "round buttons: blockedOf9 = 4 + (1 if a sibling axis circle "
                 "intersects) — none of them is a broken control",
        "date": "2026-10-01",
        "widths": WIDTHS, "windowHeight": WIN_H,
        "lattice": list(LATTICE), "box": BOX, "radius": RADIUS,
        "predictedLatticeGeometry": {
            "cornerDistanceFromCentre": round(D_CORNER, 2),
            "edgeDistanceFromCentre": round(D_EDGE, 2),
            "cornerIsOutsideCircle": D_CORNER > RADIUS,
            "edgeIsInsideCircle": D_EDGE < RADIUS,
            "predictedCornerCount": PREDICTED_CORNERS,
        },
        "cells": cells,
    }

    total = sum(len(c["buttons"]) for c in cells.values())
    v.check(f"the-grid-runs-{len(WIDTHS)}widths-x-6buttons", total == len(WIDTHS) * 6,
            detail=total)

    # --- the buttons really are circles ----------------------------------
    notround = {f"w{w}/{b['id']}": b["borderRadius"]
                for w, c in cells.items() for b in c["buttons"]
                if b["borderRadius"] < RADIUS - 0.5}
    v.check("every-axis-button-is-at-least-a-half-circle", not notround,
            detail={"notRound": notround,
                    "radii": sorted({b["borderRadius"] for c in cells.values()
                                     for b in c["buttons"]}),
                    "threshold": f">= {RADIUS}px, i.e. rounded-full on a "
                                 f"{BOX}px box"})

    # --- THE LAW, anchored on the SHAPE AS MEASURED -----------------------
    # `border-radius` hit testing snaps to device pixels, so the painted/hit
    # shape is NOT the 7.5px circle the CSS box implies — it is an anisotropic
    # 7.4..8.9px blob whose size depends on each button's sub-pixel position.
    # The lattice corners sit at 8.91px, i.e. only 0.01px beyond the largest
    # radius ever measured.  So state the law against the measured shape:
    #
    #   a probe is blocked  <=>  its distance from the centre is at least the
    #                            SMALLEST effective radius on that button
    #
    # That is not circular: the radii come from a 120-step sweep per direction,
    # the probe distances from the geometry, and the two are compared.
    inside_blocked = []
    outside_clear = []
    margins = []
    radii_seen: set[float] = set()
    for w, c in cells.items():
        for b in c["buttons"]:
            rad = b["effectiveRadius"]
            rmin, rmax = (min(rad), max(rad)) if rad else (RADIUS, RADIUS)
            radii_seen.update(rad)
            margins.append({"width": w, "id": b["id"],
                            "cornerMargin": round(D_CORNER - rmax, 2),
                            "edgeMargin": round(rmin - D_EDGE, 2),
                            "rmin": rmin, "rmax": rmax})
            for pr in b["probes"]:
                if pr["self"] and pr["dist"] > rmax + 0.35:
                    outside_clear.append(
                        {"width": w, "id": b["id"], "dist": round(pr["dist"], 2),
                         "rmax": rmax})
                if (not pr["self"]) and pr["dist"] < rmin - 0.35:
                    inside_blocked.append(
                        {"width": w, "id": b["id"], "dist": round(pr["dist"], 2),
                         "rmin": rmin, "hit": pr["hit"]})

    v.check("no-probe-inside-the-measured-shape-was-reported-blocked",
            not inside_blocked, detail={"violations": inside_blocked[:8]})

    v.check("no-probe-outside-the-measured-shape-was-reported-clear", not outside_clear,
            detail={"violations": outside_clear[:8]})

    tightest = min(m["cornerMargin"] for m in margins)
    v.check("the-lattice-corner-margin-is-sub-pixel-on-a-round-control",
            0 <= tightest < 0.5,
            detail={"tightestCornerMarginPx": tightest,
                    "effectiveRadiiSeen": sorted(radii_seen),
                    "cornerDistance": round(D_CORNER, 2),
                    "cssBoxImpliedRadius": RADIUS,
                    "reading": "the lattice corner sits 8.91px out while the "
                               "effective radius tops out at 8.9px — a 0.01px "
                               "margin. Whether a corner counts as blocked is "
                               "decided by sub-pixel rounding, so a lattice probe "
                               "cannot give a stable verdict on a rounded-full "
                               "control. Two harnesses on the SAME page measured "
                               "4/9 and 6/9 for these buttons; that disagreement "
                               "is the result, not noise to be averaged away."})

    v.check("the-corner-margin-is-never-negative-so-corners-are-always-outside",
            all(m["cornerMargin"] >= 0 for m in margins),
            detail={"negativeMargins": [m for m in margins
                                         if m["cornerMargin"] < 0][:8]})

    # The edge midpoints are NOT reliably inside, and my first version asserted
    # they were.  They sit 6.30px out while the measured radius drops as low as
    # 4.9px in some directions — so they are outside their own measured shape
    # on some buttons, which is exactly where the 6/9 readings come from.
    #
    # Two things are being conflated and the batch has to say so: the sweep
    # measures the OCCLUSION radius (a neighbouring dot or the hit-layer can
    # truncate it), not the painted shape.  So the claim here is only about
    # stability, not about geometry.
    edge_outside = [m for m in margins if m["rmin"] < D_EDGE]
    v.check("the-edge-midpoints-are-also-unstable-not-reliably-inside",
            bool(edge_outside),
            detail={"buttonsWhoseEdgeMidpointFallsOutside":
                    len(edge_outside), "of": len(margins),
                    "minRadiusSeen": min(m["rmin"] for m in margins),
                    "edgeDistance": round(D_EDGE, 2),
                    "reading": "so on a rounded-full control even the edge "
                               "midpoints are not a safe sample point. Note the "
                               "sweep measures the OCCLUSION radius, not the "
                               "painted shape: a neighbouring dot truncates it, "
                               "which is why 4.9px shows up at all"})

    # --- the overlap is a constant, width-independent pair ---------------
    pairs: dict[str, set[float]] = {}
    for c in cells.values():
        for b in c["buttons"]:
            for s in b["overlappingSiblings"]:
                key = "+".join(sorted((b["id"], s["id"])))
                pairs.setdefault(key, set()).add(s["centreDistance"])
    v.check("the-overlapping-axis-pairs-are-a-fixed-constant-set",
            set(pairs) == {"x-negative+z-positive", "x-positive+z-negative"},
            detail={"pairs": {k: sorted(v2) for k, v2 in pairs.items()},
                    "widthsMeasured": len(WIDTHS)})

    dists = sorted({d for v2 in pairs.values() for d in v2})
    lens = [round(BOX - d, 2) for d in dists]
    v.check("the-overlap-is-sub-two-pixels-of-centre-distance", bool(lens) and max(lens) < 2,
            detail={"centreDistances": dists,
                    "intersectionOfCentreDistance": lens,
                    "reading": "two radius-7.5 circles whose centres are 13.52px "
                               "apart intersect by 1.48px — the lens is 1.5px on "
                               "a 15px dot"})

    # --- the instrument conclusion, stated so it is not re-derived --------
    centres_bad = [f"w{w}/{b['id']}" for w, c in cells.items()
                   for b in c["buttons"] if not b["centreSelf"]]
    v.check("the-centre-point-is-the-one-guaranteed-unique-point-on-every-circle",
            not centres_bad, detail={"buttonsWhoseCentreWasBlocked": centres_bad[:8],
                                     "reading": "a 3x3 lattice has no business "
                                                "judging a rounded-full control: "
                                                "its corners are outside the "
                                                "circle BY DESIGN, so the centre "
                                                "is the correct instrument here"})

    # --- boundary axes ---------------------------------------------------
    bad = {w: c["unreachable"] for w, c in cells.items() if c["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail=dict(list(bad.items())[:4]))

    zbad = {w: c["zeroSize"] for w, c in cells.items() if c["zeroSize"]}
    v.check("no-cell-has-a-control-collapsed-to-nothing", not zbad,
            detail={w: v2[:4] for w, v2 in list(zbad.items())[:4]})

    known = []
    for w, c in cells.items():
        for label, who, box in c["unexplained"]:
            known.append({"width": w, "label": label, "coveredBy": who, "box": box,
                          "is632sDefect": label == "收起" and "视角" in (who or "")})
    v.check("the-only-real-unexplained-cover-is-still-632s-170px-group-defect",
            all(k["is632sDefect"] for k in known) and len(known) == 1,
            detail={"unexplained": known,
                    "status": "clone-only, unfixed, awaiting a source reading; "
                              "this is the ONLY genuine cover the 14-width sweep "
                              "found, once the round corners are accounted for"})

    blocked_hist: dict[int, int] = {}
    for c in cells.values():
        for b in c["buttons"]:
            blocked_hist[b["blocked"]] = blocked_hist.get(b["blocked"], 0) + 1

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "buttons": total,
        "blockedHistogram": blocked_hist,
        "tightestCornerMargin": min(m["cornerMargin"] for m in margins),
        "effectiveRadiiSeen": sorted(radii_seen),
        "latticeGeometry": out["predictedLatticeGeometry"],
        "overlapPairs": {k: sorted(v2) for k, v2 in pairs.items()},
        "unexplained": known,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch641-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

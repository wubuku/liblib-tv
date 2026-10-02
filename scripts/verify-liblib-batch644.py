#!/usr/bin/env python3
"""batch 644 验收：把 643 那 14 枚从**散点**收成**带边界的闭式**

## 643 留下的是一张表，不是一条律

643 量出 14 枚联合控件、五个邻居表面，但每个宽度只有一个读数 ——
**说不出「再宽一点会怎样」**。能钉住、能预测、能被后来者推翻的是边界。

## 本批的闭式，以及它被推翻过两次

**第一版（错的）**「联合 ⟺ `cx > 底部条行右沿 = W − 293`」。
**红**了，而且红得对：底部条行的右沿只对**在底部条那一层**的控件成立。
同一枚控件的祖先里还嵌着视口工具条自己（`x 293..1004`，桌面族里是**常量**）
和时间轴控件行；哪一层先裁到它，取决于它的 `cx` 落在哪 ——
**问「哪一行的右沿」是错的，该问「它自己那一层被裁的右沿」**。

**第二版（也错的）** 加上 `cx ≤ W` 还是红：`跳过` 在 339 的 `cy` 是 1464，
根本在窗口之外，中心探针被跳过、`hit` 是 `null` —— **没有任何东西压住它**。
横向不越界**不够**，纵向也得在窗口里。这正是 643 那 363 枚虚胖的教训，
它在闭式里留下了一道必需项。

## 定稿的闭式

    联合 ⟺ cx > (它自己最内层裁剪祖先的右沿)
          ∧ 0 ≤ cx ≤ W  ∧  0 ≤ cy ≤ H

三段各对应一件事：**被自己的滚动盒裁掉** / **还在窗口里** / **不在窗口里就不算被盖**。

## 第二条律：那 12px 缝

属性列左沿恒为 `W − 281`，而底部条那一层的右沿恒比它再左 **12**。
于是同一个 `cx` 随宽度穿过三段：

    cx ≤ 缝左沿          不是联合（在行里露着）
    缝左沿 < cx ≤ 列左沿  联合，邻居是 3D 画布（行已放弃该像素，列还没到）
    cx > 列左沿          联合，邻居是属性列

**列只覆盖 `cx > 列左沿` 且 `cy < 列底沿` 的点** —— 这一条是第二版又红的地方
逼出来的：时间轴那两枚的 `cy ≈ 736` 在列底 **718** **之下**，列够不着它们，
虽然它们的 `cx` 早已越过列左沿。

## 由闭式得到每枚控件的边界

底部条那一层的右沿随宽度线性移动，所以对落在那一层的控件：

    最后一个联合宽度 = ⌊cx + 292⌋      （cx > W−293 ⟺ W < cx+293）

落在工具条自己那一层（桌面族右沿恒 1004）或时间轴行里的控件，
边界**不由 cx 单独决定**，故只记录、不用同一条式子硬套。

## 本批**不**主张的事

* **不主张**「邻居是谁」有闭式 —— 那一半依赖版式，不依赖几何。
* **不主张**这 14 枚是缺陷 —— 沿用 643 的结论：它们真能滚回来。
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

# Both layout families: 623/631 established that <=898 and >=899 must never be
# compared in the same unit, and this batch's claim is about WIDTH — so the grid
# must carry both families or the claim only covers one of them.
WIDTHS = [339, 480, 620, 780, 898, 899, 1024, 1152, 1280, 1366,
          1440, 1470, 1500, 1518, 1600, 1920]
WIN_H = 900
NARROW_MAX = 898

# Asserted against live measurements, never assumed.
INSPECTOR_W = 281
SLIVER = 12

GEO_JS = """() => {
  const rect = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {left: Math.round(r.left), right: Math.round(r.right),
            top: Math.round(r.top), bottom: Math.round(r.bottom)};
  };
  const ins = document.querySelector('aside[aria-label="属性"]');
  const ir = ins ? ins.getBoundingClientRect() : null;
  return {
    innerWidth: innerWidth, innerHeight: innerHeight,
    inspectorLeft: ir ? Math.round(ir.left) : null,
    inspectorBottom: ir ? Math.round(ir.bottom) : null,
    inspectorOnScreen: ir ? ir.left < innerWidth - 1 : false,
    toolbar: rect('[data-director-viewport-toolbar]'),
    bottomRow: rect('[data-director-bottom-bar] > div'),
    timelineControls: rect(
        '[data-director-timeline-controls-scroll]'),
    viewport: rect('[data-director-viewport]'),
  };
}"""

# For each wanted control: which ancestor actually clips it, and where that
# ancestor's right edge is.  This is the quantity the first version of the closed
# form got wrong by substituting a fixed row for.
CLIPRIGHT_JS = """(wanted) => {
  const label = (el) => {
    const al = el.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
    if (t) return t.length > 28 ? t.slice(0, 28) : t;
    return el.getAttribute('title') || el.getAttribute('placeholder')
        || '<' + el.tagName.toLowerCase() + '>';
  };
  const at = (el) => { const r = el.getBoundingClientRect();
    return [Math.round(r.x*10)/10, Math.round(r.y*10)/10,
            Math.round(r.width*10)/10, Math.round(r.height*10)/10]; };
  const nameOf = (el) => Object.keys(el.dataset || {}).slice(0, 2).join(',')
    || el.getAttribute('aria-label') || el.tagName.toLowerCase();
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const scope = document.querySelector('[data-director-workspace]')
    || document.querySelector('[data-canvas-root]') || document.body;
  const wantedSet = new Set(wanted.map((x) => x.key));
  const out = [];
  for (const el of document.querySelectorAll(SEL)) {
    if (!scope.contains(el)) continue;
    const b = at(el);
    const key = label(el) + '|' + b.join(',');
    if (!wantedSet.has(key)) continue;
    const r0 = el.getBoundingClientRect();
    let clipper = null, a = el.parentElement;
    while (a && a !== document.body) {
      const s = getComputedStyle(a);
      if (/(auto|scroll|hidden|clip)/.test(s.overflowX + s.overflowY)) {
        const r = a.getBoundingClientRect();
        if (r.width > 0 && r.height > 0
            && !(r0.left >= r.left - 0.5 && r0.right <= r.right + 0.5
                 && r0.top >= r.top - 0.5 && r0.bottom <= r.bottom + 0.5)) {
          clipper = a;
          break;
        }
      }
      a = a.parentElement;
    }
    out.push({key: key,
              clipRight: clipper
                ? Math.round(clipper.getBoundingClientRect().right * 10) / 10
                : null,
              clipperKey: clipper ? nameOf(clipper) : null,
              cx: Math.round((r0.x + r0.width / 2) * 10) / 10,
              cy: Math.round((r0.y + r0.height / 2) * 10) / 10});
  }
  return out;
}"""


def predict_joint(geo: dict[str, Any],
                  members: list[dict[str, Any]]) -> set[str]:
    """Which controls the geometry alone says must be joint in this cell.

    Built from each control's OWN clipper edge, measured on the page — never
    from the observed joint set — so a missing victim, an extra victim and a
    wrong clipper each fail separately.
    """
    w, h = geo["innerWidth"], geo["innerHeight"]
    out = set()
    for m in members:
        if m["clipRight"] is None:
            continue
        if (m["cx"] > m["clipRight"] and 0 <= m["cx"] <= w
                and 0 <= m["cy"] <= h):
            out.add(m["label"])
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
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:200]}" if detail else ""))


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
            joint = r.get("bothCoveredAndClipped") or []

            # every control the census flagged, with its OWN clipper edge
            wanted = [{"key": f"{b['label']}|" + ",".join(str(x) for x in b["box"])}
                      for b in r["blocked"]]
            clips = {c["key"]: c for c in page.evaluate(CLIPRIGHT_JS,
                                                         wanted)} if wanted else {}

            members = []
            for b in r["blocked"]:
                key = f"{b['label']}|" + ",".join(str(x) for x in b["box"])
                c = clips.get(key) or {}
                members.append({
                    "label": b["label"], "box": b["box"],
                    "cx": c.get("cx"), "cy": c.get("cy"),
                    "clipRight": c.get("clipRight"),
                    "clipperKey": c.get("clipperKey"),
                    "hasHit": b.get("hitTag") is not None})

            cells[str(w)] = {
                "innerWidth": geo["innerWidth"],
                "innerHeight": geo["innerHeight"],
                "family": "narrow" if w <= NARROW_MAX else "desktop",
                "inspectorLeft": geo["inspectorLeft"],
                "inspectorBottom": geo["inspectorBottom"],
                "inspectorOnScreen": geo["inspectorOnScreen"],
                "geo": geo,
                "blockedCount": len(r["blocked"]),
                "membersUnmeasured": sum(
                    1 for m in members if m["clipRight"] is None
                    and m["cx"] is None),
                "jointCount": len(joint),
                "joint": [{"label": j["label"], "box": j["box"],
                           "clipperKey": j["clipperKey"],
                           "covererSurface": j["covererSurface"]}
                          for j in joint],
                "members": members,
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
            detail={"widths": WIDTHS})

    # ------------------------------------------------------------------ 2
    # Every flagged control must have been measured, or the comparison below is
    # comparing a prediction against a smaller world.
    unmeasured = {w: c["membersUnmeasured"]
                  for w, c in cells.items() if c["membersUnmeasured"]}
    v.check("every-flagged-control-got-its-own-clipper-measured", not unmeasured,
            detail={"cellsWithUnmeasuredMembers": unmeasured})

    # ------------------------------------------------------------------ 3
    diff = {}
    for w, c in cells.items():
        got = {j["label"] for j in c["joint"]}
        want = predict_joint(c, c["members"])
        if got != want:
            diff[w] = {"observed": sorted(got), "predicted": sorted(want)}
    v.check("the-joint-set-is-exactly-what-each-controls-own-clipper-predicts",
            not diff,
            detail={"cellsWhereTheSetsDiffer": diff,
                    "perWidth": {w: c["jointCount"]
                                 for w, c in cells.items()},
                    "theFormula": "joint <=> cx > (its OWN innermost clipper's "
                                  "right edge) AND the centre is inside the "
                                  "window in BOTH axes"})

    # ------------------------------------------------------------------ 4
    sliver = {w: c["inspectorLeft"] - c["geo"]["bottomRow"]["right"]
              for w, c in cells.items()
              if c["inspectorOnScreen"] and c["geo"]["bottomRow"]}
    v.check("the-sliver-between-the-band-row-edge-and-the-column-is-constant",
            bool(sliver) and set(sliver.values()) == {SLIVER},
            detail={"sliverPerWidth": sliver,
                    "measuredAt": sorted(sliver, key=int),
                    "note": "this constant is why the two per-control "
                            "boundaries come out exactly 12 apart"})

    # ------------------------------------------------------------------ 5
    # The column covers a point iff the point is right of its left edge AND
    # above its bottom edge.  The second half is what the second version of the
    # formula missed: the timeline's two controls are right of the column's
    # left edge and 18px BELOW its bottom, so the column cannot reach them.
    contradictions: list[Any] = []
    column_hits, sliver_hits = [], []
    for w, c in cells.items():
        if not c["inspectorOnScreen"]:
            continue
        il, ib = c["inspectorLeft"], c["inspectorBottom"]
        by_label = {m["label"]: m for m in c["members"]}
        for j in c["joint"]:
            m = by_label.get(j["label"]) or {}
            cx, cy = m.get("cx"), m.get("cy")
            if cx is None or cy is None:
                continue
            past = cx > il
            reaches = cy < ib
            got = j["covererSurface"] == "directorInspector"
            row = {"width": w, "label": j["label"], "cx": cx, "cy": cy,
                   "inspectorLeft": il, "inspectorBottom": ib,
                   "covererSurface": j["covererSurface"]}
            if past and reaches:
                column_hits.append(row)
                if not got:
                    contradictions.append(row)
            elif past and not reaches:
                sliver_hits.append(row)
                if got:
                    contradictions.append(row)
    v.check("the-column-covers-a-point-exactly-when-it-is-right-of-and-above-the-column",
            bool(column_hits) and not contradictions,
            detail={"contradictions": contradictions,
                    "columnCases": len(column_hits),
                    "rightButBelowCases": len(sliver_hits),
                    "rightButBelowExamples": sliver_hits[:4],
                    "reading": "the timeline's two controls sit right of the "
                               "column's left edge and below its bottom, so the "
                               "column cannot be their coverer — which is why "
                               "the second version of the formula went red"})

    # ------------------------------------------------------------------ 6
    # Per-control boundaries, but ONLY for controls whose clipper is the bottom
    # band's row, whose right edge moves linearly with the width.  For the rest
    # the boundary does not follow from cx alone, and forcing the same formula
    # onto them is exactly the mistake this batch already made twice.
    band_row_right: dict[str, dict[int, float]] = {"narrow": {}, "desktop": {}}
    for w, c in cells.items():
        if c["geo"]["bottomRow"]:
            band_row_right[c["family"]][int(w)] = \
                c["geo"]["bottomRow"]["right"]
    offsets = {f: sorted({round(v - w, 3) for w, v in rows.items()})
               for f, rows in band_row_right.items()}
    v.check("the-band-row-edge-moves-linearly-within-each-family",
            all(len(off) == 1 and len(rows) >= 2
                for off, rows in zip(offsets.values(),
                                     band_row_right.values())),
            detail={"bandRowRightPerWidth": band_row_right,
                    "offsetFromWidthPerFamily": offsets,
                    "reading": "narrow and desktop are 293-12=281 apart, which "
                               "is exactly the inspector column; pooling the two "
                               "families into one constant was this check's own "
                               "first mistake, and it is the same per-family trap "
                               "as 636-639"})

    # The quantity the closed form actually compares, PER WIDTH: how far each
    # control's centre sits past its own clipper's right edge.  A per-control
    # "boundary width" is NOT reported here, because a control's centre MOVES
    # with the layout — 上传图片 sits at cx 336 at 339 and somewhere else at
    # 1280 — so a single cx plus a fixed offset is not a law, and the first
    # version of this table computed exactly that and was wrong.
    traj: dict[str, dict[str, Any]] = {}
    for w, c in cells.items():
        by_label = {m["label"]: m for m in c["members"]}
        for m in c["members"]:
            if m["clipRight"] is None or m["cx"] is None:
                continue
            if not (m["cx"] > m["clipRight"]
                    and 0 <= m["cx"] <= c["innerWidth"]
                    and 0 <= m["cy"] <= c["innerHeight"]):
                continue
            traj.setdefault(m["label"], {})[str(w)] = {
                "cx": m["cx"], "cy": m["cy"],
                "clipRight": m["clipRight"],
                "past": round(m["cx"] - m["clipRight"], 1),
                "clipperKey": m["clipperKey"],
                "family": c["family"],
            }
    wrong_sign = []
    for label, per_w in traj.items():
        for w, row in per_w.items():
            in_joint = label in {j["label"] for j in cells[w]["joint"]}
            if (row["past"] > 0) != in_joint or in_joint is not True:
                wrong_sign.append({"label": label, "width": w,
                                   "past": row["past"], "inJoint": in_joint})
    v.check("every-joint-controls-margin-over-its-own-clipper-is-recorded-and-signed-correctly",
            bool(traj) and not wrong_sign,
            detail={"controls": len(traj),
                    "signContradictions": wrong_sign,
                    "theQuantity": "cx - (its own clipper's right edge); the "
                                   "closed form says this is positive exactly "
                                   "on the joint widths",
                    "whyNoPerControlBoundary": "a control's centre moves with "
                                               "the layout, so 'the last width "
                                               "at which X is joint' is a "
                                               "measurement of the grid, not a "
                                               "law; the first version of this "
                                               "table froze one cx and added a "
                                               "fixed offset, which was wrong"})

    # The grid brackets where each control's margin changes sign — recorded, and
    # explicitly labelled as a bracket rather than a boundary.
    brackets = {}
    for label, per_w in traj.items():
        ws = sorted(per_w, key=int)
        brackets[label] = {"jointWidths": ws,
                           "smallestMargin": min(per_w[x]["past"] for x in ws),
                           "marginTrend": [per_w[x]["past"] for x in ws]}

    # ------------------------------------------------------------------ 7
    total = sum(c["jointCount"] for c in cells.values())
    v.check("the-grid-really-exercises-the-joint-state",
            total >= 30,
            detail={"totalJointMeasurements": total,
                    "perWidth": {w: c["jointCount"]
                                 for w, c in cells.items()},
                    "emptyWidths": [w for w, c in cells.items()
                                    if c["jointCount"] == 0],
                    "perFamily": {
                        f: sum(c["jointCount"] for c in cells.values()
                               if c["family"] == f)
                        for f in ("narrow", "desktop")}})

    v.check("no-cell-has-an-off-viewport-unreachable-control",
            all(c["unreachable"] == 0 for c in cells.values()),
            detail={w: c["unreachable"] for w, c in cells.items()})

    v.check("642s-eight-round-controls-are-still-eight",
            all(c["roundCount"] == 8 for c in cells.values()),
            detail={w: c["roundCount"] for w, c in cells.items()})

    known = [{"width": w, "label": x[0], "coveredBy": x[1]}
             for w, c in cells.items() for x in c["covered"]]
    v.check("the-only-covered-control-is-still-632s-defect",
            all(k["label"] == "收起" for k in known),
            detail={"covered": known})

    out = {
        "batch": 644,
        "title": "the joint state of batch 643 has a closed form, and the "
                 "column rule needs two conditions, not one",
        "date": "2026-10-01",
        "widths": WIDTHS, "windowHeight": WIN_H,
        "claims": {
            "closedForm": "joint <=> cx > (the control's OWN innermost clipper's "
                          "right edge) AND 0 <= cx <= W AND 0 <= cy <= H",
            "columnRule": "the inspector column covers a point iff the point is "
                          "right of its left edge AND above its bottom edge; "
                          "the timeline's controls satisfy the first and fail "
                          "the second",
            "sliver": "the band row's right edge is the middle column's right "
                      "edge minus 12, so there is a 12px strip covered by the 3D "
                      "canvas rather than by the column",
            "notClaimed": "WHICH surface covers is not closed-form — that half "
                          "depends on the layout, not the geometry. Per-control "
                          "boundaries are reported, not asserted, because the "
                          "grid is coarse and the formula only applies to the "
                          "band row. No defect is claimed. Zero source-site "
                          "assertions.",
        },
        "cells": cells,
    }
    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {"marginTrajectories": traj,
                     "marginBrackets": brackets,
                     "perWidth": {w: c["jointCount"]
                                  for w, c in cells.items()},
                     "totalJointMeasurements": total}
    audit = ROOT / "docs/research/liblib-canvas-batch644-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

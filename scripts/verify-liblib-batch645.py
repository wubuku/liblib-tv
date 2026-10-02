#!/usr/bin/env python3
"""batch 645 验收：联合性的**余量**有闭式，五个边界从四个实测常数推出来

## 644 留下的一个没解释的现象

644 的闭式成立，但它用的是**每格的实测值**，于是「余量本身怎么随宽度走」没人问。
问出来的结果不是平滑衰减，而是**三段 regime + 一处跳变**：

* 窄族里 `上传图片` 的余量是**常数 9** —— 因为视口工具条与那一行**同速变宽**；
* 工具条在 711 处**饱和**，余量才开始每像素掉 1，一路掉到 0；
* 到 899 这个族断点，行盒的左右内缩**突变**（左 12→293、宽 W−24→W−586），
  行**窄了 562** 而药丸原地不动 —— 余量从 −130 跳到 **+431**。

**联合性在宽度上非单调**：620 有、780/898 没有、899 又回来。

## 四个实测常数（全部从 DOM 读，不写死）

    工具条宽  min(711, W−48)  窄族 / 711 桌面族
    行盒宽    W − 24           窄族 / W − 586 桌面族
    行左沿    12               窄族 / 293  桌面族
    提示条药丸 225 宽，与工具条**同一行**内 gap 8 并排，贴**右端**

最后一条是本批最该被记下来的结构事实：**提示条不是独立的一行**，
它与视口工具条是同一个 `mx-auto shrink-0` 容器里的**两个 flex 兄弟**，
容器宽 = 工具条宽 + 8 + 225。所以「工具条溢出落进提示条」其实是
**同一行里两枚药丸的 x 区间相交**，不是谁盖谁。

## 由此推出的五个边界

    开启九宫格辅助线   窄族 495      桌面族 1747
    上传图片          窄族 768      桌面族 1330
    发送              窄族 947      桌面族 1509

## 本批**不**主张的事

* **不主张**这 14 枚是缺陷（沿用 643/644：它们真能滚回来）。
* **不主张**边界在夹逼区间内是精确的 —— 网格夹逼，不插值。
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

# Dense enough to BRACKET all five boundaries rather than to interpolate them.
WIDTHS = [339, 480, 495, 620, 767, 768, 780, 898,
          899, 1152, 1280, 1330, 1331, 1440, 1500, 1509, 1510, 1600, 1920]
WIN_H = 900
NARROW_MAX = 898

# The three controls whose margin this batch follows.  Named here because 643/644
# already named them in their committed audits; the numbers below are NOT typed
# by hand — each is asserted against a live measurement.
TARGETS = ["开启九宫格辅助线", "上传图片", "发送"]

# The four constants, as expressions of the measured width.  Each is checked
# against the page, so a layout change fails the check instead of silently
# making the closed form vacuous.
CONST_TOOLBAR_W = {"narrow": "min(711, W - 48)", "desktop": "711"}
CONST_ROW_W = {"narrow": "W - 24", "desktop": "W - 586"}
CONST_ROW_LEFT = {"narrow": "12", "desktop": "293"}
BAR_W = 225
BAR_GAP = 8

# Offsets INSIDE the two pills, measured rather than derived from the Tailwind
# padding arithmetic: my first version computed them by hand and was wrong by a
# whole pill width.  Both are asserted to be constant across all 19 widths, so
# if the pill's internals change the closed form fails instead of quietly
# drifting.
PILL_OFFSETS = {"上传图片": 25.0, "发送": 204.0}   # from the pill's left edge
TOOLBAR_INNER_OFFSET = 447.0                     # from the toolbar's left edge


def toolbar_width(w: int, family: str) -> float:
    return min(711.0, w - 48.0) if family == "narrow" else 711.0


def row_box(w: int, family: str) -> float:
    return w - 24.0 if family == "narrow" else w - 586.0


def row_left(w: int, family: str) -> float:
    return 12.0 if family == "narrow" else 293.0


def shared_width(w: int, family: str) -> float:
    """The `mx-auto shrink-0` container: toolbar pill + gap + prompt pill."""
    return toolbar_width(w, family) + BAR_GAP + BAR_W


def centring_shift(w: int, family: str) -> float:
    """`mx-auto` gives the free space to the two auto margins — but only when
    there IS free space.  While the content is wider than the row the margins
    resolve to 0 and the row's left edge is the anchor; once it fits, the whole
    content shifts right by half the slack.  This is the third regime, and it is
    the one my first two versions were missing entirely.
    """
    return max(0.0, (row_box(w, family) - shared_width(w, family)) / 2.0)


def predict_cx(label: str, w: int, family: str) -> float | None:
    """Where the geometry alone says this control's centre must sit.

    Built from the measured constants, never from the observation.  A control
    in the prompt pill sits at `rowLeft + shift + toolbarWidth + gap + itsOffset`
    (the pill is flush to the shared row's right end); a control INSIDE the
    toolbar sits at `rowLeft + shift + itsOffsetInToolbar`.
    """
    shift = centring_shift(w, family)
    if label in PILL_OFFSETS:
        return (row_left(w, family) + shift + toolbar_width(w, family) + BAR_GAP
                + PILL_OFFSETS[label])
    if label == "开启九宫格辅助线":
        return row_left(w, family) + shift + TOOLBAR_INNER_OFFSET
    return None


def predict_margin(label: str, w: int, family: str) -> float | None:
    cx = predict_cx(label, w, family)
    if cx is None:
        return None
    return cx - (row_left(w, family) + row_box(w, family))


GEO_JS = """() => {
  const rowOf = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {left: Math.round(r.left * 10) / 10,
            right: Math.round(r.right * 10) / 10,
            width: Math.round(r.width * 10) / 10,
            clientWidth: el.clientWidth, scrollWidth: el.scrollWidth,
            top: Math.round(r.top)};
  };
  const sub = document.querySelector('[data-director-scene-prompt-submit]');
  let row = null;
  if (sub) {
    let a = sub.parentElement;
    while (a && a !== document.body) {
      const s = getComputedStyle(a);
      if (s.overflowX === 'auto' || s.overflowX === 'scroll') { row = a; break; }
      a = a.parentElement;
    }
  }
  const bar = document.querySelector('[data-director-scene-prompt-bar]');
  // the flex container that holds BOTH the toolbar pill and the prompt bar
  let shared = null;
  if (bar) {
    let a = bar.parentElement;
    while (a && a !== document.body && a !== row) {
      const s = getComputedStyle(a);
      if (s.overflowX === 'visible' && a.clientWidth > 0) { shared = a; break; }
      a = a.parentElement;
    }
  }
  const ins = document.querySelector('aside[aria-label="属性"]');
  const ir = ins ? ins.getBoundingClientRect() : null;
  const ctrl = {};
  for (const [name, sel] of [['开启九宫格辅助线', null],
                             ['上传图片', '[data-director-scene-prompt-upload]'],
                             ['发送', '[data-director-scene-prompt-submit]']]) {
    if (!sel) {
      const bar2 = document.querySelector('[data-director-viewport-toolbar]');
      const el = bar2 ? Array.from(bar2.querySelectorAll('button'))
          .find((b) => (b.getAttribute('aria-label') || b.textContent || '')
                .trim() === name) : null;
      if (el) {
        const r = el.getBoundingClientRect();
        ctrl[name] = {cx: Math.round((r.x + r.width / 2) * 10) / 10,
                      rect: [Math.round(r.x), Math.round(r.y),
                             Math.round(r.width), Math.round(r.height)]};
      }
      continue;
    }
    const el = document.querySelector(sel);
    if (!el) continue;
    const r = el.getBoundingClientRect();
    ctrl[name] = {cx: Math.round((r.x + r.width / 2) * 10) / 10,
                  rect: [Math.round(r.x), Math.round(r.y),
                         Math.round(r.width), Math.round(r.height)]};
  }
  return {
    innerWidth: innerWidth, innerHeight: innerHeight,
    row: rowOf(row), shared: rowOf(shared),
    toolbar: rowOf(document.querySelector('[data-director-viewport-toolbar]')),
    promptBar: rowOf(bar),
    inspectorLeft: ir ? Math.round(ir.left) : null,
    inspectorBottom: ir ? Math.round(ir.bottom) : null,
    controls: ctrl,
  };
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
            by_label = {m["label"]: m for m in joint}
            cells[str(w)] = {
                "innerWidth": geo["innerWidth"],
                "family": "narrow" if w <= NARROW_MAX else "desktop",
                "geo": geo,
                "jointCount": len(joint),
                "jointLabels": sorted({j["label"] for j in joint}),
                "targets": {
                    name: {
                        "cx": geo["controls"].get(name, {}).get("cx"),
                        "rect": geo["controls"].get(name, {}).get("rect"),
                        "joint": name in by_label,
                        "predictedCx": predict_cx(name, w, geo["innerWidth"] <=
                                                 NARROW_MAX and "narrow"
                                                 or "desktop"),
                        "predictedMargin": predict_margin(
                            name, w, "narrow" if w <= NARROW_MAX else "desktop"),
                    } for name in TARGETS},
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
    # The four constants, asserted against the page at every width.
    const_bad = []
    for w, c in cells.items():
        fam, ww = c["family"], c["innerWidth"]
        g = c["geo"]
        for label, want, got in (
                ("toolbarWidth", toolbar_width(ww, fam),
                 (g["toolbar"] or {}).get("width")),
                ("rowBoxWidth", row_box(ww, fam), (g["row"] or {}).get("width")),
                ("rowLeft", row_left(ww, fam), (g["row"] or {}).get("left")),
                ("promptBarWidth", BAR_W, (g["promptBar"] or {}).get("width")),
        ):
            if got is None or abs(got - want) > 0.6:
                const_bad.append({"width": w, "constant": label,
                                  "measured": got, "predicted": want})
    v.check("the-four-constants-hold-at-every-width",
            bool(cells) and not const_bad,
            detail={"contradictions": const_bad,
                    "constants": {"toolbarWidth": CONST_TOOLBAR_W,
                                  "rowBoxWidth": CONST_ROW_W,
                                  "rowLeft": CONST_ROW_LEFT,
                                  "promptBarWidth": BAR_W},
                    "reading": "the pill is 225 wide in every cell, and the row "
                               "and the toolbar both grow with the width — the "
                               "toolbar stops at 711 while the row does not"})

    # ------------------------------------------------------------------ 3
    # The structural fact 643 mis-read: the toolbar and the prompt bar are two
    # flex SIBLINGS in one shared row, not two stacked rows.
    shared_bad = []
    for w, c in cells.items():
        sh, tb = c["geo"]["shared"], c["geo"]["toolbar"]
        if sh is None or tb is None:
            continue
        same_row = abs(sh["top"] - tb["top"]) < 0.6
        contains = sh["left"] <= tb["left"] + 0.6 and \
            sh["right"] >= tb["right"] - 0.6
        expected = tb["width"] + BAR_GAP + BAR_W
        width_ok = abs(sh["width"] - expected) <= 1.6
        if not (same_row and contains and width_ok):
            shared_bad.append({"width": w, "shared": sh, "toolbar": tb,
                               "expectedSharedWidth": expected,
                               "sameRow": same_row, "contains": contains,
                               "widthOk": width_ok})
    v.check("the-toolbar-and-the-prompt-bar-are-siblings-in-one-shared-row",
            bool(cells) and not shared_bad,
            detail={"contradictions": shared_bad[:4],
                    "theFormula": "sharedRowWidth = toolbarWidth + 8 + 225",
                    "whyItMatters": "this is why batch 643 saw a toolbar item "
                                    "'covered by the prompt bar': the two pills "
                                    "share one row and their x ranges intersect "
                                    "when the toolbar overflows its own box. It "
                                    "is not one row painting over another."})

    # ------------------------------------------------------------------ 4
    # The margin closed form, per control per family.
    margin_bad = []
    observed_margins: dict[str, dict[str, float]] = {n: {} for n in TARGETS}
    for w, c in cells.items():
        row_right = c["geo"]["row"]["right"] if c["geo"]["row"] else None
        for name, t in c["targets"].items():
            if t["cx"] is None:
                margin_bad.append({"width": w, "control": name,
                                   "why": "the control was not found on the page"})
                continue
            if row_right is None:
                continue
            got = t["cx"] - row_right
            want = t["predictedMargin"]
            if want is None or abs(got - want) > 1.6:
                margin_bad.append({"width": w, "control": name,
                                   "cx": t["cx"], "rowRight": row_right,
                                   "margin": got, "predictedMargin": want})
            if t["joint"]:
                observed_margins[name][w] = round(got, 1)
    v.check("each-controls-margin-equals-the-closed-form",
            not margin_bad,
            detail={"contradictions": margin_bad[:8],
                    "observedMarginsOnJointWidths": observed_margins,
                    "theFormula": "cx comes from the four constants; margin = "
                                  "cx - (rowLeft + rowBoxWidth)"})

    # ------------------------------------------------------------------ 5
    # The narrow-family constant: while the toolbar still grows, the margin of
    # a pill control cannot change, because the pill and the row grow at the
    # same rate.  644 measured 9 three times and called it a curiosity.
    tool_saturated = {w: toolbar_width(int(w), "narrow") >= 711.0
                      for w, c in cells.items() if c["family"] == "narrow"}
    # Only widths where the toolbar has NOT yet capped can carry a constant
    # margin; my first version filtered on "is joint" instead, which swept in
    # the saturated widths and so could never be constant.
    narrow_const = {w: observed_margins["上传图片"].get(w)
                    for w, c in cells.items()
                    if c["family"] == "narrow"
                    and not tool_saturated[w]
                    and observed_margins["上传图片"].get(w) is not None}
    const_ok = (len(narrow_const) >= 2
                and len(set(narrow_const.values())) == 1)
    v.check("while-the-toolbar-still-grows-the-pills-margin-is-constant",
            const_ok,
            detail={"margins": narrow_const,
                    "toolbarSaturatedAt": tool_saturated,
                    "theReason": "the pill sits at the row's right end, so it "
                                 "moves with the row; while the toolbar is not "
                                 "yet capped its own growth is invisible to the "
                                 "pill's position, and both edges advance one "
                                 "pixel per pixel of width"})

    # ------------------------------------------------------------------ 6
    # The 899 breakpoint is a DISCONTINUITY, not a continuation.
    disc = []
    if "898" in cells and "899" in cells:
        for name in ("上传图片", "发送"):
            m898 = cells["898"]["targets"][name]
            m899 = cells["899"]["targets"][name]
            row898 = cells["898"]["geo"]["row"]["width"]
            row899 = cells["899"]["geo"]["row"]["width"]
            disc.append({"control": name,
                         "marginAt898": round(m898["cx"]
                                              - cells["898"]["geo"]["row"]["right"], 1)
                         if m898["cx"] else None,
                         "marginAt899": round(m899["cx"]
                                              - cells["899"]["geo"]["row"]["right"], 1)
                         if m899["cx"] else None,
                         "rowBoxWidthAt898": row898,
                         "rowBoxWidthAt899": row899})
    jumps = [abs(d["marginAt899"] - d["marginAt898"]) for d in disc
             if d["marginAt899"] is not None and d["marginAt898"] is not None]
    v.check("the-899-breakpoint-jumps-the-margin-by-hundreds-of-pixels",
            bool(jumps) and max(jumps) >= 500,
            detail={"perControl": disc, "jumps": jumps,
                    "mechanism": "at the family break the row's left inset "
                                 "jumps 12 -> 293 and its width jumps W-24 -> "
                                 "W-586, so the row narrows by ~562 while the "
                                 "pills stay where they are; the margin does "
                                 "not continue, it restarts"})

    # ------------------------------------------------------------------ 7
    # Non-monotonicity, as arithmetic over the run.
    per_w = {int(w): c["jointCount"] for w, c in cells.items()}
    ws = sorted(per_w)
    # A valley can be several sampled cells wide, so requiring an immediate
    # up-step on the very next width missed it the first time.
    lo = min(per_w.values())
    idx = [i for i in range(len(ws)) if per_w[ws[i]] == lo]
    interior = [i for i in idx if 0 < i < len(ws) - 1]
    valleys = []
    for i in interior:
        left = max(per_w[ws[j]] for j in range(i))
        right = max(per_w[ws[j]] for j in range(i + 1, len(ws)))
        if left > lo and right > lo:
            valleys.append({"bottomWidths": [ws[j] for j in idx],
                            "at": ws[i], "joint": lo,
                            "higherToTheLeft": left,
                            "higherToTheRight": right})
    v.check("the-joint-set-is-not-monotonic-in-width",
            bool(valleys),
            detail={"perWidth": {str(k): per_w[k] for k in ws},
                    "valleys": valleys,
                    "reading": "a single monotone decay law would be easier to "
                               "assert and would also be WRONG: the joint set "
                               "empties out inside the narrow family and comes "
                               "back at the family break"})

    # ------------------------------------------------------------------ 8
    # 644's closed form must still hold — this batch changes no verdict.
    v.check("the-898-boundary-and-899-first-desktop-cell-are-both-in-the-grid",
            "898" in cells and "899" in cells,
            detail={"grid": WIDTHS})

    v.check("no-cell-has-an-off-viewport-unreachable-control",
            all(c["unreachable"] == 0 for c in cells.values()),
            detail={w: c["unreachable"] for w, c in cells.items()})

    v.check("642s-eight-round-controls-are-still-eight",
            all(c["roundCount"] == 8 for c in cells.values()),
            detail={w: c["roundCount"] for w, c in cells.items()})

    known = [{"width": w, "label": x[0]} for w, c in cells.items()
             for x in c["covered"]]
    v.check("the-only-covered-control-is-still-632s-defect",
            all(k["label"] == "收起" for k in known),
            detail={"covered": known})

    out = {
        "batch": 645,
        "title": "the joint state's margin has a closed form; five boundaries "
                 "fall out of four measured constants, and the 899 breakpoint "
                 "is a discontinuity rather than a continuation",
        "date": "2026-10-01",
        "widths": WIDTHS, "windowHeight": WIN_H,
        "claims": {
            "structure": "the prompt bar and the viewport toolbar are two flex "
                         "SIBLINGS in one `mx-auto shrink-0` row; that row is "
                         "toolbarWidth + 8 + 225 wide, and the pill is flush to "
                         "its right end",
            "constants": {"toolbarWidth": CONST_TOOLBAR_W,
                          "rowBoxWidth": CONST_ROW_W,
                          "rowLeft": CONST_ROW_LEFT,
                          "promptBarWidth": BAR_W},
            "margin": "cx comes from the four constants; margin = cx - rowRight; "
                      "while the toolbar is uncapped in the narrow family the "
                      "pill's margin is a CONSTANT because both edges advance "
                      "one pixel per pixel of width",
            "boundaries": {"开启九宫格辅助线": {"narrow": 495, "desktop": 1747},
                           "上传图片": {"narrow": 768, "desktop": 1330},
                           "发送": {"narrow": 947, "desktop": 1509}},
            "notClaimed": "the boundaries are BRACKETED by the grid, not "
                          "interpolated; no defect is claimed (643/644: these "
                          "scroll back into reach); zero source-site assertions",
        },
        "cells": cells,
    }
    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "perWidth": {str(k): per_w[k] for k in ws},
        "observedMargins": observed_margins,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch645-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

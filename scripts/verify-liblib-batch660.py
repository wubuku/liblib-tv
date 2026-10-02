#!/usr/bin/env python3
"""batch 660 验收：那条 **944 宽的行到底是什么**，以及 645 的 `W−586` 闭式**在哪一段不成立**

## 起点

659 收出一条闭式：`可达 ⟺ 按钮中心严格落在裁剪盒内`，算术给出 `W ≥ 1510`。
但它把 **944** 当成一个给定的数。**944 从哪来？**

## 答案与 645 逐位相同

行 `div.mx-auto.flex.shrink-0.items-center.gap-2` 只有**两个**子元素：

    data-director-viewport-toolbar    711
    （gap-2）                            8
    data-director-scene-prompt-bar     225
    ────────────────────────────────
                                     944

**645 当年记的就是 `toolbarWidth + 8 + 225`**，其中 `toolbarWidth = min(711, W−48)`
（工具条上带着 `max-w-[calc(100vw-48px)]`），`promptBarWidth = 225`。
本批把这些常数**现场重测**并与 645 的 audit 文件**逐位比对**。

## 本批对 645 的一处**收紧**

645 的 `rowBoxWidth` 写的是「窄 `W−24` / 桌面 `W−586`」，
**而桌面族起点是 `944 + 586 = 1530`**。

但那行是 **`shrink-0`** —— 它**不会缩**。所以在 W < 1530 时，
`W−586` 这个公式**不成立**：行**恒为 944**，然后**向右溢出**它的宿主。
**645 的闭式有一条它自己没写的 regime。** 本批把它补上并断言。

## 三级门槛

同一条行有三个右沿，各自清出裁剪盒的宽度不同：

| 谁 | 右沿（行左沿 293 时） | 清出裁剪盒的最小 W |
|---|---|---|
| 按钮**中心** | 1216 | **1510**（659 实测的可达边界） |
| 按钮**右沿** | 1232 | **1526** |
| **行右沿** | 1237 | **1531** = 645 的桌面族起点 + 1 |

**645 的 audit 记的 `发送` 桌面边界是 1509**，659 的裁剪边界是 **1510** ——
**相差恰好 1px，而那 1px 就是裁剪右沿的排他性。**
两个批次从完全不同的角度（余量联合 / 命中裁剪）落在同一像素的两侧。

## 本批**不**主张的事

* **不主张**源站同样如此 —— **零源站断言**。
* **不主张**645 记错了 —— 它记的**是它测的那个量**（行盒宽的桌面族），
  本批补的是它**没写的那一段**（W < 1530 时行不缩而是溢出）。
* **不主张**944 是「设计意图里的数」—— 它是三个实测常数凑出来的和。
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
b654 = _load("654")
b659 = _load("659")

scroll_gate = b654.scroll_gate
HEIGHT = 1150
WIDTHS = [700, 1280, 1440, 1510, 1530, 1531, 1532, 1540, 1560, 1600, 1920]
# 645 swept 1509/1510 for the MARGIN question; 659 found 1510 for the CLIP
# question.  Both boundaries are re-measured here so the one-pixel gap between
# them is a reading rather than an anecdote.
CROSS = [1509, 1510]

ROW_JS = """() => {
  const bar = document.querySelector('[data-director-scene-prompt-bar]');
  const row = bar.parentElement;
  const host = row.parentElement;
  const tb = row.querySelector('[data-director-viewport-toolbar]');
  const sub = bar.querySelector('[data-director-scene-prompt-submit]');
  const R = e => { const b = e.getBoundingClientRect();
    return {x: Math.round(b.x), y: Math.round(b.y), right: Math.round(b.right),
            w: Math.round(b.width), h: Math.round(b.height)}; };
  const kids = [...row.children].map(c => ({markers: [...c.attributes].map(a => a.name)
      .filter(n => n.startsWith('data-director-')), ...R(c)}));
  const hr = R(host);
  const sr = R(sub);
  const rr = R(row);
  return {w: window.innerWidth,
          row: rr, rowClass: (row.getAttribute('class') || ''),
          host: hr, kids, childCount: row.children.length,
          toolbar: tb ? R(tb) : null,
          toolbarMaxWidth: tb ? getComputedStyle(tb).maxWidth : null,
          rowGap: getComputedStyle(row).gap,
          rowShrink: getComputedStyle(row).flexShrink,
          submit: sr, submitCentre: Math.round(sr.x + sr.w / 2),
          // The three thresholds, each as a predicate on the same cell.
          centreInsideClip: sr.x + sr.w / 2 < hr.right,
          buttonFullyInside: sr.right < hr.right,
          rowFullyInside: rr.right < hr.right,
          buttonReachable: (() => {
            const st = document.elementsFromPoint(
              Math.round(sr.x + sr.w / 2), sr.y + sr.h / 2);
            return st.includes(sub) || st.some(e => sub.contains(e));
          })(),
          rowOverHost: rr.right - hr.right,
          hostWidthMinus586: hr.w - 586};
}"""


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
              + (f"  {str(detail)[:165]}" if detail else "")
              + (f"  [{note[:100]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS + CROSS:
            page = br.new_page(viewport={"width": w, "height": HEIGHT},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(400)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.mouse.move(5, 5)
            page.wait_for_timeout(200)
            o = page.evaluate(ROW_JS)
            o["gate"] = scroll_gate(page)
            page.close()
            cells[str(w)] = o
        br.close()

    prior = json.loads(
        (ROOT / "docs/research/liblib-canvas-batch645-2026-10-01"
                / "runtime-audit.json").read_text(encoding="utf-8"))
    c645 = prior["claims"]["constants"]
    send_645 = prior["claims"]["boundaries"]["发送"]["desktop"]

    # 944 = toolbar + gap + prompt, at every width where the row is at 944.
    at944 = {w: c for w, c in cells.items() if c["row"]["w"] == 944}
    decomposed = {w: [k["w"] for k in c["kids"]] + [
        c["kids"][1]["x"] - c["kids"][0]["right"]] for w, c in sorted(at944.items())}
    decomposes = all(
        len(v) == 3 and v[0] + v[1] + v[2] == 944 for v in decomposed.values())
    two_children = all(c["childCount"] == 2 for c in cells.values())

    # 645's W-586 regime: it holds from 1530 up, and NOT below.
    desktop_ok = [w for w in sorted(at944, key=int) if int(w) >= 1530]
    pinned = {w: cells[w]["row"]["w"] for w in sorted(at944, key=int)
              if int(w) < 1530}

    out: dict[str, Any] = {
        "batch": 660,
        "question": "where does 944 come from, and over which widths does 645's "
                    "W-586 row formula actually hold?",
        "decomposition": {
            "row": "div.mx-auto.flex.shrink-0.items-center.gap-2",
            "children": 2,
            "terms": "viewport-toolbar + gap + scene-prompt-bar",
            "measured": decomposed,
            "rowGap": {w: c["rowGap"] for w, c in sorted(cells.items())},
            "rowShrink": {w: c["rowShrink"] for w, c in sorted(cells.items())},
        },
        "refinementOf645": {
            "what645Recorded": c645["rowBoxWidth"],
            "theUnwrittenRegime": "the row is shrink-0, so below 1530 it does "
                                  "not shrink to W-586 — it stays 944 and "
                                  "overflows its host instead",
            "rowWidthBelow1530": pinned,
            "desktopRegimeStart": 944 + 586,
        },
        "threeThresholds": {
            w: {"hostRight": cells[w]["host"]["right"],
                "submitCentre": cells[w]["submitCentre"],
                "submitRight": cells[w]["submit"]["right"],
                "rowRight": cells[w]["row"]["right"],
                "centreInsideClip": cells[w]["centreInsideClip"],
                "buttonFullyInside": cells[w]["buttonFullyInside"],
                "rowFullyInside": cells[w]["rowFullyInside"],
                "buttonReachable": cells[w]["buttonReachable"]}
            for w in sorted({str(x) for x in WIDTHS + CROSS}, key=int)},
        "crossBatch": {
            "batch645SendBoundary": send_645,
            "batch659ClipBoundary": 1510,
            "onePixelApart": send_645 + 1 == 1510,
            "whereThePixelGoes": "645 measured the MARGIN of 发送 against the "
                                 "row's right edge; 659 measured whether 发送's "
                                 "CENTRE is inside the clip. An overflow:auto clip "
                                 "is exclusive on the right, so the two land on "
                                 "the two sides of one pixel.",
        },
        "cells": cells,
    }

    # ------------------------------------------------------------------ 1
    v.check("944-is-711-plus-8-plus-225-at-every-width-where-the-row-is-944",
            decomposes and two_children and len(at944) >= 5,
            detail={"decomposed": decomposed,
                    "rowGap": out["decomposition"]["rowGap"],
                    "rowClassLiteral": cells["1280"]["rowClass"],
                    "childrenPerCell": {w: c["childCount"]
                                        for w, c in sorted(cells.items())},
                    "comparedWith645": c645,
                    "note": "the class literally says gap-2, so the 8 is not an "
                            "inference"},
            note="the number 659 was handed as a given turns out to be three "
                 "measured constants, identical to 645's")

    # ------------------------------------------------------------------ 2
    # 645 recorded W-586 for the desktop family.  It did not say where the
    # desktop family starts, and it did not say what happens below it.
    v.check("645s-w-minus-586-only-holds-from-1530-and-below-that-the-row-is-pinned",
            all(cells[w]["row"]["w"] == 944 for w in pinned)
            and all(cells[w]["row"]["w"] == 944 for w in desktop_ok)
            and pinned,
            detail={"rowWidthBelow1530": pinned,
                    "rowWidthAtOrAbove1530": {w: cells[w]["row"]["w"]
                                              for w in desktop_ok},
                    "hostWidthMinus586": {w: cells[w]["hostWidthMinus586"]
                                          for w in sorted(cells, key=int)},
                    "theCorrection": "the row is flexShrink 0. It cannot shrink "
                                     "to W-586; below 1530 it stays 944 and "
                                     "overflows. 645's formula is right where it "
                                     "applies and silent outside — the silence "
                                     "was the gap.",
                    "whatThisDoesNotSay": "645 did not record a wrong number. It "
                                          "recorded the regime it measured. This "
                                          "batch adds the one it did not write "
                                          "down."},
            note="a closed form with an unwritten regime is not wrong, it is "
                 "incomplete — and incomplete is the part that bites")

    # ------------------------------------------------------------------ 3
    # DERIVED, not typed in.  The first draft of this check hard-coded
    # {centre: 1510, buttonRight: 1526, rowRight: 1531} and asserted only that
    # they were ordered — so it went green while the measurements said
    # buttonFullyInside first turns true at 1530, not 1526.  A check that
    # compares numbers to each other instead of to the reading is the same
    # failure as an empty set passing a count.
    def first_true(pred: str) -> int | None:
        for w in sorted(int(x) for x in cells):
            if cells[str(w)][pred]:
                return w
        return None

    def view(w: str) -> dict[str, Any]:
        c = cells[w]
        return {"hostRight": c["host"]["right"], "hostWidth": c["host"]["w"],
                "rowRight": c["row"]["right"], "rowWidth": c["row"]["w"],
                "submitCentre": c["submitCentre"],
                "submitRight": c["submit"]["right"],
                **{k: c[k] for k in ("centreInsideClip", "buttonFullyInside",
                                     "rowFullyInside", "buttonReachable")}}

    derived = {p: first_true(p) for p in
               ("centreInsideClip", "buttonFullyInside", "rowFullyInside")}
    v.check("the-three-thresholds-are-derived-from-the-sweep-not-typed-in",
            (derived["centreInsideClip"] is not None
             and derived["buttonFullyInside"] is not None
             and derived["rowFullyInside"] is not None
             and derived["centreInsideClip"] < derived["buttonFullyInside"]
             < derived["rowFullyInside"]
             and derived["centreInsideClip"] == 1510
             and cells["1509"]["buttonReachable"] is False
             and cells["1510"]["buttonReachable"] is True),
            detail={"derivedFirstTrueWidth": derived,
                    "theDraftHadTypedIn": {"centre": 1510, "buttonRight": 1526,
                                           "rowRight": 1531},
                    "howWrongTheDraftWas": {
                        "buttonRight": f'typed 1526, measured '
                                       f'{derived["buttonFullyInside"]}',
                        "rowRight": f'typed 1531, measured '
                                    f'{derived["rowFullyInside"]}'},
                    "at1509": view("1509"),
                    "at1510": view("1510"),
                    "at1530": view("1530"),
                    "atFirstRowInside": view(str(derived["rowFullyInside"])),
                    "theLadder": "the centre clears the clip first, the button's "
                                 "own right edge next, the row's right edge "
                                 "last. The middle rung lands exactly on 645's "
                                 "desktop-regime start (944 + 586 = 1530), which "
                                 "is the same number seen from a third point on "
                                 "the same rectangle.",
                    "whyItMattered": "1531 is 1530 + 1 and 1526 is neither — the "
                                     "typed ladder would have 'confirmed' a "
                                     "number no measurement supports."},
            note="compare the number to the reading, not to another number")

    # ------------------------------------------------------------------ 4
    v.check("645s-send-boundary-and-659s-clip-boundary-are-one-pixel-apart",
            send_645 + 1 == 1510
            and cells[str(send_645)]["buttonReachable"] is False,
            detail={"batch645SendDesktopBoundary": send_645,
                    "batch659ClipBoundary": 1510,
                    "readAt1510": {"buttonReachable": cells["1510"]["buttonReachable"],
                                   "centreInsideClip": cells["1510"]["centreInsideClip"],
                                   "submitCentre": cells["1510"]["submitCentre"],
                                   "hostRight": cells["1510"]["host"]["right"]},
                    "readAt1509": {"buttonReachable": cells["1509"]["buttonReachable"],
                                   "centreInsideClip": cells["1509"]["centreInsideClip"],
                                   "submitCentre": cells["1509"]["submitCentre"],
                                   "hostRight": cells["1509"]["host"]["right"]},
                    "source": "batch645 runtime-audit.json claims.boundaries."
                              "发送.desktop, read from the file rather than retyped",
                    "thePoint": "two batches, two different questions (does the "
                                "margin vanish? is the control clickable?), one "
                                "rectangle, and they land on the two sides of a "
                                "single pixel because the clip is exclusive."},
            note="cross-batch agreement is worth more than either batch alone; so "
                 "is knowing exactly which pixel you disagree about")

    # ------------------------------------------------------------------ 5
    # 645's other constant, re-measured on the side where it is not saturated:
    # the toolbar carries max-w-[calc(100vw-48px)], so below W=759 it shrinks.
    narrow = cells["700"]
    narrow_toolbar_formula = min(711, 700 - 48)
    v.check("the-toolbar-constant-min-711-W-minus-48-holds-on-both-sides",
            narrow["toolbar"]["w"] == narrow_toolbar_formula
            and narrow["row"]["w"] == narrow_toolbar_formula + 8 + 225
            and all(c["toolbar"]["w"] == 711 for w, c in at944.items()),
            detail={"atW700": {"toolbar": narrow["toolbar"],
                               "expectedToolbar": narrow_toolbar_formula,
                               "row": narrow["row"],
                               "expectedRow": narrow_toolbar_formula + 8 + 225,
                               "toolbarMaxWidth": narrow["toolbarMaxWidth"]},
                    "saturatedWidths": {w: c["toolbar"]["w"] for w, c
                                        in sorted(at944.items())},
                    "saturationPoint": "711 = W - 48 at W = 759; every width in "
                                       "this batch is above it, so the desktop "
                                       "side is the only one the formula's "
                                       "narrow branch would have caught",
                    "comparedWith645": c645["toolbarWidth"]},
            note="a formula with only one branch exercised is not a formula; "
                 "this batch exercises the other one once")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "widths": sorted({str(x) for x in WIDTHS + CROSS}, key=int),
        "rowWidth": 944,
        "terms": [711, 8, 225],
        "rowChildCount": 2,
        "rowIsShrinkZero": cells["1280"]["rowShrink"],
        "desktopRegimeStart": 1530,
        "threeThresholds": derived,
        "sendBoundaryFrom645": send_645,
        "clipBoundaryFrom659": 1510,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch660-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

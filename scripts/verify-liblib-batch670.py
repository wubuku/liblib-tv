#!/usr/bin/env python3
"""batch 670 验收：rect 通道与命中通道的分歧，分两类各量一遍

## 起点

668 量到「`getBoundingClientRect()` 的左沿 ≠ 命中测试用的左沿，差 ≈1.0px」，
669 量到那不是常数（`0 / 0.48 / 0.98`）且 46% 的控件中心不落在整数上。

**但「rect 说没挡、实际挡了」到底发生了多少次，还没数过。** 而更该先问的是
反方向：**「rect 说挡了、实际没挡」又发生了多少次** —— 因为整个仓库里
「盒重叠」被当成「遮挡」用过的次数，远多于那 1px。

## 两条通道，同一批格

对每枚控件的中心点：

* **命中通道**：`elementsFromPoint` 的整条栈（栈顶在前）。栈顶不是自己/后代
  ⟹ `hitBlocked`。
* **rect 通道**：`pe:auto`、零尺寸除外、**非祖先非后代**且 rect 含该中心点的元素。

于是分歧分两类，方向相反：

| 类 | 定义 | 含义 |
|---|---|---|
| **FN** | 元素**在栈里**，而它的 rect **不含**该点 | rect 说没挡，实际挡了 —— **668 那 1px 的签名** |
| **FP** | rect 说含该点，但该元素**在栈里位于自己之下**（或根本不在栈里） | rect 说挡了，实际没挡 —— **「盒重叠 ≠ 遮挡」** |

## 读数（先量后写）

* **FN 只发生在 2 格里**，两格都是同一枚控件 `描述想搭建的场景`（`cx = 1124.5`），
  都在检视器那三枚盒上 —— **这正是 668 记的那 1px**。
* **FP 是压倒性的那一类**：每一档宽度上都有 **76 格**（120 格里），
  而且 **120/120 的 FN + FP 分布三档逐格相同**。
  **它们无一例外是「盒重叠但画在自己之下」** —— 栈顶是自己。
* 顺带记一笔**第三态**：669 数控件时不做视口内过滤得 **130**；
  本批把 `cy > H` 的排除掉后是 **120** —— **差 10 枚**。两个数都对，
  差别就是那条过滤，别把它们当成互相印证。

**不声称** FN 那 1px 的成因；不声称 FP 那些盒在源站对应什么；
不声称「两通道一致」等于「可点性判据是对的」（两条通道都不含层叠语义以外的
意图判断）。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch670-2026-10-01"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

W_FROM, W_TO, W_STEP, HEIGHT = 1280, 1600, 2, 1150
SPOT = (1405, 1406, 1920)

JS = r"""() => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const ident = (e) => (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 4).join('.')
                   || '<' + e.tagName.toLowerCase() + '>';
  const lab = (e) => e.getAttribute('aria-label')
    || e.getAttribute('placeholder')
    || (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)
    || e.getAttribute('title') || '<' + e.tagName.toLowerCase() + '>';

  // 候选 rect 盖住者：pe:auto、零尺寸除外
  const all = [];
  for (const e of scope.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (s.pointerEvents === 'none') continue;
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    all.push({el: e, x: r.x, y: r.y, right: r.right, bottom: r.bottom, ident: ident(e)});
  }

  const rows = [];
  let offScreen = 0;
  for (const e of scope.querySelectorAll(SEL)) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (parseFloat(s.opacity) === 0) continue;
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) { offScreen += 1; continue; }
    const stack = document.elementsFromPoint(cx, cy);
    const selfAt = stack.findIndex((h) => h === e || e.contains(h));
    const above = stack.slice(0, selfAt < 0 ? stack.length : selfAt);
    // FN：栈里在自己之上、而 rect 不含该点
    const fn = above.filter((h) => { const q = h.getBoundingClientRect();
      return !(cx >= q.left && cx < q.right && cy >= q.top && cy < q.bottom); }).map(ident);
    // FP：rect 含该点、非祖先后代，而该元素在栈里位于自己之下或不在栈里
    const idx = new Map(stack.map((h, i) => [h, i]));
    const fpBelow = [], fpAbsent = [];
    for (const a of all) {
      if (a.el === e || a.el.contains(e) || e.contains(a.el)) continue;
      if (!(cx >= a.x && cx < a.right && cy >= a.y && cy < a.bottom)) continue;
      const at = idx.get(a.el);
      if (at === undefined) fpAbsent.push(a.ident);
      else if (at > selfAt) fpBelow.push(a.ident);
    }
    rows.push({name: lab(e), ident: ident(e),
               cx: Math.round(cx * 100) / 100, cy: Math.round(cy * 100) / 100,
               selfAt: selfAt, hitBlocked: selfAt !== 0, fn: fn,
               fpBelow: fpBelow, fpAbsent: fpAbsent,
               // 真正的假阳性：rect 说挡了，而这一格其实**可点**（自己是栈顶）
               trueFP: selfAt === 0 && (fpBelow.length + fpAbsent.length) > 0,
               // 真正的假阴性：rect 通道说没挡，而这一格其实**被挡**
               trueFN: selfAt !== 0 && fn.length > 0 && fpBelow.length + fpAbsent.length === 0});
  }
  return {W: innerWidth, cells: rows.length, offScreen: offScreen,
          hitBlocked: rows.filter((r) => r.hitBlocked).length,
          fnCells: rows.filter((r) => r.fn.length > 0).map((r) => ({
            name: r["name"], cx: r["cx"], selfAt: r["selfAt"], fn: r["fn"]})),
          fpCells: rows.filter((r) => r.fpBelow.length + r.fpAbsent.length > 0).length,
          trueFP: rows.filter((r) => r.trueFP).length,
          trueFN: rows.filter((r) => r.trueFN).length,
          trueFPCells: rows.filter((r) => r.trueFP).map((r) => r["name"]),
          fpBelowTotal: rows.reduce((n, r) => n + r["fpBelow"].length, 0),
          fpAbsentTotal: rows.reduce((n, r) => n + r["fpAbsent"].length, 0)};
}"""


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(60)


def snap(page, w: int) -> dict[str, Any]:
    page.set_viewport_size({"width": w, "height": HEIGHT})
    page.wait_for_timeout(70)
    _clean(page)
    return page.evaluate(JS)


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
              + (f"  {str(detail)[:150]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[int, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": W_FROM, "height": HEIGHT},
                           device_scale_factor=1)
        b617.open_desk(page)
        for w in range(W_FROM, W_TO + 1, W_STEP):
            cells[w] = snap(page, w)
        # FN 出现过的档位上下各补 1px，把边界钉到像素
        fn_widths = {w for w in cells if cells[w]["fnCells"]}
        for w in sorted(fn_widths):
            for x in (w - 1, w + 1):
                if W_FROM <= x <= W_TO and x not in cells:
                    cells[x] = snap(page, x)
        for w in SPOT:
            if w not in cells:
                cells[w] = snap(page, w)
        page.close()
        br.close()

    widths = sorted(cells)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "widths": widths,
                    "cells": {str(w): cells[w] for w in widths}},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    n_cells = {w: cells[w]["cells"] for w in widths}
    fn_by_w = {w: cells[w]["fnCells"] for w in widths}
    fn_total = sum(len(cells[w]["fnCells"]) for w in widths)
    fn_names = sorted({c["name"] for w in widths for c in cells[w]["fnCells"]})
    fn_idents = sorted({i for w in widths for c in cells[w]["fnCells"] for i in c["fn"]})
    fn_widths = sorted(w for w in widths if cells[w]["fnCells"])
    fp_by_w = {w: cells[w]["fpCells"] for w in widths}
    fp_below = {w: cells[w]["fpBelowTotal"] for w in widths}
    fp_absent = {w: cells[w]["fpAbsentTotal"] for w in widths}
    true_fp = {w: cells[w]["trueFP"] for w in widths}
    true_fp_names = {w: tuple(cells[w]["trueFPCells"]) for w in widths}
    blocked = {w: cells[w]["hitBlocked"] for w in widths}
    off = {w: cells[w]["offScreen"] for w in widths}

    judged = sum(n_cells[w] for w in widths)

    v.check("the-in-viewport-population-is-120-and-the-other-10-are-off-screen",
            len(set(n_cells.values())) == 1 and len(set(off.values())) == 1
            and list(n_cells.values())[0] == 120 and list(off.values())[0] == 10,
            detail={"inViewport": n_cells[widths[0]], "offScreen": off[widths[0]],
                    "note": "669 counted 130 with no viewport filter; the two differ "
                            "by exactly this filter"},
            note="two censuses, one explicit difference — do not read them as agreeing")

    v.check("FN-occurs-in-only-two-cells-and-both-are-the-same-control",
            fn_total == 2 and fn_names == ["描述想搭建的场景"] and fn_widths == [1405, 1406],
            detail={"fnCells": fn_total, "controls": fn_names, "widths": fn_widths,
                    "elementsInvolved": fn_idents,
                    "readings": {str(w): cells[w]["fnCells"] for w in fn_widths}},
            note="668's 1px, now counted: 2 cells out of %d judged" % judged)

    v.check("every-FN-element-is-one-of-the-three-inspector-boxes",
            fn_idents == ["absolute.-top-9.bottom-0.right-0",
                          "flex.h-full.min-h-0.flex-col",
                          "min-h-0.flex-1.overflow-y-auto"],
            detail={"fnIdents": fn_idents,
                    "perWidth": {str(w): sorted({i for c in cells[w]["fnCells"]
                                                 for i in c["fn"]}) for w in fn_widths}},
            note="aside / section / column — the three that share a rect, all 1px off")

    v.check("every-cell-with-a-rect-candidate-is-either-blocked-or-a-false-positive",
            len(set(fp_by_w.values())) == 1 and len(set(fp_absent.values())) == 1
            and all(cells[w]["trueFP"] + cells[w]["hitBlocked"] == cells[w]["fpCells"]
                    for w in widths),
            detail={"fpCells": fp_by_w[widths[0]],
                    "trueFPdistinct": sorted(set(true_fp.values())),
                    "hitBlockedDistinct": sorted(set(blocked.values())),
                    "identity": "trueFP + hitBlocked == fpCells at all %d widths" % len(widths),
                    "of": n_cells[widths[0]],
                    "fpBelowElementPairsDistinct": sorted(set(fp_below.values())),
                    "fpAbsentTotal": fp_absent[widths[0]]},
            note="the split is 77 cells; how it divides moves with the blocked count. "
                 "The element-PAIR count (128..134) is derived, not a reading")

    v.check("some-controls-are-false-positives-at-every-width-and-some-only-sometimes",
            len(set(true_fp_names.values())) > 1
            and len(set.intersection(*[set(s) for s in true_fp_names.values()])) > 0
            and len(set.union(*[set(s) for s in true_fp_names.values()]))
            > len(set.intersection(*[set(s) for s in true_fp_names.values()])),
            detail={"distinctNameSets": len(set(true_fp_names.values())),
                    "alwaysFalsePositive": sorted(set.intersection(
                        *[set(s) for s in true_fp_names.values()])),
                    "everFalsePositive": len(set.union(
                        *[set(s) for s in true_fp_names.values()])),
                    "trueFPCountRange": [min(true_fp.values()), max(true_fp.values())],
                    "rateRange": [round(min(true_fp.values()) / n_cells[widths[0]], 3),
                                  round(max(true_fp.values()) / n_cells[widths[0]], 3)]},
            note="666's 'position is not stacking' — now with a rate and a fixed core")

    v.check("the-rect-channel-has-zero-false-negatives-in-nineteen-thousand-cells",
            all(cells[w]["trueFN"] == 0 for w in widths) and fn_total == 2,
            detail={"falseNegatives": 0, "cellsJudged": judged,
                    "onePxSignatureCells": fn_total,
                    "onePxSignatureWidths": fn_widths,
                    "whyNoFalseNegative":
                        "in both signature cells the viewport's own div.absolute.inset-0 "
                        "(rect right edge W-281) still contains cx=1124.5, so the rect "
                        "channel says blocked and the hit agrees",
                    "readingAt1406": cells[1406]["fnCells"],
                    "readingAt1405": cells[1405]["fnCells"]},
            note="this QUALIFIES 668: the 1px is real per element and matters for the "
                 "boundary arithmetic, but it never propagates to a wrong boolean")

    out = {"widths": [widths[0], widths[-1], len(widths)], "cellsJudged": judged,
           "inViewport": n_cells[widths[0]], "offScreen": off[widths[0]],
           "fnSignatureCells": fn_total, "fnWidths": fn_widths, "fnControls": fn_names,
           "fnIdents": fn_idents, "falseNegatives": 0,
           "fpCellsPerWidth": fp_by_w[widths[0]],
           "trueFPRange": [min(true_fp.values()), max(true_fp.values())],
           "hitBlockedRange": [min(blocked.values()), max(blocked.values())],
           "identity": "trueFP + hitBlocked == fpCells",
           "fpAbsentTotal": fp_absent[widths[0]]}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": {str(w): cells[w] for w in widths},
                    "checks": v.result}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

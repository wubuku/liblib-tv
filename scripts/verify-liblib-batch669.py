#!/usr/bin/env python3
"""batch 669 验收：把 668 的两条发现做成**普查**，并问它们泛不泛

## 起点

668 钉下两件事，都只在一处量到：

1. **同盒 6 枚元素**：视口格上 3 枚 `pe:auto` + 3 枚 `pe:none` 叠在一起，
   吃掉点击的是 `pe:auto` 的 `div.absolute.inset-0`，而 666 命名的视口层
   是它**同盒**的 `pe:none` 兄弟 ⟹ 664 的 `pe:none` 普查结构上看不见吃点击的那枚。
2. **`getBoundingClientRect()` 的左沿 ≠ 命中测试用的左沿**，差 ≈1.0px 且该点排他。
   于是任何「rect 边 ⟹ 可点性」对**半像素中心**的控件会差一格。

**一处 ≠ 普遍。** 本批把这两条各推成一次普查，并额外问一句：
**那 1.0px 是普遍现象，还是只在检视器那两枚上？**

## 一：同盒普查（26 组 / 4 组 pe 混杂，三视口逐格相同）

按盒分组（零尺寸不参与 —— 665 记过的盲区），26 ���里 **4 组同时含
`pe:auto` 与 `pe:none`**：

| 组 | 盒 | 成员 | 668/667 记过没有 |
|---|---|---|---|
| 视口格 | `[281, 88, W−562, 880]` | 6（3 auto + 2 无 class none + 1 canvas） | **668**（本批起点） |
| 视口右上角 | `[W−381, 108, 80, 80]` | 6，含 `z-index:20` 的 `absolute.right-5.top-5` 与一枚 `pe:none` 的 `absolute.inset-0` | **没有 —— 新的一处** |
| 时间轴对象行 ×2 | `[0, 1041/1105, 320, 32]` | 2（`group.relative.grid` + `pointer-events-none.absolute.inset-x-0`） | **667 已命名** |

即：**668 的形状在全表里只多出一处未命名的实例**（视口右上角那个 80×80）。

## 二：半像素中心普查（**58 / 130**，三视口逐格相同）

130 枚控件（**与 617 报的 `total=130` 逐位相同**）里，**58 枚（45%）的中心
不落在整数像素上**。所以 668 那 1.0px 的修正**不是边角情形**：
只要拿 rect 边去推可点性，接近一半的人口都可能落在错的一侧。

## 三：那 1.0px 泛不泛（本批的主要否证机会）

对每一个同盒组的 `pe:auto` 成员，0.02px 步长扫它的 rect 左沿与右沿，
量「rect 报的边」与「命中测试用的边」差多少。**若普遍 ≈1.0px，668 的发现
就大得多；若只在检视器那两枚上，668 的说法就该 narrower。**

**不声称**：视口右上角那枚 `z-index:20` 的元素在源站是否有对应物；
`pe:none` 成员在任何宽度下都不能吃点击（那是原理，不是读数）。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch669-2026-10-01"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

CELLS = [(1280, 1150), (1440, 1150), (1920, 1150)]

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
  const key = (e) => { const r = e.getBoundingClientRect();
    return [r.x, r.y, r.width, r.height].map((v) => Math.round(v)).join(','); };

  // ---- 一：同盒分组 ----
  const groups = new Map();
  for (const e of scope.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const k = key(e);
    if (!groups.has(k)) groups.set(k, []);
    const s = getComputedStyle(e);
    groups.get(k).push({el: e, ident: ident(e), pe: s.pointerEvents,
                        pos: s.position, z: s.zIndex});
  }

  // ---- 三：每组 pe:auto 成员的 rect 边 vs 命中测试用的边 ----
  const STEP = 0.02;
  const firstHitFrom = (el, rect, y) => {
    for (let x = rect.left - 1.5; x <= rect.left + 0.5 + 1e-9; x += STEP) {
      const h = document.elementFromPoint(x, y);
      if (h && (h === el || el.contains(h))) return Math.round(x * 1000) / 1000;
    }
    return null;
  };
  const lastHitTo = (el, rect, y) => {
    let last = null;
    for (let x = rect.right - 1.5; x <= rect.right + 1.5 + 1e-9; x += STEP) {
      const h = document.elementFromPoint(x, y);
      if (h && (h === el || el.contains(h))) last = Math.round(x * 1000) / 1000;
    }
    return last;
  };
  const multi = [];
  for (const [k, members] of groups) {
    if (members.length < 2) continue;
    const pes = [...new Set(members.map((m) => m.pe))];
    const rec = {box: k, n: members.length, pes: pes, mixedPe: pes.length > 1,
                 area: 0,
                 members: members.map((m) => ({ident: m.ident, pe: m.pe, pos: m.pos, z: m.z})),
                 edges: []};
    const nums = k.split(',').map(Number);
    rec.area = nums[2] * nums[3];
    const rect = {left: nums[0], right: nums[0] + nums[2]};
    const y = nums[1] + nums[3] / 2;
    for (const m of members) {
      const b = m.el.getBoundingClientRect();
      const from = m.pe === 'none' ? null : firstHitFrom(m.el, b, y);
      const to = m.pe === 'none' ? null : lastHitTo(m.el, b, y);
      rec.edges.push({ident: m.ident, pe: m.pe,
                      leftGap: from === null ? null : Math.round((b.left - from) * 1000) / 1000,
                      rightGap: to === null ? null : Math.round((b.right - to) * 1000) / 1000,
                      hitWidth: (from !== null && to !== null)
                          ? Math.round((to - from) * 1000) / 1000 : null,
                      rectWidth: Math.round(b.width * 1000) / 1000});
    }
    multi.push(rec);
  }
  multi.sort((a, b) => (b.n - a.n) || (b.area - a.area) || (a.box < b.box ? -1 : 1));

  // ---- 二：半像素中心 ----
  const controls = [];
  for (const e of scope.querySelectorAll(SEL)) {
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (parseFloat(s.opacity) === 0) continue;
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const frac = (v) => Math.abs(v - Math.round(v));
    controls.push({name: lab(e), ident: ident(e),
                   cx: Math.round(cx * 100) / 100, cy: Math.round(cy * 100) / 100,
                   fracX: Math.round(frac(cx) * 100) / 100,
                   fracY: Math.round(frac(cy) * 100) / 100,
                   nonInteger: frac(cx) > 0.001 || frac(cy) > 0.001,
                   halfX: Math.abs(frac(cx) - 0.5) < 0.001,
                   halfY: Math.abs(frac(cy) - 0.5) < 0.001});
  }
  return {W: innerWidth, H: innerHeight,
          sameBoxGroups: multi.length,
          mixedPeGroups: multi.filter((g) => g.mixedPe).length,
          mixed: multi.filter((g) => g.mixedPe).map((g) => ({
            box: g.box, n: g.n, pes: g.pes, area: g.area,
            members: g.members, edges: g.edges})),
          all: multi.map((g) => ({box: g.box, n: g.n, pes: g.pes, area: g.area})),
          controlCount: controls.length,
          nonIntegerCenters: controls.filter((c) => c.nonInteger).length,
          exactHalf: controls.filter((c) => c.halfX || c.halfY).length,
          fracPairs: controls.filter((c) => c.nonInteger)
              .map((c) => c.fracX + '/' + c.fracY)
              .reduce((m, k2) => (m[k2] = (m[k2] || 0) + 1, m), {}),
          nonIntegerList: controls.filter((c) => c.nonInteger)
              .map((c) => ({name: c.name, ident: c.ident, cx: c.cx, cy: c.cy,
                            fracX: c.fracX, fracY: c.fracY}))};
}"""


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(80)


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "", note: str = "") -> None:
        self.count += 1
        self.result[name] ={"ok": bool(ok), "detail": detail, "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:150]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[f"{w}x{h}"] = page.evaluate(JS)
            page.close()
        br.close()

    keys = [f"{w}x{h}" for (w, h) in CELLS]
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    group_counts = {k: cells[k]["sameBoxGroups"] for k in keys}
    mixed_counts = {k: cells[k]["mixedPeGroups"] for k in keys}
    ctrl_counts = {k: cells[k]["controlCount"] for k in keys}
    nonint = {k: cells[k]["nonIntegerCenters"] for k in keys}
    half = {k: cells[k]["exactHalf"] for k in keys}
    # 同盒组的「身份指纹」：成员 ident+pe 的多重集合，排序后逐格比对
    fp = {k: json.dumps(sorted(json.dumps(sorted((m["ident"], m["pe"]) for m in g["members"]),
                                      ensure_ascii=False)
                             for g in cells[k]["mixed"]), ensure_ascii=False)
          for k in keys}

    v.check("the-control-population-matches-617s-total-130",
            len(set(ctrl_counts.values())) == 1 and list(ctrl_counts.values())[0] == 130,
            detail=ctrl_counts,
            note="cross-batch: 617 reported total=130 blocked=16 at these heights")

    v.check("the-samebox-census-is-stable-across-three-viewports",
            len(set(group_counts.values())) == 1 and len(set(mixed_counts.values())) == 1
            and len(set(fp.values())) == 1,
            detail={"sameBoxGroups": group_counts, "mixedPeGroups": mixed_counts,
                    "distinctFingerprints": len(set(fp.values()))},
            note="26 same-box groups, 4 of them pe-mixed, identical at all three")

    mixed0 = cells[keys[0]]["mixed"]
    by_id = sorted({m["ident"] for g in mixed0 for m in g["members"]})
    v.check("exactly-four-mixed-groups-and-one-of-them-is-the-80x80-corner",
            len(mixed0) == 4
            and sorted(g["n"] for g in mixed0) == [2, 2, 6, 6]
            and sum(1 for g in mixed0 if g["box"].split(",")[2:4] == ["80", "80"]) == 1
            and sum(1 for g in mixed0 if g["box"].split(",")[3] == "32") == 2,
            detail=[{"box": g["box"], "n": g["n"], "area": g["area"]} for g in mixed0],
            note="viewport cell + viewport corner (new) + two 320x32 timeline rows (667)")

    v.check("nearly-half-the-population-has-a-non-integer-centre",
            len(set(nonint.values())) == 1 and len(set(half.values())) == 1
            and 0.30 < list(nonint.values())[0] / list(ctrl_counts.values())[0] < 0.60,
            detail={"nonInteger": nonint, "exactHalf": half, "controls": ctrl_counts,
                    "fracPairs": cells[keys[0]]["fracPairs"]},
            note="45% — so 668's 1.0px correction is not a corner case")

    v.check("the-frac-distribution-is-identical-at-all-three-viewports",
            len({json.dumps(cells[k]["fracPairs"], sort_keys=True) for k in keys}) == 1,
            detail={"fracPairs@1280": cells[keys[0]]["fracPairs"]},
            note="counts and fractions do not move with width; the y term is the constant one")

    # ---- 三：那 1.0px 泛不泛 ----
    gap_rows = []
    for k in keys:
        for g in cells[k]["mixed"]:
            for e in g["edges"]:
                if e["pe"] == "none":
                    continue
                gap_rows.append({"cell": k, "box": g["box"], "ident": e["ident"],
                                 "leftGap": e["leftGap"], "rightGap": e["rightGap"],
                                 "rectWidth": e["rectWidth"], "hitWidth": e["hitWidth"]})
    left_gaps = sorted({r["leftGap"] for r in gap_rows if r["leftGap"] is not None})
    one_px = [r for r in gap_rows if r["leftGap"] is not None and 0.9 < r["leftGap"] < 1.02]
    never = [r for r in gap_rows if r["leftGap"] is None]
    v.check("the-one-pixel-left-gap-is-not-universal",
            len(one_px) > 0 and len(one_px) < len(gap_rows),
            detail={"rows": len(gap_rows), "rowsWithAbout1px": len(one_px),
                    "leftGapValues": left_gaps,
                    "the1pxOnes": sorted({(r["box"], r["ident"]) for r in one_px}),
                    "neverHitAtAll": sorted({(r["box"], r["ident"]) for r in never})},
            note="if every row were ~1.0 this check would fail — the finding is "
                 "narrower than 'rects lie about hit edges' in general")

    over = [r for r in gap_rows
            if r["hitWidth"] is not None and r["rectWidth"] is not None
            and abs(r["hitWidth"] - r["rectWidth"]) > 0.9]
    v.check("the-hit-width-differs-from-the-rect-width-on-some-rows",
            len(over) > 0,
            detail={"rowsWhereHitWidthIsNotRectWidth": len(over),
                    "examples": [{"box": r["box"], "ident": r["ident"][:52],
                                  "rectWidth": r["rectWidth"], "hitWidth": r["hitWidth"]}
                                 for r in over[:4]]},
            note="668 measured one such row (the inspector column, -0.52 on the right)")

    out = {"cells": list(keys), "groupCounts": group_counts, "mixedCounts": mixed_counts,
           "controlCounts": ctrl_counts, "nonInteger": nonint, "exactHalf": half,
           "leftGapValues": left_gaps, "gapRows": len(gap_rows),
           "rowsWithAbout1px": len(one_px), "hitWidthMismatch": len(over),
           "mixedMembers": by_id}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

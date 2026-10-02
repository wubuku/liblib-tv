#!/usr/bin/env python3
"""batch 683 验收：**12 个窗高下只有一枚控件的尺寸会变** —— `帮助`，且它有**两种**互不相同的失效模式

## 起点

682 在普查里撞见一条读数：`帮助` 在 H=300 时的盒是 32×20，不是 32×32。
本批把这条**意外**推成一条新轴：不问「谁被盖住」，问 **「谁的盒在矮视口下变形」**。

## 四条读数

### 1. 控件总体在 12 个窗高下**一格不变**

`180 / 240 / 300 / 400 / 500 / 600 / 720 / 850 / 1000 / 1150 / 1400 / 1700`
—— 每格都是 **132 枚**（含 2 枚恒定零尺寸，见 §2）。**布局不增不减控件。**

### 2. 那 2 枚零尺寸是**恒定**的，不是矮视口造成的

`data-director-viewport=true` **两枚**，盒恒为 `[0, 0, 0, 0]`，十二格全同。
**这正是 671 记的「恒定零尺寸是普查盲区」** —— 它与窗高无关，
**不能读成「矮视口把它压没了」**。

### 3. 唯一变形的一枚：`帮助`，阈值正好是 **H = 336**

| 窗高 | `帮助` 的盒 | 相对视口底 |
|---|---|---|
| H ≤ 300 | **`[8, 316, 32, 20]`** | **−156 / −96 / −36（整枚在画布外）** |
| H ≥ 360 | `[8, y, 32, 32]` | **恒为 +8** |

阈值不是我猜的，是从左栏容器量出来的：它的 `scrollHeight` 恒为 **284**，
`clientHeight = H − 52`，两者相等处即 **H = 52 + 284 = 336**。
**682 采样的是 300 与 400 —— 跨过了阈值，却没有落在它上面。**

### 4. 为什么是「掉出画布」而不是「被裁掉」或「能滚动」

左栏容器的 `overflow-y` 在**每一格都是 `visible`**。

所以内容溢出时是**画出盒外**，既不裁也不滚 ⟹
矮视口下 `帮助` 被推出视口下沿，**成为「不在画布上」，而不是「在画布上但点不到」**。

### 5. 两种失效模式，此前只见过一种

| 模式 | 条件 | 681 见过？ |
|---|---|---|
| **被更高的 z 盖住**（`z-40` 底栏压 `z-30` 左栏） | H ≥ 336 | **是**（681 只测了 H ≥ 720） |
| **被推出画布下沿**（`overflow: visible` + 内容 284 > 248） | H < 336 | **否** |

**同一个控件，两种完全不同的失效模式，而 681 的采样区间整段落在第一种。**

## 自记：同一个错，本批犯了**三次**

**「跨高度取并集」和「逐高度比集合」是两件事，而我在本批把前者当后者用了三次：**

1. **探针**用 `setdefault` 把每条轨道的 3 枚导航钮折叠成一枚 ⟹ 报「只有 1 个键变形」。
   这是**有 bug 的路碰巧给出了正确答案**。
2. **验收器第一版**改用「跨高度取并集」判变化 ⟹ 报「3 个键变形」——
   因为那两条 `track-label` 键**在每一个高度下就有两种尺寸** `{(24,24), (36,18)}`。
3. **「两个宽度是否一致」那条判据**也用了并集 ⟹ 并集含两种尺寸，判据必然失败。

正确判据是**逐高度比较尺寸集合**。修好之后：

- **随高度变形的只有 1 个键**：`帮助`，`{32×20}`（H ≤ 300）/ `{32×32}`（H ≥ 400）；
- **另有两个键在每个高度下就有两种尺寸**（两条轨道的 `data-director-track-label`），
  这是**另一种异质性**——**673 那条「异类合并」的尺寸版**（673 是名字版的）。

**一条读数是「随高度变形」、另一条是「同一键两种尺寸」，两者都不该混进对方的统计里。**

## 不声称

- **不声称** H = 336 是源站的行为（**未取证**；这是 clone 的读数）；
- **不声称** H < 336 时 `帮助` 一定「不可点」——
  它在画布外，`elementFromPoint` 在视口内**采不到它**，
  这与「采得到但被盖住」是**两种读数**，本批不把前者说成后者；
- **不声称** 12 个窗高覆盖了所有布局临界（本次只测了一个宽度方向的临界）。
"""

import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch683-2026-10-01"

WIDTHS = [1280, 1920]
HEIGHTS = [180, 240, 300, 400, 500, 600, 720, 850, 1000, 1150, 1400, 1700]
HELP = "data-director-rail-entry=help"
RAIL_TOP = 52          # 左栏容器是 top-[52px]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

JS = r"""() => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = 'button, [role=button], [role=tab], [role=switch], [role=slider],'
    + ' [role=menuitem], input, select, textarea, a[href],'
    + ' [tabindex]:not([tabindex="-1"])';
  const cs = (e) => getComputedStyle(e);
  const dataOf = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement)
      for (const a of n.attributes) if (a.name.startsWith('data-')) return a.name + '=' + a.value;
    return '-'; };
  // **不**在这里剔除零尺寸 —— 恒定零尺寸本身是 671 记的盲区，要留下来说话
  const rows = [];
  for (const e of scope.querySelectorAll(SEL)) {
    const s = cs(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (parseFloat(s.opacity) === 0) continue;
    const r = e.getBoundingClientRect();
    rows.push({data: dataOf(e),
               box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]});
  }
  const help = document.querySelector('[data-director-rail-entry="help"]');
  let rail = help;
  while (rail && rail.parentElement && cs(rail).position === 'static')
    rail = rail.parentElement;
  const rr = rail.getBoundingClientRect(), hr = help.getBoundingClientRect();
  const rs = cs(rail);
  return {vw: innerWidth, vh: innerHeight, rows,
          rail: {box: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
                 clientH: rail.clientHeight, scrollH: rail.scrollHeight,
                 overflowY: rs.overflowY},
          help: {box: [Math.round(hr.x), Math.round(hr.y), Math.round(hr.width), Math.round(hr.height)],
                 bottomFromViewportBottom: Math.round(innerHeight - (hr.y + hr.height)),
                 fullyBelowFold: hr.y >= innerHeight}};
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
        self.result[name] = {"ok": bool(ok), "detail": detail, "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:130]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS:
            for h in HEIGHTS:
                page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                b617.open_desk(page)
                _clean(page)
                cells[f"{w}x{h}"] = page.evaluate(JS)
                page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    keys = [f"{w}x{h}" for w in WIDTHS for h in HEIGHTS]
    pop = {k: len(cells[k]["rows"]) for k in keys}

    zero_per_cell = {k: sum(1 for r in cells[k]["rows"]
                            if r["box"][2] == 0 or r["box"][3] == 0) for k in keys}
    zero_keys = {r["data"] for k in keys for r in cells[k]["rows"]
                 if r["box"][2] == 0 or r["box"][3] == 0}
    zero_series = {k: sorted({tuple(r["box"]) for r in cells[k]["rows"]
                              if r["box"][2] == 0 or r["box"][3] == 0}) for k in keys}

    # 每格每键的**尺寸集合**。判「随高度变形」必须逐高度比集合，
    # **不能跨高度取并集** —— 同一个键本来就可能在一个高度下就有两种尺寸。
    sizes_at: dict[str, dict[int, set]] = defaultdict(lambda: defaultdict(set))
    for k in keys:
        h = int(k.split("x")[1])
        for r in cells[k]["rows"]:
            if r["box"][2] and r["box"][3]:
                sizes_at[r["data"]][h].add((r["box"][2], r["box"][3]))
    # 随高度变形 = 逐高度的尺寸集合**不相同**
    varying = sorted(d for d, byh in sizes_at.items()
                     if len({frozenset(s) for s in byh.values()}) > 1)
    # 同一键在**每个**高度下就有多种尺寸（另一种异质性，与「随高度变形」无关）
    multi = sorted(d for d, byh in sizes_at.items()
                   if all(len(s) > 1 for s in byh.values()))
    help_sizes = {h: sorted(sizes_at[HELP][h]) for h in HEIGHTS}

    help_by = {k: cells[k]["help"] for k in keys}
    rail_by = {k: cells[k]["rail"] for k in keys}
    thresholds = {}
    for w in WIDTHS:
        crossing = [h for h in HEIGHTS
                    if rail_by[f"{w}x{h}"]["clientH"] >= rail_by[f"{w}x{h}"]["scrollH"]]
        thresholds[w] = {"firstHeightWithNoOverflow": crossing[0] if crossing else None,
                         "scrollH": {h: rail_by[f"{w}x{h}"]["scrollH"] for h in HEIGHTS},
                         "clientHatCrossing": (rail_by[f"{w}x{crossing[0]}"]["clientH"]
                                               if crossing else None)}

    v.check("the-control-population-is-identical-at-all-twelve-heights",
            len(set(pop.values())) == 1 and pop[keys[0]] > 100,
            detail={"population": pop, "distinctValues": sorted(set(pop.values()))},
            note="the layout neither adds nor removes a control as the viewport gets "
                 "shorter — 12 cells, one number")

    v.check("the-two-zero-sized-controls-are-constant-not-a-short-viewport-effect",
            len(zero_keys) == 1 and set(zero_per_cell.values()) == {2}
            and all(v == [(0, 0, 0, 0)] for v in zero_series.values()),
            detail={"zeroPerCell": zero_per_cell,
                    "zeroDataKeys": sorted(zero_keys),
                    "boxesPerCell": zero_series,
                    "relationTo671":
                        "671 recorded zero-sized controls as a census blind spot. These "
                        "two are zero at EVERY height, so they are a constant property, "
                        "NOT something a short viewport did."},
            note="do not read 'zero' as 'squeezed away' — that is 682's mistake once more")

    v.check("exactly-one-control-deforms-with-height-and-it-is-the-help-button",
            varying == [HELP]
            and all(help_sizes[h] == [(32, 20)] for h in HEIGHTS if h <= 300)
            and all(help_sizes[h] == [(32, 32)] for h in HEIGHTS if h >= 400),
            detail={"keysWithVaryingSizePerHeight": varying,
                    "helpSizeByHeight": help_sizes,
                    "allOtherKeysConstantAcrossHeights": len(sizes_at) - len(varying)},
            note="one control out of the whole population changes size across 12 heights")

    v.check("two-data-keys-carry-two-different-sizes-at-every-height",
            len(multi) == 2
            and all(len(s) == 2 for d in multi for s in sizes_at[d].values())
            and all(len({frozenset(s) for s in sizes_at[d].values()}) == 1 for d in multi),
            detail={"keysWithMultipleSizesAtEveryHeight": multi,
                    "theirSizes": {d: sorted({tuple(s) for s in sizes_at[d].values()})[0]
                                   for d in multi},
                    "sizes24x24_and_36x18":
                        "each track's three nav buttons are NOT all the same size — a "
                        "36x18 one sits among 24x24 ones. This is heterogeneity WITHIN a "
                        "data key, and it is constant in height — a different axis from "
                        "'deforms with height'."},
            note="a same-key-different-size population, the size-side twin of 673's "
                 "异类合并 (which was name-side)")

    v.check("the-threshold-is-52-plus-284-and-682s-grid-straddled-it-without-landing-on-it",
            all(thresholds[w]["firstHeightWithNoOverflow"] == 400 for w in WIDTHS)
            and all(rail_by[f"{w}x{h}"]["scrollH"] == max(284, rail_by[f"{w}x{h}"]["clientH"])
                    for w in WIDTHS for h in HEIGHTS)
            and all(rail_by[f"{w}x{h}"]["scrollH"] == 284
                    for w in WIDTHS for h in HEIGHTS if h <= 300),
            detail={"thresholds": thresholds,
                    "rule": "the rail stops overflowing where clientHeight (H-52) reaches the "
                            "content height 284 — i.e. H = 336. scrollH itself "
                            "tracks max(284, clientH), so it reads 284 only "
                            "while the rail is actually overflowing.",
                    "sampledHeightsAroundIt": [300, 400],
                    "derivedThreshold": 52 + 284,
                    "measuredFirstNonOverflowingHeight": 400,
                    "whyNot360": "360 would have been the first non-overflowing SAMPLE, "
                                 "but it is not in this batch's height list — 300 and 400 "
                                 "straddle the derived 336.",
                    "whyItMatters": "682 sampled 300 and 400, so it bracketed the "
                                    "threshold and never landed on it"},
            note="the threshold is measured from clientH == scrollH, not guessed")

    v.check("below-the-threshold-help-leaves-the-canvas-above-it-it-sits-8px-from-the-bottom",
            all(help_by[k]["box"][3] == 20 and help_by[k]["fullyBelowFold"]
                for k in keys if help_by[k]["box"][3] == 20)
            and all(help_by[k]["bottomFromViewportBottom"] == 8
                for k in keys if help_by[k]["box"][3] == 32),
            detail={"helpByCell": help_by},
            note="two DIFFERENT failure modes, not two sizes of one")

    v.check("the-spill-is-painted-outside-the-box-not-scrolled-or-clipped",
            all(rail_by[k]["overflowY"] == "visible" for k in keys)
            and all(rail_by[k]["scrollH"] >= rail_by[k]["clientH"] for k in keys),
            detail={"overflowY": {k: rail_by[k]["overflowY"] for k in keys},
                    "overflowBy": {k: rail_by[k]["scrollH"] - rail_by[k]["clientH"]
                                   for k in keys},
                    "why": "overflow-y: visible means the rail paints outside its own box, "
                           "so 帮助 leaves the canvas instead of being scrolled into view"},
            note="this is why the failure is 'not on the canvas', not 'on the canvas but "
                 "unclickable'")

    v.check("both-widths-agree-on-everything",
            all(help_by[f"1280x{h}"]["box"][2:] == help_by[f"1920x{h}"]["box"][2:]
                for h in HEIGHTS)
            and len({pop[f"{w}x{h}"] for w in WIDTHS for h in HEIGHTS}) == 1,
            detail={"helpSizeByHeightAndWidth": {
                        str(h): {str(w): help_by[f"{w}x{h}"]["box"][2:] for w in WIDTHS}
                        for h in HEIGHTS},
                    "populationDistinct": sorted({pop[f"{w}x{h}"] for w in WIDTHS
                                                 for h in HEIGHTS})},
            note="compared PER HEIGHT. A union across heights trivially contains both "
                 "sizes and proves nothing — that mistake was made twice in this batch")

    out = {"widths": WIDTHS, "heights": HEIGHTS, "cells": keys,
           "population": pop, "zeroPerCell": zero_per_cell,
           "keysWithVaryingSizePerHeight": varying,
           "keysWithMultipleSizesAtEveryHeight": multi,
           "helpSizeByHeight": help_sizes,
           "thresholds": thresholds,
           "helpByCell": help_by,
           "railByCell": {k: rail_by[k] for k in keys},
           "judged": sum(pop[k] for k in keys)}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

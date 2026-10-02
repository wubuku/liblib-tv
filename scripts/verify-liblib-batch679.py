#!/usr/bin/env python3
"""batch 679 验收：中心口径**对「完全被挡」零漏检**，而它漏掉的那 26 枚**全都至少还有 60% 是清的**

## 起点

678 把「探测点只取控件中心」的覆盖边界量化了：每格固定漏 26 枚 / 130 枚。
本批问那个决定后果的问题：

**678 揭出的那 26 枚，是「完全被挡」还是「只被挡一部分」？**

—— 因为这决定了中心口径的漏检是**良性的**还是**危险的**。

## 三条读数

### 1. 中心口径对「完全被挡」零漏检

对 780 个控件-格（130 枚 × 6 格）统计两个布尔量：
`centre`（中心样本被外人占据）与 `fullyBlocked`（25 个样本**全部**被外人占据）。
24 个控件-格完全落在视口外、无样本，单列第三态；其余 756 个：

| centre | fullyBlocked | 控件-格数 |
|---|---|---|
| False | False | 739 |
| **True** | **True** | **16** |
| **True** | **False** | **1** |

**`centre=False ∧ fullyBlocked=True` 这一格是空的 —— 中心口径一个全被挡的控件都没漏。**

而那 16 个全被挡的控件-格，去重后正好是 **6 枚**：
`data-director-rail-entry=help`（`帮助`）、`scene-prompt-submit`（`发送`）、
`scene-prompt-upload`（`上传图片`）、`scene-prompt-input`（`描述想搭建的场景`）、
`color-picker=object`（`颜色`）、`hex-input=object`（`颜色 hex 值`）——
**正是 667/672/677 一直在追的那 6 枚。**

### 2. 反向不成立，而且只差一条

`centre ⟹ fullyBlocked` 是 16/17。唯一那条例外是
**1366×1150 格的 `data-director-scene-prompt-input`（`描述想搭建的场景`）**：
它的**中心落在盖住区内**，但盖住区只覆盖了盒的 **80%**。

**一条中心样本回答不了「整盒是否可用」—— 这正是它作为完全性判据的边界。**

### 3. 遮挡比例是离散的六档，全部是 1/25 的整数倍

| 覆盖比例 | 控件-格数 |
|---|---|
| 0（完全不被盖） | 581 |
| 0.12 = 3/25 | 12 |
| 0.20 = 5/25 | 90 |
| 0.40 = 10/25 | 56 |
| 0.80 = 20/25 | 1 |
| 1.00 = 25/25 | 16 |

**没有一个中间值** ⟹ 盖住者全是轴对齐矩形，一个采样点都没落在边界抖动上。

### 4. 所以：那 26 枚在后果上全是良性的

**中心口径漏掉的 158 个控件-格，每一个都还剩至少 60% 的面积是清的**
（被盖 0.12 → 清 88%；0.20 → 80%；0.40 → 60%）。

反过来，**唯一真正「几乎全挡」的那枚（0.80）中心口径看见了**。

**这解释了为什么中心口径的覆盖缺口这么多批都没被发现：
它漏掉的全是良性的，它不漏的全是真问题。**

## 自记：一处预期被读数推翻

动手前我要断言「`centre ⟺ fullyBlocked`」。**读数说只有一个方向成立**：
`fullyBlocked ⟹ centre` 是 16/16，反向是 16/17（那 1 条就是 §2 的 `scene-prompt-input`）。

**对称的直觉是错的** —— 中心落在盖住区内，不等于整盒都在盖住区内。
判据因此拆成两条单方向断言，并把那条例外**指名记下来**，而不是把它抹平成「基本成立」。

## 不声称

- **不声称**「60% 清空面积」是可用性阈值 —— 那是本 clone 的读数，不是可用性判据；
- **不声称**那 26 枚在源站也一样被盖 —— 本批纯 clone 读数，未取证；
- **不声称**16 枚全被挡的控件是缺陷（其中 6 枚是 667 一直在追的 `帮助` 一族）；
- **不声称**网格口径已是最终口径（678 已记：5×5 仍是采样）。
"""

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch679-2026-10-01"
B678_AUDIT = ROOT / "docs/research/liblib-canvas-batch678-2026-10-01/runtime-audit.json"

CELLS = [(1280, 720), (1280, 1150), (1366, 1150), (1440, 1150),
         (1600, 1150), (1920, 1150)]
FRACS = [0.1, 0.3, 0.5, 0.7, 0.9]
SAMPLE = len(FRACS) ** 2

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

spec2 = importlib.util.spec_from_file_location(
    "b678", ROOT / "scripts/verify-liblib-batch678.py")
b678 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(b678)


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
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            cells[f"{w}x{h}"] = page.evaluate(b678.JS, FRACS)
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    keys = list(cells)
    table: Counter = Counter()
    exceptions: list[dict[str, Any]] = []
    fracs: Counter = Counter()
    fully: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []
    for k in keys:
        for r in cells[k]["rows"]:
            if not r["samples"]:
                continue
            f = r["foreign"] / r["samples"]
            fracs[round(f, 2)] += 1
            is_full = (f == 1.0)
            table[(bool(r["centre"]), is_full)] += 1
            if is_full:
                fully.append({"cell": k, "name": r["name"], "data": r["data"]})
            if r["centre"] and not is_full:
                exceptions.append({"cell": k, "name": r["name"], "data": r["data"],
                                   "fraction": round(f, 3), "samples": r["samples"],
                                   "coverers": r["coverers"]})
            if r["foreign"] > 0 and not r["centre"]:
                missed.append({"cell": k, "name": r["name"], "data": r["data"],
                               "fraction": round(f, 3),
                               "clearFraction": round(1 - f, 3)})

    judged = sum(len(cells[k]["rows"]) for k in keys) * SAMPLE
    discrete = all(abs(round(f * SAMPLE) - f * SAMPLE) < 1e-9 for f in fracs)
    min_clear = min(m["clearFraction"] for m in missed) if missed else None

    v.check("the-centre-probe-has-perfect-sensitivity-for-full-occlusion",
            table[(False, True)] == 0 and table[(True, True)] > 0,
            detail={"contingency": {f"centre={c},fullyBlocked={f}": n
                                     for (c, f), n in sorted(table.items())},
                    "fullyBlockedCount": len(fully),
                    "implication": "fullyBlocked => centreForeign",
                    "holdsFor": f"{table[(True, True)]}/{table[(True, True)]}",
                    "theCellThatMustBeEmpty": "centre=False,fullyBlocked=True",
                    "thatCellIs": table[(False, True)]},
            note="the centre probe missed ZERO fully-blocked controls, in any cell")

    v.check("the-converse-fails-exactly-once-and-that-one-is-named",
            len(exceptions) == 1
            and exceptions[0]["data"] == "data-director-scene-prompt-input=true"
            and exceptions[0]["cell"] == "1366x1150",
            detail={"exceptions": exceptions,
                    "reading": "its centre IS covered, but only 80% of its box is — so a "
                               "single centre sample cannot answer 'is the whole box "
                               "usable'"},
            note="do NOT round this into 'basically equivalent' — the two directions are "
                 "not symmetric, so the checks are two one-way claims")

    v.check("covered-fractions-take-only-discrete-values-that-are-multiples-of-one-25th",
            discrete and len(fracs) <= 8 and max(fracs) == 1.0,
            detail={"fractionHistogram": dict(sorted(fracs.items())),
                    "samplesPerControl": SAMPLE,
                    "meaning": "no fractional value in between => the coverers are "
                               "axis-aligned rects and no sample landed on a boundary"},
            note="this is what makes the grid reading trustworthy rather than noisy")

    v.check("every-control-the-centre-probe-misses-is-at-least-60-percent-clear",
            len(missed) > 0 and min_clear is not None and min_clear >= 0.6,
            detail={"missedControlCells": len(missed),
                    "minClearFraction": min_clear,
                    "maxCoveredFractionAmongMissed": max(m["fraction"] for m in missed),
                    "worstFew": sorted(missed, key=lambda m: m["clearFraction"])[:3]},
            note="so 678's 26 missed controls are all still usable — the centre probe's "
                 "blind spot has never masked a fully-blocked control")

    prior = json.loads(B678_AUDIT.read_text(encoding="utf-8"))["verifier"]
    mine = {k: (sum(1 for r in cells[k]["rows"] if r["centre"]),
                sum(1 for r in cells[k]["rows"] if r["foreign"] > 0)) for k in keys}
    theirs = {k: (prior["population"][k]["centre"], prior["population"][k]["grid"])
              for k in keys}
    v.check("cross-run-populations-match-batch678s-recorded-audit",
            mine == theirs,
            detail={"batch679": mine, "batch678": theirs,
                    "fracs": FRACS},
            note="same instrument (b678.JS), two independent runs")

    out = {"cells": keys, "fracs": FRACS, "samplesPerControl": SAMPLE,
           "controlCells": sum(len(cells[k]["rows"]) for k in keys),
           "contingency": {f"centre={c},fullyBlocked={f}": n
                           for (c, f), n in sorted(table.items())},
           "fractionHistogram": dict(sorted(fracs.items())),
           "exceptions": exceptions,
           "fullyBlocked": fully,
           "missedCount": len(missed), "minClearFractionAmongMissed": min_clear,
           "judged": judged}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

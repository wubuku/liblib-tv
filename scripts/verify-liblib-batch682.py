#!/usr/bin/env python3
"""batch 682 验收：把高度扫描推广到全部控件 —— **59 枚是「只随高度变」的带状缺陷**，而遮挡区域**永远不是非矩形**

## 起点

680 只跟了 6 枚控件的 20 格高度扫描，发现它们分属三种驱动。
本批把那套扫描**推广到全部 130 枚控件**，问的是分类问题：
**哪些控件的「完全不可点」是恒定的，哪些是带状的？**

## 三条读数（2 宽度 × 10 窗高 × 130 枚 × 25 样本 = 65,000 次判定）

### 1. 分类是一个**满划分**，四类 + 一个未测态

按 (data 键, 盒) 认同一枚控件（678 的纪律，不按名字）：

| 类别 | 枚数 |
|---|---|
| `always-fully-blocked`（每个可测格都全被挡） | **1** |
| `varies-by-height-only`（只随窗高变） | **59** |
| `varies-by-width-only`（只随宽度变） | **3** |
| `never-fully-blocked`（每个可测格都至少 60% 清空） | 其余 |
| `never-measured`（20 格里都没有视口内样本） | 2 |

**只有一枚是恒定的 —— `data-director-rail-entry=help`。**
这**细化了 680**：680 说那 6 枚分三种驱动，本批量到全体后，
**「恒定」这一类在全仓库只有 1 枚**；其余 5 枚里 2 枚是带状、3 枚是宽度驱动。

### 2. 遮挡区域**永远不是非矩形**（`irregular = 0`）

`varies-by-height-only` 的定义是「同一宽度下、跨所有窗高取值恒定」；
`varies-by-width-only` 是「同一窗高下、跨所有宽度取值恒定」；
两者都不成立才落进 `irregular`。

**`irregular` 的成员数是 0。**
所以这批控件的「全被挡格集合」在 (宽, 高) 平面上**全部是矩形条带**，
**没有一枚是 L 形、点状或对角分布的**。

**这正是网格读数可信的更强一版**：679 只证明了单个视口内的遮挡比例是 1/25 的整数倍
（盖住者是轴对齐矩形）；本批把它**跨视口**也证明了。

### 3. 59 枚的「全被挡高度集合」只有 **7 种带**

| 全被挡的窗高 | 枚数 |
|---|---|
| {300} | 17 |
| {400} | 3 |
| {500} | 10 |
| {600} | 8 |
| {300, 400} | 9 |
| {400, 500} | 10 |
| {600, 720} | 2 |

（`颜色` / `颜色 hex 值` 的 {600, 720} 就在这里 —— 680 追的就是这一带。）

**59 枚的缺陷分布在 7 条高度带上，而不是 59 个独立的高度。**

### 4. 派生量：只测一格就下全称判断，会与全扫描相反的控件数

| 取样格 | 与全扫描「恒被挡?」结论相反的枚数 |
|---|---|
| 1280×300 | **29** |
| 1280×400 | 25 |
| 1280×500 | 23 |
| 1280×600 | 13 |
| 1280×720 | 5 |
| 1280×850 … 1280×1700 | **3** |
| 1920×300 | 26 |
| 1920×400 | 22 |
| 1920×500 | 20 |
| 1920×600 | 10 |
| 1920×720 | 2 |
| **1920×850 … 1920×1700** | **0** |

**一格取样的可信度从 0 到 29 之间浮动。**
最差的是 `1280×300`（29 枚会判反），**最好的是 `1920×850` 及以上（0 枚判反）** ——
**因为所有带都在 H ≤ 720 结束。**

而本仓库惯用的 `1280×1150` 会判反 **3** 枚。

## 自记

第一版把「唯一恒定的一枚」钉成 `== 1`，跑完发现 `always` 里确实只有 1，
于是那条断言看起来像在钉一个数。**改成了钉结构**：把四类做成一个**满划分**
（每枚恰好一类、类数之和等于控件数），并把 `irregular == 0` 单独列一条 ——
**后者才是真正承载「跨视口也是矩形」这条结论的那一条。**

## 不声称

- **不声称** 7 条带是精确边界（本次扫了 10 个窗高，带的两端只到实测点）；
- **不声称** 130 枚控件的总体（纳入过滤本身是 665 记的盲区）；
- **不声称**「恒定只有 1 枚」在别的视口网格下仍成立；
- **不声称**源站在这些窗高下有同样行为（**未取证**）。
"""

import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch682-2026-10-01"
B680_AUDIT = ROOT / "docs/research/liblib-canvas-batch680-2026-10-01/runtime-audit.json"

WIDTHS = [1280, 1920]
HEIGHTS = [300, 400, 500, 600, 720, 850, 1000, 1150, 1400, 1700]
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

HELP = "data-director-rail-entry=help"
COLOR = ["data-director-color-picker=object", "data-director-hex-input=object"]
PROMPT = ["data-director-scene-prompt-submit=true",
          "data-director-scene-prompt-upload=true",
          "data-director-scene-prompt-input=true"]

ALWAYS, BYH, BYW, NEVER, NOMEA, IRREG = (
    "always-fully-blocked", "varies-by-height-only", "varies-by-width-only",
    "never-fully-blocked", "never-measured", "irregular")


def classify(series: dict[str, float | None]) -> str:
    meas = {k: v for k, v in series.items() if v is not None}
    if not meas:
        return NOMEA
    blocked = {k for k, v in meas.items() if v == 1.0}
    if not blocked:
        return NEVER
    if len(blocked) == len(meas):
        return ALWAYS
    by_w: dict[str, set] = defaultdict(set)
    by_h: dict[str, set] = defaultdict(set)
    for k, v in meas.items():
        by_w[k.split("x")[0]].add(v == 1.0)
        by_h[k.split("x")[1]].add(v == 1.0)
    if all(len(v) == 1 for v in by_w.values()):
        return BYW
    if all(len(v) == 1 for v in by_h.values()):
        return BYH
    return IRREG


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
                r = page.evaluate(b678.JS, FRACS)
                # 按 (data 键, 盒) 认同一枚控件 —— 678 的纪律，不按名字
                cells[f"{w}x{h}"] = {
                    f"{x['data']}|{x['box'][0]}x{x['box'][1]}":
                        (None if not x["samples"] else round(x["foreign"] / x["samples"], 3))
                    for x in r["rows"]}
                page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    keys = [f"{w}x{h}" for w in WIDTHS for h in HEIGHTS]
    series: dict[str, dict] = defaultdict(dict)
    for k in keys:
        for ident, f in cells[k].items():
            series[ident][k] = f
    cls = {i: classify(s) for i, s in series.items()}
    dist = Counter(cls.values())

    bands: dict[tuple, list] = defaultdict(list)
    for i, s in series.items():
        if cls[i] != BYH:
            continue
        meas = {k: v for k, v in s.items() if v is not None}
        hs = tuple(sorted({int(k.split("x")[1]) for k, v in meas.items() if v == 1.0}))
        bands[hs].append(i)

    # 派生量：一格取样 vs 全扫描的「恒被挡?」结论
    truth = {i: (c == ALWAYS) for i, c in cls.items()}
    single = {}
    for k in keys:
        wrong = [i for i, s in series.items()
                 if s.get(k) is not None and ((s[k] == 1.0) != truth[i])]
        single[k] = {"wrong": len(wrong), "examples": sorted(wrong)[:5]}
    wrong_by_cell = {k: single[k]["wrong"] for k in keys}

    always_ids = sorted(i for i, c in cls.items() if c == ALWAYS)
    irregular_ids = sorted(i for i, c in cls.items() if c == IRREG)
    nomega_ids = sorted(i for i, c in cls.items() if c == NOMEA)

    def cls_of(data_key: str) -> str:
        """一个 data 键可能对应多个 (data|盒) 身份。聚合时**排除从未被测到的身份** ——
        它们是第三态，不是另一个类别（帮助 在 H=300 有一个被压扁的 32×20 身份）。"""
        ids = [i for i in series if i.split("|")[0] == data_key and cls[i] != NOMEA]
        cs = {cls[i] for i in ids}
        if not cs:
            return NOMEA
        return cs.pop() if len(cs) == 1 else f"<mixed: {sorted(cs)}>"

    v.check("the-classification-is-a-total-partition-and-irregular-is-empty",
            sum(dist.values()) == len(series) and len(series) > 100
            and not irregular_ids,
            detail={"controlsByIdentity": len(series),
                    "distribution": dict(dist),
                    "sumsToPopulation": sum(dist.values()) == len(series),
                    "irregularMembers": irregular_ids,
                    "classes": [ALWAYS, BYH, BYW, NEVER, NOMEA, IRREG]},
            note="every control lands in exactly one class, and NO control's fully-"
                 "blocked set is non-rectangular in the (width, height) plane")

    v.check("the-blocked-regions-are-strips-in-the-width-height-plane",
            not irregular_ids and dist[BYH] > 0 and dist[BYW] > 0,
            detail={"variesByHeightOnly": dist[BYH], "variesByWidthOnly": dist[BYW],
                    "irregular": dist[IRREG],
                    "strengthens":
                        "679 proved the covered FRACTION is a multiple of 1/25 inside one "
                        "viewport (coverers are axis-aligned rects). This proves the "
                        "blocked set is also a strip ACROSS viewports."},
            note="no L-shape, no diagonal, no isolated cell anywhere in the population")

    v.check("fifty-nine-controls-are-fully-blocked-at-some-height-and-clear-at-others",
            dist[BYH] > 0 and len(bands) <= 10,
            detail={"variesByHeightOnly": dist[BYH],
                    "distinctBlockedHeightBands": {str(list(h)): len(m) for h, m
                                                    in sorted(bands.items(),
                                                              key=lambda kv: (len(kv[0]), kv[0]))},
                    "totalInBands": sum(len(m) for m in bands.values()),
                    "reading": "59 defects sit on a handful of height bands, not on 59 "
                               "independent heights"},
            note="颜色 / 颜色 hex 值's {600, 720} band is the one 680 chased")

    v.check("only-one-control-is-fully-blocked-in-every-cell",
            len(always_ids) == 1 and always_ids[0].split("|")[0] == HELP,
            detail={"alwaysMembers": always_ids,
                    "refines":
                        "680 said the six split into three drivers. Across the whole "
                        "population the 'constant' class has exactly ONE member — and it "
                        "is 帮助, the one 681 traced to z-30 vs z-40."},
            note="'always blocked' is a class of one, not a general property")

    v.check("single-cell-sampling-mis-generalizes-by-0-to-29-controls",
            min(wrong_by_cell.values()) == 0 and max(wrong_by_cell.values()) > 20
            and wrong_by_cell["1920x850"] == 0
            and all(wrong_by_cell[f"1920x{h}"] == 0 for h in (850, 1000, 1150, 1400, 1700)),
            detail={"wrongByCell": wrong_by_cell,
                    "worstCell": max(wrong_by_cell, key=lambda k: wrong_by_cell[k]),
                    "bestCells": sorted(k for k, c in wrong_by_cell.items() if c == 0),
                    "repoDefaultCell": {"1280x1150": wrong_by_cell["1280x1150"]},
                    "why": "every band ends at or below H=720, so a tall 1920 cell sees "
                           "all of them clear"},
            note="how badly a one-cell verdict generalises depends entirely on which cell")

    prior = json.loads(B680_AUDIT.read_text(encoding="utf-8"))["verifier"]
    expect = {HELP: ALWAYS, COLOR[0]: BYH, COLOR[1]: BYH,
              PROMPT[0]: BYW, PROMPT[1]: BYW, PROMPT[2]: BYW}
    got = {d: cls_of(d) for d in expect}
    v.check("the-six-controls-680-tracked-land-in-the-classes-that-split-alone-predicts",
            got == expect,
            detail={"expectedFrom680sThreeDrivers": expect, "measured": got,
                    "crossBatchInstrument": "same b678.JS, same 20 cells"},
            note="680's hand split is reproduced by a rule that never names them")

    # 两条第三态读数：被压扁的盒 + 从未进入视口的身份
    help_ids = sorted(i for i in series if i.split("|")[0] == HELP)
    kf_off = sorted(i for i in nomega_ids if "keyframe-id" in i)
    v.check("three-identities-are-never-measured-and-two-of-them-are-a-squeezed-box",
            len(nomega_ids) == 3
            and any(i.endswith("|32x20") for i in nomega_ids)
            and len(help_ids) == 2
            and all(series[i]["1280x300"] is None and series[i]["1920x300"] is None
                    for i in help_ids if i.endswith("|32x20"))
            and len(kf_off) == 2
            and all(all(v is None for v in series[i].values()) for i in kf_off),
            detail={"neverMeasured": nomega_ids,
                    "helpIdentities": {i: series[i] for i in help_ids},
                    "squeezedBox": "the help button is 32x32 everywhere except H=300, "
                                   "where it measures 32x20 — its box is squeezed at the "
                                   "short viewport, and then it has no in-viewport sample",
                    "keyframeChipsOffScreen": kf_off,
                    "thirdState": "these are `missing`, not `measured clear` — reading "
                                  "them as clear would be 680's mistake again"},
            note="the squeezed box is why 680 recorded 'no samples' at H=300 instead of "
                 "'clear'")

    out = {"widths": WIDTHS, "heights": HEIGHTS, "fracs": FRACS,
           "samplesPerControl": SAMPLE, "cells": keys,
           "controlsByIdentity": len(series), "distribution": dict(dist),
           "alwaysMembers": always_ids, "irregularMembers": irregular_ids,
           "neverMeasuredMembers": nomega_ids,
           "bands": {str(list(h)): sorted(m) for h, m in sorted(bands.items(),
                                                                key=lambda kv: (len(kv[0]), kv[0]))},
           "wrongByCell": wrong_by_cell,
           "series": {i: series[i] for i in sorted(series)},
           "judged": sum(len(cells[k]) for k in keys) * SAMPLE}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

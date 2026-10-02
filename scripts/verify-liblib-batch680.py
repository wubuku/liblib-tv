#!/usr/bin/env python3
"""batch 680 验收：扫**窗高** —— 679 那「6 枚完全不可用」不是一个类，是**三种不同驱动**的三个类

## 起点

679 用 667 自己的 6 个**宽度**格定出：130 枚控件里 6 枚完全不可点，其余漏掉的都 ≥60% 可点。

但那 6 枚是**一个类**吗？本批把**窗高**扫一遍 —— 此前所有批次扫的都是宽度，
630 之后窗高这一维基本没人动过。

## 三条读数（10 个窗高 × 2 个宽度 = 20 格，130 枚控件 × 25 样本 = 65,000 次判定）

### 0. 先记一条布局不变量：时间轴恒高 145、底锚定

`[data-director-timeline-track-list]` 的盒在**每一格**都是 `y = H − 145`、`h = 145`。

**所以调窗高不改变时间轴内部任何东西的相对位置** ——
高度这一维**无法靠「让时间轴挪一挪」来解掉任何遮挡**。

### 1. `帮助`（`data-director-rail-entry=help`）**永不可点**

在**所有**有样本的 (宽, 高) 组合下 `frac = 1.00`（25/25 全被盖），
盖住者**始终是同一族**：`button.group.relative`（时间轴对象行的 `收起属性` 箭头）
与 `div.group.relative`（它的包装）。

**679 说它「6 格恒定」是对的，但那句话只覆盖了宽度；本批补上：高度也一样。**
它不是某个宽度下的问题 —— **在本次扫描的 18 个可测格子里它一次都没能被点到。**

### 2. `颜色` / `颜色 hex 值`：**带状**不可点，不是单调的

| 窗高 | 在视口内？ | frac |
|---|---|---|
| H ≤ 500 | **否（无样本，第三态）** | — |
| **H = 600 / 720** | 是 | **1.00（全被盖）** |
| **H ≥ 850** | 是 | **0.00（完全可点）** |

**在被盖住与完全可点之间没有中间态**，而且**盖住者随高度换人**：
H=600 是 `div.relative.h-8`（整行包装，25/25），
H=720 是颜色色块按钮 `button.relative.flex` 与 `div.absolute.right-0`。

**「不可点」在这一族上是一个区间，不是一个趋势。** 只测 H=1150 会得出「它们是可点的」，
只测 H=720 会得出「它们永远不可点」—— **两个都会是错的。**

### 3. 三枚提示条控件：**宽度驱动**，与高度无关

`scene-prompt-submit` / `-upload` / `-input`：
**W=1280 时在每个有样本的窗高下都是 `1.00`；W=1920 时 H ≥ 400 全部 `0.00`。**
但它们的**盖住者随高度大幅换人**（`header.flex.h-12` → `fieldset` → `legend` →
`div.min-h-0.flex-1`）—— 也就是说**提示条自己的内容在 W=1280 下互相压住**，
压住谁取决于窗高。

## 结论：679 的「6 枚」是三个类的并集

| 驱动 | 控件 | 读数形状 |
|---|---|---|
| **与宽高都无关** | `帮助` | 恒 1.00 |
| **窗高（带状）** | `颜色` / `颜色 hex 值` | 1.00 仅在 H ∈ [600, 720]，H ≥ 850 转 0.00 |
| **宽度** | `发送` / `上传图片` / `描述想搭建的场景` | W=1280 恒 1.00，W=1920 转 0.00 |

**「6 枚完全不可点」这句话没错，但它掩盖了三种修法完全不同的缺陷。**

## 自记

本批**没有预期被推翻** —— 我事先猜的是「高度会救回一部分」，读数说
`帮助` 一枚也救不回。这条要记下来：**猜对不构成证据，7 条判据仍然逐条钉住读数。**

## 不声称

- **不声称**源站在这些高度下有同样行为（**未取证**，本批纯 clone 读数）；
- **不声称**「H ∈ [600,720] 这个带」是精确边界（本次扫了 10 个高度，
  带的两端只到 600 与 720 两个实测点）；
- **不声称**「永不可点」是缺陷还是设计（`帮助` 被时间轴对象行盖住这件事
  667/662 已作在案项；本批只补上「与宽高都无关」这个读数）；
- **不声称** 20 格的扫描覆盖了所有 (宽, 高) 组合。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch680-2026-10-01"
B679_AUDIT = ROOT / "docs/research/liblib-canvas-batch679-2026-10-01/runtime-audit.json"

WIDTHS = [1280, 1920]
HEIGHTS = [300, 400, 500, 600, 720, 850, 1000, 1150, 1400, 1700]
FRACS = [0.1, 0.3, 0.5, 0.7, 0.9]
SAMPLE = len(FRACS) ** 2

HELP = "data-director-rail-entry=help"
COLOR = ["data-director-color-picker=object", "data-director-hex-input=object"]
PROMPT = ["data-director-scene-prompt-submit=true",
          "data-director-scene-prompt-upload=true",
          "data-director-scene-prompt-input=true"]
TRACKED = [HELP] + COLOR + PROMPT

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

# **仪器复用 678 的网格 JS** —— 同一台量具，679/680 的读数因此可直接互相比较
spec2 = importlib.util.spec_from_file_location(
    "b678", ROOT / "scripts/verify-liblib-batch678.py")
b678 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(b678)

TIMELINE_JS = """() => {
  const t = document.querySelector('[data-director-timeline-track-list]');
  if (!t) return null;
  const r = t.getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
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
                r = page.evaluate(b678.JS, FRACS)
                tl = page.evaluate(TIMELINE_JS)
                rec: dict[str, Any] = {"controls": len(r["rows"]),
                                       "timeline": tl, "tracked": {}}
                for t in TRACKED:
                    hit = [x for x in r["rows"] if x["data"] == t]
                    if not hit:
                        rec["tracked"][t] = {"state": "absent"}
                        continue
                    x = hit[0]
                    if not x["samples"]:
                        rec["tracked"][t] = {"state": "no-samples", "box": x["box"]}
                        continue
                    rec["tracked"][t] = {
                        "state": "measured", "box": x["box"],
                        "frac": round(x["foreign"] / x["samples"], 3),
                        "foreign": x["foreign"], "samples": x["samples"],
                        "centre": x["centre"], "coverers": x["coverers"]}
                cells[f"{w}x{h}"] = rec
                page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "cells": cells}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    keys = [f"{w}x{h}" for w in WIDTHS for h in HEIGHTS]

    def frac_of(k: str, t: str) -> Any:
        return cells[k]["tracked"][t].get("frac")

    def state_of(k: str, t: str) -> str:
        return cells[k]["tracked"][t]["state"]

    def series(t: str) -> dict[str, Any]:
        return {k: {"state": state_of(k, t), "frac": frac_of(k, t)} for k in keys}

    # ---- 判据用的派生量 ----
    tl_anchor = all(cells[k]["timeline"] is not None
                    and cells[k]["timeline"][1] == int(k.split("x")[1]) - 145
                    and cells[k]["timeline"][3] == 145 for k in keys)

    help_measured = [k for k in keys if state_of(k, HELP) == "measured"]
    help_all_full = all(frac_of(k, HELP) == 1.0 for k in help_measured)
    help_cleared = [k for k in keys if state_of(k, HELP) == "absent"]
    help_nosample = [k for k in keys if state_of(k, HELP) == "no-samples"]
    help_coverers = sorted({c for k in help_measured for c in cells[k]["tracked"][HELP]["coverers"]})

    color_band = {k: frac_of(k, COLOR[0]) for k in keys if state_of(k, COLOR[0]) == "measured"}
    # 同一高度在两个宽度各出现一次 —— **去重**，否则带的两端会被数成两遍
    band_blocked = sorted({int(k.split("x")[1]) for k, f in color_band.items() if f == 1.0})
    band_clear = sorted({int(k.split("x")[1]) for k, f in color_band.items() if f == 0.0})
    band_partial = sorted({int(k.split("x")[1]) for k, f in color_band.items()
                           if f not in (0.0, 1.0)})
    band_absent = sorted({int(k.split("x")[1]) for k in keys
                          if state_of(k, COLOR[0]) != "measured"})

    prompt_by_w = {w: {h: (frac_of(f"{w}x{h}", PROMPT[0]) if state_of(f"{w}x{h}", PROMPT[0])
                            == "measured" else state_of(f"{w}x{h}", PROMPT[0]))
                       for h in HEIGHTS} for w in WIDTHS}
    prompt_coverer_families = {f"{w}x{h}": sorted(
        cells[f"{w}x{h}"]["tracked"][PROMPT[0]].get("coverers", {}))
        for w in WIDTHS for h in HEIGHTS
        if state_of(f"{w}x{h}", PROMPT[0]) == "measured"}

    v.check("the-timeline-is-145-tall-and-bottom-anchored-at-every-cell",
            tl_anchor,
            detail={"rule": "timeline.y == H - 145 and timeline.height == 145",
                    "boxes": {k: cells[k]["timeline"] for k in keys}},
            note="so no height can move anything inside the timeline relative to the "
                 "bottom edge — height alone cannot unblock anything there")

    v.check("help-is-fully-blocked-in-every-cell-where-it-has-samples",
            help_all_full and len(help_measured) >= 16 and not help_cleared,
            detail={"measuredCells": len(help_measured),
                    "allFull": help_all_full,
                    "neverClear": not help_cleared,
                    "noSamplesCells": help_nosample,
                    "absentCells": help_cleared,
                    "covererIdentities": help_coverers},
            note="679 said '6 格恒定' — that was about width. It is also true across "
                 "every height measured here")

    v.check("the-two-color-controls-are-blocked-in-a-band-not-a-trend",
            band_blocked == [600, 720] and band_clear and min(band_clear) >= 850
            and band_partial == [],
            detail={"blockedHeights": band_blocked, "clearHeights": band_clear,
                    "partialHeights": band_partial,
                    "notMeasuredHeights": band_absent,
                    "notMeasuredState": "below H=600 these two controls have no in-viewport "
                                        "sample at all — that is `no-samples`, NOT `clear`",
                    "covererByHeight":
                        {k: sorted(cells[k]["tracked"][COLOR[0]]["coverers"])
                         for k in keys if state_of(k, COLOR[0]) == "measured"},
                    "perSeries": {t: series(t) for t in COLOR}},
            note="measuring only H=1150 says 'clickable'; only H=720 says 'never "
                 "clickable' — both are wrong")

    v.check("the-three-prompt-controls-are-blocked-at-1280-and-clear-at-1920",
            all(f == 1.0 for h, f in prompt_by_w[1280].items() if isinstance(f, float))
            and all(f == 0.0 for h, f in prompt_by_w[1920].items()
                    if isinstance(f, float) and h >= 400),
            detail={"byWidth": prompt_by_w,
                    "covererIdentitiesByCell": prompt_coverer_families},
            note="width-driven, not height-driven — but WHICH element covers them "
                 "changes with height, so at 1280 the prompt bar's own contents "
                 "overlap each other")

    v.check("the-six-split-into-three-disjoint-drivers",
            len(TRACKED) == 6 and len([HELP] + COLOR + PROMPT) == 6
            and set([HELP]).isdisjoint(COLOR) and set(COLOR).isdisjoint(PROMPT)
            and all(frac_of(k, t) == 1.0 for k in keys
                    if state_of(k, t) == "measured" and t in TRACKED[:1]),
            detail={"heightInvariant": [HELP], "heightBand": COLOR, "widthDriven": PROMPT,
                    "allSixAreTracked": len(TRACKED)},
            note="'6 fully unclickable' is true but hides three defects with three "
                 "different fixes")

    prior = json.loads(B679_AUDIT.read_text(encoding="utf-8"))["verifier"]
    # 679 的 fullyBlocked 逐条带 cell —— **按格对齐**比对，而不是要求每格都该有 6 枚
    fb679_by_cell: dict[str, set] = {}
    for f in prior["fullyBlocked"]:
        fb679_by_cell.setdefault(f["cell"], set()).add(f["data"])
    overlap = {}
    for k in keys:
        h = int(k.split("x")[1])
        if h not in (720, 1150):
            continue
        overlap[k] = {t for t in TRACKED
                      if state_of(k, t) == "measured" and frac_of(k, t) == 1.0}
    shared = sorted(set(overlap) & set(fb679_by_cell))
    mismatched = {k: {"batch679": sorted(fb679_by_cell[k]), "batch680": sorted(overlap[k])}
                  for k in shared if fb679_by_cell[k] != overlap[k]}
    all_keys = {f["data"] for f in prior["fullyBlocked"]}
    v.check("the-cells-shared-with-679-agree-cell-for-cell-on-who-is-fully-blocked",
            len(shared) == 3 and not mismatched and all_keys == set(TRACKED),
            detail={"batch679ByCell": {k: sorted(s) for k, s in sorted(fb679_by_cell.items())},
                    "batch680AtSharedCells": {k: sorted(overlap[k]) for k in shared},
                    "sharedCells": shared,
                    "whyThree": "679 used 1280x720, 1280x1150, 1366x1150, 1440x1150, "
                                "1600x1150, 1920x1150. This batch sweeps both widths at "
                                "ten heights, so the pairs BOTH cover are 1280x720, "
                                "1280x1150 and 1920x1150 — three, not four. 1920x720 "
                                "exists only here, so there is nothing to compare it to.",
                    "mismatched": mismatched,
                    "sameSixControlsOverall": all_keys == set(TRACKED),
                    "whyMembershipNotTotals":
                        "679 used one height per width, this batch sweeps ten, so the "
                        "per-cell counts differ by design. The comparison is per-cell "
                        "membership of the fully-blocked set."},
            note="same instrument on the shared cells — the readings are not run-specific")

    out = {"widths": WIDTHS, "heights": HEIGHTS, "fracs": FRACS,
           "samplesPerControl": SAMPLE, "cells": keys,
           "timelineBoxes": {k: cells[k]["timeline"] for k in keys},
           "series": {t: series(t) for t in TRACKED},
           "help": {"measured": len(help_measured), "allFull": help_all_full,
                    "noSamplesCells": help_nosample, "coverers": help_coverers},
           "colorBand": {"blocked": band_blocked, "clear": band_clear,
                         "partial": band_partial},
           "promptByWidth": prompt_by_w,
           "judged": sum(cells[k]["controls"] for k in keys) * SAMPLE}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": cells, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

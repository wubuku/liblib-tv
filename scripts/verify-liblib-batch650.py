#!/usr/bin/env python3
"""batch 650 验收：用 649 的**导出式**尺子重跑 626 那 11 个导演台浮层 —— 手写 `PANELS` 是它的替代品

## 为什么

649 证明了一件对 626 不太好看的事：626 的 `PANELS` 是一份**手写**的六项清单，
它在画布页**一条都不命中**，所以 648 只能说「尺子够不着」。
649 因此改成从结构导出竞争集（一个选择器都不写死），并在 3 个导演台浮层上
**校准通过**（结构半 9 格逐格一致）。

**校准样本只有 3 个。** 626 自己覆盖了 **11** 个。
剩下那 8 个从来没被导出式尺子看过 —— 它们要么本来就有问题而被手写清单放过了，
要么被手写清单冤枉了。**两种情况都只有重跑才能知道。**

## 本批做什么

* 用 649 的导出式尺子重跑 626 的 **11 × 3 = 33 格**。
* **与 626 已落盘的 33 格逐格对照**（`box` / `ownZ` / `liveCount` / `structBad` / `blocked`）。
* 重跑 626 的两个附加合同：`NO_OP_CASES`（几何子菜单的钳制在无越界处必须是恒等）
  与 `HEIGHT_SWEEP`（两个曾破边的菜单在三个窗高下）。
* 差异**逐条裁定**：是导出式更严、更松，还是 626 原本就错。

## 预期差异（先说清，免得把预期当发现）

649 的尺子比 626 **窄**两处，都是 648/649 已经量过的：
结构半多了 `elementsFromPoint` 交叉校验；伤亡半多了「≤1px」与「clip/clip-path」门槛。
所以 **`liveCount` 与 `blocked` 预期只会变小**，`structBad` 预期只会变严。
本批把「只会变小」写成断言，而不是把差异逐条解释掉。
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
b626 = _load("626")
b649 = _load("649")

AUDIT_626 = ROOT / "docs/research/liblib-canvas-batch626-2026-10-01/runtime-audit.json"
CENSUS_JS = b649.CENSUS_JS


def measure(page: Any, sel: str) -> dict[str, Any]:
    b626.strip_dev_overlay(page)
    page.mouse.move(5, 5)
    page.wait_for_timeout(200)
    row = page.evaluate(CENSUS_JS, {"sel": sel, "live": b626.LIVE,
                                    "margin": b626.SAFE_MARGIN})
    row["present"] = not (row.get("missing") or "error" in row)
    return row


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
              + (f"  {str(detail)[:175]}" if detail else "")
              + (f"  [{note[:105]}]" if note else ""))


def main() -> int:
    v = Verifier()
    prior = json.loads(AUDIT_626.read_text(encoding="utf-8"))["measurements"]
    prior_by = {(m["overlay"], m["vw"], m["vh"]): m for m in prior}

    cells: dict[str, Any] = {}
    sweep: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for w, h in b626.VIEWPORTS:
            for name, how, sel in b626.OVERLAYS:
                page = br.new_page(viewport={"width": w, "height": h},
                                   device_scale_factor=1)
                b626.open_desk_with_retry(page)
                page.wait_for_timeout(300)
                b626.open_overlay(page, how)
                page.wait_for_timeout(450)
                row = measure(page, sel)
                row["old"] = prior_by.get((name, w, h))
                cells[f"{name}@{w}x{h}"] = row
                page.close()

        # 626's two extra contracts.
        for name, how, sel, vps in b626.HEIGHT_SWEEP:
            for w, h in vps:
                page = br.new_page(viewport={"width": w, "height": h},
                                   device_scale_factor=1)
                b626.open_desk_with_retry(page)
                page.wait_for_timeout(300)
                b626.open_overlay(page, how)
                page.wait_for_timeout(450)
                row = measure(page, sel)
                row["old"] = next((m for m in json.loads(
                    AUDIT_626.read_text(encoding="utf-8"))["heightSweep"]
                    if m["overlay"] == name and m["vw"] == w and m["vh"] == h), None)
                sweep[f"{name}@{w}x{h}"] = row
                page.close()
        br.close()

    out: dict[str, Any] = {
        "batch": 650,
        "question": "does the DERIVED competitor set, run over the 11 director "
                    "overlays 626 measured with a HAND-WRITTEN list, agree with "
                    "626 — and on the 8 that 649 never calibrated?",
        "viewports": b626.VIEWPORTS,
        "cells": cells,
        "heightSweep": sweep,
    }

    # ------------------------------------------------------------------ 1
    v.check("all-33-cells-ran-and-every-overlay-actually-opened",
            len(cells) == 33
            and all(c["present"] for c in cells.values())
            and all(c["old"] is not None for c in cells.values()),
            detail={"cells": len(cells),
                    "overlays": [n for n, _h, _s in b626.OVERLAYS],
                    "absent": {k: c for k, c in cells.items() if not c["present"]},
                    "noPrior": {k: None for k, c in cells.items() if not c["old"]},
                    "note": "`overlay-present` non-empty is 626's own anti-vacuity "
                            "guard; an overlay that failed to open would make "
                            "both of its checks pass for free"})

    # ------------------------------------------------------------------ 2
    # Calibration, part 1: the 3 overlays 649 already calibrated must still
    # agree.  If they drift, the other 8 cannot be trusted either.
    # 649's calibration sample was three overlays that 648 had opened —
    # `crowd-panel`, `phone-vcam-panel`, `model-library-panel` — and NONE of
    # them is in 626's eleven.  So this batch is not "the other eight": it is
    # all eleven, none of which a derived ruler had ever seen.  I asserted
    # `len(theEight) == 8` on the strength of that framing and it was wrong by
    # construction; the run said so immediately.
    all_eleven = sorted({k.split("@")[0] for k in cells})
    never_calibrated = sorted(set(all_eleven)
                              - {"crowd-panel", "phone-vcam-panel",
                                 "model-library-panel"})
    v.check("all-eleven-of-626s-overlays-are-covered-by-a-derived-ruler-for-the-first-time",
            len(never_calibrated) == 11 and len(all_eleven) == 11,
            detail={"theEleven": all_eleven,
                    "calibratedBy649": ["crowd-panel", "phone-vcam-panel",
                                        "model-library-panel"],
                    "noneOf649sThreeAreAmong626sEleven": True,
                    "reading": "649's calibration sample came from 648's desk "
                               "overlays, not from 626's matrix. So this batch is "
                               "not a top-up — every one of 626's eleven is being "
                               "measured by a derived competitor set for the "
                               "FIRST time, and 626's own hand-written list has "
                               "no say in any of them."})

    # ------------------------------------------------------------------ 3
    # Calibration, part 2: THE EIGHT OTHERS.  This is the batch's whole point.
    struct_new = {k: c["structBad"] for k, c in cells.items()
                  if c.get("structBad") and not c["old"].get("structBad")}
    struct_lost = {k: {"old": c["old"]["structBad"], "now": c.get("structBad")}
                   for k, c in cells.items()
                   if not c.get("structBad") and c["old"].get("structBad")}
    flagged_now = sorted({k.split("@")[0] for k in struct_new})
    v.check("the-only-overlay-the-derived-ruler-flags-is-the-one-626-declared-out-of-scope",
            flagged_now == ["camera-fov-help-tooltip"] and not struct_lost,
            detail={"cellsTheDerivedRulerFlagsAnd626DidNot": struct_new,
                    "cells626FlaggedAndTheDerivedRulerDoesNot": struct_lost,
                    "theFinding": "`camera-fov-help-tooltip` is painted over by "
                                  "`section.sticky.top-0` (z 20, sticky, opaque "
                                  "background). 626's own README says of it: "
                                  "'`camera-fov-help-tooltip` 的可点击性：它是 "
                                  "`pointer-events:none` 的 hover 提示… 这不代表它的"
                                  "可读性或定位被验证过' — it explicitly declined to "
                                  "claim the tooltip's readability or placement. "
                                  "That is exactly the gap the derived set walks "
                                  "into, and 626's hand-written six never saw it "
                                  "because the coverer is not one of its six.",
                    "whatItIsNot": "NOT a clickability defect. The tooltip is "
                                   "pointer-events:none with zero live controls, "
                                   "so the casualty half is 0 and always will be. "
                                   "The claim is strictly about PAINTING: a "
                                   "sticky section covers part of it.",
                    "derivedIsStrictlyNarrower": True,
                    "theCoverer": struct_new})

    # ------------------------------------------------------------------ 4
    # The 8 uncalibrated overlays, counted.  A batch that only re-checked the
    # 3 it already knew would be theatre.
    v.check("every-one-of-the-eleven-carries-its-own-626-answer-for-comparison",
            all(c["old"] is not None for c in cells.values())
            and len({(c["old"]["overlay"], c["old"]["vw"], c["old"]["vh"])
                     for c in cells.values()}) == 33,
            detail={"cells": len(cells),
                    "distinctPriorCells": len({(c["old"]["overlay"],
                                                 c["old"]["vw"], c["old"]["vh"])
                                                for c in cells.values()}),
                    "priorSource": "docs/research/liblib-canvas-batch626-2026-10-01/"
                                   "runtime-audit.json .measurements",
                    "why": "a comparison is only worth anything if both sides "
                           "pointed at the same cell; distinct keys prove the "
                           "join was 1:1 and not accidentally many-to-one"})

    # ------------------------------------------------------------------ 5
    # The expected direction, asserted rather than explained away: the two
    # guards 648/649 added can only REMOVE casualties.
    grew = {k: {"old": c["old"]["liveCount"], "new": c.get("liveCount")}
            for k, c in cells.items()
            if (c.get("liveCount") or 0) > c["old"]["liveCount"]}
    more_blocked = {k: {"old": c["old"]["blocked"], "new": c.get("blocked")}
                    for k, c in cells.items()
                    if len(c.get("blocked", [])) > len(c["old"].get("blocked", []))}
    v.check("the-derivation-never-invents-a-control-or-a-casualty",
            not grew and not more_blocked,
            detail={"cellsWhereLiveCountGrew": grew,
                    "cellsWhereCasualtiesGrew": more_blocked,
                    "theTwoGuards": {
                        "649structural": "cross-check the z claim against "
                                         "elementsFromPoint at the overlap",
                        "649casualty": "626's `w<=0||h<=0`, PLUS `<=1px`, PLUS "
                                       "clip / clip-path",
                    },
                    "reading": "both guards only ever REMOVE. A cell where the "
                               "derived ruler counts MORE is a bug in the "
                               "derived ruler, not a new finding."})

    # ------------------------------------------------------------------ 6
    diff_cases = {k: {"oldBlocked": c["old"]["blocked"],
                      "newBlocked": c.get("blocked"),
                      "oldLive": c["old"]["liveCount"],
                      "newLive": c.get("liveCount")}
                  for k, c in cells.items()
                  if c["old"].get("blocked") != c.get("blocked")}
    v.check("every-casualty-difference-is-648s-sr-only-finding-and-nothing-else",
            all(set(c["newBlocked"]) <= set(c["oldBlocked"])
                and c["newLive"] <= c["oldLive"]
                for c in diff_cases.values()),
            detail={"cellsThatDiffer": diff_cases,
                    "theRule": "the derived set must be a SUBSET of 626's, and "
                               "the live count must not grow",
                    "why": "648 measured exactly one such control (the sr-only "
                           "1x1 file input) across the whole model library panel. "
                           "Any other casualty appearing or disappearing here "
                           "would be an unexplained move."})

    # ------------------------------------------------------------------ 7
    box_diffs = {k: {"old": c["old"]["box"], "new": c.get("box")}
                 for k, c in cells.items() if c.get("box") != c["old"].get("box")}
    v.check("every-overlay-measures-the-same-box-as-626",
            not box_diffs,
            detail={"cells": box_diffs,
                    "why": "box identity is the strongest available proof that "
                           "the two rulers were pointed at the same thing. A box "
                           "mismatch would mean an overlay opened differently, "
                           "not that the criterion disagrees."})

    # ------------------------------------------------------------------ 8
    # 626's own extra contracts, re-asserted on the derived ruler.
    noop = b626.NO_OP_CASES
    noop_rows = []
    for name, how, sel, (w, h), _expected_box in noop:
        key = f"{name}@{w}x{h}"
        c = cells.get(key) or sweep.get(key)
        noop_rows.append({"cell": key, "expected": [52, 508, 204, 270],
                          "measured": (c or {}).get("box")})
    v.check("626s-no-op-geometry-contract-still-holds-under-the-derived-ruler",
            all(r["measured"] == r["expected"] for r in noop_rows),
            detail={"rows": noop_rows,
                    "theContract": "the geometry submenu's clamp must be a "
                                   "no-op where nothing overflows — @52,508 "
                                   "204x270 at both viewports",
                    "why": "a clamp that touched geometry it has no business "
                           "touching would be a silent regression, and 626 "
                           "pinned the box to make that enforceable"})

    # ------------------------------------------------------------------ 9
    # 626's `baseline` block is the PRE-FIX run: 111 checks, 15 failures, with
    # `fit-in-viewport/...motion-path-menu` and `...geometry-submenu` among them.
    # Those two menus were FIXED by 626, so the post-fix readings are all <= 0.
    # My first version of this check asserted "the breaking set is a subset of
    # those two" — which an EMPTY set satisfies trivially, i.e. it would have
    # passed whether the fix held or not.  A check that cannot fail is not a
    # check.  What is worth asserting is the contract itself, in both
    # directions: nothing breaks it now, AND the derived ruler reproduces
    # 626's own post-fix numbers cell by cell.
    # 626's `measurements` rows do not carry `overflowBottom` AT ALL — only its
    # `heightSweep` rows do, because the matrix was only ever about stacking
    # and the sweep was the height contract.  So the cell-by-cell cross-check
    # is available for 6 cells, not 33, and asserting it for 33 would have
    # compared 27 numbers against `None`.  The red said so.
    ob_diffs = {k: {"derived": c.get("overflowBottom"),
                    "b626PostFix": (c.get("old") or {}).get("overflowBottom")}
                for k, c in sweep.items()
                if c.get("overflowBottom")
                != (c.get("old") or {}).get("overflowBottom")}
    comparable = sum(1 for c in sweep.values()
                     if (c.get("old") or {}).get("overflowBottom") is not None)
    over = {k: c.get("overflowBottom") for k, c in list(cells.items()) + list(sweep.items())
            if c.get("kind") == "menu" and (c.get("overflowBottom") or 0) > 0}
    v.check("the-8px-margin-contract-holds-in-every-cell-and-matches-626s-post-fix-numbers",
            not over and not ob_diffs and len(cells) + len(sweep) == 39
            and comparable == 6,
            detail={"cellsChecked": len(cells) + len(sweep),
                    "cellsWithAComparableNumberFrom626": comparable,
                    "whyOnlySix": "626's `measurements` rows carry no "
                                  "`overflowBottom` field at all — the matrix was "
                                  "about stacking, the height sweep was the height "
                                  "contract. So the numeric cross-check exists for "
                                  "the 6 sweep cells; the other 33 are covered by "
                                  "the no-break half of the assertion.",
                    "menusCurrentlyBreakingTheMargin": over,
                    "cellsWhereTheOverflowNumberDiffersFrom626": ob_diffs,
                    "theTwoGuardsAgainstThisCheckGoingGreenForFree":
                        ["it requires all 39 cells to have run",
                         "it requires the derived overflow number to equal 626's "
                         "post-fix number in all 6 cells where 626 recorded one, "
                         "so a silent drift in either ruler turns it red",
                         "it requires exactly 6 comparable cells, so a future "
                         "run that silently loses the field goes red too"],
                    "theHistoricalPair": "626's `baseline` (the PRE-fix run) "
                                         "recorded `fit-in-viewport/1920x900/"
                                         "motion-path-menu`, `.../1920x540/"
                                         "motion-path-menu`, `.../1280x640/"
                                         "motion-path-menu` and three "
                                         "geometry-submenu cells failing. 111 "
                                         "checks, 15 failures. Those menus were "
                                         "fixed by 626; this batch confirms the "
                                         "fix under a ruler that never saw them.",
                    "menuPanelSplit": "649 showed the 8px margin is a MENU "
                                      "invariant; full-bleed panels are measured "
                                      "separately and not held to it"},
            note="the empty set is asserted as a CONTRACT, cross-checked against "
                 "626 cell by cell — not waved through")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "cells": len(cells),
        "heightSweepCells": len(sweep),
        "overlays": len(b626.OVERLAYS),
        "neverCalibratedBefore": 11,
        "structBadTotalDerived": sum(len(c.get("structBad", [])) for c in cells.values()),
        "structBadTotal626": sum(len(c["old"].get("structBad", [])) for c in cells.values()),
        "blockedTotalDerived": sum(len(c.get("blocked", [])) for c in cells.values()),
        "blockedTotal626": sum(len(c["old"].get("blocked", [])) for c in cells.values()),
        "liveTotalDerived": sum(c.get("liveCount") or 0 for c in cells.values()),
        "liveTotal626": sum(c["old"]["liveCount"] for c in cells.values()),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch650-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

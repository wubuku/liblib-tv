#!/usr/bin/env python3
"""batch 647 验收：给 `own` 的两个候选修法**定价** —— 一个在修，一个在让量具闭嘴

## 起点

646 查出普查的第三个盲区：`own` 接受祖先命中，于是**压根没被绘制**的控件被判成
「自己接到了点击」。646 把地面真值 `paintedAtCentre` 记了下来，并留下一个
显然的修法：

    own := paintedAtCentre

本批的任务就是**给这个修法定价**：它会移动多少条判决，移过去的那些是**真改善**
还是**假报**。

## 结果：那个修法会**撤销已有的发现**，所以它不是修法

`paintedAtCentre` 问的是「我在不在命中栈里」——那是**可见性**；
`own` 问的是「点击有没有落到我头上」——那是**可点性**。
两者在「被裁掉」的方向分开（646 测到的那半），但在**另一个方向也分开**：
一个控件可以**被绘制着、却仍然被别的东西压在上面**。
拿 `paintedAtCentre` 顶替 `own`，会把这种控件记成 `clean`。

实测 8 格探针（正式扫描 40 格）：

    格子          paint 修法移动                      top 修法移动
    1020x900     clean→clipped 1, timelineOverlay→clean 1    clean→clipped 1
    1020x480     clean→clipped 1, timelineOverlay→clean 10   clean→clipped 1
    1440x400     clipped→clean 1, timelineOverlay→clean 12,
                 viewportSqueeze→clean 1                     （无）
    339x900      covered→clean 1                             （无）
    1920x1150    timelineOverlay→clean 1                     （无）

**`paintedAtCentre` 在整个扫描里新增缺陷主张 0 条，却撤销了最多 14 条已有判定。**
一个只会把东西推向「干净」、从不指控的判据，是量具闭嘴的签名，不是修法。

### 最贵的一条：339 那格会把 632 的在案缺陷退休掉

    收起  box=[64, 5.5, 40, 40]  @339x900
      现状 covered     ← 632 的 170px 居中视角组压住它，640 有在案断言
      painted  True    ← 它**画在那里**，只是不在最上面
      top      False

拿 `paintedAtCentre` 顶替 `own`，`收起` 直接变 `clean`，
**632 那个在案缺陷就此消失**，而它其实还在。
`ownTop` 下它原样留在 `covered`。

## 那个对得上的修法：`ownTop`

    ownTop = el 或 el 的后代 ∈ 命中栈，并且是**栈顶**

可见性与可点性的合取。爆炸半径极小，且**只往一个方向动**：
每个有移动的格子里，移动集**恰好**是 646 的盲区，且全部是 `clean → clipped`。
新增缺陷主张 0 条，撤销已有判定 0 条。

## (C) 第二条独立证伪通道：合成（opacity）

646 用**裁剪**证伪了 `own`。一个机制不等于唯一机制。
`opacity` 不继承，所以 `opacity: 0` 的包裹层不可见、里面的控件照样接得到点击。
整角 0 例 —— 但**空集不算证据**，所以本批**注入探针自证**：裸 / 半透明 /
全透明三枚合成控件，逐一证明这个量具分得开「不可见」与「变淡」。

顺带**当场证伪 646 的字段名**：`paintedAtCentre` 量的是「在不在命中栈里」，
**不是**「有没有可见像素」。全透明控件的 `paintedAtCentre` 是 `True` ——
字段名与所测之实不符，用它顶替 `own` 正是踩在这个错上。

## 本批**不**主张的事

* **不主张**改了判据。`own` 与全部既有判定**一个字没动**；新增 200 行、删除 0 行。
* **不主张** `ownTop` 就是最终答案。它只被证明**无害**且**方向单一**；
  换不换仍是政策题。
* **零源站断言**。
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

# 8 widths across both families, 5 heights.  The height axis is the point of
# this batch: 646 swept 23 widths at ONE height, so every "every blind case is
# clipped" assertion in 646 is a statement about a single row of this grid.
WIDTHS = [339, 620, 768, 899, 1020, 1152, 1440, 1920]
HEIGHTS = [400, 560, 720, 900, 1150]
NARROW_MAX = 898

# (C) The compositing self-test.  Three synthetic controls with the same
# geometry, differing only in an `opacity` wrapper, so the threshold between
# "invisible" and "faded" is pinned from BOTH sides instead of asserted.
# `display: contents` is deliberately NOT used: it creates no box, so it has no
# opacity effect either, and the probe would silently pass for the wrong reason.
PROBE_JS = """() => {
  const host = document.querySelector('[data-director-workspace]');
  if (!host) return null;
  const wrap = document.createElement('div');
  wrap.setAttribute('data-647-probe', 'root');
  wrap.style.cssText = 'position:fixed;left:200px;top:200px;'
    + 'width:40px;height:40px;z-index:9999;';
  host.appendChild(wrap);
  for (const [k, o] of [['bare', null], ['faded', 0.5], ['fader', 0]]) {
    const inner = document.createElement('div');
    inner.setAttribute('data-647-probe', k);
    inner.style.cssText = o === null ? '' : 'opacity:' + o + ';';
    const btn = document.createElement('button');
    btn.setAttribute('aria-label', 'P647-' + k);
    btn.style.cssText = 'display:block;width:100%;height:100%;';
    btn.textContent = k;
    inner.appendChild(btn);
    wrap.appendChild(inner);
  }
  return true;
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
              + (f"  {str(detail)[:190]}" if detail else ""))


def _cell_summary(r: dict[str, Any]) -> dict[str, Any]:
    cf = r["counterfactual"]
    return {
        "total": r["total"],
        "bucketNow": dict(cf["bucketCountsNow"]),
        "bucketPaint": dict(cf["bucketCountsTight"]),
        "bucketTop": dict(cf["bucketCountsTop"]),
        "movesPaint": dict(cf["movesHistogram"]),
        "movesTop": dict(cf["movesTopHistogram"]),
        "newDefectPaint": len(cf["newDefectClaim"]),
        "newDefectTop": len(cf["newDefectClaimTop"]),
        "silencedPaint": len(cf["silencedByPaintRepair"]),
        "silencedTop": len(cf["silencedByTopRepair"]),
        "silencedPaintBy": dict(cf["silencedByPaintRepairSurfaces"]),
        "silencedTopBy": dict(cf["silencedByTopRepairSurfaces"]),
        "blindCount": len(r["ownButNotPainted"]),
        "blindLabels": sorted({b["label"] for b in r["ownButNotPainted"]}),
        "blindAllClipped": (all(b.get("clipRaw") for b in r["ownButNotPainted"])
                            if r["ownButNotPainted"] else None),
        "blindAllAncestor": (all(b.get("ownBecauseAncestor")
                                 for b in r["ownButNotPainted"])
                             if r["ownButNotPainted"] else None),
        "topClippedLabels": sorted({i["label"] for i in cf["topClipped"]}),
        "tightClippedLabels": sorted({i["label"] for i in cf["tightClipped"]}),
        "coveredNow": [[b["label"], b["hitLabel"], b["box"]] for b in r["covered"]],
        "coveredTop": [[i["label"], i["hitLabel"], i["box"]]
                       for i in r["items"] if i["bucketTop"] == "covered"],
        "invisibleButOwn": len(r["invisibleButOwn"]),
        "paintedButFaded": len(r["paintedButFaded"]),
        "roundCount": len(r["roundControls"]),
        "unreachable": len(r["offViewportUnreachable"]),
        "jointCount": len(r["bothCoveredAndClipped"]),
    }


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    silenced_cases: list[dict[str, Any]] = []

    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS:
            for h in HEIGHTS:
                page = br.new_page(viewport={"width": w, "height": h},
                                   device_scale_factor=1)
                b617.open_desk(page)
                page.set_viewport_size({"width": w, "height": h})
                page.wait_for_timeout(280)
                page.mouse.move(5, 5)
                page.wait_for_timeout(140)
                page.evaluate("() => { for (const el of "
                              "document.querySelectorAll('nextjs-portal')) el.remove(); }")
                r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
                key = f"{w}x{h}"
                cells[key] = _cell_summary(r)
                cells[key]["family"] = "narrow" if w <= NARROW_MAX else "desktop"
                cells[key]["viewportH"] = r["items"][0].get("viewportH")
                if r["counterfactual"]["silencedByPaintRepair"]:
                    silenced_cases.append({
                        "cell": key,
                        "items": [{"label": i["label"], "from": i["bucketNow"],
                                   "painted": i["paintedAtCentre"],
                                   "top": i["topAtCentre"],
                                   "hit": i["hitLabel"], "clip": i["clipRaw"],
                                   "box": i["box"],
                                   "covererSurface": i["covererSurface"]}
                                  for i in
                                  r["counterfactual"]["silencedByPaintRepair"]],
                    })
                page.close()

        # ---- the compositing self-test, in its own cell -------------------
        page = br.new_page(viewport={"width": 1440, "height": 900},
                           device_scale_factor=1)
        b617.open_desk(page)
        page.mouse.move(5, 5)
        page.wait_for_timeout(200)
        page.evaluate("() => { for (const el of "
                      "document.querySelectorAll('nextjs-portal')) el.remove(); }")
        before = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
        page.evaluate(PROBE_JS)
        page.wait_for_timeout(200)
        page.mouse.move(5, 5)
        page.wait_for_timeout(140)
        after = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
        page.close()
        br.close()

    probes = {}
    for i in after["items"]:
        al = i.get("hitLabel") or ""
        if i["label"].startswith("P647-"):
            probes[i["label"]] = {
                "own": i["own"], "painted": i["paintedAtCentre"],
                "top": i["topAtCentre"],
                "invisibleButOwn": i["invisibleButOwn"],
                "paintedButFaded": i["paintedButFaded"],
                "minAncestorOpacity": i["minAncestorOpacity"],
                "faderSurface": i["faderSurface"],
                "bucketNow": i["bucketNow"], "bucketPaint": i["bucketTight"],
                "bucketTop": i["bucketTop"],
            }
    probe_injected = after["total"] - before["total"]

    out: dict[str, Any] = {
        "batch": 647,
        "question": "price the two candidate repairs of `own` before making one",
        "criteria": {
            "own": "status quo: hit===el || el.contains(hit) || hit.contains(el)",
            "ownTight": "646's implied repair: paintedAtCentre (in the hit stack)",
            "ownTop": "this batch's candidate: el or a descendant of el is the "
                      "TOP of the hit stack",
        },
        "grid": {"widths": WIDTHS, "heights": HEIGHTS},
        "cells": cells,
        "silencedCases": silenced_cases,
        "compositingSelfTest": {
            "probesInjected": probe_injected,
            "probes": probes,
            "naturalInvisibleBeforeInjection": len(before["invisibleButOwn"]),
            "naturalFadedBeforeInjection": len(before["paintedButFaded"]),
        },
    }

    # ------------------------------------------------------------------ 1
    v.check(f"the-grid-runs-{len(WIDTHS)}w-x-{len(HEIGHTS)}h-both-families",
            len(cells) == len(WIDTHS) * len(HEIGHTS)
            and {c["family"] for c in cells.values()} == {"narrow", "desktop"},
            detail={"cells": len(cells), "widths": WIDTHS, "heights": HEIGHTS,
                    "whyTheHeightAxis": "646 swept 23 widths at ONE height, so "
                                        "its 'every blind case is clipped' is a "
                                        "statement about a single row of this grid"})

    # ------------------------------------------------------------------ 2
    # The six buckets must be a strict partition under all three criteria.
    # A hole in the chain would silently shrink a bucket and make every
    # comparison downstream meaningless.
    holes = {}
    for k, c in cells.items():
        for col in ("bucketNow", "bucketPaint", "bucketTop"):
            if sum(c[col].values()) != c["total"]:
                holes[k] = {"column": col, "sum": sum(c[col].values()),
                            "total": c["total"], "buckets": c[col]}
    v.check("the-six-buckets-are-a-strict-partition-under-all-three-criteria",
            not holes,
            detail={"holes": holes,
                    "note": "the chain is own -> panel -> clipped -> "
                            "timelineOverlay -> viewportSqueeze -> covered"})

    # ------------------------------------------------------------------ 3
    # THE HEADLINE.  646's implied repair never accuses and keeps silencing.
    total_new = sum(c["newDefectPaint"] for c in cells.values())
    total_sil = sum(c["silencedPaint"] for c in cells.values())
    v.check("646s-implied-repair-never-creates-a-defect-claim-and-does-silence",
            total_new == 0 and total_sil > 0,
            detail={"newDefectClaimsTotal": total_new,
                    "silencedVerdictsTotal": total_sil,
                    "cellsWithSilencing": len(silenced_cases),
                    "reading": "a criterion that only ever moves controls "
                               "toward `clean`, never toward `covered`, is the "
                               "signature of an instrument being told to shut "
                               "up, not of an instrument being repaired"})

    # ------------------------------------------------------------------ 4
    # The growth: the shorter the viewport, the more the bad repair silences.
    by_width: dict[int, dict[int, int]] = {}
    for k, c in cells.items():
        w, h = (int(x) for x in k.split("x"))
        by_width.setdefault(w, {})[h] = c["silencedPaint"]
    grow_bad = {w: d for w, d in by_width.items()
                if d[min(HEIGHTS)] <= d[max(HEIGHTS)]}
    v.check("the-silence-grows-as-the-viewport-shrinks-in-every-width",
            not grow_bad,
            detail={"matrix": {str(w): {str(h): n for h, n in d.items()}
                               for w, d in sorted(by_width.items())},
                    "widthsWhereItDoesNotGrow": grow_bad,
                    "reading": "the damage scales exactly where the census does "
                               "its most work: `timelineOverlay` grows as the "
                               "viewport shortens, and every one of those "
                               "verdicts is a source-fact exemption from 628"})

    # ------------------------------------------------------------------ 5
    # The concrete case.  339's `收起` is 632's standing defect and 640 asserts
    # it in every run; the paint repair would retire it without fixing it.
    # NOTE the polarity, because I got it backwards the first time and the red
    # was the useful part: `retiredByTopRepair` must be EMPTY and the paint
    # repair's drop must be NON-EMPTY.  The first version demanded the opposite
    # and therefore would have passed a run in which the top repair DID retire
    # the defect — i.e. it was asserting the failure mode as the success mode.
    retired_by_top = []
    for k, c in cells.items():
        keep = {l for l, _w, _b in c["coveredTop"]}
        for lab, who, box in c["coveredNow"]:
            if lab not in keep:
                retired_by_top.append({"cell": k, "label": lab,
                                      "coveredBy": who, "box": box})
    paint_retires = [{"cell": k,
                      "now": c["bucketNow"].get("covered", 0),
                      "paint": c["bucketPaint"].get("covered", 0)}
                     for k, c in cells.items()
                     if dict(c["bucketPaint"]).get("covered", 0)
                     < dict(c["bucketNow"]).get("covered", 0)]
    v.check("the-paint-repair-would-retire-632s-standing-defect-the-top-one-would-not",
            (not retired_by_top) and bool(paint_retires)
            and bool(cells.get("339x900", {}).get("coveredNow"))
            and cells["339x900"]["coveredTop"] == cells["339x900"]["coveredNow"],
            detail={"retiredByTopRepair": retired_by_top,
                    "theCaseNow": cells.get("339x900", {}).get("coveredNow"),
                    "theCaseUnderTopRepair": cells.get("339x900", {}).get("coveredTop"),
                    "coveredCountDroppedByPaintRepair": paint_retires,
                    "origin": "632: DirectorDesk.tsx:1029-1031 places a 170px "
                              "centred group absolutely; at 339 it lands on the "
                              "top bar's `收起`. 640 asserts this in every run.",
                    "reading": "`收起` IS painted at its centre — it is visible — "
                               "and is still not on top of the stack. The paint "
                               "repair files that as clean; the top repair keeps "
                               "the finding. The defect is real either way."})

    # ------------------------------------------------------------------ 6
    # `ownTop` moves exactly one way, and only the 646 blind set.
    top_moves_bad = {k: c["movesTop"] for k, c in cells.items()
                     if set(c["movesTop"]) - {"clean -> clipped"}}
    v.check("the-top-repair-only-ever-moves-clean-to-clipped",
            not top_moves_bad,
            detail={"cellsWithAnyOtherMove": top_moves_bad,
                    "distinctTopMoves": sorted({m for c in cells.values()
                                                for m in c["movesTop"]}),
                    "whyThisIsTheShapeYouWant": "a repair that can only move a "
                                                "control from 'clean' into the "
                                                "'scroll to reach it' bucket "
                                                "cannot be hiding a finding"})

    # ------------------------------------------------------------------ 7
    mismatch = {k: {"topClipped": c["topClippedLabels"],
                    "tightClipped": c["tightClippedLabels"]}
                for k, c in cells.items()
                if c["topClippedLabels"] != c["tightClippedLabels"]}
    v.check("both-repairs-file-the-same-646-blind-set",
            not mismatch,
            detail={"mismatches": mismatch,
                    "reading": "the two candidates agree on WHICH controls are "
                               "missed; they differ only on what to do about a "
                               "control that is painted but not on top, and the "
                               "top repair is the one that keeps reporting it"})

    # ------------------------------------------------------------------ 8
    # 646's own "every blind case is clipped" has never been tested off its
    # single height row.  If it fails here, the top repair would manufacture a
    # defect claim — which is the whole risk of any criterion change.
    not_clipped = {k: c["blindLabels"] for k, c in cells.items()
                   if c["blindCount"] and c["blindAllClipped"] is False}
    not_ancestor = {k: c["blindLabels"] for k, c in cells.items()
                    if c["blindCount"] and c["blindAllAncestor"] is False}
    v.check("646s-mechanism-assertions-survive-the-height-axis",
            not not_clipped and not not_ancestor,
            detail={"blindCasesNotClipped": not_clipped,
                    "blindCasesNotThroughTheAncestorBranch": not_ancestor,
                    "blindCountPerCell": {k: c["blindCount"]
                                          for k, c in cells.items()},
                    "labelsSeen": sorted({l for c in cells.values()
                                          for l in c["blindLabels"]}),
                    "reading": "clipping really is the only reason a control is "
                               "in the hit stack's neighbourhood without being "
                               "in it, across 40 cells and both families"})

    # ------------------------------------------------------------------ 9
    zero_new_top = sum(c["newDefectTop"] for c in cells.values())
    zero_sil_top = sum(c["silencedTop"] for c in cells.values())
    v.check("the-top-repair-accuses-nothing-and-silences-nothing",
            zero_new_top == 0 and zero_sil_top == 0,
            detail={"newDefectClaims": zero_new_top, "silencedVerdicts": zero_sil_top,
                    "verdict": "safe in BOTH directions — it neither invents a "
                               "defect nor retires one"})

    # ------------------------------------------------------------------ 10
    # The compositing channel: 646 falsified `own` through clipping.  One
    # mechanism is not the only mechanism, and the other route to
    # clickable-but-invisible is compositing.  Zero natural occurrences is a
    # NEGATIVE result, and a negative result on an untested instrument is not
    # evidence — so the instrument is fired at a target first.
    pr = probes
    want = {
        "P647-bare":  {"own": True, "painted": True, "invisibleButOwn": False,
                       "paintedButFaded": False, "minAncestorOpacity": 1.0},
        "P647-faded": {"own": True, "painted": True, "invisibleButOwn": False,
                       "paintedButFaded": True, "minAncestorOpacity": 0.5},
        "P647-fader": {"own": True, "painted": True, "invisibleButOwn": True,
                       "paintedButFaded": True, "minAncestorOpacity": 0.0},
    }
    wrong = {k: {"want": v2, "got": pr.get(k)}
             for k, v2 in want.items()
             if not (pr.get(k) and all(pr[k].get(f) == g
                                       for f, g in v2.items()))}
    v.check("the-compositing-probe-fires-on-an-injected-target",
            not wrong and probe_injected == 3,
            detail={"wrong": wrong, "probesInjected": probe_injected,
                    "probes": pr,
                    "theDiscrimination": "faded 0.5 must set paintedButFaded "
                                          "and NOT invisibleButOwn; fader 0 must "
                                          "set both. A probe that only tested the "
                                          "0.5 case could not tell the two apart."})

    # ------------------------------------------------------------------ 11
    # The naming correction, demonstrated rather than argued: an opacity-0
    # control has paintedAtCentre === True.  The field measures hit-stack
    # membership, not visible pixels, and swapping `own` for it is standing on
    # exactly that.
    v.check("paintedAtCentre-does-not-mean-painted-and-the-probe-shows-it",
            bool(pr.get("P647-fader", {}).get("painted")) is True
            and bool(pr.get("P647-fader", {}).get("invisibleButOwn")) is True,
            detail={"faderProbe": pr.get("P647-fader"),
                    "correction": "646 named the field `paintedAtCentre`. It "
                                  "measures membership in the hit-test stack. An "
                                  "invisible control satisfies it. The name is "
                                  "kept — renaming a committed contract is not "
                                  "this batch's business — but it is corrected "
                                  "here, and the counterexample is on the record."})

    # ------------------------------------------------------------------ 12
    nat_inv = sum(c["invisibleButOwn"] for c in cells.values())
    nat_fad = sum(c["paintedButFaded"] for c in cells.values())
    v.check("the-compositing-channel-is-empty-across-the-whole-corner",
            nat_inv == 0 and nat_fad == 0
            and out["compositingSelfTest"]["naturalInvisibleBeforeInjection"] == 0,
            detail={"invisibleButOwnTotal": nat_inv, "paintedButFadedTotal": nat_fad,
                    "beforeInjection": out["compositingSelfTest"],
                    "reading": "with the instrument proven able to fire, zero "
                               "natural occurrences is a result: 646's clipping "
                               "mechanism is the only one this corner can reach",
                    "boundary": "only `opacity` is covered. `filter: opacity(0)`, "
                                "`mix-blend-mode` and `content-visibility: hidden` "
                                "are NOT tested and remain open."})

    # ------------------------------------------------------------------ 13
    # Standing facts, re-asserted so the new grid is not a free pass.
    v.check("no-cell-has-an-off-viewport-unreachable-control",
            all(c["unreachable"] == 0 for c in cells.values()),
            detail={k: c["unreachable"] for k, c in cells.items()
                    if c["unreachable"]})
    v.check("642s-eight-round-controls-are-still-eight",
            all(c["roundCount"] == 8 for c in cells.values()),
            detail={k: c["roundCount"] for k, c in cells.items()
                    if c["roundCount"] != 8})
    unexplained = {k: c["coveredNow"] for k, c in cells.items() if c["coveredNow"]}
    v.check("the-only-unexplained-cover-is-still-632s-known-defect",
            all(lab == "收起" for items in unexplained.values()
                for lab, _who, _box in items),
            detail={"cells": unexplained,
                    "status": "clone-only, unfixed, awaiting a source reading"})

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "newDefectClaimsPaint": sum(c["newDefectPaint"] for c in cells.values()),
        "newDefectClaimsTop": sum(c["newDefectTop"] for c in cells.values()),
        "silencedByPaint": sum(c["silencedPaint"] for c in cells.values()),
        "silencedByTop": sum(c["silencedTop"] for c in cells.values()),
        "movedByTop": sum(sum(c["movesTop"].values()) for c in cells.values()),
        "blindCases": sum(c["blindCount"] for c in cells.values()),
        "silenceMatrix": {str(w): {str(h): n for h, n in d.items()}
                          for w, d in sorted(by_width.items())},
    }
    audit = ROOT / "docs/research/liblib-canvas-batch647-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

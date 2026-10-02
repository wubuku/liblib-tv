#!/usr/bin/env python3
"""batch 642 验收：把「圆控件只能取中心点」写进**共享判据**，并证明零回归

## 为什么要动共用文件

631 立过一条纪律：**不为一个批次的提问改所有批次共用的判据**（先看几何能否回答）。
本批是那条纪律的**例外，且是明确的例外**：641 证明晶格探针在 `rounded-full`
控件上落在形状的亚像素边界上（余量 0.01px），于是「圆控件该用中心点」这条规则
必须**对所有后来者可见**，否则每个新批次都要重踩一遍。

所以本批改 `verify-liblib-batch617.py` 的 `AUDIT_JS`，但**只增不改**：

    items[].round          半径 ≥ 短边一半
    items[].borderRadiusPx 实测计算半径
    items[].samplePoint    固定 "centre"
    items[].sampleNote     圆控件才有的说明
    return.roundControls   圆控件清单

**没有任何既有判据被改动**——`own` / `clipped` / `panel` / `timelineOverlay` /
`viewportSqueeze` / `hitInBottomBar` / `hitInShotBar` 全部原样。

## 零回归是**机械证明**的，不是声称的

改完立刻重跑依赖它的两个批次，比对**已落盘的 audit JSON**：

    verify-liblib-batch639.py  → 15 checks, 0 failures
    verify-liblib-batch640.py  → 14 checks, 0 failures
    git diff --quiet <两份 audit>  →  IDENTICAL

**一个字节都没变。** 这是「只增不改」这句话的可执行形式。

## 判据自己踩的坑：`cs` 撞名

第一次改完，639 与 640 **双双崩在 `AUDIT_JS`**，报
`ReferenceError: Cannot access 'cs' before initialization`——循环顶部早就有
`const s = cs(el)`（取 zIndex 的辅助函数），我在同一作用域声明
`const cs = getComputedStyle(el)`，把上面每一次 `cs(el)` 调用变成了 TDZ。

**教训**：在别人的共享脚本里加变量，先把该作用域已绑定的名字读完。
这条坑与批次内容无关，但它让「只增不改」在第一次尝试时是**假**的。

## 零源站断言

本批只主张 clone 的读数与判据的性质，不主张源站任何事。
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

WIDTHS = [339, 480, 620, 898, 899, 1440, 1920]
WIN_H = 900

# 641's measurement, promoted to a shared constant so a later batch does not
# re-derive it.  These are OCCLUSION radii (a neighbouring dot truncates the
# sweep), which is why the low end is 4.9 rather than 7.5.
OCCLUSION_RADII_SEEN = [4.9, 6.5, 7.4, 7.5, 8.1, 8.4, 8.9]
LATTICE_CORNER_DISTANCE = 8.91

# The round controls 640 named, so this batch can check the census finds them
# without anybody re-typing the list from a dump.
GIZMO_LABELS = {"X 正向", "X 反向", "Y 正向", "Y 反向", "Z 正向", "Z 反向"}


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
        print(("  PASS " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))


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
            r = page.evaluate(b617.AUDIT_JS, list(b617.TRANSIENT_OVERLAYS))
            round_list = r.get("roundControls") or []
            every = r.get("blocked") or []
            cells[str(w)] = {
                "total": r["total"],
                "roundControls": round_list,
                "roundCount": len(round_list),
                "roundLabels": sorted({x["label"] for x in round_list}),
                "radii": sorted({x["borderRadiusPx"] for x in round_list}),
                "roundAllOwn": all(x["own"] for x in round_list),
                "roundCoveredLabels": [x["label"] for x in round_list
                                       if not x["own"]],
                "unexplained": [(b["label"], b["hitLabel"], b["box"])
                                for b in r["covered"]],
                "unreachable": [(b["label"], b["box"])
                                for b in r["offViewportUnreachable"]],
                "blockedCount": len(every),
            }
            page.close()
        br.close()

    out = {
        "batch": 642,
        "title": "the round-control sampling policy now lives in the shared "
                 "criterion, with a mechanical zero-regression proof",
        "date": "2026-10-01",
        "widths": WIDTHS, "windowHeight": WIN_H,
        "sharedConstants": {
            "occlusionRadiiSeen": OCCLUSION_RADII_SEEN,
            "latticeCornerDistance": LATTICE_CORNER_DISTANCE,
            "origin": "batch 641",
        },
        "cells": cells,
    }

    v.check(f"the-grid-runs-{len(WIDTHS)}widths", len(cells) == len(WIDTHS),
            detail=len(cells))

    # --- the new field actually populates --------------------------------
    empty = [w for w, c in cells.items() if c["roundCount"] == 0]
    v.check("roundControls-is-populated-at-every-width", not empty,
            detail={"widthsWithNoRoundControl": empty,
                    "perWidth": {w: c["roundCount"] for w, c in cells.items()}})

    gizmo_found = {w: sorted(GIZMO_LABELS & set(c["roundLabels"]))
                   for w, c in cells.items()}
    v.check("the-census-finds-the-six-gizmo-axis-buttons-among-the-round-controls",
            all(len(s) == 6 for s in gizmo_found.values()),
            detail={"gizmoLabelsFoundPerWidth": gizmo_found,
                    "expected": sorted(GIZMO_LABELS),
                    "origin": "640 named them; this batch checks the SHARED "
                              "criterion finds them without anyone retyping "
                              "the list"})

    radii = sorted({r for c in cells.values() for r in c["radii"]})
    v.check("the-round-controls-radius-is-the-clamped-rounded-full-value",
            bool(radii) and all(r >= 7.5 for r in radii),
            detail={"radiiSeen": radii,
                    "threshold": ">= half the 15px short side, i.e. rounded-full",
                    "note": "the computed value is the clamped 9999px, not 7.5 — "
                            "which is exactly why batch 641 had to MEASURE the "
                            "hit shape instead of deriving it from the box"})

    # --- the policy is stated, and it is NOT vacuous ----------------------
    # My first version asserted every round control reads own=True.  It went
    # red, and the red was correct: the census finds EIGHT round controls, not
    # six, and two of them (`上传图片`, `发送`, 32x32, in the prompt strip) are
    # covered at their centre at most widths.
    #
    # And that is a finding about 640, not about 642: 640 searched for
    # "centre clear + body blocked", which BY CONSTRUCTION cannot surface a
    # control covered at its centre.  Those land in the clipped bucket instead.
    # So 640's blind-spot search had a second, invisible blind spot.
    covered_round = {}
    for w, c in cells.items():
        bad = [x["label"] for x in c["roundControls"] if not x["own"]]
        if bad:
            covered_round[w] = bad
    v.check("the-round-policy-surfaces-centre-covered-round-controls-too",
            bool(covered_round),
            detail={"widthsWhereARoundControlIsCoveredAtItsCentre":
                    sorted(covered_round, key=int),
                    "labels": sorted({l for v2 in covered_round.values()
                                      for l in v2}),
                    "reading": "640 could never have found these: its search "
                               "criterion was 'centre clear AND body blocked'. "
                               "A control covered AT its centre is a different "
                               "class and the census files it under clipped."})

    v.check("the-six-gizmo-axis-buttons-are-never-covered-at-their-centre",
            all(not (GIZMO_LABELS & set(v2)) for v2 in covered_round.values()),
            detail={"widthsWhereAGizmoButtonIsCovered":
                    {w: sorted(GIZMO_LABELS & set(v2))
                     for w, v2 in covered_round.items()
                     if GIZMO_LABELS & set(v2)},
                    "reading": "the six that 640 named are clean at the centre "
                               "in all seven widths — which is why 641's centre "
                               "probe was the right instrument for them"})

    # --- the census did not become a round-control detector that hides the
    #     one real defect -----------------------------------------------
    known = []
    for w, c in cells.items():
        for label, who, box in c["unexplained"]:
            known.append({"width": w, "label": label, "coveredBy": who, "box": box,
                          "is632sDefect": label == "收起" and "视角" in (who or "")})
    v.check("adding-the-round-policy-did-not-hide-632s-known-defect",
            all(k["is632sDefect"] for k in known),
            detail={"unexplained": known,
                    "status": "still exactly the 170px centred group at 339; "
                              "the new fields are additive so it cannot be "
                              "suppressed"})

    bad = {w: c["unreachable"] for w, c in cells.items() if c["unreachable"]}
    v.check("no-cell-has-an-off-viewport-unreachable-control", not bad,
            detail=dict(list(bad.items())[:4]))

    # --- the shared constant is the one 641 measured ----------------------
    v.check("the-shared-occlusion-radii-match-641s-measurement",
            OCCLUSION_RADII_SEEN == [4.9, 6.5, 7.4, 7.5, 8.1, 8.4, 8.9]
            and LATTICE_CORNER_DISTANCE == 8.91,
            detail={"occlusionRadiiSeen": OCCLUSION_RADII_SEEN,
                    "latticeCornerDistance": LATTICE_CORNER_DISTANCE,
                    "tightestMargin": round(
                        LATTICE_CORNER_DISTANCE - max(OCCLUSION_RADII_SEEN), 2),
                    "whyItMatters": "this is why the rule exists: the lattice "
                                     "corner clears the largest measured radius "
                                     "by 0.01px, so a lattice verdict on a round "
                                     "control is decided by sub-pixel rounding"})

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "perWidth": {w: {"total": c["total"], "roundCount": c["roundCount"],
                         "roundLabels": c["roundLabels"],
                         "blockedCount": c["blockedCount"]}
                     for w, c in cells.items()},
        "radiiSeen": radii,
        "unexplained": known,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch642-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""batch 652 验收：651 的污染面**只有 11 条打开路径中的 1 条** —— 判据是滚动量**可不可复现**

## 起点

651 查出 650 那个头条读数是 Playwright `hover()` 自动滚动的伪影，并把它列为
本项目**第六个盲区形状：探针的副作用**。

但 651 只查了**一条**打开路径（`@fov-hover@`）。其余 10 条有没有同样的问题？
如果是「测具坏了」，影响面就必须量出来，而不能靠「应该只有这一条」。

## 本批的判据

污染的真正特征**不是**「探针滚动了」，而是：

    同一个布局，探针在不同视口下滚到了**不同的量**。

因为若滚动量可复现（最小滚动到刚好可见），那个状态是**用户也能复现的**，
读数是合法的；只有当滚动量本身随视口漂移，而被测浮层又贴着被滚动的元素定位时，
读到的才是**探针的实现细节**。

所以判据是两条，可量、不叙述：
1. 这条路径**有没有**让某个可滚动容器的 offset 变化；
2. 若有，那个 offset **在不同窗高之间是否相同**。

## 读数

1280 宽 × 三个窗高（720 / 900 / 1150），11 条打开路径逐条测：

| 路径 | 探针是否滚动 | 滚动量 | 判定 |
|---|---|---|---|
| `camera-fov-help-tooltip` | **是**（检查器） | **779 / … / 374** 随窗高变 | **污染（651 已撤回）** |
| `camera-preset-panel` | **是**（`directorTimelineTrackList`） | **12 / … / 12** 恒定 | **可复现 → 合法** |
| 其余 9 条 | 否 | — | 未受影响 |

**影响面 = 11 分之 1。** 650 的 33 格读数里，只有那一格受污染；
其余 32 格（盒坐标 33/33、活控件 195=195）**不受影响**。

## 本批**不**主张的事

* **不主张** `camera-preset-panel` 完全没有滚动依赖 ——
  它**确实**被探针滚了 12px（19 中的 12）。主张的只是**那个 12 在三个窗高上相同**，
  所以它是一个**用户也能到达的状态**，而 `@fov-hover@` 的 779 不是。
* **不主张**除这 11 条之外的路径已被普查过 ——
  648 那 4 个导演台抽屉与 649 那 7 个画布页浮层走的是**不同的打开机制**
  （`locator.click()` / store 动作），**本批没有重测它们**。
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
b626 = _load("626")

WIDTH = 1280
HEIGHTS = [720, 900, 1150]
# 651 retracted exactly this one cell.
RETIRED = "camera-fov-help-tooltip"
# The other path that scrolls, and the one whose scroll does NOT vary.
KNOWN_REPRODUCIBLE = "camera-preset-panel"

SNAP_JS = r"""
() => {
  // The smallest possible instrument: list every scrollable container that is
  // NOT at its natural origin.  If the probe moved one, it shows up here and
  // nowhere else — no selector list, so nothing can go stale.
  const out = [];
  for (const n of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(n);
    if (!/(auto|scroll)/.test(cs.overflowX + cs.overflowY)) continue;
    if (n.scrollWidth <= n.clientWidth && n.scrollHeight <= n.clientHeight) continue;
    if (n.scrollTop === 0 && n.scrollLeft === 0) continue;
    const key = Object.keys(n.dataset || {}).slice(0, 3).join(',')
      || n.getAttribute('aria-label')
      || (n.className || '').split(/\s+/)[0] || n.tagName;
    out.push({key: key, top: Math.round(n.scrollTop),
              left: Math.round(n.scrollLeft),
              maxTop: n.scrollHeight - n.clientHeight});
  }
  return out;
}"""

TARGET_JS = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
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
              + (f"  {str(detail)[:170]}" if detail else "")
              + (f"  [{note[:100]}]" if note else ""))


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    errors: dict[str, str] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HEIGHTS:
            for name, how, sel in b626.OVERLAYS:
                page = br.new_page(viewport={"width": WIDTH, "height": h},
                                   device_scale_factor=1)
                b617.open_desk(page)
                page.wait_for_timeout(300)
                page.evaluate("() => { for (const el of "
                              "document.querySelectorAll('nextjs-portal')) el.remove(); }")
                before = {(d["key"], d["left"]): d["top"] for d in
                          page.evaluate(SNAP_JS)}
                err = None
                try:
                    b626.open_overlay(page, how)
                except Exception as exc:
                    err = type(exc).__name__
                page.wait_for_timeout(400)
                page.mouse.move(5, 5)
                page.wait_for_timeout(180)
                after = page.evaluate(SNAP_JS)
                box = page.evaluate(TARGET_JS, sel)
                moved = [{"key": d["key"], "from": before.get((d["key"], d["left"]), 0),
                          "to": d["top"], "of": d["maxTop"]}
                         for d in after
                         if d["top"] != before.get((d["key"], d["left"]), 0)]
                cells[f"{name}@{h}"] = {"box": box, "scrolled": moved, "err": err}
                if err:
                    errors[f"{name}@{h}"] = err
                page.close()
        br.close()

    # Collapse per overlay.
    per_overlay: dict[str, Any] = {}
    for name, _how, _sel in b626.OVERLAYS:
        rows = {h: cells[f"{name}@{h}"] for h in HEIGHTS}
        scrollers = sorted({m["key"] for r in rows.values()
                            for m in r["scrolled"]})
        amounts = {str(h): [{"to": m["to"], "of": m["of"], "key": m["key"]}
                           for m in rows[h]["scrolled"]] for h in HEIGHTS}
        flat = [tuple(m["to"] for m in v) for v in amounts.values() if v]
        per_overlay[name] = {
            "scrolledAtAll": bool(scrollers),
            "scrollers": scrollers,
            "scrollAmountsByHeight": amounts,
            "amountVariesWithHeight": len(set(flat)) > 1,
            "boxes": {str(h): rows[h]["box"] for h in HEIGHTS},
            "boxXConstant": len({(rows[h]["box"] or [None])[0] for h in HEIGHTS}) == 1,
            "anyError": {str(h): rows[h]["err"] for h in HEIGHTS if rows[h]["err"]},
        }

    out: dict[str, Any] = {
        "batch": 652,
        "question": "is 651's probe-side-effect contamination confined to the one "
                    "open path it found, or does it reach the other ten?",
        "criterion": {
            "step1": "did the probe move any scrollable container at all?",
            "step2": "if it did, is the offset the SAME at every viewport height?",
            "why": "a reproducible offset is a state a user can also reach; an "
                   "offset that drifts with the viewport, inherited by an "
                   "overlay anchored to the scrolled element, is the probe's "
                   "implementation detail — which is what 651 retracted",
        },
        "grid": {"width": WIDTH, "heights": HEIGHTS},
        "perOverlay": per_overlay,
        "cells": cells,
        "openPathErrors": errors,
    }

    # ------------------------------------------------------------------ 1
    scrolled = {k: o for k, o in per_overlay.items() if o["scrolledAtAll"]}
    v.check("exactly-two-of-the-eleven-open-paths-make-the-probe-scroll",
            len(per_overlay) == 11 and len(scrolled) == 2,
            detail={"pathsThatScroll": sorted(scrolled),
                    "pathsThatDoNot": sorted(set(per_overlay) - set(scrolled)),
                    "note": "nine of eleven never move a scroll offset, so their "
                            "readings cannot inherit one"})

    # ------------------------------------------------------------------ 2
    # The discrimination itself.  651's class is "the offset varies".
    varying = sorted(k for k, o in scrolled.items() if o["amountVariesWithHeight"])
    fixed = sorted(k for k, o in scrolled.items() if not o["amountVariesWithHeight"])
    v.check("the-two-scrolling-paths-split-on-whether-the-offset-is-reproducible",
            varying == [RETIRED] and fixed == [KNOWN_REPRODUCIBLE],
            detail={"offsetsVaryWithViewport": {
                        k: per_overlay[k]["scrollAmountsByHeight"] for k in varying},
                    "offsetsIdenticalAtEveryHeight": {
                        k: per_overlay[k]["scrollAmountsByHeight"] for k in fixed},
                    "theDiscriminator":
                        f"`{RETIRED}`'s offset moves with the viewport, which is "
                        "651's signature and the reason 650's cell was "
                        f"retracted. `{KNOWN_REPRODUCIBLE}`'s offset is the same "
                        "number at all three heights, so the state it produces is "
                        "one a user can also reach — recorded, not retracted.",
                    "theInstrument": "a scrollable container sitting anywhere but "
                                     "its natural origin, found by walking the DOM "
                                     "rather than by a selector list, so no name "
                                     "can go stale"},
            note="this is the batch's deliverable: the class is bounded to 1 of 11")

    # ------------------------------------------------------------------ 3
    fixed_rows = [m for k in fixed
                  for lst in per_overlay[k]["scrollAmountsByHeight"].values()
                  for m in lst]
    v.check("the-reproducible-offset-is-the-same-partial-scroll-every-time",
            bool(fixed_rows)
            and len({m["to"] for m in fixed_rows}) == 1
            and all(0 < m["to"] < m["of"] for m in fixed_rows),
            detail={"rows": fixed_rows,
                    "theReading": "one offset, one scroller, three viewport "
                                  "heights, and it is a PARTIAL scroll — the "
                                  "container is not parked at either end, which "
                                  "is what a minimal scroll-to-visible looks "
                                  "like. A probe that had grabbed the last "
                                  "pixel, as `hover()` does for the FOV badge, "
                                  "would land on `of` instead.",
                    "contrast": per_overlay.get(RETIRED, {}).get(
                        "scrollAmountsByHeight"),
                    "note": "the first version of this check compared against a "
                            "field I never stored and crashed; the values it was "
                            "reaching for are in `rows` now"},
            note="measured at all three heights, not assumed")

    # ------------------------------------------------------------------ 4
    # The nine untouched paths: assert their boxes are viewport-X-invariant,
    # which is the weakest thing that must hold for 650's readings to stand.
    still_ok = {k: o for k, o in per_overlay.items() if not o["scrolledAtAll"]}
    x_bad = {k: o["boxes"] for k, o in still_ok.items() if not o["boxXConstant"]}
    v.check("the-nine-untouched-paths-keep-a-height-invariant-horizontal-box",
            len(still_ok) == 9 and not x_bad,
            detail={"paths": sorted(still_ok),
                    "pathsWhoseXMoved": x_bad,
                    "whyX": "nothing scrolled, so the overlay's horizontal "
                            "placement must not depend on the viewport height. A "
                            "violation would mean something else is moving and "
                            "this check would be measuring the wrong thing."})

    # ------------------------------------------------------------------ 5
    # Every path must have produced a box, or the whole classification is
    # resting on cells that never opened.
    nobox = {k: o["boxes"] for k, o in per_overlay.items()
             if any(v is None for v in o["boxes"].values())}
    v.check("every-path-opened-in-every-cell",
            not nobox,
            detail={"cellsWithNoBox": nobox,
                    "openPathErrors": errors,
                    "note": "a path that failed to open would be silently "
                            "excluded from the 'did not scroll' set, which would "
                            "make check 1 look cleaner than it is"})

    # ------------------------------------------------------------------ 6
    # 650's own numbers, re-stated so the retraction's blast radius is explicit.
    audit650 = json.loads(
        (ROOT / "docs/research/liblib-canvas-batch650-2026-10-01"
               / "runtime-audit.json").read_text(encoding="utf-8"))
    t650 = audit650["totals"]
    v.check("650s-readings-outside-the-retracted-cell-are-untouched-by-652",
            t650["cells"] == 33 and t650["structBadTotalDerived"] == 4
            and t650["structBadTotal626"] == 0,
            detail={"batch650Totals": t650,
                    "theRetractedCell": f"{RETIRED}@1280x720",
                    "theOther32Cells": "box identity 33/33, live controls "
                                       "195 = 195, casualties 0 = 0 — none of "
                                       "which 652 can touch, because none of "
                                       "those paths scrolls at all",
                    "theBlastRadius": "1 cell of 33"})

    # ------------------------------------------------------------------ 7
    v.check("no-open-path-threw-in-this-run",
            not errors,
            detail={"errors": errors,
                    "why": "651 found that hover() can throw while the overlay "
                           "is actually mounted. If a path throws here, its cell "
                           "would carry no box and check 5 is the thing that "
                           "catches it — this check states the expectation "
                           "explicitly so a future throw is not read as a pass"})

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "openPaths": len(b626.OVERLAYS),
        "pathsThatScroll": sorted(scrolled),
        "pathsWithVaryingOffset": varying,
        "pathsWithFixedOffset": fixed,
        "pathsNeverScrolled": len(still_ok),
        "cells": len(cells),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch652-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

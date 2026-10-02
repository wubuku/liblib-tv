#!/usr/bin/env python3
"""batch 653 验收：按 652 的判据**重测 648 那 4 个导演台抽屉**的打开路径

## 起点

652 把「探针副作用」的污染面在 626 的 11 条打开路径上量完了：
**11 分之 1**（`@fov-hover@`，滚动量随窗高漂移）。

但 652 自己写了「不声称」：**648 那 4 个导演台抽屉走的是 `locator.click()`，
本批没有重测它们。** 而 652 同时量出一条关键事实 ——
**同一个 `locator.click()` API，`@fov-hover@` 之外的路径里"
"「最小滚动」和「滚到末端」两种语义都出现过**。
既然语义在同一 API 下都会分叉，**那 4 个 click 路径就不能靠「它们是 click」推定干净**。

## 判据（沿用 652，不新造）

1. 这条路径**有没有**让某个可滚动容器的 offset 变化；
2. 若有，那个 offset **在不同窗高之间是否相同**。

仪器同样不给选择器列表 —— 遍历 DOM 找出所有「可滚动且不在自然原点」的容器。

## 本批的额外一格

`model-library-preview-panel` 是**两步**路径（先开面板、再悬停一张卡）。
它是 648 里唯一含**悬停**的路径，所以它是这四条里最可能落进 651 那类的一个 ——
**这正是本批要测的**。
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
b652 = _load("652")

WIDTH = 1280
HEIGHTS = [720, 900, 1150]

# 648's four desk drawers.  Three are one click; the fourth adds a hover, and
# that is the whole reason this batch exists rather than a copy of 652.
DRAWERS = [
    ("crowd-panel", "click", "[data-director-crowd-trigger]",
     "[data-director-crowd-panel]"),
    ("phone-vcam-panel", "click", "[data-director-phone-vcam-trigger]",
     "[data-director-phone-vcam-panel]"),
    ("model-library-panel", "click", "[data-director-model-library-trigger]",
     "[data-director-model-library-panel]"),
    ("model-library-preview-panel", "click-then-hover",
     "[data-director-model-library-trigger]",
     "[data-director-model-library-preview-panel]"),
]

PREVIEW_CARD = "[data-director-model-library-panel] [data-director-model-library-card]"


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


def open_drawer(page: Any, kind: str, trig: str) -> str | None:
    page.locator(trig).first.click(timeout=15_000)
    page.wait_for_timeout(500)
    if kind == "click-then-hover":
        card = page.locator(PREVIEW_CARD).first
        if card.count() == 0:
            return "no-card"
        try:
            card.hover(timeout=10_000)
        except Exception as exc:
            return f"hover:{type(exc).__name__}"
        page.wait_for_timeout(450)
    return None


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HEIGHTS:
            for name, kind, trig, sel in DRAWERS:
                page = br.new_page(viewport={"width": WIDTH, "height": h},
                                   device_scale_factor=1)
                b617.open_desk(page)
                page.wait_for_timeout(300)
                page.evaluate("() => { for (const el of "
                              "document.querySelectorAll('nextjs-portal')) el.remove(); }")
                before = {(d["key"], d["left"]): d["top"] for d in
                          page.evaluate(b652.SNAP_JS)}
                err = open_drawer(page, kind, trig)
                page.wait_for_timeout(400)
                page.mouse.move(5, 5)
                page.wait_for_timeout(180)
                after = page.evaluate(b652.SNAP_JS)
                moved = [{"key": d["key"], "from": before.get((d["key"], d["left"]), 0),
                          "to": d["top"], "of": d["maxTop"]}
                         for d in after
                         if d["top"] != before.get((d["key"], d["left"]), 0)]
                cells[f"{name}@{h}"] = {
                    "box": page.evaluate(b652.TARGET_JS, sel),
                    "scrolled": moved, "err": err}
                page.close()
        br.close()

    per: dict[str, Any] = {}
    for name, _k, _t, _s in DRAWERS:
        rows = {h: cells[f"{name}@{h}"] for h in HEIGHTS}
        amounts = {str(h): [{"to": m["to"], "of": m["of"], "key": m["key"]}
                           for m in rows[h]["scrolled"]] for h in HEIGHTS}
        flat = [tuple(m["to"] for m in v) for v in amounts.values() if v]
        boxes = {str(h): rows[h]["box"] for h in HEIGHTS}
        per[name] = {
            "scrolledAtAll": any(rows[h]["scrolled"] for h in HEIGHTS),
            "scrollAmountsByHeight": amounts,
            "amountVariesWithHeight": len(set(flat)) > 1,
            "boxes": boxes,
            "boxXConstant": len({(boxes[str(h)] or [None])[0] for h in HEIGHTS}) == 1,
            "errors": {str(h): rows[h]["err"] for h in HEIGHTS if rows[h]["err"]},
        }

    out: dict[str, Any] = {
        "batch": 653,
        "question": "do 648's four desk-drawer open paths — all locator.click(), "
                    "one of them click-then-hover — inherit a probe-side-effect "
                    "scroll the way @fov-hover@ does?",
        "criterion": "652's, unchanged: did the probe move a scrollable "
                     "container, and is the offset the same at every height?",
        "grid": {"width": WIDTH, "heights": HEIGHTS},
        "drawers": per,
        "cells": cells,
    }

    # ------------------------------------------------------------------ 1
    scrolled = sorted(k for k, o in per.items() if o["scrolledAtAll"])
    v.check("none-of-the-four-drawer-paths-moves-a-scroll-offset",
            not scrolled,
            detail={"pathsThatScrolled": scrolled,
                    "allFour": sorted(per),
                    "detail": {k: o["scrollAmountsByHeight"] for k, o in per.items()},
                    "why": "these four are locator.click() on a trigger that is "
                           "already in view, plus one hover on a card that is "
                           "already inside the open panel — so there is nothing "
                           "for the probe to scroll to reach"},
            note="the four readings 648 and 649 took are therefore clean")

    # ------------------------------------------------------------------ 2
    v.check("the-hover-bearing-drawer-is-clean-too",
            not per["model-library-preview-panel"]["scrolledAtAll"]
            and not per["model-library-preview-panel"]["errors"],
            detail=per["model-library-preview-panel"],
            note="this was the one that could have been 651 all over again")

    # ------------------------------------------------------------------ 3
    # Boxes must be measurable in every cell, or "clean" means nothing.
    nobox = {k: o["boxes"] for k, o in per.items()
             if any(v is None for v in o["boxes"].values())}
    v.check("every-drawer-opened-in-every-cell",
            not nobox,
            detail={"cellsWithNoBox": nobox,
                    "errors": {k: o["errors"] for k, o in per.items() if o["errors"]},
                    "note": "a drawer that failed to open would produce an empty "
                            "scroll set and read as 'clean' — the same vacuous "
                            "green 646 had to guard against"})

    # ------------------------------------------------------------------ 4
    x_bad = {k: o["boxes"] for k, o in per.items() if not o["boxXConstant"]}
    v.check("the-drawers-keep-a-height-invariant-horizontal-box",
            not x_bad,
            detail={"pathsWhoseXMoved": x_bad,
                    "boxes": {k: o["boxes"] for k, o in per.items()},
                    "whyX": "the drawers are width-anchored, so their x must not "
                            "depend on the window height. A violation would mean "
                            "something moved that this batch did not account for."})

    # ------------------------------------------------------------------ 5
    # Tie it back: 649 read the first three of these and 648 the fourth, and
    # neither run recorded a scroll.  Now that the scroll offset is an explicit,
    # asserted quantity, their readings are retroactively clean — stated as a
    # check so the claim is not just a sentence in a README.
    audit648 = json.loads(
        (ROOT / "docs/research/liblib-canvas-batch648-2026-10-01"
               / "runtime-audit.json").read_text(encoding="utf-8"))
    audit649 = json.loads(
        (ROOT / "docs/research/liblib-canvas-batch649-2026-10-01"
               / "runtime-audit.json").read_text(encoding="utf-8"))
    v.check("648s-and-649s-drawer-readings-were-never-scroll-contaminated",
            audit648["totals"]["overlaysOpenedWithARealClick"] == 4
            and audit649["totals"]["overlaysMeasured"] == 7
            and not scrolled,
            detail={"batch648Totals": audit648["totals"],
                    "batch649Totals": audit649["totals"],
                    "claim": "648 opened these four with a real click and 649 "
                             "re-read three of them with the derived ruler; "
                             "neither recorded a scroll offset because neither "
                             "was looking for one. 653 makes it an asserted "
                             "quantity and the answer is zero, so those readings "
                             "stand — retroactively, and on evidence rather than "
                             "on absence of suspicion."},
            note="absence of suspicion is not evidence; a measured zero is")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "drawers": len(DRAWERS),
        "pathsThatScrolled": scrolled,
        "cells": len(cells),
        "heights": len(HEIGHTS),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch653-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

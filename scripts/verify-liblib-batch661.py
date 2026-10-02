#!/usr/bin/env python3
"""batch 661 验收：658 那两族剩余的读数各收一条闭式，并**纠正 657/659 对 `help` 的一处归因**

## 起点

658 的桌内被遮是 5（900/1150）到 7（720）枚，659 给提示条那 4 枚收了闭式，
另外两族还没有：`help`（三个窗高全中）与两枚颜色控件（**只在 720**）。
本批各收一条。

## 一：`help` 的盖住者是 `收起属性`，不是「时间轴轨道行」

**657 与 659 都写「被时间轴轨道行盖住」。那是错的。**
658 的 audit 里的 `coveredBy.label` 一直写着 **`收起属性`** ——
我读的是 class 前缀 `button.group.relative.z-[1]`，把 `z-[1]` 当成了「轨道行」的证据。

`收起` 正是 **632 的在案缺陷**（那个 170px 居中视角组）。
**盖住 `help` 的是它。** 一条缺陷的爆炸半径第一次被量到。

## 二：`elementsFromPoint` 有两种读法，**只有一种是对的**

661 开工的探针问「help 在不在命中栈里」→ **True**（它在**第 8 位**）。
658 问「栈顶是不是它」→ **False**（栈顶是 `收起属性`）。

**两个都是正确读数，答的是不同问题。** 而**用户的点击落在栈顶**，
所以 658 那个口径才是操作上正确的那个。

`help` 的真实状态是：**在栈里、但不是栈顶、因此点不到。**
把它记成「不在栈里」和记成「可点」都是错的。

## 三：颜色控件的闭式 —— 定边界的**不是**导出触发器

第一版猜的是「不可达 ⟺ 导出触发器 top < 颜色控件 bottom」⇒ `H < 756`。
**错了两处**：

1. **矩形相交不决定**。H=750 时两个矩形纵向交叠 **6px**，而控件**可达** ——
   因为它的**中心**在触发器上沿**之上**。
2. **漏了第二个盖住者**。时间轴**通栏**且在矮视口下够到检视器下部，
   所以 H=700 是被**导出规则说应该清楚**的机制盖住的。

对的那一条：

    不可达  ⟺  控件自己的中心被覆盖 —— 被【导出触发器】或【时间轴】任一覆盖

    导出触发器 top = H − 177   （它在底栏上）
    时间轴 top      = H − 182   （它钉在底边）
    颜色控件中心    = 567       （它在检视器里，不随窗高移动）

    导出触发器的窗口 = 716..744 —— **完全落在被遮区内部，它从不单独决定任何事**
    时间轴的窗口     = H ≤ 749

    ⟹ **不可达 ⟺ H ≤ 749 ，即 可达 ⟺ H ≥ 750**（749 不可达 / 750 可达）

**定边界的是时间轴，不是导出触发器** —— 移动较慢的那个不决定答案，移动较快的那个决定。

## 本批**不**主张的事

* **不主张**源站同样如此 —— **零源站断言**。
* **不主张**`收起属性` 盖住 `help` 是缺陷 —— 那是**产品判断**；
  本批只说 clone 里它盖住了，并把它接回 632。
* **不主张**「栈顶」口径在所有场景下都该替换「在栈里」口径 ——
  本批主张的是**点击**场景下该用栈顶。
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
b654 = _load("654")

scroll_gate = b654.scroll_gate
WIDTH = 1280

# Family B: bracket the predicted 756, and include two heights that already
# have a known answer (720 unreachable, 900 reachable) so the sweep is
# anchored on both sides.
COLOUR_HEIGHTS = [700, 715, 716, 720, 744, 745, 748, 749, 750, 751, 760, 900]
HELP_HEIGHTS = [720, 900, 1150]
WIDTH_PROBE = [1531]

STACK_JS = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return {found: false};
  const r = el.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const st = document.elementsFromPoint(cx, cy);
  const top = st[0] || null;
  const R = e => { const b = e.getBoundingClientRect();
    return {y: Math.round(b.y), b: Math.round(b.bottom),
            x: Math.round(b.x), r: Math.round(b.right)}; };
  return {found: true,
          rect: R(el), centre: [Math.round(cx), Math.round(cy)],
          stackDepth: st.length,
          indexInStack: st.indexOf(el),
          // READING ONE: is the target anywhere in the hit stack?
          inStack: st.includes(el) || st.some(e => el.contains(e)),
          // READING TWO: is the target what a click would actually reach?
          topIsSelf: !!(top && (top === el || el.contains(top))),
          topLabel: top ? (top.getAttribute('aria-label')
                            || (top.textContent || '').trim()
                               .replace(/\\s+/g, ' ').slice(0, 20)) : null,
          topClass: top ? (top.getAttribute('class') || '').split(' ')
                          .filter(Boolean).slice(0, 4).join('.') : null,
          topRect: top ? R(top) : null};
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
              + (f"  {str(detail)[:165]}" if detail else "")
              + (f"  [{note[:100]}]" if note else ""))


def main() -> int:
    v = Verifier()
    help_cells: dict[str, Any] = {}
    colour_cells: dict[str, Any] = {}
    width_cells: dict[str, Any] = {}
    prior = json.loads(
        (ROOT / "docs/research/liblib-canvas-batch658-2026-10-01"
                / "runtime-audit.json").read_text(encoding="utf-8"))

    with sync_playwright() as p:
        br = p.chromium.launch()
        for h in HELP_HEIGHTS:
            page = br.new_page(viewport={"width": WIDTH, "height": h},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(400)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.mouse.move(5, 5)
            page.wait_for_timeout(220)
            o = page.evaluate(STACK_JS, "[data-director-rail-entry='help']")
            exp = page.evaluate(STACK_JS, "[data-director-export-trigger]")
            o["exportTrigger"] = exp
            o["gate"] = scroll_gate(page)
            page.close()
            help_cells[str(h)] = o
        for h in COLOUR_HEIGHTS:
            page = br.new_page(viewport={"width": WIDTH, "height": h},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(400)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.mouse.move(5, 5)
            page.wait_for_timeout(220)
            o = page.evaluate(STACK_JS, "[data-director-color-picker]")
            o["hex"] = page.evaluate(STACK_JS, "[data-director-hex-input]")
            o["exportTrigger"] = page.evaluate(
                STACK_JS, "[data-director-export-trigger]")
            o["timeline"] = page.evaluate(
                STACK_JS, "[data-director-timeline]")
            o["gate"] = scroll_gate(page)
            page.close()
            colour_cells[str(h)] = o
        for w in WIDTH_PROBE:
            page = br.new_page(viewport={"width": w, "height": 1150},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(400)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.mouse.move(5, 5)
            page.wait_for_timeout(220)
            o = page.evaluate(STACK_JS, "[data-director-scene-prompt-submit]")
            o["bar"] = page.evaluate(
                STACK_JS, "[data-director-scene-prompt-bar]")
            page.close()
            width_cells[str(w)] = o
        br.close()

    # ---- family B: the closed form.
    # The first guess was "unreachable <=> exportTop < colourBottom", i.e. H < 756.
    # It was wrong twice: the rectangles overlapping does not decide it (at
    # H=750 they overlap by 6px and the control is reachable), and there is a
    # SECOND coverer the first version forgot — the timeline, which is
    # full-width and reaches the inspector's lower part at short heights.
    # What decides it is whether the control's own CENTRE is covered, by
    # either of the two.
    exp_tops = {h: c["exportTrigger"]["rect"]["y"] for h, c in colour_cells.items()}
    linear = all(exp_tops[h] == int(h) - 177 for h in exp_tops)
    colour_bottoms = {h: c["rect"]["b"] for h, c in colour_cells.items()}
    colour_centres = {h: c["centre"][1] for h, c in colour_cells.items()}
    centre_constant = len(set(colour_centres.values())) == 1
    timeline_tops = {h: c["timeline"]["rect"]["y"] for h, c in colour_cells.items()}
    tl_linear = all(timeline_tops[h] == int(h) - 182 for h in timeline_tops)

    def predicted(h: str) -> bool:
        cy = colour_centres[h]
        by_export = exp_tops[h] <= cy
        by_timeline = timeline_tops[h] <= cy
        return by_export or by_timeline   # True == unreachable

    predicted_map = {h: predicted(h) for h in colour_cells}
    mism_B = {h: {"topIsSelf": colour_cells[h]["topIsSelf"],
                  "predictedUnreachable": predicted_map[h],
                  "centreY": colour_centres[h],
                  "exportTop": exp_tops[h], "timelineTop": timeline_tops[h]}
              for h in colour_cells
              if predicted_map[h] == colour_cells[h]["topIsSelf"]}
    first_ok = next((int(h) for h in sorted(colour_cells, key=int)
                     if colour_cells[h]["topIsSelf"]), None)
    last_bad = max((int(h) for h in sorted(colour_cells, key=int)
                    if not colour_cells[h]["topIsSelf"]), default=None)
    export_window = [h for h in colour_cells
                     if exp_tops[h] <= colour_centres[h]]

    # ---- family A: the correction
    top_labels = {h: c["topLabel"] for h, c in help_cells.items()}
    in_stack = {h: c["inStack"] for h, c in help_cells.items()}
    top_self = {h: c["topIsSelf"] for h, c in help_cells.items()}
    idx = {h: c["indexInStack"] for h, c in help_cells.items()}
    b658_help = [r for r in prior["perHeight"]["1150"]["occludedKeys"]
                 if "rail-entry" in r]

    out: dict[str, Any] = {
        "batch": 661,
        "question": "close the two families 659 did not, and correct the "
                    "attribution 657/659 gave for `help`",
        "familyA_help": {
            "cells": help_cells,
            "topLabelAtEveryHeight": top_labels,
            "inStackAtEveryHeight": in_stack,
            "topIsSelfAtEveryHeight": top_self,
            "indexInStack": idx,
            "theCorrection": "657 and 659 both wrote 'covered by a timeline "
                             "object row'. 658's own audit recorded the label "
                             "`收起属性` all along; I read the class prefix "
                             "`button.group.relative.z-[1]` and let z-[1] pass "
                             "for a row. It is 632's defect, and its blast "
                             "radius now reaches the icon rail.",
            "theTwoReadings": {
                "inStack": "is the target anywhere in the hit stack? True for "
                           "help at every height, at index 8.",
                "topIsSelf": "is the target what a click reaches? False.",
                "whichIsRight": "for CLICKING, topIsSelf. `help` is in the "
                                "stack and is not clickable — both statements "
                                "are true and only one of them is operational.",
            },
        },
        "familyB_colour": {
            "cells": colour_cells,
            "closedForm": "unreachable  <=>  the control's own centre is "
                          "covered, by EITHER the export trigger OR the timeline",
            "centreY": colour_centres,
            "centreYIsConstant": centre_constant,
            "exportTop": exp_tops,
            "exportTopIsHminus177": linear,
            "timelineTop": timeline_tops,
            "timelineTopIsHminus182": tl_linear,
            "therefore": "unreachable  <=>  H <= 749,  i.e. reachable  <=>  H >= 750",
            "whoSetsTheBoundary": "the TIMELINE, not the export trigger",
            "theExportWindows": export_window,
            "theExportWindowIsEntirelyInsideTheBlockedRegion": True,
            "lastUnreachableHeight": last_bad,
            "firstReachableHeight": first_ok,
            "mismatches": mism_B,
            "theFirstGuessAndWhyItWasWrong": {
                "guessed": "unreachable <=> exportTop < colourBottom, i.e. H < 756",
                "wrongBecause1": "rectangle overlap does not decide it — at "
                                 "H=750 the two rects overlap by 6px and the "
                                 "control IS reachable, because its centre is "
                                 "above the export trigger's top edge",
                "wrongBecause2": "there is a second coverer the first version "
                                 "forgot: the timeline is full-width and reaches "
                                 "the inspector's lower part at short heights, "
                                 "so H=700 is blocked by a mechanism the export "
                                 "rule says should be clear",
            },
        },
        "widthProbe1531": width_cells,
        "from658": {"helpKey": b658_help},
    }

    # ------------------------------------------------------------------ 1
    v.check("the-coverer-of-help-is-收起属性-and-not-a-timeline-row",
            all(v_ == "收起属性" for v_ in top_labels.values())
            and not top_self["1150"],
            detail={"topLabelAtEveryHeight": top_labels,
                    "topClass": {h: help_cells[h]["topClass"]
                                 for h in sorted(help_cells)},
                    "what657And659Wrote": "「被时间轴轨道行盖住」",
                    "whatTheDataHasAlwaysSaid": "658's occludedDetail carried "
                                                "coveredBy.label = 收起属性 from "
                                                "the first run",
                    "howTheErrorHappened": "I read the class prefix and treated "
                                           "z-[1] as evidence for a row. The "
                                           "label was in the file the whole time.",
                    "connectionTo632": "收起 is 632's in-case defect — the 170px "
                                       "centred perspective group. Its blast "
                                       "radius now reaches the icon rail, which "
                                       "is new information about a known case."},
            note="a label in the data beats a class prefix in your head")

    # ------------------------------------------------------------------ 2
    v.check("help-is-in-the-stack-and-is-not-the-top-of-it",
            all(in_stack.values()) and not any(top_self.values())
            and all(idx[h] is not None and idx[h] > 0 for h in idx),
            detail={"inStack": in_stack, "topIsSelf": top_self,
                    "indexInStack": idx,
                    "theTwoQuestions": "658 asks 'is the top the target'. The "
                                       "probe that started this batch asked 'is "
                                       "the target in the stack' and answered "
                                       "True. Both are correct readings of the "
                                       "same stack; only the first one is about "
                                       "clicking.",
                    "whyItMatters": "reporting 'in the stack' as 'reachable' "
                                     "would have turned a blocked control into "
                                     "a clean one, and reporting 'not topmost' "
                                     "as 'not rendered' would have repeated 659's "
                                     "clipping error."},
            note="one API, two questions; only one of them is operational")

    # ------------------------------------------------------------------ 3
    v.check("the-colour-family-closed-form-holds-and-the-timeline-sets-756s-real-edge",
            not mism_B and linear and tl_linear and centre_constant
            and last_bad is not None and first_ok is not None
            and first_ok == last_bad + 1 and first_ok == 750,
            detail={"centreY": colour_centres,
                    "centreYIsConstant": centre_constant,
                    "exportTop": exp_tops, "exportTopIsHminus177": linear,
                    "timelineTop": timeline_tops, "timelineTopIsHminus182": tl_linear,
                    "predictedUnreachable": predicted_map,
                    "measuredReachable": {h: colour_cells[h]["topIsSelf"]
                                          for h in sorted(colour_cells, key=int)},
                    "mismatches": mism_B,
                    "lastUnreachable": last_bad, "firstReachable": first_ok,
                    "whoSetsTheBoundary": "the timeline. The export trigger's "
                                          "window (H-177 <= 567, i.e. 716..744) "
                                          "sits ENTIRELY inside the blocked "
                                          "region, so it never decides anything "
                                          "on its own.",
                    "theForm": "the export trigger rides the bottom bar, so its "
                               "top is H-177; the timeline is pinned to the "
                               "bottom, so its top is H-182; the colour picker "
                               "hangs in the inspector, so its centre is pinned "
                               "at 567 whatever the height. The timeline crosses "
                               "567 at H = 749 and that is the only edge that "
                               "changes an answer.",
                    "theFirstGuessAndWhyItWasWrong": {
                        "guessed": "unreachable <=> exportTop < colourBottom, "
                                   "i.e. H < 756",
                        "wrongBecause1": "rectangle overlap does not decide it — "
                                         "at H=750 the rects overlap by 6px and "
                                         "the control IS reachable, because its "
                                         "centre is above the trigger's top edge",
                        "wrongBecause2": "a second coverer the first version "
                                         "forgot: the timeline is full-width and "
                                         "reaches the inspector's lower part at "
                                         "short heights, so H=700 is blocked by a "
                                         "mechanism the export rule says is clear",
                    },
                    "theAnchors": "720 blocked and 900 reachable were already "
                                  "in 658's record; the sweep brackets them at "
                                  "749/750."},
            note="the two members of the comparison move differently, and the "
                 "one that moves faster is the one that decides")

    # ------------------------------------------------------------------ 4
    v.check("both-colour-controls-share-the-one-boundary",
            all(colour_cells[h]["hex"]["topIsSelf"]
                == colour_cells[h]["topIsSelf"] for h in colour_cells),
            detail={"colourPicker": {h: colour_cells[h]["topIsSelf"]
                                     for h in sorted(colour_cells, key=int)},
                    "hexInput": {h: colour_cells[h]["hex"]["topIsSelf"]
                                 for h in sorted(colour_cells, key=int)},
                    "whyWorthAsserting": "two controls covered by one trigger "
                                         "usually means one rule, but 'usually' "
                                         "is not a measurement. If they ever "
                                         "split, this goes red."},
            note="one rule for two controls is a claim until it is tested twice")

    # ------------------------------------------------------------------ 5
    # 660 left the third rung of its ladder unswept on one side.
    w31 = width_cells.get("1531", {})
    v.check("660s-third-ladder-rung-is-now-bracketed-on-both-sides",
            bool(w31) and w31.get("topIsSelf") is True,
            detail={"at1531": {k: w31.get(k) for k in
                               ("rect", "centre", "indexInStack", "inStack",
                                "topIsSelf", "topLabel")},
                    "what660Left": "660 derived rowFullyInside's first true width "
                                   "as 1532 and said the true edge might sit "
                                   "between 1531 and 1532 because 1531 had not "
                                   "been swept.",
                    "whatThisAdds": "1531 has now been swept. The prompt bar's "
                                    "row is inside its clip from 1532, and the "
                                    "submit button has been reachable since 1510 "
                                    "— so the reachable ladder's bottom rung was "
                                    "never in doubt; only the row's was."},
            note="closing a gap a previous batch left open, rather than opening "
                 "a new one")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "helpHeights": HELP_HEIGHTS,
        "helpTopLabel": sorted(set(top_labels.values())),
        "helpInStack": in_stack,
        "helpTopIsSelf": top_self,
        "colourHeights": COLOUR_HEIGHTS,
        "colourCentreY": sorted(set(colour_centres.values())),
        "colourLastUnreachable": last_bad,
        "colourFirstReachable": first_ok,
        "whoSetsTheBoundary": "timeline",
        "correctionsMade": 2,
    }
    audit = ROOT / "docs/research/liblib-canvas-batch661-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

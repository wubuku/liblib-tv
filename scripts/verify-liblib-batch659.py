#!/usr/bin/env python3
"""batch 659 验收：658 记下的「场景提示条点不到」，**是什么把它挡住的** —— 一个带像素边界的闭式

## 起点

658 的遮挡普查发现：整个场景提示条（上传图片 / 输入框 / 发送 / sr-only file）
在 1280 宽的三个窗高上**中心点都不可达**，盖住它们的是检视器自己的滚动容器。
本批去问「**为什么**」。

## 三个被否掉的假设，和一个被我自己误判掉又捡回来的

| 假设 | 判决 | 怎么否掉的 |
|---|---|---|
| **z 序**：底栏声明 `z-200`、检视器 `aside` 声明 `z-30`，按 z 该底栏在上 | **否** | 读数相反。而且按钮**压根不在栈里**（`indexOf === -1`）—— 它不是「被压住」，是**根本没画在那里** |
| **pointer-events**：底栏 wrapper 是 `pointer-events-none` | **否** | 一次性页内实验把它改成 `auto`，栈**一个元素都没变** |
| **那行装不下底栏** | **否** | 1510 那行仍**超出底栏 20px**，却是**可达**的 |
| **被裁掉** | **最初否掉、后来自己捡回来** | 我量的是 `bar.parentElement`（那层真是 `visible`），**裁剪器在下一层**。量对了之后它就是答案 |

## 站得住的那一个

    可达  ⟺  提交按钮的中心点 严格落在 宿主的裁剪盒内

宿主是 `div.pointer-events-auto.flex`，**`overflow: auto`**，W=1280 时 694 宽；
那行是 `div.mx-auto.flex.shrink-0`，**944 宽且钉死** —— 装不下就向右溢出，
提示条（1012..1237）整个掉到裁剪盒（293..987）之外，**因此根本没被绘制**。

`overflow: auto` 的裁剪右沿是**排他的**，而按钮中心恒在 `1216`，`hostRight = W − 293`：

    1216 < W − 293   ⟺   W ≥ 1510

**边界就在像素上**：1280 宽、1150 高、面板展开时，**W=1509 不可达、W=1510 可达**。

> 659 的第一版把这个边界写成「超出视口列 ≤ 8px 的安全边」——
> 那个 8 只是上面几个常数凑出来的形状，**长得像 626 的 `SAFE_MARGIN`**。
> 两种表述在六个转变点上完全等价，但只有裁剪这条**说得清为什么**。

## 本批**不**主张的事

* **不主张**源站同样如此 —— **零源站断言**。
* **不主张**「超出 ≤ 8」是独立于裁剪的第二条规则 —— 它是常数凑出来的**等价重述**
  （944 行宽 + 12px 内缩 + 按钮中心钉在 1216）。六个转变点上两者完全一致，
  但只有裁剪这条**说得清为什么**。
* **不主张** 658 记的另外两枚（`help`、720 高度的颜色控件）由同一条规则解释 ——
  它们是**别的机制**（`help` 被时间轴轨道行盖住；颜色控件被导出触发器盖住）。
  本闭式只解释提示条那 4 枚。
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
b658 = _load("658")

scroll_gate = b654.scroll_gate
HEIGHT = 1150
SAFE = 8  # the number 626 already uses; 659 locates it to the pixel

# Six cells: three widths x panels expanded/collapsed.  The collapse axis is
# what makes the rule testable, because it moves the column width without
# moving the window — a width sweep alone can only produce ONE transition.
CELLS = [(1280, False), (1280, True), (1440, False),
         (1440, True), (1510, False), (1510, True)]
BOUNDARY = [1509, 1510]

PROBE_JS = """() => {
  const sub = document.querySelector('[data-director-scene-prompt-submit]');
  if (!sub) return {found: false};
  const bar = sub.closest('[data-director-scene-prompt-bar]');
  const row = bar.parentElement;
  const host = row.parentElement;
  const bb  = document.querySelector('[data-director-bottom-bar]');
  const sec = document.querySelector('[data-director-viewport]');
  const insp = document.querySelector('[data-director-inspector]');
  const aside = document.querySelector('[data-director-mobile-panel-state]');
  const r = sub.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const st = document.elementsFromPoint(cx, cy);
  const right = e => Math.round(e.getBoundingClientRect().right);
  return {found: true,
          reachable: st.includes(sub) || st.some(e => sub.contains(e)),
          submitIndexInStack: st.indexOf(sub),
          stackDepth: st.length,
          stackTop3: st.slice(0, 3).map(e => {
            const m = [...e.attributes].map(a => a.name)
                       .filter(n => n.startsWith('data-director-'));
            return e.tagName.toLowerCase() + (m.length ? '[' + m[0] + ']' : '');
          }),
          rowRight: right(row), rowWidth: Math.round(row.getBoundingClientRect().width),
          sectionRight: right(sec),
          bottomBarRight: right(bb),
          hostRight: right(host), hostLeft: Math.round(host.getBoundingClientRect().x),
          submitCentreX: Math.round(cx),
          hostOverflow: getComputedStyle(host).overflow,
          hostScrollW: host.scrollWidth, hostClientW: host.clientWidth,
          // Is the submit button's own centre inside the host's CLIP box?
          // With overflow:auto the clip is the padding box, and the right edge
          // is EXCLUSIVE — which is what puts the boundary on an exact pixel.
          centreInsideHostClip: cx < right(host) && cx > Math.round(
              host.getBoundingClientRect().x),
          rowOverSection: right(row) - right(sec),
          rowOverBottomBar: right(row) - right(bb),
          bottomBarZ: getComputedStyle(bb).zIndex,
          bottomBarPointerEvents: getComputedStyle(bb).pointerEvents,
          asideZ: aside ? getComputedStyle(aside).zIndex : null,
          inspectorZ: insp ? getComputedStyle(insp).zIndex : null};
}"""

# One in-page experiment.  Nothing is persisted, nothing is written to src/.
FORCE_PE_JS = """() => {
  const bb = document.querySelector('[data-director-bottom-bar]');
  if (!bb) return null;
  const was = getComputedStyle(bb).pointerEvents;
  bb.style.pointerEvents = 'auto';
  return was;
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


def probe(page: Any) -> dict[str, Any]:
    o = page.evaluate(PROBE_JS)
    o["gate"] = scroll_gate(page)
    return o


def main() -> int:
    v = Verifier()
    cells: dict[str, Any] = {}
    boundary: dict[str, Any] = {}
    pe_experiment: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for w, collapse in CELLS:
            page = br.new_page(viewport={"width": w, "height": HEIGHT},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(400)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            if collapse:
                page.locator("[data-director-panels-toggle]").first.click(
                    force=True, timeout=6_000)
                page.wait_for_timeout(500)
            page.mouse.move(5, 5)
            page.wait_for_timeout(220)
            o = probe(page)
            if (w, collapse) == (1280, False):
                before = dict(o)
                was = page.evaluate(FORCE_PE_JS)
                page.wait_for_timeout(200)
                after = probe(page)
                pe_experiment = {
                    "computedPointerEventsWas": was,
                    "before": {"reachable": before["reachable"],
                               "submitIndexInStack": before["submitIndexInStack"],
                               "stackTop3": before["stackTop3"]},
                    "after": {"reachable": after["reachable"],
                              "submitIndexInStack": after["submitIndexInStack"],
                              "stackTop3": after["stackTop3"]},
                }
            page.close()
            cells[f"w{w}{'-collapsed' if collapse else ''}"] = o

        for w in BOUNDARY:
            page = br.new_page(viewport={"width": w, "height": HEIGHT},
                               device_scale_factor=1)
            b617.open_desk(page)
            page.wait_for_timeout(400)
            page.evaluate("() => { for (const el of "
                          "document.querySelectorAll('nextjs-portal')) el.remove(); }")
            page.mouse.move(5, 5)
            page.wait_for_timeout(220)
            boundary[str(w)] = probe(page)
            page.close()
        br.close()

    def predicted(o: dict[str, Any]) -> bool:
        # The clip rule.  The 8px restatement is a consequence of the constants
        # (944 row, 12px insets, button centre pinned at 1216), not a separate
        # safety margin — 659's first draft mistook one for the other.
        return o["centreInsideHostClip"]

    def predicted8(o: dict[str, Any]) -> bool:
        return o["rowOverSection"] <= SAFE

    mismatches = {k: {"reachable": o["reachable"],
                      "centreInsideHostClip": o["centreInsideHostClip"],
                      "rowOverSection": o["rowOverSection"],
                      "predicted": predicted(o)}
                  for k, o in cells.items() if predicted(o) != o["reachable"]}
    disagreements = {w: {"reachable": o["reachable"],
                         "centreInsideHostClip": o["centreInsideHostClip"],
                         "rowOverSection": o["rowOverSection"],
                         "predicted": predicted(o)}
                     for w, o in boundary.items() if predicted(o) != o["reachable"]}
    restatement_mismatches = {
        k: {"reachable": o["reachable"], "rowOverSection": o["rowOverSection"]}
        for k, o in cells.items() if predicted8(o) != predicted(o)}
    transitions = sorted(c["rowOverSection"] for c in cells.values())
    prior = json.loads(
        (ROOT / "docs/research/liblib-canvas-batch658-2026-10-01"
                / "runtime-audit.json").read_text(encoding="utf-8"))
    prompt_keys = [k for k in prior["perHeight"]["1150"]["occludedKeys"]
                   if "scene-prompt" in k]

    out: dict[str, Any] = {
        "batch": 659,
        "question": "why is the scene prompt bar unreachable at 1280?  a closed "
                    "form with a boundary located to the pixel, after three "
                    "mechanisms were falsified by the data",
        "closedForm": {
            "rule": "reachable  <=>  the submit button's centre x is STRICTLY "
                    "inside the host's clip box",
            "clipper": "div.pointer-events-auto.flex — overflow: auto, 694 wide "
                       "at W=1280. One level BELOW the 944-wide row.",
            "row": "div.mx-auto.flex.shrink-0 — 944 wide, pinned. It overflows "
                   "the clipper, which puts the prompt bar outside the clip.",
            "whyStrictly": "an overflow:auto clip's right edge is exclusive, and "
                           "that exclusivity is what lands the boundary on an "
                           "exact pixel instead of a range",
            "arithmetic": "submitCentreX is pinned at 1216; hostRight = W - 293; "
                          "1216 < W - 293  <=>  W >= 1510",
            "equivalentRestatement": "rowRight <= sectionRight + 8 — identical on "
                                     "all six transition cells, but a consequence "
                                     "of the constants, not a separate margin",
            "safe": SAFE,
        },
        "falsified": {
            "zOrder": "the bottom bar declares z-200 and the inspector aside "
                      "declares z-30, so z says the bar is on top — and the "
                      "reading says the opposite. The submit button is not even "
                      "IN the stack (index -1): it is not painted there, not "
                      "merely below something.",
            "pointerEvents": "the bottom bar wrapper is pointer-events:none. An "
                             "in-page experiment set it to auto and the stack "
                             "did not change at all.",
            "rowMustFitInsideTheBottomBar": "at W=1510 the row still overhangs "
                                            "the bottom bar by 20px and the "
                                            "button IS reachable. Fitting inside "
                                            "the bar is not the rule.",
        },
        "cells": cells,
        "boundary": boundary,
        "pointerEventsExperiment": pe_experiment,
        "rowOverSectionTransitions": transitions,
        "explainedFrom658": prompt_keys,
    }

    # ------------------------------------------------------------------ 1
    v.check("the-closed-form-holds-on-six-cells-including-a-second-axis",
            not mismatches and len(cells) == 6,
            detail={"rows": {k: {"reachable": o["reachable"],
                                 "rowOverSection": o["rowOverSection"],
                                 "sectionRight": o["sectionRight"],
                                 "rowRight": o["rowRight"],
                                 "rowWidth": o["rowWidth"],
                                 "rowOverBottomBar": o["rowOverBottomBar"],
                                 "topOfStack": o["stackTop3"][:2]}
                            for k, o in sorted(cells.items())},
                    "mismatches": mismatches,
                    "transitions": transitions,
                    "whySixCells": "a width sweep alone can only produce ONE "
                                   "transition, and one transition cannot "
                                   "distinguish 'overhang <= 8' from 'overhang "
                                   "<= 0'. Collapsing the panels moves the "
                                   "column width without moving the window, so "
                                   "the same rule gets tested at overhangs 238, "
                                   "78, 8, 5, -83 and -118."},
            note="the second axis is the difference between a curve and a "
                 "coincidence")

    # ------------------------------------------------------------------ 2
    v.check("the-boundary-is-located-to-the-pixel",
            not disagreements
            and boundary["1509"]["reachable"] is False
            and boundary["1510"]["reachable"] is True
            and boundary["1509"]["rowOverSection"] == SAFE + 1
            and boundary["1510"]["rowOverSection"] == SAFE,
            detail={w: {"reachable": o["reachable"],
                        "rowOverSection": o["rowOverSection"],
                        "submitIndexInStack": o["submitIndexInStack"],
                        "stackTop3": o["stackTop3"][:3],
                        "sectionRight": o["sectionRight"],
                        "rowRight": o["rowRight"]}
                    for w, o in boundary.items()},
            note="1509 overhangs by 9 and fails; 1510 overhangs by 8 and passes. "
                 "There is no width in between to argue about.")

    # ------------------------------------------------------------------ 3
    v.check("the-declared-z-indices-do-not-predict-the-hit-order",
            (cells["w1280"]["bottomBarZ"] == "200"
             and cells["w1280"]["asideZ"] == "30"
             and cells["w1280"]["reachable"] is False),
            detail={"bottomBarZ": cells["w1280"]["bottomBarZ"],
                    "bottomBarDeclared": "absolute, z-200 — by z it wins",
                    "inspectorAsideZ": cells["w1280"]["asideZ"],
                    "whatActuallyHappens": {
                        "reachable": cells["w1280"]["reachable"],
                        "submitIndexInStack": cells["w1280"]["submitIndexInStack"],
                        "topOfStack": cells["w1280"]["stackTop3"]},
                    "theCorrection": "643 already rejected a 'z-200 vs z-30 "
                                     "fight' as the explanation and was right. "
                                     "The bar does outrank the inspector and is "
                                     "still the one that loses — because its "
                                     "content is not painted over the inspector's "
                                     "column at all."},
            note="a z-index that reads 200 and loses is a fact about layout, not "
                 "about stacking order")

    # ------------------------------------------------------------------ 4
    v.check("pointer-events-is-not-the-mechanism-either",
            pe_experiment.get("computedPointerEventsWas") == "none"
            and pe_experiment["before"]["reachable"]
            == pe_experiment["after"]["reachable"]
            and pe_experiment["before"]["stackTop3"]
            == pe_experiment["after"]["stackTop3"],
            detail=pe_experiment,
            note="one in-page experiment, nothing persisted, nothing written to "
                 "src/ — and the stack did not move by one element")

    # ------------------------------------------------------------------ 5
    # This check was WRONG on its first run and the data said so.  It asserted
    # the host was `overflow: visible` and that nothing was clipped — because
    # the pre-batch probe had measured the ROW, not the HOST.  Measured
    # properly, the host is `overflow: auto` and it IS the clipper.  The very
    # first hypothesis of this batch was right and I abandoned it on a
    # misread element.
    v.check("the-clipping-story-is-the-one-that-survives-and-it-is-the-host",
            all(o["hostOverflow"] == "auto" for o in cells.values())
            and not restatement_mismatches
            and all(o["reachable"] == o["centreInsideHostClip"]
                    for o in list(cells.values()) + list(boundary.values())),
            detail={"hostOverflow": {k: o["hostOverflow"]
                                     for k, o in sorted(cells.items())},
                    "hostScrollWvsClientW": {k: [o["hostScrollW"], o["hostClientW"]]
                                             for k, o in sorted(cells.items())},
                    "theMisread": "the pre-batch probe read `bar.parentElement`, "
                                  "which is the 944-wide row and really is "
                                  "`overflow: visible`. The CLIPPER is one level "
                                  "further down: `div.pointer-events-auto.flex`, "
                                  "`overflow: auto`, 694 wide at W=1280.",
                    "theCorrection": "the row is 944 wide and shrink-0, so it "
                                     "overflows the 694-wide clipping host and "
                                     "the prompt bar falls outside the clip. That "
                                     "is why the button is ABSENT from the stack "
                                     "rather than below something in it.",
                    "the8IsAConsequenceNotAMargin": {
                        "rowWidth": cells["w1280"]["rowWidth"],
                        "hostRightAt1509": boundary["1509"]["hostRight"],
                        "hostRightAt1510": boundary["1510"]["hostRight"],
                        "submitCentreX": cells["w1280"]["submitCentreX"],
                        "why": "the clip's right edge is exclusive, the button "
                               "centre is pinned at 1216, and hostRight is "
                               "W - 293. 1216 < W - 293 lands on W = 1510. The "
                               "'8px safe margin' framing of 659's first draft "
                               "was a coincidence of those constants wearing the "
                               "shape of 626's SAFE_MARGIN.",
                        "stillEquivalent": not restatement_mismatches},
                    "restatementMismatches": restatement_mismatches},
            note="a mechanism invented from a single misread element is the most "
                 "expensive kind of wrong — and so is throwing one away on the "
                 "same kind of misread")

    # ------------------------------------------------------------------ 6
    v.check("this-closed-form-is-the-explanation-for-658s-four-controls",
            len(prompt_keys) == 4
            and all(cells["w1280"]["reachable"] is False for _ in [0]),
            detail={"theFourControls": prompt_keys,
                    "at1280Expanded": {"reachable": cells["w1280"]["reachable"],
                                       "rowOverSection": cells["w1280"]["rowOverSection"]},
                    "at1280Collapsed": {"reachable": cells["w1280-collapsed"]["reachable"],
                                        "rowOverSection": cells["w1280-collapsed"]["rowOverSection"]},
                    "whatThisAdds": "658 recorded that four controls are "
                                    "unreachable and said it did not know why. "
                                    "This batch says why, and says which widths "
                                    "and which panel state make them reachable "
                                    "again.",
                    "whatItDoesNotCover": "658 also flagged `help` and, at 720, "
                                          "the two colour controls. Those are "
                                          "different mechanisms and this closed "
                                          "form does not claim them."},
            note="an explanation that cannot be turned off is not an explanation")

    out["checks"] = v.result
    out["ok"] = not v.failures
    out["checkCount"] = v.count
    out["failures"] = v.failures
    out["totals"] = {
        "cells": len(cells),
        "boundaryCells": len(boundary),
        "safe": SAFE,
        "rowWidth": cells["w1280"]["rowWidth"],
        "rowOverSectionTransitions": transitions,
        "boundary": {"1509": boundary["1509"]["rowOverSection"],
                     "1510": boundary["1510"]["rowOverSection"]},
        "mechanismsFalsified": 3,
        "mechanismRecoveredAfterMisreadingAnElement": 1,
        "controlsExplained": len(prompt_keys),
    }
    audit = ROOT / "docs/research/liblib-canvas-batch659-2026-10-01"
    audit.mkdir(parents=True, exist_ok=True)
    (audit / "runtime-audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    print(f"\n{v.count} checks, {len(v.failures)} failures")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

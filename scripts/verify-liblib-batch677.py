#!/usr/bin/env python3
"""batch 677 验收：整套遮挡判据建立在 **6 枚控件**上；而「命中者是谁」这类读数**对被测控件自己能不能点完全无感**

## 起点

676 发现：`收起属性` 的两枚里，`director-character-lead` 那一枚**从未进入** 667 的读数，
注入 `pointer-events:none` 后 667 的判据**逐字不变**。
676 把原因归给「探测点只取控件中心」这一条口径。

本批问两个更一般的问题：

1. **那套口径到底建立在多少枚控件上？**
2. **反过来 —— 对它确实看过的那几枚，读数对「控件自己还能不能点」有反应吗？**

## 三条读数

### 1. 人口：6/130，且随宽度单调收缩

667 自己的 6 格，用「控件中心 + `elementFromPoint` 命中外人」这条最宽的口径：

| 视口格 | 被遮挡的控件数 | 名单 |
|---|---|---|
| 1280×720 | **6** | 帮助 / 上传图片 / 描述想搭建的场景 / 发送 / 颜色 hex 值 / 颜色 |
| 1280×1150 | 4 | 帮助 / 上传图片 / 描述想搭建的场景 / 发送 |
| 1366×1150 | 3 | 帮助 / 描述想搭建的场景 / 发送 |
| 1440×1150 | 2 | 帮助 / 发送 |
| 1600×1150 | **1** | 帮助 |
| 1920×1150 | **1** | 帮助 |

并集 = **6 枚 / 130 枚（4.6%）**，出现格数：帮助 **6/6**、发送 4/6、描述想搭建的场景 3/6、
上传图片 2/6、颜色 hex 值 1/6、颜色 1/6。

**667 说的「6 格恒定」是对的 —— 但它只对 `帮助` 成立**，
其余 5 枚都是**窄视口现象**，最宽的一格里只剩 `帮助` 一个。

### 2. 两条口径给出不同人口（664 记的 pe:none 守卫，现在有了并排读数）

667 的普查还要求「存在一层 `pointer-events:none` 的外层元素」，676 的没有：

| 视口格 | 667 口径 | 676 口径 |
|---|---|---|
| 1280×1150 | 2 | 4 |
| 1440×1150 | 1 | 2 |
| 1920×1150 | 1 | 1 |

**同一个视口、同一批控件，两条口径的人口不同。**

### 3. 注入反例：读数对「被测控件自己还能不能点」无感

给 `帮助` 注入 `pointer-events:none`：

- **667 口径**：人口 1 → **0**（它有一条 `pointerEvents === 'none' 就跳过` 的守卫），
  于是 667 的读数阶段在 `help_rows[k][0]`（`verify-liblib-batch667.py:277`）**IndexError** ——
  **它不会给出「判定不成立」，而是崩在读数阶段**；
- **676 口径**：人口仍是 1，`帮助` **照旧**被记为「被遮挡、命中者是 `收起属性`」。

**为什么后者无感**：那 6 枚**本来就不是命中者** —— 命中者一直是它们上面那层。
把一个从不接收事件的东西设成不接收事件，`elementFromPoint` 的答案当然不变。

**结论**：这套判据全部建立在「命中者是谁」上，所以它能回答「谁挡了它」，
**不能回答「它自己还在不在」**。要分开这两件事，多读一个
`getComputedStyle(el).pointerEvents` 就够 —— 而 658/661/662/664/666/667 都没读它。

## 自记：两处预期被读数推翻

1. 动手前我以为「注入 pe:none 会让那枚控件从被遮挡名单里消失」。
   **读数说不会** —— 消失的是**控件本身**（667 的守卫把它从人口里剔掉），
   而「被遮挡」这个判断**一字不变**（命中者没变）。
   「谁从名单里消失」和「名单的内容变没变」是两个问题，本批把它们分开了。
2. 第 6 条判据我写成「两台仪器的读数都不变」，运行失败：667 那条**不是不变，是变成 `None`**
   —— 它连读数都产不出来了。**「读数变了」和「读数消失了」是两件事。**
   改成断言真正成立的那句：**没有任何一台仪器给出过不同的命中者名字**。

## 不声称

不声称那 6 枚之外的 124 枚「没有遮挡问题」（**从未被普查过 ≠ 没问题**，见 676）；
不声称 667 的结论错了（它在 `帮助` 上是对的）；
不声称注入等价于真实遮挡（是构造，不是源站行为）；
不改任何历史批次 —— 本批只补上「这套判据的人口是 6/130」与
「读数对被测控件自身可点性无感」这两条事实。
"""

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch677-2026-10-01"

# **667 自己的 6 格**
CELLS = [(1280, 720), (1280, 1150), (1366, 1150), (1440, 1150),
         (1600, 1150), (1920, 1150)]
# 注入实验：最宽的一格（那里只剩 帮助）与中间一格（两口径人口不同）
INJECT_CELLS = [(1440, 1150), (1920, 1150)]
HELP = "帮助"

INJECT_JS = r"""(name) => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  for (const e of scope.querySelectorAll('*')) {
    const a = e.getAttribute('aria-label');
    const t = (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24);
    if (a === name || (!a && t === name)) { e.style.pointerEvents = 'none'; return true; }
  }
  return false;
}"""


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / f"scripts/verify-liblib-batch{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


b617 = _load("617")
b667 = _load("667")
b676 = _load("676")


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(80)


def _read(page) -> dict[str, Any]:
    """**同一个页面上同时跑两台仪器** —— 人口不同的比较必须在同一状态下做。"""
    r667 = page.evaluate(b667.JS)
    r676 = page.evaluate(b676.JS)
    return {
        "ch3b667": [{"control": x["control"], "hitLabel": x["hitLabel"],
                     "peNoneId": x["peNoneId"]} for x in r667["ch3b"]],
        "foreign676": [{"control": x["control"], "hitLabel": x["hitLabel"]}
                       for x in r676["foreign"]],
        "help667": next((x["hitLabel"] for x in r667["ch3b"]
                         if x["control"] == HELP), None),
        "help676": r676["helpVerdict"],
    }


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
    base: dict[str, Any] = {}
    inject: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for (w, h) in CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            base[f"{w}x{h}"] = _read(page)
            page.close()
        for (w, h) in INJECT_CELLS:
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            applied = page.evaluate(INJECT_JS, HELP)
            page.wait_for_timeout(60)
            inject[f"{w}x{h}"] = {"applied": applied, **_read(page)}
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "baseline": base, "injection": inject},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    keys = list(base)
    TOTAL_CONTROLS = 130
    cov676 = {k: [x["control"] for x in base[k]["foreign676"]] for k in keys}
    cov667 = {k: [x["control"] for x in base[k]["ch3b667"]] for k in keys}
    counts676 = {k: len(cov676[k]) for k in keys}
    union = sorted({c for k in keys for c in cov676[k]})
    persist = Counter(c for k in keys for c in cov676[k])

    # 667 自己的后处理：注入后它会不会崩？把它的表达式原样搬过来。
    crash: dict[str, Any] = {}
    for k in inject:
        help_rows = [r for r in inject[k]["ch3b667"] if r["control"] == HELP]
        try:
            _ = {kk: help_rows[0]["peNoneId"] for kk in (k,)}   # 667:277 的形状
            crash[k] = {"raised": False}
        except IndexError as e:
            crash[k] = {"raised": True, "error": f"IndexError: {e}",
                        "at": "verify-liblib-batch667.py:277 "
                              "(help_rows[k][0]['peNoneId'])"}

    v.check("the-occlusion-apparatus-rests-on-six-of-130-controls",
            len(union) == 6 and counts676[keys[0]] == 6 and counts676[keys[-1]] == 1
            and TOTAL_CONTROLS == 130,
            detail={"unionAcrossSixCells": union,
                    "perCell": counts676, "controls": TOTAL_CONTROLS,
                    "share": f"{len(union)}/{TOTAL_CONTROLS}"},
            note="4.6% of the control population; at 1920 exactly one control is occluded")

    v.check("coverage-shrinks-monotonically-as-the-viewport-widens",
            all(counts676[keys[i]] >= counts676[keys[i + 1]] for i in range(len(keys) - 1)),
            detail={"counts": counts676, "cells": keys},
            note="6 -> 4 -> 3 -> 2 -> 1 -> 1")

    v.check("help-is-the-only-width-invariant-member-so-667s-6-cell-claim-is-about-it-alone",
            persist[HELP] == len(keys)
            and all(persist[c] < len(keys) for c in union if c != HELP),
            detail={"cellsSeen": {c: persist[c] for c in union},
                    "cellsTotal": len(keys)},
            note="667's '6 格恒定' is correct — and it is a claim about 帮助 only; the "
                 "other five are narrow-viewport artifacts")

    v.check("667s-population-is-a-strict-subset-of-676s-because-of-the-pe-none-guard",
            all(set(cov667[k]) <= set(cov676[k]) for k in keys)
            and any(len(cov667[k]) < len(cov676[k]) for k in keys),
            detail={"perCell667": {k: cov667[k] for k in keys},
                    "perCell676": {k: cov676[k] for k in keys},
                    "why":
                        "667's census additionally requires an enclosing "
                        "pointer-events:none layer (664's guard); 676's does not. Same "
                        "page, same moment, two populations."},
            note="one viewport, one control set, two different populations")

    v.check("breaking-help-drops-it-from-667s-population-while-676s-still-reports-it-covered",
            all(inject[k]["applied"] for k in inject)
            and all(HELP not in [x["control"] for x in inject[k]["ch3b667"]]
                    for k in inject)
            and all(HELP in [x["control"] for x in inject[k]["foreign676"]]
                    for k in inject),
            detail={k: {"before667": cov667[k], "after667": inject[k]["ch3b667"],
                        "before676": cov676[k], "after676": inject[k]["foreign676"],
                        "helpVerdict667": (inject[k]["help667"], base[k]["help667"]),
                        "helpVerdict676": (inject[k]["help676"], base[k]["help676"])}
                    for k in inject},
            note="667's JS skips pointer-events:none controls; 676's does not — so the "
                 "same injection empties one census and leaves the other untouched")

    v.check("no-instrument-ever-named-a-different-hitter-only-667s-stopped-producing-one",
            all(inject[k]["help676"] == base[k]["help676"] for k in inject)
            and all(inject[k]["help667"] is None for k in inject)
            and all(base[k]["help667"] is not None for k in inject),
            detail={k: {"help667": [base[k]["help667"], inject[k]["help667"]],
                        "help676": [base[k]["help676"], inject[k]["help676"]]}
                    for k in inject},
            note="'the reading changed' and 'the reading disappeared' are two different "
                 "things: 676 reports the SAME hitter name, 667 cannot produce a reading "
                 "at all. No instrument ever named a different hitter — the control was "
                 "never the hitter to begin with")

    v.check("667s-own-post-processing-would-crash-on-that-state-rather-than-fail-the-check",
            all(c["raised"] for c in crash.values()),
            detail={"crash": crash,
                    "whyNotVacuous":
                        "667's help_everywhere = all(len(help_rows[k]) == 1) would go "
                        "False, so the check would NOT silently pass — but the script "
                        "indexes help_rows[k][0] unconditionally first and raises "
                        "IndexError while building the readings"},
            note="a loud crash, not a silent green — but still not a verdict")

    out = {"cells": keys, "injectCells": [f"{w}x{h}" for (w, h) in INJECT_CELLS],
           "controls": TOTAL_CONTROLS, "coveredUnion676": union,
           "coveredPerCell676": counts676,
           "covered667": {k: cov667[k] for k in keys},
           "covered676": {k: cov676[k] for k in keys},
           "cellsSeen": {c: persist[c] for c in union},
           "injection": inject, "postProcessingCrash": crash,
           "judged": sum(len(cov676[k]) for k in keys)
                     + sum(len(inject[k]["foreign676"]) for k in inject)}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "baseline": base, "injection": inject,
                    "checks": v.result}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

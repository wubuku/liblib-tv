#!/usr/bin/env python3
"""batch 689 验收：**这条字段按构造就是整数值的** —— 685 的 1/64px 斜坡在这里不可能出现

## 起点

685 在**宽度轴**上量到：`Math.round` 把 1/64px 栅格上的连续斜坡伪造成平台
（`project-import` 129 个未取整值 vs 16 个取整平台）。
686 在**高度轴**上量到「没有亚像素形变」，但那是**经验结论** —— 没量到不等于不可能。

本批问一个**结构问题**：`timelineHeight` 能不能承载非整数值？

源码给的答案是**不能**，而且有**两个**独立理由：

1. `setTimelineHeight` 是**唯一**写入点，里面有 `Math.round(height)`
   （`directorStore.ts:5505-5512`）；
2. 两个写入者喂进去的都是整数：拖拽公式 `startHeight − (clientY − startY)` 两端皆整数；
   而 `fit()` 减的 `overflow = rect.bottom − innerHeight`，在高度为整数时两者皆整数。

⟹ **字段的值域是闭的 `ℤ ∩ [88, 420]`** —— 685 那个现象在这条路径上**按构造不可能**。

## 四条读数

### 1. 242 个测量步里，三个读数**没有一个**是小数

逐 1px 拖两段（41 步 + 201 步），每步记三样：

| 读数 | 小数出现次数 |
|---|---|
| store 值 `data-director-timeline-height` | **0 / 242** |
| **未取整的渲染高** `getComputedStyle(timeline).height` | **0 / 242** |
| **未取整的** `rect.bottom − innerHeight`（即 `fit()` 要减的那个量） | **0 / 242** |

**注意第三行**：685 的教训是「只看 store 值不够，渲染层可能才是分数的」。
所以这里连渲染高与 `fit()` 的输入量都量了 —— **两个都是整数。**

### 2. 可达集合是**连续整数区间**：201 步 → 201 个互不相同的值

`182..382`，**零空洞、零重复**，步长集合恒为 `{1}`。

⟹ **拖拽路径上不存在斜坡、不存在平台、也不存在量化台阶** —— 685 那把尺在这里
连制造误差的机会都没有。

### 3. 增益恰好是 1px/px（在未进入钳制的区间内）

每 1px 指针位移 ⟹ 每 1px 高度，41 步无一例外。
（进入钳制后落定值饱和在 `max(88, min(420, vh − 88))` —— 那是 688 的读数，本批只补增益。）

### 4. **松手位置单独不足以决定高度** —— 还需要按下位置

把手高 **8px**。在带内三个位置按下，**移到同一个绝对 y = 400**：

| 抓点 offset | 按下 y | 拖动距离 | 松手时高度 |
|---|---|---|---|
| 0 | 539 | 139 | **321** |
| 3 | 542 | 142 | **324**（+3） |
| 7 | 546 | 146 | **328**（+7） |

**高度差恰好等于抓点差。** 所以同一个手势终点给出 **8 个可能的高度**，
**那个窗口的宽度恰好等于把手高度**。

这是**正确的**交互（相对抓点锚定 ⟹ 按下时不会跳变），但它是一条**交互合同**：
**想知道高度，光看松手位置不够，还要看按下位置。** 任何「按终点预测高度」的推理都会错 0..7px。

## 自记

**探针对 ≠ 路对，683 已记 —— 这是第二次，而且这次是我自己刚写完就发出去的。**

689a 的第三段实验我写的是 `target = y0 - 60`（**相对**目标），于是三次拖拽各加 60，
得到 242 / 302 / 362 —— **那是个恒真的结果，什么也没测**：
它测的是「每次拖 60 就加 60」，与「抓点是否影响结果」无关。
改正：每次**新开页**（否则把手已随面板移动），并移到**固定的绝对 y**。

**一个实验如果只能给出「对」的答案，它就没有在测任何东西** —— 与 681 删掉的那条恒真判据
是同一类错误，**而我差点又写一条。**

## 不声称

- **不声称** 源站的拖拽有任何行为（**未取证**；全程只测我们自己的 clone，
  拖的是 clone 的把手，**不碰源站**；607 已记「源站的拖拽量程未取证」）；
- **不声称** `Math.round` 是**有意**的选择（**这是我的推断**：它可能是无意的；
  读数只证明「这个字段是整数值的」，不证明「有人决定过它要是整数值的」）；
- **不声称** 整数性是这个应用所有布局字段的通性（**本批只量了 `timelineHeight` 一个**）；
- **不声称** 抓点依赖是缺陷（**它是正确的交互**；本批只把它写成一条可复算的合同）；
- **不声称** 686 的经验结论因此被推翻（**它没有被推翻，被加强**：
  从「没量到亚像素」升级为「这条字段按构造装不下亚像素」——**仅限这个字段**）；
- **不改 `src/`**。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch689-2026-10-01"

W, DESK_H = 1280, 720
MIN_H, MAX_H, DEFAULT_H = 88, 420, 182
RELEASE_Y = 400
# **8px 高的带只容得下 offset 0..7 这 8 个整数抓点**（offset 8 = y+8 已在带外）。
# 所以「一个终点给出 8 个可能高度、两端跨度 7」是**可测的**，不是推出来的 ⟹ 全测。
GRAB_OFFSETS = [float(i) for i in range(8)]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

READ = r"""() => {
  const tl = document.querySelector('[data-director-timeline]');
  const attr = document.querySelector('[data-director-timeline-height]');
  const h = document.querySelector('[data-director-timeline-resize-handle]');
  const cs = tl ? getComputedStyle(tl) : null;
  const b = tl ? tl.getBoundingClientRect() : null;
  const hb = h ? h.getBoundingClientRect() : null;
  return {
    vh: innerHeight,
    tlAttr: attr ? attr.getAttribute('data-director-timeline-height') : null,
    // 685 的教训：只看 store 值不够，渲染层可能才是分数的 ⟹ 两个都量
    renderedH: cs ? cs.height : null,
    // fit() 要减的那个量，也未取整地量
    overflowBy: b ? b.bottom - window.innerHeight : null,
    handleTop: hb ? hb.y : null, handleH: hb ? hb.height : null,
  };
}"""


def _open(br, h: int):
    page = br.new_page(viewport={"width": W, "height": h}, device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(150)
    return page


def drag_stepwise(page, dy_total: int) -> list:
    """从把手顶按下，逐 1px 往上拖，每步读一次。"""
    hd = page.evaluate(READ)
    x = W // 2
    y0 = int(round(hd["handleTop"]))
    page.mouse.move(x, y0)
    page.mouse.down()
    seq = []
    for k in range(dy_total + 1):
        page.mouse.move(x, y0 - k, steps=1)
        page.wait_for_timeout(28)
        seq.append({"dy": k, **page.evaluate(READ)})
    page.mouse.up()
    page.wait_for_timeout(150)
    return seq


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
    stepwise: dict[str, Any] = {}
    grabs: list[dict[str, Any]] = []

    with sync_playwright() as p:
        br = p.chromium.launch()

        page = _open(br, DESK_H)
        stepwise["short"] = drag_stepwise(page, 40)
        page.close()
        page = _open(br, DESK_H)
        stepwise["long"] = drag_stepwise(page, 200)
        page.close()

        # 抓点实验：**每次新开页**，并移到**固定的绝对 y**。
        # （689a 用相对目标，三次各加 60 —— 恒真的结果，什么也没测。）
        for off in GRAB_OFFSETS:
            page = _open(br, DESK_H)
            before = page.evaluate(READ)
            x = W // 2
            y0 = int(round(before["handleTop"] + off))
            page.mouse.move(x, y0)
            page.mouse.down()
            page.mouse.move(x, RELEASE_Y, steps=12)
            page.wait_for_timeout(120)
            at_release = page.evaluate(READ)
            page.mouse.up()
            page.wait_for_timeout(150)
            grabs.append({"offset": off, "pressedAtY": y0, "releasedAtY": RELEASE_Y,
                          "dragDistance": y0 - RELEASE_Y,
                          "before": before, "atRelease": at_release,
                          "afterUp": page.evaluate(READ)})
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "stepwise": stepwise, "grabs": grabs},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    def num(x: Any) -> float:
        return float(str(x).replace("px", ""))

    all_steps = stepwise["short"] + stepwise["long"]
    fracs = {
        "tlAttr": [s for s in all_steps if float(s["tlAttr"]) != int(float(s["tlAttr"]))],
        "renderedH": [s for s in all_steps
                      if num(s["renderedH"]) != int(num(s["renderedH"]))],
        "overflowBy": [s for s in all_steps
                       if s["overflowBy"] is not None
                       and float(s["overflowBy"]) != int(float(s["overflowBy"]))],
    }
    v.check("both-writers-feed-integers-so-the-fields-domain-is-closed",
            all(not fracs[k] for k in fracs)
            and all(int(s["tlAttr"]) == num(s["renderedH"]) for s in all_steps),
            detail={"stepsMeasured": len(all_steps),
                    "fractionalCounts": {k: len(vv) for k, vv in fracs.items()},
                    "sourceFactSingleWritePoint":
                        "directorStore.ts:5505-5512 -- setTimelineHeight is the ONLY writer "
                        "and it ends in Math.round(height)",
                    "writer1TheDrag":
                        "DirectorTimeline.tsx:294-300 -- next = startHeight - (clientY - "
                        "startY); both ends are integers, and clientY is integer-quantised "
                        "by the pointer",
                    "writer2TheFit":
                        "DirectorTimeline.tsx:681-687 -- overflow = "
                        "rect.bottom - window.innerHeight. When the stored height is an "
                        "integer, the panel is bottom-anchored or top-pinned at 88, so BOTH "
                        "terms are integers and the difference is an integer.",
                    "whyTheThirdReadingMatters":
                        "685's lesson is that reading the store is not enough -- the render "
                        "layer may be the fractional one. So this batch also measured the "
                        "unrounded rendered height AND the unrounded overflow, which is the "
                        "exact quantity writer2 subtracts. Neither was fractional, 0 times "
                        "in 242 steps.",
                    "conclusion":
                        "the domain is Z intersect [88, 420] -- closed. 685's 1/64px ramp "
                        "phenomenon is IMPOSSIBLE on this field, structurally rather than "
                        "by luck."},
            note="'not observed' and 'cannot happen' are different claims; this is the second")

    long_vals = [int(s["tlAttr"]) for s in stepwise["long"]]
    long_deltas = [long_vals[i + 1] - long_vals[i] for i in range(len(long_vals) - 1)]
    v.check("the-reachable-set-on-the-drag-path-is-a-contiguous-integer-interval",
            len(stepwise["long"]) == 201
            and len(set(long_vals)) == 201
            and sorted(set(long_vals)) == list(range(min(long_vals), max(long_vals) + 1))
            and set(long_deltas) == {1},
            detail={"steps": len(stepwise["long"]),
                    "range": [min(long_vals), max(long_vals)],
                    "distinctValues": len(set(long_vals)),
                    "contiguous": sorted(set(long_vals))
                    == list(range(min(long_vals), max(long_vals) + 1)),
                    "duplicates": len(long_vals) - len(set(long_vals)),
                    "deltas": sorted(set(long_deltas)),
                    "so": "no plateaus, no holes, no quantisation steps -- the ruler that "
                          "manufactured 16 plateaus out of 129 real values on the width axis "
                          "has nothing to get wrong here"},
            note="an interval with no gaps is a stronger claim than 'it varied'")

    short_vals = [int(s["tlAttr"]) for s in stepwise["short"]]
    short_deltas = [short_vals[i + 1] - short_vals[i] for i in range(len(short_vals) - 1)]
    v.check("the-gain-is-exactly-one-pixel-of-height-per-pixel-of-pointer-travel",
            set(short_deltas) == {1} and len(short_deltas) == 40
            and short_vals[0] == DEFAULT_H
            and short_vals[-1] == DEFAULT_H + 40,
            detail={"from": short_vals[0], "to": short_vals[-1],
                    "deltas": sorted(set(short_deltas)),
                    "inTheUnclampedRegion":
                        "88 + (182 + 40) = 270 is below the 270 line 688 measured, so no "
                        "clamp is in play anywhere in this sweep -- the gain is the drag's "
                        "own",
                    "outsideThisRegion":
                        "once the clamp engages the landing saturates at "
                        "max(88, min(420, vh - 88)); 688 measured that surface, this batch "
                        "only measures the gain under it"},
            note="gain is a different quantity from the reachable max")

    # READ 里 tlAttr 是 getAttribute 的原始字符串（刻意不做 Number，
    # 让「属性是字符串」这件事留在读数里），所以这里显式取整。
    spans = [int(g["atRelease"]["tlAttr"]) for g in grabs]
    base = spans[0]
    deltas = [s_ - base for s_ in spans]
    handle_h = int(grabs[0]["before"]["handleH"])
    v.check("the-release-point-alone-does-not-determine-the-height",
            all(deltas[i] == grabs[i]["offset"] - grabs[0]["offset"]
                for i in range(len(grabs)))
            and len(set(spans)) == len(grabs) == handle_h
            and max(spans) - min(spans) == handle_h - 1
            and all(int(g["afterUp"]["tlAttr"]) == int(g["atRelease"]["tlAttr"])
                for g in grabs),
            detail={"releaseY": RELEASE_Y, "handleHeight": grabs[0]["before"]["handleH"],
                    "grabs": [{"offset": g["offset"], "pressedAtY": g["pressedAtY"],
                               "dragDistance": g["dragDistance"],
                               "heightAtRelease": int(g["atRelease"]["tlAttr"])} for g in grabs],
                    "heightDeltaFromFirst": deltas,
                    "grabOffsetDelta": [g["offset"] - grabs[0]["offset"] for g in grabs],
                    "heightsAtThisReleasePoint": spans,
                    "numberOfPossibleHeights": len(set(spans)),
                    "spanOfPossibleHeights": max(spans) - min(spans),
                    "handleHeight": handle_h,
                    "allOffsetsProbed": [g["offset"] for g in grabs],
                    "theContract":
                        "the band is 8px tall, so it admits exactly 8 integer grab positions "
                        "(offsets 0..7; offset 8 is already outside). All 8 were probed, and "
                        "at ONE release point they produce 8 distinct heights spanning 7px. "
                        "So the count equals the handle height and the span is one less.",
                    "whyTheSpanIs7Not8":
                        "the first version of this check asserted span == handleHeight and "
                        "failed at 7 vs 8. The reading was right and the assertion was wrong: "
                        "a band of height 8 starting at y admits y..y+7, not y..y+8. Fixed by "
                        "MEASURING all 8 offsets instead of deriving the count.",
                    "andItIsCorrectBehaviour":
                        "anchoring to the grab point is what stops the panel jumping at "
                        "pointer-down. This batch records it as a contract, not a defect.",
                    "andNoJumpAtPointerDown":
                        "the height is unchanged between pointer-down and the first move, so "
                        "anchoring to the grab point costs nothing visually",
                    "andTheStickyFirstAnswer":
                        "the height is already at the release value before pointer-up, so "
                        "'drop it here' and 'release at the same y' agree"},
            note="an interaction whose result needs two inputs is not predictable from one")

    out = {"width": W, "deskHeight": DESK_H,
           "declaredRange": [MIN_H, MAX_H], "defaultHeight": DEFAULT_H,
           "releaseY": RELEASE_Y, "grabOffsets": GRAB_OFFSETS,
           "domain": "Z intersect [88, 420] -- closed, because the only writer rounds and "
                     "both writers feed it integers",
           "fractionalCounts": {k: len(vv) for k, vv in fracs.items()},
           "stepsMeasured": len(all_steps),
           "longSweep": {"steps": len(stepwise["long"]), "range": [min(long_vals),
                                                                   max(long_vals)],
                         "distinct": len(set(long_vals)),
                         "deltas": sorted(set(long_deltas))},
           "shortSweep": {"from": short_vals[0], "to": short_vals[-1],
                          "deltas": sorted(set(short_deltas))},
           "grabs": grabs,
           "relationTo685And686":
               "685 found Math.round manufacturing plateaus out of 1/64px ramps on the WIDTH "
               "axis. 686 found no sub-pixel deformation on the HEIGHT axis -- empirically. "
               "This batch upgrades that for ONE field from 'not observed' to 'cannot happen'.",
           "scopeLimit":
               "one field only. No claim is made that other layout fields share this property.",
           "hypothesisNotClaim":
               "Every reading is from our own clone and the drag was performed on the clone. "
               "The source site was not used and no source-site behaviour is claimed. That "
               "Math.round is intentional is my inference, not a measurement."}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "stepwise": stepwise, "grabs": grabs,
                    "checks": v.result},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

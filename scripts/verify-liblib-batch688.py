#!/usr/bin/env python3
"""batch 688 验收：**`88..420` 这条量程是窗口的函数，而拖拽是单向规则的逃逸口**

## 起点

687 留了一条未测：「`fit()` 只挂在 `resize` 上」。**读源码发现那句话不成立**：

```tsx
useLayoutEffect(() => {
  if (timelineCollapsed) return;
  const fit = () => { ... if (overflow > 0) setTimelineHeight(timelineHeight - overflow); };
  fit();
  window.addEventListener("resize", fit);
  ...
}, [timelineHeight, timelineCollapsed]);          // ← 依赖里有 timelineHeight
```

`fit()` 会在**任何一次**对 `timelineHeight` 的写入后重跑，而拖拽写入者
（`moveHeightResize`）**不做任何溢出检查**。于是拖拽是第二条会触发单向钳制的路径。

## 四条读数

### 1. 可达上限 = `max(88, min(420, vh − 88))`，跨点在 **508**

在 10 个窗高下把把手**死命往上拖**，读落定的值：

| 窗高 | 拖后落定 | `vh − 88` | 到 420？ |
|---|---|---|---|
| 150 | **88** | 62 | 否（且 `overflowBy = 26`，MIN 也救不了） |
| 200 | 112 | 112 | 否 |
| 250 | 162 | 162 | 否 |
| 300 | 212 | 212 | 否 |
| 400 | 312 | 312 | 否 |
| 450 | 362 | 362 | 否 |
| **507** | **419** | 419 | **否（差 1px）** |
| **508** | **420** | 420 | **是** |
| 600 / 720 | 420 | 512 / 632 | 是 |

**607 记的「量程 88..420」只在窗高 ≥ 508 时才真的可达。** 声明的量程与有效的量程
在任何一个更矮的窗口上都不是一回事。

### 2. 跨点是 **508**，从两侧都量到了（507 给 419，508 给 420）

`88 + 420 = 508` —— 面板顶边被顶到 88、加上 store 的上限 420。
与 622/623 的 898/899、685 的 620 同一种形状：**声明值算出来的边界，两侧各取一个点**。

### 3. 拖拽写入者不做溢出检查，却仍然被钳住 —— 靠的是依赖列表，不是设计

`moveHeightResize` 直接 `setTimelineHeight(next)`，没有溢出判断；是 `fit()` 在
effect 重跑时把越界减掉。**所以「拖不出界」这件事是靠依赖数组偶然成立的**，
不是靠写入者自己保证。把它当设计读会读错方向：**去掉 `timelineHeight` 依赖，
拖拽立刻就能把面板拖出屏幕**。

### 4. **拖拽是逃逸口，窗口变高不是** ⟹ 单向性是**写入者**的性质，不是 store 的

| 步骤 | 窗高 | `timelineHeight` |
|---|---|---|
| 打开 | 720 | 182 |
| **拖把手死命往上** | 720 | **420** |
| 缩到 150 | 150 | **88**（`overflowBy = 26`） |
| **回到 720** | 720 | **88**（**什么都不做**） |
| **再拖一次** | 720 | **420** ⟵ 写回来了 |

store 乐意接受 420；**是 `fit()` 拒绝向上写**。所以：

- **窗口变高不能恢复**，**拖一次就能恢复**；
- 687 的 A/B/C 三条里，**A（变高时自动恢复）并不是「能不能恢复」的前提** ——
  恢复能力已经有了，只是要用户动手一次；
- 真正的问题因此收窄成：**「自动恢复」值不值得，而不是「能不能恢复」。**

### 5. 收起/展开往返**不**丢值

| 窗高 | 拖后 | 收起 | 展开 |
|---|---|---|---|
| 720 | 420 | 88（`collapsed=true`） | **420** |
| 250 | 162 | 88（`collapsed=true`） | **162** |

`timelineCollapsed` 也在 `fit()` 的依赖里，但收起期间 `fit()` 直接 return，
展开时又无越界 ⟹ **这条路不触发降档**。

## 产物状态机（687 那张表的修正版）

| 事件 | `timelineHeight` 变成 |
|---|---|
| 打开 / 重载 | **182**（`DIRECTOR_TIMELINE_DEFAULT_HEIGHT`） |
| 拖把手 | `min(420, 起点 + 拖动量)`，**随后被 `fit()` 减去越界** ⟹ 落定在 `max(88, min(420, vh − 88))` |
| 收起 / 展开 | **不变**（收起期间显示 88，但值不写） |
| 窗口 resize 且面板越界（`H < 270`） | **减掉恰好那次溢出**，下限 88 |
| 继续 resize 且仍越界 | 继续减 |
| **窗口变高** | **什么都不做** |
| 重载 | 182 |

## 自记

**这一批的价值主要在「否掉 687 留的那条未测」，而否掉它的方式是先读源码。**
687 写「`fit()` 只挂在 `resize` 上」时我只看了 `addEventListener` 那一行，
没看依赖数组 —— **一个 effect 的两条触发路径，只看了一条**。
（与 687 那条「先 grep 注释」同族：**只读一半的代码，结论就会少一半。**）

**第二次自记：在 Python 写的 JS 串里落进 Python 语法，本会话第三次。**
前两次是 685 的 `rec = {vw: …}`（JS 的裸键名）与 `{x["data"] for x in rows}`（Python 集合推导），
这次是 `(box(vp) or [0,0,0,0])[3]`。三次都是**仪器自己先报错**，才没让错误读数流到结论。

这不是「手滑」，是一个**可复现的失败模式**：探针 JS 是嵌在 Python 字符串里的，
而我写探针时手在 Python 模式里。**同一类错误的第三次出现就该上工具** ——
本批已把 JS 串抽出来用 `node --check` 过一遍再跑（685 的 README 里记过这个做法，
**当时只用在那一批，没变成惯例**）。

## 不声称

- **不声称** 源站的拖拽量程是 88..420 或任何值（607 已记「源站的拖拽量程**未取证**」，
  **本批不重复取证、不声称任何源站行为**；全程只测我们自己的 clone，拖的是 clone 的把手）；
- **不声称** 508 是缺陷（它是「声明上限 420 + 面板顶边内缩 88」的**推论**；
  630 的注释其实已经提到「魔数上限 420 在一个 360 高的窗口里根本放不下」，
  **本批只是把那条推论量化成一个精确边界**）；
- **不声称** 拖拽应当自动恢复（**产品决定**；见 §4 的收窄）；
- **不声称** 依赖数组是「偶然」的（**这是我的推断**：目前它成立，但没有测试锁住
  「去掉 `timelineHeight` 依赖会怎样」——**那条没测**）；
- **不声称** 侧栏折叠等其它布局变化不会触发越界（**本批只测了拖拽、收起/展开、窗口 resize
  三条路径**）；
- **不改 `src/`**。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch688-2026-10-01"

W = 1280
DESK_H = 720
DEFAULT_H = 182          # directorStore.ts:98
MIN_H = 88               # directorStore.ts:99
MAX_H = 420              # directorStore.ts:100
TOP_INSET = 88           # 面板顶边被顶到的位置
FULL_RANGE_H = TOP_INSET + MAX_H   # 508：声明量程完全可达所需的最小窗高
RANGE_HEIGHTS = [150, 200, 250, 300, 400, 450, 507, 508, 600, 720]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

READ = r"""() => {
  const tl = document.querySelector('[data-director-timeline]');
  const attr = document.querySelector('[data-director-timeline-height]');
  const col = document.querySelector('[data-director-timeline-collapsed]');
  const vp = document.querySelector('[data-director-viewport]');
  const box = (e) => { if (!e) return null; const b = e.getBoundingClientRect();
    return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  const b = tl ? tl.getBoundingClientRect() : null;
  const vpb = box(vp);
  return {
    vw: innerWidth, vh: innerHeight,
    tlAttr: attr ? Number(attr.getAttribute('data-director-timeline-height')) : null,
    collapsed: col ? col.getAttribute('data-director-timeline-collapsed') : null,
    overflowBy: b ? Math.round(b.bottom - window.innerHeight) : null,
    // `vpb ? vpb[3] : null` —— **不要写成 Python 的 `(vpb or [0,0,0,0])[3]`**，
    // 那在 JS 里是语法错误（见本文件末尾的自记：第三次在 JS 串里写 Python 语法）。
    viewportH: vpb ? vpb[3] : null,
  };
}"""


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(120)


SETTLE = """() => {
  const a = document.querySelector('[data-director-timeline-height]');
  return a ? a.getAttribute('data-director-timeline-height') : null;
}"""


def settle(page) -> None:
    prev = page.evaluate(SETTLE)
    for _ in range(8):
        page.wait_for_timeout(45)
        cur = page.evaluate(SETTLE)
        if cur == prev:
            return
        prev = cur


def drag_up_far(page) -> dict[str, Any]:
    """真实指针把把手死命往上拖。拖的是**我们自己的 clone**，不涉及源站。"""
    h = page.evaluate("() => { const e = document.querySelector('[data-director-timeline-resize-handle]');"
                      " if (!e) return null; const b = e.getBoundingClientRect();"
                      " return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)]; }")
    if not h:
        return {"dragFailed": True}
    page.mouse.move(h[0], h[1])
    page.mouse.down()
    page.mouse.move(h[0], max(40, h[1] - 700), steps=12)
    page.mouse.up()
    page.wait_for_timeout(220)
    return page.evaluate(READ)


def click_collapse(page) -> dict[str, Any]:
    b = page.evaluate("() => { const e = document.querySelector('[data-director-timeline-collapse]');"
                      " if (!e) return null; const r = e.getBoundingClientRect();"
                      " return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }")
    if not b:
        return {"clickFailed": True}
    page.mouse.move(b[0], b[1])
    page.mouse.click(b[0], b[1])
    page.wait_for_timeout(220)
    return page.evaluate(READ)


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
    reach: dict[str, Any] = {}
    escape: list[dict[str, Any]] = []
    collapse: list[dict[str, Any]] = []

    with sync_playwright() as p:
        br = p.chromium.launch()

        for vh in RANGE_HEIGHTS:
            page = br.new_page(viewport={"width": W, "height": vh}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            reach[str(vh)] = {"fresh": page.evaluate(READ),
                              "afterDragUpFar": drag_up_far(page)}
            page.close()

        page = br.new_page(viewport={"width": W, "height": DESK_H}, device_scale_factor=1)
        b617.open_desk(page)
        _clean(page)
        escape.append({"step": "fresh", **page.evaluate(READ)})
        escape.append({"step": "dragUpFar", **drag_up_far(page)})
        for vh in (150, DESK_H):
            page.set_viewport_size({"width": W, "height": vh})
            settle(page)
            _clean(page)
            escape.append({"step": f"to{vh}", **page.evaluate(READ)})
        escape.append({"step": "dragUpFarAgain", **drag_up_far(page)})
        page.close()

        for vh in (DESK_H, 250):
            page = br.new_page(viewport={"width": W, "height": vh}, device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            seq = [{"step": "fresh", **page.evaluate(READ)},
                   {"step": "dragUpFar", **drag_up_far(page)},
                   {"step": "collapse", **click_collapse(page)},
                   {"step": "expand", **click_collapse(page)}]
            collapse.append({"vh": vh, "seq": seq})
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "reachableMax": reach,
                    "escape": escape, "collapse": collapse},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    def pred(h: int) -> int:
        return max(MIN_H, min(MAX_H, h - TOP_INSET))

    def es(step: str) -> dict[str, Any]:
        return next(s for s in escape if s["step"] == step)

    landed = {h: reach[str(h)]["afterDragUpFar"]["tlAttr"] for h in RANGE_HEIGHTS}
    v.check("the-reachable-max-is-clamp(viewportHeightMinus88,88,420)-not-the-declared-range",
            FULL_RANGE_H == 508
            and all(landed[h] == pred(h) for h in RANGE_HEIGHTS)
            and all(landed[h] == MAX_H for h in RANGE_HEIGHTS if h >= FULL_RANGE_H)
            and all(landed[h] < MAX_H for h in RANGE_HEIGHTS if h < FULL_RANGE_H),
            detail={"rule": "reachableMax = max(88, min(420, viewportHeight - 88))",
                    "landedByDraggingFarUp": landed,
                    "predicted": {str(h): pred(h) for h in RANGE_HEIGHTS},
                    "fullRangeOnlyFromHeight": FULL_RANGE_H,
                    "why88Plus420": "the panel's top is pinned at 88, so a height of 420 only "
                                    "fits when 88 + 420 <= H",
                    "theDeclaredVsTheEffective":
                        "607 recorded the range as 88..420 and noted the source range is "
                        "unmeasured. On any window shorter than 508 the EFFECTIVE range is "
                        "narrower than the declared one, and nothing in the UI says so.",
                    "at150": {"landed": landed[150],
                              "overflowBy": reach["150"]["afterDragUpFar"]["overflowBy"],
                              "note": "below 176 the store MIN wins and the panel still "
                                      "overflows -- 687 re-measured that, and dragging "
                                      "cannot fix it either"}},
            note="the declared range and the reachable range are different quantities")

    v.check("the-crossing-is-508-and-is-measured-from-both-sides",
            landed[507] == 419 and landed[508] == 420
            and reach["507"]["afterDragUpFar"]["overflowBy"] == 0
            and landed[507] == pred(507),
            detail={"at507": {"landed": landed[507], "expected": pred(507),
                              "vhMinus88": 507 - TOP_INSET},
                    "at508": {"landed": landed[508], "expected": pred(508),
                              "vhMinus88": 508 - TOP_INSET},
                    "mechanism": "the drag writes min(420, start + distance); at 507 that is "
                                 "420, then fit() subtracts the 1px overflow (88 + 420 - 507 = "
                                 "1) and lands on 419. At 508 the overflow is 0 and 420 "
                                 "stands.",
                    "sameShapeAs": "622/623's 898/899 and 685's 620 -- a declared number "
                                   "plus a layout constant, sampled on both sides"},
            note="a boundary derived from a constant deserves a pixel on each side")

    v.check("the-drag-writer-has-no-overflow-check-and-is-clamped-only-by-the-dependency-array",
            landed[400] == pred(400) and landed[400] < MAX_H,
            detail={"dragWriter": "DirectorTimeline.tsx:294-300 -- moveHeightResize calls "
                                  "setTimelineHeight(drag.startHeight - (clientY - startY)) "
                                  "with NO overflow test at all",
                    "whoStopsIt": "the useLayoutEffect that wraps fit(), whose dependency "
                                  "array includes timelineHeight, so it re-runs after the "
                                  "drag's write and subtracts the overflow",
                    "consequence":
                        "the panel cannot be dragged off-screen today, but that is a property "
                        "of the DEPENDENCY LIST, not of the writer. Drop timelineHeight from "
                        "the deps and the drag would put the panel off-screen immediately.",
                    "status": "this is my inference about the arrangement, not a measurement "
                              "of what happens if the dep is removed -- that was NOT tested",
                    "whyItMatters": "reading this as a design guarantee points the fix in the "
                                    "wrong direction; reading it as a dependency-list accident "
                                    "points it at the right one"},
            note="a property that holds by accident should not be documented as a guarantee")

    v.check("a-drag-restores-the-height-while-growing-the-window-does-not",
            es("fresh")["tlAttr"] == DEFAULT_H
            and es("dragUpFar")["tlAttr"] == MAX_H
            and es("to150")["tlAttr"] == MIN_H
            and es("to150")["overflowBy"] == TOP_INSET + MIN_H - 150
            and es("to720")["tlAttr"] == MIN_H
            and es("dragUpFarAgain")["tlAttr"] == MAX_H,
            detail={"sequence": {s["step"]: {"vh": s["vh"], "tlAttr": s["tlAttr"],
                                             "overflowBy": s["overflowBy"],
                                             "viewportH": s["viewportH"]}
                                 for s in escape},
                    "theContrast": "going back up to 720 changes nothing; ONE DRAG writes 420 "
                                   "straight back",
                    "whatThatProves": "the store accepts 420 readily. It is fit() that refuses "
                                      "to write upward. So the one-way property belongs to "
                                      "ONE WRITER, not to the store.",
                    "narrows687sProductQuestion":
                        "687 offered A (auto-restore on grow) / B (status quo) / C (remember "
                        "the pre-clamp value). This measurement shows recoverability already "
                        "exists via a drag, so A is not a precondition for recovery -- the "
                        "question narrows to whether one drag is acceptable UX, i.e. whether "
                        "auto-restore is worth the extra state bit.",
                    "stillAProductDecision": "this batch does not choose"},
            note="the one-way rule is a property of a writer, not of the data")

    v.check("collapse-and-expand-preserve-the-height",
            all(leg["seq"][1]["tlAttr"] == leg["seq"][3]["tlAttr"]
                and leg["seq"][2]["tlAttr"] == MIN_H
                and leg["seq"][2]["collapsed"] == "true"
                and leg["seq"][3]["collapsed"] == "false"
                for leg in collapse),
            detail={"at720": [{"step": s["step"], "tlAttr": s["tlAttr"],
                               "collapsed": s["collapsed"]} for s in collapse[0]["seq"]],
                    "at250": [{"step": s["step"], "tlAttr": s["tlAttr"],
                               "collapsed": s["collapsed"]} for s in collapse[1]["seq"]],
                    "why": "timelineCollapsed IS a dependency of the fit() effect, but fit() "
                           "returns early while collapsed, and on expand there is no overflow "
                           "-- so this path never demotes the value",
                    "andTheDisplayedValue": "while collapsed the attribute reads 88, which is "
                                            "687's '88 cannot tell you which state you are "
                                            "in' all over again: collapsed shows 88 and the "
                                            "clamped store value also reads 88"},
            note="being a dependency is not the same as being a writer")

    out = {"width": W, "deskHeight": DESK_H,
           "declaredRange": [MIN_H, MAX_H], "defaultHeight": DEFAULT_H,
           "topInset": TOP_INSET, "fullRangeOnlyFromHeight": FULL_RANGE_H,
           "rangeHeights": RANGE_HEIGHTS,
           "reachableMaxRule": "max(88, min(420, viewportHeight - 88))",
           "landedByDraggingFarUp": landed, "escape": escape, "collapse": collapse,
           "stateMachine": {
               "openOrReload": DEFAULT_H,
               "drag": "min(420, start + distance), then fit() subtracts the overflow, so it "
                       "lands at max(88, min(420, H - 88))",
               "collapseOrExpand": "unchanged",
               "resizeWithOverflow(H<270)": "minus exactly that overflow, floor 88",
               "windowGrows": "nothing",
               "reload": "back to the DEFAULT"},
           "openProductQuestion": {
               "question": "should a transient window shrink permanently demote a "
                           "user-chosen timeline height, given that one drag already restores "
                           "it and a reload does not restore the user's value at all?",
               "options": {
                   "A": "auto-restore on grow -- costs 630's 'the default 182 stays identical "
                        "pixel for pixel'",
                   "B": "status quo -- recoverable by one drag, and the user gets no signal "
                        "that anything changed",
                   "C": "remember the pre-clamp value and auto-restore only when the user "
                        "never dragged -- keeps 630's goal, costs one state bit"},
               "notTakenHere": "this batch changes no src/ file",
               "newInformationSince687":
                   "recoverability already exists via the drag, so A is not needed for "
                   "recovery. The real question is whether the recovery should need the user."},
           "hypothesisNotClaim":
               "Every reading is from our own clone; the handle drag and the collapse click "
               "were performed on the clone. The source site was not used and no source-site "
               "behaviour is claimed anywhere in this batch."}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "reachableMax": reach, "escape": escape,
                    "collapse": collapse, "checks": v.result},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

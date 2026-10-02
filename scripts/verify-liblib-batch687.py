#!/usr/bin/env python3
"""batch 687 验收：**630 那条「只减不增」的自动钳制，往返是有损的，而且损的是用户值**

## 起点

686 读到时间轴高度 store 值「被夹到 88 之后再也不涨回来」，本以为是缺陷。
读源码发现**不是**：630 的 `fit()` 明确只做减法，注释里写死了意图：

> 越界多少上移多少，**不越界一个像素不动**（不越界时根本不调 `setTimelineHeight`）
> —— 默认 182 逐像素不变。

所以「粘住」是**有意设计**。**630 从未覆盖的是往返**：窗口变矮（触发钳制）之后
再变高，值回不回来；以及更尖锐的一版 —— **用户自己拖出来的高度会不会被吃掉**。

## 五条读数

### 1. 自动钳制在 **H < 270** 介入，而 store 的 MIN 在 **H < 176** —— **两个阈值差 94px**

630 只记了后者（「窗口矮于 88 + MIN(88) = 176」）。前者是 630 自己的代码里
「面板会不会越界」的那条线：`88 + 182 = 270`。

| 往返 | 触发钳制？ | 读数 |
|---|---|---|
| 720 → **300** → 720 | **否**（300 > 270） | 182 → **182** → 182，**一点没变** |
| 720 → **200** → 720 | 是 | 182 → **112** → 112 |
| 720 → **150** → 720 | 是，且撞 MIN | 182 → **88** → 88（`overflowBy = 26`） |

### 2. 往返的损失**恰好等于触发它的那次溢出**

`fit()` 是 `setTimelineHeight(timelineHeight - overflow)`，所以：
`720→200` 的溢出是 `270 − 200 = 70`，`182 − 70 = 112` ✓；
`720→150` 的溢出是 `270 − 150 = 120`，`182 − 120 = 62` ⟹ **被 store 的 MIN 抬回 88**。

**而 150 那一步 `overflowBy = 26`** —— 独立复核了 630 记的「面板仍会越界」。

### 3. 损失**与 MIN 无关**：`720→200` 那条腿一次也没读到 88

所以「粘性」不是 MIN 的性质，是「只减不增」的性质。**只要窗口曾低于 270，
高度就永久降一档。**

### 4. 往返不是纯粹的损失，是一次**静默重分配**

| 高度值 | 3D 视口高 | 面板越界 | 面板下方空隙 |
|---|---|---|---|
| 182（默认） | 450 | 0 | 0 |
| 112（往返后） | **520** | **0** | **0** |

省下的 70px **全部给了 3D 画布**（450 → 520），而且
**越界 0、空隙 0 —— 界面看不出任何异常**。这就是它一直没被看见的原因：
损失不长得像缺陷，它长得像「画布变大了」。

### 5. 最尖锐的一版：**用户自己拖出来的 320，被一次缩窗改成 112**

| 步骤 | `timelineHeight` | 3D 视口高 |
|---|---|---|
| 打开（1280×720） | 182 | 450 |
| **拖把手 +138** | **320**（用户的偏好） | 312 |
| 缩到 1280×200 | **112** | 0 |
| **回到 1280×720** | **112**（不是 320，也不是 182） | 520 |
| 再拖 +70 | 182 | 450 |

**缩窗之后那个值是窗口高的函数（112 = 200 − 88），与用户的 320 无关。**

## 状态机（读完源码 + 五条读数后的完整描述）

| 事件 | `timelineHeight` 变成 |
|---|---|
| 打开 / **重载** | **182**（`DIRECTOR_TIMELINE_DEFAULT_HEIGHT`） |
| 拖把手 | 拖出来的值（88..420） |
| 窗口 resize 且面板会越界（`H < 270`） | **减掉恰好那次溢出**，下限 88 |
| 继续 resize 且仍越界 | 继续减 |
| **窗口变高** | **什么都不做**（不恢复） |
| **重载** | **182** —— 不是被钳后的值，**也不是用户的 320** |

**所以两条恢复路都毁掉用户偏好**：手动拖是从**被钳后的值**起步，不是从用户的值；
重载回到**默认值**，也不是用户的值。**用户的时间轴高度不是一份耐久偏好。**

## 要你拍板的那一条（本批不擅自改 `src/`）

630 的目标「默认 182 逐像素不变」**达成了**；但同一条「只减不增」规则
**让用户值被一次瞬时缩窗静默销毁**。这两条**不能同时满足**：

- **A「变高时自动恢复」** ⟹ 630 想保护的那个 182 会被自动改回去（若用户没拖过，
  那「逐像素不变」就不成立了）；
- **B「永不自动恢复」**（现状）⟹ 用户得靠手动拖或重载，而**两条都拿不回自己的值**；
- **C「记住钳制前的值，只在用户没拖过时自动恢复」** ⟹ 保住 630 的目标，
  但要引入「这个值是用户的还是自动的」这一个状态位。

**这与 628/630 对「最小视口高」的处置是同一条纪律**：视口能不能被拖到多矮
「是产品决定，不是能从几何推出的」。本批只把冲突量出来，不替它选。

## 自记：我又一次先编了故事

686 我把「粘住」当成**发现**写进 README，措辞是「store 只往下钳，不往上写」——
听起来像个缺陷。**读源码发现 630 的注释早就写明了这是意图**，而且连 176 那条边界都记了。

**这是本会话第二次栽在同一个地方**（第一次是 686 把 `timelineCollapsed ? 88 : …`
的值读成了标志）：**源码里有一行注释时，读数会显得「已被解释过」，于是不再被检查。**
正确顺序是**先 grep 注释，再决定这是发现还是复核**。
686 那条读数仍然成立（它从规则独立推出了 176，与 630 一致），但它的**框架**（「发现」）
是我加上去的，不该加。

## 不声称

- **不声称** 源站在往返后有任何行为（**未取证**；全程只测我们自己的 clone，
  拖把手也是拖 clone 的控件，**不碰源站**）；
- **不声称** 270 这条线是 630 遗漏的**缺陷**（它是 630 那句代码的**推论**，
  630 的注释谈的是 MIN 那条；本批只是把两条线分开量）；
- **不声称** 「自动恢复」是正确修法（**产品决定**；A/B/C 三条各有代价）；
- **不声称** 窗口 resize 是唯一的越界来源（`fit()` 只挂在 `resize` 上，
  但没测别的路径，例如侧栏折叠）；
- **不声称** 182 是源站实测以外的**应有行为**（`DIRECTOR_TIMELINE_DEFAULT_HEIGHT = 182`
  是 clone 的常量；613/596 记过 182 的源站出处，**本批不重复取证**）。
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch687-2026-10-01"

W = 1280
DESK_H = 720
DEFAULT_H = 182          # directorStore.ts:98 DIRECTOR_TIMELINE_DEFAULT_HEIGHT
MIN_H = 88               # directorStore.ts:99
TOP_INSET = 88           # 面板顶边被顶到的位置
ENGAGE_H = TOP_INSET + DEFAULT_H   # 270：低于它面板才会越界
MIN_BITES_H = TOP_INSET + MIN_H    # 176：低于它 store 的 MIN 才起作用

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

READ = r"""() => {
  const tl = document.querySelector('[data-director-timeline]');
  const attr = document.querySelector('[data-director-timeline-height]');
  const handle = document.querySelector('[data-director-timeline-resize-handle]');
  const vp = document.querySelector('[data-director-viewport]');
  const r = (e) => { if (!e) return null; const b = e.getBoundingClientRect();
    return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  const b = tl ? tl.getBoundingClientRect() : null;
  return {
    vw: innerWidth, vh: innerHeight,
    tlAttr: attr ? Number(attr.getAttribute('data-director-timeline-height')) : null,
    overflowBy: b ? Math.round(b.bottom - window.innerHeight) : null,
    gapBelow: b ? Math.round(window.innerHeight - b.bottom) : null,
    timelineBox: r(tl), handle: r(handle), viewport: r(vp),
    viewportH: r(vp) ? r(vp)[3] : null,
  };
}"""

SETTLE = """() => {
  const a = document.querySelector('[data-director-timeline-height]');
  return a ? a.getAttribute('data-director-timeline-height') : null;
}"""


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(120)


def settle(page) -> None:
    prev = page.evaluate(SETTLE)
    for _ in range(8):
        page.wait_for_timeout(45)
        cur = page.evaluate(SETTLE)
        if cur == prev:
            return
        prev = cur


def drag_up(page, dy: int) -> dict[str, Any]:
    """真实指针拖拽 —— 拖的是**我们自己的 clone** 的把手，不涉及源站。"""
    h = page.evaluate("() => { const e = document.querySelector('[data-director-timeline-resize-handle]');"
                      " if (!e) return null; const b = e.getBoundingClientRect();"
                      " return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)]; }")
    if not h:
        return {"dragFailed": True}
    page.mouse.move(h[0], h[1])
    page.mouse.down()
    page.mouse.move(h[0], max(50, h[1] - dy), steps=10)
    page.mouse.up()
    page.wait_for_timeout(180)
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
    legs: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        for leg, shrink in (("noEngage300", 300), ("engageNoMin200", 200),
                            ("engageHitsMin150", 150)):
            page = br.new_page(viewport={"width": W, "height": DESK_H},
                               device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            steps = [{"name": "fresh", **page.evaluate(READ)}]
            for h in (shrink, DESK_H):
                page.set_viewport_size({"width": W, "height": h})
                settle(page)
                _clean(page)
                steps.append({"name": f"to{h}", **page.evaluate(READ)})
            legs[leg] = {"shrinkTo": shrink, "steps": steps,
                         "afterDragUp120": drag_up(page, 120)}
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(600)
            b617.open_desk(page)
            _clean(page)
            legs[leg]["afterReload"] = page.evaluate(READ)
            page.close()

        # ---- 腿 4：用户自己拖出来的偏好会不会被吃掉 ----
        page = br.new_page(viewport={"width": W, "height": DESK_H}, device_scale_factor=1)
        b617.open_desk(page)
        _clean(page)
        pref = [{"name": "fresh", **page.evaluate(READ)},
                {"name": "dragUp138", **drag_up(page, 138)}]
        for h in (200, DESK_H):
            page.set_viewport_size({"width": W, "height": h})
            settle(page)
            _clean(page)
            pref.append({"name": f"to{h}", **page.evaluate(READ)})
        pref.append({"name": "dragUp70", **drag_up(page, 70)})
        legs["userPreference"] = {"shrinkTo": 200, "steps": pref}
        page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "legs": legs},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    def at(leg: str, name: str) -> dict[str, Any]:
        return next(s for s in legs[leg]["steps"] if s["name"] == name)

    v.check("the-autofit-engages-below-270-while-the-store-min-bites-below-176",
            ENGAGE_H == 270 and MIN_BITES_H == 176 and ENGAGE_H - MIN_BITES_H == 94
            and at("noEngage300", "fresh")["tlAttr"] == DEFAULT_H
            and at("noEngage300", "to300")["tlAttr"] == DEFAULT_H
            and at("noEngage300", "to720")["tlAttr"] == DEFAULT_H
            and at("engageNoMin200", "to200")["tlAttr"] == 200 - TOP_INSET
            and at("engageHitsMin150", "to150")["tlAttr"] == MIN_H,
            detail={"engageThreshold": ENGAGE_H, "minBitesThreshold": MIN_BITES_H,
                    "gapBetweenThem": ENGAGE_H - MIN_BITES_H,
                    "why270": "the panel's top is pinned at 88 and its height is 182, so it "
                              "only overflows when 88 + 182 > H",
                    "why176": "the store MIN is 88, so it can only bind when 88 + 88 > H",
                    "readings": {leg: {s["name"]: s["tlAttr"] for s in legs[leg]["steps"]}
                                 for leg in legs},
                    "what630Recorded": "630 recorded only the 176 line ('below 88 + MIN(88) "
                                       "= 176'). The 270 line is the same code's own "
                                       "consequence and is what decides whether the fit runs "
                                       "at all."},
            note="two thresholds 94px apart; measuring only the one in the comment misses "
                 "the one that decides whether anything happens")

    v.check("the-round-trip-loss-equals-exactly-the-overflow-that-triggered-it",
            at("engageNoMin200", "to200")["tlAttr"]
            == DEFAULT_H - (ENGAGE_H - 200)
            and at("engageNoMin200", "to720")["tlAttr"] == at("engageNoMin200", "to200")["tlAttr"]
            and at("engageHitsMin150", "to150")["overflowBy"] == TOP_INSET + MIN_H - 150
            and at("engageHitsMin150", "to150")["tlAttr"] == MIN_H,
            detail={"fitCode": "setTimelineHeight(timelineHeight - overflow)",
                    "noMinLeg": {"overflowAt200": ENGAGE_H - 200,
                                 "valueAt200": at("engageNoMin200", "to200")["tlAttr"],
                                 "valueBackAt720": at("engageNoMin200", "to720")["tlAttr"]},
                    "minLeg": {"overflowAt150": ENGAGE_H + MIN_H - 150,
                               "rawSubtractionWouldBe": DEFAULT_H - (ENGAGE_H - 150),
                               "valueActuallyRead": at("engageHitsMin150", "to150")["tlAttr"],
                               "overflowByStillPositive":
                                   at("engageHitsMin150", "to150")["overflowBy"],
                               "independentRecheck":
                                   "630 recorded 'the panel still overflows' below 176. "
                                   "Measured overflowBy at H=150 is exactly 26, and "
                                   "150 < 176, so the store MIN genuinely cannot save it."}},
            note="the loss is not a side effect, it IS the clamp's arithmetic")

    v.check("the-loss-does-not-require-hitting-the-store-minimum",
            at("engageNoMin200", "to200")["tlAttr"] > MIN_H
            and at("engageNoMin200", "to720")["tlAttr"] > MIN_H
            and min(s["tlAttr"] for s in legs["engageNoMin200"]["steps"]) > MIN_H
            and at("engageNoMin200", "to720")["tlAttr"] < DEFAULT_H,
            detail={"valuesSeenInThatLeg":
                    [s["tlAttr"] for s in legs["engageNoMin200"]["steps"]],
                    "neverTouchedTheMin": True,
                    "stillLost": DEFAULT_H - at("engageNoMin200", "to720")["tlAttr"],
                    "conclusion":
                        "so stickiness is a property of the ONE-WAY rule, not of the store "
                        "minimum. Any window below 270 permanently demotes the height, "
                        "however briefly it was visited."},
            note="attributing the behaviour to the MIN would have been a plausible wrong "
                 "explanation")

    v.check("growing-the-window-back-never-restores-the-height",
            all(at(leg, f"to{DESK_H}")["tlAttr"] == at(leg, f"to{legs[leg]['shrinkTo']}")["tlAttr"]
                and at(leg, f"to{DESK_H}")["tlAttr"] != DEFAULT_H
                for leg in ("engageNoMin200", "engageHitsMin150")),
            detail={"backAt720": {leg: at(leg, f"to{DESK_H}")["tlAttr"]
                                  for leg in ("engageNoMin200", "engageHitsMin150")},
                    "default": DEFAULT_H,
                    "sourceFact": "DirectorTimeline.tsx:686 -- "
                                  "if (overflow > 0) setTimelineHeight(timelineHeight - "
                                  "overflow). There is no upward branch, and the comment "
                                  "states the intent: 'not one pixel moves when it does not "
                                  "overflow -- the default 182 stays identical pixel for "
                                  "pixel'.",
                    "soThisIsByDesign": "630's goal is met. What 630 never covered is the "
                                        "round trip."},
            note="the one-way rule is the intent, not an oversight")

    v.check("after-the-round-trip-nothing-looks-broken-because-the-loss-became-canvas",
            at("engageNoMin200", "to720")["overflowBy"] == 0
            and at("engageNoMin200", "to720")["gapBelow"] == 0
            and at("engageNoMin200", "to720")["tlAttr"] == 112
            and at("engageNoMin200", "to720")["viewportH"]
            == at("engageNoMin200", "fresh")["viewportH"] + 70,
            detail={"afterRoundTrip": {k: at("engageNoMin200", "to720")[k]
                                       for k in ("tlAttr", "overflowBy", "gapBelow",
                                                 "viewportH")},
                    "before": {k: at("engageNoMin200", "fresh")[k]
                               for k in ("tlAttr", "overflowBy", "gapBelow", "viewportH")},
                    "theReallocation": "the 70px the timeline lost went to the 3D canvas "
                                       "(450 -> 520), and the panel neither overflows nor "
                                       "leaves a gap",
                    "whyItWentUnnoticed": "a defect that looks like 'the canvas got bigger' "
                                          "does not get reported"},
            note="a loss that improves something else is the hardest kind to notice")

    v.check("a-user-set-height-is-destroyed-by-one-window-shrink",
            at("userPreference", "dragUp138")["tlAttr"] == 320
            and at("userPreference", "to200")["tlAttr"] == 200 - TOP_INSET
            and at("userPreference", "to720")["tlAttr"] == 200 - TOP_INSET,
            detail={"sequence": {s["name"]: {"tlAttr": s["tlAttr"],
                                            "viewportH": s["viewportH"]}
                                 for s in legs["userPreference"]["steps"]},
                    "theReading": "after one shrink the value is a function of the WINDOW "
                                  "height (112 = 200 - 88) and has nothing to do with the "
                                  "user's 320",
                    "userSetValue": 320,
                    "valueAfterRoundTrip": at("userPreference", "to720")["tlAttr"],
                    "thisIsTheSharpestForm": "686 read the clamp as a store artefact. This "
                                             "leg shows what it costs a user: not the "
                                             "default, which 630 deliberately protects, but "
                                             "a value the user chose."},
            note="630 protects the default; nothing protects the user's choice")

    v.check("both-recovery-routes-destroy-the-user-preference-too",
            legs["engageNoMin200"]["afterReload"]["tlAttr"] == DEFAULT_H
            and legs["engageHitsMin150"]["afterReload"]["tlAttr"] == DEFAULT_H
            and legs["engageNoMin200"]["afterDragUp120"]["tlAttr"]
            == at("engageNoMin200", "to720")["tlAttr"] + 120
            and at("userPreference", "dragUp70")["tlAttr"]
            == at("userPreference", "to720")["tlAttr"] + 70,
            detail={"reloadGives": {leg: legs[leg]["afterReload"]["tlAttr"]
                                    for leg in ("engageNoMin200", "engageHitsMin150")},
                    "dragStartsFrom": {leg: at(leg, f"to{DESK_H}")["tlAttr"]
                                       for leg in ("engageNoMin200", "engageHitsMin150")},
                    "dragUp120Gives": legs["engageNoMin200"]["afterDragUp120"]["tlAttr"],
                    "theUserPreferenceLeg": {
                        "afterReloadWouldBe": DEFAULT_H,
                        "userWanted": at("userPreference", "dragUp138")["tlAttr"],
                        "andEvenTheDragStartsFrom":
                            at("userPreference", "to720")["tlAttr"],
                        "note": "the final dragUp70 lands on 182 purely by arithmetic "
                                "(112 + 70). It is not a restore."},
                    "stateMachine": {
                        "openOrReload": DEFAULT_H,
                        "drag": "the dragged value, 88..420",
                        "resizeWithOverflow(H<270)": "minus exactly that overflow, floor 88",
                        "windowGrows": "nothing",
                        "reload": "back to the DEFAULT, not the clamped value and not the "
                                  "user's value"},
                    "conclusion": "the timeline height is not a durable preference: it "
                                  "survives neither a window shrink nor a reload",
                    "sourceFact": "timelineHeight is not in the persistence schema (599's "
                                  "conclusion: view state is deliberately absent), so a "
                                  "reload always yields DIRECTOR_TIMELINE_DEFAULT_HEIGHT"},
            note="a value that cannot survive a resize is not a preference, it is a cache")

    out = {"width": W, "deskHeight": DESK_H, "defaultHeight": DEFAULT_H, "minHeight": MIN_H,
           "engageThreshold": ENGAGE_H, "minBitesThreshold": MIN_BITES_H,
           "legs": legs,
           "openProductQuestion": {
               "conflict": "630's goal 'the default 182 stays identical pixel for pixel' is "
                           "met, but the same one-way rule lets a transient window shrink "
                           "silently destroy a value the USER chose.",
               "optionA": "restore automatically when the window grows -- then 630's "
                          "protection is undone (if the user never dragged, 182 would be "
                          "written back, so 'pixel for pixel' no longer holds)",
               "optionB": "keep never-restoring (status quo) -- the user must drag, and both "
                          "routes lose their value",
               "optionC": "remember the pre-clamp value and only auto-restore when the user "
                          "never dragged -- keeps 630's goal, costs one extra state bit "
                          "('is this value the user's or the auto-fit's?')",
               "whyItIsAProductDecision":
                   "same discipline as 628/630 on the minimum viewport height: what the "
                   "window may be dragged to is not derivable from geometry",
               "notTakenHere": "this batch changes no src/ file"},
           "hypothesisNotClaim":
               "Every reading is from our own clone. The source site was not used and no "
               "source-site behaviour is claimed. The handle drag was performed on the "
               "clone, not on the source site."}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "legs": legs, "checks": v.result},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

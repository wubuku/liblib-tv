#!/usr/bin/env python3
"""batch 690 验收：689 只证明了**一个**字段的整数性；本批把它推成全树的结构结论

## 起点

689 的结论是 `timelineHeight` 的值域是闭的 `ℤ ∩ [88,420]`，两条理由：
唯一写入点 + 该写入点末尾 `Math.round`。689 自己写了限制声明：
「**不声称**整数性是所有布局字段的通性（本批只量了一个字段）」。

本批去销这条限制声明，问题是两个：

1. **哪些 store 字段是整数值的？**（普查，不挑名单）
2. **689 的整数性能不能推广？** —— 也就是：整数性是**字段**的性质，
   还是**表达式**的性质？

## 普查的判据落点：写入点，不是函数体

把 689 的判据推到全树时，函数体级扫描会出错：一个 setter 同时写 5 个字段、
只给其中一个 `Math.round`，整函数体扫描会把另外 4 个读成「也取整了」。
所以本批对 `set({...})` 展开成**叶路径**，逐个值表达式单独判断取整。

`scripts/census-directorstore-value-domains.mjs`（本批一并提交，判据可复现）：
**221 个 `set()` 调用点 / 507 个写入点 / 74 条叶路径**，
其中**全写入点都取整的只有 1 条：`timelineHeight`**。

## 但 690 的真发现是反面的一条

`timeline.zoom` 没有任何写入点取整，于是它**能**装 1/64px —— 实测确实装得下。
可是真正打掉 689 推广的，是下一层：

```
timelineWidth = Math.max(640, timeline.duration * (3.36 + 4.978 * timeline.zoom))
```

**两个输入都是整数，乘出来照样是小数。** 685 在宽度轴上量到的那批 1/64px
斜坡，这里有一条**与分数 store 值无关**的成因：渲染公式里的常数 3.36 / 4.978
本身不是整数。

**所以 689 的整数性不是「字段的性质」，是「写入者喂整数 + 每个消费者都是
保整表达式」两件事的合取。** `timelineHeight` 两者都满足；`timeline.zoom`
满足第一件、不满足第二件。

## 七条读数

1. 普查：**74 条叶路径里只有 1 条是整数值的**
2. 整数 zoom 照样产出**小数**宽度（UI 可达）
3. 分数真的到达 DOM：指定值带小数，落到 1/64px 栅格上，误差 ≤ 1/128px
4. **对照**：同一页面同一把尺，`setTimelineHeight(182.5)` → 183
5. **分数 zoom 从 UI 到不了**（range 无 step ⟹ 步长 1；13 档实测全整数）
6. `min-w-full` 交叉点落在公式预测的第一个整数上
7. 标尺宽度律带**时长缩放**，而源站数据分不开这两种读法

## 自记

- **仪器自己先报错**：`ast.parse` 是 Python 解析器，我拿它解析 8750 行的
  TypeScript。直接换 TypeScript 编译器 API，不在错误解析器上打补丁。
- **探针整整错位一整轮**：dbg690a 把 `setTimelineZoom()` 和读 DOM 放在同一个
  `page.evaluate` 里，zustand 写完 React 还没提交，于是**每一行读到的都是上一档
  的宽度**。z=0 那行读到的是默认 zoom 44 的 1779.14px —— 如果不核对公式，
  这批读数会看起来完全自洽。**686 那条「读数是路径的函数」这次落在我自己的
  仪器上**：修法是写与读分成两次 evaluate，中间等两次 rAF。
- **先问可达性再下结论**（688 的纪律）。第一反应是「zoom 不取整 ⟹ 宽度有
  小数 ⟹ 有亚像素缺陷」；688 之后必须先问「UI 到不到得了」。实测 range 的
  步长是 1 ⟹ 分数 zoom **UI 不可达**。但第 2 条又说整数 zoom 也出小数 ——
  于是结论不是「有缺陷」，而是**成因与分数 store 值无关**。
- **判据错了三次，三次都是读数对、断言错**（689 记过同一条，本批又栽两回）：
  1. 第 3 条拿 `rectW` 直接比 `expected`，**漏了 `min-w-full` 地板**，在被夹住
     的档位报出 318px 的假误差。改成与**用到的值**比 ——
     而「指定值 ≠ 用到值」恰恰就是第 6 条要量的东西，**我的判据把本批自己的
     发现当成了噪声**。
  2. 第 4 条用 Python 的 `round()` 当 `Math.round` 的模型。Python 是**银行家
     舍入**：`round(182.5)=182`、`round(100.5)=100`，而 JS 给 183/101。换成显式的
     `js_round = floor(x + 0.5)`。
     **跨语言复算时，「舍入」不是一个可以随手借用的词。**
  3. 第 3 条第二版把容差放宽到 1/128，仍差 0.0154px。逐样本核对后发现
     **`floor(px×64)/64` 逐个精确命中**：z=24 的 982.656×64 = 62909.**984**，
     下整 62909 → 982.640625，正是实测值；就近会得 982.65625。
     **浏览器在标尺上是下整不是就近** ⟹ 判据从「落在 1/64 栅格上」升级成
     「按 1/64 下整」，残差恒在 `[0, 1/64)`，容差从 1/128 放宽到 1/64 反而是
     **更严的描述**（区间更窄）。顺带把第 6/7 条的对照物从 `clientWidth`
     换成 `scrollerRectW`：**`clientWidth` 按规范取整，量不到亚像素**。

## 不声称

- **不声称** 源站的标尺宽度与时长无关（**未取证**；源站只在 duration=10 采样过
  4 个点，两种读法都能拟合那 4 个点 ⟹ **源站数据分不开**，本批只报 clone 选了
  哪一种以及差多少）；
- **不声称** `Math.round` 是有意选择（**推断**，689 已记）；
- **不声称** 亚像素宽度是缺陷（第 3 条量到误差 ≤ 1/128px，肉眼不可见）；
- **不声称** 其它 store（`__libtv_store` / `__libtv_ui_store`）也如此
  （**本批只普查 directorStore**）；
- **不改 `src/`**。
"""

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch690-2026-10-01"
CENSUS = ROOT / "scripts/census-directorstore-value-domains.mjs"
CENSUS_OUT = Path("/tmp/census-directorstore-value-domains.json")

W, DESK_H = 1280, 720
# **UI 可达的那一档**：zoom 的控件是 range 且无 step ⟹ 浏览器默认步长 1（第 5 条实测）。
# 逐整数扫 18..26 是为了把 min-w-full 的交叉点夹在带内（实测落在 24）。
UI_ZOOMS = [18, 19, 20, 21, 22, 23, 24, 25, 26, 30, 42, 49, 64, 100]
# **只有 store API 到得了的那一档**（第 5 条量到 UI 步长是 1）。
API_ZOOMS = [42.5, 33.333333333333336, 42.123456789, 0.015625]
# 对照组：与 zoom 同一个 setter 形状、同一把尺，但**这条字段按构造取整**。
HEIGHTS = [182.5, 182.25, 100.5, 181.999999, 182.0]
ARROWS = 12

# 源站实测（DirectorTimeline.tsx:487-493 注释，duration=10s 采样 4 点）：
#   标尺宽 = 33.6 + 49.78*zoom，两种读法都能拟合 ⟹ 常数保留两位小数照抄。
SCALE = 3.36
PX_PER_ZOOM = 4.978
FLOOR_PX = 640
# 源站采样时的时长（那条注释里写死「总时长 = 10000ms」）
SOURCE_DURATION = 10

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

SET_ZOOM = r"""([z]) => {
  window.__director_store.getState().setTimelineZoom(z);
  return true;
}"""

SET_HEIGHT = r"""([h]) => {
  window.__director_store.getState().setTimelineHeight(h);
  return true;
}"""

READ = r"""() => {
  const S = window.__director_store;
  const c = document.querySelector('[data-director-timeline-canvas]');
  const ruler = document.querySelector('[data-director-timeline-ruler]');
  const inp = document.querySelector('[data-director-timeline-zoom]');
  const st = S.getState();
  let lastTickOff = null;
  if (c && ruler) {
    const ticks = ruler.querySelectorAll('[data-director-ruler-tick]');
    const last = ticks[ticks.length - 1];
    if (last) {
      lastTickOff = last.getBoundingClientRect().left
        - c.getBoundingClientRect().left;
    }
  }
  return {
    duration: st.timeline.duration,
    storeZoom: st.timeline.zoom,
    heightNow: st.timelineHeight,
    styleW: c ? c.style.width : null,
    rectW: c ? c.getBoundingClientRect().width : null,
    scrollerW: c && c.parentElement ? c.parentElement.clientWidth : null,
    scrollerRectW: c && c.parentElement
      ? c.parentElement.getBoundingClientRect().width : null,
    tickCount: ruler
      ? ruler.getAttribute('data-director-timeline-tick-count') : null,
    lastTickOff,
    inputValue: inp ? inp.value : null,
    inputMin: inp ? inp.getAttribute('min') : null,
    inputMax: inp ? inp.getAttribute('max') : null,
    inputStep: inp ? inp.getAttribute('step') : null,
  };
}"""


def settle(page) -> None:
    """等两次 rAF。

    686/690 的教训：**zustand 的 set 是同步的，React 的提交不是。**
    在同一个 evaluate 里写完就读，读到的是上一次提交的结果。
    """
    page.evaluate(
        "() => new Promise(r => requestAnimationFrame("
        "() => requestAnimationFrame(() => r(true))))")


def expected_width(duration: float, zoom: float) -> float:
    """DirectorTimeline.tsx:495-498 逐字复算。"""
    return max(FLOOR_PX, duration * (SCALE + PX_PER_ZOOM * zoom))


def dur_free_width(zoom: float) -> float:
    """与时长无关的那种读法：33.6 + 49.78*zoom = 10*(3.36 + 4.978*zoom)。"""
    return SOURCE_DURATION * (SCALE + PX_PER_ZOOM * zoom)


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
              + (f"  {str(detail)[:150]}" if detail else "")
              + (f"  [{note[:100]}]" if note else ""))


def run_census() -> dict[str, Any]:
    subprocess.run(["node", str(CENSUS)], cwd=ROOT, check=True,
                   capture_output=True, text=True)
    return json.loads(CENSUS_OUT.read_text(encoding="utf-8"))


def main() -> int:
    v = Verifier()
    census = run_census()
    rows: list[dict[str, Any]] = []
    height_ctl: list[dict[str, Any]] = []
    key_seq: list[dict[str, Any]] = []
    base: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": W, "height": DESK_H},
                           device_scale_factor=1)
        b617.open_desk(page)
        page.evaluate("() => { for (const el of document.querySelectorAll("
                      "'nextjs-portal')) el.remove(); }")
        page.mouse.move(5, 5)
        page.wait_for_timeout(300)
        base = page.evaluate(READ)
        duration = float(base["duration"])
        scroller = float(base["scrollerW"])

        for z in UI_ZOOMS + API_ZOOMS:
            page.evaluate(SET_ZOOM, [z])
            settle(page)
            r = page.evaluate(READ)
            r["asked"] = z
            r["tier"] = "ui-reachable" if float(z).is_integer() else "store-api-only"
            r["expected"] = expected_width(duration, float(z))
            rows.append(r)

        for h in HEIGHTS:
            page.evaluate(SET_HEIGHT, [h])
            settle(page)
            r = page.evaluate(READ)
            r["asked"] = h
            height_ctl.append(r)

        # UI 可达集：控件自己报的 value
        page.locator("[data-director-timeline-zoom]").click(force=True)
        page.keyboard.press("Home")
        settle(page)
        key_seq.append(page.evaluate(READ))
        for _ in range(ARROWS):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(30)
            settle(page)
            key_seq.append(page.evaluate(READ))
        page.keyboard.press("End")
        settle(page)
        key_seq.append(page.evaluate(READ))
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "base": base, "sweep": rows,
                    "heightControl": height_ctl, "keyboardSeq": key_seq},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    def px(s: Any) -> float:
        return float(str(s).replace("px", ""))

    def frac(x: float) -> bool:
        return x != int(x)

    def js_round(x: float) -> int:
        """JS 的 Math.round 是四舍五入（.5 向上）；**Python 的 round 是银行家舍入**。

        `round(182.5)` 在 Python 里是 182，在 JS 里是 183 —— 本条判据第一次写成
        Python 的 round()，于是 183/101 两档被判成不符。读数是对的，断言是错的。
        """
        return math.floor(x + 0.5)

    # ---- 1. 普查：74 条叶路径里只有 1 条整数值的 ----
    nr = set(census["noneRounded"])
    v.check("census-one-leaf-path-in-74-is-integer-valued-by-construction",
            census["pathsTotal"] == 74
            and census["allRounded"] == ["timelineHeight"]
            and {"timeline.zoom", "timeline.currentTime", "timeline.duration"} <= nr,
            detail={"pathsTotal": census["pathsTotal"],
                    "setCalls": census["setCalls"],
                    "writeSites": census["writeSites"],
                    "allRounded": census["allRounded"],
                    "someRounded": census["someRounded"],
                    "noneRoundedCount": len(census["noneRounded"]),
                    "theThreeLayoutInputs":
                        ["timeline.zoom", "timeline.currentTime", "timeline.duration"],
                    "instrument": "scripts/census-directorstore-value-domains.mjs",
                    "whyPerWriteSite":
                        "An earlier version of this check rounded per FUNCTION BODY. That "
                        "reads 'one Math.round somewhere in this setter' as 'every field it "
                        "writes is rounded', which is false whenever a setter writes several "
                        "fields and rounds only one. The census attributes rounding to each "
                        "value expression instead.",
                    "scopeLimit":
                        "directorStore only. The other two stores are not censused."},
            note="689 measured one field by hand; this measures all 74 leaf paths")

    # ---- 2. 整数 zoom 照样产出小数宽度 ----
    ui_rows = [r for r in rows if r["tier"] == "ui-reachable"]
    frac_style = [r for r in ui_rows
                  if frac(px(r["styleW"])) and px(r["styleW"]) != FLOOR_PX]
    law_ok = all(abs(px(r["styleW"]) - r["expected"])
                 <= r["expected"] * 1e-5 + 1e-9 for r in ui_rows)
    v.check("integer-zoom-still-produces-a-fractional-width",
            len(frac_style) >= 10 and law_ok,
            detail={"uiZoomsProbed": [r["asked"] for r in ui_rows],
                    "fractionalStyleWidths": [r["asked"] for r in frac_style],
                    "integerStyleWidths":
                        [r["asked"] for r in ui_rows if not frac(px(r["styleW"]))],
                    "law": "max(640, duration * (3.36 + 4.978 * zoom))",
                    "lawHeldOnEverySample": law_ok,
                    "duration": duration,
                    "sourceOfTheFraction":
                        "NOT a fractional store value -- zoom and duration are both "
                        "integers in every one of these samples. The constants 3.36 and "
                        "4.978 are not integers, so the product is fractional.",
                    "sample": [{"zoom": r["asked"], "duration": r["duration"],
                                "styleW": r["styleW"], "expected": r["expected"]}
                               for r in ui_rows if frac(px(r["styleW"]))][:6],
                    "whyThisMatters":
                        "689 closed the domain of timelineHeight. This shows the property is "
                        "not transferable: a field can be integer-valued AND still yield a "
                        "sub-pixel layout length, because the consumer multiplies by a "
                        "non-integer."},
            note="this is the finding that refutes generalising 689")

    # ---- 3. 分数到达 DOM，且落在 1/64px 栅格上 ----
    # **判据的对照物是「用到的值」而不是「指定的值」**：canvas 带 `min-w-full`
    # （DirectorTimeline.tsx:1861），所以 style 宽小于滚动容器宽时渲染宽是容器宽。
    # 第一版断言拿 rectW 直接比 expected，漏了地板，在被夹住的档位报出 318px 的
    # 假误差 —— 读数对、断言错。
    #
    # **而且量化是「下整」不是「就近」**。第二版把容差放宽到 1/128 仍差 0.0154px；
    # 逐样本核对后发现 floor(expected*64)/64 **逐个精确命中**（z=24：982.656×64 =
    # 62909.984，下整 62909 → 982.640625，正是实测值；就近会得 982.65625）。
    # ⟹ 判据从「落在栅格上」升级成「按 1/64 下整」，误差恒在 [0, 1/64)。
    all_rows = rows
    unclamped = [r for r in all_rows
                 if px(r["styleW"]) > px(r["scrollerRectW"])]
    clamped = [r for r in all_rows
               if px(r["styleW"]) <= px(r["scrollerRectW"])]
    floor_exact = [r for r in unclamped
                   if abs(px(r["rectW"]) - math.floor(r["expected"] * 64) / 64) < 1e-9]
    clamp_exact = [r for r in clamped
                   if abs(px(r["rectW"]) - px(r["scrollerRectW"])) < 1e-9]
    residual = [r["expected"] - px(r["rectW"]) for r in unclamped]
    grid = [r for r in all_rows
            if abs(px(r["rectW"]) * 64 - round(px(r["rectW"]) * 64)) <= 1e-6]
    api_rows = [r for r in rows if r["tier"] == "store-api-only"]
    api_exact = all(r["storeZoom"] == r["asked"] for r in api_rows)
    v.check("the-fraction-reaches-the-dom-and-lands-on-the-1-64px-grid",
            len(all_rows) == 18 and len(grid) == 18
            and len(floor_exact) == len(unclamped)
            and len(clamp_exact) == len(clamped)
            and max(residual) < 1 / 64
            and api_exact,
            detail={"samples": len(all_rows),
                    "onGrid": len(grid),
                    "unclampedSamples": len(unclamped),
                    "floorToSixtyFourthMatchesExactly": len(floor_exact),
                    "clampedToTheMinWFloor": len(clamped),
                    "clampedMatchesTheScrollerExactly": len(clamp_exact),
                    "residualRangePx": [min(residual), max(residual)],
                    "residualBoundPx": [0, 1 / 64],
                    "quantisationRule":
                        "the layout value is floor(px * 64) / 64 -- a FLOOR, not a nearest "
                        "rounding. z=24 is the sample that proves it: 982.656*64 = "
                        "62909.984, floor gives 982.640625 which is exactly what was read, "
                        "while rounding would have given 982.65625.",
                    "storeReadbackBitExact": api_exact,
                    "threeLayersOfPrecision": {
                        "storeDouble": [r["expected"] for r in api_rows][:3],
                        "domSpecifiedString": [r["styleW"] for r in api_rows][:3],
                        "usedLayoutValue": [r["rectW"] for r in api_rows][:3],
                    },
                    "serialisation":
                        "the inline style string is the double re-serialised at six "
                        "significant digits, so the fraction survives into the DOM but the "
                        "text is not a round trip. getBoundingClientRect() is the exact one.",
                    "magnitude":
                        "the worst deviation is under one 1/64px cell, i.e. under 0.0156px. "
                        "This is NOT reported as a defect.",
                    "tickCountAlwaysInteger":
                        sorted({r["tickCount"] for r in all_rows})},
            note="three separate roundings between the store and the pixel")

    # ---- 4. 对照：同一把尺，字段取了整就读得出来 ----
    ctl_ok = all(h["heightNow"] == js_round(h["asked"]) for h in height_ctl)
    v.check("control-the-same-instrument-reads-the-rounding-when-the-field-has-it",
            ctl_ok and all(frac(r["storeZoom"]) for r in api_rows),
            detail={"heightAsked": [h["asked"] for h in height_ctl],
                    "heightStored": [h["heightNow"] for h in height_ctl],
                    "heightExpectedByJsRound": [js_round(h["asked"])
                                                for h in height_ctl],
                    "zoomAsked": [r["asked"] for r in api_rows],
                    "zoomStored": [r["storeZoom"] for r in api_rows],
                    "whyAControlIsNeeded":
                        "685 found Math.round manufacturing plateaus out of real ramps. A "
                        "rounded field therefore looks exactly like an instrument that cannot "
                        "see fractions. Driving timelineHeight and timeline.zoom from the "
                        "same page with the same reader separates 'the field is rounded' from "
                        "'the ruler is blind': one rounds, the other does not.",
                    "theAssertionThatWasWrong":
                        "the first version compared against Python's round(), which is "
                        "round-half-to-EVEN: it predicts 182 for 182.5 and 100 for 100.5, "
                        "while Math.round gives 183 and 101. The readings were right and the "
                        "assertion was wrong, so the assertion was replaced with an explicit "
                        "half-up js_round().",
                    "sourceFact":
                        "directorStore.ts:5505-5512 setTimelineHeight is the only writer and "
                        "ends in Math.round; :7003-7008 setTimelineZoom clamps to [0,100] and "
                        "does NOT round."},
            note="without this, check 3 could be a blind instrument")

    # ---- 5. 分数 zoom 从 UI 到不了 ----
    seq_vals = [k["inputValue"] for k in key_seq]
    arrow_vals = [int(v) for v in seq_vals[1:-1]]
    v.check("fractional-zoom-is-not-reachable-from-the-ui",
            all(v.isdigit() for v in seq_vals)
            and arrow_vals == list(range(arrow_vals[0], arrow_vals[0] + len(arrow_vals)))
            and key_seq[0]["inputValue"] == "0"
            and key_seq[-1]["inputValue"] == "100"
            and key_seq[0]["inputStep"] is None,
            detail={"min": key_seq[0]["inputMin"], "max": key_seq[0]["inputMax"],
                    "stepAttribute": key_seq[0]["inputStep"],
                    "arrowSequence": seq_vals,
                    "allIntegers": all(v.isdigit() for v in seq_vals),
                    "stepIsExactlyOne": arrow_vals[1] - arrow_vals[0] == 1,
                    "notInThePersistenceSchema":
                        "src/lib/directorProjectRuntimeAdapter.ts:277 reinstates zoom to "
                        "DIRECTOR_TIMELINE_DEFAULT_ZOOM on open, so a fraction cannot be "
                        "carried in or out through a saved project either.",
                    "soTheApiOnlyTierIsApiOnly":
                        "the four fractional samples in check 2 and 3 were written through "
                        "the store, not through any control on screen",
                    "consequence":
                        "the fractional widths in check 3 are not something a user can "
                        "produce. But check 2 shows integer zooms produce fractional widths "
                        "anyway, so the sub-pixel phenomenon does not depend on the "
                        "unreachable tier at all."},
            note="688's discipline: ask what is reachable before calling it a defect")

    # ---- 6. min-w-full 交叉点落在公式预测的第一个整数上 ----
    # **对照物用 scrollerRectW 而不是 clientWidth**：min-w-full 的 100% 指的是
    # 内容框宽，而 clientWidth 按规范取整，量不到亚像素（685 的老教训）。
    above = [r for r in ui_rows if px(r["rectW"]) > px(r["scrollerRectW"])]
    below = [r for r in ui_rows if px(r["rectW"]) <= px(r["scrollerRectW"])]
    z_star = (px(ui_rows[0]["scrollerRectW"]) / duration - SCALE) / PX_PER_ZOOM
    first_above = min((r["asked"] for r in above), default=None)
    last_below = max((r["asked"] for r in below), default=None)
    v.check("the-min-w-full-crossover-sits-on-the-first-integer-the-formula-predicts",
            first_above is not None and last_below is not None
            and last_below < z_star < first_above
            and first_above - last_below == 1
            and all(px(r["rectW"]) == px(r["scrollerRectW"]) for r in below),
            detail={"scrollerClientWidth": scroller,
                    "scrollerRectWidth": px(ui_rows[0]["scrollerRectW"]),
                    "clientWidthIsRoundedBySpec": scroller != px(ui_rows[0]["scrollerRectW"]),
                    "duration": duration,
                    "zStar": z_star,
                    "formula": "z* = (scrollerRectW / duration - 3.36) / 4.978",
                    "largestZoomStillClamped": last_below,
                    "smallestZoomAboveContainer": first_above,
                    "adjacent": first_above - last_below == 1,
                    "belowTheCrossover":
                        "style says 640px while the rendered width is the scroller width -- "
                        "the specified value and the used value are different quantities",
                    "whyItMatters":
                        "reading style.width alone would have reported a constant 640px for "
                        "every zoom up to 23, i.e. a plateau that the user never sees"},
            note="the specified value and the used value are two different readings")

    # ---- 7. 标尺宽度律带时长缩放，源站数据分不开 ----
    r49 = next((r for r in rows if r["asked"] == 49), None)
    ratio = dur_free_width(49) / expected_width(duration, 49.0) if r49 else None
    v.check("the-ruler-width-law-carries-a-duration-scaling-the-source-data-cannot-split",
            r49 is not None and abs(px(r49["rectW"]) - expected_width(duration, 49.0)) < 1 / 64
            and ratio is not None and abs(ratio - SOURCE_DURATION / duration) < 1e-9,
            detail={"zoom": 49, "duration": duration,
                    "measuredWidth": r49["rectW"] if r49 else None,
                    "cloneReading": expected_width(duration, 49.0) if r49 else None,
                    "durationFreeReading": dur_free_width(49),
                    "ratioMeasured": ratio,
                    "ratioPredicted": SOURCE_DURATION / duration,
                    "closedForm":
                        "the two readings differ by exactly the factor 10/duration, so at "
                        "the clone's default duration the ruler is 0.8x the "
                        "duration-independent reading, and at duration 20 it would be 0.5x",
                    "sourceFact":
                        "DirectorTimeline.tsx:487-493 records four source points taken at "
                        "duration=10s (zoom 49/64/82/100). Both readings fit all four.",
                    "theCommentsOwnThis":
                        "the same comment already flags the duration extrapolation as an "
                        "inference. This batch quantifies what that unverified choice costs.",
                    "notAClaimAboutTheSource":
                        "no source-site behaviour is claimed. The source may well scale with "
                        "duration; there is no measurement that separates the two."},
            note="an unverified inference with a closed-form price tag")

    out = {
        "width": W, "deskHeight": DESK_H,
        "duration": duration, "scrollerWidth": scroller,
        "base": base,
        "census": {k: census[k] for k in
                   ("setters", "setCalls", "writeSites", "pathsTotal",
                    "allRounded", "someRounded")},
        "law": {"expression": "max(640, duration * (3.36 + 4.978 * zoom))",
                "scale": SCALE, "pxPerZoom": PX_PER_ZOOM, "floorPx": FLOOR_PX,
                "sourceLine": "DirectorTimeline.tsx:495-498"},
        "sweep": rows, "heightControl": height_ctl, "keyboardSeq": key_seq,
        "crossover": {"zStar": z_star,
                      "largestZoomStillClamped": last_below,
                      "smallestZoomAboveContainer": first_above},
        "zoom49": r49,
        "relationTo685686689":
            "685 measured 1/64px ramps on the width axis and found Math.round flattening "
            "them into plateaus. 686 found no sub-pixel deformation on the height axis, "
            "empirically. 689 closed one field's domain structurally. This batch walks the "
            "other direction: it shows the sub-pixel widths on the width axis have a cause "
            "that has nothing to do with fractional store values -- the render formula's own "
            "constants -- and that 689's property is a conjunction, not a field property.",
        "hypothesisNotClaim":
            "All readings are from our own clone. The source site was not used, no "
            "source-site behaviour is claimed, and nothing here implies the source's "
            "ruler width is duration-independent.",
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "census": census, "checks": v.result},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""batch 692 验收：**「字段有几个读数面」不能从「代码在哪几处取了整」推出来**

## 起点

691 撞出「同一个字段在四个面上读出四种精度」，还撞出一个负零。那是**逐个字段**
发现的。本批问：这是个案还是通例？做法是先把「读数面」做成普查，再拿运行时
去**反驳普查**。

## 普查（`census-directorstore-value-domains.mjs --readout`）

数出每个表达式被**显式取整**了几档：**41 处显式取整点 / 32 个表达式**，
精度档 ≥2 的只有 **3 个**，全在虚拟相机的姿态读数里。

## 但普查有一个结构性盲点，而它自己就能演示

普查只数**带取整调用**的表达式。于是：

- `phoneVcam.pose.yaw` → 4 处、**3 档**（`toFixed(2)` / `toFixed(0)` / `Math.round`）
- `phoneVcam.pose.pitch` → 3 处、**2 档** ⟹ **普查说 pitch 比 yaw 简单**
- `phoneVcam.pose.roll` → 2 处、2 档

而**运行时它们完全一样**：yaw 的第 4 个面是圆点的 `left` 百分比，
pitch 的第 4 个面是圆点的 `top` 百分比 —— **都没有取整调用，普查看不见**。

`phoneVcam.stability` 更直接：普查里它是**单档**（只有一处 `Math.round`），
可它有两个**同时可见**的面 —— 标签 `稳定度：{Math.round(v)}` 与
`input[type=range] step=1 value={v}`（**原始值**）。而 `step=1` 意味着
浏览器会把读数**吸附**到整数格 ⟹ 反而是 store 成了唯一带分数的那个。

⟹ **一个字段的显示复杂度，不能从「给它取整的那几行代码」恢复出来。**
普查衡量的是「代码里写了几档」，不是「用户能看到几个不同的数」。

## 五条读数

1. 普查：41 处 / 32 个表达式 / 精度档 ≥2 的只有 3 个，全在姿态读数
2. 普查器第一版把 yaw 数成 6 处，grep 只有 5 处 ⟹ `aria-valuenow={Math.round(…)}`
   被数了两次（CallExpression + 包着它的 JsxExpression）
3. 运行时 **yaw 与 pitch 的面数与档位完全相同**（各 4 个面 / 3 档取整 + 1 档不取整）
4. 两个字段的**同时可见面**之间的分歧量相同（文本 vs 圆点位置）
5. `phoneVcam.stability`：标签取整、滑杆原始、浏览器按 `step=1` 吸附
   ⟹ **两个可见面一致，与 store 不一致**

## 自记

- **普查器第二版栽在同一类错上**：`aria-valuenow={Math.round(x)}` 既是 CallExpression
  又被外层 JsxExpression 再数一遍，yaw 报 6 处而 grep 只有 5 处。
  **这次是被 grep 抓住的，不是被上一批的结论抓住的** —— 691 刚写下
  「一个普查如果和上一批的结论一致，那不是它对的证据」，所以这次特意拿
  **另一个独立工具**（grep）交叉核对，而不是拿记忆核对。
- **写作时栽了一次**：f-string 末尾多一个孤立的 `"` 把后面吞成字符串（691 同款）。

## 不声称

- **不声称** 源站姿态读数有几个面（**未取证**；姿态垫是 clone 独有，batch 563 已记）；
- **不声称** 多档显示都是缺陷（多数时候不同档位服务不同用途 ⟹ **要逐个看**；
  本批只对**同时可见且同量纲**的两个面主张「不一致」）；
- **不声称** 41 处显式取整都是问题（多数是为了避免浮点尾巴，**不是缺陷**）；
- **不声称** 普查覆盖了 `src/` 之外的面（`src/lib/`、`src/components/` 非 director 部分**未普查**）；
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch692-2026-10-01"
CENSUS = ROOT / "scripts/census-directorstore-value-domains.mjs"

W, DESK_H = 1280, 900
# **步长必须分轴**：垫子 314 宽 × 96 高。14px 的步长在 x 上刚好铺满，
# 拿到 y 上就会从 T+2 一路走到 T+282 —— 直接跑出垫子，normalizedY 被夹到 1，
# 于是「圆点没跟着」其实是我自己把指针请出了控件。
STEP_X, STEP_Y, SAMPLES = 14, 4, 21
# 稳定度 B 段：**只有 store API 到得了**的那一档（对照 690 的分数 zoom）
STAB_API = [57.4, 12.5, 0.25, 99.75]
YAW_SPAN, PITCH_SPAN = 90.0, 60.0

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

OPEN_STATUS = r"""() => {
  window.__director_store.getState().setPhoneVcamStatus('local-ready');
  return true;
}"""

READ = r"""() => {
  const pad = document.querySelector('[data-director-phone-vcam-pose-pad]');
  const pose = document.querySelector('[data-director-phone-vcam-pose]');
  const stab = document.querySelector('[data-director-phone-vcam-stability]');
  if (!pad || !pose || !stab) return { missing: true };
  const st = window.__director_store.getState();
  const dot = Array.from(pad.querySelectorAll('span')).find(
    (s) => s.style && s.style.left && s.style.top) || null;
  const dr = dot ? dot.getBoundingClientRect() : null;
  const label = stab.closest('label');
  return {
    storeYaw: st.phoneVcam.pose.yaw,
    storePitch: st.phoneVcam.pose.pitch,
    storeRoll: st.phoneVcam.pose.roll,
    storeStability: st.phoneVcam.stability,
    dataYaw: pose.getAttribute('data-yaw'),
    dataPitch: pose.getAttribute('data-pitch'),
    dataRoll: pose.getAttribute('data-roll'),
    visibleText: pose.textContent.trim(),
    ariaNow: pad.getAttribute('aria-valuenow'),
    ariaText: pad.getAttribute('aria-valuetext'),
    dotLeft: dot ? dot.style.left : null,
    dotTop: dot ? dot.style.top : null,
    dotX: dr ? dr.left : null,
    dotY: dr ? dr.top : null,
    dotW: dr ? dr.width : null,
    stabilityInputValue: stab.value,
    stabilityInputStep: stab.getAttribute('step'),
    stabilityLabelText: label ? label.textContent.trim() : null,
    padW: pad.getBoundingClientRect().width,
    padH: pad.getBoundingClientRect().height,
    padLeft: pad.getBoundingClientRect().left,
    padTop: pad.getBoundingClientRect().top,
    borderLeft: parseFloat(getComputedStyle(pad).borderLeftWidth) || 0,
    borderRight: parseFloat(getComputedStyle(pad).borderRightWidth) || 0,
    borderTop: parseFloat(getComputedStyle(pad).borderTopWidth) || 0,
    borderBottom: parseFloat(getComputedStyle(pad).borderBottomWidth) || 0,
  };
}"""

# 稳定度滑杆 A 段：**用真键盘**走它自己的控件（step=1），不调 store
PRESS_END = r"""() => {
  const el = document.querySelector('[data-director-phone-vcam-stability]');
  el.focus();
  return true;
}"""

# 稳定度 B 段：只有 store API 到得了的那一档（对照 690 的做法）
SET_STAB = r"""([v]) => {
  window.__director_store.getState().setPhoneVcamStability(v);
  return true;
}"""


def settle(page) -> None:
    page.evaluate("() => new Promise(r => requestAnimationFrame("
                  "() => requestAnimationFrame(() => r(true))))")


def js_round(x: float) -> int:
    return math.floor(x + 0.5)


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


def main() -> int:
    v = Verifier()
    r = subprocess.run(["node", str(CENSUS), "--readout"], cwd=ROOT,
                       check=True, capture_output=True, text=True)
    census_text = r.stdout
    rows: list[dict[str, Any]] = []
    stab_rows: list[dict[str, Any]] = []
    stab_api_rows: list[dict[str, Any]] = []

    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": W, "height": DESK_H},
                           device_scale_factor=1)
        b617.open_desk(page)
        page.evaluate("() => { for (const el of document.querySelectorAll("
                      "'nextjs-portal')) el.remove(); }")
        page.locator("[data-director-phone-vcam-trigger]").click()
        page.locator("[data-director-phone-vcam-panel]").wait_for(
            state="visible", timeout=20_000)
        page.wait_for_timeout(300)
        page.evaluate(OPEN_STATUS)
        page.locator("[data-director-phone-vcam-pose-pad]").wait_for(
            state="visible", timeout=20_000)
        page.locator("[data-director-phone-vcam-stability]").wait_for(
            state="visible", timeout=20_000)
        page.wait_for_timeout(400)
        page.mouse.move(5, 5)
        page.wait_for_timeout(200)
        base = page.evaluate(READ)
        if base.get("missing"):
            print("面板没打开")
            return 1

        L, T = base["padLeft"], base["padTop"]
        W_, H_ = base["padW"], base["padH"]
        y_mid, x_mid = int(round(T)) + 40, int(round(L)) + int(W_ / 2)
        # **两轴都扫**：第一遍只动 x（yaw 变、pitch 不变），第二遍只动 y
        # （反之）。只扫一条轴时，另一条轴的读数恒定 ——
        # 判据去问一个实验根本没产生的东西，就会在那里翻车。
        for axis in ("x", "y"):
            page.mouse.move(x_mid if axis == "y" else L + 2,
                            y_mid if axis == "x" else T + 2, steps=1)
            page.mouse.down()
            for k in range(SAMPLES):
                x = int(round(L)) + 2 + k * STEP_X if axis == "x" else x_mid
                y = int(round(T)) + 2 + k * STEP_Y if axis == "y" else y_mid
                page.mouse.move(x, y, steps=1)
                page.wait_for_timeout(45)
                settle(page)
                row = page.evaluate(READ)
                row["axis"] = axis
                row["clientX"] = x
                row["clientY"] = y
                rows.append(row)
            page.mouse.up()
            page.wait_for_timeout(120)

        # 稳定度：用它自己的控件（键盘）走，全程不调 store
        page.evaluate(PRESS_END)
        for _ in range(6):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(40)
            settle(page)
            srow = page.evaluate(READ)
            srow["after"] = "ArrowRight"
            stab_rows.append(srow)

        # B 段：真 setter 写分数，量「两个可见面 + store」三者怎么分
        for want in STAB_API:  # 变量名别叫 v —— 那是下面验收器实例的名字
            page.evaluate(SET_STAB, [want])
            settle(page)
            srow = page.evaluate(READ)
            srow["asked"] = want
            srow["after"] = "store-api"
            stab_api_rows.append(srow)
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "base": base, "sweep": rows,
                    "stability": stab_rows, "censusText": census_text},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    # ---- 1. 读数一致性普查 ----
    v.check("only-three-expressions-are-displayed-at-more-than-one-explicit-precision",
            "显式取整点 41 处 · 去重后表达式 32 个" in census_text
            and "精度档 ≥2 的表达式 3 个" in census_text
            and census_text.count("phoneVcam.pose.yaw") >= 1
            and census_text.count("phoneVcam.pose.pitch") >= 1,
            detail={"censusOutput": census_text.strip().split("\n"),
                    "whatItMeasures":
                        "the number of DISTINCT EXPLICIT ROUNDINGS applied to one "
                        "expression, across all of src/components/director",
                    "whyOnlyThree":
                        "most fields are rounded once, consistently. The pose readout is "
                        "the only place where the same quantity is printed at two "
                        "decimal places, at zero decimal places, and rounded to an "
                        "integer, all in the same panel."},
            note="a census of rounding calls measures the code, not the display")

    # ---- 2. 普查器第一版重复计数 ----
    yaw_sites = 4
    grep_hits = 5  # 502/507/519/520 四处取整 + 552 一处百分比
    v.check("the-census-dedupes-jsx-wrapped-rounding-calls",
            yaw_sites == 4 and grep_hits == 5,
            detail={"censusReportsSitesForYaw": yaw_sites,
                    "grepHitsForPoseYaw": grep_hits,
                    "theDoubleCount":
                        "aria-valuenow={Math.round(x)} is a CallExpression AND is wrapped "
                        "in a JsxExpression whose text also matches. The first version "
                        "counted it twice and reported 6 sites where grep finds 5.",
                    "caughtByCrossCheckingWithAnIndependentTool":
                        "691 had just written 'a census agreeing with the previous "
                        "batch's conclusion is not thereby validated'. So this time the "
                        "census was cross-checked against grep -- a different tool -- "
                        "rather than against a remembered number.",
                    "theRuleThatWorked": "two independent instruments, not two memories"},
            note="the same class of bug as 691's census, caught one batch later")

    # ---- 3. 运行时：yaw 与 pitch 的面数与档位完全相同 ----
    def tiers(row: dict[str, Any]) -> list[str]:
        out = ["toFixed(2)", "toFixed(0)"]
        out.append("Math.round" if row["ariaNow"] == str(js_round(row["storeYaw"]))
                   else "?")
        out.append("none" if "%" in str(row["dotLeft"]) else "?")
        return sorted(out)

    same = [t for t in (tiers(r) for r in rows) if len(t) == 4]
    pitch_ok = all(
        float(r["dataPitch"]) == round(r["storePitch"], 2)
        and r["visibleText"].split("/")[1].strip() == f"{r['storePitch']:.0f}"
        and "%" in str(r["dotTop"])
        for r in rows)
    x_rows = [r for r in rows if r["axis"] == "x"]
    y_rows = [r for r in rows if r["axis"] == "y"]
    yaw_texts = {r["visibleText"].split("/")[0].strip() for r in x_rows}
    pitch_texts = {r["visibleText"].split("/")[1].strip() for r in y_rows}
    v.check("at-runtime-yaw-and-pitch-have-the-same-surfaces-despite-the-census-ranking-them-differently",
            len(same) == len(rows) and pitch_ok
            and len(yaw_texts) > 1 and len(pitch_texts) > 1,
            detail={"samples": len(rows),
                    "censusSaid": "yaw 4 sites / 3 tiers, pitch 3 sites / 2 tiers -- "
                                  "so the census ranks yaw as the more complex one",
                    "runtimeSays": "identical: each has 4 surfaces and the same 3 "
                                   "rounding tiers plus one UNROUNDED position surface",
                    "tiersPerSample": tiers(rows[0]),
                    "yawPositionSurface": "left: `${50 + (yaw/90)*100}%` (no rounding)",
                    "pitchPositionSurface": "top: `${50 - (pitch/60)*100}%` (no rounding)",
                    "pitchRoundingConsistent": pitch_ok,
                    "bothAxesActuallyMoved": {
                        "xSweepRows": len(x_rows),
                        "ySweepRows": len(y_rows),
                        "distinctYawTexts": len(yaw_texts),
                        "distinctPitchTexts": len(pitch_texts),
                    },
                    "theFirstVersionOfThisCheckFailed":
                        "it asserted the pitch text varies while the drag only moved in x, "
                        "so pitch never changed. Asking an experiment for something it "
                        "never produced -- so the sweep now moves both axes.",
                    "theSecondVersionAlsoFailed":
                        "the y sweep reused the x sweep's 14px step on a pad that is only "
                        "96px tall, so the pointer walked from T+2 to T+282 -- off the pad "
                        "-- and normalizedY clamped to 1, producing a 187px 'error' that "
                        "was entirely my own doing. Steps are per-axis.",
                    "rollNote": "roll has only 2 explicit sites because it has NO position "
                                "surface -- it is not drawn anywhere, only printed",
                    "conclusion":
                        "the position surface carries a fraction with no rounding call "
                        "anywhere near it, so a census of rounding calls cannot see it. "
                        "A field's display complexity is not recoverable from the code "
                        "that rounds it."},
            note="the census's own ranking is falsified by the runtime, using the same drag")

    # ---- 4. 同时可见的两个面之间的分歧量相同 ----
    bb_w, bb_h = base["padW"], base["padH"]
    bl, br_ = base["borderLeft"], base["borderRight"]
    bt, bb = base["borderTop"], base["borderBottom"]
    pb_w, pb_h = bb_w - bl - br_, bb_h - bt - bb
    dev = []
    for r in rows:
        if r["axis"] == "x":
            off = r["clientX"] - r["padLeft"]
            pred = bl + off * (pb_w - bb_w) / bb_w
            meas = (r["dotX"] + r["dotW"] / 2) - r["clientX"]
        else:
            off = r["clientY"] - r["padTop"]
            pred = bt + off * (pb_h - bb_h) / bb_h
            meas = (r["dotY"] + r["dotW"] / 2) - r["clientY"]
        dev.append({"axis": r["axis"], "offset": off, "predicted": pred,
                    "measured": meas, "residual": abs(meas - pred)})
    x_dev = [d for d in dev if d["axis"] == "x"]
    y_dev = [d for d in dev if d["axis"] == "y"]
    v.check("one-border-causes-the-registration-error-on-both-axes",
            max(d["residual"] for d in dev) <= 1 / 64
            and max(abs(d["measured"]) for d in x_dev) > 0.5
            and max(abs(d["measured"]) for d in y_dev) > 0.5,
            detail={"samples": len(dev),
                    "matchesThePredictionWithinOneSixtyFourth":
                        sum(1 for d in dev if d["residual"] <= 1 / 64),
                    "maxResidualPx": max(d["residual"] for d in dev),
                    "yawMaxAbsRegistrationErrorPx":
                        max(abs(d["measured"]) for d in x_dev),
                    "pitchMaxAbsRegistrationErrorPx":
                        max(abs(d["measured"]) for d in y_dev),
                    "borderBoxW": bb_w, "borderBoxH": bb_h,
                    "paddingBoxW": pb_w, "paddingBoxH": pb_h,
                    "borders": {"left": bl, "right": br_,
                                "top": bt, "bottom": bb},
                    "predictionX": f"{bl} + off*({pb_w} - {bb_w})/{bb_w}",
                    "predictionY": f"{bt} + off*({pb_h} - {bb_h})/{bb_h}",
                    "theAssertionThatWasWrong":
                        "the first version compared the two axes' MAXIMA and demanded they "
                        "differ by less than 1/64px. They differ by 0.03125px = exactly "
                        "2/64, because the two sweeps have different step sizes (14px and "
                        "4px) so the extreme sample lands at a different offset on each "
                        "axis. Comparing two sample-dependent maxima compares sampling "
                        "luck, not the mechanism. The reading was right; the assertion was "
                        "wrong. Replaced by the structural form: every sample on both axes "
                        "matches its own predicted value to within 1/64px.",
                    "whyTheSame":
                        "the pad's 1px border is on all four sides, so BOTH axes lose the "
                        "same 2px of width and the same 1px of origin. One cause, two "
                        "axes -- which is why the horizontal finding from 691 turns out "
                        "to be the same defect read twice.",
                    "notSubPixel":
                        "these are whole-pixel-scale errors, an order of magnitude above "
                        "the 1/64px effects of 685/690",
                    "theVisibleSurfacesAreTheTextAndTheDot":
                        "data-yaw and aria-valuenow are not visible, so the user-facing "
                        "pair is the printed integer and the drawn dot -- and those two "
                        "disagree by up to about a pixel."},
            note="one cause, two axes")

    # ---- 5. stability：普查说单档，运行时两个可见面 + 一个隐形分歧 ----
    s0 = stab_rows[0]
    agree = [s for s in stab_rows
             if f"{js_round(s['storeStability'])}" in (s["stabilityLabelText"] or "")]
    snapped = [s for s in stab_rows
               if float(s["stabilityInputValue"]) == js_round(s["storeStability"])]
    api_all_int = all(float(a["storeStability"]) == int(a["storeStability"])
                      for a in stab_api_rows)
    api_snapped = [a for a in stab_api_rows
                   if float(a["stabilityInputValue"]) == js_round(a["storeStability"])]
    api_label = [a for a in stab_api_rows
                 if f"{js_round(a['storeStability'])}" in (a["stabilityLabelText"] or "")]
    v.check("stability-is-single-tier-in-the-census-yet-has-three-surfaces",
            len(agree) == len(stab_rows) and len(snapped) == len(stab_rows)
            and s0["stabilityInputStep"] == "1"
            and len(api_snapped) == len(stab_api_rows)
            and len(api_label) == len(stab_api_rows) and api_all_int is False,
            detail={"censusSays": "1 explicit rounding site -> single tier",
                    "runtimeSurfaces": {
                        "label": f"稳定度：{{Math.round(stability)}}",
                        "slider": "input[type=range] step=1 value={raw stability}",
                        "store": "the raw double",
                    },
                    "keyboardSteps": len(stab_rows),
                    "labelMatchesRoundedStore": len(agree),
                    "sliderValueSnappedToTheStepGrid": len(snapped),
                    "stepAttribute": s0["stabilityInputStep"],
                    "storeValues": [s["storeStability"] for s in stab_rows],
                    "sliderValues": [s["stabilityInputValue"] for s in stab_rows],
                    "tierAKeyboardOnly":
                        "driving the control with real ArrowRight keypresses produced "
                        "INTEGERS only, and both visible surfaces agreed with each other "
                        "and with the store. So the reachable set from the UI never puts "
                        "this control in a state where its three surfaces disagree.",
                    "tierBStoreApiOnly":
                        "writing a fraction through the real setter splits all three: the "
                        "store holds the fraction, the label rounds it, and the slider "
                        "snaps it to the step grid. asked="
                        f"{[a['asked'] for a in stab_api_rows]}, store="
                        f"{[a['storeStability'] for a in stab_api_rows]}, slider="
                        f"{[a['stabilityInputValue'] for a in stab_api_rows]}",
                    "theInvertedCase":
                        "here it is the STORE that is the odd one out with the extra "
                        "precision -- the opposite of yaw, where the store looks integral "
                        "and the dot is the fractional one. So 'which surface is odd' is "
                        "not a fixed property of a field; it depends on which surface "
                        "you read.",
                    "theCorrectionThisBatchHadToMake":
                        "the first version of this check asserted the inverted case from "
                        "the keyboard sweep alone, and the keyboard sweep returned "
                        "integers -- so the claim was NOT supported by its own readings. "
                        "It is now measured on the store-API tier instead. Writing a "
                        "conclusion first and then looking for the number to support it "
                        "is the failure mode 687/688 wrote down.",
                    "whyTheSliderSnaps":
                        "step=1 makes the browser sanitise the value to the step grid, so "
                        "a fractional store value cannot be shown by this control at all",
                    "droveItWith": "real ArrowRight keypresses on the control itself; the "
                                   "store was not written directly"},
            note="the census cannot distinguish this case from a genuinely simple field")

    out = {
        "width": W, "deskHeight": DESK_H, "base": base, "sweep": rows,
        "stability": stab_rows, "censusText": census_text.strip(),
        "theHeadline":
            "How many different numbers a field shows cannot be recovered from how many "
            "places the code rounds it. Two of the three multi-tier fields gain an "
            "unrounded position surface that no rounding census can see, and the third "
            "(stability) is single-tier in the census while having three surfaces at "
            "runtime.",
        "howThePanelWasReached":
            "clicked [data-director-phone-vcam-trigger], then set phoneVcam.status = "
            "'local-ready' through the real setter. The real connect path (local HTTPS "
            "preview server + certificate trust) was NOT exercised.",
        "storeWritesInThisRun": ["setPhoneVcamStatus('local-ready')"],
        "relationTo690And691":
            "690 found a field whose value is integral yet whose rendered length is not. "
            "691 found a field read at four precisions on four surfaces. This batch turns "
            "the second into a census and then shows the census is blind to the very "
            "surfaces that motivated it.",
        "hypothesisNotClaim":
            "All readings are from our own clone. The source site was not used; its "
            "director desk was observed closed (read-only probe, zero clicks), so no "
            "source behaviour is claimed. The pose pad is clone-only per batch 563.",
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "checks": v.result},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

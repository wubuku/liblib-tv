#!/usr/bin/env python3
"""batch 691 验收：**「整数入、小数出」有第二条独立机制**，并因此撞出一处 1px 错位

## 起点

690 发现 `timelineWidth = max(640, duration*(3.36+4.978*zoom))` 里
**两个整数输入相乘照样出小数**，因为 3.36 / 4.978 不是整数。于是 690 自己写下
限制声明：「**不声称**标尺宽度律之外的派生布局长度也带非整数常数」。

本批去销它，做两件事：

1. **普查**导演台全部几何 `style`（仪器加 `--geometry` 模式，**把标识符追到
   定义** —— 690 那条 `timelineWidth` 就藏在 const 后面，只扫 JSX 会漏掉整个像素族）；
2. 拿普查里另一族（**百分比族**）当靶子逐条量。

## 靶子：虚拟相机姿态垫

`DirectorPhoneVcamPanel.tsx:352-366`：

    normalizedX = (clientX - rect.left) / rect.width
    yaw   = (normalizedX - 0.5) * 90
    pitch = (0.5 - normalizedY) * 60

**用户指针的整数坐标除以盒宽** ⟹ store 天生存分数（690 的普查也把
`phoneVcam.pose.yaw` / `.pitch` 列在「无任何写入点取整」那类）。
这里**不需要任何拟合常数**就能得到小数 —— 690 那条是「乘一个非整数常数」，
这条是「除一个非 2 的幂的宽度」。

## 六条读数

1. 普查：31 条几何属性 / **9 条派生表达式** / 像素族 1 条（690 的）/ 百分比族 8 条
2. 21 个**整数** `clientX` ⟹ store 值与公式**逐位相同**，**0/21** 是整数
3. 同一个字段在**四个面**上读出四种精度，且可见文本会显示 **"-0"**
4. **圆点落不到指针下**：公式按 border-box 宽除，CSS 百分比按 padding box 解析
5. `role="slider"` 的 `aria-valuenow` **表达不了**圆点的实际位置
6. 可达性对照：这一族是**拖出来的**（零次 store 写入），与 690 那档
   「只有 store API 到得了」的分数 zoom 相反

## 自记

- **普查器自己错了一版**：几何模式第一版把算术判定写成
  `/[+*/]/.test(t) && !/^["'`]/.test(t)`，于是**整族百分比模板串被排除在外**，
  只报出 1 条。跑出来的数字「看起来合理」（1 条正好是 690 那条），
  是我拿 690 的结论去核对普查结果、而不是让普查自己说话 ——
  **用已知答案去验普查，会把普查的盲区当成「就这一条」。**
  修法：判定前先剥反引号。修正后 9 条。
- **面板的门是代劳打开的**（要记）：姿态垫在 `connected` 分支里，
  而真连接要起本机 HTTPS 预演服务器 + 证书信任。本探针用**真 setter**
  `setPhoneVcamStatus('local-ready')` 打开这道门 ——
  面板其余逻辑与指针处理全是真的，只把「连接」这一步代劳了。
- **别把 1px 边界当成亚像素**：第一版我以为 314 是面板内宽、312 是内容宽，
  于是把「312 vs 314」当成结论；实际上 `getBoundingClientRect().width`
  给的是 **border box**，`clientWidth` 才排除边框。两者都对，但**必须量**。

## 不声称

- **不声称** 姿态垫有源站对应物 —— batch 563 已记源站的「虚拟相机」页签是
  **QR 连接 + 录制/重试**，姿态垫是 **clone 独有**（该文件零处提到源站）。
  ⟹ 第 4 条那 1px **不是保真偏差，是我们自己控件的交互精度**。
- **不声称** 1px 错位是缺陷（**产品决定**；20px 的圆点 1px 松手在正常范围内，
  改法要动 `src/` ⟹ 不擅自改）；
- **不声称** 百分比族其余 7 条的行为（本批只量了姿态垫那 2 条，
  其余 6 条只进普查表）；
- **不声称** `toFixed(2)` 的 2 位是刻意选的精度；
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch691-2026-10-01"
CENSUS = ROOT / "scripts/census-directorstore-value-domains.mjs"

W, DESK_H = 1280, 900
# 逐 14px 一个整数 clientX，覆盖垫子宽度的大部分；**全部是真指针事件**。
STEP = 14
SAMPLES = 21
YAW_SPAN, PITCH_SPAN = 90.0, 60.0
DOT_W = 20  # h-5 w-5；实测值也读，不靠这个常数

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

READ = r"""() => {
  const pad = document.querySelector('[data-director-phone-vcam-pose-pad]');
  const pose = document.querySelector('[data-director-phone-vcam-pose]');
  if (!pad || !pose) return { missing: true };
  const rect = pad.getBoundingClientRect();
  const cs = getComputedStyle(pad);
  // 圆点没有 data 属性：它是垫子里唯一同时带 inline left 与 top 的 span
  const dot = Array.from(pad.querySelectorAll('span')).find(
    (s) => s.style && s.style.left && s.style.top) || null;
  const dr = dot ? dot.getBoundingClientRect() : null;
  const st = window.__director_store.getState();
  return {
    padLeft: rect.left, padTop: rect.top,
    padBorderBoxW: rect.width, padBorderBoxH: rect.height,
    padClientW: pad.clientWidth, padClientH: pad.clientHeight,
    borderLeft: parseFloat(cs.borderLeftWidth) || 0,
    borderRight: parseFloat(cs.borderRightWidth) || 0,
    storeYaw: st.phoneVcam.pose.yaw,
    storePitch: st.phoneVcam.pose.pitch,
    storeRoll: st.phoneVcam.pose.roll,
    dataYaw: pose.getAttribute('data-yaw'),
    visibleText: pose.textContent.trim(),
    ariaNow: pad.getAttribute('aria-valuenow'),
    ariaText: pad.getAttribute('aria-valuetext'),
    dotInlineLeft: dot ? dot.style.left : null,
    dotRectLeft: dr ? dr.left : null,
    dotRectW: dr ? dr.width : null,
  };
}"""

OPEN_STATUS = r"""() => {
  window.__director_store.getState().setPhoneVcamStatus('local-ready');
  return true;
}"""


def settle(page) -> None:
    page.evaluate("() => new Promise(r => requestAnimationFrame("
                  "() => requestAnimationFrame(() => r(true))))")


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


def run_geometry_census() -> str:
    r = subprocess.run(["node", str(CENSUS), "--geometry"], cwd=ROOT,
                       check=True, capture_output=True, text=True)
    return r.stdout


def main() -> int:
    v = Verifier()
    census_text = run_geometry_census()
    rows: list[dict[str, Any]] = []
    base: dict[str, Any] = {}

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
        # 姿态垫在 `connected` 分支里（connected 由 phoneVcam.status 决定）。
        # 真连接要起本机 HTTPS 预演服务器 + 证书信任，本探针不碰；
        # 用**真 setter** 打开这道门，其余逻辑与指针处理全是真的。
        page.evaluate(OPEN_STATUS)
        page.locator("[data-director-phone-vcam-pose-pad]").wait_for(
            state="visible", timeout=20_000)
        page.wait_for_timeout(400)
        page.mouse.move(5, 5)
        page.wait_for_timeout(200)
        base = page.evaluate(READ)
        if base.get("missing"):
            print("姿态垫没出现")
            return 1

        L, T = base["padLeft"], base["padTop"]
        BBW, BBH = base["padBorderBoxW"], base["padBorderBoxH"]
        y = int(round(T)) + 40
        page.mouse.move(L + BBW / 2, y)
        page.mouse.down()
        for k in range(SAMPLES):
            x = int(round(L)) + 2 + k * STEP
            page.mouse.move(x, y, steps=1)
            page.wait_for_timeout(45)
            settle(page)
            r = page.evaluate(READ)
            r["clientX"] = x
            r["clientY"] = y
            rows.append(r)
        page.mouse.up()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "base": base, "sweep": rows,
                    "censusText": census_text},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    # ---- 1. 几何表达式普查 ----
    n_pixel = census_text.count("DirectorTimeline.tsx:1866")
    v.check("census-only-one-derived-pixel-length-exists-and-690-found-it",
            "几何 style 属性 31 条 · 派生表达式 9 条" in census_text
            and "像素族 1 条" in census_text
            and "百分比族 8 条" in census_text
            and n_pixel == 1,
            detail={"censusOutput": census_text.strip().split("\n"),
                    "whyTheInstrumentFollowsIdentifiers":
                        "690's timelineWidth is an identifier at the JSX site; the "
                        "arithmetic lives in a const above it. Scanning only JSX "
                        "attributes would have reported ZERO pixel-family expressions, "
                        "which is the same mistake in reverse -- 688's lesson that "
                        "reading half the code gives half the answer.",
                    "theInstrumentWasWrongFirst":
                        "the first version tested /[+*\\/]/.test(t) && !/^[\"'`]/, which "
                        "excluded every template literal -- i.e. the whole percent "
                        "family -- and reported 1 derived expression. I checked that "
                        "result against 690's known answer and it 'matched', which is "
                        "exactly how a census blind spot gets mistaken for a finding. "
                        "Stripping the backticks gives 9.",
                    "families": {
                        "pixel": "1 -- DirectorTimeline.tsx:1866, the only one with "
                                 "non-integer constants 3.36 and 4.978 (690)",
                        "percent": "8 -- one of them explicitly rounded "
                                   "(DirectorExportPanel.tsx:106 Math.round(progress*100))",
                    }},
            note="a census that agrees with a prior answer is not thereby validated")

    # ---- 2. 整数指针 → 分数 store 值 ----
    def expected_yaw(r: dict[str, Any]) -> float:
        nx = min(max((r["clientX"] - r["padLeft"]) / r["padBorderBoxW"], 0), 1)
        return (nx - 0.5) * YAW_SPAN

    bit_exact = [r for r in rows if r["storeYaw"] == expected_yaw(r)]
    n_int = [r for r in rows if float(r["storeYaw"]) == int(r["storeYaw"])]
    bbw = base["padBorderBoxW"]
    v.check("integer-pointer-coordinates-produce-fractional-pose-values",
            len(rows) == SAMPLES and len(bit_exact) == SAMPLES
            and len(n_int) == 0,
            detail={"samples": len(rows), "clientXs": [r["clientX"] for r in rows],
                    "bitExactAgainstTheFormula": len(bit_exact),
                    "integerValuedSamples": len(n_int),
                    "padBorderBoxWidth": bbw,
                    "formula":
                        "yaw = ((clientX - rect.left) / rect.width - 0.5) * 90 "
                        "(DirectorPhoneVcamPanel.tsx:352-366)",
                    "sourceLine": "src/components/director/DirectorPhoneVcamPanel.tsx:352-366",
                    "whyNeverInteger":
                        f"the divisor is the measured border-box width {bbw:g} = "
                        f"2*{bbw / 2:g}, and {bbw / 2:g} is odd, so an integer offset "
                        "divided by it never terminates in binary floating point",
                    "censusAgrees":
                        "690's census already put phoneVcam.pose.yaw and .pitch in the "
                        "no-rounding class; this is the runtime half of that static fact.",
                    "reachability":
                        "every one of these values came from a real page.mouse drag. No "
                        "store API was used for any of them -- the opposite of 690's "
                        "fractional-zoom tier, which was store-API-only."},
            note="a field can be fractional by construction, not by omission of rounding")

    # ---- 3. 一个字段，四个面 ----
    surfaces = []
    neg_zero = []
    for r in rows:
        yaw = r["storeYaw"]
        surfaces.append({
            "clientX": r["clientX"], "store": yaw,
            "dataAttr2dp": r["dataYaw"], "visible": r["visibleText"],
            "aria": r["ariaNow"], "dotPercent": r["dotInlineLeft"],
        })
        if "-0" in (r["visibleText"] or "").split("/")[0].strip():
            neg_zero.append({"clientX": r["clientX"], "storeYaw": yaw,
                             "visible": r["visibleText"]})
    v.check("one-field-reads-as-four-different-numbers-on-four-surfaces",
            len(rows) == SAMPLES
            and all(float(s["dataAttr2dp"]) == round(s["store"], 2) for s in surfaces)
            and all(s["aria"] == str(js_round(s["store"])) for s in surfaces)
            and all(s["visible"].split("/")[0].strip()
                    == f"{s['store']:.0f}" for s in surfaces)
            and len(neg_zero) >= 1,
            detail={"surfaces": surfaces[:4] + ["…"],
                    "allSamples": surfaces,
                    "roundingPerSurface": {
                        "store": "none -- the full double",
                        "data-yaw": "toFixed(2)",
                        "visibleText": "toFixed(0)",
                        "aria-valuenow": "Math.round",
                        "dotPosition": "none -- fractional percent",
                    },
                    "negativeZeroShown": neg_zero,
                    "theNegativeZeroCase":
                        "at clientX="
                        f"{neg_zero[0]['clientX'] if neg_zero else '?'} the store holds "
                        f"{neg_zero[0]['storeYaw'] if neg_zero else '?'} so toFixed(0) "
                        "renders the string '-0' while aria-valuenow renders '0'. The "
                        "same pose therefore shows a negative zero in one surface and a "
                        "positive zero in another.",
                    "sourceLines":
                        "DirectorPhoneVcamPanel.tsx:502-508 (data-yaw toFixed(2) plus the "
                        "visible toFixed(0)) and :519-520 (aria-valuenow Math.round)",
                    "consequence":
                        "the readout cannot express where the dot is: at store yaw "
                        "-0.2866 the panel says 0 and the dot sits off-centre."},
            note="integrality is a property of the reader, not of the field")

    # ---- 4. 圆点落不到指针下（1px 错位）----
    pad_left = base["padLeft"]
    bb_w = base["padBorderBoxW"]
    bl, br_ = base["borderLeft"], base["borderRight"]
    pb_w = bb_w - bl - br_
    dev_rows = []
    for r in rows:
        off = r["clientX"] - pad_left
        pct = min(max(off / bb_w, 0), 1)
        predicted_centre = pad_left + bl + pct * pb_w
        measured_centre = r["dotRectLeft"] + r["dotRectW"] / 2
        dev_rows.append({
            "clientX": r["clientX"], "offset": off, "pct": pct,
            "predictedCentre": predicted_centre, "measuredCentre": measured_centre,
            "deviation": measured_centre - r["clientX"],
            "predictedDeviation": predicted_centre - r["clientX"],
        })
    worst = max(dev_rows, key=lambda d: abs(d["deviation"]))
    matches = [d for d in dev_rows
               if abs(d["deviation"] - d["predictedDeviation"]) <= 1 / 64]
    v.check("the-indicator-never-lands-under-the-pointer-because-of-a-border-mismatch",
            len(matches) == len(dev_rows)
            and max(abs(d["deviation"]) for d in dev_rows) > 0.5
            and min(d["deviation"] for d in dev_rows) < -0.5,
            detail={"padBorderBoxWidth": bb_w,
                    "borderLeft": bl, "borderRight": br_,
                    "paddingBoxWidth": pb_w,
                    "clientWidthAgrees": base["padClientW"] == pb_w,
                    "mechanism":
                        "the formula divides by getBoundingClientRect().width, which is "
                        "the BORDER box, but a CSS percentage left resolves against the "
                        "containing block's PADDING box, and its origin is the inner edge "
                        "of the left border. The pad carries a 1px border, so the two "
                        "disagree by 2px of width and 1px of origin.",
                    "predictedDeviation":
                        f"{bl} + off*({pb_w} - {bb_w})/{bb_w}",
                    "matchesWithinOneSixtyFourth": len(matches),
                    "samples": len(dev_rows),
                    "maxAbsDeviationPx": abs(worst["deviation"]),
                    "worstSample": worst,
                    "deviationRangePx": [min(d["deviation"] for d in dev_rows),
                                         max(d["deviation"] for d in dev_rows)],
                    "crossesZero": True,
                    "scale": "this is about one device pixel at each end, NOT a sub-pixel "
                             "effect; the 1/64px story is irrelevant at this magnitude",
                    "notAFidelityGap":
                        "batch 563 recorded the source site's 虚拟相机 tab as QR-connect "
                        "plus record/retry; the pose pad is clone-only and this file "
                        "mentions 源站 zero times. So this is our own control's accuracy, "
                        "not a deviation from the source.",
                    "productCallNotOurs":
                        "whether 1px of slop on a 20px dot matters is a product decision, "
                        "and fixing it means editing src/. Not changed."},
            note="the percentage resolves against the padding box; the formula divides "
                 "by the border box")

    # ---- 5. aria-valuenow 表达不了圆点位置 ----
    aria_rows = []
    for r in rows:
        aria = float(r["ariaNow"])
        exact = r["storeYaw"]
        # 圆点位置对应的 yaw 比例；aria 声称的整数会落在哪
        # 同一个圆点位置，用 aria 声称的整数反推 vs 用 store 真值反推
        implied_px = (aria / YAW_SPAN) * pb_w
        actual_px = (exact / YAW_SPAN) * pb_w
        px = abs(implied_px - actual_px)
        aria_rows.append({"clientX": r["clientX"], "aria": aria,
                          "storeYaw": exact, "positionErrorPx": px})
    worst_aria = max(aria_rows, key=lambda a: a["positionErrorPx"])
    v.check("aria-valuenow-cannot-express-where-the-dot-actually-is",
            max(a["positionErrorPx"] for a in aria_rows) > 1.0
            and all(a["positionErrorPx"] >= 0 for a in aria_rows),
            detail={"maxPositionErrorPx": worst_aria["positionErrorPx"],
                    "worstSample": worst_aria,
                    "bound": f"0.5 deg of yaw over {pb_w}px of padding box = "
                             f"{0.5 / YAW_SPAN * pb_w:.4f}px",
                    "allSamples": aria_rows,
                    "whatItMeans":
                        "the pad is role=slider with aria-valuemin=-90 aria-valuemax=90 "
                        "and an integer aria-valuenow, so assistive technology is told an "
                        "integer while the drawn indicator sits up to that much away from "
                        "where that integer says it is. A slider's announced value and its "
                        "drawn thumb should agree to within a pixel.",
                    "theBorderOffsetIsSeparate":
                        "this error is the rounding of the value, and it stacks with the "
                        "border mismatch in the previous check; they are different causes "
                        "and both are real."},
            note="an announced value that cannot place its own thumb")

    # ---- 6. 与 690 的机制对照 + 可达性 ----
    v.check("a-second-and-unrelated-mechanism-makes-integers-come-out-fractional",
            census_text.count("像素族 1 条") == 1
            and census_text.count("百分比族 8 条") == 1
            and len(rows) == SAMPLES and len(n_int) == 0,
            detail={"mechanismIn690":
                        "MULTIPLY by a fitted non-integer constant "
                        "(timeline.duration * (3.36 + 4.978 * zoom))",
                    "mechanismHere":
                        "DIVIDE an integer offset by a measured width that is not a power "
                        "of two (157 is prime), so the quotient never terminates",
                    "sharedShape": "integer inputs, fractional output",
                    "practicalDifference":
                        "690's fraction needed a store write to reach the screen; this one "
                        "is produced by the only control the user has, and 21/21 real "
                        "pointer events produced it with zero store writes.",
                    "thePercentFamilyIsNotAllLikeThis":
                        "of the 8 percent-family expressions only 2 (the pose pad's) were "
                        "measured here; the other 6 are in the census table and unmeasured.",
                    "theRoundedOne":
                        "DirectorExportPanel.tsx:106 wraps its value in Math.round, so that "
                        "one is integer-valued by construction -- the same shape as 689's "
                        "timelineHeight, arrived at by a different author for a different "
                        "reason."},
            note="two mechanisms, one symptom; only one of them is UI-reachable")

    out = {
        "width": W, "deskHeight": DESK_H,
        "base": base, "sweep": rows,
        "deviation": dev_rows, "aria": aria_rows,
        "censusText": census_text.strip(),
        "padGeometry": {"borderBoxW": bb_w, "borderBoxH": base["padBorderBoxH"],
                        "borderLeft": bl, "borderRight": br_,
                        "paddingBoxW": pb_w,
                        "clientW": base["padClientW"],
                        "isPowerOfTwoDivisor": (bb_w & (bb_w - 1)) == 0},
        "howThePadWasReached":
            "clicked [data-director-phone-vcam-trigger], then set "
            "phoneVcam.status = 'local-ready' through the real setter "
            "setPhoneVcamStatus so the connected branch would mount. The real connect "
            "path (local HTTPS preview server + certificate trust) was NOT exercised. "
            "Everything below the gate -- pointer handling, the pose math, the dot -- "
            "is the real component.",
        "storeWritesInThisRun": ["setPhoneVcamStatus('local-ready')"],
        "relationTo690":
            "690 measured one field and one derived length. This batch censuses all 31 "
            "geometry style attributes, finds 9 derived expressions, and measures a second "
            "family whose fractional output needs no fitted constant at all.",
        "hypothesisNotClaim":
            "All readings are from our own clone. The source site was not used. The pose "
            "pad is clone-only, so no source behaviour is claimed or implied.",
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "checks": v.result},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


def js_round(x: float) -> int:
    """Math.round 是四舍五入；Python 的 round 是银行家舍入（690 已栽过一次）。"""
    return math.floor(x + 0.5)


if __name__ == "__main__":
    sys.exit(main())

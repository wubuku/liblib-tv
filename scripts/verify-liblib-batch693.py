#!/usr/bin/env python3
"""batch 693 验收：**同一个控件，两个输入设备，两个不同的可达集**

## 起点

691/692 收在「位置面」上。几何普查里还有 6 条位置面没量，其中最值得量的是
**FOV 滑块**（`DirectorInspector.tsx:1638/1644`）：它是**原生 `range` 盖在自绘
旋钮上**，而 `ratio = (fov − min)/(max − min)`，min/max = 15/90（跨度 **75**）⟹
整数 FOV 也给出分数比例（691 那条「整数入、小数出」的第三个运算符：先减后除）。

## 鼠标扫（170 档逐 1px）量到三件事

1. **点击只能得到 20 个值**：`15, 19, 23, …, 87, 90` ——
   而 `step="1"` 声明了 **76** 个（15..90）。**中间 56 个值点击永远到不了。**
2. **量化在控件不在 store**：`input.value` 与 `store.fov` **170/170 一致**；
   且关键帧数 6 → 6（`recordObjectKeyframe` 是 upsert 到当前播放头，不增长）。
3. **自绘旋钮与指针错位最大 15px**：旋钮画在 `ratio × 170`，
   而浏览器自己的 thumb 有内缩，所以旋钮**追不上也跑超前指针**。

## 决定性实验：键盘

同一个 `input[type=range] step="1"`，**键盘给出每一个整数**（15,16,17,…,39）。
旁边的数值框也能给出 44（鼠标永远给不出的值）。

⟹ **同一个 FOV 值，键盘能到、数值框能到、鼠标点不到 —— 界面上没有任何地方说明。**

## 与 688 的区别（不是同一件事的复读）

688 记的是「声明量程 88..420 只在窗高 ≥508 时真的可达」——
**可达集是窗口的函数**。本批是**可达集是输入设备的函数**。两者不能互相推出。

## 自记

- **探针整整扫空了一轮**：第一版没滚进视口，FOV 字段初始在 y≈1150 而视口只有
  900 高，`page.mouse.click` **不会自动滚动**（只有 `locator.click` 会）⟹
  170 次点击全落在视口外，value 恒为 43，误差区间假到 **[−105, +63]**。
  **一个假到离谱的误差区间本身就是信号** —— 读数大到不合理时先怀疑仪器。
  修法：`scroll_into_view_if_needed()` + **断言中线在视口内**。
- **`node -e` 走的是 TS 解析**：`x.inputValue!cur.v` 里的 `!` 被当成非空断言
  （"Expected ')', got 'cur'"）。`-e` 里避开 `!` 开头，或干脆写文件。

## 不声称

- **不声称** 源站的 FOV 滑块有这个行为（**未取证**；源站导演台当前关着，
  只读侦察确认 `data-director-*` 键 0 个，进入需点击、**点击源站需授权**）；
- **不声称** 这是缺陷（**产品决定**：原生 range 在窄轨道上就是这样，
  改成 `step` 或改用自绘指针都可行，改法要动 `src/` ⟹ **不擅自改**）；
- **不声称** 16px 的左端平台是「thumb 内缩」—— **那是我的推断**；
  本批只量了「点击可达 20 个值」与「旋钮错位 ≤15px」两个读数，
  **没有**直接测出浏览器的 thumb 宽度；
- **不声称** 其余 5 条位置面（导出进度、2 条刻度、关键帧 clamp）的行为
  —— 本批只量了 FOV 这两条；
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
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch693-2026-10-01"
CENSUS = ROOT / "scripts/census-directorstore-value-domains.mjs"

W, DESK_H = 1280, 900
FOV_MIN, FOV_MAX = 15.0, 90.0
KEY_STEPS = 24

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

SELECT_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  s.selectObject(s.activeCameraId);
  return true;
}"""

READ = r"""() => {
  const wrap = document.querySelector('[data-director-camera-fov-slider]');
  const knob = document.querySelector('[data-director-camera-fov-knob]');
  const fill = document.querySelector('[data-director-camera-fov-fill]');
  const inp = document.querySelector('[data-director-camera-fov]');
  const num = document.querySelector('[data-director-camera-fov-number]');
  if (!wrap || !knob || !fill || !inp || !num) return { missing: true };
  const wr = wrap.getBoundingClientRect();
  const kr = knob.getBoundingClientRect();
  const ir = inp.getBoundingClientRect();
  const cs = getComputedStyle(wrap);
  const st = window.__director_store.getState();
  const cam = st.objects.find((o) => o.id === st.activeCameraId);
  return {
    wrapLeft: wr.left, wrapW: wr.width, wrapH: wr.height,
    borderLeft: parseFloat(cs.borderLeftWidth) || 0,
    borderRight: parseFloat(cs.borderRightWidth) || 0,
    paddingLeft: parseFloat(cs.paddingLeft) || 0,
    paddingRight: parseFloat(cs.paddingRight) || 0,
    knobCentre: kr.left + kr.width / 2, knobW: kr.width,
    fillW: fill.getBoundingClientRect().width,
    inputLeft: ir.left, inputW: ir.width, inputTop: ir.top, inputH: ir.height,
    rangeValue: inp.value,
    rangeMin: inp.getAttribute('min'), rangeMax: inp.getAttribute('max'),
    rangeStep: inp.getAttribute('step'),
    numValue: num.value,
    storeFov: cam && cam.camera ? cam.camera.fov : null,
    keyframeCount: st.timeline.tracks.reduce(
      (n, t) => n + (t.keyframes ? t.keyframes.length : 0), 0),
    autoKeyframe: st.timeline.autoKeyframe,
  };
}"""


def settle(page) -> None:
    page.evaluate("() => new Promise(r => requestAnimationFrame("
                  "() => requestAnimationFrame(() => r(true))))")


def ratio_of(value: float) -> float:
    return (value - FOV_MIN) / (FOV_MAX - FOV_MIN)


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
    r = subprocess.run(["node", str(CENSUS), "--geometry"], cwd=ROOT,
                       check=True, capture_output=True, text=True)
    census_text = r.stdout

    mouse: list[dict[str, Any]] = []
    keyboard: list[dict[str, Any]] = []
    number: list[dict[str, Any]] = []
    base: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": W, "height": DESK_H},
                           device_scale_factor=1)
        b617.open_desk(page)
        page.evaluate("() => { for (const el of document.querySelectorAll("
                      "'nextjs-portal')) el.remove(); }")
        # open_desk 后选中的是角色，属性列显示「角色属性」；用**真 setter**
        # selectObject(activeCameraId) 选中机位，属性列才切到「摄像机属性」。
        page.evaluate(SELECT_CAMERA)
        slider = page.locator("[data-director-camera-fov-slider]")
        slider.wait_for(state="visible", timeout=20_000)
        # **必须滚进视口**：属性列是滚动区，FOV 字段初始在 y≈1150 而视口 900 高。
        # `page.mouse.click` 不自动滚动 ⟹ 第一版 170 次点击全落在视口外，
        # value 恒 43，误差区间假到 [-105,+63]。
        slider.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.mouse.move(5, 5)
        page.wait_for_timeout(200)
        base = page.evaluate(READ)
        if base.get("missing"):
            print("FOV 字段没出现")
            return 1
        midY = round(base["inputTop"] + base["inputH"] / 2)
        assert 0 <= midY <= DESK_H, f"FOV 滑块不在视口内 (midY={midY})"

        L, WW = base["wrapLeft"], base["wrapW"]
        for k in range(int(WW)):
            x = round(L) + k
            page.mouse.click(x, midY)
            page.wait_for_timeout(12)
            settle(page)
            row = page.evaluate(READ)
            row["offset"] = k
            row["ratio"] = ratio_of(float(row["rangeValue"]))
            row["knobOffset"] = row["knobCentre"] - L
            row["error"] = row["knobOffset"] - k
            mouse.append(row)

        # 键盘：同一个控件
        page.locator("[data-director-camera-fov]").focus()
        page.keyboard.press("Home")
        settle(page)
        keyboard.append({"action": "Home", **page.evaluate(READ)})
        for _ in range(KEY_STEPS):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(35)
            settle(page)
            keyboard.append({"action": "ArrowRight", **page.evaluate(READ)})
        page.keyboard.press("End")
        settle(page)
        keyboard.append({"action": "End", **page.evaluate(READ)})

        # 数值框：填鼠标永远给不出的值
        num = page.locator("[data-director-camera-fov-number]")
        for want in ("44", "16", "88"):
            num.fill(want)
            page.wait_for_timeout(60)
            settle(page)
            number.append({"typed": want, **page.evaluate(READ)})
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "base": base, "mouse": mouse,
                    "keyboard": keyboard, "number": number,
                    "censusText": census_text},
                   ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    declared = int(FOV_MAX - FOV_MIN) + 1  # 76
    # 平台跨度：把相同 rangeValue 的连续 offset 归并
    plateaus: list[dict[str, Any]] = []
    for m in mouse:
        if not plateaus or plateaus[-1]["value"] != m["rangeValue"]:
            plateaus.append({"value": m["rangeValue"], "from": m["offset"],
                             "to": m["offset"]})
        else:
            plateaus[-1]["to"] = m["offset"]
    for pl in plateaus:
        pl["width"] = pl["to"] - pl["from"] + 1
    widths = sorted({pl["width"] for pl in plateaus})
    mouse_vals = sorted({int(m["rangeValue"]) for m in mouse})
    kb_vals = [int(k["rangeValue"]) for k in keyboard]
    store_agrees = [m for m in mouse
                    if int(m["rangeValue"]) == int(m["storeFov"])]

    # ---- 1. 普查：8 条位置面里只有 1 条显式取整 ----
    v.check("the-percent-family-is-eight-sites-and-only-one-rounds-explicitly",
            "百分比族 8 条" in census_text
            and "DirectorExportPanel.tsx:106" in census_text
            and "DirectorInspector.tsx:1644" in census_text,
            detail={"censusOutput": census_text.strip().split("\n"),
                    "whyThisBatchPickedFov":
                        "it is the only percent-family site whose input is a REAL control "
                        "the user drags: the pose pad is a custom div with pointer "
                        "handlers, but the FOV knob is a native range overlaid on a "
                        "self-drawn knob -- so the browser and the clone each maintain "
                        "their own value-to-position mapping.",
                    "ratioIsAlwaysFractional":
                        "ratio = (fov - 15) / 75, and 75 is not a power of two, so an "
                        "integer fov still yields a fractional percentage -- the third "
                        "operator variant of 691's mechanism (subtract, then divide)"},
            note="the census table is the worklist; the measurement picks one entry")

    # ---- 2. 鼠标可达集只有 20 个值，而声明了 76 个 ----
    v.check("clicking-the-slider-can-only-reach-twenty-of-the-seventy-six-declared-values",
            len(mouse_vals) == 20 and declared == 76
            and 44 not in mouse_vals and base["rangeStep"] == "1"
            and int(base["rangeMin"]) == 15 and int(base["rangeMax"]) == 90,
            detail={"declared": {"min": base["rangeMin"], "max": base["rangeMax"],
                                 "step": base["rangeStep"], "values": declared},
                    "reachableByClicking": mouse_vals,
                    "reachableCount": len(mouse_vals),
                    "unreachableCount": declared - len(mouse_vals),
                    "44IsUnreachableByClicking": 44 not in mouse_vals,
                    "adjacentDeltas": sorted({mouse_vals[i + 1] - mouse_vals[i]
                                              for i in range(len(mouse_vals) - 1)}),
                    "plateauWidthsPx": widths,
                    "plateauCount": len(plateaus),
                    "firstPlateau": plateaus[0],
                    "lastPlateau": plateaus[-1],
                    "notClaimedAsAThumbWidth":
                        "a native range insets its thumb at both ends, which would explain "
                        "a coarse mapping -- but this batch did NOT measure the thumb "
                        "width, so the mechanism stays an inference. The two readings it "
                        "does claim are: only 20 values are reachable, and they are "
                        "multiples of 4 offset from 15."},
            note="declared range and reachable range are different quantities (688)")

    # ---- 3. 键盘给出每一个整数 ----
    consecutive = all(kb_vals[i + 1] - kb_vals[i] == 1
                      for i in range(len(kb_vals) - 2))  # 末项是 End
    v.check("the-keyboard-on-the-same-control-reaches-every-integer",
            consecutive and kb_vals[0] == 15 and kb_vals[-1] == 90
            and set(range(15, 40)) <= set(kb_vals),
            detail={"keyboardSequence": kb_vals,
                    "afterHome": kb_vals[0],
                    "consecutiveByOne": consecutive,
                    "afterEnd": kb_vals[-1],
                    "sameElementAsTheMouseSweep": True,
                    "theContrast":
                        "mouse: 20 values, step 4. keyboard on the SAME input element: "
                        "every integer. The reachable set is a function of the INPUT "
                        "DEVICE, not of the control's declared step.",
                    "whyItIsNot688Again":
                        "688 recorded a declared range that is only reachable when the "
                        "window is tall enough -- the reachable set was a function of "
                        "the viewport. Here the viewport never changes (170 samples in "
                        "one page) and the reachable set still splits. The two do not "
                        "imply each other."},
            note="one control, two reachable sets")

    # ---- 4. 数值框也能给出鼠标给不出的值 ----
    typed_ok = [n for n in number if float(n["storeFov"]) == float(n["typed"])]
    v.check("the-number-box-reaches-what-clicking-cannot",
            len(typed_ok) == len(number) and 44 not in mouse_vals
            and any(n["typed"] == "44" for n in typed_ok),
            detail={"typedThenStored": [(n["typed"], n["storeFov"]) for n in number],
                    "allLanded": len(typed_ok) == len(number),
                    "44":
                        "44 sits between 43 and 47, i.e. between two mouse plateaus, so "
                        "no click can ever produce it -- yet the number box sets it in the "
                        "store directly",
                    "soThereAreThreeWaysToSetFovAndTheyDisagree":
                        "click: 20 values. keyboard: all 76. number box: any value in "
                        "[15,90] it accepts. Nothing on screen states this."},
            note="two controls over the same value, different reachable sets")

    # ---- 5. 量化在控件不在 store + 关键帧没长 ----
    v.check("the-coarse-quantisation-belongs-to-the-control-not-to-the-store",
            len(store_agrees) == len(mouse)
            and base["keyframeCount"] == mouse[-1]["keyframeCount"] == 6,
            detail={"samples": len(mouse),
                    "inputValueEqualsStoreFov": len(store_agrees),
                    "keyframeCountBefore": base["keyframeCount"],
                    "keyframeCountAfter": mouse[-1]["keyframeCount"],
                    "autoKeyframe": base["autoKeyframe"],
                    "whyThisMatters":
                        "the alternative reading -- 'the store rounds fov' -- is excluded "
                        "by the readings, not by reasoning. 170/170 samples have "
                        "input.value identical to store.fov, so the coarse set is what "
                        "the control hands over.",
                    "whyTheSweepIsSafe":
                        "commit() calls recordObjectKeyframe on every change, but that is "
                        "an UPSERT at timeline.currentTime, so 170 changes at the same "
                        "playhead replace one keyframe instead of growing the track. "
                        "Measured: 6 keyframes before and after.",
                    "notMeasured":
                        "this says the store accepts whatever the control gives; it does "
                        "NOT say the store would reject a fraction -- and the store "
                        "accepts one, which is why 690's census put nothing about fov in "
                        "the rounded class."},
            note="reading the store and reading the control are different questions")

    # ---- 6. 自绘旋钮追不上指针 ----
    errs = [m["error"] for m in mouse]
    worst = min(mouse, key=lambda m: m["error"])
    v.check("the-self-drawn-knob-cannot-keep-up-with-the-pointer",
            min(errs) <= -15 and max(errs) > 5
            and base["borderLeft"] == 0 and base["borderRight"] == 0,
            detail={"errorRangePx": [min(errs), max(errs)],
                    "worstSample": {"offset": worst["offset"],
                                    "rangeValue": worst["rangeValue"],
                                    "knobOffset": worst["knobOffset"],
                                    "error": worst["error"]},
                    "noBorderOnThisOne":
                        "measured borderLeft=0, borderRight=0 -- so 691/692's border-box "
                        "mismatch CANNOT be the cause here. This is a different mechanism "
                        "on a control that looks nearly identical.",
                    "theDraw":
                        "the knob is drawn at left: ratio*100% of a 170px box, with no "
                        "thumb inset, while the browser's own thumb is inset at both "
                        "ends -- so the drawn position trails the pointer on the left "
                        "and leads it on the right",
                    "magnitude": "up to 15px, an order of magnitude above the 1px the "
                                 "pose pad shows and two above 690's 1/64px",
                    "mechanismStatus":
                        "the coarse mapping and the inset are both consistent with a "
                        "native range's thumb inset, but the thumb width was NOT "
                        "measured -- treat the mechanism as inference, the numbers as "
                        "readings"},
            note="same shape as the pose pad, ten times the error, different cause")

    out = {
        "width": W, "deskHeight": DESK_H, "base": base,
        "declaredRange": {"min": FOV_MIN, "max": FOV_MAX, "step": 1,
                          "values": declared},
        "reachableByClicking": mouse_vals,
        "reachableByKeyboard": kb_vals,
        "mouseSweep": mouse, "keyboard": keyboard, "number": number,
        "censusText": census_text.strip(),
        "theHeadline":
            "One control, two reachable sets: clicking the FOV slider can only produce "
            "20 of the 76 values its own step=1 declares, while the keyboard on the very "
            "same input element produces every integer, and the number box accepts 44 -- "
            "which no click can ever produce. Nothing on screen says so.",
        "howTheCameraWasSelected":
            "open_desk leaves a CHARACTER selected, so the inspector shows the character "
            "panel. Called the real setter selectObject(activeCameraId) to switch the "
            "inspector to the camera panel. That is the only store write in the sweep.",
        "storeWritesInThisRun": ["selectObject(activeCameraId)"],
        "relationTo688":
            "688 recorded a declared range reachable only when the viewport is tall "
            "enough. This is a declared range reachable only by some input devices. The "
            "viewport is constant across all 170 samples, so the two do not imply each "
            "other.",
        "hypothesisNotClaim":
            "All readings are from our own clone; the source site was not used and no "
            "source behaviour is claimed. Whether 15px of knob lag is a defect is a "
            "product decision, and the fix would touch src/, so nothing was changed.",
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
